"""Tests for artifact_meta cache schema, placement, failure handling, and freshness.

IPD tve77h / E-08, E-09, E-10.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
import sqlite3
import pytest

from agent_workflows import artifact_meta as meta


pytestmark = pytest.mark.core


# --------------------------------------------------------------------------------------
# E-08 & V-08: Cache schema (-k schema)
# --------------------------------------------------------------------------------------


def test_cache_schema_tables(tmp_path: Path):
    records_root = tmp_path / "records"
    records_root.mkdir()
    conn = sqlite3.connect(":memory:")
    meta.init_cache(conn, records_root)

    tables = sorted(
        [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
    )
    conn.close()

    expected = sorted(list(meta.CACHE_TABLES_4_5A))
    assert tables == expected, f"expected tables {expected}, got {tables}"


def test_cache_schema_columns(tmp_path: Path):
    records_root = tmp_path / "records"
    records_root.mkdir()
    conn = sqlite3.connect(":memory:")
    meta.init_cache(conn, records_root)

    # Check columns for each per-type table
    for rtype in meta.SUPPORTED_TYPES:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({rtype})").fetchall()]
        assert "id6" in cols
        reg_fields = meta.registry_fields(rtype)
        for rf in reg_fields:
            assert rf in cols, f"expected column {rf!r} in table {rtype!r}"

    # Check meta table keys
    meta_keys = [r[0] for r in conn.execute("SELECT key FROM meta").fetchall()]
    assert "schema_hash" in meta_keys
    assert "records_root" in meta_keys
    assert "runs_root" in meta_keys
    assert "run_reader_version" in meta_keys

    conn.close()


def test_cache_schema_hash_change_rebuilds_new_column(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()

    # Step 1: Open initial cache
    conn1 = meta.open_cache(records_root, state_root)
    cols1 = [r[1] for r in conn1.execute("PRAGMA table_info(ipd)").fetchall()]
    assert "custom_new_field_xyz" not in cols1
    conn1.close()

    # Step 2: Copy registry and add a field
    custom_reg = copy.deepcopy(meta.REGISTRY)
    custom_reg["ipd"]["custom_new_field_xyz"] = meta.FieldDef(
        "custom_new_field_xyz", "string", "generic"
    )

    hash1 = meta.compute_schema_hash()
    hash2 = meta.compute_schema_hash(custom_reg)
    assert hash1 != hash2, "schema_hash must change when field is added to registry"

    # Step 3: Open cache with new registry; should rebuild automatically
    conn2 = meta.open_cache(records_root, state_root, registry=custom_reg)
    cols2 = [r[1] for r in conn2.execute("PRAGMA table_info(ipd)").fetchall()]
    conn2.close()

    assert "custom_new_field_xyz" in cols2, "rebuilt cache must have new column"


# --------------------------------------------------------------------------------------
# E-09 & V-09: Placement, corruption, and fallbacks (-k "placement or corrupt or fallback or companion")
# --------------------------------------------------------------------------------------


def _create_sample_record(
    records_root: Path, id6: str = "tst123", status: str = "approved"
) -> None:
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    log_p = meta_dir / f"{id6}.jsonl"
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": f"plans/pending/{id6}.ipd.md",
            "fields": {
                "status": "draft",
                "set": "test",
                "order": 1,
                "id": id6,
                "type": "ipd",
            },
        },
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
    elif status != "draft":
        events.append(
            {
                "v": 1,
                "seq": seq,
                "append": seq,
                "at": f"2026-11-06T12:0{seq}:00Z",
                "actor": {"tool": "test"},
                "op": "transition",
                "from": cur,
                "to": status,
            }
        )
    log_p.write_text("".join(meta.encode_event(e) for e in events), encoding="utf-8")


def test_cache_placement_and_parity(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()

    _create_sample_record(records_root, "par123", "approved")

    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # 1. Cold cache
    q_cold = meta.query(project_context=ctx, status="approved")
    assert len(q_cold) == 1
    assert q_cold[0].id6 == "par123"

    # 2. Warm cache
    q_warm = meta.query(project_context=ctx, status="approved")
    assert len(q_warm) == 1
    assert q_warm[0].id6 == "par123"

    # 3. Deleted index.db
    db_file = state_root / "index.db"
    assert db_file.exists()
    db_file.unlink()
    q_deleted = meta.query(project_context=ctx, status="approved")
    assert len(q_deleted) == 1
    assert q_deleted[0].id6 == "par123"

    # 4. Corrupted index.db (overwritten with random bytes)
    db_file.write_bytes(b"corrupted_junk_bytes_here" * 50)
    q_corrupt = meta.query(project_context=ctx, status="approved")
    assert len(q_corrupt) == 1
    assert q_corrupt[0].id6 == "par123"

    # 5. Unopenable cache path: index.db is a DIRECTORY (portable in-memory fallback)
    if db_file.exists():
        db_file.unlink()
    db_file.mkdir()  # makes index.db a directory
    q_fallback = meta.query(project_context=ctx, status="approved")
    assert len(q_fallback) == 1
    assert q_fallback[0].id6 == "par123"

    # Parity check across all 5 conditions
    assert (
        q_cold[0].id6
        == q_warm[0].id6
        == q_deleted[0].id6
        == q_corrupt[0].id6
        == q_fallback[0].id6
    )


def test_cache_companion_backend(tmp_path: Path):
    # Companion backend: records root is outside repository checkout
    product_repo = tmp_path / "product_repo"
    companion_records = tmp_path / "companion_records"
    state_root = product_repo / ".aw" / "state"

    product_repo.mkdir(parents=True)
    companion_records.mkdir(parents=True)
    state_root.mkdir(parents=True)

    _create_sample_record(companion_records, "cmp123", "approved")

    ctx = type(
        "Ctx",
        (),
        {"logical_roots": {"records": companion_records, "state": state_root}},
    )()
    q = meta.query(project_context=ctx, status="approved")
    assert len(q) == 1
    assert q[0].id6 == "cmp123"

    # Assert log path is under companion_records
    log_p = companion_records / "meta" / "cmp123.jsonl"
    assert log_p.exists()


# --------------------------------------------------------------------------------------
# E-10 & V-10: Freshness check (-k fresh)
# --------------------------------------------------------------------------------------


def test_freshness_file_added(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Start empty
    assert len(meta.query(project_context=ctx)) == 0

    # Add file
    _create_sample_record(records_root, "add123", "approved")
    q = meta.query(project_context=ctx, status="approved")
    assert len(q) == 1
    assert q[0].id6 == "add123"


def test_freshness_file_deleted(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_sample_record(records_root, "del123", "approved")
    assert len(meta.query(project_context=ctx)) == 1

    # Delete log file
    (records_root / "meta" / "del123.jsonl").unlink()
    assert len(meta.query(project_context=ctx)) == 0


def test_freshness_disposition_mv(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_sample_record(records_root, "mv1234", "approved")
    q1 = meta.query(project_context=ctx, id6="mv1234")
    assert len(q1) == 1
    assert q1[0].status == "approved"

    # Update log with transition to executed and path in executed/
    log_p = records_root / "meta" / "mv1234.jsonl"
    ev = {
        "v": 1,
        "seq": 5,
        "append": 5,
        "at": "2026-11-06T12:05:00Z",
        "actor": {"tool": "test"},
        "op": "transition",
        "from": "approved",
        "to": "executed",
        "path": "plans/executed/mv1234.ipd.md",
    }
    with open(log_p, "a", encoding="utf-8") as f:
        f.write(meta.encode_event(ev))

    # Next query should see executed status and path without explicit rebuild
    q2 = meta.query(project_context=ctx, status="executed")
    assert len(q2) == 1
    assert q2[0].id6 == "mv1234"
    assert q2[0].path == "plans/executed/mv1234.ipd.md"


def test_freshness_same_size_same_mtime_replacement(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    _create_sample_record(records_root, "sz1234", "draft")
    q1 = meta.query(project_context=ctx, status="draft")
    assert len(q1) == 1

    log_p = records_root / "meta" / "sz1234.jsonl"
    orig_stat = log_p.stat()

    # Modify a field while keeping EXACT same file size
    # Replace '"order":1' with '"order":2' (same length)
    old_text = log_p.read_text(encoding="utf-8")
    new_text = old_text.replace('"order":1', '"order":2')
    assert len(new_text) == len(old_text)
    log_p.write_text(new_text, encoding="utf-8")

    # Restore mtime
    os.utime(log_p, ns=(orig_stat.st_atime_ns, orig_stat.st_mtime_ns))
    cur_stat = log_p.stat()
    assert cur_stat.st_size == orig_stat.st_size
    assert cur_stat.st_mtime_ns == orig_stat.st_mtime_ns

    # Next query detects content change via SHA-256 digest
    q2 = meta.query(project_context=ctx, order=2)
    assert len(q2) == 1
    assert q2[0].id6 == "sz1234"


def test_freshness_dangling_target_appearing(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Plan A depends on Plan B ('tgt999'), but Plan B does not exist yet
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    log_a = meta_dir / "plna01.jsonl"
    ev_a = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": "plans/pending/plna01.ipd.md",
            "fields": {
                "id": "plna01",
                "type": "ipd",
                "status": "draft",
                "item_dependencies": "executed:tgt999",
            },
        }
    ]
    log_a.write_text("".join(meta.encode_event(e) for e in ev_a), encoding="utf-8")

    # Initially depends_on='tgt999' returns plna01
    q1 = meta.query(project_context=ctx, depends_on="tgt999")
    assert len(q1) == 1

    # Now Plan B appears
    _create_sample_record(records_root, "tgt999", "executed")
    q2 = meta.query(project_context=ctx, depends_on="tgt999")
    assert len(q2) == 1
    assert q2[0].id6 == "plna01"


def test_freshness_new_nested_directory(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    # Create new nested directory with a record
    nested_dir = records_root / "plans" / "custom" / "subdir"
    nested_dir.mkdir(parents=True)
    nested_file = nested_dir / "20261102-test-01-nst123-slug.ipd.md"
    nested_file.write_text(
        "---\n# Title\n- Id: nst123\n- Status: draft\n", encoding="utf-8"
    )

    q = meta.query(project_context=ctx, status="draft")
    assert any(st.id6 == "nst123" for st in q)


def test_open_cache_does_not_unlink_db_under_lock_contention(
    tmp_path: Path, monkeypatch
):
    import sqlite3

    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()
    _create_sample_record(records_root, "lck001", "draft")
    assert len(meta.query(project_context=ctx)) == 1

    db_path = state_root / "index.db"
    assert db_path.exists()
    original_inode = db_path.stat().st_ino

    holder = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        holder.execute("BEGIN EXCLUSIVE")
        monkeypatch.setattr(meta, "_SQLITE_CONNECT_TIMEOUT", 0.05)
        monkeypatch.setattr(meta, "_SQLITE_BUSY_TIMEOUT_MS", 50)
        monkeypatch.setattr(meta, "_CACHE_REFRESH_LOCK_TIMEOUT", 0.05)

        conn = meta.open_cache(records_root, state_root=state_root)
        try:
            assert conn is not None
        finally:
            conn.close()
    finally:
        holder.execute("ROLLBACK")
        holder.close()

    assert db_path.exists()
    assert db_path.stat().st_ino == original_inode


def test_freshness_detects_same_mtime_same_size_edit_within_racy_window(tmp_path: Path):
    import os

    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    plan_dir = records_root / "plans" / "pending"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "20261120-race-01-rac001-slug.ipd.md"
    content_a = "# IPD: Title A\n\n- Id: rac001\n- Status: draft\n"
    content_b = "# IPD: Title B\n\n- Id: rac001\n- Status: ready\n"
    assert len(content_a) == len(content_b)
    plan_file.write_text(content_a, encoding="utf-8")
    st_before = plan_file.stat()

    q1 = meta.query(project_context=ctx, id6="rac001")
    assert len(q1) == 1
    assert q1[0].status == "draft"

    plan_file.write_text(content_b, encoding="utf-8")
    os.utime(plan_file, ns=(st_before.st_atime_ns, st_before.st_mtime_ns))

    q2 = meta.query(project_context=ctx, id6="rac001")
    assert len(q2) == 1
    assert q2[0].status == "ready"


def test_check_freshness_concurrent_threads_no_lock_error(tmp_path: Path):
    import concurrent.futures

    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()
    for idx in range(10):
        _create_sample_record(records_root, f"thr{idx:03d}", "draft")

    def _worker(i: int) -> int:
        if i == 0:
            _create_sample_record(records_root, "thr999", "approved")
        return len(meta.query(project_context=ctx))

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        counts = list(pool.map(_worker, range(6)))

    assert all(c >= 10 for c in counts)
    assert any(st.id6 == "thr999" for st in meta.query(project_context=ctx))


def test_check_freshness_purges_existing_excluded_dir_rows_from_files_table(
    tmp_path: Path,
):
    import sqlite3

    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir()
    state_root.mkdir()
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()
    _create_sample_record(records_root, "exc001", "draft")
    excluded_file = records_root / "comms" / "README.md"
    excluded_file.parent.mkdir(parents=True)
    excluded_file.write_text("# Comms\n", encoding="utf-8")

    # Populate cache first, then inject a stale row for an existing file in an excluded dir.
    assert len(meta.query(project_context=ctx)) == 1
    db_path = state_root / "index.db"
    conn = sqlite3.connect(str(db_path))
    try:
        st = excluded_file.stat()
        conn.execute(
            "INSERT OR REPLACE INTO files (path, file_role, id6, size, mtime_ns, content_digest, loaded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "comms/README.md",
                "artifact",
                None,
                st.st_size,
                st.st_mtime_ns,
                "deadbeef",
                "2026-01-01T00:00:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Next query must purge the zombie row even though comms/README.md still exists on disk.
    assert len(meta.query(project_context=ctx)) == 1
    conn = sqlite3.connect(str(db_path))
    try:
        remaining = conn.execute(
            "SELECT path FROM files WHERE path = ?", ("comms/README.md",)
        ).fetchall()
    finally:
        conn.close()
    assert remaining == []
