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

"""Tests for production fix-it turns on stall, crash, or spawn failure (IPD ob7aq9).

Validates all 12 cases of E-10 and the report test of E-11 across both hosts (oc and agy).
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import (
    runner_shared as rs,
    runner_stop,
)
from tests.test_production_correction_turn import (
    _HOSTS,
    _fake_probe_pass,
    _patch_host_agent,
    _write_backlog_item,
    _write_spec,
)


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (path / ".gitignore").write_text(
        ".aw/records/runs/\n.aw/worktrees/\n.aw/state/\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_child_plan(
    repo: Path,
    *,
    id6: str,
    backlog_id6: str | None = None,
    spec_id6: str | None = None,
    setid: str = "tstset",
    order: int = 1,
    status: str = "to-review",
    gate: str | None = None,
    scope_paths: str = "README.md",
    dependencies: str = "none",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test-child.ipd.md"

    bkl_line = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""

    content = f"""# IPD: Test Child Plan {id6}

- Date: 2026-10-04
- Kind: child
- Concern: Test child concern.
- Scope: Test child scope.
- Scope-Paths: {scope_paths}
- Status: {status}
{bkl_line}{spec_line}{gate_line}- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: {dependencies}

## Workflow history
- 2026-10-04 {status} (test): created.

## Goal
Test child goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.

## Findings
- None.

## Proposed changes (ordered, validatable)
1. E-01 do work.

