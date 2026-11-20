"""Outcome tests for m0001 step-1 preflight gates and migration journal lifecycle.

IPD vxevph (E-02, E-03, E-05 / V-02, V-03, V-05). Spec 4sd62s Sections 5.1 and 5.2
step 0 and step 1, AC-22 case (1), AC-27 cases (1) to (4).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows import (
    ipd_lifecycle,
    layout_migration,
    platform_lock,
    runner_shared,
)
from agent_workflows.migrations import chain, m0001_metadata_v2, m0001_preflight

pytestmark = pytest.mark.core


_DEFAULT_GITIGNORE = (
    "/state/\n/config/local.json\nrecords/history.jsonl\nrecords/plans/INDEX.json\n"
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "repo",
    with_sidecar: bool = True,
) -> Path:
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")

    plan = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0001-sample-plan.ipd.md"
    )
    plan.write_text(
        "# IPD: Sample plan\n\n- Id: pl0001\n- Status: approved\n- Set: demo\n- Order: 1\n- Short-Description: Sample plan\n",
        encoding="utf-8",
    )
    bk = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-demo-01-bk0001-sample-item.backlog.md"
    )
    bk.write_text(
        "- Id: bk0001\n- Status: open\n- Summary: Sample backlog item\n- Short-Description: Sample backlog item\n",
        encoding="utf-8",
    )

    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "init")

    if with_sidecar:
        sidecar = repo / ".aw" / "records" / "history.jsonl"
        rec = {
            "id6": "bk0001",
            "date": "20261101",
            "tree": "backlog",
            "workflow": "backlog",
            "actor": "tester",
            "message": "created",
        }
        sidecar.write_text(json.dumps(rec) + "\n", encoding="utf-8")

    return repo


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    """Capture relative-path -> bytes map for everything outside .git/."""
    snap: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_file():
            snap[p.relative_to(root).as_posix()] = p.read_bytes()
    return snap


def _spawn_lock_holder(lock_path: Path) -> subprocess.Popen[str]:
    script = (
        "import sys; from pathlib import Path; "
        "from agent_workflows import platform_lock; "
        "h = platform_lock.acquire(Path(sys.argv[1])); "
        "print('LOCKED', flush=True); "
        "sys.stdin.readline(); "
        "h.release()"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script, str(lock_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    ready = proc.stdout.readline().strip()
    assert (
        ready == "LOCKED"
    ), f"child failed to lock: {proc.stderr.read() if proc.stderr else ''}"
    return proc


# --------------------------------------------------------------------------------------
# AC-27 case (1): uncommitted records, held lock / None probe, unmerged / unknown lanes
# --------------------------------------------------------------------------------------


def test_preflight_uncommitted_records_refusal_and_force_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch)
    plan = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0001-sample-plan.ipd.md"
    )
    plan.write_text(
        plan.read_text(encoding="utf-8") + "\nUncommitted edit\n", encoding="utf-8"
    )
    before = _snapshot_tree(repo)

    with pytest.raises(layout_migration.PreflightGateError) as exc_info:
        m0001_metadata_v2.run(repo, apply=False)
    msg = str(exc_info.value)
    assert "UNCOMMITTED" in msg
    assert _snapshot_tree(repo) == before
    assert not (repo / ".aw" / "state" / "durable" / "migrations" / "m0001").exists()

    report = m0001_metadata_v2.run(repo, apply=False, force=True)
    assert report["status"] == "dry_run"
    overrides = report["preflight"]["overridden"]
    assert any(o["condition"] == "UNCOMMITTED" for o in overrides)
    uncommitted_ovr = next(o for o in overrides if o["condition"] == "UNCOMMITTED")
    assert "mixed into the migration commit or lost" in uncommitted_ovr["consequence"]

    # External companion records_root that is its own git working tree
    ext_records = tmp_path / "companion_records"
    ext_records.mkdir()
    _git(ext_records, "init")
    _git(ext_records, "config", "user.name", "Test User")
    _git(ext_records, "config", "user.email", "test@example.com")
    (ext_records / "note.md").write_text("clean\n", encoding="utf-8")
    _git(ext_records, "add", "note.md")
    _git(ext_records, "commit", "-m", "init companion")
    clean_repo = _init_repo(tmp_path, monkeypatch, name="clean_for_ext")
    assert (
        m0001_preflight.check_preflight(clean_repo, records_root=ext_records)["ok"]
        is True
    )

    (ext_records / "note.md").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(layout_migration.PreflightGateError, match="UNCOMMITTED"):
        m0001_preflight.check_preflight(clean_repo, records_root=ext_records)


def test_preflight_held_integration_lock_and_none_probe_refusal_and_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch)
    lock_path = runner_shared.integration_lock_path(repo)
    proc = _spawn_lock_holder(lock_path)
    try:
        before = _snapshot_tree(repo)
        with pytest.raises(layout_migration.PreflightGateError) as exc_info:
            m0001_metadata_v2.run(repo, apply=False)
        assert "LOCK" in str(exc_info.value)
        assert _snapshot_tree(repo) == before
        assert not (
            repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
        ).exists()

        report = m0001_metadata_v2.run(repo, apply=False, force=True)
        assert report["preflight"]["lock_overridden"] is True
        lock_ovr = next(
            o for o in report["preflight"]["overridden"] if o["condition"] == "LOCK"
        )
        assert "race a driver" in lock_ovr["consequence"]

        # acquire_apply_integration_lock skips touching integration.lock when lock_overridden=True
        with m0001_preflight.acquire_apply_integration_lock(
            repo, apply=True, lock_overridden=True, force=True
        ) as outcome:
            assert outcome is None

        # When not overridden, acquire_apply_integration_lock refuses if lock cannot be acquired
        with pytest.raises(layout_migration.PreflightGateError, match="LOCK"):
            with m0001_preflight.acquire_apply_integration_lock(
                repo, apply=True, lock_overridden=False, force=False, timeout=0.02
            ):
                pass
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5)

    # Once released, acquire_apply_integration_lock acquires cleanly
    with m0001_preflight.acquire_apply_integration_lock(
        repo, apply=True, lock_overridden=False, force=False, timeout=1.0
    ) as outcome:
        assert outcome is not None and outcome.acquired is True

    # Unanswerable lock probe (None) refuses on its own condition and overrides with --force
    monkeypatch.setattr(platform_lock, "probe_free", lambda _p: None)
    before_none = _snapshot_tree(repo)
    with pytest.raises(layout_migration.PreflightGateError) as exc_none:
        m0001_metadata_v2.run(repo, apply=False)
    assert "LOCK" in str(exc_none.value)
    assert "None" in str(exc_none.value) or "unanswerable" in str(exc_none.value)
    assert _snapshot_tree(repo) == before_none

    report_none = m0001_metadata_v2.run(repo, apply=False, force=True)
    assert report_none["preflight"]["lock_overridden"] is True


def test_preflight_linked_lane_unmerged_and_unknown_landing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch)
    wt_dir = tmp_path / "lane-wt"
    _git(repo, "worktree", "add", "-b", "aw/lane/pl0001", str(wt_dir), "HEAD")
    lane_plan = (
        wt_dir
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0001-sample-plan.ipd.md"
    )
    lane_plan.write_text(
        lane_plan.read_text(encoding="utf-8") + "\nLane edit\n", encoding="utf-8"
    )
    _git(wt_dir, "add", ".aw/records")
    _git(wt_dir, "commit", "-m", "lane plan change")

    before = _snapshot_tree(repo)
    with pytest.raises(layout_migration.PreflightGateError) as exc_info:
        m0001_metadata_v2.run(repo, apply=False)
    msg = str(exc_info.value)
    assert "LANES" in msg
    assert str(wt_dir) in msg
    assert _snapshot_tree(repo) == before

    report = m0001_metadata_v2.run(repo, apply=False, force=True)
    lane_ovr = next(
        o for o in report["preflight"]["overridden"] if o["condition"] == "LANES"
    )
    assert "conflict" in lane_ovr["consequence"]

    # Detached lane produces None from lane_work_has_landed and must render as "unknown"
    _git(wt_dir, "checkout", "--detach")
    with pytest.raises(layout_migration.PreflightGateError) as exc_det:
        m0001_metadata_v2.run(repo, apply=False)
    det_msg = str(exc_det.value)
    assert "LANES" in det_msg
    assert "unknown" in det_msg

    # Merged lane worktree no longer triggers LANES
    _git(repo, "merge", "--no-ff", "aw/lane/pl0001", "-m", "merge lane")
    _git(wt_dir, "checkout", "aw/lane/pl0001")
    clean_report = m0001_metadata_v2.run(repo, apply=False)
    assert clean_report["status"] == "dry_run"


# --------------------------------------------------------------------------------------
# AC-27 cases (2), (3), (4) and AC-22 case (1): worktree vs force vs missing sidecar
# --------------------------------------------------------------------------------------


def test_preflight_worktree_refusal_force_vs_force_worktree_and_missing_common_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, with_sidecar=False)
    bk = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-demo-01-bk0001-sample-item.backlog.md"
    )
    bk.write_text(
        bk.read_text(encoding="utf-8")
        + "\n## Workflow history\n\n- 2026-11-01 open (aw backlog): created\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/records")
    _git(repo, "commit", "-m", "record sidecar-writing setter history")
    wt_dir = tmp_path / "linked-wt"
    _git(repo, "worktree", "add", "-b", "lane-wt", str(wt_dir), "HEAD")

    before_wt = _snapshot_tree(wt_dir)
    # AC-27 case (2): linked worktree refuses even with --force, naming --force-worktree
    with pytest.raises(layout_migration.PreflightGateError) as exc_force:
        m0001_metadata_v2.run(wt_dir, apply=False, force=True, force_worktree=False)
    assert "WORKTREE" in str(exc_force.value)
    assert "--force-worktree" in str(exc_force.value)
    assert _snapshot_tree(wt_dir) == before_wt
    assert not (repo / ".aw" / "state" / "durable" / "migrations" / "m0001").exists()

    # AC-27 case (3) & AC-22 case (1): --force-worktree passes step 1, refuses at step 2 missing sidecar
    with pytest.raises(layout_migration.PreflightGateError) as exc_sidecar:
        m0001_metadata_v2.run(wt_dir, apply=False, force=False, force_worktree=True)
    sidecar_msg = str(exc_sidecar.value)
    assert "SIDECAR" in sidecar_msg or "sidecar" in sidecar_msg.lower()
    assert "history.jsonl" in sidecar_msg
    assert _snapshot_tree(wt_dir) == before_wt
    assert not (repo / ".aw" / "state" / "durable" / "migrations" / "m0001").exists()

    # None from checkout_git_common_dir refuses even with force=True, force_worktree=True
    monkeypatch.setattr(ipd_lifecycle, "checkout_git_common_dir", lambda _p: None)
    with pytest.raises(layout_migration.PreflightGateError) as exc_none_common:
        m0001_metadata_v2.run(repo, apply=False, force=True, force_worktree=True)
    assert "cannot establish the common directory" in str(exc_none_common.value)


def test_preflight_force_worktree_in_main_checkout_still_refuses_uncommitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-27 case (4): --force-worktree in main checkout does not override UNCOMMITTED."""
    repo = _init_repo(tmp_path, monkeypatch)
    bk = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-demo-01-bk0001-sample-item.backlog.md"
    )
    bk.write_text(bk.read_text(encoding="utf-8") + "\nDirty\n", encoding="utf-8")
    before = _snapshot_tree(repo)

    with pytest.raises(layout_migration.PreflightGateError) as exc_info:
        m0001_metadata_v2.run(repo, apply=False, force=False, force_worktree=True)
    assert "UNCOMMITTED" in str(exc_info.value)
    assert _snapshot_tree(repo) == before


