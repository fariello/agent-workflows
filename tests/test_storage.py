"""Unit tests for AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from tests.support import FIXTURES
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
        self._prev_aw_home = os.environ.get("AW_HOME")
        self._prev_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["AW_HOME"] = self.aw_home
        self.user_cfg_dir = os.path.join(self.tmp_dir, "user_cfg")
        os.makedirs(self.user_cfg_dir, exist_ok=True)
        os.environ["XDG_CONFIG_HOME"] = self.user_cfg_dir

        # Register fixture project
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        # Restore prior AW_HOME/XDG_CONFIG_HOME (sandbox values set in
        # tests/__init__.py); popping them unconditionally would clobber the
        # sandbox for later tests and leak into the real ~/.aw.
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        if self._prev_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._prev_xdg
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

        # A configured remote is observable but not acknowledged durable.
        st3 = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(
            st3.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
        )
        self.assertIsNotNone(st3.remote_url)
        self.assertFalse(st3.remote_acknowledged)

        # Explicit remote acknowledgement -> durable-private
        with patch("agent_workflows.storage._remote_reachable", return_value=True):
            st4 = acknowledge_remote_durability(
                repo_path=self.target_repo, acknowledge=True
            )
        self.assertEqual(
            st4.durability_state, DurabilityState.ACKNOWLEDGED_DURABLE.value
        )
        self.assertTrue(st4.remote_acknowledged)

        with patch("agent_workflows.storage._remote_reachable", return_value=False):
            unreachable = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(
            unreachable.durability_state, DurabilityState.UNREACHABLE.value
        )

        with patch("agent_workflows.storage._remote_reachable", return_value=None):
            unknown = get_storage_status(repo_path=self.target_repo)
        self.assertEqual(unknown.durability_state, DurabilityState.UNKNOWN.value)

        # Revoking acknowledgement -> downgrades back to local-git
        st5 = acknowledge_remote_durability(
            repo_path=self.target_repo, acknowledge=False
        )
        self.assertEqual(
            st5.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
        )
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


class CompanionAttachmentTests(unittest.TestCase):
    """Execution and validation tests for Order 05 Companion Attachment and Durability (IPD 20260810-awphysical-05-1e9ggw)."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.target_repo = self.tmp_dir / "target_repo"
        self.target_repo.mkdir()
        subprocess.run(
            ["git", "-C", str(self.target_repo), "init"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.target_repo),
                "config",
                "user.email",
                "test@example.com",
            ],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.target_repo), "config", "user.name", "Test"],
            capture_output=True,
        )

        self.aw_home = self.tmp_dir / "aw_home"
        self.aw_home.mkdir()

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

        register_or_update_project(
            str(self.target_repo), str(self.aw_home), project_id="proj-order05-test"
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_e01(self):
        """E-01: Portable companion identity and machine-local attachment record."""
        from agent_workflows.storage import (
            create_companion_identity,
            load_companion_identity,
            write_local_attachment_record,
            load_local_attachment_record,
            validate_companion_preflight,
            IdentityConflictError,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e01-identity.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        comp_dir = self.tmp_dir / "companion_repo"
        comp_dir.mkdir()
        subprocess.run(
            ["git", "-C", str(comp_dir), "init"], capture_output=True, check=True
        )

        ident = create_companion_identity(
            comp_dir, "proj-order05-test", ["config", "durable_state", "records"]
        )
        self.assertEqual(ident["project_id"], "proj-order05-test")

        loaded_ident = load_companion_identity(comp_dir)
        self.assertIsNotNone(loaded_ident)
        self.assertEqual(loaded_ident["project_id"], "proj-order05-test")

        rec = write_local_attachment_record(
            self.target_repo,
            comp_dir,
            "proj-order05-test",
            ["config", "durable_state", "records"],
        )
        self.assertEqual(rec["project_id"], "proj-order05-test")

        loaded_rec = load_local_attachment_record(self.target_repo)
        self.assertIsNotNone(loaded_rec)
        self.assertEqual(loaded_rec["companion_dir"], comp_dir.resolve().as_posix())

        # Spoof / conflicting project ID identity check -> MUST raise IdentityConflictError!
        other_comp = self.tmp_dir / "spoofed_companion"
        other_comp.mkdir()
        create_companion_identity(other_comp, "conflicting-project-id", ["config"])
        with self.assertRaises(IdentityConflictError):
            validate_companion_preflight(
                self.target_repo, other_comp, aw_home=str(self.aw_home)
            )

    def test_e02(self):
        """E-02: Preflight validation for unsafe or ambiguous storage resolution."""
        from agent_workflows.storage import (
            validate_companion_preflight,
            StorageSecurityError,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e02-preflight.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        # 1. Path traversal -> MUST raise StorageSecurityError
        with self.assertRaises(StorageSecurityError):
            validate_companion_preflight(self.target_repo, "../../etc/passwd")

        # 2. Internal nesting -> MUST raise StorageSecurityError
        inside_comp = self.target_repo / "nested_comp"
        inside_comp.mkdir()
        with self.assertRaises(StorageSecurityError):
            validate_companion_preflight(self.target_repo, inside_comp)

        # 3. Valid external companion -> passes preflight
        valid_comp = self.tmp_dir / "valid_comp"
        valid_comp.mkdir()
        report = validate_companion_preflight(
            self.target_repo, valid_comp, aw_home=str(self.aw_home)
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["target_repo"], self.target_repo.resolve().as_posix())

    def test_e03(self):
        """E-03: Materialize private companion storage bundle and Git boundary separation."""
        from agent_workflows.storage import (
            materialize_companion_storage,
            get_git_commit_boundaries,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e03-bundle.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        comp_dir = self.tmp_dir / "private_companion"
        comp_dir.mkdir()
        subprocess.run(
            ["git", "-C", str(comp_dir), "init"], capture_output=True, check=True
        )

        res = materialize_companion_storage(
            self.target_repo, comp_dir, ["config", "durable_state", "records"]
        )
        self.assertTrue(res["deltas"])
        self.assertTrue((comp_dir / ".aw" / "config").is_dir())
        self.assertTrue((comp_dir / ".aw" / "state" / "durable").is_dir())
        self.assertTrue((comp_dir / ".aw" / "records").is_dir())
        self.assertTrue((comp_dir / ".gitignore").is_file())

        boundaries = get_git_commit_boundaries(self.target_repo, comp_dir)
        self.assertTrue(boundaries["boundaries_separated"])
        self.assertEqual(
            boundaries["target_git_owner"], self.target_repo.resolve().as_posix()
        )
        self.assertEqual(
            boundaries["companion"]["git_owner"], comp_dir.resolve().as_posix()
        )

        # Public target git index check: target index MUST contain zero private canaries
        ls_target = subprocess.run(
            ["git", "-C", str(self.target_repo), "ls-files"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn("candid_private_canary", ls_target.stdout)

    def test_e04(self):
        """E-04: Truthful durability state classification and revocation handling."""
        from agent_workflows.storage import (
            get_storage_status,
            init_records_storage,
            acknowledge_remote_durability,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e04-durability.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        st1 = get_storage_status(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(st1.durability_state, DurabilityState.UNVERSIONED.value)

        st2 = init_records_storage(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home), git_init=True
        )
        self.assertEqual(st2.durability_state, DurabilityState.LOCAL_GIT.value)

        # Mock origin remote
        subprocess.run(
            [
                "git",
                "-C",
                st2.records_path,
                "remote",
                "add",
                "origin",
                "https://example.com/repo.git",
            ],
            capture_output=True,
        )

        st3 = get_storage_status(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(
            st3.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
        )

        with patch("agent_workflows.storage._remote_reachable", return_value=True):
            st4 = acknowledge_remote_durability(
                repo_path=str(self.target_repo),
                aw_home=str(self.aw_home),
                acknowledge=True,
            )
        self.assertEqual(
            st4.durability_state, DurabilityState.ACKNOWLEDGED_DURABLE.value
        )

        # Revoking acknowledgement -> MUST downgrade back and clear remote ack evidence
        st5 = acknowledge_remote_durability(
            repo_path=str(self.target_repo),
            aw_home=str(self.aw_home),
            acknowledge=False,
        )
        self.assertEqual(
            st5.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
        )
        self.assertFalse(st5.remote_acknowledged)

    def test_e05(self):
        """E-05: Attachment lifecycle operations (attach, detach, move, reattach, status)."""
        from agent_workflows.storage import (
            attach_companion,
            detach_companion,
            move_companion,
            reattach_companion,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e05-lifecycle.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        comp_dir = self.tmp_dir / "lifecycle_comp"
        comp_dir.mkdir()

        # Dry run check
        dry_res = attach_companion(
            self.target_repo, comp_dir, dry_run=True, aw_home=str(self.aw_home)
        )
        self.assertTrue(dry_res["dry_run"])
        self.assertFalse((comp_dir / ".aw").exists())

        # Real attach
        att_res = attach_companion(
            self.target_repo, comp_dir, dry_run=False, aw_home=str(self.aw_home)
        )
        self.assertTrue(att_res["attached"])
        self.assertTrue((comp_dir / ".aw").is_dir())

        # Detach -> MUST preserve companion content on disk
        det_res = detach_companion(
            self.target_repo, dry_run=False, aw_home=str(self.aw_home)
        )
        self.assertTrue(det_res["detached"])
        self.assertFalse(det_res["companion_deleted"])
        self.assertTrue(comp_dir.is_dir())

        # Move / reattach
        new_comp = self.tmp_dir / "moved_comp"
        new_comp.mkdir()
        mv_res = move_companion(
            self.target_repo, new_comp, dry_run=False, aw_home=str(self.aw_home)
        )
        self.assertTrue(mv_res["moved"])

        reatt_res = reattach_companion(
            self.target_repo, new_comp, dry_run=False, aw_home=str(self.aw_home)
        )
        self.assertTrue(reatt_res["attached"])

    def test_e06(self):
        """E-06: Independent staging and commit boundaries for target and companion."""
        from agent_workflows.storage import (
            get_git_commit_boundaries,
            attach_companion,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e06-boundaries.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        comp_dir = self.tmp_dir / "boundaries_comp"
        comp_dir.mkdir()
        subprocess.run(
            ["git", "-C", str(comp_dir), "init"], capture_output=True, check=True
        )

        attach_companion(self.target_repo, comp_dir, aw_home=str(self.aw_home))
        b = get_git_commit_boundaries(self.target_repo, comp_dir)

        self.assertTrue(b["boundaries_separated"])
        self.assertIn("target_repo", b)
        self.assertIn("companion", b)
        self.assertNotEqual(b["target_git_owner"], b["companion"]["git_owner"])

    def test_e07(self):
        """E-07: Closed matrix of attachment/durability states and transition testing."""
        from agent_workflows.storage import (
            get_storage_status,
            init_records_storage,
            acknowledge_remote_durability,
        )

        fx = FIXTURES / "awphysical" / "order05" / "e07-matrix.json"
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        states_seen = set()

        s1 = get_storage_status(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home)
        )
        states_seen.add(s1.durability_state)

        s2 = init_records_storage(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home), git_init=True
        )
        states_seen.add(s2.durability_state)

        subprocess.run(
            [
                "git",
                "-C",
                s2.records_path,
                "remote",
                "add",
                "origin",
                "https://example.com/repo.git",
            ],
            capture_output=True,
        )
        s3 = get_storage_status(
            repo_path=str(self.target_repo), aw_home=str(self.aw_home)
        )
        states_seen.add(s3.durability_state)

        with patch("agent_workflows.storage._remote_reachable", return_value=True):
            s4 = acknowledge_remote_durability(
                repo_path=str(self.target_repo),
                aw_home=str(self.aw_home),
                acknowledge=True,
            )
            states_seen.add(s4.durability_state)

        self.assertIn(DurabilityState.UNVERSIONED.value, states_seen)
        self.assertIn(DurabilityState.LOCAL_GIT.value, states_seen)
        self.assertIn(DurabilityState.UNACKNOWLEDGED_REMOTE.value, states_seen)
        self.assertIn(DurabilityState.ACKNOWLEDGED_DURABLE.value, states_seen)


if __name__ == "__main__":
    unittest.main()
