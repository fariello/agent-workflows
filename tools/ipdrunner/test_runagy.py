#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Add tool directory to sys.path before importing driver
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import runagy as driver  # noqa: E402


class AgyEventRenderTests(unittest.TestCase):
    def setUp(self):
        self.pal = driver.Palette(True)

    def test_render_init(self):
        line = json.dumps(
            {
                "event": "init",
                "conversation_id": "conv-12345678-abcd",
                "init": {"model": "gemini-3.7-flash-high"},
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Initialized Antigravity (gemini-3.7-flash-high)", rendered)
        self.assertIn("conv-123", rendered)

    def test_render_result_success(self):
        line = json.dumps(
            {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "conversation_id": "conv-12345678-abcd",
                    "response": "Done!",
                },
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Antigravity turn finished: SUCCESS", rendered)

    def test_render_result_failure(self):
        line = json.dumps(
            {
                "event": "result",
                "result": {
                    "status": "ERROR",
                    "error": "Timeout expired",
                    "conversation_id": "conv-12345678-abcd",
                },
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Antigravity turn failed: Timeout expired", rendered)

    def test_render_tool_step_active_and_done(self):
        active_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "step_index": 3,
                    "state": "ACTIVE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": "pytest tests/ -v"},
                    },
                },
            }
        )
        active_rendered = driver.render_agy_event(active_line, self.pal)
        self.assertIsNotNone(active_rendered)
        self.assertIn("run_command", active_rendered)
        self.assertIn("pytest tests/ -v", active_rendered)

        done_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "step_index": 3,
                    "state": "DONE",
                    "step_type": "tool",
                    "duration_seconds": 1.25,
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": "pytest tests/ -v"},
                    },
                },
            }
        )
        done_rendered = driver.render_agy_event(done_line, self.pal)
        self.assertIsNotNone(done_rendered)
        self.assertIn("1.25s", done_rendered)


class AgyParserAndDiscoveryTests(unittest.TestCase):
    def test_read_deps_and_set(self):
        text = textwrap.dedent(
            """
            - Date: 2026-08-24
            - Kind: child
            - Status: to-review
            - Set: "authset" (Authentication flow)
            - Order: 2
            - Dependencies: [dep001, dep002]
            - Id: a1b2c3
            """
        )
        self.assertEqual(driver._read_id(text), "a1b2c3")
        self.assertEqual(driver._read_set(text), "authset")
        self.assertEqual(driver._read_order(text), 2)
        self.assertEqual(driver._read_status(text), "to-review")
        self.assertEqual(driver._read_deps(text), ["dep001", "dep002"])

    def test_dependency_status_execution_vs_review(self):
        state = {
            "repo": "/nonexistent",
            "queue": [
                {
                    "id6": "dep001",
                    "status": "reviewed",
                    "action": "review",
                },
                {
                    "id6": "dep002",
                    "status": "approved",
                    "action": "execute",
                },
                {
                    "id6": "dep003",
                    "status": "executed",
                    "action": "execute",
                },
            ],
        }

        # Execution item depending on 'reviewed' plan -> blocked
        exec_item_1 = {
            "id6": "tgt001",
            "action": "execute",
            "dependencies": ["dep001"],
        }
        sat, missing = driver.dependency_status(exec_item_1, state)
        self.assertFalse(sat)
        self.assertEqual(missing, ["dep001"])

        # Execution item depending on 'executed' plan -> satisfied
        exec_item_3 = {
            "id6": "tgt003",
            "action": "execute",
            "dependencies": ["dep003"],
        }
        sat, missing = driver.dependency_status(exec_item_3, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])

        # Review item depending on 'reviewed' plan -> satisfied
        rev_item_1 = {
            "id6": "tgt004",
            "action": "review",
            "dependencies": ["dep001"],
        }
        sat, missing = driver.dependency_status(rev_item_1, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])


