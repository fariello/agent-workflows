"""Adversarial and functional test suite for verifier roles, clean packet procedures, and corrective routing.

awoptimize Order 08 (`5hu6bd`) E-01..E-05, validating V-01..V-05.

Covers:
  * E-01 / V-01: Role/permission/authority matrix with negative tests: every forbidden role action
                 is rejected (executor/corrector cannot self-verify; verifier cannot mutate product code;
                 only coordinator/runtime/human holds terminal completion authority; consistent with
                 Order-02 RL-E032).
  * E-02 / V-02: Verifier-packet golden test: includes every primary artifact + frozen requirements,
                 strictly excludes executor conclusion prose, binds base/head/worktree identity, and
                 rejects missing or mismatched inputs with typed validation errors.
  * E-03 / V-03: Verification procedures: requirement-by-requirement inspection, scope audit, symbol-wiring
                 check, negative cases check, test falsifiability check, targeted + full checks, artifact
                 presence, residual search, and evidence validation, each producing an explicit result
                 with evidence IDs, with each gap class deterministically blocking completion.
  * E-04 / V-04: Corrective routing: verifier findings produce bounded in-scope corrections or explicit
                 pending corrective-IPD artifacts (never vanishing into prose); original failures remain
                 immutable; changed files invalidate linked evidence; and invalidated checks rerun before
                 any pass.
  * E-05 / V-05: Full serial test suite execution and verification.
"""

from __future__ import annotations

import unittest
from typing import Any

from agent_workflows import run_ledger_schema as schema
from agent_workflows import verify_roles as vr


