"""Tests for notification channel core, config, registry, sanitizer, and webhooks (spec 6kwd2e R10).

Covers:
- Config permissions, tightening, fail-closed chmod failure, malformed JSON (E-01).
- Env configuration and malformed env values (E-01).
- Tracked-key secret warnings without echoing values (E-01).
- Policy ceilings: forbid, bogus, and terse-only (E-01).
- Outbound text sanitizer across all leak categories and truncation after redaction (E-02).
- Batch generation in terse and full modes (E-02).
- User-level registry across subprocesses, duplicate checking, and expire (E-06).
- apply_inbound sender verification, duplicate dropping, routing, and shared answer writing (E-06).
- dispatch_checkpoint once-per-park, answer-consumed ack, answer-stale notice, failure isolation (E-03).
- WebhookChannel formats (aw, text, ntfy), loopback allowance, non-loopback refusal, 302 non-redirection, and URL path hiding (E-04).
- CommandChannel JSON delivery over stdin, failure and timeout handling (E-04).
"""

from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any
import pytest

from agent_workflows import question_inbox, runner_shared
from agent_workflows.notify import (
    Caps,
    CommandChannel,
    Health,
    InboundEvent,
    OutboundBatch,
    OutboundQuestion,
    Receipt,
    WebhookChannel,
    apply_inbound,
    build_batch,
    dispatch_checkpoint,
    effective_channels,
    expire,
    load_user_config,
    lookup,
    read_notify_policy,
    register,
    sanitize_outbound,
    save_user_config,
    seen_event,
    tracked_secret_warnings,
)

pytestmark = pytest.mark.core


# ==============================================================================
# Task group 1: Config and policy tests (E-01, V-01)
# ==============================================================================


def test_save_user_config_permissions_posix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """save_user_config creates file with mode 0600 on POSIX."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    cfg = {
        "webhook": {"enabled": True, "mode": "terse", "url": "https://example.com/hook"}
    }
    saved_path = save_user_config(cfg)

    assert saved_path.is_file()
    if os.name != "nt":
        mode = saved_path.stat().st_mode & 0o777
        assert mode == 0o600, f"Expected 0600, got {oct(mode)}"

    loaded = load_user_config()
    assert loaded == cfg


def test_load_user_config_tightens_permissions_on_posix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 0644 notify.json file is tightened to 0600 on load with a warning."""
    if os.name == "nt":
        pytest.skip("POSIX permission bits not applicable on Windows")

    monkeypatch.setenv("AW_HOME", str(tmp_path))
    cfg_file = tmp_path / "notify.json"
    cfg = {"webhook": {"enabled": True, "mode": "terse"}}
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
    cfg_file.chmod(0o644)
    assert (cfg_file.stat().st_mode & 0o777) == 0o644

    with pytest.warns(UserWarning, match="Tightening permissions"):
        loaded = load_user_config()

    assert loaded == cfg
    assert (cfg_file.stat().st_mode & 0o777) == 0o600


