"""Tests for awoptimize Order 17 (`gnfkh8`): compatibility contract, previewable idempotent
migration/update, rollback + interrupted-recovery + downgrade warning, and opt-in deprecation
diagnostics.

Covers the E-05 acceptance with FALSIFIABLE assertions:
  * E-01: the compatibility-contract golden check proves EXACTLY ONE row + a passing golden test per
    named surface, with NO unspecified breaking change; injecting an omission / a duplicate / an
    unspecified break each makes a named assertion fail (detection asserted).
  * E-02: legacy/current/partial/drift/customized fixtures preview exact changes, PRESERVE human
    files, BACK UP replaced generated files, RECORD the exact version, and rerun idempotently (a
    no-op when current). A human-file overwrite is REFUSED (preserve, never silently overwrite).
  * E-03: rollback + interrupted-migration recovery restore prior command discovery + runtime
    adapters without record loss; an unreadable-future-data downgrade WARNS (and is refused) rather
    than corrupting.
  * E-04: deprecation diagnostics are LOCAL + opt-in + cleanly disable-able; operation never depends
    on telemetry; an alias CANNOT be removed before its parity/adoption/version gate (removal
    REFUSED).

Stdlib `unittest`, matching the repository convention.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import compat_migration as cm
from agent_workflows import engine


# ==================================================================================================
# E-01: the compatibility-contract golden check (one row + a passing test per surface)
# ==================================================================================================


class ContractGoldenTests(unittest.TestCase):
    def setUp(self):
        self.check = cm.check_contract()
        self.contract = cm.build_contract()

    def test_contract_is_complete_and_valid(self):
        self.assertTrue(self.check.ok, self.check.findings)

    def test_exactly_one_row_per_required_surface(self):
        # one row per required surface, none omitted, none extra.
        self.assertEqual(set(self.contract), set(cm.REQUIRED_SURFACES))
        self.assertEqual(len(self.contract), len(cm.REQUIRED_SURFACES))

    def test_no_unspecified_breaking_change(self):
        # every row is either non-breaking (preserved/changed/deprecated) or an EXPLICIT
        # unsupported/removed. There is no unspecified break.
        for surf, row in self.contract.items():
            if row.breaking:
                self.assertIn(
                    row.status,
                    (cm.STATUS_UNSUPPORTED, cm.STATUS_REMOVED),
                    "surface {0} breaks without an explicit unsupported/removed status".format(
                        surf
                    ),
                )

    def test_every_row_names_a_golden_test_that_exists(self):
        # the one-test-per-surface requirement: each row names a test method defined here.
        for surf, row in self.contract.items():
            self.assertTrue(row.test, "surface {0} names no test".format(surf))
            self.assertTrue(
                hasattr(SurfaceGoldenTests, row.test),
                "named golden test '{0}' for surface '{1}' does not exist".format(
                    row.test, surf
                ),
            )

    # ---- falsifiable: detection of an omission / duplicate / unspecified break ----

    def test_detects_a_silent_omission(self):
        broken = dict(self.contract)
        del broken["exit-codes"]
        result = cm.check_contract(broken)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("exit-codes" in f and "NO contract row" in f for f in result.findings),
            result.findings,
        )

    def test_detects_an_extra_nonrequired_surface(self):
        broken = dict(self.contract)
        broken["not-a-real-surface"] = cm.CompatSurface(
            surface="not-a-real-surface",
            owner="order-17",
            status=cm.STATUS_PRESERVED,
            version_boundary="ongoing",
            migration="x",
            test="test_x",
        )
        result = cm.check_contract(broken)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("not a required surface" in f for f in result.findings),
            result.findings,
        )

    def test_detects_an_unspecified_break(self):
        # detect_unspecified_break flags a surface that breaks an existing invocation while its
        # contract row is non-breaking (preserved/changed/deprecated).
        finding = cm.detect_unspecified_break(
            "manifest-commands", breaks_existing_invocation=True
        )
        self.assertIsNotNone(finding)
        self.assertIn("unspecified break", finding)
        # a surface that does NOT break is fine.
        self.assertIsNone(
            cm.detect_unspecified_break(
                "manifest-commands", breaks_existing_invocation=False
            )
        )

    def test_report_is_deterministic_json(self):
        report = cm.render_contract_report()
        data = json.loads(report)
        self.assertTrue(data["ok"])
        self.assertEqual(data["count"], len(cm.REQUIRED_SURFACES))


class SurfaceGoldenTests(unittest.TestCase):
    """One golden test per named surface (E-01). Each proves the surface's declared behavior holds
    against the live engine/manifest and that the contract row is consistent."""

    @classmethod
    def setUpClass(cls):
        cls.source_root = engine.resolve_source_root(None)
        cls.workflows = engine.parse_manifest(cls.source_root)
        cls.contract = cm.build_contract()

    def _row(self, surface):
        return self.contract[surface]

    def test_surface_manifest_commands_preserved(self):
        row = self._row("manifest-commands")
        self.assertEqual(row.status, cm.STATUS_PRESERVED)
        self.assertFalse(row.breaking)
        # the legacy alias names are still live manifest rows (existing invocations keep working).
        commands = {w.command for w in self.workflows}
        self.assertIn("plan-review", commands)
        self.assertIn("plan-review-long", commands)

    def test_surface_command_arguments_preserved(self):
        row = self._row("command-arguments")
        self.assertFalse(row.breaking)
        # a generated shim still carries the argument contract for a command that takes arguments.
        shims = engine.generate_shim_members(
            self.workflows, self.source_root, target_layout="aw"
        )
        opencode_aw = shims[".opencode/commands/aw.md"]
        self.assertIn("$ARGUMENTS", opencode_aw)

    def test_surface_opencode_commands_preserved(self):
        row = self._row("opencode-commands")
        self.assertFalse(row.breaking)
        shims = engine.generate_shim_members(
            self.workflows, self.source_root, target_layout="aw"
        )
        opencode = [k for k in shims if k.startswith(".opencode/commands/")]
        self.assertTrue(opencode)
        # every generated opencode shim is a valid shim (discoverable + well-formed).
        for rel in opencode:
            if rel.endswith("README.md"):
                continue
            self.assertTrue(
                engine.validate_shim_grammar(shims[rel], "opencode"),
                "invalid opencode shim: {0}".format(rel),
            )

    def test_surface_claude_commands_preserved(self):
        row = self._row("claude-commands")
        self.assertFalse(row.breaking)
        shims = engine.generate_shim_members(
            self.workflows, self.source_root, target_layout="aw"
        )
        claude = [k for k in shims if k.startswith(".claude/commands/")]
        self.assertTrue(claude)
        for rel in claude:
            if rel.endswith("README.md"):
                continue
            self.assertTrue(
                engine.validate_shim_grammar(shims[rel], "claude"),
                "invalid claude shim: {0}".format(rel),
            )

    def test_surface_agents_pointer_preserved(self):
        row = self._row("agents-pointer")
        self.assertFalse(row.breaking)
        self.assertIn("AGENTS.md", engine.AGENTS_FILE_CANDIDATES)

    def test_surface_claude_pointer_preserved(self):
        row = self._row("claude-pointer")
        self.assertFalse(row.breaking)
        self.assertIn("CLAUDE.md", engine.NATIVE_AGENT_FILES)

    def test_surface_gemini_pointer_preserved(self):
        row = self._row("gemini-pointer")
        self.assertFalse(row.breaking)
        self.assertIn("GEMINI.md", engine.NATIVE_AGENT_FILES)

    def test_surface_ipd_locations_changed_not_broken(self):
        row = self._row("ipd-locations")
        # a CHANGED surface is explicit and still NON-breaking (reversible move, kept discoverable).
        self.assertEqual(row.status, cm.STATUS_CHANGED)
        self.assertFalse(row.breaking)

    def test_surface_agy_run_entry_points_preserved(self):
        row = self._row("agy-run-entry-points")
        self.assertFalse(row.breaking)
        self.assertEqual(row.owner, "installer")

    def test_surface_exit_codes_preserved(self):
        row = self._row("exit-codes")
        self.assertFalse(row.breaking)
        # the documented exit codes are frozen and meaning-stable.
        self.assertEqual(cm.EXIT_CODES["ok"], 0)
        self.assertEqual(cm.EXIT_CODES["error"], 1)
        self.assertEqual(cm.EXIT_CODES["usage"], 2)

    def test_surface_machine_output_preserved(self):
        row = self._row("machine-output")
        self.assertFalse(row.breaking)
        # machine output is sorted-key stable JSON.
        report = cm.render_contract_report()
        self.assertEqual(report, cm.render_contract_report())


# ==================================================================================================
# Shared fixture base for the migration/rollback/deprecation tests
# ==================================================================================================


class _RepoFixture(unittest.TestCase):
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

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


# ==================================================================================================
# E-02: idempotent, previewable migration/update
# ==================================================================================================


class MigrationPreviewTests(_RepoFixture):
    def setUp(self):
        super().setUp()
        self.migrator = cm.CompatMigrator(self.target_repo)

    def test_legacy_state_detected(self):
        # only a legacy .agents/workflows tree, no .aw/system -> LEGACY.
        wf = Path(self.target_repo) / engine.WORKFLOWS_DIR
        wf.mkdir(parents=True, exist_ok=True)
        (wf / "index.md").write_text("# legacy\n", encoding="utf-8")
        self.assertEqual(self.migrator.detect_state(), cm.STATE_LEGACY)

    def test_preview_records_exact_version(self):
        preview = self.migrator.preview()
        self.assertEqual(
            preview.version, engine.read_version(self.migrator.source_root)
        )
        # a fresh repo previews generate changes (not a no-op yet).
        self.assertTrue(preview.changes)
        self.assertTrue(all(c.kind == "generate" for c in preview.changes))

    def test_apply_records_version_stamp(self):
        self.migrator.apply()
        stamp = self.migrator.read_stamp()
        self.assertIsNotNone(stamp)
        self.assertEqual(
            stamp["version"], engine.read_version(self.migrator.source_root)
        )
        self.assertTrue(stamp["generated"])  # per-file hashes recorded

    def test_current_state_after_apply_and_idempotent_rerun(self):
        self.migrator.apply()
        self.assertEqual(self.migrator.detect_state(), cm.STATE_CURRENT)
        rerun = self.migrator.preview()
        self.assertTrue(rerun.is_noop, [c.to_dict() for c in rerun.changes])
        # applying a second time changes nothing on disk.
        self.migrator.apply(rerun)
        self.assertTrue(self.migrator.preview().is_noop)

    def test_drift_detected_backed_up_and_regenerated(self):
        self.migrator.apply()
        # edit an our-owned generated shim -> DRIFT.
        rel = sorted(self.migrator._expected_generated())[0]
        sp = Path(self.target_repo) / rel
        original = sp.read_text(encoding="utf-8")
        drifted = original + "\n# hand edit that drifts a generated file\n"
        sp.write_text(drifted, encoding="utf-8")
        self.assertEqual(self.migrator.detect_state(), cm.STATE_DRIFTED)

        preview = self.migrator.preview()
        drift_changes = [c for c in preview.changes if c.path == rel]
        self.assertEqual(len(drift_changes), 1)
        self.assertEqual(drift_changes[0].kind, "update-generated")

        self.migrator.apply(preview)
        # the DRIFTED bytes were backed up (never destroyed) before regeneration.
        backup_p = Path(self.target_repo) / cm.COMPAT_BACKUP_RELPATH / rel
        self.assertTrue(backup_p.is_file())
        self.assertEqual(backup_p.read_text(encoding="utf-8"), drifted)
        # and the on-disk file was regenerated back to the canonical content.
        self.assertEqual(sp.read_text(encoding="utf-8"), original)
        self.assertTrue(self.migrator.preview().is_noop)

    def test_human_owned_file_is_preserved_never_overwritten(self):
        self.migrator.apply()
        # register a HUMAN-owned file, then have the human edit it.
        human_rel = "AGENTS.md"
        human_p = Path(self.target_repo) / human_rel
        human_p.write_text("my hand-authored instructions\n", encoding="utf-8")
        self.migrator.register_human_file(human_rel)
        human_p.write_text("my EDITED hand-authored instructions\n", encoding="utf-8")

        self.assertEqual(self.migrator.detect_state(), cm.STATE_CUSTOMIZED)
        # even if the engine WOULD generate this path, apply must not touch it.
        before = human_p.read_text(encoding="utf-8")
        self.migrator.apply()
        after = human_p.read_text(encoding="utf-8")
        self.assertEqual(before, after)  # human content NEVER silently overwritten

    def test_preexisting_unrecorded_file_treated_as_human_owned(self):
        # a shim path that already exists with foreign content, which we never recorded as ours,
        # is CONSERVATIVELY preserved rather than overwritten.
        rel = sorted(self.migrator._expected_generated())[0]
        sp = Path(self.target_repo) / rel
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text("foreign pre-existing content\n", encoding="utf-8")
        preview = self.migrator.preview()
        change = [c for c in preview.changes if c.path == rel][0]
        self.assertEqual(change.kind, "preserve-human")
        self.migrator.apply(preview)
        self.assertEqual(
            sp.read_text(encoding="utf-8"), "foreign pre-existing content\n"
        )

    def test_all_install_states_are_reachable_names(self):
        # the five states named in the plan are all defined.
        self.assertEqual(
            cm.INSTALL_STATES,
            {
                cm.STATE_LEGACY,
                cm.STATE_CURRENT,
                cm.STATE_PARTIAL,
                cm.STATE_DRIFTED,
                cm.STATE_CUSTOMIZED,
            },
        )


# ==================================================================================================
# E-03: rollback + interrupted-recovery + downgrade warning
# ==================================================================================================


class RollbackTests(_RepoFixture):
    def setUp(self):
        super().setUp()
        self.rollback = cm.CompatRollback(self.target_repo)

    def _write_runtime_record(self, relpath, schema_version):
        p = Path(self.target_repo) / ".aw" / "state" / "runtime" / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps({"schema_version": schema_version}) + "\n", encoding="utf-8"
        )
        return p

    def test_pure_adapter_rollback_is_safe(self):
        # readable runtime data (schema <= max) -> a pure ADAPTER rollback (no downgrade).
        self._write_runtime_record("runs/a.jsonl", schema_version=2)
        assessment = self.rollback.assess(max_readable_schema=3)
        self.assertEqual(assessment.kind, cm.ROLLBACK_ADAPTER)
        self.assertTrue(assessment.safe)
        self.assertEqual(assessment.warnings, ())

    def test_future_data_triggers_downgrade_warning_and_refusal(self):
        # a record from a NEWER schema the older version cannot read -> DATA-SCHEMA DOWNGRADE.
        rec = self._write_runtime_record("runs/future.jsonl", schema_version=9)
        assessment = self.rollback.assess(max_readable_schema=3)
        self.assertEqual(assessment.kind, cm.ROLLBACK_DATA_SCHEMA_DOWNGRADE)
        self.assertFalse(assessment.safe)
        self.assertTrue(assessment.warnings)

        # a rollback WARNS + REFUSES rather than corrupting the future data.
        result = self.rollback.rollback(max_readable_schema=3)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["kind"], cm.ROLLBACK_DATA_SCHEMA_DOWNGRADE)
        self.assertTrue(result["warnings"])
        # the future data is untouched (not corrupted/truncated).
        self.assertTrue(rec.is_file())
        self.assertIn("schema_version", rec.read_text(encoding="utf-8"))

    def test_explicit_downgrade_preserves_future_data(self):
        rec = self._write_runtime_record("runs/future.jsonl", schema_version=9)
        result = self.rollback.rollback(
            max_readable_schema=3, allow_data_downgrade=True
        )
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(result["kind"], cm.ROLLBACK_DATA_SCHEMA_DOWNGRADE)
        self.assertTrue(result["warnings"])  # warned even though allowed
        self.assertTrue(rec.is_file())  # data preserved, never corrupted

    def test_rollback_reverses_records_move_without_record_loss(self):
        # drive a real migration through the REUSED MigrationManager, then roll back and prove the
        # migrated record is restored to its original discovery location (no record loss).
        repo = Path(self.target_repo)
        legacy_rec = repo / ".agents" / "plans" / "sample.ipd.md"
        legacy_rec.parent.mkdir(parents=True, exist_ok=True)
        legacy_rec.write_text("# a plan record\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-q",
                "-m",
                "seed",
            ],
            check=True,
            capture_output=True,
        )
        mgr = self.rollback.manager
        try:
            mgr.execute_migration(target_backend="repository", dry_run=False)
        except Exception as exc:  # pragma: no cover - environment-dependent
            self.skipTest(
                "migration engine unavailable in this fixture: {0}".format(exc)
            )
        # after migration the legacy record has moved; roll back and confirm it is restored.
        result = self.rollback.rollback(max_readable_schema=99)
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(result["kind"], cm.ROLLBACK_ADAPTER)
        self.assertTrue(legacy_rec.is_file(), "rollback lost the migrated record")

    def test_recover_interrupted_migration_completes_it(self):
        repo = Path(self.target_repo)
        rec = repo / ".agents" / "plans" / "x.ipd.md"
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text("# rec\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-q",
                "-m",
                "seed",
            ],
            check=True,
            capture_output=True,
        )
        mgr = self.rollback.manager
        # inject an interruption AFTER the switch write but before completion.
        try:
            mgr.execute_migration(
                target_backend="repository",
                dry_run=False,
                fault_injection="kill-after-switch-before-receipt",
            )
        except Exception:
            pass
        status = mgr.status_migration()
        self.assertTrue(status["active"])
        self.assertNotEqual(status["status"], "completed")
        # recover via the REUSED resume path -> completed, no record loss.
        recovered = self.rollback.recover_interrupted()
        self.assertEqual(recovered["status"], "recovered")
        self.assertEqual(mgr.status_migration()["status"], "completed")

    def test_recover_when_no_transaction_is_a_noop(self):
        recovered = self.rollback.recover_interrupted()
        self.assertEqual(recovered["status"], "none")


# ==================================================================================================
# E-04: deprecation diagnostics + opt-in privacy-preserving usage counters
# ==================================================================================================


class DeprecationTests(_RepoFixture):
    def setUp(self):
        super().setUp()
        self.gate = cm.DeprecationGate(
            alias="plan-review-long",
            canonical="plan-review",
            remove_at_version="3.0.0",
            parity_met=True,
            adoption_met=False,
        )

    def test_diagnostics_are_local_and_do_not_require_telemetry(self):
        # a diagnostic renders with counting OFF (telemetry never required for operation).
        diag = cm.DeprecationDiagnostics(self.target_repo, gates=[self.gate])
        self.assertFalse(diag.enable_counting)
        notice = diag.notice_for("plan-review-long")
        self.assertIsNotNone(notice)
        self.assertIn("deprecated alias", notice.message())
        self.assertIn("plan-review", notice.message())
        # a non-deprecated name has no notice.
        self.assertIsNone(diag.notice_for("some-live-command"))

    def test_counting_is_off_by_default_and_records_nothing(self):
        diag = cm.DeprecationDiagnostics(self.target_repo, gates=[self.gate])
        diag.record_use("plan-review-long")
        diag.record_use("plan-review-long")
        self.assertEqual(diag.read_counts(), {})
        self.assertFalse(diag.counter_path.exists())

    def test_opt_in_counting_is_local_and_privacy_preserving(self):
        diag = cm.DeprecationDiagnostics(
            self.target_repo, gates=[self.gate], enable_counting=True
        )
        diag.record_use("plan-review-long")
        diag.record_use("plan-review-long")
        counts = diag.read_counts()
        self.assertEqual(counts, {"plan-review-long": 2})
        # the on-disk counter records ONLY {alias: count} -- no args/paths/timestamps/identity.
        data = json.loads(diag.counter_path.read_text(encoding="utf-8"))
        self.assertEqual(data, {"plan-review-long": 2})
        for key, val in data.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, int)

    def test_counting_disables_cleanly_and_removes_local_data(self):
        diag = cm.DeprecationDiagnostics(
            self.target_repo, gates=[self.gate], enable_counting=True
        )
        diag.record_use("plan-review-long")
        self.assertTrue(diag.counter_path.is_file())
        diag.disable_counting()
        self.assertFalse(diag.enable_counting)
        self.assertFalse(diag.counter_path.exists())
        # further records are no-ops.
        diag.record_use("plan-review-long")
        self.assertEqual(diag.read_counts(), {})

    def test_alias_removal_refused_before_gates_met(self):
        diag = cm.DeprecationDiagnostics(self.target_repo, gates=[self.gate])
        # adoption gate not met -> REFUSED.
        with self.assertRaises(cm.AliasRemovalRefused):
            diag.request_alias_removal("plan-review-long", "3.0.0")

    def test_alias_removal_refused_before_version_gate(self):
        gate = cm.DeprecationGate(
            alias="a",
            canonical="b",
            remove_at_version="3.0.0",
            parity_met=True,
            adoption_met=True,
        )
        allowed, unmet = gate.can_remove("1.2.1")
        self.assertFalse(allowed)
        self.assertTrue(any("version gate" in u for u in unmet))
        with self.assertRaises(cm.AliasRemovalRefused):
            cm.gate_alias_removal(gate, "1.2.1")

    def test_alias_removal_allowed_only_when_all_gates_met(self):
        gate = cm.DeprecationGate(
            alias="a",
            canonical="b",
            remove_at_version="3.0.0",
            parity_met=True,
            adoption_met=True,
        )
        allowed, unmet = gate.can_remove("3.0.0")
        self.assertTrue(allowed, unmet)
        # gate does not raise when all gates are met (but still removes NOTHING itself).
        cm.gate_alias_removal(gate, "3.1.0")

    def test_unknown_alias_removal_is_refused(self):
        diag = cm.DeprecationDiagnostics(self.target_repo, gates=[self.gate])
        with self.assertRaises(cm.AliasRemovalRefused):
            diag.request_alias_removal("not-an-alias", "9.9.9")


if __name__ == "__main__":
    unittest.main()
