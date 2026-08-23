"""Tests for awoptimize Order 15 (`kh91or`): complex orchestrated workflow migration.

Covers the E-05 acceptance with FALSIFIABLE fixtures that assert DETECTION/REJECTION, never mere
smoke:

  * E-01 release-review(+plan): both modes; every persona finding dispositioned via the Fix Bar;
    PLANNING MODE CANNOT ENTER MUTATION/RELEASE; the Fix Bar is computed; integration is SERIAL; a
    release needs EXPLICIT human authority; a silent mode flip is detected as drift.
  * E-02 verify-execution/ipd-lifecycle: verification inspects the ACTUAL diff + raw checks; gaps emit
    corrective artifacts; an EXECUTOR context CANNOT perform the terminal move; self-verification is
    refused.
  * E-03 assess-all: lanes are READ-ONLY + parallel-eligible; synthesis is SINGLE-WRITER (a second
    writer is refused). setup-repo: PREFLIGHT before mutation, per-change CONSENT, IDEMPOTENCY,
    ROLLBACK, and HEADLESS REFUSAL before any mutation.
  * E-04 incident/migrate/benchmark: operator data is LABELED unavailable (never fabricated); consent
    gates hold; a conformant artifact is emitted; an unsupported certification/submission claim is
    REFUSED (honest limitation, not implied certification).

Stdlib `unittest`, matching the repository convention.
"""

from __future__ import annotations

import unittest

from agent_workflows import migration_complex as MC
from agent_workflows import orchestrate_isolation as ISO
from agent_workflows import run_gates as GATES
from agent_workflows import verify_roles as ROLES
from tests.support import SOURCE_WORKFLOWS


def _approve_handler(_gate):
    return "approve"


def _reject_handler(_gate):
    return "reject"


# ==================================================================================================
# E-01: release-review + release-review-plan
# ==================================================================================================


