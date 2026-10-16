"""Tests for placement switch footprint retirement (IPD gjylny / Set cfgreloc)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import engine
from agent_workflows.placement_switch import (
    PlacementSwitchError,
    retire_footprint,
)
from agent_workflows.project_context import (
    _canonical_path,
    _derive_project_id,
    checkout_main_root,
)


@pytest.mark.slow
class TestPlacementSwitchRetire(unittest.TestCase):
    """Behavioral unit and integration tests for retire_footprint and uninstall_repo."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tpath = Path(self.tmp.name)
        self.aw_home = self.tpath / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        self.xdg_home = self.tpath / "xdg_home"
        self.xdg_home.mkdir(parents=True, exist_ok=True)

        self.repo_root = str(Path(__file__).resolve().parent.parent)
        self.repo, self.env = self._init_and_install_repo(
            self.tpath, self.aw_home, self.xdg_home, preset="private-target"
        )
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

    def tearDown(self) -> None:
        if self._prev_aw_home is not None:
            os.environ["AW_HOME"] = self._prev_aw_home
        else:
            os.environ.pop("AW_HOME", None)
        self.tmp.cleanup()

    def _make_env(self, tpath: Path, aw_home: Path, xdg_home: Path) -> dict[str, str]:
        return dict(
            os.environ,
            PYTHONPATH=f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(tpath),
            AW_HOME=str(aw_home),
            XDG_CONFIG_HOME=str(xdg_home),
            GIT_AUTHOR_NAME="Test User",
            GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test User",
            GIT_COMMITTER_EMAIL="test@example.com",
        )

    def _init_and_install_repo(
        self,
        tpath: Path,
        aw_home: Path,
        xdg_home: Path,
        preset: str = "private-target",
        name: str = "repo",
    ) -> tuple[Path, dict[str, str]]:
        repo = tpath / name
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(repo)], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(repo),
            check=True,
        )
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=str(repo),
            check=True,
        )

        env = self._make_env(tpath, aw_home, xdg_home)
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                str(repo),
                "--preset",
                preset,
                "-y",
                "--no-interactive",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, f"installer failed: {r.stdout}\n{r.stderr}")
        return repo, env

    def _snapshot(self, dir_path: Path) -> dict[str, bytes]:
        snap: dict[str, bytes] = {}
        if not dir_path.is_dir():
            return snap
        for p in sorted(dir_path.rglob("*")):
            if p.is_file() and not p.is_symlink():
                rel = p.relative_to(dir_path).as_posix()
                snap[rel] = p.read_bytes()
        return snap

    def _simulate_flip_to_home(self, repo: Path) -> Path:
        anchor = checkout_main_root(repo) or repo
        pid = _derive_project_id(_canonical_path(anchor))
        home_proj_dir = self.aw_home / "projects" / pid
        home_cfg_dir = home_proj_dir / "config"
        home_cfg_dir.mkdir(parents=True, exist_ok=True)

        home_policy = {
            "schema_version": 1,
            "preset": "completely-clean-target",
            "delivery_mode": "clean-delta",
            "records_backend": "home",
            "project_id": pid,
        }
        (home_cfg_dir / "project.json").write_text(
            json.dumps(home_policy, indent=2) + "\n", encoding="utf-8"
        )

        home_state_dir = home_proj_dir / "state" / "durable"
        home_state_dir.mkdir(parents=True, exist_ok=True)
        (home_state_dir / "install.json").write_text(
            json.dumps({"installed": True}, indent=2) + "\n", encoding="utf-8"
        )

        home_rec_dir = home_proj_dir / "records"
        home_rec_dir.mkdir(parents=True, exist_ok=True)
        (home_rec_dir / "keep.md").write_text("# Home Record\n", encoding="utf-8")

        # Delete in-tree config
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "rm",
                "-f",
                "--ignore-unmatch",
                ".aw/config/project.json",
                ".aw/config/local.json",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        in_proj = repo / ".aw" / "config" / "project.json"
        if in_proj.exists():
            in_proj.unlink()
        in_local = repo / ".aw" / "config" / "local.json"
        if in_local.exists():
            in_local.unlink()
        in_cfg_dir = repo / ".aw" / "config"
        if in_cfg_dir.is_dir():
            try:
                in_cfg_dir.rmdir()
            except OSError:
                pass

        self.assertTrue(
            engine._is_clean_delta_install(repo),
            "Repository must resolve as clean-delta install after simulated flip",
        )
        return home_proj_dir

    def test_01_target_side_simulated_flip_home_snapshot_byte_identical_and_staged_deletions(
        self,
    ) -> None:
        """Case (1): target side on private-target after flip stages deletions, leaves home byte-identical."""
        # 1. Add user file notes/mine.md
        (self.repo / "notes").mkdir(parents=True, exist_ok=True)
        (self.repo / "notes" / "mine.md").write_text("my notes\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "notes/mine.md"], check=True
        )

        # 2. Add user section in AGENTS.md outside managed block
        agents_path = self.repo / "AGENTS.md"
        self.assertTrue(agents_path.is_file())
        agents_text = agents_path.read_text(encoding="utf-8")
        agents_text += "\n## My Custom Section\nUser notes outside block.\n"
        agents_path.write_text(agents_text, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "AGENTS.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "commit",
                "-m",
                "add user notes and custom AGENTS section",
            ],
            check=True,
        )

        commit_count_before = int(
            subprocess.check_output(
                ["git", "-C", str(self.repo), "rev-list", "--count", "HEAD"]
            )
            .decode()
            .strip()
        )

        # 3. Simulate flip
        home_proj_dir = self._simulate_flip_to_home(self.repo)
        home_snap_before = self._snapshot(home_proj_dir)
        self.assertTrue(len(home_snap_before) > 0)

        # 4. Run retire_footprint(repo, "target")
        actions = retire_footprint(self.repo, "target")
        self.assertTrue(len(actions) > 0)

        # 5. Assert every manifest-owned in-tree file is gone
        self.assertFalse((self.repo / ".aw" / "system").exists())
        self.assertFalse((self.repo / ".aw" / ".gitignore").exists())
        self.assertFalse((self.repo / ".aw" / "inbox" / "README.md").exists())
        self.assertFalse((self.repo / ".aw" / "setup-repo-needed.md").exists())

        # 6. Assert deletions are STAGED
        diff_status = subprocess.check_output(
            ["git", "-C", str(self.repo), "diff", "--cached", "--name-status"],
            text=True,
        )
        self.assertIn("D\t.aw/system/VERSION", diff_status)
        self.assertIn("D\t.aw/inbox/README.md", diff_status)
        self.assertIn("D\t.aw/.gitignore", diff_status)

        # 7. Assert nothing is committed
        commit_count_after = int(
            subprocess.check_output(
                ["git", "-C", str(self.repo), "rev-list", "--count", "HEAD"]
            )
            .decode()
            .strip()
        )
        self.assertEqual(
            commit_count_before,
            commit_count_after,
            "Retirement must stage deletions without committing",
        )

        # 8. Assert home tree is byte-identical before and after
        home_snap_after = self._snapshot(home_proj_dir)
        self.assertEqual(
            home_snap_before,
            home_snap_after,
            "Home tree snapshot must be byte-identical before and after target retirement",
        )
        print(
            "[ASSERTION] Home tree snapshot byte-identical before and after retirement: verified"
        )

        # 9. Assert user file and user AGENTS.md section survived
        self.assertTrue((self.repo / "notes" / "mine.md").exists())
        self.assertEqual(
            (self.repo / "notes" / "mine.md").read_text(encoding="utf-8"),
            "my notes\n",
        )
        agents_after = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## My Custom Section", agents_after)
        self.assertIn("User notes outside block.", agents_after)
        self.assertNotIn("aw:pointer", agents_after)

    def test_02_target_side_drifted_file_preserved_action_reported(self) -> None:
        """Case (2): hand-edited and committed command shim survives and is reported PRESERVED."""
        advise = self.repo / ".opencode" / "commands" / "advise.md"
        self.assertTrue(advise.exists())
        advise.write_text("user customized advise command\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", str(advise)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-m", "user edit advise command"],
            check=True,
        )

        self._simulate_flip_to_home(self.repo)

        actions = retire_footprint(self.repo, "target")

        # Assert advise.md survived with user content
        self.assertTrue(advise.exists())
        self.assertEqual(
            advise.read_text(encoding="utf-8"),
            "user customized advise command\n",
        )

        # Assert PRESERVED action reported
        preserved = [
            a
            for a in actions
            if "PRESERVED" in a and ".opencode/commands/advise.md" in a
        ]
        self.assertTrue(
            len(preserved) > 0,
            f"Expected PRESERVED report for .opencode/commands/advise.md in actions, got: {actions}",
        )
        print(f"[ACTION REPORTED] {preserved[0]}")

    def test_03_target_side_preserve_records_leaves_records_untouched(self) -> None:
        """Case (3): preserve={'.aw/records'} leaves .aw/records/** untouched."""
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        task_path = self.repo / ".aw" / "records" / "backlog" / "open" / "task.md"
        task_path.write_text("# Open Task\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", str(task_path)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-m", "add open backlog task"],
            check=True,
        )

        self._simulate_flip_to_home(self.repo)

        actions = retire_footprint(self.repo, "target", preserve={".aw/records"})
        self.assertTrue(len(actions) > 0)

        self.assertTrue(task_path.exists())
        self.assertEqual(task_path.read_text(encoding="utf-8"), "# Open Task\n")
        self.assertTrue((self.repo / ".aw" / "records").is_dir())

    def test_04_home_side_removes_framework_trees_and_prunes_project_dir(self) -> None:
        """Case (4): home side removes system/, state/, config/ and prunes empty project dir."""
        anchor = checkout_main_root(self.repo) or self.repo
        pid = _derive_project_id(_canonical_path(anchor))
        home_proj_dir = self.aw_home / "projects" / pid
        (home_proj_dir / "system").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "system" / "managed-sections.json").write_text(
            "{}", encoding="utf-8"
        )
        (home_proj_dir / "state").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "state" / "runtime.json").write_text("{}", encoding="utf-8")
        (home_proj_dir / "config").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "config" / "project.json").write_text("{}", encoding="utf-8")
        (home_proj_dir / "worktrees" / ".owners").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "worktrees" / ".owners" / "owner.json").write_text(
            "{}", encoding="utf-8"
        )

        repo_snap_before = self._snapshot(self.repo)

        actions = retire_footprint(self.repo, "home")
        self.assertTrue(len(actions) > 0)

        # Assert home directories removed and project dir pruned
        self.assertFalse(
            home_proj_dir.exists(), "Home project directory must be pruned when empty"
        )

        # Assert target repo tree is completely unchanged
        repo_snap_after = self._snapshot(self.repo)
        self.assertEqual(
            repo_snap_before,
            repo_snap_after,
            "Target repo tree must remain completely unchanged after home footprint retirement",
        )

    def test_04b_target_side_tracked_paths_clean_and_inbox_user_file_preserved(
        self,
    ) -> None:
        """Case (4b): target leaves only preserved tracked paths, user inbox file survives PRESERVED."""
        # 1. Drop a user file in .aw/inbox/
        (self.repo / ".aw" / "inbox").mkdir(parents=True, exist_ok=True)
        user_drop = self.repo / ".aw" / "inbox" / "drop.txt"
        user_drop.write_text("user raw inbox drop\n", encoding="utf-8")

        # 2. Add a record in .aw/records
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        task_path = self.repo / ".aw" / "records" / "backlog" / "open" / "task.md"
        task_path.write_text("# Open Task\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", str(task_path)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-m", "add open backlog task"],
            check=True,
        )

        self._simulate_flip_to_home(self.repo)

        actions = retire_footprint(self.repo, "target", preserve={".aw/records"})

        # 3. Assert git ls-files .aw lists only .aw/records/**
        ls_out = subprocess.check_output(
            ["git", "-C", str(self.repo), "ls-files", ".aw"], text=True
        )
        tracked = [ln for ln in ls_out.splitlines() if ln]
        self.assertTrue(
            all(p.startswith(".aw/records/") for p in tracked),
            f"Expected only .aw/records tracked paths under .aw, got: {tracked}",
        )

        # 4. Assert user drop in .aw/inbox survived and was reported PRESERVED
        self.assertTrue(user_drop.exists())
        self.assertEqual(user_drop.read_text(encoding="utf-8"), "user raw inbox drop\n")
        preserved = [a for a in actions if "PRESERVED" in a and "drop.txt" in a]
        self.assertTrue(
            len(preserved) > 0,
            f"Expected PRESERVED report for drop.txt in actions, got: {actions}",
        )
        print(f"[ACTION REPORTED] {preserved[0]}")

    def test_05_home_side_records_present_raises_placement_switch_error_and_removes_nothing(
        self,
    ) -> None:
        """Case (5): home side with a file under records/ raises PlacementSwitchError and removes nothing."""
        anchor = checkout_main_root(self.repo) or self.repo
        pid = _derive_project_id(_canonical_path(anchor))
        home_proj_dir = self.aw_home / "projects" / pid
        (home_proj_dir / "system").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "system" / "managed-sections.json").write_text(
            "{}", encoding="utf-8"
        )
        (home_proj_dir / "config").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "config" / "project.json").write_text("{}", encoding="utf-8")
        (home_proj_dir / "records").mkdir(parents=True, exist_ok=True)
        (home_proj_dir / "records" / "keep.md").write_text(
            "# Keep Record\n", encoding="utf-8"
        )

        snap_before = self._snapshot(home_proj_dir)

        with self.assertRaises(PlacementSwitchError) as ctx:
            retire_footprint(self.repo, "home")

        self.assertIn("records/ under", str(ctx.exception))

        snap_after = self._snapshot(home_proj_dir)
        self.assertEqual(
            snap_before,
            snap_after,
            "Home project directory must remain completely unmodified when PlacementSwitchError is raised",
        )

    def test_06_uninstall_repo_default_clean_target_regression_removes_home_trees(
        self,
    ) -> None:
        """Case (6): uninstall_repo default (side=None) on completely-clean-target still removes home trees."""
        clean_repo, _ = self._init_and_install_repo(
            self.tpath,
            self.aw_home,
            self.xdg_home,
            preset="completely-clean-target",
            name="clean_repo",
        )
        anchor = checkout_main_root(clean_repo) or clean_repo
        pid = _derive_project_id(_canonical_path(anchor))
        home_proj_dir = self.aw_home / "projects" / pid
        self.assertTrue(home_proj_dir.exists())
        self.assertTrue((home_proj_dir / "system").exists())
        self.assertTrue((home_proj_dir / "config").exists())

        # Call default uninstall_repo
        engine.uninstall_repo(clean_repo, use_git=True)

        self.assertFalse((home_proj_dir / "system").exists())
        self.assertFalse((home_proj_dir / "config").exists())
        self.assertFalse((home_proj_dir / "state").exists())
        self.assertTrue((home_proj_dir / "records").exists())
