# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for per-run question and answer inbox (spec 6kwd2e R9.1, R9.2, R4a.1, R5.4, R5.6, A11, A42).

Validates:
1. Schema round-trip: questions/<qid>.json written with schema aw.question/v1, captured artifact hash,
   and read back via read_open_questions.
2. No-overwrite and qid validation: second write_question raises FileExistsError (O_EXCL), invalid
   qid or path traversal is refused with ValueError.
3. Concurrent first-answer-wins: two threads and two subprocesses answering the same question yield
   exactly one 'recorded' and one 'already'.
4. Refusal reasons: malformed qid, unknown qid, non-human actor (matching RL-E051), choice outside
   options, free text when not allowed, over-length answer/channel/sender, control characters, and
   answering a stale question.
5. Status transitions: open -> answered and open -> stale succeed; answered -> open is refused and
   leaves file untouched; question-status events are logged.
6. Projection refresh: open-questions.md written at park time and updated after write_answer.
7. Event ledger: events.jsonl contains human_answer and question_disposition for recorded answers.
8. Park wiring in runner: scripted execute and review park branches write questions/<qid>.json,
   populate item['question_ids'], and write open-questions.md.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    oc_runipd,
    question_inbox,
    run_ledger_schema,
    runner_shared,
    set_records,
)
from tests.support import coordinator_role


def _create_test_repo(root: Path) -> Path:
    """Initialize a git repo with required .aw structure and commit."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/runs/\n.aw/records/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
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
    setid: str = "qtest",
    order: int = 1,
    status: str = "approved",
    action: str = "execute",
    priority: str = "medium",
    work_kind: str = "feature",
) -> Path:
    """Create a conforming plan file under .aw/records/plans/pending/."""
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"20261017-{setid}-{order:02d}-{id6}-plan.ipd.md"

    content = f"""# IPD: Test Plan {id6}

- Kind: child
- Status: {status}
- Set: {setid}
- Order: {order}
- Id: {id6}
- Priority: {priority}
- Work-Kind: {work_kind}

## Goal

Test plan {id6}.
"""
    plan_path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


def _make_fake_agent_script(root: Path) -> Path:
    """Create a fake agent CLI script that simulates an agent turn."""
    script_path = root / "fake_agent.py"
    script_content = """#!/usr/bin/env python3
import json, os, re, subprocess, sys
from pathlib import Path

# Stream initialization events
print(json.dumps({"event": "init", "conversation_id": "ses-1", "init": {"model": "test-model"}}), flush=True)
print(json.dumps({"type": "text", "sessionID": "ses-1", "part": {"text": "working"}}), flush=True)

all_text = ""
for arg in sys.argv[1:]:
    if "Required JSON outcome:" in arg:
        all_text = arg
        break
    if Path(arg).is_file():
        try:
            content = Path(arg).read_text(encoding="utf-8")
            if "Required JSON outcome:" in content:
                all_text = content
                break
        except Exception:
            pass

m_pos = re.search(r"Queue position: (\\d+)", all_text)
m_id6 = re.search(r"Assigned IPD: (\\w+)", all_text)
pos = int(m_pos.group(1)) if m_pos else 1
id6 = m_id6.group(1) if m_id6 else "unknown"

m_req = re.search(r"Required JSON outcome:\\s+(\\S+)", all_text)
if m_req:
    outcome_file_path = m_req.group(1)
    m_pair = re.search(r"(\\d+)-([a-zA-Z0-9]{6})", outcome_file_path)
    if m_pair and (not m_id6 or id6 == "unknown"):
        pos = int(m_pair.group(1))
        id6 = m_pair.group(2)

payload_map = {}
raw_map = os.environ.get("FAKE_PAYLOAD_MAP_JSON")
if raw_map:
    try:
        payload_map = json.loads(raw_map)
    except Exception:
        pass

item_cfg = payload_map.get(id6)
if item_cfg is not None:
    if isinstance(item_cfg, dict) and "outcome" in item_cfg:
        payload_content = json.dumps(item_cfg["outcome"])
        if item_cfg.get("commit") and id6 != "unknown":
            f = Path(f"work_{id6}.txt")
            f.write_text(f"work: {item_cfg['commit']}\\n", encoding="utf-8")
            subprocess.run(["git", "add", str(f)], check=True)
            subprocess.run(["git", "commit", "-qm", str(item_cfg["commit"])], check=True)
    else:
        payload_content = json.dumps(item_cfg)
