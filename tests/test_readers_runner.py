"""Behavioral pinning tests for runner metadata readers (IPD k86yq7 E-02).

Pins observable behavior of the runner metadata readers across both host drivers
(`runner_shared`, `oc_runipd`, `agy_runipd`) and `plan_readiness.is_plan_review_approved`
before moving the plan-selection reads onto `artifact_meta`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agent_workflows import (
    agy_runipd,
    ipd_schema,
    oc_runipd,
    plan_readiness,
    runner_shared,
)

pytestmark = pytest.mark.core


def _valid_ipd_text(
    *,
    id6: str,
    status: str = "approved",
    kind: str = "child",
    setid: str = "alpha",
    set_desc: str = "",
    order: int = 1,
    deps: str = "none",
    from_backlog: str | None = None,
    readiness: str | None = None,
    attended: str | None = None,
    history_lines: tuple[str, ...] = ("- 2026-11-01 to-review (tester): created.",),
    bullet_prefix: str = "- ",
) -> str:
    set_val = f"{setid} ({set_desc})" if set_desc else setid
    lines = [
        f"# IPD: Plan {id6}",
        "",
        f"{bullet_prefix}Date: 2026-11-01",
        f"{bullet_prefix}Kind: {kind}",
        f"{bullet_prefix}Concern: Pin runner metadata reads.",
        f"{bullet_prefix}Scope: Pin runner metadata reads.",
        f"{bullet_prefix}Scope-Paths: agent_workflows/runner_shared.py",
        f"{bullet_prefix}Item-Dependencies: {deps}",
        f"{bullet_prefix}Status: {status}",
    ]
    if readiness is not None:
        lines.append(f"{bullet_prefix}Readiness: {readiness}")
    if attended is not None:
        lines.append(f"{bullet_prefix}Attended: {attended}")
    lines.extend(
        [
            f"{bullet_prefix}Work-Kind: chore",
            f"{bullet_prefix}Priority: medium",
            f"{bullet_prefix}Set: {set_val}",
            f"{bullet_prefix}Order: {order:02d}",
            f"{bullet_prefix}Highest E allocated: 01",
            f"{bullet_prefix}Author: tester",
            f"{bullet_prefix}Id: {id6}",
        ]
    )
    if from_backlog is not None:
        lines.append(f"{bullet_prefix}From-Backlog: {from_backlog}")
    lines.extend(
        [
            "",
            "## Workflow history",
            *history_lines,
            "",
            "## Goal",
            "",
            "Pin runner behavior.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "",
            "### Task group 1: pin",
            "",
            "- [ ] E-01 Pin the reader.",
            "  - Depends on: none",
            "  - Expected outcome: pinned.",
            "  - Execution state: pending",
            "",
            "## Project conventions discovered (Step 0)",
            "",
            "- None.",
            "",
            "## Findings",
            "",
            "- None.",
            "",
            "## Proposed changes (ordered, validatable)",
            "",
            "1. Pin.",
            "",
            "## Deferred / out of scope (with reason)",
            "",
            "- None.",
            "",
            "## Scope check",
            "",
            "- Over-scope: none.",
            "- Under-scope: none.",
            "",
            "## Required tests / validation",
            "",
            "- `python3 -m pytest`",
            "",
            "## Spec / documentation sync",
            "",
            "- None.",
            "",
            "## Open questions",
            "",
            "- None.",
            "",
            "## Validation and cross-check (verify before reporting done)",
            "",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: paste test output.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "- Size assessment: small",
            "- Cohesion rationale: not required",
            "",
        ]
    )
    return "\n".join(lines)


def _valid_spec_text(
    *, id6: str, status: str = "to-review", setid: str | None = None
) -> str:
    sid = setid or id6
    return (
        f"# Spec: Sample {id6}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"- Set: {sid}\n"
        f"- Date: 2026-11-01\n\n"
        "## Workflow history\n"
        f"- 2026-11-01 {status} (tester): created.\n\n"
        "## Requirements\n"
        "- R-01 Must behave.\n"
    )


def _valid_backlog_text(
    *,
    id6: str,
    status: str = "open",
    setid: str | None = None,
    work_kind: str = "chore",
    priority: str = "medium",
) -> str:
    sid = setid or id6
    return (
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"- Set: {sid}\n"
        f"- Priority: {priority}\n"
        f"- Work-Kind: {work_kind}\n"
        f"- Summary: Sample backlog {id6}\n\n"
        "## Workflow history\n"
        f"- 2026-11-01 {status} (tester): created.\n"
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    recs = repo / ".aw" / "records"
    for sub in (
        "plans/pending",
        "plans/executed",
        "plans/superseded",
        "specs/to-review",
        "specs/reviewed",
        "specs/approved",
        "backlog/open",
        "backlog/graduated",
        "backlog/done",
        "reviews",
    ):
        (recs / sub).mkdir(parents=True, exist_ok=True)
    return repo


def test_parse_plan_file_both_hosts_fields(tmp_path: Path) -> None:
    """Pins runner_shared/oc_runipd/agy_runipd.parse_plan_file fields, loose whitespace, multi-word status, and fallbacks."""
    assert oc_runipd.parse_plan_file is runner_shared.parse_plan_file
    assert agy_runipd.parse_plan_file is runner_shared.parse_plan_file

    repo = _make_repo(tmp_path)
    pdir = repo / ".aw" / "records" / "plans" / "pending"

    # Full fields on both hosts
    plan_full = pdir / "20261101-alpha-02-pln001-full-fields.ipd.md"
    plan_full.write_text(
        _valid_ipd_text(
            id6="pln001",
            status="approved",
            kind="child",
            setid="alpha",
            set_desc="Alpha Set",
            order=2,
            deps="executed:dep001, exists:spec:spc001, state:backlog:open:bkl001",
            from_backlog="bkl001",
            attended="required",
        ),
        encoding="utf-8",
    )

    for fn in (
        runner_shared.parse_plan_file,
        oc_runipd.parse_plan_file,
        agy_runipd.parse_plan_file,
    ):
        rec = fn(plan_full, repo)
        assert rec is not None
        assert rec.id6 == "pln001"
        assert rec.status == "approved"
        assert rec.kind == "child"
        assert rec.setid == "alpha"
        assert rec.order == 2
        assert rec.dependencies == [
            "executed:dep001",
            "exists:spec:spc001",
            "state:backlog:open:bkl001",
        ]
        assert rec.dependency_error is None
        assert rec.from_backlog == "bkl001"
        assert rec.rel_path == (
            ".aw/records/plans/pending/20261101-alpha-02-pln001-full-fields.ipd.md"
        )

    # Loose leading whitespace (`-  ` and `-\t`)
    for tag, prefix in (("two_spaces", "-  "), ("tab", "-\t")):
        lp = pdir / f"20261101-loose-03-lse{tag[0]}01-loose.ipd.md"
        lp.write_text(
            f"{prefix}Id: lse{tag[0]}01\n"
            f"{prefix}Status: reviewed\n"
            f"{prefix}Kind: orchestrator\n"
            f"{prefix}Set: loose\n"
            f"{prefix}Order: 03\n\n## Goal\nLoose.\n",
            encoding="utf-8",
        )
        for fn in (oc_runipd.parse_plan_file, agy_runipd.parse_plan_file):
            rec = fn(lp, repo)
            assert rec is not None
            assert (rec.id6, rec.status, rec.kind, rec.setid, rec.order) == (
                f"lse{tag[0]}01",
                "reviewed",
                "orchestrator",
                "loose",
                3,
            )

    # Multi-word status in pending/: under D-1 normalizes first token ("executed").
    mw = pdir / "20261101-mwset-01-mw0001-multiword.ipd.md"
    mw.write_text(
        "# IPD: Multiword\n\n"
        "- Id: mw0001\n"
        "- Status: EXECUTED (approved by maintainer)\n"
        "- Set: mwset\n"
        "- Order: 01\n\n## Goal\nMulti.\n",
        encoding="utf-8",
    )
    mw_rec = runner_shared.parse_plan_file(mw, repo)
    assert mw_rec is not None
    assert mw_rec.status == "executed"

    # Fallbacks when Set, Order, Id are absent (filename, then path hash)
    fn_only = pdir / "20261101-fnset-07-fn0007-from-filename.ipd.md"
    fn_only.write_text(
        "# IPD: Filename fallback\n\n## Goal\nFallback.\n", encoding="utf-8"
    )
    fn_rec = runner_shared.parse_plan_file(fn_only, repo)
    assert fn_rec is not None
    assert (fn_rec.id6, fn_rec.setid, fn_rec.order, fn_rec.status) == (
        "fn0007",
        "fnset",
        7,
        "pending",
    )

    bare = pdir / "bareplan.md"
    bare.write_text("# IPD: Bare\n\n## Goal\nBare.\n", encoding="utf-8")
    bare_rec = runner_shared.parse_plan_file(bare, repo)
    assert bare_rec is not None
    expected_hash = hashlib.sha256(
        ".aw/records/plans/pending/bareplan.md".encode("utf-8")
    ).hexdigest()[:6]
    assert (bare_rec.id6, bare_rec.setid, bare_rec.order, bare_rec.status) == (
        expected_hash,
        "standalone",
        99,
        "pending",
    )

    # Host re-exports for _read_id, _SET_RE, _ORDER_RE, _KIND_RE
    assert oc_runipd._read_id("-  Id: abc123\n") == "abc123"
    assert agy_runipd._read_id("-\tId: abc123\n") == "abc123"
    assert hasattr(oc_runipd, "_SET_RE") and hasattr(agy_runipd, "_SET_RE")
    assert hasattr(oc_runipd, "_ORDER_RE") and hasattr(agy_runipd, "_ORDER_RE")
    assert hasattr(oc_runipd, "_KIND_RE")


def test_hold_attended_plan_pins_attended_field(tmp_path: Path) -> None:
    """Pins Attended metadata handling at queue build via hold_attended_plan."""
    repo = _make_repo(tmp_path)
    pdir = repo / ".aw" / "records" / "plans" / "pending"
    att_plan = pdir / "20261101-attset-01-att001-needs-human.ipd.md"
    att_plan.write_text(
        _valid_ipd_text(id6="att001", status="approved", attended="required"),
        encoding="utf-8",
    )
    normal_plan = pdir / "20261101-attset-02-att002-normal.ipd.md"
    normal_plan.write_text(
        _valid_ipd_text(id6="att002", status="approved"),
        encoding="utf-8",
    )

    headless_entry = {"id6": "att001", "action": "execute", "status": "queued"}
    assert (
        runner_shared.hold_attended_plan(headless_entry, att_plan, interactive=False)
        is True
    )
    assert headless_entry["status"] == "not-run"
    assert headless_entry[runner_shared.NEEDS_INPUT_KEY] is True

    interactive_entry = {"id6": "att001", "action": "execute", "status": "queued"}
    assert (
        runner_shared.hold_attended_plan(interactive_entry, att_plan, interactive=True)
        is False
    )
    assert interactive_entry.get(runner_shared.ATTENDED_KEY) is True

    normal_entry = {"id6": "att002", "action": "execute", "status": "queued"}
    assert (
        runner_shared.hold_attended_plan(normal_entry, normal_plan, interactive=False)
        is False
    )
    assert normal_entry["status"] == "queued"


def test_discover_plans_returns_all_plan_records(tmp_path: Path) -> None:
    """Pins runner_shared.discover_plans across pending/ and executed/ while ignoring index files."""
    repo = _make_repo(tmp_path)
    plans_root = repo / ".aw" / "records" / "plans"
    (plans_root / "README.md").write_text("# Plans README\n", encoding="utf-8")
    (plans_root / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (plans_root / "STATUS.md").write_text("# Status\n", encoding="utf-8")

    (plans_root / "pending" / "20261101-s1-01-dp0001-first.ipd.md").write_text(
        _valid_ipd_text(id6="dp0001", status="approved", setid="s1", order=1),
        encoding="utf-8",
    )
    (plans_root / "executed" / "20261101-s1-02-dp0002-second.ipd.md").write_text(
        _valid_ipd_text(
            id6="dp0002",
            status="executed",
            setid="s1",
            order=2,
            deps="executed:dp0001",
        ),
        encoding="utf-8",
    )

    discovered = runner_shared.discover_plans(repo)
    assert set(discovered.keys()) == {"dp0001", "dp0002"}
    assert discovered["dp0001"].status == "approved"
    assert discovered["dp0001"].setid == "s1"
    assert discovered["dp0001"].order == 1
    assert discovered["dp0002"].status == "executed"
    assert discovered["dp0002"].dependencies == ["executed:dp0001"]


def test_discover_specs_returns_spec_records_and_skips_idless(tmp_path: Path) -> None:
    """Pins runner_shared.discover_specs returning id6 -> SpecRecord and skipping id-less legacy specs."""
    repo = _make_repo(tmp_path)
    specs_root = repo / ".aw" / "records" / "specs"
    (specs_root / "to-review" / "20261101-sp0001-01-sp0001-alpha.spec.md").write_text(
        _valid_spec_text(id6="sp0001", status="to-review"),
        encoding="utf-8",
    )
    (specs_root / "approved" / "20261101-sp0002-01-sp0002-beta.spec.md").write_text(
        _valid_spec_text(id6="sp0002", status="approved"),
        encoding="utf-8",
    )
    (specs_root / "approved" / "20260801-1200-01-legacy-idless.spec.md").write_text(
        "# Spec: Legacy\n\n- Status: approved\n",
        encoding="utf-8",
    )

    specs = runner_shared.discover_specs(repo)
    assert set(specs.keys()) == {"sp0001", "sp0002"}
    assert specs["sp0001"].status == "to-review"
    assert specs["sp0001"].file == (
        ".aw/records/specs/to-review/20261101-sp0001-01-sp0001-alpha.spec.md"
    )
    assert specs["sp0002"].status == "approved"


def test_edge_satisfied_executed_exists_and_state(tmp_path: Path) -> None:
    """Pins runner_shared.edge_satisfied for executed:, exists:, and state: edges."""
    repo = _make_repo(tmp_path)
    plans_root = repo / ".aw" / "records" / "plans"
    (plans_root / "executed" / "20261101-es-01-ed0001-done.ipd.md").write_text(
        _valid_ipd_text(
            id6="ed0001",
            status="EXECUTED (approved by maintainer)",
            setid="es",
            order=1,
        ),
        encoding="utf-8",
    )
    (plans_root / "pending" / "20261101-es-02-ed0002-reviewed.ipd.md").write_text(
        _valid_ipd_text(id6="ed0002", status="reviewed", setid="es", order=2),
        encoding="utf-8",
    )
    (plans_root / "pending" / "20261101-es-03-ed0003-toreview.ipd.md").write_text(
        _valid_ipd_text(id6="ed0003", status="to-review", setid="es", order=3),
        encoding="utf-8",
    )
    (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / "20261101-sp0010-01-sp0010-core.spec.md"
    ).write_text(_valid_spec_text(id6="sp0010", status="approved"), encoding="utf-8")
    (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-bk0010-01-bk0010-item.backlog.md"
    ).write_text(_valid_backlog_text(id6="bk0010", status="open"), encoding="utf-8")

    state = {"repo": str(repo), "queue": [], "options": {}}
    exec_item = {"action": "execute"}
    rev_item = {"action": "review"}

    def _edge(tok: str):
        e, err = ipd_schema._parse_item_dependency_edge(tok)
        assert err is None and e is not None
        return e

    # executed: against terminal executed/ (even with multi-word status)
    ok, _ = runner_shared.edge_satisfied(_edge("executed:ed0001"), exec_item, state, {})
    assert ok is True

    # executed: against pending reviewed plan -> False for execute, True for review
    ok_exec, _ = runner_shared.edge_satisfied(
        _edge("executed:ed0002"), exec_item, state, {}
    )
    ok_rev, _ = runner_shared.edge_satisfied(
        _edge("executed:ed0002"), rev_item, state, {}
    )
    assert ok_exec is False
    assert ok_rev is True

    # executed: against pending to-review plan -> False for review unless review_unreviewed_deps
    ok_rev_strict, _ = runner_shared.edge_satisfied(
        _edge("executed:ed0003"), rev_item, state, {}
    )
    assert ok_rev_strict is False
    state_relaxed = {
        "repo": str(repo),
        "queue": [],
        "options": {"review_unreviewed_deps": True},
    }
    ok_rev_relaxed, _ = runner_shared.edge_satisfied(
        _edge("executed:ed0003"), rev_item, state_relaxed, {}
    )
    assert ok_rev_relaxed is True

    # exists: edge
    ok_exists, _ = runner_shared.edge_satisfied(
        _edge("exists:spec:sp0010"), exec_item, state, {}
    )
    ok_missing, _ = runner_shared.edge_satisfied(
        _edge("exists:spec:zzz999"), exec_item, state, {}
    )
    assert ok_exists is True
    assert ok_missing is False

    # state: edge
    ok_state_hit, _ = runner_shared.edge_satisfied(
        _edge("state:backlog:open:bk0010"), exec_item, state, {}
    )
    ok_state_miss, _ = runner_shared.edge_satisfied(
        _edge("state:backlog:done:bk0010"), exec_item, state, {}
    )
    assert ok_state_hit is True
    assert ok_state_miss is False


def test_resolve_backlog_item_finds_by_declared_id(tmp_path: Path) -> None:
    """Pins runner_shared.resolve_backlog_item finding items by declared - Id: even when filename differs."""
    repo = _make_repo(tmp_path)
    target = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-other-01-zzz111-renamed.backlog.md"
    )
    target.write_text(
        _valid_backlog_text(id6="bk0101", status="open"), encoding="utf-8"
    )

    found = runner_shared.resolve_backlog_item(repo, "bk0101")
    assert found is not None
    assert found.resolve() == target.resolve()
    assert runner_shared.resolve_backlog_item(repo, "no9999") is None


def test_backlog_item_paths_for_id_returns_sorted_paths(tmp_path: Path) -> None:
    """Pins runner_shared.backlog_item_paths_for_id returning sorted repo-relative paths."""
    repo = _make_repo(tmp_path)
    p_open = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261101-dup-01-bk0202-item.backlog.md"
    )
    p_done = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "done"
        / "20261101-dup-01-bk0202-item.backlog.md"
    )
    p_open.write_text(
        _valid_backlog_text(id6="bk0202", status="open"), encoding="utf-8"
    )
    p_done.write_text(
        _valid_backlog_text(id6="bk0202", status="done"), encoding="utf-8"
    )

    paths = runner_shared.backlog_item_paths_for_id(repo, "bk0202")
    assert paths == [
        ".aw/records/backlog/done/20261101-dup-01-bk0202-item.backlog.md",
        ".aw/records/backlog/open/20261101-dup-01-bk0202-item.backlog.md",
    ]
    assert runner_shared.backlog_item_paths_for_id(repo, "no9999") == []


def test_read_set_membership_returns_orchestrator_and_children(tmp_path: Path) -> None:
    """Pins runner_shared.read_set_membership reading orchestrator and children across pending/ and executed/."""
    repo = _make_repo(tmp_path)
    plans_root = repo / ".aw" / "records" / "plans"
    (plans_root / "pending" / "20261101-myset-00-ms0000-orch.ipd.md").write_text(
        _valid_ipd_text(
            id6="ms0000", status="approved", kind="orchestrator", setid="myset", order=0
        ),
        encoding="utf-8",
    )
    (plans_root / "executed" / "20261101-myset-01-ms0001-first.ipd.md").write_text(
        _valid_ipd_text(
            id6="ms0001", status="executed", kind="child", setid="myset", order=1
        ),
        encoding="utf-8",
    )
    (plans_root / "pending" / "20261101-myset-02-ms0002-second.ipd.md").write_text(
        _valid_ipd_text(
            id6="ms0002", status="approved", kind="child", setid="myset", order=2
        ),
        encoding="utf-8",
    )

    membership = runner_shared.read_set_membership(repo, "myset")
    assert membership.setid == "myset"
    assert membership.orchestrator is not None
    assert membership.orchestrator.id6 == "ms0000"
    assert membership.orchestrator.kind == "orchestrator"
    assert membership.orchestrator.status == "approved"
    assert [(c.id6, c.order, c.status) for c in membership.children] == [
        ("ms0001", 1, "executed"),
        ("ms0002", 2, "approved"),
    ]


def test_expand_selectors_id6_set_and_status(tmp_path: Path) -> None:
    """Pins expand_selectors on both hosts for id6, Set, and status selectors ('reviews', 'all')."""
    repo = _make_repo(tmp_path)
    plans_root = repo / ".aw" / "records" / "plans"
    (plans_root / "pending" / "20261101-selset-01-ex0001-torev.ipd.md").write_text(
        _valid_ipd_text(id6="ex0001", status="to-review", setid="selset", order=1),
        encoding="utf-8",
    )
    (plans_root / "pending" / "20261101-selset-02-ex0002-appr.ipd.md").write_text(
        _valid_ipd_text(id6="ex0002", status="approved", setid="selset", order=2),
        encoding="utf-8",
    )
    (plans_root / "superseded" / "20261101-selset-03-ex0003-sup.ipd.md").write_text(
        _valid_ipd_text(id6="ex0003", status="superseded", setid="selset", order=3),
        encoding="utf-8",
    )

    discovered = runner_shared.discover_plans(repo)
    manifest = runner_shared.build_dynamic_manifest(repo, discovered)

    for host in (oc_runipd, agy_runipd):
        assert host.expand_selectors(manifest, ["ex0002"], repo) == ["ex0002"]
        assert host.expand_selectors(manifest, ["selset"], repo) == ["ex0001", "ex0002"]
        assert host.expand_selectors(manifest, ["reviews"], repo) == ["ex0001"]
        assert host.expand_selectors(manifest, ["all"], repo) == ["ex0001", "ex0002"]


def test_plan_bucket_identifies_lifecycle_directory(tmp_path: Path) -> None:
    """Pins runner_shared.plan_bucket across lifecycle directory segments."""
    for seg in (
        "executed",
        "active",
        "pending",
        "reviewed",
        "approved",
        "reusable",
        "superseded",
        "not-executed",
    ):
        assert (
            runner_shared.plan_bucket(tmp_path / "plans" / seg / "plan.ipd.md") == seg
        )
    assert runner_shared.plan_bucket(tmp_path / "other" / "plan.ipd.md") is None


def test_reconcile_disposition_review_and_execute(tmp_path: Path) -> None:
    """Pins runner_shared.reconcile_disposition for plan review, re-review, spec review, and execute."""
    repo = _make_repo(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

    # 1. Plan review that reached 'reviewed' with positive evidence (attempt log)
    p_rev = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-rc-01-rc0001-rev.ipd.md"
    )
    p_rev.write_text(
        _valid_ipd_text(
            id6="rc0001",
            status="reviewed",
            setid="rc",
            readiness="go-pending-approval",
            history_lines=(
                "- 2026-11-01 reviewed (reviewer): APPROVE.",
                "- 2026-11-01 to-review (tester): created.",
            ),
        ),
        encoding="utf-8",
    )
    log_file = run_dir / "logs" / "01-rc0001-attempt-1.jsonl"
    log_file.write_text(
        json.dumps({"type": "text", "text": "reviewed"}) + "\n", encoding="utf-8"
    )
    rev_item = {
        "id6": "rc0001",
        "position": 1,
        "action": "review",
        "artifact_type": "ipd",
        "configured_file": ".aw/records/plans/pending/20261101-rc-01-rc0001-rev.ipd.md",
        "attempts": [{"attempt": 1, "log": str(log_file)}],
    }
    disp, _ = runner_shared.reconcile_disposition(repo, rev_item, run_dir, exit_code=0)
    assert disp == "reviewed"

    # 2. Plan re-review missing Readiness -> fail-gate
    p_rerev = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-rc-02-rc0002-rerev.ipd.md"
    )
    p_rerev.write_text(
        _valid_ipd_text(id6="rc0002", status="reviewed", setid="rc", order=2),
        encoding="utf-8",
    )
    rerev_item = {
        "id6": "rc0002",
        "position": 2,
        "action": "review",
        "artifact_type": "ipd",
        "rereview": True,
        "configured_file": ".aw/records/plans/pending/20261101-rc-02-rc0002-rerev.ipd.md",
        "attempts": [{"attempt": 1, "log": str(log_file)}],
    }
    disp_rerev, _ = runner_shared.reconcile_disposition(
        repo, rerev_item, run_dir, exit_code=0
    )
    assert disp_rerev == "fail-gate"

    # 3. Spec review still to-review -> fail-gate
    s_path = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "to-review"
        / "20261101-sp0303-01-sp0303-spec.spec.md"
    )
    s_path.write_text(
        _valid_spec_text(id6="sp0303", status="to-review"), encoding="utf-8"
    )
    spec_item = {
        "id6": "sp0303",
        "position": 3,
        "action": "review",
        "artifact_type": "spec",
        "configured_file": ".aw/records/specs/to-review/20261101-sp0303-01-sp0303-spec.spec.md",
    }
    disp_spec, _ = runner_shared.reconcile_disposition(
        repo, spec_item, run_dir, exit_code=0
    )
    assert disp_spec == "fail-gate"

    # 4. Executed plan in executed/ -> executed
    p_exec = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / "20261101-rc-04-rc0004-exec.ipd.md"
    )
    p_exec.write_text(
        _valid_ipd_text(id6="rc0004", status="executed", setid="rc", order=4),
        encoding="utf-8",
    )
    exec_item = {
        "id6": "rc0004",
        "position": 4,
        "action": "execute",
        "artifact_type": "ipd",
        "configured_file": ".aw/records/plans/executed/20261101-rc-04-rc0004-exec.ipd.md",
    }
    disp_exec, _ = runner_shared.reconcile_disposition(
        repo, exec_item, run_dir, exit_code=0
    )
    assert disp_exec == "executed"


def test_enforce_freeze_time_refusal_checks_dependencies_and_status(
    tmp_path: Path,
) -> None:
    """Pins runner_shared.enforce_freeze_time_refusal on satisfied vs unsatisfiable dependencies."""
    repo = _make_repo(tmp_path)
    plans_root = repo / ".aw" / "records" / "plans"
    p_dep = plans_root / "pending" / "20261101-fz-01-fz0001-dep.ipd.md"
    p_dep.write_text(
        _valid_ipd_text(id6="fz0001", status="to-review", setid="fz", order=1),
        encoding="utf-8",
    )
    p_child = plans_root / "pending" / "20261101-fz-02-fz0002-child.ipd.md"
    p_child.write_text(
        _valid_ipd_text(
            id6="fz0002",
            status="approved",
            setid="fz",
            order=2,
            deps="executed:fz0001",
            readiness="go-pending-approval",
            history_lines=(
                "- 2026-11-01 approved (human): approved.",
                "- 2026-11-01 reviewed (reviewer): APPROVE.",
            ),
        ),
        encoding="utf-8",
    )

    queue = [
        {
            "id6": "fz0002",
            "artifact_type": "ipd",
            "initial_status": "approved",
            "status": "queued",
            "action": "execute",
            "configured_file": ".aw/records/plans/pending/20261101-fz-02-fz0002-child.ipd.md",
            "dependencies": ["executed:fz0001"],
        }
    ]
    with pytest.raises(runner_shared.DriverError) as exc_info:
        runner_shared.enforce_freeze_time_refusal(queue, repo=repo, color=False)
    assert "fz0001" in str(exc_info.value)
    assert "to-review" in str(exc_info.value)


def test_is_plan_review_approved_refuses_missing_and_unattested_readiness(
    tmp_path: Path,
) -> None:
    """Pins plan_readiness.is_plan_review_approved (4.4a row l56tyz): missing or unattested readiness is refused."""
    repo = _make_repo(tmp_path)
    pdir = repo / ".aw" / "records" / "plans" / "pending"

    # Missing readiness with no review record -> refused
    p_missing = pdir / "20261101-rd-01-rd0001-missing.ipd.md"
    p_missing.write_text(
        _valid_ipd_text(
            id6="rd0001",
            status="reviewed",
            readiness=None,
            history_lines=("- 2026-11-01 to-review (tester): created.",),
        ),
        encoding="utf-8",
    )
    assert plan_readiness.is_plan_review_approved(p_missing) is False

    # Missing readiness with forged APPROVE word in a non-review history line -> refused (l56tyz)
    p_forged_prose = pdir / "20261101-rd-02-rd0002-forged-prose.ipd.md"
    p_forged_prose.write_text(
        _valid_ipd_text(
            id6="rd0002",
            status="reviewed",
            readiness=None,
            history_lines=("- 2026-11-01 to-review (tester): please APPROVE this.",),
        ),
        encoding="utf-8",
    )
    assert plan_readiness.is_plan_review_approved(p_forged_prose) is False

    # Structured readiness WITHOUT review provenance in history -> refused (8v5pwa)
    p_unattested = pdir / "20261101-rd-03-rd0003-unattested.ipd.md"
    p_unattested.write_text(
        _valid_ipd_text(
            id6="rd0003",
            status="reviewed",
            readiness="go-pending-approval",
            history_lines=("- 2026-11-01 to-review (tester): created.",),
        ),
        encoding="utf-8",
    )
    assert plan_readiness.is_plan_review_approved(p_unattested) is False

    # Structured readiness WITH review provenance -> approved
    p_attested = pdir / "20261101-rd-04-rd0004-attested.ipd.md"
    p_attested.write_text(
        _valid_ipd_text(
            id6="rd0004",
            status="reviewed",
            readiness="go-pending-approval",
            history_lines=(
                "- 2026-11-01 /plan-review (reviewer): APPROVE.",
                "- 2026-11-01 to-review (tester): created.",
            ),
        ),
        encoding="utf-8",
    )
    assert plan_readiness.is_plan_review_approved(p_attested) is True

    # Out-of-vocab readiness -> refused
    p_bad = pdir / "20261101-rd-05-rd0005-bad.ipd.md"
    p_bad.write_text(
        _valid_ipd_text(
            id6="rd0005",
            status="reviewed",
            readiness="maybe",
            history_lines=("- 2026-11-01 /plan-review (reviewer): APPROVE.",),
        ),
        encoding="utf-8",
    )
    assert plan_readiness.is_plan_review_approved(p_bad) is False


def test_plan_audit_target_reads_executed_plan_setid(tmp_path: Path) -> None:
    """Pins runner_shared.plan_audit_target resolving an executed plan and its setid."""
    repo = _make_repo(tmp_path)
    p_exec = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / "20261101-audset-01-au0001-done.ipd.md"
    )
    p_exec.write_text(
        _valid_ipd_text(id6="au0001", status="executed", setid="audset", order=1),
        encoding="utf-8",
    )

    target = runner_shared.plan_audit_target(repo, "au0001")
    assert target.refusal == ""
    assert target.id6 == "au0001"
    assert target.setid == "audset"
    assert target.plan_path.resolve() == p_exec.resolve()


def test_parse_plan_file_hits_artifact_meta_cache_on_initialized_repo(
    tmp_path: Path,
) -> None:
    """Verifies parse_plan_file resolves id6 and hits artifact_meta.read when index.db is initialized."""
    from agent_workflows import artifact_meta, project_context

    repo = _make_repo(tmp_path)
    pdir = repo / ".aw" / "records" / "plans" / "pending"
    plan_p = pdir / "20261101-cacheset-04-ch0004-cached.ipd.md"
    plan_p.write_text(
        _valid_ipd_text(
            id6="ch0004",
            status="approved",
            kind="child",
            setid="cacheset",
            order=4,
            deps="executed:dep001",
            from_backlog="bkl004",
        ),
        encoding="utf-8",
    )
    renamed_p = pdir / "20261101-cacheset-05-zzz999-mismatched-name.ipd.md"
    renamed_p.write_text(
        _valid_ipd_text(
            id6="ch0005",
            status="reviewed",
            kind="child",
            setid="cacheset",
            order=5,
        ),
        encoding="utf-8",
    )

    # Populate index.db for this repo.
    ctx = project_context.resolve_project_context(target_repo=str(repo))
    artifact_meta.query(type="ipd", project_context=ctx)
    assert (Path(ctx.logical_roots["state"]) / "index.db").exists()

    # Conforming filename hits artifact_meta.read(id6) directly (raw_text is None).
    st, raw = runner_shared._read_state_for_path(repo, plan_p, record_type="ipd")
    assert st is not None
    assert raw is None
    assert st.id6 == "ch0004"

    rec = runner_shared.parse_plan_file(plan_p, repo)
    assert rec is not None
    assert (rec.id6, rec.status, rec.kind, rec.setid, rec.order, rec.from_backlog) == (
        "ch0004",
        "approved",
        "child",
        "cacheset",
        4,
        "bkl004",
    )
    assert rec.dependencies == ["executed:dep001"]

    # Filename id6 disagreeing with declared - Id: must not false-match another record.
    rec_renamed = runner_shared.parse_plan_file(renamed_p, repo)
    assert rec_renamed is not None
    assert (rec_renamed.id6, rec_renamed.status, rec_renamed.order) == (
        "ch0005",
        "reviewed",
        5,
    )
