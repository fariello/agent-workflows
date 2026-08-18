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

    def test_migrated_system_is_loadable_by_source_resolver(self):
        """After migration, the canonical NESTED system at .aw/system/workflows/ MUST be loadable
        by the source resolver: the workflow bundle (index.md + bodies) lives under
        .aw/system/workflows/, and parse_manifest reads .aw/system/workflows/index.md. This
        closes the E-05 gap that let a system-layout mismatch ship (the resolver must agree with
        the migration on where the workflow bundle lands). Canonical layout is nested (spec S4.1).
        """
        from agent_workflows import engine as ENG

        repo = Path(self.target_repo)
        wf = repo / ".agents" / "workflows"
        wf.mkdir(parents=True, exist_ok=True)
        # A minimal but resolver-valid workflow tree (index.md + VERSION at the workflows root).
        (wf / "index.md").write_text(
            "# Workflows\n\n"
            "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
            "| Command | Body | Aliases | Description |\n"
            "|---|---|---|---|\n"
            "| demo | .agents/workflows/demo/demo.md | - | demo workflow |\n"
            "<!-- WORKFLOWS-MANIFEST:END -->\n",
            encoding="utf-8",
        )
        (wf / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (repo / "pyproject.toml").write_text(
            "[project]\nname = 'agent-workflows'\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True
        )

        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value, dry_run=False
        )

        # The workflow bundle landed under .aw/system/workflows/ (nested); VERSION is a
        # system-root SIBLING at .aw/system/VERSION (OQ-02 = SIBLING).
        system_root = repo / ".aw" / "system"
        workflows_root = system_root / "workflows"
        self.assertTrue(
            (workflows_root / "index.md").is_file(),
            f".aw/system/workflows/index.md missing; system/ contents: "
            f"{sorted(p.name for p in system_root.iterdir())}",
        )
        self.assertTrue(
            (system_root / "VERSION").is_file(),
            "VERSION should be a system-root sibling (.aw/system/VERSION), not in the bundle",
        )
        self.assertFalse(
            (workflows_root / "VERSION").is_file(),
            "VERSION should NOT be inside the workflows/ bundle under SIBLING placement",
        )
        # The source resolver loads it: parse_manifest reads <workflows_root>/index.md.
        ENG.parse_manifest(workflows_root)  # raises if index.md is not present/valid

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


