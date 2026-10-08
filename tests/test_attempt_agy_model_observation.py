"""Tests for Antigravity attempt model observation (IPD rejqff).

Pins the producer behaviorally by driving execute_item_core and observe_host_model
over real execution shapes and asserting on observable attempt records and outcomes.
"""

from __future__ import annotations

import inspect
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from agent_workflows import agy_runipd, runner_shared
from agent_workflows.run_analytics_schema import resolve_attempt_model
from tests.support import coordinator_role
from tests.test_attempt_model_identity import _setup_test_repo


class MockProcess:
    """Mock subprocess.Popen object returning stream-json lines."""

    def __init__(self, stdout_text: str, rc: int = 0):
        self.stdout = io.StringIO(stdout_text)
        self.returncode = rc
        self.pid = 99999

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


def _drive_execute_turn_agy(
    repo_root: Path,
    plan_file: Path,
    options: dict[str, Any],
    stdout_lines: str,
    *,
    rc: int = 0,
    session_id: str | None = None,
    run_id: str = "run-test",
    item_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Drive execute_item_core using agy_runipd as driver_module and run_agy_turn as executor."""
    run_dir = repo_root / f".aw/runs/{run_id}"
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
    if item_overrides:
        item.update(item_overrides)

    state: dict[str, Any] = {
        "repo": str(repo_root),
        "run_id": run_id,
        "queue": [item],
        "options": dict(options),
    }
    state["options"].setdefault("isolate_worktrees", False)
    state["options"].setdefault("self_finalize", False)
    state["options"]["validate"] = False
    state["options"]["no_verify"] = True
    state["options"]["output_mode"] = "quiet"

    outcome = run_dir / f"outcomes/{item['position']:02d}-{item['id6']}.json"
    outcome.write_text(
        json.dumps(
            {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            }
        ),
        encoding="utf-8",
    )

    def _spawn_executor(
        prompt_path: Path,
        work_dir: Path | None,
        tracker: Any,
        plan_path: Path,
        attempt_no: int,
        turn_session_id: str | None,
        use_continue: bool,
    ) -> tuple[int, str | None, Path, list[str]]:
        eff_session_id = session_id if session_id is not None else turn_session_id
        with patch("subprocess.Popen", return_value=MockProcess(stdout_lines, rc=rc)):
            return agy_runipd.run_agy_turn(
                state,
                run_dir,
                item,
                prompt_path,
                attempt_no,
                session_id=eff_session_id,
                use_continue=use_continue,
            )

    with coordinator_role():
        runner_shared.execute_item_core(
            run_dir,
            state,
            item,
            recovery=False,
            host_labels=runner_shared.AGY_HOST_LABELS,
            spawn_executor=_spawn_executor,
            spawn_verifier=lambda *a, **k: (0, None, None, []),
            raw_launcher=agy_runipd.run_agy_turn,
            run_suite_check=lambda p, s: None,
            process_backlog_close=lambda *a, **k: None,
            driver_module=agy_runipd,
        )
    return state, item


class TestAttemptAgyModelObservation(unittest.TestCase):
    """Behavioral tests for Antigravity host model observation (IPD rejqff)."""

    def test_case_a_successful_read_records_all_three_keys(self) -> None:
        """Case (a): Attempt with model in init records host_model, host_model_provider, host_model_source."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            stdout = (
                '{"event": "init", "conversation_id": "conv-case-a", "init": {"model": "gemini-3.8-flash-low"}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {"model": "gemini-3.8-flash-low"},
                stdout,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertEqual(att.get("host_model"), "gemini-3.8-flash-low")
            self.assertEqual(att.get("host_model_provider"), "")
            self.assertEqual(att.get("host_model_source"), "init-event-echo")

    def test_case_b_no_model_in_init_records_none_and_preserves_outcome(self) -> None:
        """Case (b): Attempt with no model in init records none and matches case (a) in status/exit."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            stdout_a = (
                '{"event": "init", "conversation_id": "conv-a", "init": {"model": "gemini-3.8-flash-low"}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item_a = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {"model": "gemini-3.8-flash-low"},
                stdout_a,
                run_id="run-a",
            )
            stdout_b = (
                '{"event": "init", "conversation_id": "conv-b", "init": {}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item_b = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {},
                stdout_b,
                run_id="run-b",
            )
            att_a = item_a["attempts"][0]
            att_b = item_b["attempts"][0]

            self.assertNotIn("host_model", att_b)
            self.assertNotIn("host_model_provider", att_b)
            self.assertNotIn("host_model_source", att_b)

            # Outcome identical
            self.assertEqual(att_b.get("exit_code"), att_a.get("exit_code"))
            self.assertEqual(att_b.get("disposition"), att_a.get("disposition"))
            self.assertEqual(item_b.get("status"), item_a.get("status"))

    def test_case_c_antigravity_placeholder_records_none(self) -> None:
        """Case (c): Attempt whose init carries placeholder 'antigravity' records no host_model* keys."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            stdout = (
                '{"event": "init", "conversation_id": "conv-placeholder", "init": {"model": "antigravity"}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {},
                stdout,
            )
            att = item["attempts"][0]
            self.assertNotIn("host_model", att)
            self.assertNotIn("host_model_provider", att)
            self.assertNotIn("host_model_source", att)

    def test_case_d_empty_or_unparseable_log_records_none_and_raises_nothing(
        self,
    ) -> None:
        """Case (d): Empty or unparseable log records none and raises nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            for run_idx, stdout in enumerate(
                ["", "\n", "NOT VALID JSON\n", '{"event": "not-init"}\n']
            ):
                _, item = _drive_execute_turn_agy(
                    repo_root,
                    plan_file,
                    {},
                    stdout,
                    run_id=f"run-d-{run_idx}",
                )
                att = item["attempts"][0]
                self.assertNotIn("host_model", att)
                self.assertNotIn("host_model_provider", att)
                self.assertNotIn("host_model_source", att)

    def test_case_d2_reused_conversation_clears_stale_model(self) -> None:
        """Case (d2): Reused conversation id whose second turn has no model records none for second attempt."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            # First turn: carries model
            stdout_1 = (
                '{"event": "init", "conversation_id": "conv-reuse", "init": {"model": "gemini-3.8-flash-low"}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item_1 = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {"model": "gemini-3.8-flash-low"},
                stdout_1,
                session_id="conv-reuse",
                run_id="run-d2-1",
            )
            self.assertEqual(
                item_1["attempts"][0].get("host_model"), "gemini-3.8-flash-low"
            )

            # Second turn: reuses conversation id, but stream has no model
            stdout_2 = (
                '{"event": "init", "conversation_id": "conv-reuse", "init": {}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            _, item_2 = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {},
                stdout_2,
                session_id="conv-reuse",
                run_id="run-d2-2",
            )
            att_2 = item_2["attempts"][0]
            self.assertNotIn("host_model", att_2)
            self.assertNotIn("host_model_provider", att_2)
            self.assertNotIn("host_model_source", att_2)

    def test_case_e_seam_contract_resolution_through_driver_module(self) -> None:
        """Case (e): Reader is resolved off driver_module by execute_item_core with exact signature."""
        self.assertTrue(
            hasattr(agy_runipd, "observe_host_model"),
            "agy_runipd must define observe_host_model",
        )
        sig = inspect.signature(agy_runipd.observe_host_model)
        param_names = list(sig.parameters.keys())
        self.assertEqual(param_names, ["session_id", "options", "repo_root"])
        # options and repo_root must be keyword-only or accept keyword arguments
        self.assertIn(
            sig.parameters["options"].kind,
            (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        )
        self.assertIn(
            sig.parameters["repo_root"].kind,
            (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        )

        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            stdout = (
                '{"event": "init", "conversation_id": "conv-seam", "init": {"model": "Gemini 3.8 Flash (High)"}}\n'
                '{"event": "result", "result": {"status": "DONE"}}\n'
            )
            # execute_item_core is driven with driver_module=agy_runipd and observe_host_model=None
            _, item = _drive_execute_turn_agy(
                repo_root,
                plan_file,
                {"model": "Gemini 3.8 Flash (High)"},
                stdout,
            )
            att = item["attempts"][0]
            self.assertEqual(att.get("host_model"), "Gemini 3.8 Flash (High)")
            self.assertEqual(att.get("host_model_provider"), "")
            self.assertEqual(att.get("host_model_source"), "init-event-echo")

    def test_case_f_consumer_precedence_tier_1_with_agy_source(self) -> None:
        """Case (f): resolve_attempt_model returns tier 1 with agy source label ahead of conflicting frozen model."""
        attempt = {
            "host_model": "gemini-3.8-flash-low",
            "host_model_provider": "",
            "host_model_source": "init-event-echo",
            "model": "gemini-3.1-pro",
        }
        state = {"options": {"model": "gemini-3.1-pro"}}
        model, source = resolve_attempt_model(attempt, state=state)
        self.assertEqual(model, "gemini-3.8-flash-low")
        self.assertEqual(source, "init-event-echo")
        # Ensure attempt keys were not modified
        self.assertEqual(attempt.get("host_model"), "gemini-3.8-flash-low")
        self.assertEqual(attempt.get("model"), "gemini-3.1-pro")
