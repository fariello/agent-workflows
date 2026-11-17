"""Cache shape parity and stable derived-identity tests for artifact_meta (IPD 6oi2nu).

Exercises the five-shape migration fixture corpus (`tests/migration_corpus.py`) through real
`artifact_meta`, `project_context`, `status_set`, and `artifact_core` calls.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_workflows import (
    artifact_core,
    artifact_meta,
    project_context,
    selectors,
    status_set,
)
from tests import migration_corpus as mc

pytestmark = pytest.mark.core


def _build_shape(shape: str, tmp_path: Path) -> Path:
    dest = tmp_path / f"shape_{shape}"
    dest.mkdir()
    selectors._record_dirs_cached.cache_clear()
    return mc.SHAPES[shape](dest)


def _resolved_query_map(
    ctx: object,
) -> dict[Path, artifact_meta.State]:
    records_root = Path(ctx.logical_roots["records"])  # type: ignore[attr-defined]
    repo_root = (
        getattr(ctx, "repo_root", None)
        or getattr(ctx, "target_repo", None)
        or project_context.record_git_root(records_root)
    )
    rows = artifact_meta.query(project_context=ctx)
    return {
        artifact_meta.source_path(r.path, records_root, repo_root).resolve(): r
        for r in rows
        if r.path is not None
    }


@pytest.mark.parametrize("shape", sorted(mc.SHAPES))
def test_a_shapes_query_parity(shape: str, tmp_path: Path) -> None:
    """Case (a): artifact_meta.query matches status_set.inventory_all_artifacts across all shapes."""
    root = _build_shape(shape, tmp_path)
    inv = status_set.inventory_all_artifacts(root)
    ctx = artifact_meta.legacy_context(root)
    by_path = _resolved_query_map(ctx)

    if shape == "mixed_layout":
        # `mixed_layout` has byte-identical copies of `qa1z03` in `.aw/records/` and `.agents/`.
        # `artifacts.id6` is PRIMARY KEY, so `query` holds one row per unique id6 (preferring
        # `.aw/records/`) while both paths appear in `files`.
        by_id6 = {r.id6: r for r in by_path.values()}
        for rec in inv:
            assert rec.id6 is not None
            assert rec.id6 in by_id6
            assert (by_id6[rec.id6].status or "") == (rec.status or "").lower()
        non_legacy_dup = {
            rec.path.resolve()
            for rec in inv
            if not (rec.id6 == "qa1z03" and ".agents" in rec.path.parts)
        }
        assert non_legacy_dup <= set(by_path)
        db_path = Path(ctx.logical_roots["state"]) / "index.db"
        conn = sqlite3.connect(str(db_path))
        try:
            cached_files = {
                r[0] for r in conn.execute("SELECT path FROM files").fetchall()
            }
        finally:
            conn.close()
        assert "plans/executed/20260710-beta-01-qa1z03-shared-plan.md" in cached_files
        assert (
            "@repo/.agents/plans/executed/20260710-beta-01-qa1z03-shared-plan.md"
            in cached_files
        )
        return

    inv_by_path = {rec.path.resolve(): rec for rec in inv}
    assert set(inv_by_path) <= set(by_path)
    for rpath, rec in inv_by_path.items():
        st = by_path[rpath]
        if rec.id6 is not None:
            assert st.id6 == rec.id6
        assert (st.status or "") == (rec.status or "").lower()


@pytest.mark.parametrize("shape", ["idless_prose", "legacy_agents_layout"])
def test_b_idless_derived_id6_stability(shape: str, tmp_path: Path) -> None:
    """Case (b): id-less records keep stable derived id6 across cold, warm, edit, and rebuild."""
    root = _build_shape(shape, tmp_path)
    ctx = artifact_meta.legacy_context(root)
    records_root = Path(ctx.logical_roots["records"])
    declared_ids = artifact_core.global_id6s(root)
    inv_idless_paths = {
        rec.path.resolve()
        for rec in status_set.inventory_all_artifacts(root)
        if rec.id6 is None
    }
    assert inv_idless_paths

    cold_map = _resolved_query_map(ctx)
    derived_cold = {p: st.id6 for p, st in cold_map.items() if st.id_derived}
    assert set(derived_cold) == inv_idless_paths
    for st in cold_map.values():
        if st.id_derived:
            assert artifact_core.ID6_RE.fullmatch(st.id6)
            artifact_meta.validate_id6(st.id6)
            assert st.id6 not in declared_ids
        else:
            assert st.id6 in declared_ids

    # Warm build
    warm_map = _resolved_query_map(ctx)
    assert {p: st.id6 for p, st in warm_map.items() if st.id_derived} == derived_cold

    # After editing every id-less file in place
    for p in inv_idless_paths:
        p.write_text(
            p.read_text(encoding="utf-8") + "\nAppended line.\n", encoding="utf-8"
        )
    edited_map = _resolved_query_map(ctx)
    assert {p: st.id6 for p, st in edited_map.items() if st.id_derived} == derived_cold

    # After deleting index.db
    db_file = Path(ctx.logical_roots["state"]) / "index.db"
    assert db_file.is_file()
    db_file.unlink()
    rebuilt_map = _resolved_query_map(ctx)
    assert {p: st.id6 for p, st in rebuilt_map.items() if st.id_derived} == derived_cold
    assert all(
        st.id6 not in declared_ids for st in rebuilt_map.values() if st.id_derived
    )
    assert records_root is not None


def test_c_legacy_agents_read_and_history(tmp_path: Path) -> None:
    """Case (c): read and history work on derived id6s under legacy_agents_layout."""
    root = _build_shape("legacy_agents_layout", tmp_path)
    ctx = artifact_meta.legacy_context(root)
    records_root = Path(ctx.logical_roots["records"])

    derived_rows = [r for r in artifact_meta.query(project_context=ctx) if r.id_derived]
    assert derived_rows

    for row in derived_rows:
        st = artifact_meta.read(row.id6, project_context=ctx)
        resolved = artifact_meta.source_path(st.path, records_root, root)
        assert resolved.is_file()
        assert ".agents" in resolved.parts
        hist = artifact_meta.history(row.id6, project_context=ctx)
        assert isinstance(hist, list)


@pytest.mark.parametrize("shape", sorted(mc.SHAPES))
def test_d_query_resolved_and_logical_roots_contexts(
    shape: str, tmp_path: Path
) -> None:
    """Case (d): resolve_project_context and logical_roots-only context match legacy_context."""
    root = _build_shape(shape, tmp_path)
    ctx_legacy = artifact_meta.legacy_context(root)
    paths_legacy = set(_resolved_query_map(ctx_legacy))

    ctx_resolved = project_context.resolve_project_context(target_repo=str(root))
    paths_resolved = set(_resolved_query_map(ctx_resolved))
    assert paths_resolved == paths_legacy

    ctx_logical_only = SimpleNamespace(logical_roots=dict(ctx_legacy.logical_roots))
    paths_logical_only = set(_resolved_query_map(ctx_logical_only))
    assert paths_logical_only == paths_legacy


def test_e_declared_id_collision_rederives_idless(tmp_path: Path) -> None:
    """Case (e): a record declaring an id6 derived at k=0 forces re-derivation."""
    root = _build_shape("idless_prose", tmp_path)
    ctx = artifact_meta.legacy_context(root)
    records_root = Path(ctx.logical_roots["records"])

    initial = artifact_meta.query(project_context=ctx)
    target_row = next(
        r for r in initial if r.path and "prose-migration-ipd.md" in r.path
    )
    assert target_row.id_derived is True
    colliding_id6 = target_row.id6

    declared_path = (
        records_root
        / "plans"
        / "pending"
        / f"20260901-col-01-{colliding_id6}-declared-plan.ipd.md"
    )
    declared_path.parent.mkdir(parents=True, exist_ok=True)
    declared_path.write_text(
        f"# IPD: Declared collision plan\n\n- Id: {colliding_id6}\n- Status: draft\n- Set: col\n- Order: 01\n\nBody.\n",
        encoding="utf-8",
    )

    after_rows = artifact_meta.query(project_context=ctx)
    by_path = {r.path: r for r in after_rows}
    declared_st = by_path[f"plans/pending/{declared_path.name}"]
    assert declared_st.id6 == colliding_id6
    assert declared_st.id_derived is False

    rederived_st = by_path[target_row.path]
    assert rederived_st.id_derived is True
    assert rederived_st.id6 != colliding_id6
    expected_k1 = artifact_meta.derive_id6(
        target_row.path, set(artifact_core.global_id6s(root)) | {colliding_id6}
    )
    assert rederived_st.id6 == expected_k1


def test_f_note_append_on_derived_spec_writes_no_id_or_sidecar(tmp_path: Path) -> None:
    """Case (f): note append on a derived id6 leaves no - Id: in file or sidecar."""
    root = _build_shape("legacy_agents_layout", tmp_path)
    ctx = artifact_meta.legacy_context(root)
    records_root = Path(ctx.logical_roots["records"])

    spec_row = next(
        r
        for r in artifact_meta.query(project_context=ctx)
        if r.type == "spec" and r.id_derived
    )
    derived_id6 = spec_row.id6
    spec_file = artifact_meta.source_path(spec_row.path, records_root, root)
    assert "- Id:" not in spec_file.read_text(encoding="utf-8")

    render = artifact_meta.LegacyRender(
        day="2026-11-17",
        tag="note",
        actor_label="test",
        history=True,
        history_at_end=True,
    )
    sidecar = artifact_meta.SidecarRecord(
        tree="specs",
        workflow="note",
        actor="test",
        message="derived id note test",
        date="2026-11-17",
    )
    preview = artifact_meta.append(
        derived_id6,
        [{"op": "note", "message": "derived id note test"}],
        project_context=ctx,
        legacy_render=render,
        sidecar=sidecar,
    )
    assert preview.changed is True

    updated_text = spec_file.read_text(encoding="utf-8")
    assert "- Id:" not in updated_text
    assert derived_id6 not in updated_text
    assert "derived id note test" in updated_text

    sidecar_file = records_root / "history.jsonl"
    if sidecar_file.exists():
        assert derived_id6 not in sidecar_file.read_text(encoding="utf-8")
