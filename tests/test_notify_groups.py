"""Question groups in notification and chat channels (plan uqp95y, spec 6kwd2e R4, R10).

Drives the real notify functions against tmp_path run directories populated with
question_inbox.write_question, under the conftest AW_HOME sandbox, with no network
beyond loopback. Every assertion is on an output, a file written, or an HTTP body
received.
"""

from __future__ import annotations

import http.server
import json
import sys
import threading
from pathlib import Path
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
    register,
    registry,
)
from agent_workflows.notify.telegram import TelegramChannel
from tests.fake_telegram import run_fake_telegram

pytestmark = pytest.mark.core

CAPS = Caps(max_text=100000)


@pytest.fixture(autouse=True)
def _per_test_aw_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the user-level routing registry (and its seen-event ids) per test."""
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))


def _id6(n: int) -> str:
    return f"g{n:05d}"


def _records(count: int, text: str = "Which database?", options=None) -> list[dict]:
    opts = ["pg", "mysql"] if options is None else options
    return [
        {
            "question_id": f"{i + 1:02d}-{_id6(i)}-a1-q1",
            "artifact_id6": _id6(i),
            "text": text,
            "options": opts,
            "allow_free_text": True,
            "action": "execute",
        }
        for i in range(count)
    ]


def _park(
    repo: Path, run_dir: Path, position: int, id6: str, text: str, options=None
) -> str:
    plan = repo / f"20261017-qchan-{position:02d}-{id6}-test.ipd.md"
    plan.write_text(f"# Plan {id6}\n- Id: {id6}\n", encoding="utf-8")
    item = {
        "position": position,
        "id6": id6,
        "current_attempt": 1,
        "configured_file": str(plan),
        "artifact_path": str(plan),
        "repo": str(repo),
    }
    qid = f"{position:02d}-{id6}-a1-q1"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid,
            "text": text,
            "options": ["yes", "no"] if options is None else options,
            "allow_free_text": True,
        },
        attempt=1,
        repo=repo,
    )
    return qid


class _RecordingChannel:
    def __init__(self) -> None:
        self.batches: list[OutboundBatch] = []

    def capabilities(self) -> Caps:
        return CAPS

    def health(self) -> Health:
        return Health(ok=True)

    def send(self, batch: OutboundBatch) -> Receipt:
        self.batches.append(batch)
        return Receipt(ok=True, message_id=f"m{len(self.batches)}")


def _install_channel(monkeypatch: pytest.MonkeyPatch, mode: str = "full"):
    chan = _RecordingChannel()
    monkeypatch.setattr(
        "agent_workflows.notify.core.get_channel", lambda name, cfg: chan
    )
    monkeypatch.setattr(
        "agent_workflows.notify.config.effective_channels",
        lambda repo: {
            "webhook": {"enabled": True, "mode": mode, "url": "https://127.0.0.1/h"}
        },
    )
    return chan


def _sent_rows(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "notify" / "sent.jsonl"
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


# ---------------------------------------------------------------------------
# (1) build_batch rendering
# ---------------------------------------------------------------------------


def test_build_batch_group_terse_full_and_raiser_cap(tmp_path: Path) -> None:
    groups = question_inbox.group_questions(_records(74))
    assert len(groups) == 1
    group = groups[0]
    run_id = "run-g74"

    terse = build_batch(run_id, [group], mode="terse", caps=CAPS, repo=tmp_path)
    assert terse.message == (
        f"run {run_id}: 74 questions waiting; answer with aw runs answer {run_id}"
    )
    assert "Which database?" not in terse.message
    assert terse.question_count == 74
    assert len(terse.questions) == 1

    full = build_batch(run_id, [group], mode="full", caps=CAPS, repo=tmp_path)
    print(full.message)
    assert full.message.count("Which database?") == 1
    assert full.message.splitlines()[0] == (
        f"run {run_id}: 74 questions waiting; answer with aw runs answer {run_id}"
    )
    listed = ", ".join(_id6(i) for i in range(10))
    assert f"Asked by 74 artifact(s): {listed} and 64 more" in full.message
    assert f"Question: {group.group_id}" in full.message
    assert f"aw runs answer {run_id} --group {group.group_id}" in full.message
    entry = full.questions[0]
    assert entry.question_id == group.oq_id
    assert entry.group_id == group.group_id
    assert len(entry.member_qids) == 74
    assert entry.answer_command == f"aw runs answer {run_id} --group {group.group_id}"


def test_build_batch_ungrouped_rendering_unchanged(tmp_path: Path) -> None:
    q = OutboundQuestion(question_id="01-abc123-a1-q1", text="Approve?")
    full = build_batch("run-u", [q], mode="full", caps=CAPS, repo=tmp_path)
    assert full.message == (
        "run run-u: 1 question waiting; answer with aw runs answer run-u\n"
        "\n"
        "Question: 01-abc123-a1-q1\n"
        "Approve?\n"
        "aw runs answer run-u 01-abc123-a1-q1"
    )
    assert full.questions[0].answer_command == "aw runs answer run-u 01-abc123-a1-q1"
    assert full.questions[0].group_id is None
    terse = build_batch("run-u", [q], mode="terse", caps=CAPS, repo=tmp_path)
    assert terse.message == (
        "run run-u: 1 question waiting; answer with aw runs answer run-u"
    )


# ---------------------------------------------------------------------------
# (2) dispatch_checkpoint grouping and member tracking
# ---------------------------------------------------------------------------


def test_dispatch_checkpoint_groups_and_tracks_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chan = _install_channel(monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    for pos, id6 in ((1, "aaa001"), (2, "aaa002"), (3, "aaa003")):
        _park(tmp_path, run_dir, pos, id6, "Ship it?")
    state: dict[str, Any] = {"run_id": "run-grp", "repo": str(tmp_path)}

    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 1
    batch = chan.batches[0]
    assert len(batch.questions) == 1
    assert batch.question_count == 3
    gid = batch.questions[0].group_id
    assert gid
    assert f"aw runs answer run-grp --group {gid}" in batch.message
    rows = _sent_rows(run_dir)
    print(json.dumps(rows, indent=1))
    assert len(rows) == 3
    assert {r["group_id"] for r in rows} == {gid}
    assert {r["question_id"] for r in rows} == {
        "01-aaa001-a1-q1",
        "02-aaa002-a1-q1",
        "03-aaa003-a1-q1",
    }
    events = [
        json.loads(x)
        for x in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [e["count"] for e in events if e.get("event") == "notify-sent"] == [3]

    # Nothing new: nothing sent.
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 1

    # A fourth raiser of the same question re-notifies with all four.
    _park(tmp_path, run_dir, 4, "aaa004", "Ship it?")
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 2
    second = chan.batches[1]
    assert len(second.questions) == 1
    assert second.questions[0].raisers == ["aaa001", "aaa002", "aaa003", "aaa004"]
    assert "Asked by 4 artifact(s)" in second.message


def test_dispatch_checkpoint_notifies_question_outside_every_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chan = _install_channel(monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    q_parked = _park(tmp_path, run_dir, 1, "bbb001", "Parked question?")
    q_other = _park(tmp_path, run_dir, 2, "bbb002", "Preflight question?")
    # Only bbb001 is parked, so group_open_questions narrows to its question.
    state: dict[str, Any] = {
        "run_id": "run-unc",
        "repo": str(tmp_path),
        "queue": [
            {
                "id6": "bbb001",
                "position": 1,
                "status": "awaiting-human",
                "question_ids": [q_parked],
            },
            {"id6": "bbb002", "position": 2, "status": "queued"},
        ],
    }
    groups = question_inbox.group_open_questions(run_dir, state)
    assert [m.question_id for g in groups for m in g.members] == [q_parked]

    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 1
    batch = chan.batches[0]
    assert batch.question_count == 2
    assert f"aw runs answer run-unc {q_other}" in batch.message
    assert f"aw runs answer run-unc --group {groups[0].group_id}" in batch.message
    rows = {r["question_id"]: r for r in _sent_rows(run_dir)}
    assert "group_id" not in rows[q_other]
    assert rows[q_parked]["group_id"] == groups[0].group_id


# ---------------------------------------------------------------------------
# (3) one acknowledgement per answered group
# ---------------------------------------------------------------------------


def test_one_acknowledgement_per_answered_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chan = _install_channel(monkeypatch)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    qids = [
        _park(tmp_path, run_dir, pos, id6, "Ship it?")
        for pos, id6 in ((1, "ccc001"), (2, "ccc002"), (3, "ccc003"))
    ]
    state: dict[str, Any] = {"run_id": "run-ack", "repo": str(tmp_path)}
    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 1
    gid = chan.batches[0].questions[0].group_id
    rep = chan.batches[0].questions[0].question_id

    res = question_inbox.write_group_answer(
        run_dir,
        None,
        str(gid),
        choice=0,
        channel="terminal",
        sender="me",
        actor="human",
    )
    assert res.status == "recorded"
    for qid in qids:
        runner_shared.append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": runner_shared.utc_now(),
                "event": "answer-consumed",
                "question_id": qid,
                "channel": "terminal",
            },
        )

    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 2
    ack = chan.batches[1]
    print(ack.message)
    assert ack.message == (
        f"run run-ack ({rep}): answered via terminal (applied to 3 questions)"
    )
    assert [q.question_id for q in ack.questions] == [rep]
    ack_rows = [r for r in _sent_rows(run_dir) if r.get("type") == "ack"]
    print(json.dumps(ack_rows, indent=1))
    assert sorted(r["question_id"] for r in ack_rows) == sorted(qids)

    dispatch_checkpoint(run_dir, state, repo=tmp_path)
    assert len(chan.batches) == 2


# ---------------------------------------------------------------------------
# (4) apply_inbound group routing
# ---------------------------------------------------------------------------


class _VerifiedChannel:
    name = "telegram"

    def __init__(self) -> None:
        self.acked: list[tuple[str, str]] = []

    def verify(self, ev: InboundEvent) -> str | None:
        return "tg-user-1"

    def ack(self, ev: InboundEvent, outcome: str) -> None:
        self.acked.append((ev.event_id, outcome))


def test_apply_inbound_group_route_answers_all_members(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    qids = [
        _park(tmp_path, run_dir, pos, id6, "Ship it?")
        for pos, id6 in ((1, "ddd001"), (2, "ddd002"), (3, "ddd003"))
    ]
    group = question_inbox.group_open_questions(run_dir, None)[0]
    register(
        "telegram",
        "t:tok",
        run_dir,
        group.oq_id,
        option=1,
        group_id=group.group_id,
        member_qids=qids,
    )
    chan = _VerifiedChannel()
    outcome = apply_inbound(
        chan, InboundEvent(channel="telegram", event_id="e1", sender="x", key="t:tok")
    )
    assert outcome == "recorded"
    assert chan.acked == [("e1", "recorded")]
    for qid in qids:
        data = json.loads((run_dir / "answers" / f"{qid}.json").read_text("utf-8"))
        assert data["choice"] == 1
        assert sorted(a["question_id"] for a in data["applied_to"]) == sorted(qids)
    print((run_dir / "answers" / f"{qids[0]}.json").read_text("utf-8"))

    # The group is gone (all answered): fall back to write_answer, truthful 'already'.
    outcome2 = apply_inbound(
        chan, InboundEvent(channel="telegram", event_id="e2", sender="x", key="t:tok")
    )
    assert outcome2 == "already"


def test_apply_inbound_renumbered_split_answers_only_shown_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    fp = "deadbeefdeadbeef"
    monkeypatch.setattr(runner_shared, "question_fingerprint", lambda t, o=None: fp)
    q_c = _park(tmp_path, run_dir, 1, "eee001", "Use C?")
    q_b1 = _park(tmp_path, run_dir, 2, "eee002", "Use B?")
    q_b2 = _park(tmp_path, run_dir, 3, "eee003", "Use B?")
    before = {g.group_id: g for g in question_inbox.group_open_questions(run_dir, None)}
    b_group = before[f"g-{fp}-1"]
    assert b_group.text == "Use B?"
    register(
        "telegram",
        "t:b",
        run_dir,
        b_group.oq_id,
        option=0,
        group_id=b_group.group_id,
        member_qids=[m.question_id for m in b_group.members],
    )
    # A third variant parks and renumbers the split ids.
    q_a = _park(tmp_path, run_dir, 4, "eee004", "Use A?")
    after = {g.group_id: g for g in question_inbox.group_open_questions(run_dir, None)}
    assert after[f"g-{fp}-1"].text == "Use A?"

    outcome = apply_inbound(
        _VerifiedChannel(),
        InboundEvent(channel="telegram", event_id="e1", sender="x", key="t:b"),
    )
    assert outcome == "recorded"
    answered = sorted(p.stem for p in (run_dir / "answers").glob("*.json"))
    assert answered == sorted([q_b1, q_b2])
    assert q_a not in answered and q_c not in answered


def test_apply_inbound_route_without_group_unchanged(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    q1 = _park(tmp_path, run_dir, 1, "fff001", "Ship it?")
    q2 = _park(tmp_path, run_dir, 2, "fff002", "Ship it?")
    register("telegram", "t:single", run_dir, q1, option=0)
    outcome = apply_inbound(
        _VerifiedChannel(),
        InboundEvent(channel="telegram", event_id="e1", sender="x", key="t:single"),
    )
    assert outcome == "recorded"
    assert (run_dir / "answers" / f"{q1}.json").is_file()
    assert not (run_dir / "answers" / f"{q2}.json").exists()


# ---------------------------------------------------------------------------
# (5) aw.notify/v1 payload over loopback HTTP and the command hook
# ---------------------------------------------------------------------------


class _Server:
    def __init__(self) -> None:
        self.bodies: list[bytes] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                n = int(self.headers.get("Content-Length", 0))
                outer.bodies.append(self.rfile.read(n))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/hook"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def test_aw_webhook_and_command_payloads_carry_groups(tmp_path: Path) -> None:
    group = question_inbox.group_questions(_records(3))[0]
    full = build_batch("run-wh", [group], mode="full", caps=CAPS, repo=tmp_path)
    terse = build_batch("run-wh", [group], mode="terse", caps=CAPS, repo=tmp_path)
    srv = _Server()
    try:
        assert WebhookChannel({"url": srv.url, "format": "aw"}).send(full).ok
        assert WebhookChannel({"url": srv.url, "format": "aw"}).send(terse).ok
        assert WebhookChannel({"url": srv.url, "format": "text"}).send(full).ok
        assert WebhookChannel({"url": srv.url, "format": "ntfy"}).send(full).ok
    finally:
        srv.stop()
    p_full = json.loads(srv.bodies[0])
    p_terse = json.loads(srv.bodies[1])
    print(json.dumps(p_full, indent=1))
    print(json.dumps(p_terse, indent=1))
    assert p_full["count"] == 3
    assert p_full["distinct_count"] == 1
    assert len(p_full["questions"]) == 1
    entry = p_full["questions"][0]
    assert entry["group_id"] == group.group_id
    assert len(entry["member_qids"]) == 3
    assert entry["raisers"] == [_id6(0), _id6(1), _id6(2)]
    assert p_terse["count"] == 3
    assert p_terse["questions"] == []
    group_cmd = f"--group {group.group_id}"
    assert group_cmd in json.loads(srv.bodies[2])["text"]
    assert group_cmd in srv.bodies[3].decode("utf-8")

    out = tmp_path / "stdin.json"
    cmd = [
        sys.executable,
        "-c",
        "import sys, pathlib; pathlib.Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())",
        str(out),
    ]
    assert CommandChannel({"command": cmd, "mode": "full"}).send(full).ok
    p_cmd = json.loads(out.read_text(encoding="utf-8"))
    print(json.dumps(p_cmd, indent=1))
    assert p_cmd["count"] == 3
    assert p_cmd["distinct_count"] == 1
    assert p_cmd["questions"][0]["group_id"] == group.group_id

    # Ungrouped entries carry null group keys.
    q = OutboundQuestion(question_id="01-x-a1-q1", text="t")
    plain = build_batch("run-wh", [q], mode="full", caps=CAPS, repo=tmp_path)
    assert CommandChannel({"command": cmd, "mode": "full"}).send(plain).ok
    p_plain = json.loads(out.read_text(encoding="utf-8"))
    assert p_plain["questions"][0]["group_id"] is None
    assert p_plain["questions"][0]["member_qids"] == []
    assert p_plain["count"] == 1 and p_plain["distinct_count"] == 1


# ---------------------------------------------------------------------------
# (6) Telegram full mode against the fake Bot API
# ---------------------------------------------------------------------------


def test_telegram_full_mode_sends_one_message_per_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    qids = [
        _park(tmp_path, run_dir, pos, id6, "Ship it?")
        for pos, id6 in ((1, "hhh001"), (2, "hhh002"), (3, "hhh003"))
    ]
    group = question_inbox.group_open_questions(run_dir, None)[0]
    batch = build_batch("run-tg", [group], mode="full", caps=CAPS, repo=tmp_path)
    with run_fake_telegram() as server:
        monkeypatch.setenv("AW_NOTIFY_TELEGRAM_BASE_URL", server.base_url)
        channel = TelegramChannel(
            {"token": "123456:FAKE", "chat_id": "777", "user_id": "888"},
            run_dir=run_dir,
        )
        assert channel.send(batch).ok
        assert len(server.sent_messages) == 1
        msg = server.sent_messages[0]
        assert msg["text"].splitlines()[0] == (
            f"run run-tg ({group.group_id}, 3 artifacts):"
        )
        route = registry.lookup("telegram", str(msg["message_id"]))
        buttons = msg["reply_markup"]["inline_keyboard"][0]
        tok_routes = [registry.lookup("telegram", b["callback_data"]) for b in buttons]
        print(json.dumps([route, *tok_routes], indent=1))
        assert len(tok_routes) == 2
        for r in [route, *tok_routes]:
            assert r is not None
            assert r["question_id"] == group.oq_id
            assert r["group_id"] == group.group_id
            assert r["member_qids"] == qids

        upd = server.add_button_update(
            update_id=1,
            user_id="888",
            chat_id="777",
            message_id=int(msg["message_id"]),
            callback_data=buttons[0]["callback_data"],
        )
        ev = channel._translate_update(upd)
        assert ev is not None
        assert apply_inbound(channel, ev) == "recorded"
    answered = sorted(p.stem for p in (run_dir / "answers").glob("*.json"))
    assert answered == sorted(qids)
