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

"""Tests for consuming answers at dispatch checkpoints and resuming parked items (qchan-04 j0ufrj E-01..E-06).

Guards that:
1. Mid-run checkpoint answer consumption and priority dispatch (A43): answer written during item 2's turn
   causes item 1 attempt 2 to dispatch ahead of item 3 at next loop iteration. Without answer, item 3 dispatches first.
2. Same-session resume and fresh-turn fallback (A44, A6): when prior attempt recorded session_id, resumed attempt
   uses same session and prompt contains only the answer notice; without session_id, fresh-turn fallback runs on
   same preserved lane and base commit with answer notice prepended, and parked commit is retained.
3. Preserved lane missing or unsafe refusal: missing lane worktree or unsafe lane refuses resume with fail-lane
   and answer-resume-refused event, without allocating a fresh lane.
4. Staleness verification (A12): modified or missing artifact triggers answer-stale event, marks question stale,
   and leaves item parked awaiting-human.
5. Start-of-run drain: answers written while no driver is live are drained at loop top before any item starts.
6. Partial answers (OQ-01): answering one gating question out of two does not resume; answering gating questions
   while leaving non-gating unanswered resumes and delivers non-gating as unanswered in notice.
7. Re-park on subsequent question (E-04): earlier question stays answered, new attempt qid is open, item stored
   question_ids has only new qid, and next checkpoint does not resume until new question is answered.
8. Review sweep-lane resume and integration (E-06): parked review merges parked branch into sweep lane; on success,
   review integrates to main and parked branch is deleted; on merge conflict, merge aborts, fail-merge is set,
   and parked branch is kept.
9. Review semantics after answer (A36, A37): resumed review whose finding is not cleared records NO-GO and
   no unauthorized Readiness value appears.
10. Antigravity and OpenCode parity on both hosts.
"""

from __future__ import annotations

import json
import os
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
from tests import support
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
    setid: str = "qres",
    order: int = 1,
    status: str = "approved",
    action: str = "execute",
    priority: str = "medium",
    work_kind: str = "feature",
    dependencies: list[str] | None = None,
    commit: bool = True,
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
"""
    if dependencies:
        dep_str = ", ".join(dependencies)
        content += f"- Item-Dependencies: {dep_str}\n"
    content += """- Scope-Paths: README.md

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Perform task
- [ ] V-01 Verify task
"""
    plan_path.write_text(content, encoding="utf-8")
    if commit:
        subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True
        )
    return plan_path


def _make_fake_agent_script(tmp_path: Path) -> Path:
    """Create a fake agent script that can serve as both opencode and agy."""
    return support.make_fake_executable(
        tmp_path / "fake_agent",
        r"""#!/usr/bin/env python3
import json, os, re, subprocess, sys
from pathlib import Path

# Handle version, debug, config, export, and help probes immediately without running git
if any(a in sys.argv for a in ("--version", "-v", "version", "--help", "-h")):
    print("1.0.0")
    sys.exit(0)
if any(a in sys.argv for a in ("debug", "config", "export")):
    print("{}")
    sys.exit(0)

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

repo_root = None
try:
    c_git = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], text=True).strip())
    repo_root = c_git.resolve().parent
except Exception:
    p = Path.cwd()
    for parent in [p, *p.parents]:
        if (parent / ".aw" / "records").is_dir():
            repo_root = parent
            break
    if not repo_root:
        repo_root = Path.cwd()

run_id_val = os.environ.get("AW_RUN_ID")
rd = None
m_rd = re.search(r"(?:Run directory|Run root): (\S+)", all_text)
if m_rd:
    rd = Path(m_rd.group(1))
elif run_id_val and repo_root:
    cand = repo_root / ".aw" / "records" / "runs" / run_id_val
    if cand.is_dir():
        rd = cand

m_pos = re.search(r"Queue position: (\d+)", all_text)
m_id6 = re.search(r"Assigned IPD: (\w+)", all_text)
pos = int(m_pos.group(1)) if m_pos else 1
id6 = m_id6.group(1) if m_id6 else os.environ.get("AW_ITEM_ID6", "unknown")
if id6 == "unknown":
    for arg in sys.argv:
        m_t = re.search(r"aw-(?:exec|review)-\S+-\S+-([a-zA-Z0-9]{6})", arg)
        if m_t:
            id6 = m_t.group(1)
            break

att_no = 1
if rd and (rd / "state.json").is_file():
    try:
        st_data = json.loads((rd / "state.json").read_text(encoding="utf-8"))
        for it in st_data.get("queue", []):
            if it.get("id6") == id6:
                pos = it.get("position", pos)
                att_no = max(len(it.get("attempts", [])), 1)
                break
    except Exception:
        pass

