"""Tests for stranded run exit code behavior (strandexit entv1d).

Covers:
- E-05 (a): Success-bar statuses with refusing integration_signal exit nonzero.
- E-05 (b): Review item with review_integrated: False exits nonzero.
- E-05 (c): Landed item with earned signal exits 0.
- E-05 (d): Item with no integration_signal key exits 0.
- E-05 (e): Item released by gate answer exits 0.
- E-05 (f): Mixed queue with one stranded and one landed item exits nonzero.
- E-05 (g): Deliberate stop over queued plus landed items exits 0.
- E-05 (h): Queued item with stale refusing signal projects to "queued" and stop exits 0.
- E-05 (i): Narrow-siting guard: non-success statuses project verbatim, guarding PR-501.
"""

from typing import Any
import unittest

from agent_workflows import runner_shared, runner_stop


def _exit_code(queue: list[dict[str, Any]], *, stopped: bool = False) -> int:
    """Helper to evaluate the deliberate_stop_exit_code over projected tokens."""
    projected = runner_shared.exit_code_statuses(queue)
    return runner_stop.deliberate_stop_exit_code(
        projected,
        success_states={runner_shared.EXIT_SUCCESS_TOKEN},
        stopped=stopped,
    )


class TestStrandedRunExitCode(unittest.TestCase):
    """Behavioral tests pinning the exit code for stranded runs by outcome (E-05)."""

    def test_case_a_success_bar_statuses_with_refusing_signal_exit_nonzero(
        self,
    ) -> None:
        """Case (a): Success-bar statuses with refusing integration_signal exit nonzero.

        Pre-change baseline measured at E-01 (HEAD e2105111c / review c6c573a4):
        approved: rc=0, projected=['aw-item-met-its-action-success-bar']
        executed: rc=0, projected=['aw-item-met-its-action-success-bar']
        retired:  rc=0, projected=['aw-item-met-its-action-success-bar']
        Pre-change code exited 0 for all three, contradicting the run's stranded reality.
        With the fix, all three project onto EXIT_STRANDED_TOKEN and exit nonzero (1).
        """
        for status in runner_shared.EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES:
            with self.subTest(status=status):
                queue = [
                    {
                        "action": "execute",
                        "status": status,
                        "integration_signal": "suite-failed",
                    }
                ]
                projected = runner_shared.exit_code_statuses(queue)
                self.assertEqual(projected, [runner_shared.EXIT_STRANDED_TOKEN])
                self.assertEqual(_exit_code(queue), 1)
                self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 1)

    def test_case_b_review_stranded_shape_exits_nonzero(self) -> None:
        """Case (b): A review item with review_integrated: False exits nonzero."""
        queue = [
            {
                "action": "review",
                "status": "executed",
                "review_integrated": False,
            }
        ]
        projected = runner_shared.exit_code_statuses(queue)
        self.assertEqual(projected, [runner_shared.EXIT_STRANDED_TOKEN])
        self.assertEqual(_exit_code(queue), 1)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 1)

    def test_case_c_landed_item_with_earned_signal_exits_zero(self) -> None:
        """Case (c): A landed item with earned signal ('verifier', 'driver-run-suite') exits 0."""
        for signal in ("verifier", "driver-run-suite"):
            with self.subTest(signal=signal):
                queue = [
                    {
                        "action": "execute",
                        "status": "executed",
                        "integration_signal": signal,
                    }
                ]
                projected = runner_shared.exit_code_statuses(queue)
                self.assertEqual(projected, [runner_shared.EXIT_SUCCESS_TOKEN])
                self.assertEqual(_exit_code(queue), 0)
                self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 0)

    def test_case_d_item_with_no_integration_signal_exits_zero(self) -> None:
        """Case (d): An item with no integration_signal key at all still exits 0."""
        queue = [{"action": "execute", "status": "executed"}]
        projected = runner_shared.exit_code_statuses(queue)
        self.assertEqual(projected, [runner_shared.EXIT_SUCCESS_TOKEN])
        self.assertEqual(_exit_code(queue), 0)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 0)

    def test_case_e_item_released_by_gate_answer_exits_zero(self) -> None:
        """Case (e): An item released by the gate answer still exits 0."""
        queue = [
            {
                "action": "execute",
                "status": "executed",
                "integration_signal": "suite-failed",
                "integration_released_by_answer": True,
            }
        ]
        projected = runner_shared.exit_code_statuses(queue)
        self.assertEqual(projected, [runner_shared.EXIT_SUCCESS_TOKEN])
        self.assertEqual(_exit_code(queue), 0)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 0)

    def test_case_f_mixed_queue_with_stranded_and_landed_exits_nonzero(self) -> None:
        """Case (f): A mixed queue with one stranded and one landed item exits nonzero."""
        queue = [
            {
                "action": "execute",
                "status": "executed",
                "integration_signal": "verifier",
            },
            {
                "action": "execute",
                "status": "executed",
                "integration_signal": "suite-failed",
            },
        ]
        self.assertEqual(_exit_code(queue), 1)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 1)

    def test_case_g_deliberate_stop_over_queued_plus_landed_exits_zero(self) -> None:
        """Case (g): A deliberate stop over queued plus landed items still exits 0 (c4gd2h A1/A4)."""
        queue = [
            {
                "action": "execute",
                "status": "executed",
                "integration_signal": "verifier",
            },
            {"action": "execute", "status": "queued"},
        ]
        self.assertEqual(_exit_code(queue, stopped=True), 0)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=True), 0)

    def test_case_h_queued_item_with_stale_refusing_signal_projects_to_queued(
        self,
    ) -> None:
        """Case (h): A queued item with a stale refusing signal still projects to queued (F-14)."""
        queue = [
            {
                "action": "execute",
                "status": "queued",
                "integration_signal": "suite-failed",
            }
        ]
        projected = runner_shared.exit_code_statuses(queue)
        self.assertEqual(projected, ["queued"])
        self.assertEqual(_exit_code(queue, stopped=True), 0)
        self.assertEqual(runner_shared.run_exit_code(queue, stopped=True), 0)

    def test_case_i_narrow_siting_guard_non_success_statuses_pass_through_verbatim(
        self,
    ) -> None:
        """Case (i): Narrow-siting guard: already-failing statuses project verbatim (PR-501, F-13).

        Asserts that each of integration-blocked, failed, fail-gate, and substantially-complete
        carrying a refusing signal projects onto ITS OWN STATUS VERBATIM and NOT onto the
        stranded token. If the test were sited above the success arm, this case fails red.
        """
        for status in (
            "integration-blocked",
            "failed",
            "fail-gate",
            "substantially-complete",
        ):
            with self.subTest(status=status):
                queue = [
                    {
                        "action": "execute",
                        "status": status,
                        "integration_signal": "suite-failed",
                    }
                ]
                projected = runner_shared.exit_code_statuses(queue)
                self.assertEqual(
                    projected,
                    [status],
                    f"Status {status} must pass through verbatim, not be relabeled",
                )
                self.assertNotEqual(
                    projected,
                    [runner_shared.EXIT_STRANDED_TOKEN],
                    f"Status {status} must not project onto EXIT_STRANDED_TOKEN",
                )
                self.assertEqual(_exit_code(queue), 1)
                self.assertEqual(runner_shared.run_exit_code(queue, stopped=False), 1)