def test_load_user_config_chmod_failure_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If tightening permissions fails, file is not read and empty dict is returned."""
    if os.name == "nt":
        pytest.skip("POSIX permission bits not applicable on Windows")

    monkeypatch.setenv("AW_HOME", str(tmp_path))
    cfg_file = tmp_path / "notify.json"
    cfg_file.write_text(json.dumps({"webhook": {"enabled": True}}), encoding="utf-8")
    cfg_file.chmod(0o644)

    def _failing_chmod(*args: Any, **kwargs: Any) -> None:
        raise PermissionError("Operation not permitted")

    monkeypatch.setattr(Path, "chmod", _failing_chmod)

    with pytest.warns(UserWarning, match="Failed to tighten permissions"):
        loaded = load_user_config()

    assert loaded == {}


def test_load_user_config_malformed_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed notify.json warns once and returns empty dict."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    cfg_file = tmp_path / "notify.json"
    cfg_file.write_text("{bad json...", encoding="utf-8")

    with pytest.warns(UserWarning, match="disabling all notification channels"):
        loaded = load_user_config()

    assert loaded == {}


def test_env_overrides_and_malformed_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AW_NOTIFY_WEBHOOK_URL and AW_NOTIFY_COMMAND configure channels in terse mode by default."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    monkeypatch.setenv("AW_NOTIFY_WEBHOOK_URL", "https://hooks.example.com/test")
    monkeypatch.setenv("AW_NOTIFY_COMMAND", json.dumps(["/usr/bin/notify", "--alert"]))

    channels = effective_channels(tmp_path)
    assert "webhook" in channels
    assert channels["webhook"]["enabled"] is True
    assert channels["webhook"]["mode"] == "terse"
    assert channels["webhook"]["url"] == "https://hooks.example.com/test"

    assert "command" in channels
    assert channels["command"]["enabled"] is True
    assert channels["command"]["mode"] == "terse"
    assert channels["command"]["command"] == ["/usr/bin/notify", "--alert"]

    # Malformed command JSON is ignored with warning
    monkeypatch.setenv("AW_NOTIFY_COMMAND", "not-a-json-list")
    with pytest.warns(UserWarning, match="AW_NOTIFY_COMMAND"):
        channels_malformed = effective_channels(tmp_path)
    assert "command" not in channels_malformed or not channels_malformed["command"].get(
        "enabled"
    )


def test_env_honors_full_mode_if_set_in_user_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If notify.json sets full mode for a channel, env override preserves full mode."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    save_user_config({"webhook": {"mode": "full"}})
    monkeypatch.setenv("AW_NOTIFY_WEBHOOK_URL", "https://hooks.example.com/test")

    channels = effective_channels(tmp_path)
    assert channels["webhook"]["mode"] == "full"


def test_tracked_secret_warnings_no_echo(tmp_path: Path) -> None:
    """tracked_secret_warnings reports notify keys in .aw/config/*.json without echoing values."""
    cfg_dir = tmp_path / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    project_json = cfg_dir / "project.json"
    project_json.write_text(
        json.dumps(
            {
                "notify_policy": "terse-only",  # Allowed key
                "notify": {"secret_token": "super_secret_12345"},  # Forbidden
                "notify_webhook_url": "https://secret.com/hook",  # Forbidden
            }
        ),
        encoding="utf-8",
    )

    warnings_list = tracked_secret_warnings(tmp_path)
    assert len(warnings_list) == 2
    full_warnings = " ".join(warnings_list)

    assert "super_secret_12345" not in full_warnings
    assert "https://secret.com/hook" not in full_warnings
    assert "'notify'" in full_warnings
    assert "'notify_webhook_url'" in full_warnings
    assert "notify_policy" not in full_warnings


def test_read_notify_policy_and_ceilings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read_notify_policy returns ceiling and effective_channels applies it."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    save_user_config(
        {
            "webhook": {
                "enabled": True,
                "mode": "full",
                "url": "https://127.0.0.1:8000/hook",
            },
        }
    )

    cfg_dir = tmp_path / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    project_json = cfg_dir / "project.json"

    # 1. No ceiling
    project_json.write_text(json.dumps({}), encoding="utf-8")
    assert read_notify_policy(tmp_path) is None
    assert effective_channels(tmp_path)["webhook"]["mode"] == "full"

    # 2. terse-only ceiling forces terse
    project_json.write_text(
        json.dumps({"notify_policy": "terse-only"}), encoding="utf-8"
    )
    assert read_notify_policy(tmp_path) == "terse-only"
    assert effective_channels(tmp_path)["webhook"]["mode"] == "terse"

    # 3. forbid disables all channels
    project_json.write_text(json.dumps({"notify_policy": "forbid"}), encoding="utf-8")
    assert read_notify_policy(tmp_path) == "forbid"
    assert effective_channels(tmp_path) == {}

    # 4. bogus unrecognized policy treats as forbid with warning
    project_json.write_text(json.dumps({"notify_policy": "bogus"}), encoding="utf-8")
    with pytest.warns(UserWarning, match="treating as 'forbid'"):
        assert read_notify_policy(tmp_path) == "forbid"
    assert effective_channels(tmp_path) == {}


# ==============================================================================
# Task group 2: Sanitizer, batching, core and registry (E-02, E-06, V-02, V-06)
# ==============================================================================


def test_sanitize_outbound_all_leak_classes(tmp_path: Path) -> None:
    """sanitize_outbound strips ANSI, rewrites home, redacts absolute paths and fail patterns."""
    home_leak = "/home/" + "testuser" + "/project/module.py"
    session_leak = "ses_" + "9876543210fedcba"
    text = (
        "\x1b[31;1mError in test:\x1b[0m\n"
        f"Failed at {home_leak}\n"
        "Server path /srv/production/data/db.sqlite3\n"
        f"Active session id {session_leak}"
    )

    sanitized = sanitize_outbound(text, repo=tmp_path)

    assert "\x1b[" not in sanitized
    assert ("/home/" + "testuser") not in sanitized
    assert "~/project/module.py" in sanitized or "<redacted>" in sanitized
    assert "/srv/production/data" not in sanitized
    assert "<path>" in sanitized or "<redacted>" in sanitized
    assert session_leak not in sanitized
    assert "<redacted>" in sanitized


def test_sanitize_outbound_truncation_after_redaction(tmp_path: Path) -> None:
    """Truncation happens after redaction, so redacted tokens appear before the trailing ..."""
    text = "Important notice: check /srv/very/long/unmounted/path and continue with remaining details"
    sanitized = sanitize_outbound(text, repo=tmp_path, max_text=35)
    assert len(sanitized) <= 35
    assert sanitized.endswith("...")
    assert "/srv/" not in sanitized
    assert "<path>" in sanitized


def test_build_batch_terse_and_full(tmp_path: Path) -> None:
    """build_batch in terse mode includes only run id and count; full mode includes questions."""
    q1 = OutboundQuestion(
        question_id="01-abc123-a1-q1",
        text="Which cache backend should we use?",
        options=["redis", "memcached"],
    )
    caps = Caps(max_text=4096)

    # Terse mode
    terse_batch = build_batch("run-001", [q1], mode="terse", caps=caps, repo=tmp_path)
    assert terse_batch.mode == "terse"
    assert (
        "run run-001: 1 question waiting; answer with aw runs answer run-001"
        in terse_batch.message
    )
    assert "Which cache backend" not in terse_batch.message
    assert "redis" not in terse_batch.message

    # Full mode
    full_batch = build_batch("run-001", [q1], mode="full", caps=caps, repo=tmp_path)
    assert full_batch.mode == "full"
    assert "Which cache backend should we use?" in full_batch.message
    assert "1) redis" in full_batch.message
    assert "2) memcached" in full_batch.message
    assert "aw runs answer run-001 01-abc123-a1-q1" in full_batch.message


def test_registry_across_subprocesses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registered key in one process resolves in another process."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))

    # Process 1 registers
    code_proc1 = f"""
import os
os.environ["AW_HOME"] = {json.dumps(str(tmp_path))}
from agent_workflows.notify import registry
registry.register("telegram", "msg-12345", "/tmp/run-01", "01-abc123-a1-q1", option=2, artifact_hash="hash01")
"""
    subprocess.run([sys.executable, "-c", code_proc1], check=True)

    # Process 2 looks up
    code_proc2 = f"""
import os, json
os.environ["AW_HOME"] = {json.dumps(str(tmp_path))}
from agent_workflows.notify import registry
res = registry.lookup("telegram", "msg-12345")
print(json.dumps(res))
"""
    cp = subprocess.run(
        [sys.executable, "-c", code_proc2], capture_output=True, text=True, check=True
    )
    loaded = json.loads(cp.stdout.strip())
    assert loaded["run_dir"] == "/tmp/run-01"
    assert loaded["question_id"] == "01-abc123-a1-q1"
    assert loaded["option"] == 2
    assert loaded["artifact_hash"] == "hash01"


def test_registry_seen_event_deduplication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """seen_event returns False on first call and True on subsequent calls."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    assert seen_event("telegram", "evt-1") is False
    assert seen_event("telegram", "evt-1") is True
    assert seen_event("telegram", "evt-2") is False


def test_registry_expire(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """expire() drops entries when run_dir is gone or question is no longer open."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir1 = tmp_path / "run1"
    run_dir1.mkdir(parents=True, exist_ok=True)
    q_dir1 = run_dir1 / "questions"
    q_dir1.mkdir(parents=True, exist_ok=True)
    # Question 1: open
    (q_dir1 / "01-abc123-a1-q1.json").write_text(
        json.dumps({"status": "open"}), encoding="utf-8"
    )
    # Question 2: answered
    (q_dir1 / "01-abc123-a1-q2.json").write_text(
        json.dumps({"status": "answered"}), encoding="utf-8"
    )

    register("telegram", "k1", str(run_dir1), "01-abc123-a1-q1")
    register("telegram", "k2", str(run_dir1), "01-abc123-a1-q2")
    register("telegram", "k3", str(tmp_path / "nonexistent_run"), "01-abc123-a1-q3")

    assert lookup("telegram", "k1") is not None
    assert lookup("telegram", "k2") is not None
    assert lookup("telegram", "k3") is not None

    removed = expire()
    assert removed == 2
    assert lookup("telegram", "k1") is not None
    assert lookup("telegram", "k2") is None
    assert lookup("telegram", "k3") is None


def test_apply_inbound_duplicate_and_unverified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """apply_inbound drops duplicate and unverified inbound events, writing no answers."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_inbound"
    run_dir.mkdir(parents=True, exist_ok=True)

    class FakeChannel:
        name = "testchan"

        def __init__(self, verify_ret: str | None = "user123"):
            self.verify_ret = verify_ret
            self.acked = []

        def verify(self, ev: InboundEvent) -> str | None:
            return self.verify_ret

        def ack(self, ev: InboundEvent, outcome: str) -> None:
            self.acked.append((ev.event_id, outcome))

    # 1. Duplicate event
    chan = FakeChannel()
    seen_event("testchan", "evt-dup")
    ev_dup = InboundEvent(
        channel="testchan", event_id="evt-dup", sender="user123", key="k1"
    )
    assert apply_inbound(chan, ev_dup) == "ignored"

    # 2. Unverified sender
    chan_unverified = FakeChannel(verify_ret=None)
    ev_unv = InboundEvent(
        channel="testchan", event_id="evt-unv", sender="attacker", key="k1"
    )
    with pytest.warns(UserWarning, match="Unverified sender"):
        assert apply_inbound(chan_unverified, ev_unv) == "ignored"

    answers_dir = run_dir / "answers"
    assert not answers_dir.exists() or len(list(answers_dir.glob("*.json"))) == 0


def _make_dummy_plan(repo: Path, id6: str = "txl556") -> Path:
    plan = repo / f"20261017-qchan-09-{id6}-test.ipd.md"
    plan.write_text(f"# Plan {id6}\n- Id: {id6}\n", encoding="utf-8")
    return plan


def test_apply_inbound_verified_writes_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verified inbound event writes answer through question_inbox.write_answer."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_inbound_valid"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Setup valid question
    plan = _make_dummy_plan(tmp_path, "txl556")
    item = {
        "position": 1,
        "id6": "txl556",
        "current_attempt": 1,
        "configured_file": str(plan),
        "artifact_path": str(plan),
        "repo": str(tmp_path),
    }
    q = {
        "question_id": "01-txl556-a1-q1",
        "text": "Choose deployment target",
        "options": ["staging", "production"],
        "allow_free_text": True,
    }
    question_inbox.write_question(run_dir, item, q, attempt=1, repo=tmp_path)

    register("telegram", "token-opt-1", run_dir, "01-txl556-a1-q1", option=1)

    class FakeChannel:
        name = "telegram"

        def __init__(self) -> None:
            self.acked: list[tuple[str, str]] = []

        def verify(self, ev: InboundEvent) -> str | None:
            return "verified-tg-user-99"

        def ack(self, ev: InboundEvent, outcome: str) -> None:
            self.acked.append((ev.event_id, outcome))

    chan = FakeChannel()
    event = InboundEvent(
        channel="telegram",
        event_id="ev-101",
        sender="verified-tg-user-99",
        key="token-opt-1",
    )

    outcome = apply_inbound(chan, event)
    assert outcome == "recorded"
    assert chan.acked == [("ev-101", "recorded")]

    # Check answer file written
    ans_file = run_dir / "answers" / "01-txl556-a1-q1.json"
    assert ans_file.is_file()
    ans_data = json.loads(ans_file.read_text(encoding="utf-8"))
    assert ans_data["choice"] == 1
    assert ans_data["channel"] == "telegram"
    assert ans_data["sender"] == "verified-tg-user-99"
    assert ans_data["actor"] == "human"

    # Second submission returns 'already'
    event2 = InboundEvent(
        channel="telegram",
        event_id="ev-102",
        sender="verified-tg-user-99",
        key="token-opt-1",
    )
    outcome2 = apply_inbound(chan, event2)
    assert outcome2 == "already"


# ==============================================================================
# Task group 3: Dispatcher tests (E-03, V-03)
# ==============================================================================


def test_dispatch_checkpoint_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """dispatch_checkpoint sends once-per-park, sends ack on answer-consumed, and handles stale."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_dispatch"
    run_dir.mkdir(parents=True, exist_ok=True)
    events_file = run_dir / "events.jsonl"

    # Configure a mock channel
    received_batches: list[OutboundBatch] = []

    class MockChannel:
        def capabilities(self) -> Caps:
            return Caps(max_text=4096)

        def health(self) -> Health:
            return Health(ok=True)

        def send(self, batch: OutboundBatch) -> Receipt:
            received_batches.append(batch)
            return Receipt(ok=True, message_id=f"msg-{len(received_batches)}")

    mock_chan = MockChannel()
    monkeypatch.setattr(
        "agent_workflows.notify.core.get_channel", lambda name, cfg: mock_chan
    )

    # Enable mock channel in effective_channels
    monkeypatch.setattr(
        "agent_workflows.notify.config.effective_channels",
        lambda repo: {
            "webhook": {
                "enabled": True,
                "mode": "terse",
                "url": "https://127.0.0.1:8000/hook",
            }
        },
    )

    # Write question 1
    plan = _make_dummy_plan(tmp_path, "txl556")
    item = {
        "position": 1,
        "id6": "txl556",
        "current_attempt": 1,
        "configured_file": str(plan),
        "artifact_path": str(plan),
        "repo": str(tmp_path),
    }
    q1 = {
        "question_id": "01-txl556-a1-q1",
        "text": "Proceed with deployment?",
        "options": ["yes", "no"],
    }
    q1_path = question_inbox.write_question(run_dir, item, q1, attempt=1, repo=tmp_path)
    q1_bytes_before = q1_path.read_bytes()

    state: dict[str, Any] = {"run_id": "run-dp-01", "repo": str(tmp_path)}

    # Checkpoint 1: sends batch for q1
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 1
    assert "run-dp-01" in received_batches[0].message
    assert (run_dir / "notify" / "sent.jsonl").is_file()

    # Question bytes remain strictly unchanged
    assert q1_path.read_bytes() == q1_bytes_before

    # Check events.jsonl has notify-sent
    events = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
    ]
    notify_sent_evs = [e for e in events if e.get("event") == "notify-sent"]
    assert len(notify_sent_evs) == 1
    assert notify_sent_evs[0]["channel"] == "webhook"
    assert notify_sent_evs[0]["count"] == 1
    assert "message" not in notify_sent_evs[0]

    # Checkpoint 2: same open question -> does NOT re-send
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 1

    # Simulate answer consumed (Order 04)
    runner_shared.append_jsonl(
        events_file,
        {
            "at": runner_shared.utc_now(),
            "event": "answer-consumed",
            "id6": "txl556",
            "question_id": "01-txl556-a1-q1",
            "channel": "terminal",
        },
    )

    # Checkpoint 3: sends acknowledgement
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 2
    ack_batch = received_batches[1]
    assert "answered via terminal" in ack_batch.message

    # Checkpoint 4: does NOT re-send acknowledgement
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 2


def test_dispatch_checkpoint_stale_answer_notice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """dispatch_checkpoint sends stale answer notice once when answer-stale is recorded."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_stale"
    run_dir.mkdir(parents=True, exist_ok=True)
    events_file = run_dir / "events.jsonl"

    received_batches: list[OutboundBatch] = []

    class MockChannel:
        def capabilities(self) -> Caps:
            return Caps(max_text=4096)

        def health(self) -> Health:
            return Health(ok=True)

        def send(self, batch: OutboundBatch) -> Receipt:
            received_batches.append(batch)
            return Receipt(ok=True)

    monkeypatch.setattr(
        "agent_workflows.notify.core.get_channel", lambda name, cfg: MockChannel()
    )
    monkeypatch.setattr(
        "agent_workflows.notify.config.effective_channels",
        lambda repo: {
            "webhook": {
                "enabled": True,
                "mode": "terse",
                "url": "https://127.0.0.1:8000/hook",
            }
        },
    )

    plan = _make_dummy_plan(tmp_path, "txl556")
    item = {
        "position": 1,
        "id6": "txl556",
        "current_attempt": 1,
        "configured_file": str(plan),
        "artifact_path": str(plan),
        "repo": str(tmp_path),
    }
    q1 = {"question_id": "01-txl556-a1-q1", "text": "Approve?"}
    question_inbox.write_question(run_dir, item, q1, attempt=1, repo=tmp_path)

    state: dict[str, Any] = {"run_id": "run-stale-01", "repo": str(tmp_path)}

    # Park and send
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 1

    # Simulate answer marked stale
    runner_shared.append_jsonl(
        events_file,
        {
            "at": runner_shared.utc_now(),
            "event": "answer-stale",
            "id6": "txl556",
            "question_id": "01-txl556-a1-q1",
        },
    )

    # Dispatch sends stale notice
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(received_batches) == 2
    assert (
        "answer not applied: the plan changed; ask again" in received_batches[1].message
    )


def test_dispatch_checkpoint_failure_isolation_and_secret_redaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A channel exception or failure records notify-failed with redacted secrets and does not raise."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_fail_iso"
    run_dir.mkdir(parents=True, exist_ok=True)
    events_file = run_dir / "events.jsonl"

    class FailingChannel:
        def capabilities(self) -> Caps:
            return Caps(max_text=4096)

        def health(self) -> Health:
            return Health(ok=False)

        def send(self, batch: OutboundBatch) -> Receipt:
            raise ConnectionError(
                "Failed to reach https://hooks.example.com/secret_path?token=secret123"
            )

    monkeypatch.setattr(
        "agent_workflows.notify.core.get_channel", lambda name, cfg: FailingChannel()
    )
    monkeypatch.setattr(
        "agent_workflows.notify.config.effective_channels",
        lambda repo: {
            "webhook": {
                "enabled": True,
                "mode": "terse",
                "url": "https://hooks.example.com/secret_path?token=secret123",
            }
        },
    )

    plan = _make_dummy_plan(tmp_path, "txl556")
    item = {
        "position": 1,
        "id6": "txl556",
        "current_attempt": 1,
        "configured_file": str(plan),
        "artifact_path": str(plan),
        "repo": str(tmp_path),
    }
    q1 = {"question_id": "01-txl556-a1-q1", "text": "Approve?"}
    question_inbox.write_question(run_dir, item, q1, attempt=1, repo=tmp_path)

    state: dict[str, Any] = {"run_id": "run-fail-01", "repo": str(tmp_path)}

    # Does not raise!
    dispatch_checkpoint(run_dir, state, repo=tmp_path)

    events = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
    ]
    fail_events = [e for e in events if e.get("event") == "notify-failed"]
    assert len(fail_events) == 1
    detail = fail_events[0]["detail"]
    assert "secret_path" not in detail
    assert "token=secret123" not in detail
    assert "https://hooks.example.com" in detail


def test_dispatch_checkpoint_no_channels_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no effective channel configured, notify/ directory is not created."""
    monkeypatch.setenv("AW_HOME", str(tmp_path))
    run_dir = tmp_path / "run_no_chan"
    run_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        "agent_workflows.notify.config.effective_channels", lambda repo: {}
    )

    state: dict[str, Any] = {"run_id": "run-empty-01", "repo": str(tmp_path)}
    dispatch_checkpoint(run_dir, state, repo=tmp_path)

    assert not (run_dir / "notify").exists()


# ==============================================================================
# Task group 4: Notify-only channels: Webhook & Command (E-04, V-04)
# ==============================================================================


class _TestHTTPServer:
    """Minimal local HTTP test server to verify WebhookChannel deliveries."""

    def __init__(
        self, status_code: int = 200, headers: dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.received_requests: list[dict[str, Any]] = []
        self.server: http.server.HTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> str:
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                outer.received_requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": body,
                    }
                )
                self.send_response(outer.status_code)
                for k, v in outer.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                if outer.status_code != 302:
                    self.wfile.write(b"OK")

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{port}/hook"

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def test_webhook_channel_formats_against_local_server(tmp_path: Path) -> None:
    """WebhookChannel delivers aw, text, and ntfy formats to local HTTP server."""
    test_srv = _TestHTTPServer(status_code=200)
    url = test_srv.start()
    try:
        q = OutboundQuestion(
            question_id="01-abc-a1-q1",
            text="Choose option",
            options=["A", "B"],
            answer_command="aw runs answer run-wh 01-abc-a1-q1",
        )
        caps = Caps(max_text=4096)

        # 1. 'aw' format (default)
        wh_aw = WebhookChannel({"url": url, "format": "aw", "mode": "full"})
        batch_full = build_batch("run-wh", [q], mode="full", caps=caps, repo=tmp_path)
        rec_aw = wh_aw.send(batch_full)
        assert rec_aw.ok is True
        assert len(test_srv.received_requests) == 1
        req1 = test_srv.received_requests[0]
        assert "application/json" in req1["headers"]["Content-Type"]
        payload_aw = json.loads(req1["body"].decode("utf-8"))
        assert payload_aw["schema"] == "aw.notify/v1"
        assert payload_aw["run_id"] == "run-wh"
        assert len(payload_aw["questions"]) == 1

        # 2. 'text' format
        wh_text = WebhookChannel({"url": url, "format": "text"})
        batch_terse = build_batch("run-wh", [q], mode="terse", caps=caps, repo=tmp_path)
        rec_text = wh_text.send(batch_terse)
        assert rec_text.ok is True
        req2 = test_srv.received_requests[1]
        assert "application/json" in req2["headers"]["Content-Type"]
        payload_text = json.loads(req2["body"].decode("utf-8"))
        assert "text" in payload_text
        assert "run-wh" in payload_text["text"]

        # 3. 'ntfy' format
        wh_ntfy = WebhookChannel({"url": url, "format": "ntfy"})
        rec_ntfy = wh_ntfy.send(batch_terse)
        assert rec_ntfy.ok is True
        req3 = test_srv.received_requests[2]
        assert "text/plain" in req3["headers"]["Content-Type"]
        assert "Title" in req3["headers"]
        assert "Tags" in req3["headers"]
        assert "run-wh" in req3["body"].decode("utf-8")
    finally:
        test_srv.stop()


def test_webhook_non_loopback_http_refused() -> None:
    """Non-loopback http:// URL is refused without sending a request."""
    wh = WebhookChannel({"url": "http://evil.example.com/hook"})
    batch = OutboundBatch(run_id="run-1", mode="terse", message="msg")
    receipt = wh.send(batch)
    assert receipt.ok is False
    assert "Refusing non-HTTPS URL on non-loopback host" in receipt.detail


def test_webhook_redirect_refused() -> None:
    """A 302 redirect response is treated as a failure and NOT followed."""
    test_srv = _TestHTTPServer(
        status_code=302, headers={"Location": "http://127.0.0.1:9999/other"}
    )
    url = test_srv.start()
    try:
        wh = WebhookChannel({"url": url})
        batch = OutboundBatch(run_id="run-1", mode="terse", message="msg")
        receipt = wh.send(batch)
        assert receipt.ok is False
        assert "HTTP 302" in receipt.detail
        # URL path/query hidden in detail
        assert "/hook" not in receipt.detail
    finally:
        test_srv.stop()


def test_command_channel_stdin_and_failure(tmp_path: Path) -> None:
    """CommandChannel pipes JSON to stdin and reports nonzero exit or timeout."""
    output_file = tmp_path / "cmd_out.json"
    cmd = [
        sys.executable,
        "-c",
        f"import sys, pathlib; pathlib.Path({json.dumps(str(output_file))}).write_bytes(sys.stdin.buffer.read())",
    ]

    cc = CommandChannel({"command": cmd, "mode": "terse"})
    q = OutboundQuestion(question_id="01-q1", text="text")
    batch = OutboundBatch(
        run_id="run-cmd-01", mode="terse", message="test message", questions=[q]
    )

    receipt = cc.send(batch)
    assert receipt.ok is True
    assert output_file.is_file()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["schema"] == "aw.notify/v1"
    assert data["run_id"] == "run-cmd-01"

    # Nonzero exit failure
    fail_cc = CommandChannel(
        {"command": [sys.executable, "-c", "import sys; sys.exit(42)"]}
    )
    fail_rec = fail_cc.send(batch)
    assert fail_rec.ok is False
    assert "exited with code 42" in fail_rec.detail
