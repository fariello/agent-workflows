"""Tests for plan findings severity gating in `aw commit` and `aw work begin` (IPD s7cu7n).

Covers:
  E-03 / V-03: `aw commit` passes with non-blocking advisory on `warning` findings, refuses on
               `error` findings and unregistered rules (default error), and names both in mixed cases.
  E-04 / V-04: `aw work begin` allocates with non-blocking advisory on `warning` findings, refuses
               without lease on `error` findings, and end-to-end unpatched misnamed plan refuses on
               error without warning-tier findings.
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core, check_engine, cli
from tests import support

_PLAN = """# IPD: Demo work plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement for review.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
- Priority: medium
- Work-Kind: chore
- Set: wk
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: wk0001

## Workflow history
- 2026-08-28 approved (aw set): approved

## Goal
A real goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: work
- [ ] E-01 Do a real observable thing.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""

_BAD_PLAN = """# IPD: Bad name plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
- Priority: medium
- Work-Kind: chore
- Set: wk
- Order: 2
- Highest E allocated: 01
- Author: tester
- Id: bad001

## Workflow history
- 2026-08-28 approved (aw set): approved

## Goal
A real goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: work
- [ ] E-01 Do something.
  - Depends on: none
  - Expected outcome: done.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


class WorkGateSeverityTest(unittest.TestCase):
    def setUp(self):
        support.declare_execution_role(self)
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
        self.plan_path.write_text(_PLAN, encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "f.py").write_text("print('hello')\n", encoding="utf-8")
        # gitignore the worktrees + state so the throwaway repo does not embed them
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
        output = out.getvalue() + err.getvalue()
        return rc, output

    # ----------------------------------------------------------------------------------
    # Baseline check
    # ----------------------------------------------------------------------------------

    def test_fixture_baseline_clean_of_warnings_and_errors(self):
        """Confirm the unpatched fixture plan produces no warning or error findings."""
        drifts = check_engine.check_type(self.root, "plans")
        target = str(self.plan_path.resolve())
        plan_drifts = [
            check_engine.enrich_drift(d)
            for d in drifts
            if str(Path(d.location).resolve()) == target
        ]
        blocking_or_advisory = [
            ed for ed in plan_drifts if ed.severity in ("warning", "error")
        ]
        self.assertEqual(
            blocking_or_advisory,
            [],
            f"Fixture must be clean of warning/error findings; got: {[(ed.severity, ed.rule) for ed in plan_drifts]}",
        )

    # ----------------------------------------------------------------------------------
    # aw commit cases (E-03)
    # ----------------------------------------------------------------------------------

    def test_commit_warning_drift_commits_with_advisory(self):
        """(a) warning-severity finding prints advisory notice and permits commit."""
        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        drift = artifact_core.Drift(
            str(self.plan_path),
            "check.review-decision-unescalated",
            "probe unescalated",
        )
        with mock.patch.object(check_engine, "check_type", return_value=[drift]):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "update f",
                    "--",
                    "src/f.py",
                ]
            )
        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")
        self.assertIn("advisory", out)
        self.assertIn("check.review-decision-unescalated", out)
        # Verify commit succeeded
        show = subprocess.check_output(
            ["git", "show", "--stat", "HEAD"], cwd=self.root, text=True
        )
        self.assertIn("src/f.py", show)

    def test_commit_error_drift_refuses_without_committing(self):
        """(b) error-severity finding refuses commit with rc 1 and leaves HEAD unchanged."""
        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        drift = artifact_core.Drift(
            str(self.plan_path), "check.name-nonconformant", "probe bad name"
        )
        with mock.patch.object(check_engine, "check_type", return_value=[drift]):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "update f",
                    "--",
                    "src/f.py",
                ]
            )
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("refusing", out)
        self.assertIn("check.name-nonconformant", out)
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.assertEqual(head_before, head_after)

    def test_commit_unregistered_rule_refuses_fail_closed(self):
        """(c) unregistered rule id defaults to error severity and refuses commit."""
        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        drift = artifact_core.Drift(
            str(self.plan_path),
            "check.gatesev-probe-unregistered",
            "probe unregistered",
        )
        with mock.patch.object(check_engine, "check_type", return_value=[drift]):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "update f",
                    "--",
                    "src/f.py",
                ]
            )
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("refusing", out)
        self.assertIn("check.gatesev-probe-unregistered", out)
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.assertEqual(head_before, head_after)

    def test_commit_mixed_warning_and_error_refuses_and_names_both(self):
        """(d) one warning plus one error refuses commit and names both rules."""
        (self.root / "src" / "f.py").write_text("print('modified')\n", encoding="utf-8")
        head_before = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        drifts = [
            artifact_core.Drift(
                str(self.plan_path),
                "check.review-decision-unescalated",
                "probe unescalated",
            ),
            artifact_core.Drift(
                str(self.plan_path), "check.name-nonconformant", "probe bad name"
            ),
        ]
        with mock.patch.object(check_engine, "check_type", return_value=drifts):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "update f",
                    "--",
                    "src/f.py",
                ]
            )
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("check.review-decision-unescalated", out)
        self.assertIn("check.name-nonconformant", out)
        head_after = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.assertEqual(head_before, head_after)

    # ----------------------------------------------------------------------------------
    # aw work begin cases (E-04)
    # ----------------------------------------------------------------------------------

    def test_work_begin_warning_drift_allocates_with_advisory(self):
        """(a) warning-severity finding prints advisory notice and allocates worktree."""
        drift = artifact_core.Drift(
            str(self.plan_path),
            "check.review-decision-unescalated",
            "probe unescalated",
        )
        with mock.patch.object(check_engine, "check_type", return_value=[drift]):
            rc, out = self._run(["work", "begin", "wk0001", "--dir", str(self.root)])
        self.assertEqual(rc, 0, f"Expected rc 0, got {rc}. Output:\n{out}")
        self.assertIn("allocated worktree", out)
        self.assertIn("advisory", out)
        self.assertIn("check.review-decision-unescalated", out)
        lease_file = self.root / ".aw" / "state" / "work" / "wk0001" / "work-lease.json"
        self.assertTrue(lease_file.is_file(), "Lease file must exist after allocation")

    def test_work_begin_error_drift_refuses_without_lease(self):
        """(b) error-severity finding refuses work begin with rc 1 and allocates no lease."""
        drift = artifact_core.Drift(
            str(self.plan_path), "check.name-nonconformant", "probe bad name"
        )
        with mock.patch.object(check_engine, "check_type", return_value=[drift]):
            rc, out = self._run(["work", "begin", "wk0001", "--dir", str(self.root)])
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("refusing to start", out)
        self.assertIn("check.name-nonconformant", out)
        lease_file = self.root / ".aw" / "state" / "work" / "wk0001" / "work-lease.json"
        self.assertFalse(lease_file.exists(), "Lease file must not exist on refusal")

    def test_work_begin_unpatched_misnamed_plan_refuses_on_error_without_warnings(self):
        """(c) UNPATCHED end-to-end: misnamed plan trips check.name-nonconformant, refuses without warnings."""
        # Note: check_engine.check_type is deliberately UNPATCHED here to test real engine reach.
        bad_plan_path = self.plans / "badname.ipd.md"
        bad_plan_path.write_text(_BAD_PLAN, encoding="utf-8")
        subprocess.run(["git", "add", str(bad_plan_path)], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "add bad plan"], cwd=self.root, check=True
        )

        rc, out = self._run(["work", "begin", "bad001", "--dir", str(self.root)])
        self.assertEqual(rc, 1, f"Expected rc 1, got {rc}. Output:\n{out}")
        self.assertIn("refusing to start", out)
        self.assertIn("check.name-nonconformant", out)

        # Assert that no warning-tier rule id appears in the refusal output
        warning_rules = [
            k for k, v in check_engine.RULE_REGISTRY.items() if v.severity == "warning"
        ]
        for w_rule in warning_rules:
            self.assertNotIn(
                w_rule,
                out,
                f"Warning rule {w_rule} should not appear in refusing output",
            )

        lease_file = self.root / ".aw" / "state" / "work" / "bad001" / "work-lease.json"
        self.assertFalse(lease_file.exists(), "Lease file must not exist on refusal")
