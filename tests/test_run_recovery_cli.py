"""Model-free deterministic tests for bounded retry/correction, resume/cancel/crash recovery, and
the mutating `aw run` subcommands (awoptimize Order 07 `7yqm1v` E-01..E-04).

These tests are falsifiable: they assert DETECTION/REJECTION (raised typed exceptions, distinct
nonzero exit codes, error output) and concrete durable effects on the append-only ledger, never that
an enum equals itself. No live model, no network.

Coverage:
  * E-01 retry path: failed attempts preserved, budget enforced (RetryLimitExceededError), no
    repetition-to-success, evidence invalidated after change, idempotency dedup, escalation.
  * E-02 resume/cancel/crash: pure-ledger reconstruction, unknown_outcome detection + refusal +
    explicit reconciliation, torn-line crash recovery.
  * legal/illegal transitions mapped to run_state.TRANSITION_RULES, human gate, dependency branch,
    lock collision (lease), evidence invalidation.
  * E-03 CLI golden tests for every subcommand + each exit class; NO ANSI in machine output;
    terminal refusal (finalize refuses incomplete/invalid/unauthorized); JSONL index rebuild from
    the ledger.
"""

from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from agent_workflows import cli, run_engine, run_evidence, run_recovery, run_state
from agent_workflows import run_cli
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store

RUN_ID = "run-abcdef1234"
HEAD = "1" * 40


def _run_record(run_id: str = RUN_ID, head: str = HEAD) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "run",
        "run_id": run_id,
        "actor": "runtime",
        "workflow_digest": "a" * 64,
        "requirement_digest": "b" * 64,
        "repo": "agent-workflows",
        "head": head,
        "parent": "",
    }


def _requirement_set(reqs: List[str]) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "run_id": RUN_ID,
        "actor": "runtime",
        "requirement_digest": "b" * 64,
        "requirements": [{"id": r} for r in reqs],
        "scope_fence": {},
        "parent": "",
    }


_WORKFLOW: Dict[str, Any] = {
    "id": "wf",
    "steps": [
        {"id": "S-01", "action": "setup", "depends_on": [], "satisfies": ["R-01"]},
        {
            "id": "S-02",
            "action": "deploy",
            "depends_on": ["S-01"],
            "gates": ["deploy_gate"],
            "satisfies": ["R-02"],
        },
    ],
    "requirements": [{"id": "R-01"}, {"id": "R-02"}],
}


def _new_store(tmp: Path) -> ledger_store.RunLedgerStore:
    return ledger_store.RunLedgerStore(tmp / "run.jsonl")


def _seed_store(tmp: Path, reqs: List[str]) -> ledger_store.RunLedgerStore:
    store = _new_store(tmp)
    store.append(_run_record())
    store.append(_requirement_set(reqs))
    return store


def _engine(store: ledger_store.RunLedgerStore) -> run_engine.RunEngine:
    return run_engine.RunEngine(_WORKFLOW, store, run_id=RUN_ID)


# ==================================================================================================
# E-01: bounded retry + correction keyed by failure class
# ==================================================================================================


