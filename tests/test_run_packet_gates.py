"""Tests for bounded step-packet rendering, outcome envelopes, and human decision gates.

awoptimize Order 06 (`ptsfjn`) E-01..E-04.

Validates:
  * E-01 / V-01: Bounded JIT step-packet rendering: all contract fields present, current requirements
                 mapped, unrelated bulk context omitted, size budget respected, deterministic packet digest
                 that changes when a bound requirement changes.
  * E-02 / V-02: Structured outcome envelopes (performed, blocked, failed): legal state updates, rejection
                 of unsupported prose, rejection of missing evidence IDs, wrong attempt numbers, and
                 foreign actors.
  * E-03 / V-03: Human decision gates: interactive choices recorded, headless non-interactive runs stopping
                 at 'needs_input' before gated side effects, no synthesized consent, and timeout policy enforcement.
  * E-04 / V-04: Full suite integration and model-free stdlib unittest execution.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import run_engine, run_freeze, run_gates, run_packet
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store


class TestStepPacketRendering(unittest.TestCase):
    """Test bounded JIT step-packet rendering contract, budgets, and digests (E-01 / V-01)."""

    def setUp(self) -> None:
        self.raw_requirements = {
            "must": [
                "Render bounded step packet with strict contract fields",
                "Reject unsupported prose in outcome envelopes",
                "Stop headless runs at needs_input before gated side effects",
            ],
            "scope": [
                "Touch only run_packet.py, run_gates.py, and test_run_packet_gates.py",
            ],
            "validation": [
                "Golden packet tests pass with size budget and digest verification",
            ],
            "output": [
                "Structured outcome envelope and gate decision records",
            ],
        }
        self.frozen_reqs = run_freeze.freeze_requirements(self.raw_requirements)

        self.workflow_data = {
            "schema_version": 1,
            "id": "test-step-packet-wf",
            "intent": "operate",
            "risk": "medium",
            "interaction": "optional",
            "mutation_boundary": "product",
            "summary": "Workflow for step packet rendering and gate verification",
            "permissions": {
                "allowed_paths": ["agent_workflows/**", "tests/**"],
                "forbidden_paths": ["secrets/**"],
            },
            "requirements": [
                {
                    "id": "R-01",
                    "text": "Render bounded step packet with strict contract fields",
                    "evidence": ["test_report"],
                },
                {
                    "id": "R-02",
                    "text": "Reject unsupported prose in outcome envelopes",
                    "evidence": ["test_report"],
                },
                {
                    "id": "R-03",
                    "text": "Stop headless runs at needs_input before gated side effects",
                    "evidence": ["test_report"],
                },
            ],
            "steps": [
                {
                    "id": "S-01",
                    "action": "Implement bounded JIT step packet rendering",
                    "satisfies": ["R-01"],
                    "depends_on": [],
                    "evidence": ["test_report", "artifact"],
                    "stop_conditions": ["Packet size exceeds budget"],
                    "expected_artifacts": ["agent_workflows/run_packet.py"],
                },
                {
                    "id": "S-02",
                    "action": "Implement outcome envelope validation",
                    "satisfies": ["R-02"],
                    "depends_on": ["S-01"],
                    "evidence": ["test_report"],
                    "stop_conditions": ["Unsupported prose detected"],
                    "expected_artifacts": ["agent_workflows/run_packet.py"],
                },
                {
                    "id": "S-03",
                    "action": "Implement human decision gates and headless needs_input stop",
                    "satisfies": ["R-03"],
                    "depends_on": ["S-02"],
                    "gates": ["human_review_gate"],
                    "evidence": ["test_report"],
                    "stop_conditions": ["Non-interactive consent synthesis attempted"],
                    "expected_artifacts": ["agent_workflows/run_gates.py"],
                },
            ],
            "validations": [
                {"id": "V-01", "verifies": "R-01", "evidence": ["test_report"]},
                {"id": "V-02", "verifies": "R-02", "evidence": ["test_report"]},
                {"id": "V-03", "verifies": "R-03", "evidence": ["test_report"]},
            ],
        }

    def test_golden_packet_contains_every_contract_field(self) -> None:
        """Verify rendered step packet carries all immutable metadata, requirements, scope, tools, action,
        artifacts, evidence contract, stop conditions, dependencies, exit checklist, trace, and digest."""
        packet = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            attempt=1,
            frozen_requirements=self.frozen_reqs,
        )

        # 1. Immutable run & step metadata
        self.assertEqual(packet.run_id, "run-12345678")
        self.assertEqual(packet.workflow_id, "test-step-packet-wf")
        self.assertEqual(packet.step_id, "S-01")
        self.assertEqual(packet.attempt, 1)
        self.assertTrue(schema.is_timestamp(packet.timestamp))

        # 2. Action & artifacts
        self.assertEqual(packet.action, "Implement bounded JIT step packet rendering")
        self.assertEqual(packet.expected_artifacts, ("agent_workflows/run_packet.py",))

        # 3. Evidence contract & stop conditions
        self.assertEqual(packet.evidence_contract, ("test_report", "artifact"))
        self.assertEqual(packet.stop_conditions, ("Packet size exceeds budget",))
        self.assertEqual(packet.depends_on, ())

        # 4. Scope fence & permissions
        self.assertIn("allowed_paths", packet.scope_fence)
        self.assertIn("forbidden_paths", packet.scope_fence)
        self.assertEqual(packet.allowed_files, ("agent_workflows/**", "tests/**"))

        # 5. Bound requirements (only R-01 for S-01, not R-02 or R-03)
        bound_ids = [r.id for r in packet.bound_requirements]
        self.assertIn("R-01", bound_ids)
        self.assertNotIn("R-02", bound_ids)
        self.assertNotIn("R-03", bound_ids)

        # 6. Exit checklist
        self.assertTrue(len(packet.exit_checklist) >= 3)
        self.assertTrue(any("action" in item.lower() for item in packet.exit_checklist))
        self.assertTrue(
            any("evidence" in item.lower() for item in packet.exit_checklist)
        )

        # 7. Source-to-requirement trace
        self.assertIn("S-01", packet.trace)
        self.assertIn("R-01", packet.trace["S-01"])

        # 8. Deterministic digest
        self.assertTrue(schema.is_sha256(packet.packet_digest))

    def test_packet_omits_unrelated_bulk_context(self) -> None:
        """Verify packet for S-01 does not include actions or details of S-02 and S-03."""
        packet = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=self.frozen_reqs,
        )
        rendered_text = packet.render_prompt()

        # Target step action must be present
        self.assertIn("Implement bounded JIT step packet rendering", rendered_text)

        # Unrelated step actions MUST NOT be in rendered prompt
        self.assertNotIn("Implement outcome envelope validation", rendered_text)
        self.assertNotIn("Implement human decision gates", rendered_text)

    def test_packet_digest_changes_when_bound_requirement_changes(self) -> None:
        """Verify deterministic packet digest changes when a bound requirement's text or digest changes."""
        packet_orig = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=self.frozen_reqs,
        )

        # Modify requirement R-01
        modified_reqs = {
            "must": [
                "Render bounded step packet with STRICT CONTRACT FIELDS AND SCHEMA (REVISED)",
                "Reject unsupported prose in outcome envelopes",
                "Stop headless runs at needs_input before gated side effects",
            ],
            "scope": self.raw_requirements["scope"],
            "validation": self.raw_requirements["validation"],
            "output": self.raw_requirements["output"],
        }
        frozen_modified = run_freeze.freeze_requirements(modified_reqs)

        packet_modified = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=frozen_modified,
        )

        self.assertNotEqual(packet_orig.packet_digest, packet_modified.packet_digest)

        # Digest should be stable for same input
        packet_repeat = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=self.frozen_reqs,
        )
        self.assertEqual(packet_orig.packet_digest, packet_repeat.packet_digest)

    def test_packet_size_budget_enforcement(self) -> None:
        """Verify packet rendering respects size budget and raises error if exceeded."""
        # A normal packet should be well under default budget (e.g. 16KB)
        packet = run_packet.build_step_packet(
            workflow=self.workflow_data,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=self.frozen_reqs,
            budget_bytes=8192,
        )
        self.assertLess(len(packet.render_prompt().encode("utf-8")), 8192)

        # When budget is set absurdly low (e.g. 50 bytes), build_step_packet must raise PacketBudgetExceededError
        with self.assertRaises(run_packet.PacketBudgetExceededError):
            run_packet.build_step_packet(
                workflow=self.workflow_data,
                step_id="S-01",
                run_id="run-12345678",
                frozen_requirements=self.frozen_reqs,
                budget_bytes=50,
            )


