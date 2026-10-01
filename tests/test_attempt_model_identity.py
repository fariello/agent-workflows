"""Tests for attempt model identity (attmodel czut8j E-05).

Pins the producer behaviorally by driving execute_item_core over real execution shapes
and asserting on observable attempt records and outcomes.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from agent_workflows import host_sandbox_profile as hsp
from agent_workflows import oc_runipd, runner_shared, runner_stop
from tests.test_host_capability_extension import synthetic_gated_action


def _fail_spawn(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("Must not spawn executor")


@contextmanager
def _bound_contract_action(
    runner_action: str = "execute", contract_action: str = "_gated_for_test"
):
    """Temporarily map a runner action to a contract action in runner_shared."""
    table = getattr(runner_shared, "RUNNER_ACTION_TO_CONTRACT_ACTION", None)
    if table is None:
        yield
        return
    saved = dict(table)
    table[runner_action] = contract_action
    try:
        yield
    finally:
        table.clear()
        table.update(saved)


def _setup_test_repo(root: Path) -> tuple[Path, Path]:
    """Initialize a git repo with a commit and an approved IPD plan."""
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "file.txt").write_text("initial content", encoding="utf-8")
    subprocess.run(
        ["git", "add", "file.txt"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True
    )

    plan_dir = root / ".aw/records/plans/pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "20261001-test-01-tst001-test.ipd.md"
    plan_file.write_text(
        "# IPD: Test\n- Id: tst001\n- Set: test\n- Status: approved\n- Scope-Paths: file.txt\n",
        encoding="utf-8",
    )
    return root, plan_file


def _drive_execute_turn(
    repo_root: Path,
    plan_file: Path,
    options: dict[str, Any],
    *,
    in_flight_callback: Any = None,
    spawn_executor: Any = None,
    spawn_verifier: Any = None,
    validate: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Drive execute_item_core on a standard item and return (state, item)."""
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
    state: dict[str, Any] = {
        "repo": str(repo_root),
        "run_id": "run-test",
        "queue": [item],
        "options": dict(options),
    }
    state["options"].setdefault("isolate_worktrees", False)
    state["options"].setdefault("self_finalize", False)
    if validate:
        state["options"]["validate"] = True
    else:
        state["options"]["validate"] = False
        state["options"]["no_verify"] = True

    if spawn_executor is None:

        def default_executor(
            prompt_path: Path,
            work_dir: Any,
            tracker: Any,
            p_path: Path,
            attempt_no: int,
            session_id: Any,
            use_continue: bool,
        ) -> tuple[int, str, Path, list[str]]:
            if in_flight_callback:
                in_flight_callback(run_dir, state, item)
            log_path = run_dir / "logs/test.log"
            log_path.write_text("test log", encoding="utf-8")
            outcome = run_dir / "outcomes/01-tst001.json"
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
            return 0, "session-123", log_path, ["mock_agent"]

        spawn_executor = default_executor

    if spawn_verifier is None:

        def default_verifier(*a: Any, **k: Any) -> tuple[int, None, None, list[str]]:
            return 0, None, None, []

        spawn_verifier = default_verifier

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery=False,
        host_labels=runner_shared.OC_HOST_LABELS,
        spawn_executor=spawn_executor,
        spawn_verifier=spawn_verifier,
        raw_launcher=lambda *a, **k: None,
        run_suite_check=lambda p, s: None,
        process_backlog_close=lambda *a, **k: None,
        driver_module=oc_runipd,
    )
    return state, item


