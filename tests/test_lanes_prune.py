"""Tests for aw lanes list and aw lanes prune [--apply].

Plan lanegc 45z93e (E-01 to E-07).
Drives the real CLI and scripted runner operations in scratch repositories.
Asserts on git worktree list, git branch --list, exit codes, and output.
No source introspection (AGENTS.md P16).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    lane_containment,
    lanes_cli,
    runner_shared,
    worktree_lease,
)
from agent_workflows.cli import main


def _git(cwd: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _init_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "branch", "-M", "main")
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n*.ignored\n__pycache__/\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "README.md")
    _git(repo, "commit", "-qm", "Initial commit")
    _rc, out, _ = _git(repo, "rev-parse", "HEAD")
    return out


def _create_run_record(
    repo: Path,
    run_id: str,
    lane_records: list[dict[str, Any]],
    queue: list[dict[str, Any]] | None = None,
    sweep_lane: dict[str, Any] | None = None,
) -> Path:
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    q = queue or []
    lane_by_id6 = {rec.get("id6"): rec for rec in lane_records if rec.get("id6")}
    for item in q:
        item_id6 = item.get("id6")
        if item_id6 in lane_by_id6 and not item.get("attempts"):
            rec = lane_by_id6[item_id6]
            item["attempts"] = [
                {
                    "attempt": 1,
                    "worktree": rec.get("worktree"),
                    "worktree_branch": rec.get("branch"),
                    "worktree_lane_id": rec.get("lane_id"),
                }
            ]
    state: dict[str, Any] = {
        "run_id": run_id,
        "repo": str(repo),
        "queue": q,
        "lanes": lane_records,
    }
    if sweep_lane:
        state[runner_shared.REVIEW_SWEEP_LANE_KEY] = sweep_lane
    (run_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return run_dir


# ======================================================================================
# E-03 / V-03: aw lanes list (all verdicts present)
# ======================================================================================


def test_lanes_list_verdicts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate all verdicts rendered by aw lanes list (E-03)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    # 1. Merged clean lane -> removable
    h_mrg = worktree_lease.allocate_worktree(repo, "mrg001")
    worktree_lease.clear_lane_owner(repo, "mrg001")
    (h_mrg.path / "file_mrg.txt").write_text("merged\n", encoding="utf-8")
    _git(h_mrg.path, "add", "file_mrg.txt")
    _git(h_mrg.path, "commit", "-qm", "commit on mrg001")
    _git(repo, "merge", "--no-ff", "-qm", "merge mrg001", h_mrg.branch)

    # 2. Unmerged lane -> keep: unmerged work
    h_unm = worktree_lease.allocate_worktree(repo, "unm001")
    worktree_lease.clear_lane_owner(repo, "unm001")
    (h_unm.path / "file_unm.txt").write_text("unmerged\n", encoding="utf-8")
    _git(h_unm.path, "add", "file_unm.txt")
    _git(h_unm.path, "commit", "-qm", "commit on unm001")

    # 3. Dirty lane -> keep: uncommitted changes
    h_drt = worktree_lease.allocate_worktree(repo, "drt001")
    worktree_lease.clear_lane_owner(repo, "drt001")
    _git(repo, "merge", "--no-ff", "-qm", "merge drt001", h_drt.branch)
    (h_drt.path / "dirty.txt").write_text("uncommitted edits\n", encoding="utf-8")

    # 4. Lane owned by live PID -> keep: live owner
    h_liv = worktree_lease.allocate_worktree(repo, "liv001")
    token_live = worktree_lease._process_start_token(os.getppid())
    worktree_lease.write_lane_owner(
        repo,
        "liv001",
        pid=os.getppid(),  # Parent process is live
        start_token=token_live,
        run_id="run-liv",
        role="worker",
    )

    # 5. Lane with unknown owner (different host) -> keep: unknown owner
    h_unk = worktree_lease.allocate_worktree(repo, "unk001")
    worktree_lease.write_lane_owner(
        repo,
        "unk001",
        pid=999999,
        host="other-remote-host.invalid",
        run_id="run-unk",
        role="worker",
    )

    # 6. Lane with no run record -> keep: no run record
    h_norun = worktree_lease.allocate_worktree(repo, "norun1")
    worktree_lease.clear_lane_owner(repo, "norun1")
    _git(repo, "merge", "--no-ff", "-qm", "merge norun1", h_norun.branch)

    # 7. Detached worktree under .aw/worktrees/ -> other: not a lane
    iso_dir = repo / ".aw" / "worktrees" / ".aw-isocommit-sample"
    iso_dir.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", "--detach", str(iso_dir), "HEAD")

    # 8. Broken branch pointing at non-existent object -> broken: <git error>
    ref_brk = repo / ".git" / "refs" / "heads" / "aw" / "lane" / "brk001"
    ref_brk.parent.mkdir(parents=True, exist_ok=True)
    ref_brk.write_text("0123456789abcdef0123456789abcdef01234567\n", encoding="utf-8")

    # Create run records for lanes 1-5
    def _lane_rec(handle: worktree_lease.WorktreeHandle, id6: str) -> dict[str, Any]:
        return {
            "lane_id": handle.lane_id,
            "branch": handle.branch,
            "worktree": str(handle.path),
            "id6": id6,
        }

    _create_run_record(
        repo,
        "run-test-01",
        lane_records=[
            _lane_rec(h_mrg, "mrg001"),
            _lane_rec(h_unm, "unm001"),
            _lane_rec(h_drt, "drt001"),
            _lane_rec(h_liv, "liv001"),
            _lane_rec(h_unk, "unk001"),
        ],
        queue=[
            {"id6": "mrg001", "position": 1, "action": "execute"},
            {"id6": "unm001", "position": 2, "action": "execute"},
            {"id6": "drt001", "position": 3, "action": "execute"},
            {"id6": "liv001", "position": 4, "action": "execute"},
            {"id6": "unk001", "position": 5, "action": "execute"},
        ],
    )

    rows = lanes_cli.collect_lane_rows(repo)
    verdicts = {r.lane: r.verdict for r in rows}

    assert verdicts.get("mrg001") == "removable"
    assert verdicts.get("unm001") == "keep: unmerged work"
    assert verdicts.get("drt001") == "keep: uncommitted changes"
    assert verdicts.get("liv001") == "keep: live owner"
    assert verdicts.get("unk001") == "keep: unknown owner"
    assert verdicts.get("norun1") == "keep: no run record"
    assert any("other: not a lane" in r.verdict for r in rows)
    assert any(r.verdict.startswith("broken:") for r in rows)

    # Test table render via CLI
    with mock.patch("sys.argv", ["aw", "lanes", "list"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            assert "removable" in captured.out
            assert "keep: unmerged work" in captured.out
            assert "keep: uncommitted changes" in captured.out
            assert "keep: live owner" in captured.out
            assert "keep: unknown owner" in captured.out
            assert "keep: no run record" in captured.out
            assert "other: not a lane" in captured.out
            assert "broken:" in captured.out

    # Test --agent output via CLI
    with mock.patch("sys.argv", ["aw", "lanes", "list", "--agent"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            record = json.loads(captured.out.strip().splitlines()[-1])
            assert record["cmd"] == "lanes list"
            assert record["outcome"] == "ok"
            assert record["exit"] == 0
            assert record["verified"] is True
            assert record["complete"] is True
            assert len(record["lanes"]) == len(rows)


# ======================================================================================
# E-04 / V-04: aw lanes prune (dry run and --apply)
# ======================================================================================


def test_lanes_prune_dry_run_and_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate dry run leaves lanes intact and --apply removes merged clean lanes (E-04)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    h_mrg = worktree_lease.allocate_worktree(repo, "mrg002")
    worktree_lease.clear_lane_owner(repo, "mrg002")
    (h_mrg.path / "file.txt").write_text("clean work\n", encoding="utf-8")
    _git(h_mrg.path, "add", "file.txt")
    _git(h_mrg.path, "commit", "-qm", "clean work")
    _git(repo, "merge", "--no-ff", "-qm", "merge mrg002", h_mrg.branch)

    _create_run_record(
        repo,
        "run-prune-01",
        lane_records=[
            {
                "lane_id": h_mrg.lane_id,
                "branch": h_mrg.branch,
                "worktree": str(h_mrg.path),
                "id6": "mrg002",
            }
        ],
        queue=[{"id6": "mrg002", "position": 1, "action": "execute"}],
    )

    # 1. Dry run
    with mock.patch("sys.argv", ["aw", "lanes", "prune"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            assert "dry run: pass --apply to remove" in captured.out
            assert "will remove worktree" in captured.out
            # Worktree and branch still exist
            assert h_mrg.path.exists()
            rc_br, out_br, _ = _git(repo, "branch", "--list", h_mrg.branch)
            assert h_mrg.branch in out_br

    # 2. Apply removal
    with mock.patch("sys.argv", ["aw", "lanes", "prune", "--apply"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            assert (
                f"removed worktree .aw/worktrees/mrg002 and branch {h_mrg.branch}"
                in captured.out
            )
            # Worktree and branch are gone
            assert not h_mrg.path.exists()
            rc_br, out_br, _ = _git(repo, "branch", "--list", h_mrg.branch)
            assert h_mrg.branch not in out_br

    # 3. Second apply is a no-op
    with mock.patch("sys.argv", ["aw", "lanes", "prune", "--apply"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            assert "removed worktree" not in captured.out


# ======================================================================================
# E-06: Untracked vs ignored files in R5.5 inventory gate
# ======================================================================================


def test_lanes_prune_unaccounted_untracked_kept_and_ignored_removed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A lane with unaccounted UNTRACKED is kept; a lane with only IGNORED is removed (E-06)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    # Lane 1: Merged but contains an unaccounted untracked file
    h_untracked = worktree_lease.allocate_worktree(repo, "untr01")
    worktree_lease.clear_lane_owner(repo, "untr01")
    _git(repo, "merge", "--no-ff", "-qm", "merge untr01", h_untracked.branch)
    (h_untracked.path / "unknown_extra.txt").write_text(
        "untracked payload\n", encoding="utf-8"
    )

    # Lane 2: Merged with only an ignored file (__pycache__/x.pyc)
    h_ignored = worktree_lease.allocate_worktree(repo, "ign001")
    worktree_lease.clear_lane_owner(repo, "ign001")
    _git(repo, "merge", "--no-ff", "-qm", "merge ign001", h_ignored.branch)
    pycache = h_ignored.path / "__pycache__"
    pycache.mkdir(parents=True, exist_ok=True)
    (pycache / "compiled.pyc").write_bytes(b"\x00\x00\x00\x00")

    _create_run_record(
        repo,
        "run-gate-01",
        lane_records=[
            {
                "lane_id": h_untracked.lane_id,
                "branch": h_untracked.branch,
                "worktree": str(h_untracked.path),
                "id6": "untr01",
            },
            {
                "lane_id": h_ignored.lane_id,
                "branch": h_ignored.branch,
                "worktree": str(h_ignored.path),
                "id6": "ign001",
            },
        ],
        queue=[
            {"id6": "untr01", "position": 1, "action": "execute"},
            {"id6": "ign001", "position": 2, "action": "execute"},
        ],
    )

    with mock.patch("sys.argv", ["aw", "lanes", "prune", "--apply"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            # Exit code 0 because every removable lane (ign001) was removed, untr01 was kept as uncommitted changes
            assert rc == 0
            captured = capsys.readouterr()

            # untr01 kept because of uncommitted changes
            assert "keep: uncommitted changes" in captured.out
            assert h_untracked.path.exists()
            rc_br, out_br, _ = _git(repo, "branch", "--list", h_untracked.branch)
            assert h_untracked.branch in out_br

            # ign001 removed despite ignored file (R5.5 amended 2026-09-18)
            assert (
                f"removed worktree .aw/worktrees/ign001 and branch {h_ignored.branch}"
                in captured.out
            )
            assert not h_ignored.path.exists()
            rc_br2, out_br2, _ = _git(repo, "branch", "--list", h_ignored.branch)
            assert h_ignored.branch not in out_br2


def test_lanes_prune_gate_refusal_uncollected_submission_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A removable lane refused by R5.5 inventory gate prints reason codes and exits 1 (E-04)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    h_ref = worktree_lease.allocate_worktree(repo, "ref001")
    worktree_lease.clear_lane_owner(repo, "ref001")
    _git(repo, "merge", "--no-ff", "-qm", "merge ref001", h_ref.branch)

    # Place uncollected submission under .aw/state/ (which is gitignored, so tree is clean to inspect_lane)
    sub_dir = lane_containment.lane_submission_root(
        h_ref.path, "run-ref-01", {"id6": "ref001", "position": 1}, 1
    )
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / "uncollected_submission.txt").write_text(
        "uncollected data\n", encoding="utf-8"
    )

    _create_run_record(
        repo,
        "run-ref-01",
        lane_records=[
            {
                "lane_id": h_ref.lane_id,
                "branch": h_ref.branch,
                "worktree": str(h_ref.path),
                "id6": "ref001",
            }
        ],
        queue=[{"id6": "ref001", "position": 1, "action": "execute"}],
    )

    with mock.patch("sys.argv", ["aw", "lanes", "prune", "--apply"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            # Exit code 1 because removable lane was refused by the inventory gate
            assert rc == 1
            captured = capsys.readouterr()
            assert "refused ref001" in captured.out
            assert "uncollected-submission" in captured.out
            assert h_ref.path.exists()
            rc_br, out_br, _ = _git(repo, "branch", "--list", h_ref.branch)
            assert h_ref.branch in out_br


# ======================================================================================
# E-04 / E-06: Live-owned lane and unrecorded lane are kept
# ======================================================================================


def test_lanes_prune_live_owned_and_no_record_kept(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A lane owned by a live process or with no run record is never removed (E-04)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    # 1. Live owned lane
    h_live = worktree_lease.allocate_worktree(repo, "liv002")
    _git(repo, "merge", "--no-ff", "-qm", "merge liv002", h_live.branch)
    token_live = worktree_lease._process_start_token(os.getppid())
    worktree_lease.write_lane_owner(
        repo,
        "liv002",
        pid=os.getppid(),
        start_token=token_live,
        run_id="run-live-02",
        role="worker",
    )

    # 2. Lane with no run record
    h_norun = worktree_lease.allocate_worktree(repo, "norun2")
    worktree_lease.clear_lane_owner(repo, "norun2")
    _git(repo, "merge", "--no-ff", "-qm", "merge norun2", h_norun.branch)

    with mock.patch("sys.argv", ["aw", "lanes", "prune", "--apply"]):
        with mock.patch("os.getcwd", return_value=str(repo)):
            rc = main()
            assert rc == 0
            captured = capsys.readouterr()
            assert "removed worktree" not in captured.out
            assert h_live.path.exists()
            assert h_norun.path.exists()


# ======================================================================================
# E-02 / V-02: Run-end reclamation and interrupt snapshot invariance
# ======================================================================================


def test_reclaim_run_lanes_run_end_mode(tmp_path: Path) -> None:
    """Run-end mode reclaims merged clean lanes, preserves unmerged without snapshot (E-02)."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    run_dir = repo / ".aw" / "records" / "runs" / "run-end-01"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Lane A: Merged clean -> reclaimed
    h_a = worktree_lease.allocate_worktree(repo, "itemA")
    worktree_lease.clear_lane_owner(repo, "itemA")
    (h_a.path / "file_a.txt").write_text("a work\n", encoding="utf-8")
    _git(h_a.path, "add", "file_a.txt")
    _git(h_a.path, "commit", "-qm", "commit a")
    _git(repo, "merge", "--no-ff", "-qm", "merge a", h_a.branch)

    # Lane B: Unmerged with dirty tracked changes -> preserved without snapshot
    h_b = worktree_lease.allocate_worktree(repo, "itemB")
    worktree_lease.clear_lane_owner(repo, "itemB")
    (h_b.path / "file_b.txt").write_text("b work\n", encoding="utf-8")
    _git(h_b.path, "add", "file_b.txt")
    _git(h_b.path, "commit", "-qm", "commit b")
    (h_b.path / "file_b.txt").write_text("b dirty\n", encoding="utf-8")

    # Lane C: Empty lane holding uncollected submission -> preserved with uncollected-submission
    h_c = worktree_lease.allocate_worktree(repo, "itemC")
    worktree_lease.clear_lane_owner(repo, "itemC")
    sub_dir = lane_containment.lane_submission_root(
        h_c.path, "run-end-01", {"id6": "itemC", "position": 3}, 1
    )
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / "uncollected_output.txt").write_text(
        "uncollected data\n", encoding="utf-8"
    )

    state = {
        "run_id": "run-end-01",
        "repo": str(repo),
        "queue": [
            {
                "id6": "itemA",
                "position": 1,
                "action": "execute",
                "attempts": [
                    {
                        "attempt": 1,
                        "worktree": str(h_a.path),
                        "worktree_branch": h_a.branch,
                        "worktree_lane_id": h_a.lane_id,
                    }
                ],
            },
            {
                "id6": "itemB",
                "position": 2,
                "action": "execute",
                "attempts": [
                    {
                        "attempt": 1,
                        "worktree": str(h_b.path),
                        "worktree_branch": h_b.branch,
                        "worktree_lane_id": h_b.lane_id,
                    }
                ],
            },
            {
                "id6": "itemC",
                "position": 3,
                "action": "execute",
                "attempts": [
                    {
                        "attempt": 1,
                        "worktree": str(h_c.path),
                        "worktree_branch": h_c.branch,
                        "worktree_lane_id": h_c.lane_id,
                    }
                ],
            },
        ],
        "lanes": [
            {
                "lane_id": h_a.lane_id,
                "branch": h_a.branch,
                "worktree": str(h_a.path),
                "id6": "itemA",
            },
            {
                "lane_id": h_b.lane_id,
                "branch": h_b.branch,
                "worktree": str(h_b.path),
                "id6": "itemB",
            },
            {
                "lane_id": h_c.lane_id,
                "branch": h_c.branch,
                "worktree": str(h_c.path),
                "id6": "itemC",
            },
        ],
    }

    lanes = runner_shared.reclaim_run_lanes(repo, run_dir, state)

    # Verify actions
    action_by_id = {lane_entry["id6"]: lane_entry["action"] for lane_entry in lanes}
    assert action_by_id["itemA"] == "reclaimed"
    assert action_by_id["itemB"] == "preserved"
    assert action_by_id["itemC"] == "preserved"

    # Verify worktree presence on disk
    assert not h_a.path.exists()
    assert h_b.path.exists()
    assert h_c.path.exists()

    # Verify B has NO snapshot commit
    _rc, log_msg, _ = _git(repo, "log", "-1", "--format=%s", h_b.branch)
    assert not log_msg.startswith("WIP INTERRUPTED SNAPSHOT")
    assert log_msg == "commit b"

    # Verify events
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    event_names = [e["event"] for e in events]
    assert "lane-reclaimed-at-run-end" in event_names
    assert "lane-preserved-at-run-end" in event_names

    # Item C retention reason code is uncollected-submission
    c_event = next(
        e
        for e in events
        if e.get("id6") == "itemC" and e["event"] == "lane-preserved-at-run-end"
    )
    assert "uncollected-submission" in c_event["retention_reasons"]

    # Verify summary line in state
    assert state.get("lanes_summary") == "lanes: 1 removed, 2 kept (aw lanes list)"


