"""Tests for install state records placement, redaction, and upgrade migration (pfub72).

Validates that:
(a) Fresh install and second install place install snapshot and history exclusively under
    .aw/state/durable/ with the running version, no machine-identifying home paths, and no
    aw_home or companion_dir keys.
(b) Upgrade migration relocates/merges pre-cutover root state files into durable/ and removes
    the root files.
(c) The install history cutover reader reads durable history first and falls back to root.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import agent_workflows
from agent_workflows import config


class TestInstallStateRecords(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.test_dir.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.home = self.base / "distinct_home_pfub72_uniq"
        self.home.mkdir()

        # Initialize git repo with attribution
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(self.repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.repo),
            check=True,
        )

        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["XDG_CONFIG_HOME"] = str(self.home / ".config")
        self.env["AW_NO_REEXEC"] = "1"
        repo_root = Path(__file__).resolve().parent.parent
        self.env["PYTHONPATH"] = f"{repo_root}:{self.env.get('PYTHONPATH', '')}"

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def _run_aw(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        return subprocess.run(
            cmd,
            cwd=str(self.repo),
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_fresh_install_and_reinstall_state_records(self) -> None:
        """Case (a): Fresh install and reinstall place records under durable/ with running version and no leaks."""
        # 1. First install
        self._run_aw(
            "install", ".", "--preset", "private-target", "-y", "--no-interactive"
        )

        state_dir = self.repo / ".aw" / "state"
        durable_install = state_dir / "durable" / "install.json"
        durable_history = state_dir / "durable" / "history" / "installs.jsonl"

        # Assert nothing at state/ root
        root_files = [p for p in state_dir.iterdir() if p.is_file()]
        self.assertEqual(root_files, [], f"Unexpected root state files: {root_files}")

        self.assertTrue(durable_install.is_file())
        self.assertTrue(durable_history.is_file())

        snap1 = json.loads(durable_install.read_text(encoding="utf-8"))
        self.assertEqual(snap1.get("installed_version"), agent_workflows.__version__)

        home_str = str(self.home)
        install_text1 = durable_install.read_text(encoding="utf-8")
        history_text1 = durable_history.read_text(encoding="utf-8")

        self.assertNotIn(home_str, install_text1)
        self.assertNotIn("aw_home", install_text1)
        self.assertNotIn("companion_dir", install_text1)

        self.assertNotIn(home_str, history_text1)
        self.assertNotIn("aw_home", history_text1)
        self.assertNotIn("companion_dir", history_text1)

        lines1 = [line for line in history_text1.splitlines() if line.strip()]
        self.assertEqual(len(lines1), 1)

        # 2. Second install (reinstall)
        self._run_aw("install", ".", "-y", "--no-interactive")

        root_files2 = [p for p in state_dir.iterdir() if p.is_file()]
        self.assertEqual(
            root_files2, [], f"Unexpected root state files on reinstall: {root_files2}"
        )

        snap2 = json.loads(durable_install.read_text(encoding="utf-8"))
        self.assertEqual(snap2.get("installed_version"), agent_workflows.__version__)

        install_text2 = durable_install.read_text(encoding="utf-8")
        history_text2 = durable_history.read_text(encoding="utf-8")

        self.assertNotIn(home_str, install_text2)
        self.assertNotIn("aw_home", install_text2)
        self.assertNotIn("companion_dir", install_text2)

        self.assertNotIn(home_str, history_text2)
        self.assertNotIn("aw_home", history_text2)
        self.assertNotIn("companion_dir", history_text2)

        lines2 = [line for line in history_text2.splitlines() if line.strip()]
        self.assertEqual(len(lines2), 2)

    def test_upgrade_migration_four_file_layout(self) -> None:
        """Case (b): Upgrade migrates root state files into durable/ and removes root files."""
        state_dir = self.repo / ".aw" / "state"
        root_hist_dir = state_dir / "history"
        durable_hist_dir = state_dir / "durable" / "history"
        root_hist_dir.mkdir(parents=True, exist_ok=True)
        durable_hist_dir.mkdir(parents=True, exist_ok=True)

        root_install = state_dir / "install.json"
        durable_install = state_dir / "durable" / "install.json"
        root_hist = root_hist_dir / "installs.jsonl"
        durable_hist = durable_hist_dir / "installs.jsonl"

        root_install.write_text('{"legacy": "root_snap"}\n', encoding="utf-8")
        durable_install.write_text('{"existing": "durable_snap"}\n', encoding="utf-8")

        line_prior = '{"timestamp": "2026-07-31T00:00:00Z", "event": "durable_prior"}'
        line_shared = '{"timestamp": "2026-08-02T00:00:00Z", "event": "shared"}'
        line_root1 = '{"timestamp": "2026-08-01T00:00:00Z", "event": "root_one"}'
        line_root3 = '{"timestamp": "2026-08-03T00:00:00Z", "event": "root_three"}'

        durable_hist.write_text(f"{line_prior}\n{line_shared}\n", encoding="utf-8")
        root_hist.write_text(
            f"{line_root1}\n{line_shared}\n{line_root3}\n", encoding="utf-8"
        )

        # Reinstall to trigger upgrade migration
        proc = self._run_aw(
            "install", ".", "--preset", "private-target", "-y", "--no-interactive"
        )
        self.assertIn("Legacy layout migrated", proc.stdout)

        # Assert root files are gone
        self.assertFalse(root_install.exists())
        self.assertFalse(root_hist.exists())
        self.assertFalse(root_hist_dir.exists())

        # Assert durable history has distinct lines preserved once
        hist_lines = [
            line.strip()
            for line in durable_hist.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertIn(line_prior, hist_lines)
        self.assertIn(line_shared, hist_lines)
        self.assertIn(line_root1, hist_lines)
        self.assertIn(line_root3, hist_lines)

        # Count occurrences of shared line
        self.assertEqual(hist_lines.count(line_shared), 1)
        self.assertEqual(hist_lines.count(line_root1), 1)
        self.assertEqual(hist_lines.count(line_root3), 1)

    def test_cutover_reader_durable_and_root(self) -> None:
        """Case (c): Cutover reader returns same date from durable-only and root-only fixtures, preferring durable."""
        durable_repo = self.base / "durable_repo"
        root_repo = self.base / "root_repo"
        both_repo = self.base / "both_repo"

        for r in (durable_repo, root_repo, both_repo):
            r.mkdir(parents=True, exist_ok=True)

        durable_hist = (
            durable_repo / ".aw" / "state" / "durable" / "history" / "installs.jsonl"
        )
        durable_hist.parent.mkdir(parents=True, exist_ok=True)
        durable_hist.write_text(
            json.dumps({"timestamp": "2026-08-29T10:00:00Z"}) + "\n", encoding="utf-8"
        )

        root_hist = root_repo / ".aw" / "state" / "history" / "installs.jsonl"
        root_hist.parent.mkdir(parents=True, exist_ok=True)
        root_hist.write_text(
            json.dumps({"timestamp": "2026-08-29T10:00:00Z"}) + "\n", encoding="utf-8"
        )

        both_durable = (
            both_repo / ".aw" / "state" / "durable" / "history" / "installs.jsonl"
        )
        both_durable.parent.mkdir(parents=True, exist_ok=True)
        both_durable.write_text(
            json.dumps({"timestamp": "2026-08-30T10:00:00Z"}) + "\n", encoding="utf-8"
        )

        both_root = both_repo / ".aw" / "state" / "history" / "installs.jsonl"
        both_root.parent.mkdir(parents=True, exist_ok=True)
        both_root.write_text(
            json.dumps({"timestamp": "2026-08-29T10:00:00Z"}) + "\n", encoding="utf-8"
        )

        # spec_id6 is registered at 2026-08-28
        res_durable = config._find_install_history_cutover(durable_repo, "spec_id6")
        res_root = config._find_install_history_cutover(root_repo, "spec_id6")
        self.assertIsNotNone(res_durable)
        self.assertEqual(res_durable, res_root)

        # In both_repo, durable date (2026-08-30 -> 20260830) must win over root date (2026-08-29 -> 20260829)
        res_both = config._find_install_history_cutover(both_repo, "spec_id6")
        self.assertEqual(res_both, "20260830")


if __name__ == "__main__":
    unittest.main()
