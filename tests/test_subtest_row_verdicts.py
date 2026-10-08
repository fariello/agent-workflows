"""Tests proving truthful row-level subTest verdicts under opt-in strict mode.

Tests observable behavior and recorded verdicts (GUIDING_PRINCIPLES P16):
- Pins the hazard of the append-only idiom (failing row falsely reported as PASS).
- Verifies strict-mode switch behavior:
  - When switch is OFF: aggregate error reported, subtest recorded as PASS.
  - When switch is ON: subtest recorded as FAIL, sweep continues, enclosing test fails.
- Verifies that all four repaired e2e gate tests fail in-context under strict mode
  when a row is corrupted, and continue executing remaining rows.
"""

from __future__ import annotations

import io
import os
import unittest

from agent_workflows import subtest_rows
import tests.test_executed_transition_gate_e2e as e2e


class SubTestRowVerdictsPropertyTests(unittest.TestCase):
    """Generic property tests comparing append-only vs in-context failure idioms."""

    def test_append_only_idiom_demonstrates_the_hazard(self):
        """Append-only subTest blocks record PASS for failing rows, hiding defects."""

        class AppendOnlyCase(unittest.TestCase):
            ROWS = [("row_pass", True), ("row_fail", False)]

            def test_run(self):
                wrong = []
                for case, ok in self.ROWS:
                    with self.subTest(case=case):
                        if not ok:
                            wrong.append(f"failed: {case}")
                self.assertEqual(wrong, [], f"aggregate: {wrong}")

        suite = unittest.TestSuite([AppendOnlyCase("test_run")])
        null_stream = io.StringIO()
        res = subtest_rows.SubTestRowResult(
            stream=null_stream, descriptions=True, verbosity=0
        )
        suite.run(res)

        records = res.subtest_records.get(AppendOnlyCase("test_run").id(), [])
        self.assertEqual(len(records), 2)
        # Hazard: both rows reported PASS even though row_fail was bad
        self.assertEqual(records[0]["status"], "PASS")
        self.assertEqual(records[1]["status"], "PASS")
        # Enclosing test did fail at aggregate assertion
        self.assertIn(AppendOnlyCase("test_run").id(), res.enclosing_failures)

    def test_strict_switch_idiom_when_switch_is_off(self):
        """When strict switch is OFF, behavior matches append-only with full aggregate prose."""

        class StrictSwitchCase(unittest.TestCase):
            ROWS = [("row_pass", True), ("row_fail", False)]

            def test_run(self):
                strict = os.environ.get("AW_ROW_STRICT") == "1"
                wrong = []
                for case, ok in self.ROWS:
                    with self.subTest(case=case):
                        if not ok:
                            wrong.append(f"failed: {case}")
                            if strict:
                                self.fail(f"in-context failure: {case}")
                self.assertEqual(wrong, [], f"aggregate prose listing {wrong}")

        orig_strict = os.environ.pop("AW_ROW_STRICT", None)
        try:
            suite = unittest.TestSuite([StrictSwitchCase("test_run")])
            null_stream = io.StringIO()
            res = subtest_rows.SubTestRowResult(
                stream=null_stream, descriptions=True, verbosity=0
            )
            suite.run(res)

            records = res.subtest_records.get(StrictSwitchCase("test_run").id(), [])
            self.assertEqual(len(records), 2)
            # Switch OFF: subtests report PASS
            self.assertEqual(records[0]["status"], "PASS")
            self.assertEqual(records[1]["status"], "PASS")
            # Enclosing test failed at aggregate
            self.assertIn(StrictSwitchCase("test_run").id(), res.enclosing_failures)
            self.assertEqual(len(res.failures), 1)
            self.assertIn("aggregate prose listing", res.failures[0][1])
        finally:
            if orig_strict is not None:
                os.environ["AW_ROW_STRICT"] = orig_strict

    def test_strict_switch_idiom_when_switch_is_on(self):
        """When strict switch is ON, failing row is recorded as FAIL and sweep completes."""

        class StrictSwitchCase(unittest.TestCase):
            ROWS = [("row_pass", True), ("row_fail", False), ("row_pass_2", True)]

            def test_run(self):
                strict = os.environ.get("AW_ROW_STRICT") == "1"
                wrong = []
                for case, ok in self.ROWS:
                    with self.subTest(case=case):
                        if not ok:
                            wrong.append(f"failed: {case}")
                            if strict:
                                self.fail(f"in-context failure: {case}")
                self.assertEqual(wrong, [], f"aggregate prose listing {wrong}")

        orig_strict = os.environ.get("AW_ROW_STRICT")
        os.environ["AW_ROW_STRICT"] = "1"
        try:
            suite = unittest.TestSuite([StrictSwitchCase("test_run")])
            null_stream = io.StringIO()
            res = subtest_rows.SubTestRowResult(
                stream=null_stream, descriptions=True, verbosity=0
            )
            suite.run(res)

            records = res.subtest_records.get(StrictSwitchCase("test_run").id(), [])
            self.assertEqual(len(records), 3)
            # Row 0 pass
            self.assertEqual(records[0]["status"], "PASS")
            # Row 1 fail
            self.assertEqual(records[1]["status"], "FAIL")
            # Row 2 pass (sweep was not aborted by earlier failure)
            self.assertEqual(records[2]["status"], "PASS")
            # Enclosing test failed
            self.assertFalse(res.wasSuccessful())
        finally:
            if orig_strict is None:
                os.environ.pop("AW_ROW_STRICT", None)
            else:
                os.environ["AW_ROW_STRICT"] = orig_strict


