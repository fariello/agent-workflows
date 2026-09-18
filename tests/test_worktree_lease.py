"""Tests for worktree_lease memoization and inspection fast-paths (Set attperf, Order 01).

Stdlib unittest, verifies that memoize_worktrees executes git worktree list and branch queries
at most once per pass, and restores cache state cleanly upon exit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import worktree_lease


class WorktreeLeaseMemoizationTests(unittest.TestCase):
    def test_registered_worktrees_memoized(self):
        """Test that within memoize_worktrees, git worktree list is called at most once."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # Mock _git to record calls
            git_calls: list[list[str]] = []
            orig_git = worktree_lease._git

            def fake_git(r, args, **kwargs):
                git_calls.append(list(args))
                if args == ["worktree", "list", "--porcelain"]:
                    return (
                        0,
                        "worktree "
                        + str(repo)
                        + "\nHEAD abc1234\nbranch refs/heads/main\n\n",
                        "",
                    )
                if args[:2] == ["for-each-ref", "--format=%(refname) %(objectname)"]:
                    return 0, "refs/heads/main abc1234\n", ""
                if args == ["rev-parse", "HEAD"]:
                    return 0, "abc1234\n", ""
                return orig_git(r, args, **kwargs)

            with mock.patch.object(worktree_lease, "_git", side_effect=fake_git):
                # Before context manager, cache is None
                self.assertIsNone(worktree_lease._WORKTREE_CACHE)
                self.assertIsNone(worktree_lease._BRANCH_CACHE)

                with worktree_lease.memoize_worktrees(repo):
                    # During context manager, cache is populated
                    self.assertIsNotNone(worktree_lease._WORKTREE_CACHE)
                    self.assertIsNotNone(worktree_lease._BRANCH_CACHE)

                    wt_calls_before = sum(
                        1 for c in git_calls if c == ["worktree", "list", "--porcelain"]
                    )
                    self.assertEqual(wt_calls_before, 1)

                    # Call _registered_worktrees multiple times
                    reg1 = worktree_lease._registered_worktrees(repo)
                    reg2 = worktree_lease._registered_worktrees(repo)
                    self.assertIn("refs/heads/main", reg1)
                    self.assertEqual(reg1, reg2)

                    # No additional git worktree list calls occurred
                    wt_calls_after = sum(
                        1 for c in git_calls if c == ["worktree", "list", "--porcelain"]
                    )
                    self.assertEqual(wt_calls_after, 1)

                    # Calling inspect_lane for an absent lane uses cache fast-path without subprocesses
                    calls_before_inspect = len(git_calls)
                    state = worktree_lease.inspect_lane(repo, "nonexistent999")
                    self.assertEqual(state.state, worktree_lease.LANE_ABSENT)
                    self.assertFalse(state.branch_exists)
                    self.assertFalse(state.worktree_registered)
                    self.assertEqual(len(git_calls), calls_before_inspect)

                # After context manager exit, cache is cleanly cleared
                self.assertIsNone(worktree_lease._WORKTREE_CACHE)
                self.assertIsNone(worktree_lease._BRANCH_CACHE)
                self.assertIsNone(worktree_lease._HEAD_SHA_CACHE)


if __name__ == "__main__":
    unittest.main()
