"""Tests for artifact_meta write path, operation journal, failure injection, and repair.

IPD tve77h / E-15, E-16.
Validates V-15 (-k "append or create or inject") and V-16 (-k "repair or diverge or merge").
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import pytest

from agent_workflows import artifact_core as core
from agent_workflows import artifact_meta as meta


pytestmark = pytest.mark.core


def _init_git_repo(repo_dir: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )


# --------------------------------------------------------------------------------------
# E-15 & V-15: Append, Create, and Failure Injection (-k "append or create or inject")
# --------------------------------------------------------------------------------------


def test_append_consecutive_seq_and_single_append_metadata(tmp_path: Path):
    """Appending 3 events assigns consecutive seq, one append, one at, and one actor across all 3."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Step 1: Create initial plan
    meta.create(
        "app001",
        "ipd",
        {"status": "draft", "set": "metastore", "order": 1},
        "# Plan Title\nBody\n",
        destination="plans/pending/app001.ipd.md",
        project_context=ctx,
    )

    # Step 2: Append 3 note events together
    events = [
        {"op": "note", "message": "note 1"},
        {"op": "note", "message": "note 2"},
        {"op": "note", "message": "note 3"},
    ]
    res = meta.append("app001", events, expect_seq=1, project_context=ctx)
    assert res["committed"] is True

    # Read log
    log_p = records_root / "meta" / "app001.jsonl"
    lines = log_p.read_text(encoding="utf-8").splitlines(keepends=True)
    assert len(lines) == 4

    evs = [meta.decode_line(line) for line in lines[1:]]
    assert len(evs) == 3

    # Consecutive seq
    assert [e["seq"] for e in evs] == [2, 3, 4]

    # Single append value (the seq of the first event in the append = 2)
    assert evs[0]["append"] == 2
    assert evs[1]["append"] == 2
    assert evs[2]["append"] == 2

    # Same at timestamp
    assert evs[0]["at"] == evs[1]["at"] == evs[2]["at"]

    # Same actor
    assert evs[0]["actor"] == evs[1]["actor"] == evs[2]["actor"]


def test_append_dry_run(tmp_path: Path):
    """dry_run=True returns prepared events without writing to disk."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    res = meta.append(
        "dry001",
        [
            {
                "op": "create",
                "path": "plans/pending/dry001.ipd.md",
                "fields": {"id": "dry001", "type": "ipd", "status": "draft"},
            }
        ],
        dry_run=True,
        project_context=ctx,
    )
    assert res["committed"] is False
    assert res["dry_run"] is True
    assert len(res["events"]) == 1

    log_p = records_root / "meta" / "dry001.jsonl"
    assert not log_p.exists()


def test_append_optimistic_concurrency(tmp_path: Path):
    """expect_seq mismatch raises ValueError."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    meta.create(
        "opt001",
        "ipd",
        {"status": "draft"},
        "# Body\n",
        project_context=ctx,
    )

    with pytest.raises(ValueError, match="optimistic concurrency failure"):
        meta.append(
            "opt001",
            [{"op": "note", "message": "msg"}],
            expect_seq=999,
            project_context=ctx,
        )


