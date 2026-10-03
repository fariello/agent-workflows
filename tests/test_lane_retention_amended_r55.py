"""Behavioral outcome tests for the amended spec 7ckptx R5.5 lane retention gate.

This module restores the outcome-level guard on the amended spec 7ckptx R5.5 classification,
which was left unguarded when commit 19313eed deleted tests/test_lane_retention.py and
tests/test_worktree_lease_merged_reclaim.py. It verifies by outcome that an interrupted or
merged lane holding only gitignored files is torn down as disposable while untracked and dirty
tracked content are preserved.

Honest limits of this guard (plan hyuos6 E-04):
1. CLASSIFICATION ONLY, NOT DECISION ORDER: This module guards the R5.5 classification logic
   inside `lane_containment.teardown_lane_if_classified` only, and specifically does NOT guard
   the interrupt-path decision order delivered by plan 65cuw0 E-03 (consulting merged-ness
   before bailing out on holds_work). The only surviving coverage referencing
   `reclaim_lanes_on_interrupt` is the operator-discard test at
   `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_discard_lane_reclaim`,
   which exercises the discard branch rather than merged-lane reclaim. The merged-lane reclaim
   decision-order guard was owned by backlog item `dwfmxz` (chore, filed at authoring), which
   has since graduated to pending plan `2rtp96` (`.aw/records/plans/pending/20260930-dwfmxz-01-2rtp96-guard-the-interrupt-path-merged-lane-reclaim-decision-order.ipd.md`).
2. DRIVES GATE DIRECTLY: Tests here drive `lane_containment.teardown_lane_if_classified`
   directly rather than through runner_shared / driver `reclaim_lanes_on_interrupt`. A regression
   that breaks how the runner reaches or invokes the gate would not fail this module.
3. COMPLETE RECEIPT WORKAROUND AND PENDING PLAN z8ex9f: An absent collection receipt causes
   `submission_retention` to report `uncollected=True`, which would mask retention checks under
   `('uncollected-submission',)`. This module supplies a complete collection receipt in each case
   to test classification in isolation. The question of whether an absent receipt should block an
   interrupted lane that provably wrote nothing was owned by backlog item `nvymif`, which
   graduated on 2026-09-30 to pending plan `z8ex9f` (`.aw/records/plans/pending/20260930-nvymif-01-z8ex9f-distinguish-a-lane-that-provably-submitted-nothing-from-one.ipd.md`).
   Plan z8ex9f declares `agent_workflows/lane_containment.py` in scope, narrows
   `submission_retention`, and adds a landing condition whose absent-branch case blocks.
   At the time plan hyuos6 executes, z8ex9f has not landed (`inventory_lane` does not accept a
   branch parameter). The lanes here are nevertheless fully merged into main so that threading a
   branch will satisfy the landing check once z8ex9f lands.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Tuple

import pytest

from agent_workflows import lane_containment, worktree_lease


def _git(cwd: Path, *args: str) -> None:
    """Run git in cwd and fail loudly on error."""
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def temp_repo_and_run(tmp_path: Path) -> Tuple[Path, Path, dict[str, Any], int]:
    """Create a git repo with a commit on main and a valid collection receipt in run_dir."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Tester")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "commit.gpgsign", "false")

    # Set up initial commit on main with .gitignore and a tracked file
    (repo / ".gitignore").write_text("build/\n*.ignored\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("initial content\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "tracked.txt")
    _git(repo, "commit", "-m", "initial commit")
    _git(repo, "branch", "-M", "main")

    # Set up run_dir with a complete collection receipt (item must have integer position)
    run_dir = tmp_path / "run_dir"
    collections_dir = run_dir / "collections"
    collections_dir.mkdir(parents=True)
    item = {"position": 1, "id6": "tst001"}
    attempt = 1
    receipt_path = lane_containment.collection_receipt_path(run_dir, item, attempt)
    receipt_path.write_text(
        json.dumps({"status": lane_containment.RECEIPT_COMPLETE, "submissions": []}),
        encoding="utf-8",
    )

    return repo, run_dir, item, attempt