class TestVerifierRolesAndPermissions(unittest.TestCase):
    """Test role contracts, permissions, state authority, and negative enforcement (E-01 / V-01)."""

    def test_all_roles_defined_with_complete_contracts(self) -> None:
        """Verify all 7 roles are registered with explicit contracts."""
        self.assertEqual(len(vr.ALL_ROLES), 7)
        for role in vr.ALL_ROLES:
            contract = vr.get_role_contract(role)
            self.assertEqual(contract.role, role)
            self.assertTrue(len(contract.description) > 0)
            self.assertIsInstance(contract.allowed_actions, frozenset)
            self.assertIsInstance(contract.forbidden_actions, frozenset)
            self.assertIsInstance(contract.state_authority, frozenset)
            # Verify serialization
            d = contract.to_dict()
            self.assertEqual(d["role"], role)

    def test_unknown_role_raises_error(self) -> None:
        """Verify requesting an unknown role raises RolePermissionError."""
        with self.assertRaises(vr.RolePermissionError) as ctx:
            vr.get_role_contract("malicious_hacker")
        self.assertIn("Unknown role 'malicious_hacker'", str(ctx.exception))

    def test_coordinator_authority_and_forbidden_actions(self) -> None:
        """Coordinator has terminal authority and step release, but cannot mutate code or self-verify."""
        coord = vr.get_role_contract(vr.ROLE_COORDINATOR)
        self.assertTrue(coord.can_author_terminal_transaction)
        self.assertTrue(coord.can_release_steps)
        self.assertTrue(coord.can_record_human_approval)
        self.assertFalse(coord.can_mutate_product_code)
        self.assertFalse(coord.can_author_verifier_decision)

        # Allowed actions
        res = vr.check_role_action(vr.ROLE_COORDINATOR, "author_terminal_transaction")
        self.assertTrue(res.allowed)
        res = vr.check_role_action(vr.ROLE_COORDINATOR, "release_step")
        self.assertTrue(res.allowed)

        # Forbidden: mutate product code
        with self.assertRaises(vr.ProductMutationForbiddenError):
            vr.enforce_role_action(vr.ROLE_COORDINATOR, "mutate_product_code")

        # Forbidden: author verifier decision
        with self.assertRaises(vr.ForbiddenActionError):
            vr.enforce_role_action(vr.ROLE_COORDINATOR, "author_verifier_decision")

    def test_executor_permissions_and_forbidden_actions(self) -> None:
        """Executor can mutate code and attempt steps, but cannot verify work or finalize run."""
        exec_role = vr.get_role_contract(vr.ROLE_EXECUTOR)
        self.assertTrue(exec_role.can_mutate_product_code)
        self.assertTrue(exec_role.can_mutate_test_code)
        self.assertTrue(exec_role.can_author_step_attempt)
        self.assertFalse(exec_role.can_author_verifier_decision)
        self.assertFalse(exec_role.can_author_terminal_transaction)
        self.assertFalse(exec_role.can_release_steps)

        # Allowed actions
        vr.enforce_role_action(vr.ROLE_EXECUTOR, "mutate_product_code")
        vr.enforce_role_action(vr.ROLE_EXECUTOR, "author_step_attempt")

        # Forbidden: self-verification / author verifier decision (RL-E032)
        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "author_verifier_decision")

        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "self_verify")

        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.check_self_verification(vr.ROLE_EXECUTOR, vr.ROLE_EXECUTOR, "R-01")

        # Forbidden: terminal completion
        with self.assertRaises(vr.TerminalAuthorityError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "author_terminal_transaction")

        # Forbidden: release step
        with self.assertRaises(vr.ForbiddenActionError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "release_steps")

    def test_verifier_least_privilege_and_forbidden_actions(self) -> None:
        """Verifier can author verifier decisions, but CANNOT mutate product or test code (least privilege)."""
        verif = vr.get_role_contract(vr.ROLE_VERIFIER)
        self.assertTrue(verif.can_author_verifier_decision)
        self.assertFalse(verif.can_mutate_product_code)
        self.assertFalse(verif.can_mutate_test_code)
        self.assertFalse(verif.can_author_terminal_transaction)
        self.assertFalse(verif.can_release_steps)
        self.assertFalse(verif.can_author_step_attempt)

        # Allowed action: author verifier decision
        vr.enforce_role_action(vr.ROLE_VERIFIER, "author_verifier_decision")

        # Forbidden: verifier mutating product code is a hard refusal
        with self.assertRaises(vr.ProductMutationForbiddenError) as ctx:
            vr.check_code_mutation_allowed(
                vr.ROLE_VERIFIER, "agent_workflows/core.py", is_product_code=True
            )
        self.assertIn("cannot mutate product code", str(ctx.exception))

        with self.assertRaises(vr.ProductMutationForbiddenError):
            vr.enforce_role_action(vr.ROLE_VERIFIER, "mutate_product_code")

        # Forbidden: verifier mutating test code
        with self.assertRaises(vr.RolePermissionError):
            vr.check_code_mutation_allowed(
                vr.ROLE_VERIFIER, "tests/test_core.py", is_product_code=False
            )

        # Forbidden: verifier finalizing run
        with self.assertRaises(vr.TerminalAuthorityError):
            vr.enforce_role_action(vr.ROLE_VERIFIER, "author_terminal_transaction")

        # Forbidden: verifier attempting step execution
        with self.assertRaises(vr.ForbiddenActionError):
            vr.enforce_role_action(vr.ROLE_VERIFIER, "author_step_attempt")

    def test_corrector_permissions_and_forbidden_actions(self) -> None:
        """Corrector can mutate code and author corrections, but cannot verify own corrective work."""
        corr = vr.get_role_contract(vr.ROLE_CORRECTOR)
        self.assertTrue(corr.can_mutate_product_code)
        self.assertTrue(corr.can_author_correction)
        self.assertFalse(corr.can_author_verifier_decision)
        self.assertFalse(corr.can_author_terminal_transaction)

        # Allowed actions
        vr.enforce_role_action(vr.ROLE_CORRECTOR, "author_correction")
        vr.enforce_role_action(vr.ROLE_CORRECTOR, "mutate_product_code")

        # Forbidden: self-verification
        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.enforce_role_action(vr.ROLE_CORRECTOR, "author_verifier_decision")

        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.check_self_verification(vr.ROLE_CORRECTOR, vr.ROLE_CORRECTOR, "R-02")

        # Forbidden: terminal completion
        with self.assertRaises(vr.TerminalAuthorityError):
            vr.enforce_role_action(vr.ROLE_CORRECTOR, "author_terminal_transaction")

    def test_investigator_read_only_status(self) -> None:
        """Investigator has read-only access and cannot mutate code, release steps, or finalize."""
        inv = vr.get_role_contract(vr.ROLE_INVESTIGATOR)
        self.assertFalse(inv.can_mutate_product_code)
        self.assertFalse(inv.can_mutate_test_code)
        self.assertFalse(inv.can_author_step_attempt)
        self.assertFalse(inv.can_author_verifier_decision)
        self.assertFalse(inv.can_author_terminal_transaction)

        with self.assertRaises(vr.ProductMutationForbiddenError):
            vr.enforce_role_action(vr.ROLE_INVESTIGATOR, "mutate_product_code")

        with self.assertRaises(vr.ForbiddenActionError):
            vr.enforce_role_action(vr.ROLE_INVESTIGATOR, "author_step_attempt")


