"""Tests for check.graduated-item-closable and the graduated-closable attention surface.

IPD isnqja (Set wfswdb, Order 01).
Verifies:
1. Graduated item + executed plan + implemented spec -> exactly one check.graduated-item-closable warning.
2. Same with spec approved -> zero warnings.
3. Graduated item with pending plan -> zero warnings.
4. Graduated IPD-only item whose plan is executed -> one warning.
5. Open item and done item with all-terminal carriers -> zero warnings.
6. Graduated item with no carrier -> zero warnings.
7. Remedy works: Fix command moves release-gated item to done, even with different-gate carrier.
8. Attention surface renders graduated-closable (1) in human view without affecting exit code, hidden from --agent.
9. Rule registration in RULE_REGISTRY with severity "info".
"""

from __future__ import annotations

import argparse
import io
import shlex
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import attention as att
from agent_workflows import attention_contract as A
from agent_workflows import check_engine


def _create_minimal_repo(root: Path) -> Path:
    """Create a minimal conformant repository structure."""
    for p in (
        root / ".aw" / "records" / "releases",
        root / ".aw" / "records" / "backlog" / "open",
        root / ".aw" / "records" / "backlog" / "graduated",
        root / ".aw" / "records" / "backlog" / "done",
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "plans" / "executed",
        root / ".aw" / "records" / "specs" / "approved",
        root / ".aw" / "records" / "specs" / "implemented",
    ):
        p.mkdir(parents=True, exist_ok=True)
    # create planned releases
    rel_file = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
    )
    rel_file.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    rel2_file = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel002-01-rel002-v2.release.md"
    )
    rel2_file.write_text(
        "# Release: 2.0.0\n\n"
        "- Id: rel002\n"
        "- Status: planned\n"
        "- Version: 2.0.0\n"
        "- Summary: Test release 2\n",
        encoding="utf-8",
    )
    return root


def _attn_args(root: Path, **over) -> argparse.Namespace:
    """Full aw attention arguments namespace matching CLI defaults."""
    ns = dict(
        dir=str(root),
        format=None,
        check=False,
        selectors=[],
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        run_status=[],
        runs=False,
        order_by=A.ORDER_CLASS,
        agent=False,
        json=False,
        no_color=True,
        color=False,
        all=False,
        long=False,
        details=False,
        id6_only=False,
        paths=False,
        filenames=False,
        active=False,
        not_active=False,
    )
    ns.update(over)
    return argparse.Namespace(**ns)