def _create_merged_lane(
    repo: Path, lane_path: Path, branch_name: str, lane_id: str
) -> worktree_lease.WorktreeHandle:
    """Create a worktree lane, commit work on it, merge it to main, and return its handle."""
    _git(repo, "worktree", "add", "-b", branch_name, str(lane_path), "main")
    (lane_path / f"commit_{lane_id}.txt").write_text(
        f"work for {lane_id}\n", encoding="utf-8"
    )
    _git(lane_path, "add", f"commit_{lane_id}.txt")
    _git(lane_path, "commit", "-m", f"lane work for {lane_id}")
    _git(repo, "merge", branch_name)
    return worktree_lease.WorktreeHandle(
        lane_id=lane_id,
        path=lane_path,
        branch=branch_name,
        base_commit="HEAD",
    )


def test_merged_lane_holding_only_gitignored_file_is_torn_down(
    tmp_path: Path, temp_repo_and_run: Tuple[Path, Path, dict[str, Any], int]
) -> None:
    """A merged lane whose only unexplained content is gitignored is torn down and enumerated."""
    repo, run_dir, item, attempt = temp_repo_and_run
    lane_path = tmp_path / "lane_ignored"
    handle = _create_merged_lane(repo, lane_path, "lane/ignored", "lane_ignored")

    # Add gitignored content matching .gitignore ("build/")
    build_dir = lane_path / "build"
    build_dir.mkdir()
    precious = build_dir / "precious.txt"
    precious.write_text("ignored residue\n", encoding="utf-8")

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo,
        handle=handle,
        run_dir=run_dir,
        item=item,
        attempt=attempt,
    )

    assert decision.torn_down is True
    assert decision.inventory.reason_codes == ()
    assert not lane_path.exists()
    assert decision.inventory.unknown_ignored == ("build/precious.txt",)


def test_merged_lane_holding_untracked_file_is_preserved(
    tmp_path: Path, temp_repo_and_run: Tuple[Path, Path, dict[str, Any], int]
) -> None:
    """A merged lane holding an untracked unexplained file is preserved with its file intact."""
    repo, run_dir, item, attempt = temp_repo_and_run
    lane_path = tmp_path / "lane_untracked"
    handle = _create_merged_lane(repo, lane_path, "lane/untracked", "lane_untracked")

    untracked_file = lane_path / "unexplained.txt"
    untracked_file.write_text("untracked work\n", encoding="utf-8")

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo,
        handle=handle,
        run_dir=run_dir,
        item=item,
        attempt=attempt,
    )

    assert decision.torn_down is False
    assert decision.inventory.reason_codes == ("unknown-untracked-file",)
    assert lane_path.exists()
    assert untracked_file.exists()


def test_merged_lane_holding_dirty_tracked_file_is_preserved(
    tmp_path: Path, temp_repo_and_run: Tuple[Path, Path, dict[str, Any], int]
) -> None:
    """A merged lane holding an uncommitted dirty tracked file is preserved."""
    repo, run_dir, item, attempt = temp_repo_and_run
    lane_path = tmp_path / "lane_dirty"
    handle = _create_merged_lane(repo, lane_path, "lane/dirty", "lane_dirty")

    # Modify an existing tracked file without committing
    tracked_file = lane_path / "tracked.txt"
    tracked_file.write_text("dirty uncommitted change\n", encoding="utf-8")

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo,
        handle=handle,
        run_dir=run_dir,
        item=item,
        attempt=attempt,
    )

    assert decision.torn_down is False
    assert decision.inventory.reason_codes == ("dirty-tracked-file",)
    assert lane_path.exists()
    assert tracked_file.read_text(encoding="utf-8") == "dirty uncommitted change\n"


def test_merged_lane_clean_is_torn_down(
    tmp_path: Path, temp_repo_and_run: Tuple[Path, Path, dict[str, Any], int]
) -> None:
    """A merged lane that is completely clean and accounted for is torn down."""
    repo, run_dir, item, attempt = temp_repo_and_run
    lane_path = tmp_path / "lane_clean"
    handle = _create_merged_lane(repo, lane_path, "lane/clean", "lane_clean")

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo,
        handle=handle,
        run_dir=run_dir,
        item=item,
        attempt=attempt,
    )

    assert decision.torn_down is True
    assert decision.inventory.reason_codes == ()
    assert not lane_path.exists()