class TestBoundedRetry(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01"])
        self.engine = _engine(self.store)
        # Drive S-01 to a failed attempt.
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="failed", actor="executor")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_failed_attempt_is_preserved(self) -> None:
        """The failed attempt is durably preserved in the ledger (never deleted)."""
        preserved = run_recovery.failed_attempts(self.engine, "S-01")
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0]["state"], "failed")

    def test_retry_records_budget_and_preserves_failure(self) -> None:
        """plan_retry appends a retry record and does NOT delete the failed attempt."""
        plan = run_recovery.plan_retry(self.engine, "S-01", "transient")
        self.assertFalse(plan.duplicate)
        self.assertEqual(run_recovery.count_retries(self.engine, "S-01"), 1)
        # failed attempt is still present
        self.assertEqual(len(run_recovery.failed_attempts(self.engine, "S-01")), 1)

    def test_idempotency_key_dedup_no_duplicate(self) -> None:
        """A retry with an already-recorded idempotency key is a no-op append (not duplicated)."""
        first = run_recovery.plan_retry(
            self.engine, "S-01", "transient", idempotency_key="k1"
        )
        self.assertFalse(first.duplicate)
        dup = run_recovery.plan_retry(
            self.engine, "S-01", "transient", idempotency_key="k1"
        )
        self.assertTrue(dup.duplicate)
        # only ONE retry recorded despite two calls with same key
        self.assertEqual(run_recovery.count_retries(self.engine, "S-01"), 1)

    def test_retry_limit_escalates_not_loops(self) -> None:
        """Once the budget is exhausted, plan_retry escalates with RetryLimitExceededError."""
        run_recovery.plan_retry(self.engine, "S-01", "transient", idempotency_key="k1")
        run_recovery.plan_retry(self.engine, "S-01", "transient", idempotency_key="k2")
        run_recovery.plan_retry(self.engine, "S-01", "transient", idempotency_key="k3")
        with self.assertRaises(run_recovery.RetryLimitExceededError) as ctx:
            run_recovery.plan_retry(
                self.engine, "S-01", "transient", idempotency_key="k4"
            )
        self.assertEqual(ctx.exception.limit, run_recovery.DEFAULT_RETRY_LIMIT)
        self.assertGreaterEqual(
            ctx.exception.attempts, run_recovery.DEFAULT_RETRY_LIMIT
        )

    def test_retry_is_not_repetition_to_success(self) -> None:
        """A retry never converts the failed step to success by mere repetition."""
        run_recovery.plan_retry(self.engine, "S-01", "transient")
        # The step's reconstructed state is still failed; retry alone did not make it complete.
        self.assertEqual(self.engine.step_state("S-01"), "failed")

    def test_retry_of_non_retryable_state_rejected(self) -> None:
        """Planning a retry for a non-failed/blocked step fails closed."""
        # Build a fresh run where S-01 is performed (not retryable).
        tmp2 = Path(tempfile.mkdtemp())
        st = _seed_store(tmp2, ["R-01"])
        eng = _engine(st)
        eng.release_step("S-01")
        eng.start_step("S-01")
        eng.record_step_attempt("S-01", state="performed", actor="executor")
        with self.assertRaises(run_recovery.NoRetryableStateError):
            run_recovery.plan_retry(eng, "S-01", "transient")

    def test_evidence_invalidated_after_change(self) -> None:
        """Evidence bound to the retried step is invalidated so a stale green result is not reused."""
        tmp2 = Path(tempfile.mkdtemp())
        st = _seed_store(tmp2, ["R-01"])
        eng = _engine(st)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # capture evidence bound to S-01 BEFORE the failure
        st.append(
            run_evidence.build_evidence_envelope(
                RUN_ID, "command", ["S-01"], HEAD, "/repo"
            )
        )
        eng.record_step_attempt("S-01", state="failed", actor="executor")
        # live evidence exists before retry
        recs_before = st.read_records()
        live_before = run_recovery._step_evidence_seqs(recs_before, "S-01")
        self.assertTrue(live_before)
        plan = run_recovery.plan_retry(eng, "S-01", "transient")
        self.assertEqual(set(plan.invalidated_evidence), set(live_before))
        # after invalidation, no live evidence remains bound to S-01
        recs_after = st.read_records()
        self.assertEqual(run_recovery._step_evidence_seqs(recs_after, "S-01"), ())

    def test_correction_required_appends_blocker(self) -> None:
        """correction_required appends a correction the completion predicate treats as a blocker."""
        run_recovery.correction_required(self.engine, "R-01", "fix the bug")
        recs = self.store.read_records()
        corrections = [r for r in recs if r.get("kind") == "correction"]
        self.assertTrue(
            any(c.get("corrects_requirement") == "R-01" for c in corrections)
        )

    def test_retry_budget_remaining(self) -> None:
        """retry_budget_remaining decrements as retries are consumed and never goes negative."""
        self.assertEqual(run_recovery.retry_budget_remaining(self.engine, "S-01"), 3)
        run_recovery.plan_retry(self.engine, "S-01", "transient", idempotency_key="k1")
        self.assertEqual(run_recovery.retry_budget_remaining(self.engine, "S-01"), 2)


