"""Tests for two-way Telegram notification channel (spec 6kwd2e R10.5, R10.6, R10.8a, qrup8m).

Guards that:
1. Token is never leaked in errors, tracebacks, or health summaries.
2. Long text is truncated to <= 4000 UTF-16 units without splitting surrogate pairs.
3. Terse mode sends one message with no buttons; full mode sends inline keyboard with tokens and force_reply.
4. Send failures/timeouts record notify-uncertain and do not auto-resend.
5. Inbound events are verified (numeric user id, private chat id, not a bot), duplicate updates ignored,
   tokens mapped to questions, unthreaded text rejected, and callbacks/replies acknowledged (A50, A52).
6. Offset file is updated atomically only after handling, and batch stops on failure without advancing.
7. Receiver daemon thread coordinates via per-bot lock, drains queued updates on startup, handles takeover,
   and stops on 409 Conflict without affecting run exit code (A51).
8. Polling is refused when a webhook is configured (E-04).
9. Consumed answers trigger editMessageReplyMarkup and threaded chat acknowledgement (E-06, A55).
10. End-to-end scripted run on both OpenCode and Antigravity runners parks, receives Telegram answer,
    consumes, and resumes to completion.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import threading
import time
import traceback
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    question_inbox,
    runner_shared,
)
from agent_workflows.notify import config, core as notify_core, registry
from agent_workflows.notify.core import OutboundBatch, OutboundQuestion
from agent_workflows.notify.telegram import (
    TelegramChannel,
    TelegramError,
    TelegramReceiver,
    ensure_receiver,
    read_offset,
    save_offset,
    truncate_utf16,
    utf16_len,
)
from tests.fake_telegram import run_fake_telegram
from tests.support import coordinator_role

pytestmark = pytest.mark.core


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _create_test_repo(root: Path) -> Path:
    """Initialize a git repo with required .aw structure and initial commit."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (
        repo
        / ".aw"
        / "records"
        / "releases"
        / "20261009-rel001-01-rel001-v1.release.md"
    ).write_text(
        "# Release: 1.0.0\n\n- Id: rel001\n- Version: 1.0.0\n- Status: planned\n- Set: rel001 (1.0.0)\n- Order: 01\n",
        encoding="utf-8",
    )
    (repo / ".aw" / "records" / "plans" / "pending" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )
    (repo / ".aw" / "records" / "backlog" / "open" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial repo commit"], cwd=repo, check=True
    )
    return repo


