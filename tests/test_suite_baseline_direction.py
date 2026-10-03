"""Behavioral tests for the pre-work suite baseline direction rule.

Authored under plan `kcc71f`. This module pins the BEHAVIORAL DIRECTION of the pre-work
suite baseline rule rather than asserting on comment or docstring text. In accordance with
maintainer ruling and GUIDING_PRINCIPLES P16, this file asserts only on returned runtime
verdicts from `_relative_revalidation_verdict` and reads no module source or comment text.

The direction rule enforces two invariants:
1. Permissive direction is reachable: a baseline comparison can excuse pre-existing failures,
   turning what would otherwise be a refusal into a pass.
2. Forbidden direction is absent: a baseline comparison never makes an outcome stricter (no
   baseline value turns a pass into a refusal across green, red, or unmeasured suites).
"""

from typing import Any, Mapping

from agent_workflows import runner_shared


def _make_item(baseline_record: Mapping[str, Any] | None) -> dict[str, Any]:
    item: dict[str, Any] = {"id6": "kcc71f"}
    if baseline_record is not None:
        item["attempts"] = [{"suite_baseline": baseline_record}]
    else:
        item["attempts"] = [{}]
    return item


def test_permissive_direction_is_reachable() -> None:
    """Assertion (a): A red measurement whose failures the baseline names passes where no baseline refuses."""
    failing_line = "FAILED tests/t.py::test_a - assert 1 == 2"
    red_measurement = {
        "passed": False,
        "measured": True,
        "suite_passed": False,
        "failures": [failing_line],
        "reason": "1 failure",
    }
    baseline_matching = {
        "state": "completed",
        "base_commit": "abcdef012345",
        "failures": [failing_line],
        "reason": "1 failure",
        "summary": "1 failed",
    }

    item_with_baseline = _make_item(baseline_matching)
    item_without_baseline = _make_item(None)

    passed_with, reason_with, comp_with = runner_shared._relative_revalidation_verdict(
        item_with_baseline, red_measurement
    )
    passed_without, reason_without, comp_without = (
        runner_shared._relative_revalidation_verdict(
            item_without_baseline, red_measurement
        )
    )

    assert (
        passed_with is True
    ), f"Expected red suite with matching baseline to pass, got False: {reason_with}"
    assert (
        passed_without is False
    ), f"Expected red suite without baseline to refuse, got True: {reason_without}"
    assert comp_with is not None and comp_with.introduced_nothing is True
    assert (
        comp_without is not None
        and comp_without.judgement == runner_shared.REVALIDATION_UNKNOWN
    )


def test_forbidden_direction_is_absent() -> None:
    """Assertion (b): Across the E-01 matrix, no baseline value turns a pass into a refusal."""
    measurements = {
        "red": {
            "passed": False,
            "measured": True,
            "suite_passed": False,
            "failures": ["FAILED tests/t.py::test_a - assert 1 == 2"],
            "reason": "1 failure",
        },
        "green": {
            "passed": True,
            "measured": True,
            "suite_passed": True,
            "failures": [],
            "reason": "passed",
        },
        "unmeasured": {
            "passed": False,
            "measured": False,
            "suite_passed": False,
            "failures": [],
            "reason": "unmeasured harness fault",
        },
    }

    baselines = {
        "(a) names same": {
            "state": "completed",
            "base_commit": "abcdef012345",
            "failures": ["FAILED tests/t.py::test_a - assert 1 == 2"],
            "reason": "1 failure",
            "summary": "1 failed",
        },
        "(b) names other": {
            "state": "completed",
            "base_commit": "abcdef012345",
            "failures": ["FAILED tests/t.py::test_b - assert 3 == 4"],
            "reason": "1 failure",
            "summary": "1 failed",
        },
        "(c) empty completed": {
            "state": "completed",
            "base_commit": "abcdef012345",
            "failures": [],
            "reason": "passed",
            "summary": "all passed",
        },
        "(d) no baseline": None,
    }

    for m_name, m_val in measurements.items():
        verdict_without, _, _ = runner_shared._relative_revalidation_verdict(
            _make_item(None), m_val
        )
        for b_name, b_val in baselines.items():
            verdict_with, reason_with, _ = runner_shared._relative_revalidation_verdict(
                _make_item(b_val), m_val
            )
            # The baseline must never turn a pass into a refusal.
            if verdict_without:
                assert verdict_with, f"Baseline {b_name} turned a passing {m_name} measurement into a refusal: {reason_with}"
