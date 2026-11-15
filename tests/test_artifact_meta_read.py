"""Tests for artifact_meta read operations, query planner, and git read_at.

IPD tve77h / E-13, E-14.
Validates V-13 (-k "read or query or incomplete") and V-14 (-k read_at).
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess
import pytest

from agent_workflows import artifact_meta as meta


pytestmark = pytest.mark.core


# --------------------------------------------------------------------------------------
# Helper to initialize records
# --------------------------------------------------------------------------------------


def _create_plan_log(
    records_root: Path,
    id6: str,
    status: str = "draft",
    set_id: str = "test",
    order_nn: int = 1,
    depends_on: str | None = None,
    path: str | None = None,
) -> Path:
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    log_p = meta_dir / f"{id6}.jsonl"
    p = path or f"plans/pending/{id6}.ipd.md"
    fields = {
        "id": id6,
        "type": "ipd",
        "status": "draft",
        "set": set_id,
        "order": order_nn,
    }
    if depends_on:
        fields["item_dependencies"] = f"executed:{depends_on}"

    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": p,
            "fields": fields,
        }
    ]
    cur = "draft"
    seq = 2
    ladder = ["draft", "to-review", "reviewed", "approved", "executed"]
    if status in ladder:
        idx = ladder.index(status)
        for target in ladder[1 : idx + 1]:
            events.append(
                {
                    "v": 1,
                    "seq": seq,
                    "append": seq,
                    "at": f"2026-11-06T12:0{seq}:00Z",
                    "actor": {"tool": "test"},
                    "op": "transition",
                    "from": cur,
                    "to": target,
                }
            )
            cur = target
            seq += 1

    log_p.write_text("".join(meta.encode_event(e) for e in events), encoding="utf-8")
    return log_p


# --------------------------------------------------------------------------------------
# E-13 & V-13: Read functions, Query, and Incomplete Reporting (-k "read or query or incomplete")
# --------------------------------------------------------------------------------------


def test_read_valid_record(tmp_path: Path):
    """read(id6) returns current State."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_plan_log(records_root, "rd0001", "approved", "metastore", 1)
    st = meta.read("rd0001", project_context=ctx)
    assert st.id6 == "rd0001"
    assert st.status == "approved"
    assert st.set_id == "metastore"
    assert st.order_nn == 1
    assert st.valid == 1


def test_read_absent_record_fails_closed(tmp_path: Path):
    """read(id6) fails closed on absent record."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    with pytest.raises(ValueError, match="artifact not found"):
        meta.read("abs001", project_context=ctx)


def test_read_invalid_record_fails_closed(tmp_path: Path):
    """read(id6) fails closed on invalid record."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Corrupt log
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True)
    (meta_dir / "bad001.jsonl").write_text("not-json-line\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid record"):
        meta.read("bad001", project_context=ctx)


def test_history_event_log(tmp_path: Path):
    """history(id6) returns ordered events."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_plan_log(records_root, "hst001", "approved")
    hist = meta.history("hst001", project_context=ctx)
    assert len(hist) == 4
    assert [e["seq"] for e in hist] == [1, 2, 3, 4]
    assert hist[0]["op"] == "create"
    assert hist[-1]["op"] == "transition"
    assert hist[-1]["to"] == "approved"


def test_resolve_path_and_id6(tmp_path: Path):
    """resolve(path_or_id6) resolves canonical path."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_plan_log(
        records_root,
        "res001",
        "draft",
        path="plans/pending/20261102-test-01-res001-slug.ipd.md",
    )
    p1 = meta.resolve("res001", project_context=ctx)
    assert p1 == "plans/pending/20261102-test-01-res001-slug.ipd.md"

    p2 = meta.resolve(
        "plans/pending/20261102-test-01-res001-slug.ipd.md", project_context=ctx
    )
    assert p2 == "plans/pending/20261102-test-01-res001-slug.ipd.md"


