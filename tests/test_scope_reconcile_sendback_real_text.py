"""h3fnoc: a REAL scope-reconciliation refusal must classify as retryable.

Measured 2026-10-09 (run-20261009T030837Z-2088618, item m47znv): finalize refused with the
scope-reconciliation summary and ONE answerable finding, yet the runner recorded
`retryable: false` and stranded verified work. The refusal text `ipd_lifecycle.finalize` actually
produces carries an `attribution:` line, a `Supply them with:` line and a suggested command
between the summary and the finding, and the classifier's scope arm required EVERY non-summary
line to be a finding. The existing tests used a hand-written two-line message, so they could not
see it.

These cases build the message the way the runner does (a real `LC.finalize` refusal, rendered in
the runner's `refused: <summary>` + `  IPD-FINALIZE <finding>` shape) and assert on the classifier
and the retry decision.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from agent_workflows import runner_shared, worktree_lease
from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _write_plan,
)


def _runner_rendered(res: LC.FinalizeResult) -> str:
    """Render a finalize result exactly as `driver_finalize` hands it to the classifier."""
    lines = [f"refused: {res.message}"]
    lines.extend(f"  IPD-FINALIZE {f}" for f in res.findings)
    return "\n".join(lines) + "\n"


class RealScopeRefusalTextTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _refusal(self, plan_id: str, extra: tuple[str, ...]) -> LC.FinalizeResult:
        plan_name = f"20260824-demo-01-{plan_id}-demo.ipd.md"
        _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths="src/demo.py"),
            plan_name,
        )
        (self.root / "src").mkdir(parents=True, exist_ok=True)
        (self.root / "src" / "demo.py").write_text("print('demo')\n", encoding="utf-8")
        _commit_all(self.root, "initial commit")
        lane = worktree_lease.allocate_worktree(self.root, plan_id).path
        plan = lane / ".aw" / "records" / "plans" / "pending" / plan_name
        self.assertEqual(
            LC.begin(lane, plan, "a", timestamp="2026-10-09T00:00:00Z").exit_code,
            LC.EXIT_OK,
        )
        (lane / "src" / "demo.py").write_text("print('in')\n", encoding="utf-8")
        for rel in extra:
            target = lane / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=lane, check=True)
        subprocess.run(["git", "commit", "-qm", "work"], cwd=lane, check=True)
        res = LC.finalize(lane, plan, "a", "m", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        return res

    def test_real_single_out_of_scope_refusal_is_retryable(self) -> None:
        res = self._refusal("rsr001", ("notes/defect.md",))
        msg = _runner_rendered(res)
        # The real text carries the lines that broke the classifier; pin that premise.
        self.assertIn(runner_shared.RETRYABLE_SCOPE_RECONCILIATION_SUMMARY, msg)
        self.assertIn("Supply them with:", msg)
        self.assertIn(
            "IPD-FINALIZE out-of-scope path needs a --scope-reason: notes/defect.md",
            msg,
        )
        self.assertTrue(runner_shared.finalize_refusal_is_retryable(msg))

    def test_real_two_path_refusal_is_retryable(self) -> None:
        res = self._refusal("rsr002", ("a_extra.py", "b_extra.py"))
        self.assertTrue(
            runner_shared.finalize_refusal_is_retryable(_runner_rendered(res))
        )

    def test_retry_decision_schedules_a_correction_turn(self) -> None:
        res = self._refusal("rsr003", ("notes/defect.md",))
        item = {
            "id6": "rsr003",
            "attempts": [{"finalize_refused": _runner_rendered(res)}],
        }
        decision = runner_shared.finalize_retry_decision(
            item, {"options": {"retry_budget": 2}}, _runner_rendered(res)
        )
        self.assertTrue(decision.retry, decision.reason)
        self.assertFalse(decision.exhausted)

    def test_the_recorded_m47znv_refusal_is_retryable(self) -> None:
        recorded = (
            "refused: finalize needs scope reconciliation answers (plan left unmoved).\n"
            "  attribution: run-record-exact (this execution's own recorded commit SHAs; "
            "every path below is genuinely this plan's)\n"
            "Supply them with:\n"
            "  aw ipd finalize m47znv --actor 'aw agy run model=X' --message 'm' --apply "
            "--scope-reason .aw/records/backlog/open/x.backlog.md=<why-this-out-of-scope-edit-was-needed>\n"
            "  IPD-FINALIZE out-of-scope path needs a --scope-reason: "
            ".aw/records/backlog/open/x.backlog.md"
        )
        self.assertTrue(runner_shared.finalize_refusal_is_retryable(recorded))

    def test_a_mixed_finding_still_refuses(self) -> None:
        """The every-FINDING rule still holds: a non-answerable finding rides along -> not retryable."""
        res = self._refusal("rsr004", ("notes/defect.md",))
        msg = _runner_rendered(res) + "  IPD-FINALIZE some other unanswerable finding\n"
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(msg))

    def test_summary_with_no_finding_lines_refuses(self) -> None:
        msg = (
            "refused: finalize needs scope reconciliation answers (plan left unmoved).\n"
            "  attribution: run-record-exact (x)\nSupply them with:\n  aw ipd finalize x\n"
        )
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(msg))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
