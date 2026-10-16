"""Behavioral tests asserting evaluate_clean_base ignores untracked files on both hosts (IPD og11nj).

Re-establishes behavioral coverage proving that untracked files in the target checkout
leave the clean-base guard clean (no refusal, no dirty path) on both hosts (oc_runipd, agy_runipd)
and on both paths (isolated and shared-tree), while a dirty tracked file still classifies not-clean
so the guard is proven non-vacuous.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import clean_git_env, git, init_repo


class CleanBaseUntrackedCoverageTests(unittest.TestCase):
    """Behavioral tests asserting untracked files leave evaluate_clean_base clean on both hosts."""

    def setUp(self) -> None:
        super().setUp()
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.repo = init_repo(Path(tmp_dir.name) / "repo")

        patcher = mock.patch.dict(os.environ, clean_git_env(), clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.tracked_file = self.repo / "tracked.txt"
        self.tracked_file.write_text("initial tracked content\n", encoding="utf-8")
        c_env = clean_git_env()
        git(self.repo, "add", "tracked.txt", env=c_env)
        git(self.repo, "commit", "-q", "-m", "add tracked file", env=c_env)

    def _create_untracked_files(self) -> None:
        (self.repo / "scratch.log").write_text("scratch log\n", encoding="utf-8")
        (self.repo / "notes.md").write_text("notes markdown\n", encoding="utf-8")
        sub_dir = self.repo / "new_subdir"
        sub_dir.mkdir(parents=True, exist_ok=True)
        (sub_dir / "nested.txt").write_text("nested untracked\n", encoding="utf-8")

    def test_untracked_files_leave_clean_base_clean_on_both_hosts(self) -> None:
        """E-01: untracked files leave evaluate_clean_base clean and proceeding on both hosts."""
        self._create_untracked_files()

        hosts = (
            ("oc_runipd", oc_runipd),
            ("agy_runipd", agy_runipd),
        )
        for host_name, driver in hosts:
            for shared_tree in (False, True):
                with self.subTest(host=host_name, shared_tree=shared_tree):
                    result = driver.evaluate_clean_base_for_launch(
                        self.repo, shared_tree=shared_tree
                    )
                    self.assertEqual(result.dirty_paths, ())
                    self.assertIs(result.clean, True)
                    self.assertIs(result.refuses, False)
                    decision = runner_shared.clean_base_launch_decision(result)
                    self.assertEqual(decision.verdict, runner_shared.CLEAN_BASE_PROCEED)

    def test_dirty_tracked_file_control_refuses_or_warns_on_both_hosts(self) -> None:
        """E-02: control test modifying tracked.txt proves guard sees tree and is non-vacuous."""
        self._create_untracked_files()
        self.tracked_file.write_text("modified tracked content\n", encoding="utf-8")

        hosts = (
            ("oc_runipd", oc_runipd),
            ("agy_runipd", agy_runipd),
        )
        for host_name, driver in hosts:
            for shared_tree in (False, True):
                with self.subTest(host=host_name, shared_tree=shared_tree):
                    result = driver.evaluate_clean_base_for_launch(
                        self.repo, shared_tree=shared_tree
                    )
                    self.assertIs(result.clean, False)
                    self.assertEqual(result.dirty_paths, ("tracked.txt",))
                    decision = runner_shared.clean_base_launch_decision(result)
                    if shared_tree:
                        self.assertIs(result.refuses, True)
                        self.assertEqual(
                            decision.verdict, runner_shared.CLEAN_BASE_REFUSE
                        )
                    else:
                        self.assertIs(result.refuses, False)
                        self.assertEqual(
                            decision.verdict, runner_shared.CLEAN_BASE_WARN
                        )

    def test_both_hosts_agree_across_states(self) -> None:
        """E-03: host agreement across clean, untracked only, and untracked plus dirty tracked."""
        clean_sequence_oc: list[bool] = []
        clean_sequence_agy: list[bool] = []

        # State 1: clean base (tracked.txt committed, no untracked files)
        for shared_tree in (False, True):
            with self.subTest(state="clean", shared_tree=shared_tree):
                oc_res = oc_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                agy_res = agy_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                self.assertEqual(
                    (oc_res.clean, oc_res.dirty_paths),
                    (agy_res.clean, agy_res.dirty_paths),
                )
        oc_1 = oc_runipd.evaluate_clean_base_for_launch(self.repo)
        agy_1 = agy_runipd.evaluate_clean_base_for_launch(self.repo)
        clean_sequence_oc.append(oc_1.clean)
        clean_sequence_agy.append(agy_1.clean)

        # State 2: untracked only (untracked files added, tracked.txt unchanged)
        self._create_untracked_files()
        for shared_tree in (False, True):
            with self.subTest(state="untracked_only", shared_tree=shared_tree):
                oc_res = oc_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                agy_res = agy_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                self.assertEqual(
                    (oc_res.clean, oc_res.dirty_paths),
                    (agy_res.clean, agy_res.dirty_paths),
                )
        oc_2 = oc_runipd.evaluate_clean_base_for_launch(self.repo)
        agy_2 = agy_runipd.evaluate_clean_base_for_launch(self.repo)
        clean_sequence_oc.append(oc_2.clean)
        clean_sequence_agy.append(agy_2.clean)

        # State 3: untracked plus dirty tracked (tracked.txt modified)
        self.tracked_file.write_text("modified content\n", encoding="utf-8")
        for shared_tree in (False, True):
            with self.subTest(
                state="untracked_plus_dirty_tracked", shared_tree=shared_tree
            ):
                oc_res = oc_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                agy_res = agy_runipd.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=shared_tree
                )
                self.assertEqual(
                    (oc_res.clean, oc_res.dirty_paths),
                    (agy_res.clean, agy_res.dirty_paths),
                )
        oc_3 = oc_runipd.evaluate_clean_base_for_launch(self.repo)
        agy_3 = agy_runipd.evaluate_clean_base_for_launch(self.repo)
        clean_sequence_oc.append(oc_3.clean)
        clean_sequence_agy.append(agy_3.clean)

        self.assertEqual(clean_sequence_oc, [True, True, False])
        self.assertEqual(clean_sequence_agy, [True, True, False])


if __name__ == "__main__":
    unittest.main()