class ReleaseReviewCoordinatorTests(unittest.TestCase):
    def _seed_ledger(self, coordinator: MC.ReleaseReviewCoordinator) -> None:
        for i, persona in enumerate(MC.RELEASE_PERSONAS):
            coordinator.ledger.add(
                MC.PersonaFinding(
                    finding_id="F-{0:02d}".format(i),
                    persona=persona,
                    summary="finding from {0}".format(persona),
                    remediation_risk="low" if i % 2 == 0 else "high",
                )
            )

    def test_both_modes_construct_with_frozen_scope(self):
        full = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        plan = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        self.assertNotEqual(
            full.frozen.requirement_digest, plan.frozen.requirement_digest
        )

    def test_unknown_mode_rejected(self):
        with self.assertRaises(MC.ReleaseModeError):
            MC.ReleaseReviewCoordinator(mode="release-review-turbo")

    def test_fix_bar_computed(self):
        # fix by default; defer only when the cure's remediation risk is Medium-High or higher.
        self.assertTrue(MC.fix_bar("low"))
        self.assertTrue(MC.fix_bar("medium"))
        self.assertFalse(MC.fix_bar("medium-high"))
        self.assertFalse(MC.fix_bar("high"))
        with self.assertRaises(MC.ComplexMigrationError):
            MC.fix_bar("nonsense")

    def test_every_persona_finding_dispositioned(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        self._seed_ledger(c)
        c.run_fix_bar()
        # zero findings left un-triaged: no silently dropped finding.
        self.assertEqual(c.ledger.undispositioned(), [])
        for f in c.ledger.findings:
            self.assertIn(f.disposition, MC.FINDING_DISPOSITIONS)

    def test_data_integrity_finding_never_deferred(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        # a LIVE/High data-integrity finding whose cure is risky: escalate, NEVER defer.
        c.ledger.add(
            MC.PersonaFinding(
                finding_id="F-LIVE",
                persona="qa_qc",
                summary="live data corruption",
                remediation_risk="high",
                data_integrity=True,
            )
        )
        c.run_fix_bar()
        disp = {f.finding_id: f.disposition for f in c.ledger.findings}
        self.assertEqual(disp["F-LIVE"], MC.DISPOSITION_ESCALATE)
        self.assertNotEqual(disp["F-LIVE"], MC.DISPOSITION_DEFER)

    def test_undispositioned_finding_blocks_progress(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        # Inject a finding with an unknown remediation risk so disposition_all raises.
        c.ledger.findings.append(
            MC.PersonaFinding(
                finding_id="F-BAD",
                persona="architect",
                summary="x",
                remediation_risk="bananas",
            )
        )
        with self.assertRaises(MC.ComplexMigrationError):
            c.run_fix_bar()

    def test_unknown_persona_rejected(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        with self.assertRaises(MC.ComplexMigrationError):
            c.ledger.add(
                MC.PersonaFinding(
                    finding_id="F-X",
                    persona="dragon-slayer",
                    summary="x",
                    remediation_risk="low",
                )
            )

    def test_planning_mode_cannot_enter_mutation(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        c.enter_stage(MC.STAGE_AUDIT)
        c.enter_stage(MC.STAGE_PLAN)
        with self.assertRaises(MC.ReleaseModeError):
            c.enter_stage(MC.STAGE_MUTATION)

    def test_planning_mode_cannot_enter_release(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        with self.assertRaises(MC.ReleaseModeError):
            c.enter_stage(MC.STAGE_RELEASE)
        # and it certainly cannot authorize a release.
        with self.assertRaises(MC.ReleaseModeError):
            c.authorize_release(interactive=True, input_handler=_approve_handler)

    def test_full_mode_can_enter_mutation(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        c.enter_stage(MC.STAGE_MUTATION)  # allowed
        self.assertIn(MC.STAGE_MUTATION, c.stages_entered)

    def test_integration_is_serial_not_parallel_mutating(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        lanes = (
            ISO.LaneRequest(
                lane_id="fix-a",
                actor_role=ROLES.ROLE_EXECUTOR,
                lane_kind=ISO.LANE_KIND_MUTATING,
                files_targeted=("src/a.py",),
            ),
            ISO.LaneRequest(
                lane_id="fix-b",
                actor_role=ROLES.ROLE_EXECUTOR,
                lane_kind=ISO.LANE_KIND_MUTATING,
                files_targeted=("src/b.py",),
            ),
        )
        result = c.integrate_fixes(lanes)
        self.assertNotEqual(result.execution_mode, ISO.EXEC_MODE_PARALLEL_MUTATING)
        self.assertFalse(result.is_eligible_parallel)

    def test_release_needs_explicit_authority_headless_refused(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        # Headless: no human -> refused (needs_input surfaces as ReleaseAuthorityError).
        with self.assertRaises(MC.ReleaseAuthorityError):
            c.authorize_release(interactive=False)

    def test_release_refused_on_rejection(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        with self.assertRaises(MC.ReleaseAuthorityError):
            c.authorize_release(interactive=True, input_handler=_reject_handler)

    def test_release_granted_on_explicit_approval(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        decision = c.authorize_release(interactive=True, input_handler=_approve_handler)
        self.assertTrue(decision.is_approved)
        self.assertEqual(decision.status, GATES.GATE_STATUS_APPROVED)

    def test_mode_flip_detected_as_drift(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        # a planning->full flip changes the frozen scope: detected as drift.
        self.assertTrue(MC.detect_mode_drift(c, MC.RELEASE_MODE_FULL))
        # same mode: no drift.
        self.assertFalse(MC.detect_mode_drift(c, MC.RELEASE_MODE_PLANNING))

    def test_executor_cannot_finalize_release_review(self):
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        self.assertFalse(c.can_finalize(ROLES.ROLE_EXECUTOR))
        self.assertTrue(c.can_finalize(ROLES.ROLE_COORDINATOR))


# ==================================================================================================
# E-02: verify-execution + ipd-lifecycle
# ==================================================================================================


class VerifyExecutionCoordinatorTests(unittest.TestCase):
    def test_clean_inspection_verifies_no_corrective(self):
        insp = MC.DiffInspection(
            diff_paths=("src/a.py",),
            declared_paths=("src/a.py", "tests/test_a.py"),
            raw_check_results={"pytest": True, "lint": True},
        )
        v = MC.VerifyExecutionCoordinator(plan_id="plan-1")
        verified, artifacts = v.verify(
            insp, verifier_role=ROLES.ROLE_VERIFIER, author_role=ROLES.ROLE_EXECUTOR
        )
        self.assertTrue(verified)
        self.assertEqual(artifacts, [])

    def test_actual_diff_out_of_scope_emits_corrective(self):
        insp = MC.DiffInspection(
            diff_paths=("src/a.py", "src/SECRET.py"),
            declared_paths=("src/a.py",),
            raw_check_results={"pytest": True},
        )
        v = MC.VerifyExecutionCoordinator(plan_id="plan-2")
        verified, artifacts = v.verify(
            insp, verifier_role=ROLES.ROLE_VERIFIER, author_role=ROLES.ROLE_EXECUTOR
        )
        self.assertFalse(verified)
        self.assertTrue(any("scope" in a.artifact_id for a in artifacts))
        # the corrective artifact names the ACTUAL out-of-scope file, from the real diff.
        scope_art = [a for a in artifacts if "scope" in a.artifact_id][0]
        self.assertIn("src/SECRET.py", scope_art.failed_items)

    def test_raw_check_failure_emits_corrective(self):
        insp = MC.DiffInspection(
            diff_paths=("src/a.py",),
            declared_paths=("src/a.py",),
            raw_check_results={"pytest": False, "lint": True},
        )
        v = MC.VerifyExecutionCoordinator(plan_id="plan-3")
        verified, artifacts = v.verify(
            insp, verifier_role=ROLES.ROLE_VERIFIER, author_role=ROLES.ROLE_EXECUTOR
        )
        self.assertFalse(verified)
        checks_art = [a for a in artifacts if "checks" in a.artifact_id][0]
        self.assertIn("pytest", checks_art.failed_items)

    def test_self_verification_refused(self):
        insp = MC.DiffInspection(diff_paths=(), declared_paths=(), raw_check_results={})
        v = MC.VerifyExecutionCoordinator(plan_id="plan-4")
        # an executor cannot verify its own work (verifier_role must be the independent verifier).
        with self.assertRaises(ROLES.SelfVerificationForbiddenError):
            v.verify(
                insp,
                verifier_role=ROLES.ROLE_EXECUTOR,
                author_role=ROLES.ROLE_EXECUTOR,
            )

    def test_executor_cannot_perform_terminal_move(self):
        v = MC.VerifyExecutionCoordinator(plan_id="plan-5")
        self.assertFalse(
            v.can_mark_executed(ROLES.ROLE_EXECUTOR, verifier_verified=True)
        )
        with self.assertRaises(MC.TerminalUnreachableError):
            v.mark_executed(ROLES.ROLE_EXECUTOR, verifier_verified=True)

    def test_terminal_move_needs_verifier_verified(self):
        v = MC.VerifyExecutionCoordinator(plan_id="plan-6")
        # even the coordinator cannot finalize without an independent `verified` decision.
        self.assertFalse(
            v.can_mark_executed(ROLES.ROLE_COORDINATOR, verifier_verified=False)
        )
        with self.assertRaises(MC.TerminalUnreachableError):
            v.mark_executed(ROLES.ROLE_COORDINATOR, verifier_verified=False)

    def test_coordinator_can_perform_terminal_move_after_verified(self):
        v = MC.VerifyExecutionCoordinator(plan_id="plan-7")
        self.assertTrue(
            v.can_mark_executed(ROLES.ROLE_COORDINATOR, verifier_verified=True)
        )
        rule = v.mark_executed(ROLES.ROLE_COORDINATOR, verifier_verified=True)
        self.assertEqual(rule.source, "verified")
        self.assertEqual(rule.target, "complete")


# ==================================================================================================
# E-03: assess-all read-only lanes + single-writer synthesis; setup-repo state machine
# ==================================================================================================


class AssessAllCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.c = MC.AssessAllCoordinator(members=("security", "performance", "tests"))

    def test_lanes_are_read_only_and_parallel_eligible(self):
        self.c.assert_lanes_read_only()
        elig = self.c.eligibility()
        self.assertTrue(elig.is_eligible_parallel)
        self.assertEqual(elig.execution_mode, ISO.EXEC_MODE_PARALLEL_READ_ONLY)

    def test_single_writer_synthesis(self):
        out = self.c.synthesize(
            "coordinator-A",
            {"security": ["a", "b"], "performance": ["b", "c"]},
        )
        # de-duplicated across lanes.
        self.assertEqual(out["consolidated_findings"], ["b", "c", "a"])

    def test_second_writer_refused(self):
        self.c.claim_synthesis_writer("coordinator-A")
        with self.assertRaises(MC.SingleWriterViolationError):
            self.c.claim_synthesis_writer("coordinator-B")

    def test_same_writer_reclaim_allowed(self):
        self.c.claim_synthesis_writer("coordinator-A")
        self.c.claim_synthesis_writer("coordinator-A")  # idempotent, no raise


class SetupRepoStateMachineTests(unittest.TestCase):
    def _change(self, cid="c1", fail=False):
        return MC.SetupChange(
            change_id=cid,
            description="write config {0}".format(cid),
            idempotency_key="key-{0}".format(cid),
            rollback="delete config {0}".format(cid),
        )

    def test_headless_refused_before_any_mutation(self):
        sm = MC.SetupRepoStateMachine(interactive=False, preconditions={"git": True})
        with self.assertRaises(MC.SetupHeadlessRefusalError):
            sm.preflight()
        self.assertEqual(sm.state, MC.SETUP_STATE_REFUSED)
        self.assertEqual(sm.applied_changes, [])

    def test_preflight_refuses_on_unmet_precondition(self):
        sm = MC.SetupRepoStateMachine(
            interactive=True, preconditions={"git": True, "writable": False}
        )
        with self.assertRaises(MC.SetupPreflightError):
            sm.preflight()
        self.assertEqual(sm.state, MC.SETUP_STATE_REFUSED)
        self.assertEqual(sm.applied_changes, [])

    def test_cannot_apply_before_preflight(self):
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={})
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(self._change(), input_handler=_approve_handler)

    def test_per_change_consent_gate_rejection_blocks(self):
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(self._change(), input_handler=_reject_handler)

    def test_consent_approval_applies_change(self):
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        result = sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        self.assertEqual(result, "applied")
        self.assertIn("c1", sm.applied_changes)

    def test_idempotency_reapply_is_noop(self):
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        # re-applying the same idempotency key does not mutate again.
        result = sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        self.assertEqual(result, "noop")
        self.assertEqual(sm.applied_changes.count("c1"), 1)

    def test_failed_change_rolls_back_in_reverse(self):
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        sm.apply_change(self._change("c2"), input_handler=_approve_handler)
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(
                self._change("c3", fail=True), input_handler=_approve_handler, fail=True
            )
        # rolled back in reverse order of application.
        self.assertEqual(sm.state, MC.SETUP_STATE_ROLLED_BACK)
        self.assertEqual(sm.rolled_back, ["c2", "c1"])
        self.assertEqual(sm.applied_changes, [])


# ==================================================================================================
# E-04: incident / migrate / benchmark -- operator data + honest limitations
# ==================================================================================================


class RiskAwarePackageTests(unittest.TestCase):
    def test_operator_data_labeled_unavailable_not_fabricated(self):
        pkg = MC.build_incident_package()
        pkg.add_datum(
            MC.OperatorDatum(key="siem_timeline", provenance=MC.PROVENANCE_UNAVAILABLE)
        )
        pkg.add_datum(
            MC.OperatorDatum(
                key="repo_commit",
                provenance=MC.PROVENANCE_REPO,
                value="abc123",
            )
        )
        self.assertIn("siem_timeline", pkg.unavailable_data())
        art = pkg.build_artifact()
        self.assertIn("siem_timeline", art["operator_data_unavailable"])

    def test_unavailable_datum_with_fabricated_value_rejected(self):
        with self.assertRaises(MC.ComplexMigrationError):
            MC.OperatorDatum(
                key="dashboard",
                provenance=MC.PROVENANCE_UNAVAILABLE,
                value="99.9% uptime",  # fabricated: unavailable data must not carry a value.
            )

    def test_unknown_provenance_rejected(self):
        with self.assertRaises(MC.ComplexMigrationError):
            MC.OperatorDatum(key="x", provenance="made-up")

    def test_consent_gate_headless_needs_input(self):
        pkg = MC.build_benchmark_package()
        decision = pkg.consent_gate("run-benchmarks", interactive=False)
        self.assertEqual(decision.status, GATES.GATE_STATUS_NEEDS_INPUT)
        self.assertFalse(decision.is_approved)

    def test_consent_gate_explicit_approval(self):
        pkg = MC.build_benchmark_package()
        decision = pkg.consent_gate(
            "run-benchmarks", interactive=True, input_handler=_approve_handler
        )
        self.assertTrue(decision.is_approved)

    def test_unsupported_certification_claim_refused(self):
        pkg = MC.build_benchmark_package()
        with self.assertRaises(MC.UnsupportedClaimError):
            pkg.assert_supportable_claim(MC.CLAIM_CERTIFICATION)

    def test_unsupported_hpc_submission_claim_refused(self):
        pkg = MC.build_benchmark_package()
        with self.assertRaises(MC.UnsupportedClaimError):
            pkg.assert_supportable_claim(MC.CLAIM_HPC_SUBMISSION)

    def test_unsupported_compliance_attestation_refused(self):
        pkg = MC.build_migrate_package()
        with self.assertRaises(MC.UnsupportedClaimError):
            pkg.assert_supportable_claim(MC.CLAIM_COMPLIANCE_ATTESTATION)

    def test_supported_claim_allowed(self):
        pkg = MC.build_migrate_package()
        # a repo-scoped claim is allowed (no raise).
        pkg.assert_supportable_claim("repo-scoped-migration-plan")

    def test_artifact_is_conformant_and_verifiable(self):
        pkg = MC.build_migrate_package()
        pkg.add_datum(
            MC.OperatorDatum(key="prod_schema", provenance=MC.PROVENANCE_UNAVAILABLE)
        )
        art = pkg.build_artifact()
        # conformant shape + a deterministic digest for verifiability.
        self.assertEqual(art["workflow"], "migrate")
        self.assertIn("honest_limitation", art)
        self.assertIn("artifact_digest", art)
        # digest is stable (verifiable): rebuild yields the same digest.
        self.assertEqual(
            art["artifact_digest"], pkg.build_artifact()["artifact_digest"]
        )


# ==================================================================================================
# Manifest authority (non-destructive contract): every migrated command is a real manifest row
# ==================================================================================================


class ManifestAuthorityTests(unittest.TestCase):
    def test_all_order15_commands_present_in_live_manifest(self):
        missing = MC.assert_commands_in_manifest(SOURCE_WORKFLOWS)
        self.assertEqual(missing, [], "missing manifest rows: {0}".format(missing))


if __name__ == "__main__":
    unittest.main()
