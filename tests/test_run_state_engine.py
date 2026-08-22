"""Tests for the deterministic run state machine and single-writer engine (awoptimize Order 05).

Validates:
  * E-01 / V-01: Exhaustive state transition table, authorized actors per edge, predicate enforcement,
                 rejection of unlisted/backward transitions, rejection of executor-authored completion,
                 rejection of transitions with missing prerequisites.
  * E-02 / V-02: DAG dependency scheduling, gate approval enforcement, single-writer lease concurrency,
                 fail-closed behavior on lock loss, fail-closed refusal on partial/torn ledger state.
  * E-03 / V-03: Full integration of run state machine + engine with ledger store, verifier decisions,
                 and completion predicates.
"""

from __future__ import annotations

import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_workflows import run_engine, run_state
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store


class TestRunStateMachineTransitionTable(unittest.TestCase):
    """Exhaustive transition table tests verifying state set, edge authority, and predicates."""

    def test_all_states_and_roles_defined(self) -> None:
        """Verify legal states and roles are well-defined closed sets."""
        expected_states = {
            "pending",
            "runnable",
            "running",
            "performed",
            "blocked",
            "failed",
            "verifying",
            "verified",
            "correction_required",
            "cancelled",
            "complete",
        }
        self.assertEqual(run_state.ALL_STATES, expected_states)
        self.assertEqual(
            run_state.ACTIVE_STATES,
            {
                "pending",
                "runnable",
                "running",
                "performed",
                "verifying",
                "correction_required",
            },
        )
        self.assertEqual(run_state.TERMINAL_STATES, {"complete", "cancelled"})

    def test_legal_transitions_with_authorized_actors(self) -> None:
        """Verify each legal edge allows only its authorized actors and specifies its predicate."""
        # 1. pending -> runnable (runtime, coordinator)
        rule = run_state.check_transition(
            "pending",
            "runnable",
            "runtime",
            predicate_values={"dependencies_and_approvals_satisfied": True},
        )
        self.assertEqual(
            rule.required_predicate, "dependencies_and_approvals_satisfied"
        )

        rule_coord = run_state.check_transition(
            "pending",
            "runnable",
            "coordinator",
            predicate_values={"dependencies_and_approvals_satisfied": True},
        )
        self.assertEqual(rule_coord.source, "pending")

        # 2. runnable -> running (runtime, coordinator)
        rule = run_state.check_transition(
            "runnable",
            "running",
            "runtime",
            predicate_values={"lease_acquired_and_packet_emitted": True},
        )
        self.assertEqual(rule.required_predicate, "lease_acquired_and_packet_emitted")

        # 3. running -> performed | blocked | failed (runtime, coordinator)
        for target in ("performed", "blocked", "failed"):
            rule = run_state.check_transition(
                "running",
                target,
                "runtime",
                predicate_values={"valid_attempt_and_evidence": True},
            )
            self.assertEqual(rule.target, target)

        # 4. performed -> verifying (coordinator, runtime)
        rule = run_state.check_transition(
            "performed",
            "verifying",
            "coordinator",
            predicate_values={"required_execution_events_complete": True},
        )
        self.assertEqual(rule.target, "verifying")

        # 5. verifying -> verified | correction_required (verifier, runtime)
        rule = run_state.check_transition(
            "verifying",
            "verified",
            "verifier",
            predicate_values={"verifier_authority_and_evidence_satisfied": True},
        )
        self.assertEqual(rule.target, "verified")

        rule = run_state.check_transition(
            "verifying",
            "correction_required",
            "verifier",
            predicate_values={"verifier_authority_and_findings_recorded": True},
        )
        self.assertEqual(rule.target, "correction_required")

        # 6. verified -> complete (coordinator, runtime)
        rule = run_state.check_transition(
            "verified",
            "complete",
            "coordinator",
            predicate_values={"every_frozen_completion_predicate_true": True},
        )
        self.assertEqual(rule.target, "complete")

        # 7. any active state -> cancelled (coordinator, human)
        for active in run_state.ACTIVE_STATES:
            rule = run_state.check_transition(
                active,
                "cancelled",
                "coordinator",
                predicate_values={"cancellation_event_recorded": True},
            )
            self.assertEqual(rule.target, "cancelled")
            rule_human = run_state.check_transition(
                active,
                "cancelled",
                "human",
                predicate_values={"cancellation_event_recorded": True},
            )
            self.assertEqual(rule_human.target, "cancelled")

    def test_executor_cannot_author_terminal_completion(self) -> None:
        """Reject executor attempting verified -> complete transition."""
        res = run_state.validate_transition(
            "verified",
            "complete",
            "executor",
            predicate_values={"every_frozen_completion_predicate_true": True},
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "ST-UNAUTHORIZED-ACTOR" for f in res.findings))

        with self.assertRaises(run_state.UnauthorizedActorError) as ctx:
            run_state.check_transition(
                "verified",
                "complete",
                "executor",
                predicate_values={"every_frozen_completion_predicate_true": True},
            )
        self.assertIn("executor", str(ctx.exception))

    def test_executor_cannot_author_verifier_transitions(self) -> None:
        """Reject executor attempting verifying -> verified transition."""
        res = run_state.validate_transition(
            "verifying",
            "verified",
            "executor",
            predicate_values={"verifier_authority_and_evidence_satisfied": True},
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "ST-UNAUTHORIZED-ACTOR" for f in res.findings))

        with self.assertRaises(run_state.UnauthorizedActorError):
            run_state.check_transition(
                "verifying",
                "verified",
                "executor",
                predicate_values={"verifier_authority_and_evidence_satisfied": True},
            )

    def test_executor_cannot_cancel_run(self) -> None:
        """Reject executor attempting active -> cancelled transition."""
        res = run_state.validate_transition(
            "running",
            "cancelled",
            "executor",
            predicate_values={"cancellation_event_recorded": True},
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "ST-UNAUTHORIZED-ACTOR" for f in res.findings))

        with self.assertRaises(run_state.UnauthorizedActorError):
            run_state.check_transition(
                "running",
                "cancelled",
                "executor",
                predicate_values={"cancellation_event_recorded": True},
            )

    def test_unlisted_and_backward_transitions_rejected(self) -> None:
        """Exhaustively verify unlisted, skipping, and backward transitions fail closed."""
        invalid_edges = [
            ("pending", "complete"),
            ("pending", "running"),
            ("pending", "performed"),
            ("pending", "verified"),
            ("runnable", "complete"),
            ("runnable", "performed"),
            ("running", "complete"),
            ("running", "verified"),
            ("running", "runnable"),
            ("performed", "complete"),
            ("performed", "running"),
            ("performed", "pending"),
            ("verifying", "complete"),
            ("verifying", "running"),
            ("verified", "running"),
            ("verified", "pending"),
            ("verified", "performed"),
            ("complete", "pending"),
            ("complete", "running"),
            ("complete", "verified"),
            ("cancelled", "running"),
            ("cancelled", "complete"),
        ]
        for src, tgt in invalid_edges:
            for actor in run_state.ROLES:
                res = run_state.validate_transition(src, tgt, actor)
                self.assertFalse(
                    res.ok, f"Expected {src} -> {tgt} by {actor} to be rejected"
                )
                with self.assertRaises(
                    (
                        run_state.IllegalTransitionError,
                        run_state.UnauthorizedActorError,
                    ),
                    msg=f"{src}->{tgt} by {actor}",
                ):
                    run_state.check_transition(src, tgt, actor)

    def test_missing_predicate_fails_closed(self) -> None:
        """Verify transitions fail closed when required predicate is False or missing."""
        # pending -> runnable without satisfied deps
        res = run_state.validate_transition(
            "pending",
            "runnable",
            "runtime",
            predicate_values={"dependencies_and_approvals_satisfied": False},
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "ST-PREDICATE-UNSATISFIED" for f in res.findings))

        with self.assertRaises(run_state.PredicateUnsatisfiedError):
            run_state.check_transition(
                "pending",
                "runnable",
                "runtime",
                predicate_values={"dependencies_and_approvals_satisfied": False},
            )

        # verified -> complete without completion predicates
        res = run_state.validate_transition(
            "verified",
            "complete",
            "coordinator",
            predicate_values={"every_frozen_completion_predicate_true": False},
        )
        self.assertFalse(res.ok)
        self.assertTrue(any(f.code == "ST-PREDICATE-UNSATISFIED" for f in res.findings))

        with self.assertRaises(run_state.PredicateUnsatisfiedError):
            run_state.check_transition(
                "verified",
                "complete",
                "coordinator",
                predicate_values={"every_frozen_completion_predicate_true": False},
            )

    def test_exhaustive_state_actor_matrix(self) -> None:
        """Enumerate all (source, target, actor) tuples and ensure exact agreement with rule table."""
        legal_count = 0
        illegal_count = 0
        for src in run_state.ALL_STATES:
            for tgt in run_state.ALL_STATES:
                for actor in run_state.ROLES:
                    is_legal = run_state.is_legal_edge(src, tgt, actor)
                    res = run_state.validate_transition(src, tgt, actor)
                    if is_legal:
                        legal_count += 1
                        # When predicate is supplied as True, it should validate OK
                        rule = run_state.get_transition_rule(src, tgt)
                        self.assertIsNotNone(rule)
                        res_with_pred = run_state.validate_transition(
                            src,
                            tgt,
                            actor,
                            predicate_values={rule.required_predicate: True},
                        )
                        self.assertTrue(res_with_pred.ok)
                    else:
                        illegal_count += 1
                        self.assertFalse(res.ok)
        self.assertGreater(legal_count, 0)
        self.assertGreater(illegal_count, 0)


