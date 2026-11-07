"""Legacy loader parity with today's readers (backlog `suth7l`).

The `artifact_meta` cache's legacy loader disagreed with `status_set`'s reader on 1388 of 3146
records of this repository (measured 2026-11-07) and wrote no per-type field rows at all. These
tests pin the three corrected behaviors on small fixture repositories, through the public read
interface (`artifact_meta.query`) and the cache's per-type tables:

1. a bullet block with NO `# ` title (every backlog item) is read;
2. YAML front matter is read for research records named by their KIND facet (`findings`,
   `roadmap`, ...), and the record is cached under the `research` registry type;
3. registry fields are written to the per-type table, and a cache built by an older loader is
   rebuilt rather than served.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import status_set

pytestmark = pytest.mark.core


def _ctx(tmp_path: Path):
    records = tmp_path / ".aw" / "records"
    state = tmp_path / ".aw" / "state"
    records.mkdir(parents=True)
    state.mkdir(parents=True)
    ctx = type("Ctx", (), {"logical_roots": {"records": records, "state": state}})
    return ctx, records, state


def _write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


BACKLOG = (
    "- Id: bkl001\n- Status: open\n- Set: bkl001\n- Priority: high\n- Work-Kind: bug\n"
    "- Blocks-Release: next\n- Summary: a backlog item has no title line\n\n"
    "## Workflow history\n- 2026-11-07 created (aw backlog): x\n\n## Problem\n\nBody.\n"
)
FINDINGS = (
    "---\nid: rsh001\ncreated: 20261016\nset: rset\norder: 01\nkind: findings\n"
    "status: active\noutcome: adopted\n---\n# Findings: something\n\nBody.\n"
)
PLAN = (
    "# IPD: a plan\n\n- Date: 2026-11-07\n- Kind: child\n- Status: approved\n- Set: pset\n"
    "- Priority: medium\n- Work-Kind: feature\n- Item-Dependencies: executed:abc123\n- Id: pln001\n\n"
    "## Workflow history\n- 2026-11-07 approved (aw set): x\n\n## Goal\n\nG.\n"
)


def _seed(records: Path) -> None:
    _write(
        records / "backlog" / "open" / "20261107-bkl001-01-bkl001-item.backlog.md",
        BACKLOG,
    )
    _write(records / "research" / "20261016-rset-01-rsh001-topic.findings.md", FINDINGS)
    _write(
        records / "plans" / "pending" / "20261107-pset-01-pln001-a-plan.ipd.md", PLAN
    )


def test_untitled_backlog_bullets_are_read(tmp_path: Path):
    ctx, records, _ = _ctx(tmp_path)
    _seed(records)
    [st] = meta.query(project_context=ctx, id6="bkl001")
    assert st.type == "backlog"
    assert st.status == "open"
    assert st.set_id == "bkl001"


def test_research_kind_facet_record_reads_yaml_status_under_research_type(
    tmp_path: Path,
):
    ctx, records, _ = _ctx(tmp_path)
    _seed(records)
    [st] = meta.query(project_context=ctx, id6="rsh001")
    assert st.type == "research"
    assert st.status == "active"
    assert st.set_id == "rset"


def test_registry_fields_reach_the_per_type_tables(tmp_path: Path):
    ctx, records, state = _ctx(tmp_path)
    _seed(records)
    meta.query(project_context=ctx)
    con = sqlite3.connect(str(state / "index.db"))
    try:
        assert con.execute(
            "select priority, work_kind, blocks_release from backlog where id6='bkl001'"
        ).fetchone() == ("high", "bug", "next")
        assert con.execute(
            "select research_kind, outcome from research where id6='rsh001'"
        ).fetchone() == ("findings", "adopted")
        assert con.execute(
            "select priority, work_kind, item_dependencies, plan_role from ipd where id6='pln001'"
        ).fetchone() == ("medium", "feature", "executed:abc123", "child")
    finally:
        con.close()


def test_cache_agrees_with_status_set_reader_on_every_fixture_record(tmp_path: Path):
    """The parity contract downstream plans rely on: id6 and status match today's reader."""
    ctx, records, _ = _ctx(tmp_path)
    _seed(records)
    by_path = {
        str((records / s.path).resolve()): s for s in meta.query(project_context=ctx)
    }
    inv = status_set.inventory_all_artifacts(tmp_path)
    assert len(inv) == 3
    for rec in inv:
        st = by_path[str(rec.path.resolve())]
        assert st.id6 == rec.id6
        assert st.status == (rec.status or "").lower()
        if rec.set_id is not None:
            assert st.set_id == rec.set_id
        else:
            # THE ONE DELIBERATE DIFFERENCE (maintainer decision 2026-11-07, recorded on backlog
            # `suth7l` and carried by `ffceq0`'s reader ledger): a record with no in-file `- Set:`
            # bullet gets NO Set from today's reader, while the cache takes it from the filename,
            # which spec `4sd62s` C10 makes the checked mirror of `set`. Here the research record
            # declares `set:` only in YAML, which today's bullet reader does not see.
            assert st.set_id == "rset" and rec.path.name.startswith("20261016-rset-")


def test_a_cache_built_by_an_older_loader_is_rebuilt_not_served(tmp_path: Path):
    ctx, records, state = _ctx(tmp_path)
    _seed(records)
    meta.query(project_context=ctx)
    con = sqlite3.connect(str(state / "index.db"))
    try:
        # Simulate a cache left by an older loader: stale status, no per-type row, old hash.
        con.execute("update artifacts set status=NULL where id6='bkl001'")
        con.execute("delete from backlog")
        con.execute("update meta set value='stale' where key='schema_hash'")
        con.commit()
    finally:
        con.close()
    [st] = meta.query(project_context=ctx, id6="bkl001")
    assert st.status == "open"
    con = sqlite3.connect(str(state / "index.db"))
    try:
        assert con.execute("select count(*) from backlog").fetchone()[0] == 1
    finally:
        con.close()
