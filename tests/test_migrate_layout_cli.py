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

    # Task group 4: usable result, summary, self-commit, [Y/n] defaults (migusable)

    def _git_out(self, *args: str) -> str:
        return support.git(self.repo, *args, env=support.clean_git_env()).stdout

    def test_enter_at_confirm_accepts_and_commits(self) -> None:
        # Empty answers take every default: backend, leftovers, confirm [Y/n], commit [Y/n].
        head_before = self._git_out("rev-parse", "HEAD").strip()
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("\n\n\n\n")), mock.patch(
            "sys.stdout", out
        ):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("[Y/n]", out.getvalue())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertNotEqual(self._git_out("rev-parse", "HEAD").strip(), head_before)
        # Nothing the migration moved is left staged or modified.
        status = self._git_out("status", "--porcelain")
        self.assertNotIn(".aw/records", status)
        self.assertNotIn(".agents/plans", status)
        self.assertNotIn(".aw/state", status)

    def test_summary_reports_what_moved(self) -> None:
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("Migration Summary", text)
        self.assertIn(".agents/plans -> .aw/records/plans", text)
        self.assertRegex(text, r"Moved \d+ file\(s\)")

    def test_yes_commits_and_leaves_clean_tree(self) -> None:
        code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)
        self.assertIn(
            "migrate legacy layout", self._git_out("log", "-1", "--format=%s")
        )
        tracked = self._git_out("ls-files")
        self.assertIn(".aw/records/plans/pending/p.md", tracked)
        self.assertIn(".aw/.gitignore", tracked)
        self.assertNotIn(".agents/plans/pending/p.md", tracked)
        # Per-machine state is never committed and is ignored, so it does not dirty the tree.
        self.assertNotIn(".aw/state/", tracked)
        self.assertNotIn(".aw/state", self._git_out("status", "--porcelain"))

    def test_no_commit_leaves_moves_staged_and_head_unchanged(self) -> None:
        head_before = self._git_out("rev-parse", "HEAD").strip()
        code = cli.main(["migrate-layout", "--yes", "--no-commit"])
        self.assertEqual(code, 0)
        self.assertEqual(self._git_out("rev-parse", "HEAD").strip(), head_before)
        self.assertIn(
            ".aw/records/plans/pending/p.md",
            self._git_out("diff", "--cached", "--name-only"),
        )

    def test_migrated_plan_without_id_gets_one(self) -> None:
        plan = self.repo / ".agents/plans/pending/20260926-2339-01-legacy.md"
        plan.write_text(
            "# IPD: legacy\n\n- Date: 2026-09-26\n- Status: approved\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        support.git(self.repo, "add", ".", env=support.clean_git_env())
        support.git(
            self.repo, "commit", "-q", "-m", "legacy", env=support.clean_git_env()
        )
        code = cli.main(["migrate-layout", "--yes", "--rename-to-grammar"])
        self.assertEqual(code, 0)
        moved = self.repo / ".aw/records/plans/pending/20260926-2339-01-legacy.ipd.md"
        text = moved.read_text(encoding="utf-8")
        ids = [ln for ln in text.splitlines() if ln.startswith("- Id: ")]
        self.assertEqual(len(ids), 1, text)
        # The Id lands inside the metadata block (before the first H2), right after Status.
        self.assertLess(text.index("- Id: "), text.index("## Goal"))
        self.assertGreater(text.index("- Id: "), text.index("- Status: approved"))

    def test_finalize_refusal_for_id_less_plan_names_the_fix(self) -> None:
        plan = self.repo / "nolid.ipd.md"
        plan.write_text("# IPD: x\n\n- Status: approved\n\n## Goal\n", encoding="utf-8")
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = cli.main(
                [
                    "ipd",
                    "finalize",
                    str(plan),
                    "--actor",
                    "t",
                    "-m",
                    "x",
                    "--dir",
                    str(self.repo),
                ]
            )
        self.assertNotEqual(code, 0)
        self.assertIn("aw ipd sync", out.getvalue())

    def test_migration_stamps_legacy_cutovers_and_keeps_policy(self) -> None:
        code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)
        pj = json.loads(
            (self.repo / ".aw/config/project.json").read_text(encoding="utf-8")
        )
        self.assertIn("ipd_begin_receipt", pj["cutovers"])
        self.assertIn("ipd_plan_format", pj["cutovers"])
        # project.json shadows config.json once it exists, so it must carry the same backend.
        self.assertEqual(pj.get("records_backend"), "repository")
        self.assertIn(".aw/config/project.json", self._git_out("ls-files"))

    def test_rollback_removes_created_project_json(self) -> None:
        self.assertEqual(cli.main(["migrate-layout", "--yes", "--no-commit"]), 0)
        self.assertTrue((self.repo / ".aw/config/project.json").is_file())
        self.assertEqual(cli.main(["migrate-layout", "rollback"]), 0)
        self.assertFalse((self.repo / ".aw/config/project.json").exists())

    def test_rollback_restores_original_plan_bytes(self) -> None:
        plan = self.repo / ".agents/plans/pending/20260926-2339-01-legacy.md"
        original = "# IPD: legacy\n\n- Status: approved\n\n## Goal\n"
        plan.write_text(original, encoding="utf-8")
        support.git(self.repo, "add", ".", env=support.clean_git_env())
        support.git(
            self.repo, "commit", "-q", "-m", "legacy", env=support.clean_git_env()
        )
        self.assertEqual(cli.main(["migrate-layout", "--yes", "--no-commit"]), 0)
        self.assertEqual(cli.main(["migrate-layout", "rollback"]), 0)
        self.assertEqual(plan.read_text(encoding="utf-8"), original)
        self.assertFalse((self.repo / ".aw/.gitignore").exists())

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
