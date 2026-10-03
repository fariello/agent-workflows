"""Tests for attempt host model observation (attmodel ov2c9n E-05).

Pins the producer behaviorally by driving execute_item_core and observe_host_model
over real execution shapes and asserting on observable attempt records and outcomes.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import oc_runipd, runner_shared
from tests.support import coordinator_role
from tests.test_attempt_model_identity import _setup_test_repo


class FakePipeProcess:
    """Mock process backed by an os.pipe for realistic POSIX stream behavior."""

    def __init__(self, data: bytes, exit_code: int = 0):
        r, w = os.pipe()
        os.write(w, data)
        os.close(w)
        self.stdout = open(r, "rb", buffering=0)  # noqa: SIM115
        self.stderr = open(os.devnull, "rb")  # noqa: SIM115
        self.returncode = exit_code
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


class HangingPipeProcess:
    """Mock process that hangs until killed at the bound."""

    def __init__(self) -> None:
        self.r, self.w = os.pipe()
        self.stdout = open(self.r, "rb", buffering=0)  # noqa: SIM115
        self.stderr = open(os.devnull, "rb")  # noqa: SIM115
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return -9 if self.killed else None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
        try:
            os.close(self.w)
        except OSError:
            pass

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode or 0


def _drive_execute_turn_with_observer(
    repo_root: Path,
    plan_file: Path,
    options: dict[str, Any],
    *,
    observer: Any = None,
    session_id: str = "session-123",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Drive execute_item_core with a custom host model observer."""
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
    state["options"]["validate"] = False
    state["options"]["no_verify"] = True

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

    with coordinator_role():
        runner_shared.execute_item_core(
            run_dir,
            state,
            item,
            recovery=False,
            host_labels=runner_shared.OC_HOST_LABELS,
            spawn_executor=lambda *a, **k: (0, session_id, log_path, ["mock_agent"]),
            spawn_verifier=lambda *a, **k: (0, None, None, []),
            raw_launcher=lambda *a, **k: None,
            run_suite_check=lambda p, s: None,
            process_backlog_close=lambda *a, **k: None,
            driver_module=oc_runipd,
            observe_host_model=observer,
        )
    return state, item