def test_interrupt_path_still_snapshots(tmp_path: Path) -> None:
    """The interrupt path (mode='interrupt') still creates snapshot commits on dirty lanes (E-02)."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    run_dir = repo / ".aw" / "records" / "runs" / "run-int-01"
    run_dir.mkdir(parents=True, exist_ok=True)

    h_int = worktree_lease.allocate_worktree(repo, "itemInt")
    worktree_lease.clear_lane_owner(repo, "itemInt")
    (h_int.path / "file.txt").write_text("int work\n", encoding="utf-8")
    _git(h_int.path, "add", "file.txt")
    _git(h_int.path, "commit", "-qm", "initial work")
    (h_int.path / "file.txt").write_text("dirty edit\n", encoding="utf-8")

    state = {
        "run_id": "run-int-01",
        "repo": str(repo),
        "queue": [
            {
                "id6": "itemInt",
                "position": 1,
                "action": "execute",
                "attempts": [
                    {
                        "attempt": 1,
                        "worktree": str(h_int.path),
                        "worktree_branch": h_int.branch,
                        "worktree_lane_id": h_int.lane_id,
                    }
                ],
            }
        ],
        "lanes": [
            {
                "lane_id": h_int.lane_id,
                "branch": h_int.branch,
                "worktree": str(h_int.path),
                "id6": "itemInt",
            }
        ],
    }

    lanes = runner_shared.reclaim_lanes_on_interrupt(
        repo,
        run_dir,
        state,
        interactive=False,
        reason="interrupt",
        mode="interrupt",
        lane_prompt=lambda lane, default: None,
        disable_prompt=lambda: None,
    )

    assert lanes[0]["action"] == "preserved"
    _rc, log_msg, _ = _git(repo, "log", "-1", "--format=%s", h_int.branch)
    assert log_msg.startswith("WIP INTERRUPTED SNAPSHOT")

    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any(e["event"] == "lane-preserved-on-interrupt" for e in events)


# ======================================================================================
# E-07 / V-07: Lane-to-run resolution
# ======================================================================================


def test_resolve_lane_to_run(tmp_path: Path) -> None:
    """resolve_lane_to_run maps lanes to run records, skips malformed state.json (E-07)."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    # Run 1: Normal execute lane
    _create_run_record(
        repo,
        "run-res-01",
        lane_records=[
            {
                "lane_id": "res001",
                "branch": "aw/lane/res001",
                "worktree": ".aw/worktrees/res001",
                "id6": "res001",
            }
        ],
        queue=[{"id6": "res001", "position": 1, "action": "execute"}],
    )

    # Run 2: Review sweep lane
    _create_run_record(
        repo,
        "run-res-02",
        lane_records=[],
        sweep_lane={
            "lane_id": "sweep-res-02",
            "branch": "aw/lane/review-sweep-res02",
            "worktree": ".aw/worktrees/review-sweep-res02",
        },
        queue=[
            {"id6": "rev001", "position": 1, "action": "review"},
            {"id6": "rev002", "position": 2, "action": "review"},
            {"id6": "exe003", "position": 3, "action": "execute"},
        ],
    )

    # Run 3: Corrupted state.json (malformed JSON)
    bad_run = repo / ".aw" / "records" / "runs" / "run-bad-03"
    bad_run.mkdir(parents=True, exist_ok=True)
    (bad_run / "state.json").write_text("{invalid json", encoding="utf-8")

    # 1. Resolve regular lane
    res1 = lanes_cli.resolve_lane_to_run(repo, "aw/lane/res001", ".aw/worktrees/res001")
    assert res1 is not None
    assert res1.run_dir.name == "run-res-01"
    assert res1.item is not None
    assert res1.item["id6"] == "res001"
    assert res1.is_sweep is False

    # 2. Resolve sweep lane
    res2 = lanes_cli.resolve_lane_to_run(
        repo, "aw/lane/review-sweep-res02", ".aw/worktrees/review-sweep-res02"
    )
    assert res2 is not None
    assert res2.run_dir.name == "run-res-02"
    assert res2.is_sweep is True
    assert res2.review_items is not None
    assert len(res2.review_items) == 2
    assert {it["id6"] for it in res2.review_items} == {"rev001", "rev002"}

    # 3. Unrecorded lane resolves to None
    res_none = lanes_cli.resolve_lane_to_run(
        repo, "aw/lane/unrecorded", ".aw/worktrees/unrecorded"
    )
    assert res_none is None
