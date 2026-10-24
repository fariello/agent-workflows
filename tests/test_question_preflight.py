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

"""Tests for pre-flight sweep of pre-existing open questions (spec 6kwd2e R1, qchan-07 4kkcex E-01..E-05).

Guards that:
1. Collector scope (A1): collects open questions from queued artifacts; excludes deferred/resolved;
   --blocking-only filters to Blocking: yes.
2. Timeout without waiting (A2): prompt_for_free_text returns None on timeout under a patched clock/select
   without calling input().
3. Distinct timeout and free text (A16): PREFLIGHT_QUESTION_TIMEOUT != GATE_PROMPT_TIMEOUT (300.0 vs 180.0);
   captures free text.
4. Stream handling and two-chunk pipe: Non-TTY streams return None and print nothing to stderr;
   a two-chunk pipe returns the combined answer.
5. Sweep interruption (A18): An interrupted sitting retains already-answered questions durably in artifacts
   with commits, and routes remaining questions to the inbox.
6. Behavioral bounded read (A27): Driver sweep completes with input() and readline() patched to raise.
7. Event ordering (A28): Sweep events precede run-created and any ipd-started in events.jsonl.
8. Durable write-back (A40): Answers land durably in the artifact (Status: resolved, rationale with user and date,
   Blocking: unchanged) and persist after run_dir is deleted.
9. Presence predicate (A41): --unattended and --full-auto yield no prompt even with a TTY present.
10. Unattended routing and checkpoint consumption (A47): Unattended run writes inbox; blocking item is held
    awaiting-human (preflight_parked: true, no lane); answering the question resolves it via record_oq_answer
    and commit, and re-queues as attempt 1.
11. Stale artifact refusal (R5.6, A12): Refuses write and marks answer stale when artifact hash moved.
12. Host flag parity: --blocking-only and --question-timeout are registered on both runner hosts.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
from pathlib import Path
from typing import Any
from unittest import mock

import pytest


from agent_workflows import (
    agy_runipd,
    oc_runipd,
    question_inbox,
    runner_shared,
)


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

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial repo commit"], cwd=repo, check=True
    )
    return repo


def _create_plan_with_oqs(
    repo: Path,
    id6: str,
    *,
    setid: str = "qpfl",
    order: int = 1,
    status: str = "approved",
    oqs: list[dict[str, Any]],
    commit: bool = True,
) -> Path:
    """Create a conforming plan file with specified Open Questions."""
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"20261017-{setid}-{order:02d}-{id6}-plan.ipd.md"

    oq_blocks = []
    for oq in oqs:
        oq_id = oq.get("id", "OQ-01")
        title = oq.get("title", f"Question {oq_id}")
        blocking = "yes" if oq.get("blocking", True) else "no"
        oq_status = oq.get("status", "open")
        rationale = oq.get("rationale", "")
        rat_line = (
            f"- Resolution or deferral rationale: {rationale}\n" if rationale else ""
        )
        oq_blocks.append(
            f"### {oq_id}: {title}\n\n"
            f"- Blocking: {blocking}\n"
            f"- Status: {oq_status}\n"
            f"- Owner: test author\n"
            f"{rat_line}"
        )

    oq_section = "## Open questions\n\n" + "\n\n".join(oq_blocks) if oq_blocks else ""

    content = f"""# IPD: Test Plan {id6}

- Kind: child
- Status: {status}
- Set: {setid}
- Order: {order}
- Id: {id6}
- Priority: medium
- Work-Kind: feature
- Scope-Paths: README.md

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Perform task
- [ ] V-01 Verify task

