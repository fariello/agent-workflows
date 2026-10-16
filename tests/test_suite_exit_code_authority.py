#!/usr/bin/env python3
"""Behavioral tests for the suite exit code authority (IPD xssw86, backlog jgpts7).

Restores behavioral coverage that the post-merge suite's exit code, not its parsed
failing-test list, is the authority on integration:
- A non-passing suite never earns integration merely because its failing list is empty (the 32ij2j inversion).
- A passing exit earns integration regardless of the list.
- A non-passing suite always escalates to the agent with non-empty evidence rather than silently integrating.
- Empty lists on non-passing suites in relative comparisons (new_failures_since_baseline,
  unattributed_merged_failures) yield unknown judgements rather than vacuous passes.

Behavior-only tests: observable behavior and outcomes only (P16).
"""

from __future__ import annotations

import unittest

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd
from agent_workflows import runner_shared


def _suite_result(
    *,
    passing: bool = False,
    exit_code: int = 1,
    summary: str = "1 failed, 1 passed in 0.01s",
    reason: str = "the driver-run suite did not pass",
    cwd: str = ".",
    timeout_seconds: float = 600.0,
    elapsed_seconds: float = 0.5,
    failures: tuple[str, ...] = (),
) -> runner_shared.SuiteCheckResult:
    """Build a SuiteCheckResult with explicit defaults for suite adjudication tests."""
    return runner_shared.SuiteCheckResult(
        passing=passing,
        exit_code=exit_code,
        summary=summary,
        reason=reason,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        elapsed_seconds=elapsed_seconds,
        failures=failures,
    )


