"""Tests for bounded correction turns on refused production and review actions (IPD nnsa2o).

Covers:
- E-01: production_set_retry_decision unit cases (budget, exhausted, mixed, idempotency key).
- E-02: production correction loop for backlog and spec production (fixed on first turn,
  never fixed / exhausted with budget 2, budget 0, mixed findings).
- E-03: review orchestrator readiness check, demotion, remand, and outcome (c) record-missing.
- E-04: attempt records, events, execution report lines, and refusal strings on exhaustion.
- E-05: all eight required scenarios on both hosts (oc and agy).
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
    agy_runipd,
    oc_runipd,
    runner_shared as rs,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_backlog_item(
    repo: Path,
    *,
    id6: str,
    status: str = "open",
    summary: str = "Test backlog item",
    slug: str = "test-item",
    gate: str | None = None,
    work_kind: str = "feature",
    priority: str = "high",
    setid: str | None = None,
) -> Path:
    bkl_dir = repo / ".aw" / "records" / "backlog" / status
    bkl_dir.mkdir(parents=True, exist_ok=True)
    if setid is None:
        setid = id6
    file_path = bkl_dir / f"20261004-{setid}-01-{id6}-{slug}.backlog.md"

    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    content = f"""- Id: {id6}
- Status: {status}
- Set: {setid}
{gate_line}- Priority: {priority}
- Work-Kind: {work_kind}
- Summary: {summary}

