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

"""Tests for aw runs answer and aw runs questions against runner runs (spec 6kwd2e R9.5, R4a.2, A45, A10c).

Validates:
1. Registration & help: aw runs answer registered on runs_sub, positionals optional,
   aw runs --help names answer as fifth exception, --help documents exit codes 0-2.
2. Interactive answering: piped stdin with --interactive records answers, preserves
   answers on EOF, prints already answered on repeat, strips ANSI escape sequences.
3. Non-interactive & machine output: --choice and --answer record answers without prompting,
   --agent emits valid aw.agent/v1 result records passing agent_schema.validate_agent_record,
   --json emits structured JSON, exits 0 on recorded/listed, 1 on already/refusal, 2 on usage/unknown run/malformed qid.
4. Runner run lookup in aw runs questions: reads <run_dir>/open-questions.md, exits 0 when
   questions are open, exits 1 when none are open, preserves Set-run/ledger lookup.
5. Live run integration with barrier: Item 1 parks with gating question, Item 2 blocks on barrier
   while driver holds driver.lock, aw runs questions and aw runs answer succeed against the live run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any
from unittest import mock


from agent_workflows import (
    agent_schema,
    oc_runipd,
    question_inbox,
    run_viewer,
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
    setid: str = "qans",
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


def _run_cli(
    repo: Path,
    args: list[str],
    input_str: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI as a subprocess in repo root."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path.cwd())
    env.pop("CI", None)
    env.pop("AW_NONINTERACTIVE", None)
    if extra_env:
        env.update(extra_env)
    cmd = [sys.executable, "-m", "agent_workflows"] + args
    return subprocess.run(
        cmd,
        cwd=repo,
        input=input_str,
        text=True,
        capture_output=True,
        check=False,
    )


def test_runs_answer_help(tmp_path: Path) -> None:
    """E-01: aw runs answer --help documents usage, flags, and exit codes; aw runs --help names answer."""
    repo = _create_test_repo(tmp_path)

    # aw runs answer --help
    proc = _run_cli(repo, ["runs", "answer", "--help"])
    assert proc.returncode == 0
    assert "Answer open questions for a live or finished run" in proc.stdout
    assert "--answer" in proc.stdout
    assert "--choice" in proc.stdout
    assert "Exit codes: 0 recorded or questions listed" in proc.stdout

    # aw runs --help names answer among the exceptions
    proc_family = _run_cli(repo, ["runs", "--help"])
    assert proc_family.returncode == 0
    assert "with FIVE exceptions" in proc_family.stdout
    assert "aw runs answer" in proc_family.stdout
    assert "MUTATES: answer open questions" in proc_family.stdout


def test_runs_answer_unknown_run(tmp_path: Path) -> None:
    """E-01 / V-01: Unknown run id exits 2 with error record under --agent."""
    repo = _create_test_repo(tmp_path)

    proc_human = _run_cli(repo, ["runs", "answer", "run-nonexistent"])
    assert proc_human.returncode == 2
    assert "error: unknown run: run-nonexistent" in proc_human.stdout

    proc_agent = _run_cli(repo, ["runs", "answer", "run-nonexistent", "--agent"])
    assert proc_agent.returncode == 2
    rec = json.loads(proc_agent.stdout.strip())
    assert rec["schema"] == "aw.agent/v1"
    assert rec["kind"] == "result"
    assert rec["exit"] == 2
    assert rec["outcome"] == "error"
    assert agent_schema.validate_agent_record(rec) == []


def test_runs_answer_interactive_and_ansi_stripped(tmp_path: Path) -> None:
    """E-02 / V-02: Interactive form answers two questions via piped stdin, strips ANSI from question text."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "ans001", setid="qans", order=1)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T230000Z-000001"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner_shared.save_state(
        run_dir,
        {
            "run_id": "run-20261017T230000Z-000001",
            "repo": str(repo),
            "queue": [],
        },
    )

    item: dict[str, Any] = {
        "position": 1,
        "id6": "ans001",
        "action": "execute",
        "configured_file": str(plan),
        "repo": str(repo),
        "run_id": "run-20261017T230000Z-000001",
    }

    # Q1: Choice with free text allowed (alphabetically first: q1-db)
    qid1 = "01-ans001-a1-q1-db"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid1,
            "text": "Which DB engine should be used?",
            "options": ["PostgreSQL", "SQLite"],
            "allow_free_text": True,
            "evidence": ["db.py"],
        },
    )

    # Q2: Question with ANSI escape codes in text (alphabetically second: q2-ansi)
    qid2 = "01-ans001-a1-q2-ansi"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid2,
            "text": "\x1b[31mCritical Warning\x1b[0m: select fallback policy",
            "options": ["Retry", "FailFast"],
            "allow_free_text": True,
            "evidence": ["policy.py"],
        },
    )
    question_inbox.write_projection(run_dir)

    # Interactive session providing "1\n" for Q1 (choice 0) and "Use custom policy\n" for Q2
    proc = _run_cli(
        repo,
        ["runs", "answer", "run-20261017T230000Z-000001", "--interactive"],
        input_str="1\nUse custom policy\n",
    )
    assert proc.returncode == 0
    # Both recorded
    assert proc.stdout.count("recorded") == 2

    # Verify both answers exist on disk
    ans1_file = run_dir / "answers" / f"{qid1}.json"
    ans2_file = run_dir / "answers" / f"{qid2}.json"
    assert ans1_file.is_file()
    assert ans2_file.is_file()

    ans1_data = json.loads(ans1_file.read_text(encoding="utf-8"))
    assert ans1_data["choice"] == 0
    assert ans1_data["answer"] == "PostgreSQL"

    ans2_data = json.loads(ans2_file.read_text(encoding="utf-8"))
    assert ans2_data["answer"] == "Use custom policy"

    # Verify ANSI was stripped from stdout
    assert "Critical Warning: select fallback policy" in proc.stdout
    assert "\x1b[" not in proc.stdout
    assert "\x1b" not in proc.stdout

    # Now a second attempt to answer should report already answered or no open questions
    proc_repeat = _run_cli(
        repo,
        ["runs", "answer", "run-20261017T230000Z-000001", "--interactive"],
        input_str="1\n",
    )
    assert proc_repeat.returncode == 1
    assert (
        "already answered" in proc_repeat.stdout
        or "no open questions found" in proc_repeat.stdout
    )