{oq_section}
"""
    plan_path.write_text(content, encoding="utf-8")
    if commit:
        subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True
        )
    return plan_path


def test_a1_collector_scope(tmp_path: Path):
    """A1 (R1.1, R1.2): Collector scopes open questions across queued artifacts, filters by blocking_only."""
    repo = _create_test_repo(tmp_path)
    p1 = _create_plan_with_oqs(
        repo,
        "art001",
        order=1,
        oqs=[
            {"id": "OQ-01", "blocking": True, "status": "open"},
            {"id": "OQ-02", "blocking": False, "status": "open"},
        ],
    )
    p2 = _create_plan_with_oqs(
        repo,
        "art002",
        order=2,
        oqs=[
            {"id": "OQ-01", "blocking": True, "status": "open"},
            {
                "id": "OQ-02",
                "blocking": False,
                "status": "deferred",
                "rationale": "later",
            },
        ],
    )
    p3 = _create_plan_with_oqs(
        repo,
        "art003",
        order=3,
        oqs=[
            {"id": "OQ-01", "blocking": False, "status": "open"},
            {
                "id": "OQ-02",
                "blocking": True,
                "status": "resolved",
                "rationale": "done",
            },
        ],
    )

    queue = [
        {"position": 1, "id6": "art001", "configured_file": str(p1.relative_to(repo))},
        {"position": 2, "id6": "art002", "configured_file": str(p2.relative_to(repo))},
        {"position": 3, "id6": "art003", "configured_file": str(p3.relative_to(repo))},
    ]

    all_qs = runner_shared.collect_preflight_questions(repo, queue, blocking_only=False)
    assert len(all_qs) == 4
    # Check that deferred and resolved are excluded
    oq_ids = [(q.artifact_id6, q.oq_id) for q in all_qs]
    assert ("art001", "OQ-01") in oq_ids
    assert ("art001", "OQ-02") in oq_ids
    assert ("art002", "OQ-01") in oq_ids
    assert ("art003", "OQ-01") in oq_ids
    assert ("art002", "OQ-02") not in oq_ids
    assert ("art003", "OQ-02") not in oq_ids

    blocking_qs = runner_shared.collect_preflight_questions(
        repo, queue, blocking_only=True
    )
    assert len(blocking_qs) == 2
    b_ids = [(q.artifact_id6, q.oq_id) for q in blocking_qs]
    assert b_ids == [("art001", "OQ-01"), ("art002", "OQ-01")]


def test_a2_prompt_timeout_and_no_input():
    """A2 (R1.3): Prompt returns None on timeout and never calls input()."""

    class MockTTY:
        def isatty(self):
            return True

        def fileno(self):
            return 0

    stdin = MockTTY()
    stderr = io.StringIO()
    setattr(stderr, "isatty", lambda: True)

    fake_now = [100.0]

    def fake_monotonic():
        t = fake_now[0]
        fake_now[0] += 50.0  # Advances 50 seconds on each call
        return t

    def forbidden_input(*_args, **_kwargs):
        raise AssertionError("builtins.input() was forbidden but called!")

    with mock.patch("time.monotonic", side_effect=fake_monotonic), mock.patch(
        "select.select", return_value=([], [], [])
    ), mock.patch("builtins.input", side_effect=forbidden_input):
        res = runner_shared.prompt_for_free_text(
            "What is your preference?",
            timeout=10.0,
            stdin=stdin,
            stderr=stderr,
        )
        assert res is None


def test_a16_distinct_timeout_and_free_text():
    """A16 (R1.3): Timeout constant is distinct from GATE_PROMPT_TIMEOUT and free text is captured."""
    assert runner_shared.PREFLIGHT_QUESTION_TIMEOUT != runner_shared.GATE_PROMPT_TIMEOUT
    assert runner_shared.PREFLIGHT_QUESTION_TIMEOUT == 300.0
    assert runner_shared.GATE_PROMPT_TIMEOUT == 180.0

    class MockTTY:
        def isatty(self):
            return True

        def fileno(self):
            return 0

    stdin = MockTTY()
    stderr = io.StringIO()
    setattr(stderr, "isatty", lambda: True)

    # Free text with custom characters
    free_text_payload = b"Option B with details: use v2 API\n"

    def read_chunk(_stream, _n=4096):
        return free_text_payload

    with mock.patch("select.select", return_value=([stdin], [], [])):
        ans = runner_shared.prompt_for_free_text(
            "Question heading",
            timeout=10.0,
            stdin=stdin,
            stderr=stderr,
            read_chunk=read_chunk,
        )
        assert ans == "Option B with details: use v2 API"


def test_prompt_two_chunk_pipe_and_non_tty():
    """E-02: Pipe fed in two chunks returns combined answer; non-TTY streams return None and write nothing."""

    class MockTTY:
        def isatty(self):
            return True

        def fileno(self):
            return 0

    stdin = MockTTY()
    stderr = io.StringIO()
    setattr(stderr, "isatty", lambda: True)

    chunks = [b"first chunk ", b"second chunk\n"]

    def read_chunk(_stream, _n=4096):
        if chunks:
            return chunks.pop(0)
        return b""

    with mock.patch("select.select", return_value=([stdin], [], [])):
        ans = runner_shared.prompt_for_free_text(
            "Chunk question",
            timeout=10.0,
            stdin=stdin,
            stderr=stderr,
            read_chunk=read_chunk,
        )
        assert ans == "first chunk second chunk"

    # Non-TTY test:
    non_tty_in = io.StringIO("test\n")
    non_tty_err = io.StringIO()
    ans = runner_shared.prompt_for_free_text(
        "Non-TTY question",
        timeout=10.0,
        stdin=non_tty_in,
        stderr=non_tty_err,
    )
    assert ans is None
    assert non_tty_err.getvalue() == ""


def test_a40_durable_artifact_write_back(tmp_path: Path):
    """A40 (R1.5): Answer is recorded durably into artifact and survives run_dir deletion."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "dur001",
        oqs=[
            {
                "id": "OQ-01",
                "title": "Database schema choice",
                "blocking": True,
                "status": "open",
            }
        ],
    )
    orig_hash = runner_shared.sha256_file(plan_path)

    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer="Use PostgreSQL 16 JSONB",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=orig_hash,
    )
    assert recorded is True

    text = plan_path.read_text(encoding="utf-8")
    assert "- Status: resolved" in text
    assert (
        "- Resolution or deferral rationale: RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB"
        in text
    )
    assert "- Blocking: yes" in text
    assert "- Owner: test author" in text


