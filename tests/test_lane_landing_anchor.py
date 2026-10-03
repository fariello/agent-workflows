#!/usr/bin/env python3
"""Behavioral regression tests for checkout-anchored lane landing predicates.

Validates that `lane_work_has_landed`, `lane_work_landed_by_content`, `inspect_lane`,
and `classify_lane_integration` answer identically regardless of whether they are invoked
with the main repository root or an isolated lane worktree root as `repo` (backlog `cjrjtu`).

Tests outcomes and returned values against real `git worktree` instances, never production
source text (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import unittest

from agent_workflows import ipd_lifecycle, runner_shared, worktree_lease


def _run_git(cwd: pathlib.Path, *args: str) -> tuple[int, str, str]:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return res.returncode, res.stdout, res.stderr


class TestLaneLandingAnchor(unittest.TestCase):
    """Pin cwd-insensitive behavior for lane landing predicates across roots and layouts."""

    def setUp(self) -> None:
        self.tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_lane_anchor_"))
        ipd_lifecycle.clear_checkout_control_root_cache()

    def tearDown(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _init_repo(self, repo_dir: pathlib.Path) -> str:
        repo_dir.mkdir(parents=True, exist_ok=True)
        _run_git(repo_dir, "init", "-b", "main")
        _run_git(repo_dir, "config", "user.name", "Test User")
        _run_git(repo_dir, "config", "user.email", "test@example.com")
        (repo_dir / "base.txt").write_text("base\n", encoding="utf-8")
        _run_git(repo_dir, "add", "base.txt")
        _run_git(repo_dir, "commit", "-m", "initial commit")
        rc, out, _ = _run_git(repo_dir, "rev-parse", "HEAD")
        self.assertEqual(rc, 0)
        return out.strip()

    def _add_production_lane(
        self,
        repo_dir: pathlib.Path,
        lane_dir: pathlib.Path,
        lane_id: str,
        base_sha: str,
        *,
        commit: bool = True,
    ) -> dict[str, str]:
        """Create a lane the way production creates one (`worktree_lease.allocate_worktree`).

        Passing an explicit base sha ensures the creation reflog records `Created from <sha>`
        rather than `Created from HEAD`, isolating target resolution from creation-reflog parsing.
        """
        branch = f"aw/lane/{lane_id}"
        rc, _, err = _run_git(
            repo_dir, "worktree", "add", "-b", branch, str(lane_dir), base_sha
        )
        self.assertEqual(rc, 0, f"worktree add failed: {err}")
        if commit:
            (lane_dir / f"{lane_id}.txt").write_text("lane work\n", encoding="utf-8")
            _run_git(lane_dir, "add", f"{lane_id}.txt")
            _run_git(lane_dir, "commit", "-m", f"work in {lane_id}")
        return {
            "lane_id": lane_id,
            "id6": lane_id,
            "base_commit": base_sha,
            "branch": branch,
            "worktree": str(lane_dir),
        }

    def test_case_a_unmerged_lane_answers_equal_and_false_from_both_roots(self) -> None:
        """Case (a): Unmerged lane with 1 commit reports False from both main and lane roots.

        Specifically asserts the lane-root value is False, preventing false-positive reclamation.
        """
        main_root = self.tmp_dir / "repo_a"
        base_sha = self._init_repo(main_root)
        lane_root = self.tmp_dir / "lane_a"
        lane = self._add_production_lane(
            main_root, lane_root, "case_a", base_sha, commit=True
        )
        branch = lane["branch"]

        # Predicate reachability
        main_landed = runner_shared.lane_work_has_landed(main_root, branch)
        lane_landed = runner_shared.lane_work_has_landed(lane_root, branch)
        self.assertFalse(main_landed, "main root must answer False for unmerged lane")
        self.assertFalse(
            lane_landed, "lane root must answer False for unmerged lane (no false True)"
        )
        self.assertEqual(main_landed, lane_landed)

        # Destroy-authorizing field: inspect_lane
        main_inspect = worktree_lease.inspect_lane(
            main_root, "case_a", base_commit=base_sha
        )
        lane_inspect = worktree_lease.inspect_lane(
            lane_root, "case_a", base_commit=base_sha
        )
        self.assertFalse(main_inspect.merged_into_target)
        self.assertFalse(lane_inspect.merged_into_target)
        self.assertFalse(main_inspect.reclaimable)
        self.assertFalse(lane_inspect.reclaimable)
        self.assertEqual(
            main_inspect.merged_into_target, lane_inspect.merged_into_target
        )
        self.assertEqual(main_inspect.reclaimable, lane_inspect.reclaimable)

        # Sibling predicate: content reading
        main_content = runner_shared.lane_work_landed_by_content(main_root, branch)
        lane_content = runner_shared.lane_work_landed_by_content(lane_root, branch)
        self.assertFalse(main_content)
        self.assertFalse(lane_content)
        self.assertEqual(main_content, lane_content)

    def test_case_b_genuinely_merged_lane_answers_true_from_both_roots(self) -> None:
        """Case (b): Genuinely merged lane reports True from both main and lane roots.

        Pins the true-positive case so the fix cannot break reclamation of landed work.
        """
        main_root = self.tmp_dir / "repo_b"
        base_sha = self._init_repo(main_root)
        lane_root = self.tmp_dir / "lane_b"
        lane = self._add_production_lane(
            main_root, lane_root, "case_b", base_sha, commit=True
        )
        branch = lane["branch"]

        # Merge lane into main with --ff-only, matching integrate_lane_branch
        rc, _, err = _run_git(main_root, "merge", "--ff-only", branch)
        self.assertEqual(rc, 0, f"merge failed: {err}")

        # Predicate reachability
        main_landed = runner_shared.lane_work_has_landed(main_root, branch)
        lane_landed = runner_shared.lane_work_has_landed(lane_root, branch)
        self.assertTrue(main_landed, "main root must answer True for merged lane")
        self.assertTrue(lane_landed, "lane root must answer True for merged lane")
        self.assertEqual(main_landed, lane_landed)

        # Destroy-authorizing field: inspect_lane
        main_inspect = worktree_lease.inspect_lane(
            main_root, "case_b", base_commit=base_sha
        )
        lane_inspect = worktree_lease.inspect_lane(
            lane_root, "case_b", base_commit=base_sha
        )
        self.assertTrue(main_inspect.merged_into_target)
        self.assertTrue(lane_inspect.merged_into_target)
        self.assertTrue(main_inspect.reclaimable)
        self.assertTrue(lane_inspect.reclaimable)

    def test_case_c_second_surface_classify_lane_integration_answers_equal(
        self,
    ) -> None:
        """Case (c): classify_lane_integration returns equal landed and landed_by from both roots."""
        main_root = self.tmp_dir / "repo_c"
        base_sha = self._init_repo(main_root)
        lane_root = self.tmp_dir / "lane_c"
        lane = self._add_production_lane(
            main_root, lane_root, "case_c", base_sha, commit=True
        )

        main_class = runner_shared.classify_lane_integration(main_root, lane)
        lane_class = runner_shared.classify_lane_integration(lane_root, lane)

        self.assertFalse(main_class.get("landed"))
        self.assertFalse(lane_class.get("landed"))
        self.assertIsNone(main_class.get("landed_by"))
        self.assertIsNone(lane_class.get("landed_by"))
        self.assertEqual(main_class.get("integration_target"), "HEAD")
        self.assertEqual(lane_class.get("integration_target"), "HEAD")
        self.assertEqual(main_class.get("lane_state"), lane_class.get("lane_state"))

    def test_case_d_fail_toward_preservation_unresolvable_anchor(self) -> None:
        """Case (d): Unresolvable target returns None, and primitive returns None for non-git paths."""
        main_root = self.tmp_dir / "repo_d"
        base_sha = self._init_repo(main_root)
        lane_root = self.tmp_dir / "lane_d"
        lane = self._add_production_lane(
            main_root, lane_root, "case_d", base_sha, commit=True
        )
        branch = lane["branch"]

        # Nonexistent target driven from lane root and main root must return None (fail toward preservation)
        self.assertIsNone(
            runner_shared.lane_work_has_landed(
                lane_root, branch, target="refs/heads/nosuch"
            ),
            "unresolvable target must return None from lane root, never trivially True",
        )
        self.assertIsNone(
            runner_shared.lane_work_has_landed(
                main_root, branch, target="refs/heads/nosuch"
            ),
            "unresolvable target must return None from main root",
        )
        self.assertIsNone(
            runner_shared.lane_work_landed_by_content(
                lane_root, branch, target="refs/heads/nosuch"
            ),
            "unresolvable target must return None from lane root for content reading",
        )

        # Primitive directly: non-git directory outside repository returns None
        non_git_dir = self.tmp_dir / "not_git"
        non_git_dir.mkdir()
        self.assertIsNone(ipd_lifecycle.checkout_git_common_dir(non_git_dir))

        # Primitive directly: nonexistent directory returns None
        missing_dir = self.tmp_dir / "does_not_exist"
        self.assertIsNone(ipd_lifecycle.checkout_git_common_dir(missing_dir))

    def test_case_e_separate_git_dir_answers_equal_and_non_none(self) -> None:
        """Case (e): A git init --separate-git-dir checkout gives equal, non-None answers."""
        sep_main = self.tmp_dir / "sep_main"
        sep_git = self.tmp_dir / "store.git"
        sep_main.mkdir(parents=True, exist_ok=True)
        _run_git(
            self.tmp_dir, "init", "--separate-git-dir", str(sep_git), str(sep_main)
        )
        _run_git(sep_main, "config", "user.name", "Test User")
        _run_git(sep_main, "config", "user.email", "test@example.com")
        (sep_main / "file.txt").write_text("base\n", encoding="utf-8")
        _run_git(sep_main, "add", "file.txt")
        _run_git(sep_main, "commit", "-m", "init")
        rc, out, _ = _run_git(sep_main, "rev-parse", "HEAD")
        self.assertEqual(rc, 0)
        base_sha = out.strip()

        # Unmerged lane in separate-git-dir checkout
        sep_lane = self.tmp_dir / "sep_lane"
        lane = self._add_production_lane(
            sep_main, sep_lane, "case_e", base_sha, commit=True
        )
        branch = lane["branch"]

        unmerged_main = runner_shared.lane_work_has_landed(sep_main, branch)
        unmerged_lane = runner_shared.lane_work_has_landed(sep_lane, branch)
        self.assertFalse(unmerged_main)
        self.assertFalse(unmerged_lane)
        self.assertEqual(unmerged_main, unmerged_lane)
        self.assertFalse(
            worktree_lease.inspect_lane(
                sep_main, "case_e", base_commit=base_sha
            ).reclaimable
        )
        self.assertFalse(
            worktree_lease.inspect_lane(
                sep_lane, "case_e", base_commit=base_sha
            ).reclaimable
        )

        # Merged lane in separate-git-dir checkout
        rc, _, err = _run_git(sep_main, "merge", "--ff-only", branch)
        self.assertEqual(rc, 0, f"merge failed: {err}")

        merged_main = runner_shared.lane_work_has_landed(sep_main, branch)
        merged_lane = runner_shared.lane_work_has_landed(sep_lane, branch)
        self.assertTrue(merged_main)
        self.assertTrue(merged_lane)
        self.assertEqual(merged_main, merged_lane)
        self.assertTrue(
            worktree_lease.inspect_lane(
                sep_main, "case_e", base_commit=base_sha
            ).reclaimable
        )
        self.assertTrue(
            worktree_lease.inspect_lane(
                sep_lane, "case_e", base_commit=base_sha
            ).reclaimable
        )


if __name__ == "__main__":
    unittest.main()
