"""End-to-end CLI tests for records-only root switches (IPD vv9ki4 / Set rbswitch).

Tests --relocate, --dry-run, --relocate-resume, and --relocate-rollback on records-only
backend changes where config directory is preserved but records root moves.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Tuple

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
) -> Dict[str, Tuple[str | None, int | None, int | None]]:
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


class TestRecordsRootSwitchCli(unittest.TestCase):
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

    def _derive_pid(self, repo: Path) -> str:
        anchor = repo
        try:
            if (repo / ".git").exists():
                anchor = checkout_main_root(repo) or repo
        except (OSError, RuntimeError):
            anchor = repo
        return _derive_project_id(_canonical_path(anchor))

    def _create_fixture_repo(
        self, tpath: Path, aw_home: Path, xdg_home: Path
    ) -> tuple[Path, dict[str, str]]:
        repo = tpath / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        env = self._make_env(tpath, aw_home, xdg_home)
        subprocess.run(
            ["git", "init", "-b", "main", str(repo)],
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(repo),
            check=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(repo),
            check=True,
            env=env,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=str(repo),
            check=True,
            env=env,
        )

        # Fresh install --preset private-target -y --no-interactive
        r = subprocess.run(
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
            timeout=120,
        )
        self.assertEqual(
            r.returncode, 0, f"Initial install failed: {r.stdout}\n{r.stderr}"
        )

        # Commit user record
        rec_file = repo / ".aw" / "records" / "backlog" / "mine.md"
        rec_file.parent.mkdir(parents=True, exist_ok=True)
        rec_file.write_text("# mine\n", encoding="utf-8")

        # Customize project.json
        proj_file = repo / ".aw" / "config" / "project.json"
        proj_data = json.loads(proj_file.read_text(encoding="utf-8"))
        proj_data.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        proj_file.write_text(json.dumps(proj_data, indent=2), encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(repo), check=True, env=env)
        subprocess.run(
            ["git", "commit", "-m", "add record and customize project.json"],
            cwd=str(repo),
            check=True,
            env=env,
        )
        return repo, env

    def test_case_1_backlog_repro_without_relocate_refuses(self) -> None:
        """(1) install <repo> --records-backend home -y --no-interactive exits 1, output contains --relocate, tree and home unchanged."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            tree_before = _take_working_tree_snapshot(repo)
            home_before = _take_working_tree_snapshot(aw_home)

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 1)
            output = r.stdout + r.stderr
            self.assertIn("--relocate", output)

            tree_after = _take_working_tree_snapshot(repo)
            home_after = _take_working_tree_snapshot(aw_home)
            self.assertEqual(tree_before, tree_after)
            self.assertEqual(home_before, home_after)

    def test_case_2_relocate_dry_run_previews_and_writes_nothing(self) -> None:
        """(2) --records-backend home --relocate --dry-run -y exits 0, output names records only, record count, and project.json, tree and home unchanged."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            tree_before = _take_working_tree_snapshot(repo)
            home_before = _take_working_tree_snapshot(aw_home)

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "--relocate",
                    "--dry-run",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 0, f"dry-run failed: {r.stdout}\n{r.stderr}")
            output = r.stdout + r.stderr
            self.assertIn("records only", output)
            self.assertIn("records", output)
            self.assertIn("project.json", output)
            self.assertIn("[DRY RUN]", output)

            tree_after = _take_working_tree_snapshot(repo)
            home_after = _take_working_tree_snapshot(aw_home)
            self.assertEqual(tree_before, tree_after)
            self.assertEqual(home_before, home_after)

    def test_case_3_relocate_execute_to_home(self) -> None:
        """(3) --records-backend home --relocate -y exits 0, moves records to home, stages deletions, installer commits project.json."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            pid = self._derive_pid(repo)
            orig_mine = (repo / ".aw" / "records" / "backlog" / "mine.md").read_bytes()

            pre_head = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=str(repo), env=env
                )
                .decode()
                .strip()
            )

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 0, f"install failed: {r.stdout}\n{r.stderr}")

            # mine.md byte-identical under home records and absent in-tree
            home_mine = aw_home / "projects" / pid / "records" / "backlog" / "mine.md"
            self.assertTrue(home_mine.is_file())
            self.assertEqual(home_mine.read_bytes(), orig_mine)
            self.assertFalse(
                (repo / ".aw" / "records" / "backlog" / "mine.md").exists()
            )

            # context --json reports home records root and records_backend: home
            r_ctx = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "context",
                    "--json",
                    "--repo",
                    str(repo),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                r_ctx.returncode, 0, f"context failed: {r_ctx.stdout}\n{r_ctx.stderr}"
            )
            ctx_data = json.loads(r_ctx.stdout)
            self.assertEqual(ctx_data["data"]["records_backend"], "home")
            expected_root = str((aw_home / "projects" / pid / "records").resolve())
            self.assertEqual(
                str(Path(ctx_data["data"]["logical_roots"]["records"]).resolve()),
                expected_root,
            )

            # config dir still in-tree and 2020 cutover preserved
            proj_file = repo / ".aw" / "config" / "project.json"
            self.assertTrue(proj_file.is_file())
            proj_data = json.loads(proj_file.read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )

            # git diff --cached --name-status shows D for the record and nothing for project.json
            cached_diff = subprocess.check_output(
                ["git", "diff", "--cached", "--name-status"], cwd=str(repo), env=env
            ).decode()
            cached_lines = [
                line.split("\t") for line in cached_diff.splitlines() if line.strip()
            ]
            staged_actions = {
                parts[1]: parts[0] for parts in cached_lines if len(parts) >= 2
            }
            self.assertEqual(staged_actions.get(".aw/records/backlog/mine.md"), "D")
            self.assertNotIn(".aw/config/project.json", staged_actions)

            # every new commit since pre_head is 'agent-workflows: sync via installer' and names no path under .aw/records/
            new_commits = (
                subprocess.check_output(
                    ["git", "rev-list", f"{pre_head}..HEAD"], cwd=str(repo), env=env
                )
                .decode()
                .splitlines()
            )
            for c in new_commits:
                c = c.strip()
                if not c:
                    continue
                subj = (
                    subprocess.check_output(
                        ["git", "log", "-1", "--format=%s", c], cwd=str(repo), env=env
                    )
                    .decode()
                    .strip()
                )
                self.assertEqual(subj, "agent-workflows: sync via installer")
                changed = (
                    subprocess.check_output(
                        ["git", "show", "--name-only", "--format=", c],
                        cwd=str(repo),
                        env=env,
                    )
                    .decode()
                    .splitlines()
                )
                for f in changed:
                    self.assertFalse(f.strip().startswith(".aw/records/"))

            # aw find backlog mine finds the record
            r_find = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "find",
                    "backlog",
                    "mine",
                ],
                cwd=str(repo),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                r_find.returncode, 0, f"find failed: {r_find.stdout}\n{r_find.stderr}"
            )
            self.assertIn("mine", r_find.stdout)

    def test_case_4_reverse_relocate_to_target(self) -> None:
        """(4) on (3) after git commit -qm move, the reverse --records-backend repository --relocate -y returns record in-tree staged A."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            orig_mine = (repo / ".aw" / "records" / "backlog" / "mine.md").read_bytes()

            # Move to home first
            r1 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r1.returncode, 0)

            # Commit the deletions
            subprocess.run(
                ["git", "commit", "-qm", "move"], cwd=str(repo), check=True, env=env
            )

            # Reverse back to repository
            r2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "repository",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r2.returncode, 0, f"reverse install failed: {r2.stdout}\n{r2.stderr}"
            )

            # Record is back in-tree and staged A
            in_tree_mine = repo / ".aw" / "records" / "backlog" / "mine.md"
            self.assertTrue(in_tree_mine.is_file())
            self.assertEqual(in_tree_mine.read_bytes(), orig_mine)

            cached_diff = subprocess.check_output(
                ["git", "diff", "--cached", "--name-status"], cwd=str(repo), env=env
            ).decode()
            cached_lines = [
                line.split("\t") for line in cached_diff.splitlines() if line.strip()
            ]
            staged_actions = {
                parts[1]: parts[0] for parts in cached_lines if len(parts) >= 2
            }
            self.assertEqual(staged_actions.get(".aw/records/backlog/mine.md"), "A")

    def test_case_5_dirty_records_tree_refuses(self) -> None:
        """(5) a dirty .aw/records file with --relocate --dry-run exits 1 naming dirty-aw-tree."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            # Make .aw/records file dirty
            (repo / ".aw" / "records" / "backlog" / "mine.md").write_text(
                "# dirty\n", encoding="utf-8"
            )

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "--relocate",
                    "--dry-run",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 1)
            output = r.stdout + r.stderr
            self.assertIn("dirty-aw-tree", output)

    def test_case_6_recovery_resume_and_rollback(self) -> None:
        """(6) Recovery: fault_injection after-switch, guards refuse, resume completes; fault_injection after-copy, rollback restores pre-switch tree."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            pid = self._derive_pid(repo)
            orig_mine = (repo / ".aw" / "records" / "backlog" / "mine.md").read_bytes()

            driver_code = """
