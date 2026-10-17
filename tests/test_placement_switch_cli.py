"""End-to-end CLI tests for config placement switch (IPD ozr356 / Set cfgreloc)."""

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


class TestPlacementSwitchCLI(unittest.TestCase):
    """End-to-end tests for aw install --relocate, preview, and recovery."""

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
        rec_file = repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
        rec_file.parent.mkdir(parents=True, exist_ok=True)
        rec_file.write_text("# Backlog Item X\n", encoding="utf-8")

        # Customize project.json
        proj_file = repo / ".aw" / "config" / "project.json"
        proj_data = json.loads(proj_file.read_text(encoding="utf-8"))
        proj_data.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        proj_data["run"] = {"retry_budget": 3}
        proj_data["setids"] = {"warn_length": 10}
        proj_file.write_text(json.dumps(proj_data, indent=2), encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(repo), check=True, env=env)
        subprocess.run(
            ["git", "commit", "-m", "add record and customize project.json"],
            cwd=str(repo),
            check=True,
            env=env,
        )
        return repo, env

    def test_case_1_reinstall_cross_placement_without_relocate_refuses(self) -> None:
        """(1) --preset local-only -y without --relocate on committed private-target repo -> exit 1, tree and home unchanged."""
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
                    "--preset",
                    "local-only",
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
            self.assertIn("Switching config placement", output)

            tree_after = _take_working_tree_snapshot(repo)
            home_after = _take_working_tree_snapshot(aw_home)
            self.assertEqual(tree_before, tree_after)
            self.assertEqual(home_before, home_after)

    def test_case_2_relocate_dry_run(self) -> None:
        """(2) --preset local-only --relocate --dry-run -y -> exit 0, lists config_project, record count, staged-deletion count, tree and home unchanged."""
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
                    "--preset",
                    "local-only",
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
            self.assertIn("[DRY RUN]", output)
            self.assertIn("config_project", output)
            self.assertIn("records", output)
            self.assertIn("Tracked target files that will be staged as removed", output)

            tree_after = _take_working_tree_snapshot(repo)
            home_after = _take_working_tree_snapshot(aw_home)
            self.assertEqual(tree_before, tree_after)
            self.assertEqual(home_before, home_after)

    def test_case_3_relocate_execute_to_home(self) -> None:
        """(3) --preset local-only --relocate -y -> exit 0; exactly one project.json, readers agree, keys preserved, record in home, etc."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            pid = self._derive_pid(repo)

            rev_count_before = (
                subprocess.check_output(
                    ["git", "rev-list", "--count", "HEAD"], cwd=str(repo), env=env
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
                    "--preset",
                    "local-only",
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
                r.returncode, 0, f"relocate failed: {r.stdout}\n{r.stderr}"
            )

            # 1. Exactly one project.json (home, none in repo)
            in_tree_proj = repo / ".aw" / "config" / "project.json"
            home_proj = aw_home / "projects" / pid / "config" / "project.json"
            self.assertFalse(in_tree_proj.exists())
            self.assertTrue(home_proj.exists())

            # 2. aw-level readers agree
            r_ctx = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "context",
                    "--json",
                ],
                cwd=str(repo),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            ctx_data = json.loads(r_ctx.stdout)
            inner_data = ctx_data.get("data", ctx_data)
            self.assertEqual(inner_data.get("preset"), Preset.LOCAL_ONLY.value)
            config_proj_path = inner_data.get("physical_classes", {}).get(
                "config_project"
            )
            self.assertEqual(Path(config_proj_path).resolve(), home_proj.resolve())

            # 3. Customized keys and cutover preserved
            proj_data = json.loads(home_proj.read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_data.get("run"), {"retry_budget": 3})
            self.assertEqual(proj_data.get("setids"), {"warn_length": 10})

            # 4. User record present under home records root
            home_record = (
                aw_home
                / "projects"
                / pid
                / "records"
                / "backlog"
                / "open"
                / "x.backlog.md"
            )
            self.assertTrue(home_record.exists())

            # 5. git ls-files .aw empty
            ls_res = subprocess.check_output(
                ["git", "ls-files", "--", ".aw"], cwd=str(repo), env=env
            ).decode()
            self.assertEqual(ls_res.strip(), "")

            # 6. Any file left under .aw/ named PRESERVED in switch receipt
            receipt_path = (
                aw_home
                / "projects"
                / pid
                / "state"
                / "durable"
                / "migrations"
                / "placement_switch_receipt.json"
            )
            self.assertTrue(receipt_path.exists())
            receipt_data = json.loads(receipt_path.read_text(encoding="utf-8"))

            remaining_aw_files = [p for p in (repo / ".aw").rglob("*") if p.is_file()]
            for rf in remaining_aw_files:
                rel = rf.relative_to(repo).as_posix()
                # Check that it is acknowledged as PRESERVED or in retire_actions
                preserved_found = any(
                    rel in act and "PRESERVED" in act
                    for act in receipt_data.get("retire_actions", [])
                )
                self.assertTrue(
                    preserved_found,
                    f"Remaining file {rel} not recorded as PRESERVED in receipt: {receipt_data.get('retire_actions')}",
                )

            # 7. Every staged entry D except M on AGENTS.md and .gitignore
            st_res = (
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=str(repo), env=env
                )
                .decode()
                .splitlines()
            )
            for line in st_res:
                if not line.strip():
                    continue
                code = line[:2]
                path_part = line[3:].strip()
                if path_part in ("AGENTS.md", ".gitignore"):
                    self.assertIn("M", code, f"Expected M on {path_part}, got {line}")
                else:
                    self.assertIn("D", code, f"Expected D on {path_part}, got {line}")

            # 8. git rev-list --count HEAD unchanged
            rev_count_after = (
                subprocess.check_output(
                    ["git", "rev-list", "--count", "HEAD"], cwd=str(repo), env=env
                )
                .decode()
                .strip()
            )
            self.assertEqual(rev_count_before, rev_count_after)

    def test_case_4_reverse_relocate_to_target(self) -> None:
        """(4) Reverse switch: dirty-aw-tree refusal before commit, then commit, then reverse switch succeeds."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            pid = self._derive_pid(repo)

            # First switch to local-only
            r1 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "local-only",
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

            # Running reverse switch BEFORE committing staged deletions trips dirty-aw-tree
            r_rev_dirty = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
                    "--relocate",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_rev_dirty.returncode, 1)
            self.assertIn("dirty-aw-tree", r_rev_dirty.stdout + r_rev_dirty.stderr)

            # Documented operator step: commit the staged deletions
            subprocess.run(
                ["git", "commit", "-q", "-m", "switch"],
                cwd=str(repo),
                check=True,
                env=env,
            )

            # Now run reverse switch
            r_rev = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
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
                r_rev.returncode,
                0,
                f"reverse switch failed: {r_rev.stdout}\n{r_rev.stderr}",
            )

            # In-tree authoritative config
            in_tree_proj = repo / ".aw" / "config" / "project.json"
            self.assertTrue(in_tree_proj.exists())

            # Records back in .aw/records/ (staged A)
            in_tree_record = (
                repo / ".aw" / "records" / "backlog" / "open" / "x.backlog.md"
            )
            self.assertTrue(in_tree_record.exists())

            st_res = (
                subprocess.check_output(
                    ["git", "status", "--porcelain", "--", ".aw/records"],
                    cwd=str(repo),
                    env=env,
                )
                .decode()
                .splitlines()
            )
            staged_a_found = any(
                line.startswith("A ") and "x.backlog.md" in line for line in st_res
            )
            self.assertTrue(
                staged_a_found,
                f"Expected staged A for record in git status: {st_res}",
            )

            # Home project dir has no config/, system/, state/
            home_project_dir = aw_home / "projects" / pid
            self.assertFalse((home_project_dir / "config").exists())
            self.assertFalse((home_project_dir / "system").exists())
            self.assertFalse((home_project_dir / "state").exists())

    def test_case_5_dirty_records_trips_dirty_aw_tree(self) -> None:
        """(5) --preset completely-clean-target --relocate --dry-run on a dirty .aw/records file -> exit 1 naming dirty-aw-tree."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)

            dirty_file = repo / ".aw" / "records" / "uncommitted.txt"
            dirty_file.write_text("dirty uncommitted\n", encoding="utf-8")

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "completely-clean-target",
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
        """(6) Recovery: fault_injection after-switch, guards refuse, resume completes; fault_injection after-copy, rollback restores; no journal exit 1."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)
            pid = self._derive_pid(repo)

            driver_code = """
import sys
from agent_workflows.install_wizard import resolve_policy_noninteractive, resolve_existing_policy
from agent_workflows.placement_switch import execute_placement_switch

repo = sys.argv[1]
fault = sys.argv[2]
existing = resolve_existing_policy(repo)
policy = resolve_policy_noninteractive(
    repo,
    existing_policy=existing,
    explicit_preset="local-only",
    allow_placement_switch=True,
)
execute_placement_switch(repo, policy, fault_injection=fault)
"""

            # Trigger after-switch fault
            r_fault = subprocess.run(
                [sys.executable, "-c", driver_code, str(repo), "after-switch"],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_fault.returncode, 0)

            # 1. install <repo> --preset local-only -y refuses naming --relocate-resume
            r_refuse = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "local-only",
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

            # 2. install all -y with repo in scratch config allowlist reports failed naming --relocate-resume
            config_file = xdg_home / "agent-workflows" / "config.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps({"repos": [str(repo)]}), encoding="utf-8")

            r_all = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    "all",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertNotEqual(r_all.returncode, 0)
            self.assertIn("--relocate-resume", r_all.stdout + r_all.stderr)

            # 3. install <repo> --relocate-resume -y exits 0 with end state of (3)
            r_res = subprocess.run(
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
                r_res.returncode, 0, f"resume failed: {r_res.stdout}\n{r_res.stderr}"
            )

            in_tree_proj = repo / ".aw" / "config" / "project.json"
            home_proj = aw_home / "projects" / pid / "config" / "project.json"
            self.assertFalse(in_tree_proj.exists())
            self.assertTrue(home_proj.exists())

        # 4. fault_injection="after-copy", --relocate-rollback restores pre-switch tree
        with tempfile.TemporaryDirectory() as td2:
            tpath2 = Path(td2)
            aw_home2 = tpath2 / "aw_home"
            aw_home2.mkdir()
            xdg_home2 = tpath2 / "xdg"
            xdg_home2.mkdir()

            repo2, env2 = self._create_fixture_repo(tpath2, aw_home2, xdg_home2)
            pid2 = self._derive_pid(repo2)
            tree_before = _take_working_tree_snapshot(repo2)

            # Trigger after-copy fault
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

            home_proj2 = aw_home2 / "projects" / pid2 / "config" / "project.json"
            self.assertFalse(home_proj2.exists())

            # 5. --relocate-resume with no journal exits 1
            r_no_j = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo2),
                    "--relocate-resume",
                    "-y",
                    "--no-interactive",
                ],
                env=env2,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_no_j.returncode, 1)
            self.assertIn(
                "no interrupted placement switch", r_no_j.stdout + r_no_j.stderr
            )

    def test_case_6b_declined_relocation(self) -> None:
        """(6b) A declined relocation: --preset local-only --relocate with --no-interactive and no -y exits non-zero, tree and home unchanged."""
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
                    "--preset",
                    "local-only",
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

    def test_case_6c_relocate_on_same_placement_is_normal_install(self) -> None:
        """(6c) --relocate on a same-placement request is a normal install (no switch, exit 0)."""
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
                    "--preset",
                    "private-target",
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

    def test_case_7_companion_target_refusals(self) -> None:
        """(7) Companion target: with --relocate --dry-run refuses naming companion-unsupported; without --relocate names n9vd2h and no --relocate."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()

            repo, env = self._create_fixture_repo(tpath, aw_home, xdg_home)

            # With --relocate --dry-run -> companion-unsupported
            r_reloc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "public-target-private-companion",
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
            self.assertEqual(r_reloc.returncode, 1)
            output_reloc = r_reloc.stdout + r_reloc.stderr
            self.assertIn("companion-unsupported", output_reloc)

            # Without --relocate -> names n9vd2h and does NOT contain --relocate
            r_plain = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "public-target-private-companion",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(r_plain.returncode, 1)
            output_plain = r_plain.stdout + r_plain.stderr
            self.assertIn("n9vd2h", output_plain)
            self.assertNotIn("--relocate", output_plain)