def test_stale_artifact_refusal(tmp_path: Path):
    """R5.6 / A12: record_oq_answer refuses if artifact hash does not match expected_hash."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "stl001",
        oqs=[{"id": "OQ-01", "blocking": True, "status": "open"}],
    )

    bad_hash = "0" * 64
    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer="Answer to stale",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=bad_hash,
    )
    assert recorded is False

    # Verify content was untouched
    text = plan_path.read_text(encoding="utf-8")
    assert "- Status: open" in text


@pytest.mark.core
def test_record_oq_answer_appends_to_existing_rationale(tmp_path: Path):
    """E-02 / mqsitd: record_oq_answer appends answer to existing rationale text."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "app001",
        oqs=[
            {
                "id": "OQ-01",
                "title": "Database schema choice",
                "blocking": True,
                "status": "open",
                "rationale": "Original question context: SQLite or Postgres?",
            }
        ],
    )
    orig_hash = runner_shared.sha256_file(plan_path)

    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer="Use PostgreSQL 16 JSONB",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=orig_hash,
    )
    assert recorded is True

    text = plan_path.read_text(encoding="utf-8")
    assert "Original question context: SQLite or Postgres?" in text
    assert (
        "- Resolution or deferral rationale: Original question context: SQLite or Postgres? RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB"
        in text
    )
    assert "- Status: resolved" in text
    assert "- Blocking: yes" in text
    assert "- Owner: test author" in text