class RepairedBlocksVerdictsTests(unittest.TestCase):
    """Tests asserting all four repaired test blocks report truthful per-row verdicts."""

    def test_repaired_merge_decisions_fails_in_context_under_strict_mode(self):
        """MERGE_DECISIONS reports corrupted row as FAIL and runs remaining rows."""
        orig_rows = e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS
        try:
            rows = list(orig_rows)
            r0 = list(rows[0])
            r0[2] = 99  # want_rc = 99 (corrupted)
            rows[0] = tuple(r0)
            e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS = tuple(rows)

            stream = io.StringIO()
            outcomes = subtest_rows.run(
                "tests.test_executed_transition_gate_e2e.MergeAwareInTreeEvidenceTests.test_merge_state_never_becomes_a_blanket_exemption",
                stream=stream,
            )
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome["enclosing_verdict"], "FAILED")
            subtests = outcome["subtests"]
            self.assertEqual(len(subtests), 7)
            # Row 0 must be recorded as FAIL
            self.assertEqual(
                subtests[0]["status"],
                "FAIL",
                "MERGE_DECISIONS row 0 must report FAIL in strict mode",
            )
            # Remaining rows must be recorded as PASS (sweep was not aborted)
            for i in range(1, 7):
                self.assertEqual(
                    subtests[i]["status"],
                    "PASS",
                    f"MERGE_DECISIONS row {i} must report PASS",
                )
            self.assertFalse(outcome["failed_without_failing_subtest"])
        finally:
            e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS = orig_rows

    def test_repaired_detector_states_fails_in_context_under_strict_mode(self):
        """DETECTOR_STATES reports corrupted row as FAIL and runs remaining rows."""
        orig_rows = e2e.MergeAwareInTreeEvidenceTests.DETECTOR_STATES
        try:
            rows = list(orig_rows)
            r0 = list(rows[0])
            r0[1] = lambda self: (self.root, ["corrupted_sha"])
            rows[0] = tuple(r0)
            e2e.MergeAwareInTreeEvidenceTests.DETECTOR_STATES = tuple(rows)

            stream = io.StringIO()
            outcomes = subtest_rows.run(
                "tests.test_executed_transition_gate_e2e.MergeAwareInTreeEvidenceTests.test_the_merge_detector_reports_the_incoming_side_in_every_state",
                stream=stream,
            )
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome["enclosing_verdict"], "FAILED")
            subtests = outcome["subtests"]
            self.assertEqual(len(subtests), 4)
            # Row 0 must be recorded as FAIL
            self.assertEqual(
                subtests[0]["status"],
                "FAIL",
                "DETECTOR_STATES row 0 must report FAIL in strict mode",
            )
            # Remaining rows must be PASS
            for i in range(1, 4):
                self.assertEqual(
                    subtests[i]["status"],
                    "PASS",
                    f"DETECTOR_STATES row {i} must report PASS",
                )
            self.assertFalse(outcome["failed_without_failing_subtest"])
        finally:
            e2e.MergeAwareInTreeEvidenceTests.DETECTOR_STATES = orig_rows

    def test_repaired_situations_fails_in_context_under_strict_mode(self):
        """SITUATIONS reports corrupted row as FAIL and runs remaining rows."""
        orig_rows = e2e.PreCommitExecutedGateTests.SITUATIONS
        try:
            rows = list(orig_rows)
            r0 = list(rows[0])
            r0[3] = 99  # want_rc = 99 (corrupted)
            rows[0] = tuple(r0)
            e2e.PreCommitExecutedGateTests.SITUATIONS = tuple(rows)

            stream = io.StringIO()
            outcomes = subtest_rows.run(
                "tests.test_executed_transition_gate_e2e.PreCommitExecutedGateTests.test_each_staged_situation_gets_its_own_verdict_and_reason",
                stream=stream,
            )
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome["enclosing_verdict"], "FAILED")
            subtests = outcome["subtests"]
            self.assertEqual(len(subtests), 15)
            # Row 0 must be recorded as FAIL
            self.assertEqual(
                subtests[0]["status"],
                "FAIL",
                "SITUATIONS row 0 must report FAIL in strict mode",
            )
            # Remaining rows must be PASS
            for i in range(1, 15):
                self.assertEqual(
                    subtests[i]["status"],
                    "PASS",
                    f"SITUATIONS row {i} must report PASS",
                )
            self.assertFalse(outcome["failed_without_failing_subtest"])
        finally:
            e2e.PreCommitExecutedGateTests.SITUATIONS = orig_rows

    def test_repaired_installed_hooks_fails_in_context_under_strict_mode(self):
        """INSTALLED_HOOK_RUNS reports corrupted row as FAIL and runs remaining rows."""
        orig_rows = e2e.MergeAwareInTreeEvidenceTests.INSTALLED_HOOK_RUNS
        try:
            rows = list(orig_rows)
            r0 = list(rows[0])
            r0[4] = 99  # want_rc = 99 (corrupted)
            rows[0] = tuple(r0)
            e2e.MergeAwareInTreeEvidenceTests.INSTALLED_HOOK_RUNS = tuple(rows)

            stream = io.StringIO()
            outcomes = subtest_rows.run(
                "tests.test_executed_transition_gate_e2e.MergeAwareInTreeEvidenceTests.test_git_itself_enforces_the_gate_at_both_merge_stages",
                stream=stream,
            )
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome["enclosing_verdict"], "FAILED")
            subtests = outcome["subtests"]
            self.assertEqual(len(subtests), 4)
            # Row 0 must be recorded as FAIL
            self.assertEqual(
                subtests[0]["status"],
                "FAIL",
                "INSTALLED_HOOK_RUNS row 0 must report FAIL in strict mode",
            )
            # Remaining rows must be PASS
            for i in range(1, 4):
                self.assertEqual(
                    subtests[i]["status"],
                    "PASS",
                    f"INSTALLED_HOOK_RUNS row {i} must report PASS",
                )
            self.assertFalse(outcome["failed_without_failing_subtest"])
        finally:
            e2e.MergeAwareInTreeEvidenceTests.INSTALLED_HOOK_RUNS = orig_rows

    def test_repaired_merge_decisions_retains_aggregate_failure_when_switch_is_off(
        self,
    ):
        """With switch OFF, corrupted row is not recorded as FAIL and aggregate assertion fails."""
        orig_rows = e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS
        orig_strict = os.environ.pop("AW_ROW_STRICT", None)
        try:
            rows = list(orig_rows)
            r0 = list(rows[0])
            r0[2] = 99  # want_rc = 99 (corrupted)
            rows[0] = tuple(r0)
            e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS = tuple(rows)

            suite = unittest.TestSuite()
            suite.addTest(
                e2e.MergeAwareInTreeEvidenceTests(
                    "test_merge_state_never_becomes_a_blanket_exemption"
                )
            )
            null_stream = io.StringIO()
            res = subtest_rows.SubTestRowResult(
                stream=null_stream, descriptions=True, verbosity=0
            )
            suite.run(res)

            test_id = e2e.MergeAwareInTreeEvidenceTests(
                "test_merge_state_never_becomes_a_blanket_exemption"
            ).id()
            records = res.subtest_records.get(test_id, [])
            self.assertEqual(len(records), 7)
            # Switch OFF: row 0 reports PASS (the append-only / default behavior)
            self.assertEqual(records[0]["status"], "PASS")
            # Enclosing test failed at aggregate assertion
            self.assertIn(test_id, res.enclosing_failures)
            self.assertEqual(len(res.failures), 1)
            self.assertIn("decided 1 of 7 merge situations wrongly", res.failures[0][1])
        finally:
            e2e.MergeAwareInTreeEvidenceTests.MERGE_DECISIONS = orig_rows
            if orig_strict is not None:
                os.environ["AW_ROW_STRICT"] = orig_strict