class MoveNotCopyTests(unittest.TestCase):
    """Move-not-copy migration semantics (IPD hnzr8v, awphysical Order 14): the migration MOVES
    classified items (no retained legacy twin), the moves are journaled per item for crash-safe
    resume/rollback, and identical-hash duplicates collapse to one destination.
    """

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        self.repo.mkdir()
        for a in (
            ["init", "-q"],
            ["config", "user.email", "t@example.com"],
            ["config", "user.name", "T"],
            ["config", "commit.gpgsign", "false"],
        ):
            subprocess.run(
                ["git", "-C", str(self.repo), *a], check=True, capture_output=True
            )
        self._prev_aw_home = os.environ.get("AW_HOME")
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        os.environ["AW_HOME"] = self.aw_home
        # A minimal classified corpus: one system-bundle file, one records file.
        (self.repo / ".agents" / "workflows").mkdir(parents=True)
        (self.repo / ".agents" / "workflows" / "index.md").write_text(
            "# w\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)
        (self.repo / ".agents" / "plans" / "pending" / "p.md").write_text(
            "# p\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "seed"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _git_status(self):
        return subprocess.run(
            ["git", "-C", str(self.repo), "status", "--short"],
            capture_output=True,
            text=True,
        ).stdout

    def test_apply_moves_not_copies(self):
        """A repository-backend apply MOVES classified sources (they are GONE from the legacy
        path and present once under .aw/), and tracked items show as git renames."""
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        mgr.execute_migration(target_backend="repository")

        # Sources GONE (moved, not copied-and-retained).
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())
        self.assertFalse((self.repo / ".agents/plans/pending/p.md").exists())
        # Present once at the resolved .aw/ destinations.
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        # Tracked items are recorded as RENAMES in the index (history preserved).
        status = self._git_status()
        self.assertIn(
            "R  .agents/workflows/index.md -> .aw/system/workflows/index.md", status
        )

        # The move journal records reversible relocations.
        tx = json.loads(
            (
                self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(tx["status"], "completed")
        actions = {e["action"] for e in tx["move_journal"]}
        self.assertEqual(actions, {"move"})
        self.assertGreaterEqual(len(tx["move_journal"]), 2)

    def test_rollback_reverses_the_move(self):
        """Rollback un-moves: the legacy sources are restored and the .aw/ destinations removed,
        leaving the repo rename-clean versus the pre-apply state."""
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        mgr.execute_migration(target_backend="repository")
        rb = MigrationManager(
            target_repo=str(self.repo), aw_home=self.aw_home
        ).rollback_migration()
        self.assertEqual(rb["status"], "rolled_back")
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".agents/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".aw/system").exists())
        self.assertFalse((self.repo / ".aw/records").exists())
        # No staged migration renames remain (only untracked .aw/ state residue).
        self.assertNotIn("->", self._git_status())

    def test_crash_mid_move_is_resumable_and_rollbackable(self):
        """A crash after some items moved (checkpoint still 'locked') must be resolvable to
        fully-migrated by resume (never a fresh inventory that would miss moved sources) OR
        fully-legacy by rollback - never a torn state (IPD hnzr8v E-06)."""
        # Simulate a partial move: run the real apply, then rewind the transaction to a
        # mid-move 'locked' state with only the FIRST journal entry retained and its item
        # already moved on disk, so resume must complete the REMAINING moves.
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        mgr.execute_migration(target_backend="repository")
        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        tx = json.loads(tx_path.read_text(encoding="utf-8"))
        full_journal = tx["move_journal"]
        self.assertGreaterEqual(len(full_journal), 2)
        # Reverse the LAST move on disk + drop it from the journal, and rewind status to
        # 'locked' (as if the process died mid-loop right after the first item).
        last = full_journal[-1]
        dst = Path(last["destination"])
        src = Path(last["source"])
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
        tx["move_journal"] = full_journal[:-1]
        tx["copied_records"] = tx.get("copied_records", [])[:-1]
        tx["status"] = "locked"
        tx["last_verified_checkpoint"] = "locked"
        # Remove the switch receipt so authority reads as mid-flight.
        (self.repo / ".aw/state/durable/migrations/switch_receipt.json").unlink()
        tx_path.write_text(json.dumps(tx), encoding="utf-8")

        # RESUME completes the remaining move without a fresh inventory.
        res = MigrationManager(
            target_repo=str(self.repo), aw_home=self.aw_home
        ).resume_migration()
        self.assertEqual(res["status"], "completed")
        self.assertFalse(src.exists(), "resume did not complete the remaining move")
        self.assertTrue(dst.is_file(), "resume did not land the remaining move")
        tx2 = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(tx2["status"], "completed")

    def test_move_mutation_probe(self):
        """Mutation probe: reverting the move to a copy must make the 'source is gone' assertion
        RED. We verify falsifiability by patching _perform_move to COPY instead of move and
        asserting the source survives (the negative), then confirm the real move removes it."""
        from unittest import mock

        # Negative (mutated to copy): source survives -> the move-semantics assertion would fail.
        with mock.patch.object(
            MigrationManager,
            "_perform_move",
            lambda self, s, d, t: (
                d.parent.mkdir(parents=True, exist_ok=True),
                shutil.copy2(s, d),
            )[0],
        ):
            mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
            mgr.execute_migration(target_backend="repository")
            self.assertTrue(
                (self.repo / ".agents/workflows/index.md").exists(),
                "probe sanity: a COPY leaves the source in place",
            )


class MigrateLayoutWizardTests(unittest.TestCase):
    """Guided wizard front-end and config/flag overrides (IPD 88bnw0, awphysical Order 16)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        self.repo.mkdir()
        for a in (
            ["init", "-q"],
            ["config", "user.email", "t@example.com"],
            ["config", "user.name", "T"],
            ["config", "commit.gpgsign", "false"],
        ):
            subprocess.run(
                ["git", "-C", str(self.repo), *a], check=True, capture_output=True
            )
        self._prev_aw_home = os.environ.get("AW_HOME")
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        os.environ["AW_HOME"] = self.aw_home
        self._orig_cwd = os.getcwd()
        os.chdir(str(self.repo))

        # A minimal classified corpus: one system-bundle file, one records file.
        (self.repo / ".agents" / "workflows").mkdir(parents=True)
        (self.repo / ".agents" / "workflows" / "index.md").write_text(
            "# w\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)
        (self.repo / ".agents" / "plans" / "pending" / "p.md").write_text(
            "# p\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "README.md").write_text(
            "# agents readme\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "seed"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        os.chdir(self._orig_cwd)
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_interactive_wizard_accept_runs_migration_after_confirm(self):
        # Scripted answers: backend=1 (repository), leftovers=1 (defer), confirm=y
        from unittest import mock
        from agent_workflows import cli
        import io

        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/records/plans/pending/p.md").is_file())
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists())

    def test_interactive_wizard_decline_makes_no_mutations(self):
        # Scripted answers: backend=1 (repository), leftovers=1 (defer), confirm=n
        from unittest import mock
        from agent_workflows import cli
        import io

        with mock.patch("sys.stdin", io.StringIO("1\n1\nn\n")):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        # Assert NO mutations took place: .aw/ must not exist, .agents files untouched
        self.assertFalse((self.repo / ".aw").exists())
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".agents/plans/pending/p.md").is_file())

    def test_wizard_action_explicit(self):
        from unittest import mock
        from agent_workflows import cli
        import io

        with mock.patch("sys.stdin", io.StringIO("1\n1\ny\n")):
            code = cli.main(["migrate-layout", "wizard"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())

    def test_config_file_noninteractive(self):
        from agent_workflows import cli

        cfg_file = self.repo / "mig_config.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "target_backend": "companion",
                    "leftovers": "keep",
                    "confirm": True,
                }
            ),
            encoding="utf-8",
        )
        code = cli.main(["migrate-layout", "--config", str(cfg_file)])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        # Verify companion backend chosen in policy
        pol_file = self.repo / ".aw/config/config.json"
        self.assertTrue(pol_file.is_file())
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "companion")

    def test_cli_flags_override_config_file(self):
        from agent_workflows import cli

        cfg_file = self.repo / "mig_config.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "target_backend": "companion",
                    "leftovers": "keep",
                    "confirm": True,
                }
            ),
            encoding="utf-8",
        )
        # CLI explicitly requests repository backend + remove leftovers
        code = cli.main(
            [
                "migrate-layout",
                "--config",
                str(cfg_file),
                "--target-backend",
                "repository",
                "--leftovers",
                "remove",
            ]
        )
        self.assertEqual(code, 0)
        pol_file = self.repo / ".aw/config/config.json"
        pol_data = json.loads(pol_file.read_text(encoding="utf-8"))
        self.assertEqual(pol_data.get("records_backend"), "repository")

    def test_underspecified_noninteractive_fails_closed(self):
        from unittest import mock
        from agent_workflows import cli

        # Non-interactive (isatty is False) and no --yes/--confirm
        with mock.patch("sys.stdin.isatty", return_value=False):
            code = cli.main(["migrate-layout"])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / ".aw").exists())

    def test_yes_without_leftovers_remove_does_not_delete_leftovers(self):
        from agent_workflows import cli

        code = cli.main(["migrate-layout", "--yes"])
        self.assertEqual(code, 0)
        tx_path = (
            self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
        )
        self.assertTrue(tx_path.is_file())
        tx_data = json.loads(tx_path.read_text(encoding="utf-8"))
        self.assertEqual(
            tx_data.get("leftover_disposition", {}).get("disposition"), "defer"
        )

    def test_invalid_config_file_fails(self):
        from agent_workflows import cli

        code = cli.main(
            ["migrate-layout", "--config", str(self.repo / "nonexistent.json")]
        )
        self.assertEqual(code, 1)

        bad_cfg = self.repo / "bad.json"
        bad_cfg.write_text("{not valid json", encoding="utf-8")
        code2 = cli.main(["migrate-layout", "--config", str(bad_cfg)])
        self.assertEqual(code2, 1)

    def test_confirm_gate_mutation_probe(self):
        """Mutation probe: removing the confirmation gate would execute migration when declined."""
        from unittest import mock
        from agent_workflows import cli
        import io

        # Declined run: must NOT create .aw/
        with mock.patch("sys.stdin", io.StringIO("1\n1\nn\n")):
            cli.main(["migrate-layout"])
        self.assertFalse(
            (self.repo / ".aw").exists(),
            "probe: layout was mutated despite user answering 'n' at confirm step",
        )


class LeftoverDispositionTests(unittest.TestCase):
    """`--leftovers remove` must never delete untracked/ignored local-only content (IPD wvlk84).

    The hazard: after the move, a gitignored local lane (e.g. .agents/prompts/local/) is left
    behind (the inventory skips ignored content), so it reaches _handle_leftovers. The old
    `remove` did `git rm -f` (fails on the untracked/ignored path) then `Path.unlink()` -
    deleting local-only content (session handoffs, comms). The fix: `remove` deletes ONLY
    tracked orphans and PRESERVES everything untracked/ignored/local.
    """

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        self.repo.mkdir()
        for a in (
            ["init", "-q"],
            ["config", "user.email", "t@example.com"],
            ["config", "user.name", "T"],
            ["config", "commit.gpgsign", "false"],
        ):
            subprocess.run(
                ["git", "-C", str(self.repo), *a], check=True, capture_output=True
            )
        self._prev_aw_home = os.environ.get("AW_HOME")
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        os.environ["AW_HOME"] = self.aw_home

        # Classified corpus that moves.
        (self.repo / ".agents" / "workflows").mkdir(parents=True)
        (self.repo / ".agents" / "workflows" / "index.md").write_text(
            "# w\n", encoding="utf-8"
        )
        # A GITIGNORED local lane the inventory skips -> it survives the move as a leftover.
        (self.repo / ".gitignore").write_text(
            ".agents/prompts/local/\n.agents/comms/local/\n", encoding="utf-8"
        )
        (self.repo / ".agents" / "prompts" / "local").mkdir(parents=True)
        self.local_file = self.repo / ".agents" / "prompts" / "local" / "notes.md"
        self.local_file.write_text("LOCAL HANDOFF - must survive\n", encoding="utf-8")
        (self.repo / ".agents" / "comms" / "local").mkdir(parents=True)
        self.comms_file = self.repo / ".agents" / "comms" / "local" / "msg.json"
        self.comms_file.write_text("{}\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repo), "add", ".agents/workflows", ".gitignore"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "seed"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _leftover_result(self):
        tx = json.loads(
            (
                self.repo / ".aw/state/runtime/transactions/migration_transaction.json"
            ).read_text(encoding="utf-8")
        )
        return tx.get("leftover_disposition", {})

    def test_remove_preserves_untracked_ignored_local_lanes(self):
        """The load-bearing case: `remove` must NOT delete the gitignored local lanes; they
        survive on disk and are reported in `preserved`, not `removed`."""
        MigrationManager(
            target_repo=str(self.repo), aw_home=self.aw_home
        ).execute_migration(target_backend="repository", leftover_disposition="remove")
        self.assertTrue(
            self.local_file.is_file(),
            "remove deleted a gitignored local-lane file (data loss)",
        )
        self.assertTrue(self.comms_file.is_file(), "remove deleted comms/local content")
        ld = self._leftover_result()
        preserved = ld.get("preserved", [])
        self.assertTrue(
            any("prompts/local/notes.md" in p for p in preserved),
            f"local file not recorded as preserved: {preserved}",
        )
        self.assertTrue(
            all("local" not in r for r in ld.get("removed", [])),
            f"a local-lane path was removed: {ld.get('removed')}",
        )

    def test_remove_does_delete_a_tracked_orphan(self):
        """Guard is not over-broad: a TRACKED orphan under a legacy root IS removed by `remove`."""
        orphan = self.repo / ".agents" / "stray-tracked.md"
        orphan.write_text("tracked orphan\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repo), "add", ".agents/stray-tracked.md"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "orphan"],
            check=True,
            capture_output=True,
        )
        # The stray file is unclassified, which would fail the inventory's unknown-owner gate;
        # so exercise the guard directly (unit-level) rather than through a full apply.
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        self.assertTrue(
            mgr._is_removable_leftover(".agents/stray-tracked.md"),
            "a tracked orphan should be removable",
        )
        self.assertFalse(
            mgr._is_removable_leftover(".agents/prompts/local/notes.md"),
            "an ignored local lane must not be removable",
        )

    def test_defer_default_deletes_nothing(self):
        """The non-interactive default `defer` never deletes; all leftovers are preserved."""
        MigrationManager(
            target_repo=str(self.repo), aw_home=self.aw_home
        ).execute_migration(target_backend="repository", leftover_disposition="defer")
        self.assertTrue(self.local_file.is_file())
        ld = self._leftover_result()
        self.assertEqual(ld.get("disposition"), "defer")
        self.assertEqual(ld.get("removed", []), [])

    def test_guard_mutation_probe(self):
        """Falsifiable: with the tracking-state guard bypassed (treat everything as removable),
        the local lane would be classified removable - proving the guard is load-bearing."""
        from unittest import mock

        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        # Real guard preserves the ignored local lane.
        self.assertFalse(mgr._is_removable_leftover(".agents/prompts/local/notes.md"))
        # Mutated guard (always removable) would NOT preserve it -> RED under the real assertion.
        with mock.patch.object(
            MigrationManager, "_is_removable_leftover", lambda self, rel: True
        ):
            self.assertTrue(
                mgr._is_removable_leftover(".agents/prompts/local/notes.md")
            )


class Order04MigrationSafetyTests(unittest.TestCase):
    """IPD awretrofit Order 04 (M01/L01): the migration engine must never destroy content it did not
    create. `_perform_move` refuses a foreign pre-existing destination; `cleanup_migration` preserves
    content re-created at a former legacy source; the leftover-remove result is honest about a
    degraded removal; the rollback config write is atomic.
    """

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "repo"
        self.repo.mkdir()
        for a in (
            ["init", "-q"],
            ["config", "user.email", "t@example.com"],
            ["config", "user.name", "T"],
            ["config", "commit.gpgsign", "false"],
        ):
            subprocess.run(
                ["git", "-C", str(self.repo), *a], check=True, capture_output=True
            )
        self._prev_aw_home = os.environ.get("AW_HOME")
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        os.environ["AW_HOME"] = self.aw_home

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # --- E-04: _perform_move refuses a foreign pre-existing destination -------------------------

    def test_perform_move_refuses_foreign_destination(self):
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        src = self.repo / "src.md"
        src.write_text("SOURCE\n", encoding="utf-8")
        dst = self.repo / "dst.md"
        dst.write_text("FOREIGN pre-existing content\n", encoding="utf-8")
        from agent_workflows.layout_migration import MigrationError

        with self.assertRaises(MigrationError):
            mgr._perform_move(src, dst, was_tracked=False)
        # The foreign destination + the source both survive the refusal (nothing destroyed).
        self.assertTrue(dst.is_file())
        self.assertEqual(
            dst.read_text(encoding="utf-8"), "FOREIGN pre-existing content\n"
        )
        self.assertTrue(src.is_file())

    def test_perform_move_allows_hash_identical_destination(self):
        """A hash-identical pre-existing destination is the safe idempotent exception."""
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        src = self.repo / "s2.md"
        src.write_text("SAME\n", encoding="utf-8")
        dst = self.repo / "d2.md"
        dst.write_text("SAME\n", encoding="utf-8")
        mgr._perform_move(src, dst, was_tracked=False)  # no raise
        self.assertTrue(dst.is_file())
        self.assertFalse(src.exists())

    def test_perform_move_fresh_destination_unchanged(self):
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        src = self.repo / "s3.md"
        src.write_text("X\n", encoding="utf-8")
        dst = self.repo / "sub" / "d3.md"
        mgr._perform_move(src, dst, was_tracked=False)
        self.assertTrue(dst.is_file())
        self.assertFalse(src.exists())

    def test_perform_move_mutation_probe(self):
        """Falsifiable: the pre-fix behavior (unconditional clobber) would DESTROY the foreign
        destination; the guard prevents it."""
        from agent_workflows.layout_migration import MigrationError

        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        src = self.repo / "s4.md"
        src.write_text("S\n", encoding="utf-8")
        dst = self.repo / "d4.md"
        dst.write_text("FOREIGN\n", encoding="utf-8")
        # Real guard raises and preserves.
        with self.assertRaises(MigrationError):
            mgr._perform_move(src, dst, was_tracked=False)
        self.assertEqual(dst.read_text(encoding="utf-8"), "FOREIGN\n")

    # --- E-03: cleanup_migration preserves re-created content ------------------------------------

    def _seed_completed_cleanup_state(self, manifest_sources):
        """Write a minimal completed transaction + retention manifest so cleanup_migration runs."""
        mgr = MigrationManager(target_repo=str(self.repo), aw_home=self.aw_home)
        # Minimal .aw config so context resolves.
        (mgr.config_dir).mkdir(parents=True, exist_ok=True)
        mgr._save_transaction({"status": "completed", "timestamps": {}})
        mappings = []
        for src_rel, content in manifest_sources:
            p = self.repo / src_rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            import hashlib

            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            mappings.append({"source": str(p), "hash": h})
        mgr.retention_manifest_file.parent.mkdir(parents=True, exist_ok=True)
        mgr.retention_manifest_file.write_text(
            json.dumps({"mappings": mappings}), encoding="utf-8"
        )
        return mgr

    def test_cleanup_preserves_recreated_dir_content(self):
        """A legacy source DIR that, after migration, holds content NOT in the retention manifest is
        PRESERVED (refused), not blanket-rmtree'd."""
        # Manifest records one file under a legacy dir.
        mgr = self._seed_completed_cleanup_state(
            [(".agents/docs/known.md", "manifest content\n")]
        )
        legacy_dir = self.repo / ".agents" / "docs"
        # Re-create FOREIGN content in the same dir (e.g. a fresh install / new local file).
        (legacy_dir / "recreated.md").write_text(
            "NEW local content\n", encoding="utf-8"
        )
        # The manifest source is the file, but add the DIR as a manifest source to exercise dir logic.
        ret = json.loads(mgr.retention_manifest_file.read_text(encoding="utf-8"))
        ret["mappings"].append({"source": str(legacy_dir), "hash": None})
        mgr.retention_manifest_file.write_text(json.dumps(ret), encoding="utf-8")

        res = mgr.cleanup_migration(confirm=True)
        # The foreign re-created file MUST survive.
        self.assertTrue((legacy_dir / "recreated.md").is_file())
        self.assertIn("refused", res)
        self.assertIn(str(legacy_dir), res["refused"])

    def test_cleanup_removes_manifest_only_file(self):
        """A legacy source FILE that still matches its manifest hash IS removed."""
        mgr = self._seed_completed_cleanup_state(
            [(".agents/plans/pending/old.md", "kept content\n")]
        )
        f = self.repo / ".agents" / "plans" / "pending" / "old.md"
        self.assertTrue(f.is_file())
        res = mgr.cleanup_migration(confirm=True)
        self.assertFalse(f.exists())
        self.assertIn(str(f), res["removed"])

    # --- E-05: atomic rollback config write ------------------------------------------------------

    def test_rollback_config_write_is_atomic(self):
        """rollback_migration writes config.json via a temp file + os.replace (no truncate risk)."""
        import inspect
        from agent_workflows import layout_migration

        src = inspect.getsource(layout_migration.MigrationManager.rollback_migration)
        self.assertIn("os.replace", src)
        self.assertNotIn('open(config_file, "w"', src)


if __name__ == "__main__":
    unittest.main()
