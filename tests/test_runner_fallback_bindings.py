"""Tests for execute_item_core fallback bindings and execution limits (IPD vfjw09 E-04, E-05; u3ji9d E-05).

Pins the behavior of runner_shared.execute_item_core when driven with a descriptor-only
driver_module that defines none of the rebound host collaborators.
"""

from __future__ import annotations

from collections import namedtuple
import json
import os
from pathlib import Path
import re
import tempfile
import types
from typing import Any
from unittest import mock


from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.test_attempt_model_identity import _setup_test_repo

Verdict = namedtuple("Verdict", ["earned", "signal", "detail"])


def _clean_env() -> dict[str, str]:
    return {
        k: v
        for k, v in os.environ.items()
        if k not in ("AW_EXECUTION_ROLE", "AW_RUN_ID", "AW_ITEM_ID6")
    }


def _drive_execute_turn_with_driver(
    repo_root: Path,
    plan_file: Path,
    driver_module: Any,
    options: dict[str, Any] | None = None,
    *,
    host_labels: Any = runner_shared.OC_HOST_LABELS,
    run_suite_check: Any = None,
    spawn_executor: Any = None,
    item_action: str = "execute",
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    """Drive execute_item_core with a specified driver_module, reusing the turn setup."""
    run_dir = repo_root / ".aw/runs/run-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "id6": "tst001",
        "setid": "test",
        "position": 1,
        "action": item_action,
        "status": "queued",
        "configured_file": str(plan_file),
    }
    opts = dict(options or {})
    opts.setdefault("isolate_worktree", False)
    opts.setdefault("self_finalize", False)
    opts.setdefault("validate", False)
    opts.setdefault("no_verify", True)

    state: dict[str, Any] = {
        "repo": str(repo_root),
        "run_id": "run-test",
        "queue": [item],
        "options": opts,
    }

    log_path = run_dir / "logs/test.log"
    outcome_path = run_dir / "outcomes/01-tst001.json"

    def default_executor(*args: Any, **kwargs: Any) -> tuple[int, str, Path, list[str]]:
        log_path.write_text("test log", encoding="utf-8")
        outcome_path.write_text(
            json.dumps(
                {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                }
            ),
            encoding="utf-8",
        )
        return 0, "session-123", log_path, ["mock_agent"]

    def default_verifier(
        *args: Any, **kwargs: Any
    ) -> tuple[int, None, None, list[str]]:
        return 0, None, None, []

    suite_check_fn = run_suite_check or (lambda p, s: None)
    executor_fn = spawn_executor or default_executor

    with mock.patch.dict(os.environ, _clean_env(), clear=True):
        runner_shared.execute_item_core(
            run_dir,
            state,
            item,
            recovery=False,
            host_labels=host_labels,
            spawn_executor=executor_fn,
            spawn_verifier=default_verifier,
            raw_launcher=lambda *a, **k: None,
            run_suite_check=suite_check_fn,
            process_backlog_close=lambda *a, **k: None,
            driver_module=driver_module,
        )
    return state, item, run_dir


def test_descriptor_only_host_fallbacks_unblock_and_record_git_state() -> None:
    """E-04 / E-05: With an empty driver_module, fallbacks unblock and record git state.

    The turn passes route_recovery_turn, git_head, git_status, and integration_is_earned,
    returning without raising TypeError and reaching a terminal disposition.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo_root, plan_file = _setup_test_repo(root)
        empty_module = types.ModuleType("descriptor_only")

        state, item, run_dir = _drive_execute_turn_with_driver(
            repo_root, plan_file, driver_module=empty_module
        )

        assert item.get("status") in (
            "fail-gate",
            "executed",
            "substantially-complete",
            "failed-safely",
        )
        state_file = repo_root / ".aw/runs/run-test/state.json"
        assert state_file.exists(), "state.json must be persisted"
        persisted_state = json.loads(state_file.read_text(encoding="utf-8"))
        item_persisted = persisted_state["queue"][0]
        attempts = item_persisted.get("attempts", [])
        assert len(attempts) == 1, f"Expected 1 attempt recorded, got {len(attempts)}"

        attempt = attempts[0]
        starting_head = attempt.get("starting_head")
        assert starting_head is not None
        assert not starting_head.startswith("<unobserved:")
        assert re.fullmatch(
            r"[0-9a-f]{40}", starting_head
        ), f"starting_head must be a 40-hex commit hash, got {starting_head!r}"

        starting_status = attempt.get("starting_status")
        assert starting_status is not None
        assert not starting_status.startswith("<unobserved:")
        assert (
            "??" in starting_status
        ), f"starting_status should reflect real porcelain status (untracked .aw), got: {starting_status!r}"


def test_pin_descriptor_only_host_execution_limit_integration_is_earned() -> None:
    """E-05: Fallback for integration_is_earned forwards to shared definition.

    With an empty driver_module, integration_is_earned resolves to the shared predicate
    and returns an IntegrationVerdict without raising TypeError.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo_root, plan_file = _setup_test_repo(root)
        empty_module = types.ModuleType("descriptor_only")

        recorded_calls: list[dict[str, Any]] = []
        original_predicate = runner_shared.integration_is_earned

        def recording_predicate(
            *, validate: bool, verify_disp: str | None, suite_result: Any
        ) -> Any:
            verdict = original_predicate(
                validate=validate, verify_disp=verify_disp, suite_result=suite_result
            )
            recorded_calls.append(
                {
                    "validate": validate,
                    "verify_disp": verify_disp,
                    "suite_result": suite_result,
                    "verdict": verdict,
                }
            )
            return verdict

        with mock.patch.object(
            runner_shared, "integration_is_earned", side_effect=recording_predicate
        ):
            state, item, run_dir = _drive_execute_turn_with_driver(
                repo_root, plan_file, driver_module=empty_module
            )

        assert (
            len(recorded_calls) == 1
        ), f"Expected 1 integration_is_earned call, got {len(recorded_calls)}"
        assert recorded_calls[0]["validate"] is False
        assert recorded_calls[0]["verify_disp"] is None
        assert isinstance(
            recorded_calls[0]["verdict"], runner_shared.IntegrationVerdict
        )


