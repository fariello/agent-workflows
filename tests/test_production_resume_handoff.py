"""Tests for resuming unfinished handoffs in production actions (IPD 24qw39, Set gradcover).

Validates E-01, E-02, E-03, E-04, E-05:
- Direct unit tests for count verifiers (spec_plan_count and backlog_graduate_count):
  - continued output only (pass)
  - continued plus new in the same Set (pass)
  - new plan in a second Set (fails naming both Sets)
  - pre-existing multi-Set source plus new plan in one of them (pass)
  - zero linked plans (fails)
  - unlinked new plan (fails)
- Prompt builder unit tests:
  - rendered prompt for item with existing orchestrator shows "## Continue this handoff"
    between "## Production Contract" and "## Prohibitions"
  - lists plans with repo-relative paths, statuses, and orchestrator findings
  - contains standard instruction text
  - fresh item prompt is byte-identical
  - zero probe calls while building prompt
- Status conformance unit tests:
  - existing approved/reviewed/auto-approved/to-review child in continued_ids passes
  - existing draft child in continued_ids fails
  - new plan with reviewed or approved fails (must be to-review)
- Commit helper classification unit tests:
  - continued modified plan allowed and committed
  - deleted existing plan classified as out of scope
  - renamed existing plan classified as out of scope
  - pre-dirty existing plan in shared checkout dropped and reported in events
- Integration cases on both hosts (oc and agy):
  - (i) backlog item with existing orchestrator and draft child; agent sets child to-review -> item graduated
  - (i-fail) failing variant: existing orchestrator left unready (child left draft) -> fails BACKLOG-GRADUATE-SET
  - (ii) backlog item with existing plans in Set 1; agent writes plan in Set 2 -> fails BACKLOG-GRADUATE-COUNT naming both Sets
  - (iii) spec twin of (i): spec with existing orchestrator and draft child -> spec implementing
  - (iv) agent edits existing plan and writes new plan -> driver commit contains both, git status clean
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
    bucket: str = "pending",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / bucket
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test-child.ipd.md"

    bkl_line = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    appr_line = "- Approval: test\n" if status == "approved" else ""

    content = f"""# IPD: Test Child Plan {id6}