class TestAttemptModelIdentity(unittest.TestCase):
    """Behavioral tests for per-attempt model identity (attmodel czut8j E-05)."""

    def test_case_a_one_model_run_records_model_with_source_options(self) -> None:
        """Case (a): A one-model run records that model on the attempt with source 'options'."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {"model": "test-provider/one-model-v1"},
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("model"), "test-provider/one-model-v1")
            self.assertEqual(attempt.get("model_source"), "options")

    def test_case_b_cost_attribution_fallback_records_model_with_source_cost_attribution(
        self,
    ) -> None:
        """Case (b): options.model is None but cost_attribution.model is set; records source 'cost_attribution'."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {
                    "model": None,
                    "cost_attribution": {
                        "kind": "launch-time-snapshot",
                        "host": "oc",
                        "model": "host-default-model-x",
                        "model_source": "host-default",
                    },
                },
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("model"), "host-default-model-x")
            self.assertEqual(attempt.get("model_source"), "cost_attribution")

    def test_case_c_neither_model_set_records_empty_model_with_source_unrecorded(
        self,
    ) -> None:
        """Case (c): Neither model nor cost_attribution has a model; records empty model with source 'unrecorded'."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {"model": None},
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertIn("model", attempt)
            self.assertIn("model_source", attempt)
            self.assertEqual(attempt.get("model"), "")
            self.assertEqual(attempt.get("model_source"), "unrecorded")

    def test_case_d_two_model_run_records_executor_and_verifier_models(self) -> None:
        """Case (d): A two-model run records executor on model and verifier on verify_model."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def mock_verifier(
                prompt_path: Path,
                p_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                v_log = run_dir / "logs/verify.log"
                v_log.write_text("verify log", encoding="utf-8")
                outcome = run_dir / "outcomes/01-tst001-verification.json"
                outcome.write_text(
                    json.dumps({"verdict": "VERIFIED", "summary": "all passed"}),
                    encoding="utf-8",
                )
                return (
                    0,
                    "v-session",
                    v_log,
                    ["mock_verifier", "--model", "provB/verifier-model"],
                )

            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {
                    "model": "provA/executor-model",
                    "verify_model": "provB/verifier-model",
                    "verify_launch_profile": {"profile": "ver-prof"},
                },
                validate=True,
                spawn_verifier=mock_verifier,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("model"), "provA/executor-model")
            self.assertEqual(attempt.get("model_source"), "options")
            self.assertEqual(attempt.get("verify_model"), "provB/verifier-model")
            self.assertEqual(attempt.get("verify_model_source"), "options")

    def test_case_e_agy_explicit_model_resolves_through_options(self) -> None:
        """Case (e): options carrying agy explicit_model resolves through it with source 'options'."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {
                    "model": None,
                    "explicit_model": "gemini-2.5-pro",
                    "cost_attribution": {"model": "fallback-model"},
                },
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("model"), "gemini-2.5-pro")
            self.assertEqual(attempt.get("model_source"), "options")

    def test_case_f_malformed_options_resolves_to_unrecorded_without_raising(
        self,
    ) -> None:
        """Case (f): Malformed options resolves to ('', 'unrecorded') without raising."""
        # Non-mapping cost_attribution
        res1 = runner_shared.launch_model_for_role(
            {"model": None, "cost_attribution": "this is a string not a mapping"}
        )
        self.assertEqual(res1, ("", "unrecorded"))

        # Non-mapping options itself
        res2 = runner_shared.launch_model_for_role(None)
        self.assertEqual(res2, ("", "unrecorded"))

        res3 = runner_shared.launch_model_for_role("not a mapping")  # type: ignore
        self.assertEqual(res3, ("", "unrecorded"))

        # Empty mapping
        res4 = runner_shared.launch_model_for_role({})
        self.assertEqual(res4, ("", "unrecorded"))

    def test_in_flight_attempt_has_model_before_turn_ends(self) -> None:
        """V-02: State inspected WHILE turn is in flight carries model and model_source."""
        in_flight_state: dict[str, Any] = {}

        def check_in_flight(
            run_dir: Path, state: dict[str, Any], item: dict[str, Any]
        ) -> None:
            nonlocal in_flight_state
            # Read attempt currently registered in item
            attempts = item.get("attempts", [])
            if attempts:
                in_flight_state = dict(attempts[0])

        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {"model": "test-provider/in-flight-model"},
                in_flight_callback=check_in_flight,
            )
            # In flight attempt must have model and model_source, but NOT ended_at
            self.assertEqual(
                in_flight_state.get("model"), "test-provider/in-flight-model"
            )
            self.assertEqual(in_flight_state.get("model_source"), "options")
            self.assertNotIn("ended_at", in_flight_state)

            # And after turn ends, ended_at exists
            attempts = item.get("attempts", [])
            self.assertIn("ended_at", attempts[0])

    def test_no_verifier_attempt_carries_neither_verify_key(self) -> None:
        """V-03: A run with no verifier phase carries neither verify_model nor verify_model_source."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            _, item = _drive_execute_turn(
                repo_root,
                plan_file,
                {"model": "test-provider/no-verifier-model"},
                validate=False,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertNotIn("verify_model", attempt)
            self.assertNotIn("verify_model_source", attempt)

    def test_scope_target_refusal_records_model_without_raising(self) -> None:
        """V-04 / F-07: Scope-target refusal records model/model_source and does not raise UnboundLocalError."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, _ = _setup_test_repo(Path(td))
            # Create a plan with a vanished/stale scope path
            plan_dir = repo_root / ".aw/records/plans/pending"
            plan_file = plan_dir / "20261001-test-02-stale1-stale.ipd.md"
            # Reference a path under .aw/records/ that does not exist (vanished)
            plan_file.write_text(
                "# IPD: Stale\n- Id: stale1\n- Set: test\n- Status: approved\n"
                "- Scope-Paths: .aw/records/plans/pending/20261001-nonexistent-99-nonex-vanished.ipd.md\n",
                encoding="utf-8",
            )
            run_dir = repo_root / ".aw/runs/run-stale"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, Any] = {
                "id6": "stale1",
                "setid": "test",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
            }
            state: dict[str, Any] = {
                "repo": str(repo_root),
                "run_id": "run-stale",
                "queue": [item],
                "options": {"model": "test-model/scope-stale"},
            }
            runner_shared.execute_item_core(
                run_dir,
                state,
                item,
                recovery=False,
                host_labels=runner_shared.OC_HOST_LABELS,
                spawn_executor=_fail_spawn,
                spawn_verifier=lambda *a, **k: (0, None, None, []),
                raw_launcher=lambda *a, **k: None,
                run_suite_check=lambda p, s: None,
                process_backlog_close=lambda *a, **k: None,
                driver_module=oc_runipd,
            )
            self.assertEqual(item.get("status"), "fail-gate")
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("disposition"), "fail-gate")
            self.assertIn("scope_target_refused", attempt)
            self.assertEqual(attempt.get("model"), "test-model/scope-stale")
            self.assertEqual(attempt.get("model_source"), "options")

    def test_host_capability_refusal_records_model_without_raising(self) -> None:
        """V-04 / F-07: Host-capability refusal records model/model_source and does not raise UnboundLocalError."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-cap"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, Any] = {
                "id6": "tst001",
                "setid": "test",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
            }
            state: dict[str, Any] = {
                "repo": str(repo_root),
                "run_id": "run-cap",
                "queue": [item],
                "options": {"model": "test-model/cap-refused"},
            }
            with (
                hsp.forced_runner_safety_verdicts(
                    {hsp.CAP_COMMIT_GATEWAY: (False, "forced unavailable for test")}
                ),
                synthetic_gated_action(),
                _bound_contract_action("execute", "_gated_for_test"),
            ):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fail_spawn,
                    spawn_verifier=lambda *a, **k: (0, None, None, []),
                    raw_launcher=lambda *a, **k: None,
                    run_suite_check=lambda p, s: None,
                    process_backlog_close=lambda *a, **k: None,
                    driver_module=oc_runipd,
                )
            self.assertEqual(item.get("status"), "fail-gate")
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("disposition"), "fail-gate")
            self.assertIn("host_capability_unavailable", attempt)
            self.assertEqual(attempt.get("model"), "test-model/cap-refused")
            self.assertEqual(attempt.get("model_source"), "options")

    def test_interrupted_attempt_preserves_model_through_accounting(self) -> None:
        """V-04: Interrupted attempt created with model/model_source retains them after accounting."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-interrupt"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)

            log_path = run_dir / "logs/interrupted.log"
            log_path.write_text("session log before interrupt\n", encoding="utf-8")

            def mock_interrupt(*args: Any, **kwargs: Any) -> None:
                raise runner_stop.StopNowForce(requester="operator")

            item: dict[str, Any] = {
                "id6": "tst001",
                "setid": "test",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
            }
            state: dict[str, Any] = {
                "repo": str(repo_root),
                "run_id": "run-interrupt",
                "queue": [item],
                "options": {
                    "isolate_worktrees": False,
                    "self_finalize": False,
                    "model": "test-model/interrupted",
                },
            }

            with self.assertRaises(runner_stop.StopNowForce):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=mock_interrupt,
                    spawn_verifier=lambda *a, **k: (0, None, None, []),
                    raw_launcher=lambda *a, **k: None,
                    run_suite_check=lambda p, s: None,
                    process_backlog_close=lambda *a, **k: None,
                    driver_module=oc_runipd,
                )

            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            attempt = attempts[0]
            self.assertEqual(attempt.get("model"), "test-model/interrupted")
            self.assertEqual(attempt.get("model_source"), "options")
            self.assertIn("interrupted_at", attempt)
            self.assertEqual(
                attempt.get("interrupt_reason"), "deliberate-stop-now-force"
            )
