"""Tests for classify_git_state (the pre-install git diagnostics classifier). Stdlib unittest.

Regression guard for the false-alarm bug (2146-01): a repo dirty ONLY from untracked files and
in sync must NOT trigger the diagnostics prompt, and a no-op pull must NOT be offered/defaulted when
the branch is not behind. The classifier is pure (no subprocess), so these are deterministic.
"""

from __future__ import annotations

import unittest

from agent_workflows.engine import classify_git_state

BR = "main"
UP = "origin/main"


class ClassifyGitStateTests(unittest.TestCase):
    def test_untracked_only_in_sync_does_not_prompt(self):
        # The reported bug: 4 untracked files, in sync -> was showing a scary menu + no-op pull.
        s = classify_git_state("?? a.md\n?? b.md\n?? c.md\n?? d.md", 0, True, BR, UP)
        self.assertEqual(s.untracked, 4)
        self.assertEqual(s.tracked_dirty, 0)
        self.assertFalse(s.needs_prompt)
        self.assertFalse(s.offer_pull)

    def test_fully_clean_in_sync_does_not_prompt(self):
        s = classify_git_state("", 0, True, BR, UP)
        self.assertFalse(s.needs_prompt)
        self.assertFalse(s.offer_pull)

    def test_tracked_dirty_in_sync_prompts_without_pull(self):
        # Local tracked edits + in sync: prompt (real risk), but pull is a no-op -> not offered.
        s = classify_git_state(" M x.py\nA  new.py\n?? scratch.txt", 0, True, BR, UP)
        self.assertEqual(s.tracked_dirty, 2)
        self.assertEqual(s.untracked, 1)
        self.assertTrue(s.needs_prompt)
        self.assertFalse(s.offer_pull)

    def test_behind_offers_pull(self):
        # Behind the remote: a pull genuinely helps, so it is offered.
        s = classify_git_state("", 3, True, BR, UP)
        self.assertEqual(s.behind, 3)
        self.assertTrue(s.needs_prompt)
        self.assertTrue(s.offer_pull)

    def test_behind_and_tracked_dirty_offers_pull(self):
        s = classify_git_state(" M x.py", 1, True, BR, UP)
        self.assertTrue(s.needs_prompt)
        self.assertTrue(s.offer_pull)

    def test_no_tracking_alone_is_not_a_blocking_prompt(self):
        # A missing upstream, with a clean tree, is a soft note - not a blocking menu.
        s = classify_git_state("", 0, False, BR, "")
        self.assertFalse(s.needs_prompt)
        self.assertFalse(s.offer_pull)
        self.assertTrue(any("no tracking" in w for w in s.warnings))

    def test_warnings_report_tracked_count_not_untracked(self):
        s = classify_git_state(" M x.py\n?? a\n?? b\n?? c", 0, True, BR, UP)
        # The actionable warning counts tracked changes (1), not the 3 untracked files.
        self.assertTrue(any("1 uncommitted tracked change" in w for w in s.warnings))
        self.assertFalse(any("untracked" in w.lower() for w in s.warnings))


if __name__ == "__main__":
    unittest.main()
