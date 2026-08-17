#!/usr/bin/env python3
"""Tests for tools/agy_run.py and tools/antigravity_execute_ipd.py."""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Ensure tools directory is in sys.path
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import agy_run  # noqa: E402
import antigravity_execute_ipd  # noqa: E402


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.local"], check=True
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test Runner"], check=True
    )
    return path


class AgyRunArgParseTests(unittest.TestCase):
    """Verify CLI argument parsing across all supported modes and flags."""

    def test_default_options(self):
        args = agy_run.parse_args(["7cvh9t"])
        self.assertEqual(args.target, "7cvh9t")
        self.assertEqual(args.model, "gemini-3.7-flash-high")
        self.assertEqual(args.timeout, "240m")
        self.assertFalse(args.new_session)
        self.assertTrue(args.continue_session)
        self.assertFalse(args.no_audit)
        self.assertFalse(args.audit_only)

    def test_explicit_ipd_mode(self):
        args = agy_run.parse_args(["--ipd", "20260816-test-01-abc123-test.md"])
        self.assertEqual(args.ipd_target, "20260816-test-01-abc123-test.md")

    def test_explicit_spec_mode(self):
        args = agy_run.parse_args(["--spec", ".agents/docs/specs/test.spec.md"])
        self.assertEqual(args.spec_target, ".agents/docs/specs/test.spec.md")

    def test_explicit_file_mode(self):
        args = agy_run.parse_args(["--file", ".agents/prompts/local/brief.md"])
        self.assertEqual(args.file_target, ".agents/prompts/local/brief.md")
        args_short = agy_run.parse_args(["-f", ".agents/prompts/local/brief.md"])
        self.assertEqual(args_short.file_target, ".agents/prompts/local/brief.md")

    def test_explicit_prompt_mode(self):
        args = agy_run.parse_args(["-p", "refactor test runner"])
        self.assertEqual(args.prompt_target, "refactor test runner")
        args_long = agy_run.parse_args(["--prompt", "refactor test runner"])
        self.assertEqual(args_long.prompt_target, "refactor test runner")

    def test_session_continuity_flags(self):
        # Specific session ID
        args_s = agy_run.parse_args(["-s", "conv-12345", "-p", "test"])
        self.assertEqual(args_s.session_id, "conv-12345")
        args_c = agy_run.parse_args(["-c", "conv-67890", "-p", "test"])
        self.assertEqual(args_c.session_id, "conv-67890")
        args_long = agy_run.parse_args(["--session-id", "conv-abcde", "-p", "test"])
        self.assertEqual(args_long.session_id, "conv-abcde")

        # New session isolation
        args_new = agy_run.parse_args(["--new-session", "7cvh9t"])
        self.assertTrue(args_new.new_session)
        args_n = agy_run.parse_args(["-n", "7cvh9t"])
        self.assertTrue(args_n.new_session)

    def test_runtime_and_model_options(self):
        args = agy_run.parse_args(
            [
                "--model",
                "gemini-1.5-pro",
                "--timeout",
                "60m",
                "--dangerously-skip-permissions",
                "-p",
                "test",
            ]
        )
        self.assertEqual(args.model, "gemini-1.5-pro")
        self.assertEqual(args.timeout, "60m")
        self.assertTrue(args.dangerously_skip_permissions)

    def test_validation_turn_controls(self):
        args_no_audit = agy_run.parse_args(["--no-audit", "-p", "test"])
        self.assertTrue(args_no_audit.no_audit)
        args_audit_only = agy_run.parse_args(
            ["--audit-only", "--session-id", "conv-1", "--ipd", "7cvh9t"]
        )
        self.assertTrue(args_audit_only.audit_only)