## Deferred / out of scope (with reason)
- None.
  - Carrier-Declined: none

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_orchestrator_plan(
    repo: Path,
    *,
    id6: str = "orc001",
    backlog_id6: str | None = None,
    spec_id6: str | None = None,
    setid: str = "tstset",
    status: str = "to-review",
    gate: str | None = None,
    child_rows: list[tuple[str, str, str]] | None = None,
    checklist_item: str | None = None,
    readiness: str | None = None,
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261004-{setid}-00-{id6}-test-orch.ipd.md"

    if child_rows is None:
        child_rows = [
            (
                "01",
                "chd001",
                f".aw/records/plans/pending/20261004-{setid}-01-chd001-test-child.ipd.md",
            )
        ]

    if checklist_item is None:
        first_child = child_rows[0][1] if child_rows else "chd001"
        checklist_item = (
            f"- [ ] E-01 CONFIRM {first_child} REACHED executed\n"
            "  - Depends on: none\n"
            "  - Expected outcome: done\n"
            "  - Execution state: pending"
        )

    bkl_line = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    readiness_line = f"- Readiness: {readiness}\n" if readiness else ""

    lines = [
        f"# IPD: Test Orchestrator {id6}",
        "",
        "- Date: 2026-10-04",
        "- Kind: orchestrator",
        f"- Id: {id6}",
        f"- Set: {setid}",
        "- Order: 0",
        f"- Status: {status}",
        f"{readiness_line}{bkl_line}{spec_line}{gate_line}- Priority: medium",
        "- Work-Kind: chore",
        "- Author: test",
        "- Highest E allocated: 01",
        "- Concern: Test orchestrator concern.",
        "- Scope: Test orchestrator scope.",
        "- Scope-Paths: README.md",
        "- Item-Dependencies: none",
        "",
        "## Workflow history",
        f"- 2026-10-04 {status} (test): created.",
        "",
        "## Goal",
        "Test orchestrator goal.",
        "",
        "## Detailed Implementation Checklist (TODO)",
        "Execution-state rule: mark performed only after doing it.",
        "### Task group 1: orchestrate",
        checklist_item,
        "",
        "## Child IPDs, sequence, and dependencies",
        "",
        "| Order | Id | Status | Plan | Depends on |",
        "|---|---|---|---|---|",
    ]
    for ord_tok, c_id6, c_path in child_rows:
        lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
    lines.extend(
        [
            "",
            "## Completion criteria (the whole Set is done only when)",
            "- None.",
            "",
            "## Cross-IPD validation",
            "- None.",
            "",
            "## Deferred / out of scope (with reason)",
            "- None.",
            "  - Carrier-Declined: none",
            "",
            "## Scope check",
            "- None.",
            "",
            "## Required tests / validation",
            "- None.",
            "",
            "## Spec / documentation sync",
            "- None.",
            "",
            "## Open questions",
            "- None.",
            "",
            "## Validation and cross-check (verify before reporting the Set complete)",
            "Validation-state rule: inspect evidence.",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: check.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "- None.",
            "",
        ]
    )
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def _write_review_plan(
    repo: Path,
    *,
    id6: str = "rev001",
    setid: str = "revset",
    status: str = "to-review",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261024-{setid}-01-{id6}-test-plan.ipd.md"
    content = f"""# IPD: Review Plan {id6}

- Date: 2026-10-24
- Kind: child
- Concern: Test concern.
- Scope: Test scope.
- Scope-Paths: README.md
- Status: {status}
- Set: {setid}
- Order: 1
- Highest E allocated: 01
- Author: tester
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: none

## Workflow history
- 2026-10-24 {status} (tester): created.

## Goal
Test goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: work
- [ ] E-01 Work
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.

## Findings
- None.

## Proposed changes (ordered, validatable)
1. E-01 work.

## Deferred / out of scope (with reason)
- None.
  - Carrier-Declined: none

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


class TestProductionFixIt(unittest.TestCase):
    """Test suite validating IPD ob7aq9."""

    def test_e10_01_backlog_production_stall_then_success(self) -> None:
        """E-10 (1): Backlog production stall then success in same lane and session."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl001", status="open", setid="set001"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add bkl"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-bkl-stall-succ"
                    cmd = [
                        "start",
                        "bkl001",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]
                    received_sessions: list[str | None] = []

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        session_arg = (
                            kwargs.get("resume_session")
                            if "resume_session" in kwargs
                            else kwargs.get("session_id")
                        )
                        received_sessions.append(session_arg)
                        if turns[0] == 1:
                            raise rs.StallTimeout(
                                "timed out waiting for agent", session_id="ses-p1"
                            )
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc001",
                            backlog_id6="bkl001",
                            setid="set001",
                            child_rows=[
                                (
                                    "01",
                                    "chd001",
                                    ".aw/records/plans/pending/20261004-set001-01-chd001-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd001", backlog_id6="bkl001", setid="set001"
                        )
                        return 0, "ses-p1", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(item.get("turn_retry_attempts"), 1)
                    self.assertEqual(rs.production_set_retry_attempts(item), 0)

                    attempts = item["attempts"]
                    self.assertEqual(len(attempts), 2)
                    self.assertEqual(attempts[0]["turn_failure_kind"], "stall")
                    self.assertEqual(attempts[0]["session_id"], "ses-p1")
                    self.assertTrue(attempts[0].get("turn_correction"))

                    self.assertEqual(attempts[1]["fix_it_lane"], "resumed")
                    self.assertEqual(attempts[1]["worktree"], attempts[0]["worktree"])
                    self.assertEqual(received_sessions[0], None)
                    self.assertEqual(received_sessions[1], "ses-p1")

                    # Backlog item graduated
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set001*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))

    def test_e10_02_stalled_attempt_child_plan_committed(self) -> None:
        """E-10 (2): Child plan written in stalled attempt 1 and orchestrator in attempt 2 are both committed."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl002", status="open", setid="set002"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add bkl"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-child-committed"
                    cmd = [
                        "start",
                        "bkl002",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turns[0] == 1:
                            # Write child plan 01 before stalling
                            _write_child_plan(
                                target,
                                id6="chd001",
                                backlog_id6="bkl002",
                                setid="set002",
                            )
                            raise rs.StallTimeout(
                                "stall after writing child", session_id="ses-p2"
                            )
                        # Resumed attempt writes orchestrator referencing child 01
                        _write_orchestrator_plan(
                            target,
                            id6="orc002",
                            backlog_id6="bkl002",
                            setid="set002",
                            child_rows=[
                                (
                                    "01",
                                    "chd001",
                                    ".aw/records/plans/pending/20261004-set002-01-chd001-test-child.ipd.md",
                                )
                            ],
                        )
                        return 0, "ses-p2", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")

                    # Both plans must exist committed in repo pending plans
                    chd_p = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20261004-set002-01-chd001-test-child.ipd.md"
                    )
                    orc_p = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20261004-set002-00-orc002-test-orch.ipd.md"
                    )
                    self.assertTrue(chd_p.is_file())
                    self.assertTrue(orc_p.is_file())

                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    out_of_scope_events = [
                        e
                        for e in events
                        if e.get("event") == "backlog-production-out-of-scope-paths"
                    ]
                    self.assertEqual(out_of_scope_events, [])

    def test_e10_03_spec_production_nonzero_exit_then_success(self) -> None:
        """E-10 (3): Spec production nonzero exit records no-outcome then succeeds on fix-it turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spec-crash"
                    cmd = [
                        "start",
                        "spc001",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        if turns[0] == 1:
                            return 1, "ses-spc1", rdir / "log.txt", ["cmd"]
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc003",
                            spec_id6="spc001",
                            setid="set003",
                            child_rows=[
                                (
                                    "01",
                                    "chd003",
                                    ".aw/records/plans/pending/20261004-set003-01-chd003-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd003", spec_id6="spc001", setid="set003"
                        )
                        return 0, "ses-spc1", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(item.get("turn_retry_attempts"), 1)
                    attempts = item["attempts"]
                    self.assertEqual(attempts[0]["turn_failure_kind"], "no-outcome")
                    self.assertTrue(attempts[0].get("turn_correction"))
                    self.assertEqual(attempts[1]["fix_it_lane"], "resumed")

    def test_e10_04_spawn_failure_exhausts_budget_next_runs(self) -> None:
        """E-10 (4): Spawn failure exhausts budget, item failed-safely, next item runs."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl004", status="open", setid="set004"
                    )
                    _write_backlog_item(
                        repo, id6="bkl005", status="open", setid="set005"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add items"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spawn-exhaust"
                    cmd = [
                        "start",
                        "bkl004",
                        "bkl005",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        if item["id6"] == "bkl004":
                            raise rs.HostSpawnError("binary not found")
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc005",
                            backlog_id6="bkl005",
                            setid="set005",
                            child_rows=[
                                (
                                    "01",
                                    "chd005",
                                    ".aw/records/plans/pending/20261004-set005-01-chd005-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd005", backlog_id6="bkl005", setid="set005"
                        )
                        return 0, "ses-bkl5", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item1 = state["queue"][0]
                    item2 = state["queue"][1]
                    self.assertEqual(item1["status"], "failed-safely")
                    self.assertEqual(item1.get("turn_retry_attempts"), 2)
                    self.assertIn(
                        "turn-retry", item1.get("refusal", {}).get("code", "")
                    )

                    self.assertEqual(item2["status"], "executed")

    def test_e10_05_budget_zero_no_fix_it_turn(self) -> None:
        """E-10 (5): Budget 0 yields no fix-it turn, item fails immediately."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl006", status="open", setid="set006"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-b0"
                    cmd = [
                        "start",
                        "bkl006",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "0",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(*args: Any, **kwargs: Any) -> Any:
                        raise rs.StallTimeout("stalled", session_id="ses-b6")

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "failed-safely")
                    self.assertEqual(len(item["attempts"]), 1)
                    self.assertEqual(item.get("turn_retry_attempts", 0), 0)

    def test_e10_06_fallback_lane_removed_fresh_session(self) -> None:
        """E-10 (6): Prior lane removed between attempts falls back to fresh lane and session."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl007", status="open", setid="set007"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-fallback"
                    cmd = [
                        "start",
                        "bkl007",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]
                    first_wt = [""]
                    received_sessions: list[str | None] = []

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        session_arg = (
                            kwargs.get("resume_session")
                            if "resume_session" in kwargs
                            else kwargs.get("session_id")
                        )
                        received_sessions.append(session_arg)
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turns[0] == 1:
                            first_wt[0] = str(target)
                            raise rs.StallTimeout("stall", session_id="ses-fb1")
                        _write_orchestrator_plan(
                            target,
                            id6="orc007",
                            backlog_id6="bkl007",
                            setid="set007",
                            child_rows=[
                                (
                                    "01",
                                    "chd007",
                                    ".aw/records/plans/pending/20261004-set007-01-chd007-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd007", backlog_id6="bkl007", setid="set007"
                        )
                        return 0, "ses-fb2", rdir / "log.txt", ["cmd"]

                    # Hook into append_jsonl to delete first_wt when ipd-stalled is appended
                    orig_append_jsonl = rs.append_jsonl

                    def hook_append_jsonl(path: Path, event: dict[str, Any]) -> None:
                        orig_append_jsonl(path, event)
                        if event.get("event") == "ipd-stalled" and first_wt[0]:
                            subprocess.run(
                                ["git", "worktree", "remove", "--force", first_wt[0]],
                                cwd=repo,
                                check=True,
                            )

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ), mock.patch.object(rs, "append_jsonl", hook_append_jsonl):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    attempts = item["attempts"]
                    self.assertTrue(attempts[1]["fix_it_lane"].startswith("fresh:"))
                    self.assertIn("does not exist", attempts[1]["fix_it_lane"])
                    self.assertEqual(received_sessions[1], None)

    def test_e10_07_set_finding_refusal_exit_0_turn_retry_skipped(self) -> None:
        """E-10 (7): Set-finding refusal on exit-0 records turn_retry_skipped and no double-count."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl008", status="open", setid="set008"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-set-corr"
                    cmd = [
                        "start",
                        "bkl008",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turns[0] == 1:
                            # Turn 1: exit 0 but missing child 02
                            _write_orchestrator_plan(
                                target,
                                id6="orc008",
                                backlog_id6="bkl008",
                                setid="set008",
                                child_rows=[
                                    (
                                        "01",
                                        "cd008a",
                                        ".aw/records/plans/pending/20261004-set008-01-cd008a-test-child.ipd.md",
                                    ),
                                    (
                                        "02",
                                        "cd008b",
                                        ".aw/records/plans/pending/20261004-set008-02-cd008b-test-child.ipd.md",
                                    ),
                                ],
                            )
                            _write_child_plan(
                                target,
                                id6="cd008a",
                                backlog_id6="bkl008",
                                setid="set008",
                            )
                        else:
                            # Set correction turn: write child 02
                            _write_child_plan(
                                target,
                                id6="cd008b",
                                backlog_id6="bkl008",
                                setid="set008",
                                order=2,
                            )
                        return 0, "ses-set8", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(rs.production_set_retry_attempts(item), 1)
                    self.assertEqual(item.get("turn_retry_attempts", 0), 0)

                    att1 = item["attempts"][0]
                    self.assertIn(
                        "Set correction loop", att1.get("turn_retry_skipped", "")
                    )
                    self.assertIsNone(att1.get("turn_failure_kind"))

    def test_e10_08_recovery_prompt_has_notice_first_attempt_does_not(self) -> None:
        """E-10 (8): Recovery prompt file begins with correction notice; attempt 1 prompt does not."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl009", status="open", setid="set009"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-prompt-check"
                    cmd = [
                        "start",
                        "bkl009",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        if turns[0] == 1:
                            raise rs.StallTimeout("stall", session_id="ses-pr1")
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc009",
                            backlog_id6="bkl009",
                            setid="set009",
                            child_rows=[
                                (
                                    "01",
                                    "chd009",
                                    ".aw/records/plans/pending/20261004-set009-01-chd009-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd009", backlog_id6="bkl009", setid="set009"
                        )
                        return 0, "ses-pr1", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    prompts_dir = run_dir / "prompts"
                    p1_text = (prompts_dir / "01-bkl009-exec-attempt-1.md").read_text(
                        encoding="utf-8"
                    )
                    p2_text = (prompts_dir / "01-bkl009-exec-attempt-2.md").read_text(
                        encoding="utf-8"
                    )

                    self.assertNotIn("Failure kind: stall", p1_text)
                    self.assertNotIn("The previous attempt FAILED", p1_text)

                    # Prompt 2 must start with the correction notice
                    self.assertTrue(
                        p2_text.lstrip().startswith("## stall (attempt 1 of 2)")
                    )
                    self.assertIn("Failure kind: stall", p2_text)

    def test_e10_09_lane_kept_for_fix_it_on_run_end(self) -> None:
        """E-10 (9): Run ends after stall and before retry: lane survives with lane-kept-for-fix-it."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl010", status="open", setid="set010"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-stop-between"
                    cmd = [
                        "start",
                        "bkl010",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]
                    stall_lane_wt = [""]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turns[0] == 1:
                            stall_lane_wt[0] = str(target)
                            # Request stop after this call, so loop stops before attempt 2
                            runner_stop.request_stop(
                                run_dir, runner_stop.LEVEL_AFTER_CALL, requester="test"
                            )
                            # Write uncommitted plan to test snapshot
                            _write_child_plan(
                                target,
                                id6="chd010",
                                backlog_id6="bkl010",
                                setid="set010",
                            )
                            raise rs.StallTimeout(
                                "stall in turn 1", session_id="ses-stop1"
                            )
                        # Turn 2 on resume
                        _write_orchestrator_plan(
                            target,
                            id6="orc010",
                            backlog_id6="bkl010",
                            setid="set010",
                            child_rows=[
                                (
                                    "01",
                                    "chd010",
                                    ".aw/records/plans/pending/20261004-set010-01-chd010-test-child.ipd.md",
                                )
                            ],
                        )
                        return 0, "ses-stop1", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # Inspect events: lane-kept-for-fix-it must be present, NO lane-reclaimed-* for stall_lane_wt
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    kept_events = [
                        e for e in events if e.get("event") == "lane-kept-for-fix-it"
                    ]
                    self.assertEqual(len(kept_events), 1)
                    self.assertEqual(kept_events[0]["worktree"], stall_lane_wt[0])

                    reclaimed_events = [
                        e
                        for e in events
                        if e.get("event")
                        in ("lane-reclaimed-at-run-end", "lane-reclaimed-on-interrupt")
                        and e.get("worktree") == stall_lane_wt[0]
                    ]
                    self.assertEqual(reclaimed_events, [])

                    # Lane still listed in git worktree list
                    res = subprocess.run(
                        ["git", "worktree", "list", "--porcelain"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertIn(stall_lane_wt[0], res.stdout)

                    # Snapshot commit exists on the lane branch
                    branch_log = subprocess.run(
                        ["git", "log", "-n", "2", "--oneline", "aw/lane/bkl010"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertIn("WIP INTERRUPTED SNAPSHOT", branch_log.stdout)

                    # Now resume the run: clear the stop-request record so resume can proceed
                    (run_dir / "stop-request.json").unlink(missing_ok=True)
                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    attempts = item["attempts"]
                    self.assertEqual(len(attempts), 2)
                    self.assertEqual(attempts[1]["fix_it_lane"], "resumed")
                    self.assertEqual(attempts[1]["worktree"], stall_lane_wt[0])

    def test_e10_10_review_item_stalled_ends_interrupted_no_turn_correction(
        self,
    ) -> None:
        """E-10 (10): A review item that stalls still ends interrupted with no turn_correction."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_review_plan(repo, id6="rev001")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add plan"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-rev-stall"
                    cmd = [
                        "start",
                        "rev001",
                        "--action",
                        "review",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(*args: Any, **kwargs: Any) -> Any:
                        raise rs.StallTimeout("review stall", session_id="ses-rev1")

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "interrupted")
                    att = item["attempts"][0]
                    self.assertEqual(att.get("turn_failure_kind"), "stall")
                    self.assertNotIn("turn_correction", att)

    def test_e10_11_stall_inside_set_correction_turn(self) -> None:
        """E-10 (11) and E-14: A stall inside the Set-level production correction turn routes to fix-it."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl011", status="open", setid="set011"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-set-stall"
                    cmd = [
                        "start",
                        "bkl011",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turns[0] == 1:
                            # Turn 1: exit 0, missing child 02 -> enters Set correction loop
                            _write_orchestrator_plan(
                                target,
                                id6="orc011",
                                backlog_id6="bkl011",
                                setid="set011",
                                child_rows=[
                                    (
                                        "01",
                                        "cd011a",
                                        ".aw/records/plans/pending/20261004-set011-01-cd011a-test-child.ipd.md",
                                    ),
                                    (
                                        "02",
                                        "cd011b",
                                        ".aw/records/plans/pending/20261004-set011-02-cd011b-test-child.ipd.md",
                                    ),
                                ],
                            )
                            _write_child_plan(
                                target,
                                id6="cd011a",
                                backlog_id6="bkl011",
                                setid="set011",
                            )
                            return 0, "ses-turn1", rdir / "log.txt", ["cmd"]
                        elif turns[0] == 2:
                            # Set correction turn: raises StallTimeout!
                            raise rs.StallTimeout(
                                "stall inside set correction",
                                session_id="ses-corr-stall",
                            )
                        else:
                            # Fix-it recovery turn: writes missing child 02 and completes!
                            _write_child_plan(
                                target,
                                id6="cd011b",
                                backlog_id6="bkl011",
                                setid="set011",
                                order=2,
                            )
                            return 0, "ses-corr-stall", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertNotIn("driver_error", item)

                    # Check attempt 1 (which stalled in Set correction)
                    att1 = item["attempts"][0]
                    self.assertEqual(att1["turn_failure_kind"], "stall")
                    self.assertTrue(att1.get("turn_correction"))
                    self.assertEqual(att1["session_id"], "ses-corr-stall")

                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    retry_events = [
                        e for e in events if e.get("event") == "ipd-turn-retry"
                    ]
                    self.assertTrue(len(retry_events) >= 1)

    def test_e10_12_shared_tree_fix_it_committed_new_output(self) -> None:
        """E-10 (12): Shared tree (--no-isolate-worktree) fix-it completes and commits plans as new output."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl012", status="open", setid="set012"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-shared-tree"
                    cmd = [
                        "start",
                        "bkl012",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "2",
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turns = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        turns[0] += 1
                        target = repo
                        if turns[0] == 1:
                            # Write one child plan, then exit 1 (crash / no outcome)
                            _write_child_plan(
                                target,
                                id6="chd012",
                                backlog_id6="bkl012",
                                setid="set012",
                            )
                            return 1, "ses-sh1", rdir / "log.txt", ["cmd"]
                        # Turn 2: write orchestrator
                        _write_orchestrator_plan(
                            target,
                            id6="orc012",
                            backlog_id6="bkl012",
                            setid="set012",
                            child_rows=[
                                (
                                    "01",
                                    "chd012",
                                    ".aw/records/plans/pending/20261004-set012-01-chd012-test-child.ipd.md",
                                )
                            ],
                        )
                        return 0, "ses-sh1", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", _fake_probe_pass
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")

                    # Both plans must be committed as new output
                    chd_p = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20261004-set012-01-chd012-test-child.ipd.md"
                    )
                    orc_p = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20261004-set012-00-orc012-test-orch.ipd.md"
                    )
                    self.assertTrue(chd_p.is_file())
                    self.assertTrue(orc_p.is_file())

                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    out_of_scope = [
                        e
                        for e in events
                        if e.get("event") == "backlog-production-out-of-scope-paths"
                    ]
                    self.assertEqual(out_of_scope, [])
                    pre_dirty = [
                        e
                        for e in events
                        if e.get("event") == "continued-plan-pre-dirty-dropped"
                    ]
                    self.assertEqual(pre_dirty, [])

    def test_e11_reclaimed_lane_not_in_report_preserved_lane_is(self) -> None:
        """E-11: Reclaimed lane does not appear in execution report under Preserved lanes; real preserved lane does."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl013", status="open", setid="set013"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo, check=True
                    )

                    # Run A: stall with budget 0 -> empty lane is reclaimed at run end
                    run_id = f"run-{host_label}-reclaim-rpt"
                    cmd = [
                        "start",
                        "bkl013",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "0",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent_stall(*args: Any, **kwargs: Any) -> Any:
                        raise rs.StallTimeout("stall", session_id="ses-r13")

                    with _patch_host_agent(mod, fake_agent_stall):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    report_text = (run_dir / "execution-report.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertNotIn("## Preserved lanes (NOT torn down)", report_text)
                    self.assertNotIn(
                        "bkl013",
                        report_text.split("##")[-1]
                        if "##" in report_text
                        else report_text,
                    )

                # Run B: lane with unmerged commits left on disk -> preserved
                with tempfile.TemporaryDirectory() as td2:
                    repo2 = _make_test_repo(Path(td2))
                    _write_backlog_item(
                        repo2, id6="bkl014", status="open", setid="set014"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo2, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add item"], cwd=repo2, check=True
                    )

                    run_id2 = f"run-{host_label}-pres-rpt"
                    cmd2 = [
                        "start",
                        "bkl014",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo2),
                        "--run-id",
                        run_id2,
                        "--retry-budget",
                        "0",
                    ]
                    args2 = mod.build_parser().parse_args(cmd2)
                    buf2 = io.StringIO()
                    with contextlib.redirect_stdout(buf2), contextlib.redirect_stderr(
                        buf2
                    ):
                        run_dir2 = mod.initialize_run(args2)

                    def fake_agent_dirty(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        ppath: Any,
                        att_no: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        # Commit work to the lane branch so it holds unmerged commits
                        (target / "work.txt").write_text(
                            "unmerged work\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "work.txt"], cwd=target, check=True
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "lane commit"],
                            cwd=target,
                            check=True,
                        )
                        raise rs.StallTimeout("stall", session_id="ses-r14")

                    with _patch_host_agent(mod, fake_agent_dirty):
                        with contextlib.redirect_stdout(
                            buf2
                        ), contextlib.redirect_stderr(buf2):
                            mod.run_queue(run_dir2, retry_incomplete=False)

                    report_text2 = (run_dir2 / "execution-report.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("## Preserved lanes (NOT torn down)", report_text2)
                    self.assertIn("bkl014", report_text2)
                    self.assertIn("holds-unmerged-work", report_text2)
