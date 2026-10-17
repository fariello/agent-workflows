"""Companion-pair execution tests for placement switch (IPD fo08zx / Set cmpreloc).

Comprehensive test coverage for companion placement switches:
- Case (0): without allow_companion, execute_placement_switch refuses naming companion-unsupported.
- Case (1): happy paths for representative pairs (a), (b), (c), (d).
- Case (2): resume across all fault points for pairs (a) and (c).
- Case (3): rollback pre-sources-removed across all fault points for pairs (a) and (d).
- Case (4): companion-dirty blocker cleanly refuses with nothing written.
- Case (5): conflicting companion_identity.json refuses naming companion-preflight.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional

import pytest

from agent_workflows.install_wizard import ProjectPolicy, get_preset_defaults
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
    resolve_project_context,
)
from agent_workflows.project_schema import Preset

pytestmark = pytest.mark.slow

COMP = Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
PRIV = Preset.PRIVATE_TARGET.value
LOCAL = Preset.LOCAL_ONLY.value
CLEAN = Preset.COMPLETELY_CLEAN_TARGET.value

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
RECORD_REL = "backlog/open/x.backlog.md"
RUNS_REL = "runs/r1/state.json"


def _take_tree_snapshot(root: Path) -> dict[str, str]:
    """Capture relative path -> sha256 for all files outside .git directories."""
    snap: dict[str, str] = {}
    if not root.exists():
        return snap
    for p in sorted(root.rglob("*")):
        if ".git" in p.parts:
            continue
        if p.is_file():
            sha, _, _ = _calc_file_meta(p)
            snap[p.relative_to(root).as_posix()] = sha or ""
    return snap


def _git_status(cwd: Path, env: dict[str, str]) -> str:
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _git_diff_cached(cwd: Path, env: dict[str, str]) -> str:
    res = subprocess.run(
        ["git", "diff", "--cached"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _rev_count(cwd: Path, env: dict[str, str]) -> str:
    res = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        res_all = subprocess.run(
            ["git", "rev-list", "--all", "--count"],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )
        if res_all.returncode == 0:
            return res_all.stdout.strip()
        return "0"
    return res.stdout.strip()


class _Scratch:
    """One scratch world: HOME, AW_HOME, XDG_CONFIG_HOME, a target repo, an optional companion."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.aw_home = root / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        (root / "xdg").mkdir(parents=True, exist_ok=True)
        self.repo = root / "repo"
        self.companion: Optional[Path] = None
        self.env: Dict[str, str] = dict(
            os.environ,
            PYTHONPATH=f"{REPO_ROOT}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(root),
            AW_HOME=str(self.aw_home),
            XDG_CONFIG_HOME=str(root / "xdg"),
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

    def rev_count(self, cwd: Path) -> str:
        return _rev_count(cwd, self.env)

    def init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, "init", "-q", "-b", "main")
        self.git(path, "config", "user.name", "Test User")
        self.git(path, "config", "user.email", "test@example.com")
        self.git(path, "commit", "-q", "--allow-empty", "-m", "init")

    def install(self, preset: str, companion: Optional[Path] = None) -> None:
        self.init_repo(self.repo)
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "install",
            str(self.repo),
            "--preset",
            preset,
            "-y",
            "--no-interactive",
        ]
        if preset == COMP:
            self.companion = companion or (self.root / "comp")
            cmd += ["--companion-dir", str(self.companion)]
        res = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        if res.returncode != 0:
            raise AssertionError(f"installer failed: {res.stdout}\n{res.stderr}")

    def commit_companion(self, message: str = "companion") -> None:
        assert self.companion is not None
        self.git(self.companion, "add", "-A")
        self.git(self.companion, "commit", "-q", "-m", message)

    def derive_project_id(self) -> str:
        anchor = self.repo
        try:
            if (self.repo / ".git").exists():
                anchor = checkout_main_root(self.repo) or self.repo
        except (OSError, RuntimeError):
            anchor = self.repo
        return _derive_project_id(_canonical_path(anchor))

    def project_json_path(self, preset: str) -> Path:
        if preset in (PRIV, COMP):
            return self.repo / ".aw" / "config" / "project.json"
        pid = self.derive_project_id()
        return self.aw_home / "projects" / pid / "config" / "project.json"

    def customize_project_json(self, preset: str) -> None:
        proj_p = self.project_json_path(preset)
        data = json.loads(proj_p.read_text(encoding="utf-8"))
        data.setdefault("cutovers", {})["spec_id6"] = "2020-01-01"
        data["setids"] = {"warn_length": 10}
        proj_p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if preset == PRIV:
            self.git(self.repo, "add", "--", str(proj_p))
            self.git(self.repo, "commit", "-q", "-m", "customize project.json")

    def records_root(self, preset: str) -> Path:
        if preset == COMP:
            assert self.companion is not None
            return self.companion / "records"
        if preset == PRIV:
            return self.repo / ".aw" / "records"
        pid = self.derive_project_id()
        return self.aw_home / "projects" / pid / "records"

    def add_user_record(self, preset: str) -> Path:
        rec = self.records_root(preset) / RECORD_REL
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text("# Backlog item x\n", encoding="utf-8")
        if preset == COMP:
            self.commit_companion("add user record")
        elif preset == PRIV:
            self.git(self.repo, "add", "--", str(rec))
            self.git(self.repo, "commit", "-q", "-m", "add user record")
        return rec

    def add_runs_file(self, preset: str) -> Path:
        runs_f = self.records_root(preset) / RUNS_REL
        runs_f.parent.mkdir(parents=True, exist_ok=True)
        runs_f.write_text('{"state": "ok"}\n', encoding="utf-8")
        return runs_f

    def policy(
        self, preset: str, companion_dir: Optional[Path] = None
    ) -> ProjectPolicy:
        pls, gps, dm, rb, ds = get_preset_defaults(preset)
        return ProjectPolicy(
            preset=preset,
            role="target",
            delivery_mode=dm,
            records_backend=rb,
            durability_state=ds,
            aw_home=str(self.aw_home),
            companion_dir=str(companion_dir) if companion_dir is not None else None,
        )