def test_query_filters(tmp_path: Path):
    """query(...) applies typed filters for status, set_id, depends_on, latest_gate_review_of, path."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Plan 1: metastore, approved
    _create_plan_log(
        records_root,
        "qpln01",
        "approved",
        "metastore",
        1,
        path="plans/executed/qpln01.ipd.md",
    )
    # Plan 2: metastore, draft, depends on qpln01
    _create_plan_log(
        records_root,
        "qpln02",
        "draft",
        "metastore",
        2,
        depends_on="qpln01",
        path="plans/pending/qpln02.ipd.md",
    )
    # Plan 3: other, draft
    _create_plan_log(
        records_root, "qpln03", "draft", "other", 1, path="plans/pending/qpln03.ipd.md"
    )

    # Add review file for qpln01
    rev_dir = records_root / "reviews"
    rev_dir.mkdir(parents=True)
    rev_f = rev_dir / "20261102-test-01-rev001-qpln01-review.review.md"
    rev_f.write_text(
        "# Review\n\n- Subject-Id: qpln01\n- Verdict: APPROVE\n\n## Round 1\n",
        encoding="utf-8",
    )

    # 1. status and set_id filter
    r1 = meta.query(project_context=ctx, status="approved", set_id="metastore")
    assert len(r1) == 1
    assert r1[0].id6 == "qpln01"

    # 2. depends_on filter
    r2 = meta.query(project_context=ctx, depends_on="qpln01")
    assert len(r2) == 1
    assert r2[0].id6 == "qpln02"

    # 3. path filter
    r3 = meta.query(project_context=ctx, path="plans/executed/qpln01.ipd.md")
    assert len(r3) == 1
    assert r3[0].id6 == "qpln01"

    # 4. latest_gate_review_of filter
    r4 = meta.query(project_context=ctx, latest_gate_review_of="qpln01")
    assert len(r4) == 1
    assert r4[0].id6 == "qpln01"


def test_query_incomplete_reporting(tmp_path: Path):
    """One invalid record in a 3-record fixture yields 2 rows and incomplete == [<id6>]."""
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_plan_log(records_root, "ok0001", "draft")
    _create_plan_log(records_root, "ok0002", "draft")

    # Corrupt log for third record
    meta_dir = records_root / "meta"
    (meta_dir / "cor001.jsonl").write_text("invalid json line\n", encoding="utf-8")

    q = meta.query(project_context=ctx)
    assert len(q) == 2
    assert sorted([r.id6 for r in q]) == ["ok0001", "ok0002"]
    assert q.incomplete == ["cor001"]


def test_query_explain_query_plan_indexes(tmp_path: Path):
    """EXPLAIN QUERY PLAN for the four indexed queries name indexes (AC-23 (3))."""
    records_root = tmp_path / "records"
    records_root.mkdir()
    conn = sqlite3.connect(":memory:")
    meta.init_cache(conn, records_root)

    # Populate rows and run ANALYZE so query optimizer chooses indexes
    for i in range(100):
        id_str = f"id{i:04d}"
        conn.execute(
            "INSERT INTO artifacts (id6, status, set_id, order_nn, valid) VALUES (?, ?, ?, ?, 1)",
            (id_str, "approved" if i % 2 == 0 else "draft", f"set{i % 5}", i),
        )
        conn.execute(
            "INSERT INTO dependencies (dependent_id6, ordinal, target_id6) VALUES (?, 1, ?)",
            (id_str, f"id{(i + 1):04d}"),
        )
        conn.execute(
            "INSERT INTO reviews (subject_id6, seq, review_kind) VALUES (?, 1, ?)",
            (id_str, "gate" if i % 2 == 0 else "refinement"),
        )
        conn.execute(
            "INSERT INTO artifact_paths (id6, seq, path) VALUES (?, ?, ?)",
            (id_str, 1, f"path/{i}.md"),
        )
    conn.execute("ANALYZE")

    # 1. query(status=..., set_id=...)
    qp1 = conn.execute(
        """EXPLAIN QUERY PLAN
           SELECT a.id6 FROM artifacts a
           WHERE a.valid = 1 AND a.status = ? AND a.set_id = ?
           ORDER BY a.set_id, a.order_nn, a.id6""",
        ("approved", "set1"),
    ).fetchall()
    qp1_text = " ".join(r[3] for r in qp1)
    assert "USING INDEX idx_artifacts_set_order" in qp1_text

    # 2. query(depends_on=X)
    qp2 = conn.execute(
        """EXPLAIN QUERY PLAN
           SELECT a.id6 FROM artifacts a
           WHERE a.valid = 1 AND EXISTS (
               SELECT 1 FROM dependencies d WHERE d.dependent_id6 = a.id6 AND d.target_id6 = ?
           )""",
        ("id0005",),
    ).fetchall()
    qp2_text = " ".join(r[3] for r in qp2)
    assert "USING INDEX idx_dependencies_target_id6" in qp2_text

    # 3. query(latest_gate_review_of=X)
    qp3 = conn.execute(
        """EXPLAIN QUERY PLAN
           SELECT a.id6 FROM artifacts a
           WHERE a.valid = 1 AND EXISTS (
               SELECT 1 FROM reviews r WHERE r.subject_id6 = a.id6 AND r.subject_id6 = ? AND r.review_kind = 'gate'
           )""",
        ("id0005",),
    ).fetchall()
    qp3_text = " ".join(r[3] for r in qp3)
    assert (
        "USING COVERING INDEX idx_reviews_subject_kind_seq" in qp3_text
        or "USING INDEX idx_reviews_subject_kind_seq" in qp3_text
    )

    # 4. query(path=P)
    qp4 = conn.execute(
        """EXPLAIN QUERY PLAN
           SELECT a.id6 FROM artifacts a
           WHERE a.valid = 1 AND EXISTS (
               SELECT 1 FROM artifact_paths ap WHERE ap.id6 = a.id6 AND ap.path = ?
           )""",
        ("path/5.md",),
    ).fetchall()
    qp4_text = " ".join(r[3] for r in qp4)
    assert "USING INDEX idx_artifact_paths_path" in qp4_text

    conn.close()


# --------------------------------------------------------------------------------------
# E-14 & V-14: Git read_at (-k read_at)
# --------------------------------------------------------------------------------------


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


def test_read_at_rename_case(tmp_path: Path):
    """read_at(id6, 'HEAD~1') returns old metadata from old path after rename commit."""
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

    # Commit 1: Plan at old path in approved status (seq 1..4)
    log_p = _create_plan_log(
        records_root, "rn0001", "approved", path="plans/pending/rn0001.ipd.md"
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_dir, check=True)

    # Commit 2: Transition from approved to executed at new path (seq 5)
    ev2 = {
        "v": 1,
        "seq": 5,
        "append": 5,
        "at": "2026-11-06T12:05:00Z",
        "actor": {"tool": "test"},
        "op": "transition",
        "from": "approved",
        "to": "executed",
        "path": "plans/executed/rn0001.ipd.md",
    }
    with open(log_p, "a", encoding="utf-8") as f:
        f.write(meta.encode_event(ev2))
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "rename commit"], cwd=repo_dir, check=True)

    # read_at HEAD~1
    res1 = meta.read_at("rn0001", "HEAD~1", project_context=ctx)
    assert res1.kind == "ok"
    assert res1.state is not None
    assert res1.state.status == "approved"
    assert res1.state.path == "plans/pending/rn0001.ipd.md"

    # read_at HEAD
    res2 = meta.read_at("rn0001", "HEAD", project_context=ctx)
    assert res2.kind == "ok"
    assert res2.state is not None
    assert res2.state.status == "executed"
    assert res2.state.path == "plans/executed/rn0001.ipd.md"


def test_read_at_invalid_revision_vs_absent_record(tmp_path: Path):
    """read_at returns distinct kinds for invalid-revision vs absent record."""
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

    _create_plan_log(records_root, "ex0001", "draft")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "commit 1"], cwd=repo_dir, check=True)

    # 1. Invalid revision
    r_inv = meta.read_at("ex0001", "nosuchrev", project_context=ctx)
    assert r_inv.kind == "invalid-revision"

    # 2. Absent record
    r_abs = meta.read_at("abs999", "HEAD", project_context=ctx)
    assert r_abs.kind == "absent"


def test_read_at_companion_backend(tmp_path: Path):
    """Companion fixture reads blobs from companion records repository."""
    companion_repo = tmp_path / "companion"
    companion_repo.mkdir()
    _init_git_repo(companion_repo)

    state_root = tmp_path / "state"
    state_root.mkdir()
    records_root = companion_repo  # root of companion repo is records root

    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_plan_log(records_root, "cmp001", "approved")
    subprocess.run(["git", "add", "."], cwd=companion_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "companion commit"], cwd=companion_repo, check=True
    )

    r = meta.read_at("cmp001", "HEAD", project_context=ctx)
    assert r.kind == "ok"
    assert r.state is not None
    assert r.state.id6 == "cmp001"
    assert r.state.status == "approved"


def test_read_at_unversioned(tmp_path: Path):
    """read_at returns unversioned kind when records_root is not in a git repo."""
    records_root = tmp_path / "not_a_git_repo" / "records"
    state_root = tmp_path / "state"
    records_root.mkdir(parents=True)
    state_root.mkdir()

    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()
    _create_plan_log(records_root, "unv001", "draft")

    r = meta.read_at("unv001", "HEAD", project_context=ctx)
    assert r.kind == "unversioned"


def test_read_at_corrupt_blob(tmp_path: Path):
    """Corrupt blob fails closed, returns corrupt kind, and leaves no rev_log_states row (AC-33)."""
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

    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True)
    log_p = meta_dir / "crp001.jsonl"
    log_p.write_text('{"v": 1, "seq": 999, "corrupt": true}\n', encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "corrupt commit"], cwd=repo_dir, check=True)

    r = meta.read_at("crp001", "HEAD", project_context=ctx)
    assert r.kind == "corrupt"

    # Verify no row in rev_log_states
    conn = meta.open_cache(records_root, state_root)
    cached_rows = conn.execute("SELECT * FROM rev_log_states").fetchall()
    conn.close()
    assert len(cached_rows) == 0


def _legacy_repo(tmp_path: Path) -> tuple[Path, object]:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_git_repo(repo_dir)
    records_root = repo_dir / ".aw" / "records"
    state_root = repo_dir / ".aw" / "state"
    (records_root / "plans" / "pending").mkdir(parents=True)
    state_root.mkdir(parents=True)
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()
    return repo_dir, ctx


def _legacy_plan_text(id6: str, status: str) -> str:
    return (
        f"# IPD: Legacy plan {id6}\n\n- Id: {id6}\n- Status: {status}\n"
        "- Set: legacy\n\n## Concern\n\nA phase-B record with no meta log.\n"
    )


def test_read_at_finds_a_phase_b_legacy_record(tmp_path: Path):
    """A record with no meta log is read from its Markdown file at the revision."""
    repo_dir, ctx = _legacy_repo(tmp_path)
    plan = (
        repo_dir
        / ".aw/records/plans/pending/20261101-legacy-01-lg0001-legacy-plan.ipd.md"
    )
    plan.write_text(_legacy_plan_text("lg0001", "approved"), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-qm", "legacy"], cwd=repo_dir, check=True)

    plan.write_text(_legacy_plan_text("lg0001", "executed"), encoding="utf-8")

    res = meta.read_at("lg0001", "HEAD", project_context=ctx)
    assert res.kind == "ok", res.error
    assert res.state is not None
    assert res.state.id6 == "lg0001"
    assert res.state.status == "approved"
    assert res.state.path == (
        "plans/pending/20261101-legacy-01-lg0001-legacy-plan.ipd.md"
    )


def test_read_at_ignores_quoted_ids_and_files_outside_the_records_root(
    tmp_path: Path,
):
    """Only a records file whose own `- Id:` line is the id6 counts as the record."""
    repo_dir, ctx = _legacy_repo(tmp_path)
    (repo_dir / "NOTES.md").write_text("- Id: lg0002\n", encoding="utf-8")
    quoting = repo_dir / ".aw/records/plans/pending/20261101-legacy-02-qt0001-q.ipd.md"
    quoting.write_text(
        _legacy_plan_text("qt0001", "draft") + "\n  - Id: lg0002\n- Id: lg00021\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-qm", "quotes"], cwd=repo_dir, check=True)

    res = meta.read_at("lg0002", "HEAD", project_context=ctx)
    assert res.kind == "absent"


def test_read_at_finds_a_phase_b_legacy_record_with_crlf_line_endings(tmp_path: Path):
    """A Phase B legacy record committed with CRLF line endings is still found by read_at."""
    repo_dir, ctx = _legacy_repo(tmp_path)
    subprocess.run(
        ["git", "config", "core.autocrlf", "false"], cwd=repo_dir, check=True
    )
    plan = (
        repo_dir
        / ".aw/records/plans/pending/20261101-legacy-01-cr0001-crlf-plan.ipd.md"
    )
    crlf_bytes = (
        _legacy_plan_text("cr0001", "approved").replace("\n", "\r\n").encode("utf-8")
    )
    plan.write_bytes(crlf_bytes)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-qm", "legacy crlf"], cwd=repo_dir, check=True)

    res = meta.read_at("cr0001", "HEAD", project_context=ctx)
    assert res.kind == "ok", res.error
    assert res.state is not None
    assert res.state.id6 == "cr0001"
    assert res.state.status == "approved"
