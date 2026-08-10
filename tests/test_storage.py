"""Unit tests for AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.project_registry import (
    register_or_update_project,
)
from agent_workflows.project_schema import (
    DurabilityState,
    RecordsBackend,
)
from agent_workflows.storage import (
    IdentityConflictError,
    StorageSecurityError,
    acknowledge_remote_durability,
    get_storage_status,
    init_records_storage,
    validate_storage_boundaries,
)


class TestStorageBackendsAndDurability(unittest.TestCase):
    """Test storage backends, safety boundaries, and durability classification."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        # Environment setup for isolated test runs
        os.environ["AW_HOME"] = self.aw_home
        self.user_cfg_dir = os.path.join(self.tmp_dir, "user_cfg")
        os.makedirs(self.user_cfg_dir, exist_ok=True)
        os.environ["XDG_CONFIG_HOME"] = self.user_cfg_dir

        # Register fixture project
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        os.environ.pop("XDG_CONFIG_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_durability_classification_truthfulness(self):
        """Test durability classification: local-git vs durable-private vs unversioned."""
        # Unversioned initially
        st1 = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(st1.durability_state, DurabilityState.UNVERSIONED.value)
        self.assertFalse(st1.has_git)
        self.assertFalse(st1.remote_acknowledged)

        # Initialize local Git -> local-git
        st2 = init_records_storage(repo_path=self.target_repo, git_init=True)
        self.assertEqual(st2.durability_state, DurabilityState.LOCAL_GIT.value)
        self.assertTrue(st2.has_git)

        # Mock remote origin URL in storage repo
        records_dir = st2.records_path
        subprocess.run(
            [
                "git",
                "-C",
                records_dir,
                "remote",
                "add",
                "origin",
                "https://github.com/myorg/records.git",
            ],
            capture_output=True,
        )

        # Remote present WITHOUT explicit user acknowledgement STILL maps to local-git (spec Section 6.2 & L3-01!)
        st3 = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(st3.durability_state, DurabilityState.LOCAL_GIT.value)
        self.assertIsNotNone(st3.remote_url)
        self.assertFalse(st3.remote_acknowledged)

        # Explicit remote acknowledgement -> durable-private
        st4 = acknowledge_remote_durability(
            repo_path=self.target_repo, acknowledge=True
        )
        self.assertEqual(st4.durability_state, DurabilityState.DURABLE_PRIVATE.value)
        self.assertTrue(st4.remote_acknowledged)

        # Revoking acknowledgement -> downgrades back to local-git
        st5 = acknowledge_remote_durability(
            repo_path=self.target_repo, acknowledge=False
        )
        self.assertEqual(st5.durability_state, DurabilityState.LOCAL_GIT.value)
        self.assertFalse(st5.remote_acknowledged)

    def test_repository_backend_managed_durability(self):
        """Repository backend maps to repository-managed durability state."""
        ctx_cfg = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(ctx_cfg, exist_ok=True)
        with open(os.path.join(ctx_cfg, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"delivery_mode": "tracked", "records_backend": "repository"}, f)

        st = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(st.records_backend, RecordsBackend.REPOSITORY.value)
        self.assertEqual(st.durability_state, DurabilityState.REPOSITORY_MANAGED.value)

    def test_safety_boundary_refusals(self):
        """Validate safety boundary refusals for path traversal and internal nesting."""
        # Traversal refusal
        with self.assertRaises(StorageSecurityError):
            validate_storage_boundaries(
                self.target_repo, "../../etc/passwd", "home", self.aw_home
            )

        # External backend resolving inside target repository refusal
        inside_target = os.path.join(self.target_repo, "sub", "records")
        with self.assertRaises(StorageSecurityError):
            validate_storage_boundaries(
                self.target_repo, inside_target, "home", self.aw_home
            )

    def test_identity_conflicting_companion_refusal(self):
        """Companion storage attached to another project ID must be refused."""
        companion_dir = os.path.join(self.tmp_dir, "other_companion")
        os.makedirs(companion_dir, exist_ok=True)

        # Register another repo at companion_dir
        other_repo = os.path.join(self.tmp_dir, "other_repo")
        os.makedirs(other_repo, exist_ok=True)
        register_or_update_project(other_repo, self.aw_home, project_id="other-999999")
        register_or_update_project(
            companion_dir, self.aw_home, project_id="other-999999"
        )

        # Validate storage boundaries for self.target_repo using companion_dir -> MUST raise IdentityConflictError!
        with self.assertRaises(IdentityConflictError):
            validate_storage_boundaries(
                self.target_repo, companion_dir, "companion", self.aw_home
            )

    def test_cli_storage_status_json(self):
        """Test `aw storage status --json` via CLI invocation."""
        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "storage",
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
        self.assertIn("records_backend", data)
        self.assertIn("durability_state", data)
        self.assertIn("recommendation", data)

    def test_cli_storage_init_dry_run(self):
        """Test `aw storage init --dry-run` does not mutate filesystem."""
        cmd = [
            "python3",
            "-m",
            "agent_workflows",
            "storage",
            "init",
            "--repo",
            self.target_repo,
            "--dry-run",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("[DRY RUN]", res.stdout)


if __name__ == "__main__":
    unittest.main()