def test_fallback_driver_finalize_forwards_host_equivalent_arguments() -> None:
    """E-03 / E-05: driver_finalize fallback forwards host labels and builders."""
    for host_labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root, plan_file = _setup_test_repo(root)
            empty_module = types.ModuleType("descriptor_only")
            empty_module.driver_begin = lambda *a, **k: (0, "ok")

            finalize_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

            def mock_finalize(*args: Any, **kwargs: Any) -> tuple[int, str]:
                finalize_calls.append((args, kwargs))
                return 0, "finalized"

            with mock.patch.object(
                runner_shared, "driver_finalize", side_effect=mock_finalize
            ):
                state, item, run_dir = _drive_execute_turn_with_driver(
                    repo_root,
                    plan_file,
                    driver_module=empty_module,
                    options={
                        "isolate_worktree": False,
                        "self_finalize": True,
                        "validate": False,
                        "no_verify": True,
                    },
                    host_labels=host_labels,
                    run_suite_check=lambda p, s: runner_shared.SuiteCheckResult(
                        True, 0, "ok", "ok", "", 1.0, 0.1
                    ),
                )

            assert (
                len(finalize_calls) == 1
            ), f"Expected 1 driver_finalize call, got {len(finalize_calls)}"
            args, kwargs = finalize_calls[0]
            assert args[0] == repo_root
            assert args[1] == plan_file
            assert args[2] == "tst001"
            assert kwargs["labels"] is host_labels
            assert kwargs["env_builder"] is runner_shared.pinned_child_env
            assert kwargs["argv_builder"] is runner_shared.pinned_module_argv
            assert kwargs["run_id"] == "run-test"
            assert item.get("status") == "executed"


