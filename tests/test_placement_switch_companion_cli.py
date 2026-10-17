"""End-to-end CLI tests for companion placement switches (IPD y1e2m9 / Set cmpreloc)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows.placement_switch import (
    _calc_file_meta,
    _canonical_path,
    _derive_project_id,
    checkout_main_root,
)

pytestmark = pytest.mark.slow


def _take_working_tree_snapshot(
    dir_path: Path,
) -> dict[str, tuple[str | None, int | None, int | None]]:
    """Capture relative path -> (sha256, size, mode) ignoring .git directory."""
    snap: dict[str, tuple[str | None, int | None, int | None]] = {}
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


class _ScratchWorld:
    """Isolated scratch environment for CLI companion tests."""

    def __init__(self, root: Path, repo_root: str) -> None:
        self.root = root
        self.repo_root = repo_root
        self.aw_home = root / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        self.xdg_home = root / "xdg"
        self.xdg_home.mkdir(parents=True, exist_ok=True)
        self.target = root / "target"
        self.companion = root / "companion"
        self.env = dict(
            os.environ,
            PYTHONPATH=f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(root),
            AW_HOME=str(self.aw_home),
            XDG_CONFIG_HOME=str(self.xdg_home),
            GIT_AUTHOR_NAME="Test User",
            GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test User",
            GIT_COMMITTER_EMAIL="test@example.com",
            GIT_OPTIONAL_LOCKS="0",
        )

    def git(self, cwd: Path, *args: str, check: bool = True) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=self.env,
            capture_output=True,
            text=True,
        )
        if check and res.returncode != 0:
            raise AssertionError(
                f"git {args} in {cwd} failed: {res.stdout}\n{res.stderr}"
            )
        return res.stdout

    def git_status(self, cwd: Path) -> str:
        return self.git(cwd, "status", "--porcelain")

    def rev_count(self, cwd: Path) -> str:
        res = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(cwd),
            env=self.env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            return "0"
        return res.stdout.strip()

    def derive_project_id(self) -> str:
        anchor = self.target
        try:
            if (self.target / ".git").exists():
                anchor = checkout_main_root(self.target) or self.target
        except (OSError, RuntimeError):
            anchor = self.target
        return _derive_project_id(_canonical_path(anchor))

    def init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, "init", "-b", "main")
        self.git(path, "config", "user.name", "Test User")
        self.git(path, "config", "user.email", "test@example.com")
        self.git(path, "commit", "--allow-empty", "-m", "init")

    def install_target_private(self) -> None:
        self.init_repo(self.target)
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                str(self.target),
                "--preset",
                "private-target",
                "-y",
                "--no-interactive",
            ],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            raise AssertionError(
                f"install private-target failed: {r.stdout}\n{r.stderr}"
            )
        rec = self.target / ".aw" / "records" / "backlog" / "open" / "item.backlog.md"
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text("# Item\n", encoding="utf-8")
        self.git(self.target, "add", ".")
        self.git(self.target, "commit", "-m", "commit item")

    def init_companion(self) -> None:
        self.init_repo(self.companion)


class TestPlacementSwitchCompanionCLI(unittest.TestCase):
    """End-to-end CLI tests for companion placement switches."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = str(Path(__file__).resolve().parent.parent)

    def _make_scratch(self, root: Path) -> _ScratchWorld:
        return _ScratchWorld(root, self.repo_root)

    def test_cli_relocate_companion_dry_run_prints_preview(self) -> None:
        """(1) Relocate companion dry-run prints preview and makes no filesystem changes."""
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()
            scratch.init_companion()

            target_snap_before = _take_working_tree_snapshot(scratch.target)
            comp_snap_before = _take_working_tree_snapshot(scratch.companion)
            home_snap_before = _take_working_tree_snapshot(scratch.aw_home)

            cmd = [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                str(scratch.target),
                "--preset",
                "public-target-private-companion",
                "--companion-dir",
                str(scratch.companion),
                "--relocate",
                "--dry-run",
                "-y",
                "--no-interactive",
            ]
            r = subprocess.run(
                cmd,
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 0, f"dry-run failed: {r.stdout}\n{r.stderr}")
            out = r.stdout + r.stderr
            self.assertIn("[DRY RUN]", out)
            self.assertIn("Companion directory: " + str(scratch.companion), out)
            self.assertIn("Companion action:    attach", out)
            self.assertIn("records/ will be created", out)
            self.assertIn("Staged counts per repository:", out)
            self.assertIn("target:", out)
            self.assertIn("companion:", out)
            self.assertIn(
                "config-becomes-untracked: project.json becomes untracked in the target",
                out,
            )
            self.assertIn("records-leave-target-history:", out)

            # Assert no filesystem changes occurred
            self.assertEqual(
                target_snap_before, _take_working_tree_snapshot(scratch.target)
            )
            self.assertEqual(
                comp_snap_before, _take_working_tree_snapshot(scratch.companion)
            )
            self.assertEqual(
                home_snap_before, _take_working_tree_snapshot(scratch.aw_home)
            )

    def test_cli_relocate_companion_execute_attaches_and_stages(self) -> None:
        """(2) Relocate companion execute attaches companion, moves records, and stages changes in both repos without committing."""
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()
            scratch.init_companion()

            target_revs_before = scratch.rev_count(scratch.target)
            comp_revs_before = scratch.rev_count(scratch.companion)

            cmd = [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                str(scratch.target),
                "--preset",
                "public-target-private-companion",
                "--companion-dir",
                str(scratch.companion),
                "--relocate",
                "-y",
                "--no-interactive",
            ]
            r = subprocess.run(
                cmd,
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r.returncode, 0, f"relocate failed: {r.stdout}\n{r.stderr}"
            )

            # Inspect target and companion git status: records moved and staged without committing
            target_status = scratch.git_status(scratch.target)
            comp_status = scratch.git_status(scratch.companion)

            # Target git status has staged deletions for records
            self.assertTrue(
                any(
                    line.startswith("D ") and ".aw/records" in line
                    for line in target_status.splitlines()
                )
            )
            # Companion git status has staged additions for records
            self.assertTrue(
                any(
                    line.startswith("A ") and "records" in line
                    for line in comp_status.splitlines()
                )
            )

            # Verify no commit was made (HEAD rev counts unchanged)
            self.assertEqual(target_revs_before, scratch.rev_count(scratch.target))
            self.assertEqual(comp_revs_before, scratch.rev_count(scratch.companion))

            # Inspect project.json in target to prove companion attachment and updated placement
            target_proj = scratch.target / ".aw" / "config" / "project.json"
            self.assertTrue(target_proj.exists())
            proj_data = json.loads(target_proj.read_text(encoding="utf-8"))
            self.assertEqual(proj_data.get("preset"), "public-target-private-companion")
            self.assertEqual(proj_data.get("records_backend"), "companion")

            # Inspect aw path records: proves records resolve to companion
            path_r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "path",
                    "records",
                    "--repo",
                    str(scratch.target),
                    "--agent",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(path_r.returncode, 0)
            expected_records_path = str((scratch.companion / "records").resolve())
            self.assertIn(expected_records_path, path_r.stdout.strip())

    def test_cli_relocate_from_companion_to_target_executed(self) -> None:
        """(3) Relocate from companion to target moves records to target, stages in target, and retains companion repo in place."""
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()
            scratch.init_companion()

            # First relocate to companion
            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--companion-dir",
                    str(scratch.companion),
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 0)

            # Commit staged and untracked changes in both repos so working trees are clean for next switch
            scratch.git(scratch.target, "commit", "-q", "-m", "commit target deletions")
            scratch.git(scratch.companion, "add", "-A")
            scratch.git(
                scratch.companion, "commit", "-q", "-m", "commit companion additions"
            )

            # Add an extra record in companion to verify it moves
            comp_rec = (
                scratch.companion / "records" / "backlog" / "open" / "c_item.backlog.md"
            )
            comp_rec.write_text("# Companion Item\n", encoding="utf-8")
            scratch.git(scratch.companion, "add", "-A")
            scratch.git(scratch.companion, "commit", "-q", "-m", "add extra record")

            # Now relocate back to private-target
            r_back = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "private-target",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_back.returncode,
                0,
                f"switch to private-target failed: {r_back.stdout}\n{r_back.stderr}",
            )

            # Records moved to target
            target_rec = (
                scratch.target
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "c_item.backlog.md"
            )
            self.assertTrue(
                target_rec.exists(), "Record should exist in target .aw/records"
            )

            # Target git has records staged as added (A)
            target_status = scratch.git_status(scratch.target)
            self.assertTrue(
                any(
                    line.startswith("A ") and "c_item.backlog.md" in line
                    for line in target_status.splitlines()
                )
            )

            # Companion repository was detached but retained in place
            self.assertTrue(
                scratch.companion.exists(), "Companion directory must still exist"
            )
            self.assertTrue(
                (scratch.companion / ".git").exists(), "Companion git must still exist"
            )

            # project.json updated to private-target
            target_proj = scratch.target / ".aw" / "config" / "project.json"
            proj_data = json.loads(target_proj.read_text(encoding="utf-8"))
            self.assertEqual(proj_data.get("preset"), "private-target")
            self.assertEqual(proj_data.get("records_backend"), "repository")

    def test_cli_relocate_from_companion_to_home_executed(self) -> None:
        """(4) Relocate from companion to home moves records to AW_HOME, stages in target, and retains companion repo."""
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()
            scratch.init_companion()

            # Relocate to companion
            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--companion-dir",
                    str(scratch.companion),
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 0)

            # Commit staged and untracked changes
            scratch.git(scratch.target, "commit", "-q", "-m", "commit target deletions")
            scratch.git(scratch.companion, "add", "-A")
            scratch.git(
                scratch.companion, "commit", "-q", "-m", "commit companion additions"
            )

            # Relocate from companion to completely-clean-target
            r_home = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "completely-clean-target",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_home.returncode,
                0,
                f"switch to completely-clean-target failed: {r_home.stdout}\n{r_home.stderr}",
            )

            # Records moved to AW_HOME
            pid = scratch.derive_project_id()
            home_record = (
                scratch.aw_home
                / "projects"
                / pid
                / "records"
                / "backlog"
                / "open"
                / "item.backlog.md"
            )
            self.assertTrue(
                home_record.exists(),
                "Record should exist in AW_HOME projects/<pid>/records",
            )

            # Companion detached and retained in place
            self.assertTrue(scratch.companion.exists())
            self.assertTrue((scratch.companion / ".git").exists())

            # Target git staged changes: in-tree project.json removed from target
            self.assertFalse(
                (scratch.target / ".aw" / "config" / "project.json").exists()
            )

    def test_cli_relocate_resume_and_rollback_cli(self) -> None:
        """(5) Relocate resume and rollback CLI flags for companion transactions."""
        driver_code = """
import sys
from agent_workflows.install_wizard import resolve_policy_noninteractive, resolve_existing_policy
from agent_workflows.placement_switch import execute_placement_switch

repo = sys.argv[1]
companion = sys.argv[2]
fault = sys.argv[3]
existing = resolve_existing_policy(repo)
policy = resolve_policy_noninteractive(
    repo,
    existing_policy=existing,
    explicit_preset="public-target-private-companion",
    explicit_companion=companion,
    allow_placement_switch=True,
)
execute_placement_switch(repo, policy, fault_injection=fault)
"""
        # Part A: fault after-switch -> --relocate-resume
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()
            scratch.init_companion()

            r_fault = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    driver_code,
                    str(scratch.target),
                    str(scratch.companion),
                    "after-switch",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_fault.returncode, 0)

            # Refuses normal install naming --relocate-resume
            r_refuse = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--companion-dir",
                    str(scratch.companion),
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_refuse.returncode, 1)
            self.assertIn("--relocate-resume", r_refuse.stdout + r_refuse.stderr)

            # Resume succeeds
            r_res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--relocate-resume",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_res.returncode, 0, f"resume failed: {r_res.stdout}\n{r_res.stderr}"
            )

            # Verify companion has records
            self.assertTrue(
                (
                    scratch.companion
                    / "records"
                    / "backlog"
                    / "open"
                    / "item.backlog.md"
                ).exists()
            )

        # Part B: fault after-copy -> --relocate-rollback
        with tempfile.TemporaryDirectory() as td2:
            scratch2 = self._make_scratch(Path(td2))
            scratch2.install_target_private()
            scratch2.init_companion()

            r_fault2 = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    driver_code,
                    str(scratch2.target),
                    str(scratch2.companion),
                    "after-copy",
                ],
                env=scratch2.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_fault2.returncode, 0)

            # Rollback succeeds
            r_rb = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch2.target),
                    "--relocate-rollback",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch2.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_rb.returncode, 0, f"rollback failed: {r_rb.stdout}\n{r_rb.stderr}"
            )

            # Target still has records
            self.assertTrue(
                (
                    scratch2.target
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "item.backlog.md"
                ).exists()
            )
            # Companion does not have records
            self.assertFalse((scratch2.companion / "records").exists())

    def test_cli_companion_dir_validation(self) -> None:
        """(6) Companion dir validation: missing, nonexistent, or non-git directory refuses."""
        with tempfile.TemporaryDirectory() as td:
            scratch = self._make_scratch(Path(td))
            scratch.install_target_private()

            # 6a: without --companion-dir
            r_no_dir = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_no_dir.returncode, 1)
            self.assertIn("--companion-dir", r_no_dir.stdout + r_no_dir.stderr)

            # 6b: nonexistent path resolving inside target
            nested = scratch.target / "nested-comp"
            r_nonexistent = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--companion-dir",
                    str(nested),
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_nonexistent.returncode, 1)
            out_nested = r_nonexistent.stdout + r_nonexistent.stderr
            self.assertTrue(
                "companion-preflight" in out_nested
                or "cannot resolve inside target repo" in out_nested,
                f"Expected preflight refusal for nested companion path: {out_nested}",
            )

            # 6c: invalid git repo (directory exists but not a git repo)
            not_git = Path(td) / "not_git_dir"
            not_git.mkdir()
            r_not_git = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(scratch.target),
                    "--preset",
                    "public-target-private-companion",
                    "--companion-dir",
                    str(not_git),
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=scratch.env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_not_git.returncode, 1)
            out_not_git = r_not_git.stdout + r_not_git.stderr
            self.assertTrue(
                "companion-not-git" in out_not_git
                or "not the top of its own git repository" in out_not_git,
                f"Expected companion-not-git refusal for non-git directory: {out_not_git}",
            )


if __name__ == "__main__":
    unittest.main()
