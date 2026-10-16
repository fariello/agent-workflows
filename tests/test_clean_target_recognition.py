"""Outcome tests for clean-target project recognition (IPD fnnwj3).

Validates that:
(a) checkout_main_root correctly resolves main checkout roots and linked worktrees,
    and returns None for submodules, bare repos, separate-git-dirs, non-git and missing paths;
(b) home_configured_root returns True only for installed clean-delta roots and their linked
    worktrees, and False for subdirectories, tracked projects, uninstalled repos, and $HOME;
(b2) external lane shares project_config_dir and resolve_project_context(...).project_id with
    the main root, while tracked in-repo installs remain unchanged;
(c) find_project_root, is_project_dir, and classify_project_dir recognize clean-target roots,
    subdirectories, and external lanes (including when AW_HOME/config/ exists);
(d) negative controls (tracked in-repo, non-git .aw, nested uninstalled repo, submodule)
    remain identical to baseline;
(e) aw doctor --dir <root> --json reports layout "home (clean-target)", preset, and backend,
    and aw status --json lists root and lane (via cwd fallback with empty user config);
(f) aw attention --format json in external lane succeeds without no-project refusal, and
    aw context --agent reports the main root's project_id.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle
from agent_workflows.project_context import (
    ProjectLocationCase,
    checkout_main_root,
    classify_project_dir,
    find_project_root,
    home_configured_root,
    is_project_dir,
    project_config_dir,
    resolve_project_context,
)


class TestCleanTargetRecognition(unittest.TestCase):
    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()

        self.fake_home = self.base / "home"
        self.fake_home.mkdir()
        self.fake_aw_home = self.fake_home / ".aw"
        self.fake_aw_home.mkdir()
        self.fake_xdg = self.fake_home / ".config"
        self.fake_xdg.mkdir()

        self.repo_root = Path(__file__).resolve().parent.parent

        self._orig_env = dict(os.environ)
        os.environ["HOME"] = str(self.fake_home)
        os.environ["AW_HOME"] = str(self.fake_aw_home)
        os.environ["XDG_CONFIG_HOME"] = str(self.fake_xdg)
        os.environ["AW_NO_REEXEC"] = "1"
        os.environ["PYTHONPATH"] = (
            f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}"
        )
        os.environ.pop("AW_CONFIG_DIR", None)

        self.env = dict(os.environ)

        # Set up completely-clean-target fixture
        self.clean_repo = self.base / "clean_repo"
        self._init_git_repo(self.clean_repo)
        self._run_aw(
            "install",
            str(self.clean_repo),
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
            cwd=self.clean_repo,
        )
        self._strip_in_target_residue(self.clean_repo)
        self.clean_subdir = self.clean_repo / "sub" / "deep"
        self.clean_subdir.mkdir(parents=True)

        ctx_clean = resolve_project_context(
            target_repo=str(self.clean_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.clean_proj_id = ctx_clean.project_id
        self.clean_lane = (
            self.fake_aw_home / "projects" / self.clean_proj_id / "worktrees" / "abc123"
        )
        self.clean_lane.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.clean_repo),
                "worktree",
                "add",
                "--detach",
                str(self.clean_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.clean_lane_sub = self.clean_lane / "x"
        self.clean_lane_sub.mkdir()

        # Set up local-only fixture
        self.local_repo = self.base / "local_repo"
        self._init_git_repo(self.local_repo)
        self._run_aw(
            "install",
            str(self.local_repo),
            "--preset",
            "local-only",
            "-y",
            "--no-interactive",
            cwd=self.local_repo,
        )
        self._strip_in_target_residue(self.local_repo)
        ctx_local = resolve_project_context(
            target_repo=str(self.local_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.local_proj_id = ctx_local.project_id
        self.local_lane = (
            self.fake_aw_home / "projects" / self.local_proj_id / "worktrees" / "loc123"
        )
        self.local_lane.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.local_repo),
                "worktree",
                "add",
                "--detach",
                str(self.local_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )

        # Set up tracked in-repo fixture (private-target)
        self.tracked_repo = self.base / "tracked_repo"
        self._init_git_repo(self.tracked_repo)
        self._run_aw(
            "install",
            str(self.tracked_repo),
            "--preset",
            "private-target",
            "-y",
            "--no-interactive",
            cwd=self.tracked_repo,
        )
        self.tracked_lane = self.tracked_repo / "lane1"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.tracked_repo),
                "worktree",
                "add",
                str(self.tracked_lane),
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)
        self.tmp.cleanup()

    def _init_git_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(path)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "user.name", "Test User"],
            check=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "config", "user.email", "test@example.com"],
            check=True,
            env=self.env,
        )
        (path / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(path), "add", "README.md"], check=True, env=self.env
        )
        subprocess.run(
            ["git", "-C", str(path), "commit", "-m", "Initial commit"],
            check=True,
            capture_output=True,
            env=self.env,
        )

    def _strip_in_target_residue(self, path: Path) -> None:
        subprocess.run(
            ["git", "-C", str(path), "rm", "-r", "--cached", "."],
            check=True,
            capture_output=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "add", "README.md"], check=True, env=self.env
        )
        subprocess.run(
            ["git", "-C", str(path), "commit", "-m", "Clean residue"],
            check=True,
            capture_output=True,
            env=self.env,
        )
        subprocess.run(
            ["git", "-C", str(path), "clean", "-fdx"],
            check=True,
            capture_output=True,
            env=self.env,
        )

    def _run_aw(
        self, *args: str, cwd: Path | None = None, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        return subprocess.run(
            cmd,
            cwd=str(cwd or self.clean_repo),
            env=self.env,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_a_checkout_main_root_table(self) -> None:
        """(a) checkout_main_root table incl. submodule, bare, separate-git-dir -> None."""
        # 1. Main worktree
        self.assertEqual(checkout_main_root(self.clean_repo), self.clean_repo)
        # 2. Subdirectory of main
        self.assertEqual(checkout_main_root(self.clean_subdir), self.clean_repo)
        # 3. In-repo linked worktree
        self.assertEqual(checkout_main_root(self.tracked_lane), self.tracked_repo)
        # 4. External linked worktree
        self.assertEqual(checkout_main_root(self.clean_lane), self.clean_repo)
        # 5. Subdirectory of external lane
        self.assertEqual(checkout_main_root(self.clean_lane_sub), self.clean_repo)

        # 6. Submodule checkout -> None
        subm_parent = self.base / "subm_parent"
        self._init_git_repo(subm_parent)
        subprocess.run(
            [
                "git",
                "-c",
                "protocol.file.allow=always",
                "-C",
                str(subm_parent),
                "submodule",
                "add",
                str(self.clean_repo),
                "subm",
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )
        subm_dir = subm_parent / "subm"
        self.assertIsNone(checkout_main_root(subm_dir))

        # 7. Bare repo worktree -> None
        bare_repo = self.base / "bare.git"
        subprocess.run(
            ["git", "clone", "--bare", str(self.clean_repo), str(bare_repo)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        bare_wt = self.base / "bare_wt"
        subprocess.run(
            ["git", "-C", str(bare_repo), "worktree", "add", str(bare_wt)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertIsNone(checkout_main_root(bare_wt))

        # 8. Separate git dir -> None
        sep_wt = self.base / "sep_wt"
        sep_git = self.base / "sep.git"
        subprocess.run(
            ["git", "init", "--separate-git-dir", str(sep_git), str(sep_wt)],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertIsNone(checkout_main_root(sep_wt))

        # 9. Non-git directory -> None
        non_git = self.base / "non_git"
        non_git.mkdir()
        self.assertIsNone(checkout_main_root(non_git))

        # 10. Missing path -> None
        self.assertIsNone(checkout_main_root(self.base / "does_not_exist"))

    def test_b_home_configured_root_table(self) -> None:
        """(b) home_configured_root true/false table."""
        # True cases
        self.assertTrue(
            home_configured_root(self.clean_repo, aw_home=self.fake_aw_home)
        )
        self.assertTrue(
            home_configured_root(self.clean_lane, aw_home=self.fake_aw_home)
        )
        self.assertTrue(
            home_configured_root(self.local_repo, aw_home=self.fake_aw_home)
        )
        self.assertTrue(
            home_configured_root(self.local_lane, aw_home=self.fake_aw_home)
        )

        # False cases
        self.assertFalse(
            home_configured_root(self.clean_subdir, aw_home=self.fake_aw_home)
        )
        self.assertFalse(
            home_configured_root(self.clean_lane_sub, aw_home=self.fake_aw_home)
        )
        self.assertFalse(
            home_configured_root(self.tracked_repo, aw_home=self.fake_aw_home)
        )
        self.assertFalse(
            home_configured_root(self.fake_home, aw_home=self.fake_aw_home)
        )

        # Home project.json with delivery_mode: tracked -> False
        fake_proj = self.fake_aw_home / "projects" / "custom-tracked" / "config"
        fake_proj.mkdir(parents=True)
        (fake_proj / "project.json").write_text(
            json.dumps({"delivery_mode": "tracked"}), encoding="utf-8"
        )
        uninst_repo = self.base / "uninst_repo"
        self._init_git_repo(uninst_repo)
        self.assertFalse(home_configured_root(uninst_repo, aw_home=self.fake_aw_home))

    def test_b2_identity_table(self) -> None:
        """(b2) identity table: project_config_dir and project_id equal for root and lane."""
        clean_root_cfg = project_config_dir(self.clean_repo, aw_home=self.fake_aw_home)
        clean_lane_cfg = project_config_dir(self.clean_lane, aw_home=self.fake_aw_home)
        self.assertEqual(clean_lane_cfg, clean_root_cfg)

        ctx_root = resolve_project_context(
            target_repo=str(self.clean_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        ctx_lane = resolve_project_context(
            target_repo=str(self.clean_lane),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.assertEqual(ctx_lane.project_id, ctx_root.project_id)
        self.assertEqual(
            ctx_lane.delivery_mode.value
            if hasattr(ctx_lane.delivery_mode, "value")
            else str(ctx_lane.delivery_mode),
            "clean-delta",
        )

        # Tracked in-repo install unchanged
        tracked_root_cfg = project_config_dir(
            self.tracked_repo, aw_home=self.fake_aw_home
        )
        tracked_lane_cfg = project_config_dir(
            self.tracked_lane, aw_home=self.fake_aw_home
        )
        self.assertEqual(tracked_root_cfg, self.tracked_repo / ".aw" / "config")
        self.assertEqual(tracked_lane_cfg, self.tracked_lane / ".aw" / "config")
        ctx_t_root = resolve_project_context(
            target_repo=str(self.tracked_repo),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        ctx_t_lane = resolve_project_context(
            target_repo=str(self.tracked_lane),
            aw_home=str(self.fake_aw_home),
            user_config_dir=str(self.fake_xdg / "agent-workflows"),
        )
        self.assertEqual(
            ctx_t_root.delivery_mode.value
            if hasattr(ctx_t_root.delivery_mode, "value")
            else str(ctx_t_root.delivery_mode),
            "tracked",
        )
        self.assertEqual(
            ctx_t_lane.delivery_mode.value
            if hasattr(ctx_t_lane.delivery_mode, "value")
            else str(ctx_t_lane.delivery_mode),
            "tracked",
        )

    def test_c_predicate_table(self) -> None:
        """(c) predicate table for root, subdir, external lane and lane subdir."""
        # 1. Clean root
        self.assertTrue(is_project_dir(self.clean_repo))
        self.assertEqual(find_project_root(self.clean_repo), self.clean_repo)
        self.assertEqual(
            classify_project_dir(self.clean_repo).case,
            ProjectLocationCase.IS_PROJECT_ROOT,
        )

        # 2. Clean subdir
        self.assertFalse(is_project_dir(self.clean_subdir))
        self.assertEqual(find_project_root(self.clean_subdir), self.clean_repo)
        self.assertEqual(
            classify_project_dir(self.clean_subdir).case,
            ProjectLocationCase.INSIDE_PROJECT,
        )

        # 3. External lane
        self.assertTrue(is_project_dir(self.clean_lane))
        self.assertEqual(find_project_root(self.clean_lane), self.clean_lane)
        self.assertEqual(
            classify_project_dir(self.clean_lane).case,
            ProjectLocationCase.IS_PROJECT_ROOT,
        )

        # 4. External lane subdir
        self.assertFalse(is_project_dir(self.clean_lane_sub))
        self.assertEqual(find_project_root(self.clean_lane_sub), self.clean_lane)
        self.assertEqual(
            classify_project_dir(self.clean_lane_sub).case,
            ProjectLocationCase.INSIDE_PROJECT,
        )

        # Repeat with <AW_HOME>/config/ present (the $HOME-hazard case)
        (self.fake_aw_home / "config").mkdir(exist_ok=True)
        self.assertTrue(is_project_dir(self.clean_lane))
        self.assertEqual(find_project_root(self.clean_lane), self.clean_lane)
        self.assertEqual(find_project_root(self.clean_lane_sub), self.clean_lane)
        self.assertNotEqual(find_project_root(self.clean_lane), self.fake_home)
        self.assertNotEqual(find_project_root(self.clean_lane_sub), self.fake_home)

    def test_d_negative_controls(self) -> None:
        """(d) negative controls unchanged."""
        # 1. Tracked in-repo install
        self.assertTrue(is_project_dir(self.tracked_repo))
        self.assertEqual(find_project_root(self.tracked_repo), self.tracked_repo)
        self.assertEqual(
            classify_project_dir(self.tracked_repo).case,
            ProjectLocationCase.IS_PROJECT_ROOT,
        )

        # 2. Non-git .aw project
        non_git_aw = self.base / "non_git_aw"
        (non_git_aw / ".aw" / "records").mkdir(parents=True)
        self.assertTrue(is_project_dir(non_git_aw))
        self.assertEqual(find_project_root(non_git_aw), non_git_aw)
        self.assertEqual(
            classify_project_dir(non_git_aw).case, ProjectLocationCase.IS_PROJECT_ROOT
        )
        self.assertFalse(home_configured_root(non_git_aw, aw_home=self.fake_aw_home))

        # 3. Uninstalled git repo inside an AW project (stops at git boundary)
        nested_git = self.tracked_repo / "scratch" / "nested"
        self._init_git_repo(nested_git)
        self.assertIsNone(find_project_root(nested_git))
        self.assertFalse(is_project_dir(nested_git))

        # 4. Registered submodule without .aw resolves to parent project
        subm_parent = self.base / "subm_parent_aw"
        self._init_git_repo(subm_parent)
        (subm_parent / ".aw" / "records").mkdir(parents=True)
        subm_child = self.base / "subm_child"
        self._init_git_repo(subm_child)
        subprocess.run(
            [
                "git",
                "-c",
                "protocol.file.allow=always",
                "-C",
                str(subm_parent),
                "submodule",
                "add",
                str(subm_child),
                "child",
            ],
            check=True,
            capture_output=True,
            env=self.env,
        )
        self.assertEqual(find_project_root(subm_parent / "child"), subm_parent)

    def test_e_doctor_and_status_subprocesses(self) -> None:
        """(e) subprocess aw doctor --dir <root> --json and aw status --json."""
        # 1. aw doctor --dir <clean_repo> --json
        res_doc = self._run_aw(
            "doctor", "--dir", str(self.clean_repo), "--json", check=False
        )
        self.assertIn(res_doc.returncode, (0, 1), f"doctor stderr: {res_doc.stderr}")
        doc_json = json.loads(res_doc.stdout)
        env_data = doc_json["data"]["report"]["env"]
        self.assertEqual(env_data["layout"], "home (clean-target)")
        self.assertEqual(env_data["preset"], "completely-clean-target")
        self.assertEqual(env_data["backend"], "home")

        # 2. aw doctor --dir <tracked_repo> --json still reports layout ".aw"
        res_doc_tr = self._run_aw(
            "doctor", "--dir", str(self.tracked_repo), "--json", check=False
        )
        self.assertIn(
            res_doc_tr.returncode, (0, 1), f"doctor tracked stderr: {res_doc_tr.stderr}"
        )
        doc_tr_json = json.loads(res_doc_tr.stdout)
        self.assertEqual(doc_tr_json["data"]["report"]["env"]["layout"], ".aw")

        # 3. aw status --json with cwd = clean_repo
        res_st_root = self._run_aw("status", "--json", cwd=self.clean_repo)
        self.assertEqual(
            res_st_root.returncode, 0, f"status root stderr: {res_st_root.stderr}"
        )
        st_root_data = json.loads(res_st_root.stdout)
        root_paths = [r["path"] for r in st_root_data["data"]["repositories"]]
        self.assertIn(str(self.clean_repo), root_paths)

        # 4. aw status --json with cwd = external lane (with user config listing no repos -> fallback)
        cfg_dir = self.fake_xdg / "agent-workflows"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "config.json").write_text(
            json.dumps(
                {
                    "config_version": 2,
                    "repos": {
                        "search": [],
                        "installed": [],
                        "exclude": [],
                        "ignore": [],
                    },
                }
            ),
            encoding="utf-8",
        )
        res_st_lane = self._run_aw("status", "--json", cwd=self.clean_lane)
        self.assertEqual(
            res_st_lane.returncode, 0, f"status lane stderr: {res_st_lane.stderr}"
        )
        st_lane_data = json.loads(res_st_lane.stdout)
        lane_repos = st_lane_data["data"]["repositories"]
        self.assertEqual(len(lane_repos), 1)
        self.assertEqual(lane_repos[0]["path"], str(self.clean_lane))
        self.assertEqual(lane_repos[0]["layout"], "home (clean-target)")
        self.assertEqual(lane_repos[0]["preset"], "completely-clean-target")
        self.assertEqual(lane_repos[0]["backend"], "home")

    def test_f_attention_and_context_subprocesses(self) -> None:
        """(f) subprocess aw attention and aw context in external lane."""
        # 1. aw attention --format json in external lane exits 0 without no-project refusal
        res_attn = self._run_aw("attention", "--format", "json", cwd=self.clean_lane)
        self.assertEqual(res_attn.returncode, 0, f"attention stderr: {res_attn.stderr}")
        attn_data = json.loads(res_attn.stdout)
        self.assertNotIn("status", attn_data)  # "status": "cannot-run" is absent
        self.assertTrue(attn_data.get("valid"))

        # 2. aw context --agent in external lane reports main root's project_id
        res_ctx = self._run_aw("context", "--agent", cwd=self.clean_lane)
        self.assertEqual(res_ctx.returncode, 0, f"context stderr: {res_ctx.stderr}")
        ctx_data = json.loads(res_ctx.stdout)
        self.assertEqual(ctx_data.get("outcome"), "clean")
        evidence = ctx_data.get("evidence", [])
        self.assertTrue(
            any(f"project_id:{self.clean_proj_id}" in str(e) for e in evidence),
            f"Expected project_id:{self.clean_proj_id} in {evidence}",
        )
