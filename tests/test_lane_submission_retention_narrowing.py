"""Tests for lane submission retention narrowing and unlanded commits gate.

Contract and honest limits (spec 7ckptx R2.5, R5.5, R5.7; plan z8ex9f E-04, E-05):
1. DRIVES TEARDOWN GATE DIRECTLY: These tests invoke `lane_containment.teardown_lane_if_classified`
   directly, not through `runner_shared.reclaim_lanes_on_interrupt`. A regression that stopped the
   interrupt path from reaching the gate would not be caught by this module.
2. ANCESTRY-BASED REACHABILITY: The landing condition checks ancestry (`git merge-base --is-ancestor`)
   via `runner_shared.lane_work_has_landed`. Work that reached the target as a different commit
   (e.g., cherry-pick or squash) reads as unlanded and is PRESERVED, which is the safe, fail-toward-
   preservation direction. The content-based reachability helper
   `runner_shared.lane_work_landed_by_content` is deliberately not wired into this retention gate.
3. INTERRUPT ROUTE COLLAPSE UNPERFORMED: Collapsing the two interrupt-path teardown routes from plan
   65cuw0 (.aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md)
   into a single gate-driven path is made possible by this change but is explicitly deferred to
   subsequent work.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest import mock


from agent_workflows import lane_containment, worktree_lease


def _run_git(cwd: Path, *args: str) -> str:
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
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.invalid")
    _run_git(repo, "config", "user.name", "Test User")
    _run_git(repo, "config", "commit.gpgsign", "false")
    _run_git(repo, "branch", "-M", "main")
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _run_git(repo, "add", ".gitignore", "README.md")
    _run_git(repo, "commit", "-qm", "Initial commit")
    return _run_git(repo, "rev-parse", "HEAD")


def _setup_lane(
    repo: Path,
    lane_id: str,
    *,
    commit_work: bool = False,
    merge_lane: bool = False,
) -> worktree_lease.WorktreeHandle:
    handle = worktree_lease.allocate_worktree(repo, lane_id)
    if commit_work:
        (handle.path / "work.txt").write_text(f"work in {lane_id}\n", encoding="utf-8")
        _run_git(handle.path, "add", "work.txt")
        _run_git(handle.path, "commit", "-qm", f"work in {lane_id}")
    if merge_lane:
        _run_git(
            repo, "merge", "--no-ff", "-qm", f"merge {handle.branch}", handle.branch
        )
    return handle


def _make_item(
    lane_id: str, handle: worktree_lease.WorktreeHandle, attempt: int = 1
) -> dict[str, Any]:
    return {
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
            for _ in range(attempt)
        ],
    }


# ======================================================================================
# The Six Core Lane Shapes (F-08)
# ======================================================================================


def test_shape_1_interrupted_wrote_nothing_no_submission_tree(tmp_path: Path) -> None:
    """Shape 1: Interrupted turn, wrote nothing, no submission tree on disk -> TORN DOWN."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp001"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp001", handle)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is True
    assert decision.reason_codes == ()
    assert not handle.path.exists()


def test_shape_2_interrupted_tree_prepared_wrote_nothing(tmp_path: Path) -> None:
    """Shape 2: Interrupted turn, driver prepared tree, worker wrote nothing -> TORN DOWN."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp002")
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp002"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp002", handle)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    paths = lane_containment.project_worker_paths(
        item=item,
        run_id="run-shp002",
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=handle.path,
    )
    lane_containment.prepare_lane_submission_dir(paths)
    assert paths.lane_outcome is not None
    assert paths.lane_outcome.parent.is_dir()
    assert list(paths.lane_outcome.parent.iterdir()) == []

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is True
    assert decision.reason_codes == ()
    assert not handle.path.exists()


def test_shape_3_wrote_submission_never_collected(tmp_path: Path) -> None:
    """Shape 3: Worker wrote a submission, collection never ran -> PRESERVED with uncollected-submission."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp003")
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp003"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp003", handle)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    paths = lane_containment.project_worker_paths(
        item=item,
        run_id="run-shp003",
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=handle.path,
    )
    lane_containment.prepare_lane_submission_dir(paths)
    assert paths.lane_outcome is not None
    paths.lane_outcome.write_text(
        json.dumps({"disposition": "executed"}), encoding="utf-8"
    )

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is False
    assert decision.reason_codes == (lane_containment.RETENTION_UNCOLLECTED_SUBMISSION,)
    assert handle.path.exists()