class TestGraduatedClosableWarning(unittest.TestCase):
    """Behavioral tests for graduated closable warning and attention surface."""

    def test_case_1_graduated_with_executed_plan_and_implemented_spec(self) -> None:
        """Case 1: graduated item + executed plan + implemented spec -> 1 warning."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "implemented"
                / "20261012-spec01-01-spec01-test-spec.spec.md"
            )
            spec_file.write_text(
                "# Spec: Test spec 01\n\n"
                "- Id: spec01\n"
                "- Status: implemented\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 implemented (test): done.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(len(warnings), 1)
            d = warnings[0]
            self.assertEqual(d.rule, "check.graduated-item-closable")
            self.assertEqual(d.location, str(item_file))
            self.assertIn("aw backlog set bklg01 --status done --evidence ", d.detail)
            rel_plan = plan_file.resolve().relative_to(repo.resolve()).as_posix()
            self.assertIn(rel_plan, d.detail)

    def test_case_2_spec_approved_produces_zero_warnings(self) -> None:
        """Case 2: same with spec approved -> zero warnings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261012-spec01-01-spec01-test-spec.spec.md"
            )
            spec_file.write_text(
                "# Spec: Test spec 01\n\n"
                "- Id: spec01\n"
                "- Status: approved\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 approved (test): approved.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(warnings, [])

    def test_case_3_pending_plan_produces_zero_warnings(self) -> None:
        """Case 3: graduated item with pending plan -> zero warnings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: approved\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 approved (test): approved.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(warnings, [])

    def test_case_4_graduated_ipd_only_item_with_executed_plan(self) -> None:
        """Case 4: graduated IPD-only item whose plan is executed -> one warning."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(len(warnings), 1)
            d = warnings[0]
            self.assertEqual(d.rule, "check.graduated-item-closable")
            self.assertEqual(d.location, str(item_file))
            self.assertIn("aw backlog set bklg01 --status done --evidence ", d.detail)

    def test_case_5_open_and_done_items_produce_zero_warnings(self) -> None:
        """Case 5: an open item and a done item with all-terminal carriers -> zero warnings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            open_item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20261012-0001-01-bklg01-open-item.bklg.md"
            )
            open_item.write_text(
                "# Backlog: Open item 01\n\n"
                "- Id: bklg01\n"
                "- Status: open\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Open item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 open (test): open.\n",
                encoding="utf-8",
            )
            done_item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20261012-0002-01-bklg02-done-item.bklg.md"
            )
            done_item.write_text(
                "# Backlog: Done item 02\n\n"
                "- Id: bklg02\n"
                "- Status: done\n"
                "- Set: bklg02\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Done item 02\n\n"
                "## Workflow history\n"
                "- 2026-10-12 done (test): done.\n",
                encoding="utf-8",
            )
            plan1 = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan1.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            plan2 = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set02-01-plan02-test-plan.ipd.md"
            )
            plan2.write_text(
                "# IPD: Test plan 02\n\n"
                "- Id: plan02\n"
                "- Status: executed\n"
                "- Set: set02\n"
                "- From-Backlog: bklg02\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(warnings, [])

    def test_case_6_graduated_item_with_no_carrier_produces_zero_warnings(self) -> None:
        """Case 6: a graduated item with no carrier -> zero warnings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(warnings, [])

    def test_case_7_remedy_works_with_same_and_different_gate(self) -> None:
        """Case 7: Fix command moves release-gated item to done, with same and different gate."""
        # Subcase A: Item and plan carrier share the same Blocks-Release gate
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Blocks-Release: rel001\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- Blocks-Release: rel001\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "implemented"
                / "20261012-spec01-01-spec01-test-spec.spec.md"
            )
            spec_file.write_text(
                "# Spec: Test spec 01\n\n"
                "- Id: spec01\n"
                "- Status: implemented\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 implemented (test): done.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(len(warnings), 1)
            fix_part = warnings[0].detail.partition("\n    Fix: ")[2].strip()
            self.assertTrue(fix_part.startswith("aw backlog set "))
            raw_args = shlex.split(fix_part[len("aw backlog set ") :])
            cmd = [
                sys.executable,
                "-m",
                "agent_workflows",
                "backlog",
                "set",
                *raw_args,
                "--dir",
                str(repo),
                "--no-commit",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(
                res.returncode, 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"
            )
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*bklg01*")
            )
            self.assertEqual(len(done_items), 1)
            grad_items = list(
                (repo / ".aw" / "records" / "backlog" / "graduated").glob("*bklg01*")
            )
            self.assertEqual(len(grad_items), 0)

        # Subcase B: Item and plan carrier carry DIFFERENT Blocks-Release gates
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0002-01-bklg02-test-item.bklg.md"
            )
            item_file.write_text(
                "# Backlog: Test item 02\n\n"
                "- Id: bklg02\n"
                "- Status: graduated\n"
                "- Set: bklg02\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Blocks-Release: rel001\n"
                "- Summary: Test item 02\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set02-01-plan02-test-plan.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test plan 02\n\n"
                "- Id: plan02\n"
                "- Status: executed\n"
                "- Set: set02\n"
                "- Blocks-Release: rel002\n"
                "- From-Backlog: bklg02\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "implemented"
                / "20261012-spec02-01-spec02-test-spec.spec.md"
            )
            spec_file.write_text(
                "# Spec: Test spec 02\n\n"
                "- Id: spec02\n"
                "- Status: implemented\n"
                "- From-Backlog: bklg02\n\n"
                "## Workflow history\n"
                "- 2026-10-12 implemented (test): done.\n",
                encoding="utf-8",
            )

            warnings = check_engine.graduated_closable_warnings(repo)
            self.assertEqual(len(warnings), 1)
            fix_part = warnings[0].detail.partition("\n    Fix: ")[2].strip()
            self.assertTrue(fix_part.startswith("aw backlog set "))
            raw_args = shlex.split(fix_part[len("aw backlog set ") :])
            cmd = [
                sys.executable,
                "-m",
                "agent_workflows",
                "backlog",
                "set",
                *raw_args,
                "--dir",
                str(repo),
                "--no-commit",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(
                res.returncode, 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"
            )
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*bklg02*")
            )
            self.assertEqual(len(done_items), 1)
            grad_items = list(
                (repo / ".aw" / "records" / "backlog" / "graduated").glob("*bklg02*")
            )
            self.assertEqual(len(grad_items), 0)

    def test_case_8_attention_surface_rendering_and_invariants(self) -> None:
        """Case 8: Attention surface renders graduated-closable (1) in human view, invisible to --agent."""
        with TemporaryDirectory() as tmp1, TemporaryDirectory() as tmp2:
            # Case 1 repo: closable item
            repo1 = _create_minimal_repo(Path(tmp1))
            (
                repo1
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            ).write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            (
                repo1
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            ).write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            (
                repo1
                / ".aw"
                / "records"
                / "specs"
                / "implemented"
                / "20261012-spec01-01-spec01-test-spec.spec.md"
            ).write_text(
                "# Spec: Test spec 01\n\n"
                "- Id: spec01\n"
                "- Status: implemented\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 implemented (test): done.\n",
                encoding="utf-8",
            )

            # Case 2 repo: not closable (spec approved)
            repo2 = _create_minimal_repo(Path(tmp2))
            (
                repo2
                / ".aw"
                / "records"
                / "backlog"
                / "graduated"
                / "20261012-0001-01-bklg01-test-item.bklg.md"
            ).write_text(
                "# Backlog: Test item 01\n\n"
                "- Id: bklg01\n"
                "- Status: graduated\n"
                "- Set: bklg01\n"
                "- Priority: medium\n"
                "- Work-Kind: followup\n"
                "- Summary: Test item 01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 graduated (test): graduated.\n",
                encoding="utf-8",
            )
            (
                repo2
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261012-set01-01-plan01-test-plan.ipd.md"
            ).write_text(
                "# IPD: Test plan 01\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- Set: set01\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 executed (test): done.\n",
                encoding="utf-8",
            )
            (
                repo2
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261012-spec01-01-spec01-test-spec.spec.md"
            ).write_text(
                "# Spec: Test spec 01\n\n"
                "- Id: spec01\n"
                "- Status: approved\n"
                "- From-Backlog: bklg01\n\n"
                "## Workflow history\n"
                "- 2026-10-12 approved (test): approved.\n",
                encoding="utf-8",
            )

            # Drive human board on case 1
            buf1 = io.StringIO()
            with redirect_stdout(buf1):
                rc1 = att.run(_attn_args(repo1))
            out1 = buf1.getvalue()
            self.assertIn("graduated-closable (1)", out1)
            self.assertIn("bklg01", out1)
            self.assertIn("Fix: aw backlog set bklg01 --status done --evidence ", out1)

            # Compare human return codes
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                rc2 = att.run(_attn_args(repo2))
            self.assertEqual(rc1, rc2)

            # Compare --check return codes
            buf_chk1 = io.StringIO()
            with redirect_stdout(buf_chk1):
                rc_chk1 = att.run(_attn_args(repo1, check=True))
            buf_chk2 = io.StringIO()
            with redirect_stdout(buf_chk2):
                rc_chk2 = att.run(_attn_args(repo2, check=True))
            self.assertEqual(rc_chk1, rc_chk2)

            # Drive --agent on case 1: must not contain check.graduated-item-closable
            buf_agent = io.StringIO()
            with redirect_stdout(buf_agent):
                att.run(_attn_args(repo1, agent=True))
            out_agent = buf_agent.getvalue()
            self.assertNotIn("check.graduated-item-closable", out_agent)

    def test_case_9_rule_spec_registration_and_severity(self) -> None:
        """Case 9: check.graduated-item-closable rule spec is registered with severity info."""
        spec = check_engine.rule_spec("check.graduated-item-closable")
        self.assertEqual(spec.severity, "info")
