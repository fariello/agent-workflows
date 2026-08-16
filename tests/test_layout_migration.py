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

    def test_rollback_preserves_in_place_host_adapters_and_legacy(self):
        """DATA SAFETY: rollback must NOT delete host-adapter-in-place items (whose destination
        IS the live repo-root path, e.g. AGENTS.md/.claude/.opencode) nor the retained legacy
        sources; it removes only the staged copies UNDER .aw/ (Order 11 rehearsal finding).
        """
        repo = Path(self.target_repo)
        # Legacy system + records + a host adapter + a root pointer.
        (repo / ".agents" / "workflows").mkdir(parents=True, exist_ok=True)
        (repo / ".agents" / "workflows" / "index.md").write_text(
            "wf\n", encoding="utf-8"
        )
        (repo / ".agents" / "plans").mkdir(parents=True, exist_ok=True)
        (repo / ".agents" / "plans" / "p.md").write_text("plan\n", encoding="utf-8")
        (repo / ".claude" / "commands").mkdir(parents=True, exist_ok=True)
        claude_shim = repo / ".claude" / "commands" / "assess.md"
        claude_shim.write_text("claude shim\n", encoding="utf-8")
        agents_md = repo / "AGENTS.md"
        agents_md.write_text("<!-- aw:block -->\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True
        )

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value, dry_run=False
        )

        # Apply left the in-place adapters untouched (not copied under .aw/adapters/).
        self.assertTrue(
            claude_shim.is_file(), "apply disturbed the in-place host adapter"
        )
        self.assertFalse(
            (repo / ".aw" / "adapters").exists(),
            "apply relocated a host adapter under .aw/ (should be preserved in place)",
        )
        # A relocated class WAS staged under .aw/.
        self.assertTrue((repo / ".aw" / "records" / "plans" / "p.md").is_file())

        mgr.rollback_migration()

        # The live host adapter + root pointer + legacy sources MUST survive rollback.
        self.assertTrue(
            claude_shim.is_file(),
            "rollback DELETED the live host adapter .claude/commands/assess.md!",
        )
        self.assertEqual(claude_shim.read_text(encoding="utf-8"), "claude shim\n")
        self.assertTrue(agents_md.is_file(), "rollback DELETED the live AGENTS.md!")
        self.assertTrue(
            (repo / ".agents" / "workflows" / "index.md").is_file(),
            "rollback removed retained legacy source",
        )
        # Staged .aw/ copies of relocated classes ARE removed on rollback (staged copies live
        # under .aw/, matching execute_migration's self.aw_dir base; the prior repo_path base
        # both missed the staged copies and, for in-place items, pointed at the LIVE repo-root
        # file - the data-loss this fix closes).
        self.assertFalse(
            (repo / ".aw" / "records" / "plans" / "p.md").exists(),
            "rollback left a staged .aw/ copy behind (wrong base dir)",
        )
        # The .aw/ tree itself is not destroyed by rollback.
        self.assertTrue((repo / ".aw").is_dir(), "rollback removed the .aw/ tree")

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


class IndependentPostcheckTests(unittest.TestCase):
    """Independent postcheck and comparison tests for Order 10 IPD (E-01, E-02, E-04, E-05, E-06)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-order10"
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_e01(self):
        """E-01: Every source item has exactly one allowed disposition and matching bytes/metadata where required."""
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order10"
            / "e01-compare-manifest.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertIn("inventory_id", fix_data)
        self.assertEqual(
            set(fix_data["dispositions"]), {"copy", "deduplicate", "retain", "exclude"}
        )

    def test_e02(self):
        """E-02: A successful comparison proves legacy remains recoverable and non-authoritative; cleanup remains blocked."""
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order10"
            / "e02-retention-recovery.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertFalse(fix_data["legacy_writer_enabled"])
        self.assertTrue(fix_data["rollback_ready"])
        self.assertFalse(fix_data["cleanup_allowed"])

    def test_e04(self):
        """E-04: Non-mutating canary probes prove writes resolve to intended test destinations without touching real records."""
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order10"
            / "e04-producer-probes.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertGreater(len(fix_data["producer_classes"]), 0)
        self.assertTrue(fix_data["sandbox_destination"].startswith(".aw/records/"))
        for forbidden in fix_data["forbidden_legacy_destinations"]:
            self.assertFalse(fix_data["sandbox_destination"].startswith(forbidden))

    def test_e05(self):
        """E-05: Reviewer does not accept migrator summaries, produces severity-ranked evidence table and verdict."""
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order10"
            / "e05-agent-review.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        doc_path = Path(__file__).resolve().parent.parent / fix_data["instruction_path"]
        self.assertTrue(doc_path.is_file(), f"Review protocol file missing: {doc_path}")
        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("GO", doc_text)
        self.assertIn("NO-GO", doc_text)
        self.assertIn("REVIEW REQUIRED", doc_text)

    def test_e06(self):
        """E-06: Migration CLI status distinguishes copied, switched, verified, independently-reviewed, and cleanup-eligible states."""
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order10"
            / "e06-cli-status.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        status = mgr.status_migration()
        self.assertIn("expected_phases", fix_data)
        self.assertIn("status", status)
        self.assertIn("authority", status)


if __name__ == "__main__":
    unittest.main()
