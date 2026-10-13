"""Tests for clean-target project config and install state under AW_HOME (p425hv).

Validates that:
(a) clean-target install leaves no <target>/.aw/config and no <target>/.aw/state, and
    git status --porcelain --ignored -- .aw/config .aw/state is empty;
(b) project.json, local.json, install.json, history/installs.jsonl exist under
    AW_HOME/projects/<id>/ where <id> equals resolve_project_context(...).project_id,
    is non-empty, and equals the id in the dry-run's printed paths; nothing exists at
    AW_HOME/projects/state;
(c) a second clean-target install exits 0, keeps the stored preset, and appends a
    second history line in the same home file;
(d) config.resolve_cutover_date(repo, "spec_id6") returns the date stamped in the home project.json;
(e) a private-target install still writes <target>/.aw/config/project.json (staged) and
    local.json (ignored) and nothing under AW_HOME/projects/*/config;
(f) a target pre-seeded with the OLD polluted layout (target local.json with project_id: ""
    and a target project.json) resolves a non-empty project id and keeps reading the target config;
(g) cases (a) and (b) repeated for --preset local-only;
(h) after a clean-target install, aw doctor reports the stored preset;
(i) after a clean-target install, aw uninstall . -y removes the home config and state files
    and a following install exits 0 as a first install;
(j) a public-target-private-companion install is unchanged (its config_project stays under
    the target, its delivery_mode is tracked).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import config
from agent_workflows.project_context import project_config_dir, resolve_project_context


class TestCleanTargetConfigHome(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.test_dir.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.home = self.base / "fake_home"
        self.home.mkdir()
        self.aw_home = self.home / ".aw"
        self.aw_home.mkdir()

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(self.repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(self.repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.repo),
            check=True,
        )
        (self.repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit"], cwd=str(self.repo), check=True
        )

        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["AW_HOME"] = str(self.aw_home)
        self.env["XDG_CONFIG_HOME"] = str(self.home / ".config")
        self.env["AW_NO_REEXEC"] = "1"
        repo_root = Path(__file__).resolve().parent.parent
        self.env["PYTHONPATH"] = f"{repo_root}:{self.env.get('PYTHONPATH', '')}"

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def _run_aw(
        self, *args: str, check: bool = True, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        return subprocess.run(
            cmd,
            cwd=str(cwd or self.repo),
            env=self.env,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_case_a_clean_target_no_target_config_or_state(self) -> None:
        """Case (a): clean-target install leaves no <target>/.aw/config and no <target>/.aw/state."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        # Assert no .aw/config and no .aw/state in the target
        self.assertFalse((self.repo / ".aw" / "config").exists())
        self.assertFalse((self.repo / ".aw" / "state").exists())

        # Check git status for .aw/config and .aw/state
        res = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--ignored",
                "--",
                ".aw/config",
                ".aw/state",
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")

    def test_case_b_home_project_id_and_files(self) -> None:
        """Case (b): project.json, local.json, install.json, history/installs.jsonl exist under AW_HOME/projects/<id>/."""
        dry_res = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
            "--dry-run",
        )
        match = re.search(r"projects/([^/\s]+)/config/project\.json", dry_res.stdout)
        self.assertIsNotNone(
            match, f"Failed to extract project id from dry-run: {dry_res.stdout}"
        )
        dry_pid = match.group(1)
        self.assertTrue(bool(dry_pid.strip()))

        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(ctx.project_id, dry_pid)
        self.assertTrue(bool(ctx.project_id.strip()))

        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())
        self.assertTrue((proj_dir / "config" / "local.json").is_file())
        self.assertTrue((proj_dir / "state" / "durable" / "install.json").is_file())
        self.assertTrue(
            (proj_dir / "state" / "durable" / "history" / "installs.jsonl").is_file()
        )

        # Nothing exists at AW_HOME/projects/state
        self.assertFalse((self.aw_home / "projects" / "state").exists())

        # local.json carries the non-empty project_id
        local_data = json.loads(
            (proj_dir / "config" / "local.json").read_text(encoding="utf-8")
        )
        self.assertEqual(local_data.get("project_id"), ctx.project_id)

    def test_case_c_second_install_keeps_preset_appends_history(self) -> None:
        """Case (c): second clean-target install exits 0, keeps stored preset, and appends a second history line."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(ctx.preset, "completely-clean-target")

        proj_dir = self.aw_home / "projects" / ctx.project_id
        hist_file = proj_dir / "state" / "durable" / "history" / "installs.jsonl"
        lines = [
            line.strip()
            for line in hist_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 2)

    def test_case_d_cutover_date_resolved_from_home_config(self) -> None:
        """Case (d): config.resolve_cutover_date(repo, 'spec_id6') returns the date stamped in the home project.json."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_json = (
            self.aw_home / "projects" / ctx.project_id / "config" / "project.json"
        )
        pdata = json.loads(proj_json.read_text(encoding="utf-8"))
        pdata.setdefault("cutovers", {})["spec_id6"] = "2026-10-12"
        proj_json.write_text(json.dumps(pdata, indent=2), encoding="utf-8")

        # Set AW_HOME in os.environ for in-process resolution
        old_aw_home = os.environ.get("AW_HOME")
        try:
            os.environ["AW_HOME"] = str(self.aw_home)
            c_date = config.resolve_cutover_date(self.repo, "spec_id6")
            self.assertEqual(c_date, "20261012")
        finally:
            if old_aw_home is not None:
                os.environ["AW_HOME"] = old_aw_home
            else:
                os.environ.pop("AW_HOME", None)

    def test_case_e_private_target_writes_target_config(self) -> None:
        """Case (e): private-target install still writes <target>/.aw/config/project.json and local.json."""
        self._run_aw(
            "install", ".", "--preset", "private-target", "-y", "--no-interactive"
        )

        self.assertTrue((self.repo / ".aw" / "config" / "project.json").is_file())
        self.assertTrue((self.repo / ".aw" / "config" / "local.json").is_file())

        # No home config directories created
        projects_dir = self.aw_home / "projects"
        if projects_dir.exists():
            home_configs = list(projects_dir.glob("*/config"))
            self.assertEqual(home_configs, [])

    def test_case_f_legacy_polluted_target_preserved(self) -> None:
        """Case (f): target pre-seeded with old polluted layout resolves non-empty id and reads target config."""
        cfg_dir = self.repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "project.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "preset": "completely-clean-target",
                    "delivery_mode": "clean-delta",
                }
            ),
            encoding="utf-8",
        )
        (cfg_dir / "local.json").write_text(
            json.dumps({"schema_version": 2, "project_id": ""}),
            encoding="utf-8",
        )

        old_aw_home = os.environ.get("AW_HOME")
        try:
            os.environ["AW_HOME"] = str(self.aw_home)
            pcd = project_config_dir(self.repo)
            self.assertEqual(pcd, cfg_dir)

            ctx = resolve_project_context(target_repo=str(self.repo))
            self.assertTrue(bool(ctx.project_id.strip()))
            self.assertEqual(ctx.preset, "completely-clean-target")
        finally:
            if old_aw_home is not None:
                os.environ["AW_HOME"] = old_aw_home
            else:
                os.environ.pop("AW_HOME", None)

    def test_case_g_local_only_preset(self) -> None:
        """Case (g): cases (a) and (b) repeated for --preset local-only."""
        # Case (a) for local-only
        self._run_aw("install", ".", "--preset", "local-only", "-y", "--no-interactive")
        self.assertFalse((self.repo / ".aw" / "config").exists())
        self.assertFalse((self.repo / ".aw" / "state").exists())

        res = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--ignored",
                "--",
                ".aw/config",
                ".aw/state",
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")

        # Case (b) for local-only
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertTrue(bool(ctx.project_id.strip()))
        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())
        self.assertTrue((proj_dir / "config" / "local.json").is_file())
        self.assertTrue((proj_dir / "state" / "durable" / "install.json").is_file())
        self.assertTrue(
            (proj_dir / "state" / "durable" / "history" / "installs.jsonl").is_file()
        )
        self.assertFalse((self.aw_home / "projects" / "state").exists())

    def test_case_h_doctor_reports_preset(self) -> None:
        """Case (h): after a clean-target install, aw doctor reports the stored preset."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        doc_res = self._run_aw("doctor", check=False)
        self.assertIn("preset: completely-clean-target", doc_res.stdout)

    def test_case_i_uninstall_cleans_home_and_allows_reinstall(self) -> None:
        """Case (i): after clean-target install, aw uninstall . -y removes home files and allows reinstall."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())

        un_res = self._run_aw("uninstall", ".", "-y")
        self.assertFalse((proj_dir / "config" / "project.json").exists())
        self.assertFalse((proj_dir / "state").exists())
        self.assertIn("removed", un_res.stdout)

        re_res = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self.assertEqual(re_res.returncode, 0)
        self.assertTrue((proj_dir / "config" / "project.json").is_file())

    def test_case_j_public_target_private_companion(self) -> None:
        """Case (j): public-target-private-companion install keeps config_project in target and tracked delivery."""
        companion_repo = self.base / "companion_repo"
        companion_repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(companion_repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(companion_repo),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(companion_repo),
            check=True,
        )
        (companion_repo / "README.md").write_text("# Companion\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(companion_repo), check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit"],
            cwd=str(companion_repo),
            check=True,
        )

        self._run_aw(
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "--companion-dir",
            str(companion_repo),
            "-y",
            "--no-interactive",
        )

        self.assertTrue((self.repo / ".aw" / "config" / "project.json").is_file())
        ctx = resolve_project_context(
            target_repo=str(self.repo), companion_dir=str(companion_repo)
        )
        self.assertEqual(ctx.delivery_mode, "tracked")


if __name__ == "__main__":
    unittest.main()