class TestPlacementSwitchCompanionExecute(unittest.TestCase):
    """Behavioral tests for companion placement switch execution, resume, and rollback."""

    def test_case_0_without_allow_companion_refuses(self) -> None:
        """Case (0): without allow_companion, execute_placement_switch refuses naming companion-unsupported."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(PRIV)
            s.customize_project_json(PRIV)
            s.add_user_record(PRIV)
            comp = s.root / "comp"
            pol = s.policy(COMP, companion_dir=comp)

            pre_repo_snap = _take_tree_snapshot(s.repo)
            pre_aw_home_snap = _take_tree_snapshot(s.aw_home)
            pre_repo_status = _git_status(s.repo, s.env)

            with self.assertRaises(PlacementSwitchError) as ctx:
                execute_placement_switch(s.repo, pol, aw_home=s.aw_home)

            self.assertIn("companion-unsupported", str(ctx.exception))
            self.assertFalse(comp.exists())
            self.assertEqual(pre_repo_snap, _take_tree_snapshot(s.repo))
            self.assertEqual(pre_aw_home_snap, _take_tree_snapshot(s.aw_home))
            self.assertEqual(pre_repo_status, _git_status(s.repo, s.env))
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_1_happy_path_pair_a(self) -> None:
        """Case (1)(a): private-target -> companion with nonexistent companion path."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(PRIV)
            s.customize_project_json(PRIV)
            s.add_user_record(PRIV)
            s.add_runs_file(PRIV)
            comp = s.root / "comp"
            self.assertFalse(comp.exists())
            pol = s.policy(COMP, companion_dir=comp)

            rev_target_before = s.rev_count(s.repo)

            result = execute_placement_switch(
                s.repo, pol, aw_home=s.aw_home, allow_companion=True
            )

            # 1. Exactly one project.json for the project
            all_projs = (
                list(s.repo.rglob("project.json"))
                + list(s.aw_home.rglob("project.json"))
                + list(comp.rglob("project.json"))
            )
            self.assertEqual(len(all_projs), 1, f"Found project.json: {all_projs}")
            self.assertEqual(
                all_projs[0].resolve(),
                (s.repo / ".aw" / "config" / "project.json").resolve(),
            )

            # 2. project_config_dir and resolve_project_context
            pcd = project_config_dir(s.repo, aw_home=s.aw_home)
            self.assertEqual(pcd.resolve(), (s.repo / ".aw" / "config").resolve())
            ctx = resolve_project_context(
                target_repo=str(s.repo), aw_home=str(s.aw_home)
            )
            self.assertEqual(ctx.preset, COMP)
            self.assertEqual(
                Path(ctx.physical_classes["records"]).resolve(),
                (comp / "records").resolve(),
            )

            # 3. Customized keys preserved
            proj_data = json.loads(all_projs[0].read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_data.get("setids", {}).get("warn_length"), 10)

            # 4. x.backlog.md byte-identical at destination and staged A in destination repo
            dest_rec = comp / "records" / RECORD_REL
            self.assertTrue(dest_rec.is_file())
            self.assertEqual(dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n")
            comp_diff = s.git(comp, "diff", "--cached", "--name-status")
            self.assertIn(f"A\trecords/{RECORD_REL}", comp_diff)

            # 5. Source removal staged D in source repo
            target_diff = s.git(s.repo, "diff", "--cached", "--name-status")
            self.assertIn(f"D\t.aw/records/{RECORD_REL}", target_diff)

            # 6. git rev-list --count HEAD unchanged in BOTH repositories
            self.assertEqual(s.rev_count(s.repo), rev_target_before)
            self.assertEqual(s.rev_count(comp), "0")

            # 7. records/runs/r1/state.json present at destination and NOT staged
            dest_runs = comp / "records" / RUNS_REL
            self.assertTrue(dest_runs.is_file())
            comp_staged_names = s.git(
                comp, "diff", "--cached", "--name-only"
            ).splitlines()
            self.assertNotIn(f"records/{RUNS_REL}", comp_staged_names)

            # 8. companion identity present with project_id and NOT in diff --cached
            comp_id_file = comp / ".aw" / "companion_identity.json"
            self.assertTrue(comp_id_file.is_file())
            comp_id_data = json.loads(comp_id_file.read_text(encoding="utf-8"))
            self.assertEqual(comp_id_data.get("project_id"), s.derive_project_id())
            self.assertNotIn(".aw/companion_identity.json", comp_staged_names)

            # 9. companion_attachment.json present
            attach_file = (
                s.repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            self.assertTrue(attach_file.is_file())

            # 10. For (a) project.json untracked D in git index but still on disk
            proj_diff = s.git(
                s.repo,
                "diff",
                "--cached",
                "--name-status",
                "--",
                ".aw/config/project.json",
            )
            self.assertIn("D\t.aw/config/project.json", proj_diff)
            self.assertTrue((s.repo / ".aw" / "config" / "project.json").is_file())

            # 11. Receipt present, control dir gone
            self.assertTrue(result.receipt_path.is_file())
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_1_happy_path_pair_b(self) -> None:
        """Case (1)(b): companion -> private-target."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(COMP)
            s.commit_companion()
            s.customize_project_json(COMP)
            s.add_user_record(COMP)
            # Ensure companion .gitignore ignores records/runs/ so writing state.json leaves working tree clean
            comp_gi = s.companion / ".gitignore"
            gi_content = comp_gi.read_text(encoding="utf-8") if comp_gi.exists() else ""
            if "records/runs/" not in gi_content:
                comp_gi.write_text(gi_content + "\nrecords/runs/\n", encoding="utf-8")
                s.commit_companion("ignore runs in companion")
            s.add_runs_file(COMP)

            rev_target_before = s.rev_count(s.repo)
            rev_comp_before = s.rev_count(s.companion)

            pol = s.policy(PRIV)
            result = execute_placement_switch(
                s.repo, pol, aw_home=s.aw_home, allow_companion=True
            )

            # 1. Exactly one project.json
            all_projs = (
                list(s.repo.rglob("project.json"))
                + list(s.aw_home.rglob("project.json"))
                + list(s.companion.rglob("project.json"))
            )
            self.assertEqual(len(all_projs), 1)
            self.assertEqual(
                all_projs[0].resolve(),
                (s.repo / ".aw" / "config" / "project.json").resolve(),
            )

            # 2. project_config_dir and resolve_project_context
            pcd = project_config_dir(s.repo, aw_home=s.aw_home)
            self.assertEqual(pcd.resolve(), (s.repo / ".aw" / "config").resolve())
            ctx = resolve_project_context(
                target_repo=str(s.repo), aw_home=str(s.aw_home)
            )
            self.assertEqual(ctx.preset, PRIV)
            self.assertEqual(
                Path(ctx.physical_classes["records"]).resolve(),
                (s.repo / ".aw" / "records").resolve(),
            )

            # 3. Customized keys
            proj_data = json.loads(all_projs[0].read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_data.get("setids", {}).get("warn_length"), 10)

            # 4. x.backlog.md at destination and staged A in target repo
            dest_rec = s.repo / ".aw" / "records" / RECORD_REL
            self.assertTrue(dest_rec.is_file())
            self.assertEqual(dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n")
            target_diff = s.git(s.repo, "diff", "--cached", "--name-status")
            self.assertIn(f"A\t.aw/records/{RECORD_REL}", target_diff)

            # 5. Source removal staged D in companion repo
            comp_diff = s.git(s.companion, "diff", "--cached", "--name-status")
            self.assertIn(f"D\trecords/{RECORD_REL}", comp_diff)

            # 6. rev counts unchanged
            self.assertEqual(s.rev_count(s.repo), rev_target_before)
            self.assertEqual(s.rev_count(s.companion), rev_comp_before)

            # 7. runs file present at destination and not staged in target
            dest_runs = s.repo / ".aw" / "records" / RUNS_REL
            self.assertTrue(dest_runs.is_file())
            target_staged_names = s.git(
                s.repo, "diff", "--cached", "--name-only"
            ).splitlines()
            self.assertNotIn(f".aw/records/{RUNS_REL}", target_staged_names)

            # 8. companion_attachment.json absent after detach, companion dir and .git remain
            attach_file = (
                s.repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            self.assertFalse(attach_file.exists())
            self.assertTrue(s.companion.is_dir())
            self.assertTrue((s.companion / ".git").is_dir())

            # 9. receipt present, control dir gone
            self.assertTrue(result.receipt_path.is_file())
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_1_happy_path_pair_c(self) -> None:
        """Case (1)(c): companion -> local-only."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(COMP)
            s.commit_companion()
            s.customize_project_json(COMP)
            s.add_user_record(COMP)
            comp_gi = s.companion / ".gitignore"
            gi_content = comp_gi.read_text(encoding="utf-8") if comp_gi.exists() else ""
            if "records/runs/" not in gi_content:
                comp_gi.write_text(gi_content + "\nrecords/runs/\n", encoding="utf-8")
                s.commit_companion("ignore runs in companion")
            s.add_runs_file(COMP)

            rev_target_before = s.rev_count(s.repo)
            rev_comp_before = s.rev_count(s.companion)

            pid = s.derive_project_id()
            pol = s.policy(LOCAL)
            result = execute_placement_switch(
                s.repo, pol, aw_home=s.aw_home, allow_companion=True
            )

            # 1. Exactly one project.json
            all_projs = (
                list(s.repo.rglob("project.json"))
                + list(s.aw_home.rglob("project.json"))
                + list(s.companion.rglob("project.json"))
            )
            self.assertEqual(len(all_projs), 1)
            expected_proj = s.aw_home / "projects" / pid / "config" / "project.json"
            self.assertEqual(all_projs[0].resolve(), expected_proj.resolve())

            # 2. project_config_dir and resolve_project_context
            pcd = project_config_dir(s.repo, aw_home=s.aw_home)
            self.assertEqual(
                pcd.resolve(), (s.aw_home / "projects" / pid / "config").resolve()
            )
            ctx = resolve_project_context(
                target_repo=str(s.repo), aw_home=str(s.aw_home)
            )
            self.assertEqual(ctx.preset, LOCAL)
            self.assertEqual(
                Path(ctx.physical_classes["records"]).resolve(),
                (s.aw_home / "projects" / pid / "records").resolve(),
            )

            # 3. Customized keys
            proj_data = json.loads(all_projs[0].read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_data.get("setids", {}).get("warn_length"), 10)

            # 4. x.backlog.md at destination (aw_home)
            dest_rec = s.aw_home / "projects" / pid / "records" / RECORD_REL
            self.assertTrue(dest_rec.is_file())
            self.assertEqual(dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n")

            # 5. Source removal staged D in companion repo
            comp_diff = s.git(s.companion, "diff", "--cached", "--name-status")
            self.assertIn(f"D\trecords/{RECORD_REL}", comp_diff)

            # 6. rev counts unchanged
            self.assertEqual(s.rev_count(s.repo), rev_target_before)
            self.assertEqual(s.rev_count(s.companion), rev_comp_before)

            # 7. runs file at destination
            dest_runs = s.aw_home / "projects" / pid / "records" / RUNS_REL
            self.assertTrue(dest_runs.is_file())

            # 8. companion_attachment.json absent, companion and .git remain
            attach_file = (
                s.repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            self.assertFalse(attach_file.exists())
            self.assertTrue(s.companion.is_dir())
            self.assertTrue((s.companion / ".git").is_dir())

            # 9. receipt present, control dir gone
            self.assertTrue(result.receipt_path.is_file())
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_1_happy_path_pair_d(self) -> None:
        """Case (1)(d): local-only -> companion with existing empty committed companion."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(LOCAL)
            s.customize_project_json(LOCAL)
            s.add_user_record(LOCAL)
            s.add_runs_file(LOCAL)

            comp = s.root / "comp"
            s.init_repo(comp)
            rev_target_before = s.rev_count(s.repo)
            rev_comp_before = s.rev_count(comp)

            pol = s.policy(COMP, companion_dir=comp)
            result = execute_placement_switch(
                s.repo, pol, aw_home=s.aw_home, allow_companion=True
            )

            # 1. Exactly one project.json
            all_projs = (
                list(s.repo.rglob("project.json"))
                + list(s.aw_home.rglob("project.json"))
                + list(comp.rglob("project.json"))
            )
            self.assertEqual(len(all_projs), 1)
            self.assertEqual(
                all_projs[0].resolve(),
                (s.repo / ".aw" / "config" / "project.json").resolve(),
            )

            # 2. project_config_dir and resolve_project_context
            pcd = project_config_dir(s.repo, aw_home=s.aw_home)
            self.assertEqual(pcd.resolve(), (s.repo / ".aw" / "config").resolve())
            ctx = resolve_project_context(
                target_repo=str(s.repo), aw_home=str(s.aw_home)
            )
            self.assertEqual(ctx.preset, COMP)
            self.assertEqual(
                Path(ctx.physical_classes["records"]).resolve(),
                (comp / "records").resolve(),
            )

            # 3. Customized keys
            proj_data = json.loads(all_projs[0].read_text(encoding="utf-8"))
            self.assertEqual(
                proj_data.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_data.get("setids", {}).get("warn_length"), 10)

            # 4. x.backlog.md at destination and staged A in companion
            dest_rec = comp / "records" / RECORD_REL
            self.assertTrue(dest_rec.is_file())
            self.assertEqual(dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n")
            comp_diff = s.git(comp, "diff", "--cached", "--name-status")
            self.assertIn(f"A\trecords/{RECORD_REL}", comp_diff)

            # 5. rev counts unchanged
            self.assertEqual(s.rev_count(s.repo), rev_target_before)
            self.assertEqual(s.rev_count(comp), rev_comp_before)

            # 6. runs file present at destination and not staged
            dest_runs = comp / "records" / RUNS_REL
            self.assertTrue(dest_runs.is_file())
            comp_staged_names = s.git(
                comp, "diff", "--cached", "--name-only"
            ).splitlines()
            self.assertNotIn(f"records/{RUNS_REL}", comp_staged_names)

            # 7. companion identity present with project_id and not in diff --cached
            comp_id_file = comp / ".aw" / "companion_identity.json"
            self.assertTrue(comp_id_file.is_file())
            comp_id_data = json.loads(comp_id_file.read_text(encoding="utf-8"))
            self.assertEqual(comp_id_data.get("project_id"), s.derive_project_id())
            self.assertNotIn(".aw/companion_identity.json", comp_staged_names)

            # 8. companion_attachment.json present
            attach_file = (
                s.repo / ".aw" / "state" / "durable" / "companion_attachment.json"
            )
            self.assertTrue(attach_file.is_file())

            # 9. receipt present, control dir gone
            self.assertTrue(result.receipt_path.is_file())
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_2_resume_all_fault_points_pair_a(self) -> None:
        """Case (2): all fault points in pair (a) resume to Case (1)(a) end state."""
        fault_points = [
            "after-copy",
            "mid-verify",
            "mid-companion-stage",
            "after-attach",
            "after-switch",
            "mid-source-removal",
            "before-retire",
        ]
        for fp in fault_points:
            with tempfile.TemporaryDirectory() as td:
                s = _Scratch(Path(td))
                s.install(PRIV)
                s.customize_project_json(PRIV)
                s.add_user_record(PRIV)
                s.add_runs_file(PRIV)
                comp = s.root / "comp"
                pol = s.policy(COMP, companion_dir=comp)

                with self.assertRaises(PlacementSwitchError) as ctx:
                    execute_placement_switch(
                        s.repo,
                        pol,
                        aw_home=s.aw_home,
                        fault_injection=fp,
                        allow_companion=True,
                    )
                self.assertIn(f"Fault injected: {fp}", str(ctx.exception))

                status = placement_switch_status(s.repo, aw_home=s.aw_home)
                self.assertIsNotNone(status)

                res = resume_placement_switch(s.repo, aw_home=s.aw_home)
                self.assertTrue(res.receipt_path.is_file())

                all_projs = (
                    list(s.repo.rglob("project.json"))
                    + list(s.aw_home.rglob("project.json"))
                    + list(comp.rglob("project.json"))
                )
                self.assertEqual(len(all_projs), 1)
                pcd = project_config_dir(s.repo, aw_home=s.aw_home)
                self.assertEqual(pcd.resolve(), (s.repo / ".aw" / "config").resolve())
                ctx_pc = resolve_project_context(
                    target_repo=str(s.repo), aw_home=str(s.aw_home)
                )
                self.assertEqual(ctx_pc.preset, COMP)
                dest_rec = comp / "records" / RECORD_REL
                self.assertTrue(dest_rec.is_file())
                self.assertEqual(
                    dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n"
                )
                pid = s.derive_project_id()
                self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_2_resume_all_fault_points_pair_c(self) -> None:
        """Case (2): all fault points in pair (c) resume to Case (1)(c) end state."""
        fault_points = [
            "after-copy",
            "mid-verify",
            "mid-companion-stage",
            "after-attach",
            "after-switch",
            "mid-source-removal",
            "before-retire",
        ]
        for fp in fault_points:
            with tempfile.TemporaryDirectory() as td:
                s = _Scratch(Path(td))
                s.install(COMP)
                s.commit_companion()
                s.customize_project_json(COMP)
                s.add_user_record(COMP)
                comp_gi = s.companion / ".gitignore"
                gi_content = (
                    comp_gi.read_text(encoding="utf-8") if comp_gi.exists() else ""
                )
                if "records/runs/" not in gi_content:
                    comp_gi.write_text(
                        gi_content + "\nrecords/runs/\n", encoding="utf-8"
                    )
                    s.commit_companion("ignore runs in companion")
                s.add_runs_file(COMP)

                pid = s.derive_project_id()
                pol = s.policy(LOCAL)

                with self.assertRaises(PlacementSwitchError) as ctx:
                    execute_placement_switch(
                        s.repo,
                        pol,
                        aw_home=s.aw_home,
                        fault_injection=fp,
                        allow_companion=True,
                    )
                self.assertIn(f"Fault injected: {fp}", str(ctx.exception))

                status = placement_switch_status(s.repo, aw_home=s.aw_home)
                self.assertIsNotNone(status)

                res = resume_placement_switch(s.repo, aw_home=s.aw_home)
                self.assertTrue(res.receipt_path.is_file())

                all_projs = (
                    list(s.repo.rglob("project.json"))
                    + list(s.aw_home.rglob("project.json"))
                    + list(s.companion.rglob("project.json"))
                )
                self.assertEqual(len(all_projs), 1)
                pcd = project_config_dir(s.repo, aw_home=s.aw_home)
                self.assertEqual(
                    pcd.resolve(), (s.aw_home / "projects" / pid / "config").resolve()
                )
                ctx_pc = resolve_project_context(
                    target_repo=str(s.repo), aw_home=str(s.aw_home)
                )
                self.assertEqual(ctx_pc.preset, LOCAL)
                dest_rec = s.aw_home / "projects" / pid / "records" / RECORD_REL
                self.assertTrue(dest_rec.is_file())
                self.assertEqual(
                    dest_rec.read_text(encoding="utf-8"), "# Backlog item x\n"
                )
                self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_3_rollback_pre_sources_removed_pair_a(self) -> None:
        """Case (3): pre-sources-removed fault points in pair (a) rollback to pre-switch snapshot."""
        fault_points = [
            "after-copy",
            "mid-verify",
            "mid-companion-stage",
            "after-attach",
            "after-switch",
        ]
        for fp in fault_points:
            with tempfile.TemporaryDirectory() as td:
                s = _Scratch(Path(td))
                s.install(PRIV)
                s.customize_project_json(PRIV)
                s.add_user_record(PRIV)
                s.add_runs_file(PRIV)
                comp = s.root / "comp"
                pol = s.policy(COMP, companion_dir=comp)

                pre_target_tree = _take_tree_snapshot(s.repo)
                pre_target_status = _git_status(s.repo, s.env)
                pre_target_diff = _git_diff_cached(s.repo, s.env)
                pre_target_proj_bytes = (
                    s.repo / ".aw" / "config" / "project.json"
                ).read_bytes()
                pre_aw_home_tree = _take_tree_snapshot(s.aw_home)

                with self.assertRaises(PlacementSwitchError):
                    execute_placement_switch(
                        s.repo,
                        pol,
                        aw_home=s.aw_home,
                        fault_injection=fp,
                        allow_companion=True,
                    )

                rollback_placement_switch(s.repo, aw_home=s.aw_home)

                self.assertEqual(_take_tree_snapshot(s.repo), pre_target_tree)
                self.assertEqual(_git_status(s.repo, s.env), pre_target_status)
                self.assertEqual(_git_diff_cached(s.repo, s.env), pre_target_diff)
                self.assertEqual(
                    (s.repo / ".aw" / "config" / "project.json").read_bytes(),
                    pre_target_proj_bytes,
                )
                self.assertEqual(_take_tree_snapshot(s.aw_home), pre_aw_home_tree)
                self.assertFalse(comp.exists())
                pid = s.derive_project_id()
                self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_3_rollback_pre_sources_removed_pair_d(self) -> None:
        """Case (3): pre-sources-removed fault points in pair (d) rollback to pre-switch snapshot."""
        fault_points = [
            "after-copy",
            "mid-verify",
            "mid-companion-stage",
            "after-attach",
            "after-switch",
        ]
        for fp in fault_points:
            with tempfile.TemporaryDirectory() as td:
                s = _Scratch(Path(td))
                s.install(LOCAL)
                s.customize_project_json(LOCAL)
                s.add_user_record(LOCAL)
                s.add_runs_file(LOCAL)
                comp = s.root / "comp"
                s.init_repo(comp)

                pre_target_tree = _take_tree_snapshot(s.repo)
                pre_target_status = _git_status(s.repo, s.env)
                pre_target_diff = _git_diff_cached(s.repo, s.env)
                pre_aw_home_tree = _take_tree_snapshot(s.aw_home)
                pre_comp_tree = _take_tree_snapshot(comp)
                pre_comp_status = _git_status(comp, s.env)
                pre_comp_diff = _git_diff_cached(comp, s.env)

                pol = s.policy(COMP, companion_dir=comp)

                with self.assertRaises(PlacementSwitchError):
                    execute_placement_switch(
                        s.repo,
                        pol,
                        aw_home=s.aw_home,
                        fault_injection=fp,
                        allow_companion=True,
                    )

                rollback_placement_switch(s.repo, aw_home=s.aw_home)

                self.assertEqual(_take_tree_snapshot(s.repo), pre_target_tree)
                self.assertEqual(_git_status(s.repo, s.env), pre_target_status)
                self.assertEqual(_git_diff_cached(s.repo, s.env), pre_target_diff)
                self.assertEqual(_take_tree_snapshot(s.aw_home), pre_aw_home_tree)

                self.assertEqual(_take_tree_snapshot(comp), pre_comp_tree)
                self.assertEqual(_git_status(comp, s.env), pre_comp_status)
                self.assertEqual(_git_diff_cached(comp, s.env), pre_comp_diff)
                self.assertFalse((comp / ".aw" / "config").exists())
                self.assertFalse((comp / ".aw" / "state" / "durable").exists())
                self.assertFalse((comp / ".gitignore").exists())
                pid = s.derive_project_id()
                self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_4_blocker_companion_dirty_refuses(self) -> None:
        """Case (4): blocker companion-dirty refuses cleanly with nothing written."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(PRIV)
            s.customize_project_json(PRIV)
            s.add_user_record(PRIV)

            comp = s.root / "comp"
            s.init_repo(comp)
            (comp / "stray.txt").write_text("untracked dirty file\n", encoding="utf-8")

            pre_repo_snap = _take_tree_snapshot(s.repo)
            pre_aw_home_snap = _take_tree_snapshot(s.aw_home)
            pol = s.policy(COMP, companion_dir=comp)

            with self.assertRaises(PlacementSwitchError) as ctx:
                execute_placement_switch(
                    s.repo, pol, aw_home=s.aw_home, allow_companion=True
                )
            self.assertIn("companion-dirty", str(ctx.exception))
            self.assertEqual(_take_tree_snapshot(s.repo), pre_repo_snap)
            self.assertEqual(_take_tree_snapshot(s.aw_home), pre_aw_home_snap)
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())

    def test_case_5_conflicting_companion_identity_refuses_preflight(self) -> None:
        """Case (5): conflicting companion_identity.json refuses naming companion-preflight."""
        with tempfile.TemporaryDirectory() as td:
            s = _Scratch(Path(td))
            s.install(LOCAL)
            s.customize_project_json(LOCAL)
            s.add_user_record(LOCAL)

            comp = s.root / "comp"
            s.init_repo(comp)
            comp_id_file = comp / ".aw" / "companion_identity.json"
            comp_id_file.parent.mkdir(parents=True, exist_ok=True)
            comp_id_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "project_id": "other-conflicting-project-id",
                        "git_common_dir_hash": "dummy",
                    }
                ),
                encoding="utf-8",
            )
            s.git(comp, "add", "-A")
            s.git(comp, "commit", "-q", "-m", "add conflicting identity")

            pre_repo_snap = _take_tree_snapshot(s.repo)
            pre_aw_home_snap = _take_tree_snapshot(s.aw_home)
            pol = s.policy(COMP, companion_dir=comp)

            with self.assertRaises(PlacementSwitchError) as ctx:
                execute_placement_switch(
                    s.repo, pol, aw_home=s.aw_home, allow_companion=True
                )
            self.assertIn("companion-preflight", str(ctx.exception))
            self.assertEqual(_take_tree_snapshot(s.repo), pre_repo_snap)
            self.assertEqual(_take_tree_snapshot(s.aw_home), pre_aw_home_snap)
            pid = s.derive_project_id()
            self.assertFalse((s.aw_home / "placement-switches" / pid).exists())