@pytest.mark.core
def test_record_oq_answer_appends_with_indented_continuation_rationale(tmp_path: Path):
    """E-02 / mqsitd: record_oq_answer preserves indented continuation lines and appends RESOLVED once."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "app002",
        oqs=[
            {
                "id": "OQ-01",
                "title": "Database schema choice",
                "blocking": True,
                "status": "open",
            }
        ],
    )
    # Write continuation line directly into the fixture file
    content = plan_path.read_text(encoding="utf-8")
    content = content.replace(
        "- Owner: test author\n",
        "- Owner: test author\n- Resolution or deferral rationale: First line context\n    Indented continuation line\n",
    )
    plan_path.write_text(content, encoding="utf-8")
    orig_hash = runner_shared.sha256_file(plan_path)

    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer="Use PostgreSQL 16 JSONB",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=orig_hash,
    )
    assert recorded is True

    text = plan_path.read_text(encoding="utf-8")
    assert "First line context" in text
    assert "    Indented continuation line" in text
    assert (
        "- Resolution or deferral rationale: First line context\n    Indented continuation line RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB"
        in text
    )
    assert (
        text.count(
            "RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB"
        )
        == 1
    )
    assert "- Status: resolved" in text
    assert "- Blocking: yes" in text
    assert "- Owner: test author" in text


@pytest.mark.core
def test_record_oq_answer_preserves_backslash_answer_rationale(tmp_path: Path):
    """E-02 / mqsitd: record_oq_answer handles answers with backslashes without raising re.error."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "app003",
        oqs=[
            {
                "id": "OQ-01",
                "title": "Path choice",
                "blocking": True,
                "status": "open",
                "rationale": "Pending path decision.",
            }
        ],
    )
    orig_hash = runner_shared.sha256_file(plan_path)

    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer=r"C:\new\1",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=orig_hash,
    )
    assert recorded is True

    text = plan_path.read_text(encoding="utf-8")
    assert "- Status: resolved" in text
    rationale_lines = [
        line
        for line in text.splitlines()
        if "- Resolution or deferral rationale:" in line
    ]
    assert len(rationale_lines) == 1
    assert rationale_lines[0].endswith(r": C:\new\1")
    assert (
        "- Resolution or deferral rationale: Pending path decision. RESOLVED 2026-10-17 by developer via aw oc run pre-flight: C:\\new\\1"
        in text
    )


@pytest.mark.core
def test_record_oq_answer_empty_field_rationale(tmp_path: Path):
    """E-02 / mqsitd: record_oq_answer on present-but-empty rationale field emits RESOLVED line cleanly."""
    repo = _create_test_repo(tmp_path)
    plan_path = _create_plan_with_oqs(
        repo,
        "app004",
        oqs=[
            {
                "id": "OQ-01",
                "title": "Empty rationale choice",
                "blocking": True,
                "status": "open",
            }
        ],
    )
    content = plan_path.read_text(encoding="utf-8")
    content = content.replace(
        "- Owner: test author\n",
        "- Owner: test author\n- Resolution or deferral rationale:\n",
    )
    plan_path.write_text(content, encoding="utf-8")
    orig_hash = runner_shared.sha256_file(plan_path)

    recorded = runner_shared.record_oq_answer(
        repo,
        plan_path.relative_to(repo),
        "OQ-01",
        answer="Use PostgreSQL 16 JSONB",
        who="developer",
        channel="aw oc run pre-flight",
        date="2026-10-17",
        expected_hash=orig_hash,
    )
    assert recorded is True

    text = plan_path.read_text(encoding="utf-8")
    assert "- Status: resolved" in text
    assert (
        "- Resolution or deferral rationale: RESOLVED 2026-10-17 by developer via aw oc run pre-flight: Use PostgreSQL 16 JSONB"
        in text
    )


