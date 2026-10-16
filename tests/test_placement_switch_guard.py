"""Tests for config placement switch detection and entry point refusals (IPD ppu39q / Set cfgreloc)."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_workflows import cli
from agent_workflows.install_wizard import (
    PlacementSwitchRequired,
    ProjectPolicy,
    config_placement_switch,
    persist_project_policy,
)
from agent_workflows.project_schema import Preset


class TestPlacementSwitchGuardUnit(unittest.TestCase):
    """In-process unit tests for config_placement_switch detector, persist guard, and interactive CLI."""

    def _init_git_repo(self, path: Path) -> None:
        subprocess.run(
            ["git", "init", "-b", "main", str(path)], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(path), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(path),
            check=True,
        )
        (path / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(path), check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), check=True)

    def _make_policy(
        self,
        preset: str,
        aw_home: str | None = None,
        companion_dir: str | None = None,
    ) -> ProjectPolicy:
        from agent_workflows.install_wizard import get_preset_defaults

        _pls, _gps, dm, rb, ds = get_preset_defaults(preset)
        return ProjectPolicy(
            preset=preset,
            delivery_mode=dm,
            records_backend=rb,
            durability_state=ds,
            role="source-checkout",
            aw_home=aw_home,
            companion_dir=companion_dir,
            non_secret_consent={"telemetry": True},
        )

    def test_config_placement_switch_cases(self) -> None:
        """(1) Detector returns None for fresh/same-placement, and expected path/label hits."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env_patch = {
                "HOME": str(tpath),
                "AW_HOME": str(aw_home),
                "XDG_CONFIG_HOME": str(xdg_home),
                "AW_NO_REEXEC": "1",
            }
            with patch.dict(os.environ, env_patch):
                pol_priv = self._make_policy(
                    Preset.PRIVATE_TARGET.value, aw_home=str(aw_home)
                )
                pol_local = self._make_policy(
                    Preset.LOCAL_ONLY.value, aw_home=str(aw_home)
                )

                # 1. Fresh repo: returns None
                res_fresh = config_placement_switch(str(repo), pol_priv)
                self.assertIsNone(res_fresh)

                # Persist private-target policy to disk
                persist_project_policy(str(repo), pol_priv)

                # 2. Same-placement policy: returns None
                res_same = config_placement_switch(str(repo), pol_priv)
                self.assertIsNone(res_same)

                # 3. private-target repo given local-only policy: reason="path" hit with both dirs
                res_switch = config_placement_switch(str(repo), pol_local)
                self.assertIsNotNone(res_switch)
                self.assertEqual(res_switch.reason, "path")
                self.assertEqual(
                    res_switch.current_dir.resolve(),
                    (repo / ".aw" / "config").resolve(),
                )
                self.assertNotEqual(
                    res_switch.current_dir.resolve(), res_switch.target_dir.resolve()
                )

                # 4. Repo whose in-tree .aw/config holds only local.json (no project.json) given local-only policy
                repo_local_only = tpath / "repo_local_only"
                repo_local_only.mkdir()
                self._init_git_repo(repo_local_only)
                cfg_local_dir = repo_local_only / ".aw" / "config"
                cfg_local_dir.mkdir(parents=True)
                with open(cfg_local_dir / "local.json", "w", encoding="utf-8") as f:
                    json.dump({"schema_version": 2, "project_id": "test_id"}, f)

                res_local_only = config_placement_switch(
                    str(repo_local_only), pol_local
                )
                self.assertIsNotNone(res_local_only)
                self.assertEqual(res_local_only.reason, "path")
                self.assertEqual(
                    res_local_only.current_dir.resolve(), cfg_local_dir.resolve()
                )
                self.assertNotEqual(
                    res_local_only.current_dir.resolve(),
                    res_local_only.target_dir.resolve(),
                )

                # 5. existing_policy=private-target given public-target-private-companion policy: reason="label" hit
                comp_dir = tpath / "companion_store"
                comp_dir.mkdir()
                pol_comp = self._make_policy(
                    Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
                    aw_home=str(aw_home),
                    companion_dir=str(comp_dir),
                )
                res_label = config_placement_switch(
                    str(repo), pol_comp, existing_policy=pol_priv
                )
                self.assertIsNotNone(res_label)
                self.assertEqual(res_label.reason, "label")
                self.assertEqual(
                    res_label.current_dir.resolve(), res_label.target_dir.resolve()
                )

    def test_persist_project_policy_refuses_cross_placement(self) -> None:
        """(2) persist_project_policy with local-only on private-target repo raises PlacementSwitchRequired."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env_patch = {
                "HOME": str(tpath),
                "AW_HOME": str(aw_home),
                "XDG_CONFIG_HOME": str(xdg_home),
                "AW_NO_REEXEC": "1",
            }
            with patch.dict(os.environ, env_patch):
                pol_priv = self._make_policy(
                    Preset.PRIVATE_TARGET.value, aw_home=str(aw_home)
                )
                persist_project_policy(str(repo), pol_priv)

                pol_local = self._make_policy(
                    Preset.LOCAL_ONLY.value, aw_home=str(aw_home)
                )
                with self.assertRaises(PlacementSwitchRequired) as cm:
                    persist_project_policy(str(repo), pol_local)

                self.assertEqual(cm.exception.reason, "path")
                self.assertIn("Switching config placement", str(cm.exception))
                self.assertIn("ui1aln", str(cm.exception))
                home_projects = list(aw_home.glob("projects/*/config/project.json"))
                self.assertEqual(home_projects, [])

    def test_interactive_wizard_end_to_end_refuses(self) -> None:
        """(3) In-process interactive wizard path refuses without writing to AW_HOME/projects."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env_patch = {
                "HOME": str(tpath),
                "AW_HOME": str(aw_home),
                "XDG_CONFIG_HOME": str(xdg_home),
                "AW_NO_REEXEC": "1",
            }
            with patch.dict(os.environ, env_patch):
                rc_init = cli.main(
                    [
                        "--no-color",
                        "install",
                        str(repo),
                        "--preset",
                        "private-target",
                        "-y",
                        "--no-interactive",
                    ]
                )
                self.assertEqual(rc_init, 0)

                proj_file = repo / ".aw" / "config" / "project.json"
                before_bytes = proj_file.read_bytes()

                with patch("sys.stdin", io.StringIO("n\n4\nprivate\n\n\n\n\n")):
                    rc = cli.main(["--no-color", "install", str(repo)])

                self.assertEqual(rc, 1)
                after_bytes = proj_file.read_bytes()
                self.assertEqual(before_bytes, after_bytes)
                home_projects = list(aw_home.glob("projects/*/config/project.json"))
                self.assertEqual(home_projects, [])