class SuiteExitCodeAuthorityTests(unittest.TestCase):
    """Behavioral tests restoring the exit code authority properties."""

    def test_red_exit_with_empty_failing_list_still_escalates(self) -> None:
        """The exit code, not the list, is the authority: a red suite with an empty list refuses and escalates."""
        for host_name, host_module in (("oc", oc_runipd), ("agy", agy_runipd)):
            with self.subTest(host=host_name, case="exit 1 empty failures"):
                res = _suite_result(passing=False, exit_code=1, failures=())
                verdict = host_module.integration_is_earned(
                    validate=False,
                    verify_disp=None,
                    suite_result=res,
                )
                self.assertFalse(
                    verdict.earned,
                    "The exit code, not the list, is the authority: exit 1 with empty failures must refuse integration",
                )
                self.assertEqual(
                    verdict.signal,
                    runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
                    "The exit code, not the list, is the authority: refusal signal must be suite-failed",
                )
                warranted, _ = runner_shared.gate_answer_is_warranted(
                    integration_gate_relevant=True,
                    earned=verdict.earned,
                    integration_signal=verdict.signal,
                    session_id="s",
                )
                self.assertTrue(
                    warranted,
                    "The exit code, not the list, is the authority: unparseable red suite must escalate to agent",
                )

            with self.subTest(host=host_name, case="exit 1 empty summary"):
                res = _suite_result(passing=False, exit_code=1, summary="", failures=())
                verdict = host_module.integration_is_earned(
                    validate=False,
                    verify_disp=None,
                    suite_result=res,
                )
                self.assertFalse(
                    verdict.earned,
                    "The exit code, not the list, is the authority: exit 1 with empty summary must refuse integration",
                )
                self.assertEqual(
                    verdict.signal,
                    runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
                    "The exit code, not the list, is the authority: refusal signal must be suite-failed",
                )
                warranted, _ = runner_shared.gate_answer_is_warranted(
                    integration_gate_relevant=True,
                    earned=verdict.earned,
                    integration_signal=verdict.signal,
                    session_id="s",
                )
                self.assertTrue(
                    warranted,
                    "The exit code, not the list, is the authority: empty summary red suite must escalate to agent",
                )

            for code in (124, 127):
                with self.subTest(host=host_name, exit_code=code):
                    res = _suite_result(
                        passing=False, exit_code=code, summary="", failures=()
                    )
                    verdict = host_module.integration_is_earned(
                        validate=False,
                        verify_disp=None,
                        suite_result=res,
                    )
                    self.assertFalse(
                        verdict.earned,
                        f"The exit code, not the list, is the authority: exit code {code} must refuse integration",
                    )
                    self.assertEqual(
                        verdict.signal,
                        runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
                        f"The exit code, not the list, is the authority: exit code {code} signal must be suite-failed",
                    )
                    warranted, _ = runner_shared.gate_answer_is_warranted(
                        integration_gate_relevant=True,
                        earned=verdict.earned,
                        integration_signal=verdict.signal,
                        session_id="s",
                    )
                    self.assertTrue(
                        warranted,
                        f"The exit code, not the list, is the authority: exit code {code} must escalate to agent",
                    )

    def test_passing_exit_earns_integration_regardless_of_the_list(self) -> None:
        """The exit code is the authority in both directions: exit 0 earns integration and is not taxed."""
        for host_name, host_module in (("oc", oc_runipd), ("agy", agy_runipd)):
            with self.subTest(host=host_name):
                res = _suite_result(
                    passing=True,
                    exit_code=0,
                    summary="9 passed",
                    failures=("FAILED stale::leftover",),
                )
                verdict = host_module.integration_is_earned(
                    validate=False,
                    verify_disp=None,
                    suite_result=res,
                )
                self.assertTrue(
                    verdict.earned,
                    "The exit code, not the list, is the authority: exit 0 earns integration regardless of failing list",
                )
                warranted, _ = runner_shared.gate_answer_is_warranted(
                    integration_gate_relevant=True,
                    earned=verdict.earned,
                    integration_signal=verdict.signal,
                    session_id="s",
                )
                self.assertFalse(
                    warranted,
                    "The exit code, not the list, is the authority: green suite is never taxed with a question",
                )

    def test_the_question_never_shows_an_empty_evidence_section(self) -> None:
        """An empty section reads as 'no failures'; question must show non-empty evidence."""
        text = _suite_result(failures=(), summary="").failing_text
        self.assertTrue(text.strip())
        prompt = runner_shared.gate_answer_question(
            failing=text, changed_files=("a.py",)
        )
        self.assertIn(text.splitlines()[0][:30], prompt)

    def test_new_failures_since_baseline_empty_red_is_unknown(self) -> None:
        """An empty merged list on a non-passing suite is unknown, never no-regression."""
        baseline = runner_shared.SuiteBaseline(
            state="completed",
            base_commit="abc",
            failures=("FAILED tests/t.py::a - assert 1 == 2",),
        )
        res_explicit = runner_shared.new_failures_since_baseline(
            merged_failures=(),
            baseline=baseline,
            suite_passed=False,
        )
        self.assertEqual(res_explicit.judgement, runner_shared.REVALIDATION_UNKNOWN)
        self.assertFalse(res_explicit.introduced_nothing)

        res_default = runner_shared.new_failures_since_baseline(
            merged_failures=(),
            baseline=baseline,
        )
        self.assertEqual(res_default.judgement, runner_shared.REVALIDATION_UNKNOWN)
        self.assertFalse(res_default.introduced_nothing)

    def test_new_failures_since_baseline_passing_control(self) -> None:
        """When suite_passed=True, an empty merged list is no-regression."""
        baseline = runner_shared.SuiteBaseline(
            state="completed",
            base_commit="abc",
            failures=("FAILED tests/t.py::a - assert 1 == 2",),
        )
        res_passing = runner_shared.new_failures_since_baseline(
            merged_failures=(),
            baseline=baseline,
            suite_passed=True,
        )
        self.assertEqual(
            res_passing.judgement, runner_shared.REVALIDATION_NO_REGRESSION
        )
        self.assertTrue(res_passing.introduced_nothing)

    def test_unattributed_merged_failures_empty_red_and_controls(self) -> None:
        """An empty merged list on a non-passing suite is unknown; controls verify non-empty behavior."""
        attributed = (
            runner_shared.normalize_failure_id("FAILED tests/t.py::a - assert 1 == 2"),
        )
        res_explicit = runner_shared.unattributed_merged_failures(
            merged_failures=(),
            attributed=attributed,
            suite_passed=False,
        )
        self.assertEqual(res_explicit.judgement, runner_shared.REVALIDATION_UNKNOWN)

        res_default = runner_shared.unattributed_merged_failures(
            merged_failures=(),
            attributed=attributed,
        )
        self.assertEqual(res_default.judgement, runner_shared.REVALIDATION_UNKNOWN)

        # Control: merged list with single attributed failure returns no-regression
        res_single = runner_shared.unattributed_merged_failures(
            merged_failures=("FAILED tests/t.py::a - x",),
            attributed=attributed,
            suite_passed=False,
        )
        self.assertEqual(res_single.judgement, runner_shared.REVALIDATION_NO_REGRESSION)

        # Control: merged list with unattributed failure returns regressed
        res_regressed = runner_shared.unattributed_merged_failures(
            merged_failures=("FAILED tests/t.py::a - x", "FAILED tests/t.py::b - y"),
            attributed=attributed,
            suite_passed=False,
        )
        self.assertEqual(res_regressed.judgement, runner_shared.REVALIDATION_REGRESSED)


if __name__ == "__main__":
    unittest.main()
