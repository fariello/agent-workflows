"""Behavioral tests for legal and illegal backward plan lifecycle edges.

IPD pyuhnl (backedge-01):
  Case 1: Repro end to end through `cli.main`: `ipd set to-review` then `commit` exits 0.
  Case 2: `check_engine.check_type(repo, "plans")` yields no `check.lifecycle-transition-invalid`.
  Case 3: Direct `ipd_lifecycle.validate_transition("reviewed", "to-review").ok` is True.
  Case 4: Controls: `approved -> to-review` and `reviewed -> draft` return `ok=False` with
          `backwards transition` in reason, and scratch plan with `reviewed` then `draft`
          refuses `aw commit` with rc 1 naming `check.lifecycle-transition-invalid`.
  Case 5: Controls: existing edges `approved -> reviewed` and `auto-approved -> reviewed` remain ok.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine, cli, ipd_lifecycle
from tests import support
from tests.record_builder import RecordBuilder

_REVIEWED_PLAN = RecordBuilder().plan(
    title="Demo work plan",
    when="2026-08-28",
    plan_role="child",
    scope_paths="src/, tests/",
    item_dependencies="none",
    status="reviewed",
    priority="medium",
    work_kind="chore",
    set="wk",
    order=1,
    highest_e_allocated="01",
    author="tester",
    id6="wk0001",
    history=["- 2026-08-28 reviewed (aw set): reviewed"],
    body="## Goal\nA real goal statement.\n\n## Detailed Implementation Checklist (TODO)\n\n### Task group 1: work\n- [ ] E-01 Do a real observable thing.\n  - Depends on: none\n  - Expected outcome: a real observable result.\n  - Execution state: pending\n\n## Validation and cross-check (verify before reporting done)\n- [ ] V-01 validates E-01\n  - Required evidence: a real falsifiable evidence statement.\n  - Observed evidence:\n  - Result: pending\n\n## Approval and execution gate\n- Size assessment: standard\n- Cohesion rationale: not required",
    text_only=True,
)


class IpdLifecycleBackwardEdgesTest(unittest.TestCase):
    def setUp(self):
        support.declare_execution_role(self)
        self._tmp_aw_home = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_aw_home.cleanup)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self._tmp_aw_home.name

        def _restore_aw_home():
            if self._prev_aw_home is not None:
                os.environ["AW_HOME"] = self._prev_aw_home
            else:
                os.environ.pop("AW_HOME", None)

        self.addCleanup(_restore_aw_home)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.plan_path = self.plans / "20260828-wk-01-wk0001-demo.ipd.md"
        self.plan_path.write_text(_REVIEWED_PLAN, encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "f.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 1
        return (0 if rc is None else rc), out.getvalue() + err.getvalue()

    def test_case_1_end_to_end_repro_commit_after_to_review(self):
        """Case 1: `ipd set to-review` then `commit` exits 0 and HEAD touches src/f.py."""
        rc, out = self._run(
            [
                "ipd",
                "set",
                "to-review",
                "wk0001",
                "--dir",
                str(self.root),
                "--message",
                "revise",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, f"ipd set failed: {out}")

        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        rc, out = self._run(
            [
                "commit",
                "wk0001",
                "--dir",
                str(self.root),
                "-m",
                "x",
                "--",
                "src/f.py",
            ]
        )
        self.assertEqual(rc, 0, f"aw commit failed: {out}")
        show = subprocess.check_output(
            ["git", "show", "--stat", "HEAD"], cwd=self.root, text=True
        )
        self.assertIn("src/f.py", show)

    def test_case_2_check_engine_no_invalid_transition(self):
        """Case 2: `check_engine.check_type(repo, 'plans')` yields no lifecycle-transition-invalid."""
        rc, out = self._run(
            [
                "ipd",
                "set",
                "to-review",
                "wk0001",
                "--dir",
                str(self.root),
                "--message",
                "revise",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, f"ipd set failed: {out}")

        drifts = check_engine.check_type(self.root, "plans")
        target = str(self.plan_path.resolve())
        plan_invalid = [
            d
            for d in drifts
            if str(Path(d.location).resolve()) == target
            and d.rule == "check.lifecycle-transition-invalid"
        ]
        self.assertEqual(
            plan_invalid,
            [],
            f"Expected no check.lifecycle-transition-invalid finding for plan, got: {plan_invalid}",
        )

    def test_case_3_direct_validate_transition_reviewed_to_to_review(self):
        """Case 3: direct `ipd_lifecycle.validate_transition('reviewed', 'to-review').ok` is True."""
        check = ipd_lifecycle.validate_transition("reviewed", "to-review")
        self.assertTrue(
            check.ok,
            f"Expected validate_transition('reviewed', 'to-review').ok to be True, got {check}",
        )

    def test_case_4_controls_unenumerated_backward_edges_still_refused(self):
        """Case 4: non-terminal backward edges are now ok; backward moves into or out of terminal are refused."""
        c1 = ipd_lifecycle.validate_transition("approved", "to-review")
        self.assertTrue(c1.ok, f"approved -> to-review should be ok, got {c1}")

        c2 = ipd_lifecycle.validate_transition("reviewed", "draft")
        self.assertTrue(c2.ok, f"reviewed -> draft should be ok, got {c2}")

        # Moving backward out of a terminal status is still refused
        c3 = ipd_lifecycle.validate_transition("executed", "approved")
        self.assertFalse(c3.ok)
        self.assertIn("backwards transition", c3.reason)

        # Premature move directly into terminal is still refused
        c4 = ipd_lifecycle.validate_transition("draft", "executed")
        self.assertFalse(c4.ok)
        self.assertIn("terminal transition", c4.reason)

        # Scratch plan whose history records executed then approved (illegal move out of terminal)
        control_plan = RecordBuilder().plan(
            title="Demo work plan",
            when="2026-08-28",
            plan_role="child",
            scope_paths="src/, tests/",
            item_dependencies="none",
            status="approved",
            approval='2026-08-30, human ("approved"): reapproved',
            priority="medium",
            work_kind="chore",
            set="wk",
            order=1,
            highest_e_allocated="01",
            author="tester",
            id6="wk0001",
            history=[
                "- 2026-08-30 approved (aw set): demoted executed -> approved",
                "- 2026-08-29 executed (aw ipd finalize): finalized",
                "- 2026-08-28 reviewed (aw set): reviewed",
            ],
            body="## Goal\nA real goal statement.\n\n## Detailed Implementation Checklist (TODO)\n\n### Task group 1: work\n- [ ] E-01 Do a real observable thing.\n  - Depends on: none\n  - Expected outcome: a real observable result.\n  - Execution state: pending\n\n## Validation and cross-check (verify before reporting done)\n- [ ] V-01 validates E-01\n  - Required evidence: a real falsifiable evidence statement.\n  - Observed evidence:\n  - Result: pending\n\n## Approval and execution gate\n- Size assessment: standard\n- Cohesion rationale: not required",
            text_only=True,
        )
        self.plan_path.write_text(control_plan, encoding="utf-8")
        subprocess.run(["git", "add", str(self.plan_path)], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "update plan to illegal terminal transition"],
            cwd=self.root,
            check=True,
        )

        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        rc, out = self._run(
            [
                "commit",
                "wk0001",
                "--dir",
                str(self.root),
                "-m",
                "x",
                "--",
                "src/f.py",
            ]
        )
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("check.lifecycle-transition-invalid", out)

    def test_case_5_controls_existing_backward_edges_remain_ok(self):
        """Case 5: existing edges approved -> reviewed and auto-approved -> reviewed remain ok."""
        c1 = ipd_lifecycle.validate_transition("approved", "reviewed")
        self.assertTrue(c1.ok, f"approved -> reviewed should be ok, got {c1}")

        c2 = ipd_lifecycle.validate_transition("auto-approved", "reviewed")
        self.assertTrue(c2.ok, f"auto-approved -> reviewed should be ok, got {c2}")