# ==================================================================================================
# E-02: resume / cancel / crash recovery
# ==================================================================================================


class TestResumeCancelCrash(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_resume_reconstructs_from_ledger_only(self) -> None:
        """resume reconstructs state purely from the ledger (a fresh engine sees the same state)."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        eng.record_step_attempt("S-01", state="performed", actor="executor")
        # New engine over the SAME ledger reconstructs identical state (no shared memory).
        fresh = _engine(ledger_store.RunLedgerStore(store.path))
        report = run_recovery.resume(fresh)
        self.assertEqual(report.run_id, RUN_ID)
        self.assertFalse(report.terminal)

    def test_unknown_outcome_detected_and_refused(self) -> None:
        """A step left running with no terminal attempt is unknown_outcome; resume refuses it."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step(
            "S-01"
        )  # running, no terminal attempt -> interrupted side effect
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ("S-01",))
        with self.assertRaises(run_recovery.UnknownOutcomeError) as ctx:
            run_recovery.resume(eng)
        self.assertEqual(ctx.exception.step_id, "S-01")

    def test_reconcile_unknown_outcome_requires_explicit_state(self) -> None:
        """Reconciliation requires an explicit terminal outcome; a silent rerun is never done."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # invalid reconciled state rejected
        with self.assertRaises(run_recovery.NoRetryableStateError):
            run_recovery.reconcile_unknown_outcome(eng, "S-01", "running")
        # explicit reconciliation clears the unknown-outcome condition
        run_recovery.reconcile_unknown_outcome(
            eng, "S-01", "performed", actor="coordinator"
        )
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ())
        report = run_recovery.resume(eng)
        self.assertEqual(report.run_state, "running")

    def test_reconcile_of_non_unknown_step_rejected(self) -> None:
        """Reconciling a step that is not in an unknown-outcome condition fails closed."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        with self.assertRaises(run_recovery.RecoveryError):
            run_recovery.reconcile_unknown_outcome(eng, "S-01", "performed")

    def test_cancel_records_terminal_transaction(self) -> None:
        """cancel records a terminal cancellation and the run reconstructs as cancelled."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        snap = run_recovery.cancel(eng, reason="operator abort", actor="coordinator")
        self.assertEqual(snap.state, run_state.STATE_CANCELLED)
        self.assertEqual(snap.cancellation_reason, "operator abort")

    def test_crash_recovery_truncates_torn_line_and_flags_unknown(self) -> None:
        """recover_crash truncates a torn trailing line and reconstructs surviving state."""
        store = _seed_store(self.tmp, ["R-01"])
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        eng.record_step_attempt("S-01", state="performed", actor="executor")
        # Simulate a crash mid-append: a torn partial trailing line with no newline.
        with open(store.path, "a", encoding="utf-8") as fh:
            fh.write('{"kind":"step_attempt","seq":99,"partial"')
        report = run_recovery.recover_crash(eng)
        self.assertTrue(report.recovered_torn_line)
        self.assertGreater(report.truncated_bytes, 0)
        # After recovery, the surviving ledger is clean and reconstructs S-01 performed.
        self.assertEqual(eng.step_state("S-01"), "performed")


# ==================================================================================================
# Legal/illegal transitions, human gate, dependency branch, lock collision
# ==================================================================================================


class TestTransitionsAndDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01", "R-02"])
        self.engine = _engine(self.store)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_every_legal_edge_in_table_is_accepted(self) -> None:
        """Each rule in TRANSITION_RULES is accepted for an authorized actor with its predicate."""
        for rule in run_state.TRANSITION_RULES:
            actor = sorted(rule.authorized_actors)[0]
            accepted = run_state.check_transition(
                rule.source,
                rule.target,
                actor,
                predicate_values={rule.required_predicate: True},
            )
            self.assertEqual(accepted.target, rule.target)

    def test_illegal_edge_rejected(self) -> None:
        """An edge absent from the table is rejected as illegal."""
        with self.assertRaises(run_state.IllegalTransitionError):
            run_state.check_transition("pending", "complete", "coordinator")

    def test_executor_cannot_author_completion(self) -> None:
        """verified -> complete authored by executor is rejected (unauthorized)."""
        with self.assertRaises(run_state.UnauthorizedActorError):
            run_state.check_transition(
                "verified",
                "complete",
                "executor",
                predicate_values={"every_frozen_completion_predicate_true": True},
            )

    def test_missing_predicate_rejected(self) -> None:
        """A legal, authorized edge with an unsatisfied predicate fails closed."""
        with self.assertRaises(run_state.PredicateUnsatisfiedError):
            run_state.check_transition(
                "pending",
                "runnable",
                "runtime",
                predicate_values={"dependencies_and_approvals_satisfied": False},
            )

    def test_dependency_branch_gates_downstream_step(self) -> None:
        """S-02 is not runnable until S-01 is performed (dependency) AND the gate is approved."""
        self.assertEqual(
            [s.step_id for s in self.engine.get_runnable_steps()], ["S-01"]
        )
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="performed", actor="executor")
        # dependency satisfied, but the human gate blocks S-02
        self.assertEqual(self.engine.get_runnable_steps(), [])
        self.engine.record_approval("deploy_gate", approver="lead", actor="human")
        self.assertEqual(
            [s.step_id for s in self.engine.get_runnable_steps()], ["S-02"]
        )

    def test_lock_collision_fails_closed(self) -> None:
        """A second writer contending for the single-writer lock times out (lease serialization)."""
        held = threading.Event()
        release = threading.Event()

        def holder() -> None:
            with self.engine.lease(timeout=5.0):
                held.set()
                release.wait(2.0)

        t = threading.Thread(target=holder)
        t.start()
        self.assertTrue(held.wait(2.0))
        other = run_engine.RunEngine(
            _WORKFLOW,
            ledger_store.RunLedgerStore(self.store.path, lock_timeout=0.2),
            run_id=RUN_ID,
        )
        with self.assertRaises(ledger_store.LedgerLockError):
            with other.lease(timeout=0.2):
                pass
        release.set()
        t.join()


# ==================================================================================================
# E-03: CLI golden tests for every subcommand + each exit class
# ==================================================================================================


def _complete_run_records() -> List[Dict[str, Any]]:
    """Records for a clean, complete, finalizable run (requirements covered by verifier passes)."""
    return [
        _run_record(),
        _requirement_set(["R-01"]),
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "step_attempt",
            "run_id": RUN_ID,
            "actor": "executor",
            "step": "S-01",
            "state": "performed",
            "attempt": 1,
            "parent": "",
        },
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "verifier_decision",
            "run_id": RUN_ID,
            "actor": "verifier",
            "requirement": "R-01",
            "result": "satisfied",
            "parent": "",
        },
    ]


class TestRunCliSubcommands(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ledger = self.tmp / "run.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _store(self) -> ledger_store.RunLedgerStore:
        return ledger_store.RunLedgerStore(self.ledger)

    def _workflow_file(self) -> str:
        """Write the DAG workflow to a JSON file so DAG-dependent CLI commands know the steps."""
        p = self.tmp / "wf.json"
        p.write_text(json.dumps(_WORKFLOW), encoding="utf-8")
        return str(p)

    def _seed_complete(self) -> None:
        store = self._store()
        for rec in _complete_run_records():
            store.append(rec)

    def _seed_incomplete(self) -> None:
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))

    def _cli(self, *argv: str) -> "tuple[int, str]":
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    # ---- exit-class: invalid invocation / missing ledger -----------------------------------------

    def test_missing_ledger_invalid_invocation(self) -> None:
        rc, out = self._cli("run", "status", str(self.tmp / "nope.jsonl"))
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)

    def test_start_without_step_invalid_invocation(self) -> None:
        self._seed_incomplete()
        rc, _ = self._cli("run", "start", str(self.ledger))
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)

    def test_record_invalid_state_invalid_invocation(self) -> None:
        self._seed_incomplete()
        rc, _ = self._cli(
            "run", "record", str(self.ledger), "--step", "S-01", "--state", "bogus"
        )
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)

    # ---- status ----------------------------------------------------------------------------------

    def test_status_incomplete_exit_one(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli("run", "status", str(self.ledger))
        self.assertEqual(rc, run_cli.EXIT_INCOMPLETE)
        self.assertIn("Run:", out)

    def test_status_agent_machine_is_ansi_free(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli("run", "status", str(self.ledger), "--agent")
        self.assertNotIn("\x1b", out)
        data = json.loads(out.strip())
        self.assertEqual(data["run_id"], RUN_ID)

    # ---- next ------------------------------------------------------------------------------------

    def test_next_lists_runnable(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli(
            "run",
            "next",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--json",
        )
        self.assertEqual(rc, run_cli.EXIT_OK)
        data = json.loads(out)
        self.assertIn("S-01", data["runnable_steps"])

    def test_next_blocked_when_none_runnable(self) -> None:
        # A run whose only root step is already performed leaves S-02 gated (deploy_gate).
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "step_attempt",
                "run_id": RUN_ID,
                "actor": "executor",
                "step": "S-01",
                "state": "performed",
                "attempt": 1,
                "parent": "",
            }
        )
        # S-02 requires the deploy_gate; without approval nothing is runnable.
        rc, _ = self._cli(
            "run",
            "next",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--agent",
        )
        self.assertEqual(rc, run_cli.EXIT_BLOCKED)

    # ---- record ----------------------------------------------------------------------------------

    def test_record_performed_exit_ok_and_persists(self) -> None:
        """Recording a performed outcome for a runnable root step succeeds and is durable."""
        self._seed_incomplete()
        rc, out = self._cli(
            "run",
            "record",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--step",
            "S-01",
            "--state",
            "performed",
        )
        self.assertEqual(rc, run_cli.EXIT_OK)
        # The step_attempt is persisted: a fresh engine reconstructs S-01 as performed.
        eng = run_engine.RunEngine(_WORKFLOW, self._store(), run_id=RUN_ID)
        self.assertEqual(eng.step_state("S-01"), "performed")

    def test_record_failed_returns_blocked_class(self) -> None:
        """Recording a failed outcome returns the blocked exit class (a failure is not success)."""
        self._seed_incomplete()
        rc, _ = self._cli(
            "run",
            "record",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--step",
            "S-01",
            "--state",
            "failed",
        )
        self.assertEqual(rc, run_cli.EXIT_BLOCKED)

    def test_record_non_runnable_step_blocked(self) -> None:
        """Recording an outcome for a step whose dependencies/gates are unmet is refused (blocked)."""
        self._seed_incomplete()
        # S-02 depends on S-01 (unperformed) and needs the deploy_gate: not runnable.
        rc, _ = self._cli(
            "run",
            "record",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--step",
            "S-02",
            "--state",
            "performed",
        )
        self.assertEqual(rc, run_cli.EXIT_BLOCKED)

    def test_record_unknown_step_invalid(self) -> None:
        self._seed_incomplete()
        rc, _ = self._cli(
            "run",
            "record",
            str(self.ledger),
            "--workflow",
            self._workflow_file(),
            "--step",
            "S-99",
            "--state",
            "performed",
        )
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)

    # ---- resume ----------------------------------------------------------------------------------

    def test_resume_ok(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli("run", "resume", str(self.ledger), "--json")
        self.assertEqual(rc, run_cli.EXIT_OK)
        data = json.loads(out)
        self.assertFalse(data["terminal"])

    def test_resume_cli_reports_unknown_outcome_condition(self) -> None:
        """The resume CLI surfaces the UNKNOWN_OUTCOME sentinel when a side effect is interrupted."""
        self._seed_incomplete()

        # Force the interrupted-side-effect branch: patch detection + resume to raise as if a step
        # were left running mid-flight (running state is ephemeral and not persisted across procs).
        def _fake_detect(_engine: Any) -> "tuple[str, ...]":
            return ("S-01",)

        def _fake_resume(_engine: Any) -> Any:
            raise run_recovery.UnknownOutcomeError("S-01")

        with patch.object(
            run_recovery, "detect_unknown_outcomes", _fake_detect
        ), patch.object(run_recovery, "resume", _fake_resume):
            rc, out = self._cli(
                "run",
                "resume",
                str(self.ledger),
                "--workflow",
                self._workflow_file(),
                "--json",
            )
        self.assertEqual(rc, run_cli.EXIT_BLOCKED)
        data = json.loads(out)
        self.assertEqual(data["condition"], run_recovery.UNKNOWN_OUTCOME)
        self.assertIn("S-01", data["unknown_outcome_steps"])

    def test_resume_refuses_unknown_outcome(self) -> None:
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))
        eng = _engine(store)
        eng.release_step("S-01")
        eng.start_step("S-01")
        # persist a running side-effect marker so a fresh CLI process detects it: the ledger has a
        # step_attempt only if recorded; to make it visible we record a running via a torn state is
        # not possible, so we assert the detection at the recovery layer through the in-process ledger
        # by recording NO terminal attempt. The CLI reconstructs S-01 as pending (running is
        # ephemeral), so unknown_outcome is only observable in-process; assert that path directly.
        self.assertEqual(run_recovery.detect_unknown_outcomes(eng), ("S-01",))
        with self.assertRaises(run_recovery.UnknownOutcomeError):
            run_recovery.resume(eng)

    # ---- cancel ----------------------------------------------------------------------------------

    def test_cancel_ok(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli(
            "run", "cancel", str(self.ledger), "--reason", "abort", "--json"
        )
        self.assertEqual(rc, run_cli.EXIT_OK)
        data = json.loads(out)
        self.assertTrue(data["cancelled"])
        self.assertEqual(data["run_state"], run_state.STATE_CANCELLED)

    def test_cancel_unauthorized_actor_operational(self) -> None:
        self._seed_incomplete()
        rc, _ = self._cli("run", "cancel", str(self.ledger), "--actor", "executor")
        self.assertEqual(rc, run_cli.EXIT_OPERATIONAL)

    # ---- finalize: terminal refusal --------------------------------------------------------------

    def test_finalize_complete_exit_ok(self) -> None:
        self._seed_complete()
        rc, out = self._cli("run", "finalize", str(self.ledger), "--json")
        self.assertEqual(rc, run_cli.EXIT_OK)
        data = json.loads(out)
        self.assertTrue(data["finalized"])

    def test_finalize_refuses_incomplete(self) -> None:
        self._seed_incomplete()
        rc, out = self._cli("run", "finalize", str(self.ledger), "--json")
        self.assertEqual(rc, run_cli.EXIT_INCOMPLETE)
        self.assertIn("incomplete", out.lower())

    def test_finalize_refuses_unauthorized(self) -> None:
        self._seed_complete()
        rc, _ = self._cli("run", "finalize", str(self.ledger), "--actor", "executor")
        self.assertEqual(rc, run_cli.EXIT_OPERATIONAL)

    def test_finalize_refuses_invalid_evidence(self) -> None:
        """A ledger with an invalid tool_event (failed exit) is refused with the invalid-evidence code."""
        store = self._store()
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "step_attempt",
                "run_id": RUN_ID,
                "actor": "executor",
                "step": "S-01",
                "state": "performed",
                "attempt": 1,
                "parent": "",
            }
        )
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "tool_event",
                "run_id": RUN_ID,
                "actor": "executor",
                "argv": ["pytest"],
                "cwd": "/repo",
                "exit_code": 1,  # failed exit -> EV-FAILED-EXIT
                "stdout_sha256": "e" * 64,
                "parent": "",
            }
        )
        store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "verifier_decision",
                "run_id": RUN_ID,
                "actor": "verifier",
                "requirement": "R-01",
                "result": "satisfied",
                "parent": "",
            }
        )
        rc, out = self._cli("run", "finalize", str(self.ledger), "--json")
        self.assertEqual(rc, run_cli.EXIT_INVALID_EVIDENCE)
        self.assertIn("EV-FAILED-EXIT", out)

    def test_finalize_corrupted_ledger(self) -> None:
        """A corrupted (broken hash chain) ledger is refused with the corrupted-ledger code."""
        self._seed_complete()
        # Corrupt the chain: append a hand-written line with a wrong prev_hash.
        with open(self.ledger, "a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "step_attempt",
                        "seq": 99,
                        "run_id": RUN_ID,
                        "actor": "executor",
                        "timestamp": "2026-08-22T10:00:09Z",
                        "parent": "",
                        "prev_hash": "0" * 64,
                        "step": "S-02",
                        "state": "performed",
                        "attempt": 1,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
        rc, _ = self._cli("run", "finalize", str(self.ledger), "--json")
        self.assertEqual(rc, run_cli.EXIT_CORRUPTED_LEDGER)

    # ---- machine output is ANSI-free across all mutating subcommands ------------------------------

    def test_all_machine_modes_ansi_free(self) -> None:
        self._seed_complete()
        for sub in ("status", "next", "resume"):
            _, out = self._cli("run", sub, str(self.ledger), "--agent")
            self.assertNotIn("\x1b", out, f"ANSI leaked in `run {sub} --agent`")
            _, out2 = self._cli("run", sub, str(self.ledger), "--json")
            self.assertNotIn("\x1b", out2, f"ANSI leaked in `run {sub} --json`")


# ==================================================================================================
# JSONL index rebuildable from the authoritative ledger
# ==================================================================================================


class TestRebuildableIndex(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ledger = self.tmp / "run.jsonl"
        store = ledger_store.RunLedgerStore(self.ledger)
        for rec in _complete_run_records():
            store.append(rec)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_index_is_rebuilt_from_ledger(self) -> None:
        """The runtime index is a rebuildable projection of the ledger (append-only JSONL, no SQLite)."""
        rows = run_cli.rebuild_index(self.ledger)
        kinds = [r["kind"] for r in rows]
        self.assertEqual(kinds[0], "run")
        self.assertIn("step_attempt", kinds)
        self.assertIn("verifier_decision", kinds)
        # seqs are contiguous from 0 (the ledger stays authoritative)
        self.assertEqual([r["seq"] for r in rows], list(range(len(rows))))

    def test_index_written_as_jsonl_and_reparses(self) -> None:
        index_path = self.tmp / "index.jsonl"
        out = run_cli.write_index(self.ledger, index_path)
        self.assertTrue(out.is_file())
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        parsed = [json.loads(line) for line in lines]
        self.assertEqual(len(parsed), len(run_cli.rebuild_index(self.ledger)))
        # Rebuilding again is deterministic (idempotent projection).
        run_cli.write_index(self.ledger, index_path)
        lines2 = out.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(lines, lines2)


class TestLedgerResolutionAndWrongFormatVerdict(unittest.TestCase):
    """`e6b9kt`: the ledger must not claim `events.jsonl`, and wrong-format is not corruption.

    Before this fix, `aw run show <any-real-run-id>` resolved to the driver's own `events.jsonl` and
    printed `ledger corruption detected` with eight RL-E010 findings about a perfectly healthy file.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.run_id = RUN_ID
        self.run_dir = self.tmp / ".aw" / "records" / "runs" / self.run_id
        self.run_dir.mkdir(parents=True)
        # The RUNNER's own event log: healthy, and NOT a ledger.
        (self.run_dir / "events.jsonl").write_text(
            json.dumps({"at": "2026-08-24T14:01:12Z", "event": "run_start", "queue": 3})
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cli(self, *argv: str) -> "tuple[int, str]":
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    # ---- resolution ---------------------------------------------------------------------------

    def test_run_id_does_not_resolve_to_the_drivers_event_log(self) -> None:
        resolved = run_cli.resolve_ledger_path(self.run_id, self.tmp)
        self.assertIsNone(
            resolved,
            "a bare run id must not resolve to events.jsonl, which the ledger does not own",
        )

    def test_run_id_resolves_to_a_real_ledger_when_one_exists(self) -> None:
        ledger = self.run_dir / ledger_store.LEDGER_FILENAME
        store = ledger_store.RunLedgerStore(ledger)
        store.append(_run_record())
        resolved = run_cli.resolve_ledger_path(self.run_id, self.tmp)
        self.assertEqual(resolved, ledger.resolve())

    def test_explicit_path_is_still_honoured_verbatim(self) -> None:
        """An operator pointing at an explicit file keeps working; the shape check judges it."""
        odd = self.tmp / "somewhere-else.jsonl"
        odd.write_text("{}\n", encoding="utf-8")
        self.assertEqual(run_cli.resolve_ledger_path(str(odd), self.tmp), odd.resolve())

    # ---- the verdict --------------------------------------------------------------------------

    def test_show_on_a_real_run_id_reports_missing_not_corrupt(self) -> None:
        rc, out = self._cli("run", "show", self.run_id, "--dir", str(self.tmp))
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        self.assertNotIn("corruption", out.lower())

    def test_show_on_the_event_log_path_is_wrong_format_not_corruption(self) -> None:
        rc, out = self._cli("run", "show", str(self.run_dir / "events.jsonl"))
        self.assertEqual(rc, run_cli.EXIT_NOT_A_LEDGER)
        self.assertIn("not a run ledger", out.lower())
        self.assertNotIn("corrupt", out.lower())

    def test_verify_ledger_on_the_event_log_is_wrong_format(self) -> None:
        rc, out = self._cli("run", "verify-ledger", str(self.run_dir / "events.jsonl"))
        self.assertEqual(rc, run_cli.EXIT_NOT_A_LEDGER)
        self.assertNotIn("corrupt", out.lower())

    def test_evidence_on_the_event_log_is_wrong_format(self) -> None:
        rc, out = self._cli("run", "evidence", str(self.run_dir / "events.jsonl"))
        self.assertEqual(rc, run_cli.EXIT_NOT_A_LEDGER)
        self.assertNotIn("corrupt", out.lower())

    def test_status_on_the_event_log_is_wrong_format(self) -> None:
        """The mutating family shares the verdict through `_build_engine`."""
        rc, out = self._cli("run", "status", str(self.run_dir / "events.jsonl"))
        self.assertEqual(rc, run_cli.EXIT_NOT_A_LEDGER)
        self.assertNotIn("corrupt", out.lower())

    def test_machine_output_flags_not_a_ledger_and_denies_corruption(self) -> None:
        rc, out = self._cli(
            "run", "show", str(self.run_dir / "events.jsonl"), "--agent"
        )
        self.assertEqual(rc, run_cli.EXIT_NOT_A_LEDGER)
        payload = json.loads(out.strip().splitlines()[-1])
        self.assertTrue(payload["not_a_ledger"])
        self.assertFalse(payload["corrupted"])
        self.assertEqual(payload["exit_code"], run_cli.EXIT_NOT_A_LEDGER)
        self.assertNotIn("\x1b[", out)

    # ---- ADVERSARIAL: real corruption must still be reported as corruption ---------------------

    def test_tampered_ledger_still_reported_as_corruption_via_cli(self) -> None:
        """The new wrong-format path must not swallow real tamper evidence at the CLI boundary."""
        ledger = self.run_dir / ledger_store.LEDGER_FILENAME
        store = ledger_store.RunLedgerStore(ledger)
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))
        lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
        tampered = json.loads(lines[1])
        tampered["prev_hash"] = "f" * 64
        lines[1] = json.dumps(tampered, sort_keys=True) + "\n"
        ledger.write_text("".join(lines), encoding="utf-8")

        rc, out = self._cli("run", "show", str(ledger))
        self.assertNotEqual(
            rc,
            run_cli.EXIT_NOT_A_LEDGER,
            "a tampered ledger must never be excused as a wrong-format file",
        )
        self.assertIn("corruption", out.lower())


if __name__ == "__main__":
    unittest.main()
