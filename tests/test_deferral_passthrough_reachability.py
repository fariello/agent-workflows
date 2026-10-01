"""Behavioral tests pinning the deferral passthrough's contract and reachability.

Tests the surviving contract of `reconcile_disposition`'s deferral passthrough
and proves by direct observation that neither scoring point in `execute_item_core`
can observe `merge-retry`.

Note: Assertion 3 (`test_unreachability_observed_across_scoring_points`) is the one
that would go red if a future change made `merge-retry` reachable at either scoring
point in `execute_item_core`. That failure would be a legitimate signal to re-read
the wording in `rescore_is_an_improvement` and `reconcile_disposition` rather than to
loosen the test.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import test_defect_report


class DeferralPassthroughReachabilityTests(unittest.TestCase):
    def test_passthrough_contract(self) -> None:
        """Assertion (1): Passthrough returns merge-retry for both exit codes; not terminal."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            run_dir = root / "run"
            run_dir.mkdir()

            item_deferred = {
                "id6": "tst001",
                "configured_file": "test.ipd.md",
                "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
            }

            results: dict[int, tuple[str, dict[str, Any] | None]] = {}
            for code in (0, 1):
                disp, outcome = runner_shared.reconcile_disposition(
                    repo, item_deferred, run_dir, exit_code=code
                )
                results[code] = (disp, outcome)

            expected = runner_shared.INTEGRATION_DEFERRED_STATUS
            self.assertEqual(
                {0: (expected, None), 1: (expected, None)},
                results,
                f"expected {expected} on both exit codes, got {results}",
            )

            # Assert why it matters: merge-retry is absent from TERMINAL_STATES on all hosts
            self.assertNotIn(
                runner_shared.INTEGRATION_DEFERRED_STATUS, runner_shared.TERMINAL_STATES
            )
            self.assertNotIn(
                runner_shared.INTEGRATION_DEFERRED_STATUS, oc_runipd.TERMINAL_STATES
            )
            self.assertNotIn(
                runner_shared.INTEGRATION_DEFERRED_STATUS, agy_runipd.TERMINAL_STATES
            )

    def test_negative_control_running(self) -> None:
        """Assertion (2): Negative control - item with 'running' status does NOT return merge-retry."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            run_dir = root / "run"
            run_dir.mkdir()

            item_running = {
                "id6": "tst001",
                "configured_file": "test.ipd.md",
                "status": "running",
            }

            disp_0, outcome_0 = runner_shared.reconcile_disposition(
                repo, item_running, run_dir, exit_code=0
            )
            self.assertNotEqual(runner_shared.INTEGRATION_DEFERRED_STATUS, disp_0)
            self.assertEqual("fail-verify", disp_0)
            self.assertIsNone(outcome_0)

            disp_nonzero, outcome_nonzero = runner_shared.reconcile_disposition(
                repo, item_running, run_dir, exit_code=1
            )
            self.assertNotEqual(runner_shared.INTEGRATION_DEFERRED_STATUS, disp_nonzero)
            self.assertEqual("fail-gate", disp_nonzero)
            self.assertIsNone(outcome_nonzero)

    def test_unreachability_observed_across_scoring_points(self) -> None:
        """Assertion (3): Observed status across both scoring points delegates to real code."""
        harness = test_defect_report.RescoreAfterAReaskTests()
        captured_statuses: list[Any] = []
        real_reconcile = runner_shared.reconcile_disposition

        def recorder(
            repo: Path,
            item: dict[str, Any],
            run_dir: Path,
            exit_code: int,
            plan_repo: Path | None = None,
        ) -> tuple[str, dict[str, Any] | None]:
            captured_statuses.append(item.get("status"))
            return real_reconcile(repo, item, run_dir, exit_code, plan_repo=plan_repo)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _run_dir, _state, _item, _events, _gate, launches = harness._drive(
                root,
                first_outcome=harness.NO_REPORT_PARTIAL,
                reask_outcome=harness.REASK_STILL_PARTIAL,
                reconcile=recorder,
            )

            # Two launches occurred: initial attempt and re-ask
            self.assertEqual(2, len(launches))

            # Exactly two reconcile_disposition calls: first score and rescore
            self.assertEqual(2, len(captured_statuses))

            # First score sees 'running', rescore sees first score's result ('fail-verify')
            self.assertEqual(["running", "fail-verify"], captured_statuses)

            # Neither scoring point observes merge-retry
            self.assertNotIn(
                runner_shared.INTEGRATION_DEFERRED_STATUS, captured_statuses
            )
