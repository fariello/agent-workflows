"""Behavioral pinning tests for record-module readers (IPDs kyl3m4 E-02, cb5eda E-01..E-03).

Pins observable behavior of the plans, research, and prompts record modules before and after
moving their metadata reads onto ``artifact_meta.query`` / ``artifact_meta.read_text``:
- ``agent_workflows.plans_index``
- ``agent_workflows.plans_archive``
- ``agent_workflows.plans_refs`` (read side)
- ``agent_workflows.ipd_set_plan``
- ``agent_workflows.completion`` (plan id6 and Set id candidates)
- ``agent_workflows.research_index`` (including banner-blind ``has_body``)
- ``agent_workflows.research_archive``
- ``agent_workflows.prompts_index``

Tests assert only observable outputs and side effects; none inspects production source code.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

from agent_workflows import (
    completion,
    ipd_set_plan,
    plans_archive,
    plans_index,
    plans_refs,
    prompts_index,
    research_archive,
    research_cmd,
    research_contract,
    research_index,
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
        RecordBuilder().plan(
            title="Multiword Executed Plan",
            when="2026-07-10",
            plan_role="child",
            id6="mlt001",
            set="oldset",
            order=1,
            body="## Goal\n\nPin D-1 multi-word status.",
            raw_fields={"Status": "EXECUTED (approved by maintainer)"},
            text_only=True,
        ),
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


# --------------------------------------------------------------------------------------
# Research and prompts record-module pinning tests (IPD cb5eda E-01, E-02, E-03)
# --------------------------------------------------------------------------------------


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo, check=True)


def _build_records_repo(
    tmp_path: Path, *, git: bool = False
) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps({"schema_version": 2, "records_backend": "repository"}) + "\n",
        encoding="utf-8",
    )
    research_dir = repo / ".aw" / "records" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = repo / ".aw" / "records" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    if git:
        _init_git_repo(repo)
    return repo, research_dir, prompts_dir


def _write_research_doc(
    research_dir: Path,
    *,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    status: str | None,
    created: str = "20260701",
    kind: str = "notes",
    model: str | None = None,
    outcome: str = "none-yet",
    topic: list[str] | None = None,
    consumed_by: list[str] | None = None,
    priority: str | None = None,
    body: str | None = None,
    subdir: str | None = None,
) -> Path:
    target_dir = research_dir / subdir if subdir else research_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    name = research_contract.format_name(
        research_contract.ResearchName(
            date=created,
            set_id=set_id,
            order=f"{order:02d}",
            id6=id6,
            slug=slug,
            model=model,
            kind=kind,
        )
    )
    content = research_cmd.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=topic if topic is not None else ["pin"],
        model=model,
        kind=kind,
        status=status,
        outcome=outcome,
        summary=f"summary {id6}",
        consumed_by=consumed_by,
        priority=priority,
    )
    if body:
        content += f"\n{body}\n"
    path = target_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def test_research_index_scan_query_cited_and_consumers(tmp_path: Path) -> None:
    """Pin research_index._scan_docs, query, cited_by_executed_ids, resolvable_consumer_ids, and check_drift."""
    repo, research_dir, _prompts_dir = _build_records_repo(tmp_path)

    _write_research_doc(
        research_dir,
        set_id="pinset",
        order=0,
        id6="rpr001",
        slug="prompt",
        status=None,
        created="20260801",
        kind="research-prompt",
        outcome="none-yet",
    )
    _write_research_doc(
        research_dir,
        set_id="pinset",
        order=1,
        id6="rrp001",
        slug="report",
        status="todo",
        created="20260802",
        kind="research-report",
        model="gpt56",
        topic=["cache", "readers"],
        priority="high",
        body="## Findings\n\nObserved report body.",
    )
    _write_research_doc(
        research_dir,
        set_id="refset",
        order=0,
        id6="rref01",
        slug="refdoc",
        status="reference",
        created="20260715",
        kind="findings",
        outcome="adopted",
        consumed_by=["pln101"],
        subdir="reference/202607",
        body="## Summary\n\nAdopted findings.",
    )
    # Non-conformant filename without frontmatter must be skipped quietly
    (research_dir / "notes-scratch.md").write_text("# Scratch\n", encoding="utf-8")
    # Non-conformant filename WITH frontmatter must emit name-invalid
    (research_dir / "bad-name-with-fm.md").write_text(
        research_cmd.build_frontmatter(
            id6="rbad01",
            created="20260803",
            set_id="bad",
            order="00",
            topic=["x"],
            model=None,
            kind="notes",
            status="todo",
            outcome="none-yet",
            summary="bad name",
        ),
        encoding="utf-8",
    )

    # Executed plan, implemented spec, and done backlog item (plus non-executed counterparts)
    RecordBuilder(repo).plan(
        id6="pln101",
        title="Executed Plan",
        when="2026-08-05",
        set="cset",
        order=1,
        slug="exec",
        status="executed",
        disposition="executed",
        body="## Goal\n\nCites RSCH-rrp001.\n",
    )
    RecordBuilder(repo).plan(
        id6="pln102",
        title="Pending Plan",
        when="2026-08-06",
        set="cset",
        order=2,
        slug="pend",
        status="approved",
        disposition="pending",
        body="## Goal\n\nCites RSCH-rpr001.\n",
    )
    specs_dir = repo / ".aw" / "records" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    (specs_dir / "20260805-cset-01-spc101-impl.spec.md").write_text(
        RecordBuilder().spec(
            id6="spc101",
            title="Implemented Spec",
            when="2026-08-05",
            set="cset",
            order=1,
            slug="impl",
            status="implemented",
            body="## Scope\n\nCites RSCH-rref01.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )
    (specs_dir / "20260806-cset-02-spc102-draft.spec.md").write_text(
        RecordBuilder().spec(
            id6="spc102",
            title="Draft Spec",
            when="2026-08-06",
            set="cset",
            order=2,
            slug="draft",
            status="draft",
            body="## Scope\n\nCites RSCH-unexec.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )
    bkl_open = repo / ".aw" / "records" / "backlog" / "open"
    bkl_open.mkdir(parents=True, exist_ok=True)
    (bkl_open / "20260806-bkl101-01-bkl101-open.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl101",
            title="Open Backlog",
            when="2026-08-06",
            status="open",
            body="Cites RSCH-unbkl1.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )
    (bkl_open / "20260806-bkl102-01-bkl102-inline-done.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl102",
            title="Inline Done Backlog",
            when="2026-08-06",
            status="done",
            body="Cites RSCH-rpr001.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    entries, scan_drift = research_index._scan_docs(research_dir, repo_root=repo)
    assert [d.rule for d in scan_drift] == ["name-invalid"]
    by_id = {e.id6: e for e in entries}
    assert set(by_id) == {"rpr001", "rrp001", "rref01"}
    assert by_id["rpr001"].status == ""
    assert by_id["rpr001"].has_body is False
    assert by_id["rrp001"].status == "todo"
    assert by_id["rrp001"].model == "gpt56"
    assert by_id["rrp001"].topic == ["cache", "readers"]
    assert by_id["rrp001"].priority == "high"
    assert by_id["rrp001"].has_body is True
    assert by_id["rref01"].consumed_by == ["pln101"]

    positions = research_index.derive_pipeline_positions(entries)
    assert positions == {"pinset": "partial"}
    assert [e.id6 for e in research_index.query(entries, topic="cache")] == ["rrp001"]
    assert [e.id6 for e in research_index.query(entries, position="partial")] == [
        "rpr001"
    ]

    cited = research_index.cited_by_executed_ids(repo, research_dir)
    assert {"rrp001", "rref01", "rpr001"}.issubset(cited)
    assert "unexec" not in cited
    assert "unbkl1" not in cited

    consumers = research_index.resolvable_consumer_ids(repo)
    assert {"pln101", "pln102", "spc101", "spc102", "bkl101", "bkl102"}.issubset(
        consumers
    )

    # Drift checks: adopted consumer resolves cleanly; rrp001 cited by executed plan flags stale-state
    drift = research_index.check_drift(repo, research_dir)
    rules = {d.rule for d in drift}
    assert research_index.STALE_STATE_RULE in rules
    assert research_index.DANGLING_CONSUMED_RULE not in rules


def test_research_archive_plan_sweep_miscategorized_and_apply(tmp_path: Path) -> None:
    """Pin research_archive._all_docs, plan_transition, sweep_candidates, find_miscategorized, and apply_moves."""
    repo, research_dir, _prompts_dir = _build_records_repo(tmp_path, git=True)

    p_old = _write_research_doc(
        research_dir,
        set_id="oldset",
        order=0,
        id6="rar001",
        slug="aged",
        status="intake",
        created="20260110",
    )
    _write_research_doc(
        research_dir,
        set_id="newset",
        order=0,
        id6="rar002",
        slug="fresh",
        status="todo",
        created="20260720",
    )
    _write_research_doc(
        research_dir,
        set_id="arcset",
        order=0,
        id6="rar003",
        slug="archived-cited",
        status="archive",
        created="20260105",
        consumed_by=["pln999"],
        subdir="archive/202601",
    )
    p_prompt = _write_research_doc(
        research_dir,
        set_id="prmset",
        order=0,
        id6="rar004",
        slug="statusless-prompt",
        status=None,
        created="20260705",
        kind="research-prompt",
    )

    all_docs = research_archive._all_docs(research_dir)
    assert {parsed.id6 for _p, parsed, _fm in all_docs} == {
        "rar001",
        "rar002",
        "rar003",
        "rar004",
    }

    assert research_archive.find_miscategorized(repo, research_dir) == ["rar003"]

    cands = research_archive.sweep_candidates(
        repo, research_dir, older_than_days=14.0, today=date(2026, 7, 25)
    )
    assert "rar001" in cands
    assert "rar002" not in cands
    assert "rar003" not in cands

    mv_bad, err_bad = research_archive.plan_transition_for_path(
        research_dir, p_prompt, "todo"
    )
    assert mv_bad is None
    assert err_bad is not None and "research-prompt carries no hot status" in err_bad

    mv_ref, err_ref = research_archive.plan_transition(
        research_dir, "rar001", "reference"
    )
    assert err_ref is None
    assert mv_ref is not None
    assert mv_ref.old_path == p_old
    assert mv_ref.new_path.parent.as_posix().endswith("reference/202601")

    mv_prm, err_prm = research_archive.plan_transition_for_path(
        research_dir, p_prompt, "reference"
    )
    assert err_prm is None
    assert mv_prm is not None

    research_archive.apply_moves(repo, research_dir, [mv_ref, mv_prm])
    assert mv_ref.new_path.is_file()
    assert mv_prm.new_path.is_file()
    entries_after, drift_after = research_index._scan_docs(research_dir, repo_root=repo)
    assert drift_after == []
    after_by_id = {e.id6: e for e in entries_after}
    assert after_by_id["rar001"].status == "reference"
    assert after_by_id["rar004"].status == "reference"


def test_prompts_index_scan_build_and_drift(tmp_path: Path) -> None:
    """Pin prompts_index.scan_prompts, build_index_json, build_index_md, and check_drift."""
    repo, _research_dir, prompts_dir = _build_records_repo(tmp_path)
    for bucket in ("pending", "executed", "superseded", "untracked"):
        (prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

    (
        prompts_dir / "pending" / "20260920-seta-01-prm101-first-prompt.prompt.md"
    ).write_text(
        "<!-- aw-prompt: Kind: research | Id: prm101 | Set: seta | Order: 01 | Status: pending | Slug: first-prompt -->\n\nPrompt body.\n",
        encoding="utf-8",
    )
    (prompts_dir / "executed" / "20260810-1544-01-old-run.prompt.md").write_text(
        "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-10 -->\n\nLegacy prompt.\n",
        encoding="utf-8",
    )
    (prompts_dir / "superseded" / "20260717-1950-01-plain-old.prompt.md").write_text(
        "# Old prompt\n\nBody.\n", encoding="utf-8"
    )
    (prompts_dir / "untracked" / "20260920-local.prompt.md").write_text(
        "# Ignored\n", encoding="utf-8"
    )

    entries, drift = prompts_index.scan_prompts(prompts_dir)
    assert drift == []
    assert len(entries) == 3
    by_path = {e.path: e for e in entries}

    e1 = by_path["pending/20260920-seta-01-prm101-first-prompt.prompt.md"]
    assert e1.id6 == "prm101"
    assert e1.set_id == "seta"
    assert e1.order == 1
    assert e1.kind == "research"
    assert e1.status == "pending"
    assert e1.date == "20260920"

    e2 = by_path["executed/20260810-1544-01-old-run.prompt.md"]
    assert e2.id6 is None
    assert e2.kind == "run-once"
    assert e2.status == "executed"
    assert e2.date == "2026-08-10"

    e3 = by_path["superseded/20260717-1950-01-plain-old.prompt.md"]
    assert e3.id6 is None
    assert e3.status == "superseded"
    assert e3.date == "20260717"

    rendered_json = json.loads(prompts_index.build_index_json(entries))
    assert len(rendered_json) == 3
    rendered_md = prompts_index.build_index_md(entries)
    assert "## seta" in rendered_md
    assert "prm101" in rendered_md

    # Mismatched filename id6 / set vs metadata comment must emit name-metadata-mismatch
    (prompts_dir / "pending" / "20260920-setb-01-xyz111-badmeta.prompt.md").write_text(
        "<!-- aw-prompt: Kind: research | Id: dif999 | Set: setc | Order: 01 | Status: pending | Slug: badmeta -->\n\nBody.\n",
        encoding="utf-8",
    )
    drift_after = prompts_index.check_drift(repo, prompts_dir)
    mismatches = [d for d in drift_after if d.rule == "name-metadata-mismatch"]
    assert any("xyz111" in d.detail and "dif999" in d.detail for d in mismatches)
    assert any("setb" in d.detail and "setc" in d.detail for d in mismatches)


def test_research_readers_answer_without_index_files_from_log_format_meta(
    tmp_path: Path,
) -> None:
    """Verify AC-9: research readers answer from artifact_meta.query on log-format metadata without INDEX files."""
    from agent_workflows import artifact_meta

    repo, research_dir, _prompts_dir = _build_records_repo(tmp_path)
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    # 1. Research report backed by seq=1 create log + 4.1 two-key mirror and banner
    rpt_rel = "research/20260110-logr01-01-lrp001-findings.research-report.md"
    rpt_path = repo / ".aw" / "records" / rpt_rel
    rpt_path.write_text(
        artifact_meta.render_in_file_mirror("lrp001", "research", "todo")
        + "\n# Log Report\n\nObserved content.\n",
        encoding="utf-8",
    )
    (meta_dir / "lrp001.jsonl").write_text(
        artifact_meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-01-10T00:00:00Z",
                "actor": {"tool": "aw"},
                "op": "create",
                "path": rpt_rel,
                "fields": {
                    "type": "research",
                    "title": "Log Report",
                    "set": "logr01",
                    "order": 1,
                    "research_kind": "research-report",
                    "status": "todo",
                    "outcome": "none-yet",
                    "created": "20260110",
                    "summary": "Log-format research report",
                    "topic": ["metastore", "cache"],
                    "consumed_by": [],
                    "priority": "medium",
                },
            }
        ),
        encoding="utf-8",
    )

    # 2. Archived-but-cited research doc backed by seq=0 checkpoint log (migrated shape)
    arc_rel = "research/archive/202601/20260105-logr02-00-lar001-archived.notes.md"
    arc_path = repo / ".aw" / "records" / arc_rel
    arc_path.parent.mkdir(parents=True, exist_ok=True)
    arc_path.write_text(
        artifact_meta.render_in_file_mirror("lar001", "research", "archive")
        + "\n# Archived Notes\n",
        encoding="utf-8",
    )
    (meta_dir / "lar001.jsonl").write_text(
        artifact_meta.encode_event(
            {
                "v": 1,
                "seq": 0,
                "append": 0,
                "at": "2026-01-05T00:00:00Z",
                "actor": {"tool": "aw"},
                "op": "checkpoint",
                "path": arc_rel,
                "fields": {
                    "type": "research",
                    "title": "Archived Notes",
                    "set": "logr02",
                    "order": 0,
                    "research_kind": "notes",
                    "status": "archive",
                    "outcome": "adopted",
                    "created": "20260105",
                    "summary": "Migrated archived note",
                    "topic": ["archive"],
                    "consumed_by": ["lsp001"],
                },
            }
        ),
        encoding="utf-8",
    )

    # 3. Implemented spec backed by log-format metadata citing RSCH-lrp001
    spec_rel = "specs/20260112-logr01-01-lsp001-log-spec.spec.md"
    spec_path = repo / ".aw" / "records" / spec_rel
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        artifact_meta.render_in_file_mirror("lsp001", "spec", "implemented")
        + "\n# Log Spec\n\nCites RSCH-lrp001.\n",
        encoding="utf-8",
    )
    (meta_dir / "lsp001.jsonl").write_text(
        artifact_meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-01-12T00:00:00Z",
                "actor": {"tool": "aw"},
                "op": "create",
                "path": spec_rel,
                "fields": {
                    "type": "spec",
                    "title": "Log Spec",
                    "set": "logr01",
                    "order": 1,
                    "status": "implemented",
                },
            }
        ),
        encoding="utf-8",
    )

    assert not (research_dir / "INDEX.json").exists()
    assert not (research_dir / "INDEX.md").exists()

    entries, drift = research_index._scan_docs(research_dir, repo_root=repo)
    assert drift == []
    by_id = {e.id6: e for e in entries}
    assert set(by_id) == {"lrp001", "lar001"}
    assert by_id["lrp001"].status == "todo"
    assert by_id["lrp001"].topic == ["metastore", "cache"]
    assert by_id["lrp001"].priority == "medium"
    assert by_id["lrp001"].has_body is True
    assert by_id["lar001"].status == "archive"
    assert by_id["lar001"].consumed_by == ["lsp001"]

    assert "lsp001" in research_index.resolvable_consumer_ids(repo)
    assert "lrp001" in research_index.cited_by_executed_ids(repo, research_dir)

    assert research_archive.find_miscategorized(repo, research_dir) == ["lar001"]
    mv, err = research_archive.plan_transition(research_dir, "lrp001", "reference")
    assert err is None
    assert mv is not None
    assert mv.new_path.parent.as_posix().endswith("reference/202601")


def test_prompts_readers_answer_without_index_files_from_log_format_meta(
    tmp_path: Path,
) -> None:
    """Verify AC-9: prompts readers answer from artifact_meta.query on log-format metadata without INDEX files."""
    from agent_workflows import artifact_meta

    repo, _research_dir, prompts_dir = _build_records_repo(tmp_path)
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    p_rel = "prompts/pending/20261110-logp01-01-lpr001-log-prompt.prompt.md"
    p_path = repo / ".aw" / "records" / p_rel
    p_path.parent.mkdir(parents=True, exist_ok=True)
    p_path.write_text(
        artifact_meta.render_in_file_mirror("lpr001", "prompt", "pending")
        + "\nPrompt body without legacy aw-prompt comment.\n",
        encoding="utf-8",
    )
    (meta_dir / "lpr001.jsonl").write_text(
        artifact_meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-10T00:00:00Z",
                "actor": {"tool": "aw"},
                "op": "create",
                "path": p_rel,
                "fields": {
                    "type": "prompt",
                    "title": "Log Prompt",
                    "set": "logp01",
                    "order": 1,
                    "prompt_kind": "research",
                    "status": "pending",
                    "created_day": "2026-11-10",
                    "filename_date": "20261110",
                },
            }
        ),
        encoding="utf-8",
    )

    assert not (prompts_dir / "INDEX.json").exists()
    assert not (prompts_dir / "INDEX.md").exists()

    entries, drift = prompts_index.scan_prompts(prompts_dir)
    assert drift == []
    assert len(entries) == 1
    e = entries[0]
    assert e.id6 == "lpr001"
    assert e.set_id == "logp01"
    assert e.order == 1
    assert e.kind == "research"
    assert e.status == "pending"
    assert e.date == "2026-11-10"
    assert e.slug == "log-prompt"


@pytest.mark.parametrize("shape", ["banner", "no_banner"])
@pytest.mark.parametrize("expected_position", ["unrun", "partial", "synthesized"])
def test_research_banner_pipeline_position(
    tmp_path: Path, shape: str, expected_position: str
) -> None:
    """E-03 (F-09): research has_body ignores the 4.1 aw-managed banner in post-cutover and pre-cutover shapes."""
    from agent_workflows import artifact_meta

    repo, research_dir, _prompts_dir = _build_records_repo(tmp_path)
    meta_dir = repo / ".aw" / "records" / "meta"

    def _add_doc(
        *,
        order: int,
        id6: str,
        slug: str,
        kind: str,
        status: str | None,
        body: str,
    ) -> None:
        name = research_contract.format_name(
            research_contract.ResearchName(
                date="20261109",
                set_id="bset01",
                order=f"{order:02d}",
                id6=id6,
                slug=slug,
                model=None,
                kind=kind,
            )
        )
        doc_path = research_dir / name
        if shape == "banner":
            meta_dir.mkdir(parents=True, exist_ok=True)
            mirror = artifact_meta.render_in_file_mirror(id6, "research", status)
            doc_path.write_text(mirror + body, encoding="utf-8")
            fields: dict[str, object] = {
                "type": "research",
                "title": f"Doc {id6}",
                "set": "bset01",
                "order": order,
                "research_kind": kind,
                "outcome": "none-yet",
                "created": "20261109",
                "summary": f"summary {id6}",
                "topic": ["banner"],
                "consumed_by": [],
            }
            if status is not None:
                fields["status"] = status
            (meta_dir / f"{id6}.jsonl").write_text(
                artifact_meta.encode_event(
                    {
                        "v": 1,
                        "seq": 1,
                        "append": 1,
                        "at": "2026-11-09T00:00:00Z",
                        "actor": {"tool": "aw"},
                        "op": "create",
                        "path": f"research/{name}",
                        "fields": fields,
                    }
                ),
                encoding="utf-8",
            )
        else:
            fm = research_cmd.build_frontmatter(
                id6=id6,
                created="20261109",
                set_id="bset01",
                order=f"{order:02d}",
                topic=["pre"],
                model=None,
                kind=kind,
                status=status,
                outcome="none-yet",
                summary=f"summary {id6}",
            )
            doc_path.write_text(fm + body, encoding="utf-8")

    # Tree 1 (unrun): research-prompt (outcome: none-yet) + reconciliation-report with no real body
    _add_doc(
        order=0,
        id6="bpr001",
        slug="prompt",
        kind="research-prompt",
        status=None,
        body="",
    )
    recon_body = (
        "\n# Reconciliation Heading\n" if expected_position == "synthesized" else ""
    )
    _add_doc(
        order=2,
        id6="brc001",
        slug="reconcile",
        kind="reconciliation-report",
        status="todo",
        body=recon_body,
    )
    # Tree 2 (partial) & Tree 3 (synthesized): add a research-report with a heading
    if expected_position in ("partial", "synthesized"):
        _add_doc(
            order=1,
            id6="brp001",
            slug="report",
            kind="research-report",
            status="todo",
            body="\n# Report Heading\n",
        )

    entries, drift = research_index._scan_docs(research_dir, repo_root=repo)
    assert drift == []
    positions = research_index.derive_pipeline_positions(entries)
    assert positions.get("bset01") == expected_position


def test_research_body_preserves_arbitrary_html_comment() -> None:
    """Only a single leading 4.1 aw-managed comment is ignored; arbitrary HTML comments count as body."""
    from agent_workflows import artifact_meta

    mirror = artifact_meta.render_in_file_mirror("cmt001", "research", "todo")
    assert research_index.has_research_body(mirror) is False
    assert research_index.has_research_body(mirror + "\n   \n") is False
    assert research_index.has_research_body(mirror + "<!-- user note -->\n") is True
    assert (
        research_index.has_research_body(
            "---\nid: cmt001\nstatus: todo\n---\n<!-- user note -->\n"
        )
        is True
    )
    # A second aw-managed comment is not stripped
    second = "<!-- aw-managed: second comment -->\n"
    assert research_index.has_research_body(mirror + second) is True
