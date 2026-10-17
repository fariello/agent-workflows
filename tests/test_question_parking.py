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

"""Tests for non-terminal question parking and queue continuation (qchan-02 epsti7 E-01..E-06).

Guards that:
1. Status vocabulary: awaiting-human is known, non-terminal, absent from all success sets on both hosts,
   and maps to run_state.STATE_BLOCKED (A32, V-01).
2. Execute turn parking: turn returning gating question parks non-terminally (awaiting-human), preserves lane
   with reason RETENTION_AWAITING_HUMAN, leaves main untouched, leaves commits on lane branch, and emits no
   verifier or finalize events (A3, A5, V-02). Non-gating questions do not park.
3. 10-item queue continuation: item 3 parks, independent items execute, dependents wait non-terminally in
   queued with awaiting_upstream naming the upstream question, nothing fail-depend (A4, A7, V-03).
4. Drain exit codes & summary: queue drained only by parked questions exits 3 and prints summary line
   'N item(s) parked awaiting answers; M waiting on them'; run with parked + independent fail-gate still
   exits 3 (A8, A38, V-04).
5. Review sweep-lane park: shared sweep lane parks gating review turn onto aw/parked/<run_id>/<id6>, resets
   sweep lane hard to review_lane_tip_before, leaves sweep lane clean, subsequent review merges earlier
   deferred review + its own commit to main, and parked review is absent from main (A13, A15, E-06, V-06).
   Refuses to park safely when sweep lane tip is not a descendant.
6. Antigravity parity: agy runner parks identically without permission config (A15, A39).
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    lane_containment,
    lifecycle_style,
    oc_runipd,
    run_state,
    runner_shared,
    runner_shutdown,
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
    setid: str = "qtest",
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

# Handle version and help probes immediately without running git
if any(a in sys.argv for a in ("--version", "-v", "version", "--help", "-h")):
    print("1.0.0")
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

m_pos = re.search(r"Queue position: (\d+)", all_text)
m_id6 = re.search(r"Assigned IPD: (\w+)", all_text)
m_rd = re.search(r"(?:Run directory|Run root): (\S+)", all_text)
pos = int(m_pos.group(1)) if m_pos else 1
id6 = m_id6.group(1) if m_id6 else "unknown"

m_req = re.search(r"Required JSON outcome:\s+(\S+)", all_text)
if m_req:
    outcome_file_path = m_req.group(1)
    m_pair = re.search(r"(\d+)-([a-zA-Z0-9]{6})", outcome_file_path)
    if m_pair and (not m_id6 or id6 == "unknown"):
        pos = int(m_pair.group(1))
        id6 = m_pair.group(2)

# Read configured behavior
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
            f.write_text(f"work: {item_cfg['commit']}\n", encoding="utf-8")
            subprocess.run(["git", "add", str(f)], check=True)
            subprocess.run(["git", "commit", "-qm", str(item_cfg["commit"])], check=True)
        if item_cfg.get("dirty_file"):
            dp = Path(item_cfg["dirty_file"])
            dp.parent.mkdir(parents=True, exist_ok=True)
            dp.write_text(f"dirty work for {id6}\n", encoding="utf-8")
        if item_cfg.get("commit_plan_edit"):
            p_file = Path(f".aw/records/plans/pending/20261017-revq-{pos:02d}-{id6}-plan.ipd.md")
            if p_file.is_file():
                txt = p_file.read_text(encoding="utf-8")
                txt += "\n- Readiness: ready-for-gate\n"
                p_file.write_text(txt, encoding="utf-8")
                subprocess.run(["git", "add", str(p_file)], check=True)
                subprocess.run(["git", "commit", "-qm", f"edit plan {id6}"], check=True)
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
if all_text and m_req:
    p = Path(m_req.group(1))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(payload_content, encoding="utf-8")

# Write outcome file to run outcomes directory as well
if m_rd and pos and id6 and id6 != "unknown":
    rd = Path(m_rd.group(1))
    out_dir = rd / "outcomes"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{pos:02d}-{id6}.json").write_text(payload_content, encoding="utf-8")
elif m_req and pos and id6 and id6 != "unknown":
    m_run_id = re.search(r"lane-submissions/([^/]+)/", outcome_file_path)
    if m_run_id:
        out_dir = Path(".aw/records/runs") / m_run_id.group(1) / "outcomes"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{pos:02d}-{id6}.json").write_text(payload_content, encoding="utf-8")

# Handle plan file status updates on executed / reviewed
try:
    data = json.loads(payload_content)
    if data.get("disposition") == "executed" and m_id6:
        m_plan = re.search(r"Plan file at launch: (\S+)", all_text)
        if m_plan:
            pf = Path(m_plan.group(1))
            if pf.is_file() and "pending" in pf.parts:
                exec_dir = pf.parent.parent / "executed"
                exec_dir.mkdir(parents=True, exist_ok=True)
                pf.rename(exec_dir / pf.name)
    elif data.get("disposition") == "reviewed" and data.get("verdict") and "APPROVE" in data.get("verdict", ""):
        m_plan = re.search(r"Plan file at launch: (\S+)", all_text)
        if m_plan:
            pf = Path(m_plan.group(1))
            if pf.is_file():
                t = pf.read_text(encoding="utf-8")
                t = t.replace("- Status: to-review", "- Status: reviewed\n- Readiness: go-pending-approval")
                t += f"\n## Workflow history\n- 2026-10-17 reviewed: {data.get('verdict')}\n"
                pf.write_text(t, encoding="utf-8")
                if item_cfg and isinstance(item_cfg, dict) and item_cfg.get("commit_plan_edit"):
                    subprocess.run(["git", "add", str(pf)], check=True)
                    subprocess.run(["git", "commit", "-qm", f"review {id6} update plan"], check=True)
except Exception:
    pass

sys.exit(0)
""",
    )