class AgyRunTargetResolutionTests(unittest.TestCase):
    """Verify target resolution and auto-detection across repository structures."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = init_repo(Path(self._tmp.name) / "repo")
        (self.root / ".agents" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".agents" / "plans" / "executed").mkdir(parents=True)
        (self.root / ".agents" / "docs" / "specs").mkdir(parents=True)
        (self.root / ".agents" / "prompts" / "local").mkdir(parents=True)

        # Plant fixtures
        self.ipd_file = (
            self.root
            / ".agents"
            / "plans"
            / "pending"
            / "20260816-test-01-ab12cd-test-plan.md"
        )
        self.ipd_file.write_text("# Test IPD\n", encoding="utf-8")

        self.spec_file = (
            self.root / ".agents" / "docs" / "specs" / "20260810-01-feature.spec.md"
        )
        self.spec_file.write_text("# Feature Spec\n", encoding="utf-8")

        self.prompt_file = self.root / ".agents" / "prompts" / "local" / "brief.md"
        self.prompt_file.write_text("Do something useful.\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_resolve_ipd_by_id6(self):
        resolved = agy_run.resolve_ipd(self.root, "ab12cd", ("pending",))
        self.assertEqual(resolved, self.ipd_file)

    def test_resolve_ipd_by_filename(self):
        resolved = agy_run.resolve_ipd(
            self.root, "20260816-test-01-ab12cd-test-plan.md", ("pending",)
        )
        self.assertEqual(resolved, self.ipd_file)

    def test_resolve_ipd_by_path(self):
        resolved = agy_run.resolve_ipd(
            self.root,
            ".agents/plans/pending/20260816-test-01-ab12cd-test-plan.md",
            ("pending",),
        )
        self.assertEqual(resolved, self.ipd_file)

    def test_resolve_spec_by_path_and_name(self):
        resolved = agy_run.resolve_spec(
            self.root, ".agents/docs/specs/20260810-01-feature.spec.md"
        )
        self.assertEqual(resolved, self.spec_file)
        resolved_name = agy_run.resolve_spec(self.root, "20260810-01-feature.spec.md")
        self.assertEqual(resolved_name, self.spec_file)

    def test_resolve_prompt_file(self):
        resolved = agy_run.resolve_prompt_file(
            self.root, ".agents/prompts/local/brief.md"
        )
        self.assertEqual(resolved, self.prompt_file)

    def test_auto_detect_ipd_by_id6(self):
        args = agy_run.parse_args(["ab12cd"])
        mode, target, extra = agy_run.resolve_mode_and_target(self.root, args)
        self.assertEqual(mode, "ipd")
        self.assertEqual(
            target, ".agents/plans/pending/20260816-test-01-ab12cd-test-plan.md"
        )

    def test_auto_detect_spec_file(self):
        args = agy_run.parse_args([str(self.spec_file)])
        mode, target, extra = agy_run.resolve_mode_and_target(self.root, args)
        self.assertEqual(mode, "spec")
        self.assertEqual(target, ".agents/docs/specs/20260810-01-feature.spec.md")

    def test_auto_detect_prompt_file(self):
        args = agy_run.parse_args([str(self.prompt_file)])
        mode, target, extra = agy_run.resolve_mode_and_target(self.root, args)
        self.assertEqual(mode, "file")
        self.assertEqual(target, ".agents/prompts/local/brief.md")

    def test_auto_detect_raw_prompt_string(self):
        args = agy_run.parse_args(["implement feature X in engine.py"])
        mode, target, extra = agy_run.resolve_mode_and_target(self.root, args)
        self.assertEqual(mode, "prompt")
        self.assertEqual(target, "implement feature X in engine.py")


class AgyRunPromptBuilderTests(unittest.TestCase):
    """Verify prompt synthesis and preamble loading across all modes."""

    def test_build_turn1_prompt_ipd(self):
        prompt = agy_run.build_turn1_prompt("ipd", ".agents/plans/pending/test.md")
        self.assertIn("read and execute `.agents/plans/pending/test.md`", prompt)
        self.assertIn("Implement real behavior", prompt)

    def test_build_turn1_prompt_spec(self):
        prompt = agy_run.build_turn1_prompt("spec", ".agents/docs/specs/test.spec.md")
        self.assertIn("Author a conformant Implementation Plan Document (IPD)", prompt)
        self.assertIn(".agents/docs/specs/test.spec.md", prompt)

    def test_build_turn1_prompt_file(self):
        prompt = agy_run.build_turn1_prompt("file", ".agents/prompts/local/brief.md")
        self.assertIn("read and execute `.agents/prompts/local/brief.md`", prompt)

    def test_build_turn1_prompt_raw(self):
        prompt = agy_run.build_turn1_prompt("prompt", "refactor test runner")
        self.assertIn("refactor test runner", prompt)

    def test_build_turn2_prompt_ipd(self):
        prompt = agy_run.build_turn2_prompt("ipd", ".agents/plans/executed/test.md")
        self.assertIn(".agents/plans/executed/test.md", prompt)
        self.assertIn("evidence table", prompt.lower())

    def test_build_turn2_prompt_spec(self):
        prompt = agy_run.build_turn2_prompt(
            "spec", ".agents/plans/pending/test.md", ".agents/docs/specs/test.spec.md"
        )
        self.assertIn(".agents/plans/pending/test.md", prompt)
        self.assertIn(".agents/docs/specs/test.spec.md", prompt)


class AgyRunExecutionEngineTests(unittest.TestCase):
    """Verify two-turn headless execution, progress filtering, and error handling."""

    def test_compact_string_truncation(self):
        short = agy_run._compact("simple string")
        self.assertEqual(short, "simple string")
        long_str = "x" * 200
        compacted = agy_run._compact(long_str, limit=50)
        self.assertTrue(compacted.endswith("..."))
        self.assertEqual(len(compacted), 50)

    def test_is_test_command_detection(self):
        self.assertTrue(agy_run._is_test_command("python3 -m unittest tests.test_cli"))
        self.assertTrue(agy_run._is_test_command("pytest tests/"))
        self.assertTrue(agy_run._is_test_command("cargo test"))
        self.assertFalse(agy_run._is_test_command("git status"))
        self.assertFalse(agy_run._is_test_command("ls -la"))

    def test_progress_messages_parsing(self):
        # init event
        init_msgs = agy_run._progress_messages({"event": "init"}, "execution")
        self.assertEqual(init_msgs, [("init", "[execution] Antigravity initialized")])

        # tool event with test command
        step_event = {
            "event": "step_update",
            "step_update": {
                "step_index": 1,
                "state": "ACTIVE",
                "tool_info": {
                    "name": "run_command",
                    "parameters": {"command": "python3 -m unittest tests.test_cli"},
                },
            },
        }
        step_msgs = agy_run._progress_messages(step_event, "execution")
        self.assertEqual(len(step_msgs), 1)
        self.assertIn("tests started", step_msgs[0][1])

        # result event
        res_msgs = agy_run._progress_messages(
            {"event": "result", "result": {"status": "SUCCESS"}}, "audit"
        )
        self.assertEqual(res_msgs, [("result:SUCCESS", "[audit] completed: SUCCESS")])

    def test_two_turn_execution_flow_mock(self):
        # Create temporary repo
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = init_repo(Path(tmp_dir) / "repo")
            (root / ".agents" / "plans" / "pending").mkdir(parents=True)
            plan_file = (
                root
                / ".agents"
                / "plans"
                / "pending"
                / "20260816-test-01-ab12cd-test.md"
            )
            plan_file.write_text("# Plan\n", encoding="utf-8")

            # Mock run_agy to return AgyResult
            mock_turn1 = agy_run.AgyResult(
                conversation_id="conv-42", response="Turn 1 done", status="SUCCESS"
            )
            mock_turn2 = agy_run.AgyResult(
                conversation_id="conv-42",
                response="Turn 2 audit PASS",
                status="SUCCESS",
            )

            with mock.patch.object(
                agy_run, "run_agy", side_effect=[mock_turn1, mock_turn2]
            ) as mock_run:
                with mock.patch.object(agy_run, "resolve_agy", return_value="/bin/agy"):
                    with mock.patch.object(
                        agy_run, "repository_root", return_value=root
                    ):
                        exit_code = agy_run.run(["ab12cd"])
                        self.assertEqual(exit_code, 0)
                        self.assertEqual(mock_run.call_count, 2)
                        # Turn 1 called with phase="execution"
                        self.assertEqual(
                            mock_run.call_args_list[0].kwargs["phase"], "execution"
                        )
                        # Turn 2 called with phase="audit" and session_id="conv-42"
                        self.assertEqual(
                            mock_run.call_args_list[1].kwargs["phase"], "audit"
                        )
                        self.assertEqual(
                            mock_run.call_args_list[1].kwargs["session_id"], "conv-42"
                        )

    def test_turn1_failure_halts_immediately(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = init_repo(Path(tmp_dir) / "repo")
            with mock.patch.object(
                agy_run, "run_agy", side_effect=agy_run.ScriptError("Turn 1 failed")
            ):
                with mock.patch.object(agy_run, "resolve_agy", return_value="/bin/agy"):
                    with mock.patch.object(
                        agy_run, "repository_root", return_value=root
                    ):
                        with self.assertRaises(agy_run.ScriptError):
                            agy_run.run(["-p", "bad prompt"])


class AntigravityExecuteIpdCompatibilityTests(unittest.TestCase):
    """Verify backwards compatibility of tools/antigravity_execute_ipd.py."""

    def test_re_exports_and_interface_parity(self):
        self.assertTrue(hasattr(antigravity_execute_ipd, "ScriptError"))
        self.assertTrue(hasattr(antigravity_execute_ipd, "AgyResult"))
        self.assertTrue(hasattr(antigravity_execute_ipd, "resolve_ipd"))
        self.assertTrue(hasattr(antigravity_execute_ipd, "run_agy"))
        self.assertTrue(hasattr(antigravity_execute_ipd, "main"))
        self.assertTrue(hasattr(antigravity_execute_ipd, "run"))

    def test_delegation_to_agy_run(self):
        with mock.patch.object(agy_run, "run", return_value=0) as mock_run:
            rc = antigravity_execute_ipd.run(["7cvh9t"])
            self.assertEqual(rc, 0)
            mock_run.assert_called_once_with(["7cvh9t"])


class AgySessionsTests(unittest.TestCase):
    """Verify session discovery, active detection, and formatting in agy_sessions.py."""

    def test_format_duration(self):
        import agy_sessions

        dt1 = datetime.datetime(2026, 8, 16, 10, 0, 0)
        dt2 = datetime.datetime(2026, 8, 16, 10, 15, 30)
        dt3 = datetime.datetime(2026, 8, 16, 12, 15, 30)

        self.assertEqual(agy_sessions._format_duration(dt1, dt2), "15m 30s")
        self.assertEqual(agy_sessions._format_duration(dt1, dt3), "2h 15m 30s")
        self.assertEqual(agy_sessions._format_duration(None, dt2), "-")

    def test_get_sessions_with_fixtures(self):
        import agy_sessions

        with tempfile.TemporaryDirectory() as tmp_app_dir:
            app_dir = Path(tmp_app_dir)
            presence_dir = app_dir / "presence"
            presence_dir.mkdir(parents=True)
            brain_dir = app_dir / "brain"
            brain_dir.mkdir(parents=True)

            # Create history.jsonl
            hist_file = app_dir / "history.jsonl"
            hist_entry = {
                "workspace": "/fake/workspace",
                "timestamp": 1786930000000,
                "conversationId": "fake-conv-12345",
                "display": "Run tests and verify",
            }
            hist_file.write_text(json.dumps(hist_entry) + "\n", encoding="utf-8")

            # Create transcript in brain dir
            t_log_dir = brain_dir / "fake-conv-12345" / ".system_generated" / "logs"
            t_log_dir.mkdir(parents=True)
            t_file = t_log_dir / "transcript.jsonl"
            t_file.write_text(
                json.dumps({"created_at": "2026-08-16T10:00:00Z", "content": "step 1"})
                + "\n"
                + json.dumps(
                    {"created_at": "2026-08-16T10:20:00Z", "content": "step 2"}
                )
                + "\n",
                encoding="utf-8",
            )

            # Retrieve sessions
            sessions = agy_sessions.get_sessions(
                workspace_filter="/fake/workspace", app_data_dir=app_dir
            )
            self.assertEqual(len(sessions), 1)
            s = sessions[0]
            self.assertEqual(s.conversation_id, "fake-conv-12345")
            self.assertEqual(s.duration_str, "20m 00s")
            self.assertEqual(s.step_count, 2)
            self.assertFalse(s.is_active)


if __name__ == "__main__":
    unittest.main()