else:
    payload_content = os.environ.get(
        "FAKE_PAYLOAD_JSON",
        json.dumps({"disposition": "executed", "defect_report": {"state": "none-found", "findings": []}, "pushed": False})
    )

if m_req:
    p = Path(m_req.group(1))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(payload_content, encoding="utf-8")
"""
    script_path.write_text(script_content, encoding="utf-8")
    script_path.chmod(0o755)
    if sys.platform == "win32":
        cmd_path = root / "fake_agent.cmd"
        cmd_path.write_text(
            f'@"{sys.executable}" "{script_path}" %*\n', encoding="utf-8"
        )
        return cmd_path
    return script_path


def test_question_schema_roundtrip_and_hash(tmp_path: Path) -> None:
    """E-01 / V-01: Question file schema round-trip, artifact hash capture, and read_open_questions."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb001", setid="qinb", order=1)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000001"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 1,
        "id6": "inb001",
        "action": "execute",
        "configured_file": str(plan),
        "repo": str(repo),
        "run_id": "run-20261017T220000Z-000001",
    }
    question: dict[str, Any] = {
        "question_id": "q-cache-backend",
        "text": "Which cache backend should we use?",
        "options": ["Redis", "Memcached"],
        "allow_free_text": True,
        "gates_verdict": True,
        "evidence": ["plan.ipd.md", "settings.py"],
    }

    q_path = question_inbox.write_question(
        run_dir, item, question, attempt=1, repo=repo
    )
    assert q_path.is_file()
    assert q_path.name == "01-inb001-a1-q-cache-backend.json"

    # Verify sha256 artifact hash matches main checkout at park time
    expected_hash = hashlib.sha256(plan.read_bytes()).hexdigest()
    raw_data = json.loads(q_path.read_text(encoding="utf-8"))
    assert raw_data["schema"] == "aw.question/v1"
    assert raw_data["question_id"] == "01-inb001-a1-q-cache-backend"
    assert raw_data["run_id"] == "run-20261017T220000Z-000001"
    assert raw_data["artifact_id6"] == "inb001"
    assert raw_data["artifact_path"] == str(plan.relative_to(repo).as_posix())
    assert raw_data["artifact_hash"] == expected_hash
    assert raw_data["gates_verdict"] is True
    assert raw_data["text"] == "Which cache backend should we use?"
    assert raw_data["options"] == ["Redis", "Memcached"]
    assert raw_data["allow_free_text"] is True
    assert raw_data["evidence"] == ["plan.ipd.md", "settings.py"]
    assert raw_data["action"] == "execute"
    assert raw_data["status"] == "open"
    assert "created_at" in raw_data

    # Read back via read_open_questions
    open_qs = question_inbox.read_open_questions(run_dir)
    assert len(open_qs) == 1
    assert open_qs[0]["question_id"] == "01-inb001-a1-q-cache-backend"
    assert open_qs[0]["artifact_hash"] == expected_hash

    # Single item read
    single_q = question_inbox.read_question(run_dir, "01-inb001-a1-q-cache-backend")
    assert single_q is not None
    assert single_q["text"] == "Which cache backend should we use?"