# --------------------------------------------------------------------------------------
# Journal lifecycle (E-03): dry-run isolation, interrupt-mid-apply, resume, rollback
# --------------------------------------------------------------------------------------


def test_journal_dry_run_isolation_and_chain_delegation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch)
    before = _snapshot_tree(repo)

    # Delegate through chain.MIGRATIONS[0].run
    report = chain.MIGRATIONS[0].run(repo, apply=False)
    assert report["status"] == "dry_run"
    assert report["dry_run"] is True

    # Git status must stay clean; tracked files byte-identical; layout journal untouched
    st = _git(repo, "status", "--porcelain")
    assert st.stdout.strip() == ""
    for rel, content in before.items():
        assert (repo / rel).read_bytes() == content

    journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
    assert (journal_dir / "journal.json").is_file()
    assert (journal_dir / "scratch" / "records").is_dir()
    assert not (journal_dir / "writer.lock").exists()
    assert not (
        repo
        / ".aw"
        / "state"
        / "runtime"
        / "transactions"
        / "migration_transaction.json"
    ).exists()

    journal = json.loads((journal_dir / "journal.json").read_text(encoding="utf-8"))
    for key in (
        "minted_ids",
        "rename_map",
        "steps",
        "applied_files",
        "descriptions",
        "orphan_export_path",
        "orphan_counts",
        "terminal_commit_marker",
    ):
        assert key in journal
    assert journal["terminal_commit_marker"] is None


