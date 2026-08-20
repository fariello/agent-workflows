"""Unit tests for physical AW layout transactional migration (IPD 20260810-awphysical-07)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.layout_migration import (
    CleanupError,
    MigrationError,
    MigrationManager,
    PreflightGateError,
    StaleInputError,
    SwitchError,
    TransactionLockError,
    VerificationError,
)
from agent_workflows import layout_inventory as inv_mod


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class TransactionalMigrationTests(unittest.TestCase):
    """Test suite validating Order 07 migration transaction invariants and falsifiability."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="test_awphys_07_")
        self.repo = Path(self.tmp) / "repo"
        self.repo.mkdir(parents=True)

        # Init git repo
        _run_git(self.repo, ["init"])
        _run_git(self.repo, ["config", "user.name", "Test User"])
        _run_git(self.repo, ["config", "user.email", "test@example.com"])

        # Create sample legacy files
        self.agents_wf = self.repo / ".agents" / "workflows" / "test.md"
        self.agents_wf.parent.mkdir(parents=True, exist_ok=True)
        self.agents_wf.write_text("# Test Workflow\n", encoding="utf-8")

        self.artifacts_dir = self.repo / "workflow-artifacts" / "run1"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.art_file = self.artifacts_dir / "output.txt"
        self.art_file.write_text("artifact data\n", encoding="utf-8")

        _run_git(self.repo, ["add", "."])
        _run_git(self.repo, ["commit", "-m", "initial commit"])

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_e01(self) -> None:
        """E-01 / V-01: Freeze inputs and transaction state machine under state/runtime/transactions."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Positive assertion: transaction starts, creates lock & journal, completes phase
        plan = mgr.execute_migration(target_backend="repository")
        self.assertTrue(plan.is_valid)

        tx_file = (
            self.repo
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        self.assertTrue(tx_file.exists())

        tx_data = json.loads(tx_file.read_text(encoding="utf-8"))
        self.assertIn("transaction_id", tx_data)
        self.assertEqual(tx_data["status"], "completed")
        self.assertIn("inventory_digest", tx_data)
        self.assertIn("map_digest", tx_data)
        self.assertIn("policy_digest", tx_data)

        # Failure condition: stale input is rejected
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(StaleInputError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="stale-input"
            )

        # Failure condition: active concurrent lock is rejected
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(TransactionLockError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="concurrent-writer"
            )

    def test_e02(self) -> None:
        """E-02 / V-02: Writer lock and pre-apply revalidation."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Positive assertion: preflight revalidation succeeds on clean repo
        st = mgr.status_migration()
        self.assertFalse(st["active"])

        roots = inv_mod._default_roots(self.repo)
        inv_res = inv_mod.inventory(self.repo, roots, False)
        map_res = inv_mod.build_migration_map(self.repo, inv_res, "repository")
        risk_res = inv_mod.analyze_migration_risks(self.repo, inv_res, map_res)
        plan_doc = {
            "schema_version": 1,
            "inventory": inv_res,
            "migration_map": map_res,
            "risk_analysis": risk_res,
            "valid": True,
        }

        # Modify source file after plan doc creation to force preflight hash revalidation failure
        self.art_file.write_text("tampered content after freeze\n", encoding="utf-8")

        with self.assertRaises(PreflightGateError):
            mgr.execute_migration(target_backend="repository", plan_doc=plan_doc)

        # Failure condition: disk-loss / permission-loss fault injection
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(PreflightGateError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="disk-loss"
            )

    def test_e03(self) -> None:
        """E-03 / V-03: Copy, verify, and switch once."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Positive assertion: files are copied and byte/hash verified
        mgr.execute_migration(target_backend="repository")

        staged_art = self.repo / ".aw" / "records" / "run1" / "output.txt"
        self.assertTrue(staged_art.exists())
        self.assertEqual(staged_art.read_text(encoding="utf-8"), "artifact data\n")

        # Failure condition: verification hash mismatch halts before switch
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(VerificationError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="verify-mismatch"
            )

    def test_e04(self) -> None:
        """E-04 / V-04: Destination verification & authoritative policy switch written LAST."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Positive assertion: policy switch occurs and switch receipt is written
        mgr.execute_migration(target_backend="repository")

        config_file = self.repo / ".aw" / "config" / "config.json"
        self.assertTrue(config_file.exists())
        cfg = json.loads(config_file.read_text(encoding="utf-8"))
        self.assertEqual(cfg["records_backend"], "repository")

        receipt_file = (
            self.repo
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "switch_receipt.json"
        )
        self.assertTrue(receipt_file.exists())
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        self.assertEqual(receipt["authority"], "switched")

        # Failure condition: switch failure leaves legacy authoritative
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(SwitchError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="switch-failure"
            )

        # Failure condition: kill after switch leaves detectable authority
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(MigrationError):
            mgr.execute_migration(
                target_backend="repository",
                fault_injection="kill-after-switch-before-receipt",
            )

    def test_e05(self) -> None:
        """E-05 / V-05: MOVE-not-copy relocation (IPD hnzr8v). The legacy source is MOVED (gone
        from the legacy path, present once under .aw/), and the manifest records the move journal
        as the rollback source while forbidding cleanup during cutover."""
        mgr = MigrationManager(target_repo=str(self.repo))

        mgr.execute_migration(target_backend="repository")

        # Source MOVED: gone from the legacy path, content now at the .aw/records destination.
        moved = self.repo / ".aw" / "records" / "run1" / "output.txt"
        self.assertFalse(
            self.art_file.exists(),
            "move-not-copy: the legacy source should be gone after the move",
        )
        self.assertTrue(moved.is_file())
        self.assertEqual(moved.read_text(encoding="utf-8"), "artifact data\n")

        ret_file = (
            self.repo
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        self.assertTrue(ret_file.exists())
        ret = json.loads(ret_file.read_text(encoding="utf-8"))
        self.assertFalse(ret["cleanup_allowed"])
        self.assertTrue(ret.get("move_journal"), "manifest missing the move journal")

    def test_e06(self) -> None:
        """E-06 / V-06: Git boundaries and separate staging plans."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Positive assertion: transaction generates separate Git staging plans
        mgr.execute_migration(target_backend="repository")

        tx_file = (
            self.repo
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        tx_data = json.loads(tx_file.read_text(encoding="utf-8"))
        self.assertIn("git_staging_plans", tx_data)
        plans = tx_data["git_staging_plans"]
        self.assertIn("target", plans)
        self.assertIn("companion", plans)
        self.assertIn("source", plans)

        # Verify target plan contains target paths and doesn't mix companion paths
        target_paths = plans["target"]["staged_paths"]
        self.assertTrue(any("records" in p for p in target_paths))

        # Failure condition: cross-git partial stage failure is caught and raised
        if (self.repo / ".aw").exists():
            shutil.rmtree(self.repo / ".aw")
        with self.assertRaises(MigrationError):
            mgr.execute_migration(
                target_backend="repository", fault_injection="cross-git-partial-stage"
            )

    def test_e07(self) -> None:
        """E-07 / V-07: Status, resume, rollback, and preview-first cleanup commands."""
        mgr = MigrationManager(target_repo=str(self.repo))

        # Status before migration
        st = mgr.status_migration()
        self.assertFalse(st["active"])

        # Execute migration (MOVE): the legacy source is relocated, not copied-and-retained.
        mgr.execute_migration(target_backend="repository")
        self.assertFalse(
            self.art_file.exists(), "move-not-copy: legacy source should be gone"
        )

        # Under move semantics, cleanup has NOTHING to remove (the sources are already gone);
        # preview is a safe no-op with an empty would_remove list (IPD hnzr8v E-05).
        prev = mgr.cleanup_migration(confirm=False)
        self.assertEqual(prev["status"], "preview")
        self.assertEqual(prev["would_remove"], [])

        # Rollback reverses the move: authority reverts to legacy AND the source is restored.
        rb = mgr.rollback_migration()
        self.assertEqual(rb["status"], "rolled_back")
        self.assertEqual(rb["authority"], "legacy")
        self.assertTrue(
            self.art_file.exists(), "rollback did not restore the moved source"
        )

        # Config reverted to legacy
        config_file = self.repo / ".aw" / "config" / "config.json"
        cfg = json.loads(config_file.read_text(encoding="utf-8"))
        self.assertEqual(cfg["records_backend"], "legacy")

        # Cleanup refusal fault injection
        with self.assertRaises(CleanupError):
            mgr.cleanup_migration(fault_injection="cleanup-refusal")

    def test_e08(self) -> None:
        """E-08 / V-08: Fault injection matrix across every phase."""
        mgr = MigrationManager(target_repo=str(self.repo))

        injections = [
            ("stale-input", StaleInputError),
            ("concurrent-writer", TransactionLockError),
            ("copy-failure", MigrationError),
            ("verify-mismatch", VerificationError),
            ("switch-failure", SwitchError),
            ("kill-after-switch-before-receipt", MigrationError),
            ("disk-loss", PreflightGateError),
            ("permission-loss", PreflightGateError),
            ("cross-git-partial-stage", MigrationError),
        ]

        for inj_name, expected_exc in injections:
            with self.subTest(injection=inj_name):
                if (self.repo / ".aw").exists():
                    shutil.rmtree(self.repo / ".aw")
                with self.assertRaises(expected_exc):
                    mgr.execute_migration(
                        target_backend="repository", fault_injection=inj_name
                    )


if __name__ == "__main__":
    unittest.main()
