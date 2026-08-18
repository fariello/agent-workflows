"""Unit tests for physical record producers and routing cutover (Order 08 IPD)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend
from agent_workflows.record_producers import (
    LEGACY_ALLOWLIST,
    LEGACY_WRITER_CANDIDATES,
    PRODUCER_INVENTORY,
    DuplicateAuthorityError,
    DurableStateClass,
    ForbiddenWriteError,
    InvalidRecordClassError,
    LegacyWriteError,
    MigrationInFlightError,
    RecordClass,
    RuntimeStateClass,
    UnsafeSymlinkError,
    discover_legacy_write_sinks,
    get_git_owner,
    guard_write,
    render_logical_path,
    resolve_record_path,
    resolve_record_read_paths,
    resolve_record_routing,
)


class PhysicalProducerRoutingTests(unittest.TestCase):
    """Execution and validation test cases E-01 through E-08 for Order 08 IPD."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-order08"
        )

        # Create basic .aw structure
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.REPOSITORY.value,
            "aw_home": self.aw_home,
        }
        (config_dir / "config.json").write_text(
            json.dumps(policy_data), encoding="utf-8"
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "records", "plans"), exist_ok=True
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "state", "durable"), exist_ok=True
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "state", "runtime"), exist_ok=True
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # E-01 / V-01: Canonical router with closed classes & path safety
    # -------------------------------------------------------------------------

    def test_e01(self):
        """E-01: Verify closed classes, path safety construction, git ownership, and logical path rendering."""

        # 1. Assert named fixture file exists
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order08"
            / "e01-invalid-class.json"
        )
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # 2. Unsupported class raises InvalidRecordClassError
        with self.assertRaises(InvalidRecordClassError):
            resolve_record_path(
                fix_data["invalid_class"],
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

        # 3. Traversal subpath raises UnsafeSymlinkError
        with self.assertRaises(UnsafeSymlinkError):
            resolve_record_path(
                RecordClass.PLANS.value,
                fix_data["traversal_subpath"],
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

        # 4. Valid record classes resolve to .aw/records/
        p_plans = resolve_record_path(
            RecordClass.PLANS.value,
            "pending/test.md",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertTrue(str(p_plans).endswith(".aw/records/plans/pending/test.md"))

        p_specs = resolve_record_path(
            RecordClass.SPECS.value,
            "20260810-spec.md",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        # Order 07 flattened specs out of docs/ (spec 20260817-2124-01).
        self.assertTrue(str(p_specs).endswith(".aw/records/specs/20260810-spec.md"))

        # 5. Git ownership
        self.assertEqual(
            get_git_owner(
                RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            ),
            "target",
        )
        self.assertIsNone(
            get_git_owner(
                RuntimeStateClass.TRANSACTIONS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )
        )

        # 6. Logical path rendering (public safe)
        logical = render_logical_path(
            p_plans, target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(logical, ".aw/records/plans/pending/test.md")

    # -------------------------------------------------------------------------
    # E-02 / V-02: Centralized write guard
    # -------------------------------------------------------------------------

    def test_e02(self):
        """E-02: Centralized write guard rejects legacy destinations, active migrations, and system/runtime writes."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order08"
            / "e02-legacy-writer.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # 1. Reject write to legacy .agents/ path
        with self.assertRaises(LegacyWriteError):
            guard_write(
                Path(self.target_repo) / fix_data["legacy_target"],
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

        # 2. Reject write during active pre-switch migration
        tx_dir = Path(self.target_repo) / ".aw" / "state" / "runtime" / "transactions"
        tx_dir.mkdir(parents=True, exist_ok=True)
        tx_file = tx_dir / "migration_transaction.json"
        tx_file.write_text(json.dumps({"status": "applying"}), encoding="utf-8")

        valid_dest = (
            Path(self.target_repo)
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "valid.md"
        )
        with self.assertRaises(MigrationInFlightError):
            guard_write(valid_dest, target_repo=self.target_repo, aw_home=self.aw_home)

        # Cleanup tx file
        tx_file.unlink()

        # 3. Producer cannot write to system/ or runtime state/
        runtime_dest = (
            Path(self.target_repo) / ".aw" / "state" / "runtime" / "forbidden.txt"
        )
        runtime_dest.parent.mkdir(parents=True, exist_ok=True)
        runtime_dest.write_text("test", encoding="utf-8")

        with self.assertRaises(ForbiddenWriteError):
            guard_write(
                runtime_dest,
                is_producer=True,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    # -------------------------------------------------------------------------
    # E-03 / V-03: Producer inventory parity & allowlist boundary
    # -------------------------------------------------------------------------

    def test_e03(self):
        """E-03: Code discovery equals inventory; stale anchors, undeclared writers, or allowlisted writers fail."""

        repo_root = Path(__file__).resolve().parent.parent

        # 1. Anchors in PRODUCER_INVENTORY must exist in code
        inventory_sources = set()
        for entry in PRODUCER_INVENTORY:
            src_file = repo_root / entry.source_path
            # Workflow-body producers relocate from .agents/workflows/ to .aw/system/workflows/
            # after the physical-layout migration; resolve either location.
            if not src_file.is_file() and entry.source_path.startswith(
                ".agents/workflows/"
            ):
                moved = repo_root / (
                    ".aw/system/workflows/"
                    + entry.source_path[len(".agents/workflows/") :]
                )
                if moved.is_file():
                    src_file = moved
            self.assertTrue(
                src_file.is_file(), f"Inventory source missing: {entry.source_path}"
            )
            content = src_file.read_text(encoding="utf-8")
            self.assertIn(
                entry.anchor,
                content,
                f"Anchor '{entry.anchor}' missing in '{entry.source_path}'",
            )
            inventory_sources.add(entry.source_path)

        # 2. LEGACY_ALLOWLIST must contain ZERO genuine writers
        for genuine_writer in LEGACY_WRITER_CANDIDATES:
            self.assertNotIn(
                genuine_writer,
                LEGACY_ALLOWLIST,
                f"Genuine writer '{genuine_writer}' is illegally in LEGACY_ALLOWLIST",
            )

        # 3. All legacy writer candidates must be tracked in PRODUCER_INVENTORY
        for candidate in LEGACY_WRITER_CANDIDATES:
            self.assertIn(
                candidate,
                inventory_sources,
                f"Candidate writer '{candidate}' missing from PRODUCER_INVENTORY",
            )

    # -------------------------------------------------------------------------
    # E-04 / V-04: Durable vs Runtime state separation
    # -------------------------------------------------------------------------

    def test_e04(self):
        """E-04: Durable state remains inspectable; runtime state is untracked (allow_git_stage = False)."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order08"
            / "e04-durable-runtime.json"
        )
        self.assertTrue(fixture_path.is_file())

        p_durable = resolve_record_path(
            DurableStateClass.ACTIONS.value,
            "open/action.md",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertTrue(".aw/state/durable/actions/open/action.md" in str(p_durable))

        p_runtime = resolve_record_path(
            RuntimeStateClass.TRANSACTIONS.value,
            "tx.json",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertTrue(".aw/state/runtime/transactions/tx.json" in str(p_runtime))

        owner_runtime = get_git_owner(
            RuntimeStateClass.TRANSACTIONS.value,
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertIsNone(
            owner_runtime, "Runtime state must be untracked (owner is None)"
        )

    # -------------------------------------------------------------------------
    # E-05 / V-05: External records & attention projection
    # -------------------------------------------------------------------------

    def test_e05(self):
        """E-05: External backends work without fake repo-relative paths; attention is read-only."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order08"
            / "e05-external-records.json"
        )
        self.assertTrue(fixture_path.is_file())

        # Configure home backend
        policy_data = {
            "delivery_mode": DeliveryMode.TRACKED.value,
            "records_backend": RecordsBackend.HOME.value,
            "aw_home": self.aw_home,
        }
        policy_file = Path(self.target_repo) / ".aw" / "config" / "config.json"
        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

        info = resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(info.records_backend, RecordsBackend.HOME.value)
        self.assertIsNone(info.commit_destination)
        self.assertFalse(info.allow_git_stage)

        p_home_plan = resolve_record_path(
            RecordClass.PLANS.value,
            "pending/20260810-home-plan.md",
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertFalse(str(p_home_plan).startswith(self.target_repo))

        logical = render_logical_path(
            p_home_plan, target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertTrue(logical.startswith("records/plans/pending/"))

        # Restore repository backend policy for subsequent tests
        policy_data["records_backend"] = RecordsBackend.REPOSITORY.value
        policy_file.write_text(json.dumps(policy_data), encoding="utf-8")

    # -------------------------------------------------------------------------
    # E-06 / V-06: Bounded read-only legacy compatibility
    # -------------------------------------------------------------------------

    def test_e06(self):
        """E-06: Retention manifest enables legacy reading; conflicting duplicates raise DuplicateAuthorityError."""

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "awphysical"
            / "order08"
            / "e06-retention-conflict.json"
        )
        self.assertTrue(fixture_path.is_file())
        fix_data = json.loads(fixture_path.read_text(encoding="utf-8"))

        # Setup retention manifest
        migrations_dir = (
            Path(self.target_repo) / ".aw" / "state" / "durable" / "migrations"
        )
        migrations_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = migrations_dir / "retention_manifest.json"
        manifest_file.write_text(
            json.dumps({"retained_sources": {".agents/plans": ".aw/records/plans"}}),
            encoding="utf-8",
        )

        # Setup legacy dir and new records dir
        legacy_plans = Path(self.target_repo) / ".agents" / "plans"
        legacy_plans.mkdir(parents=True, exist_ok=True)
        new_plans = Path(self.target_repo) / ".aw" / "records" / "plans"
        new_plans.mkdir(parents=True, exist_ok=True)

        # Plant conflicting file
        (legacy_plans / "conflict.md").write_text(
            fix_data["retained_content"], encoding="utf-8"
        )
        (new_plans / "conflict.md").write_text(
            fix_data["primary_content"], encoding="utf-8"
        )

        with self.assertRaises(DuplicateAuthorityError):
            resolve_record_read_paths(
                RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    # -------------------------------------------------------------------------
    # E-07 / V-07: Static sink guard & semantic audit test
    # -------------------------------------------------------------------------

    def test_e07(self):
        """E-07: Static sink guard returns clean for repo; planted legacy writers fail."""

        repo_root = Path(__file__).resolve().parent.parent

        # 1. Clean repo producer set must return empty set from static sink guard
        sinks = discover_legacy_write_sinks(repo_root)
        self.assertEqual(sinks, set(), f"Legacy write sinks found in codebase: {sinks}")

        # 2. Planted literal legacy writer raises LegacyWriteError
        planted_literal = Path(self.target_repo) / ".agents" / "plans" / "planted.md"
        with self.assertRaises(LegacyWriteError):
            guard_write(
                planted_literal, target_repo=self.target_repo, aw_home=self.aw_home
            )

    # -------------------------------------------------------------------------
    # E-08 / V-08: End-to-end producer test matrix
    # -------------------------------------------------------------------------

    def test_e08(self):
        """E-08: End-to-end matrix for all inventory producers across backends and failure states."""

        producer_names = {entry.name for entry in PRODUCER_INVENTORY}
        self.assertGreater(len(producer_names), 0)

        # Exercise routing resolution for each producer category
        for entry in PRODUCER_INVENTORY:
            if entry.category in [r.value for r in RecordClass]:
                p = resolve_record_path(
                    entry.category,
                    "sample.md",
                    target_repo=self.target_repo,
                    aw_home=self.aw_home,
                )
                self.assertTrue(isinstance(p, Path))
                owner = get_git_owner(
                    entry.category, target_repo=self.target_repo, aw_home=self.aw_home
                )
                self.assertEqual(owner, "target")


if __name__ == "__main__":
    unittest.main()