class TestCleanVerifierPacketBuilder(unittest.TestCase):
    """Test clean verifier packet builder, digest determinism, and prose exclusion (E-02 / V-02)."""

    def setUp(self) -> None:
        self.frozen_reqs = {
            "must": [
                "Define verifier roles with explicit contracts",
                "Construct clean verifier packet with primary artifacts",
                "Execute 9 verification procedures producing explicit results",
                "Route verifier findings to corrections or corrective IPD",
            ],
            "scope": [
                "Touch only agent_workflows/verify_roles.py and tests/test_verify_roles_packet.py"
            ],
            "validation": ["Pass full canonical test suite with make test"],
            "output": ["Conforming verifier_decision and correction ledger records"],
        }
        self.scope_fence = {
            "allowed_paths": [
                "agent_workflows/verify_roles.py",
                "tests/test_verify_roles_packet.py",
            ],
            "forbidden_paths": ["secrets/**", "agent_workflows/core.py"],
        }
        self.actual_diff = (
            "diff --git a/agent_workflows/verify_roles.py b/agent_workflows/verify_roles.py\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/agent_workflows/verify_roles.py\n"
            "@@ -0,0 +1,50 @@\n"
            "+class RoleContract:\n"
            "+    pass\n"
        )
        self.raw_evidence = (
            {
                "evidence_id": "ev-01",
                "kind": "tool_event",
                "argv": ["pytest", "tests/test_verify_roles_packet.py"],
                "exit_code": 0,
                "head": "a" * 40,
                "binds": ["M-01", "V-01"],
                "falsifiable": True,
            },
            {
                "evidence_id": "ev-02",
                "kind": "tool_event",
                "argv": ["make test"],
                "exit_code": 0,
                "head": "a" * 40,
                "binds": ["M-02", "M-03", "M-04"],
            },
        )

    def test_golden_verifier_packet_building(self) -> None:
        """Golden packet test: builds complete packet with primary artifacts, binds base/head/worktree, computes digest."""
        packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-test-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo/agent-workflows",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff=self.actual_diff,
            untracked_inventory=("tests/test_verify_roles_packet.py",),
            test_diff="+++ b/tests/test_verify_roles_packet.py\n+class TestVerifierRolesAndPermissions:",
            raw_evidence_manifest=self.raw_evidence,
            timestamp="2026-08-22T12:00:00Z",
        )

        self.assertEqual(packet.run_id, "run-12345678")
        self.assertEqual(packet.base_commit, "0" * 40)
        self.assertEqual(packet.head_commit, "a" * 40)
        self.assertEqual(packet.worktree_path, "/repo/agent-workflows")
        self.assertEqual(len(packet.raw_evidence_manifest), 2)
        self.assertIn("tests/test_verify_roles_packet.py", packet.untracked_inventory)
        self.assertTrue(len(packet.packet_digest) == 64)

        # Validate packet structure
        val_res = vr.validate_verifier_packet(packet)
        self.assertTrue(val_res.ok)
        self.assertEqual(len(val_res.findings), 0)
        self.assertIsNotNone(val_res.packet)

    def test_executor_conclusion_prose_is_strictly_excluded(self) -> None:
        """Verifier packet builder strips and rejects executor conclusion prose and narrative."""
        leaky_outcomes = [
            {
                "step_id": "S-01",
                "attempt": 1,
                "status": "performed",
                "actor": "executor",
                "evidence_ids": ["ev-01"],
                "prose": "I have successfully verified all requirements and everything is perfect!",
                "conclusion": "Task completed without any flaws.",
                "verdict": "satisfied",
            }
        ]

        packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-test-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo/agent-workflows",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff=self.actual_diff,
            raw_step_outcomes=leaky_outcomes,
            timestamp="2026-08-22T12:00:00Z",
        )

        # Ensure no prose leaked into prior_attempts
        packet_dict = packet.to_dict()
        packet_json = packet.to_json()
        self.assertNotIn("I have successfully verified", packet_json)
        self.assertNotIn("Task completed without any flaws", packet_json)
        for att in packet_dict["prior_attempts"]:
            self.assertNotIn("prose", att)
            self.assertNotIn("conclusion", att)
            self.assertNotIn("verdict", att)

    def test_prose_leak_in_raw_packet_is_detected_and_rejected(self) -> None:
        """If unstripped raw packet contains conclusion prose, validator rejects it with VP-PROSE-LEAK."""
        raw_dict = {
            "run_id": "run-12345678",
            "workflow_id": "wf-test-08",
            "base_commit": "0" * 40,
            "head_commit": "a" * 40,
            "worktree_path": "/repo",
            "frozen_requirements": self.frozen_reqs,
            "declared_scope": self.scope_fence,
            "actual_diff": self.actual_diff,
            "untracked_inventory": [],
            "test_diff": "",
            "raw_evidence_manifest": [],
            "prior_attempts": [{"prose": "Executor self-audit says complete"}],
            "verification_rubric": {"procedures": list(vr.ALL_PROCEDURES)},
            "timestamp": "2026-08-22T12:00:00Z",
        }
        raw_dict["packet_digest"] = vr.compute_verifier_packet_digest(raw_dict)

        val_res = vr.validate_verifier_packet(raw_dict)
        self.assertFalse(val_res.ok)
        codes = [f.code for f in val_res.findings]
        self.assertIn("VP-PROSE-LEAK", codes)

    def test_corrupted_digest_rejected(self) -> None:
        """A packet with a tampered digest is rejected with VP-CORRUPTED-DIGEST."""
        raw_dict = {
            "run_id": "run-12345678",
            "workflow_id": "wf-test-08",
            "base_commit": "0" * 40,
            "head_commit": "a" * 40,
            "worktree_path": "/repo",
            "frozen_requirements": self.frozen_reqs,
            "declared_scope": self.scope_fence,
            "actual_diff": self.actual_diff,
            "untracked_inventory": [],
            "test_diff": "",
            "raw_evidence_manifest": [],
            "prior_attempts": [],
            "verification_rubric": {"procedures": list(vr.ALL_PROCEDURES)},
            "timestamp": "2026-08-22T12:00:00Z",
            "packet_digest": "f" * 64,  # Bad digest
        }
        val_res = vr.validate_verifier_packet(raw_dict)
        self.assertFalse(val_res.ok)
        self.assertIn("VP-CORRUPTED-DIGEST", [f.code for f in val_res.findings])

    def test_missing_required_fields_rejected(self) -> None:
        """Packets with missing fields (run_id, base_commit, head_commit, scope, reqs) are rejected."""
        bad_packet = {
            "run_id": "not-a-valid-run-id",
            "declared_scope": {},
            "frozen_requirements": {},
            "actual_diff": "",
            "packet_digest": "dummy",
        }
        val_res = vr.validate_verifier_packet(bad_packet)
        self.assertFalse(val_res.ok)
        fields = [f.field for f in val_res.findings]
        self.assertIn("run_id", fields)
        self.assertIn("base_commit", fields)
        self.assertIn("head_commit", fields)
        self.assertIn("worktree_path", fields)
        self.assertIn("frozen_requirements", fields)