@pytest.mark.slow
class TestPlacementSwitchGuardSubprocess(unittest.TestCase):
    """Subprocess tests for CLI refusal behavior on placement switch."""

    def setUp(self) -> None:
        self.repo_root = str(Path(__file__).parent.parent.resolve())

    def _init_git_repo(self, path: Path) -> None:
        subprocess.run(
            ["git", "init", "-b", "main", str(path)], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(path), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(path),
            check=True,
        )
        (path / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(path), check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), check=True)

    def _make_env(self, tpath: Path, aw_home: Path, xdg_home: Path) -> dict:
        return dict(
            os.environ,
            PYTHONPATH=f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(tpath),
            AW_HOME=str(aw_home),
            XDG_CONFIG_HOME=str(xdg_home),
        )

    def test_subprocess_reinstall_delivery_mode_switch_refuses(self) -> None:
        """(4) Subprocess reinstall --delivery-mode clean-delta on private-target repo exits 1."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            r_init = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r_init.returncode, 0)

            proj_file = repo / ".aw" / "config" / "project.json"
            before_bytes = proj_file.read_bytes()

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--delivery-mode",
                    "clean-delta",
                    "--records-backend",
                    "home",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 1)
            output = r.stdout + r.stderr
            self.assertIn("Switching config placement", output)
            after_bytes = proj_file.read_bytes()
            self.assertEqual(before_bytes, after_bytes)
            home_projects = list(aw_home.glob("projects/*/config/project.json"))
            self.assertEqual(home_projects, [])

    def test_subprocess_reinstall_delivery_mode_switch_dry_run_refuses(self) -> None:
        """(5) Subprocess reinstall with --dry-run also exits 1 and writes nothing."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            r_init = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r_init.returncode, 0)

            proj_file = repo / ".aw" / "config" / "project.json"
            before_bytes = proj_file.read_bytes()

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--delivery-mode",
                    "clean-delta",
                    "--records-backend",
                    "home",
                    "-y",
                    "--no-interactive",
                    "--dry-run",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 1)
            output = r.stdout + r.stderr
            self.assertIn("Switching config placement", output)
            after_bytes = proj_file.read_bytes()
            self.assertEqual(before_bytes, after_bytes)
            home_projects = list(aw_home.glob("projects/*/config/project.json"))
            self.assertEqual(home_projects, [])
