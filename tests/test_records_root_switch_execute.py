"""Tests for records-only root switch planner and executor (IPD fxbm7j / Set rbswitch)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows.install_wizard import ProjectPolicy
from agent_workflows.placement_switch import (
    PlacementSwitchError,
    _calc_file_meta,
    _canonical_path,
    _derive_project_id,
    checkout_main_root,
    execute_placement_switch,
    execute_records_root_switch,
    placement_switch_status,
    plan_records_root_switch,
    resume_placement_switch,
    rollback_placement_switch,
)
from agent_workflows.project_context import (
    project_config_dir,
    resolve_project_context,
)
from agent_workflows.project_schema import Preset

pytestmark = pytest.mark.slow


def _take_working_tree_snapshot(
    dir_path: Path,
) -> dict[str, tuple[str | None, int | None, int | None]]:
    """Capture relative path -> (sha256, size, mode) ignoring .git directory."""
    snap = {}
    if not dir_path.exists():
        return snap
    for p in dir_path.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_file() or p.is_symlink():
            rel = p.relative_to(dir_path).as_posix()
            sha, size, mode = _calc_file_meta(p)
            snap[rel] = (sha, size, mode)
    return snap


class TestRecordsRootSwitchExecute(unittest.TestCase):
    """Behavioral tests for records root switch execution, recovery, and mutations."""

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
        extra_args: list[str] | None = None,
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
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "install",
            str(repo),
            "--preset",
            preset,
            "-y",
            "--no-interactive",
        ]
        if extra_args:
            cmd.extend(extra_args)
        r = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, f"installer failed: {r.stdout}\n{r.stderr}")
        return repo, env

    def _derive_pid(self, repo: Path) -> str:
        anchor = repo
        try:
            if (repo / ".git").exists():
                anchor = checkout_main_root(repo) or repo
        except (OSError, RuntimeError):
            anchor = repo
        return _derive_project_id(_canonical_path(anchor))

    def _setup_private_target_fixture(
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
            ["git", "commit", "-m", "fixture private target"],
            cwd=str(repo),
            env=env,
            check=True,
        )

        runs_file = repo / ".aw" / "records" / "runs" / "r1" / "state.json"
        runs_file.parent.mkdir(parents=True, exist_ok=True)
        runs_file.write_text('{"state": "running"}\n', encoding="utf-8")

        pid = self._derive_pid(repo)
        return repo, env, pid

    def _setup_home_records_fixture(
        self, tpath: Path, aw_home: Path, xdg_home: Path
    ) -> tuple[Path, dict[str, str], str]:
        repo, env = self._init_and_install_repo(
            tpath,
            aw_home,
            xdg_home,
            preset=Preset.PRIVATE_TARGET.value,
            extra_args=["--records-backend", "home"],
        )
        pid = self._derive_pid(repo)
        home_records = aw_home / "projects" / pid / "records"

        proj_path = repo / ".aw" / "config" / "project.json"
        d = json.loads(proj_path.read_text(encoding="utf-8"))
        d.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        d["run"] = {"retry_budget": 3}
        d["setids"] = {"warn_length": 10}
        proj_path.write_text(json.dumps(d, indent=2), encoding="utf-8")

        subprocess.run(
            ["git", "add", str(proj_path)],
            cwd=str(repo),
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "fixture home records"],
            cwd=str(repo),
            env=env,
            check=True,
        )

        backlog_file = home_records / "backlog" / "open" / "x.backlog.md"
        backlog_file.parent.mkdir(parents=True, exist_ok=True)
        backlog_file.write_text("# Backlog x\n", encoding="utf-8")

        runs_file = home_records / "runs" / "r1" / "state.json"
        runs_file.parent.mkdir(parents=True, exist_ok=True)
        runs_file.write_text('{"state": "running"}\n', encoding="utf-8")

        return repo, env, pid

    def test_01_records_to_home_happy_path(self) -> None:
        """(1) records-to-home happy path verification."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            proj_file = repo / ".aw" / "config" / "project.json"
            pre_proj_data = json.loads(proj_file.read_text(encoding="utf-8"))

            x_file = repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
            x_bytes = x_file.read_bytes()
            runs_file = repo / ".aw" / "records" / "runs" / "r1" / "state.json"
            runs_bytes = runs_file.read_bytes()

            rev_count_before = int(
                subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            )

            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            res = execute_records_root_switch(repo, policy, aw_home=aw_home)

            home_records = aw_home / "projects" / pid / "records"
            self.assertEqual(
                (home_records / "backlog/open/x.backlog.md").read_bytes(), x_bytes
            )
            self.assertEqual(
                (home_records / "runs/r1/state.json").read_bytes(), runs_bytes
            )

            # none left under repo/.aw/records except unplanned_leftovers named in receipt
            repo_records = repo / ".aw" / "records"
            if repo_records.exists():
                remaining = [
                    p.relative_to(repo).as_posix()
                    for p in repo_records.rglob("*")
                    if p.is_file()
                ]
                self.assertEqual(remaining, res.unplanned_leftovers)

            # project_config_dir unchanged (still in-tree)
            self.assertEqual(
                Path(project_config_dir(repo, aw_home=aw_home)).resolve(),
                (repo / ".aw" / "config").resolve(),
            )

            # project.json differs only in the 3 keys
            post_proj_data = json.loads(proj_file.read_text(encoding="utf-8"))
            self.assertEqual(post_proj_data["records_backend"], "home")
            self.assertEqual(post_proj_data["placements"]["records"], "home-untracked")
            self.assertEqual(post_proj_data["git_policies"]["records"], "untracked")

            pre_copy = json.loads(json.dumps(pre_proj_data))
            post_copy = json.loads(json.dumps(post_proj_data))
            pre_copy.pop("records_backend")
            post_copy.pop("records_backend")
            pre_copy["placements"].pop("records")
            post_copy["placements"].pop("records")
            pre_copy["git_policies"].pop("records")
            post_copy["git_policies"].pop("records")
            self.assertEqual(pre_copy, post_copy)

            # git diff --cached --name-status shows D for tracked records and M for project.json
            diff_proc = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            )
            diff_lines = [
                line.strip() for line in diff_proc.stdout.splitlines() if line.strip()
            ]
            self.assertIn("M\t.aw/config/project.json", diff_lines)
            for line in diff_lines:
                if line == "M\t.aw/config/project.json":
                    continue
                self.assertTrue(
                    line.startswith("D\t.aw/records/"),
                    f"Unexpected staged diff line: {line}",
                )

            # git rev-list --count HEAD unchanged
            rev_count_after = int(
                subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            )
            self.assertEqual(rev_count_before, rev_count_after)

            # receipt present, control dir gone
            self.assertTrue(res.receipt_path.exists())
            control_dir = aw_home / "placement-switches" / pid
            self.assertFalse(control_dir.exists())

    def test_02_records_to_target_happy_path(self) -> None:
        """(2) records-to-target happy path verification."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_home_records_fixture(tpath, aw_home, xdg_home)

            policy = ProjectPolicy(
                preset="private-target",
                records_backend="repository",
                aw_home=str(aw_home),
            )
            execute_records_root_switch(repo, policy, aw_home=aw_home)

            # in-tree records
            in_tree_x = repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
            self.assertTrue(in_tree_x.exists())

            # tracked ones staged A
            diff_proc = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=True,
            )
            diff_lines = [
                line.strip() for line in diff_proc.stdout.splitlines() if line.strip()
            ]
            self.assertIn("A\t.aw/records/backlog/open/x.backlog.md", diff_lines)

            # runs/r1/state.json present and ignored
            in_tree_runs = repo / ".aw" / "records" / "runs" / "r1" / "state.json"
            self.assertTrue(in_tree_runs.exists())
            ci_proc = subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "-q",
                    "--",
                    ".aw/records/runs/r1/state.json",
                ],
                cwd=str(repo),
                check=False,
            )
            self.assertEqual(ci_proc.returncode, 0)

            # home records holds no record files
            home_records = aw_home / "projects" / pid / "records"
            if home_records.exists():
                files = [p for p in home_records.rglob("*") if p.is_file()]
                self.assertEqual(files, [])

    def test_03_local_json_records_backend_rewritten_and_resolver_follows(
        self,
    ) -> None:
        """(3) local.json records_backend rewrite and resolver verification."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            local_json = repo / ".aw" / "config" / "local.json"
            local_data = {
                "schema_version": 2,
                "project_id": pid,
                "human_slug": "repo",
                "records_backend": "repository",
            }
            local_json.write_text(json.dumps(local_data, indent=2), encoding="utf-8")

            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            execute_records_root_switch(repo, policy, aw_home=aw_home)

            updated_local = json.loads(local_json.read_text(encoding="utf-8"))
            self.assertEqual(updated_local["records_backend"], "home")

            ctx = resolve_project_context(target_repo=str(repo), aw_home=aw_home)
            expected_home = (aw_home / "projects" / pid / "records").resolve()
            self.assertEqual(
                Path(ctx.logical_roots["records"]).resolve(), expected_home
            )

    def test_04_fault_points_resume_to_completed_state(self) -> None:
        """(4) Each fault point in each direction resumes to completion."""
        faults = ["after-copy", "mid-verify", "after-switch", "mid-source-removal"]
        # Direction: records-to-home
        for fault in faults:
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                xdg_home = tpath / "xdg"
                repo, env, pid = self._setup_private_target_fixture(
                    tpath, aw_home, xdg_home
                )

                policy = ProjectPolicy(
                    preset="private-target",
                    records_backend="home",
                    aw_home=str(aw_home),
                )
                with self.assertRaises(PlacementSwitchError):
                    execute_records_root_switch(
                        repo, policy, aw_home=aw_home, fault_injection=fault
                    )

                st = placement_switch_status(repo, aw_home=aw_home)
                self.assertIsNotNone(st)
                self.assertEqual(st.get("mode"), "records")

                res = resume_placement_switch(repo, aw_home=aw_home)
                self.assertEqual(res.direction, "records-to-home")
                home_records = aw_home / "projects" / pid / "records"
                self.assertTrue((home_records / "backlog/open/x.backlog.md").exists())

        # Direction: records-to-target
        for fault in faults:
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                xdg_home = tpath / "xdg"
                repo, env, pid = self._setup_home_records_fixture(
                    tpath, aw_home, xdg_home
                )

                policy = ProjectPolicy(
                    preset="private-target",
                    records_backend="repository",
                    aw_home=str(aw_home),
                )
                with self.assertRaises(PlacementSwitchError):
                    execute_records_root_switch(
                        repo, policy, aw_home=aw_home, fault_injection=fault
                    )

                st = placement_switch_status(repo, aw_home=aw_home)
                self.assertIsNotNone(st)
                self.assertEqual(st.get("mode"), "records")

                res = resume_placement_switch(repo, aw_home=aw_home)
                self.assertEqual(res.direction, "records-to-target")
                in_tree_x = (
                    repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
                )
                self.assertTrue(in_tree_x.exists())

    def test_05_pre_sources_removed_fault_points_rollback_byte_identical(
        self,
    ) -> None:
        """(5) Pre-sources-removed fault points roll back to a byte-identical repo."""
        faults = ["after-copy", "mid-verify", "after-switch"]
        for fault in faults:
            with tempfile.TemporaryDirectory() as td:
                tpath = Path(td)
                aw_home = tpath / "aw_home"
                xdg_home = tpath / "xdg"
                repo, env, pid = self._setup_private_target_fixture(
                    tpath, aw_home, xdg_home
                )

                snap_before = _take_working_tree_snapshot(repo)
                status_before = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                diff_before = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                policy = ProjectPolicy(
                    preset="private-target",
                    records_backend="home",
                    aw_home=str(aw_home),
                )
                with self.assertRaises(PlacementSwitchError):
                    execute_records_root_switch(
                        repo, policy, aw_home=aw_home, fault_injection=fault
                    )

                rollback_placement_switch(repo, aw_home=aw_home)

                snap_after = _take_working_tree_snapshot(repo)
                status_after = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                diff_after = subprocess.run(
                    ["git", "diff", "--cached"],
                    cwd=str(repo),
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                self.assertEqual(snap_before, snap_after)
                self.assertEqual(status_before, status_after)
                self.assertEqual(diff_before, diff_after)

                # aw_home has no new record files and control dir is deleted
                home_records = aw_home / "projects" / pid / "records"
                if home_records.exists():
                    self.assertEqual(
                        [p for p in home_records.rglob("*") if p.is_file()], []
                    )
                self.assertFalse((aw_home / "placement-switches" / pid).exists())

    def test_06_rollback_refused_after_mid_source_removal(self) -> None:
        """(6) Rollback refused after mid-source-removal naming resume."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            with self.assertRaises(PlacementSwitchError):
                execute_records_root_switch(
                    repo, policy, aw_home=aw_home, fault_injection="mid-source-removal"
                )

            with self.assertRaises(PlacementSwitchError) as exc_info:
                rollback_placement_switch(repo, aw_home=aw_home)

            msg = str(exc_info.exception)
            self.assertIn("past the point of no return", msg)
            self.assertIn("resume", msg)

    def test_07_blockers_refuse_cleanly(self) -> None:
        """(7) dirty-aw-tree, destination-not-empty, companion-unsupported blockers."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            # 1. dirty-aw-tree
            dirty_f = repo / ".aw" / "records" / "dirty.txt"
            dirty_f.write_text("dirty\n", encoding="utf-8")
            switches_dir = aw_home / "placement-switches"
            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )

            with self.assertRaises(PlacementSwitchError) as exc_info:
                execute_records_root_switch(repo, policy, aw_home=aw_home)
            self.assertIn("dirty-aw-tree", str(exc_info.exception))
            self.assertFalse(switches_dir.exists())
            dirty_f.unlink()

            # 2. destination-not-empty
            dest_file = (
                aw_home
                / "projects"
                / pid
                / "records"
                / "backlog"
                / "open"
                / "x.backlog.md"
            )
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text("different bytes\n", encoding="utf-8")

            with self.assertRaises(PlacementSwitchError) as exc_info:
                execute_records_root_switch(repo, policy, aw_home=aw_home)
            self.assertIn("destination-not-empty", str(exc_info.exception))
            dest_file.unlink()

            # 3. companion-unsupported
            comp_policy = ProjectPolicy(
                preset="private-target",
                records_backend="companion",
                aw_home=str(aw_home),
            )
            with self.assertRaises(PlacementSwitchError) as exc_info:
                execute_records_root_switch(repo, comp_policy, aw_home=aw_home)
            self.assertIn("companion-unsupported", str(exc_info.exception))

    def test_08_mutual_blocking_placement_and_records_modes(self) -> None:
        """(8) Existing journal of either mode blocks the other."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            # Placement switch leaves after-copy journal
            local_policy = ProjectPolicy(
                preset=Preset.LOCAL_ONLY.value,
                role="target",
                delivery_mode="clean-delta",
                records_backend="home",
                durability_state="transient",
                aw_home=str(aw_home),
            )
            with self.assertRaises(PlacementSwitchError):
                execute_placement_switch(
                    repo, local_policy, aw_home=aw_home, fault_injection="after-copy"
                )

            # Records switch blocked
            rec_policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            with self.assertRaises(PlacementSwitchError) as exc_info:
                execute_records_root_switch(repo, rec_policy, aw_home=aw_home)
            self.assertIn(
                "An incomplete placement switch transaction already exists",
                str(exc_info.exception),
            )

            rollback_placement_switch(repo, aw_home=aw_home)

            # Now records switch leaves after-copy journal
            with self.assertRaises(PlacementSwitchError):
                execute_records_root_switch(
                    repo, rec_policy, aw_home=aw_home, fault_injection="after-copy"
                )

            # Placement switch blocked
            with self.assertRaises(PlacementSwitchError) as exc_info:
                execute_placement_switch(repo, local_policy, aw_home=aw_home)
            self.assertIn(
                "An incomplete placement switch transaction already exists",
                str(exc_info.exception),
            )

            rollback_placement_switch(repo, aw_home=aw_home)

    def test_09_independent_postcheck_destination_comparison(self) -> None:
        """(9) Independent postcheck: re-derive expected destination set from pre-switch snapshot."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            old_records_root = repo / ".aw" / "records"
            scaffold_names = {".gitkeep", "README.md"}
            home_records_root = aw_home / "projects" / pid / "records"

            # Derive expected set
            expected_rels = set()
            for p in old_records_root.rglob("*"):
                if p.is_file() or p.is_symlink():
                    if p.name in ("INDEX.json", "INDEX.md"):
                        continue
                    rel = p.relative_to(old_records_root).as_posix()
                    dest_p = home_records_root / rel
                    if p.name in scaffold_names and dest_p.exists():
                        continue
                    expected_rels.add(rel)

            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            execute_records_root_switch(repo, policy, aw_home=aw_home)

            actual_rels = {
                p.relative_to(home_records_root).as_posix()
                for p in home_records_root.rglob("*")
                if p.is_file() or p.is_symlink()
            }
            self.assertEqual(expected_rels, actual_rels)

    def test_10_preexisting_destination_scaffold(self) -> None:
        """(10) Pre-existing destination scaffold becomes discard item and remains untouched."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            xdg_home = tpath / "xdg"
            repo, env, pid = self._setup_private_target_fixture(
                tpath, aw_home, xdg_home
            )

            source_scaffold = repo / ".aw" / "records" / "backlog" / "README.md"
            source_scaffold.write_text("# Default Backlog README\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", str(source_scaffold)], cwd=str(repo), check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "add source scaffold"],
                cwd=str(repo),
                check=True,
            )

            home_scaffold = (
                aw_home / "projects" / pid / "records" / "backlog" / "README.md"
            )
            home_scaffold.parent.mkdir(parents=True, exist_ok=True)
            custom_bytes = b"# Pre-existing Custom Backlog Scaffold\n"
            home_scaffold.write_bytes(custom_bytes)
            sha_before, _, _ = _calc_file_meta(home_scaffold)

            policy = ProjectPolicy(
                preset="private-target", records_backend="home", aw_home=str(aw_home)
            )
            plan = plan_records_root_switch(repo, policy, aw_home=aw_home)

            # plan shows that source as discard with no blocker
            discard_scaffolds = [
                it
                for it in plan.items
                if it.item_class == "records"
                and it.source.name == "README.md"
                and "backlog" in it.source.parts
            ]
            self.assertTrue(len(discard_scaffolds) >= 1)
            self.assertEqual(discard_scaffolds[0].kind, "discard")
            self.assertIsNone(discard_scaffolds[0].destination)
            self.assertEqual(plan.blockers, [])

            # after-copy rollback leaves that file byte-identical
            with self.assertRaises(PlacementSwitchError):
                execute_records_root_switch(
                    repo, policy, aw_home=aw_home, fault_injection="after-copy"
                )
            sha_after_copy, _, _ = _calc_file_meta(home_scaffold)
            self.assertEqual(sha_before, sha_after_copy)

            rollback_placement_switch(repo, aw_home=aw_home)
            sha_after_rollback, _, _ = _calc_file_meta(home_scaffold)
            self.assertEqual(sha_before, sha_after_rollback)

            # completed switch leaves that file byte-identical
            execute_records_root_switch(repo, policy, aw_home=aw_home)
            sha_after_complete, _, _ = _calc_file_meta(home_scaffold)
            self.assertEqual(sha_before, sha_after_complete)
            self.assertEqual(home_scaffold.read_bytes(), custom_bytes)


if __name__ == "__main__":
    unittest.main()