class TestVerificationProcedures(unittest.TestCase):
    """Test all 9 verification procedures and gap class detection (E-03 / V-03)."""

    def setUp(self) -> None:
        self.frozen_reqs = {
            "must": ["M1 requirement", "M2 requirement"],
            "validation": ["V1 validation"],
        }
        self.scope_fence = {
            "allowed_paths": [
                "agent_workflows/verify_roles.py",
                "tests/test_verify_roles_packet.py",
            ],
            "forbidden_paths": ["secrets/**"],
        }
        self.clean_diff = (
            "diff --git a/agent_workflows/verify_roles.py b/agent_workflows/verify_roles.py\n"
            "+++ b/agent_workflows/verify_roles.py\n"
            "+class RoleContract:\n"
            "+    pass\n"
        )
        self.clean_test_diff = (
            "diff --git a/tests/test_verify_roles_packet.py b/tests/test_verify_roles_packet.py\n"
            "+++ b/tests/test_verify_roles_packet.py\n"
            "+class TestVerifierRolesAndPermissions:\n"
            "+    def test_negative_cases(self):\n"
            "+        with self.assertRaises(RolePermissionError):\n"
            "+            pass\n"
            "+    def test_contract(self):\n"
            "+        contract = RoleContract()\n"
        )
        self.clean_evidence = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01"],
                "exit_code": 0,
                "status": "success",
                "head": "a" * 40,
                "argv": ["pytest", "tests/test_verify_roles_packet.py"],
                "falsifiable": True,
            },
            {
                "evidence_id": "ev-02",
                "binds": ["M-02", "V-01"],
                "exit_code": 0,
                "status": "success",
                "head": "a" * 40,
                "argv": ["make test"],
            },
        )

    def _build_clean_packet(self, **kwargs: Any) -> vr.VerifierPacket:
        args = {
            "run_id": "run-abcdef12",
            "workflow_id": "wf-08",
            "base_commit": "0" * 40,
            "head_commit": "a" * 40,
            "worktree_path": "/repo",
            "frozen_requirements": self.frozen_reqs,
            "declared_scope": self.scope_fence,
            "actual_diff": self.clean_diff,
            "test_diff": self.clean_test_diff,
            "raw_evidence_manifest": self.clean_evidence,
            "timestamp": "2026-08-22T12:00:00Z",
        }
        args.update(kwargs)
        return vr.build_verifier_packet(**args)

    def test_clean_packet_passes_all_procedures(self) -> None:
        """A clean packet passes all 9 verification procedures and produces satisfied verifier decisions."""
        packet = self._build_clean_packet()
        report = vr.run_verification_procedures(
            packet,
            declared_symbols=["RoleContract"],
            codebase_content={"test": self.clean_test_diff},
        )

        self.assertTrue(report.is_verified)
        self.assertEqual(report.overall_result, vr.RESULT_SATISFIED)
        self.assertEqual(len(report.blocking_gaps), 0)
        self.assertEqual(report.requirement_results["M-01"], vr.RESULT_SATISFIED)
        self.assertEqual(report.requirement_results["M-02"], vr.RESULT_SATISFIED)
        self.assertEqual(report.requirement_results["V-01"], vr.RESULT_SATISFIED)

        # Check verifier_decision record generation
        decisions = report.to_verifier_decisions()
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertEqual(d["kind"], "verifier_decision")
            self.assertEqual(d["actor"], vr.ROLE_VERIFIER)
            self.assertEqual(d["result"], vr.RESULT_SATISFIED)
            val = schema.validate_record(d)
            self.assertTrue(val.ok)

    def test_gap_1_missing_evidence_blocks_completion(self) -> None:
        """Gap Class: Missing evidence for requirement causes failure and blocks completion."""
        # Manifest without binding for V-01
        ev = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01", "M-02"],
                "exit_code": 0,
                "head": "a" * 40,
            },
        )
        packet = self._build_clean_packet(raw_evidence_manifest=ev)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        self.assertEqual(report.overall_result, vr.RESULT_FAILED)
        self.assertEqual(report.requirement_results["V-01"], vr.RESULT_FAILED)
        self.assertTrue(
            any(
                "VP-REQ-MISSING-EVIDENCE" in g or "missing_evidence" in g
                for g in report.blocking_gaps
            )
        )

    def test_gap_2_evidence_failure_blocks_completion(self) -> None:
        """Gap Class: Evidence with failed exit code causes failure and blocks completion."""
        ev = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01"],
                "exit_code": 1,
                "head": "a" * 40,
            },
            {
                "evidence_id": "ev-02",
                "binds": ["M-02", "V-01"],
                "exit_code": 0,
                "head": "a" * 40,
            },
        )
        packet = self._build_clean_packet(raw_evidence_manifest=ev)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        self.assertEqual(report.overall_result, vr.RESULT_FAILED)
        self.assertEqual(report.requirement_results["M-01"], vr.RESULT_FAILED)

    def test_gap_3_scope_violation_blocks_completion(self) -> None:
        """Gap Class: Touching forbidden path or unlisted file blocks completion."""
        dirty_diff = self.clean_diff + "\n+++ b/secrets/tokens.json\n+token=123"
        packet = self._build_clean_packet(actual_diff=dirty_diff)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        self.assertEqual(report.overall_result, vr.RESULT_FAILED)
        scope_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_SCOPE_AUDIT
        )
        self.assertEqual(scope_proc.result, vr.RESULT_FAILED)
        self.assertEqual(scope_proc.findings[0].code, "VP-SCOPE-FORBIDDEN-PATH")

    def test_gap_4_unwired_symbol_blocks_completion(self) -> None:
        """Gap Class: Dead vocabulary (defined symbol never consumed) blocks completion."""
        packet = self._build_clean_packet()
        report = vr.run_verification_procedures(
            packet,
            declared_symbols=["DeadVocabularyClass"],
            codebase_content={"test": ""},  # No usages anywhere
        )

        self.assertFalse(report.is_verified)
        symbol_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_SYMBOL_WIRING
        )
        self.assertEqual(symbol_proc.result, vr.RESULT_FAILED)
        self.assertEqual(symbol_proc.findings[0].code, "VP-SYMBOL-UNWIRED")

    def test_gap_5_missing_negative_cases_blocks_completion(self) -> None:
        """Gap Class: Test suite lacking negative/failure assertions blocks completion."""
        shallow_test_diff = (
            "+++ b/tests/test_shallow.py\n"
            "+class TestHappyPath:\n"
            "+    def test_happy(self):\n"
            "+        assert 1 == 1\n"
        )
        packet = self._build_clean_packet(test_diff=shallow_test_diff)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        neg_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_NEGATIVE_CASES
        )
        self.assertEqual(neg_proc.result, vr.RESULT_FAILED)
        self.assertEqual(neg_proc.findings[0].code, "VP-NEGATIVE-CASES-MISSING")

    def test_gap_6_test_falsifiability_gap_blocks_completion(self) -> None:
        """Gap Class: Lack of falsifiability proof blocks completion."""
        # Evidence with no falsifiability proof and tests without negative assertion patterns
        unfalsifiable_ev = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "falsifiable": False,
            },
            {
                "evidence_id": "ev-02",
                "binds": ["M-02", "V-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "argv": ["make test"],
            },
        )
        packet = self._build_clean_packet(
            test_diff="+++ b/tests/test_x.py\n+def test_x(): pass",
            raw_evidence_manifest=unfalsifiable_ev,
        )
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        fals_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_TEST_FALSIFIABILITY
        )
        self.assertEqual(fals_proc.result, vr.RESULT_FAILED)
        self.assertEqual(fals_proc.findings[0].code, "VP-FALSIFIABILITY-GAP")

    def test_gap_7_full_suite_gap_blocks_completion(self) -> None:
        """Gap Class: Missing canonical full suite (make test) blocks completion."""
        targeted_only_ev = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01", "M-02", "V-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "argv": ["pytest tests/test_single.py"],
                "falsifiable": True,
            },
        )
        packet = self._build_clean_packet(raw_evidence_manifest=targeted_only_ev)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        suite_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_TARGETED_AND_FULL_CHECKS
        )
        self.assertEqual(suite_proc.result, vr.RESULT_FAILED)
        self.assertEqual(suite_proc.findings[0].code, "VP-FULL-SUITE-GAP")

    def test_gap_8_missing_expected_artifact_blocks_completion(self) -> None:
        """Gap Class: Missing declared artifact blocks completion."""
        packet = self._build_clean_packet()
        report = vr.run_verification_procedures(
            packet,
            expected_artifacts=["agent_workflows/missing_module.py"],
            worktree_files={},
        )

        self.assertFalse(report.is_verified)
        art_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_ARTIFACT_PRESENCE
        )
        self.assertEqual(art_proc.result, vr.RESULT_FAILED)
        self.assertEqual(art_proc.findings[0].code, "VP-ARTIFACT-MISSING")

    def test_gap_9_residual_marker_blocks_completion(self) -> None:
        """Gap Class: Leftover TODO / DEBUG marker in diff blocks completion."""
        residual_diff = (
            self.clean_diff + "\n+# TODO: remove temporary hack before commit"
        )
        packet = self._build_clean_packet(actual_diff=residual_diff)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        res_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_RESIDUAL_SEARCH
        )
        self.assertEqual(res_proc.result, vr.RESULT_FAILED)
        self.assertEqual(res_proc.findings[0].code, "VP-RESIDUAL-MARKER")

    def test_gap_10_stale_evidence_head_mismatch_blocks_completion(self) -> None:
        """Gap Class: Stale evidence from different commit head blocks completion."""
        stale_ev = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01"],
                "exit_code": 0,
                "head": "b" * 40,
                "falsifiable": True,
            },  # Wrong head
            {
                "evidence_id": "ev-02",
                "binds": ["M-02", "V-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "argv": ["make test"],
            },
        )
        packet = self._build_clean_packet(raw_evidence_manifest=stale_ev)
        report = vr.run_verification_procedures(packet)

        self.assertFalse(report.is_verified)
        ev_proc = next(
            p
            for p in report.procedure_results
            if p.procedure_name == vr.PROC_EVIDENCE_VALIDATION
        )
        self.assertEqual(ev_proc.result, vr.RESULT_FAILED)
        self.assertEqual(ev_proc.findings[0].code, "VP-EVIDENCE-HEAD-MISMATCH")