class TestOutcomeEnvelopeLegality(unittest.TestCase):
    """Test structured outcome envelopes, validation, and refusal of unsupported prose (E-02 / V-02)."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.ledger_path = Path(self.tmpdir) / "run.jsonl"
        self.store = ledger_store.RunLedgerStore(self.ledger_path)

        self.workflow_data = {
            "id": "envelope-test-wf",
            "steps": [
                {
                    "id": "S-01",
                    "action": "execute task 1",
                    "depends_on": [],
                    "satisfies": ["R-01"],
                    "evidence": ["test_report"],
                }
            ],
            "requirements": [{"id": "R-01", "description": "task 1 done"}],
        }

        # Initialize ledger
        self.store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "run",
                "run_id": "run-00000001",
                "actor": "runtime",
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "test-repo",
                "head": "c" * 64,
                "parent": "",
            }
        )
        self.store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "requirement_set",
                "run_id": "run-00000001",
                "actor": "runtime",
                "requirement_digest": "b" * 64,
                "requirements": [{"id": "R-01"}],
                "scope_fence": {},
                "parent": "",
            }
        )

        self.engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_structured_performed_envelope_accepted(self) -> None:
        """Verify structured performed envelope with valid evidence ID updates state to performed."""
        envelope = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=1,
            status="performed",
            actor="executor",
            evidence_ids=("ev-cmd-12345",),
            artifacts=({"path": "output.txt", "sha256": "d" * 64},),
            prose="All unit tests passed cleanly.",
        )

        val_res = run_packet.validate_outcome_envelope(
            envelope,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
            required_evidence_kinds=["test_report"],
        )
        self.assertTrue(val_res.ok, f"Validation failed: {val_res.findings}")

        snapshot = run_packet.apply_outcome_envelope(
            self.engine, envelope, required_evidence_kinds=["test_report"]
        )
        self.assertEqual(snapshot.state, "performed")
        self.assertEqual(self.engine.step_state("S-01"), "performed")

    def test_structured_blocked_and_failed_envelopes_accepted(self) -> None:
        """Verify structured blocked and failed envelopes update state correctly."""
        # 1. Blocked envelope
        blocked_env = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=1,
            status="blocked",
            actor="executor",
            block_reason="Upstream service unavailable",
        )
        val_res = run_packet.validate_outcome_envelope(
            blocked_env,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
        )
        self.assertTrue(val_res.ok)

        # 2. Failed envelope
        failed_env = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=1,
            status="failed",
            actor="executor",
            failure_reason="Assertion failed during test execution",
        )
        val_res_f = run_packet.validate_outcome_envelope(
            failed_env,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
        )
        self.assertTrue(val_res_f.ok)

    def test_unsupported_freeform_prose_rejected_and_cannot_mutate_state(self) -> None:
        """Verify plain prose (e.g. 'all tests pass') without structured status cannot mutate durable state."""
        unsupported_inputs = [
            "I have finished S-01 and all 100 tests pass!",
            {"prose": "Everything is complete and working perfectly."},
            {"message": "done", "status_text": "success"},
            {
                "step": "S-01",
                "result": "performed",
            },  # missing required schema envelope fields
        ]

        for raw_input in unsupported_inputs:
            val_res = run_packet.validate_outcome_envelope(raw_input)
            self.assertFalse(val_res.ok)
            self.assertTrue(
                any(
                    f.code in ("OE-UNSUPPORTED-PROSE", "OE-INVALID-STRUCTURE")
                    for f in val_res.findings
                )
            )

            # Applying unsupported prose must fail closed and NOT mutate durable state
            with self.assertRaises(run_packet.OutcomeEnvelopeError):
                run_packet.apply_outcome_envelope(self.engine, raw_input)

            self.assertEqual(
                self.engine.step_state("S-01"),
                "running",
                "State was modified despite invalid unsupported prose",
            )

    def test_missing_evidence_ids_rejected(self) -> None:
        """Verify performed envelope with empty evidence_ids is rejected when evidence is required."""
        envelope_no_ev = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=1,
            status="performed",
            actor="executor",
            evidence_ids=(),  # empty!
        )
        val_res = run_packet.validate_outcome_envelope(
            envelope_no_ev,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
            required_evidence_kinds=["test_report"],
        )
        self.assertFalse(val_res.ok)
        self.assertTrue(any(f.code == "OE-MISSING-EVIDENCE" for f in val_res.findings))

        with self.assertRaises(run_packet.MissingEvidenceError):
            run_packet.apply_outcome_envelope(
                self.engine, envelope_no_ev, required_evidence_kinds=["test_report"]
            )

    def test_wrong_attempt_number_rejected(self) -> None:
        """Verify envelope with mismatched attempt number is rejected."""
        envelope_wrong_att = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=5,  # expected 1
            status="performed",
            actor="executor",
            evidence_ids=("ev-1",),
        )
        val_res = run_packet.validate_outcome_envelope(
            envelope_wrong_att,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
        )
        self.assertFalse(val_res.ok)
        self.assertTrue(any(f.code == "OE-WRONG-ATTEMPT" for f in val_res.findings))

        with self.assertRaises(run_packet.WrongAttemptError):
            run_packet.apply_outcome_envelope(self.engine, envelope_wrong_att)

    def test_foreign_actor_rejected(self) -> None:
        """Verify envelope authored by unauthorized or foreign actor is rejected."""
        envelope_foreign = run_packet.StepOutcomeEnvelope(
            run_id="run-00000001",
            step_id="S-01",
            attempt=1,
            status="performed",
            actor="unauthorized_foreign_bot",
            evidence_ids=("ev-1",),
        )
        val_res = run_packet.validate_outcome_envelope(
            envelope_foreign,
            expected_run_id="run-00000001",
            expected_step_id="S-01",
            expected_attempt=1,
        )
        self.assertFalse(val_res.ok)
        self.assertTrue(any(f.code == "OE-FOREIGN-ACTOR" for f in val_res.findings))

        with self.assertRaises(run_packet.ForeignActorError):
            run_packet.apply_outcome_envelope(self.engine, envelope_foreign)


class TestHumanDecisionGates(unittest.TestCase):
    """Test human decision gates, headless needs_input refusal, and consent rules (E-03 / V-03)."""

    def setUp(self) -> None:
        self.gate = run_gates.DecisionGate(
            gate_id="deploy_approval_gate",
            prompt="Authorize production deployment of release v2.0?",
            options=("approve", "reject", "abort"),
            default_option="abort",
            timeout_seconds=30.0,
            timeout_policy="refuse",
            requires_human=True,
        )
        self.side_effect_executed = False

    def _sample_action(self) -> str:
        self.side_effect_executed = True
        return "DEPLOYMENT_SUCCESS"

    def test_interactive_choice_recorded_and_executes_action_when_approved(
        self,
    ) -> None:
        """Interactive gate with human approval records decision and executes gated action."""
        decision, result = run_gates.execute_gated_action(
            gate=self.gate,
            action=self._sample_action,
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="alice-lead",
        )

        self.assertTrue(decision.is_approved)
        self.assertEqual(decision.status, run_gates.GATE_STATUS_APPROVED)
        self.assertEqual(decision.selected_option, "approve")
        self.assertEqual(decision.approver, "alice-lead")
        self.assertEqual(decision.actor, "human")
        self.assertTrue(decision.interactive)
        self.assertTrue(self.side_effect_executed)
        self.assertEqual(result, "DEPLOYMENT_SUCCESS")

    def test_interactive_rejection_prevents_side_effect(self) -> None:
        """Interactive gate with rejection stops execution without executing gated action."""
        decision, result = run_gates.execute_gated_action(
            gate=self.gate,
            action=self._sample_action,
            interactive=True,
            input_handler=lambda _g: "reject",
            approver="bob-reviewer",
        )

        self.assertFalse(decision.is_approved)
        self.assertEqual(decision.status, run_gates.GATE_STATUS_REJECTED)
        self.assertEqual(decision.selected_option, "reject")
        self.assertFalse(self.side_effect_executed)
        self.assertIsNone(result)

    def test_headless_noninteractive_run_stops_at_needs_input_before_side_effect(
        self,
    ) -> None:
        """Headless run (interactive=False) MUST stop at needs_input and never execute side effect."""
        decision, result = run_gates.execute_gated_action(
            gate=self.gate,
            action=self._sample_action,
            interactive=False,  # Headless mode!
        )

        self.assertFalse(decision.is_approved)
        self.assertEqual(decision.status, run_gates.GATE_STATUS_NEEDS_INPUT)
        self.assertIsNone(decision.selected_option)
        self.assertIsNone(decision.approver)
        self.assertFalse(decision.interactive)
        self.assertFalse(
            self.side_effect_executed, "Side effect was executed during headless run!"
        )
        self.assertIsNone(result)

    def test_no_synthesized_consent_even_if_default_is_approve(self) -> None:
        """Consent must NEVER be synthesized: even if a gate declares default_option='approve',
        a headless run MUST still return needs_input and NEVER auto-approve."""
        dangerous_gate = run_gates.DecisionGate(
            gate_id="dangerous_gate",
            prompt="Proceed with irreversible wipe?",
            options=("approve", "cancel"),
            default_option="approve",  # declared default
            timeout_policy="apply_default",
            requires_human=True,
        )

        # Headless evaluation
        decision = run_gates.evaluate_gate(dangerous_gate, interactive=False)
        self.assertEqual(
            decision.status,
            run_gates.GATE_STATUS_NEEDS_INPUT,
            "Headless mode synthesized default consent!",
        )
        self.assertFalse(decision.is_approved)

    def test_timeout_policy_enforcement(self) -> None:
        """Verify timeout follows declared policy."""
        # 1. Policy 'refuse' / 'fail' -> returns timed_out / refused
        timeout_gate = run_gates.DecisionGate(
            gate_id="timeout_gate",
            prompt="Quick decision required?",
            options=("yes", "no"),
            timeout_seconds=0.1,
            timeout_policy="refuse",
        )

        def timeout_handler(_g: run_gates.DecisionGate) -> str:
            raise TimeoutError("Human did not respond within deadline")

        decision = run_gates.evaluate_gate(
            timeout_gate, interactive=True, input_handler=timeout_handler
        )
        self.assertEqual(decision.status, run_gates.GATE_STATUS_TIMED_OUT)
        self.assertFalse(decision.is_approved)

        # 2. Policy 'apply_default' with safe non-approval default 'abort'
        abort_gate = run_gates.DecisionGate(
            gate_id="abort_gate",
            prompt="Proceed?",
            options=("proceed", "abort"),
            default_option="abort",
            timeout_policy="apply_default",
        )
        decision_def = run_gates.evaluate_gate(
            abort_gate, interactive=True, input_handler=timeout_handler
        )
        self.assertEqual(decision_def.status, run_gates.GATE_STATUS_ABORTED)
        self.assertEqual(decision_def.selected_option, "abort")
        self.assertFalse(decision_def.is_approved)

    def test_gate_integration_with_run_engine_and_ledger(self) -> None:
        """Verify gate approval integrates with RunEngine and writes human_approval record."""
        tmpdir = tempfile.mkdtemp()
        try:
            lpath = Path(tmpdir) / "run.jsonl"
            store = ledger_store.RunLedgerStore(lpath)
            store.append(
                {
                    "schema_version": schema.LEDGER_SCHEMA_VERSION,
                    "kind": "run",
                    "run_id": "run-00000001",
                    "actor": "runtime",
                    "workflow_digest": "a" * 64,
                    "requirement_digest": "b" * 64,
                    "repo": "test-repo",
                    "head": "c" * 64,
                    "parent": "",
                }
            )
            store.append(
                {
                    "schema_version": schema.LEDGER_SCHEMA_VERSION,
                    "kind": "requirement_set",
                    "run_id": "run-00000001",
                    "actor": "runtime",
                    "requirement_digest": "b" * 64,
                    "requirements": [{"id": "R-01"}],
                    "scope_fence": {},
                    "parent": "",
                }
            )

            wf = {
                "id": "gated-wf",
                "steps": [
                    {
                        "id": "S-01",
                        "action": "gated deploy",
                        "gates": ["deploy_approval_gate"],
                        "satisfies": ["R-01"],
                    }
                ],
                "requirements": [{"id": "R-01"}],
            }
            engine = run_engine.RunEngine(wf, store, run_id="run-00000001")

            # Initially blocked because gate is unapproved
            self.assertEqual(engine.get_runnable_steps(), [])

            # Execute gate with approval
            decision, result = run_gates.execute_gated_action(
                gate=self.gate,
                action=self._sample_action,
                engine=engine,
                interactive=True,
                input_handler=lambda _g: "approve",
                approver="carol-lead",
            )
            self.assertTrue(decision.is_approved)

            # Step S-01 should now be runnable in the engine
            runnable = engine.get_runnable_steps()
            self.assertEqual([s.step_id for s in runnable], ["S-01"])

            # Verify human_approval record was persisted to ledger
            records = store.read_records(verify=True)
            app_recs = [r for r in records if r.get("kind") == "human_approval"]
            self.assertEqual(len(app_recs), 1)
            self.assertEqual(app_recs[0]["gate"], "deploy_approval_gate")
            self.assertEqual(app_recs[0]["approver"], "carol-lead")
            self.assertEqual(app_recs[0]["actor"], "human")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_invalid_option_chosen_refused_at_gate(self) -> None:
        """Verify picking an unlisted option at a decision gate is refused and does not execute action."""
        decision, result = run_gates.execute_gated_action(
            gate=self.gate,
            action=self._sample_action,
            interactive=True,
            input_handler=lambda _g: "unlisted_invalid_option",
            approver="dave",
        )
        self.assertFalse(decision.is_approved)
        self.assertEqual(decision.status, run_gates.GATE_STATUS_REFUSED)
        self.assertFalse(self.side_effect_executed)
        self.assertIsNone(result)

    def test_empty_input_at_gate_refused(self) -> None:
        """Verify empty input at decision gate is refused."""
        decision = run_gates.evaluate_gate(
            self.gate,
            interactive=True,
            input_handler=lambda _g: "   ",
        )
        self.assertFalse(decision.is_approved)
        self.assertEqual(decision.status, run_gates.GATE_STATUS_REFUSED)


class TestStepPacketEdgeCases(unittest.TestCase):
    """Test packet serialization roundtrips, multi-requirement steps, and prompt rendering."""

    def test_packet_serialization_roundtrip(self) -> None:
        """Verify StepPacket to_dict and to_json produce valid serializable JSON with all fields."""
        wf = {
            "id": "wf-roundtrip",
            "steps": [
                {
                    "id": "S-01",
                    "action": "test action",
                    "satisfies": ["R-01", "R-02"],
                    "depends_on": ["S-00"],
                    "evidence": ["command"],
                    "expected_artifacts": ["art.txt"],
                    "stop_conditions": ["error"],
                }
            ],
            "requirements": [
                {"id": "R-01", "text": "Requirement 1"},
                {"id": "R-02", "text": "Requirement 2"},
            ],
            "permissions": {
                "allowed_paths": ["src/**"],
                "forbidden_paths": ["secret/**"],
            },
        }
        packet = run_packet.build_step_packet(
            wf, step_id="S-01", run_id="run-00000002", attempt=2
        )
        json_str = packet.to_json()
        parsed = json.loads(json_str)

        self.assertEqual(parsed["run_id"], "run-00000002")
        self.assertEqual(parsed["step_id"], "S-01")
        self.assertEqual(parsed["attempt"], 2)
        self.assertEqual(len(parsed["bound_requirements"]), 2)
        self.assertEqual(parsed["depends_on"], ["S-00"])
        self.assertEqual(parsed["expected_artifacts"], ["art.txt"])
        self.assertEqual(parsed["evidence_contract"], ["command"])
        self.assertEqual(parsed["allowed_files"], ["src/**"])
        self.assertEqual(parsed["scope_fence"]["forbidden_paths"], ["secret/**"])

    def test_unknown_step_id_raises_key_error(self) -> None:
        """Verify requesting a packet for an unlisted step id raises KeyError."""
        wf = {"id": "wf-mini", "steps": [{"id": "S-01", "action": "act"}]}
        with self.assertRaises(KeyError):
            run_packet.build_step_packet(wf, step_id="S-99")


if __name__ == "__main__":
    unittest.main()