def test_fallback_set_plan_approved_forwards_host_equivalent_arguments() -> None:
    """E-03 / E-05: set_plan_approved fallback forwards host labels and run_checked."""
    for host_labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root, plan_file = _setup_test_repo(root)
            plan_text = plan_file.read_text(encoding="utf-8")
            plan_text = plan_text.replace("- Status: pending", "- Status: to-review")
            plan_file.write_text(plan_text, encoding="utf-8")

            run_dir = repo_root / ".aw/runs/run-test"
            run_dir.mkdir(parents=True, exist_ok=True)
            log_path = run_dir / "logs/test.log"
            outcome_path = run_dir / "outcomes/01-tst001.json"

            def review_executor(
                *args: Any, **kwargs: Any
            ) -> tuple[int, str, Path, list[str]]:
                log_path.write_text("review log", encoding="utf-8")
                outcome_path.write_text(
                    json.dumps(
                        {
                            "disposition": "reviewed",
                            "verdict": "APPROVE WITH REVISIONS APPLIED",
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                t = plan_file.read_text(encoding="utf-8")
                t = t.replace(
                    "- Status: to-review",
                    "- Status: reviewed\n- Readiness: go-pending-approval",
                )
                t += "\n## Workflow history\n- 2026-10-12 reviewed (/plan-review): APPROVE WITH REVISIONS APPLIED\n"
                plan_file.write_text(t, encoding="utf-8")
                return 0, "session-123", log_path, ["mock_agent"]

            empty_module = types.ModuleType("descriptor_only")
            empty_module.driver_begin = lambda *a, **k: (0, "ok")

            approved_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

            def mock_approve(*args: Any, **kwargs: Any) -> None:
                approved_calls.append((args, kwargs))

            with mock.patch.object(
                runner_shared, "set_plan_approved", side_effect=mock_approve
            ):
                state, item, run_dir = _drive_execute_turn_with_driver(
                    repo_root,
                    plan_file,
                    driver_module=empty_module,
                    options={
                        "isolate_review": False,
                        "full_auto": True,
                        "validate": False,
                        "no_verify": True,
                    },
                    host_labels=host_labels,
                    spawn_executor=review_executor,
                    item_action="review",
                )

            assert (
                len(approved_calls) == 1
            ), f"Expected 1 set_plan_approved call, got {len(approved_calls)}"
            args, kwargs = approved_calls[0]
            assert args[0] == repo_root
            assert args[1] == "tst001"
            assert args[2] == runner_shared.FULL_AUTO_APPROVAL_MESSAGE
            assert kwargs["labels"] is host_labels
            assert kwargs["argv_builder"] is runner_shared.pinned_module_argv
            run_checked_fn = kwargs["run_checked"]
            assert callable(run_checked_fn)
            ret = run_checked_fn(["git", "rev-parse", "HEAD"], cwd=repo_root)
            assert re.fullmatch(r"[0-9a-f]{40}\n?", ret.strip())
            assert item.get("status") == "queued"
            assert item.get("auto_approved") is True


def test_fallback_integrate_review_lane_branch_forwards_host_equivalent_arguments() -> (
    None
):
    """E-04 / E-05: integrate_review_lane_branch fallback forwards review action and command label."""
    assert not hasattr(runner_shared, "integrate_review_lane_branch")

    for host_labels in (runner_shared.OC_HOST_LABELS, runner_shared.AGY_HOST_LABELS):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root, plan_file = _setup_test_repo(root)
            plan_text = plan_file.read_text(encoding="utf-8")
            plan_text = plan_text.replace("- Status: pending", "- Status: to-review")
            plan_file.write_text(plan_text, encoding="utf-8")

            run_dir = repo_root / ".aw/runs/run-test"
            run_dir.mkdir(parents=True, exist_ok=True)
            log_path = run_dir / "logs/test.log"
            outcome_path = run_dir / "outcomes/01-tst001.json"

            def review_executor(
                *args: Any, **kwargs: Any
            ) -> tuple[int, str, Path, list[str]]:
                log_path.write_text("review log", encoding="utf-8")
                outcome_path.write_text(
                    json.dumps(
                        {
                            "disposition": "reviewed",
                            "verdict": "APPROVE WITH REVISIONS APPLIED",
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                t = plan_file.read_text(encoding="utf-8")
                t = t.replace(
                    "- Status: to-review",
                    "- Status: reviewed\n- Readiness: go-pending-approval",
                )
                t += "\n## Workflow history\n- 2026-10-12 reviewed (/plan-review): APPROVE WITH REVISIONS APPLIED\n"
                plan_file.write_text(t, encoding="utf-8")
                return 0, "session-123", log_path, ["mock_agent"]

            empty_module = types.ModuleType("descriptor_only")
            empty_module.driver_begin = lambda *a, **k: (0, "ok")

            irlb_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

            def mock_irlb(*args: Any, **kwargs: Any) -> tuple[bool, str, str]:
                irlb_calls.append((args, kwargs))
                return True, "merged", ""

            with (
                mock.patch.object(
                    runner_shared, "integrate_lane_branch", side_effect=mock_irlb
                ),
                mock.patch.object(
                    runner_shared, "set_plan_approved", return_value=None
                ),
            ):
                state, item, run_dir = _drive_execute_turn_with_driver(
                    repo_root,
                    plan_file,
                    driver_module=empty_module,
                    options={
                        "isolate_review": True,
                        "full_auto": True,
                        "validate": False,
                        "no_verify": True,
                    },
                    host_labels=host_labels,
                    spawn_executor=review_executor,
                    item_action="review",
                )

            assert (
                len(irlb_calls) == 1
            ), f"Expected 1 integrate_review_lane_branch call, got {len(irlb_calls)}"
            args, kwargs = irlb_calls[0]
            assert args[0] == repo_root
            assert args[2] == "tst001"
            assert args[3] is None  # validation_runner is None for review
            assert kwargs["host_label"] == host_labels.command
            assert kwargs["action_kind"] == "review"
            assert callable(kwargs["run_checked"])


def test_host_preference_preserved_for_shipped_hosts() -> None:
    """E-05: Host-defined attributes take precedence over runner_shared fallbacks."""
    for host_mod, host_labels in (
        (oc_runipd, runner_shared.OC_HOST_LABELS),
        (agy_runipd, runner_shared.AGY_HOST_LABELS),
    ):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root, plan_file = _setup_test_repo(root)

            shared_calls: list[str] = []
            host_calls: list[str] = []

            def mock_shared_finalize(*args: Any, **kwargs: Any) -> tuple[int, str]:
                shared_calls.append("shared_finalize")
                return 0, "shared"

            def mock_host_finalize(*args: Any, **kwargs: Any) -> tuple[int, str]:
                host_calls.append("host_finalize")
                return 0, "host"

            with (
                mock.patch.object(
                    runner_shared, "driver_finalize", side_effect=mock_shared_finalize
                ),
                mock.patch.object(host_mod, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(
                    host_mod,
                    "run_suite_check",
                    return_value=runner_shared.SuiteCheckResult(
                        True, 0, "ok", "ok", "", 1.0, 0.1
                    ),
                ),
                mock.patch.object(
                    host_mod, "driver_finalize", side_effect=mock_host_finalize
                ),
            ):
                state, item, run_dir = _drive_execute_turn_with_driver(
                    repo_root,
                    plan_file,
                    driver_module=host_mod,
                    options={
                        "isolate_worktree": False,
                        "self_finalize": True,
                        "validate": False,
                        "no_verify": True,
                    },
                    host_labels=host_labels,
                )

            assert (
                "host_finalize" in host_calls
            ), "Host module driver_finalize must be called"
            assert (
                "shared_finalize" not in shared_calls
            ), "Shared fallback must NOT be called when host defines attribute"

        # Review turn: integrate_review_lane_branch and set_plan_approved
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root, plan_file = _setup_test_repo(root)
            plan_text = plan_file.read_text(encoding="utf-8")
            plan_text = plan_text.replace("- Status: pending", "- Status: to-review")
            plan_file.write_text(plan_text, encoding="utf-8")

            run_dir = repo_root / ".aw/runs/run-test"
            run_dir.mkdir(parents=True, exist_ok=True)
            log_path = run_dir / "logs/test.log"
            outcome_path = run_dir / "outcomes/01-tst001.json"

            def review_executor(
                *args: Any, **kwargs: Any
            ) -> tuple[int, str, Path, list[str]]:
                log_path.write_text("review log", encoding="utf-8")
                outcome_path.write_text(
                    json.dumps(
                        {
                            "disposition": "reviewed",
                            "verdict": "APPROVE WITH REVISIONS APPLIED",
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                t = plan_file.read_text(encoding="utf-8")
                t = t.replace(
                    "- Status: to-review",
                    "- Status: reviewed\n- Readiness: go-pending-approval",
                )
                t += "\n## Workflow history\n- 2026-10-12 reviewed (/plan-review): APPROVE WITH REVISIONS APPLIED\n"
                plan_file.write_text(t, encoding="utf-8")
                return 0, "session-123", log_path, ["mock_agent"]

            host_irlb_calls: list[str] = []
            host_approve_calls: list[str] = []
            shared_approve_calls: list[str] = []

            def mock_host_irlb(*args: Any, **kwargs: Any) -> tuple[bool, str, str]:
                host_irlb_calls.append("host_irlb")
                return True, "merged", ""

            def mock_host_approve(*args: Any, **kwargs: Any) -> None:
                host_approve_calls.append("host_approve")

            def mock_shared_approve(*args: Any, **kwargs: Any) -> None:
                shared_approve_calls.append("shared_approve")

            with (
                mock.patch.object(host_mod, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(
                    host_mod, "integrate_review_lane_branch", side_effect=mock_host_irlb
                ),
                mock.patch.object(
                    host_mod, "set_plan_approved", side_effect=mock_host_approve
                ),
                mock.patch.object(
                    runner_shared, "set_plan_approved", side_effect=mock_shared_approve
                ),
            ):
                state, item, run_dir = _drive_execute_turn_with_driver(
                    repo_root,
                    plan_file,
                    driver_module=host_mod,
                    options={
                        "isolate_review": True,
                        "full_auto": True,
                        "validate": False,
                        "no_verify": True,
                    },
                    host_labels=host_labels,
                    spawn_executor=review_executor,
                    item_action="review",
                )

            assert (
                "host_irlb" in host_irlb_calls
            ), "Host module integrate_review_lane_branch must be called"
            assert (
                "host_approve" in host_approve_calls
            ), "Host module set_plan_approved must be called"
            assert (
                "shared_approve" not in shared_approve_calls
            ), "Shared fallback set_plan_approved must NOT be called"