def test_runs_answer_interactive_eof_preserves_earlier(tmp_path: Path) -> None:
    """E-02: EOF or interrupt mid-session preserves earlier answers."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "ans002", setid="qans", order=2)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T230000Z-000002"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner_shared.save_state(
        run_dir,
        {
            "run_id": "run-20261017T230000Z-000002",
            "repo": str(repo),
            "queue": [],
        },
    )

    item: dict[str, Any] = {
        "position": 1,
        "id6": "ans002",
        "action": "execute",
        "configured_file": str(plan),
        "repo": str(repo),
        "run_id": "run-20261017T230000Z-000002",
    }

    qid1 = "01-ans002-a1-q1"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid1,
            "text": "Question 1?",
            "options": ["A", "B"],
        },
    )
    qid2 = "01-ans002-a1-q2"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid2,
            "text": "Question 2?",
            "options": ["C", "D"],
        },
    )
    question_inbox.write_projection(run_dir)

    # Input answers Q1 with choice 0 ("1\n"), then closes stdin (EOF) before Q2
    proc = _run_cli(
        repo,
        ["runs", "answer", "run-20261017T230000Z-000002", "--interactive"],
        input_str="1\n",
    )
    assert proc.returncode == 0
    assert "recorded" in proc.stdout

    # Q1 is answered, Q2 has no answer file
    assert (run_dir / "answers" / f"{qid1}.json").is_file()
    assert not (run_dir / "answers" / f"{qid2}.json").exists()

    # Re-answering Q1 reports already answered
    proc_rep = _run_cli(
        repo,
        ["runs", "answer", "run-20261017T230000Z-000002", qid1, "--choice", "0"],
    )
    assert proc_rep.returncode == 1
    assert "already answered" in proc_rep.stdout


def test_runs_answer_non_interactive_and_agent(tmp_path: Path) -> None:
    """E-03 / V-03: Non-interactive form, --agent record validation, and refusal exit codes."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "ans003", setid="qans", order=3)

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261017T230000Z-000003"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner_shared.save_state(
        run_dir,
        {
            "run_id": "run-20261017T230000Z-000003",
            "repo": str(repo),
            "queue": [],
        },
    )

    item: dict[str, Any] = {
        "position": 1,
        "id6": "ans003",
        "action": "execute",
        "configured_file": str(plan),
        "repo": str(repo),
        "run_id": "run-20261017T230000Z-000003",
    }

    qid_choice = "01-ans003-a1-q-choice"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid_choice,
            "text": "Choose deployment target",
            "options": ["Staging", "Prod"],
            "allow_free_text": False,
        },
    )

    qid_free = "01-ans003-a1-q-free"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid_free,
            "text": "Enter service name",
            "options": None,
            "allow_free_text": True,
        },
    )
    question_inbox.write_projection(run_dir)

    # 1. Non-interactive listing (no answer flags)
    proc_list = _run_cli(repo, ["runs", "answer", "run-20261017T230000Z-000003"])
    assert proc_list.returncode == 0
    assert "Choose deployment target" in proc_list.stdout
    assert "Enter service name" in proc_list.stdout

    # 2. Non-interactive listing under --agent
    proc_list_agent = _run_cli(
        repo, ["runs", "answer", "run-20261017T230000Z-000003", "--agent"]
    )
    assert proc_list_agent.returncode == 0
    rec_list = json.loads(proc_list_agent.stdout.strip())
    assert rec_list["schema"] == "aw.agent/v1"
    assert rec_list["kind"] == "result"
    assert rec_list["exit"] == 0
    assert rec_list["outcome"] == "ok"
    assert len(rec_list["questions"]) == 2
    assert agent_schema.validate_agent_record(rec_list) == []

    # 3. Non-interactive --choice answering under --agent
    proc_agent = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_choice,
            "--choice",
            "0",
            "--agent",
        ],
    )
    assert proc_agent.returncode == 0
    rec_ans = json.loads(proc_agent.stdout.strip())
    assert rec_ans["schema"] == "aw.agent/v1"
    assert rec_ans["kind"] == "result"
    assert rec_ans["exit"] == 0
    assert rec_ans["outcome"] == "ok"
    assert rec_ans["answer"]["status"] == "recorded"
    assert rec_ans["answer"]["question_id"] == qid_choice
    assert agent_schema.validate_agent_record(rec_ans) == []

    # 4. Repeat answer exits 1 ("already")
    proc_repeat = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_choice,
            "--choice",
            "0",
        ],
    )
    assert proc_repeat.returncode == 1
    assert "already answered" in proc_repeat.stdout

    # Repeat under --agent exits 1
    proc_repeat_agent = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_choice,
            "--choice",
            "0",
            "--agent",
        ],
    )
    assert proc_repeat_agent.returncode == 1
    rec_rep = json.loads(proc_repeat_agent.stdout.strip())
    assert rec_rep["exit"] == 1
    assert rec_rep["outcome"] == "fail"
    assert rec_rep["answer"]["status"] == "already"
    assert agent_schema.validate_agent_record(rec_rep) == []

    # 5. Non-interactive --answer under --json
    proc_json = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_free,
            "--answer",
            "auth-svc",
            "--json",
        ],
    )
    assert proc_json.returncode == 0
    data_json = json.loads(proc_json.stdout.strip())
    assert data_json["answer"]["status"] == "recorded"
    assert data_json["answer"]["question_id"] == qid_free

    # 6. Refusal: choice out of range (exits 1)
    qid_choice2 = "01-ans003-a1-q-ch2"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid_choice2,
            "text": "Option pick",
            "options": ["A", "B"],
        },
    )
    proc_oor = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_choice2,
            "--choice",
            "99",
        ],
    )
    assert proc_oor.returncode == 1
    assert "outside options" in proc_oor.stdout

    # 7. Refusal: free text when allow_free_text is False (exits 1)
    qid_nofree = "01-ans003-a1-q-nofree"
    question_inbox.write_question(
        run_dir,
        item,
        {
            "question_id": qid_nofree,
            "text": "Strict choice",
            "options": ["Yes", "No"],
            "allow_free_text": False,
        },
    )
    proc_nofree = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            qid_nofree,
            "--answer",
            "custom text",
        ],
    )
    assert proc_nofree.returncode == 1
    assert "not allowed when allow_free_text is false" in proc_nofree.stdout

    # 8. Refusal: malformed qid exits 2
    proc_mal = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            "bad-qid!",
            "--choice",
            "0",
        ],
    )
    assert proc_mal.returncode == 2
    assert "malformed question_id" in proc_mal.stdout

    # 9. Refusal: unknown qid exits 2
    proc_unk = _run_cli(
        repo,
        [
            "runs",
            "answer",
            "run-20261017T230000Z-000003",
            "01-ans003-a1-q-unknown",
            "--choice",
            "0",
        ],
    )
    assert proc_unk.returncode == 2
    assert "unknown question_id" in proc_unk.stdout

    # 10. Usage error: --answer without question_id exits 2
    proc_missing_qid = _run_cli(
        repo,
        ["runs", "answer", "run-20261017T230000Z-000003", "--answer", "hi"],
    )
    assert proc_missing_qid.returncode == 2
    assert "--answer/--choice requires both" in proc_missing_qid.stdout


