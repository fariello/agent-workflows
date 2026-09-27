"""Outcome tests for check_engine status reads and retirement bounded to the metadata region.

Covers IPD ahq0mq (fencegate-02):
- (a) REGRESSION: Plan text with no front-matter status and a fenced status quote in body
      evaluates to None (not the quoted status) and is_retired is False.
- (b) CONTROL: Front matter - Status: approved with a fenced quote evaluates to approved.
- (c) CONTROL: Headingless document whose first bullet is - Status: approved and later quotes
      executed evaluates to approved. Guard against last-match / findall rewrites.
- (d) CONTROL: End-to-end untooled-change detector returns no drift when body adds a fenced quote.
- (e) CONTROL: Real - Status: executed in metadata on a non-retired path still evaluates to True.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine
from tests import support


class CheckEngineStatusMetaTests(unittest.TestCase):
    """Outcome cases for _status_meta, is_retired, and check_status_untooled."""

    def test_status_meta_no_front_matter_fenced_quote_is_none(self):
        """Case (a) [REGRESSION TEST]: No front-matter status + ## Goal + fenced quote.

        DISCRIMINATES: Fails pre-change (returns 'executed' and is_retired=True),
        passes after (returns None and is_retired=False).
        """
        text_a = (
            "# Plan: Unset Plan\n\n"
            "- Id: ut0001\n"
            "- Kind: child\n\n"
            "## Goal\n\n"
            "Here is a quoted status:\n"
            "```\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertIsNone(check_engine._status_meta(text_a))

        with tempfile.TemporaryDirectory(prefix="aw_test_active_") as tmp_dir:
            file_path = Path(tmp_dir) / "active-plan.ipd.md"
            file_path.write_text(text_a, encoding="utf-8")
            self.assertFalse(check_engine.is_retired(file_path))

    def test_status_meta_front_matter_approved_with_fenced_quote(self):
        """Case (b) [CONTROL]: Front matter - Status: approved + same fenced quote.

        CONTROL: Expected to pass before AND after.
        """
        text_b = (
            "# Plan: Approved Plan\n\n"
            "- Id: ut0002\n"
            "- Status: approved\n"
            "- Kind: child\n\n"
            "## Goal\n\n"
            "Here is a quoted status:\n"
            "```\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertEqual(check_engine._status_meta(text_b), "approved")

    def test_status_meta_headingless_first_bullet_approved(self):
        """Case (c) [CONTROL]: Headingless plan, first bullet approved, later quotes executed.

        CONTROL: Expected to pass before AND after.
        Kept because selectors.metadata_region returns the whole text for a record
        with no '##' heading, so only search's first-match semantics keep the answer
        right; this guards against a future last-match or findall rewrite.
        """
        text_c = (
            "- Status: approved\n"
            "- Id: ut0003\n\n"
            "Some body text quoting:\n"
            "```\n"
            "- Status: executed\n"
            "```\n"
        )
        self.assertEqual(check_engine._status_meta(text_c), "approved")

    def test_check_status_untooled_fenced_quote_in_body_no_drift(self):
        """Case (d) [CONTROL]: Git repo end-to-end staged edit adding fenced quote produces no drift.

        CONTROL: Expected to pass before AND after.
        Pre-fix drift is already [] because the plan carries a real front-matter
        - Status: approved which search finds first on both HEAD and staged blobs.
        Guards end-to-end against matching the last occurrence.
        """
        with tempfile.TemporaryDirectory(prefix="aw_test_git_repo_") as tmp_dir:
            repo_root = Path(tmp_dir)
            support.init_repo(repo_root)

            plan_dir = repo_root / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plan_dir / "20260927-fencegate-01-tst001-plan.ipd.md"

            initial_content = (
                "# IPD: Test Plan tst001\n\n"
                "- Date: 2026-09-27\n"
                "- Kind: child\n"
                "- Status: approved\n"
                "- Work-Kind: chore\n"
                "- Priority: medium\n"
                "- Set: fencegate\n"
                "- Order: 1\n"
                "- Id: tst001\n\n"
                "## Workflow history\n\n"
                "- 2026-09-27 approved (author): initial approved plan.\n\n"
                "## Goal\n\n"
                "Test goal.\n"
            )
            plan_file.write_text(initial_content, encoding="utf-8")
            support.git(repo_root, "add", str(plan_file))
            support.git(repo_root, "commit", "-m", "add approved plan")

            # Stage an edit that ONLY adds a fenced quote in the body
            edited_content = initial_content + (
                "\nHere is a fenced quote:\n" "```\n" "- Status: executed\n" "```\n"
            )
            plan_file.write_text(edited_content, encoding="utf-8")
            support.git(repo_root, "add", str(plan_file))

            drift = check_engine.check_status_untooled(repo_root)
            self.assertEqual(drift, [])

    def test_is_retired_real_status_executed_signal(self):
        """Case (e) [CONTROL]: is_retired on non-retired-path file with - Status: executed.

        CONTROL: Expected to pass before AND after. Confirms real retirement signal still works.
        """
        text_e = (
            "# Plan: Executed Plan\n\n"
            "- Id: ut0005\n"
            "- Status: executed\n"
            "- Kind: child\n\n"
            "## Goal\n\n"
            "All work completed.\n"
        )
        with tempfile.TemporaryDirectory(prefix="aw_test_active_") as tmp_dir:
            file_path = Path(tmp_dir) / "plan.ipd.md"
            file_path.write_text(text_e, encoding="utf-8")
            self.assertTrue(check_engine.is_retired(file_path))


if __name__ == "__main__":
    unittest.main()
