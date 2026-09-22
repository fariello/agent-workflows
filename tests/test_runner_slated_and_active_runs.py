"""Tests for runner plan start detail line, active run conflict detection, and slated artifacts table.

Verifies:
1. When a runner starts a plan, it displays the detail line shown with `aw att -d`.
2. Artifacts handled by an active live run trigger an abort with `aw att --runs` table.
3. At the start of a run, all slated artifacts are listed as if run by `aw att --runs`.
4. Symmetrical support across both oc_runipd and agy_runipd.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_workflows import agy_runipd, attention, oc_runipd, runner_shared, term as T


def test_format_plan_detail_line(tmp_path: Path) -> None:
    # 1. Summary field
    plan_with_summary = tmp_path / "plan_summary.ipd.md"
    plan_with_summary.write_text(
        "---\n"
        "- Id: p1sum1\n"
        "- Summary: Test plan for doing awesome things\n"
        "---\n\n"
        "# Plan\n",
        encoding="utf-8",
    )
    uncolored = attention.format_plan_detail_line(
        plan_with_summary, term=T.Term(color=False)
    )
    assert uncolored is not None
    assert uncolored == "      summary: Test plan for doing awesome things"

    colored_term = T.Term(color=True)
    colored = attention.format_plan_detail_line(plan_with_summary, term=colored_term)
    assert colored is not None
    assert "Test plan for doing awesome things" in colored
    assert "\033[" in colored

    # 2. Scope field when summary absent
    plan_with_scope = tmp_path / "plan_scope.ipd.md"
    plan_with_scope.write_text(
        "---\n"
        "- Id: p1scp1\n"
        "- Scope: Limit to specific test components\n"
        "---\n\n"
        "# Plan\n",
        encoding="utf-8",
    )
    uncolored_scope = attention.format_plan_detail_line(
        plan_with_scope, term=T.Term(color=False)
    )
    assert uncolored_scope is not None
    assert uncolored_scope == "      scope: Limit to specific test components"

    # 3. Non-existent file
    missing = tmp_path / "does_not_exist.ipd.md"
    assert attention.format_plan_detail_line(missing) is None


def test_execute_item_core_prints_detail_line(tmp_path: Path, monkeypatch) -> None:
    plan_file = tmp_path / "20260901-testset-01-tst001-plan.ipd.md"
    plan_file.write_text(
        "---\n"
        "- Id: tst001\n"
        "- Summary: Execute item detail demonstration\n"
        "---\n\n"
        "# Plan\n",
        encoding="utf-8",
    )

    state = {
        "repo": str(tmp_path),
        "run_id": "run-test-detail",
        "options": {"isolate_worktree": False, "self_finalize": True},
        "queue": [
            {
                "id6": "tst001",
                "position": 1,
                "order": 1,
                "setid": "testset",
                "configured_file": str(plan_file),
                "status": "queued",
            }
        ],
    }
    item = {
        "id6": "tst001",
        "position": 1,
        "order": 1,
        "action": "execute",
        "configured_file": str(plan_file),
        "setid": "testset",
    }
    run_dir = tmp_path / "run-dir"
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    captured_out = io.StringIO()
    monkeypatch.setattr("sys.stdout", captured_out)

    refusal_decision = MagicMock()
    refusal_decision.warned = False
    refusal_decision.consented = False
    refusal_decision.refused = True
    refusal_decision.reason = "test stop"
    refusal_decision.dirty_paths = []

    with patch(
        "agent_workflows.runner_shared.evaluate_clean_base_for_launch",
        return_value=None,
    ):
        with patch(
            "agent_workflows.runner_shared.clean_base_launch_decision",
            return_value=refusal_decision,
        ):
            with patch.object(oc_runipd, "git_head", return_value="head123"):
                with patch.object(oc_runipd, "git_branch", return_value="main"):
                    with patch.object(oc_runipd, "git_status", return_value=""):
                        runner_shared.execute_item_core(
                            run_dir,
                            state,
                            item,
                            recovery=False,
                            host_labels=runner_shared.OC_HOST_LABELS,
                            spawn_executor=MagicMock(),
                            spawn_verifier=MagicMock(),
                            raw_launcher=MagicMock(),
                            run_suite_check=MagicMock(),
                            process_backlog_close=MagicMock(),
                            driver_module=oc_runipd,
                        )

    out = captured_out.getvalue()
    assert "plan: " in out
    assert "summary: Execute item detail demonstration" in out


def test_enforce_no_active_runner_conflict_aborts_with_runs_table(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "20260901-testset-01-cfl001-active.ipd.md"
    plan_path.write_text(
        "---\n" "- Id: cfl001\n" "- Status: approved\n" "---\n\n" "# Plan\n",
        encoding="utf-8",
    )

    # Active run map indicates cfl001 is running
    fake_run_map = {"cfl001": "running"}

    with patch(
        "agent_workflows.attention.get_active_runs_map", return_value=fake_run_map
    ):
        with pytest.raises(runner_shared.DriverError) as exc_info:
            runner_shared.enforce_no_active_runner_conflict(
                tmp_path,
                ["cfl001"],
                [plan_path],
            )
        err_msg = str(exc_info.value)
        assert (
            "Cannot run artifacts that are actively being processed by another runner."
            in err_msg
        )
        assert (
            "The following artifact(s) are currently handled by an active live run:"
            in err_msg
        )
        assert "cfl001" in err_msg
        assert "Run" in err_msg
        assert "running" in err_msg


def test_enforce_no_active_runner_conflict_passes_when_no_active_runs(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "20260901-testset-01-cfl002-idle.ipd.md"
    plan_path.write_text(
        "---\n" "- Id: cfl002\n" "- Status: approved\n" "---\n\n" "# Plan\n",
        encoding="utf-8",
    )

    # Empty run map
    with patch("agent_workflows.attention.get_active_runs_map", return_value={}):
        # Should not raise
        runner_shared.enforce_no_active_runner_conflict(
            tmp_path,
            ["cfl002"],
            [plan_path],
        )

    # Map with only idle/none runs
    with patch(
        "agent_workflows.attention.get_active_runs_map", return_value={"cfl002": "-"}
    ):
        runner_shared.enforce_no_active_runner_conflict(
            tmp_path,
            ["cfl002"],
            [plan_path],
        )


def test_initialize_run_core_checks_active_runner_conflict_before_creating_run_dir(
    tmp_path: Path,
) -> None:
    plan_path = (
        tmp_path
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20260901-testset-01-cfl003-test.ipd.md"
    )
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "---\n" "- Id: cfl003\n" "- Status: to-review\n" "---\n\n" "# Plan\n",
        encoding="utf-8",
    )

    # Initialize git repo in tmp_path so it passes git repo checks
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    args = argparse.Namespace(
        repo=str(tmp_path),
        selectors=["cfl003"],
        manifest=None,
        action="review",
        allow_uncovered_orchestrator_work=None,
        retry_budget=None,
        auto=True,
        execution_profile=None,
        host_sandbox_profile=None,
        validate=False,
        no_audit=True,
        agy_executable=None,
        agy=None,
        model=None,
        effort=None,
        timeout=10,
        new_session=False,
        dangerously_skip_permissions=True,
        no_verify=True,
    )

    fake_run_map = {"cfl003": "running"}

    runs_root = tmp_path / ".aw" / "records" / "runs"

    with patch(
        "agent_workflows.attention.get_active_runs_map", return_value=fake_run_map
    ):
        with pytest.raises(runner_shared.DriverError) as exc_info:
            oc_runipd.initialize_run(args)
        assert (
            "Cannot run artifacts that are actively being processed by another runner."
            in str(exc_info.value)
        )
        # Ensure no run directory was created
        if runs_root.exists():
            assert list(runs_root.iterdir()) == []

        with pytest.raises(runner_shared.DriverError) as exc_info:
            agy_runipd.initialize_run(args)
        assert (
            "Cannot run artifacts that are actively being processed by another runner."
            in str(exc_info.value)
        )
        if runs_root.exists():
            assert list(runs_root.iterdir()) == []


def test_format_slated_artifacts_table(tmp_path: Path) -> None:
    plan_path = tmp_path / "20260901-myset-01-slt001-first.ipd.md"
    plan_path.write_text(
        "---\n" "- Id: slt001\n" "- Status: approved\n" "---\n\n" "# Plan\n",
        encoding="utf-8",
    )

    queue = [
        {
            "id6": "slt001",
            "configured_file": str(plan_path),
            "status": "queued",
            "initial_status": "approved",
            "dependencies": [],
        }
    ]

    table = runner_shared.format_slated_artifacts_table(
        tmp_path, queue, term=T.Term(color=False)
    )
    assert "Status" in table
    assert "Run" in table
    assert "Type" in table
    assert "slt001" in table
    assert "queued" in table
    assert "Run = Active runner state" in table


def test_announce_run_order_includes_slated_artifacts_table(tmp_path: Path) -> None:
    plan_path = tmp_path / "20260901-myset-01-slt002-announce.ipd.md"
    plan_path.write_text(
        "---\n" "- Id: slt002\n" "- Status: approved\n" "---\n\n" "# Plan\n",
        encoding="utf-8",
    )

    state = {
        "repo": str(tmp_path),
        "run_id": "run-test-announce",
        "queue": [
            {
                "id6": "slt002",
                "configured_file": str(plan_path),
                "status": "queued",
                "initial_status": "approved",
                "dependencies": [],
            }
        ],
        "selectors": ["slt002"],
    }
    run_dir = tmp_path / "run-test-announce"
    run_dir.mkdir(parents=True, exist_ok=True)

    out = io.StringIO()
    oc_runipd.announce_run_order(run_dir, state, stream=out)
    text = out.getvalue()

    assert "Run order" in text
    assert "slt002" in text
    assert "Status" in text
    assert "Run" in text
    assert "queued" in text
    assert "Run = Active runner state" in text


def test_runners_reexport_shared_functions() -> None:
    # Both runners must expose the same functions from runner_shared
    for runner in (oc_runipd, agy_runipd):
        assert hasattr(runner, "enforce_no_active_runner_conflict")
        assert (
            runner.enforce_no_active_runner_conflict
            is runner_shared.enforce_no_active_runner_conflict
        )
        assert hasattr(runner, "format_slated_artifacts_table")
        assert (
            runner.format_slated_artifacts_table
            is runner_shared.format_slated_artifacts_table
        )
