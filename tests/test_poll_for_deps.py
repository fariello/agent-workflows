"""Behavioral tests for --poll-for-deps on aw agy run and aw oc run (plan z7uxhf)."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo, check=True)
    (repo / "README.md").write_text("demo\n", encoding="utf-8")
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo


def _write_plan(
    repo: Path,
    id6: str,
    *,
    order: int,
    status: str = "approved",
    dependencies: str = "none",
    subdir: str = "pending",
) -> Path:
    history = [
        f"- 2026-11-21 {status} (tester): set status",
        "- 2026-11-21 /plan-review (tester): APPROVE",
        "- 2026-11-21 draft (tester): created.",
    ]
    approval = "2026-11-21, tester" if status in ("approved", "executed") else None
    readiness = (
        "go-pending-approval"
        if status in ("reviewed", "approved", "executed")
        else None
    )
    text = RecordBuilder().plan(
        id6=id6,
        title=f"Plan {id6}",
        when="2026-11-21",
        set="demo",
        order=order,
        slug=f"plan-{id6}",
        status=status,
        readiness=readiness,
        approval=approval,
        scope_paths="README.md",
        item_dependencies=dependencies,
        work_kind="feature",
        priority="medium",
        author="tester",
        history=history,
        body=(
            "## Goal\n\n"
            f"Deliver {id6}.\n\n"
            "## Detailed Implementation Checklist (TODO)\n\n"
            "### Task group 1: work\n\n"
            "- [ ] E-01 Update README.md.\n"
            "  - Depends on: none\n"
            "  - Expected outcome: README.md updated.\n"
            "  - Execution state: pending\n\n"
            "## Project conventions discovered (Step 0)\n\n"
            "- Standard conventions.\n\n"
            "## Findings\n\n"
            "None.\n\n"
            "## Proposed changes (ordered, validatable)\n\n"
            "1. Update README.md.\n\n"
            "## Deferred / out of scope (with reason)\n\n"
            "None.\n\n"
            "## Scope check\n\n"
            "- Over-scope: none.\n"
            "- Under-scope: none.\n\n"
            "## Required tests / validation\n\n"
            "Verify README.md.\n\n"
            "## Spec / documentation sync\n\n"
            "N/A.\n\n"
            "## Open questions\n\n"
            "None.\n\n"
            "## Validation and cross-check (verify before reporting done)\n\n"
            "- [ ] V-01 validates E-01\n"
            "  - Required evidence: diff of README.md.\n"
            "  - Observed evidence:\n"
            "  - Result: pending\n\n"
            "## Approval and execution gate\n\n"
            "- Size assessment: standard\n"
            "- Cohesion rationale: not required\n"
        ),
        text_only=True,
    )
    assert isinstance(text, str)
    target = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / subdir
        / f"20261121-demo-{order:02d}-{id6}-plan-{id6}.ipd.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _make_args(
    repo: Path,
    selectors: list[str],
    *,
    poll_for_deps: str | None = None,
    prepare_only: bool = False,
    full_auto: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        repo=str(repo),
        selectors=selectors,
        manifest=None,
        runbook=None,
        full_auto=full_auto,
        unattended=True,
        prepare_only=prepare_only,
        poll_for_deps=poll_for_deps,
        with_dependencies=False,
        allow_drafts=False,
        allow_mixed=False,
        allow_unverifiable=False,
        allow_dirty_base=False,
        allow_concurrent_driver=None,
        allow_uncovered_orchestrator_work=None,
        ack_spec_edits=None,
        allow_red_ci=None,
        allow_failed_checks=None,
        retry_budget=None,
        integration_retry_limit=None,
        on_integration_blocked=None,
        on_conflict=None,
        question_timeout=None,
        question_rounds=None,
        max_park_percent=None,
        runaway_min_parked=None,
        blocking_only=False,
        review_unreviewed_deps=False,
        types=None,
        action=None,
        color=False,
        no_color=True,
        interactive=False,
        no_interactive=True,
        session=None,
        model=None,
        variant=None,
        agent=None,
        run_id=None,
        stall_timeout=600.0,
        self_finalize=True,
        isolate_worktree=True,
        max_items_per_session=4,
    )


def _init_via_core(args: argparse.Namespace, *, poll_sleep_fn=None) -> Path:
    return runner_shared.initialize_run_core(
        args,
        host="agy",
        driver_path=Path(agy_runipd.__file__),
        host_options={},
        labels=runner_shared.AGY_HOST_LABELS,
        expand_selectors_fn=agy_runipd.expand_selectors,
        enforce_dependency_preflight_fn=agy_runipd.enforce_dependency_preflight,
        edge_satisfied_fn=agy_runipd.edge_satisfied,
        set_plan_approved_fn=agy_runipd.set_plan_approved,
        announce_run_order_fn=agy_runipd.announce_run_order,
        is_plan_review_approved_fn=agy_runipd.is_plan_review_approved,
        run_order_rationale_fn=agy_runipd.run_order_rationale,
        write_report_fn=agy_runipd.write_report,
        git_common_dir_fn=agy_runipd.git_common_dir,
        parse_dependency_token_fn=agy_runipd.parse_dependency_token,
        default_runbook_text="Runbook",
        poll_sleep_fn=poll_sleep_fn,
    )


def test_parse_and_resolve_poll_duration_valid_and_invalid() -> None:
    assert runner_shared.parse_poll_duration("30s") == pytest.approx(30.0)
    assert runner_shared.parse_poll_duration("5m") == pytest.approx(300.0)
    assert runner_shared.parse_poll_duration("30m") == pytest.approx(1800.0)
    assert runner_shared.parse_poll_duration("1.5h") == pytest.approx(5400.0)
    assert runner_shared.parse_poll_duration("1d") == pytest.approx(86400.0)
    assert runner_shared.parse_poll_duration("  2S ") == pytest.approx(2.0)

    assert runner_shared.resolve_poll_for_deps(None) is None
    assert runner_shared.resolve_poll_for_deps(False) is None
    assert runner_shared.resolve_poll_for_deps("15m") == pytest.approx(900.0)

    for bad in ("", "   ", "0s", "0m", "-5m", "30", "30x", "m", "1e999d", "abc"):
        with pytest.raises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_poll_for_deps(bad)


def test_poll_for_deps_registered_on_both_hosts_and_refused_on_resume() -> None:
    assert "--poll-for-deps" in runner_shared.RUN_POLICY_FLAGS_BY_FLAG
    row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--poll-for-deps"]
    assert row.dest == "poll_for_deps"
    assert row.resume_rule == runner_shared.RESUME_REFUSE

    for mod in (oc_runipd, agy_runipd):
        parser = mod.build_parser()
        ns = parser.parse_args(["start", "--poll-for-deps", "30m", "all"])
        assert ns.poll_for_deps == "30m"

        res_ns = parser.parse_args(["resume", "run-123", "--poll-for-deps", "30m"])
        assert res_ns.poll_for_deps == "30m"
        with pytest.raises(runner_shared.RunFlagRefusal):
            runner_shared.refuse_frozen_flags_on_resume(res_ns)


def test_poll_for_deps_waits_until_external_plan_executes_then_starts(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    dep_path = _write_plan(repo, "dep001", order=1, status="approved")
    _write_plan(
        repo, "cns002", order=2, status="approved", dependencies="executed:dep001"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

    # Without --poll-for-deps: immediate refusal and zero run directories
    with pytest.raises(runner_shared.DriverError, match="RUN-DEPENDENCY-UNSATISFIABLE"):
        _init_via_core(_make_args(repo, ["cns002"]))
    runs_dir = repo / ".aw" / "records" / "runs"
    assert not runs_dir.exists() or list(runs_dir.glob("run-*")) == []

    # With --poll-for-deps + --prepare-only: immediate refusal, zero sleeps
    prep_sleeps: list[float] = []
    with pytest.raises(runner_shared.DriverError, match="RUN-DEPENDENCY-UNSATISFIABLE"):
        _init_via_core(
            _make_args(repo, ["cns002"], poll_for_deps="5m", prepare_only=True),
            poll_sleep_fn=prep_sleeps.append,
        )
    assert prep_sleeps == []

    # With --poll-for-deps 5m: polls twice, external dep executes on tick 2, tick 3 succeeds
    sleeps: list[float] = []

    def _fake_sleep(secs: float) -> None:
        sleeps.append(secs)
        # No durable run directory exists while still waiting
        assert not runs_dir.exists() or list(runs_dir.glob("run-*")) == []
        if len(sleeps) == 2:
            dep_path.unlink()
            _write_plan(repo, "dep001", order=1, status="executed", subdir="executed")

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        run_dir = _init_via_core(
            _make_args(repo, ["cns002"], poll_for_deps="5m"),
            poll_sleep_fn=_fake_sleep,
        )

    assert sleeps == [300.0, 300.0]
    assert "waiting for external dependencies: dep001 (approved)" in err.getvalue()
    assert run_dir.is_dir()
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["options"]["poll_for_deps"] == "5m"
    assert [it["id6"] for it in state["queue"]] == ["cns002"]


def test_poll_for_deps_refuses_immediately_on_permanent_or_internal_unsatisfiable(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    _write_plan(repo, "dead01", order=1, status="superseded", subdir="superseded")
    _write_plan(
        repo, "cns002", order=2, status="approved", dependencies="executed:dead01"
    )
    _write_plan(repo, "rev003", order=3, status="reviewed")
    _write_plan(
        repo, "cns004", order=4, status="approved", dependencies="executed:rev003"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

    # Superseded external dependency -> permanently unsatisfiable, 0 sleeps
    sleeps: list[float] = []
    with pytest.raises(runner_shared.DriverError, match="RUN-DEPENDENCY-UNSATISFIABLE"):
        _init_via_core(
            _make_args(repo, ["cns002"], poll_for_deps="5m"),
            poll_sleep_fn=sleeps.append,
        )
    assert sleeps == []

    # Internal unrunnable dependency (rev003 in this run, frozen at reviewed without --full-auto) -> 0 sleeps
    with pytest.raises(runner_shared.DriverError, match="RUN-DEPENDENCY-UNSATISFIABLE"):
        _init_via_core(
            _make_args(repo, ["rev003", "cns004"], poll_for_deps="5m", full_auto=False),
            poll_sleep_fn=sleeps.append,
        )
    assert sleeps == []


def test_poll_for_deps_keyboard_interrupt_cancels_cleanly_without_durable_state(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    _write_plan(repo, "dep001", order=1, status="approved")
    _write_plan(
        repo, "cns002", order=2, status="approved", dependencies="executed:dep001"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

    def _interrupt(_secs: float) -> None:
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        _init_via_core(
            _make_args(repo, ["cns002"], poll_for_deps="30m"),
            poll_sleep_fn=_interrupt,
        )
    runs_dir = repo / ".aw" / "records" / "runs"
    assert not runs_dir.exists() or list(runs_dir.glob("run-*")) == []