class TestStatusVocabulary(unittest.TestCase):
    """E-01 / A32 / V-01: Status vocabulary, absence from terminal/success sets, run state mapping."""

    def test_status_vocabulary(self) -> None:
        """awaiting-human is in known & in-flight sets, absent from terminal & success sets, maps to blocked."""
        # 1. KNOWN_ITEM_STATUSES
        self.assertIn("awaiting-human", runner_shutdown.KNOWN_ITEM_STATUSES)

        # 2. IN_FLIGHT_QUEUE_STATUSES
        self.assertIn(
            runner_shared.AWAITING_HUMAN_STATUS, runner_shared.IN_FLIGHT_QUEUE_STATUSES
        )

        # 3. Absent from TERMINAL_STATES and canonical on both hosts
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, runner_shared.TERMINAL_STATES
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, runner_shared.TERMINAL_STATES_CANONICAL
        )
        self.assertNotIn(runner_shared.AWAITING_HUMAN_STATUS, oc_runipd.TERMINAL_STATES)
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, agy_runipd.TERMINAL_STATES
        )

        # 4. Absent from EXECUTION_SUCCESS_STATES on both hosts
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, runner_shared.EXECUTION_SUCCESS_STATES
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, oc_runipd.EXECUTION_SUCCESS_STATES
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS, agy_runipd.EXECUTION_SUCCESS_STATES
        )

        # 5. Absent from reporting success sets
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS,
            runner_shared.EXECUTE_REPORTING_SUCCESS_STATES,
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS,
            runner_shared.EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES,
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS,
            runner_shared.SKIP_REPORTING_SUCCESS_STATES,
        )
        self.assertNotIn(
            runner_shared.AWAITING_HUMAN_STATUS,
            runner_shared.PLAN_REPORTING_SUCCESS_STATES,
        )

        # 6. map_driver_status_to_run_state maps awaiting-human to STATE_BLOCKED
        mapped_state = runner_shared.map_driver_status_to_run_state(
            runner_shared.AWAITING_HUMAN_STATUS
        )
        self.assertEqual(mapped_state, run_state.STATE_BLOCKED)

        # 7. lifecycle_style maps awaiting-human to WAITING_INPUT
        resolved = lifecycle_style.resolve("runner-item", "awaiting-human")
        self.assertEqual(resolved.stage, lifecycle_style.WAITING_INPUT)
        self.assertEqual(resolved.style.unicode, "…")

        # Print for V-01 visibility
        print(
            f"V-01: awaiting-human mapped_state={mapped_state!r}, glyph={resolved.style.unicode!r}"
        )


