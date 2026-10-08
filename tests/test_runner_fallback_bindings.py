"""Tests for execute_item_core fallback bindings and execution limits (IPD vfjw09 E-04, E-05).

Pins the behavior of runner_shared.execute_item_core when driven with a descriptor-only
driver_module that defines none of the rebound host collaborators.
"""

from __future__ import annotations

from collections import namedtuple
import json
from pathlib import Path
import re
import tempfile
import types
from typing import Any

import pytest

from agent_workflows import runner_shared
from tests.test_attempt_model_identity import _setup_test_repo

Verdict = namedtuple("Verdict", ["earned", "signal", "detail"])


def _drive_execute_turn_with_driver(
    repo_root: Path,
    plan_file: Path,
    driver_module: Any,
    options: dict[str, Any] | None = None,
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
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
    }
    opts = dict(options or {})
    opts.setdefault("isolate_worktrees", False)
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

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery=False,
        host_labels=runner_shared.OC_HOST_LABELS,
        spawn_executor=default_executor,
        spawn_verifier=default_verifier,
        raw_launcher=lambda *a, **k: None,
        run_suite_check=lambda p, s: None,
        process_backlog_close=lambda *a, **k: None,
        driver_module=driver_module,
    )
    return state, item, run_dir


def test_descriptor_only_host_fallbacks_unblock_and_record_git_state() -> None:
    """E-04: With an empty driver_module, fallbacks unblock and record git state.

    The turn passes route_recovery_turn, git_head, and git_status, recording
    valid starting_head (40-hex SHA) and starting_status rather than an error.
    It stops at integration_is_earned (next wall), raising TypeError.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo_root, plan_file = _setup_test_repo(root)
        empty_module = types.ModuleType("descriptor_only")

        with pytest.raises(TypeError) as exc_info:
            _drive_execute_turn_with_driver(
                repo_root, plan_file, driver_module=empty_module
            )

        # Before E-02, the exception is:
        # TypeError: route_recovery_turn() missing 1 required keyword-only argument: 'save_state'
        # which fails before recording the attempt.
        # After E-02, route_recovery_turn, git_head, and git_status succeed, and the turn
        # raises TypeError('\'NoneType\' object is not callable') at integration_is_earned.
        assert (
            "'NoneType' object is not callable" in str(exc_info.value)
        ), f"Expected next-wall TypeError('NoneType object is not callable'), got: {exc_info.value}"

        state_file = repo_root / ".aw/runs/run-test/state.json"
        assert state_file.exists(), "state.json must be persisted"
        persisted_state = json.loads(state_file.read_text(encoding="utf-8"))
        item = persisted_state["queue"][0]
        attempts = item.get("attempts", [])
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
    """E-05: Pin the measured limit for a descriptor-only host.

    Records that after the 5 broken fallbacks are fixed, the next blocker is
    the unguarded None default for integration_is_earned (and subsequent
    deferred symbols: driver_finalize, set_plan_approved, integrate_review_lane_branch).
    Proves by outcome:
    1. Unmodified empty module raises TypeError: 'NoneType' object is not callable
       and integration_signal is NEVER recorded on the attempt.
    2. When integration_is_earned is supplied on the module, the turn moves past
       integration_is_earned (sentinel is called) and does not raise at that site.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo_root, plan_file = _setup_test_repo(root)
        empty_module = types.ModuleType("descriptor_only")

        with pytest.raises(TypeError) as exc_info:
            _drive_execute_turn_with_driver(
                repo_root, plan_file, driver_module=empty_module
            )

        assert "'NoneType' object is not callable" in str(exc_info.value)

        state_file = repo_root / ".aw/runs/run-test/state.json"
        persisted_state = json.loads(state_file.read_text(encoding="utf-8"))
        attempt = persisted_state["queue"][0]["attempts"][0]
        assert (
            "integration_signal" not in attempt
        ), "integration_signal must not be recorded when integration_is_earned is None"

    # Sentinel test: supplying integration_is_earned moves past the wall
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo_root, plan_file = _setup_test_repo(root)
        mock_module = types.ModuleType("descriptor_only_with_sentinel")

        sentinel_calls: list[dict[str, Any]] = []
        mock_module.integration_is_earned = lambda **kws: (
            sentinel_calls.append(kws)
            or Verdict(earned=False, signal="refused", detail="sentinel_verdict")
        )

        # The turn moves past integration_is_earned without raising TypeError at that site
        _drive_execute_turn_with_driver(repo_root, plan_file, driver_module=mock_module)

        assert (
            len(sentinel_calls) == 1
        ), f"Expected sentinel integration_is_earned to be called once, got {len(sentinel_calls)}"
