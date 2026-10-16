"""Behavioral tests for agent_workflows.cli._run_migrate_layout (IPD 1ue3kr).

Tests drive cli.main(["migrate-layout", ...]) in temporary git repos seeded with
a legacy .agents/ layout and assert on exit codes, filesystem state, configuration,
and transaction logs.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from agent_workflows import cli
from tests import support


class MigrateLayoutCliTests(unittest.TestCase):
    """Behavioral tests for the migrate-layout CLI entry point."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        support.init_repo(self.repo)

        self._prev_aw_home = os.environ.get("AW_HOME")
        self.aw_home = Path(self.tmp_dir) / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        os.environ["AW_HOME"] = str(self.aw_home)

        self._orig_cwd = os.getcwd()
        os.chdir(str(self.repo))

        (self.repo / ".agents" / "workflows").mkdir(parents=True)
        (self.repo / ".agents" / "workflows" / "index.md").write_text(
            "# w\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)
        (self.repo / ".agents" / "plans" / "pending" / "p.md").write_text(
            "# p\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "README.md").write_text(
            "# agents readme\n", encoding="utf-8"
        )

        c_env = support.clean_git_env()
        p1 = support.git(self.repo, "add", ".", env=c_env)
        if p1.returncode != 0:
            raise RuntimeError(f"git add failed: {p1.stderr}")
        p2 = support.git(self.repo, "commit", "-q", "-m", "seed", env=c_env)
        if p2.returncode != 0:
            raise RuntimeError(f"git commit failed: {p2.stderr}")

    def tearDown(self) -> None:
        os.chdir(self._orig_cwd)
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # Task group 1: Wizard and confirm gate (E-01)

    def test_interactive_wizard_accept_runs_migration_after_confirm(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())

    def test_wizard_action_explicit(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout", "wizard"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())

    def test_interactive_wizard_decline_makes_no_mutations(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("1\n1\nn\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".agents/plans/pending/p.md").is_file())
        self.assertTrue((self.repo / ".agents/README.md").is_file())
        self.assertEqual(
            (self.repo / ".agents/workflows/index.md").read_text(encoding="utf-8"),
            "# w\n",
        )
        self.assertEqual(
            (self.repo / ".agents/plans/pending/p.md").read_text(encoding="utf-8"),
            "# p\n",
        )
        self.assertEqual(
            (self.repo / ".agents/README.md").read_text(encoding="utf-8"),
            "# agents readme\n",
        )

    # Task group 2: Config file and flag precedence (E-02)

    def test_config_file_noninteractive(self) -> None:
        cfg_file = self.repo / "mig_config.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "target_backend": "companion",
                    "leftovers": "keep",
                    "confirm": True,
                }
            ),
            encoding="utf-8",
        )
        code = cli.main(["migrate-layout", "--config", str(cfg_file)])
        self.assertEqual(code, 0)

        pol_file = self.repo / ".aw/config/config.json"
        self.assertTrue(pol_file.is_file())
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "companion")

        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "keep"
        )
        self.assertTrue((self.repo / ".agents/README.md").is_file())

    def test_cli_flags_override_config_file(self) -> None:
        cfg_file = self.repo / "mig_config.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "target_backend": "companion",
                    "leftovers": "keep",
                    "confirm": True,
                }
            ),
            encoding="utf-8",
        )
        code = cli.main(
            [
                "migrate-layout",
                "--config",
                str(cfg_file),
                "--target-backend",
                "repository",
                "--leftovers",
                "remove",
            ]
        )
        self.assertEqual(code, 0)

        pol_file = self.repo / ".aw/config/config.json"
        self.assertTrue(pol_file.is_file())
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "repository")

        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "remove"
        )
        self.assertFalse((self.repo / ".agents/README.md").exists())

    def test_missing_and_invalid_config_files(self) -> None:
        code = cli.main(
            ["migrate-layout", "--config", str(self.repo / "nonexistent.json")]
        )
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())

        bad_cfg = self.repo / "bad.json"
        bad_cfg.write_text("{not valid json", encoding="utf-8")
        code2 = cli.main(["migrate-layout", "--config", str(bad_cfg)])
        self.assertEqual(code2, 1)
        self.assertFalse((self.repo / ".aw").exists())

    # Task group 3: Non-interactive gate and preview path (E-03)

    def test_underspecified_noninteractive_fails_closed(self) -> None:
        with mock.patch("sys.stdin.isatty", return_value=False):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())

    def test_yes_without_leftovers_remove_does_not_delete_leftovers(self) -> None:
        code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)

        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "defer"
        )
        self.assertTrue((self.repo / ".agents/README.md").is_file())

    def test_plan_preview_writes_output_and_creates_no_aw(self) -> None:
        out_path = self.repo / "o.json"
        code = cli.main(["migrate-layout", "plan", "--output", str(out_path)])
        self.assertEqual(code, 0)
        self.assertTrue(out_path.is_file())
        out_data = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIn("migration_map", out_data)
        self.assertFalse((self.repo / ".aw").exists())


if __name__ == "__main__":
    unittest.main()