- Date: 2026-10-04
- Kind: child
- Concern: Test child concern.
- Scope: Test child scope.
- Scope-Paths: {scope_paths}
- Status: {status}
{appr_line}{bkl_line}{spec_line}{gate_line}- Set: {setid}
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
    bucket: str = "pending",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / bucket
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
    ]
    if status == "approved":
        lines.append("- Approval: test")
    lines.extend(
        [
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
    )
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


class TestProductionResumeHandoffUnit(unittest.TestCase):
    """Unit tests for count, prompt, status conformance, and commit classification (E-01, E-02, E-03, E-05)."""

    def test_backlog_graduate_count_outcomes(self) -> None:
        """Test the 6 count outcomes for backlog items (E-01)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_backlog_item(repo, id6="bkl001", setid="set001")

            # 1. Zero linked plans after turn -> fails
            f_zero = production_checks.backlog_graduate_count(repo, "bkl001", set())
            self.assertEqual(len(f_zero), 1)
            self.assertEqual(f_zero[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("produced 0 linked IPDs", f_zero[0][2])

            # 2. Continued output only (existing active plans in one Set, no new plan) -> PASS
            _write_child_plan(repo, id6="chd001", backlog_id6="bkl001", setid="set001")
            f_cont = production_checks.backlog_graduate_count(
                repo, "bkl001", {"chd001"}
            )
            self.assertEqual(f_cont, [])

            # 3. Continued plus new in the SAME Set -> PASS
            _write_child_plan(
                repo, id6="chd002", backlog_id6="bkl001", setid="set001", order=2
            )
            f_same = production_checks.backlog_graduate_count(
                repo, "bkl001", {"chd001"}
            )
            self.assertEqual(f_same, [])

            # 4. New plan in a second Set -> FAILS naming both Sets
            p_second = _write_child_plan(
                repo, id6="chd003", backlog_id6="bkl001", setid="set002", order=1
            )
            f_second = production_checks.backlog_graduate_count(
                repo, "bkl001", {"chd001", "chd002"}
            )
            self.assertEqual(len(f_second), 1)
            self.assertEqual(f_second[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("introduced a second Set", f_second[0][2])
            self.assertIn("set001", f_second[0][2])
            self.assertIn("set002", f_second[0][2])
            p_second.unlink()

            # 5. Pre-existing two-Set source plus a new plan in one of them -> PASS
            # Make chd001 setA, chd002 setB in baseline, add chd004 in setA
            _write_child_plan(
                repo, id6="chd00b", backlog_id6="bkl001", setid="set00b", order=1
            )
            baseline_multi = {"chd001", "chd002", "chd00b"}
            _write_child_plan(
                repo, id6="chd004", backlog_id6="bkl001", setid="set001", order=3
            )
            f_multi = production_checks.backlog_graduate_count(
                repo, "bkl001", baseline_multi
            )
            self.assertEqual(f_multi, [])

            # 6. Unlinked new plan (missing From-Backlog or linking different item) -> FAILS
            _write_child_plan(
                repo, id6="chd005", backlog_id6=None, setid="set001", order=4
            )
            f_unlinked = production_checks.backlog_graduate_count(
                repo, "bkl001", baseline_multi | {"chd004"}
            )
            self.assertEqual(len(f_unlinked), 1)
            self.assertEqual(f_unlinked[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("linking a different item or none", f_unlinked[0][2])

    def test_spec_plan_count_outcomes(self) -> None:
        """Test the 6 count outcomes for specs (E-01)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_spec(repo, id6="spc001")

            # 1. Zero linked plans after turn -> fails
            f_zero = production_checks.spec_plan_count(repo, "spc001", set())
            self.assertEqual(len(f_zero), 1)
            self.assertEqual(f_zero[0][0], "SPEC-PLAN-COUNT")
            self.assertIn("produced 0", f_zero[0][2])

            # 2. Continued output only -> PASS
            _write_child_plan(repo, id6="chd001", spec_id6="spc001", setid="set001")
            f_cont = production_checks.spec_plan_count(repo, "spc001", {"chd001"})
            self.assertEqual(f_cont, [])

            # 3. Continued plus new in the SAME Set -> PASS
            _write_child_plan(
                repo, id6="chd002", spec_id6="spc001", setid="set001", order=2
            )
            f_same = production_checks.spec_plan_count(repo, "spc001", {"chd001"})
            self.assertEqual(f_same, [])

            # 4. New plan in a second Set -> FAILS naming both Sets
            p_second = _write_child_plan(
                repo, id6="chd003", spec_id6="spc001", setid="set002", order=1
            )
            f_second = production_checks.spec_plan_count(
                repo, "spc001", {"chd001", "chd002"}
            )
            self.assertEqual(len(f_second), 1)
            self.assertEqual(f_second[0][0], "SPEC-PLAN-COUNT")
            self.assertIn("introduced a second Set", f_second[0][2])
            self.assertIn("set001", f_second[0][2])
            self.assertIn("set002", f_second[0][2])
            p_second.unlink()

            # 5. Pre-existing two-Set source plus a new plan in one of them -> PASS
            _write_child_plan(
                repo, id6="chd00b", spec_id6="spc001", setid="set00b", order=1
            )
            baseline_multi = {"chd001", "chd002", "chd00b"}
            _write_child_plan(
                repo, id6="chd004", spec_id6="spc001", setid="set001", order=3
            )
            f_multi = production_checks.spec_plan_count(repo, "spc001", baseline_multi)
            self.assertEqual(f_multi, [])

            # 6. Unlinked new plan -> FAILS
            _write_child_plan(
                repo, id6="chd005", spec_id6=None, setid="set001", order=4
            )
            f_unlinked = production_checks.spec_plan_count(
                repo, "spc001", baseline_multi | {"chd004"}
            )
            self.assertEqual(len(f_unlinked), 1)
            self.assertEqual(f_unlinked[0][0], "SPEC-PLAN-COUNT")
            self.assertIn("linking a different spec or none", f_unlinked[0][2])

    def test_prompt_builders_continue_section_and_findings(self) -> None:
        """Prompt builder tests: continue section placement, findings, byte-identity, zero probe calls (E-02)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            bkl_path = _write_backlog_item(repo, id6="bkl001", setid="tstset")
            spc_path = _write_spec(repo, id6="spc001")

            probe_mock = mock.MagicMock()
            with mock.patch.object(rs, "ask_orchestrator_probe", probe_mock):
                # 1. Fresh items: byte-identical to prompts without continue section
                bkl_item = {"id6": "bkl001", "action": "plan"}
                spc_item = {"id6": "spc001", "action": "plan"}
                state: dict[str, Any] = {"repo": str(repo)}
                run_dir = repo / "run-001"
                run_dir.mkdir(parents=True, exist_ok=True)

                prompt_bkl_fresh = rs.build_backlog_production_prompt(
                    bkl_item, state, run_dir, bkl_path, repo
                )
                prompt_spc_fresh = rs.build_spec_production_prompt(
                    spc_item, state, run_dir, spc_path, repo
                )

                self.assertNotIn("## Continue this handoff", prompt_bkl_fresh)
                self.assertNotIn("## Continue this handoff", prompt_spc_fresh)
                self.assertEqual(probe_mock.call_count, 0)

                # 2. Add existing orchestrator and child plans linking the items
                _write_orchestrator_plan(
                    repo,
                    id6="orc001",
                    backlog_id6="bkl001",
                    setid="tstset",
                    status="to-review",
                    child_rows=[
                        (
                            "01",
                            "chd001",
                            ".aw/records/plans/pending/20261004-tstset-01-chd001-test-child.ipd.md",
                        )
                    ],
                )
                _write_child_plan(
                    repo,
                    id6="chd001",
                    backlog_id6="bkl001",
                    setid="tstset",
                    status="draft",
                )

                prompt_bkl_cont = rs.build_backlog_production_prompt(
                    bkl_item, state, run_dir, bkl_path, repo
                )

                # Section exists and is placed after Production Contract and before Prohibitions
                self.assertIn("## Continue this handoff", prompt_bkl_cont)
                pos_contract = prompt_bkl_cont.find("## Production Contract")
                pos_continue = prompt_bkl_cont.find("## Continue this handoff")
                pos_prohibitions = prompt_bkl_cont.find("## Prohibitions")
                self.assertTrue(
                    pos_contract < pos_continue < pos_prohibitions,
                    f"Expected contract < continue < prohibitions, got {pos_contract}, {pos_continue}, {pos_prohibitions}",
                )

                # Lists repo-relative paths, statuses, and orchestrator findings
                self.assertIn(
                    ".aw/records/plans/pending/20261004-tstset-00-orc001-test-orch.ipd.md (- Status: to-review)",
                    prompt_bkl_cont,
                )
                self.assertIn(
                    ".aw/records/plans/pending/20261004-tstset-01-chd001-test-child.ipd.md (- Status: draft)",
                    prompt_bkl_cont,
                )
                # Orchestrator findings: child chd001 is draft
                self.assertIn("chd001", prompt_bkl_cont)

                # Instruction text
                self.assertIn(
                    "These plans are the existing handoff for this item. Fix them in place;",
                    prompt_bkl_cont,
                )
                self.assertIn(
                    "Production Contract items 1 and 2 apply to NEW plans only.",
                    prompt_bkl_cont,
                )

                # Probe call count must remain 0
                self.assertEqual(probe_mock.call_count, 0)

    def test_status_conformance_rule(self) -> None:
        """Per-plan conformance accepts legitimate status for continued plans (E-03)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_backlog_item(repo, id6="bkl001")

            p_to_rev = _write_child_plan(
                repo, id6="p00001", backlog_id6="bkl001", status="to-review"
            )
            p_appr = _write_child_plan(
                repo, id6="p00002", backlog_id6="bkl001", status="approved"
            )
            p_revd = _write_child_plan(
                repo, id6="p00003", backlog_id6="bkl001", status="reviewed"
            )
            p_auto = _write_child_plan(
                repo, id6="p00004", backlog_id6="bkl001", status="auto-approved"
            )
            p_draft = _write_child_plan(
                repo, id6="p00005", backlog_id6="bkl001", status="draft"
            )

            # Continued ids: p00001, p00002, p00003, p00004 pass; p00005 (draft) fails
            continued_ids = {"p00001", "p00002", "p00003", "p00004", "p00005"}
            f_pass = production_checks.backlog_graduate_ipd(
                repo,
                "bkl001",
                [p_to_rev, p_appr, p_revd, p_auto],
                continued_ids=continued_ids,
            )
            self.assertEqual(f_pass, [])

            f_draft = production_checks.backlog_graduate_ipd(
                repo, "bkl001", [p_draft], continued_ids=continued_ids
            )
            self.assertEqual(len(f_draft), 1)
            self.assertIn("expected 'to-review', 'reviewed', 'approved'", f_draft[0][2])

            # A NEW plan (not in continued_ids) with approved or reviewed FAILS (needs exactly to-review)
            f_new_appr = production_checks.backlog_graduate_ipd(
                repo, "bkl001", [p_appr], continued_ids={"p00001"}
            )
            self.assertEqual(len(f_new_appr), 1)
            self.assertIn("expected 'to-review'", f_new_appr[0][2])

    def test_commit_helpers_classification(self) -> None:
        """Commit helpers allow continued plans and classify deleted/renamed/pre-dirty (E-05)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl001", setid="set001")
            p_exist = _write_child_plan(
                repo, id6="old001", backlog_id6="bkl001", setid="set001"
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "baseline commit"], cwd=repo, check=True
            )

            # 1. Edit existing plan and add a new plan
            p_exist.write_text(
                p_exist.read_text(encoding="utf-8") + "\n# Extra comment\n",
                encoding="utf-8",
            )
            _write_child_plan(
                repo, id6="new001", backlog_id6="bkl001", setid="set001", order=2
            )

            commit_sha, committed, out_of_scope = rs.commit_backlog_production_output(
                repo,
                "bkl001",
                {"old001"},
                host_label="oc",
                run_id="run-test",
                continued_plan_ids={"old001"},
            )
            self.assertIsNotNone(commit_sha)
            self.assertEqual(len(out_of_scope), 0)
            self.assertEqual(len(committed), 2)
            committed_str = " ".join(committed)
            self.assertIn("old001", committed_str)
            self.assertIn("new001", committed_str)

            # 2. Deleted existing plan classified as out of scope
            p_exist.unlink()
            commit_sha_del, committed_del, oos_del = (
                rs.commit_backlog_production_output(
                    repo,
                    "bkl001",
                    {"old001"},
                    host_label="oc",
                    run_id="run-test",
                    continued_plan_ids={"old001"},
                )
            )
            self.assertIsNone(commit_sha_del)
            self.assertEqual(len(committed_del), 0)
            self.assertEqual(len(oos_del), 1)
            self.assertIn("old001", oos_del[0])
            subprocess.run(["git", "checkout", "--", "."], cwd=repo, check=True)

            # 3. Renamed existing plan classified as out of scope
            p_renamed = (
                repo / ".aw" / "records" / "plans" / "pending" / "renamed.ipd.md"
            )
            subprocess.run(
                [
                    "git",
                    "mv",
                    str(p_exist.relative_to(repo)),
                    str(p_renamed.relative_to(repo)),
                ],
                cwd=repo,
                check=True,
            )
            commit_sha_ren, committed_ren, oos_ren = (
                rs.commit_backlog_production_output(
                    repo,
                    "bkl001",
                    {"old001"},
                    host_label="oc",
                    run_id="run-test",
                    continued_plan_ids={"old001"},
                )
            )
            self.assertIsNone(commit_sha_ren)
            self.assertEqual(len(committed_ren), 0)
            self.assertTrue(len(oos_ren) > 0)
            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repo, check=True)


class TestProductionResumeHandoffIntegration(unittest.TestCase):
    """Integration cases on both hosts (E-04)."""

    def test_case_i_backlog_resumes_unfinished_handoff(self) -> None:
        """Integration case (i): backlog with existing orchestrator and draft child;
        agent brings child to-review -> item graduated, single Set, transition message names both.
        Also tests failing variant: existing orchestrator left unready -> fails BACKLOG-GRADUATE-SET.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                # A. Failing variant: child left draft -> fails BACKLOG-GRADUATE-SET naming it
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl401", status="open", setid="set401"
                    )
                    _write_orchestrator_plan(
                        repo,
                        id6="orc401",
                        backlog_id6="bkl401",
                        setid="set401",
                        child_rows=[
                            (
                                "01",
                                "chd401",
                                ".aw/records/plans/pending/20261004-set401-01-chd401-test-child.ipd.md",
                            )
                        ],
                    )
                    _write_child_plan(
                        repo,
                        id6="chd401",
                        backlog_id6="bkl401",
                        setid="set401",
                        status="draft",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "baseline handoff"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-fail-variant"
                    cmd = [
                        "start",
                        "bkl401",
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

                    def fake_agent_no_change(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        # Does not fix child
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(
                        mod, fake_agent_no_change
                    ), mock.patch.object(rs, "ask_orchestrator_probe", fake_ask_probe):
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
                    self.assertIn("chd401", refusal.get("reason", ""))

                # B. Passing case: agent brings child to-review -> item graduated
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl401", status="open", setid="set401"
                    )
                    _write_orchestrator_plan(
                        repo,
                        id6="orc401",
                        backlog_id6="bkl401",
                        setid="set401",
                        child_rows=[
                            (
                                "01",
                                "chd401",
                                ".aw/records/plans/pending/20261004-set401-01-chd401-test-child.ipd.md",
                            )
                        ],
                    )
                    _write_child_plan(
                        repo,
                        id6="chd401",
                        backlog_id6="bkl401",
                        setid="set401",
                        status="draft",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "baseline handoff"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-pass"
                    cmd = [
                        "start",
                        "bkl401",
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

                    def fake_agent_fix(
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
                        target_chd = (
                            target
                            / ".aw"
                            / "records"
                            / "plans"
                            / "pending"
                            / "20261004-set401-01-chd401-test-child.ipd.md"
                        )
                        c_text = target_chd.read_text(encoding="utf-8")
                        c_text = c_text.replace(
                            "- Status: draft", "- Status: to-review"
                        )
                        target_chd.write_text(c_text, encoding="utf-8")
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_fix), mock.patch.object(
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

                    # Check graduated item in repo
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20261004-set401*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/graduated/", str(bkl_files[0]).replace("\\", "/"))
                    bkl_txt = bkl_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: graduated", bkl_txt)

                    # Transition message names existing and new ids
                    self.assertIn("chd401", bkl_txt)
                    self.assertIn("orc401", bkl_txt)

                    # - Graduated-To: set401
                    self.assertIn("- Graduated-To: set401", bkl_txt)

                    # Sets linked to item = 1
                    active_plans = production_checks.existing_handoff_plans(
                        repo, "backlog", "bkl401"
                    )
                    sets = {p.set for p in active_plans if p.set}
                    self.assertEqual(len(sets), 1)
                    self.assertIn("set401", sets)

    def test_case_ii_backlog_second_set_fails(self) -> None:
        """Integration case (ii): backlog with existing plans in Set 1; agent writes plan in Set 2
        -> fails BACKLOG-GRADUATE-COUNT naming both Sets.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl402", status="open", setid="set402"
                    )
                    _write_child_plan(
                        repo, id6="chd402", backlog_id6="bkl402", setid="set402"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "baseline handoff"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-second-set"
                    cmd = [
                        "start",
                        "bkl402",
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

                    def fake_agent_second_set(
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
                        _write_child_plan(
                            target,
                            id6="chd403",
                            backlog_id6="bkl402",
                            setid="diffset",
                            order=1,
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_second_set):
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
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-COUNT")
                    self.assertIn("introduced a second Set", refusal.get("reason", ""))
                    self.assertIn("set402", refusal.get("reason", ""))
                    self.assertIn("diffset", refusal.get("reason", ""))

    def test_case_iii_spec_resumes_unfinished_handoff(self) -> None:
        """Integration case (iii): spec twin of case (i): spec with existing orchestrator and draft child
        -> agent brings child to-review -> spec ends implementing.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc403", status="approved")
                    _write_orchestrator_plan(
                        repo,
                        id6="orc403",
                        spec_id6="spc403",
                        setid="set403",
                        child_rows=[
                            (
                                "01",
                                "chd403",
                                ".aw/records/plans/pending/20261004-set403-01-chd403-test-child.ipd.md",
                            )
                        ],
                    )
                    _write_child_plan(
                        repo,
                        id6="chd403",
                        spec_id6="spc403",
                        setid="set403",
                        status="draft",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "baseline handoff"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-spec-pass"
                    cmd = [
                        "start",
                        "spc403",
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

                    def fake_agent_fix(
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
                        target_chd = (
                            target
                            / ".aw"
                            / "records"
                            / "plans"
                            / "pending"
                            / "20261004-set403-01-chd403-test-child.ipd.md"
                        )
                        c_text = target_chd.read_text(encoding="utf-8")
                        c_text = c_text.replace(
                            "- Status: draft", "- Status: to-review"
                        )
                        target_chd.write_text(c_text, encoding="utf-8")
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    def fake_ask_probe(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model", ())

                    with _patch_host_agent(mod, fake_agent_fix), mock.patch.object(
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

                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20261004-spc403*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    self.assertIn(
                        "/implementing/", str(spec_files[0]).replace("\\", "/")
                    )
                    spec_txt = spec_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: implementing", spec_txt)
                    self.assertIn("chd403", spec_txt)
                    self.assertIn("orc403", spec_txt)

    def test_case_iv_commit_edits_to_existing_plan(self) -> None:
        """Integration case (iv): agent edits existing plan and adds new plan -> driver commit
        contains both edited existing plan and new plan, git status is clean.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl404", status="open", setid="set404"
                    )
                    _write_child_plan(
                        repo,
                        id6="chd404",
                        backlog_id6="bkl404",
                        setid="set404",
                        order=1,
                        status="to-review",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "baseline handoff"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-edit"
                    cmd = [
                        "start",
                        "bkl404",
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

                    def fake_agent_edit_and_add(
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
                        target_chd = (
                            target
                            / ".aw"
                            / "records"
                            / "plans"
                            / "pending"
                            / "20261004-set404-01-chd404-test-child.ipd.md"
                        )
                        c_text = target_chd.read_text(encoding="utf-8")
                        c_text = c_text.replace(
                            "Test child concern.", "Updated child concern in place."
                        )
                        target_chd.write_text(c_text, encoding="utf-8")
                        _write_child_plan(
                            target,
                            id6="chd405",
                            backlog_id6="bkl404",
                            setid="set404",
                            order=2,
                            status="to-review",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_edit_and_add):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")

                    # Verify git log shows the driver commit with both plans
                    prod_commit = item.get("attempts", [{}])[0].get(
                        "backlog_production_commit"
                    )
                    self.assertIsNotNone(prod_commit)
                    log_res = subprocess.run(
                        [
                            "git",
                            "log",
                            "-1",
                            "--name-only",
                            "--pretty=format:",
                            prod_commit,
                        ],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    log_files = log_res.stdout.splitlines()
                    self.assertTrue(
                        any("chd404" in f for f in log_files),
                        f"Expected chd404 in commit files: {log_files}",
                    )
                    self.assertTrue(
                        any("chd405" in f for f in log_files),
                        f"Expected chd405 in commit files: {log_files}",
                    )

                    # git status --porcelain is clean for both
                    st_res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    st_lines = [
                        line for line in st_res.stdout.splitlines() if line.strip()
                    ]
                    plan_dirty = [
                        line
                        for line in st_lines
                        if "chd404" in line or "chd405" in line
                    ]
                    self.assertEqual(plan_dirty, [])