def test_live_run_questions_and_answer_with_barrier(tmp_path: Path) -> None:
    """E-04 / E-05 / V-04: Live driver run with barrier holds driver.lock; aw runs questions reads open-questions.md."""
    repo = _create_test_repo(tmp_path)
    plan1 = _create_plan_file(repo, "bar001", setid="qbar", order=1)
    plan2 = _create_plan_file(repo, "bar002", setid="qbar", order=2)

    run_id = "run-live-barrier-001"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    gating_question = {
        "question_id": "q-arch-db",
        "text": "Approve database architecture change?",
        "artifact_id6": "bar001",
        "gates_verdict": True,
        "options": ["Approve", "Reject"],
        "allow_free_text": True,
        "evidence": ["arch.md"],
    }

    item1: dict[str, Any] = {
        "id6": "bar001",
        "setid": "qbar",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan1),
        "attempts": [],
    }

    item2: dict[str, Any] = {
        "id6": "bar002",
        "setid": "qbar",
        "position": 2,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan2),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": run_id,
        "queue": [item1, item2],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }

    runner_shared.save_state(run_dir, state)

    barrier_entered = threading.Event()
    barrier_release = threading.Event()

    def fake_turn_executor(
        state_arg: Any,
        rd_arg: Any,
        it_arg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[int, str | None, Path, list[str]]:
        pos = it_arg["position"]
        cid6 = it_arg["id6"]
        out_file = rd_arg / f"outcomes/{pos:02d}-{cid6}.json"
        log_f = rd_arg / f"logs/{cid6}.log"
        log_f.parent.mkdir(parents=True, exist_ok=True)
        log_f.write_text("turn log\n", encoding="utf-8")

        if cid6 == "bar001":
            # Item 1 records executed with gating question, triggering runner park branch
            outcome_data = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [gating_question],
                "pushed": False,
            }
            out_file.write_text(json.dumps(outcome_data), encoding="utf-8")
            return (0, "ses-1", log_f, [])
        elif cid6 == "bar002":
            # Item 2 signals it has started, then waits on the barrier
            barrier_entered.set()
            barrier_release.wait(timeout=10.0)

            outcome_data = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            }
            out_file.write_text(json.dumps(outcome_data), encoding="utf-8")
            exec_dir = repo / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True, exist_ok=True)
            if plan2.exists():
                plan2.rename(exec_dir / plan2.name)
            return (0, "ses-1", log_f, [])
        return (1, None, log_f, [])

    # Launch driver in a background thread holding the run lock
    driver_error: list[Exception] = []

    def run_driver() -> None:
        try:
            with (
                runner_shared.locked_run(run_dir),
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(
                    oc_runipd, "run_opencode", side_effect=fake_turn_executor
                ),
                coordinator_role(),
            ):
                oc_runipd.run_queue(run_dir, state)
        except Exception as exc:
            driver_error.append(exc)

    driver_thread = threading.Thread(target=run_driver, daemon=True)
    driver_thread.start()

    # Wait until Item 2 is executing and blocked on the barrier
    assert barrier_entered.wait(timeout=10.0), "Item 2 did not start execution"

    try:
        # 1. Assert driver holds driver.lock
        assert run_viewer.driver_holder_state(run_dir) == run_viewer.HOLDER_LIVE

        # 2. aw runs questions <run-id> reads <run_dir>/open-questions.md (A10c)
        proc_qs = _run_cli(repo, ["runs", "questions", run_id])
        assert proc_qs.returncode == 0
        assert "Approve database architecture change?" in proc_qs.stdout
        assert "01-bar001-a1-q-arch-db" in proc_qs.stdout

        # 3. aw runs answer with no run-id discovers live run and lists its open questions
        proc_ans_list = _run_cli(repo, ["runs", "answer"])
        assert proc_ans_list.returncode == 0
        assert run_id in proc_ans_list.stdout
        assert "Approve database architecture change?" in proc_ans_list.stdout

        # 4. Answer the question from another terminal / subprocess
        qid = "01-bar001-a1-q-arch-db"
        proc_ans = _run_cli(repo, ["runs", "answer", run_id, qid, "--choice", "0"])
        assert proc_ans.returncode == 0
        assert "recorded" in proc_ans.stdout

        # Answer file exists on disk
        ans_file = run_dir / "answers" / f"{qid}.json"
        assert ans_file.is_file()
        assert json.loads(ans_file.read_text(encoding="utf-8"))["choice"] == 0

    finally:
        # Release the barrier so Item 2 and the driver finish cleanly
        barrier_release.set()
        driver_thread.join(timeout=10.0)

    assert not driver_thread.is_alive(), "Driver thread failed to terminate"
    assert not driver_error, f"Driver thread raised error: {driver_error}"