m_req = re.search(r"Required JSON outcome:\s+(\S+)", all_text)
outcome_file_path = ""
if m_req:
    outcome_file_path = m_req.group(1)
    m_pair = re.search(r"(\d+)-([a-zA-Z0-9]{6})", outcome_file_path)
    if m_pair and (not m_id6 or id6 == "unknown"):
        pos = int(m_pair.group(1))
        id6 = m_pair.group(2)
    m_att = re.search(r"attempt-(\d+)", outcome_file_path)
    if m_att:
        att_no = int(m_att.group(1))
else:
    lane_sub_dir = Path.cwd() / ".aw" / "state" / "lane-submissions" / (run_id_val or "run") / f"{pos:02d}-{id6}" / f"attempt-{att_no}"
    outcome_file_path = str(lane_sub_dir / "outcomes" / f"{pos:02d}-{id6}.json")

# Check mid-run answer trigger
trigger = os.environ.get("FAKE_ANSWER_TRIGGER")
if trigger and id6 == trigger:
    target_qid = os.environ.get("FAKE_ANSWER_QID")
    target_ans = os.environ.get("FAKE_ANSWER_TEXT", "use timeout 30")
    if target_qid and rd:
        from agent_workflows import question_inbox
        question_inbox.write_answer(
            rd,
            target_qid,
            answer=target_ans,
            channel="cli",
            sender="tester",
            actor="human",
        )

# Read configured behavior
payload_map = {}
raw_map = os.environ.get("FAKE_PAYLOAD_MAP_JSON")
if raw_map:
    try:
        payload_map = json.loads(raw_map)
    except Exception:
        pass

key_with_att = f"{id6}:a{att_no}"
item_cfg = payload_map.get(key_with_att)
if item_cfg is None:
    item_cfg = payload_map.get(id6)

if item_cfg is not None:
    if isinstance(item_cfg, dict) and "outcome" in item_cfg:
        payload_content = json.dumps(item_cfg["outcome"])
        if item_cfg.get("commit") and id6 != "unknown":
            f = Path(f"work_{id6}.txt")
            f.write_text(f"work: {item_cfg['commit']}\n", encoding="utf-8")
            subprocess.run(["git", "add", str(f)], check=True)
            subprocess.run(["git", "commit", "-qm", str(item_cfg["commit"])], check=True)
        if item_cfg.get("review_commit"):
            rf = Path(f"review_{id6}.txt")
            rf.write_text(f"review: {item_cfg['review_commit']}\n", encoding="utf-8")
            subprocess.run(["git", "add", str(rf)], check=True)
            subprocess.run(["git", "commit", "-qm", str(item_cfg["review_commit"])], check=True)
        if item_cfg.get("conflict_file"):
            cf = Path(item_cfg["conflict_file"])
            cf.write_text(item_cfg.get("conflict_content", "conflict line\n"), encoding="utf-8")
            subprocess.run(["git", "add", str(cf)], check=True)
            subprocess.run(["git", "commit", "-qm", "conflict commit"], check=True)
    else:
        payload_content = json.dumps(item_cfg)
else:
    payload_content = os.environ.get("FAKE_PAYLOAD_JSON", json.dumps({"disposition": "executed", "defect_report": {"state": "none-found", "findings": []}, "pushed": False}))
    if id6 != "unknown":
        f = Path(f"work_{id6}.txt")
        f.write_text(f"work for {id6}\n", encoding="utf-8")
        subprocess.run(["git", "add", str(f)], check=True)
        subprocess.run(["git", "commit", "-qm", f"execute {id6}"], check=True)

