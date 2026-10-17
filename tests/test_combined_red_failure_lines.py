"""Behavioral tests for runner_shared.combined_red_failure_lines (IPD 44nfmd E-06)."""

from __future__ import annotations

import pytest
from agent_workflows import runner_shared

pytestmark = pytest.mark.core


def test_combined_red_failure_lines_with_baseline_comparison_new_ids() -> None:
    record = {
        "failures": [
            "tests/test_old.py::test_failing_baseline",
            "tests/test_new.py::test_new_failure",
        ],
        "baseline_comparison": {
            "new_ids": ["tests/test_new.py::test_new_failure"],
            "baseline_ids": ["tests/test_old.py::test_failing_baseline"],
        },
    }
    result = runner_shared.combined_red_failure_lines(record)
    assert "- tests/test_new.py::test_new_failure" in result
    assert "test_failing_baseline" not in result


def test_combined_red_failure_lines_with_only_failures_and_none_baseline() -> None:
    record = {
        "failures": ["tests/test_demo.py::test_one", "tests/test_demo.py::test_two"],
        "baseline_comparison": None,
    }
    result = runner_shared.combined_red_failure_lines(record)
    assert "- tests/test_demo.py::test_one" in result
    assert "- tests/test_demo.py::test_two" in result


def test_combined_red_failure_lines_without_ids_and_budget_reason() -> None:
    budget_reason = (
        "suite FAILED with exit 1 in /repo ONLY on the core-tier wall-time budget "
        "(no test failed; 810 passed)"
    )
    record = {
        "reason": budget_reason,
        "failures": [],
        "baseline_comparison": None,
    }
    result = runner_shared.combined_red_failure_lines(record)
    assert budget_reason in result
    assert (
        "no failing test id was recorded; the recorded revalidation reason was: "
        in result
    )
    assert "no test ids recorded" not in result


def test_combined_red_failure_lines_empty_mapping() -> None:
    result = runner_shared.combined_red_failure_lines({})
    assert "(no reason recorded)" in result
    assert (
        result
        == "no failing test id was recorded; the recorded revalidation reason was: (no reason recorded)"
    )
