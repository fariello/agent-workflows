"""Tests for production action orchestrator set verifiers (Order 06, Set gradcover).

Validates E-01, E-02, E-03, E-04 from IPD r2wa38:
- Direct unit tests for backlog_graduate_set and spec_plan_set against hand-built trees
  (draft child, missing child, quoted uncovered passage, ready, no orchestrator produced).
- Integration cases on both hosts (oc and agy) using initialize_run + run_queue + _patch_host_agent:
  - backlog production with draft child ends fail-gate, item open, BACKLOG-GRADUATE-SET refusal, lane preserved;
  - backlog production with ready Set ends executed, item graduated, coverage pass recorded and committed,
    probe double called exactly once, git status clean, git log shows production commit then coverage commit;
  - spec production with draft child ends fail-gate, spec approved, SPEC-PLAN-SET refusal;
  - spec production with ready Set ends executed, spec implementing, coverage pass recorded and committed;
  - ready Set whose probe double answers could-not-ask ends fail-gate naming aw ipd coverage;
  - not-ready orchestrator yields exactly one finding (no BACKLOG-GRADUATE-IPD restatement of IPD-S408).
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
    production_checks,
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
- Title: {title}
- Slug: {slug}
- Id: {id6}
{gate_line}
## Workflow history
- 2026-10-04 {status} (tester): set status

## 1. Overview
Overview of spec {id6}.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_child_plan(
    repo: Path,
    *,
    id6: str = "chd001",
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
    omit_child_table: bool = False,
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

    lines = [
        f"# IPD: Test Orchestrator {id6}",
        "",
        "- Date: 2026-10-04",
        "- Kind: orchestrator",
        f"- Id: {id6}",
        f"- Set: {setid}",
        "- Order: 0",
        f"- Status: {status}",
        f"{bkl_line}{spec_line}{gate_line}- Priority: medium",
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
    ]
    if not omit_child_table:
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
            ]
        )
        for ord_tok, c_id6, c_path in child_rows:
            lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
        lines.append("")

    lines.extend(
        [
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


class TestProductionSetCheckUnit(unittest.TestCase):
    """Unit cases for backlog_graduate_set and spec_plan_set (E-01)."""

    def test_backlog_graduate_set_draft_child(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc001", backlog_id6="bkl001", setid="set001"
            )
            _write_child_plan(
                repo, id6="chd001", backlog_id6="bkl001", setid="set001", status="draft"
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.backlog_graduate_set(
                repo,
                "bkl001",
                [orch],
                host="oc",
                run_id="run-test",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "BACKLOG-GRADUATE-SET")
            self.assertEqual(plan_id, "orc001")
            self.assertIn("chd001", msg)
            self.assertIn("draft", msg)
            self.assertIn("aw ipd set to-review chd001", msg)
            self.assertIn("aw oc run resume run-test", msg)

    def test_backlog_graduate_set_missing_child(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            child_rows = [
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
            ]
            orch = _write_orchestrator_plan(
                repo,
                id6="orc001",
                backlog_id6="bkl001",
                setid="set001",
                child_rows=child_rows,
            )
            _write_child_plan(
                repo,
                id6="chd001",
                backlog_id6="bkl001",
                setid="set001",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.backlog_graduate_set(
                repo,
                "bkl001",
                [orch],
                host="oc",
                run_id="run-test",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "BACKLOG-GRADUATE-SET")
            self.assertEqual(plan_id, "orc001")
            self.assertIn("02", msg)
            self.assertIn("author the missing child", msg)

    def test_backlog_graduate_set_quoted_uncovered_passage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc001", backlog_id6="bkl001", setid="set001"
            )
            _write_child_plan(
                repo,
                id6="chd001",
                backlog_id6="bkl001",
                setid="set001",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            fake_quote = "uncovered obligation: handle error gracefully"

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_EXECUTIONS, "fake-model", (fake_quote,))

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.backlog_graduate_set(
                repo,
                "bkl001",
                [orch],
                host="oc",
                run_id="run-test",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "BACKLOG-GRADUATE-SET")
            self.assertIn(fake_quote, msg)
            self.assertIn("assign the quoted obligation", msg)

    def test_backlog_graduate_set_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc001", backlog_id6="bkl001", setid="set001"
            )
            _write_child_plan(
                repo,
                id6="chd001",
                backlog_id6="bkl001",
                setid="set001",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.backlog_graduate_set(
                repo,
                "bkl001",
                [orch],
                host="oc",
                run_id="run-test",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(findings, [])

            orch_text = orch.read_text(encoding="utf-8")
            self.assertIn("- Coverage: pass", orch_text)
            self.assertIn("- Coverage-Fingerprint:", orch_text)
            self.assertIn("coverage pass (aw oc run)", orch_text)

    def test_backlog_graduate_set_no_orchestrator(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            chd = _write_child_plan(
                repo,
                id6="chd001",
                backlog_id6="bkl001",
                setid="set001",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add child"], cwd=repo, check=True)

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.backlog_graduate_set(
                repo, "bkl001", [chd], host="oc", run_id="run-test", state=state
            )
            self.assertEqual(findings, [])

    def test_spec_plan_set_draft_child(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc002", spec_id6="spc001", setid="set002"
            )
            _write_child_plan(
                repo, id6="chd002", spec_id6="spc001", setid="set002", status="draft"
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.spec_plan_set(
                repo,
                "spc001",
                [orch],
                host="agy",
                run_id="run-spec",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "SPEC-PLAN-SET")
            self.assertEqual(plan_id, "orc002")
            self.assertIn("chd002", msg)
            self.assertIn("draft", msg)
            self.assertIn("aw agy run resume run-spec", msg)

    def test_spec_plan_set_missing_child(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            child_rows = [
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
            ]
            orch = _write_orchestrator_plan(
                repo,
                id6="orc002",
                spec_id6="spc001",
                setid="set002",
                child_rows=child_rows,
            )
            _write_child_plan(
                repo,
                id6="chd001",
                spec_id6="spc001",
                setid="set002",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.spec_plan_set(
                repo,
                "spc001",
                [orch],
                host="oc",
                run_id="run-spec",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "SPEC-PLAN-SET")
            self.assertEqual(plan_id, "orc002")
            self.assertIn("02", msg)

    def test_spec_plan_set_quoted_uncovered_passage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc002", spec_id6="spc001", setid="set002"
            )
            _write_child_plan(
                repo,
                id6="chd002",
                spec_id6="spc001",
                setid="set002",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            fake_quote = "uncovered spec requirement R-03"

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_EXECUTIONS, "fake-model", (fake_quote,))

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.spec_plan_set(
                repo,
                "spc001",
                [orch],
                host="oc",
                run_id="run-spec",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(len(findings), 1)
            code, plan_id, msg = findings[0]
            self.assertEqual(code, "SPEC-PLAN-SET")
            self.assertIn(fake_quote, msg)

    def test_spec_plan_set_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc002", spec_id6="spc001", setid="set002"
            )
            _write_child_plan(
                repo,
                id6="chd002",
                spec_id6="spc001",
                setid="set002",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            def fake_asker(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.spec_plan_set(
                repo,
                "spc001",
                [orch],
                host="oc",
                run_id="run-spec",
                state=state,
                asker=fake_asker,
            )
            self.assertEqual(findings, [])

            orch_text = orch.read_text(encoding="utf-8")
            self.assertIn("- Coverage: pass", orch_text)
            self.assertIn("- Coverage-Fingerprint:", orch_text)
            self.assertIn("coverage pass (aw oc run)", orch_text)

    def test_spec_plan_set_no_orchestrator(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            chd = _write_child_plan(
                repo,
                id6="chd002",
                spec_id6="spc001",
                setid="set002",
                status="to-review",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add child"], cwd=repo, check=True)

            state = {"options": {}, "retry_budget": 0}
            findings = production_checks.spec_plan_set(
                repo, "spc001", [chd], host="oc", run_id="run-spec", state=state
            )
            self.assertEqual(findings, [])


class TestProductionSetCheckIntegration(unittest.TestCase):
    """Integration cases on both hosts (E-04)."""

    def test_backlog_production_draft_child_fail_gate(self) -> None:
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl301", status="open", setid="set301"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-draft"
                    cmd = [
                        "start",
                        "bkl301",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc301",
                            backlog_id6="bkl301",
                            setid="set301",
                            child_rows=[
                                (
                                    "01",
                                    "chd301",
                                    ".aw/records/plans/pending/20261004-set301-01-chd301-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target,
                            id6="chd301",
                            backlog_id6="bkl301",
                            setid="set301",
                            status="draft",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", fake_ask_probe
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-SET")

                    # Backlog item remains in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set301*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))
                    bkl_txt = bkl_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: open", bkl_txt)

    def test_backlog_production_ready_set_graduated(self) -> None:
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl302", status="open", setid="set302"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-ready"
                    cmd = [
                        "start",
                        "bkl302",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc302",
                            backlog_id6="bkl302",
                            setid="set302",
                            child_rows=[
                                (
                                    "01",
                                    "chd302",
                                    ".aw/records/plans/pending/20261004-set302-01-chd302-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target,
                            id6="chd302",
                            backlog_id6="bkl302",
                            setid="set302",
                            status="to-review",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    probe_calls = []

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls.append(host)
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", fake_ask_probe
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

                    # Exactly one probe call per produced orchestrator
                    self.assertEqual(len(probe_calls), 1)

                    # Backlog item moved to graduated/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set302*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))
                    bkl_txt = bkl_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: graduated", bkl_txt)

                    # Orchestrator plan carries Coverage: pass
                    orch_files = list(
                        repo.glob(".aw/records/plans/pending/*-orc302-*.ipd.md")
                    )
                    self.assertEqual(len(orch_files), 1)
                    orch_p = orch_files[0]
                    orch_txt = orch_p.read_text(encoding="utf-8")
                    self.assertIn("- Coverage: pass", orch_txt)

                    # git status --porcelain on orchestrator is empty
                    rel_orch = str(orch_p.relative_to(repo)).replace("\\", "/")
                    st_proc = subprocess.run(
                        ["git", "status", "--porcelain", "--", rel_orch],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertEqual(st_proc.stdout.strip(), "")

                    # git log lists coverage commit after production commit
                    log_proc = subprocess.run(
                        ["git", "log", "--format=%s", "--", rel_orch],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    commits = log_proc.stdout.strip().splitlines()
                    self.assertTrue(len(commits) >= 2)
                    self.assertIn("coverage(", commits[0])
                    self.assertIn("work(", commits[1])

    def test_spec_production_unready_child_fail_gate(self) -> None:
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc301", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spec-fail"
                    cmd = [
                        "start",
                        "spc301",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc303",
                            spec_id6="spc301",
                            setid="spc301",
                            child_rows=[
                                (
                                    "01",
                                    "chd303",
                                    ".aw/records/plans/pending/20261004-spc301-01-chd303-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target,
                            id6="chd303",
                            spec_id6="spc301",
                            setid="spc301",
                            status="draft",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", fake_ask_probe
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-SET")

                    # Spec remains approved
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20261004-spc301*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    self.assertIn("/approved/", str(spec_files[0]).replace("\\", "/"))
                    spec_txt = spec_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: approved", spec_txt)

    def test_spec_production_ready_set_implementing(self) -> None:
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc302", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-spec-ready"
                    cmd = [
                        "start",
                        "spc302",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_orchestrator_plan(
                            target,
                            id6="orc304",
                            spec_id6="spc302",
                            setid="spc302",
                            child_rows=[
                                (
                                    "01",
                                    "chd304",
                                    ".aw/records/plans/pending/20261004-spc302-01-chd304-test-child.ipd.md",
                                )
                            ],
                        )
                        _write_child_plan(
                            target,
                            id6="chd304",
                            spec_id6="spc302",
                            setid="spc302",
                            status="to-review",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    probe_calls = []

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls.append(host)
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", fake_ask_probe
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

                    # Exactly one probe call per produced orchestrator
                    self.assertEqual(len(probe_calls), 1)

                    # Spec moved to implementing/
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20261004-spc302*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    self.assertIn(
                        "/implementing/", str(spec_files[0]).replace("\\", "/")
                    )
                    spec_txt = spec_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: implementing", spec_txt)

    def test_backlog_production_could_not_ask(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl303", status="open", setid="set303")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
            )

            mod = oc_runipd
            run_id = "run-oc-couldnotask"
            cmd = [
                "start",
                "bkl303",
                "--action",
                "plan",
                "--repo",
                str(repo),
                "--run-id",
                run_id,
                "--no-isolate-worktree",
            ]
            args = mod.build_parser().parse_args(cmd)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
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
                work_dir = kwargs.get("work_dir")
                target = Path(work_dir) if work_dir else Path(state["repo"])
                _write_orchestrator_plan(
                    target,
                    id6="orc305",
                    backlog_id6="bkl303",
                    setid="set303",
                    child_rows=[
                        (
                            "01",
                            "chd305",
                            ".aw/records/plans/pending/20261004-set303-01-chd305-test-child.ipd.md",
                        )
                    ],
                )
                _write_child_plan(
                    target,
                    id6="chd305",
                    backlog_id6="bkl303",
                    setid="set303",
                    status="to-review",
                )
                return 0, "session", rdir / "log.txt", ["cmd"]

            def fake_ask_probe(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (rs.PROBE_ANSWER_COULD_NOT_ASK, "probe host unreachable", ())

            with _patch_host_agent(mod, fake_agent), mock.patch.object(
                rs, "ask_orchestrator_probe", fake_ask_probe
            ):
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    mod.run_queue(run_dir, retry_incomplete=False)

            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            item = state["queue"][0]
            self.assertEqual(item["status"], "fail-gate")
            refusal = item.get("refusal") or {}
            self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-SET")
            self.assertIn(
                "aw ipd coverage",
                (refusal.get("reason", "") + refusal.get("remedy", "")),
            )

            # Backlog item remains in open/
            bkl_files = list(
                repo.glob(".aw/records/backlog/**/20261004-set303*.backlog.md")
            )
            self.assertEqual(len(bkl_files), 1)
            self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))
            bkl_txt = bkl_files[0].read_text(encoding="utf-8")
            self.assertIn("- Status: open", bkl_txt)

    def test_single_finding_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl304", status="open", setid="set304")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
            )

            mod = oc_runipd
            run_id = "run-oc-dedup"
            cmd = [
                "start",
                "bkl304",
                "--action",
                "plan",
                "--repo",
                str(repo),
                "--run-id",
                run_id,
                "--no-isolate-worktree",
            ]
            args = mod.build_parser().parse_args(cmd)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
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
                work_dir = kwargs.get("work_dir")
                target = Path(work_dir) if work_dir else Path(state["repo"])
                _write_orchestrator_plan(
                    target,
                    id6="orc306",
                    backlog_id6="bkl304",
                    setid="set304",
                    child_rows=[
                        (
                            "01",
                            "chd306",
                            ".aw/records/plans/pending/20261004-set304-01-chd306-test-child.ipd.md",
                        )
                    ],
                )
                _write_child_plan(
                    target,
                    id6="chd306",
                    backlog_id6="bkl304",
                    setid="set304",
                    status="to-review",
                )
                return 0, "session", rdir / "log.txt", ["cmd"]

            def fake_ask_probe(
                state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
            ) -> tuple[str, str, tuple[str, ...]]:
                return (
                    rs.PROBE_ANSWER_EXECUTIONS,
                    "fake-model",
                    ("uncovered work passage",),
                )

            with _patch_host_agent(mod, fake_agent), mock.patch.object(
                rs, "ask_orchestrator_probe", fake_ask_probe
            ):
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    mod.run_queue(run_dir, retry_incomplete=False)

            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            item = state["queue"][0]
            self.assertEqual(item["status"], "fail-gate")
            refusal = item.get("refusal") or {}
            self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-SET")

            # Verify deduplication: BACKLOG-GRADUATE-SET is present, but NO BACKLOG-GRADUATE-IPD
            # restatement of IPD-S408 appears in runner stderr
            stderr_out = buf.getvalue()
            self.assertIn(
                "Backlog production refused [BACKLOG-GRADUATE-SET]", stderr_out
            )
            self.assertNotIn(
                "Backlog production refused [BACKLOG-GRADUATE-IPD]", stderr_out
            )
            self.assertNotIn("IPD-S408", stderr_out)