def test_shape_4_wrote_submission_receipt_complete(tmp_path: Path) -> None:
    """Shape 4: Wrote submission, collection complete with receipt -> TORN DOWN."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp004")
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp004"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp004", handle)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    paths = lane_containment.project_worker_paths(
        item=item,
        run_id="run-shp004",
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=handle.path,
    )
    lane_containment.prepare_lane_submission_dir(paths)
    assert paths.lane_outcome is not None
    paths.lane_outcome.write_text(
        json.dumps({"disposition": "executed"}), encoding="utf-8"
    )

    collect_result = lane_containment.collect_lane_submissions(
        run_dir=run_dir,
        item=item,
        run_id="run-shp004",
        lane_root=handle.path,
        plan_path=plan_path,
        attempt=1,
    )
    assert collect_result is not None
    assert collect_result.get("status") == lane_containment.RECEIPT_COMPLETE

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is True
    assert decision.reason_codes == ()
    assert not handle.path.exists()


def test_shape_5_unmerged_commits_no_submission(tmp_path: Path) -> None:
    """Shape 5: Unmerged commits on branch, clean porcelain, no submission -> PRESERVED with unlanded-lane-commits."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp005", commit_work=True, merge_lane=False)
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp005"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp005", handle)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is False
    assert decision.reason_codes == (lane_containment.RETENTION_UNLANDED_LANE_COMMITS,)
    assert handle.path.exists()
    # Confirm branch still exists
    assert _run_git(repo, "rev-parse", "--verify", handle.branch)


def test_shape_6_merged_commits_no_submission(tmp_path: Path) -> None:
    """Shape 6: Merged commits, clean porcelain, no submission -> TORN DOWN."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "shp006", commit_work=True, merge_lane=True)
    run_dir = repo / ".aw" / "records" / "runs" / "run-shp006"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("shp006", handle)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is True
    assert decision.reason_codes == ()
    assert not handle.path.exists()


# ======================================================================================
# Fail-Toward-Preservation Cases
# ======================================================================================


def test_prior_attempt_uncollected_submission_preserves_lane(tmp_path: Path) -> None:
    """Prior attempt 1 wrote a submission, attempt 2 wrote nothing -> PRESERVED with uncollected-submission."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "prv001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-prv001"
    run_dir.mkdir(parents=True, exist_ok=True)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    # Attempt 1 item writes a submission
    item_att1 = _make_item("prv001", handle, attempt=1)
    paths_att1 = lane_containment.project_worker_paths(
        item=item_att1,
        run_id="run-prv001",
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=handle.path,
    )
    lane_containment.prepare_lane_submission_dir(paths_att1)
    assert paths_att1.lane_outcome is not None
    paths_att1.lane_outcome.write_text(
        json.dumps({"disposition": "partial"}), encoding="utf-8"
    )

    # Item is retried as attempt 2; attempt 2 wrote nothing
    item_att2 = _make_item("prv001", handle, attempt=2)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item_att2
    )

    assert decision.torn_down is False
    assert decision.reason_codes == (lane_containment.RETENTION_UNCOLLECTED_SUBMISSION,)
    assert handle.path.exists()


def test_item_none_preserves_lane(tmp_path: Path) -> None:
    """Item=None cannot determine submission status -> PRESERVED with uncollected-submission."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "non001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-non001"
    run_dir.mkdir(parents=True, exist_ok=True)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=None
    )

    assert decision.torn_down is False
    assert decision.reason_codes == (lane_containment.RETENTION_UNCOLLECTED_SUBMISSION,)
    assert handle.path.exists()


def test_unanswerable_landing_question_preserves_lane(tmp_path: Path) -> None:
    """Deleted or unresolvable branch -> PRESERVED with unlanded-lane-commits."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "una001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-una001"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("una001", handle)

    # Detach HEAD in the lane worktree so git allows deleting the branch
    _run_git(handle.path, "checkout", "--detach")
    _run_git(repo, "branch", "-D", handle.branch)

    decision = lane_containment.teardown_lane_if_classified(
        repo=repo, handle=handle, run_dir=run_dir, item=item
    )

    assert decision.torn_down is False
    assert decision.reason_codes == (lane_containment.RETENTION_UNLANDED_LANE_COMMITS,)
    assert handle.path.exists()


# ======================================================================================
# Detailed Predicate Behavior & Sweep Lane Tests
# ======================================================================================


