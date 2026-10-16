"""Behavioral tests for perform_gate_answer baseline indifference (IPD tosnwd).

Restores regression coverage for the maintainer's 2026-09-08 and 2026-09-20 binding ruling:
no programmatic check may refuse or rescue a gate-answer verdict on the strength of a suite baseline,
and the baseline must alter nothing in the outcome except the 'suite_baseline' audit record itself.
"""

from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from typing import Any

from agent_workflows import oc_runipd
from agent_workflows import runner_shared

DEFAULT_FAILING_ID = (
    "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2"
)

FIELDS_TO_COMPARE = (
    "answer",
    "reason",
    "usable",
    "integrates",
    "refuses",
    "released",
    "awaits_human_decision",
    "violation",
    "recheck_attempts",
    "recheck_passed",
    "failing_tests",
)


def _suite_result(
    failures: tuple[str, ...] = (DEFAULT_FAILING_ID,),
) -> oc_runipd.SuiteCheckResult:
    return oc_runipd.SuiteCheckResult(
        passing=False,
        exit_code=1,
        summary="1 failed, 7830 passed, 3 skipped, 2 xfailed in 198.60s",
        reason="stub",
        cwd="/primary",
        timeout_seconds=oc_runipd.SUITE_CHECK_TIMEOUT_SECONDS,
        elapsed_seconds=198.6,
        failures=failures,
    )


def _completed(
    failures: tuple[str, ...] = (DEFAULT_FAILING_ID,),
    *,
    base_commit: str = "0123456789abcdef",
) -> runner_shared.SuiteBaseline:
    return runner_shared.SuiteBaseline(
        state=runner_shared.SUITE_BASELINE_COMPLETED,
        base_commit=base_commit,
        failures=failures,
        summary=f"{len(failures)} failed, 7830 passed in 198.60s",
    )


def _perform(
    answer: dict[str, Any],
    baseline: runner_shared.SuiteBaseline | None,
) -> runner_shared.GateAnswerOutcome:
    with tempfile.TemporaryDirectory() as temp:
        path = pathlib.Path(temp) / "outcome.json"

        def ask(prompt: str) -> tuple[int, str, pathlib.Path, list[str]]:
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "disposition": "executed",
                        runner_shared.GATE_ANSWER_KEY: answer,
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses-1", path, ["stub"]

        return runner_shared.perform_gate_answer(
            suite_result=_suite_result(),
            changed_files=("agent_workflows/term.py",),
            ask=ask,
            outcome_path=path,
            session_id="ses-1",
            baseline=baseline,
        )


class GateAnswerBaselineIndifferenceTests(unittest.TestCase):
    def test_not_mine_outcome_equivalence(self) -> None:
        """A not-mine verdict produces identical outcomes across all baseline states."""
        answer = {
            "answer": "not-mine",
            "reason": "it fails in a file I never touched",
        }
        corroborating = _perform(answer, _completed((DEFAULT_FAILING_ID,)))
        contradicting = _perform(
            answer,
            _completed(("FAILED tests/test_something_else.py::T::test_other",)),
        )
        absent = _perform(
            answer,
            runner_shared.suite_baseline_absent("no baseline was taken"),
        )
        unsupplied = _perform(answer, None)

        self.assertTrue(corroborating.release)
        self.assertTrue(contradicting.release)
        self.assertTrue(absent.release)
        self.assertTrue(unsupplied.release)

        self.assertEqual(corroborating.record["answer"], "not-mine")
        self.assertEqual(contradicting.record["answer"], "not-mine")
        self.assertEqual(absent.record["answer"], "not-mine")
        self.assertEqual(unsupplied.record["answer"], "not-mine")

        for field in FIELDS_TO_COMPARE:
            with self.subTest(field=field):
                self.assertEqual(
                    corroborating.record[field],
                    contradicting.record[field],
                    f"{field} differs between corroborating and contradicting baselines",
                )
                self.assertEqual(
                    corroborating.record[field],
                    absent.record[field],
                    f"{field} differs between corroborating and absent baselines",
                )
                self.assertEqual(
                    corroborating.record[field],
                    unsupplied.record[field],
                    f"{field} differs between corroborating and unsupplied (None) baselines",
                )

    def test_differing_keys_is_only_suite_baseline(self) -> None:
        """A record is not a check: the audit field may differ, and nothing else may."""
        answer = {"answer": "not-mine", "reason": "unrelated failure"}
        completed_outcome = _perform(answer, _completed())
        absent_outcome = _perform(
            answer, runner_shared.suite_baseline_absent("no baseline was taken")
        )
        differing = {
            k
            for k in completed_outcome.record
            if completed_outcome.record[k] != absent_outcome.record.get(k)
        }
        self.assertEqual(
            {"suite_baseline"},
            differing,
            "exactly one field may differ between completed and absent baseline, and it must be suite_baseline",
        )

    def test_mine_symmetry(self) -> None:
        """The property is symmetric: the baseline must not rescue a refusal either."""
        answer = {"answer": "mine", "reason": "I broke it"}
        with_completed = _perform(answer, _completed())
        with_none = _perform(answer, None)
        self.assertFalse(with_completed.release)
        self.assertFalse(with_none.release)
        self.assertEqual(with_completed.record["answer"], "mine")
        self.assertEqual(with_none.record["answer"], "mine")
        differing = {
            k
            for k in with_completed.record
            if with_completed.record[k] != with_none.record.get(k)
        }
        self.assertEqual(
            {"suite_baseline"},
            differing,
            "exactly one field may differ for mine answer, and it must be suite_baseline",
        )


if __name__ == "__main__":
    unittest.main()