def test_question_no_overwrite_and_qid_validation(tmp_path: Path) -> None:
    """E-01 / V-01: Refuse overwrite (O_EXCL), refuse invalid qid or path traversal."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb002", setid="qinb", order=2)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000002"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 2,
        "id6": "inb002",
        "action": "execute",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Initial question",
        "gates_verdict": True,
    }

    p1 = question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    assert p1.is_file()

    # Second write for identical qid must raise FileExistsError and leave file unchanged
    q_diff: dict[str, Any] = {
        "question_id": "q1",
        "text": "Overwriting question text attempt",
        "gates_verdict": True,
    }
    with pytest.raises(FileExistsError):
        question_inbox.write_question(run_dir, item, q_diff, attempt=1, repo=repo)

    # Content unchanged
    assert (
        question_inbox.read_question(run_dir, "02-inb002-a1-q1")["text"]
        == "Initial question"
    )

    # Path traversal ../x or invalid characters
    q_traversal: dict[str, Any] = {
        "question_id": "../x",
        "text": "Escape",
        "gates_verdict": True,
    }
    with pytest.raises(ValueError, match="Invalid question_id"):
        question_inbox.write_question(run_dir, item, q_traversal, attempt=1, repo=repo)

    with pytest.raises(ValueError, match="Invalid question_id"):
        question_inbox.resolve_question_path(run_dir, "../x")


def test_concurrent_answers_threads(tmp_path: Path) -> None:
    """E-02 / A42 / V-02: Two concurrent threads answering same qid yield exactly one recorded and one already."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb003", setid="qinb", order=3)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000003"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 3,
        "id6": "inb003",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Choice?",
        "options": ["A", "B"],
        "gates_verdict": True,
    }
    question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    qid = "03-inb003-a1-q1"

    results: list[question_inbox.AnswerResult] = []

    def _worker(worker_id: int) -> question_inbox.AnswerResult:
        return question_inbox.write_answer(
            run_dir,
            qid,
            choice=worker_id % 2,
            channel="cli",
            sender=f"worker-{worker_id}",
            actor="human",
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futs = [executor.submit(_worker, 1), executor.submit(_worker, 2)]
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())

    statuses = [r.status for r in results]
    assert sorted(statuses) == ["already", "recorded"]

    # Recorded answer file is single-valued
    ans_file = run_dir / "answers" / f"{qid}.json"
    assert ans_file.is_file()
    ans_data = json.loads(ans_file.read_text(encoding="utf-8"))
    assert ans_data["schema"] == "aw.answer/v1"
    assert ans_data["question_id"] == qid
    assert ans_data["actor"] == "human"

    # Sidecar rejection file has the second attempt
    rej_file = run_dir / "answers" / f"{qid}.rejected.jsonl"
    assert rej_file.is_file()
    rej_lines = rej_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(rej_lines) == 1
    rej_entry = json.loads(rej_lines[0])
    assert rej_entry["status"] == "already"
    assert rej_entry["reason"] == "already answered"


def test_concurrent_answers_subprocesses(tmp_path: Path) -> None:
    """E-02 / A42 / V-02: Two concurrent subprocesses answering same qid yield exactly one recorded and one already."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb004", setid="qinb", order=4)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000004"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 4,
        "id6": "inb004",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Pick one",
        "options": ["X", "Y"],
        "gates_verdict": True,
    }
    question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    qid = "04-inb004-a1-q1"

    py_cmd = f"""
import sys
from pathlib import Path
from agent_workflows import question_inbox