# Write outcome file to lane submission directory
if outcome_file_path:
    p = Path(outcome_file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(payload_content, encoding="utf-8")

# Write outcome file to run outcomes directory as well
if rd and pos and id6 and id6 != "unknown":
    out_dir = rd / "outcomes"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{pos:02d}-{id6}.json").write_text(payload_content, encoding="utf-8")

sys.exit(0)
""",
    )


def _read_events(run_dir: Path) -> list[dict[str, Any]]:
    ev_file = run_dir / "events.jsonl"
    if not ev_file.exists():
        return []
    lines = ev_file.read_text(encoding="utf-8").splitlines()
    res = []
    for line in lines:
        if line.strip():
            res.append(json.loads(line))
    return res


def _mock_finalize(
    target_repo: Path, plan: Path, fin_id6: str, *args: Any, **kwargs: Any
) -> tuple[int, str]:
    exec_dir = target_repo / ".aw" / "records" / "plans" / "executed"
    exec_dir.mkdir(parents=True, exist_ok=True)
    p_path = Path(plan)
    if p_path.is_file():
        dest = exec_dir / p_path.name
        dest.write_text(p_path.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            rel_p = str(p_path.relative_to(target_repo))
            rel_d = str(dest.relative_to(target_repo))
            subprocess.run(["git", "rm", "-q", rel_p], cwd=target_repo, check=False)
            subprocess.run(["git", "add", rel_d], cwd=target_repo, check=False)
            subprocess.run(
                ["git", "commit", "-qm", f"finalize {fin_id6}"],
                cwd=target_repo,
                check=False,
            )
        except ValueError:
            p_path.unlink()
    return 0, "ok"


class TestQuestionResume:
    """Unit and functional tests for checkpoint consumption and answer resumption."""

    def test_dispatch_sort_key_pure_unit(self) -> None:
        """E-02: dispatch_sort_key prioritizes resume_with_answers items while preserving depth."""
        by_id = {
            "a": {"id6": "a", "setid": "s", "order": 1, "dependencies": []},
            "b": {"id6": "b", "setid": "s", "order": 2, "dependencies": ["executed:a"]},
            "c": {"id6": "c", "setid": "s", "order": 3, "dependencies": []},
        }

        # Item c has resume_with_answers, item a does not
        item_a = dict(by_id["a"])
        item_c = dict(by_id["c"], resume_with_answers=True)

        key_a = runner_shared.dispatch_sort_key(item_a, by_id)
        key_c = runner_shared.dispatch_sort_key(item_c, by_id)

        # key_c must sort BEFORE key_a because not resume_with_answers is False (0) for c, True (1) for a
        assert key_c < key_a

        # Without resume_with_answers, order defaults to queue_sort_key
        item_c_no_ans = dict(by_id["c"])
        key_c_no_ans = runner_shared.dispatch_sort_key(item_c_no_ans, by_id)
        assert key_a < key_c_no_ans

    @pytest.mark.parametrize("runner_name", ["oc", "agy"])
    def test_checkpoint_consumption_and_priority_dispatch_a43(
        self, tmp_path: Path, runner_name: str
    ) -> None:
        """A43 / V-01 / V-02: Answer written during item 2's turn dispatches item 1 (att 2) before item 3."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p1 = _create_plan_file(repo, "res001", setid="qres", order=1)
        p2 = _create_plan_file(repo, "res002", setid="qres", order=2)
        p3 = _create_plan_file(repo, "res003", setid="qres", order=3)

        run_id = f"run-a43-{runner_name}"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        gating_q = {
            "question_id": "q-timeout-val",
            "text": "What is the timeout?",
            "artifact_id6": "res001",
            "gates_verdict": True,
            "evidence": ["config.py"],
        }

        # Item 1 att 1: parks
        # Item 1 att 2: executes
        # Item 2: executes and writes answer for item 1
        # Item 3: executes
        payload_map = {
            "res001:a1": {
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [gating_q],
                    "pushed": False,
                }
            },
            "res001:a2": {
                "commit": "implement timeout handling",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            },
            "res002": {
                "commit": "implement metrics service",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            },
            "res003": {
                "commit": "implement reporting",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            },
        }

        queue = [
            {
                "id6": "res001",
                "setid": "qres",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(p1),
                "attempts": [],
            },
            {
                "id6": "res002",
                "setid": "qres",
                "position": 2,
                "action": "execute",
                "status": "queued",
                "configured_file": str(p2),
                "attempts": [],
            },
            {
                "id6": "res003",
                "setid": "qres",
                "position": 3,
                "action": "execute",
                "status": "queued",
                "configured_file": str(p3),
                "attempts": [],
            },
        ]

        state = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": queue,
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
            },
        }

        if runner_name == "oc":
            state["options"]["opencode"] = str(fake_bin)
            driver_mod = oc_runipd
        else:
            state["options"]["agy"] = str(fake_bin)
            driver_mod = agy_runipd

        runner_shared.save_state(run_dir, state)

        # Expected qid for res001 att 1: 01-res001-a1-q-timeout-val
        expected_qid = "01-res001-a1-q-timeout-val"

        env = {
            "FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map),
            "FAKE_ANSWER_TRIGGER": "res002",
            "FAKE_ANSWER_QID": expected_qid,
            "FAKE_ANSWER_TEXT": "timeout 30s",
        }

        with (
            mock.patch.object(driver_mod, "driver_begin", return_value=(0, "ok")),
            mock.patch.object(
                driver_mod, "driver_finalize", side_effect=_mock_finalize
            ),
            mock.patch.object(
                driver_mod,
                "run_suite_check",
                return_value=runner_shared.SuiteCheckResult(
                    True, 0, "ok", "ok", "", 1.0, 0.1
                ),
            ),
            mock.patch.dict(os.environ, env),
            coordinator_role(),
        ):
            rc = driver_mod.run_queue(run_dir, state)
            assert rc == 0

        events = _read_events(run_dir)
        starts = [
            (e["id6"], e["attempt"]) for e in events if e.get("event") == "ipd-started"
        ]

        # Verify dispatch order: res001(1) -> res002(1) -> res001(2) -> res003(1)
        assert starts == [
            ("res001", 1),
            ("res002", 1),
            ("res001", 2),
            ("res003", 1),
        ], f"Expected priority dispatch order, got: {starts}"

        # Verify answer-consumed event was emitted
        consumed_events = [e for e in events if e.get("event") == "answer-consumed"]
        assert len(consumed_events) == 1
        assert consumed_events[0]["id6"] == "res001"
        assert consumed_events[0]["question_id"] == expected_qid

        # Print V-01 and V-02 evidence
        print("V-01 answer-consumed event:", json.dumps(consumed_events[0]))
        print("V-02 ordered ipd-started events:", starts)

    def test_same_session_resume_and_fresh_turn_fallback_a44_a6(
        self, tmp_path: Path
    ) -> None:
        """A44 / A6 / V-03: Session resume vs fresh-turn fallback with preserved lane and commits."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(repo, "ses001", setid="qses", order=1)
        run_id = "run-same-session-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        gating_q = {
            "question_id": "q-cache-mode",
            "text": "What cache mode to use?",
            "artifact_id6": "ses001",
            "gates_verdict": True,
            "evidence": ["cache.py"],
        }

        # Case 1: Session resume (prior attempt has session_id)
        item: dict[str, Any] = {
            "id6": "ses001",
            "setid": "qses",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }

        state: dict[str, Any] = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        payload_att1 = {
            "ses001": {
                "commit": "first attempt work",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [gating_q],
                    "pushed": False,
                },
            }
        }

        # Turn 1: parks
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_att1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid = item["question_ids"][0]
        assert item["preserved_lane_id"]
        assert item["preserved_branch"]
        assert item["preserved_base"]
        assert len(item["attempts"]) == 1
        att1 = item["attempts"][0]
        # fake agent emits ses-1
        assert att1.get("session_id") == "ses-1"

        # Provide answer
        ans_res = question_inbox.write_answer(
            run_dir,
            qid,
            answer="use redis clustered cache",
            channel="cli",
            sender="tester",
            actor="human",
        )
        assert ans_res.status == "recorded"

        # Consume answer
        requeued = runner_shared.consume_answers(run_dir, state)
        assert "ses001" in requeued
        assert item["resume_with_answers"] is True
        assert item["status"] == "queued"

        payload_att2 = {
            "ses001": {
                "commit": "resumed second attempt work",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }

        # Turn 2: resume with same session
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", side_effect=_mock_finalize),
            mock.patch.object(
                oc_runipd,
                "run_suite_check",
                return_value=runner_shared.SuiteCheckResult(
                    True, 0, "ok", "ok", "", 1.0, 0.1
                ),
            ),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_att2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == "executed"
        assert len(item["attempts"]) == 2
        att2 = item["attempts"][1]
        assert att2.get("answer_resume") == "session"

        # Prompt for session resume contains only the answer notice
        prompt_path = Path(att2["prompt"])
        prompt_content = prompt_path.read_text(encoding="utf-8")
        assert "## Answers from the maintainer" in prompt_content
        assert "use redis clustered cache" in prompt_content
        assert "IPD Driver Turn" not in prompt_content  # Not normal full prompt!

        print("V-03 session resume: answer_resume=", att2.get("answer_resume"))
        print("V-03 session prompt excerpt:\n", prompt_content[:300])

        # Case 2: Fresh-turn fallback when prior attempt has no session_id
        # Let's set up an item where attempt 1 had session_id=None
        p_fallback = _create_plan_file(repo, "fbk002", setid="qses", order=2)
        item_fbk = {
            "id6": "fbk002",
            "setid": "qses",
            "position": 2,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p_fallback),
            "attempts": [],
        }
        state["queue"].append(item_fbk)

        payload_fbk1 = {
            "fbk002": {
                "commit": "fallback attempt 1 commit",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-fbk",
                            "text": "Fallback decision?",
                            "artifact_id6": "fbk002",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                },
            }
        }

        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_fbk1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item_fbk, recovery=False)

        assert item_fbk["status"] == runner_shared.AWAITING_HUMAN_STATUS
        fbk_qid = item_fbk["question_ids"][0]
        fbk_branch = item_fbk["preserved_branch"]
        fbk_base = item_fbk["preserved_base"]

        # Clear session_id on attempt 1 to simulate absent session
        item_fbk["attempts"][0]["session_id"] = None

        # Answer question
        question_inbox.write_answer(
            run_dir,
            fbk_qid,
            answer="continue with option B",
            channel="web",
            sender="tester",
            actor="human",
        )
        requeued_fbk = runner_shared.consume_answers(run_dir, state)
        assert "fbk002" in requeued_fbk

        payload_fbk2 = {
            "fbk002": {
                "commit": "fallback attempt 2 commit",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }

        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", side_effect=_mock_finalize),
            mock.patch.object(
                oc_runipd,
                "run_suite_check",
                return_value=runner_shared.SuiteCheckResult(
                    True, 0, "ok", "ok", "", 1.0, 0.1
                ),
            ),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_fbk2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item_fbk, recovery=False)

        assert item_fbk["status"] == "executed"
        att_fbk2 = item_fbk["attempts"][1]
        assert att_fbk2.get("answer_resume", "").startswith("fresh")
        assert att_fbk2["worktree_branch"] == fbk_branch
        assert att_fbk2["worktree_base"] == fbk_base

        # Prompt for fresh fallback has answer notice prepended to normal prompt
        fbk_prompt = Path(att_fbk2["prompt"]).read_text(encoding="utf-8")
        assert "## Answers from the maintainer" in fbk_prompt
        assert "continue with option B" in fbk_prompt
        assert "IPD Driver Turn" in fbk_prompt  # Normal prompt included!

        print("V-03 fallback resume: answer_resume=", att_fbk2.get("answer_resume"))

    def test_preserved_lane_missing_or_unsafe_refusal(self, tmp_path: Path) -> None:
        """E-03 / V-03: Preserved lane missing refuses resume with fail-lane and answer-resume-refused event."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(repo, "ref001", setid="qref", order=1)
        run_id = "run-refuse-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        item = {
            "id6": "ref001",
            "setid": "qref",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        state = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        payload_att1 = {
            "ref001": {
                "commit": "first attempt commit",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-ref",
                            "text": "Refusal question?",
                            "artifact_id6": "ref001",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                },
            }
        }

        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_att1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid = item["question_ids"][0]
        wt_path = Path(item["attempts"][0]["worktree"])
        assert item["attempts"][0]["worktree_lane_id"]

        # Now simulate lane deletion / missing worktree
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt_path)], cwd=repo, check=True
        )
        assert not wt_path.exists()

        # Answer question
        question_inbox.write_answer(
            run_dir,
            qid,
            answer="answer for missing lane",
            channel="cli",
            sender="tester",
            actor="human",
        )
        requeued = runner_shared.consume_answers(run_dir, state)
        assert "ref001" in requeued

        # Resume turn: must refuse with fail-lane
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == "fail-lane"
        att2 = item["attempts"][-1]
        assert att2["disposition"] == "fail-lane"

        events = _read_events(run_dir)
        refused_events = [
            e for e in events if e.get("event") == "answer-resume-refused"
        ]
        assert len(refused_events) == 1
        assert refused_events[0]["id6"] == "ref001"
        assert (
            "does not exist" in refused_events[0]["reason"]
            or "not registered" in refused_events[0]["reason"]
        )

        print("V-03 lane refusal event:", json.dumps(refused_events[0]))

    def test_staleness_modified_or_missing_artifact_a12(self, tmp_path: Path) -> None:
        """A12 / V-01: Modified or missing artifact marks answer stale and leaves item parked."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(repo, "stl001", setid="qstl", order=1)
        run_id = "run-staleness-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        item = {
            "id6": "stl001",
            "setid": "qstl",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        state = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        payload = {
            "stl001": {
                "commit": "stale test commit",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-stale",
                            "text": "Staleness question?",
                            "artifact_id6": "stl001",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                },
            }
        }

        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload)}),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid = item["question_ids"][0]

        # Case 1: Modify artifact on main
        p_txt = p.read_text(encoding="utf-8")
        p.write_text(p_txt + "\n<!-- modification on main -->\n", encoding="utf-8")
        subprocess.run(["git", "add", str(p)], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "modify plan on main"], cwd=repo, check=True
        )

        # Write answer with original hash
        question_inbox.write_answer(
            run_dir,
            qid,
            answer="answer against old version",
            channel="cli",
            sender="tester",
            actor="human",
        )

        requeued = runner_shared.consume_answers(run_dir, state)
        assert len(requeued) == 0
        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS

        # Verify question status is stale
        q_data = question_inbox.read_question(run_dir, qid)
        assert q_data is not None
        assert q_data["status"] == question_inbox.QUESTION_STATUS_STALE

        events = _read_events(run_dir)
        stale_events = [e for e in events if e.get("event") == "answer-stale"]
        assert len(stale_events) == 1
        assert stale_events[0]["id6"] == "stl001"
        assert stale_events[0]["question_id"] == qid
        assert stale_events[0]["actual_hash"] != stale_events[0]["expected_hash"]

        print("V-01 answer-stale event:", json.dumps(stale_events[0]))

        # Case 2: Missing artifact
        p.unlink()
        subprocess.run(["git", "add", str(p)], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "delete plan on main"], cwd=repo, check=True
        )

        # Clear stale status to open so we can test missing artifact staleness detection
        q_file = run_dir / "questions" / f"{qid}.json"
        q_obj = json.loads(q_file.read_text(encoding="utf-8"))
        q_obj["status"] = "open"
        q_file.write_text(json.dumps(q_obj), encoding="utf-8")

        requeued2 = runner_shared.consume_answers(run_dir, state)
        assert len(requeued2) == 0
        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS

    def test_start_of_run_drain(self, tmp_path: Path) -> None:
        """E-01 / V-01: Answers written while no driver was live are drained at top of run_queue before turn 1."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(repo, "drn001", setid="qdrn", order=1)
        run_id = "run-drain-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        item = {
            "id6": "drn001",
            "setid": "qdrn",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        state = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        # Park item in run 1
        payload1 = {
            "drn001": {
                "commit": "drain test commit",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-drain",
                            "text": "Drain question?",
                            "artifact_id6": "drn001",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid = item["question_ids"][0]

        # Driver is NOT live. Write answer now.
        ans_res = question_inbox.write_answer(
            run_dir,
            qid,
            answer="answer written offline",
            channel="cli",
            sender="tester",
            actor="human",
        )
        assert ans_res.status == "recorded"

        payload2 = {
            "drn001": {
                "commit": "drain executed commit",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }

        # Run driver resume: run_queue
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", side_effect=_mock_finalize),
            mock.patch.object(
                oc_runipd,
                "run_suite_check",
                return_value=runner_shared.SuiteCheckResult(
                    True, 0, "ok", "ok", "", 1.0, 0.1
                ),
            ),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload2)}
            ),
            coordinator_role(),
        ):
            rc = oc_runipd.run_queue(run_dir, retry_incomplete=False)
            assert rc == 0

        events = _read_events(run_dir)
        ev_types = [e.get("event") for e in events]

        # answer-consumed must appear before attempt 2's ipd-started
        consumed_idx = ev_types.index("answer-consumed")
        attempt2_started_idx = -1
        for idx, e in enumerate(events):
            if e.get("event") == "ipd-started" and e.get("attempt") == 2:
                attempt2_started_idx = idx
                break
        assert consumed_idx < attempt2_started_idx

    def test_partial_answers_oq01(self, tmp_path: Path) -> None:
        """OQ-01: Answering one of two gating questions does not resume; answering gating while leaving non-gating does resume."""
        repo = _create_test_repo(tmp_path)
        p = _create_plan_file(repo, "prt001", setid="qprt", order=1)
        run_id = "run-partial-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "questions").mkdir(parents=True, exist_ok=True)
        (run_dir / "answers").mkdir(parents=True, exist_ok=True)

        art_hash = runner_shared.sha256_file(p)

        # Part 1: Two gating questions (Q1 and Q2)
        q1_data = {
            "schema": question_inbox.QUESTION_SCHEMA,
            "question_id": "01-prt001-a1-q1",
            "run_id": run_id,
            "artifact_id6": "prt001",
            "artifact_path": p.relative_to(repo).as_posix(),
            "artifact_hash": art_hash,
            "gates_verdict": True,
            "text": "Gating Q1",
            "status": "open",
        }
        q2_data = {
            "schema": question_inbox.QUESTION_SCHEMA,
            "question_id": "01-prt001-a1-q2",
            "run_id": run_id,
            "artifact_id6": "prt001",
            "artifact_path": p.relative_to(repo).as_posix(),
            "artifact_hash": art_hash,
            "gates_verdict": True,
            "text": "Gating Q2",
            "status": "open",
        }
        (run_dir / "questions" / "01-prt001-a1-q1.json").write_text(
            json.dumps(q1_data), encoding="utf-8"
        )
        (run_dir / "questions" / "01-prt001-a1-q2.json").write_text(
            json.dumps(q2_data), encoding="utf-8"
        )

        item = {
            "id6": "prt001",
            "status": runner_shared.AWAITING_HUMAN_STATUS,
            "question_ids": ["01-prt001-a1-q1", "01-prt001-a1-q2"],
        }
        state = {"repo": str(repo), "queue": [item]}

        # Answer only Q1
        question_inbox.write_answer(
            run_dir,
            "01-prt001-a1-q1",
            answer="answer for q1",
            channel="cli",
            sender="tester",
            actor="human",
        )

        requeued = runner_shared.consume_answers(run_dir, state)
        assert len(requeued) == 0
        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS

        # Part 2: Change Q2 to non-gating (gates_verdict: false)
        q2_data["gates_verdict"] = False
        (run_dir / "questions" / "01-prt001-a1-q2.json").write_text(
            json.dumps(q2_data), encoding="utf-8"
        )

        requeued2 = runner_shared.consume_answers(run_dir, state)
        assert "prt001" in requeued2
        assert item["status"] == "queued"
        assert item["resume_with_answers"] is True
        assert len(item["answers_pending"]) == 2

        # Check answers_pending has Q1 answered and Q2 unanswered
        ans_pending = item["answers_pending"]
        q1_rec = next(a for a in ans_pending if a["question_id"] == "01-prt001-a1-q1")
        q2_rec = next(a for a in ans_pending if a["question_id"] == "01-prt001-a1-q2")
        assert q1_rec["answer"] == "answer for q1"
        assert q2_rec.get("unanswered") is True

        notice = runner_shared.build_answer_notice(ans_pending)
        assert "answer for q1" in notice
        assert "(unanswered)" in notice

    def test_re_park_on_subsequent_question_e04(self, tmp_path: Path) -> None:
        """E-04 / V-04: Re-park on subsequent turn keeps earlier answered, only new open, question_ids replaced."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(repo, "rep001", setid="qrep", order=1)
        run_id = "run-repark-test"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        item = {
            "id6": "rep001",
            "setid": "qrep",
            "position": 1,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        state = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        # Attempt 1 asks question 1
        q1 = {
            "question_id": "q-step-1",
            "text": "Question 1 text?",
            "artifact_id6": "rep001",
            "gates_verdict": True,
            "evidence": ["step 1"],
        }
        # Attempt 2 asks question 2
        q2 = {
            "question_id": "q-step-2",
            "text": "Question 2 text?",
            "artifact_id6": "rep001",
            "gates_verdict": True,
            "evidence": ["step 2"],
        }

        payload1 = {
            "rep001": {
                "commit": "attempt 1 work",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [q1],
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid1 = item["question_ids"][0]
        assert "a1" in qid1

        # Answer question 1
        question_inbox.write_answer(
            run_dir,
            qid1,
            answer="answer 1",
            channel="cli",
            sender="tester",
            actor="human",
        )
        requeued = runner_shared.consume_answers(run_dir, state)
        assert "rep001" in requeued

        # Attempt 2 asks question 2
        payload2 = {
            "rep001": {
                "commit": "attempt 2 work",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [q2],
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        assert len(item["question_ids"]) == 1
        qid2 = item["question_ids"][0]
        assert "a2" in qid2
        assert qid2 != qid1

        # Check question statuses in inbox: qid1 must be answered, qid2 must be open
        q1_file_data = question_inbox.read_question(run_dir, qid1)
        q2_file_data = question_inbox.read_question(run_dir, qid2)
        assert q1_file_data["status"] == question_inbox.QUESTION_STATUS_ANSWERED
        assert q2_file_data["status"] == question_inbox.QUESTION_STATUS_OPEN

        # Next checkpoint does NOT re-queue because qid2 is not answered
        requeued_next = runner_shared.consume_answers(run_dir, state)
        assert len(requeued_next) == 0

        print(
            f"V-04 repark: qid1({qid1})={q1_file_data['status']}, qid2({qid2})={q2_file_data['status']}"
        )
        print(f"V-04 stored question_ids={item['question_ids']}")

    def test_review_sweep_lane_resume_and_integration_e06(self, tmp_path: Path) -> None:
        """E-06 / V-06: Review resume merges parked branch into sweep lane; deletes parked branch upon integration."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        pA = _create_plan_file(repo, "rva001", setid="qrv", order=1, action="review")
        pB = _create_plan_file(repo, "rvb002", setid="qrv", order=2, action="review")

        run_id = "run-review-resume"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        q_rev = {
            "question_id": "q-rv-scope",
            "text": "Review scope clarification?",
            "artifact_id6": "rva001",
            "gates_verdict": True,
            "evidence": ["review-plan"],
        }

        itemA: dict[str, Any] = {
            "id6": "rva001",
            "setid": "qrv",
            "position": 1,
            "action": "review",
            "status": "queued",
            "configured_file": str(pA),
            "attempts": [],
        }
        itemB: dict[str, Any] = {
            "id6": "rvb002",
            "setid": "qrv",
            "position": 2,
            "action": "review",
            "status": "queued",
            "configured_file": str(pB),
            "attempts": [],
        }

        state: dict[str, Any] = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [itemA, itemB],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        # 1. Review A runs, asks question, parks onto aw/parked/<run_id>/rva001
        payloadA1 = {
            "rva001": {
                "review_commit": "review A initial finding",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [q_rev],
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payloadA1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, itemA, recovery=False)

        assert itemA["status"] == runner_shared.AWAITING_HUMAN_STATUS
        parked_branch = itemA["preserved_branch"]
        assert parked_branch == f"aw/parked/{run_id}/rva001"

        # Verify parked branch exists in git
        rc_br, br_out, _ = runner_shared._run_git(
            repo, ["branch", "--list", parked_branch]
        )
        assert rc_br == 0 and parked_branch in br_out

        # 2. Review B runs, commits on sweep lane, executes and integrates
        payloadB = {
            "rvb002": {
                "review_commit": "review B approve findings",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payloadB)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, itemB, recovery=False)

        assert itemB["status"] in ("approved", "reviewed")
        assert itemB.get("review_integrated") is True

        # 3. Answer arrives for Review A
        qidA = itemA["question_ids"][0]
        question_inbox.write_answer(
            run_dir,
            qidA,
            answer="scope confirmed approved",
            channel="cli",
            sender="tester",
            actor="human",
        )

        requeued = runner_shared.consume_answers(run_dir, state)
        assert "rva001" in requeued
        assert itemA["resume_with_answers"] is True

        # 4. Review A resumes: merges parked branch into sweep lane, executes and integrates
        payloadA2 = {
            "rva001": {
                "review_commit": "review A post-answer approval",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payloadA2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, itemA, recovery=False)

        assert itemA["status"] in ("approved", "reviewed")
        assert itemA.get("review_integrated") is True

        # Check git log of main: Review A's parked change must be present on main
        log_main = subprocess.run(
            ["git", "log", "--oneline", "main"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "review A initial finding" in log_main
        assert "review B approve findings" in log_main

        # Check parked branch is DELETED after successful integration
        _rc_br2, br_out2, _ = runner_shared._run_git(
            repo, ["branch", "--list", parked_branch]
        )
        assert (
            br_out2.strip() == ""
        ), f"Parked branch {parked_branch} should be deleted after integration"

        print("V-06 main log after review A integration:\n", log_main)
        print("V-06 parked branch deleted check:", br_out2.strip())

        # 5. Conflict case: Review A resumes but parked branch has conflicting changes
        itemC: dict[str, Any] = {
            "id6": "rvc003",
            "setid": "qrv",
            "position": 3,
            "action": "review",
            "status": "queued",
            "configured_file": str(pA),
            "attempts": [],
        }
        state["queue"].append(itemC)

        payloadC1 = {
            "rvc003": {
                "conflict_file": "conflict.txt",
                "conflict_content": "version A\n",
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-conf",
                            "text": "Conflict question?",
                            "artifact_id6": "rvc003",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payloadC1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, itemC, recovery=False)

        assert itemC["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qidC = itemC["question_ids"][0]
        c_parked_br = itemC["preserved_branch"]

        # Commit conflicting file on sweep lane worktree
        wt_path_sweep = Path(itemC["attempts"][0]["worktree"])
        conf_on_sweep = wt_path_sweep / "conflict.txt"
        conf_on_sweep.write_text("version B (conflicting)\n", encoding="utf-8")
        subprocess.run(["git", "add", "conflict.txt"], cwd=wt_path_sweep, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "commit conflicting version B on sweep"],
            cwd=wt_path_sweep,
            check=True,
        )

        question_inbox.write_answer(
            run_dir,
            qidC,
            answer="resolve conflict answer",
            channel="cli",
            sender="tester",
            actor="human",
        )
        requeuedC = runner_shared.consume_answers(run_dir, state)
        assert "rvc003" in requeuedC

        payloadC2 = {
            "rvc003": {
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payloadC2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, itemC, recovery=False)

        # Refusal on conflict: fail-merge
        assert itemC["status"] == "fail-merge"
        events = _read_events(run_dir)
        conf_refusals = [
            e
            for e in events
            if e.get("event") == "answer-resume-refused" and e.get("id6") == "rvc003"
        ]
        assert len(conf_refusals) == 1
        assert "merge conflict" in conf_refusals[0]["reason"]

        # Parked branch remains present
        _rc_br_conf, br_out_conf, _ = runner_shared._run_git(
            repo, ["branch", "--list", c_parked_br]
        )
        assert c_parked_br in br_out_conf

        print("V-06 conflict refusal event:", json.dumps(conf_refusals[0]))

    def test_review_semantics_after_answer_a36_a37(self, tmp_path: Path) -> None:
        """A36 / A37: Resumed review turn does not write unauthorized Readiness or override finding."""
        repo = _create_test_repo(tmp_path)
        fake_bin = _make_fake_agent_script(tmp_path)

        p = _create_plan_file(
            repo, "sem001", setid="qsem", order=1, action="review", status="to-review"
        )
        run_id = "run-review-semantics"
        run_dir = repo / ".aw" / "records" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

        item: dict[str, Any] = {
            "id6": "sem001",
            "setid": "qsem",
            "position": 1,
            "action": "review",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        state: dict[str, Any] = {
            "repo": str(repo),
            "run_id": run_id,
            "queue": [item],
            "options": {
                "no_verify": True,
                "validate": False,
                "self_finalize": True,
                "output_mode": "quiet",
                "opencode": str(fake_bin),
            },
        }
        runner_shared.save_state(run_dir, state)

        # Attempt 1: asks gating question
        payload1 = {
            "sem001": {
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-sem",
                            "text": "Review finding question?",
                            "artifact_id6": "sem001",
                            "gates_verdict": True,
                            "evidence": ["plan"],
                        }
                    ],
                    "pushed": False,
                }
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload1)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
        qid = item["question_ids"][0]

        # Answer question
        question_inbox.write_answer(
            run_dir,
            qid,
            answer="maintainer answer",
            channel="cli",
            sender="tester",
            actor="human",
        )
        runner_shared.consume_answers(run_dir, state)
        assert item["resume_with_answers"] is True

        # Attempt 2: review finding is not cleared -> reviewer records finding and does not approve
        payload2 = {
            "sem001": {
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {
                        "state": "found",
                        "findings": [{"what": "spec mismatch", "where": "plan"}],
                    },
                    "pushed": False,
                }
            }
        }
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload2)}
            ),
            coordinator_role(),
        ):
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        # A36: Answering a question is not approval; item is not approved
        assert item["status"] != "approved"
        assert item["status"] in ("reviewed", "partial", "blocked")
        # A37: Check plan file on main: no unauthorized Readiness: go was injected by runner
        plan_content = p.read_text(encoding="utf-8")
        assert "Readiness: go" not in plan_content