class AgyExecutionLifecycleTests(unittest.TestCase):
    def _create_mock_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test Agent"],
            cwd=repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "agent@example.com"],
            cwd=repo,
            check=True,
        )

        plans_pending = repo / ".aw" / "records" / "plans" / "pending"
        plans_pending.mkdir(parents=True)

        plan1 = plans_pending / "20260824-demo-01-a1b2c3-implement-first-feature.ipd.md"
        plan1.write_text(
            textwrap.dedent(
                """
            # IPD: First Feature

            - Date: 2026-08-24
            - Kind: child
            - Status: approved
            - Set: demo
            - Order: 1
            - Author: Antigravity
            - Id: a1b2c3

            ## Workflow history
            - 2026-08-24 approved (Human): ready

            ## Goal
            Goal 1
            """
            ),
            encoding="utf-8",
        )

        dummy = repo / "README.md"
        dummy.write_text("# Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
        return repo

    def test_runagy_two_turn_execution_with_clean_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)

            # Create a mock fake-agy script that outputs stream-json events
            fake_agy = root / "fake_agy.sh"
            fake_agy.write_text(
                textwrap.dedent(
                    """#!/bin/bash
                    # Parse args to see if this is turn 1 or turn 2 verification
                    PROMPT="$2"
                    if [[ "$PROMPT" == *"Independent Rigorous Verification"* ]]; then
                        echo '{"event":"init","conversation_id":"conv-verify-9999","init":{"model":"gemini-3.7-flash-high"}}'
                        echo '{"event":"step_update","step_update":{"step_index":1,"state":"DONE","step_type":"tool","tool_info":{"name":"run_command","parameters":{"CommandLine":"pytest"}}}}'
                        echo '{"event":"result","result":{"status":"SUCCESS","conversation_id":"conv-verify-9999","response":"Verification completed: VERIFIED"}}'
                    else
                        echo '{"event":"init","conversation_id":"conv-exec-1111","init":{"model":"gemini-3.7-flash-high"}}'
                        echo '{"event":"step_update","step_update":{"step_index":1,"state":"DONE","step_type":"tool","tool_info":{"name":"write_to_file","parameters":{"TargetFile":"test.py"}}}}'
                        echo '{"event":"result","result":{"status":"SUCCESS","conversation_id":"conv-exec-1111","response":"Implementation done"}}'
                    fi
                    exit 0
                    """
                ),
                encoding="utf-8",
            )
            fake_agy.chmod(0o755)

            # Start runagy
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            # Locate run directory
            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Initialized run:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            state_file = run_dir / "state.json"
            self.assertTrue(state_file.is_file())

            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(len(state["queue"]), 1)
            item = state["queue"][0]
            self.assertEqual(item["status"], "executed")
            self.assertEqual(item["verification_status"], "verified")
            self.assertEqual(len(item["attempts"]), 1)

            # Confirm both execution session log and verification session log exist
            exec_log = run_dir / "sessions" / "01-a1b2c3-attempt-1.jsonl"
            verify_log = run_dir / "sessions" / "01-a1b2c3-verify-attempt-1.jsonl"
            self.assertTrue(exec_log.is_file())
            self.assertTrue(verify_log.is_file())

            # Confirm clean session used for verification (different conv IDs)
            self.assertIn("conv-exec-1111", exec_log.read_text())
            self.assertIn("conv-verify-9999", verify_log.read_text())

    def test_runagy_no_verify_skips_turn2(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)

            fake_agy = root / "fake_agy.sh"
            fake_agy.write_text(
                textwrap.dedent(
                    """#!/bin/bash
                    echo '{"event":"init","conversation_id":"conv-exec-2222","init":{"model":"gemini-3.7-flash-high"}}'
                    echo '{"event":"result","result":{"status":"SUCCESS","conversation_id":"conv-exec-2222","response":"Done"}}'
                    exit 0
                    """
                ),
                encoding="utf-8",
            )
            fake_agy.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                    "--no-verify",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Initialized run:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            verify_log = run_dir / "sessions" / "01-a1b2c3-verify-attempt-1.jsonl"
            self.assertFalse(verify_log.exists())

    def test_runagy_status_and_report_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)

            fake_agy = root / "fake_agy.sh"
            fake_agy.write_text(
                textwrap.dedent(
                    """#!/bin/bash
                    echo '{"event":"init","conversation_id":"conv-exec-3333","init":{"model":"gemini-3.7-flash-high"}}'
                    echo '{"event":"result","result":{"status":"SUCCESS","conversation_id":"conv-exec-3333","response":"Done"}}'
                    exit 0
                    """
                ),
                encoding="utf-8",
            )
            fake_agy.chmod(0o755)

            # Start run
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                    "--no-verify",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Initialized run:")
            )

            # Test status command (text)
            status_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "status",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(status_res.returncode, 0)
            self.assertIn(run_id, status_res.stdout)
            self.assertIn("a1b2c3", status_res.stdout)

            # Test status command (json)
            status_json_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "status",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                    "--json",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(status_json_res.returncode, 0)
            status_data = json.loads(status_json_res.stdout)
            self.assertEqual(status_data["run_id"], run_id)
            self.assertEqual(status_data["queue"][0]["id6"], "a1b2c3")

            # Test report command
            report_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "report",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(report_res.returncode, 0)
            self.assertIn(
                "# Antigravity IPD Driver Execution Report", report_res.stdout
            )
            self.assertIn(run_id, report_res.stdout)

    def test_continuation_hint_rendering(self):
        state = {
            "repo": "/my/repo",
            "run_id": "run-test-12345",
            "set_sessions": {
                "setA": "conv-setA-1111",
                "setB": "conv-setB-2222",
            },
        }
        hint = driver.render_continuation_hint(state, Path("/tmp"))
        self.assertIn("conv-setA-1111", hint)
        self.assertIn("conv-setB-2222", hint)
        self.assertIn("runagy resume --repo /my/repo run-test-12345", hint)


if __name__ == "__main__":
    unittest.main()