def _create_plan_file(
    repo: Path,
    id6: str,
    *,
    setid: str = "testset",
    order: int = 1,
    status: str = "approved",
    priority: str = "medium",
    work_kind: str = "feature",
) -> Path:
    """Create a minimal valid plan file in pending/."""
    plan_path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261017-{setid}-{order:02d}-{id6}-test-plan.ipd.md"
    )
    plan_content = f"""# Test Plan: {id6}

- Id: {id6}
- Set: {setid}
- Order: {order}
- Status: {status}
- Priority: {priority}
- Work-Kind: {work_kind}

## Goal

Test plan {id6}.
"""
    plan_path.write_text(plan_content, encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


# -----------------------------------------------------------------------------
# E-01 / V-01: Transport, token redaction, UTF-16 truncation, sends
# -----------------------------------------------------------------------------


def test_token_redaction_and_transport_safety(monkeypatch: pytest.MonkeyPatch) -> None:
    """V-01: 401 error and connection refused raise TelegramError with no token in str, repr or traceback."""
    secret_token = "987654321:SECRET_TOKEN_XYZ_12345"
    channel = TelegramChannel(
        {
            "token": secret_token,
            "chat_id": "111",
            "user_id": "111",
        }
    )

    # Test 1: Refused connection
    # Point at closed loopback port
    monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", "http://127.0.0.1:54321")
    refused_exc: TelegramError | None = None
    refused_tb: str = ""
    try:
        channel._call("getMe", timeout=1.0)
    except TelegramError as e:
        refused_exc = e
        refused_tb = traceback.format_exc()

    assert refused_exc is not None
    assert secret_token not in str(refused_exc)
    assert secret_token not in repr(refused_exc)
    assert secret_token not in refused_tb
    assert (
        "Connection refused" in str(refused_exc)
        or "54321" in str(refused_exc)
        or "getMe" in refused_tb
    )

    # Test 2: HTTP 401 from fake server
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        invalid_channel = TelegramChannel(
            {
                "token": f"invalid_{secret_token}",
                "chat_id": "111",
                "user_id": "111",
            }
        )
        http_401_exc: TelegramError | None = None
        http_401_tb: str = ""
        try:
            invalid_channel._call("getMe", timeout=2.0)
        except TelegramError as e:
            http_401_exc = e
            http_401_tb = traceback.format_exc()

        assert http_401_exc is not None
        assert http_401_exc.code == 401
        assert secret_token not in str(http_401_exc)
        assert secret_token not in repr(http_401_exc)
        assert secret_token not in http_401_tb
        assert "401" in str(http_401_exc)

    # Test 3: Refuse non-HTTPS on non-loopback host
    monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", "http://api.telegram.org")
    with pytest.raises(TelegramError) as exc_info:
        channel._call("getMe")
    assert "Refusing non-HTTPS" in str(exc_info.value)


def test_utf16_limit_with_non_bmp_text() -> None:
    """V-01: 5000-character text with non-BMP characters at the cut is truncated to <= 4000 UTF-16 units without splitting surrogate pairs."""
    # Each '😀' (U+1F600) is 2 UTF-16 code units (1 code point, 4 bytes UTF-8)
    # Build text of 2500 emojis (5000 UTF-16 code units)
    text = "😀" * 2500
    assert len(text) == 2500
    assert utf16_len(text) == 5000

    truncated = truncate_utf16(text, max_units=4000)
    assert utf16_len(truncated) == 4000
    assert len(truncated) == 2000
    # Decodes cleanly to UTF-16LE with no lone surrogates
    encoded_utf16 = truncated.encode("utf-16-le")
    assert len(encoded_utf16) == 8000
    assert encoded_utf16.decode("utf-16-le") == truncated

    # Test edge case: 3999 BMP characters + 1 non-BMP character
    edge_text = ("a" * 3999) + "😀"
    assert utf16_len(edge_text) == 4001
    edge_truncated = truncate_utf16(edge_text, max_units=4000)
    assert utf16_len(edge_truncated) == 3999
    assert edge_truncated == "a" * 3999


def test_terse_and_full_sends_against_fake_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-01: Full-mode question produces sendMessage with no parse_mode, previews disabled, callback_data <= 64 bytes, force_reply; terse batch has no reply_markup."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        channel = TelegramChannel(
            {
                "token": "123456:FAKE_TOKEN",
                "chat_id": "999888",
                "user_id": "999888",
                "mode": "full",
            },
            run_dir=tmp_path,
        )

        # 1. Full mode question with options and free text
        batch_full = OutboundBatch(
            run_id="run-test-full",
            mode="full",
            message="run run-test-full: 1 question waiting",
            questions=[
                OutboundQuestion(
                    question_id="q_full_01",
                    text="Should we migrate the database now?",
                    options=["Migrate Now", "Postpone"],
                    allow_free_text=True,
                    answer_command="aw runs answer run-test-full q_full_01",
                )
            ],
        )

        receipt = channel.send(batch_full)
        assert receipt.ok is True
        assert len(server.sent_messages) == 1

        msg = server.sent_messages[0]
        # Verify message body properties
        assert "parse_mode" not in msg
        assert msg.get("link_preview_options") == {"is_disabled": True}
        assert "reply_markup" in msg
        markup = msg["reply_markup"]
        assert markup.get("force_reply") is True
        assert "inline_keyboard" in markup
        rows = markup["inline_keyboard"]
        assert len(rows) == 1
        buttons = rows[0]
        assert len(buttons) == 2
        for btn in buttons:
            cb_data = btn.get("callback_data", "")
            assert len(cb_data.encode("utf-8")) <= 64
            assert cb_data.startswith("t:")

        # Verify registry registration before send completed
        routes = registry.lookup("telegram", str(msg["message_id"]))
        assert routes is not None
        assert routes["question_id"] == "q_full_01"
        assert routes["option"] is None

        btn0_tok = buttons[0]["callback_data"]
        btn0_route = registry.lookup("telegram", btn0_tok)
        assert btn0_route is not None
        assert btn0_route["question_id"] == "q_full_01"
        assert btn0_route["option"] == 0

        # 2. Terse mode batch
        server.sent_messages.clear()
        channel_terse = TelegramChannel(
            {
                "token": "123456:FAKE_TOKEN",
                "chat_id": "999888",
                "user_id": "999888",
                "mode": "terse",
            },
            run_dir=tmp_path,
        )
        batch_terse = OutboundBatch(
            run_id="run-test-terse",
            mode="terse",
            message="run run-test-terse: 1 question waiting; answer with aw runs answer run-test-terse",
            questions=[
                OutboundQuestion(
                    question_id="q_terse_01",
                    text="Should we migrate?",
                )
            ],
        )
        receipt_terse = channel_terse.send(batch_terse)
        assert receipt_terse.ok is True
        assert len(server.sent_messages) == 1

        msg_terse = server.sent_messages[0]
        assert "parse_mode" not in msg_terse
        assert msg_terse.get("link_preview_options") == {"is_disabled": True}
        assert "reply_markup" not in msg_terse


