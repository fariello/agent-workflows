"""Tests for pure placement switch planner (IPD xvlemm / Set cfgreloc)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pytest

from agent_workflows.install_wizard import (
    ProjectPolicy,
    get_preset_defaults,
)
from agent_workflows.placement_switch import (
    plan_placement_switch,
)
from agent_workflows.project_schema import Preset


@pytest.mark.slow
class TestPlacementSwitchPlan(unittest.TestCase):
    """Subprocess and behavioral tests for pure placement switch planner."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = str(Path(__file__).resolve().parent.parent)

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
        )
        self.assertEqual(r.returncode, 0, f"installer failed: {r.stdout}\n{r.stderr}")
        return repo, env

    def _make_policy(
        self, preset: str, aw_home: str | Path, role: str = "target"
    ) -> ProjectPolicy:
        pls, gps, dm, rb, ds = get_preset_defaults(preset)
        return ProjectPolicy(
            preset=preset,
            role=role,
            delivery_mode=dm,
            records_backend=rb,
            durability_state=ds,
            aw_home=str(aw_home),
        )

    def test_to_home_census_and_warnings(self) -> None:
        """(1) to-home item census moves records, rewrites config, sets retire_side=target, and reports warning."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )

            # Add and commit a user record
            backlog_dir = repo / ".aw" / "records" / "backlog" / "open"
            backlog_dir.mkdir(parents=True, exist_ok=True)
            user_record = backlog_dir / "x.backlog.md"
            user_record.write_text("# Backlog item x\n", encoding="utf-8")
            subprocess.run(["git", "add", str(user_record)], cwd=str(repo), check=True)
            subprocess.run(
                ["git", "commit", "-m", "add user record"],
                cwd=str(repo),
                env=env,
                check=True,
            )

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)

            self.assertEqual(plan.direction, "to-home")
            self.assertEqual(plan.retire_side, "target")
            self.assertEqual(plan.blockers, [])
            self.assertEqual(plan.from_preset, Preset.PRIVATE_TARGET.value)
            self.assertEqual(plan.to_preset, Preset.LOCAL_ONLY.value)

            # Check config_project rewrite
            proj_items = [it for it in plan.items if it.item_class == "config_project"]
            self.assertEqual(len(proj_items), 1)
            self.assertEqual(proj_items[0].kind, "rewrite")
            self.assertTrue(proj_items[0].tracked)
            expected_proj_dst = (
                aw_home / "projects" / plan.project_id / "config" / "project.json"
            )
            self.assertEqual(proj_items[0].destination, expected_proj_dst)

            # Check user record move
            user_items = [
                it
                for it in plan.items
                if it.item_class == "records" and it.source.name == "x.backlog.md"
            ]
            self.assertEqual(len(user_items), 1)
            self.assertEqual(user_items[0].kind, "move")
            self.assertTrue(user_items[0].tracked)
            expected_user_dst = (
                aw_home
                / "projects"
                / plan.project_id
                / "records"
                / "backlog"
                / "open"
                / "x.backlog.md"
            )
            self.assertEqual(user_items[0].destination, expected_user_dst)

            # Warnings count
            self.assertIn("records-become-untracked", plan.warnings)
            self.assertGreater(plan.warnings["records-become-untracked"], 0)

    def test_to_target_census(self) -> None:
        """(2) to-target census moves records from home into target, sets retire_side=home, and reports warning."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.LOCAL_ONLY.value
            )

            pol_priv = self._make_policy(Preset.PRIVATE_TARGET.value, aw_home=aw_home)
            plan = plan_placement_switch(repo, pol_priv, aw_home=aw_home)

            self.assertEqual(plan.direction, "to-target")
            self.assertEqual(plan.retire_side, "home")
            self.assertEqual(plan.blockers, [])
            self.assertEqual(plan.from_preset, Preset.LOCAL_ONLY.value)
            self.assertEqual(plan.to_preset, Preset.PRIVATE_TARGET.value)

            # Check config_project rewrite
            proj_items = [it for it in plan.items if it.item_class == "config_project"]
            self.assertEqual(len(proj_items), 1)
            self.assertEqual(proj_items[0].kind, "rewrite")
            self.assertFalse(proj_items[0].tracked)
            self.assertEqual(
                proj_items[0].destination, repo / ".aw" / "config" / "project.json"
            )

            # Check records moves into target
            rec_items = [
                it
                for it in plan.items
                if it.item_class == "records" and it.kind == "move"
            ]
            self.assertGreater(len(rec_items), 0)
            for it in rec_items:
                self.assertFalse(it.tracked)
                self.assertTrue(
                    str(it.destination).startswith(str(repo / ".aw" / "records"))
                )

            # Warnings count
            self.assertIn("records-become-tracked-candidates", plan.warnings)
            self.assertEqual(
                plan.warnings["records-become-tracked-candidates"], len(rec_items)
            )

    def test_not_a_placement_switch(self) -> None:
        """(3) Same-placement policy returns empty items and blocker 'not-a-placement-switch'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_priv = self._make_policy(Preset.PRIVATE_TARGET.value, aw_home=aw_home)

            plan = plan_placement_switch(repo, pol_priv, aw_home=aw_home)
            self.assertEqual(plan.items, [])
            self.assertIn("not-a-placement-switch", plan.blockers)

    def test_companion_unsupported_short_circuit(self) -> None:
        """(4) Companion policy on private-target returns 'companion-unsupported' (not 'not-a-placement-switch')."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_comp = self._make_policy(
                Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value, aw_home=aw_home
            )

            plan = plan_placement_switch(repo, pol_comp, aw_home=aw_home)
            self.assertEqual(plan.items, [])
            self.assertIn("companion-unsupported", plan.blockers)
            self.assertNotIn("not-a-placement-switch", plan.blockers)
            self.assertIn("n9vd2h", plan.blocker_messages["companion-unsupported"])

    def test_project_id_mismatch_on_copied_checkout(self) -> None:
        """(5) Copied checkout with stale local.json triggers 'project-id-mismatch'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            repo_copy = tpath / "repo_copy"
            shutil.copytree(repo, repo_copy)

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            plan = plan_placement_switch(repo_copy, pol_local, aw_home=aw_home)

            self.assertIn("project-id-mismatch", plan.blockers)

    def test_blocker_dirty_aw_tree(self) -> None:
        """(6a) Untracked or modified file under .aw triggers 'dirty-aw-tree'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            (repo / ".aw" / "records" / "untracked_note.md").write_text("note\n")

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)

            self.assertEqual(plan.blockers, ["dirty-aw-tree"])

    def test_blocker_unmerged(self) -> None:
        """(6b) Git merge conflict outside .aw triggers 'unmerged' without 'dirty-aw-tree'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )

            subprocess.run(
                ["git", "checkout", "-b", "b_conflict"],
                cwd=str(repo),
                check=True,
                capture_output=True,
            )
            (repo / "conflict.txt").write_text("branch1\n")
            subprocess.run(["git", "add", "conflict.txt"], cwd=str(repo), check=True)
            subprocess.run(
                ["git", "commit", "-m", "conflict b1"],
                cwd=str(repo),
                env=env,
                check=True,
            )

            subprocess.run(
                ["git", "checkout", "main"],
                cwd=str(repo),
                check=True,
                capture_output=True,
            )
            (repo / "conflict.txt").write_text("branch2\n")
            subprocess.run(["git", "add", "conflict.txt"], cwd=str(repo), check=True)
            subprocess.run(
                ["git", "commit", "-m", "conflict b2"],
                cwd=str(repo),
                env=env,
                check=True,
            )

            subprocess.run(
                ["git", "merge", "b_conflict"],
                cwd=str(repo),
                check=False,
                capture_output=True,
            )

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)

            self.assertEqual(plan.blockers, ["unmerged"])

    def test_blocker_destination_not_empty(self) -> None:
        """(6c) Non-empty home project child directory triggers 'destination-not-empty'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            clean_plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertEqual(clean_plan.blockers, [])

            # Create unexpected child directory under home project
            home_proj = aw_home / "projects" / clean_plan.project_id
            (home_proj / "records").mkdir(parents=True)

            blocked_plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertEqual(blocked_plan.blockers, ["destination-not-empty"])

    def test_blocker_live_lane(self) -> None:
        """(6d) Active git worktree under .aw/worktrees triggers 'live-lane'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            wt_dir = repo / ".aw" / "worktrees" / "lane_test"
            subprocess.run(
                ["git", "worktree", "add", "-b", "lane_test", str(wt_dir), "main"],
                cwd=str(repo),
                check=True,
                capture_output=True,
            )

            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertEqual(plan.blockers, ["live-lane"])

    def test_blocker_unparseable_config(self) -> None:
        """(6e) Committed malformed project.json triggers 'unparseable-config'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            proj_file = repo / ".aw" / "config" / "project.json"
            proj_file.write_text("[1, 2\n", encoding="utf-8")
            subprocess.run(
                ["git", "commit", "-am", "corrupt project.json"],
                cwd=str(repo),
                env=env,
                check=True,
                capture_output=True,
            )

            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertEqual(plan.blockers, ["unparseable-config"])

    def test_blocker_source_checkout(self) -> None:
        """(6f) source-checkout role triggers 'source-checkout' blocker."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_src = self._make_policy(
                Preset.LOCAL_ONLY.value, aw_home=aw_home, role="source-checkout"
            )

            plan = plan_placement_switch(repo, pol_src, aw_home=aw_home)
            self.assertEqual(plan.blockers, ["source-checkout"])

    def test_purity_snapshot(self) -> None:
        """(8) Planning is strictly pure: filesystem stat and git index untouched even after dirty stat."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._init_and_install_repo(
                tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
            )
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            # Touch a tracked file to dirty its stat in relation to git index
            readme = repo / "README.md"
            time.sleep(0.01)
            os.utime(readme, None)

            def snapshot(root: Path) -> dict[str, tuple[int, int]]:
                snap = {}
                for p in root.rglob("*"):
                    try:
                        st = p.lstat()
                        snap[str(p)] = (st.st_mtime_ns, st.st_size)
                    except OSError:
                        pass
                return snap

            env_git = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
            git_status_before = subprocess.run(
                ["git", "-c", "core.fsmonitor=false", "status", "--porcelain"],
                cwd=str(repo),
                env=env_git,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

            snap_repo_before = snapshot(repo)
            snap_home_before = snapshot(aw_home)

            # Execute pure planner
            plan = plan_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertEqual(plan.direction, "to-home")
            self.assertEqual(plan.blockers, [])

            snap_repo_after = snapshot(repo)
            snap_home_after = snapshot(aw_home)
            git_status_after = subprocess.run(
                ["git", "-c", "core.fsmonitor=false", "status", "--porcelain"],
                cwd=str(repo),
                env=env_git,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

            self.assertEqual(
                snap_repo_before,
                snap_repo_after,
                "Repository files (including .git/index) mutated by planner!",
            )
            self.assertEqual(
                snap_home_before,
                snap_home_after,
                "AW_HOME files mutated by planner!",
            )
            self.assertEqual(
                git_status_before,
                git_status_after,
                "git status changed after planner execution!",
            )