class TestRunEngineDAGScheduling(unittest.TestCase):
    """Test single-writer state engine DAG dependency scheduling and gate enforcement."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.ledger_path = Path(self.tmpdir) / "run.jsonl"
        self.store = ledger_store.RunLedgerStore(self.ledger_path)

        self.workflow_data = {
            "id": "test-workflow",
            "steps": [
                {
                    "id": "S-01",
                    "action": "setup environment",
                    "depends_on": [],
                    "satisfies": ["R-01"],
                },
                {
                    "id": "S-02",
                    "action": "run core task A",
                    "depends_on": ["S-01"],
                    "satisfies": ["R-02"],
                },
                {
                    "id": "S-03",
                    "action": "run core task B",
                    "depends_on": ["S-01"],
                    "satisfies": ["R-03"],
                },
                {
                    "id": "S-04",
                    "action": "deploy with gate approval",
                    "depends_on": ["S-02", "S-03"],
                    "gates": ["human_deploy_gate"],
                    "satisfies": ["R-04"],
                },
            ],
            "requirements": [
                {"id": "R-01", "description": "setup ready"},
                {"id": "R-02", "description": "task A done"},
                {"id": "R-03", "description": "task B done"},
                {"id": "R-04", "description": "deploy done"},
            ],
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _init_ledger(self) -> None:
        """Initialize ledger with kind=run and requirement_set records."""
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
                "requirements": [
                    {"id": "R-01"},
                    {"id": "R-02"},
                    {"id": "R-03"},
                    {"id": "R-04"},
                ],
                "scope_fence": {},
                "parent": "",
            }
        )

    def test_initial_state_only_root_step_runnable(self) -> None:
        """Only steps with no unsatisfied dependencies are runnable initially."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        runnable = engine.get_runnable_steps()
        self.assertEqual([s.step_id for s in runnable], ["S-01"])
        self.assertEqual(engine.step_state("S-01"), "pending")
        self.assertEqual(engine.step_state("S-02"), "pending")
        self.assertEqual(engine.step_state("S-03"), "pending")
        self.assertEqual(engine.step_state("S-04"), "pending")

    def test_dag_progression_releases_dependent_steps(self) -> None:
        """Advancing S-01 to performed releases S-02 and S-03 in parallel."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # Release and perform S-01
        engine.release_step("S-01")
        self.assertEqual(engine.step_state("S-01"), "runnable")

        engine.start_step("S-01")
        self.assertEqual(engine.step_state("S-01"), "running")

        engine.record_step_attempt("S-01", state="performed", actor="executor")
        self.assertEqual(engine.step_state("S-01"), "performed")

        # Now S-02 and S-03 should be runnable
        runnable = engine.get_runnable_steps()
        self.assertEqual(sorted([s.step_id for s in runnable]), ["S-02", "S-03"])

        # S-04 requires both S-02 and S-03; performing only S-02 does not release S-04
        engine.release_step("S-02")
        engine.start_step("S-02")
        engine.record_step_attempt("S-02", state="performed", actor="executor")

        runnable_after_s02 = engine.get_runnable_steps()
        self.assertEqual([s.step_id for s in runnable_after_s02], ["S-03"])

    def test_gate_approval_blocks_step_until_approved(self) -> None:
        """S-04 is blocked even when dependencies are satisfied until human approval is recorded."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # Perform S-01, S-02, S-03
        for sid in ("S-01", "S-02", "S-03"):
            engine.release_step(sid)
            engine.start_step(sid)
            engine.record_step_attempt(sid, state="performed", actor="executor")

        # Both S-02 and S-03 are performed, but S-04 has human_deploy_gate
        runnable_before_gate = engine.get_runnable_steps()
        self.assertEqual(runnable_before_gate, [])

        # Record gate approval
        engine.record_approval(
            "human_deploy_gate", approver="human-lead", actor="human"
        )

        # S-04 should now be runnable
        runnable_after_gate = engine.get_runnable_steps()
        self.assertEqual([s.step_id for s in runnable_after_gate], ["S-04"])

    def test_failed_or_blocked_step_stops_downstream_dag(self) -> None:
        """A failed step stops dependent steps from becoming runnable."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        engine.release_step("S-01")
        engine.start_step("S-01")
        engine.record_step_attempt("S-01", state="failed", actor="executor")
        self.assertEqual(engine.step_state("S-01"), "failed")

        runnable = engine.get_runnable_steps()
        self.assertEqual(runnable, [])


class TestRunEngineConcurrencyAndIntegrity(unittest.TestCase):
    """Test single-writer lease serialization, lock loss, and torn ledger fail-closed behavior."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.ledger_path = Path(self.tmpdir) / "run.jsonl"
        self.store = ledger_store.RunLedgerStore(self.ledger_path)

        self.workflow_data = {
            "id": "test-workflow",
            "steps": [
                {
                    "id": "S-01",
                    "action": "task 1",
                    "depends_on": [],
                    "satisfies": ["R-01"],
                },
                {
                    "id": "S-02",
                    "action": "task 2",
                    "depends_on": ["S-01"],
                    "satisfies": ["R-02"],
                },
            ],
            "requirements": [
                {"id": "R-01", "description": "req 1"},
                {"id": "R-02", "description": "req 2"},
            ],
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _init_ledger(self) -> None:
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
                "requirements": [{"id": "R-01"}, {"id": "R-02"}],
                "scope_fence": {},
                "parent": "",
            }
        )

    def test_concurrent_coordinators_cannot_both_act_simultaneously(self) -> None:
        """Two concurrent coordinator engines serialize through the single-writer lock."""
        self._init_ledger()
        engine1 = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )
        engine2 = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        results: list[str] = []
        errors: list[Exception] = []

        def worker(engine: run_engine.RunEngine, worker_id: str) -> None:
            try:
                for _ in range(5):
                    with engine.lease():
                        time.sleep(0.01)
                        results.append(worker_id)
            except (ledger_store.LedgerLockError, RuntimeError, OSError) as e:
                errors.append(e)

        t1 = threading.Thread(target=worker, args=(engine1, "coord1"))
        t2 = threading.Thread(target=worker, args=(engine2, "coord2"))
        t1.start()
        t2.start()
        t1.join(timeout=5.0)
        t2.join(timeout=5.0)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)

    def test_lock_loss_fails_closed(self) -> None:
        """Lock contention timeout raises LedgerLockError and halts progress."""
        self._init_ledger()
        store_fast_timeout = ledger_store.RunLedgerStore(
            self.ledger_path, lock_timeout=0.05
        )
        engine1 = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )
        engine2 = run_engine.RunEngine(
            self.workflow_data, store_fast_timeout, run_id="run-00000001"
        )

        # Hold lock with engine1
        with (
            engine1.lease(),
            self.assertRaises(ledger_store.LedgerLockError),
            engine2.lease(timeout=0.05),
        ):
            pass

    def test_torn_or_corrupt_ledger_fails_closed(self) -> None:
        """A torn trailing line in the ledger fails closed and cannot produce runnable steps."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # Append valid step release
        engine.release_step("S-01")

        # Corrupt the ledger by appending a torn/incomplete JSON line
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(
                '{"kind":"step_attempt","seq":2,"run_id":"run-00000001'
            )  # Torn JSON

        # Engine must fail closed and refuse to reconstruct or release steps
        with self.assertRaises(ledger_store.LedgerCorruption):
            engine.get_runnable_steps()

        with self.assertRaises(ledger_store.LedgerCorruption):
            engine.reconstruct_state()

    def test_broken_hash_chain_fails_closed(self) -> None:
        """A modified record breaking the SHA-256 hash chain fails closed and stops scheduling."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )
        engine.release_step("S-01")
        engine.start_step("S-01")
        engine.record_step_attempt("S-01", state="performed", actor="executor")

        # Mutate the first line in the ledger file to break the hash chain
        lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
        lines[0] = lines[0].replace("test-repo", "tampered-repo")
        self.ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Must fail closed on read/reconstruct
        with self.assertRaises(ledger_store.LedgerCorruption):
            engine.get_runnable_steps()

    def test_cancellation_from_multiple_states(self) -> None:
        """Verify cancellation transition succeeds from active states and stops progress."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # Cancel while pending
        snap = engine.cancel_run(reason="user aborted", actor="coordinator")
        self.assertEqual(snap.state, "cancelled")
        self.assertEqual(engine.run_state(), "cancelled")
        self.assertEqual(engine.get_runnable_steps(), [])

    def test_incomplete_predicates_reject_completion(self) -> None:
        """Evaluating completion when requirements are unsatisfied fails closed."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # Perform only S-01, leaving S-02 unperformed and no verifier decisions
        engine.release_step("S-01")
        engine.start_step("S-01")
        engine.record_step_attempt("S-01", state="performed", actor="executor")

        with self.assertRaises(run_state.PredicateUnsatisfiedError) as ctx:
            engine.complete_run(actor="coordinator")
        self.assertIn("completion predicates failed", str(ctx.exception))

    def test_full_lifecycle_and_completion_enforcement(self) -> None:
        """Complete workflow lifecycle to verified and complete, asserting executor cannot complete."""
        self._init_ledger()
        engine = run_engine.RunEngine(
            self.workflow_data, self.store, run_id="run-00000001"
        )

        # S-01
        engine.release_step("S-01")
        engine.start_step("S-01")
        engine.record_step_attempt("S-01", state="performed", actor="executor")

        # S-02
        engine.release_step("S-02")
        engine.start_step("S-02")
        engine.record_step_attempt("S-02", state="performed", actor="executor")

        # Verifier decisions
        engine.record_verifier_decision("R-01", result="satisfied", actor="verifier")
        engine.record_verifier_decision("R-02", result="satisfied", actor="verifier")

        # Executor attempting to complete run must be rejected
        with self.assertRaises(run_state.UnauthorizedActorError):
            engine.complete_run(actor="executor")

        # Coordinator completing run succeeds
        final_snapshot = engine.complete_run(actor="coordinator")
        self.assertEqual(final_snapshot.state, "complete")
        self.assertEqual(engine.run_state(), "complete")


if __name__ == "__main__":
    unittest.main()