## Workflow history
- 2026-10-04 {status} (tester): created item
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_spec(
    repo: Path,
    *,
    id6: str,
    status: str = "approved",
    title: str = "Test Spec",
    slug: str = "test-spec",
    gate: str | None = None,
) -> Path:
    bucket = "approved" if status == "approved" else status
    specs_dir = repo / ".aw" / "records" / "specs" / bucket
    specs_dir.mkdir(parents=True, exist_ok=True)
    file_path = specs_dir / f"20261004-{id6}-01-{id6}-{slug}.spec.md"

    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    content = f"""# SPEC: {title}

- Date: 2026-10-04
- Status: {status}
{gate_line}- Id: {id6}

## Workflow history
- 2026-10-04 {status} (tester): created spec
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


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


def _patch_host_agent(module: Any, agent_fn: Any) -> Any:
    if module is oc_runipd:
        return mock.patch.object(oc_runipd, "run_opencode", agent_fn)

    def _agy_wrapper(
        state: Any,
        run_dir: Any,
        item: Any,
        prompt_path: Any,
        attempt_no: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        work_dir = kwargs.get("work_dir")
        root = Path(work_dir) if work_dir else Path(state.get("repo", "."))
        plan_path = rs.queue_artifact_path(root, item)
        return agent_fn(
            state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
        )

    return mock.patch.object(agy_runipd, "run_agy_turn", _agy_wrapper)


def _fake_probe_pass(
    state: Any,
    excerpt: str,
    host: str,
    repo: Path,
    runner: Any = None,
) -> tuple[str, str, tuple[str, ...]]:
    return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())


class TestProductionCorrectionTurn(unittest.TestCase):
    """Test suite validating IPD nnsa2o."""

    def test_e01_production_set_retry_decision_unit(self) -> None:
        """V-01: Unit test for production_set_retry_decision across budget, exhausted, mixed, repeated key."""
        state = {"options": {}, "retry_budget": 2}
        item: dict[str, Any] = {"id6": "bkl001"}

        # 1. Set-only findings under budget -> retry=True, exhausted=False
        findings = [
            ("BACKLOG-GRADUATE-SET", "orc001", "orchestrator not ready"),
            ("SPEC-PLAN-SET", "orc002", "spec orchestrator not ready"),
        ]
        dec = rs.production_set_retry_decision(item, state, findings, attempt_no=1)
        self.assertTrue(dec.retry)
        self.assertFalse(dec.exhausted)
        self.assertEqual(dec.attempts, 0)
        self.assertEqual(dec.budget, 2)
        self.assertEqual(dec.key, "bkl001:production-set-attempt-1")

        # 2. Repeated key -> retry=False, exhausted=False, no spend (idempotency)
        item_spent = {
            "id6": "bkl001",
            rs.PRODUCTION_SET_RETRY_KEYS_KEY: ["bkl001:production-set-attempt-1"],
            rs.PRODUCTION_SET_RETRY_COUNT_KEY: 1,
        }
        dec_spent = rs.production_set_retry_decision(
            item_spent, state, findings, attempt_no=1
        )
        self.assertFalse(dec_spent.retry)
        self.assertFalse(dec_spent.exhausted)
        self.assertIn("ALREADY recorded", dec_spent.reason)

        # 3. Budget exhausted -> retry=False, exhausted=True
        item_exhausted = {
            "id6": "bkl001",
            rs.PRODUCTION_SET_RETRY_COUNT_KEY: 2,
        }
        dec_ex = rs.production_set_retry_decision(
            item_exhausted, state, findings, attempt_no=3
        )
        self.assertFalse(dec_ex.retry)
        self.assertTrue(dec_ex.exhausted)
        self.assertIn("budget is exhausted", dec_ex.reason)

        # 4. Mixed findings (non-set finding present) -> retry=False, exhausted=False
        mixed_findings = [
            ("BACKLOG-GRADUATE-SET", "orc001", "orchestrator not ready"),
            ("BACKLOG-GRADUATE-IPD", "orc001", "check.from-backlog failed"),
        ]
        dec_mixed = rs.production_set_retry_decision(
            item, state, mixed_findings, attempt_no=1
        )
        self.assertFalse(dec_mixed.retry)
        self.assertFalse(dec_mixed.exhausted)
        self.assertIn(
            "not in the retryable Set-level production classes", dec_mixed.reason
        )

    def test_e02_backlog_production_fixed_on_first_correction(self) -> None:
        """E-02, E-05 (1): Backlog production fixed on 1st correction turn -> source graduated, 1 correction turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl001", status="open", setid="set001"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-fix1"
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
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turn_counter[0] == 1:
                            # Turn 1: Orchestrator names chd001 and chd002, but only chd001 is written
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
                                    ),
                                    (
                                        "02",
                                        "chd002",
                                        ".aw/records/plans/pending/20261004-set001-02-chd002-test-child.ipd.md",
                                    ),
                                ],
                            )
                            _write_child_plan(
                                target,
                                id6="chd001",
                                backlog_id6="bkl001",
                                setid="set001",
                            )
                        else:
                            # Correction turn 1: Agent authors the missing child chd002
                            _write_child_plan(
                                target,
                                id6="chd002",
                                backlog_id6="bkl001",
                                setid="set001",
                                order=2,
                            )
                        return 0, "session-1", rdir / "log.txt", ["cmd"]

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

                    # Assert item graduated and executed
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(rs.production_set_retry_attempts(item), 1)

                    # Backlog file transitioned to graduated
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set001*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))
                    self.assertIn(
                        "- Status: graduated", bkl_files[0].read_text(encoding="utf-8")
                    )

                    # Assert correction recorded in attempts
                    corrections = [
                        a
                        for a in item["attempts"]
                        if a.get("action") == "production-set-correction"
                    ]
                    self.assertEqual(len(corrections), 1)
                    self.assertEqual(corrections[0]["turn"], 1)
                    self.assertTrue(len(corrections[0]["findings_given"]) > 0)
                    self.assertEqual(len(corrections[0]["findings_after"]), 0)

                    # Assert report line in execution-report.md
                    report_text = (run_dir / "execution-report.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("## Correction turns", report_text)
                    self.assertIn("`bkl001`: 1 correction turn", report_text)

    def test_e02_backlog_production_never_fixed_exhausted(self) -> None:
        """E-02, E-05 (2): Never fixed with budget 2 -> 2 correction turns, fail-gate, item open."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl002", status="open", setid="set002"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-never"
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
                        "--no-isolate-worktree",
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
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        # Always leave chd002 missing
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
                                ),
                                (
                                    "02",
                                    "chd002",
                                    ".aw/records/plans/pending/20261004-set002-02-chd002-test-child.ipd.md",
                                ),
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd001", backlog_id6="bkl002", setid="set002"
                        )
                        return 0, "session-1", rdir / "log.txt", ["cmd"]

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

                    # Assert item fail-gate and 2 turns consumed
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertEqual(rs.production_set_retry_attempts(item), 2)

                    # Backlog item remains open
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set002*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))
                    self.assertIn(
                        "- Status: open", bkl_files[0].read_text(encoding="utf-8")
                    )

                    # Refusal names turns spent
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-SET")
                    self.assertIn(
                        "correction budget exhausted (2 correction turns spent)",
                        refusal.get("reason", ""),
                    )

    def test_e02_budget_zero(self) -> None:
        """E-05 (3): Budget 0 -> no correction turn, immediate fail-gate."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl003", status="open", setid="set003"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-b0"
                    cmd = [
                        "start",
                        "bkl003",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "0",
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc003",
                            backlog_id6="bkl003",
                            setid="set003",
                            child_rows=[
                                (
                                    "01",
                                    "chd001",
                                    ".aw/records/plans/pending/20261004-set003-01-chd001-test-child.ipd.md",
                                ),
                                (
                                    "02",
                                    "chd002",
                                    ".aw/records/plans/pending/20261004-set003-02-chd002-test-child.ipd.md",
                                ),
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd001", backlog_id6="bkl003", setid="set003"
                        )
                        return 0, "session-1", rdir / "log.txt", ["cmd"]

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

                    self.assertEqual(turn_counter[0], 1)
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertEqual(rs.production_set_retry_attempts(item), 0)

    def test_e02_mixed_findings_no_retry(self) -> None:
        """E-05 (4): Mixed findings list -> no correction turn, immediate fail-gate."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl004", status="open", setid="set004"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-mix"
                    cmd = [
                        "start",
                        "bkl004",
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

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        # Orchestrator has missing child AND mismatched From-Backlog (causes BACKLOG-GRADUATE-IPD)
                        _write_orchestrator_plan(
                            target,
                            id6="orc004",
                            backlog_id6="bkl999",  # mismatched!
                            setid="set004",
                            child_rows=[
                                (
                                    "01",
                                    "chd001",
                                    ".aw/records/plans/pending/20261004-set004-01-chd001-test-child.ipd.md",
                                ),
                                (
                                    "02",
                                    "chd002",
                                    ".aw/records/plans/pending/20261004-set004-02-chd002-test-child.ipd.md",
                                ),
                            ],
                        )
                        _write_child_plan(
                            target, id6="chd001", backlog_id6="bkl004", setid="set004"
                        )
                        return 0, "session-1", rdir / "log.txt", ["cmd"]

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

                    self.assertEqual(turn_counter[0], 1)
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertEqual(rs.production_set_retry_attempts(item), 0)

    def test_e02_spec_production_fixed_on_first_correction(self) -> None:
        """E-05 (5): Spec production twin of first case -> spec implementing, 1 correction turn."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spc1"
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
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turn_counter[0] == 1:
                            _write_orchestrator_plan(
                                target,
                                id6="orc101",
                                spec_id6="spc001",
                                setid="set101",
                                child_rows=[
                                    (
                                        "01",
                                        "chd101",
                                        ".aw/records/plans/pending/20261004-set101-01-chd101-test-child.ipd.md",
                                    ),
                                    (
                                        "02",
                                        "chd102",
                                        ".aw/records/plans/pending/20261004-set101-02-chd102-test-child.ipd.md",
                                    ),
                                ],
                            )
                            _write_child_plan(
                                target, id6="chd101", spec_id6="spc001", setid="set101"
                            )
                        else:
                            _write_child_plan(
                                target,
                                id6="chd102",
                                spec_id6="spc001",
                                setid="set101",
                                order=2,
                            )
                        return 0, "session-1", rdir / "log.txt", ["cmd"]

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

                    # Spec implementing, item executed
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(rs.production_set_retry_attempts(item), 1)

                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20261004-spc001*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    self.assertIn(
                        "/implementing/", str(spec_files[0]).replace("\\", "/")
                    )

    def test_e03_review_orchestrator_fixed_and_exhausted(self) -> None:
        """E-03, E-05 (6): Review twin: fixed ends reviewed; exhausted ends to-review without Readiness and fail-gate."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label, case="fixed"):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_orchestrator_plan(
                        repo,
                        id6="orcrev",
                        setid="setrev",
                        status="to-review",
                        child_rows=[
                            (
                                "01",
                                "chd001",
                                ".aw/records/plans/pending/20261004-setrev-01-chd001-test-child.ipd.md",
                            ),
                            (
                                "02",
                                "chd002",
                                ".aw/records/plans/pending/20261004-setrev-02-chd002-test-child.ipd.md",
                            ),
                        ],
                    )
                    _write_child_plan(repo, id6="chd001", setid="setrev")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-rev-fix"
                    cmd = [
                        "start",
                        "orcrev",
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

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turn_counter[0] == 1:
                            # Sets reviewed in file directly (to test demotion and remand)
                            p = list(
                                target.glob(
                                    ".aw/records/plans/**/20261004-setrev-00-orcrev*.ipd.md"
                                )
                            )[0]
                            p.write_text(
                                p.read_text(encoding="utf-8").replace(
                                    "- Status: to-review",
                                    "- Status: reviewed\n- Readiness: go-pending-approval",
                                ),
                                encoding="utf-8",
                            )
                        else:
                            # Correction turn: authors chd002 and sets reviewed with coverage
                            from agent_workflows import coverage_record as _cr

                            _write_child_plan(
                                target, id6="chd002", setid="setrev", order=2
                            )
                            p = list(
                                target.glob(
                                    ".aw/records/plans/**/20261004-setrev-00-orcrev*.ipd.md"
                                )
                            )[0]
                            _cr.write(p, _cr.COVERAGE_PASS, repo=target, commit=True)
                            subprocess.run(
                                [
                                    "python3",
                                    "-m",
                                    "agent_workflows",
                                    "ipd",
                                    "set",
                                    "reviewed",
                                    "orcrev",
                                    "--message",
                                    "fixed",
                                    "--yes",
                                    "--dir",
                                    str(target),
                                ],
                                check=True,
                            )
                        return 0, "session-rev", rdir / "log.txt", ["cmd"]

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
                    self.assertEqual(item["status"], "reviewed")
                    self.assertEqual(rs.review_orchestrator_retry_attempts(item), 1)

            with self.subTest(host=host_label, case="exhausted"):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_orchestrator_plan(
                        repo,
                        id6="orce01",
                        setid="setex",
                        status="to-review",
                        child_rows=[
                            (
                                "01",
                                "chd001",
                                ".aw/records/plans/pending/20261004-setex-01-chd001-test-child.ipd.md",
                            ),
                            (
                                "02",
                                "chd002",
                                ".aw/records/plans/pending/20261004-setex-02-chd002-test-child.ipd.md",
                            ),
                        ],
                    )
                    _write_child_plan(repo, id6="chd001", setid="setex")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-rev-ex"
                    cmd = [
                        "start",
                        "orce01",
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

                    def fake_agent_ex(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        # Keeps setting reviewed without fixing chd002
                        p = list(
                            target.glob(
                                ".aw/records/plans/**/20261004-setex-00-orce01*.ipd.md"
                            )
                        )[0]
                        p.write_text(
                            p.read_text(encoding="utf-8").replace(
                                "- Status: to-review",
                                "- Status: reviewed\n- Readiness: go-pending-approval",
                            ),
                            encoding="utf-8",
                        )
                        return 0, "session-rev", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_ex), mock.patch.object(
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

                    # Item fail-gate, 2 turns consumed
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertEqual(rs.review_orchestrator_retry_attempts(item), 2)

                    # Plan on disk remains to-review and has NO - Readiness: line
                    plan_p = list(
                        repo.glob(
                            ".aw/records/plans/**/20261004-setex-00-orce01*.ipd.md"
                        )
                    )[0]
                    plan_txt = plan_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: to-review", plan_txt)
                    self.assertNotIn("- Readiness:", plan_txt)

                    refusal = item.get("refusal") or {}
                    self.assertEqual(
                        refusal.get("code"), "IPD-REVIEW-ORCHESTRATOR-READY"
                    )
                    self.assertIn(
                        "correction budget exhausted (2 correction turns spent)",
                        refusal.get("reason", ""),
                    )

    def test_e03_review_orchestrator_record_missing_outcome_c(self) -> None:
        """E-03 (c), E-05 (7): Record-missing review case on both hosts; asserts session kwargs."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    # Complete Set on disk with coverage pass recorded
                    _write_orchestrator_plan(
                        repo,
                        id6="orcrec",
                        setid="setrec",
                        status="to-review",
                        child_rows=[
                            (
                                "01",
                                "chd001",
                                ".aw/records/plans/pending/20261004-setrec-01-chd001-test-child.ipd.md",
                            ),
                        ],
                    )
                    _write_child_plan(repo, id6="chd001", setid="setrec")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c"
                    cmd = [
                        "start",
                        "orcrec",
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

                    turn_counter = [0]
                    recorded_kwargs: list[dict[str, Any]] = []

                    def fake_agent_c(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        recorded_kwargs.append(dict(kwargs))
                        target = Path(kwargs.get("work_dir") or state["repo"])
                        if turn_counter[0] == 1:
                            # Turn 1 leaves status to-review (setter refused before coverage record existed)
                            pass
                        else:
                            # Turn 2: runs reviewed transition now that record exists
                            subprocess.run(
                                [
                                    "python3",
                                    "-m",
                                    "agent_workflows",
                                    "ipd",
                                    "set",
                                    "reviewed",
                                    "orcrec",
                                    "--message",
                                    "coverage present",
                                    "--yes",
                                    "--dir",
                                    str(target),
                                ],
                                check=True,
                            )
                        return 0, "session-c-123", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_c), mock.patch.object(
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

                    # 1 correction turn used, ends reviewed
                    self.assertEqual(item["status"], "reviewed")
                    self.assertEqual(rs.review_orchestrator_retry_attempts(item), 1)

                    # Verify host-specific resume kwargs on the correction turn (turn 2)
                    self.assertEqual(len(recorded_kwargs), 2)
                    corr_kw = recorded_kwargs[1]
                    if host_label == "oc":
                        self.assertEqual(corr_kw.get("resume_session"), "session-c-123")
                    else:
                        self.assertEqual(corr_kw.get("session_id"), "session-c-123")
                        self.assertFalse(corr_kw.get("use_continue", True))

    def test_e02_correction_prompt_contents(self) -> None:
        """E-05 (8): Correction prompt contains quoted passage and the 'never delete the checklist' rule."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_orchestrator_plan(
                repo,
                id6="orcpmt",
                setid="setpmt",
                child_rows=[
                    (
                        "01",
                        "chd001",
                        ".aw/records/plans/pending/20261004-setpmt-01-chd001-test-child.ipd.md",
                    ),
                    (
                        "02",
                        "chd002",
                        ".aw/records/plans/pending/20261004-setpmt-02-chd002-test-child.ipd.md",
                    ),
                ],
            )
            _write_child_plan(repo, id6="chd001", setid="setpmt")

            findings = [
                (
                    "BACKLOG-GRADUATE-SET",
                    "orcpmt",
                    "Orchestrator orcpmt is not ready: chd002: child plan declared in child table does not exist on disk",
                )
            ]
            item = {"id6": "bklpmt"}
            decision = rs.ProductionSetRetryDecision(
                retry=True,
                exhausted=False,
                reason="retry",
                attempts=0,
                budget=2,
                key="bklpmt:production-set-attempt-1",
            )
            prompt = rs.build_production_set_correction_prompt(
                item, findings, repo, attempt_no=1, decision=decision
            )

            # Assert required passages
            self.assertIn("never delete the checklist", prompt)
            self.assertIn(
                "Every whole-Set obligation must name the child that performs it",
                prompt,
            )
            self.assertIn("child-unauthored", prompt)
            self.assertIn("resolves to no plan on disk", prompt)


if __name__ == "__main__":
    unittest.main()