run_dir = Path({str(run_dir)!r})
qid = {qid!r}
res = question_inbox.write_answer(
    run_dir,
    qid,
    answer=f"Answer from {{sys.argv[1]}}",
    choice=0,
    channel="cli",
    sender=sys.argv[1],
    actor="human",
)
print(res.status)
"""

    p1 = subprocess.Popen(
        [sys.executable, "-c", py_cmd, "proc-1"], stdout=subprocess.PIPE, text=True
    )
    p2 = subprocess.Popen(
        [sys.executable, "-c", py_cmd, "proc-2"], stdout=subprocess.PIPE, text=True
    )

    out1, _ = p1.communicate()
    out2, _ = p2.communicate()

    assert p1.returncode == 0
    assert p2.returncode == 0

    outputs = [out1.strip(), out2.strip()]
    assert sorted(outputs) == ["already", "recorded"]


def test_answer_refusal_reasons(tmp_path: Path) -> None:
    """E-02 / A11 / A42 / V-02: Test all refusal reasons and assert ledger agreement on RL-E051."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb005", setid="qinb", order=5)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000005"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 5,
        "id6": "inb005",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Select environment",
        "options": ["staging", "production"],
        "allow_free_text": False,
        "gates_verdict": True,
    }
    question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    qid = "05-inb005-a1-q1"

    # 1. Unknown qid
    res_unknown = question_inbox.write_answer(
        run_dir,
        "99-unk001-a1-q1",
        answer="test",
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_unknown.status == "rejected"
    assert "unknown question_id" in res_unknown.reason

    # 2. Malformed qid
    res_malformed = question_inbox.write_answer(
        run_dir,
        "bad-qid",
        answer="test",
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_malformed.status == "rejected"
    assert "malformed question_id" in res_malformed.reason

    # 3. Non-human actor (A11): write_answer refuses AND run_ledger_schema enforces RL-E051
    res_bot = question_inbox.write_answer(
        run_dir,
        qid,
        choice=0,
        channel="cli",
        sender="dev",
        actor="bot",
    )
    assert res_bot.status == "rejected"
    assert "RL-E051" in res_bot.reason

    # Assert run_ledger_schema agrees
    raw_rec = {
        "seq": 1,
        "parent": "0000000000000000000000000000000000000000000000000000000000000000",
        "run_id": "run-00000001",
        "kind": "human_answer",
        "actor": "bot",
        "question_id": qid,
        "answer": "staging",
        "at": "2026-10-17T22:00:00Z",
    }
    verdict = run_ledger_schema.validate_record(raw_rec)
    violation_codes = [f.code for f in verdict.findings]
    assert "RL-E051" in violation_codes

    # 4. Out-of-range choice
    res_choice = question_inbox.write_answer(
        run_dir,
        qid,
        choice=5,
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_choice.status == "rejected"
    assert "outside options" in res_choice.reason

    # 5. Free-text answer when allow_free_text is false
    res_freetext = question_inbox.write_answer(
        run_dir,
        qid,
        answer="arbitrary environment",
        choice=None,
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_freetext.status == "rejected"
    assert "free-text answer not allowed" in res_freetext.reason

    # 6. Over-length answer (>4000)
    res_len = question_inbox.write_answer(
        run_dir,
        qid,
        answer="A" * 4001,
        choice=0,
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_len.status == "rejected"
    assert "exceeds 4000" in res_len.reason

    # 7. Over-length channel / sender
    res_chan = question_inbox.write_answer(
        run_dir,
        qid,
        choice=0,
        channel="C" * 201,
        sender="dev",
        actor="human",
    )
    assert res_chan.status == "rejected"
    assert "channel length" in res_chan.reason

    res_sender = question_inbox.write_answer(
        run_dir,
        qid,
        choice=0,
        channel="cli",
        sender="S" * 201,
        actor="human",
    )
    assert res_sender.status == "rejected"
    assert "sender length" in res_sender.reason

    # 8. Control characters
    res_ctrl = question_inbox.write_answer(
        run_dir,
        qid,
        answer="bad\x00data",
        choice=0,
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_ctrl.status == "rejected"
    assert "control characters" in res_ctrl.reason

    # 9. Stale question
    q_stale: dict[str, Any] = {
        "question_id": "q2",
        "text": "Stale Q?",
        "gates_verdict": True,
    }
    question_inbox.write_question(run_dir, item, q_stale, attempt=1, repo=repo)
    qid_stale = "05-inb005-a1-q2"
    question_inbox.set_question_status(run_dir, qid_stale, "stale", reason="superseded")
    res_stale = question_inbox.write_answer(
        run_dir,
        qid_stale,
        answer="late answer",
        channel="cli",
        sender="dev",
        actor="human",
    )
    assert res_stale.status == "rejected"
    assert "question status is not open" in res_stale.reason


def test_question_status_transitions(tmp_path: Path) -> None:
    """E-05 / V-05: Status transitions open -> answered and open -> stale; illegal transitions refused."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb006", setid="qinb", order=6)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000006"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 6,
        "id6": "inb006",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q1: dict[str, Any] = {
        "question_id": "q1",
        "text": "Question 1",
        "gates_verdict": True,
    }
    q2: dict[str, Any] = {
        "question_id": "q2",
        "text": "Question 2",
        "gates_verdict": True,
    }

    question_inbox.write_question(run_dir, item, q1, attempt=1, repo=repo)
    question_inbox.write_question(run_dir, item, q2, attempt=1, repo=repo)
    qid1 = "06-inb006-a1-q1"
    qid2 = "06-inb006-a1-q2"

    assert len(question_inbox.read_open_questions(run_dir)) == 2

    # 1. open -> answered
    ok1 = question_inbox.set_question_status(
        run_dir, qid1, "answered", reason="human answered via terminal"
    )
    assert ok1 is True
    assert question_inbox.read_question(run_dir, qid1)["status"] == "answered"

    # read_open_questions now reflects only qid2
    open_qs = question_inbox.read_open_questions(run_dir)
    assert len(open_qs) == 1
    assert open_qs[0]["question_id"] == qid2

    # 2. open -> stale
    ok2 = question_inbox.set_question_status(
        run_dir, qid2, "stale", reason="artifact changed"
    )
    assert ok2 is True
    assert question_inbox.read_question(run_dir, qid2)["status"] == "stale"
    assert len(question_inbox.read_open_questions(run_dir)) == 0

    # 3. answered -> open (illegal: a stale/answered question is never reopened)
    status_before = question_inbox.read_question(run_dir, qid1)["status"]
    assert status_before == "answered"
    ok_illegal = question_inbox.set_question_status(
        run_dir, qid1, "open", reason="try reopening"
    )
    assert ok_illegal is False
    status_after = question_inbox.read_question(run_dir, qid1)["status"]
    assert status_after == "answered"

    # 4. stale -> open (illegal)
    ok_illegal_stale = question_inbox.set_question_status(
        run_dir, qid2, "open", reason="try reopening"
    )
    assert ok_illegal_stale is False
    assert question_inbox.read_question(run_dir, qid2)["status"] == "stale"

    # Check question-status events in events.jsonl
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    status_events = [
        json.loads(e) for e in events if json.loads(e).get("event") == "question-status"
    ]
    assert len(status_events) == 2
    assert status_events[0]["question_id"] == qid1
    assert status_events[0]["status"] == "answered"
    assert status_events[1]["question_id"] == qid2
    assert status_events[1]["status"] == "stale"


def test_projection_refresh_and_lock(tmp_path: Path) -> None:
    """E-03 / V-03: Projection open-questions.md written at park and refreshed when answered."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb007", setid="qinb", order=7)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000007"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 7,
        "id6": "inb007",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Approve database migration?",
        "gates_verdict": True,
    }

    question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    qid = "07-inb007-a1-q1"

    # Projection initially lists the question
    p_path = question_inbox.write_projection(run_dir)
    assert p_path is not None
    assert p_path.is_file()
    initial_text = p_path.read_text(encoding="utf-8")
    assert f"## {qid}" in initial_text
    assert "Context: Approve database migration?" in initial_text

    # After write_answer, projection is updated to no unresolved questions
    res = question_inbox.write_answer(
        run_dir,
        qid,
        answer="Approved migration",
        channel="cli",
        sender="dba",
        actor="human",
    )
    assert res.status == "recorded"
    updated_text = p_path.read_text(encoding="utf-8")
    assert "_No unresolved questions._" in updated_text
    assert f"## {qid}" not in updated_text


def test_answer_atomicity_and_events(tmp_path: Path) -> None:
    """E-02 / V-02: Atomicity, events.jsonl contains human_answer and question_disposition."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb008", setid="qinb", order=8)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T220000Z-000008"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "position": 8,
        "id6": "inb008",
        "configured_file": str(plan),
        "repo": str(repo),
    }
    q: dict[str, Any] = {
        "question_id": "q1",
        "text": "Deploy region?",
        "options": ["us-east", "us-west"],
        "gates_verdict": True,
    }

    question_inbox.write_question(run_dir, item, q, attempt=1, repo=repo)
    qid = "08-inb008-a1-q1"

    res = question_inbox.write_answer(
        run_dir,
        qid,
        choice=1,
        channel="terminal",
        sender="testuser",
        actor="human",
    )
    assert res.status == "recorded"

    # Check answers/<qid>.json
    ans_file = run_dir / "answers" / f"{qid}.json"
    assert ans_file.is_file()
    ans = json.loads(ans_file.read_text(encoding="utf-8"))
    assert ans["schema"] == "aw.answer/v1"
    assert ans["question_id"] == qid
    assert ans["answer"] == "us-west"
    assert ans["choice"] == 1
    assert ans["actor"] == "human"
    assert ans["channel"] == "terminal"
    assert ans["sender"] == "testuser"
    assert ans["artifact_hash"] == hashlib.sha256(plan.read_bytes()).hexdigest()

    # Check events.jsonl lines
    events_file = run_dir / "events.jsonl"
    assert events_file.is_file()
    ev_lines = events_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(ev_lines) == 2
    ev1 = json.loads(ev_lines[0])
    ev2 = json.loads(ev_lines[1])

    assert ev1["event"] == "human_answer"
    assert ev1["kind"] == "human_answer"
    assert ev1["question_id"] == qid
    assert ev1["answer"] == "us-west"
    assert ev1["actor"] == "human"
    assert ev1["channel"] == "terminal"
    assert ev1["sender"] == "testuser"

    assert ev2["event"] == "question_disposition"
    assert ev2["kind"] == "question_disposition"
    assert ev2["question_id"] == qid
    assert ev2["disposition"] == "answered_by_human"
    assert ev2["actor"] == "human"


def test_park_wiring_in_scripted_run(tmp_path: Path) -> None:
    """E-03 / V-03: Scripted runner execute turn parks, writes inbox files and projection."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "inb009", setid="qinb", order=9)
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / "run-scripted-park"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    gating_question = {
        "question_id": "q-db-engine",
        "text": "Which database engine should be used for user records?",
        "artifact_id6": "inb009",
        "gates_verdict": True,
        "options": ["PostgreSQL", "SQLite"],
        "allow_free_text": True,
        "evidence": ["schema.sql"],
    }

    env_map = {
        "inb009": {
            "commit": "implement storage layer",
            "outcome": {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [gating_question],
                "pushed": False,
            },
        },
    }

    item: dict[str, Any] = {
        "id6": "inb009",
        "setid": "qinb",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": "run-scripted-park",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": True,
            "opencode": str(fake_bin),
            "output_mode": "quiet",
        },
    }

    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(env_map)}),
        coordinator_role(),
    ):
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    # Item parked
    assert item["status"] == "awaiting-human"
    assert item.get(runner_shared.NEEDS_INPUT_KEY) is True
    assert "question_ids" in item
    assert len(item["question_ids"]) == 1
    qid = item["question_ids"][0]
    assert qid == "01-inb009-a1-q-db-engine"

    # questions/<qid>.json exists
    q_file = run_dir / "questions" / f"{qid}.json"
    assert q_file.is_file()
    q_data = json.loads(q_file.read_text(encoding="utf-8"))
    assert q_data["status"] == "open"
    assert q_data["text"] == "Which database engine should be used for user records?"

    # open-questions.md exists and contains the heading
    proj_file = run_dir / set_records.OPEN_QUESTIONS_FILE
    assert proj_file.is_file()
    proj_content = proj_file.read_text(encoding="utf-8")
    assert f"## {qid}" in proj_content
    assert "Which database engine should be used for user records?" in proj_content

    # Now record an answer via write_answer
    ans_res = question_inbox.write_answer(
        run_dir,
        qid,
        choice=0,
        channel="cli",
        sender="lead",
        actor="human",
    )
    assert ans_res.status == "recorded"

    # open-questions.md refreshed
    proj_content_after = proj_file.read_text(encoding="utf-8")
    assert "_No unresolved questions._" in proj_content_after
    assert f"## {qid}" not in proj_content_after