class TestCorrectiveRouting(unittest.TestCase):
    """Test corrective routing, evidence invalidation, and rerun verification (E-04 / V-04)."""

    def setUp(self) -> None:
        self.frozen_reqs = {
            "must": ["M1 implement roles", "M2 implement packet"],
            "validation": ["V1 test procedures"],
        }
        self.scope_fence = {
            "allowed_paths": [
                "agent_workflows/verify_roles.py",
                "tests/test_verify_roles_packet.py",
            ],
            "forbidden_paths": ["secrets/**"],
        }
        self.clean_evidence = (
            {
                "evidence_id": "ev-01",
                "binds": ["M-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "bound_files": ["agent_workflows/verify_roles.py"],
                "falsifiable": True,
            },
            {
                "evidence_id": "ev-02",
                "binds": ["M-02", "V-01"],
                "exit_code": 0,
                "head": "a" * 40,
                "argv": ["make test"],
            },
        )

    def test_clean_report_produces_clean_routing(self) -> None:
        """When report is verified, corrective routing returns is_clean=True with zero corrections."""
        packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff="+++ b/agent_workflows/verify_roles.py\n+class RoleContract:\n+    pass",
            test_diff="+++ b/tests/test_verify_roles_packet.py\n+assertRaises\n+RoleContract",
            raw_evidence_manifest=self.clean_evidence,
            timestamp="2026-08-22T12:00:00Z",
        )
        report = vr.run_verification_procedures(
            packet, declared_symbols=["RoleContract"]
        )
        self.assertTrue(report.is_verified)

        routing = vr.route_verifier_findings(report, packet)
        self.assertTrue(routing.is_clean)
        self.assertEqual(len(routing.in_scope_corrections), 0)
        self.assertEqual(len(routing.corrective_artifacts), 0)

    def test_in_scope_gap_routes_to_bounded_correction(self) -> None:
        """In-scope finding routes to BoundedCorrection for corrector role with invalidated procedures."""
        packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff="+++ b/agent_workflows/verify_roles.py\n+class UnusedClass:\n+    pass",
            test_diff="+++ b/tests/test_verify_roles_packet.py\n+assertRaises",
            raw_evidence_manifest=self.clean_evidence,
            timestamp="2026-08-22T12:00:00Z",
        )
        report = vr.run_verification_procedures(
            packet,
            declared_symbols=["UnusedClass"],
            codebase_content={"test": ""},
        )
        self.assertFalse(report.is_verified)

        routing = vr.route_verifier_findings(report, packet)
        self.assertFalse(routing.is_clean)
        self.assertEqual(len(routing.in_scope_corrections), 1)
        self.assertEqual(len(routing.corrective_artifacts), 0)

        corr = routing.in_scope_corrections[0]
        self.assertEqual(corr.gap_class, "unwired_symbol")
        self.assertEqual(corr.target_role, vr.ROLE_CORRECTOR)
        self.assertIn(vr.PROC_SYMBOL_WIRING, corr.invalidated_procedures)

        # Check serialization
        d = corr.to_dict()
        self.assertEqual(d["gap_class"], "unwired_symbol")
        self.assertEqual(d["target_role"], vr.ROLE_CORRECTOR)

    def test_out_of_scope_gap_routes_to_corrective_ipd_artifact(self) -> None:
        """Scope violation or out-of-scope finding routes to pending CorrectiveIPDArtifact."""
        dirty_diff = "+++ b/secrets/config.json\n+token=123"
        packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff=dirty_diff,
            test_diff="+++ b/tests/test_x.py\n+assertRaises",
            raw_evidence_manifest=self.clean_evidence,
            timestamp="2026-08-22T12:00:00Z",
        )
        report = vr.run_verification_procedures(packet)
        self.assertFalse(report.is_verified)

        routing = vr.route_verifier_findings(report, packet)
        self.assertFalse(routing.is_clean)
        self.assertEqual(len(routing.corrective_artifacts), 1)

        art = routing.corrective_artifacts[0]
        self.assertEqual(art.status, "pending")
        self.assertIn("Corrective IPD", art.content)
        self.assertIn("secrets/config.json", art.content)

    def test_evidence_invalidation_on_file_modification(self) -> None:
        """Modifying files invalidates linked evidence envelopes."""
        ev_manifest = (
            {
                "evidence_id": "ev-01",
                "bound_files": ["agent_workflows/verify_roles.py"],
                "exit_code": 0,
            },
            {"evidence_id": "ev-02", "bound_files": ["unrelated.py"], "exit_code": 0},
        )
        updated = vr.invalidate_evidence_on_correction(
            ev_manifest,
            changed_files=["agent_workflows/verify_roles.py"],
            invalidated_evidence_ids=["ev-02"],
        )

        self.assertTrue(updated[0].get("invalidated"))
        self.assertTrue(updated[0].get("stale"))
        self.assertEqual(updated[0].get("invalidation_reason"), "source_file_modified")

        self.assertTrue(updated[1].get("invalidated"))
        self.assertTrue(updated[1].get("stale"))
        self.assertEqual(
            updated[1].get("invalidation_reason"), "explicit_verifier_invalidation"
        )

    def test_immutability_and_rerun_verification(self) -> None:
        """Original failure remains immutable, and rerun verification evaluates fresh packet."""
        orig_packet = vr.build_verifier_packet(
            run_id="run-12345678",
            workflow_id="wf-08",
            base_commit="0" * 40,
            head_commit="a" * 40,
            worktree_path="/repo",
            frozen_requirements=self.frozen_reqs,
            declared_scope=self.scope_fence,
            actual_diff="+++ b/agent_workflows/verify_roles.py\n+class FixMeClass:\n+    pass",
            test_diff="+++ b/tests/test_verify_roles_packet.py\n+assertRaises",
            raw_evidence_manifest=self.clean_evidence,
            timestamp="2026-08-22T12:00:00Z",
        )
        prior_report = vr.run_verification_procedures(
            orig_packet,
            declared_symbols=["FixMeClass"],
            codebase_content={"test": ""},
        )
        self.assertFalse(prior_report.is_verified)

        routing = vr.route_verifier_findings(prior_report, orig_packet)
        corr = routing.in_scope_corrections[0]

        # Apply correction: wire the symbol into test diff
        fresh_test_diff = (
            "+++ b/tests/test_verify_roles_packet.py\n"
            "+class TestFixMe:\n"
            "+    def test_ok(self):\n"
            "+        with self.assertRaises(Exception):\n"
            "+            FixMeClass()\n"
        )
        fresh_report = vr.rerun_verification_after_correction(
            orig_packet,
            prior_report,
            corr,
            updated_diff=orig_packet.actual_diff,
            fresh_evidence=self.clean_evidence,
            declared_symbols=["FixMeClass"],
            codebase_content={"test": fresh_test_diff},
        )

        # Prior report remains failed (immutable)
        self.assertFalse(prior_report.is_verified)
        self.assertEqual(prior_report.overall_result, vr.RESULT_FAILED)

        # Fresh report is satisfied
        self.assertTrue(fresh_report.is_verified)
        self.assertEqual(fresh_report.overall_result, vr.RESULT_SATISFIED)


if __name__ == "__main__":
    unittest.main()
