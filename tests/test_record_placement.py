"""Unit tests for the shared record placement library (agent_workflows/record_placement.py; IPD r9uvwc)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as AC
from agent_workflows import backlog as BL
from agent_workflows import plans as PL
from agent_workflows import record_placement as RP


class RecordPlacementDerivationTests(unittest.TestCase):
    """Verify that record_placement derives its vocabulary from existing authorities without hardcoding."""

    def test_backlog_statuses_derive_from_status_dirs(self) -> None:
        for status in BL.STATUS_DIRS:
            self.assertEqual(RP.target_subdir("backlog", status), status)

    def test_spec_statuses_derive_from_attention_contract(self) -> None:
        for status in AC.SPEC_STATUSES:
            self.assertEqual(RP.target_subdir("specs", status), status)

    def test_plans_many_to_one_mapping_matches_authorities(self) -> None:
        # All 5 pending-mapped statuses must resolve to 'pending'
        for status in PL.PRE_TERMINAL:
            self.assertEqual(
                RP.target_subdir("plans", status),
                "pending",
                f"plans status {status!r} must map to 'pending'",
            )
            self.assertEqual(
                RP.target_subdir("prompts", status),
                "pending",
                f"prompts status {status!r} must map to 'pending'",
            )

        # Terminal and standing statuses map to their own name
        for status in PL.TERMINAL:
            self.assertEqual(RP.target_subdir("plans", status), status)
            self.assertEqual(RP.target_subdir("prompts", status), status)
        for status in PL.STANDING:
            self.assertEqual(RP.target_subdir("plans", status), status)
            self.assertEqual(RP.target_subdir("prompts", status), status)

    def test_non_lifecycle_types_have_no_target_subdir(self) -> None:
        self.assertFalse(RP.has_lifecycle_subdirs("research"))
        self.assertIsNone(RP.target_subdir("research", "active"))
        self.assertFalse(RP.has_lifecycle_subdirs("walkthroughs"))
        self.assertIsNone(RP.target_subdir("walkthroughs", "draft"))


class RecordPlacementPathResolutionTests(unittest.TestCase):
    """Test creation and transition path resolution across all lifecycle-bearing record types."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        # Create .aw marker and standard directories
        (self.repo_root / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "plans" / "executed" / "202601").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "specs" / "draft").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "specs" / "to-review").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "backlog" / "graduated").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_creation_placement_for_all_types(self) -> None:
        # Plans creation
        p_path = RP.resolve_creation_path(
            "plans", "draft", "20260920-set-01-pl1234-test.ipd.md", self.repo_root
        )
        self.assertEqual(
            p_path,
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260920-set-01-pl1234-test.ipd.md",
        )

        # Specs creation
        s_path = RP.resolve_creation_path(
            "specs", "draft", "20260920-sp1234-01-sp1234-test.spec.md", self.repo_root
        )
        self.assertEqual(
            s_path,
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260920-sp1234-01-sp1234-test.spec.md",
        )

        # Backlog creation
        b_path = RP.resolve_creation_path(
            "backlog",
            "open",
            "20260920-bk1234-01-bk1234-test.backlog.md",
            self.repo_root,
        )
        self.assertEqual(
            b_path,
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260920-bk1234-01-bk1234-test.backlog.md",
        )

    def test_source_dir_equals_target_dir_is_identity(self) -> None:
        # Plans: pending -> pending (e.g. draft -> to-review)
        plan_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260920-set-01-pl1234-test.ipd.md"
        )
        self.assertEqual(
            RP.resolve_transition_path("plans", plan_cur, "to-review", self.repo_root),
            plan_cur,
        )

        # Backlog: open -> open
        bkl_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260920-bk1234-01-bk1234-test.backlog.md"
        )
        self.assertEqual(
            RP.resolve_transition_path("backlog", bkl_cur, "open", self.repo_root),
            bkl_cur,
        )

        # Specs: draft -> draft
        spec_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260920-sp1234-01-sp1234-test.spec.md"
        )
        self.assertEqual(
            RP.resolve_transition_path("specs", spec_cur, "draft", self.repo_root),
            spec_cur,
        )

    def test_transition_moves_to_correct_subdirectory(self) -> None:
        # Backlog: open -> graduated
        bkl_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260920-bk1234-01-bk1234-test.backlog.md"
        )
        bkl_dest = RP.resolve_transition_path(
            "backlog", bkl_cur, "graduated", self.repo_root
        )
        self.assertEqual(
            bkl_dest,
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260920-bk1234-01-bk1234-test.backlog.md",
        )

        # Specs: draft -> to-review
        spec_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "draft"
            / "20260920-sp1234-01-sp1234-test.spec.md"
        )
        spec_dest = RP.resolve_transition_path(
            "specs", spec_cur, "to-review", self.repo_root
        )
        self.assertEqual(
            spec_dest,
            self.repo_root
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20260920-sp1234-01-sp1234-test.spec.md",
        )

        # Plans: pending -> executed
        plan_cur = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260920-set-01-pl1234-test.ipd.md"
        )
        plan_dest = RP.resolve_transition_path(
            "plans", plan_cur, "executed", self.repo_root
        )
        self.assertEqual(
            plan_dest,
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260920-set-01-pl1234-test.ipd.md",
        )

    def test_sharded_plan_transition_preserves_shard_for_terminal_statuses(
        self,
    ) -> None:
        """PIN BEHAVIOR: Sharded plans under <disp>/YYYYMM/ preserve the shard across terminal transitions."""
        plan_sharded = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "202601"
            / "20260105-set-00-pl1234-test.ipd.md"
        )
        # executed/202601/... -> superseded/202601/...
        dest = RP.resolve_transition_path(
            "plans", plan_sharded, "superseded", self.repo_root
        )
        self.assertEqual(
            dest,
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "superseded"
            / "202601"
            / "20260105-set-00-pl1234-test.ipd.md",
        )

        # executed/202601/... -> pending/... (pending is flat, so shard is stripped)
        dest_pending = RP.resolve_transition_path(
            "plans", plan_sharded, "draft", self.repo_root
        )
        self.assertEqual(
            dest_pending,
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260105-set-00-pl1234-test.ipd.md",
        )


if __name__ == "__main__":
    unittest.main()