def test_review_park_wiring(tmp_path: Path) -> None:
    """E-03 / V-03: Scripted runner review turn parks with gating question and writes inbox files."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(
        repo, "rev010", setid="qrev", order=10, status="to-review", action="review"
    )
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / "run-review-park"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    gating_question = {
        "question_id": "q-arch-review",
        "text": "Is the proposed modular architecture acceptable?",
        "artifact_id6": "rev010",
        "gates_verdict": True,
        "evidence": ["architecture doc"],
    }

    env_map = {
        "rev010": {
            "commit": "review comments",
            "dirty_file": f".aw/records/plans/pending/{plan.name}",
            "outcome": {
                "disposition": "reviewed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [gating_question],
                "pushed": False,
            },
        },
    }

    item: dict[str, Any] = {
        "id6": "rev010",
        "setid": "qrev",
        "position": 1,
        "action": "review",
        "review_handler": "plan-review",
        "status": "queued",
        "configured_file": str(plan),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": "run-review-park",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "isolate_review": True,
            "opencode": str(fake_bin),
            "output_mode": "quiet",
        },
    }

    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(env_map)}),
        coordinator_role(),
    ):
        oc_runipd.execute_item(run_dir, state, item, recovery=False)

    # Review item parked
    assert item["status"] == "awaiting-human"
    assert item.get(runner_shared.NEEDS_INPUT_KEY) is True
    assert "question_ids" in item
    assert len(item["question_ids"]) == 1
    qid = item["question_ids"][0]
    assert qid == "01-rev010-a1-q-arch-review"

    # questions/<qid>.json exists
    q_file = run_dir / "questions" / f"{qid}.json"
    assert q_file.is_file()
    q_data = json.loads(q_file.read_text(encoding="utf-8"))
    assert q_data["status"] == "open"
    assert q_data["action"] == "review"

    # open-questions.md exists
    proj_file = run_dir / set_records.OPEN_QUESTIONS_FILE
    assert proj_file.is_file()
    assert f"## {qid}" in proj_file.read_text(encoding="utf-8")
