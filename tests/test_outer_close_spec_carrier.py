"""Behavioral tests for runner_shared.evaluate_backlog_close judging spec carriers.

IPD 5eygjt / Set 10w6ww: Make the outer backlog-close predicate judge spec carriers
in the mixed case instead of returning before it sees them.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows.runner_shared import (
    CARRIER_KIND_IPD,
    CARRIER_KIND_OTHER,
    evaluate_backlog_close,
)
from tests.test_backlog_handoff_close import (
    _make_scratch_repo,
    _write_backlog_item,
    _write_plan,
    _write_spec,
)


class TestOuterCloseSpecCarrier(unittest.TestCase):
    """Pin evaluate_backlog_close behavior on mixed and single-kind carriers."""

    def test_case_1_mixed_executed_plan_plus_approved_spec_refuses(self) -> None:
        """Case 1: MIXED, executed plan plus approved spec -> close is False naming spec."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            plan_path = _write_plan(
                repo,
                "pln001",
                bucket="executed",
                status="executed",
                from_backlog="itm001",
                blocks_release="next",
            )
            spec_path = _write_spec(
                repo,
                "spc001",
                subdir="approved",
                status="approved",
                from_backlog="itm001",
                blocks_release="next",
            )

            plan_rel = str(plan_path.resolve().relative_to(repo.resolve()))
            spec_rel = str(spec_path.resolve().relative_to(repo.resolve()))

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[plan_rel])
            self.assertFalse(verdict.close)
            self.assertIn(spec_rel, verdict.reason)

    def test_case_2_mixed_executed_plan_plus_implemented_spec_allows(self) -> None:
        """Case 2: MIXED, executed plan plus implemented spec -> close is True (rule='ipd')."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            plan_path = _write_plan(
                repo,
                "pln001",
                bucket="executed",
                status="executed",
                from_backlog="itm001",
                blocks_release="next",
            )
            _write_spec(
                repo,
                "spc001",
                subdir="implemented",
                status="implemented",
                from_backlog="itm001",
                blocks_release="next",
            )

            plan_rel = str(plan_path.resolve().relative_to(repo.resolve()))

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[plan_rel])
            self.assertTrue(verdict.close)
            self.assertEqual(verdict.rule, CARRIER_KIND_IPD)

    def test_case_3_ipd_only_executed_plan_allows(self) -> None:
        """Case 3: IPD-ONLY regression, one executed plan and no spec -> close is True."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            plan_path = _write_plan(
                repo,
                "pln001",
                bucket="executed",
                status="executed",
                from_backlog="itm001",
                blocks_release="next",
            )

            plan_rel = str(plan_path.resolve().relative_to(repo.resolve()))

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[plan_rel])
            self.assertTrue(verdict.close)
            self.assertEqual(verdict.rule, CARRIER_KIND_IPD)

    def test_case_4_spec_only_draft_spec_allows(self) -> None:
        """Case 4: SPEC-ONLY regression, a single draft spec and no plan -> close is True with rule='other'."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            (repo / ".aw" / "records" / "specs" / "draft").mkdir(
                parents=True, exist_ok=True
            )
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            spec_path = _write_spec(
                repo,
                "spc001",
                subdir="draft",
                status="draft",
                from_backlog="itm001",
                blocks_release="next",
            )

            spec_rel = str(spec_path.resolve().relative_to(repo.resolve()))

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[spec_rel])
            self.assertTrue(verdict.close)
            self.assertEqual(verdict.rule, CARRIER_KIND_OTHER)

    def test_case_5_mixed_unexecuted_plan_and_unimplemented_spec_refuses_both(
        self,
    ) -> None:
        """Case 5: MIXED, unexecuted plan and unimplemented spec -> close is False naming BOTH."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            plan_path = _write_plan(
                repo,
                "pln001",
                bucket="pending",
                status="approved",
                from_backlog="itm001",
                blocks_release="next",
            )
            spec_path = _write_spec(
                repo,
                "spc001",
                subdir="approved",
                status="approved",
                from_backlog="itm001",
                blocks_release="next",
            )

            plan_rel = str(plan_path.resolve().relative_to(repo.resolve()))
            spec_rel = str(spec_path.resolve().relative_to(repo.resolve()))

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[plan_rel])
            self.assertFalse(verdict.close)
            self.assertIn(plan_rel, verdict.reason)
            self.assertIn(spec_rel, verdict.reason)

    def test_case_6_mixed_all_terminal_empty_earned_paths_refuses(self) -> None:
        """Case 6: Earned-close precedence: mixed all-terminal fixture with empty earned_paths -> close is False."""
        with TemporaryDirectory() as tmpdir:
            repo = _make_scratch_repo(Path(tmpdir))
            _write_backlog_item(repo, "itm001", status="open", blocks_release="next")
            _write_plan(
                repo,
                "pln001",
                bucket="executed",
                status="executed",
                from_backlog="itm001",
                blocks_release="next",
            )
            _write_spec(
                repo,
                "spc001",
                subdir="implemented",
                status="implemented",
                from_backlog="itm001",
                blocks_release="next",
            )

            verdict = evaluate_backlog_close(repo, "itm001", earned_paths=[])
            self.assertFalse(verdict.close)
            self.assertIn("this run executed none of its carriers", verdict.reason)


if __name__ == "__main__":
    unittest.main()
