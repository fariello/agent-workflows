"""Restored behavioral coverage for reusable plans and plan_already_finalized (IPD pud8rp).

Guards the fail-open hazard where substituting run_selection_policy.is_in_terminal_directory
for the executed-bucket check would misclassify reusable plans as already finalized, causing
a missing begin receipt to be treated as consumed and converting driver-seam refusals to exit 0.

Fixture choice:
Reuses `tests.support.declare_execution_role` (to declare the coordinator role and prevent role
leakage across `-n auto` workers) and `tests.support.ready_plan_text`.
Local fixture helpers (`_init_git`, `_completed_plan_text`, `_commit_all`, and `_write_plan`)
are defined locally in this module rather than importing private helpers from
`test_ipd_lifecycle_cli` across modules, ensuring proper repository initialization,
git configuration, `.aw/state/` gitignore isolation, and lint-clean pre-transition plans.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from agent_workflows import ipd_lint as L
from agent_workflows import run_selection_policy as RSP
from agent_workflows import runner_shared as RS
from tests import support


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    # Mirror the real repo: the begin receipt lives in the gitignored .aw/state/ tree,
    # so writing it never dirties the worktree.
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _completed_plan_text(
    *,
    plan_id: str = "abc123",
    status: str = "approved",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    """A ready-plan whose single E-01/V-01 is marked performed/pass so it lints CONFORMING at
    the pre-transition checkpoint (finalize requires this)."""
    t = support.ready_plan_text(plan_id=plan_id, status=status, scope_paths=scope_paths)
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return t


def _write_plan(root: Path, text: str, name: str, bucket: str = "pending") -> Path:
    d = root / ".aw" / "records" / "plans" / bucket
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


class ReusablePlanIsNotAlreadyFinalized(unittest.TestCase):
    """THE FAIL-OPEN CONTROL (IPD pud8rp / backlog tvv8gg).

    `run_selection_policy.is_in_terminal_directory` returns True for `/reusable/`, which is NOT a
    completed disposition: `.aw/records/plans/reusable/README.md` says 'Not a terminal state' and
    `_IPD_ACTIONS["reusable"]` is `ACTION_EXECUTE`, so the runner dispatches such a plan repeatedly.
    Keying ALREADY-FINALIZED on that predicate would therefore read a never-issued receipt on every
    reusable run as 'already finalized' and integrate with NO execution authority at all - converting
    a driver-seam refusal into exit code 0.
    """

    REUSABLE_ID = "reu777"
    REUSABLE_NAME = "20260917-demo-01-reu777-demo.ipd.md"

    EXECUTED_ID = "exe888"
    EXECUTED_NAME = "20260917-demo-01-exe888-demo.ipd.md"

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)

        self.reusable_plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=self.REUSABLE_ID, status="reusable"),
            self.REUSABLE_NAME,
            bucket="reusable",
        )
        self.executed_plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=self.EXECUTED_ID, status="executed"),
            self.EXECUTED_NAME,
            bucket="executed",
        )
        _commit_all(self.root, "init fixture plans")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_scratch_fixture_plan_lints_clean_pre_transition(self):
        """Smoke test verifying the fixture builds a scratch repo with a lint-clean reusable plan."""
        self.assertTrue(self.reusable_plan.is_file())
        self.assertEqual(
            self.reusable_plan.parent,
            self.root / ".aw" / "records" / "plans" / "reusable",
        )
        res = L.lint_file(self.reusable_plan, checkpoint="pre-transition")
        self.assertEqual(
            res.disposition, "conforming", f"diagnostics: {res.diagnostics}"
        )

    def test_is_in_terminal_directory_admits_reusable_so_it_is_NOT_the_predicate(self):
        """Predicate assertions (E-03): run_selection_policy counterfactual and bucket discrimination."""
        # 1. run_selection_policy counterfactual: the rejected predicate admits reusable
        self.assertTrue(
            RSP.is_in_terminal_directory(self.reusable_plan),
            "the counterfactual this control exists for: the rejected predicate admits reusable",
        )
        # 2. _IPD_ACTIONS["reusable"] is ACTION_EXECUTE
        self.assertEqual(
            RSP._IPD_ACTIONS.get("reusable"),
            RSP.ACTION_EXECUTE,
            "reusable plans must be marked ACTION_EXECUTE",
        )
        # 3. plan_bucket discrimination
        self.assertEqual(RS.plan_bucket(self.reusable_plan), "reusable")
        # 4. plan_already_finalized answers False for reusable and True for executed
        reusable_verdict = LC.plan_already_finalized(
            self.root, self.reusable_plan, self.REUSABLE_ID
        )
        self.assertFalse(
            reusable_verdict.already,
            "reusable plan must NOT be reported as already finalized",
        )
        executed_verdict = LC.plan_already_finalized(
            self.root, self.executed_plan, self.EXECUTED_ID
        )
        self.assertTrue(
            executed_verdict.already,
            "executed plan must be reported as already finalized (non-vacuous contrast)",
        )

    def test_reusable_without_receipt_refuses_at_precheck_and_driver_seam(self):
        """Consequence assertions (E-04): classification seam and driver seam with executed contrast."""
        # Classification seam: precheck on reusable plan without receipt
        before_bytes = self.reusable_plan.read_bytes()
        code, message, _evidence, findings = LC.finalize_precheck(
            self.root, self.reusable_plan
        )
        self.assertEqual(code, LC.EXIT_FINDINGS, message)
        self.assertIn(
            LC.FINDING_RECEIPT_NEVER_ISSUED,
            findings,
            "a receipt-less reusable plan must classify as receipt-never-issued",
        )
        self.assertNotIn(
            LC.FINDING_RECEIPT_ALREADY_FINALIZED,
            findings,
            "a reusable plan must NOT classify as receipt-consumed-already-finalized",
        )
        # Leaves the plan file unmoved
        self.assertTrue(self.reusable_plan.is_file())
        self.assertEqual(self.reusable_plan.read_bytes(), before_bytes)

        # Driver seam: runner_shared.finalize_outcome and finalize_already_done
        self.assertFalse(
            RS.finalize_already_done(self.root, self.reusable_plan, self.REUSABLE_ID),
            "finalize_already_done must be False for reusable plan",
        )
        fin_rc, fin_msg = RS.finalize_outcome(
            self.root, self.reusable_plan, self.REUSABLE_ID, code, message
        )
        self.assertNotEqual(
            fin_rc,
            0,
            "finalize_outcome must keep a nonzero refusal for reusable plan with no receipt",
        )

        # Positive contrast in the same test: executed plan
        self.assertTrue(
            RS.finalize_already_done(self.root, self.executed_plan, self.EXECUTED_ID),
            "finalize_already_done must be True for executed plan",
        )
        contrast_rc, contrast_msg = RS.finalize_outcome(
            self.root,
            self.executed_plan,
            self.EXECUTED_ID,
            1,
            "synthetic refusal to test idempotence",
        )
        self.assertEqual(
            contrast_rc,
            0,
            "finalize_outcome must return 0 for executed plan (positive contrast)",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
