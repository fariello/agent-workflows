"""Outcome tests for m0001 step-4a terminal-commit marker, hook acceptance, and step-5 cleanup.

IPD o19353 (E-01..E-04 / V-01..V-04). Spec 4sd62s Sections 5.2 steps 4a and 5.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Tuple

import pytest

from agent_workflows import layout_migration
from agent_workflows.hooks import (
    backlog_blocking_close_gate,
    executed_transition_gate,
)
from agent_workflows.migrations import m0001_metadata_v2

pytestmark = pytest.mark.core


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str = "repo"
) -> Path:
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        json.dumps(
            {"schema_version": 2, "cutovers": {"release_gate_at_rest": "2026-10-01"}}
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / ".aw" / ".gitignore").write_text(
        "/state/\n/config/local.json\nrecords/runs/\n",
        encoding="utf-8",
    )
    return repo


def _stage_plan_executed_transition(repo: Path) -> Tuple[Path, Path]:
    """Commit a pending plan, then stage its raw move into executed/."""
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    executed_dir = repo / ".aw" / "records" / "plans" / "executed"
    pending_dir.mkdir(parents=True, exist_ok=True)
    executed_dir.mkdir(parents=True, exist_ok=True)

    pending_plan = pending_dir / "20261101-demo-01-pl0001-sample.ipd.md"
    pending_plan.write_text(
        "# IPD: Sample\n\n- Id: pl0001\n- Status: approved\n- Set: demo\n- Order: 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed pending plan")

    executed_plan = executed_dir / pending_plan.name
    _git(
        repo,
        "mv",
        pending_plan.relative_to(repo).as_posix(),
        executed_plan.relative_to(repo).as_posix(),
    )
    executed_plan.write_text(
        "# IPD: Sample\n\n- Id: pl0001\n- Status: executed\n- Set: demo\n- Order: 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", executed_plan.relative_to(repo).as_posix())
    journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
    return executed_plan, journal_dir


def _stage_release_blocking_backlog_close(repo: Path) -> Tuple[Path, Path]:
    """Commit an open release-blocking backlog item, then stage its raw close to done/."""
    releases_dir = repo / ".aw" / "records" / "releases"
    open_dir = repo / ".aw" / "records" / "backlog" / "open"
    done_dir = repo / ".aw" / "records" / "backlog" / "done"
    releases_dir.mkdir(parents=True, exist_ok=True)
    open_dir.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)

    (releases_dir / "20260901-rel001-01-rel001-v1.release.md").write_text(
        "# Release: 1.0.0\n\n- Id: rel001\n- Status: planned\n- Version: 1.0.0\n",
        encoding="utf-8",
    )
    open_item = open_dir / "20261101-bk0001-01-bk0001-gate-item.backlog.md"
    open_item.write_text(
        "- Id: bk0001\n"
        "- Status: open\n"
        "- Blocks-Release: next\n"
        "- Set: bk0001\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Release blocking item\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed release and open backlog item")

    done_item = done_dir / open_item.name
    _git(
        repo,
        "mv",
        open_item.relative_to(repo).as_posix(),
        done_item.relative_to(repo).as_posix(),
    )
    done_item.write_text(
        "- Id: bk0001\n"
        "- Status: done\n"
        "- Blocks-Release: next\n"
        "- Set: bk0001\n"
        "- Priority: high\n"
        "- Work-Kind: feature\n"
        "- Summary: Release blocking item\n",
        encoding="utf-8",
    )
    _git(repo, "add", done_item.relative_to(repo).as_posix())
    journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
    return done_item, journal_dir


# --------------------------------------------------------------------------------------
# Executed transition gate marker acceptance
# --------------------------------------------------------------------------------------


class TestExecutedTransitionGateMarker:
    """Marker validation behavior for ``executed_transition_gate.check``."""

    def test_refused_without_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="exec_no_marker")
        _stage_plan_executed_transition(repo)

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 1
        assert msgs and "pl0001" in msgs[0]

    def test_accepted_with_matching_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="exec_match")
        _executed_plan, journal_dir = _stage_plan_executed_transition(repo)

        marker_path = m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)
        assert marker_path.is_file()
        marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
        assert marker_data["migration_id"] == "m0001"
        assert marker_data["tree_id"] == _git(repo, "write-tree").stdout.strip()

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 0
        assert msgs == []

        # Also verify checkout_control_root fallback from a detached linked worktree
        # (matching commit_lock.commit_isolated's detached .aw-isocommit-* worktree).
        wt = tmp_path / "linked_wt"
        head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _git(repo, "worktree", "add", "--detach", str(wt), head_sha)
        try:
            _git(
                wt,
                "rm",
                "-q",
                ".aw/records/plans/pending/20261101-demo-01-pl0001-sample.ipd.md",
            )
            wt_exec = (
                wt
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20261101-demo-01-pl0001-sample.ipd.md"
            )
            wt_exec.parent.mkdir(parents=True, exist_ok=True)
            wt_exec.write_text(
                (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / "20261101-demo-01-pl0001-sample.ipd.md"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            _git(wt, "add", wt_exec.relative_to(wt).as_posix())
            assert _git(wt, "write-tree").stdout.strip() == marker_data["tree_id"]
            wt_rc, wt_msgs = executed_transition_gate.check(wt)
            assert wt_rc == 0
            assert wt_msgs == []
        finally:
            _git(repo, "worktree", "remove", "--force", str(wt), check=False)

    def test_refused_after_extra_staged_edit(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="exec_extra_edit")
        _executed_plan, journal_dir = _stage_plan_executed_transition(repo)
        m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)

        (repo / "extra.txt").write_text("extra staged file\n", encoding="utf-8")
        _git(repo, "add", "extra.txt")

        rc, msgs = executed_transition_gate.check(repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert msgs
        assert "mismatch" in err.lower()
        assert len([ln for ln in err.splitlines() if ln.strip()]) == 1

    def test_refused_after_marker_consumed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="exec_consumed")
        _executed_plan, journal_dir = _stage_plan_executed_transition(repo)
        marker_path = m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)
        assert marker_path.is_file()

        m0001_metadata_v2._cleanup_marker(journal_dir, repo=repo)
        assert not marker_path.exists()
        journal_data = json.loads(
            (journal_dir / "journal.json").read_text(encoding="utf-8")
        )
        assert journal_data["terminal_commit_marker"] is None

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 1
        assert msgs


# --------------------------------------------------------------------------------------
# Backlog blocking-close gate marker acceptance
# --------------------------------------------------------------------------------------


class TestBacklogBlockingCloseGateMarker:
    """Marker validation behavior for ``backlog_blocking_close_gate.check``."""

    def test_refused_without_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="bk_no_marker")
        _stage_release_blocking_backlog_close(repo)

        rc, msgs = backlog_blocking_close_gate.check(repo)
        assert rc == 1
        assert msgs

    def test_accepted_with_matching_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="bk_match")
        _done_item, journal_dir = _stage_release_blocking_backlog_close(repo)
        marker_path = m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)
        assert marker_path.is_file()

        rc, msgs = backlog_blocking_close_gate.check(repo)
        assert rc == 0
        assert msgs == []

        # Also verify journal.json fallback when standalone marker file is absent.
        marker_path.unlink()
        rc_j, msgs_j = backlog_blocking_close_gate.check(repo)
        assert rc_j == 0
        assert msgs_j == []

    def test_refused_after_extra_staged_edit(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="bk_extra_edit")
        _done_item, journal_dir = _stage_release_blocking_backlog_close(repo)
        m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)

        (repo / "extra.txt").write_text("unrelated change\n", encoding="utf-8")
        _git(repo, "add", "extra.txt")

        rc, msgs = backlog_blocking_close_gate.check(repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert msgs
        assert "mismatch" in err.lower()

    def test_refused_after_marker_consumed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="bk_consumed")
        _done_item, journal_dir = _stage_release_blocking_backlog_close(repo)
        marker_path = m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)

        # Complete step-7 commit via commit_staged and verify marker consumption.
        outcome = m0001_metadata_v2.commit_staged(
            repo,
            [
                ".aw/records/backlog/open/20261101-bk0001-01-bk0001-gate-item.backlog.md",
                ".aw/records/backlog/done/20261101-bk0001-01-bk0001-gate-item.backlog.md",
            ],
        )
        assert outcome.status == "committed"
        assert not marker_path.exists()
        journal_data = json.loads(
            (journal_dir / "journal.json").read_text(encoding="utf-8")
        )
        assert journal_data["terminal_commit_marker"] is None

        # A subsequent raw close without a new marker is refused.
        done_dir = repo / ".aw" / "records" / "backlog" / "done"
        second = done_dir / "20261102-bk0002-01-bk0002-second.backlog.md"
        second.write_text(
            "- Id: bk0002\n"
            "- Status: done\n"
            "- Blocks-Release: next\n"
            "- Set: bk0002\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: Second ungated close\n",
            encoding="utf-8",
        )
        _git(repo, "add", second.relative_to(repo).as_posix())
        rc, msgs = backlog_blocking_close_gate.check(repo)
        assert rc == 1
        assert msgs


# --------------------------------------------------------------------------------------
# Step 5 cleanup and rollback
# --------------------------------------------------------------------------------------


class TestStep5Cleanup:
    """Behavior of ``m0001_metadata_v2._step_5_cleanup`` and ``rollback``."""

    def _seed_cleanup_targets(self, repo: Path) -> dict[Path, bytes]:
        rec = repo / ".aw" / "records"
        targets = {
            rec / "plans" / "STATUS.md": b"# STATUS\n\nGenerated status.\n",
            rec / "plans" / "INDEX.json": b'{"plans": []}\n',
            rec / "plans" / "INDEX.md": b"# Plans Index\n",
            rec / "research" / "INDEX.json": b'{"research": []}\n',
            rec / "research" / "INDEX.md": b"# Research Index\n",
            rec / "prompts" / "INDEX.json": b'{"prompts": []}\n',
            rec / "prompts" / "INDEX.md": b"# Prompts Index\n",
            repo / ".aw" / ".gitignore": (
                b"/state/\n"
                b"/config/local.json\n"
                b"records/runs/\n"
                b"records/plans/INDEX.json\n"
                b"records/plans/INDEX.md\n"
                b"records/research/INDEX.json\n"
                b"records/research/INDEX.md\n"
                b"records/prompts/INDEX.json\n"
                b"records/prompts/INDEX.md\n"
                b"/worktrees/\n"
            ),
        }
        for path, raw in targets.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return targets

    def test_step_5_removes_status_and_index_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="step5_remove")
        targets = self._seed_cleanup_targets(repo)

        # Dry run reports planned deletions without mutating files on disk.
        dry = m0001_metadata_v2._step_5_cleanup(repo, apply=False)
        assert dry["applied"] is False
        assert len(dry["status_files"]) == 1
        assert len(dry["index_files"]) == 6
        assert len(dry["gitignore_lines_removed"]) == 6
        for path, raw in targets.items():
            assert path.read_bytes() == raw

        # Apply deletes STATUS.md, all 6 INDEX files, and anchored INDEX ignore lines.
        res = m0001_metadata_v2._step_5_cleanup(repo, apply=True)
        assert res["applied"] is True
        assert len(res["deleted_files"]) == 7
        for path in targets:
            if path.name != ".gitignore":
                assert not path.exists(), f"{path} should be deleted"
        gi_text = (repo / ".aw" / ".gitignore").read_text(encoding="utf-8")
        assert gi_text == "/state/\n/config/local.json\nrecords/runs/\n/worktrees/\n"
        assert gi_text.endswith("\n")

    def test_step_5_idempotent_on_missing_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="step5_idempotent")
        orig_gi = (repo / ".aw" / ".gitignore").read_bytes()

        res1 = m0001_metadata_v2._step_5_cleanup(repo, apply=True)
        assert res1["deleted_files"] == []
        assert res1["gitignore_lines_removed"] == []
        assert (repo / ".aw" / ".gitignore").read_bytes() == orig_gi

        # Second call after already-clean state is a clean no-op.
        self._seed_cleanup_targets(repo)
        m0001_metadata_v2._step_5_cleanup(repo, apply=True)
        res2 = m0001_metadata_v2._step_5_cleanup(repo, apply=True)
        assert res2["deleted_files"] == []
        assert res2["gitignore_lines_removed"] == []

    def test_step_5_rollback_restores_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="step5_rollback")
        targets = self._seed_cleanup_targets(repo)
        # Seed one tracked plan so full run(apply=True) also has a record to migrate.
        plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261101-demo-01-pl0002-plan.ipd.md"
        )
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(
            "# IPD: Plan\n\n- Id: pl0002\n- Status: approved\n- Set: demo\n- Order: 1\n",
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "seed step5 rollback fixture")

        dry = m0001_metadata_v2.run(repo, apply=False)
        assert len(dry["cleanup"]["deleted_files"]) == 7

        applied = m0001_metadata_v2.run(repo, apply=True)
        assert applied["status"] == "applied"
        for path in targets:
            if path.name != ".gitignore":
                assert not path.exists()
        assert (repo / ".aw" / ".gitignore").read_text(encoding="utf-8") == (
            "/state/\n/config/local.json\nrecords/runs/\n/worktrees/\n"
        )
        assert applied["terminal_commit_marker"] is not None

        rb = m0001_metadata_v2.rollback(repo)
        assert rb["status"] == "rolled_back"
        for path, raw in targets.items():
            assert path.read_bytes() == raw
        journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
        assert not (journal_dir / "terminal_commit_marker.json").exists()
        assert _git(repo, "status", "--porcelain").stdout.strip() == ""


# --------------------------------------------------------------------------------------
# Marker error handling
# --------------------------------------------------------------------------------------


class TestMarkerErrorHandling:
    """Fail-closed behavior on corrupt markers, wrong migration ids, and unmerged indexes."""

    def test_corrupt_marker_json_falls_back_to_refusal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="err_corrupt")
        _executed_plan, journal_dir = _stage_plan_executed_transition(repo)
        journal_dir.mkdir(parents=True, exist_ok=True)
        (journal_dir / "terminal_commit_marker.json").write_text(
            "{not valid json", encoding="utf-8"
        )

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 1
        assert msgs

    def test_wrong_migration_id_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="err_wrong_id")
        _executed_plan, journal_dir = _stage_plan_executed_transition(repo)
        tree_id = _git(repo, "write-tree").stdout.strip()
        journal_dir.mkdir(parents=True, exist_ok=True)
        (journal_dir / "terminal_commit_marker.json").write_text(
            json.dumps({"migration_id": "m9999", "tree_id": tree_id}),
            encoding="utf-8",
        )

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 1
        assert msgs

    def test_unmerged_index_falls_back_to_refusal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _init_git_repo(tmp_path, monkeypatch, name="err_unmerged")
        journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"

        # Build a real merge conflict so git write-tree exits non-zero.
        conflict_file = repo / "conflict.txt"
        conflict_file.write_text("base\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "base conflict file")

        _git(repo, "checkout", "-q", "-b", "side_branch")
        conflict_file.write_text("side\n", encoding="utf-8")
        _git(repo, "add", "conflict.txt")
        _git(repo, "commit", "-q", "-m", "side edit")

        _git(repo, "checkout", "-q", "-")
        conflict_file.write_text("main\n", encoding="utf-8")
        _git(repo, "add", "conflict.txt")
        _git(repo, "commit", "-q", "-m", "main edit")

        merge_proc = _git(repo, "merge", "side_branch", check=False)
        assert merge_proc.returncode != 0

        # _step_4a_write_marker refuses an unmerged index via PreflightGateError.
        with pytest.raises(layout_migration.PreflightGateError, match="write-tree"):
            m0001_metadata_v2._step_4a_write_marker(repo, journal_dir)

        # Stage a raw executed plan transition alongside the unmerged index and a marker;
        # the hook fails closed without crashing when git write-tree fails.
        raw_plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20261102-demo-01-pl0003-unmerged.ipd.md"
        )
        raw_plan.parent.mkdir(parents=True, exist_ok=True)
        raw_plan.write_text(
            "# IPD: Unmerged\n\n- Id: pl0003\n- Status: executed\n",
            encoding="utf-8",
        )
        _git(repo, "add", raw_plan.relative_to(repo).as_posix())
        journal_dir.mkdir(parents=True, exist_ok=True)
        (journal_dir / "terminal_commit_marker.json").write_text(
            json.dumps({"migration_id": "m0001", "tree_id": "0" * 40}),
            encoding="utf-8",
        )

        rc, msgs = executed_transition_gate.check(repo)
        assert rc == 1
        assert msgs
