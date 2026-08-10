"""Unit tests for AW operational actions, lifecycle transitions, and install history (IPD 20260809-awlayout-06)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.actions import (
    ActionError,
    ActionManager,
    InvalidActionIdError,
    record_install_history,
    validate_action_id,
)
from agent_workflows.project_registry import register_or_update_project


class TestActionsAndInstallHistory(unittest.TestCase):
    """Test action lifecycle, ID format validation, single-dir uniqueness, and install history append."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(self.target_repo, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", self.target_repo], check=True, capture_output=True
        )
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        os.environ["AW_HOME"] = self.aw_home

        # Register project fixture
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_action_id_validation_format(self):
        """Action ID must match pattern [a-z][a-z0-9]*(?:-[a-z0-9]+)* without aw- prefix (E-01)."""
        validate_action_id("setup-repo")
        validate_action_id("configure-durability")
        validate_action_id("check123")

        with self.assertRaises(InvalidActionIdError):
            validate_action_id("AW-SETUP")  # Uppercase forbidden

        with self.assertRaises(InvalidActionIdError):
            validate_action_id("setup_repo")  # Underscore forbidden

        with self.assertRaises(InvalidActionIdError):
            validate_action_id("aw-setup")  # aw- prefix forbidden (spec 12.2)

        with self.assertRaises(InvalidActionIdError):
            validate_action_id("aw")  # bare 'aw' forbidden

        with self.assertRaises(InvalidActionIdError):
            validate_action_id("-setup")  # Leading hyphen forbidden

    def test_action_creation_and_lifecycle_transitions(self):
        """Test action creation, single-dir uniqueness, and lifecycle transitions (E-01 & V-01)."""
        mgr = ActionManager(target_repo=self.target_repo)
        doc = mgr.create_action(
            action_id="setup-repo",
            generation=1,
            title="Setup repository",
            description="Run setup-repo workflow.",
        )

        self.assertEqual(doc.status, "open")

        # Duplicate creation in any status MUST be refused
        with self.assertRaises(ActionError):
            mgr.create_action("setup-repo", 1, "Duplicate", "Desc")

        # Transition open -> completed
        doc_completed = mgr.transition_action("setup-repo", "completed")
        self.assertEqual(doc_completed.status, "completed")

        # Verify file moved to completed/ and source in open/ disappeared
        open_file = mgr.actions_dir / "open" / "setup-repo-v1.md"
        completed_file = mgr.actions_dir / "completed" / "setup-repo-v1.md"
        self.assertFalse(open_file.exists())
        self.assertTrue(completed_file.is_file())

        # Transition completed -> open (reopen)
        doc_reopened = mgr.transition_action("setup-repo", "open")
        self.assertEqual(doc_reopened.status, "open")
        self.assertTrue(open_file.is_file())
        self.assertFalse(completed_file.exists())

    def test_twelve_sequential_updates_do_not_recreate_action(self):
        """Twelve sequential updates must not recreate a completed action (E-03 & V-05)."""
        mgr = ActionManager(target_repo=self.target_repo)
        mgr.create_action("setup-repo", 1, "Setup", "Desc")
        mgr.transition_action("setup-repo", "completed")

        # Simulate 12 sequential update checks
        for _ in range(12):
            # Attempting to recreate generation 1 must be refused
            with self.assertRaises(ActionError):
                mgr.create_action("setup-repo", 1, "Setup", "Desc")

        # Verify action remains completed
        status, _ = mgr.find_action_file("setup-repo", 1)
        self.assertEqual(status, "completed")

    def test_install_history_atomic_append(self):
        """Install history appends JSONL lines with O_APPEND and fsync (E-04 & V-04)."""
        record_install_history(
            self.target_repo, "install", {"version": "2026.8.9"}, aw_home=self.aw_home
        )
        record_install_history(
            self.target_repo, "update", {"version": "2026.8.9"}, aw_home=self.aw_home
        )

        # History lives under the resolver's STATE root (external for the home backend),
        # not inside the target repo.
        from agent_workflows.project_context import resolve_project_context
        from agent_workflows.project_schema import LogicalRoot

        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
        history_file = state_root / "history" / "installs.jsonl"
        self.assertTrue(history_file.is_file())

        lines = history_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)

        data1 = json.loads(lines[0])
        data2 = json.loads(lines[1])
        self.assertEqual(data1["event_type"], "install")
        self.assertEqual(data2["event_type"], "update")

    def test_install_history_redacts_machine_identifying_details(self):
        """Install-history details route through the canonical leak sanitizer (L6-04): a real home
        path is redacted while non-sensitive fields survive. The leaky value is built at runtime from
        the current home directory so no maintainer path is hardcoded in this tracked test."""
        leaky = os.path.join(os.path.expanduser("~"), "some", "secret", "path")
        record_install_history(
            self.target_repo,
            "install",
            {"note": f"ran from {leaky}", "version": "9.9.9"},
            aw_home=self.aw_home,
        )
        from agent_workflows.project_context import resolve_project_context
        from agent_workflows.project_schema import LogicalRoot

        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])
        line = (state_root / "history" / "installs.jsonl").read_text(encoding="utf-8")
        self.assertNotIn(leaky, line)
        self.assertIn("9.9.9", line)

    def test_cli_todo_agent_json_output(self):
        """Test `aw todo --agent` returns clean JSON array without ANSI bytes (E-02 & V-02)."""
        mgr = ActionManager(target_repo=self.target_repo)
        mgr.create_action("setup-repo", 1, "Setup", "Desc")

        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "todo",
            "--agent",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(self.target_repo)
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        self.assertNotIn("\033[", res.stdout)
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "setup-repo")


if __name__ == "__main__":
    unittest.main()