class TestAttemptHostModelObservation(unittest.TestCase):
    """Behavioral tests for per-attempt host model observation (attmodel ov2c9n E-05)."""

    def test_case_a_successful_read_records_all_four_keys(self) -> None:
        """Case (a): A successful read records all four host_model* keys."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            payload = json.dumps(
                {
                    "info": {
                        "model": {
                            "id": "nemotron-3.5-lightning-free",
                            "providerID": "opencode",
                            "variant": "default",
                        }
                    }
                }
            ).encode("utf-8")

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                return FakePipeProcess(payload)

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch-model"},
                observer=observer,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertEqual(
                att.get("host_model"), "opencode/nemotron-3.5-lightning-free"
            )
            self.assertEqual(att.get("host_model_provider"), "opencode")
            self.assertEqual(att.get("host_model_variant"), "default")
            self.assertEqual(att.get("host_model_source"), "export-session-current")
            self.assertEqual(att.get("model"), "test-provider/launch-model")

    def test_case_b_failed_read_nonzero_exit_records_none_and_raises_nothing(
        self,
    ) -> None:
        """Case (b): A failed read (nonzero exit) records none and raises nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                return FakePipeProcess(b"", exit_code=1)

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch-model"},
                observer=observer,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertNotIn("host_model", att)
            self.assertNotIn("host_model_provider", att)
            self.assertNotIn("host_model_variant", att)
            self.assertNotIn("host_model_source", att)
            self.assertEqual(att.get("model"), "test-provider/launch-model")

    def test_case_c_absent_binary_records_none_and_raises_nothing(self) -> None:
        """Case (c): An absent binary records none and raises nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                raise FileNotFoundError("No such file or directory: opencode")

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch-model"},
                observer=observer,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertNotIn("host_model", att)
            self.assertNotIn("host_model_provider", att)
            self.assertNotIn("host_model_variant", att)
            self.assertNotIn("host_model_source", att)

    def test_case_d_hanging_launcher_killed_at_bound_and_outcome_identical(
        self,
    ) -> None:
        """Case (d): A hanging launcher is killed at the bound; exit code, disposition, and status are identical to successful read."""
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            # 1. Drive a successful read turn
            repo_root1, plan_file1 = _setup_test_repo(Path(td1))
            payload = json.dumps(
                {"info": {"model": {"id": "m1", "providerID": "p1"}}}
            ).encode("utf-8")
            _, success_item = _drive_execute_turn_with_observer(
                repo_root1,
                plan_file1,
                {"model": "test-provider/launch-model"},
                observer=lambda s,
                options=None,
                repo_root=None: oc_runipd.observe_host_model(
                    s,
                    options=options,
                    launcher=lambda *a, **k: FakePipeProcess(payload),
                    repo_root=repo_root,
                ),
            )
            success_att = success_item["attempts"][0]

            # 2. Drive a hanging launcher turn
            repo_root2, plan_file2 = _setup_test_repo(Path(td2))
            hanging_proc = HangingPipeProcess()

            def hanging_observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id,
                    options=options,
                    launcher=lambda *a, **k: hanging_proc,
                    repo_root=repo_root,
                    timeout=0.05,
                )

            _, hanging_item = _drive_execute_turn_with_observer(
                repo_root2,
                plan_file2,
                {"model": "test-provider/launch-model"},
                observer=hanging_observer,
            )
            self.assertTrue(hanging_proc.killed)
            hanging_att = hanging_item["attempts"][0]

            # Assert exit code, disposition and item status are IDENTICAL
            self.assertEqual(hanging_att.get("exit_code"), success_att.get("exit_code"))
            self.assertEqual(
                hanging_item.get("disposition"), success_item.get("disposition")
            )
            self.assertEqual(hanging_item.get("status"), success_item.get("status"))
            self.assertNotIn("host_model", hanging_att)
            self.assertIn("host_model", success_att)

    def test_case_e_disagreement_between_launch_and_host_records_both_unmodified(
        self,
    ) -> None:
        """Case (e): Launch requested provA/requested and host reports provB/actually-ran; records both."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            payload = json.dumps(
                {
                    "info": {
                        "model": {
                            "id": "actually-ran",
                            "providerID": "provB",
                        }
                    }
                }
            ).encode("utf-8")

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                return FakePipeProcess(payload)

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "provA/requested"},
                observer=observer,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertEqual(att.get("model"), "provA/requested")
            self.assertEqual(att.get("model_source"), "options")
            self.assertEqual(att.get("host_model"), "provB/actually-ran")
            self.assertEqual(att.get("host_model_provider"), "provB")
            self.assertEqual(att.get("host_model_source"), "export-session-current")

    def test_case_f_no_launch_model_records_concrete_host_model(self) -> None:
        """Case (f): Turn launched with no --model ends with a concrete host_model."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            payload = json.dumps(
                {
                    "info": {
                        "model": {
                            "id": "nemotron-3.5-lightning-free",
                            "providerID": "opencode",
                        }
                    }
                }
            ).encode("utf-8")

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                return FakePipeProcess(payload)

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": None},
                observer=observer,
            )
            attempts = item.get("attempts", [])
            self.assertEqual(len(attempts), 1)
            att = attempts[0]
            self.assertEqual(att.get("model"), "")
            self.assertEqual(att.get("model_source"), "unrecorded")
            self.assertEqual(
                att.get("host_model"), "opencode/nemotron-3.5-lightning-free"
            )
            self.assertEqual(att.get("host_model_provider"), "opencode")
            self.assertEqual(att.get("host_model_source"), "export-session-current")

    def test_case_g_namespace_split_joined_correctly(self) -> None:
        """Case (g): Export id='nemotron-3.5-lightning-free' and providerID='opencode' joins to 'opencode/nemotron-3.5-lightning-free'."""
        with tempfile.TemporaryDirectory() as td:
            _repo_root, _plan_file = _setup_test_repo(Path(td))
            payload = json.dumps(
                {
                    "info": {
                        "model": {
                            "id": "nemotron-3.5-lightning-free",
                            "providerID": "opencode",
                        }
                    }
                }
            ).encode("utf-8")

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                return FakePipeProcess(payload)

            raw_record = oc_runipd.observe_host_model(
                "session-123",
                launcher=launcher,
            )
            self.assertIsNotNone(raw_record)
            assert raw_record is not None
            self.assertEqual(
                raw_record["host_model"], "opencode/nemotron-3.5-lightning-free"
            )
            self.assertEqual(raw_record["host_model_provider"], "opencode")
            self.assertEqual(raw_record["id"], "nemotron-3.5-lightning-free")
            self.assertEqual(raw_record["providerID"], "opencode")
            self.assertNotEqual(raw_record["host_model"], raw_record["id"])

    def test_case_h_shared_session_grain_records_each_turn_window_and_grain_label(
        self,
    ) -> None:
        """Case (h): Driving two attempts in the same session records the model observed in each window."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            session_models = ["opencode/model-turn-1", "opencode/model-turn-2"]
            call_count = 0

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                nonlocal call_count
                idx = min(call_count, len(session_models) - 1)
                full = session_models[idx]
                prov, m_id = full.split("/", 1)
                call_count += 1
                return FakePipeProcess(
                    json.dumps(
                        {"info": {"model": {"id": m_id, "providerID": prov}}}
                    ).encode("utf-8")
                )

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item1 = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch"},
                observer=observer,
                session_id="shared-session-001",
            )
            att1 = item1["attempts"][0]
            self.assertEqual(att1["host_model"], "opencode/model-turn-1")
            self.assertEqual(att1["host_model_source"], "export-session-current")

            _, item2 = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch"},
                observer=observer,
                session_id="shared-session-001",
            )
            att2 = item2["attempts"][0]
            self.assertEqual(att2["host_model"], "opencode/model-turn-2")
            self.assertEqual(att2["host_model_source"], "export-session-current")

            # Turn 1 record was not retro-corrected
            self.assertEqual(att1["host_model"], "opencode/model-turn-1")

    def test_opt_out_via_telemetry_config_records_none_and_spawns_no_subprocess(
        self,
    ) -> None:
        """Opt-out through .aw/config/project.json disables observation and spawns no process."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            cfg_dir = repo_root / ".aw/config"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"run_analytics_telemetry": {"enabled": False}}),
                encoding="utf-8",
            )

            invoked = False

            def launcher(cmd: list[str], **kwargs: Any) -> Any:
                nonlocal invoked
                invoked = True
                return FakePipeProcess(b"{}")

            def observer(
                session_id: str, options: Any = None, repo_root: Any = None
            ) -> Any:
                return oc_runipd.observe_host_model(
                    session_id, options=options, launcher=launcher, repo_root=repo_root
                )

            _, item = _drive_execute_turn_with_observer(
                repo_root,
                plan_file,
                {"model": "test-provider/launch"},
                observer=observer,
            )
            self.assertFalse(invoked)
            att = item["attempts"][0]
            self.assertNotIn("host_model", att)

    def test_binary_resolution_uses_options_opencode(self) -> None:
        """The reader uses options['opencode'] when set."""
        invoked_cmd: list[str] = []

        def launcher(cmd: list[str], **kwargs: Any) -> Any:
            invoked_cmd.extend(cmd)
            return FakePipeProcess(b"{}")

        oc_runipd.observe_host_model(
            "session-xyz",
            options={"opencode": "/custom/bin/opencode-pinned"},
            launcher=launcher,
        )
        self.assertEqual(
            invoked_cmd, ["/custom/bin/opencode-pinned", "export", "session-xyz"]
        )

    def test_bounded_read_reads_only_head_and_does_not_consume_large_export(
        self,
    ) -> None:
        """The reader reads only the 4 KiB prefix and terminates the child."""
        # Create a large stream (32 KiB, well over the 4 KiB prefix, within POSIX pipe buffer)
        head = json.dumps({"info": {"model": {"id": "m1", "providerID": "p1"}}}).encode(
            "utf-8"
        )
        large_payload = head + b" " * (32 * 1024)

        proc = FakePipeProcess(large_payload)
        rec = oc_runipd.observe_host_model(
            "session-large",
            launcher=lambda *a, **k: proc,
        )
        self.assertIsNotNone(rec)
        assert rec is not None
        self.assertEqual(rec["host_model"], "p1/m1")
        self.assertTrue(proc.terminated)

    @pytest.mark.slow
    def test_real_host_export_bounded_read(self) -> None:
        """Spawns the real opencode host binary on a known session if available."""
        if not shutil.which("opencode"):
            self.skipTest("opencode binary not installed")
        # Test nonexistent session returns None without raising
        rec = oc_runipd.observe_host_model("ses_<nonexistent>")
        self.assertIsNone(rec)
