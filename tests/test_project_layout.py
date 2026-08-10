"""Unit tests for AW physical layout materialization, ownership boundaries, and journaled compensating transactions (IPD 20260809-awlayout-05)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_wizard import ProjectPolicy
from agent_workflows.manifest import Manifest, SCHEMA_VERSION
from agent_workflows.project_layout import (
    ConfigMergeError,
    TransactionJournal,
    materialize_project_layout,
    merge_config_policy,
)
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class TestProjectLayoutAndOwnership(unittest.TestCase):
    """Test logical-to-physical materialization, ownership boundaries, and journaled transactions."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        os.environ["AW_HOME"] = self.aw_home

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_materialize_tracked_home_backend_omits_target_records_dir(self):
        """Tracked delivery with home records backend MUST NOT create target `.aw/records/` directory (E-01 & V-01)."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        target_aw = Path(self.target_repo) / ".aw"
        self.assertTrue((target_aw / "system").is_dir())
        self.assertTrue((target_aw / "config").is_dir())
        self.assertTrue((target_aw / "state").is_dir())

        # INVARIANT: Target repo MUST NOT contain `.aw/records/` directory for external backend!
        self.assertFalse(
            (target_aw / "records").exists(),
            "Target repository contained .aw/records/ for an external records backend!",
        )

    def test_materialize_tracked_repository_backend_creates_records_dir(self):
        """Tracked delivery with repository backend creates `.aw/records/` directory in target repo."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.REPOSITORY.value,
            aw_home=self.aw_home,
        )

        materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        target_aw = Path(self.target_repo) / ".aw"
        self.assertTrue((target_aw / "records").is_dir())

    def test_sentinel_bytes_preserved_outside_intended_roots(self):
        """Sentinel bytes outside intended roots remain byte-identical after layout materialization (V-01 & V-02)."""
        target_p = Path(self.target_repo)
        sentinel_file = target_p / "user_file.txt"
        sentinel_content = b"SENTINEL_BYTES_USER_PRESERVED_12345\n"
        sentinel_file.write_bytes(sentinel_content)

        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        self.assertEqual(sentinel_file.read_bytes(), sentinel_content)

    def test_config_merge_preserves_unknown_human_keys(self):
        """Config merge preserves unknown human-added JSON keys in config/policy.json (E-02 & V-02)."""
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_file = config_dir / "policy.json"

        # Pre-populate with human-added key "custom_team_policy"
        human_config = {
            "delivery_mode": "tracked",
            "records_backend": "home",
            "custom_team_policy": {"strict_ci": True, "reviewer_count": 2},
        }
        with open(policy_file, "w", encoding="utf-8") as f:
            json.dump(human_config, f, indent=2)

        # Merge new policy
        new_pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            enabled_hosts=["opencode", "claude"],
        )

        merged = merge_config_policy(policy_file, new_pol, replace_config=False)

        # Human-added key MUST be preserved byte-for-byte in merged config!
        self.assertIn("custom_team_policy", merged)
        self.assertEqual(merged["custom_team_policy"]["strict_ci"], True)
        self.assertEqual(merged["enabled_hosts"], ["opencode", "claude"])

    def test_config_merge_malformed_json_refusal(self):
        """Malformed config/policy.json is refused unless --replace-config is specified (E-02 & V-02)."""
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_file = config_dir / "policy.json"

        # Write invalid JSON syntax
        policy_file.write_text("{ malformed json content ...", encoding="utf-8")

        new_pol = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
        )

        with self.assertRaises(ConfigMergeError):
            merge_config_policy(policy_file, new_pol, replace_config=False)

        # Passing replace_config=True succeeds
        replaced = merge_config_policy(policy_file, new_pol, replace_config=True)
        self.assertEqual(replaced["delivery_mode"], "tracked")

    def test_journaled_compensating_transaction_rollback_on_failure(self):
        """Transaction journal executes reverse-order compensation on failure (E-04 & V-04)."""
        target_file = os.path.join(self.target_repo, "test_file.txt")
        original_content = "ORIGINAL_CONTENT_BEFORE_TRANSACTION\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(original_content)

        journal_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        journal = TransactionJournal(
            target_repo=self.target_repo, journal_dir=journal_dir
        )

        # Stage write op that modifies test_file.txt
        op = journal.add_write_op(target_file, "NEW_CONTENT_DURING_TRANSACTION\n")
        self.assertTrue(op.completed)
        self.assertEqual(
            Path(target_file).read_text(encoding="utf-8"),
            "NEW_CONTENT_DURING_TRANSACTION\n",
        )

        # Simulate transaction failure & trigger compensation
        success, errors = journal.compensate()
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

        # Original content MUST be restored byte-for-byte!
        self.assertEqual(
            Path(target_file).read_text(encoding="utf-8"), original_content
        )

    def test_manifest_schema_version_2(self):
        """Manifest written during materialization uses SCHEMA_VERSION = 2 (E-02 & V-05)."""
        policy = ProjectPolicy(
            delivery_mode=DeliveryMode.TRACKED.value,
            records_backend=RecordsBackend.HOME.value,
            aw_home=self.aw_home,
        )

        materialize_project_layout(
            target_repo=self.target_repo, policy=policy, aw_home=self.aw_home
        )

        manifest_file = (
            Path(self.target_repo) / ".aw" / "system" / "managed-sections.json"
        )
        self.assertTrue(manifest_file.is_file())

        mf = Manifest.load_from(manifest_file)
        self.assertEqual(mf.schema_version, 2)
        self.assertEqual(SCHEMA_VERSION, 2)


if __name__ == "__main__":
    unittest.main()
