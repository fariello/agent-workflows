"""Behavioral pinning tests for record-module readers (IPD kyl3m4 E-02).

Pins observable behavior of the plans record modules before and after moving their metadata
reads onto ``artifact_meta.query`` / ``artifact_meta.read_text``:
- ``agent_workflows.plans_index``
- ``agent_workflows.plans_archive``
- ``agent_workflows.plans_refs`` (read side)
- ``agent_workflows.ipd_set_plan``
- ``agent_workflows.completion`` (plan id6 and Set id candidates)

Tests assert only observable outputs and side effects; none inspects production source code.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pytest

from agent_workflows import (
    completion,
    ipd_set_plan,
    plans_archive,
    plans_index,
    plans_refs,
)
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _write_plan(
    plans_dir: Path,
    rel_dir: str,
    filename: str,
    *,
    plan_id: str | None,
    set_raw: str | None = "alpha (Alpha Set)",
    order: int | None = 1,
    status: str = "approved",
    kind: str = "child",
    plan_date: str | None = "2026-07-01",
    body: str = "## Goal\n\nPin reader behavior.\n",
) -> Path:
    target_dir = plans_dir / rel_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    raw_fields: dict[str, str | None] = {}
    if plan_id is None:
        raw_fields["Id"] = None
    if set_raw is None:
        raw_fields["Set"] = None
    else:
        raw_fields["Set"] = set_raw
    if order is None:
        raw_fields["Order"] = None
    if plan_date is None:
        raw_fields["Date"] = None
    else:
        raw_fields["Date"] = plan_date
    text = str(
        RecordBuilder().plan(
            id6=plan_id or "tmp001",
            title=f"Plan {plan_id or filename}",
            when="2026-07-01",
            plan_role=kind,
            set="alpha",
            order=order if order is not None else 1,
            status=status,
            author="tester",
            body=body,
            raw_fields=raw_fields,
            text_only=True,
        )
    )
    path = target_dir / filename
    path.write_text(text, encoding="utf-8")
    return path


def _build_plans_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps({"schema_version": 2, "records_backend": "repository"}) + "\n",
        encoding="utf-8",
    )
    plans_dir = repo / ".aw" / "records" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    return repo, plans_dir


def test_plans_index_scan_query_and_drift(tmp_path: Path) -> None:
    """Pin plans_index.scan_plans, plan_entry, query, _meta, and check_drift."""
    repo, plans_dir = _build_plans_repo(tmp_path)

    p_pending = _write_plan(
        plans_dir,
        "pending",
        "20260701-alpha-01-pln001-first.ipd.md",
        plan_id="pln001",
        set_raw="alpha (Alpha Set)",
        order=1,
        status="approved",
        kind="child",
        plan_date="2026-07-01",
    )
    _write_plan(
        plans_dir,
        "executed/202606",
        "20260615-alpha-02-pln002-sharded.ipd.md",
        plan_id="pln002",
        set_raw="alpha (Alpha Set)",
        order=2,
        status="executed",
        kind="child",
        plan_date="2026-06-15",
    )
    _write_plan(
        plans_dir,
        "executed",
        "20260705-solo-00-pln003-singleton.ipd.md",
        plan_id="pln003",
        set_raw=None,
        order=None,
        status="executed",
        kind="child",
        plan_date="2026-07-05",
    )
    # Non-plan marker must be excluded
    (plans_dir / "README.md").write_text("# Plans\n", encoding="utf-8")

    entries, drift = plans_index.scan_plans(plans_dir)
    assert drift == []
    by_id = {e.plan_id: e for e in entries}
    assert set(by_id) == {"pln001", "pln002", "pln003"}

    assert by_id["pln001"].disposition == "pending"
    assert by_id["pln001"].set_id == "alpha"
    assert by_id["pln001"].order == 1
    assert by_id["pln001"].status == "approved"
    assert by_id["pln001"].kind == "child"

    assert by_id["pln002"].disposition == "executed"
    assert (
        by_id["pln002"].path
        == "executed/202606/20260615-alpha-02-pln002-sharded.ipd.md"
    )
    assert by_id["pln002"].set_id == "alpha"
    assert by_id["pln002"].order == 2

    assert by_id["pln003"].set_id is None
    assert by_id["pln003"].disposition == "executed"

    # Direct plan_entry call
    pe_res = plans_index.plan_entry(plans_dir, p_pending, ignored_dirs=set())
    assert pe_res is not None
    pe_entry, pe_drift = pe_res
    assert pe_entry.plan_id == "pln001"
    assert pe_drift == []

    # Query filters
    assert [e.plan_id for e in plans_index.query(entries, set_id="alpha")] == [
        "pln001",
        "pln002",
    ]
    assert [e.plan_id for e in plans_index.query(entries, disposition="pending")] == [
        "pln001"
    ]
    assert [e.plan_id for e in plans_index.query(entries, status_not="executed")] == [
        "pln001"
    ]

    # _meta helper
    text = p_pending.read_text(encoding="utf-8")
    assert plans_index._meta(text, "Id") == "pln001"
    assert plans_index._meta(text, "Kind") == "child"
    assert plans_index._meta(text, "Order") == "1"

    # Drift detection: missing Id in pending and name-vs-metadata mismatch
    _write_plan(
        plans_dir,
        "pending",
        "20260706-alpha-03-nope-missing-id.ipd.md",
        plan_id=None,
        set_raw="alpha",
        order=3,
        status="draft",
    )
    _write_plan(
        plans_dir,
        "executed",
        "20260707-alpha-04-zzzzzz-mismatch.ipd.md",
        plan_id="pln004",
        set_raw="beta",
        order=4,
        status="executed",
    )
    check_res = plans_index.check_drift(repo, plans_dir)
    rules = {d.rule for d in check_res}
    assert "id-missing" in rules
    assert "name-metadata-mismatch" in rules


def test_plans_index_multiword_status_d1(tmp_path: Path) -> None:
    """Pin D-1 multi-word status behavior on plans_index.scan_plans."""
    _repo, plans_dir = _build_plans_repo(tmp_path)
    target = plans_dir / "executed" / "20260710-oldset-01-mlt001-multiword.ipd.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# IPD: Multiword Executed Plan\n\n"
        "- Date: 2026-07-10\n"
        "- Kind: child\n"
        "- Id: mlt001\n"
        "- Set: oldset\n"
        "- Order: 01\n"
        "- Status: EXECUTED (approved by maintainer)\n\n"
        "## Goal\n\nPin D-1 multi-word status.\n",
        encoding="utf-8",
    )
    entries, _ = plans_index.scan_plans(plans_dir)
    assert len(entries) == 1
    # D-1: plans_index returns the canonical normalized status for multi-word executed plans.
    assert entries[0].status == "executed"


def test_plans_readers_answer_without_index_files_from_log_format_meta(
    tmp_path: Path,
) -> None:
    """Verify AC-9: plans readers answer from artifact_meta.query on log-format metadata without INDEX files."""
    from agent_workflows import artifact_meta

    repo, plans_dir = _build_plans_repo(tmp_path)
    pending_rel = "plans/pending/20261110-logset-01-log001-log-only.ipd.md"
    exec_rel = "plans/executed/20260110-logset-02-log002-log-exec.ipd.md"
    p_pend = repo / ".aw" / "records" / pending_rel
    p_exec = repo / ".aw" / "records" / exec_rel
    p_pend.parent.mkdir(parents=True, exist_ok=True)
    p_exec.parent.mkdir(parents=True, exist_ok=True)
    # Body-only markdown files (no bullet front matter); metadata lives solely in meta/<id6>.jsonl.
    p_pend.write_text("# IPD: Log Pending\n\n## Goal\n\nBody only.\n", encoding="utf-8")
    p_exec.write_text(
        "# IPD: Log Executed\n\n## Goal\n\nBody only.\n", encoding="utf-8"
    )

    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    ev_pend = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-10T00:00:00Z",
        "actor": {"tool": "aw"},
        "op": "create",
        "path": pending_rel,
        "fields": {
            "title": "Log Pending",
            "set": "logset",
            "order": 1,
            "plan_role": "child",
            "status": "approved",
            "created_day": "2026-11-10",
            "filename_date": "20261110",
        },
    }
    ev_exec = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-01-10T00:00:00Z",
        "actor": {"tool": "aw"},
        "op": "create",
        "path": exec_rel,
        "fields": {
            "title": "Log Executed",
            "set": "logset",
            "order": 2,
            "plan_role": "child",
            "status": "executed",
            "created_day": "2026-01-10",
            "filename_date": "20260110",
        },
    }
    (meta_dir / "log001.jsonl").write_text(
        artifact_meta.encode_event(ev_pend), encoding="utf-8"
    )
    (meta_dir / "log002.jsonl").write_text(
        artifact_meta.encode_event(ev_exec), encoding="utf-8"
    )

    assert not (plans_dir / "INDEX.json").exists()
    assert not (plans_dir / "INDEX.md").exists()

    entries, drift = plans_index.scan_plans(plans_dir)
    assert drift == []
    by_id = {e.plan_id: e for e in entries}
    assert set(by_id) == {"log001", "log002"}
    assert by_id["log001"].status == "approved"
    assert by_id["log001"].set_id == "logset"
    assert by_id["log001"].order == 1
    assert by_id["log001"].kind == "child"
    assert by_id["log001"].date == "2026-11-10"

    assert plans_refs._find_plan_by_id(plans_dir, "log001") == p_pend.resolve()
    mv = plans_archive.plan_shard_move(plans_dir, p_exec)
    assert mv is not None
    assert mv.id6 == "log002"
    assert mv.new_path.parent.name == "202601"
    assert plans_archive._plan_status(p_pend, plans_dir) == "approved"

    assert completion.plan_id6_candidates(repo) == ["log001"]
    assert completion.set_id_candidates(repo) == ["logset"]


def test_plans_archive_shard_move_status_and_sweep(tmp_path: Path) -> None:
    """Pin plans_archive.plan_shard_move, _plan_status, _resolve_plan_date, and sweep_candidates."""
    _repo, plans_dir = _build_plans_repo(tmp_path)

    p_old = _write_plan(
        plans_dir,
        "executed",
        "20260110-oldset-01-arc001-old.ipd.md",
        plan_id="arc001",
        set_raw="oldset",
        order=1,
        status="executed",
        plan_date="2026-01-10",
    )
    p_malformed_date = _write_plan(
        plans_dir,
        "executed",
        "20260715-soloset-01-arc002-bad-date.ipd.md",
        plan_id="arc002",
        set_raw=None,
        order=1,
        status="executed",
        plan_date="2026-07-23 (fleshed 2026-07-26)",
    )
    p_pending = _write_plan(
        plans_dir,
        "pending",
        "20260720-mixset-01-arc003-pending.ipd.md",
        plan_id="arc003",
        set_raw="mixset",
        order=1,
        status="draft",
        plan_date="2026-07-20",
    )
    p_mix_old = _write_plan(
        plans_dir,
        "executed",
        "20260105-mixset-02-arc004-old-member.ipd.md",
        plan_id="arc004",
        set_raw="mixset",
        order=2,
        status="executed",
        plan_date="2026-01-05",
    )
    p_sharded = _write_plan(
        plans_dir,
        "executed/202606",
        "20260601-done-01-arc005-sharded.ipd.md",
        plan_id="arc005",
        set_raw="done",
        order=1,
        status="executed",
        plan_date="2026-06-01",
    )

    mv_old = plans_archive.plan_shard_move(plans_dir, p_old)
    assert mv_old is not None
    assert mv_old.id6 == "arc001"
    assert mv_old.new_path.parent.name == "202601"

    mv_bad = plans_archive.plan_shard_move(plans_dir, p_malformed_date)
    assert mv_bad is not None
    assert mv_bad.id6 == "arc002"
    assert mv_bad.new_path.parent.name == "202607"

    assert plans_archive.plan_shard_move(plans_dir, p_pending) is None
    assert plans_archive.plan_shard_move(plans_dir, p_sharded) is None

    assert plans_archive._plan_status(p_pending, plans_dir) == "draft"
    assert (
        plans_archive._plan_status(p_sharded, plans_dir)
        == "executed, already in 202606/ shard"
    )

    # Sweep on 2026-07-25 with 14d age:
    # - arc001 (2026-01-10) -> swept
    # - arc002 (2026-07-15, 10d old) -> NOT swept
    # - arc004 (2026-01-05, in mixset with arc003 5d old) -> NOT swept (set cohesion)
    cands = plans_archive.sweep_candidates(
        plans_dir, older_than_days=14, today=date(2026, 7, 25)
    )
    assert [p.name for p in cands] == [p_old.name]
    assert p_mix_old not in cands


def test_plans_refs_read_side_lookup_and_plan_set_assign(tmp_path: Path) -> None:
    """Pin plans_refs read-side helpers, plan_set_assign, and run_mv preview."""
    repo, plans_dir = _build_plans_repo(tmp_path)

    p_child = _write_plan(
        plans_dir,
        "pending",
        "20260801-alpha-02-ref001-child.ipd.md",
        plan_id="ref001",
        set_raw="alpha (Alpha Set)",
        order=2,
        status="to-review",
        kind="child",
        plan_date="2026-08-01",
    )
    p_no_order = _write_plan(
        plans_dir,
        "pending",
        "20260802-alpha-05-ref002-no-order.ipd.md",
        plan_id="ref002",
        set_raw="alpha",
        order=None,
        status="to-review",
        kind="child",
        plan_date="2026-08-02",
    )

    assert plans_refs._find_plan_by_id(plans_dir, "ref001") == p_child
    assert plans_refs._find_plan_by_id(plans_dir, "zzzzzz") is None

    text_child = p_child.read_text(encoding="utf-8")
    text_no_order = p_no_order.read_text(encoding="utf-8")
    assert plans_refs._read_id(text_child) == "ref001"
    assert plans_refs._plan_date(text_child) == "20260801"
    assert plans_refs._preserved_order(p_child.name, text_child) == 2
    assert plans_refs._preserved_order(p_no_order.name, text_no_order) == 5
    assert plans_refs._preserved_date(p_child.name, text_child) == "20260801"
    assert plans_refs._validate_plan_order(text_child, 2) is None
    assert plans_refs._validate_plan_order(text_child, 0) is not None

    # plan_set_assign preserves each plan's order when start_order is None
    planned, err = plans_refs.plan_set_assign(
        plans_dir,
        ["ref001", "ref002"],
        "newset",
        rename=True,
        repo_root=repo,
        emit_human=False,
    )
    assert err is None
    assert planned is not None
    assert [p.order for p in planned] == [2, 5]
    assert planned[0].new_path.name == "20260801-newset-02-ref001-child.ipd.md"
    assert planned[1].new_path.name == "20260802-newset-05-ref002-no-order.ipd.md"

    # run_mv preview preserves set, order, and date
    mv_res = plans_refs.run_mv(
        argparse.Namespace(
            dir=str(repo),
            id="ref001",
            slug="renamed-child",
            set=None,
            order=None,
            apply=False,
            no_refs=True,
            yes=True,
            force=False,
            allow_invalid_order=False,
        ),
        emit_human=False,
    )
    assert mv_res.rc == 0
    assert len(mv_res.targets) == 1
    assert mv_res.targets[0].new_path.endswith(
        "20260801-alpha-02-ref001-renamed-child.ipd.md"
    )


def test_plans_ipd_set_plan_inventory_and_gates(tmp_path: Path) -> None:
    """Pin ipd_set_plan.resolve_set inventory, cross-edges, and deferred gates."""
    _repo, plans_dir = _build_plans_repo(tmp_path)

    orch_body = (
        "## Child IPDs, sequence, and dependencies\n\n"
        "| Order | File | Purpose | Depends on |\n"
        "| --- | --- | --- | --- |\n"
        "| 01 | `20260823-demo-01-set001-one.ipd.md` | one | none |\n"
        "| 02 | `20260823-demo-02-set002-two.ipd.md` | two | 01 |\n"
        "| 03 | `20260823-demo-03-set003-three.ipd.md` | three | none |\n\n"
        "## Goal\n\nOrchestrate demo.\n"
    )
    child_body = (
        "## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 step one\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: ok\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n"
    )

    _write_plan(
        plans_dir,
        "pending",
        "20260823-demo-00-orc001-orch.ipd.md",
        plan_id="orc001",
        set_raw="demo (Demo Set)",
        order=0,
        status="approved",
        kind="orchestrator",
        body=orch_body,
    )
    _write_plan(
        plans_dir,
        "pending",
        "20260823-demo-01-set001-one.ipd.md",
        plan_id="set001",
        set_raw="demo",
        order=1,
        status="draft",
        kind="child",
        body=child_body,
    )
    _write_plan(
        plans_dir,
        "pending",
        "20260823-demo-02-set002-two.ipd.md",
        plan_id="set002",
        set_raw="demo",
        order=2,
        status="approved",
        kind="child",
        body=child_body,
    )
    _write_plan(
        plans_dir,
        "pending",
        "20260823-demo-03-set003-three.ipd.md",
        plan_id="set003",
        set_raw="demo",
        order=3,
        status="approved",
        kind="child",
        body=child_body,
    )

    inv = ipd_set_plan.resolve_set(plans_dir, "demo")
    assert inv.orchestrator_id == "orc001"
    assert [c.plan_id for c in inv.children] == ["set001", "set002", "set003"]
    assert inv.cross_edges_source == "orchestrator-table"
    assert dict(inv.cross_edges)["set002"] == ("set001",)
    assert inv.deferred_gates == ("set001",)
    assert inv.blocked_children == ("set001", "set002")


def test_plans_completion_active_candidates(tmp_path: Path) -> None:
    """Pin completion.plan_id6_candidates and set_id_candidates active scoping."""
    repo, plans_dir = _build_plans_repo(tmp_path)

    _write_plan(
        plans_dir,
        "pending",
        "20260828-actset-01-cmp001-active.ipd.md",
        plan_id="cmp001",
        set_raw="actset (Active Set)",
        order=1,
        status="to-review",
    )
    _write_plan(
        plans_dir,
        "reusable",
        "20260828-reuset-01-cmp002-reusable.ipd.md",
        plan_id="cmp002",
        set_raw="reuset",
        order=1,
        status="reusable",
    )
    _write_plan(
        plans_dir,
        "executed",
        "20260801-oldset-01-cmp003-executed.ipd.md",
        plan_id="cmp003",
        set_raw="oldset",
        order=1,
        status="executed",
    )

    ids = set(completion.plan_id6_candidates(repo))
    sets = set(completion.set_id_candidates(repo))
    assert ids == {"cmp001", "cmp002"}
    assert sets == {"actset", "reuset"}


def test_plans_index_bare_tempdir_stays_scoped(tmp_path: Path) -> None:
    """A standalone plans_dir with no `plans` ancestor scopes artifact_meta strictly inside itself."""
    bare = tmp_path / "scratch_dir"
    _write_plan(
        bare,
        "pending",
        "20260829-bare-01-bar001-scoped.ipd.md",
        plan_id="bar001",
        set_raw="bare",
        order=1,
        status="approved",
        kind="child",
    )
    ctx, records_root, _scan_repo = plans_index._meta_context_for_plans_dir(bare)
    assert records_root.resolve() == bare.resolve()
    assert Path(ctx.logical_roots["state"]).resolve().is_relative_to(bare.resolve())

    entries, drift = plans_index.scan_plans(bare)
    assert drift == []
    assert [e.plan_id for e in entries] == ["bar001"]
    assert entries[0].set_id == "bare"
    assert entries[0].order == 1
