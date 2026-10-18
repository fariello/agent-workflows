"""Tests for runner_shared.aggregated_run_items and run_exit_code (mh60nd/q32qeg E-05, E-06)."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_evidence,
    runner_shared,
    runner_shutdown,
    runner_stop,
)


class TestRunExitAggregate(unittest.TestCase):
    """Behavioral tests for the spec 25kzda 5.6 run exit aggregate wiring (E-05)."""

    def test_case_a_defect_fixed_human_gate_returns_exit_3(self):
        """Case (a): The defect is fixed - an execute item requiring approval yields exit 3."""
        queue = [{"action": "execute", "status": "reviewed", "needs_input": True}]
        exit_code = runner_shared.run_exit_code(queue, stopped=False)
        self.assertEqual(
            exit_code,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_NEEDS_INPUT],
        )

    def test_case_b_spec_review_regression_prevented_returns_exit_0(self):
        """Case (b): The regression is prevented - successfully reviewed spec yields exit 0.

        F-05: runner_shared sets needs_input=True on a spec that reviewed SUCCESSFULLY.
        Mapping the raw flag onto needs_input without checking not item_reached_success
        would regress a passing spec review from exit 0 to exit 3.
        """
        queue = [
            {
                "action": "review",
                "status": "reviewed",
                "artifact_type": "spec",
                "needs_input": True,
            }
        ]
        exit_code = runner_shared.run_exit_code(queue, stopped=False)
        self.assertEqual(
            exit_code,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )

    def test_case_c_precedence_gate_over_failure_returns_exit_3(self):
        """Case (c): Precedence - a human-gated item outranks a plain failure."""
        queue = [
            {"action": "execute", "status": "reviewed", "needs_input": True},
            {"action": "execute", "status": "failed"},
        ]
        exit_code = runner_shared.run_exit_code(queue, stopped=False)
        self.assertEqual(
            exit_code,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_NEEDS_INPUT],
        )

    def test_case_d_deliberate_stop_with_queued_remainder_exits_0(self):
        """Case (d): The deliberate stop concession still exits 0 when remainder is queued."""
        queue = [
            {"action": "execute", "status": "executed"},
            {"action": "execute", "status": "queued"},
        ]
        exit_stopped = runner_shared.run_exit_code(queue, stopped=True)
        self.assertEqual(
            exit_stopped,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )
        exit_not_stopped = runner_shared.run_exit_code(queue, stopped=False)
        self.assertNotEqual(
            exit_not_stopped,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )

    def test_case_d2_gated_deliberate_stop_still_exits_0(self):
        """Case (d2): Deliberate stop still exits 0 when the excused queued item carries needs_input.

        Added at review (PR-801, F-14): F-14 measures that the originally-authored clause order
        returns 3 here, because aggregate_run_exit raises its needs_input candidate without
        consulting the item's contribution. Clause 2 must suppress needs_input under stopped=True
        so the deliberate-stop concession wins over the stale gate annotation.
        """
        queue = [
            {"action": "execute", "status": "executed"},
            {"action": "execute", "status": "queued", "needs_input": True},
        ]
        exit_code = runner_shared.run_exit_code(queue, stopped=True)
        self.assertEqual(
            exit_code,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )

    def test_case_e_malformed_entry_is_nonzero_under_both_stopped_arms(self):
        """Case (e): A malformed entry is nonzero under both stopped arms."""
        queue = ["not-a-mapping-entry"]
        exit_stopped = runner_shared.run_exit_code(queue, stopped=True)
        self.assertNotEqual(
            exit_stopped,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )
        exit_not_stopped = runner_shared.run_exit_code(queue, stopped=False)
        self.assertNotEqual(
            exit_not_stopped,
            run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ALL_CLEAR],
        )

    def test_case_f_nothing_is_mutated(self):
        """Case (f): Queue entries are never mutated by the projection (spec c4gd2h R22)."""
        queue = [
            {"action": "execute", "status": "reviewed", "needs_input": True},
            {
                "action": "review",
                "status": "reviewed",
                "artifact_type": "spec",
                "needs_input": True,
            },
            {"action": "execute", "status": "queued"},
        ]
        expected = copy.deepcopy(queue)
        _ = runner_shared.run_exit_code(queue, stopped=True)
        self.assertEqual(queue, expected)
        _ = runner_shared.run_exit_code(queue, stopped=False)
        self.assertEqual(queue, expected)


class TestRunExitEquivalenceSweep(unittest.TestCase):
    """Exhaustive equivalence sweep comparing old vs new exit computation (E-06)."""

    def test_exhaustive_equivalence_sweep(self):
        """Exhaustively verify that the change is a strict, bounded refinement (1 -> 3)."""
        actions = ("execute", "review", "plan", "skip", "orchestrate", None)
        expected_total = len(runner_shutdown.KNOWN_ITEM_STATUSES) * len(actions) * 2 * 2
        total = 0
        diffs = []
        for status in runner_shutdown.KNOWN_ITEM_STATUSES:
            for action in actions:
                for needs_input in (False, True):
                    for stopped in (False, True):
                        total += 1
                        entry = {"status": status, "needs_input": needs_input}
                        if action is not None:
                            entry["action"] = action
                        old_rc = runner_stop.deliberate_stop_exit_code(
                            runner_shared.exit_code_statuses([entry]),
                            success_states={runner_shared.EXIT_SUCCESS_TOKEN},
                            stopped=stopped,
                        )
                        new_rc = runner_shared.run_exit_code([entry], stopped=stopped)
                        if old_rc != new_rc:
                            diffs.append(
                                (
                                    status,
                                    action,
                                    needs_input,
                                    stopped,
                                    old_rc,
                                    new_rc,
                                )
                            )

        self.assertEqual(total, expected_total)
        self.assertTrue(diffs, "Equivalence sweep difference set must not be empty")
        self.assertTrue(
            all(d[2] is True or d[0] == "awaiting-human" for d in diffs),
            "Every differing combination must have needs_input=True or status == awaiting-human",
        )
        self.assertTrue(
            all((d[4], d[5]) == (1, 3) for d in diffs),
            "Every differing combination must be exactly (old, new) == (1, 3)",
        )


class RunQueueExitCodeReflectsTheRealOutcome(unittest.TestCase):
    """Behavioral tests verifying run_queue exit code reflects terminal item status across hosts (eg6r2t)."""

    def _drive_run(self, module, terminal_status: str) -> tuple[int, dict]:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        run_dir = root / "run-test"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = {
            "position": 1,
            "id6": "aaa111",
            "setid": "s",
            "action": "execute",
            "kind": "child",
            "status": "queued",
            "dependencies": [],
            "attempts": [],
        }
        state = {
            "schema_version": 1,
            "run_id": "run-test",
            "repo": str(root),
            "created_at": "2026-10-14T00:00:00+00:00",
            "updated_at": "2026-10-14T00:00:00+00:00",
            "selectors": ["synthetic"],
            "options": {},
            "set_sessions": {},
            "queue": [item],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        def fake_exec(rd, st, it, *a, **kw):
            it["status"] = terminal_status
            module.save_state(rd, st)

        buf = io.StringIO()
        with (
            patch.object(module, "execute_item", side_effect=fake_exec),
            contextlib.redirect_stdout(buf),
            contextlib.redirect_stderr(buf),
        ):
            exit_code = module.run_queue(run_dir, retry_incomplete=False)

        reloaded_state = json.loads(
            (run_dir / "state.json").read_text(encoding="utf-8")
        )
        return exit_code, reloaded_state

    def test_a_fully_executed_queue_exits_zero(self):
        """Control test (E-01): an executed item exits 0 and remains executed on both hosts."""
        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
            with self.subTest(host=host_name):
                exit_code, state = self._drive_run(module, "executed")
                self.assertEqual(exit_code, 0)
                self.assertEqual(state["queue"][0]["status"], "executed")

    def test_the_exit_code_reads_success_states_not_execution_success_states(self):
        """Restored S-29 property (E-02): substantially-complete exits nonzero on both hosts."""
        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
            with self.subTest(host=host_name):
                exit_code, state = self._drive_run(module, "substantially-complete")
                self.assertNotEqual(
                    exit_code,
                    0,
                    f"{host_name}: substantially-complete is not a completion success for the exit code",
                )
                self.assertEqual(state["queue"][0]["status"], "substantially-complete")

    def test_a_queue_with_a_non_success_terminal_item_exits_nonzero(self):
        """Restored sibling property (E-03): failed-safely exits nonzero on both hosts."""
        for host_name, module in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
            with self.subTest(host=host_name):
                exit_code, state = self._drive_run(module, "failed-safely")
                self.assertNotEqual(exit_code, 0)
                self.assertEqual(state["queue"][0]["status"], "failed-safely")
