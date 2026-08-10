"""Unit tests for record routing resolution, Git absence, and state-root exclusion (IPD 20260809-awlayout-08)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, LogicalRoot, RecordsBackend
from agent_workflows.record_producers import resolve_record_routing


class TestRecordRouting(unittest.TestCase):
    """Test record routing resolution across backends (E-02, E-04 & V-02, V-04)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )

    def tearDown(self):
        os.environ.pop("AW_HOME", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_repository_backend_routing(self):
        """Repository backend routes to target `.aw/records/` and allows Git staging (E-02)."""
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.REPOSITORY.value,
            "aw_home": self.aw_home,
        }
        policy_file = Path(self.target_repo) / ".aw" / "config" / "policy.json"
        policy_file.parent.mkdir(parents=True, exist_ok=True)
        import json

        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

        info = resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(info.records_backend, RecordsBackend.REPOSITORY.value)
        self.assertEqual(info.commit_destination, "repository")
        self.assertTrue(info.allow_git_stage)
        self.assertTrue(info.records_root.startswith(self.target_repo))

    def test_home_backend_routing_target_git_absence(self):
        """Home backend routes outside target repo; commit destination is None; Git status is clean (E-04 & V-04)."""
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.HOME.value,
            "aw_home": self.aw_home,
        }
        policy_file = Path(self.target_repo) / ".aw" / "config" / "policy.json"
        policy_file.parent.mkdir(parents=True, exist_ok=True)
        import json

        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

        info = resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(info.records_backend, RecordsBackend.HOME.value)
        self.assertIsNone(info.commit_destination)
        self.assertFalse(info.allow_git_stage)

        # Target repo MUST NOT contain physical records root
        self.assertFalse(info.records_root.startswith(self.target_repo))

    def test_records_producers_state_root_exclusion(self):
        """Records producers must resolve records_root distinct from state_root (E-03 & V-03)."""
        ctx = resolve_project_context(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        state_root = ctx.logical_roots[LogicalRoot.STATE.value]
        records_root = ctx.logical_roots[LogicalRoot.RECORDS.value]

        self.assertNotEqual(state_root, records_root)
        self.assertFalse(records_root.startswith(state_root))


if __name__ == "__main__":
    unittest.main()