def test_create_record_and_recovery_journal(tmp_path: Path):
    """create writes operation journal before commit point and clears on success."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    res = meta.create(
        "crt001",
        "ipd",
        {"status": "draft", "set": "test", "order": 1},
        "# Created Plan Body\n",
        destination="plans/pending/crt001.ipd.md",
        project_context=ctx,
    )
    assert res["committed"] is True

    # Log exists
    log_p = records_root / "meta" / "crt001.jsonl"
    assert log_p.exists()

    # Mirror body exists
    doc_p = records_root / "plans" / "pending" / "crt001.ipd.md"
    assert doc_p.exists()
    assert "Created Plan Body" in doc_p.read_text(encoding="utf-8")

    # Journal is cleared on success
    j_p = state_root / "operation_journal" / "crt001.json"
    assert not j_p.exists()


def test_inject_failure_before_commit_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Injected failure before step 1 leaves every file byte-identical and reports no change."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    meta.create(
        "inj001",
        "ipd",
        {"status": "draft"},
        "# Body\n",
        destination="plans/pending/inj001.ipd.md",
        project_context=ctx,
    )

    log_p = records_root / "meta" / "inj001.jsonl"
    orig_log_bytes = log_p.read_bytes()

    # Inject failure into _atomic_replace_fsync (commit point step 1)
    def broken_fsync(path, content):
        raise OSError("injected disk failure before fsync commit")

    monkeypatch.setattr(meta, "_atomic_replace_fsync", broken_fsync)

    res = meta.append(
        "inj001",
        [{"op": "transition", "from": "draft", "to": "to-review"}],
        project_context=ctx,
    )
    assert res["committed"] is False
    assert "no change" in res["error"]

    # File remains byte-identical
    assert log_p.read_bytes() == orig_log_bytes


def test_inject_failure_after_commit_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Injected failure after step 1 leaves events committed and names repair."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    meta.create(
        "inj002",
        "ipd",
        {"status": "draft"},
        "# Body\n",
        destination="plans/pending/inj002.ipd.md",
        project_context=ctx,
    )

    # Inject failure into atomic_write (step 2 mirror update)
    def broken_atomic_write(path, text):
        raise RuntimeError("injected mirror write failure")

    monkeypatch.setattr(core, "atomic_write", broken_atomic_write)

    res = meta.append(
        "inj002",
        [{"op": "transition", "from": "draft", "to": "to-review"}],
        project_context=ctx,
    )
    assert res["committed"] is True
    assert "run repair" in res["warning"]

    # Log was committed
    log_p = records_root / "meta" / "inj002.jsonl"
    lines = log_p.read_text(encoding="utf-8").splitlines(keepends=True)
    assert len(lines) == 2
    assert meta.decode_line(lines[1])["op"] == "transition"


def test_inject_failure_before_commit_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Failure before commit in create leaves no log or doc file."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    def broken_fsync(path, content):
        raise OSError("disk full")

    monkeypatch.setattr(meta, "_atomic_replace_fsync", broken_fsync)

    res = meta.create(
        "inj003",
        "ipd",
        {"status": "draft"},
        "# Body\n",
        destination="plans/pending/inj003.ipd.md",
        project_context=ctx,
    )
    assert res["committed"] is False
    assert "no change" in res["error"]

    log_p = records_root / "meta" / "inj003.jsonl"
    assert not log_p.exists()
    doc_p = records_root / "plans" / "pending" / "inj003.ipd.md"
    assert not doc_p.exists()


def test_inject_failure_after_commit_create_blocks_subsequent_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Failure after commit in create leaves journal, refusing subsequent mutation until repair."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    def broken_write_body(dest_path, text):
        raise OSError("mirror write error")

    monkeypatch.setattr(core, "atomic_write", broken_write_body)

    with pytest.raises(OSError, match="mirror write error"):
        meta.create(
            "inj004",
            "ipd",
            {"status": "draft"},
            "# Body\n",
            destination="plans/pending/inj004.ipd.md",
            project_context=ctx,
        )

    # Journal exists
    j_p = state_root / "operation_journal" / "inj004.json"
    assert j_p.exists()

    # Subsequent mutation is refused
    with pytest.raises(RuntimeError, match="recovery is pending; run repair first"):
        meta.append("inj004", [{"op": "note", "message": "msg"}], project_context=ctx)


# --------------------------------------------------------------------------------------
# E-16 & V-16: Repair, Divergence, and Merge (-k "repair or diverge or merge")
# --------------------------------------------------------------------------------------


def test_repair_idempotent_double_repair(tmp_path: Path):
    """Calling repair twice yields the same bytes (idempotent)."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    meta.create(
        "rep001",
        "ipd",
        {"status": "draft"},
        "# Body Heading\nBody text\n",
        destination="plans/pending/rep001.ipd.md",
        project_context=ctx,
    )

    doc_p = records_root / "plans" / "pending" / "rep001.ipd.md"
    log_p = records_root / "meta" / "rep001.jsonl"

    # Repair 1
    rep1 = meta.repair("rep001", project_context=ctx)
    assert rep1["repaired"] is True
    log_bytes_1 = log_p.read_bytes()
    doc_bytes_1 = doc_p.read_bytes()

    # Repair 2
    rep2 = meta.repair("rep001", project_context=ctx)
    assert rep2["repaired"] is True
    log_bytes_2 = log_p.read_bytes()
    doc_bytes_2 = doc_p.read_bytes()

    assert log_bytes_1 == log_bytes_2
    assert doc_bytes_1 == doc_bytes_2


