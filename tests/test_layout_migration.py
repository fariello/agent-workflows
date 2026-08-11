"""Unit tests for layout migration, rollback, and conservative uninstall (IPD 20260809-awlayout-09)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.layout_migration import (
    MigrationManager,
)
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class TestLayoutMigration(unittest.TestCase):
    """Test layout migration planning, transactional execution, and conservative uninstall."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(self.target_repo, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", self.target_repo], check=True, capture_output=True
        )
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home

        # Register project fixture
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

        # Create basic policy fixture
        policy_file = Path(self.target_repo) / ".aw" / "config" / "policy.json"
        policy_file.parent.mkdir(parents=True, exist_ok=True)
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.HOME.value,
            "aw_home": self.aw_home,
        }
        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

    def tearDown(self):
        # Restore the prior AW_HOME (sandbox value set in tests/__init__.py);
        # popping it unconditionally would clobber the sandbox for later tests
        # and leak into the real ~/.aw.
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_migration_planning_dry_run(self):
        """Test migration planning dry run outputs valid plan without mutating filesystem (E-01 & V-01)."""
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        plan = mgr.plan_migration(target_backend=RecordsBackend.REPOSITORY.value)

        self.assertTrue(plan.is_valid)
        self.assertEqual(plan.source_backend, RecordsBackend.HOME.value)
        self.assertEqual(plan.target_backend, RecordsBackend.REPOSITORY.value)
        self.assertGreater(plan.available_bytes, 0)

    def test_transactional_migration_execution(self):
        """Test transactional migration updates policy and creates journal (E-02 & V-02)."""
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        plan = mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value, dry_run=False
        )

        self.assertTrue(plan.is_valid)

        # Policy switch MUST be written to the resolver's durable source (config.json), so a
        # subsequent resolve honors the new backend.
        policy_file = Path(self.target_repo) / ".aw" / "config" / "config.json"
        policy_data = json.loads(policy_file.read_text(encoding="utf-8"))
        self.assertEqual(
            policy_data["records_backend"], RecordsBackend.REPOSITORY.value
        )

        # Migration journal MUST be written under state/runtime/transactions/
        journal_p = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        self.assertTrue(journal_p.is_file())
        journal_data = json.loads(journal_p.read_text(encoding="utf-8"))
        self.assertEqual(journal_data["status"], "completed")

    def test_conservative_uninstall_preserves_config_state_records(self):
        """Uninstall MUST remove system files but PRESERVE config, state, and records by default (E-04 & L9-02)."""
        target_aw = Path(self.target_repo) / ".aw"
        (target_aw / "system").mkdir(parents=True, exist_ok=True)
        (target_aw / "system" / "manifest.json").write_text("{}", encoding="utf-8")
        (target_aw / "config").mkdir(parents=True, exist_ok=True)
        (target_aw / "config" / "policy.json").write_text("{}", encoding="utf-8")
        (target_aw / "state").mkdir(parents=True, exist_ok=True)
        (target_aw / "records").mkdir(parents=True, exist_ok=True)
        (target_aw / "records" / "sample.md").write_text("# Record", encoding="utf-8")

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        res = mgr.uninstall_layout(preserve_records=True, deep_remove_records=False)

        self.assertEqual(res["status"], "uninstalled")
        self.assertFalse(
            (target_aw / "system").exists(),
            "system/ directory was not removed on uninstall!",
        )

        # INVARIANT: config, state, and records MUST be preserved by default!
        self.assertTrue((target_aw / "config").is_dir())
        self.assertTrue((target_aw / "state").is_dir())
        self.assertTrue((target_aw / "records").is_dir())
        self.assertTrue((target_aw / "records" / "sample.md").is_file())

    def test_guarded_deep_removal(self):
        """Deep record removal deletes records directory only when explicitly flagged (E-04 & V-04)."""
        target_aw = Path(self.target_repo) / ".aw"
        (target_aw / "system").mkdir(parents=True, exist_ok=True)
        (target_aw / "records").mkdir(parents=True, exist_ok=True)
        (target_aw / "records" / "sample.md").write_text("# Record", encoding="utf-8")

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.uninstall_layout(preserve_records=False, deep_remove_records=True)

        self.assertFalse((target_aw / "records").exists())

    def test_preserve_records_wins_over_deep_remove(self):
        """SAFETY: preserve_records=True is authoritative and protects records even if a caller ALSO
        passes deep_remove_records=True (spec 15.4 / L9-02 - deep removal is unambiguous-intent only)."""
        target_aw = Path(self.target_repo) / ".aw"
        (target_aw / "system").mkdir(parents=True, exist_ok=True)
        (target_aw / "records").mkdir(parents=True, exist_ok=True)
        (target_aw / "records" / "precious.md").write_text(
            "# PRECIOUS", encoding="utf-8"
        )

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.uninstall_layout(preserve_records=True, deep_remove_records=True)

        self.assertTrue(
            (target_aw / "records" / "precious.md").exists(),
            "preserve_records=True must protect records even when deep_remove_records=True",
        )


if __name__ == "__main__":
    unittest.main()