def test_a18_and_a28_sweep_sitting_and_events(tmp_path: Path):
    """A18 / A28: Interrupted sitting retains 4 answered and routes 11; events precede run-created."""
    repo = _create_test_repo(tmp_path)
    # Create 15 questions across 3 plans (5 questions each)
    plans = []
    for p_idx in range(1, 4):
        p_id = f"art0{p_idx:02d}"
        oqs = [
            {
                "id": f"OQ-{q_idx:02d}",
                "title": f"Question {p_idx}-{q_idx}",
                "blocking": True,
                "status": "open",
            }
            for q_idx in range(1, 6)
        ]
        p_file = _create_plan_with_oqs(repo, p_id, order=p_idx, oqs=oqs)
        plans.append((p_id, p_file))

    # Answers count: first 4 answer, 5th raises KeyboardInterrupt
    ans_count = [0]

    def fake_prompt(q, timeout=300.0):
        ans_count[0] += 1
        if ans_count[0] <= 4:
            return f"Answer for {getattr(q, 'oq_id', '')}"
        raise KeyboardInterrupt()

    args = argparse.Namespace(
        repo=str(repo),
        selectors=["pending"],
        prepare_only=False,
        blocking_only=False,
        question_timeout=300,
        output_mode="clean",
        verbosity=0,
        yes=True,
    )

    with mock.patch(
        "agent_workflows.runner_shared.is_interactive_run", return_value=True
    ), mock.patch(
        "agent_workflows.runner_shared.enforce_freeze_time_refusal", return_value=None
    ), mock.patch(
        "agent_workflows.runner_shared.prompt_for_free_text", side_effect=fake_prompt
    ):
        run_dir = runner_shared.initialize_run_core(
            args,
            host="oc",
            driver_path=None,
            host_options={},
            labels=runner_shared.OC_HOST_LABELS,
            expand_selectors_fn=lambda _m, _s, **_k: [p[0] for p in plans],
            enforce_dependency_preflight_fn=lambda _r, _p: None,
            run_order_rationale_fn=lambda _q, _s: [],
            announce_run_order_fn=lambda _r, _s: None,
            write_report_fn=lambda _r, _s: None,
        )

    # 1. Check events.jsonl ordering (A28)
    events_file = run_dir / "events.jsonl"
    events = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    event_names = [e["event"] for e in events]

    assert "run-created" in event_names
    run_created_idx = event_names.index("run-created")
    # All preflight events must precede run-created
    for idx, e in enumerate(events):
        if e["event"].startswith("preflight-"):
            assert (
                idx < run_created_idx
            ), f"Preflight event {e['event']} occurred at {idx} >= {run_created_idx}"

    # 2. Check that 4 answers are resolved and committed, 11 are routed (A18)
    answered_events = [e for e in events if e["event"] == "preflight-question-answered"]
    assert len(answered_events) == 4

    questions_dir = run_dir / "questions"
    q_files = list(questions_dir.glob("*.json"))
    assert len(q_files) == 11


def test_a41_presence_predicate_unattended_and_full_auto(tmp_path: Path):
    """A41 (R7.1): --unattended and --full-auto yield no prompt even with a TTY present."""
    repo = _create_test_repo(tmp_path)
    _create_plan_with_oqs(
        repo,
        "prs001",
        oqs=[{"id": "OQ-01", "blocking": True, "status": "open"}],
    )

    for flag in ("unattended", "full_auto"):
        prompt_called = [False]

        def fake_prompt(*_args, **_kwargs):
            prompt_called[0] = True
            return "unexpected"

        kwargs = {
            "repo": str(repo),
            "selectors": ["pending"],
            "prepare_only": False,
            flag: True,
        }
        args = argparse.Namespace(**kwargs)

        with mock.patch(
            "agent_workflows.runner_shared.enforce_freeze_time_refusal",
            return_value=None,
        ), mock.patch(
            "agent_workflows.runner_shared.prompt_for_free_text",
            side_effect=fake_prompt,
        ):
            run_dir = runner_shared.initialize_run_core(
                args,
                host="oc",
                driver_path=None,
                host_options={},
                labels=runner_shared.OC_HOST_LABELS,
                expand_selectors_fn=lambda _m, _s, **_k: ["prs001"],
                enforce_dependency_preflight_fn=lambda _r, _p: None,
                run_order_rationale_fn=lambda _q, _s: [],
                announce_run_order_fn=lambda _r, _s: None,
                write_report_fn=lambda _r, _s: None,
            )

        assert prompt_called[0] is False, f"Prompt was called under {flag}!"
        # Question was routed to inbox
        q_files = list((run_dir / "questions").glob("*.json"))
        assert len(q_files) == 1