def test_uncertain_send_delivery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E-01: Network / timeout errors during send record notify-uncertain and do not automatically resend."""
    with run_fake_telegram() as server:
        server.scripted_send_message.append(500)
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)

        channel = TelegramChannel(
            {
                "token": "123456:FAKE_TOKEN",
                "chat_id": "999888",
                "user_id": "999888",
                "mode": "terse",
            },
            run_dir=tmp_path,
        )

        batch = OutboundBatch(
            run_id="run-uncertain",
            mode="terse",
            message="run run-uncertain: 1 question waiting",
            questions=[OutboundQuestion(question_id="q_unc_1", text="?")],
        )

        receipt = channel.send(batch)
        assert receipt.ok is False
        assert getattr(receipt, "uncertain", False) is True

        # Check events.jsonl
        events_file = tmp_path / "events.jsonl"
        assert events_file.is_file()
        lines = [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert any(ev.get("event") == "notify-uncertain" for ev in lines)


# -----------------------------------------------------------------------------
# E-02 / V-02: Inbound routing, verification, replay dedup, offset handling
# -----------------------------------------------------------------------------


def test_inbound_routing_and_replays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-02: Button press, threaded reply, unthreaded text, wrong user, bot sender, group chat, and replayed update (A50, A52)."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        channel = TelegramChannel(
            {
                "token": "123456:FAKE_TOKEN",
                "chat_id": "777",
                "user_id": "888",
            },
            run_dir=tmp_path,
        )

        # Create question in inbox
        run_dir = tmp_path / "test_run"
        run_dir.mkdir(parents=True, exist_ok=True)
        plan1 = tmp_path / "20261017-qchan-09-it0001-test.ipd.md"
        plan1.write_text("# Plan it0001\n- Id: it0001\n", encoding="utf-8")
        item1 = {
            "position": 1,
            "id6": "it0001",
            "current_attempt": 1,
            "configured_file": str(plan1),
            "artifact_path": str(plan1),
            "repo": str(tmp_path),
        }
        qid = "01-it0001-a1-q1"
        question_inbox.write_question(
            run_dir=run_dir,
            item=item1,
            question={
                "question_id": qid,
                "text": "Approve release?",
                "options": ["Yes", "No"],
                "allow_free_text": True,
            },
            attempt=1,
            repo=tmp_path,
        )

        # Register message_id and tokens
        msg_id = "5001"
        btn_token = "t:secret_choice_token"
        registry.register("telegram", msg_id, run_dir, qid, option=None)
        registry.register("telegram", btn_token, run_dir, qid, option=0)

        # Case 1: Valid button press
        upd_btn = server.add_button_update(
            update_id=101,
            user_id="888",
            chat_id="777",
            message_id=int(msg_id),
            callback_data=btn_token,
            callback_id="cb_ok",
        )
        ev_btn = channel._translate_update(upd_btn)
        assert ev_btn is not None
        outcome_btn = notify_core.apply_inbound(channel, ev_btn)
        assert outcome_btn == "recorded"
        # Check answer written
        ans_file = run_dir / "answers" / f"{qid}.json"
        assert ans_file.is_file()
        ans_data = json.loads(ans_file.read_text(encoding="utf-8"))
        assert ans_data["choice"] == 0
        assert ans_data["channel"] == "telegram"
        assert ans_data["actor"] == "human"
        assert ans_data["sender"] == "888"
        # Check ack
        assert len(server.callback_answers) == 1
        assert server.callback_answers[0]["callback_query_id"] == "cb_ok"
        assert server.callback_answers[0]["text"] == "recorded"

        # Case 2: Replayed button update
        outcome_replay = notify_core.apply_inbound(channel, ev_btn)
        assert outcome_replay == "ignored"

        # Case 3: Threaded text reply to a new question
        plan2 = tmp_path / "20261017-qchan-09-it0002-test.ipd.md"
        plan2.write_text("# Plan it0002\n- Id: it0002\n", encoding="utf-8")
        item2 = {
            "position": 2,
            "id6": "it0002",
            "current_attempt": 1,
            "configured_file": str(plan2),
            "artifact_path": str(plan2),
            "repo": str(tmp_path),
        }
        qid2 = "02-it0002-a1-q2"
        question_inbox.write_question(
            run_dir=run_dir,
            item=item2,
            question={
                "question_id": qid2,
                "text": "What version name?",
                "allow_free_text": True,
            },
            attempt=1,
            repo=tmp_path,
        )
        msg_id2 = "5002"
        registry.register("telegram", msg_id2, run_dir, qid2, option=None)

        upd_text = server.add_text_update(
            update_id=102,
            user_id="888",
            chat_id="777",
            text="v2.0-rc1",
            reply_to_message_id=int(msg_id2),
        )
        ev_text = channel._translate_update(upd_text)
        assert ev_text is not None
        outcome_text = notify_core.apply_inbound(channel, ev_text)
        assert outcome_text == "recorded"
        ans_file2 = run_dir / "answers" / f"{qid2}.json"
        assert ans_file2.is_file()
        ans_data2 = json.loads(ans_file2.read_text(encoding="utf-8"))
        assert ans_data2["answer"] == "v2.0-rc1"
        # Check ack message
        assert any(
            m.get("text") == "recorded" and m.get("reply_to_message_id") == 2102
            for m in server.sent_messages
        )

        # Case 4: Unthreaded text message
        upd_unthreaded = server.add_text_update(
            update_id=103,
            user_id="888",
            chat_id="777",
            text="random unsolicited chat",
            reply_to_message_id=None,
        )
        ev_unthreaded = channel._translate_update(upd_unthreaded)
        assert ev_unthreaded is not None
        outcome_unthreaded = notify_core.apply_inbound(channel, ev_unthreaded)
        assert outcome_unthreaded == "rejected"
        # Acked 'not accepted'
        assert any(
            m.get("text") == "not accepted" and m.get("reply_to_message_id") == 2103
            for m in server.sent_messages
        )

        # Case 5: Wrong user id (A50)
        upd_wrong_user = server.add_text_update(
            update_id=104,
            user_id="999",  # not 888
            chat_id="777",
            text="intruder",
            reply_to_message_id=int(msg_id2),
        )
        ev_wrong_user = channel._translate_update(upd_wrong_user)
        assert ev_wrong_user is not None
        assert channel.verify(ev_wrong_user) is None
        outcome_wrong_user = notify_core.apply_inbound(channel, ev_wrong_user)
        assert outcome_wrong_user == "ignored"

        # Case 6: Bot sender (A50)
        upd_bot = server.add_text_update(
            update_id=105,
            user_id="888",
            chat_id="777",
            text="bot message",
            reply_to_message_id=int(msg_id2),
            is_bot=True,
        )
        ev_bot = channel._translate_update(upd_bot)
        assert ev_bot is not None
        assert channel.verify(ev_bot) is None
        outcome_bot = notify_core.apply_inbound(channel, ev_bot)
        assert outcome_bot == "ignored"

        # Case 7: Group chat (A50)
        upd_group = server.add_text_update(
            update_id=106,
            user_id="888",
            chat_id="777",
            text="group message",
            reply_to_message_id=int(msg_id2),
            chat_type="group",
        )
        ev_group = channel._translate_update(upd_group)
        assert ev_group is not None
        assert channel.verify(ev_group) is None
        outcome_group = notify_core.apply_inbound(channel, ev_group)
        assert outcome_group == "ignored"


def test_offset_persistence_and_batch_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E-02: Offset file holds cursor atomically; if apply_inbound raises, offset is not advanced past that update."""
    bot_id = "testbot123"

    # Initial state
    assert read_offset(bot_id) is None
    save_offset(bot_id, 100)
    assert read_offset(bot_id) == 100

    # Simulate receiver batch handling
    channel = TelegramChannel(
        {"token": f"{bot_id}:TOKEN", "chat_id": "1", "user_id": "1"},
        run_dir=tmp_path,
        poll_timeout_cap=0.1,
    )
    receiver = TelegramReceiver(
        bot_id=bot_id,
        channel=channel,
        run_dir=tmp_path,
        poll_timeout_cap=0.1,
    )

    ev1 = notify_core.InboundEvent(
        channel="telegram", event_id="101", sender="1", key=None
    )
    ev2 = notify_core.InboundEvent(
        channel="telegram", event_id="102", sender="1", key=None
    )

    def fake_receive(
        cursor: int | None = None, deadline: float = 0.0
    ) -> tuple[list[notify_core.InboundEvent], int | None]:
        return [ev1, ev2], 103

    applied_ev2 = threading.Event()

    def fake_apply(ch: Any, ev: notify_core.InboundEvent) -> str:
        if ev.event_id == "102":
            applied_ev2.set()
            raise RuntimeError("Disk write failure")
        return "recorded"

    with (
        mock.patch.object(channel, "receive", side_effect=fake_receive),
        mock.patch(
            "agent_workflows.notify.telegram.apply_inbound", side_effect=fake_apply
        ),
    ):
        receiver.start()
        assert applied_ev2.wait(
            timeout=10.0
        ), "timed out waiting for receiver to process batch"
        receiver.stop(timeout=2.0)

    # Event 1 advanced offset to 102; Event 2 failed so offset was NOT advanced to 103
    assert read_offset(bot_id) == 102
    events_file = tmp_path / "events.jsonl"
    records = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        r.get("event") == "notify-inbound-failed" and r.get("update_id") == 102
        for r in records
    )