def test_runs_questions_runner_no_questions_exits_1(tmp_path: Path) -> None:
    """E-04: A runner run with no open questions reports none open (exit 1)."""
    repo = _create_test_repo(tmp_path)
    run_dir = repo / ".aw" / "records" / "runs" / "run-empty-park"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner_shared.save_state(
        run_dir,
        {
            "run_id": "run-empty-park",
            "repo": str(repo),
            "queue": [],
        },
    )

    proc = _run_cli(repo, ["runs", "questions", "run-empty-park"])
    assert proc.returncode == 1
    assert "_No unresolved questions._" in proc.stdout


def test_runs_questions_set_run_ledger_unchanged(tmp_path: Path) -> None:
    """E-04: Non-runner targets continue using the workflow-artifacts lookup and exit 1 when empty."""
    repo = _create_test_repo(tmp_path)

    # Create empty open-questions.md in workflow-artifacts
    proj_dir = repo / ".aw" / "workflow-artifacts" / "exec-set" / "test-set-001"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / set_records.OPEN_QUESTIONS_FILE).write_text(
        "_No unresolved questions._\n", encoding="utf-8"
    )

    proc = _run_cli(repo, ["runs", "questions", "test-set-001"])
    assert proc.returncode == 1
    assert "_No unresolved questions._" in proc.stdout
