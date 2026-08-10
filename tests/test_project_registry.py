"""Unit tests for AW_HOME precedence, project identity, matching engine, and atomic registry (IPD 20260809-awlayout-02)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import config
from agent_workflows.project_registry import (
    RegistrySecurityError,
    find_project,
    generate_project_id,
    get_git_common_dir,
    load_registry,
    normalize_origin_hint,
    register_or_update_project,
    save_registry,
    _check_registry_path_security,
)


class TestProjectRegistry(unittest.TestCase):
    """Test registry schema, AW_HOME precedence, identity matching, security boundaries, and CLI."""

    @staticmethod
    def _git_init(path: str, origin: str | None = None) -> None:
        """Create a REAL git repository (an empty .git dir is not a valid repo, so the
        git-common-dir and origin probes would return None and mask the behavior under test)."""
        os.makedirs(path, exist_ok=True)
        subprocess.run(["git", "init", "-q", path], check=True, capture_output=True)
        if origin:
            subprocess.run(
                ["git", "-C", path, "remote", "add", "origin", origin],
                check=True,
                capture_output=True,
            )

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        self._git_init(self.target_repo)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_aw_home_precedence(self):
        """Test AW_HOME resolution precedence (explicit > env > config > platform default)."""
        # 1. Platform default
        p_def, src_def = config.get_aw_home()
        self.assertIn("platform default", src_def)

        # 2. Config value
        cfg = config.default_config()
        cfg["aw_home"] = self.aw_home
        user_cfg_dir = os.path.join(self.tmp_dir, "user_cfg")
        os.makedirs(user_cfg_dir, exist_ok=True)
        os.environ["XDG_CONFIG_HOME"] = user_cfg_dir
        config.save(cfg)

        p_cfg, src_cfg = config.get_aw_home()
        self.assertEqual(p_cfg, Path(self.aw_home).resolve())

        # 3. Environment variable overrides config
        env_home = os.path.join(self.tmp_dir, "env_aw_home")
        os.environ["AW_HOME"] = env_home
        p_env, src_env = config.get_aw_home()
        self.assertEqual(p_env, Path(env_home).resolve())
        self.assertIn("environment variable", src_env)

        # 4. Explicit flag overrides environment variable
        flag_home = os.path.join(self.tmp_dir, "flag_aw_home")
        p_flag, src_flag = config.get_aw_home(explicit_flag=flag_home)
        self.assertEqual(p_flag, Path(flag_home).resolve())
        self.assertIn("--aw-home flag", src_flag)

        # Clean up env
        os.environ.pop("AW_HOME", None)
        os.environ.pop("XDG_CONFIG_HOME", None)

    def test_origin_hint_normalization_and_redaction(self):
        """Test origin URL normalization and credential/token redaction."""
        # Strips credentials & tokens
        self.assertEqual(
            normalize_origin_hint(
                "https://user:secret-token123@github.com/org/repo.git"
            ),
            "github.com/org/repo",
        )

        # Strips SSH format
        self.assertEqual(
            normalize_origin_hint("git@github.com:org/repo.git"),
            "github.com/org/repo",
        )

        # Strips query params and fragment
        self.assertEqual(
            normalize_origin_hint("https://github.com/org/repo.git?token=abc#L10"),
            "github.com/org/repo",
        )

    def test_git_common_dir_probe(self):
        """Test git rev-parse --git-common-dir probe on git repo."""
        common_dir = get_git_common_dir(self.target_repo)
        self.assertIsNotNone(common_dir)
        self.assertTrue(os.path.isabs(common_dir))

    def test_stable_project_id_generation(self):
        """Project ID must be deterministic, opaque, and prefixed with clean slug."""
        pid1, slug1 = generate_project_id(self.target_repo)
        pid2, slug2 = generate_project_id(self.target_repo)
        self.assertEqual(pid1, pid2)
        self.assertEqual(slug1, "myrepo")
        self.assertTrue(pid1.startswith("myrepo-"))

    def test_atomic_registry_save_and_load(self):
        """Test atomic registry save with locking and fsync."""
        reg_file = os.path.join(self.aw_home, "config", "registry.json")
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

        reg_data = load_registry(reg_file)
        self.assertIn("myrepo-123456", reg_data["projects"])
        self.assertEqual(
            reg_data["projects"]["myrepo-123456"]["target_paths"][0],
            Path(self.target_repo).resolve().as_posix(),
        )

    def test_negative_two_projects_shared_origin_no_auto_attach(self):
        """NEGATIVE TEST: Two projects with the same origin URL MUST NOT auto-attach!"""
        # Register Repo A (a real repo sharing the origin)
        repo_a = os.path.join(self.tmp_dir, "repo_a")
        self._git_init(repo_a, origin="https://github.com/org/shared-repo.git")
        register_or_update_project(repo_a, self.aw_home, project_id="repo-a-111111")

        # Manually set origin hint on entry_a
        reg_file = os.path.join(self.aw_home, "config", "registry.json")
        reg_data = load_registry(reg_file)
        reg_data["projects"]["repo-a-111111"]["origin_hint"] = (
            "github.com/org/shared-repo"
        )
        save_registry(reg_data, reg_file)

        # Create Repo B: a SEPARATE real clone with the SAME origin URL
        repo_b = os.path.join(self.tmp_dir, "repo_b")
        self._git_init(repo_b, origin="https://github.com/org/shared-repo.git")

        # Search for project from Repo B
        match_res = find_project(repo_b, aw_home=self.aw_home)

        # MUST NOT auto-attach Repo B to repo-a-111111!
        self.assertIsNone(
            match_res.entry, "Repo B was falsely auto-attached based on origin URL!"
        )
        self.assertTrue(
            match_res.ambiguous, "Match result should be flagged ambiguous!"
        )
        self.assertIsNotNone(
            match_res.candidate_hint, "Candidate hint should be provided for display!"
        )
        self.assertEqual(match_res.candidate_hint.project_id, "repo-a-111111")

    def test_path_security_boundaries(self):
        """Test registry security refusal for traversal and unsafe containment."""
        with self.assertRaises(RegistrySecurityError):
            _check_registry_path_security(self.aw_home, "../../etc/passwd")

        with self.assertRaises(RegistrySecurityError):
            _check_registry_path_security(self.aw_home, self.aw_home)

    def test_cli_project_status_json(self):
        """Test `aw project status --json` via CLI invocation."""
        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "project",
            "status",
            "--repo",
            self.target_repo,
            "--json",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("target_repo", data)
        self.assertIn("effective_aw_home", data)

    def test_cli_project_attach_and_move(self):
        """Test `aw project attach` and `aw project move` CLI commands."""
        pid = "testproj-999999"
        # Attach with --yes
        cmd_attach = [
            "python3",
            "-m",
            "agent_workflows",
            "project",
            "attach",
            pid,
            "--repo",
            self.target_repo,
            "--yes",
        ]
        res1 = subprocess.run(
            cmd_attach, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res1.returncode, 0, f"Attach CLI error: {res1.stderr}")

        # Verify status matches attached pid
        cmd_status = [
            "python3",
            "-m",
            "agent_workflows",
            "project",
            "status",
            "--repo",
            self.target_repo,
            "--json",
        ]
        res2 = subprocess.run(
            cmd_status, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        data = json.loads(res2.stdout)
        self.assertTrue(data["matched"])
        self.assertEqual(data["project_entry"]["project_id"], pid)

        # Move to new path
        new_repo = os.path.join(self.tmp_dir, "newrepo")
        self._git_init(new_repo)
        cmd_move = [
            "python3",
            "-m",
            "agent_workflows",
            "project",
            "move",
            pid,
            new_repo,
            "--yes",
        ]
        res3 = subprocess.run(
            cmd_move, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res3.returncode, 0, f"Move CLI error: {res3.stderr}")


if __name__ == "__main__":
    unittest.main()