# -----------------------------------------------------------------------------
# E-03 / V-03: Receiver lock, takeover, startup drain, 409 conflict
# -----------------------------------------------------------------------------


def test_receiver_lock_and_takeover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-03: Two runners on one bot: only lock holder polls; second runner takes over after first exits (A51)."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        bot_id = "5555"
        token = f"{bot_id}:SECRET"

        cfg = {
            "telegram": {
                "enabled": True,
                "token": token,
                "chat_id": "123",
                "user_id": "123",
            }
        }
        config.save_user_config(cfg)

        run_dir_1 = tmp_path / "run_1"
        run_dir_2 = tmp_path / "run_2"
        run_dir_1.mkdir(parents=True, exist_ok=True)
        run_dir_2.mkdir(parents=True, exist_ok=True)

        # Start Runner 1 receiver
        r1 = ensure_receiver(run_dir_1, poll_timeout_cap=0.1)
        assert r1 is not None
        assert r1.is_alive()

        # Runner 2 attempts receiver while Runner 1 holds lock
        # Reset _CURRENT_RECEIVER to simulate independent runner process
        import agent_workflows.notify.telegram as tg_mod

        tg_mod._CURRENT_RECEIVER = None

        r2 = ensure_receiver(run_dir_2, poll_timeout_cap=0.1)
        assert r2 is None  # Lock held by Runner 1!

        def _wait_for_started_event(
            run_dir: Path, timeout: float = 10.0
        ) -> list[dict[str, Any]]:
            events_path = run_dir / "events.jsonl"
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if events_path.exists():
                    events = [
                        json.loads(line)
                        for line in events_path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                    if any(
                        ev.get("event") == "notify-receiver-started" for ev in events
                    ):
                        return events
                time.sleep(0.02)
            raise TimeoutError(
                f"timed out waiting for notify-receiver-started in {events_path}"
            )

        events_1 = _wait_for_started_event(run_dir_1)
        assert any(ev.get("event") == "notify-receiver-started" for ev in events_1)

        # Stop Runner 1
        r1.stop(timeout=2.0)
        assert not r1.is_alive()

        # Now Runner 2 takes over at its checkpoint!
        tg_mod._CURRENT_RECEIVER = None
        r2_takeover = ensure_receiver(run_dir_2, poll_timeout_cap=0.1)
        assert r2_takeover is not None
        assert r2_takeover.is_alive()

        events_2 = _wait_for_started_event(run_dir_2)
        assert any(ev.get("event") == "notify-receiver-started" for ev in events_2)

        r2_takeover.stop(timeout=2.0)


def test_receiver_409_conflict_stops_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-03: HTTP 409 conflict stops the receiver thread, releases lock, and records notify-receiver-stopped with remedy."""
    with run_fake_telegram() as server:
        server.scripted_get_updates.append(409)
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        bot_id = "409409"
        token = f"{bot_id}:SECRET"

        cfg = {
            "telegram": {
                "enabled": True,
                "token": token,
                "chat_id": "123",
                "user_id": "123",
            }
        }
        config.save_user_config(cfg)

        import agent_workflows.notify.telegram as tg_mod

        tg_mod._CURRENT_RECEIVER = None

        receiver = ensure_receiver(tmp_path, poll_timeout_cap=0.1)
        assert receiver is not None

        # Thread will hit 409 and terminate
        t0 = time.time()
        while receiver.is_alive() and time.time() - t0 < 2.0:
            time.sleep(0.05)
        assert not receiver.is_alive()

        events = [
            json.loads(line)
            for line in (tmp_path / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        stopped_ev = [
            ev for ev in events if ev.get("event") == "notify-receiver-stopped"
        ]
        assert len(stopped_ev) >= 1
        assert "409" in stopped_ev[0].get("reason", "") or "409" in stopped_ev[0].get(
            "detail", ""
        )
        assert "one bot per machine" in stopped_ev[0].get("detail", "")


def test_receiver_start_of_run_drain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-03: An update queued before any runner started is applied after the next run starts (A51)."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        bot_id = "drain123"
        token = f"{bot_id}:SECRET"

        # Create question in inbox
        run_dir = tmp_path / "run_drain"
        run_dir.mkdir(parents=True, exist_ok=True)
        plan_drain = tmp_path / "20261017-qchan-09-drn001-test.ipd.md"
        plan_drain.write_text("# Plan drn001\n- Id: drn001\n", encoding="utf-8")
        item_drain = {
            "position": 1,
            "id6": "drn001",
            "current_attempt": 1,
            "configured_file": str(plan_drain),
            "artifact_path": str(plan_drain),
            "repo": str(tmp_path),
        }
        qid_drain = "01-drn001-a1-q1"
        question_inbox.write_question(
            run_dir=run_dir,
            item=item_drain,
            question={
                "question_id": qid_drain,
                "text": "Drain test?",
                "options": ["Proceed"],
            },
            attempt=1,
            repo=tmp_path,
        )
        registry.register("telegram", "t:drain_token", run_dir, qid_drain, option=0)

        # Enqueue update on fake server BEFORE runner starts
        server.add_button_update(
            update_id=50,
            user_id="123",
            chat_id="123",
            message_id=999,
            callback_data="t:drain_token",
        )

        cfg = {
            "telegram": {
                "enabled": True,
                "token": token,
                "chat_id": "123",
                "user_id": "123",
            }
        }
        config.save_user_config(cfg)

        import agent_workflows.notify.telegram as tg_mod

        tg_mod._CURRENT_RECEIVER = None

        receiver = ensure_receiver(run_dir, poll_timeout_cap=0.1)
        assert receiver is not None

        # Wait for drain poll
        time.sleep(0.3)
        receiver.stop(timeout=2.0)

        # Verify answer was applied
        ans_file = run_dir / "answers" / f"{qid_drain}.json"
        assert ans_file.is_file()
        ans_data = json.loads(ans_file.read_text(encoding="utf-8"))
        assert ans_data["choice"] == 0
        assert ans_data["actor"] == "human"


def test_no_telegram_starts_no_thread(tmp_path: Path) -> None:
    """V-03: Run without Telegram configured starts no receiver thread and records no receiver event."""
    config.save_user_config({})
    import agent_workflows.notify.telegram as tg_mod

    tg_mod._CURRENT_RECEIVER = None

    receiver = ensure_receiver(tmp_path)
    assert receiver is None
    assert not (tmp_path / "events.jsonl").exists()


# -----------------------------------------------------------------------------
# E-04 / V-04: Webhook refusal
# -----------------------------------------------------------------------------


def test_webhook_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V-04: With a webhook set on fake bot, no getUpdates and no deleteWebhook is called; sends still succeed (E-04)."""
    with run_fake_telegram() as server:
        server.webhook_url = "https://example.com/existing_webhook"
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        bot_id = "wh_refuse"
        token = f"{bot_id}:SECRET"

        cfg = {
            "telegram": {
                "enabled": True,
                "token": token,
                "chat_id": "123",
                "user_id": "123",
            }
        }
        config.save_user_config(cfg)

        import agent_workflows.notify.telegram as tg_mod

        tg_mod._CURRENT_RECEIVER = None

        receiver = ensure_receiver(tmp_path)
        assert receiver is None  # Refused!

        # Check recorded event
        events = [
            json.loads(line)
            for line in (tmp_path / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert any(
            ev.get("event") == "notify-receiver-stopped"
            and "Webhook active" in ev.get("detail", "")
            and "deleteWebhook" in ev.get("detail", "")
            for ev in events
        )

        # Check fake server requests: getWebhookInfo called, but NO getUpdates and NO deleteWebhook
        called_methods = [r["api_method"] for r in server.requests]
        assert "getWebhookInfo" in called_methods
        assert "getUpdates" not in called_methods
        assert "deleteWebhook" not in called_methods

        # Outbound sends still work!
        channel = TelegramChannel(cfg["telegram"], run_dir=tmp_path)
        receipt = channel.send(
            OutboundBatch(
                run_id="run-wh",
                mode="terse",
                message="run run-wh: 1 question waiting",
                questions=[OutboundQuestion(question_id="q1", text="?")],
            )
        )
        assert receipt.ok is True


# -----------------------------------------------------------------------------
# E-06 / V-06: Chat acknowledgements
# -----------------------------------------------------------------------------


def test_chat_acknowledgements(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V-06: Consumed answers edit original reply markup and send threaded acknowledgement; stale answers send stale notice (E-06, A55)."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        channel = TelegramChannel(
            {
                "token": "123456:SECRET",
                "chat_id": "777",
                "user_id": "888",
            },
            run_dir=tmp_path,
        )

        # Register a question message
        qid_consumed = "q_ack_consumed"
        qid_stale = "q_ack_stale"
        orig_msg_id_1 = "6101"
        orig_msg_id_2 = "6102"
        registry.register("telegram", orig_msg_id_1, tmp_path, qid_consumed)
        registry.register("telegram", orig_msg_id_2, tmp_path, qid_stale)

        # 1. Consumed acknowledgement batch
        batch_consumed = OutboundBatch(
            run_id="run-ack",
            mode="terse",
            message="run run-ack (q_ack_consumed): answered via telegram",
            questions=[OutboundQuestion(question_id=qid_consumed, text="")],
        )
        receipt_consumed = channel.send(batch_consumed)
        assert receipt_consumed.ok is True

        # Check fake server: editMessageReplyMarkup for 6101 and threaded sendMessage
        assert len(server.reply_markup_edits) == 1
        assert server.reply_markup_edits[0]["message_id"] == 6101
        assert server.reply_markup_edits[0]["reply_markup"] == {"inline_keyboard": []}

        sent = server.sent_messages[-1]
        assert sent["reply_to_message_id"] == 6101
        assert "answered via telegram" in sent["text"]

        # 2. Stale acknowledgement batch
        batch_stale = OutboundBatch(
            run_id="run-ack",
            mode="terse",
            message="run run-ack (q_ack_stale): answer not applied: the plan changed; ask again",
            questions=[OutboundQuestion(question_id=qid_stale, text="")],
        )
        receipt_stale = channel.send(batch_stale)
        assert receipt_stale.ok is True

        assert len(server.reply_markup_edits) == 2
        assert server.reply_markup_edits[1]["message_id"] == 6102

        sent_stale = server.sent_messages[-1]
        assert sent_stale["reply_to_message_id"] == 6102
        assert "answer not applied: the plan changed" in sent_stale["text"]


# -----------------------------------------------------------------------------
# E-05: Scripted end-to-end runner test on OpenCode and Antigravity
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_end_to_end_scripted_run(
    runner_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E-05: Scripted end-to-end run on oc and agy: parked question reaches fake Telegram, button press answered, checkpoint consumes and resumes."""
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_POLL_TIMEOUT", "0.05")

        repo = _create_test_repo(tmp_path)
        plan = _create_plan_file(repo, "e2e001")

        bot_id = f"e2e_{runner_name}"
        token = f"{bot_id}:SECRET_KEY"
        cfg = {
            "telegram": {
                "enabled": True,
                "token": token,
                "chat_id": "4444",
                "user_id": "4444",
                "mode": "full",
            }
        }
        config.save_user_config(cfg)

        import agent_workflows.notify.telegram as tg_mod

        tg_mod._CURRENT_RECEIVER = None

        run_dir = repo / ".aw" / "records" / "runs" / f"run-e2e-{runner_name}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        qid = "01-e2e001-a1-q-deploy"
        outcome_turn_1 = {
            "disposition": "partial",
            "defect_report": {"state": "none-found", "findings": []},
            "questions": [
                {
                    "question_id": qid,
                    "text": "Approve deploy?",
                    "artifact_id6": "e2e001",
                    "evidence": ["e2e test verification"],
                    "options": ["Approve", "Deny"],
                    "gates_verdict": True,
                }
            ],
            "pushed": False,
        }
        outcome_turn_2 = {
            "disposition": "executed",
            "defect_report": {"state": "none-found", "findings": []},
            "pushed": False,
        }

        item = {
            "id6": "e2e001",
            "setid": "testset",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(plan),
            "attempts": [],
        }

        fake_bin = tmp_path / "fake_agent.sh"
        fake_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_bin.chmod(0o755)

        state = {
            "repo": str(repo),
            "run_id": f"run-e2e-{runner_name}",
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": False,
                "output_mode": "quiet",
            },
        }

        driver_module = oc_runipd if runner_name == "oc" else agy_runipd
        turn_count = 0

        def side_effect_executor(
            state_arg: Any,
            rd_arg: Any,
            it_arg: Any,
            *args: Any,
            **kwargs: Any,
        ) -> tuple[int, str | None, Path, list[str]]:
            log_f = rd_arg / f"logs/{it_arg['id6']}.log"
            log_f.parent.mkdir(parents=True, exist_ok=True)
            log_f.write_text("log\n", encoding="utf-8")

            if it_arg.get("id6") == "probe1":
                return (0, "ses-probe", log_f, [])

            nonlocal turn_count
            turn_count += 1
            out_file = (
                rd_arg / f"outcomes/{it_arg['position']:02d}-{it_arg['id6']}.json"
            )

            if turn_count == 1:
                # Turn 1: park with question
                out_file.write_text(json.dumps(outcome_turn_1), encoding="utf-8")
                return (3, "ses-1", log_f, [])
            else:
                # Turn 2: executed
                out_file.write_text(json.dumps(outcome_turn_2), encoding="utf-8")
                exec_dir = repo / ".aw" / "records" / "plans" / "executed"
                exec_dir.mkdir(parents=True, exist_ok=True)
                if plan.exists():
                    plan.rename(exec_dir / plan.name)
                return (0, "ses-1", log_f, [])

        runner_shared.save_state(run_dir, state)

        with (
            mock.patch.object(
                driver_module,
                "run_opencode" if runner_name == "oc" else "run_agy_turn",
                side_effect=side_effect_executor,
            ),
            mock.patch.object(driver_module, "driver_begin", return_value=(0, "ok")),
            mock.patch.object(driver_module, "driver_finalize", return_value=(0, "ok")),
            coordinator_role(),
        ):
            # Stage 1: Item parks awaiting-human with exit code 3
            rc1 = driver_module.run_queue(run_dir, state)
            assert rc1 == 3

            # Verify question was sent to fake Telegram with inline button
            assert len(server.sent_messages) >= 1
            msg = server.sent_messages[0]
            kb = msg.get("reply_markup", {}).get("inline_keyboard", [])
            assert kb, "Expected inline keyboard on question message"
            tok = kb[0][0]["callback_data"]

            # User answers by pressing the button on Telegram while run is paused awaiting human
            u_id = 9001 if runner_name == "oc" else 9002
            server.add_button_update(
                update_id=u_id,
                user_id="4444",
                chat_id="4444",
                message_id=msg["message_id"],
                callback_data=tok,
            )

            # Stage 2: Resume run; receiver performs start-of-run drain, answers are consumed, item finishes
            state = runner_shared.load_state(run_dir)
            rc2 = driver_module.run_queue(run_dir, state)
            assert rc2 == 0

        # Check answer was written to answers/ and consumed
        ans_file = run_dir / "answers" / f"{qid}.json"
        assert ans_file.is_file()

        final_state = runner_shared.load_state(run_dir)
        final_item = final_state["queue"][0]
        assert final_item["status"] == "executed"
        assert turn_count == 2
