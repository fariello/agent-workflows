"""Tests verifying <run_dir>/outcomes/ guarantee and purity invariants (IPD 2kyw59, backlog 3kr193).

Pins all three classes of outcomes-parent handling by real outcome against bare directories:
(a) Non-isolated prepare_lane_submission_dir guarantees the driver-side outcome parent.
(b) Isolated prepare_lane_submission_dir creates lane-side parent without creating driver-side outcomes/.
(c) Pure readers recorded_outcome_path and read_recorded_outcome create nothing and tolerate absence.
(d) build_verifier_prompt guarantees outcomes/ parent for both in-run (audit=False) and audit (audit=True).
(e) collect_lane_submissions into a bare run directory creates destination parent and collects outcome.
(f) Isolated prepare_lane_submission_dir creates nothing relative to current process cwd.
"""

from __future__ import annotations

import contextlib
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import lane_containment, runner_shared
from tests import support


class RunDirOutcomesParentGuaranteedTests(unittest.TestCase):
    """Behavioral outcome-based tests for <run_dir>/outcomes/ guarantee across all three classes."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_a_non_isolated_prepare_lane_submission_dir_creates_driver_outcome_parent(
        self,
    ) -> None:
        """(a) NON-ISOLATED project_worker_paths + prepare_lane_submission_dir leaves prompt_outcome parent existing."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir = root / "run"
            run_dir.mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            item = {
                "position": 1,
                "id6": "abc123",
                "action": "exec",
                "attempt": 1,
            }
            self.assertFalse((run_dir / "outcomes").exists())

            paths = lane_containment.project_worker_paths(
                item=item,
                run_id="run-test",
                run_dir=run_dir,
                plan_path=plan_path,
                lane_root=None,
            )
            lane_containment.prepare_lane_submission_dir(paths)

            prompt_outcome_parent = Path(paths.prompt_outcome).parent
            self.assertTrue(prompt_outcome_parent.is_dir())
            self.assertTrue((run_dir / "outcomes").is_dir())

    def test_b_isolated_prepare_lane_submission_dir_preserves_driver_outcomes_absence(
        self,
    ) -> None:
        """(b) ISOLATED prepare_lane_submission_dir creates LANE-side parent and does NOT create driver-side run_dir/outcomes."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir = root / "run"
            run_dir.mkdir(parents=True)
            lane_root = root / "lane"
            lane_root.mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            item = {
                "position": 1,
                "id6": "abc123",
                "action": "exec",
                "attempt": 1,
            }
            self.assertFalse((run_dir / "outcomes").exists())

            paths = lane_containment.project_worker_paths(
                item=item,
                run_id="run-test",
                run_dir=run_dir,
                plan_path=plan_path,
                lane_root=lane_root,
            )
            self.assertIsNotNone(paths.lane_outcome)
            self.assertFalse(paths.lane_outcome.parent.exists())

            lane_containment.prepare_lane_submission_dir(paths)

            self.assertTrue(paths.lane_outcome.parent.is_dir())
            self.assertFalse((run_dir / "outcomes").exists())

    def test_c_readers_remain_pure_and_tolerate_absence(self) -> None:
        """(c) recorded_outcome_path and read_recorded_outcome remain PURE, asserting not exists and returns None."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir = root / "run"
            run_dir.mkdir(parents=True)
            item = {
                "position": 1,
                "id6": "abc123",
                "action": "exec",
                "attempt": 1,
            }
            self.assertFalse((run_dir / "outcomes").exists())

            outcome_path = runner_shared.recorded_outcome_path(run_dir, item)
            self.assertEqual(outcome_path, run_dir / "outcomes" / "01-abc123.json")
            self.assertFalse((run_dir / "outcomes").exists())

            recorded_outcome = runner_shared.read_recorded_outcome(run_dir, item)
            self.assertIsNone(recorded_outcome)
            self.assertFalse((run_dir / "outcomes").exists())

    def test_d_build_verifier_prompt_guarantees_outcomes_parent(self) -> None:
        """(d) build_verifier_prompt creates outcomes/ for both audit=False and audit=True."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir_verify = root / "run_verify"
            run_dir_verify.mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")
            item = {
                "position": 1,
                "id6": "abc123",
                "setid": "testset",
                "action": "exec",
            }
            state = {"run_id": "run-test"}

            self.assertFalse((run_dir_verify / "outcomes").exists())
            prompt_verify = runner_shared.build_verifier_prompt(
                item=item,
                state=state,
                run_dir=run_dir_verify,
                plan_path=plan_path,
                labels=runner_shared.OC_HOST_LABELS,
                audit=False,
            )
            self.assertTrue((run_dir_verify / "outcomes").is_dir())
            self.assertIn("01-abc123-verification.json", prompt_verify)

            run_dir_audit = root / "run_audit"
            run_dir_audit.mkdir(parents=True)
            self.assertFalse((run_dir_audit / "outcomes").exists())
            prompt_audit = runner_shared.build_verifier_prompt(
                item=item,
                state=state,
                run_dir=run_dir_audit,
                plan_path=plan_path,
                labels=runner_shared.OC_HOST_LABELS,
                audit=True,
            )
            self.assertTrue((run_dir_audit / "outcomes").is_dir())
            self.assertIn("01-abc123-verification.json", prompt_audit)

    def test_e_collect_lane_submissions_into_bare_run_dir_lands_outcome(self) -> None:
        """(e) collect_lane_submissions into a BARE run directory still lands the outcome file (Class B guarantee)."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir = root / "run"
            run_dir.mkdir(parents=True)
            lane_root = root / "lane"
            lane_root.mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")
            item = {
                "position": 1,
                "id6": "abc123",
                "setid": "testset",
                "action": "exec",
                "attempt": 1,
            }
            self.assertFalse((run_dir / "outcomes").exists())

            paths = lane_containment.project_worker_paths(
                item=item,
                run_id="run-test",
                run_dir=run_dir,
                plan_path=plan_path,
                lane_root=lane_root,
            )
            lane_containment.prepare_lane_submission_dir(paths)
            self.assertIsNotNone(paths.lane_outcome)
            paths.lane_outcome.write_text(
                json.dumps({"disposition": "executed"}), encoding="utf-8"
            )

            result = lane_containment.collect_lane_submissions(
                run_dir=run_dir,
                item=item,
                run_id="run-test",
                lane_root=lane_root,
                plan_path=plan_path,
                attempt=1,
            )
            self.assertIsNotNone(result)
            self.assertTrue((run_dir / "outcomes").is_dir())
            collected_outcome_file = run_dir / "outcomes" / "01-abc123.json"
            self.assertTrue(collected_outcome_file.is_file())
            data = json.loads(collected_outcome_file.read_text(encoding="utf-8"))
            self.assertEqual(data.get("disposition"), "executed")

    def test_f_isolated_prepare_lane_submission_dir_leaves_cwd_empty(self) -> None:
        """(f) ISOLATED prepare_lane_submission_dir with PROCESS CWD set to a throwaway empty directory creates NOTHING relative to cwd."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            run_dir = root / "run"
            run_dir.mkdir(parents=True)
            lane_root = root / "lane"
            lane_root.mkdir(parents=True)
            plan_path = root / "plan.ipd.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")
            item = {
                "position": 1,
                "id6": "abc123",
                "action": "exec",
                "attempt": 1,
            }
            empty_cwd_dir = root / "empty_cwd"
            empty_cwd_dir.mkdir(parents=True)

            paths = lane_containment.project_worker_paths(
                item=item,
                run_id="run-test",
                run_dir=run_dir,
                plan_path=plan_path,
                lane_root=lane_root,
            )
            with contextlib.chdir(empty_cwd_dir):
                self.assertEqual(list(Path.cwd().iterdir()), [])
                lane_containment.prepare_lane_submission_dir(paths)
                self.assertEqual(list(Path.cwd().iterdir()), [])