def test_submission_retention_all_six_answers(tmp_path: Path) -> None:
    """Validate all six submission_retention answers directly."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "ret001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-ret001"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("ret001", handle)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    # 1. No receipt + provably empty tree -> uncollected=False, collected_paths=()
    ans1 = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=handle.path
    )
    assert ans1.uncollected is False
    assert ans1.collected_paths == ()
    assert "no file for this run" in (ans1.detail or "")

    # 2. No receipt + tree holding a file -> uncollected=True
    paths = lane_containment.project_worker_paths(
        item=item,
        run_id="run-ret001",
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=handle.path,
    )
    lane_containment.prepare_lane_submission_dir(paths)
    assert paths.lane_outcome is not None
    paths.lane_outcome.write_text(
        json.dumps({"disposition": "executed"}), encoding="utf-8"
    )
    ans2 = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=handle.path
    )
    assert ans2.uncollected is True
    assert "absence means NOT collected" in (ans2.detail or "")

    # 3. Receipt in-progress -> uncollected=True
    receipt_p = lane_containment.collection_receipt_path(run_dir, item, 1)
    receipt_p.parent.mkdir(parents=True, exist_ok=True)
    receipt_p.write_text(json.dumps({"status": "in-progress"}), encoding="utf-8")
    ans3 = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=handle.path
    )
    assert ans3.uncollected is True
    assert "in-progress" in (ans3.detail or "")

    # 4. Receipt complete with a failed submission -> uncollected=True
    receipt_p.write_text(
        json.dumps(
            {
                "status": "complete",
                "submissions": [
                    {"name": "outcome", "result": "failed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    ans4 = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=handle.path
    )
    assert ans4.uncollected is True
    assert "collection FAILED" in (ans4.detail or "")

    # 5. Receipt complete, all collected -> uncollected=False with collected_paths
    receipt_p.write_text(
        json.dumps(
            {
                "status": "complete",
                "submissions": [
                    {
                        "name": "outcome",
                        "result": "collected",
                        "source": str(paths.lane_outcome),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    ans5 = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=handle.path
    )
    assert ans5.uncollected is False
    assert len(ans5.collected_paths) == 1

    # 6. run_dir or item absent -> uncollected=True
    ans6_run = lane_containment.submission_retention(
        run_dir=None, item=item, lane_root=handle.path
    )
    assert ans6_run.uncollected is True
    ans6_item = lane_containment.submission_retention(
        run_dir=run_dir, item=None, lane_root=handle.path
    )
    assert ans6_item.uncollected is True


def test_submission_retention_enumeration_failure_preserves(tmp_path: Path) -> None:
    """When submission enumeration fails (unresolvable root or unreadable dir), fails toward preservation."""
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    item = {"id6": "err001", "position": 1, "attempts": []}

    # Nonexistent lane root
    bad_root = tmp_path / "nonexistent" / "lane"
    ans = lane_containment.submission_retention(
        run_dir=run_dir, item=item, lane_root=bad_root
    )
    assert ans.uncollected is True
    assert "enumeration failed" in (ans.detail or "")


def test_sweep_lane_landed_and_unlanded(tmp_path: Path) -> None:
    """Validate teardown_review_sweep_lane in both landed and unlanded states (V-03)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    # 1. Sweep lane with work merged -> tears down
    handle1 = _setup_lane(repo, "swp001", commit_work=True, merge_lane=True)
    run_dir1 = repo / ".aw" / "records" / "runs" / "run-swp001"
    run_dir1.mkdir(parents=True, exist_ok=True)
    item1 = _make_item("swp001", handle1)
    dec1 = lane_containment.teardown_review_sweep_lane(
        repo=repo, handle=handle1, run_dir=run_dir1, items=[item1]
    )
    assert dec1.torn_down is True
    assert not handle1.path.exists()

    # 2. Sweep lane with unmerged work -> refuses with unlanded-lane-commits
    handle2 = _setup_lane(repo, "swp002", commit_work=True, merge_lane=False)
    run_dir2 = repo / ".aw" / "records" / "runs" / "run-swp002"
    run_dir2.mkdir(parents=True, exist_ok=True)
    item2 = _make_item("swp002", handle2)
    dec2 = lane_containment.teardown_review_sweep_lane(
        repo=repo, handle=handle2, run_dir=run_dir2, items=[item2]
    )
    assert dec2.torn_down is False
    assert dec2.reason_codes == (lane_containment.RETENTION_UNLANDED_LANE_COMMITS,)
    assert handle2.path.exists()


def test_landing_delegation_to_shared_predicate(tmp_path: Path) -> None:
    """Prove R6.1 is honored by patching lane_work_has_landed and observing inventory change."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    handle = _setup_lane(repo, "dlg001")
    run_dir = repo / ".aw" / "records" / "runs" / "run-dlg001"
    run_dir.mkdir(parents=True, exist_ok=True)
    item = _make_item("dlg001", handle)

    # Normally clean lane with 0 commits has landed work
    inv_normal = lane_containment.inventory_lane(
        lane_root=handle.path, run_dir=run_dir, item=item, branch=handle.branch
    )
    assert inv_normal.unlanded_commits is False
    assert inv_normal.classified is True

    # Patch lane_work_has_landed to return False
    with mock.patch(
        "agent_workflows.runner_shared.lane_work_has_landed", return_value=False
    ):
        inv_patched = lane_containment.inventory_lane(
            lane_root=handle.path, run_dir=run_dir, item=item, branch=handle.branch
        )
        assert inv_patched.unlanded_commits is True
        assert inv_patched.classified is False
        assert (
            lane_containment.RETENTION_UNLANDED_LANE_COMMITS in inv_patched.reason_codes
        )
