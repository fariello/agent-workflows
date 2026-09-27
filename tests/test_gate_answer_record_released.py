"""Behavioral tests for the gate-answer record 'released' field (IPD nzznlm / backlog w51mpv).

Proves that:
1. 'released' records whether the answer actually released the lane (agreeing with GateAnswerOutcome.release).
2. For verified 'fixed', 'released' is True while 'integrates' remains False (resolving the contradiction).
3. For refused or unverified repairs, 'released' is False.
4. For 'not-mine', both 'released' and 'integrates' are True.
5. Pre-existing keys are preserved (additivity control) and round-trip through JSON.
6. A direct call to gate_answer_record with no 'released' argument yields None.
7. An interrupted follow-up records released=False and is distinguishable from genuine refusal.
"""

from __future__ import annotations

import json
import tempfile
import types
import unittest
from typing import Any

from agent_workflows import runner_shared


def _drive_gate_answer(
    tok: str,
    *,
    rerun_passing: bool = True,
    rerun_suite: Any = "default",
    retry_budget: int = 1,
) -> runner_shared.GateAnswerOutcome:
    failing = types.SimpleNamespace(
        passing=False,
        failures=["test_failing.py::test_case"],
        failing_text="test_failing.py::test_case failed",
        summary="1 failed",
    )
    passing = types.SimpleNamespace(
        passing=True,
        failures=[],
        failing_text="",
        summary="all passed",
    )
    if rerun_suite == "default":
        actual_rerun = (lambda: passing) if rerun_passing else (lambda: failing)
    else:
        actual_rerun = rerun_suite

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
        json.dump(
            {runner_shared.GATE_ANSWER_KEY: {"answer": tok, "reason": "test-reason"}},
            f,
        )
        f.flush()
        return runner_shared.perform_gate_answer(
            suite_result=failing,
            ask=lambda prompt: None,
            outcome_path=f.name,
            rerun_suite=actual_rerun,
            retry_budget=retry_budget,
        )


class GateAnswerRecordReleasedTests(unittest.TestCase):
    def test_case_1_four_tokens_released_matches_outcome_release(self) -> None:
        """Case 1: For each of the four tokens, record['released'] == outcome.release."""
        for tok in runner_shared.GATE_ANSWERS:
            outcome = _drive_gate_answer(tok)
            self.assertEqual(
                outcome.record["released"],
                outcome.release,
                f"Mismatch for token {tok!r}: record['released']={outcome.record.get('released')} vs release={outcome.release}",
            )

    def test_case_2_fixed_passing_rerun_contradiction_resolved(self) -> None:
        """Case 2: fixed with passing re-run yields released=True, integrates=False."""
        outcome = _drive_gate_answer("fixed", rerun_passing=True)
        self.assertIs(outcome.record["released"], True)
        self.assertIs(outcome.record["integrates"], False)
        self.assertIs(outcome.release, True)

    def test_case_3_fixed_failing_rerun_exhausted_budget(self) -> None:
        """Case 3: fixed with re-run that keeps failing yields released=False."""
        outcome = _drive_gate_answer("fixed", rerun_passing=False, retry_budget=1)
        self.assertIs(outcome.record["released"], False)
        self.assertIs(outcome.release, False)

    def test_case_4_fixed_rerun_suite_none(self) -> None:
        """Case 4: fixed with rerun_suite=None yields released=False."""
        outcome = _drive_gate_answer("fixed", rerun_suite=None)
        self.assertIs(outcome.record["released"], False)
        self.assertIs(outcome.release, False)

    def test_case_5_not_mine_releases_and_integrates(self) -> None:
        """Case 5: not-mine yields released=True and integrates=True."""
        outcome = _drive_gate_answer("not-mine")
        self.assertIs(outcome.record["released"], True)
        self.assertIs(outcome.record["integrates"], True)
        self.assertIs(outcome.release, True)

    def test_case_6_control_preexisting_keys_preserved(self) -> None:
        """Case 6 (CONTROL): The record carries every pre-existing key (additivity check)."""
        pre_existing_keys = {
            "answer",
            "reason",
            "violation",
            "usable",
            "integrates",
            "refuses",
            "awaits_human_decision",
            "asked",
            "ask_reason",
            "session_id",
            "signal",
            "failing_tests",
            "recheck_attempts",
            "recheck_budget",
            "recheck_passed",
            "recheck_summary",
            "suite_baseline",
        }
        outcome = _drive_gate_answer("not-mine")
        rec = outcome.record
        self.assertTrue(pre_existing_keys.issubset(rec.keys()))
        self.assertEqual(set(rec.keys()) - {"released"}, pre_existing_keys)

    def test_case_7_direct_call_without_released_yields_none(self) -> None:
        """Case 7: gate_answer_record called directly with no released argument yields 'released': None."""
        verdict = runner_shared.validate_gate_answer(
            {"answer": "not-mine", "reason": "because"}
        )
        rec = runner_shared.gate_answer_record(verdict, asked=True, ask_reason="")
        self.assertIs(rec["released"], None)

    def test_case_8_control_json_roundtrip(self) -> None:
        """Case 8 (CONTROL): The record round-trips through json.dumps/json.loads unchanged."""
        outcome = _drive_gate_answer("not-mine")
        rec = outcome.record
        self.assertEqual(json.loads(json.dumps(rec)), rec)

    def test_case_9_interrupted_follow_up_record(self) -> None:
        """Case 9 (E-05): Interrupted follow-up records released=False and is distinguishable from refusal."""
        verdict = runner_shared.GateAnswerVerdict(
            "",
            "",
            "the follow-up turn was interrupted before it answered",
        )
        # Check that the pre-change baseline record had all four boolean fields False:
        rec_unadorned = runner_shared.gate_answer_record(
            verdict,
            asked=True,
            ask_reason="the follow-up turn was interrupted before it answered",
        )
        self.assertIs(rec_unadorned["usable"], False)
        self.assertEqual(rec_unadorned["answer"], "")
        self.assertIs(rec_unadorned["integrates"], False)
        self.assertIs(rec_unadorned["refuses"], False)

        try:
            rec = runner_shared.gate_answer_record(
                verdict,
                asked=True,
                ask_reason="the follow-up turn was interrupted before it answered",
                released=False,
            )
        except TypeError:
            rec = rec_unadorned

        self.assertIs(rec["released"], False)
        self.assertIs(rec["usable"], False)
        self.assertEqual(rec["answer"], "")
        self.assertIs(rec["integrates"], False)
        self.assertIs(rec["refuses"], False)


if __name__ == "__main__":
    unittest.main()