def test_execute_turn_parking_and_nongating(tmp_path: Path) -> None:
    """E-02 / A3 / A5 / V-02: Execute turn parks with gating question; does not park with non-gating question."""
    repo = _create_test_repo(tmp_path)
    plan_gating = _create_plan_file(repo, "exg001", setid="qex", order=1)
    plan_nongating = _create_plan_file(repo, "exn002", setid="qex", order=2)
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / "run-execute-park"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Record main HEAD before execute turn
    main_before = subprocess.run(
        ["git", "rev-parse", "main"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Part 1: Gating question -> parks awaiting-human
    gating_question = {
        "question_id": "q-db-timeout",
        "text": "What is the database connection timeout?",
        "artifact_id6": "exg001",
        "gates_verdict": True,
        "evidence": ["spec doc", "config.py"],
    }
    payload_map = {
        "exg001": {
            "commit": "implement database driver",
            "outcome": {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [gating_question],
                "pushed": False,
            },
        },
        "exn002": {
            "commit": "implement cache layer",
            "outcome": {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-cache-size",
                        "text": "Cache size preference?",
                        "artifact_id6": "exn002",
                        "gates_verdict": False,
                        "evidence": ["cache.py"],
                    }
                ],
                "pushed": False,
            },
        },
    }

    item_gating: dict[str, Any] = {
        "id6": "exg001",
        "setid": "qex",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_gating),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": "run-execute-park",
        "queue": [item_gating],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": True,
            "output_mode": "quiet",
            "opencode": str(fake_bin),
        },
    }
    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        oc_runipd.execute_item(run_dir, state, item_gating, recovery=False)

    # Assert gating item parked
    assert item_gating["status"] == runner_shared.AWAITING_HUMAN_STATUS
    assert item_gating.get("needs_input") is True
    assert item_gating.get("preserved_branch") is not None
    assert item_gating.get("preserved_base") == main_before
    assert item_gating.get("preserved_lane_id") is not None
    assert item_gating.get("preserved_retention_reasons") == [
        lane_containment.RETENTION_AWAITING_HUMAN
    ]
    assert len(item_gating.get("questions", [])) == 1

    # Check main HEAD unchanged
    main_after = subprocess.run(
        ["git", "rev-parse", "main"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert main_before == main_after, "Main HEAD must not change when an item parks"

    # Check commit in lane branch
    lane_branch = item_gating["preserved_branch"]
    log_lane = subprocess.run(
        ["git", "log", f"main..{lane_branch}", "--oneline"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert "implement database driver" in log_lane

    # Check events.jsonl contains lane-preserved and ipd-finished, no verifier/finalize events
    events_file = run_dir / "events.jsonl"
    event_names = []
    if events_file.exists():
        for line in events_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                event_names.append(json.loads(line).get("event"))

    assert lane_containment.LANE_PRESERVED_EVENT in event_names
    assert "ipd-finished" in event_names
    for ev in event_names:
        assert not ev.startswith("verifier-"), f"Unexpected verifier event: {ev}"
        assert not ev.startswith("finalize-"), f"Unexpected finalize event: {ev}"

    # Print for V-02 visibility
    print(f"V-02 Gating: main_before={main_before} main_after={main_after}")
    print(f"V-02 Lane log: {log_lane}")
    print(f"V-02 Events: {event_names}")

    # Part 2: Non-gating question -> completes executed, integrates to main
    item_nongating: dict[str, Any] = {
        "id6": "exn002",
        "setid": "qex",
        "position": 2,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_nongating),
        "attempts": [],
    }
    state["queue"].append(item_nongating)
    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
        mock.patch.object(oc_runipd, "driver_finalize", return_value=(0, "ok")),
        mock.patch.object(
            oc_runipd,
            "run_suite_check",
            return_value=runner_shared.SuiteCheckResult(
                True, 0, "ok", "ok", "", 1.0, 0.1
            ),
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        oc_runipd.execute_item(run_dir, state, item_nongating, recovery=False)

    assert item_nongating["status"] == "executed"
    assert item_nongating.get("questions") is None
    assert len(item_nongating["attempts"][-1]["questions_verdict"]["questions"]) == 1

    main_after_nongating = subprocess.run(
        ["git", "rev-parse", "main"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert (
        main_after_nongating != main_before
    ), "Main HEAD should advance when non-gating item executes"
    print(
        f"V-02 Non-gating: status={item_nongating['status']}, main_after={main_after_nongating}"
    )


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_ten_item_queue_continuation_a4_a7_v03(
    tmp_path: Path, runner_name: str
) -> None:
    """E-03 / A4 / A7 / V-03: 10-item queue where item 3 parks; independent items finish; dependents wait."""
    repo = _create_test_repo(tmp_path)
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-10item-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    plans = []
    queue = []
    payload_map: dict[str, Any] = {}

    for i in range(1, 11):
        id6 = f"it{i:04d}"
        deps = None
        if i == 4:
            deps = ["executed:it0003"]
        elif i == 5:
            deps = ["executed:it0004"]

        p = _create_plan_file(
            repo, id6, setid="tenq", order=i, dependencies=deps, commit=False
        )
        plans.append(p)

        item = {
            "id6": id6,
            "setid": "tenq",
            "position": i,
            "action": "execute",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        if deps:
            item["dependencies"] = list(deps)
        queue.append(item)

        if i == 3:
            payload_map[id6] = {
                "outcome": {
                    "disposition": "partial",
                    "defect_report": {"state": "none-found", "findings": []},
                    "questions": [
                        {
                            "question_id": "q-item-3",
                            "text": "What is the target retry limit for item 3?",
                            "artifact_id6": "it0003",
                            "gates_verdict": True,
                            "evidence": ["plan it0003"],
                        }
                    ],
                    "pushed": False,
                }
            }
        else:
            payload_map[id6] = {
                "commit": f"work for {id6}",
                "outcome": {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                },
            }

    # Batch commit all plans at once to save time
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "batch add ten plans"], cwd=repo, check=True
    )

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": f"run-10item-{runner_name}",
        "queue": queue,
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }

    if runner_name == "oc":
        state["options"]["opencode"] = str(fake_bin)
        driver_module = oc_runipd
    else:
        state["options"]["agy"] = str(fake_bin)
        driver_module = agy_runipd

    runner_shared.save_state(run_dir, state)

    def mock_finalize(
        target_repo: Path, plan: Path, fin_id6: str, *args: Any, **kwargs: Any
    ) -> tuple[int, str]:
        exec_dir = target_repo / ".aw" / "records" / "plans" / "executed"
        exec_dir.mkdir(parents=True, exist_ok=True)
        p_path = Path(plan)
        if p_path.is_file():
            dest = exec_dir / p_path.name
            dest.write_text(p_path.read_text(encoding="utf-8"), encoding="utf-8")
            p_path.unlink()
        return 0, "ok"

    with (
        mock.patch.object(driver_module, "driver_begin", return_value=(0, "ok")),
        mock.patch.object(driver_module, "driver_finalize", side_effect=mock_finalize),
        mock.patch.object(
            driver_module,
            "run_suite_check",
            return_value=runner_shared.SuiteCheckResult(
                True, 0, "ok", "ok", "", 1.0, 0.1
            ),
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        rc = driver_module.run_queue(run_dir, state)
        assert rc == 3

    final_state = runner_shared.load_state(run_dir)
    by_id = {it["id6"]: it for it in final_state["queue"]}

    # Item 3: awaiting-human
    assert by_id["it0003"]["status"] == runner_shared.AWAITING_HUMAN_STATUS

    # Items 1, 2, 6, 7, 8, 9, 10: executed
    for i in (1, 2, 6, 7, 8, 9, 10):
        id6 = f"it{i:04d}"
        assert (
            by_id[id6]["status"] == "executed"
        ), f"{id6} should be executed but got {by_id[id6]['status']}"

    # Items 4 and 5: queued (waiting on item 3)
    assert by_id["it0004"]["status"] == "queued"
    assert by_id["it0005"]["status"] == "queued"
    assert len(by_id["it0004"]["attempts"]) == 0
    assert len(by_id["it0005"]["attempts"]) == 0

    # awaiting_upstream on dependents names item 3 question
    upstream_4 = by_id["it0004"].get("awaiting_upstream", {})
    assert "it0003" in upstream_4
    assert "What is the target retry limit for item 3?" in upstream_4["it0003"]

    upstream_5 = by_id["it0005"].get("awaiting_upstream", {})
    assert "it0003" in upstream_5

    # No item has fail-depend or dependency-blocked
    for id6, it in by_id.items():
        assert it["status"] not in (
            "fail-depend",
            "dependency-blocked",
        ), f"{id6} unexpectedly marked {it['status']}"

    # Print for V-03 visibility
    statuses = {k: v["status"] for k, v in by_id.items()}
    print(f"V-03 Final Queue Statuses ({runner_name}): {statuses}")
    print(f"V-03 it0004 awaiting_upstream: {upstream_4}")


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_drain_exit_codes_and_summary_a8_a38_v04(
    tmp_path: Path, runner_name: str, capsys: Any
) -> None:
    """E-04 / A8 / A38 / V-04: Parked-only drain exits 3 and prints summary; parked + fail-gate still exits 3."""
    repo = _create_test_repo(tmp_path)
    fake_bin = _make_fake_agent_script(tmp_path)

    # Case 1: 1 parked item + 1 waiting dependent
    run_dir = repo / ".aw" / "records" / "runs" / f"run-drain-parked-{runner_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    plan_1 = _create_plan_file(repo, "dr0001", setid="drset", order=1, commit=False)
    plan_2 = _create_plan_file(
        repo,
        "dr0002",
        setid="drset",
        order=2,
        dependencies=["executed:dr0001"],
        commit=False,
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "batch add drain plans"], cwd=repo, check=True
    )

    item_1 = {
        "id6": "dr0001",
        "setid": "drset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_1),
        "attempts": [],
    }
    item_2 = {
        "id6": "dr0002",
        "setid": "drset",
        "position": 2,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_2),
        "dependencies": ["executed:dr0001"],
        "attempts": [],
    }

    payload_map_1 = {
        "dr0001": {
            "outcome": {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-drain-1",
                        "text": "Choose deployment target?",
                        "artifact_id6": "dr0001",
                        "gates_verdict": True,
                        "evidence": ["plan dr0001"],
                    }
                ],
                "pushed": False,
            }
        }
    }

    state_1 = {
        "repo": str(repo),
        "run_id": f"run-drain-parked-{runner_name}",
        "queue": [item_1, item_2],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    driver_module = oc_runipd if runner_name == "oc" else agy_runipd
    state_1["options"]["opencode" if runner_name == "oc" else "agy"] = str(fake_bin)
    runner_shared.save_state(run_dir, state_1)

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map_1)}
    ), coordinator_role():
        rc_1 = driver_module.run_queue(run_dir, state_1)

    assert rc_1 == 3, f"Expected exit code 3 for parked-only queue, got {rc_1}"
    captured_1 = capsys.readouterr()
    combined_1 = captured_1.out + captured_1.err
    assert "1 item(s) parked awaiting answers; 1 waiting on them" in combined_1
    assert str(run_dir) in combined_1

    # Print for V-04 visibility
    print(f"V-04 Case 1 Exit Code ({runner_name}): {rc_1}")
    for line in combined_1.splitlines():
        if "parked awaiting answers" in line:
            print(f"V-04 Summary Line: {line}")

    # Case 2: 1 parked item + 1 independent fail-gate item -> still exits 3
    run_dir_2 = repo / ".aw" / "records" / "runs" / f"run-drain-mixed-{runner_name}"
    run_dir_2.mkdir(parents=True, exist_ok=True)
    (run_dir_2 / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir_2 / "prompts").mkdir(parents=True, exist_ok=True)

    plan_m1 = _create_plan_file(repo, "mx0001", setid="mxset", order=1, commit=False)
    plan_m2 = _create_plan_file(repo, "mx0002", setid="mxset", order=2, commit=False)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "batch add mixed plans"], cwd=repo, check=True
    )

    item_m1 = {
        "id6": "mx0001",
        "setid": "mxset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_m1),
        "attempts": [],
    }
    item_m2 = {
        "id6": "mx0002",
        "setid": "mxset",
        "position": 2,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_m2),
        "attempts": [],
    }

    payload_map_2 = {
        "mx0001": {
            "outcome": {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-mixed-1",
                        "text": "Database engine?",
                        "artifact_id6": "mx0001",
                        "gates_verdict": True,
                        "evidence": ["ev"],
                    }
                ],
                "pushed": False,
            }
        },
        "mx0002": {
            "outcome": {
                "disposition": "fail-gate",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            }
        },
    }

    state_2 = {
        "repo": str(repo),
        "run_id": f"run-drain-mixed-{runner_name}",
        "queue": [item_m1, item_m2],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "output_mode": "quiet",
        },
    }
    state_2["options"]["opencode" if runner_name == "oc" else "agy"] = str(fake_bin)
    runner_shared.save_state(run_dir_2, state_2)

    with mock.patch.dict(
        os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map_2)}
    ), coordinator_role():
        rc_2 = driver_module.run_queue(run_dir_2, state_2)

    assert (
        rc_2 == 3
    ), f"Expected exit code 3 (needs input outranks item failure), got {rc_2}"
    print(f"V-04 Case 2 Exit Code ({runner_name}): {rc_2}")


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_review_sweep_lane_parking_and_refusal_e06_v06(
    tmp_path: Path, runner_name: str
) -> None:
    """E-06 / A13 / A15 / V-06: 3-review fixture on shared sweep lane; refusal on non-descendant."""
    repo = _create_test_repo(tmp_path)
    fake_bin = _make_fake_agent_script(tmp_path)

    run_id = f"run-rev-sweep-{runner_name}"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Review 1: deferred integration
    # Review 2: gating question -> parks, branches aw/parked/<run_id>/rv0002, resets to tip_before
    # Review 3: normal review -> merges sweep lane (carrying Rev 1 + Rev 3) to main
    p1 = _create_plan_file(
        repo,
        "rv0001",
        setid="revq",
        order=1,
        status="to-review",
        action="review",
        commit=False,
    )
    p2 = _create_plan_file(
        repo,
        "rv0002",
        setid="revq",
        order=2,
        status="to-review",
        action="review",
        commit=False,
    )
    p3 = _create_plan_file(
        repo,
        "rv0003",
        setid="revq",
        order=3,
        status="to-review",
        action="review",
        commit=False,
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "batch add review plans"], cwd=repo, check=True
    )

    item_1: dict[str, Any] = {
        "id6": "rv0001",
        "setid": "revq",
        "position": 1,
        "action": "review",
        "review_handler": "plan-review",
        "status": "queued",
        "configured_file": str(p1),
        "attempts": [],
    }
    item_2: dict[str, Any] = {
        "id6": "rv0002",
        "setid": "revq",
        "position": 2,
        "action": "review",
        "review_handler": "plan-review",
        "status": "queued",
        "configured_file": str(p2),
        "attempts": [],
    }
    item_3: dict[str, Any] = {
        "id6": "rv0003",
        "setid": "revq",
        "position": 3,
        "action": "review",
        "review_handler": "plan-review",
        "status": "queued",
        "configured_file": str(p3),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": run_id,
        "queue": [item_1, item_2, item_3],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "isolate_review": True,
            "output_mode": "quiet",
        },
    }
    driver_module = oc_runipd if runner_name == "oc" else agy_runipd
    state["options"]["opencode" if runner_name == "oc" else "agy"] = str(fake_bin)
    runner_shared.save_state(run_dir, state)

    payload_map = {
        "rv0001": {
            "commit": "review 1 pass",
            "commit_plan_edit": True,
            "outcome": {
                "disposition": "reviewed",
                "verdict": "APPROVE WITH REVISIONS APPLIED",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            },
        },
        "rv0002": {
            "commit": "review 2 intermediate finding",
            "dirty_file": f".aw/records/plans/pending/{p2.name}",
            "outcome": {
                "disposition": "reviewed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-rev-boundary",
                        "text": "Is the domain boundary appropriate?",
                        "artifact_id6": "rv0002",
                        "gates_verdict": True,
                        "evidence": ["spec boundary"],
                    }
                ],
                "pushed": False,
            },
        },
        "rv0003": {
            "commit": "review 3 pass",
            "commit_plan_edit": True,
            "outcome": {
                "disposition": "reviewed",
                "verdict": "APPROVE WITH REVISIONS APPLIED",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            },
        },
    }

    # Execute review 1 with deferred integration
    orig_integrate = driver_module.integrate_review_lane_branch

    def mock_integrate(
        r: Path, h: Any, id6: str, *args: Any, **kwargs: Any
    ) -> tuple[bool, str, str]:
        if id6 == "rv0001":
            return (
                False,
                "integration-deferred for testing",
                runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
            )
        return orig_integrate(r, h, id6, *args, **kwargs)

    with (
        mock.patch.object(
            driver_module, "integrate_review_lane_branch", side_effect=mock_integrate
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        driver_module.execute_item(run_dir, state, item_1, recovery=False)

    assert item_1["status"] in (
        "integration-deferred",
        "merge-retry",
        "integration-blocked",
        "queued",
    )
    sweep_handle = runner_shared.review_sweep_lane_handle(state)
    assert sweep_handle is not None
    sweep_wt = Path(sweep_handle.path)
    tip_after_rev1 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sweep_wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Execute review 2: parks with gating question
    with (
        mock.patch.object(
            driver_module, "integrate_review_lane_branch", side_effect=mock_integrate
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        driver_module.execute_item(run_dir, state, item_2, recovery=False)

    assert item_2["status"] == runner_shared.AWAITING_HUMAN_STATUS
    assert item_2.get("needs_input") is True
    assert item_2.get("preserved_branch") == f"aw/parked/{run_id}/rv0002"
    assert item_2.get("preserved_base") == tip_after_rev1

    # Assert sweep lane status is clean and HEAD == tip_after_rev1
    sweep_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=sweep_wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert (
        sweep_status == ""
    ), f"Sweep lane should be clean after parking, got: {sweep_status}"

    sweep_head_after_park = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sweep_wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert (
        sweep_head_after_park == tip_after_rev1
    ), "Sweep lane HEAD should equal review_lane_tip_before"

    # Assert plan 2 file has NO - Readiness:
    plan_2_text = p2.read_text(encoding="utf-8")
    assert "- Readiness:" not in plan_2_text

    # Execute review 3: normal review, integrates to main
    with (
        mock.patch.object(
            driver_module, "integrate_review_lane_branch", side_effect=mock_integrate
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        driver_module.execute_item(run_dir, state, item_3, recovery=False)

    assert item_3["status"] == "reviewed"

    # Check git logs for main and parked branch
    log_main = subprocess.run(
        ["git", "log", "--oneline", "main"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    log_parked = subprocess.run(
        ["git", "log", "--oneline", f"aw/parked/{run_id}/rv0002"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert "review 1 pass" in log_main
    assert "review 3 pass" in log_main
    assert (
        "review 2 intermediate finding" not in log_main
    ), "Review 2 commits must be absent from main"
    assert (
        "review 2 intermediate finding" in log_parked
    ), "Review 2 commits must be on parked branch"

    # Print for V-06 visibility
    print(f"V-06 git log --oneline main:\n{log_main}")
    print(f"V-06 git log --oneline aw/parked/{run_id}/rv0002:\n{log_parked}")
    print(f"V-06 sweep lane status --porcelain: {sweep_status!r}")
    print(f"V-06 sweep lane rev-parse HEAD: {sweep_head_after_park}")

    # Part 2: Refuse to park when sweep lane tip is not a descendant of review_lane_tip_before
    plan_refuse = _create_plan_file(
        repo, "rf0004", setid="revq", order=4, status="to-review", action="review"
    )
    item_refuse: dict[str, Any] = {
        "id6": "rf0004",
        "setid": "revq",
        "position": 4,
        "action": "review",
        "review_handler": "plan-review",
        "status": "queued",
        "configured_file": str(plan_refuse),
        "attempts": [],
    }
    state["queue"].append(item_refuse)
    runner_shared.save_state(run_dir, state)

    payload_map["rf0004"] = {
        "outcome": {
            "disposition": "reviewed",
            "defect_report": {"state": "none-found", "findings": []},
            "questions": [
                {
                    "question_id": "q-refuse-1",
                    "text": "Refusal question?",
                    "artifact_id6": "rf0004",
                    "gates_verdict": True,
                    "evidence": ["ev"],
                }
            ],
            "pushed": False,
        }
    }

    with (
        mock.patch.object(
            runner_shared,
            "lane_branch_tip",
            return_value="0000000000000000000000000000000000000000",
        ),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        driver_module.execute_item(run_dir, state, item_refuse, recovery=False)

    assert item_refuse["status"] == "fail-gate"
    refusal = item_refuse.get("refusal") or {}
    assert refusal.get("code") == "review-park-refused"
    print(f"V-06 Refusal output: status={item_refuse['status']}, refusal={refusal}")


def test_agy_parks_without_permission_config_a15_a39(tmp_path: Path) -> None:
    """E-02 / A15 / A39: Antigravity runner parks without any permission configuration."""
    repo = _create_test_repo(tmp_path)
    plan = _create_plan_file(repo, "agp001", setid="agset", order=1)
    fake_bin = _make_fake_agent_script(tmp_path)

    run_dir = repo / ".aw" / "records" / "runs" / "run-agy-no-perm"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    payload_map = {
        "agp001": {
            "commit": "agy commit in lane",
            "outcome": {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-agy-1",
                        "text": "Antigravity question?",
                        "artifact_id6": "agp001",
                        "gates_verdict": True,
                        "evidence": ["agy evidence"],
                    }
                ],
                "pushed": False,
            },
        }
    }

    item: dict[str, Any] = {
        "id6": "agp001",
        "setid": "agset",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan),
        "attempts": [],
    }

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": "run-agy-no-perm",
        "queue": [item],
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": True,
            "output_mode": "quiet",
            "agy": str(fake_bin),
        },
    }
    runner_shared.save_state(run_dir, state)

    with (
        mock.patch.object(agy_runipd, "driver_begin", return_value=(0, "ok")),
        mock.patch.dict(os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}),
        coordinator_role(),
    ):
        agy_runipd.execute_item(run_dir, state, item, recovery=False)

    assert item["status"] == runner_shared.AWAITING_HUMAN_STATUS
    assert item.get("needs_input") is True
    assert item.get("preserved_branch") is not None
    assert item.get("preserved_base") is not None
    assert item.get("preserved_lane_id") is not None
    assert len(item.get("questions", [])) == 1
    print("A39 Antigravity parked successfully without permission configuration.")