def test_repair_missing_body_refusal(tmp_path: Path):
    """Create repair whose journaled body is missing is refused naming missing recovery source."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    j_dir = state_root / "operation_journal"
    j_dir.mkdir(parents=True)
    j_p = j_dir / "rep002.json"
    j_p.write_text(
        json.dumps(
            {
                "op": "create",
                "id6": "rep002",
                "destination": "plans/pending/rep002.ipd.md",
                "body": "",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="missing recovery source"):
        meta.repair("rep002", project_context=ctx)


def test_repair_pending_create_journal(tmp_path: Path):
    """Repair restores pending create body from journal."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Initial log exists
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True)
    log_p = meta_dir / "rep003.jsonl"
    log_p.write_text(
        meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-06T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": "plans/pending/rep003.ipd.md",
                "fields": {"id": "rep003", "type": "ipd", "status": "draft"},
            }
        ),
        encoding="utf-8",
    )

    # Retain journal with body
    j_dir = state_root / "operation_journal"
    j_dir.mkdir(parents=True)
    j_p = j_dir / "rep003.json"
    j_p.write_text(
        json.dumps(
            {
                "op": "create",
                "id6": "rep003",
                "destination": "plans/pending/rep003.ipd.md",
                "body": "# Recovered Body\n",
            }
        ),
        encoding="utf-8",
    )

    rep = meta.repair("rep003", project_context=ctx)
    assert rep["repaired"] is True

    doc_p = records_root / "plans" / "pending" / "rep003.ipd.md"
    assert doc_p.exists()
    assert "Recovered Body" in doc_p.read_text(encoding="utf-8")
    assert not j_p.exists()


def test_repair_git_merge_two_branch_divergence(tmp_path: Path):
    """Real two-branch git merge fixture with diverged tail resequences cleanly after confirmed repair (AC-17)."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_git_repo(repo_dir)

    records_root = repo_dir / ".aw" / "records"
    state_root = repo_dir / ".aw" / "state"
    records_root.mkdir(parents=True)
    state_root.mkdir(parents=True)
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Base commit on main: plan at seq 1
    meta.create(
        "mrg001",
        "ipd",
        {"status": "draft", "set": "test", "order": 1},
        "# Merge Plan Body\n",
        destination="plans/pending/mrg001.ipd.md",
        project_context=ctx,
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base commit (seq 1)"], cwd=repo_dir, check=True
    )

    # Branch A: appends note event at seq 2
    subprocess.run(["git", "checkout", "-b", "branch-a"], cwd=repo_dir, check=True)
    meta.append(
        "mrg001",
        [{"op": "note", "message": "branch A note"}],
        expect_seq=1,
        project_context=ctx,
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "branch A append"], cwd=repo_dir, check=True)

    # Branch B: starts from main, appends different note event at seq 2
    subprocess.run(["git", "checkout", "main"], cwd=repo_dir, check=True)
    subprocess.run(["git", "checkout", "-b", "branch-b"], cwd=repo_dir, check=True)
    meta.append(
        "mrg001",
        [{"op": "note", "message": "branch B note"}],
        expect_seq=1,
        project_context=ctx,
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "branch B append"], cwd=repo_dir, check=True)

    # Merge branch-a into branch-b
    # Git merge creates diverged log with duplicate seq 2 (e.g. union merge or manual concatenate)
    # Simulate merged log with both appends concatenated
    log_p = records_root / "meta" / "mrg001.jsonl"
    lines_b = log_p.read_text(encoding="utf-8").splitlines(keepends=True)
    git_show_a = subprocess.run(
        ["git", "show", "branch-a:.aw/records/meta/mrg001.jsonl"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    lines_a = git_show_a.stdout.splitlines(keepends=True)

    # Combined log has seq 1 (base), seq 2 (branch A), seq 2 (branch B)
    merged_lines = [lines_a[0], lines_a[1], lines_b[1]]
    log_p.write_text("".join(merged_lines), encoding="utf-8")

    # Replay/read fails due to duplicate seq 2
    with pytest.raises(ValueError, match="duplicate.*2"):
        meta.read("mrg001", project_context=ctx)

    # Unconfirmed repair reports divergence
    rep_unconfirmed = meta.repair("mrg001", confirm=False, project_context=ctx)
    assert rep_unconfirmed["diverged"] is True
    assert rep_unconfirmed["repaired"] is False

    # Confirmed repair resolves divergence
    rep_confirmed = meta.repair("mrg001", confirm=True, project_context=ctx)
    assert rep_confirmed["repaired"] is True
    assert rep_confirmed["seq"] == 3

    # Winning prefix (seq 1..2) is preserved; tail event is renumbered to seq 3
    final_lines = log_p.read_text(encoding="utf-8").splitlines(keepends=True)
    assert len(final_lines) == 3
    ev0 = meta.decode_line(final_lines[0])
    ev1 = meta.decode_line(final_lines[1])
    ev2 = meta.decode_line(final_lines[2])

    assert ev0["seq"] == 1
    assert ev1["seq"] == 2
    assert ev2["seq"] == 3

    # read() now succeeds
    st = meta.read("mrg001", project_context=ctx)
    assert st.id6 == "mrg001"
    assert st.valid == 1
