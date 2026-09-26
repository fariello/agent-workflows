from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    render_stream,
    runner_shared,
    runner_stop,
)
from agent_workflows.run_viewer import extract_step_usage
from tests import support
from tests.test_agy_runipd_cli import (
    _init_repo_with_conforming_plan as _init_agy_repo_with_conforming_plan,
)
from tests.test_oc_runipd import (
    _init_repo_with_conforming_plan as _init_oc_repo_with_conforming_plan,
)

LOG_ENTRY = {
    "type": "step_finish",
    "sessionID": "ses_probe1",
    "part": {
        "cost": 2.17,
        "tokens": {
            "input": 100,
            "output": 20,
            "cache": {"read": 5, "write": 0},
        },
    },
}


class InterruptAttemptMetadataUnitTests(unittest.TestCase):
    """Unit tests for record_interrupted_attempt_accounting (E-04)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_helper_empty_set_sessions(self):
        """Case 1: work_dir=None, empty set_sessions: attempt and state populated; session_turn_counts unchanged."""
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "attempt.log"
            log_path.write_text(json.dumps(LOG_ENTRY) + "\n", encoding="utf-8")
            attempt = {"log": str(log_path)}
            item = {"id6": "demo01", "setid": "demo"}
            state = {"set_sessions": {}, "session_turn_counts": {}}
            runner_shared.record_interrupted_attempt_accounting(
                state, item, attempt, work_dir=None
            )
            self.assertEqual(attempt.get("session_id"), "ses_probe1")
            self.assertEqual(attempt.get("cost"), 2.17)
            self.assertIsInstance(attempt.get("tokens"), dict)
            self.assertEqual(attempt["tokens"]["total"], 125)
            self.assertEqual(state["set_sessions"].get("demo"), "ses_probe1")
            self.assertEqual(state.get("session_id"), "ses_probe1")
            self.assertEqual(state.get("session_turn_counts", {}), {})

    def test_helper_session_reconciliation_conflict(self):
        """Case 2: set_sessions == {'demo': 'ses_other'}: conflict recorded, set_sessions unchanged, cost written."""
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "attempt.log"
            log_path.write_text(json.dumps(LOG_ENTRY) + "\n", encoding="utf-8")
            attempt = {"log": str(log_path)}
            item = {"id6": "demo01", "setid": "demo"}
            state = {"set_sessions": {"demo": "ses_other"}, "session_turn_counts": {}}
            runner_shared.record_interrupted_attempt_accounting(
                state, item, attempt, work_dir=None
            )
            self.assertEqual(
                attempt.get("session_reconciliation_error"),
                "persisted=ses_other observed=ses_probe1",
            )
            self.assertEqual(state["set_sessions"]["demo"], "ses_other")
            self.assertEqual(attempt.get("cost"), 2.17)
            self.assertEqual(attempt.get("tokens", {}).get("total"), 125)

    def test_helper_lane_work_dir_does_not_mutate_set_sessions(self):
        """Case 3: work_dir='/some/lane': attempt fields written, set_sessions untouched."""
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "attempt.log"
            log_path.write_text(json.dumps(LOG_ENTRY) + "\n", encoding="utf-8")
            attempt = {"log": str(log_path)}
            item = {"id6": "demo01", "setid": "demo"}
            state = {"set_sessions": {}, "session_turn_counts": {}}
            runner_shared.record_interrupted_attempt_accounting(
                state, item, attempt, work_dir="/some/lane"
            )
            self.assertEqual(attempt.get("session_id"), "ses_probe1")
            self.assertEqual(attempt.get("cost"), 2.17)
            self.assertEqual(attempt.get("tokens", {}).get("total"), 125)
            self.assertEqual(state["set_sessions"], {})

    def test_helper_missing_log_file_noop(self):
        """Case 4: attempt['log'] pointing at a missing file: no keys added, no exception."""
        with tempfile.TemporaryDirectory() as td:
            missing_log = Path(td) / "nonexistent.log"
            attempt = {"log": str(missing_log)}
            item = {"id6": "demo01", "setid": "demo"}
            state = {"set_sessions": {}}
            runner_shared.record_interrupted_attempt_accounting(
                state, item, attempt, work_dir=None
            )
            self.assertEqual(attempt, {"log": str(missing_log)})
            self.assertEqual(state["set_sessions"], {})

    def test_helper_no_log_key_noop(self):
        """Case 5: attempt with no 'log' key at all: no keys added, no exception."""
        attempt = {}
        item = {"id6": "demo01", "setid": "demo"}
        state = {"set_sessions": {}}
        runner_shared.record_interrupted_attempt_accounting(
            state, item, attempt, work_dir=None
        )
        self.assertEqual(attempt, {})
        self.assertEqual(state["set_sessions"], {})


class InterruptAttemptNoDoubleCountTests(unittest.TestCase):
    """No double-count test for precedence claim (E-05)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_extract_step_usage_no_double_count(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            log_path = run_dir / "sessions" / "01-wir001-attempt-1.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps(LOG_ENTRY) + "\n", encoding="utf-8")

            item_before = {
                "attempts": [
                    {
                        "number": 1,
                        "log": str(log_path),
                    }
                ]
            }
            usage_before = extract_step_usage(item_before, run_dir)

            item_after = {
                "attempts": [
                    {
                        "number": 1,
                        "log": str(log_path),
                        "session_id": "ses_probe1",
                        "cost": 2.17,
                        "tokens": {
                            "total": 125,
                            "input": 100,
                            "output": 20,
                            "cache": 5,
                        },
                    }
                ]
            }
            usage_after = extract_step_usage(item_after, run_dir)

            self.assertEqual(usage_before, usage_after)


class HostBehavioralInterruptMetadataTests(unittest.TestCase):
    """Behavioral tests through each host's real execute_item (E-06)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _state_and_item(
        self, repo: Path, plan: Path, driver_name: str
    ) -> tuple[dict, dict]:
        id6 = "wir001" if driver_name == "oc" else "agy001"
        item = {
            "position": 1,
            "id6": id6,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        options = {
            "model": "opus",
            "self_finalize": False,
            "isolate_worktree": False,
            "no_audit": True,
        }
        if driver_name == "oc":
            options["opencode"] = "/bin/true"
        else:
            options["no_verify"] = True

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": options,
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        return run_dir

    def _assert_host_interrupt(self, host: str, raise_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            if host == "oc":
                driver = oc_runipd
                labels = runner_shared.OC_HOST_LABELS
                plan = _init_oc_repo_with_conforming_plan(repo, "wir001")
                spawn_target = "run_opencode"
            else:
                driver = agy_runipd
                labels = runner_shared.AGY_HOST_LABELS
                plan = _init_agy_repo_with_conforming_plan(repo, "agy001")
                spawn_target = "run_agy_turn"

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, host)

            if raise_kind == "stall_timeout":
                exc = runner_shared.StallTimeout("stall")
            elif raise_kind == "stop_now_force":
                exc = runner_stop.StopNowForce()
            elif raise_kind == "stop_at_checkpoint":
                exc = runner_stop.StopAtCheckpoint(
                    runner_stop.CheckpointObserver(
                        detector=lambda s: False, last_checkpoint_label="E-01"
                    )
                )
            elif raise_kind == "keyboard_interrupt":
                exc = KeyboardInterrupt("clean-up-and-terminate")
            else:
                raise ValueError(f"Unknown raise_kind: {raise_kind}")

            def fake_spawn(*args, **kwargs):
                log_path = runner_shared.attempt_log_path(run_dir, item, 1)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(json.dumps(LOG_ENTRY) + "\n", encoding="utf-8")
                if isinstance(exc, KeyboardInterrupt):
                    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
                raise exc

            with (
                mock.patch.object(driver, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(driver, spawn_target, fake_spawn),
            ):
                if isinstance(
                    exc,
                    (
                        KeyboardInterrupt,
                        runner_stop.StopNowForce,
                        runner_stop.StopAtCheckpoint,
                    ),
                ):
                    with pytest.raises(type(exc)):
                        driver.execute_item(run_dir, state, item, recovery=False)
                else:
                    driver.execute_item(run_dir, state, item, recovery=False)

            # Assert in-memory item attempts[-1]
            last_att = item["attempts"][-1]
            self.assertEqual(last_att.get("session_id"), "ses_probe1")
            self.assertEqual(last_att.get("cost"), 2.17)
            self.assertIsInstance(last_att.get("tokens"), dict)
            self.assertEqual(last_att["tokens"].get("total"), 125)

            # Assert persisted state.json agrees
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            saved_att = saved_state["queue"][0]["attempts"][-1]
            self.assertEqual(saved_att.get("session_id"), "ses_probe1")
            self.assertEqual(saved_att.get("cost"), 2.17)
            self.assertIsInstance(saved_att.get("tokens"), dict)
            self.assertEqual(saved_att["tokens"].get("total"), 125)

            # Assert state["set_sessions"]["demo"] == "ses_probe1"
            self.assertEqual(state.get("set_sessions", {}).get("demo"), "ses_probe1")
            self.assertEqual(
                saved_state.get("set_sessions", {}).get("demo"), "ses_probe1"
            )

            # Assert render_run_summary_table output contains 2.17
            summary_table = render_stream.render_run_summary_table(state, run_dir)
            self.assertIn("2.17", summary_table)

            # Assert continuation hint contains ses_probe1
            hint = runner_shared.render_continuation_hint(state, run_dir, labels=labels)
            self.assertIn("ses_probe1", hint)

    def test_oc_stall_timeout(self):
        self._assert_host_interrupt("oc", "stall_timeout")

    def test_oc_stop_now_force(self):
        self._assert_host_interrupt("oc", "stop_now_force")

    def test_oc_stop_at_checkpoint(self):
        self._assert_host_interrupt("oc", "stop_at_checkpoint")

    def test_oc_keyboard_interrupt(self):
        self._assert_host_interrupt("oc", "keyboard_interrupt")

    def test_agy_stall_timeout(self):
        self._assert_host_interrupt("agy", "stall_timeout")

    def test_agy_stop_now_force(self):
        self._assert_host_interrupt("agy", "stop_now_force")

    def test_agy_stop_at_checkpoint(self):
        self._assert_host_interrupt("agy", "stop_at_checkpoint")

    def test_agy_keyboard_interrupt(self):
        self._assert_host_interrupt("agy", "keyboard_interrupt")
