"""Behavioral tests asserting evaluate_clean_base tracked scope is identical on both paths (IPD 9wqjac).

Re-establishes behavioral coverage proving that the clean/dirty classification
(`clean`, `dirty_paths`) produced by lane_containment.evaluate_clean_base is identical
whether shared_tree is True or False, while only the consequence (`refuses`) differs
for dirty checkouts.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import lane_containment, runner_shared
from tests.support import clean_git_env, git, init_repo


class CleanBaseTrackedScopeTests(unittest.TestCase):
    """Behavioral tests asserting evaluate_clean_base tracked scope is identical on both paths."""

    def test_clean_base_tracked_scope_identical_on_both_paths(self):
        """E-01: pure-rule coverage across clean and dirty porcelain inputs."""
        inputs = (
            "",
            " M a.py\n",
            "M  b.py\nR  c -> d\n",
            "MM x.py\n D gone.py\n",
        )
        for porcelain in inputs:
            with self.subTest(porcelain=porcelain):
                isolated = lane_containment.evaluate_clean_base(porcelain)
                shared = lane_containment.evaluate_clean_base(
                    porcelain, shared_tree=True
                )
                self.assertEqual(isolated.clean, shared.clean)
                self.assertEqual(isolated.dirty_paths, shared.dirty_paths)
                if porcelain == "":
                    self.assertTrue(isolated.clean)
                    self.assertTrue(shared.clean)
                    self.assertEqual(isolated.dirty_paths, ())
                    self.assertEqual(shared.dirty_paths, ())
                    self.assertFalse(isolated.refuses)
                    self.assertFalse(shared.refuses)
                else:
                    self.assertFalse(isolated.clean)
                    self.assertFalse(shared.clean)
                    self.assertFalse(isolated.refuses)
                    self.assertTrue(shared.refuses)

    def test_evaluate_clean_base_for_launch_tracked_scope(self):
        """E-02: real-repository coverage through runner_shared.evaluate_clean_base_for_launch."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = init_repo(Path(tmp_dir) / "repo")
            tracked_file = repo / "tracked.txt"
            with open(tracked_file, "w", encoding="utf-8") as f:
                f.write("committed content\n")
            c_env = clean_git_env()
            git(repo, "add", "tracked.txt", env=c_env)
            git(repo, "commit", "-q", "-m", "add tracked file", env=c_env)

            with mock.patch.dict(os.environ, clean_git_env(), clear=True):
                # Shape 1: clean
                iso_clean = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=False
                )
                shared_clean = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=True
                )
                self.assertEqual(iso_clean.clean, shared_clean.clean)
                self.assertEqual(iso_clean.dirty_paths, shared_clean.dirty_paths)
                self.assertTrue(iso_clean.clean)
                self.assertTrue(shared_clean.clean)
                self.assertEqual(iso_clean.dirty_paths, ())
                self.assertEqual(shared_clean.dirty_paths, ())
                self.assertFalse(iso_clean.refuses)
                self.assertFalse(shared_clean.refuses)

                # Shape 2: tracked file modified
                with open(tracked_file, "w", encoding="utf-8") as f:
                    f.write("modified content\n")
                iso_mod = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=False
                )
                shared_mod = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=True
                )
                self.assertEqual(iso_mod.clean, shared_mod.clean)
                self.assertEqual(iso_mod.dirty_paths, shared_mod.dirty_paths)
                self.assertFalse(iso_mod.clean)
                self.assertFalse(shared_mod.clean)
                self.assertIn("tracked.txt", iso_mod.dirty_paths)
                self.assertIn("tracked.txt", shared_mod.dirty_paths)
                self.assertFalse(iso_mod.refuses)
                self.assertTrue(shared_mod.refuses)

                # Shape 3: untracked file only
                with open(tracked_file, "w", encoding="utf-8") as f:
                    f.write("committed content\n")
                git(repo, "checkout", "--", "tracked.txt", env=clean_git_env())
                untracked_file = repo / "untracked.txt"
                with open(untracked_file, "w", encoding="utf-8") as f:
                    f.write("untracked file\n")
                iso_untracked = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=False
                )
                shared_untracked = runner_shared.evaluate_clean_base_for_launch(
                    repo, shared_tree=True
                )
                self.assertEqual(iso_untracked.clean, shared_untracked.clean)
                self.assertEqual(
                    iso_untracked.dirty_paths, shared_untracked.dirty_paths
                )
                self.assertTrue(iso_untracked.clean)
                self.assertTrue(shared_untracked.clean)
                self.assertEqual(iso_untracked.dirty_paths, ())
                self.assertEqual(shared_untracked.dirty_paths, ())
                self.assertFalse(iso_untracked.refuses)
                self.assertFalse(shared_untracked.refuses)


if __name__ == "__main__":
    unittest.main()