import sys
from agent_workflows.install_wizard import resolve_policy_noninteractive, resolve_existing_policy
from agent_workflows.placement_switch import execute_records_root_switch

repo = sys.argv[1]
fault = sys.argv[2]
existing = resolve_existing_policy(repo)
policy = resolve_policy_noninteractive(
    repo,
    existing_policy=existing,
    explicit_backend="home",
    allow_records_switch=True,
)
execute_records_root_switch(repo, policy, fault_injection=fault)
"""

            # 1. Trigger after-switch fault
            r_fault = subprocess.run(
                [sys.executable, "-c", driver_code, str(repo), "after-switch"],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_fault.returncode, 0)

            # plain install <repo> -y refuses naming --relocate-resume
            r_refuse = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_refuse.returncode, 1)
            self.assertIn("--relocate-resume", r_refuse.stdout + r_refuse.stderr)

            # install <repo> --relocate-resume -y exits 0 with end state of (3)
            r_resume = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--relocate-resume",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_resume.returncode,
                0,
                f"resume failed: {r_resume.stdout}\n{r_resume.stderr}",
            )
            home_mine = aw_home / "projects" / pid / "records" / "backlog" / "mine.md"
            self.assertTrue(home_mine.is_file())
            self.assertEqual(home_mine.read_bytes(), orig_mine)
            self.assertFalse(
                (repo / ".aw" / "records" / "backlog" / "mine.md").exists()
            )

        # 2. fault_injection="after-copy", rollback restores pre-switch tree and clean AW_HOME
        with tempfile.TemporaryDirectory() as td2:
            tpath2 = Path(td2)
            aw_home2 = tpath2 / "aw_home"
            aw_home2.mkdir()
            xdg_home2 = tpath2 / "xdg"
            xdg_home2.mkdir()

            repo2, env2 = self._create_fixture_repo(tpath2, aw_home2, xdg_home2)
            pid2 = self._derive_pid(repo2)
            tree_before = _take_working_tree_snapshot(repo2)

            r_fault2 = subprocess.run(
                [sys.executable, "-c", driver_code, str(repo2), "after-copy"],
                env=env2,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_fault2.returncode, 0)

            # Rollback
            r_rb = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo2),
                    "--relocate-rollback",
                    "-y",
                    "--no-interactive",
                ],
                env=env2,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_rb.returncode, 0, f"rollback failed: {r_rb.stdout}\n{r_rb.stderr}"
            )

            tree_after = _take_working_tree_snapshot(repo2)
            self.assertEqual(tree_before, tree_after)

            home_records = aw_home2 / "projects" / pid2 / "records"
            if home_records.exists():
                rec_files = [p for p in home_records.rglob("*") if p.is_file()]
                self.assertEqual(rec_files, [])

    def test_case_7_declined_relocation(self) -> None:
        """(7) a declined relocation (--relocate --no-interactive without -y) exits non-zero, nothing written."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            tree_before = _take_working_tree_snapshot(repo)
            home_before = _take_working_tree_snapshot(aw_home)

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "--relocate",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r.returncode, 0)

            tree_after = _take_working_tree_snapshot(repo)
            home_after = _take_working_tree_snapshot(aw_home)
            self.assertEqual(tree_before, tree_after)
            self.assertEqual(home_before, home_after)

    def test_case_8_companion_relocate_dry_run_refuses(self) -> None:
        """(8) --records-backend companion --relocate --dry-run refuses naming n9vd2h and not suggesting --relocate."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "companion",
                    "--relocate",
                    "--dry-run",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r.returncode, 1)
            output = r.stdout + r.stderr
            self.assertIn("n9vd2h", output)
            self.assertNotIn("Preview with --relocate", output)

    def test_case_9_scaffold_only_backend_switch_allowed(self) -> None:
        """(9) a repo with scaffold only: --records-backend home -y (no --relocate) exits 0 as a plain update (Order 01 OQ-01)."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo = tpath / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            env = self._make_env(tpath, aw_home, xdg_home)
            subprocess.run(
                ["git", "init", "-b", "main", str(repo)],
                check=True,
                env=env,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=str(repo),
                check=True,
                env=env,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=str(repo),
                check=True,
                env=env,
            )
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "init"],
                cwd=str(repo),
                check=True,
                env=env,
            )

            # Fresh install with scaffold only (no user records committed)
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
                timeout=120,
            )
            self.assertEqual(r_init.returncode, 0)

            # Update records backend without --relocate
            r_up = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--records-backend",
                    "home",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(
                r_up.returncode,
                0,
                f"scaffold-only update failed: {r_up.stdout}\n{r_up.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
