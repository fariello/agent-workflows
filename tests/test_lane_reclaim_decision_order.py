"""Outcome-level tests guarding the interrupt-path merged-lane reclaim decision order.

Guards the decision order in `runner_shared.reclaim_lanes_on_interrupt` and its
predicate `lane_is_recovered_and_reclaimable` across both host drivers (`oc` and `agy`).
"""

import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Tuple
import unittest

from agent_workflows import (
    agy_runipd,
    lane_containment,
    oc_runipd,
    runner_shared,
    worktree_lease,
)

HOST_DRIVERS = (
    ("oc", oc_runipd),
    ("agy", agy_runipd),
)


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return res.stdout.strip()


def _init_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "branch", "-M", "main")
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n*.ignored\nbuild/\n",
        encoding="utf-8",
    )
    (repo / "seed.txt").write_text("seed commit\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "seed.txt")
    _git(repo, "commit", "-qm", "seed commit")
    base_sha = _git(repo, "rev-parse", "HEAD")
    return base_sha


def setup_lane_fixture(
    temp_dir: Path,
    lane_id: str = "mrg001",
    *,
    advance_target: bool = True,
    commit_work: bool = True,
    merge_lane: bool = True,
    write_receipt: bool = True,
) -> Tuple[
    Path, Path, dict[str, Any], worktree_lease.WorktreeHandle, dict[str, Any], str
]:
    """Create a real git repo with an isolated lane worktree and durable runner state."""
    repo = temp_dir / "repo"
    base_sha = _init_repo(repo)

    if advance_target:
        (repo / "advance.txt").write_text("advance target\n", encoding="utf-8")
        _git(repo, "add", "advance.txt")
        _git(repo, "commit", "-qm", "advance target")

    lane_base = base_sha if advance_target else "HEAD"
    handle = worktree_lease.allocate_worktree(repo, lane_id, base_commit=lane_base)

    if commit_work:
        (handle.path / f"{lane_id}_work.txt").write_text(
            f"work for {lane_id}\n", encoding="utf-8"
        )
        _git(handle.path, "add", f"{lane_id}_work.txt")
        _git(handle.path, "commit", "-qm", f"work for {lane_id}")

    if merge_lane:
        _git(repo, "merge", "--no-ff", "-qm", f"merge {handle.branch}", handle.branch)

    run_dir = repo / ".aw" / "records" / "runs" / f"run-{lane_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "id6": lane_id,
        "position": 1,
        "status": "running",
        "attempts": [
            {
                "worktree": str(handle.path),
                "worktree_branch": handle.branch,
                "worktree_lane_id": handle.lane_id,
                "worktree_base": handle.base_commit,
                "worktree_disposition": handle.disposition,
            }
        ],
    }

    if write_receipt:
        receipt_path = lane_containment.collection_receipt_path(run_dir, item, 1)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(
                {
                    "status": lane_containment.RECEIPT_COMPLETE,
                    "submissions": [],
                    "collected": [],
                    "failed": [],
                }
            ),
            encoding="utf-8",
        )

    state = {
        "run_id": f"run-{lane_id}",
        "repo": str(repo),
        "queue": [item],
    }

    return repo, run_dir, state, handle, item, base_sha


