#!/usr/bin/env python3
"""Behavioral regression tests pinning lane owner record anchoring (IPD tjags7, backlog voxbcx).

Pins:
  (a) Anchoring equivalence: `read_lane_owner` and `_owner_record_path` return the same result from
      the main checkout and from inside a linked lane worktree.
  (b) Gate no longer inverts: `lane_is_safe_to_adopt` and `lane_owned_by_other_live_process` return
      consistent fail-safe results from both roots when an active third-party process owns the lane.
  (c) Non-git no-op: for a non-git directory, the composed owners path is byte-identical to direct
      composition, ensuring compatibility for existing temp-directory tests.
  (d) Absent versus unreachable distinction: genuinely absent records remain adoptable, while an
      unreachable owners store (replaced by a file or chmod 0) refuses adoption with an unreadable
      store verdict and counts as owned.

Tested purely through observable filesystem state, CLI invocations, and function return values.
Contains no AST, inspect, regex, or source text inspection (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle, worktree_lease


class LaneOwnerRecordAnchoringTests(unittest.TestCase):
    """Pin owner record anchoring and store reachability across worktree boundaries."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="test_owner_anchor_"))
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        # Clear positive memoization cache so scratch checkouts resolve freshly
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.addCleanup(ipd_lifecycle.clear_checkout_control_root_cache)

        self.main_repo = self.tmp_dir / "main_repo"
        self._init_repo(self.main_repo)

    def _init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
        subprocess.run(
            ["git", "-C", str(path), "config", "user.name", "Test Runner"], check=True
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "commit.gpgsign", "false"], check=True
        )
        (path / "README.md").write_text("initial commit\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
        subprocess.run(
            ["git", "-C", str(path), "commit", "-qm", "initial commit"], check=True
        )

    def _allocate_lane_with_cleanup(
        self, lane_id: str
    ) -> worktree_lease.WorktreeHandle:
        handle = worktree_lease.allocate_worktree(
            self.main_repo, lane_id, base_commit="HEAD"
        )

        def cleanup_lane() -> None:
            # Cleanly teardown worktree and remove branch if still registered
            try:
                worktree_lease.teardown_worktree(self.main_repo, lane_id)
            except Exception:
                pass
            # Fallback force cleanup if teardown refused or left residue
            if handle.path.exists():
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(self.main_repo),
                        "worktree",
                        "remove",
                        "--force",
                        str(handle.path),
                    ],
                    capture_output=True,
                )
            subprocess.run(
                ["git", "-C", str(self.main_repo), "branch", "-D", handle.branch],
                capture_output=True,
            )

        self.addCleanup(cleanup_lane)
        return handle

    def test_owner_record_path_and_read_anchoring_equivalence(self) -> None:
        """Case (a): _owner_record_path and read_lane_owner return the same record from main and lane."""
        lane_id = "lane_a"
        handle = self._allocate_lane_with_cleanup(lane_id)
        lane_root = handle.path

        # Write owner record from main repo
        record_path = worktree_lease.write_lane_owner(
            self.main_repo, lane_id, custom_field="val_a"
        )
        self.assertTrue(record_path.exists())

        path_main = worktree_lease._owner_record_path(self.main_repo, lane_id)
        path_lane = worktree_lease._owner_record_path(lane_root, lane_id)

        # Paths composed from main and lane must be identical
        self.assertEqual(path_main, path_lane)

        # Reads from main and lane must both find the record written by main
        read_main = worktree_lease.read_lane_owner(self.main_repo, lane_id)
        read_lane = worktree_lease.read_lane_owner(lane_root, lane_id)

        self.assertIsNotNone(read_main)
        self.assertIsNotNone(read_lane)
        self.assertEqual(read_main, read_lane)
        self.assertEqual(read_lane.get("custom_field"), "val_a")

    def test_gate_does_not_invert_from_lane_root(self) -> None:
        """Case (b): lane_is_safe_to_adopt and lane_owned_by_other_live_process agree across roots."""
        lane_id = "lane_b"
        handle = self._allocate_lane_with_cleanup(lane_id)
        lane_root = handle.path

        # Spawn a live child process to act as the third-party owner
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])

        def reap_child() -> None:
            child.terminate()
            child.wait()

        self.addCleanup(reap_child)

        # Write owner record pointing to the live child process
        worktree_lease.write_lane_owner(
            self.main_repo,
            lane_id,
            pid=child.pid,
            start_token=worktree_lease._process_start_token(child.pid),
        )

        safe_main, reason_main = worktree_lease.lane_is_safe_to_adopt(
            self.main_repo, lane_id
        )
        owned_main = worktree_lease.lane_owned_by_other_live_process(
            self.main_repo, lane_id
        )

        safe_lane, reason_lane = worktree_lease.lane_is_safe_to_adopt(
            lane_root, lane_id
        )
        owned_lane = worktree_lease.lane_owned_by_other_live_process(lane_root, lane_id)

        # Both roots must report not-safe to adopt with a LIVE reason
        self.assertFalse(safe_main)
        self.assertIn("LIVE", reason_main)
        self.assertFalse(safe_lane)
        self.assertIn("LIVE", reason_lane)

        # Both roots must report owned by other live process
        self.assertTrue(owned_main)
        self.assertTrue(owned_lane)

    def test_nongit_temp_directory_path_composition_noop(self) -> None:
        """Case (c): for a non-git temp directory, composed owners path is byte-identical to direct composition."""
        nongit_dir = self.tmp_dir / "nongit"
        nongit_dir.mkdir(parents=True, exist_ok=True)

        lane_id = "temp_lane"
        expected = (
            nongit_dir / worktree_lease.OWNERS_SUBDIR / f"{lane_id}.json"
        ).resolve()
        actual = worktree_lease._owner_record_path(nongit_dir, lane_id)

        self.assertEqual(actual, expected)

    def test_absent_versus_unreachable_owner_store(self) -> None:
        """Case (d): genuinely absent records are adoptable; unreachable stores refuse adoption."""
        lane_id = "lane_d"
        self._allocate_lane_with_cleanup(lane_id)

        # 1. Genuinely absent: no owners dir exists yet
        owners_dir = self.main_repo / worktree_lease.OWNERS_SUBDIR
        if owners_dir.exists():
            shutil.rmtree(owners_dir)

        safe, reason = worktree_lease.lane_is_safe_to_adopt(self.main_repo, lane_id)
        owned = worktree_lease.lane_owned_by_other_live_process(self.main_repo, lane_id)
        self.assertTrue(safe)
        self.assertEqual(reason, "no owner record; unclaimed")
        self.assertFalse(owned)

        # 2. Genuinely absent: owners dir exists but contains no record for lane_d
        owners_dir.mkdir(parents=True, exist_ok=True)
        safe, reason = worktree_lease.lane_is_safe_to_adopt(self.main_repo, lane_id)
        owned = worktree_lease.lane_owned_by_other_live_process(self.main_repo, lane_id)
        self.assertTrue(safe)
        self.assertEqual(reason, "no owner record; unclaimed")
        self.assertFalse(owned)

        # 3. Unreachable: owners directory replaced by a regular file
        shutil.rmtree(owners_dir)
        owners_dir.write_text("not a directory\n", encoding="utf-8")
        safe, reason = worktree_lease.lane_is_safe_to_adopt(self.main_repo, lane_id)
        owned = worktree_lease.lane_owned_by_other_live_process(self.main_repo, lane_id)
        self.assertFalse(safe)
        self.assertIn("unreadable", reason)
        self.assertTrue(owned)

        # 4. Unreachable: chmod 0 on owners directory (skipped for root)
        owners_dir.unlink()
        owners_dir.mkdir(parents=True, exist_ok=True)
        if os.geteuid() != 0:
            os.chmod(owners_dir, 0)
            self.addCleanup(os.chmod, owners_dir, 0o755)
            try:
                safe, reason = worktree_lease.lane_is_safe_to_adopt(
                    self.main_repo, lane_id
                )
                owned = worktree_lease.lane_owned_by_other_live_process(
                    self.main_repo, lane_id
                )
                self.assertFalse(safe)
                self.assertIn("unreadable", reason)
                self.assertTrue(owned)
            finally:
                os.chmod(owners_dir, 0o755)

        # 5. Dead owner process: adoptable
        dead_proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
        dead_proc.wait()
        worktree_lease.write_lane_owner(
            self.main_repo,
            lane_id,
            pid=dead_proc.pid,
            start_token=worktree_lease._process_start_token(dead_proc.pid),
        )
        safe, reason = worktree_lease.lane_is_safe_to_adopt(self.main_repo, lane_id)
        self.assertTrue(safe)
        self.assertIn("gone", reason)

        # 6. Owned by THIS process: self-reallocation adoptable
        worktree_lease.write_lane_owner(self.main_repo, lane_id)
        safe, reason = worktree_lease.lane_is_safe_to_adopt(self.main_repo, lane_id)
        self.assertTrue(safe)
        self.assertIn("THIS process", reason)


if __name__ == "__main__":
    unittest.main()
