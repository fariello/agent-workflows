"""Behavioral pinning tests for moving check_engine and hook git readers onto artifact_meta.read_at.

Implements the pin-first behavioral tests for IPD snh19k (E-03 check_engine git-content readers
and E-04 pre-commit hook CLI entry points). Every test exercises real temporary git repositories
and asserts observable outcomes (Drift findings, exit codes, and CLI verdicts) without reading
production source code.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows import (
    attention_contract,
    backlog,
    check_engine,
    ipd_lifecycle,
    ipd_schema,
)

pytestmark = pytest.mark.core

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Gate Fixture")
    _git(repo, "config", "user.email", "gate@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    for sub in (
        ".aw/records/plans/pending",
        ".aw/records/plans/executed",
        ".aw/records/plans/superseded",
        ".aw/records/specs/approved",
        ".aw/records/releases",
        ".aw/config",
    ):
        (repo / sub).mkdir(parents=True, exist_ok=True)
    for st in backlog.STATUSES:
        (repo / ".aw" / "records" / "backlog" / st).mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        '{"dependency_schema_cutover": {"date": "2020-01-01"}}',
        encoding="utf-8",
    )
    rel_file = (
        repo
        / ".aw"
        / "records"
        / "releases"
        / "20261101-rel001-01-rel001-v1.release.md"
    )
    rel_file.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )


def _plan_text(
    *,
    id6: str,
    status: str = "draft",
    order: int = 1,
    item_deps: str = "none",
    history_lines: tuple[str, ...] = ("- 2026-11-01 draft (author): created",),
    extra_bullets: tuple[str, ...] = (),
) -> str:
    extra = "".join(f"{b}\n" for b in extra_bullets)
    hist = "\n".join(history_lines)
    return (
        f"# IPD: Fixture Plan {id6}\n\n"
        f"- Date: 2026-11-01\n"
        f"- Kind: child\n"
        f"- Scope-Paths: x.py\n"
        f"- Item-Dependencies: {item_deps}\n"
        f"- Status: {status}\n"
        f"- Set: demo\n"
        f"- Order: {order}\n"
        f"- Id: {id6}\n"
        f"{extra}\n"
        f"## Workflow history\n"
        f"{hist}\n\n"
        f"## Goal\n\n"
        f"Fixture goal.\n"
    )


def _backlog_text(
    *,
    id6: str,
    status: str,
    blocks_release: str | None = None,
    work_kind: str = "bug",
) -> str:
    gate = f"- Blocks-Release: {blocks_release}\n" if blocks_release else ""
    gate_block = (
        "- Gate-Kind: branch\n- Gate-Ref: main\n" if status == "blocked" else ""
    )
    return (
        f"# {id6}: Fixture item\n\n"
        f"- Date: 2026-11-01\n"
        f"- Status: {status}\n"
        f"- Work-Kind: {work_kind}\n"
        f"- Priority: high\n"
        f"- Id: {id6}\n"
        f"- Set: demo\n"
        f"{gate}"
        f"{gate_block}\n"
        f"## Workflow history\n"
        f"- 2026-11-01 {status} (aw backlog): state\n\n"
        f"## Details\n\n"
        f"Fixture details.\n"
    )


def _run_aw_cli(repo: Path, *cli_args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["AW_NO_REEXEC"] = "1"
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_REPO_ROOT}{os.pathsep}{existing_pp}" if existing_pp else str(_REPO_ROOT)
    )
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *cli_args],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _derive_illegal_backlog_edge() -> tuple[str, str]:
    for s1 in sorted(backlog.STATUSES):
        for s2 in sorted(backlog.STATUSES):
            if s1 != s2 and not attention_contract.backlog_transition_allowed(s1, s2):
                return s1, s2
    pytest.skip("BACKLOG_TRANSITIONS has no illegal edges")


# --------------------------------------------------------------------------------------
# E-03: check_engine git-content reader pinning tests (-k check_engine)
# --------------------------------------------------------------------------------------


def test_check_engine_untooled_status_flip_refused(tmp_path: Path) -> None:
    """A staged plan status flip with no matching Workflow history line emits check.status-untooled."""
    _init_repo(tmp_path)
    plan = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0001-flip.ipd.md"
    )
    plan.write_text(_plan_text(id6="pl0001", status="draft"), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed plan")

    # Hand-flip status without adding an approved history line.
    plan.write_text(_plan_text(id6="pl0001", status="approved"), encoding="utf-8")
    _git(tmp_path, "add", str(plan.relative_to(tmp_path)))

    drift = check_engine.check_status_untooled(tmp_path)
    assert len(drift) == 1
    assert drift[0].rule == "check.status-untooled"
    assert "approved" in drift[0].detail


def test_check_engine_tooled_status_flip_accepted(tmp_path: Path) -> None:
    """A staged plan status flip WITH a matching tool-authored Workflow history line produces no drift."""
    _init_repo(tmp_path)
    plan = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0002-tooled.ipd.md"
    )
    plan.write_text(_plan_text(id6="pl0002", status="draft"), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed plan")

    plan.write_text(
        _plan_text(
            id6="pl0002",
            status="approved",
            history_lines=(
                "- 2026-11-01 approved (aw set): human approved",
                "- 2026-11-01 draft (author): created",
            ),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", str(plan.relative_to(tmp_path)))

    assert check_engine.check_status_untooled(tmp_path) == []


def test_check_engine_staged_rename_into_executed_and_range(tmp_path: Path) -> None:
    """Staged rename into executed/ is excluded from check_status_untooled; range check demands finalize commit."""
    _init_repo(tmp_path)
    rel_pending = ".aw/records/plans/pending/20261101-demo-01-pl0003-ren.ipd.md"
    rel_executed = ".aw/records/plans/executed/20261101-demo-01-pl0003-ren.ipd.md"
    rel_superseded = ".aw/records/plans/superseded/20261101-demo-01-pl0004-ret.ipd.md"
    rel_pending4 = ".aw/records/plans/pending/20261101-demo-02-pl0004-ret.ipd.md"

    (tmp_path / rel_pending).write_text(
        _plan_text(
            id6="pl0003",
            status="approved",
            order=1,
            history_lines=("- 2026-11-01 approved (aw set): ok",),
        ),
        encoding="utf-8",
    )
    (tmp_path / rel_pending4).write_text(
        _plan_text(
            id6="pl0004",
            status="approved",
            order=2,
            history_lines=("- 2026-11-01 approved (aw set): ok",),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    base_sha = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    # Staged rename of pl0003 into executed/ -> check_status_untooled skips executed/
    _git(tmp_path, "mv", rel_pending, rel_executed)
    (tmp_path / rel_executed).write_text(
        _plan_text(
            id6="pl0003",
            status="executed",
            order=1,
            history_lines=("- 2026-11-01 approved (aw set): ok",),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_executed)
    assert check_engine.check_status_untooled(tmp_path) == []

    # Commit WITHOUT finalize subject -> range check flags untooled executed arrival.
    _git(tmp_path, "commit", "-q", "-m", "chore: raw move to executed")
    bad_head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    range_drift = check_engine.check_status_untooled_range(tmp_path, base_sha, bad_head)
    assert len(range_drift) == 1
    assert range_drift[0].rule == "check.status-untooled"
    assert "executed/" in range_drift[0].detail

    # Adding a matching finalize commit in the range clears the range finding.
    _git(
        tmp_path,
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "lifecycle(pl0003): finalize pl0003 -> executed",
    )
    good_head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    assert check_engine.check_status_untooled_range(tmp_path, base_sha, good_head) == []

    # Staged rename into superseded/ with untooled status flip IS flagged by check_status_untooled.
    _git(tmp_path, "mv", rel_pending4, rel_superseded)
    (tmp_path / rel_superseded).write_text(
        _plan_text(
            id6="pl0004",
            status="superseded",
            order=2,
            history_lines=("- 2026-11-01 approved (aw set): ok",),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_superseded)
    ret_drift = check_engine.check_status_untooled(tmp_path)
    assert len(ret_drift) == 1
    assert ret_drift[0].rule == "check.status-untooled"
    assert "superseded" in ret_drift[0].detail


def test_check_engine_illegal_backlog_transition(tmp_path: Path) -> None:
    """check_staged_illegal_backlog_transition refuses an illegal staged move and accepts a legal one."""
    from_st, to_st = _derive_illegal_backlog_edge()
    _init_repo(tmp_path)
    rel_from = f".aw/records/backlog/{from_st}/20261101-demo-01-bk0001-item.backlog.md"
    rel_to = f".aw/records/backlog/{to_st}/20261101-demo-01-bk0001-item.backlog.md"
    (tmp_path / rel_from).write_text(
        _backlog_text(id6="bk0001", status=from_st, work_kind="chore"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed backlog item")

    _git(tmp_path, "mv", rel_from, rel_to)
    (tmp_path / rel_to).write_text(
        _backlog_text(id6="bk0001", status=to_st, work_kind="chore"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_to)

    findings = check_engine.check_staged_illegal_backlog_transition(tmp_path)
    assert len(findings) == 1
    assert findings[0].rule == "check.staged-illegal-backlog-transition"
    assert findings[0].location == rel_to
    assert f"from '{from_st}' to '{to_st}'" in findings[0].detail


def test_check_engine_release_blocking_done_without_and_with_handoff(
    tmp_path: Path,
) -> None:
    """Staged release-blocking done item fails without handoff and passes with an executed From-Backlog plan."""
    _init_repo(tmp_path)
    rel_open = ".aw/records/backlog/open/20261101-demo-01-bk0002-blocker.backlog.md"
    rel_done = ".aw/records/backlog/done/20261101-demo-01-bk0002-blocker.backlog.md"
    (tmp_path / rel_open).write_text(
        _backlog_text(id6="bk0002", status="open", blocks_release="next"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed blocking item")

    # Stage closing to done without any handoff carrier or evidence.
    _git(tmp_path, "mv", rel_open, rel_done)
    (tmp_path / rel_done).write_text(
        _backlog_text(id6="bk0002", status="done", blocks_release="next"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_done)

    without_handoff = check_engine.check_release_gate_consistency(
        tmp_path, staged_only=True
    )
    assert [d.rule for d in without_handoff] == [
        "check.blocking-item-closed-without-gate"
    ]

    # Add an executed From-Backlog plan carrying the same Blocks-Release gate.
    carrier = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / "20261101-demo-01-pl0005-carrier.ipd.md"
    )
    carrier.write_text(
        _plan_text(
            id6="pl0005",
            status="executed",
            extra_bullets=("- From-Backlog: bk0002", "- Blocks-Release: next"),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", str(carrier.relative_to(tmp_path)))

    with_handoff = check_engine.check_release_gate_consistency(
        tmp_path, staged_only=True
    )
    assert with_handoff == []


def test_check_engine_lane_carrier_is_executed_plan_and_spec(tmp_path: Path) -> None:
    """_lane_carrier_is_executed verifies plan in executed/ and spec status == implemented at a ref."""
    _init_repo(tmp_path)
    spec_path = (
        tmp_path
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / "20261101-demo-01-sp0001-carrier.spec.md"
    )
    spec_path.write_text(
        "# Spec: Carrier\n\n- Id: sp0001\n- Status: approved\n- Set: demo\n\n## Details\n\nBody.\n",
        encoding="utf-8",
    )
    plan_pending = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0006-carrier.ipd.md"
    )
    plan_pending.write_text(
        _plan_text(id6="pl0006", status="approved"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base carriers")

    assert not check_engine._lane_carrier_is_executed(tmp_path, spec_path, "HEAD")
    assert not check_engine._lane_carrier_is_executed(tmp_path, plan_pending, "HEAD")

    # On a lane branch, mark spec implemented and move plan to executed/.
    _git(tmp_path, "checkout", "-q", "-b", "lane-carriers")
    spec_path.write_text(
        "# Spec: Carrier\n\n- Id: sp0001\n- Status: implemented\n- Set: demo\n\n## Details\n\nBody.\n",
        encoding="utf-8",
    )
    plan_exec = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / "20261101-demo-01-pl0006-carrier.ipd.md"
    )
    _git(
        tmp_path,
        "mv",
        str(plan_pending.relative_to(tmp_path)),
        str(plan_exec.relative_to(tmp_path)),
    )
    plan_exec.write_text(_plan_text(id6="pl0006", status="executed"), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "complete carriers on lane")
    _git(tmp_path, "checkout", "-q", "main")

    assert check_engine._lane_carrier_is_executed(tmp_path, spec_path, "lane-carriers")
    assert check_engine._lane_carrier_is_executed(
        tmp_path, plan_pending, "lane-carriers"
    )
    assert not check_engine._lane_carrier_is_executed(tmp_path, spec_path, "HEAD")


# --------------------------------------------------------------------------------------
# E-04: pre-commit hook CLI entry point pinning tests (-k hook)
# --------------------------------------------------------------------------------------


def test_hook_ipd_executed_gate_cli_refuses_raw_transitions(tmp_path: Path) -> None:
    """aw ipd-executed-gate refuses raw DONE flip (D-2) and raw move into executed/ (exit 1)."""
    _init_repo(tmp_path)
    rel_pending = ".aw/records/plans/pending/20261101-demo-01-hk0001-plan.ipd.md"
    rel_executed = ".aw/records/plans/executed/20261101-demo-01-hk0001-plan.ipd.md"
    (tmp_path / rel_pending).write_text(
        _plan_text(id6="hk0001", status="approved"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed plan")

    # 1. Raw case-insensitive status flip (`DONE`, D-2) -> refused (exit 1).
    (tmp_path / rel_pending).write_text(
        _plan_text(id6="hk0001", status="DONE"), encoding="utf-8"
    )
    _git(tmp_path, "add", rel_pending)
    res_flip = _run_aw_cli(tmp_path, "ipd-executed-gate")
    assert res_flip.returncode == 1, res_flip.stderr
    assert "hk0001" in res_flip.stderr

    # 2. Raw move into executed/ without journal -> refused (exit 1).
    _git(tmp_path, "mv", rel_pending, rel_executed)
    (tmp_path / rel_executed).write_text(
        _plan_text(id6="hk0001", status="executed"), encoding="utf-8"
    )
    _git(tmp_path, "add", rel_executed)
    res_mv = _run_aw_cli(tmp_path, "ipd-executed-gate")
    assert res_mv.returncode == 1, res_mv.stderr
    assert "hk0001" in res_mv.stderr


def test_hook_ipd_executed_gate_cli_accepts_journal_and_followup_edit(
    tmp_path: Path,
) -> None:
    """aw ipd-executed-gate accepts matching finalize journal and edits to an already-executed plan (exit 0)."""
    _init_repo(tmp_path)
    rel_pending = ".aw/records/plans/pending/20261101-demo-01-hk0001-plan.ipd.md"
    rel_executed = ".aw/records/plans/executed/20261101-demo-01-hk0001-plan.ipd.md"
    (tmp_path / rel_pending).write_text(
        _plan_text(id6="hk0001", status="approved"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed plan")

    _git(tmp_path, "mv", rel_pending, rel_executed)
    (tmp_path / rel_executed).write_text(
        _plan_text(id6="hk0001", status="executed"), encoding="utf-8"
    )
    _git(tmp_path, "add", rel_executed)

    # 1. With a matching finalize journal at ready-to-commit -> accepted (exit 0).
    ipd_lifecycle._write_finalize_journal(
        tmp_path,
        {
            "schema_version": 1,
            "plan_id": "hk0001",
            "original_path": rel_pending,
            "dest_path": rel_executed,
            "phase": "ready-to-commit",
        },
    )
    res_ok = _run_aw_cli(tmp_path, "ipd-executed-gate")
    assert res_ok.returncode == 0, res_ok.stderr

    # 2. After committing executed plan and removing journal, ordinary body edit -> accepted (exit 0).
    _git(
        tmp_path, "commit", "-q", "-m", "lifecycle(hk0001): finalize hk0001 -> executed"
    )
    ipd_lifecycle._clear_finalize_journal(tmp_path, "hk0001")
    (tmp_path / rel_executed).write_text(
        (tmp_path / rel_executed).read_text(encoding="utf-8") + "\nFollow-up note.\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_executed)
    res_edit = _run_aw_cli(tmp_path, "ipd-executed-gate")
    assert res_edit.returncode == 0, res_edit.stderr


def test_hook_ipd_status_untooled_gate_cli(tmp_path: Path) -> None:
    """aw ipd-status-untooled-gate refuses untooled staged status flip (exit 1) and accepts tooled flip (exit 0)."""
    _init_repo(tmp_path)
    rel_plan = ".aw/records/plans/pending/20261101-demo-01-hk0002-status.ipd.md"
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0002", status="draft"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed plan")

    # Untooled flip -> exit 1
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0002", status="to-review"), encoding="utf-8"
    )
    _git(tmp_path, "add", rel_plan)
    res_bad = _run_aw_cli(tmp_path, "ipd-status-untooled-gate")
    assert res_bad.returncode == 1, res_bad.stderr

    # Tooled flip with matching history line -> exit 0
    (tmp_path / rel_plan).write_text(
        _plan_text(
            id6="hk0002",
            status="to-review",
            history_lines=(
                "- 2026-11-01 to-review (aw set): ready",
                "- 2026-11-01 draft (author): created",
            ),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)
    res_ok = _run_aw_cli(tmp_path, "ipd-status-untooled-gate")
    assert res_ok.returncode == 0, res_ok.stderr


def test_hook_backlog_blocking_close_gate_cli(tmp_path: Path) -> None:
    """aw backlog-blocking-close-gate refuses blocking done without handoff (exit 1) and accepts with handoff (exit 0)."""
    _init_repo(tmp_path)
    rel_open = ".aw/records/backlog/open/20261101-demo-01-hk0003-gate.backlog.md"
    rel_done = ".aw/records/backlog/done/20261101-demo-01-hk0003-gate.backlog.md"
    (tmp_path / rel_open).write_text(
        _backlog_text(id6="hk0003", status="open", blocks_release="next"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed blocking backlog")

    _git(tmp_path, "mv", rel_open, rel_done)
    (tmp_path / rel_done).write_text(
        _backlog_text(id6="hk0003", status="done", blocks_release="next"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_done)

    res_bad = _run_aw_cli(tmp_path, "backlog-blocking-close-gate")
    assert res_bad.returncode == 1, res_bad.stderr

    # Add executed From-Backlog carrier with matching Blocks-Release -> exit 0.
    carrier = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / "20261101-demo-01-hk0004-carrier.ipd.md"
    )
    carrier.write_text(
        _plan_text(
            id6="hk0004",
            status="executed",
            extra_bullets=("- From-Backlog: hk0003", "- Blocks-Release: next"),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", str(carrier.relative_to(tmp_path)))

    res_ok = _run_aw_cli(tmp_path, "backlog-blocking-close-gate")
    assert res_ok.returncode == 0, res_ok.stderr


def test_hook_ipd_dependency_statement_gate_cli_refusals(tmp_path: Path) -> None:
    """aw ipd-dependency-statement-gate refuses dangling edges and advancing unresolved statements (exit 1)."""
    _init_repo(tmp_path)
    rel_plan = ".aw/records/plans/pending/20261101-demo-01-hk0005-deps.ipd.md"

    # 1. Dangling edge -> exit 1.
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0005", status="draft", item_deps="executed:zzzzzz"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)
    res_dangling = _run_aw_cli(tmp_path, "ipd-dependency-statement-gate")
    assert res_dangling.returncode == 1, res_dangling.stderr
    assert ipd_schema.RULE_IPD_DEP_DANGLING in res_dangling.stderr

    # 2. Unresolved advancing to approved -> exit 1.
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0005", status="approved", item_deps="unresolved"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)
    res_adv = _run_aw_cli(tmp_path, "ipd-dependency-statement-gate")
    assert res_adv.returncode == 1, res_adv.stderr
    assert ipd_schema.RULE_IPD_DEP_UNRESOLVED in res_adv.stderr


def test_hook_ipd_dependency_statement_gate_cli_accepts(tmp_path: Path) -> None:
    """aw ipd-dependency-statement-gate accepts draft unresolved and valid `none` statements (exit 0)."""
    _init_repo(tmp_path)
    rel_plan = ".aw/records/plans/pending/20261101-demo-01-hk0005-deps.ipd.md"

    # 1. Unresolved at draft -> exit 0.
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0005", status="draft", item_deps="unresolved"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)
    res_draft = _run_aw_cli(tmp_path, "ipd-dependency-statement-gate")
    assert res_draft.returncode == 0, res_draft.stderr

    # 2. Valid `none` -> exit 0.
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="hk0005", status="approved", item_deps="none"),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)
    res_valid = _run_aw_cli(tmp_path, "ipd-dependency-statement-gate")
    assert res_valid.returncode == 0, res_valid.stderr


# --------------------------------------------------------------------------------------
# Regression coverage for artifact_meta.read_at index (`:0:`), fields, history & fences
# --------------------------------------------------------------------------------------


def test_read_at_staged_index_fields_history_and_fenced_preamble(
    tmp_path: Path,
) -> None:
    """artifact_meta.read_at(':0:') reads staged fields/history and ignores fenced preamble bullets."""
    from agent_workflows import artifact_meta as meta

    _init_repo(tmp_path)
    rel_plan = ".aw/records/plans/pending/20261101-demo-01-ra0001-stage.ipd.md"
    (tmp_path / rel_plan).write_text(
        "# IPD: Staged Read Test\n\n"
        "Preamble quote:\n"
        "```text\n"
        "- Id: ffffff\n"
        "- Status: executed\n"
        "```\n\n"
        "- Id: ra0001\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-11-01 approved (aw set): ok\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_plan)

    ctx = check_engine._git_read_at_context(tmp_path)
    with meta.ephemeral_if_uninitialized():
        assert meta.resolve_id_at(rel_plan, ":0:", project_context=ctx) == "ra0001"
        res = meta.read_at("ra0001", ":0:", project_context=ctx)
        assert res.kind == "ok", res.error
        assert res.state is not None
        assert res.state.id6 == "ra0001"
        assert res.state.status == "approved"
        assert res.state.fields.get("item_dependencies") == "none"
        assert len(res.history) == 1
        assert "approved" in res.history[0]["line"]
        # The fenced quote id must NOT resolve as a real record.
        assert meta.read_at("ffffff", ":0:", project_context=ctx).kind == "absent"


def test_read_at_commits_rev_mirrors_and_rev_log_states_cache(tmp_path: Path) -> None:
    """read_at and resolve_mirror_at commit rev_mirrors and rev_log_states rows across connections."""
    from agent_workflows import artifact_meta as meta

    _init_repo(tmp_path)
    records_root = tmp_path / ".aw" / "records"
    state_root = tmp_path / ".aw" / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    ctx = type(
        "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
    )()

    rel_plan = ".aw/records/plans/pending/20261101-demo-01-cm0001-cache.ipd.md"
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="cm0001", status="approved"), encoding="utf-8"
    )
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "cm0002.jsonl").write_text(
        meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-01T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": "plans/pending/20261101-demo-02-cm0002-log.ipd.md",
                "fields": {
                    "id": "cm0002",
                    "type": "ipd",
                    "status": "draft",
                    "set": "demo",
                    "order": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed cache fixtures")

    r_legacy = meta.read_at("cm0001", "HEAD", project_context=ctx)
    assert r_legacy.kind == "ok", r_legacy.error
    r_v2 = meta.read_at("cm0002", "HEAD", project_context=ctx)
    assert r_v2.kind == "ok", r_v2.error

    conn = meta.open_cache(records_root, state_root)
    try:
        mirror_ids = {
            row[0] for row in conn.execute("SELECT id6 FROM rev_mirrors").fetchall()
        }
        log_ids = {
            row[0] for row in conn.execute("SELECT id6 FROM rev_log_states").fetchall()
        }
    finally:
        conn.close()
    assert "cm0001" in mirror_ids
    assert "cm0002" in log_ids


def test_evaluate_ipd_dependencies_overlay_states_missing_respects_date_cutover(
    tmp_path: Path,
) -> None:
    """evaluate_ipd_dependencies with overlay_states uses State date for cutover grandfathering."""
    from agent_workflows import artifact_meta as meta

    _init_repo(tmp_path)
    post_path = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-ov0001-post.ipd.md"
    )
    pre_path = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20190101-demo-02-ov0002-pre.ipd.md"
    )
    post_text = (
        "# IPD: Post-cutover missing deps\n\n"
        "- Date: 2026-11-01\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Status: draft\n- Set: demo\n- Order: 1\n- Id: ov0001\n\n## Goal\ng\n"
    )
    pre_text = (
        "# IPD: Pre-cutover missing deps\n\n"
        "- Date: 2019-01-01\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Status: draft\n- Set: demo\n- Order: 2\n- Id: ov0002\n\n## Goal\ng\n"
    )
    overlay_states = {
        str(post_path.resolve()): meta.read_text(post_text, record_type="ipd"),
        str(pre_path.resolve()): meta.read_text(pre_text, record_type="ipd"),
    }
    plans = [(post_path.resolve(), ""), (pre_path.resolve(), "")]
    drift = check_engine.evaluate_ipd_dependencies(
        tmp_path,
        phase="pre-execution",
        plans=plans,
        overlay_states=overlay_states,
    )
    missing_locs = [
        d.location for d in drift if d.rule == ipd_schema.RULE_IPD_DEP_MISSING
    ]
    assert str(post_path.resolve()) in missing_locs
    assert str(pre_path.resolve()) not in missing_locs


# --------------------------------------------------------------------------------------
# iqhzse E-02: setter HEAD-status pinning test (-k setter_head)
# --------------------------------------------------------------------------------------


def test_setter_head_status_differs_from_working_tree(tmp_path: Path) -> None:
    """aw ipd set compares working-tree status against HEAD status via read_at.

    When a plan was committed at HEAD as `to-review` and hand-edited in the working tree to
    `reviewed`, `aw ipd set reviewed` detects the HEAD mismatch (writing a `reviewed` history
    token and clearing `check.status-untooled`) instead of treating it as `same-status`; when
    HEAD matches the working tree (`reviewed`), it writes `same-status`.
    """
    from agent_workflows import ipd_lint

    _init_repo(tmp_path)
    rel_diff = ".aw/records/plans/pending/20261101-demo-01-sh0001-diff.ipd.md"
    rel_same = ".aw/records/plans/pending/20261101-demo-02-sh0002-same.ipd.md"
    (tmp_path / rel_diff).write_text(
        _plan_text(
            id6="sh0001",
            status="to-review",
            order=1,
            history_lines=("- 2026-11-01 to-review (author): ready",),
            extra_bullets=("- Work-Kind: chore", "- Priority: medium"),
        ),
        encoding="utf-8",
    )
    (tmp_path / rel_same).write_text(
        _plan_text(
            id6="sh0002",
            status="reviewed",
            order=2,
            history_lines=("- 2026-11-01 reviewed (author): reviewed",),
            extra_bullets=("- Work-Kind: chore", "- Priority: medium"),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed setter_head plans")

    # Hand-edit sh0001 in working tree: HEAD is `to-review`, working tree is `reviewed`.
    plan_diff = tmp_path / rel_diff
    plan_diff.write_text(
        plan_diff.read_text(encoding="utf-8").replace(
            "- Status: to-review", "- Status: reviewed"
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", rel_diff)
    assert [d.rule for d in check_engine.check_status_untooled(tmp_path)] == [
        "check.status-untooled"
    ]

    res_diff = _run_aw_cli(
        tmp_path, "ipd", "set", "reviewed", "sh0001", "--yes", "--no-commit"
    )
    assert res_diff.returncode == 0, res_diff.stdout + res_diff.stderr
    _git(tmp_path, "add", rel_diff)
    assert check_engine.check_status_untooled(tmp_path) == []

    doc_diff = ipd_lint.parse(plan_diff.read_text(encoding="utf-8"))
    tokens_diff = [
        m.group(1).rstrip(":").lower()
        for _ln, line in doc_diff.history_lines
        if (m := ipd_lint._HISTORY_LINE_RE.match(line.strip()))
    ]
    assert tokens_diff[0] == "reviewed"

    # Contrast: sh0002 has HEAD == working tree (`reviewed`), so setter records `same-status`.
    res_same = _run_aw_cli(
        tmp_path,
        "ipd",
        "set",
        "reviewed",
        "sh0002",
        "--yes",
        "--no-commit",
        "--message",
        "note",
    )
    assert res_same.returncode == 0, res_same.stdout + res_same.stderr
    doc_same = ipd_lint.parse((tmp_path / rel_same).read_text(encoding="utf-8"))
    tokens_same = [
        m.group(1).rstrip(":").lower()
        for _ln, line in doc_same.history_lines
        if (m := ipd_lint._HISTORY_LINE_RE.match(line.strip()))
    ]
    assert tokens_same[0] == "same-status"


def test_read_at_merge_stages_and_predicted_tree(tmp_path: Path) -> None:
    """artifact_meta.read_at supports merge-stage revisions (:1:/:2:/:3:) and predicted merge trees."""
    from agent_workflows import artifact_meta as meta

    _init_repo(tmp_path)
    rel_plan = ".aw/records/plans/pending/20261101-demo-01-mg0001-stage.ipd.md"
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="mg0001", status="approved"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")

    # Branch: change status to reviewed
    _git(tmp_path, "checkout", "-q", "-b", "lane-stage")
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="mg0001", status="reviewed"), encoding="utf-8"
    )
    _git(tmp_path, "commit", "-q", "-am", "lane reviewed")

    # Main: change status to executed (creates a genuine 3-way conflict at rel_plan)
    _git(tmp_path, "checkout", "-q", "main")
    (tmp_path / rel_plan).write_text(
        _plan_text(id6="mg0001", status="executed"), encoding="utf-8"
    )
    _git(tmp_path, "commit", "-q", "-am", "main executed")

    # Predicted tree check on HEAD^{tree} vs blob SHA (blob must still be invalid-revision)
    ctx = check_engine._git_read_at_context(tmp_path, rel_path=rel_plan)
    tree_sha = _git(tmp_path, "rev-parse", "HEAD^{tree}").stdout.strip()
    blob_sha = _git(tmp_path, "rev-parse", f"HEAD:{rel_plan}").stdout.strip()
    with meta.ephemeral_if_uninitialized():
        r_tree = meta.read_at(
            "mg0001", tree_sha, project_context=ctx, path_hint=rel_plan
        )
        assert r_tree.kind == "ok" and r_tree.state is not None
        assert r_tree.state.status == "executed"
        assert (
            meta.read_at("mg0001", blob_sha, project_context=ctx).kind
            == "invalid-revision"
        )

    # Trigger in-progress merge conflict so stages :1:, :2:, :3: populate the index
    merge_proc = subprocess.run(
        ["git", "merge", "--no-ff", "--no-edit", "lane-stage"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert merge_proc.returncode != 0
    try:
        with meta.ephemeral_if_uninitialized():
            r1 = meta.read_at("mg0001", ":1:", project_context=ctx, path_hint=rel_plan)
            r2 = meta.read_at("mg0001", ":2:", project_context=ctx)
            r3 = meta.read_at("mg0001", ":3:", project_context=ctx, path_hint=rel_plan)
            assert (
                r1.kind == "ok"
                and r1.state is not None
                and r1.state.status == "approved"
            )
            assert (
                r2.kind == "ok"
                and r2.state is not None
                and r2.state.status == "executed"
            )
            assert (
                r3.kind == "ok"
                and r3.state is not None
                and r3.state.status == "reviewed"
            )
    finally:
        _git(tmp_path, "merge", "--abort")