class LaneReclaimDecisionOrderTests(unittest.TestCase):
    """Outcome-level test suite guarding the interrupt-path merged-lane decision order."""

    def test_fixture_integrity_precondition_conjunction(self) -> None:
        """E-01: Merged lane simultaneously reports merged_into_target=True, holds_work=True, dirty=False."""
        for host_label, _driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, _run_dir, state, handle, _item, base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="mrg001",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=True,
                    write_receipt=True,
                )

                # Verify real git worktree presence
                wt_list = _git(repo, "worktree", "list")
                self.assertIn(str(handle.path), wt_list)

                # Verify target head is ahead of the lane's base commit
                rev_list = _git(repo, "rev-list", f"{base_sha}..HEAD")
                self.assertTrue(
                    len(rev_list.splitlines()) >= 2,
                    f"Target HEAD must be ahead of base {base_sha}",
                )

                lanes = [
                    runner_shared.describe_lane_with_recovery(repo, rec)
                    for rec in runner_shared.lane_records_including_sweep(state)
                ]
                self.assertEqual(len(lanes), 1)
                lane = lanes[0]

                # Assert the load-bearing conjunction that forms the defect's precondition
                self.assertTrue(
                    lane["merged_into_target"],
                    "merged lane must report merged_into_target=True",
                )
                self.assertTrue(
                    lane["holds_work"],
                    "merged lane must report holds_work=True because commits_ahead is measured against lane base",
                )
                self.assertFalse(
                    lane["dirty"],
                    "merged lane without uncommitted files must report dirty=False",
                )
                self.assertTrue(
                    lane["reclaimable"],
                    "merged clean lane must report reclaimable=True",
                )

    def test_decision_order_merged_lane_is_reclaimed(self) -> None:
        """E-02: Merged lane with complete receipt is reclaimed, worktree removed, event emitted."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, _item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="mrg002",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=True,
                    write_receipt=True,
                )

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Assert that the lane still reported holds_work=True (WHY the order matters)
                self.assertTrue(
                    lane["holds_work"],
                    "Lane must report holds_work=True because commits_ahead is measured against lane base; "
                    "this is why decision order matters: a holds_work-first bail-out would never reach the merged branch",
                )

                # Assert observable outcome: action == 'reclaimed' and worktree removed
                self.assertEqual(
                    lane["action"],
                    "reclaimed",
                    "Merged lane must have action='reclaimed', not 'preserved'",
                )
                self.assertFalse(
                    handle.path.exists(),
                    f"Worktree directory {handle.path} must no longer exist on disk",
                )
                wt_list = _git(repo, "worktree", "list")
                self.assertNotIn(
                    str(handle.path),
                    wt_list,
                    "Reclaimed lane must be absent from git worktree list",
                )

                # Assert event emitted in events.jsonl
                events_file = run_dir / "events.jsonl"
                self.assertTrue(events_file.exists(), "events.jsonl must exist")
                events = [
                    json.loads(line)
                    for line in events_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                reclaim_events = [
                    e for e in events if e.get("event") == "lane-reclaimed-on-interrupt"
                ]
                self.assertEqual(
                    len(reclaim_events),
                    1,
                    f"Expected exactly 1 lane-reclaimed-on-interrupt event, got {len(reclaim_events)}",
                )
                self.assertEqual(reclaim_events[0]["branch"], handle.branch)
                self.assertTrue(
                    reclaim_events[0]["merged_into_target"],
                    "Reclaim event must carry merged_into_target=True",
                )

    def test_merged_lane_with_untracked_file_is_preserved(self) -> None:
        """E-03(1): Merged lane holding unaccounted untracked file is preserved without reason codes."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, _item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="mrg003",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=True,
                    write_receipt=True,
                )

                # Add unaccounted untracked file
                untracked_file = handle.path / "untracked.txt"
                untracked_file.write_text("untracked work\n", encoding="utf-8")

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Assert survival
                self.assertEqual(lane["action"], "preserved")
                self.assertTrue(
                    handle.path.is_dir(), "Worktree directory must survive on disk"
                )
                self.assertTrue(
                    untracked_file.exists(), "Untracked file must survive on disk"
                )
                self.assertEqual(
                    untracked_file.read_text(encoding="utf-8"), "untracked work\n"
                )

                # Assert that retention_reason_codes is absent (mechanism: dirty clause stopped it, never reached gate)
                self.assertIsNone(
                    lane.get("retention_reason_codes"),
                    "Untracked shape never reaches R5.5 gate because dirty clause stopped it earlier; "
                    "retention_reason_codes must be None",
                )

    def test_merged_lane_without_collection_receipt_is_preserved_with_code(
        self,
    ) -> None:
        """E-03(2): Merged lane without collection receipt reaches gate and is preserved with uncollected-submission."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="mrg004",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=True,
                    write_receipt=False,
                )

                # Precondition: no receipt written
                receipt_path = lane_containment.collection_receipt_path(
                    run_dir, item, 1
                )
                self.assertFalse(
                    receipt_path.exists(), "Collection receipt must not exist"
                )

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Assert gate refusal and retention reason codes
                self.assertEqual(lane["action"], "preserved")
                self.assertTrue(
                    handle.path.is_dir(), "Worktree directory must survive on disk"
                )
                self.assertIsNotNone(lane.get("retention_reason_codes"))
                self.assertIn(
                    lane_containment.RETENTION_UNCOLLECTED_SUBMISSION,
                    lane["retention_reason_codes"],
                )

    def test_unmerged_dirty_lane_is_preserved_with_snapshot(self) -> None:
        """E-03(3): Unmerged dirty lane is preserved with snapshot commit and empty stash list."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, _item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="unm001",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=False,
                    write_receipt=True,
                )

                # Add uncommitted dirty modification
                dirty_file = handle.path / "dirty.txt"
                dirty_file.write_text("uncommitted dirty work\n", encoding="utf-8")

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Assert preservation with snapshot
                self.assertEqual(lane["action"], "preserved")
                self.assertTrue(
                    handle.path.is_dir(), "Worktree directory must survive on disk"
                )
                snapshot = lane.get("snapshot_commit")
                self.assertTrue(bool(snapshot), "snapshot_commit must be populated")

                # Branch must be resolvable
                branch_sha = _git(repo, "rev-parse", "--verify", handle.branch)
                self.assertTrue(bool(branch_sha))

                # git stash list must be EMPTY
                stash_list = _git(repo, "stash", "list")
                self.assertEqual(stash_list, "", "git stash list must remain empty")

    def test_empty_lane_at_head_without_receipt_is_reclaimed(self) -> None:
        """E-04(1): Provably empty lane at HEAD without collection receipt is reclaimed."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="emp001",
                    advance_target=False,
                    commit_work=False,
                    merge_lane=False,
                    write_receipt=False,
                )

                # Assert fixture precondition: collection receipt does NOT exist
                receipt_path = lane_containment.collection_receipt_path(
                    run_dir, item, 1
                )
                self.assertFalse(
                    receipt_path.exists(),
                    "Precondition: collection receipt must not exist for empty-lane fixture",
                )

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Observable outcome: reclaimed and worktree gone
                self.assertEqual(lane["action"], "reclaimed")
                self.assertFalse(handle.path.exists(), "Empty worktree must be removed")
                wt_list = _git(repo, "worktree", "list")
                self.assertNotIn(str(handle.path), wt_list)

    def test_merged_lane_with_only_gitignored_residue_is_reclaimed(self) -> None:
        """E-04(2): Merged lane holding only gitignored residue is reclaimed through the gate."""
        for host_label, driver in HOST_DRIVERS:
            with self.subTest(host=host_label), tempfile.TemporaryDirectory() as td:
                temp_dir = Path(td)
                repo, run_dir, state, handle, _item, _base_sha = setup_lane_fixture(
                    temp_dir,
                    lane_id="ign001",
                    advance_target=True,
                    commit_work=True,
                    merge_lane=True,
                    write_receipt=True,
                )

                # Add gitignored residue
                ignored_file = handle.path / "residue.ignored"
                ignored_file.write_text("ignored residue\n", encoding="utf-8")

                # Precondition check: git check-ignore confirms it is genuinely ignored
                rc = subprocess.run(
                    ["git", "check-ignore", "-q", "residue.ignored"],
                    cwd=handle.path,
                ).returncode
                self.assertEqual(
                    rc,
                    0,
                    "residue.ignored must be genuinely ignored by git check-ignore",
                )

                reclaimed = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=False
                )

                self.assertEqual(len(reclaimed), 1)
                lane = reclaimed[0]

                # Observable outcome: reclaimed and worktree gone
                self.assertEqual(lane["action"], "reclaimed")
                self.assertFalse(
                    handle.path.exists(),
                    "Worktree holding only ignored residue must be removed",
                )
                wt_list = _git(repo, "worktree", "list")
                self.assertNotIn(str(handle.path), wt_list)
