"""Tests for placement switch transaction execution (IPD 6u755v / Set cfgreloc)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import platform_lock
from agent_workflows.install_wizard import (
    ProjectPolicy,
    get_preset_defaults,
)
from agent_workflows.placement_switch import (
    PlacementSwitchError,
    _calc_file_meta,
    _canonical_path,
    _derive_project_id,
    checkout_main_root,
    execute_placement_switch,
    placement_switch_status,
    resume_placement_switch,
    rollback_placement_switch,
)
from agent_workflows.project_context import (
    project_config_dir,
)
from agent_workflows.project_schema import Preset

pytestmark = pytest.mark.slow


def _take_working_tree_snapshot(
    dir_path: Path,
) -> dict[str, tuple[str | None, int | None, int | None]]:
    """Capture relative path -> (sha256, size, mode) ignoring .git directory."""
    snap = {}
    for p in dir_path.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_file() or p.is_symlink():
            rel = p.relative_to(dir_path).as_posix()
            sha, size, mode = _calc_file_meta(p)
            snap[rel] = (sha, size, mode)
    return snap


class TestPlacementSwitchExecute(unittest.TestCase):
    """Behavioral tests for journaled placement switch executor, resume and rollback."""

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

    def _derive_pid(self, repo: Path) -> str:
        anchor = repo
        try:
            if (repo / ".git").exists():
                anchor = checkout_main_root(repo) or repo
        except (OSError, RuntimeError):
            anchor = repo
        return _derive_project_id(_canonical_path(anchor))

    def _setup_private_target_customized(
        self, tpath: Path, aw_home: Path, xdg_home: Path
    ) -> tuple[Path, dict[str, str], str]:
        repo, env = self._init_and_install_repo(
            tpath, aw_home, xdg_home, preset=Preset.PRIVATE_TARGET.value
        )
        proj_path = repo / ".aw" / "config" / "project.json"
        d = json.loads(proj_path.read_text(encoding="utf-8"))
        d.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        d["run"] = {"retry_budget": 3}
        d["setids"] = {"warn_length": 10}
        d["enabled_hosts"] = ["opencode"]
        d["non_secret_consent"] = {"telemetry_prompted": True}
        proj_path.write_text(json.dumps(d, indent=2), encoding="utf-8")

        backlog_file = repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
        backlog_file.parent.mkdir(parents=True, exist_ok=True)
        backlog_file.write_text("# Backlog x\n", encoding="utf-8")

        subprocess.run(
            ["git", "add", str(proj_path), str(backlog_file)],
            cwd=str(repo),
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "customized private target"],
            cwd=str(repo),
            env=env,
            check=True,
        )
        pid = self._derive_pid(repo)
        return repo, env, pid

    def _setup_local_only_customized(
        self, tpath: Path, aw_home: Path, xdg_home: Path
    ) -> tuple[Path, dict[str, str], str]:
        repo, env = self._init_and_install_repo(
            tpath, aw_home, xdg_home, preset=Preset.LOCAL_ONLY.value
        )
        pid = self._derive_pid(repo)
        home_proj_dir = aw_home / "projects" / pid
        proj_path = home_proj_dir / "config" / "project.json"
        d = json.loads(proj_path.read_text(encoding="utf-8"))
        d.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        d["run"] = {"retry_budget": 3}
        d["setids"] = {"warn_length": 10}
        d["enabled_hosts"] = ["opencode"]
        d["non_secret_consent"] = {"telemetry_prompted": True}
        proj_path.write_text(json.dumps(d, indent=2), encoding="utf-8")

        backlog_file = home_proj_dir / "records" / "backlog" / "open" / "x.backlog.md"
        backlog_file.parent.mkdir(parents=True, exist_ok=True)
        backlog_file.write_text("# Backlog x\n", encoding="utf-8")

        runs_file = home_proj_dir / "records" / "runs" / "r1" / "state.json"
        runs_file.parent.mkdir(parents=True, exist_ok=True)
        runs_file.write_text('{"state": "ok"}\n', encoding="utf-8")

        return repo, env, pid

    def test_01_to_home_happy_path_from_private_target(self) -> None:
        """Case (1): to-home happy path from private-target."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_private_target_customized(
                tpath, aw_home, xdg_home
            )
            rev_count_before = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            result = execute_placement_switch(repo, pol_local, aw_home=aw_home)

            # 1. Exactly one project.json (home)
            all_projs = list(repo.rglob("project.json")) + list(
                aw_home.rglob("project.json")
            )
            self.assertEqual(
                len(all_projs), 1, f"Found multiple project.json files: {all_projs}"
            )
            expected_proj_path = aw_home / "projects" / pid / "config" / "project.json"
            self.assertEqual(all_projs[0].resolve(), expected_proj_path.resolve())

            # 2. project_config_dir is home
            pcd = project_config_dir(repo, aw_home=aw_home)
            self.assertEqual(
                pcd.resolve(), (aw_home / "projects" / pid / "config").resolve()
            )

            # 3. Every customized key and 2020 cutover preserved
            home_proj = json.loads(all_projs[0].read_text(encoding="utf-8"))
            self.assertEqual(
                home_proj.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(home_proj.get("run", {}).get("retry_budget"), 3)
            self.assertEqual(home_proj.get("setids", {}).get("warn_length"), 10)
            self.assertEqual(home_proj.get("enabled_hosts"), ["opencode"])
            self.assertEqual(
                home_proj.get("non_secret_consent"), {"telemetry_prompted": True}
            )

            # 4. x.backlog.md byte-identical at <AW_HOME>/projects/<id>/records/backlog/open/
            dest_backlog = (
                aw_home
                / "projects"
                / pid
                / "records"
                / "backlog"
                / "open"
                / "x.backlog.md"
            )
            self.assertTrue(dest_backlog.is_file())
            self.assertEqual(dest_backlog.read_text(encoding="utf-8"), "# Backlog x\n")

            # 5. state/durable/history/installs.jsonl moved
            dest_history = (
                aw_home
                / "projects"
                / pid
                / "state"
                / "durable"
                / "history"
                / "installs.jsonl"
            )
            self.assertTrue(dest_history.is_file())

            # 6. git diff --cached --name-status shows D for record, config, system/**
            # and every staged entry is D except M on exactly .gitignore and AGENTS.md
            diff_lines = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()

            for line in diff_lines:
                status, path_part = line.split(None, 1)
                if path_part in (".gitignore", "AGENTS.md"):
                    self.assertEqual(
                        status, "M", f"Expected M on {path_part}, got {status}"
                    )
                else:
                    self.assertEqual(
                        status, "D", f"Expected D on {path_part}, got {status}"
                    )

            # 7. git rev-list --count HEAD unchanged
            rev_count_after = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(rev_count_before, rev_count_after)

            # 8. No tracked path left under .aw/
            ls_aw = subprocess.run(
                ["git", "ls-files", ".aw"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(ls_aw, "")

            # 9. Receipt present, control dir and lock-adjacent control dir gone
            self.assertTrue(result.receipt_path.is_file())
            ctrl_dir = aw_home / "placement-switches" / pid
            self.assertFalse(ctrl_dir.exists())

            # Any remaining .aw/ file is named PRESERVED in the receipt
            receipt_data = json.loads(result.receipt_path.read_text(encoding="utf-8"))
            retire_actions = receipt_data.get("retire_actions", [])
            for p in (repo / ".aw").rglob("*"):
                if p.is_file():
                    rel = p.relative_to(repo).as_posix()
                    self.assertTrue(
                        any(a.startswith(f"PRESERVED {rel}") for a in retire_actions),
                        f"Remaining file {rel} was not named PRESERVED in receipt: {retire_actions}",
                    )

    def test_02_to_target_happy_path_from_local_only(self) -> None:
        """Case (2): to-target happy path from local-only."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_local_only_customized(tpath, aw_home, xdg_home)
            home_p = aw_home / "projects" / pid

            pol_priv = self._make_policy(Preset.PRIVATE_TARGET.value, aw_home=aw_home)
            result = execute_placement_switch(repo, pol_priv, aw_home=aw_home)

            # 1. in-tree project.json authoritative
            pcd = project_config_dir(repo, aw_home=aw_home)
            self.assertEqual(pcd.resolve(), (repo / ".aw" / "config").resolve())

            # 2. home config/, system/, state/ gone
            self.assertFalse((home_p / "config").exists())
            self.assertFalse((home_p / "system").exists())
            self.assertFalse((home_p / "state").exists())

            # 3. x.backlog.md staged as A
            diff_cached = {
                p: status
                for status, p in (
                    line.split(None, 1)
                    for line in subprocess.run(
                        ["git", "diff", "--cached", "--name-status"],
                        cwd=str(repo),
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.splitlines()
                )
            }
            self.assertEqual(
                diff_cached.get(".aw/records/backlog/open/x.backlog.md"), "A"
            )

            # 4. records/runs/r1/state.json present in-tree but NOT staged and git check-ignore reports ignored
            target_runs = repo / ".aw" / "records" / "runs" / "r1" / "state.json"
            self.assertTrue(target_runs.is_file())
            self.assertNotIn(".aw/records/runs/r1/state.json", diff_cached)
            ci_res = subprocess.run(
                ["git", "check-ignore", ".aw/records/runs/r1/state.json"],
                cwd=str(repo),
                capture_output=True,
                text=True,
            )
            self.assertEqual(ci_res.returncode, 0)

            # 5. .aw/.gitignore present
            self.assertTrue((repo / ".aw" / ".gitignore").is_file())
            self.assertTrue(result.receipt_path.is_file())

    def test_03_fault_points_resume_to_same_end_state(self) -> None:
        """Case (3): for each fault point in each direction, run with fault then resume."""
        fault_points = [
            "after-copy",
            "mid-verify",
            "after-switch",
            "mid-source-removal",
            "before-retire",
        ]

        for fp in fault_points:
            # 1. to-home direction
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                aw_home.mkdir()
                xdg_home = tpath / "xdg"
                xdg_home.mkdir()

                repo, env, pid = self._setup_private_target_customized(
                    tpath, aw_home, xdg_home
                )
                pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

                with self.assertRaises(PlacementSwitchError) as ctx:
                    execute_placement_switch(
                        repo, pol_local, aw_home=aw_home, fault_injection=fp
                    )
                self.assertIn(f"Fault injected: {fp}", str(ctx.exception))

                status = placement_switch_status(repo, aw_home=aw_home)
                self.assertIsNotNone(status)
                if fp in ("after-copy", "mid-verify"):
                    self.assertEqual(status["phase"], "copied")
                elif fp == "after-switch":
                    self.assertEqual(status["phase"], "switched")
                elif fp in ("mid-source-removal", "before-retire"):
                    self.assertEqual(status["phase"], "sources-removed")

                res = resume_placement_switch(repo, aw_home=aw_home)
                self.assertTrue(res.receipt_path.is_file())
                pcd = project_config_dir(repo, aw_home=aw_home)
                self.assertEqual(
                    pcd.resolve(), (aw_home / "projects" / pid / "config").resolve()
                )

            # 2. to-target direction
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                aw_home.mkdir()
                xdg_home = tpath / "xdg"
                xdg_home.mkdir()

                repo, env, pid = self._setup_local_only_customized(
                    tpath, aw_home, xdg_home
                )
                pol_priv = self._make_policy(
                    Preset.PRIVATE_TARGET.value, aw_home=aw_home
                )

                with self.assertRaises(PlacementSwitchError) as ctx:
                    execute_placement_switch(
                        repo, pol_priv, aw_home=aw_home, fault_injection=fp
                    )
                self.assertIn(f"Fault injected: {fp}", str(ctx.exception))

                status = placement_switch_status(repo, aw_home=aw_home)
                self.assertIsNotNone(status)
                if fp in ("after-copy", "mid-verify"):
                    self.assertEqual(status["phase"], "copied")
                elif fp == "after-switch":
                    self.assertEqual(status["phase"], "switched")
                elif fp in ("mid-source-removal", "before-retire"):
                    self.assertEqual(status["phase"], "sources-removed")

                res = resume_placement_switch(repo, aw_home=aw_home)
                self.assertTrue(res.receipt_path.is_file())
                pcd = project_config_dir(repo, aw_home=aw_home)
                self.assertEqual(pcd.resolve(), (repo / ".aw" / "config").resolve())

    def test_04_pre_sources_removed_fault_points_rollback_byte_identical(self) -> None:
        """Case (4): rollback from pre-sources-removed fault points produces byte-identical old side."""
        pre_faults = ["after-copy", "mid-verify", "after-switch"]

        for fp in pre_faults:
            # 1. to-home direction
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                aw_home.mkdir()
                xdg_home = tpath / "xdg"
                xdg_home.mkdir()

                repo, env, pid = self._setup_private_target_customized(
                    tpath, aw_home, xdg_home
                )
                pre_repo_snap = _take_working_tree_snapshot(repo)
                pre_aw_home_snap = _take_working_tree_snapshot(aw_home)
                pre_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                pre_diff_cached = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
                with self.assertRaises(PlacementSwitchError):
                    execute_placement_switch(
                        repo, pol_local, aw_home=aw_home, fault_injection=fp
                    )

                rollback_placement_switch(repo, aw_home=aw_home)

                post_repo_snap = _take_working_tree_snapshot(repo)
                post_aw_home_snap = _take_working_tree_snapshot(aw_home)
                post_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                post_diff_cached = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                self.assertEqual(
                    pre_repo_snap, post_repo_snap, f"to-home {fp}: repo tree modified"
                )
                self.assertEqual(
                    pre_aw_home_snap,
                    post_aw_home_snap,
                    f"to-home {fp}: AW_HOME tree modified",
                )
                self.assertEqual(pre_status, post_status)
                self.assertEqual(pre_diff_cached, post_diff_cached)

                all_projs = list(repo.rglob("project.json")) + list(
                    aw_home.rglob("project.json")
                )
                self.assertEqual(
                    len(all_projs), 1, f"to-home {fp}: expected exactly 1 project.json"
                )

            # 2. to-target direction
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                aw_home.mkdir()
                xdg_home = tpath / "xdg"
                xdg_home.mkdir()

                repo, env, pid = self._setup_local_only_customized(
                    tpath, aw_home, xdg_home
                )
                pre_repo_snap = _take_working_tree_snapshot(repo)
                pre_aw_home_snap = _take_working_tree_snapshot(aw_home)
                pre_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                pre_diff_cached = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                pol_priv = self._make_policy(
                    Preset.PRIVATE_TARGET.value, aw_home=aw_home
                )
                with self.assertRaises(PlacementSwitchError):
                    execute_placement_switch(
                        repo, pol_priv, aw_home=aw_home, fault_injection=fp
                    )

                rollback_placement_switch(repo, aw_home=aw_home)

                post_repo_snap = _take_working_tree_snapshot(repo)
                post_aw_home_snap = _take_working_tree_snapshot(aw_home)
                post_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                post_diff_cached = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                self.assertEqual(
                    pre_repo_snap, post_repo_snap, f"to-target {fp}: repo tree modified"
                )
                self.assertEqual(
                    pre_aw_home_snap,
                    post_aw_home_snap,
                    f"to-target {fp}: AW_HOME tree modified",
                )
                self.assertEqual(pre_status, post_status)
                self.assertEqual(pre_diff_cached, post_diff_cached)

                all_projs = list(repo.rglob("project.json")) + list(
                    aw_home.rglob("project.json")
                )
                self.assertEqual(
                    len(all_projs),
                    1,
                    f"to-target {fp}: expected exactly 1 project.json",
                )

    def test_05_rollback_refused_after_sources_removed_and_resume_completes(
        self,
    ) -> None:
        """Case (5): rollback refused after mid-source-removal and before-retire, resume completes."""
        refuse_faults = ["mid-source-removal", "before-retire"]

        for fp in refuse_faults:
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                aw_home.mkdir()
                xdg_home = tpath / "xdg"
                xdg_home.mkdir()

                repo, env, pid = self._setup_private_target_customized(
                    tpath, aw_home, xdg_home
                )
                pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

                with self.assertRaises(PlacementSwitchError):
                    execute_placement_switch(
                        repo, pol_local, aw_home=aw_home, fault_injection=fp
                    )

                with self.assertRaises(PlacementSwitchError) as ctx:
                    rollback_placement_switch(repo, aw_home=aw_home)
                self.assertIn("resume", str(ctx.exception).lower())

                res = resume_placement_switch(repo, aw_home=aw_home)
                self.assertTrue(res.receipt_path.is_file())
                pcd = project_config_dir(repo, aw_home=aw_home)
                self.assertEqual(
                    pcd.resolve(), (aw_home / "projects" / pid / "config").resolve()
                )

    def test_06_blocker_refusal_dirty_aw_tree(self) -> None:
        """Case (6): dirty .aw/records file refuses with dirty-aw-tree and writes nothing."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_private_target_customized(
                tpath, aw_home, xdg_home
            )

            # Make working tree under .aw dirty
            dirty_file = repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
            dirty_file.write_text("# modified\n", encoding="utf-8")

            pre_aw_home_snap = _take_working_tree_snapshot(aw_home)
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            with self.assertRaises(PlacementSwitchError) as ctx:
                execute_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertIn("dirty-aw-tree", str(ctx.exception))

            post_aw_home_snap = _take_working_tree_snapshot(aw_home)
            self.assertEqual(pre_aw_home_snap, post_aw_home_snap)
            self.assertFalse((aw_home / "placement-switches" / pid).exists())

    def test_07_concurrent_lock_refusal(self) -> None:
        """Case (7): concurrent lock held refuses execute, resume, and rollback."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_private_target_customized(
                tpath, aw_home, xdg_home
            )
            lock_file = aw_home / "placement-switches" / f"{pid}.lock"
            lock_file.parent.mkdir(parents=True, exist_ok=True)

            lock_handle = platform_lock.acquire(lock_file)
            try:
                pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

                with self.assertRaises(PlacementSwitchError) as ctx_exec:
                    execute_placement_switch(repo, pol_local, aw_home=aw_home)
                self.assertIn(
                    "another placement switch is running", str(ctx_exec.exception)
                )

                with self.assertRaises(PlacementSwitchError) as ctx_res:
                    resume_placement_switch(repo, aw_home=aw_home)
                self.assertIn(
                    "another placement switch is running", str(ctx_res.exception)
                )

                with self.assertRaises(PlacementSwitchError) as ctx_rb:
                    rollback_placement_switch(repo, aw_home=aw_home)
                self.assertIn(
                    "another placement switch is running", str(ctx_rb.exception)
                )
            finally:
                lock_handle.release()

    def test_08_independent_postcheck_destination_comparison(self) -> None:
        """Case (8): independent check re-derives expected destinations from pre-switch snapshot."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_private_target_customized(
                tpath, aw_home, xdg_home
            )

            # Re-derive expected destinations from repo snapshot before switch
            records_root = repo / ".aw" / "records"
            expected_records = {}
            for p in records_root.rglob("*"):
                if p.is_file() and p.name not in ("INDEX.json", "INDEX.md"):
                    rel = p.relative_to(records_root).as_posix()
                    sha, _, _ = _calc_file_meta(p)
                    expected_records[rel] = sha

            durable_root = repo / ".aw" / "state" / "durable"
            expected_durable = {}
            for p in durable_root.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(durable_root).as_posix()
                    if rel == "install.json" or rel.startswith("history/"):
                        sha, _, _ = _calc_file_meta(p)
                        expected_durable[rel] = sha

            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)
            result = execute_placement_switch(repo, pol_local, aw_home=aw_home)
            self.assertTrue(result.receipt_path.is_file())

            dest_records_root = aw_home / "projects" / pid / "records"
            actual_records = {}
            for p in sorted(dest_records_root.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(dest_records_root).as_posix()
                    sha, _, _ = _calc_file_meta(p)
                    actual_records[rel] = sha

            self.assertEqual(
                sorted(expected_records.keys()),
                sorted(actual_records.keys()),
            )
            for k in expected_records:
                self.assertEqual(expected_records[k], actual_records[k])

            dest_durable_root = aw_home / "projects" / pid / "state" / "durable"
            for rel, expected_sha in sorted(expected_durable.items()):
                p = dest_durable_root / rel
                self.assertTrue(p.is_file(), f"Missing durable destination: {p}")
                act_sha, _, _ = _calc_file_meta(p)
                self.assertEqual(expected_sha, act_sha)

    def test_09_existing_journal_blocks_fresh_execute(self) -> None:
        """Case (9): existing journal blocks fresh execute_placement_switch."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env, pid = self._setup_private_target_customized(
                tpath, aw_home, xdg_home
            )
            pol_local = self._make_policy(Preset.LOCAL_ONLY.value, aw_home=aw_home)

            with self.assertRaises(PlacementSwitchError):
                execute_placement_switch(
                    repo, pol_local, aw_home=aw_home, fault_injection="after-copy"
                )

            with self.assertRaises(PlacementSwitchError) as ctx:
                execute_placement_switch(repo, pol_local, aw_home=aw_home)

            msg = str(ctx.exception)
            self.assertIn("resume", msg.lower())
            self.assertIn("rollback", msg.lower())