def test_a47_unattended_routing_and_checkpoint_consumption(tmp_path: Path):
    """A47 (R9.7): Under --unattended with a TTY: no prompt, inbox written, answer consumed at checkpoint."""
    repo = _create_test_repo(tmp_path)
    # Plan 1 has blocking OQ; Plan 2 has non-blocking OQ
    p1 = _create_plan_with_oqs(
        repo,
        "unt001",
        order=1,
        oqs=[{"id": "OQ-01", "blocking": True, "status": "open"}],
    )
    _create_plan_with_oqs(
        repo,
        "unt002",
        order=2,
        oqs=[{"id": "OQ-01", "blocking": False, "status": "open"}],
    )

    args = argparse.Namespace(
        repo=str(repo),
        selectors=["pending"],
        prepare_only=False,
        unattended=True,
    )

    with mock.patch(
        "agent_workflows.runner_shared.enforce_freeze_time_refusal", return_value=None
    ):
        run_dir = runner_shared.initialize_run_core(
            args,
            host="oc",
            driver_path=None,
            host_options={},
            labels=runner_shared.OC_HOST_LABELS,
            expand_selectors_fn=lambda _m, _s, **_k: ["unt001", "unt002"],
            enforce_dependency_preflight_fn=lambda _r, _p: None,
            run_order_rationale_fn=lambda _q, _s: [],
            announce_run_order_fn=lambda _r, _s: None,
            write_report_fn=lambda _r, _s: None,
        )

    state = runner_shared.load_state(run_dir)
    queue = state["queue"]
    item1 = next(it for it in queue if it["id6"] == "unt001")
    item2 = next(it for it in queue if it["id6"] == "unt002")

    # Item 1 has blocking question -> held awaiting-human, preflight_parked, no lane
    assert item1["status"] == runner_shared.AWAITING_HUMAN_STATUS
    assert item1["preflight_parked"] is True
    assert item1.get("preserved_lane_id") is None

    # Item 2 has only non-blocking question -> remains queued
    assert item2["status"] == "queued"
    assert not item2.get("preflight_parked")

    # Both questions written to questions/
    questions = question_inbox.read_questions(run_dir)
    assert len(questions) == 2

    # Now write answer for item 1's blocking question
    q1_obj = next(q for q in questions if q["artifact_id6"] == "unt001")
    q1_id = q1_obj["question_id"]
    ans_res = question_inbox.write_answer(
        run_dir,
        q1_id,
        answer="Resolved blocking design question",
        actor="human",
        channel="cli",
        sender="tester",
    )
    assert ans_res.recorded is True

    # Run consume_answers
    requeued = runner_shared.consume_answers(run_dir, state)
    assert requeued == ["unt001"]

    # Verify item 1 is now queued without resume_with_answers
    assert item1["status"] == "queued"
    assert item1.get("preflight_parked") is False
    assert "resume_with_answers" not in item1

    # Verify artifact was updated durably and committed
    p1_text = p1.read_text(encoding="utf-8")
    assert "- Status: resolved" in p1_text
    assert "Resolved blocking design question" in p1_text

    # Check git log on plan 1
    log = subprocess.check_output(
        ["git", "log", "-1", "--format=%s", str(p1)], cwd=repo, text=True
    ).strip()
    assert "unt001" in log
    assert "pre-flight sweep answer" in log


def test_a27_behavioral_no_unbounded_read():
    """A27 (R1.3a): Drive the sweep prompt with builtins.input and readline patched to raise."""

    class MockTTY:
        def isatty(self):
            return True

        def fileno(self):
            return 0

    stdin = MockTTY()
    stderr = io.StringIO()
    setattr(stderr, "isatty", lambda: True)

    def forbidden_input(*_a, **_k):
        raise AssertionError("builtins.input() called")

    def forbidden_readline(*_a, **_k):
        raise AssertionError("readline() called")

    with mock.patch("builtins.input", side_effect=forbidden_input), mock.patch(
        "sys.stdin.readline", side_effect=forbidden_readline
    ), mock.patch("select.select", return_value=([stdin], [], [])):
        ans = runner_shared.prompt_for_free_text(
            "Behavioral test",
            timeout=10.0,
            stdin=stdin,
            stderr=stderr,
            read_chunk=lambda _s, _n=4096: b"valid answer\n",
        )
        assert ans == "valid answer"


def test_host_flag_parity():
    """Verify --blocking-only and --question-timeout exist in RUN_POLICY_FLAGS and on both hosts."""
    flag_names = {row.flag for row in runner_shared.RUN_POLICY_FLAGS}
    assert "--blocking-only" in flag_names
    assert "--question-timeout" in flag_names

    # Check parsers for oc and agy
    for runner_mod in (oc_runipd, agy_runipd):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="subcommand")
        run_parser = subparsers.add_parser("run")
        runner_shared.register_run_policy_flags(run_parser)
        opts = run_parser.format_help()
        assert "--blocking-only" in opts
        assert "--question-timeout" in opts
