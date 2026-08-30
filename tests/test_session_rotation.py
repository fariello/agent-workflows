#!/usr/bin/env python3
"""Tests for session rotation after max items per session."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd


class SessionRotationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir(parents=True)
        # Initialize a real git repository in temp repo
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(self.repo),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(self.repo),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.repo),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=str(self.repo),
            check=True,
            capture_output=True,
        )

        self.run_dir = self.root / "run"
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "sessions").mkdir(parents=True)
        (self.run_dir / "outcomes").mkdir(parents=True)
        (self.run_dir / "prompts").mkdir(parents=True)
        self.plan_path = self.repo / "plan.ipd.md"
        self.plan_path.write_text("- Id: test01\n- Set: demo\n", encoding="utf-8")
        self.prompt_path = self.run_dir / "prompt.md"
        self.prompt_path.write_text("Review this plan\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_state(self, max_items: int = 4) -> dict:
        return {
            "schema_version": 1,
            "run_id": "run-test-sessrot",
            "repo": str(self.repo),
            "set_sessions": {},
            "session_turn_counts": {},
            "options": {
                "opencode": "/bin/false",
                "max_items_per_session": max_items,
                "auto": True,
            },
            "queue": [],
        }

    def _get_oc_argv(self, state: dict, turn: int = 1) -> list[str]:
        captured = {}

        def fake_popen(argv, **kwargs):
            captured["argv"] = list(argv)
            raise RuntimeError("stop-before-launch")

        import subprocess as _sp

        real_popen = _sp.Popen
        _sp.Popen = fake_popen
        item = {"id6": "test01", "setid": "demo", "position": 1, "action": "review"}
        try:
            oc_runipd.run_opencode(
                state, self.run_dir, item, self.plan_path, self.prompt_path, turn
            )
        except Exception:
            pass
        finally:
            _sp.Popen = real_popen
        return captured.get("argv", [])

    def test_oc_runipd_default_rotation_after_four_reviews(self):
        """oc_runipd rotates to a fresh session on the 5th review turn."""
        state = self._make_state(max_items=4)

        # Turn 1: Starts fresh session mock_session_1
        argv1 = self._get_oc_argv(state, 1)
        self.assertNotIn("--session", argv1)
        # Simulate OpenCode outputting session mock_session_1 and post-turn update
        state["set_sessions"]["demo"] = "mock_session_1"
        state["session_id"] = "mock_session_1"
        state.setdefault("session_turn_counts", {})["mock_session_1"] = 1

        # Turns 2, 3, 4: Should reuse mock_session_1
        for turn in range(2, 5):
            argv = self._get_oc_argv(state, turn)
            self.assertIn("--session", argv)
            self.assertEqual(argv[argv.index("--session") + 1], "mock_session_1")
            state["session_turn_counts"]["mock_session_1"] += 1

        self.assertEqual(state["session_turn_counts"]["mock_session_1"], 4)

        # Turn 5: Reached limit (4 >= 4) -> ROTATES to fresh session (no --session)
        argv5 = self._get_oc_argv(state, 5)
        self.assertNotIn(
            "--session",
            argv5,
            "Turn 5 must rotate to a fresh session when max_items_per_session is 4",
        )

    def test_oc_runipd_planned_rotation_in_execute_item_does_not_raise(self):
        """execute_item accepts a new session ID when planned rotation occurred."""
        state = self._make_state(max_items=2)
        state["set_sessions"]["demo"] = "mock_session_old"
        state["session_turn_counts"]["mock_session_old"] = 2
        item = {
            "id6": "test01",
            "setid": "demo",
            "position": 1,
            "action": "review",
            "configured_file": "plan.ipd.md",
            "attempts": [],
        }

        def mock_run_opencode(*args, **kwargs):
            return 0, "mock_session_new", self.run_dir / "turn.log", ["opencode", "run"]

        with patch(
            "agent_workflows.oc_runipd.run_opencode", side_effect=mock_run_opencode
        ), patch(
            "agent_workflows.oc_runipd.reconcile_disposition",
            return_value=("reviewed", {"status": "reviewed"}),
        ):
            oc_runipd.execute_item(self.run_dir, state, item, False)

        self.assertEqual(state["set_sessions"]["demo"], "mock_session_new")
        self.assertEqual(state["session_turn_counts"]["mock_session_new"], 1)

    def test_oc_runipd_unplanned_session_change_raises_driver_error(self):
        """execute_item raises DriverError if session changed unexpectedly before limit."""
        state = self._make_state(max_items=4)
        state["set_sessions"]["demo"] = "mock_session_old"
        state["session_turn_counts"]["mock_session_old"] = 1  # Only 1 turn (limit is 4)
        item = {
            "id6": "test01",
            "setid": "demo",
            "position": 1,
            "action": "review",
            "configured_file": "plan.ipd.md",
            "attempts": [],
        }

        def mock_run_opencode(*args, **kwargs):
            return (
                0,
                "mock_session_unexp",
                self.run_dir / "turn.log",
                ["opencode", "run"],
            )

        with patch(
            "agent_workflows.oc_runipd.run_opencode", side_effect=mock_run_opencode
        ):
            with self.assertRaises(oc_runipd.DriverError) as ctx:
                oc_runipd.execute_item(self.run_dir, state, item, False)
            self.assertIn("changed session unexpectedly", str(ctx.exception))

    def test_oc_runipd_disabled_rotation_with_zero(self):
        """When max_items_per_session is 0, session rotation is disabled."""
        state = self._make_state(max_items=0)
        state["set_sessions"]["demo"] = "mock_session_persist"
        state["session_turn_counts"]["mock_session_persist"] = 10
        argv = self._get_oc_argv(state, 11)
        self.assertIn("--session", argv)
        self.assertEqual(argv[argv.index("--session") + 1], "mock_session_persist")

    def test_agy_runipd_rotation_at_limit(self):
        """agy_runipd resets session_id and use_continue when threshold is reached."""
        state = self._make_state(max_items=3)
        state["set_sessions"]["demo"] = "agy_mock_session_1"
        state["session_turn_counts"]["agy_mock_session_1"] = 3
        item = {
            "id6": "test01",
            "setid": "demo",
            "position": 1,
            "action": "review",
            "configured_file": "plan.ipd.md",
            "attempts": [],
        }

        captured_calls = []

        def mock_run_agy_turn(
            st, rd, itm, p_path, att_no, session_id=None, use_continue=False, **kwargs
        ):
            captured_calls.append(
                {"session_id": session_id, "use_continue": use_continue}
            )
            return 0, "agy_ses_2", rd / "turn.log", ["agy"]

        with patch(
            "agent_workflows.agy_runipd.run_agy_turn", side_effect=mock_run_agy_turn
        ), patch(
            "agent_workflows.agy_runipd.reconcile_disposition",
            return_value=("reviewed", {"status": "reviewed"}),
        ):
            agy_runipd.execute_item(self.run_dir, state, item, False)

        self.assertEqual(len(captured_calls), 1)
        self.assertIsNone(captured_calls[0]["session_id"])
        self.assertFalse(captured_calls[0]["use_continue"])
        self.assertEqual(state["set_sessions"]["demo"], "agy_ses_2")
        self.assertEqual(state["session_turn_counts"]["agy_ses_2"], 1)


if __name__ == "__main__":
    unittest.main()