def test_journal_interrupt_mid_apply_resume_and_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Uninterrupted reference repo
    ref_repo = _init_repo(tmp_path, monkeypatch, name="ref_repo")
    ref_res = m0001_metadata_v2.run(ref_repo, apply=True, commit=False)
    assert ref_res["status"] == "applied"
    ref_gitignore_bytes = (ref_repo / ".aw" / ".gitignore").read_bytes()
    assert not (ref_repo / ".aw" / "records" / "history.jsonl").exists()

    # Interrupted repo -> resume via run(apply=True)
    repo_a = _init_repo(tmp_path, monkeypatch, name="repo_a")
    orig_a_sidecar = (repo_a / ".aw" / "records" / "history.jsonl").read_bytes()
    orig_a_gitignore = (repo_a / ".aw" / ".gitignore").read_bytes()

    with pytest.raises(layout_migration.MigrationError, match="interrupt-mid-apply"):
        m0001_metadata_v2.run(
            repo_a, apply=True, fault_injection="interrupt-mid-apply", commit=False
        )

    jpath_a = (
        repo_a / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    jdata_a = json.loads(jpath_a.read_text(encoding="utf-8"))
    assert jdata_a["status"] == "applying"
    assert len(jdata_a["applied_files"]) == 1
    assert (repo_a / ".aw" / ".gitignore").read_bytes() == orig_a_gitignore

    resumed_a = m0001_metadata_v2.run(repo_a, apply=True, commit=False)
    assert resumed_a["status"] == "applied"
    assert resumed_a["resumed"] is True
    assert (repo_a / ".aw" / ".gitignore").read_bytes() == ref_gitignore_bytes
    assert not (repo_a / ".aw" / "records" / "history.jsonl").exists()

    # Rollback restores pre-apply bytes byte-for-byte
    rb_a = m0001_metadata_v2.rollback(repo_a)
    assert rb_a["status"] == "rolled_back"
    assert (repo_a / ".aw" / "records" / "history.jsonl").read_bytes() == orig_a_sidecar
    assert (repo_a / ".aw" / ".gitignore").read_bytes() == orig_a_gitignore
    assert not (
        repo_a
        / ".aw"
        / "state"
        / "durable"
        / "migrations"
        / "m0001"
        / "history.jsonl.imported"
    ).exists()

    # Explicit resume(repo) also completes an interrupted run identically
    repo_b = _init_repo(tmp_path, monkeypatch, name="repo_b")
    with pytest.raises(layout_migration.MigrationError, match="interrupt-mid-apply"):
        m0001_metadata_v2.run(
            repo_b, apply=True, fault_injection="interrupt-mid-apply", commit=False
        )
    resumed_b = m0001_metadata_v2.resume(repo_b, commit=False)
    assert resumed_b["status"] == "applied"
    assert (repo_b / ".aw" / ".gitignore").read_bytes() == ref_gitignore_bytes
    assert (
        hashlib.sha256((repo_b / ".aw" / ".gitignore").read_bytes()).hexdigest()
        == hashlib.sha256(ref_gitignore_bytes).hexdigest()
    )


def test_stage_scratch_ignores_lock_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_stage_scratch skips *.lock files such as runs/integration.lock so Windows mandatory locks never fail copytree."""
    repo = _init_repo(tmp_path, monkeypatch, name="lock_ignore")
    runs_dir = repo / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    lock_file = runs_dir / "integration.lock"
    lock_file.write_text("held\n", encoding="utf-8")

    scratch_dir = tmp_path / "scratch"
    m0001_metadata_v2._stage_scratch(repo, repo / ".aw" / "records", scratch_dir)

    assert not (
        scratch_dir / "repo" / ".aw" / "records" / "runs" / "integration.lock"
    ).exists()
    assert not (scratch_dir / "records" / "runs" / "integration.lock").exists()
