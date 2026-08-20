"""Unit tests for install-history + the setup-repo marker (setupmarker Order 01: the operational-
action ledger was deleted; install history is retained, the setup reminder is now a marker file)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_history import record_install_history
from agent_workflows.project_registry import register_or_update_project


class TestActionsAndInstallHistory(unittest.TestCase):
    """Test install history append + redaction (the ledger lifecycle tests were removed with the ledger)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(self.target_repo, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", self.target_repo], check=True, capture_output=True
        )
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home

        # Register project fixture
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        # Restore the prior AW_HOME (the tests package sets a sandbox value in
        # tests/__init__.py); popping it unconditionally would clobber that
        # sandbox for later tests and leak into the real ~/.aw.
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

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

    def test_cli_todo_agent_output_clean(self):
        """`aw todo --agent` (an alias of `attention`, awcmdsurf Order 04) returns clean, ANSI-free
        output. setupmarker Order 01: the action ledger is gone; todo/attention just render the
        cross-tree board with no ANSI escapes."""
        os.makedirs(os.path.join(self.target_repo, ".aw", "records"), exist_ok=True)
        cmd = ["python3", "-m", "agent_workflows", "todo", "--agent"]
        source_root = str(Path(__file__).resolve().parent.parent)
        python_path = os.environ.get("PYTHONPATH")
        env = dict(os.environ)
        env["PYTHONPATH"] = (
            source_root if not python_path else source_root + os.pathsep + python_path
        )
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(self.target_repo), env=env
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        self.assertNotIn("\033[", res.stdout)

    def test_setup_marker_lifecycle(self):
        """setupmarker Order 01: write/remove the self-explaining marker + setup_needed derives from it."""
        from agent_workflows import engine, attention

        repo = Path(self.target_repo)
        m = engine.write_setup_marker(repo)
        self.assertTrue(m.is_file())
        self.assertIn("setup not yet run", m.read_text(encoding="utf-8"))
        self.assertIn(
            "setup-repo-needed.md",
            (repo / ".aw" / ".gitignore").read_text(encoding="utf-8"),
        )
        self.assertTrue(attention.setup_needed(repo))
        self.assertTrue(engine.remove_setup_marker(repo))
        self.assertFalse(m.is_file())
        self.assertFalse(attention.setup_needed(repo))

    def test_attention_scan_does_not_create_aw(self):
        """setupmarker Order 01 regression: a read-only attention scan must NOT stamp .aw/ (the
        write-on-read bug the deleted ledger caused)."""
        from agent_workflows import attention

        fresh = Path(self.tmp_dir) / "freshrepo"
        fresh.mkdir()
        attention.scan(fresh)
        self.assertFalse(
            (fresh / ".aw").exists(),
            "attention.scan must not create .aw/ (write-on-read)",
        )


if __name__ == "__main__":
    unittest.main()
