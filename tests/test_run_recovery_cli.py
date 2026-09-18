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
        """Once the budget is exhausted, plan_retry escalates with RetryLimitExceededError.

        Consumes exactly `DEFAULT_RETRY_LIMIT` retries and then expects the refusal, DERIVING the
        count from the constant rather than hard-coding it: the previous version issued three fixed
        retries, which silently coupled this test to the value being 3.
        """
        for i in range(run_recovery.DEFAULT_RETRY_LIMIT):
            run_recovery.plan_retry(
                self.engine, "S-01", "transient", idempotency_key=f"k{i + 1}"
            )
        with self.assertRaises(run_recovery.RetryLimitExceededError) as ctx:
            run_recovery.plan_retry(
                self.engine, "S-01", "transient", idempotency_key="k-over-budget"
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
        """retry_budget_remaining decrements as retries are consumed and never goes negative.

        Anchored to `DEFAULT_RETRY_LIMIT` rather than a literal, so aligning the default to the
        spec's 2 (2026-08-31) cannot silently invalidate the assertion.
        """
        limit = run_recovery.DEFAULT_RETRY_LIMIT
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01"), limit
        )
        run_recovery.plan_retry(self.engine, "S-01", "transient", idempotency_key="k1")
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01"), limit - 1
        )


# ==================================================================================================
# runcodes Order 3 (`sq61qd`): spec 25kzda 2.1's 0..10 inclusive retry-budget range
# ==================================================================================================


class TestRetryBudgetRangeValidation(unittest.TestCase):
    """The retry budget's legal range is enforced at every entry point that accepts one.

    Falsifiable by construction: these assert the BOUNDARIES (-1, 0, 10, 11), not a middle value,
    because an off-by-one is the only bug this validation can realistically ship and a middle value
    passes against one. They also assert the ERROR TYPE, since a bad `limit` (a caller error) must be
    distinguishable from `RetryLimitExceededError` (a step exhausting its budget at runtime).
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.store = _seed_store(self.tmp, ["R-01"])
        self.engine = _engine(self.store)
        # Drive S-01 to a failed attempt so it is retryable (a non-retryable step would raise
        # NoRetryableStateError first and mask which check actually fired).
        self.engine.release_step("S-01")
        self.engine.start_step("S-01")
        self.engine.record_step_attempt("S-01", state="failed", actor="executor")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ---- the shared validator, called with the value ALONE ----------------------------------------

    def test_validator_is_callable_with_the_value_alone(self) -> None:
        """The bound lives in ONE validator taking just the value (no engine, no step id).

        This is what makes it reachable from the `--retry-budget` flag layer (`uyeko5` E-04), which
        validates an operator value at parse time when no engine or step exists.

        Uses an arbitrary in-range value, deliberately NOT the default, so this test says nothing
        about what the default happens to be.
        """
        self.assertEqual(run_recovery.validate_retry_budget(5), 5)

    def test_validator_rejects_below_lower_bound(self) -> None:
        """-1 is refused, and the message names the offending value and the legal range."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError) as ctx:
            run_recovery.validate_retry_budget(-1)
        msg = str(ctx.exception)
        self.assertIn("-1", msg)
        self.assertIn(
            f"{run_recovery.MIN_RETRY_LIMIT}..{run_recovery.MAX_RETRY_LIMIT}", msg
        )

    def test_validator_rejects_above_upper_bound(self) -> None:
        """11 (one past the inclusive upper bound) is refused: the boundary, not a middle value."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError) as ctx:
            run_recovery.validate_retry_budget(run_recovery.MAX_RETRY_LIMIT + 1)
        self.assertIn(str(run_recovery.MAX_RETRY_LIMIT + 1), str(ctx.exception))

    def test_validator_rejects_an_effectively_unbounded_budget(self) -> None:
        """A huge budget is refused: an unbounded correction loop is what the bound exists to stop."""
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(10_000)

    def test_validator_accepts_both_inclusive_boundaries(self) -> None:
        """0 and 10 are LEGAL (the range is inclusive at both ends)."""
        self.assertEqual(
            run_recovery.validate_retry_budget(run_recovery.MIN_RETRY_LIMIT),
            run_recovery.MIN_RETRY_LIMIT,
        )
        self.assertEqual(
            run_recovery.validate_retry_budget(run_recovery.MAX_RETRY_LIMIT),
            run_recovery.MAX_RETRY_LIMIT,
        )

    def test_validator_rejects_bool_and_non_int(self) -> None:
        """`bool` is a subclass of `int`, so `True` must not silently mean a budget of 1."""
        for bad in (True, False, 2.0, "3", None):
            with self.subTest(bad=bad):
                with self.assertRaises(run_recovery.InvalidRetryBudgetError):
                    run_recovery.validate_retry_budget(bad)

    def test_invalid_budget_error_is_not_a_retry_limit_exceeded_error(self) -> None:
        """A caller error must NOT be catchable as normal budget escalation, and vice versa.

        Asserted rather than assumed: `assertRaises(Exception)` would pass against exactly the
        conflation this distinction forbids.
        """
        self.assertTrue(
            issubclass(run_recovery.InvalidRetryBudgetError, run_recovery.RecoveryError)
        )
        self.assertFalse(
            issubclass(
                run_recovery.InvalidRetryBudgetError,
                run_recovery.RetryLimitExceededError,
            )
        )
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(-1)
        try:
            run_recovery.validate_retry_budget(-1)
        except (
            run_recovery.RetryLimitExceededError
        ) as exc:  # pragma: no cover - must not happen
            self.fail(f"out-of-range budget was caught as budget exhaustion: {exc!r}")
        except run_recovery.InvalidRetryBudgetError:
            pass

    # ---- plan_retry routes through the same validator ---------------------------------------------

    def test_plan_retry_rejects_below_lower_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=-1)

    def test_plan_retry_rejects_above_upper_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(
                self.engine,
                "S-01",
                "transient",
                limit=run_recovery.MAX_RETRY_LIMIT + 1,
            )

    def test_plan_retry_rejects_bool_budget(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=True)

    def test_plan_retry_accepts_upper_boundary(self) -> None:
        plan = run_recovery.plan_retry(
            self.engine, "S-01", "transient", limit=run_recovery.MAX_RETRY_LIMIT
        )
        self.assertEqual(plan.limit, run_recovery.MAX_RETRY_LIMIT)
        self.assertFalse(plan.duplicate)

    def test_an_out_of_range_budget_appends_nothing(self) -> None:
        """A refused budget is refused BEFORE any ledger append (fail closed, no side effect)."""
        before = len(self.store.read_records())
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=-1)
        self.assertEqual(len(self.store.read_records()), before)

    # ---- retry_budget_remaining routes through the same validator ---------------------------------

    def test_retry_budget_remaining_rejects_below_lower_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=-1)

    def test_retry_budget_remaining_rejects_above_upper_bound(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(
                self.engine, "S-01", limit=run_recovery.MAX_RETRY_LIMIT + 1
            )

    def test_retry_budget_remaining_rejects_bool_budget(self) -> None:
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=True)

    def test_retry_budget_remaining_accepts_upper_boundary(self) -> None:
        self.assertEqual(
            run_recovery.retry_budget_remaining(
                self.engine, "S-01", limit=run_recovery.MAX_RETRY_LIMIT
            ),
            run_recovery.MAX_RETRY_LIMIT,
        )

    def test_retry_budget_remaining_clamp_still_never_negative(self) -> None:
        """The independent `max(0, ...)` clamp survives: a consumed budget never reports negative."""
        limit = run_recovery.MIN_RETRY_LIMIT + 1
        run_recovery.plan_retry(
            self.engine, "S-01", "transient", limit=limit, idempotency_key="k1"
        )
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=limit), 0
        )

    # ---- 0 means NO RETRIES, behaviorally ---------------------------------------------------------

    def test_zero_budget_means_no_retries_not_the_default(self) -> None:
        """`limit=0` is accepted AND means zero retries, not a silently substituted default.

        "Accepted" alone would also pass against an implementation that treated the falsy 0 as unset
        and swapped in DEFAULT_RETRY_LIMIT, so the BEHAVIOR is what is asserted here.
        """
        zero = run_recovery.MIN_RETRY_LIMIT
        self.assertEqual(
            run_recovery.retry_budget_remaining(self.engine, "S-01", limit=zero), 0
        )
        with self.assertRaises(run_recovery.RetryLimitExceededError) as ctx:
            run_recovery.plan_retry(self.engine, "S-01", "transient", limit=zero)
        self.assertEqual(ctx.exception.limit, zero)
        # No retry was recorded: the FIRST retry was refused, not merely a later one.
        self.assertEqual(run_recovery.count_retries(self.engine, "S-01"), 0)

    def test_the_default_budget_is_itself_in_range(self) -> None:
        """The shipped default must satisfy the bound it ships beside.

        Derived from the constant rather than hard-coding 2, matching the existing tests in this
        module, so aligning the default cannot silently invalidate this assertion.
        """
        self.assertEqual(
            run_recovery.validate_retry_budget(run_recovery.DEFAULT_RETRY_LIMIT),
            run_recovery.DEFAULT_RETRY_LIMIT,
        )


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


#: The check vocabulary shared by the two CLI-surface tables below. A row's expectations are a
#: tuple of these, so one loop can express "exits 4 AND names EV-FAILED-EXIT" and "exits 7 AND the
#: JSON says not_a_ledger AND denies corruption" without either table weakening to a single claim.
#:
#:   ("text-in", needle)         a substring a user or an agent greps for MUST be present
#:   ("text-not-in", needle)     a substring that MUST NOT be present (a wrong VERDICT, e.g. the
#:                               word "corrupt" on a file that is merely the wrong format)
#:   ("itext-in" / "itext-not-in", needle)
#:                               the same two, CASE-INSENSITIVELY, for prose whose capitalization
#:                               is not itself a contract
#:   ("json-eq", key, value)     machine output parses and that key equals that value EXACTLY
#:   ("json-in", key, member)    machine output parses and that key's collection contains it
#:
#: Case folding is deliberately confined to the TEXT modes: JSON keys and values are consumed by
#: machines, so they are always compared exactly.
_CHECK_MODES = (
    "text-in",
    "text-not-in",
    "itext-in",
    "itext-not-in",
    "json-eq",
    "json-in",
)


def _parse_machine(out: str) -> Any:
    """Parse machine output, tolerating both the pretty `--json` block and one-line `--agent`.

    `--agent` emits a single compact line (sometimes preceded by human prose), while `--json`
    pretty-prints a multi-line object, so neither "parse the whole thing" nor "parse the last line"
    works alone.
    """
    text = out.strip()
    try:
        return json.loads(text)
    except ValueError:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise
        return json.loads(lines[-1])


def _stdout_problems(out: str, checks: "tuple[tuple[Any, ...], ...]") -> List[str]:
    """Return one human-readable problem string per failed check (never raises, never short-circuits).

    Accumulating rather than asserting is what lets a row report BOTH a wrong exit code and a wrong
    payload in the same run, which is the difference between "the verdict moved" and "the wording
    moved".
    """
    problems: List[str] = []
    parsed: Any = None
    parse_error: Any = None
    if any(mode.startswith("json") for mode, *_ in checks):
        try:
            parsed = _parse_machine(out)
        except ValueError as exc:
            parse_error = exc
    for check in checks:
        mode = check[0]
        assert mode in _CHECK_MODES, f"unknown check mode {mode!r}"
        if mode in ("text-in", "itext-in"):
            haystack = out.lower() if mode == "itext-in" else out
            if check[1] not in haystack:
                problems.append(f"stdout is missing {check[1]!r}; got {out[:300]!r}")
        elif mode in ("text-not-in", "itext-not-in"):
            haystack = out.lower() if mode == "itext-not-in" else out
            if check[1] in haystack:
                problems.append(
                    f"stdout must NOT contain {check[1]!r} (that is the WRONG VERDICT for this "
                    f"input); got {out[:300]!r}"
                )
        elif parse_error is not None:
            problems.append(
                f"machine output did not parse as JSON ({parse_error}); got {out[:300]!r}"
            )
        elif not isinstance(parsed, dict):
            problems.append(f"machine output is not a JSON object; got {parsed!r}")
        elif check[1] not in parsed:
            problems.append(
                f"machine output has no key {check[1]!r}; keys are {sorted(parsed)}"
            )
        elif mode == "json-eq":
            if parsed[check[1]] != check[2]:
                problems.append(
                    f"machine key {check[1]!r} expected {check[2]!r}, got {parsed[check[1]]!r}"
                )
        elif check[2] not in parsed[check[1]]:
            problems.append(
                f"machine key {check[1]!r} does not contain {check[2]!r}; it is "
                f"{parsed[check[1]]!r}"
            )
    return problems


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
    """Every `aw run`/`aw runs` invocation exits in its own class and says why (E-03).

    ONE table replaces seventeen tests of identical shape: seed a ledger, run one argv, assert the
    exit code and (sometimes) one substring or JSON key. Only the SEED, the ARGV and the EXPECTED
    VERDICT differed.

    Why the table beats the seventeen. THE EXIT CODES ARE A CLOSED SET THAT MACHINES CONSUME
    (`run_cli.EXIT_*`: 0 ok, 1 incomplete, 2 invalid invocation, 3 blocked, 4 invalid evidence, 5
    corrupted ledger, 6 operational, 7 not a ledger), and the realistic failure is not one command
    breaking in isolation but a renumbering, or a shared helper (`_build_engine`, the runnability
    check, the terminal-refusal gate) changing the class it maps a condition onto. Seventeen tests
    report that as seventeen unrelated red lines with no way to see that they all moved the SAME
    direction; the table reports one failure listing every invocation whose class moved, which is
    the shape of the real problem.

    MODES ARE COLUMNS, NOT SEPARATE TABLES. `--json` (pretty multi-line), `--agent` (one compact
    line) and plain human output are all in the `argv` column, and the `checks` column carries a
    check MODE per expectation so a row can make two DIFFERENT KINDS of claim about one invocation
    (exit 4 AND `EV-FAILED-EXIT` present; exit 7 AND `not_a_ledger` true AND the word "corrupt"
    absent) rather than being weakened to whichever single claim fits a uniform table.

    POSITIVE ROWS ARE IN THE SAME TABLE deliberately, and their failure message says so: every
    nonzero row is VACUOUS against a CLI that refuses everything, so `next` exiting 0 with S-01
    runnable, `record performed` exiting 0, `cancel` exiting 0 and `finalize` on a complete run
    exiting 0 are the rows that keep the refusal rows meaningful.

    HUMAN PROSE IS PINNED ONLY AS THE ONE IDENTIFYING PHRASE a user greps for (`Run:`,
    `incomplete`, `EV-FAILED-EXIT`). Whole sentences of error text are NOT asserted: they are not
    load-bearing, and pinning them would make a reworded message a test failure.
    """

    #: (case, seed, argv template, expected exit code, checks, why this row exists)
    #:
    #: `seed` is one of "none" (no ledger file at all), "incomplete", "complete", "root-performed",
    #: "bad-evidence", "corrupt". In the argv template `LEDGER` is replaced by the ledger path and
    #: `WORKFLOW` by the workflow JSON path, so a row stays readable as an invocation.
    INVOCATIONS = (
        # ---- exit 2: invalid invocation. An OPERATOR error, distinct from a run-state refusal. ----
        (
            "status on a ledger path that does not exist",
            "none",
            ("runs", "status", "LEDGER"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "a missing file is the operator's mistake, so it is exit 2 and NOT exit 5 "
            "(corrupted) or 7 (wrong format): nothing was read, so nothing can be judged",
        ),
        (
            "start with no --step",
            "incomplete",
            ("run", "start", "LEDGER"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "a required flag is missing, which is an invocation error and must not be reported as "
            "the run being blocked",
        ),
        (
            "record with a --state outside the enum",
            "incomplete",
            ("run", "record", "LEDGER", "--step", "S-01", "--state", "bogus"),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "an unparseable state is rejected at the boundary; accepting it would append a "
            "meaningless attempt to an append-only ledger that can never be deleted",
        ),
        (
            "record naming a step the workflow does not define",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-99",
                "--state",
                "performed",
            ),
            run_cli.EXIT_INVALID_INVOCATION,
            (),
            "an UNKNOWN step is exit 2 while a known-but-not-runnable step is exit 3 (the row "
            "below). Collapsing the two would hide a typo'd step id as a dependency problem",
        ),
        # ---- exit 1: incomplete. The run was read fine; its predicates are unsatisfied. ----------
        (
            "status on an incomplete run (human output)",
            "incomplete",
            ("runs", "status", "LEDGER"),
            run_cli.EXIT_INCOMPLETE,
            (("text-in", "Run:"),),
            "`Run:` is the ONE identifying phrase a human greps for in the status block; the rest "
            "of the prose is deliberately not pinned",
        ),
        (
            "status --agent on an incomplete run",
            "incomplete",
            ("runs", "status", "LEDGER", "--agent"),
            run_cli.EXIT_INCOMPLETE,
            (("json-eq", "run_id", RUN_ID),),
            "MODE COLUMN: the machine mode must carry the same verdict as the human mode and "
            "surface the run id as a KEY, since an agent keys off the field rather than the prose",
        ),
        (
            "finalize refuses an incomplete run",
            "incomplete",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_INCOMPLETE,
            (("text-in", "incomplete"),),
            "TERMINAL REFUSAL: finalizing is the act that declares a run done, so an unsatisfied "
            "predicate must refuse rather than exit 0, and must NAME incompleteness as the reason",
        ),
        # ---- exit 3: blocked. Legal invocation, correct ledger, the run cannot proceed. ----------
        (
            "next when the only root step is already performed and S-02 is gated",
            "root-performed",
            ("runs", "next", "LEDGER", "--workflow", "WORKFLOW", "--agent"),
            run_cli.EXIT_BLOCKED,
            (("json-eq", "runnable_steps", []),),
            "nothing runnable is BLOCKED (3), not OK (0) with an empty list: an unattended driver "
            "polling `next` must be able to tell 'wait for a human' from 'there is work'",
        ),
        (
            "record a failed outcome",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-01",
                "--state",
                "failed",
            ),
            run_cli.EXIT_BLOCKED,
            (),
            "RECORDING A FAILURE SUCCEEDS AS AN APPEND BUT IS NOT SUCCESS: the command exits 3, so "
            "a script cannot read 'the step failed and I wrote that down' as a green step",
        ),
        (
            "record a step whose dependencies and gate are unmet",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-02",
                "--state",
                "performed",
            ),
            run_cli.EXIT_BLOCKED,
            (),
            "S-02 depends on an unperformed S-01 and needs deploy_gate, so claiming it performed is "
            "refused: the ledger must never record work the DAG says could not have happened",
        ),
        # ---- exit 6: operational. Authorization, not invocation shape and not run state. ---------
        (
            "cancel authored by the executor",
            "incomplete",
            ("run", "cancel", "LEDGER", "--actor", "executor"),
            run_cli.EXIT_OPERATIONAL,
            (),
            "only a coordinator or a human may cancel; an UNAUTHORIZED actor is its own class (6) "
            "so it is not confused with a malformed command (2) or a blocked run (3)",
        ),
        (
            "finalize authored by the executor",
            "complete",
            ("run", "finalize", "LEDGER", "--actor", "executor"),
            run_cli.EXIT_OPERATIONAL,
            (),
            "the executor cannot author its own completion. Note the seed is COMPLETE, so this row "
            "proves authority is checked even when every predicate would otherwise pass",
        ),
        # ---- exit 4 and 5: the two ways captured evidence can refuse a finalize. -----------------
        (
            "finalize with a tool_event that exited nonzero",
            "bad-evidence",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_INVALID_EVIDENCE,
            (("text-in", "EV-FAILED-EXIT"),),
            "a failing command inside a 'complete' run is INVALID EVIDENCE (4), separate from "
            "corruption (5). The finding code is asserted because it is what tells an agent WHICH "
            "evidence rule fired",
        ),
        (
            "finalize on a ledger whose hash chain was broken by hand",
            "corrupt",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_CORRUPTED_LEDGER,
            (),
            "TAMPERING IS ITS OWN CLASS (5): it must never be excused as merely incomplete (1) or "
            "invalid evidence (4), because the file itself can no longer be trusted",
        ),
        # ---- exit 0: the positive rows. Without these every row above is vacuous. ----------------
        (
            "next on a fresh run lists the runnable root step",
            "incomplete",
            ("runs", "next", "LEDGER", "--workflow", "WORKFLOW", "--json"),
            run_cli.EXIT_OK,
            (("json-in", "runnable_steps", "S-01"),),
            "POSITIVE: work available is exit 0 and NAMES the step. A CLI that returned 3 for "
            "everything would satisfy every blocked row above while being useless",
        ),
        (
            "record a performed outcome for a runnable root step",
            "incomplete",
            (
                "run",
                "record",
                "LEDGER",
                "--workflow",
                "WORKFLOW",
                "--step",
                "S-01",
                "--state",
                "performed",
            ),
            run_cli.EXIT_OK,
            (),
            "POSITIVE: the legal append succeeds, which is what makes the three refusal rows above "
            "evidence of a check rather than of a broken command. Durability is asserted "
            "separately by `test_a_recorded_attempt_is_durable_in_the_ledger`",
        ),
        (
            "resume a non-terminal run",
            "incomplete",
            ("runs", "resume", "LEDGER", "--json"),
            run_cli.EXIT_OK,
            (("json-eq", "terminal", False),),
            "POSITIVE: a healthy resume exits 0 and reports the run as NOT terminal, so a driver "
            "knows it may continue rather than that the run is over",
        ),
        (
            "cancel with a reason",
            "incomplete",
            ("run", "cancel", "LEDGER", "--reason", "abort", "--json"),
            run_cli.EXIT_OK,
            (
                ("json-eq", "cancelled", True),
                ("json-eq", "run_state", run_state.STATE_CANCELLED),
            ),
            "POSITIVE, and TWO KINDS OF CLAIM about one invocation: the command reports it acted "
            "(`cancelled`) AND that the reconstructed run state is terminal-cancelled, which is "
            "the durable effect rather than the report of it",
        ),
        (
            "finalize a complete run",
            "complete",
            ("run", "finalize", "LEDGER", "--json"),
            run_cli.EXIT_OK,
            (("json-eq", "finalized", True),),
            "POSITIVE, and the most important one here: four rows above assert finalize REFUSES. "
            "Without this row a finalize that refused unconditionally would pass all of them",
        ),
    )

    def test_every_invocation_exits_in_its_class_and_says_why(self) -> None:
        wrong = []
        by_code: Dict[int, int] = {}
        for case, seed, template, expected_rc, checks, why in self.INVOCATIONS:
            with tempfile.TemporaryDirectory() as seed_dir:
                argv = self._materialize(template, Path(seed_dir), seed)
                rc, out = self._cli(*argv)
            problems = []
            if rc != expected_rc:
                by_code[expected_rc] = by_code.get(expected_rc, 0) + 1
                problems.append(
                    f"exit code expected {expected_rc} "
                    f"({self._exit_name(expected_rc)}), got {rc} ({self._exit_name(rc)})"
                )
            problems.extend(_stdout_problems(out, checks))
            if "\x1b" in out:
                problems.append(
                    "ANSI escape leaked into the output of a machine-consumed command"
                )
            if problems:
                printable = " ".join(
                    arg if "/" not in arg else f"<{Path(arg).name}>" for arg in argv
                )
                wrong.append(
                    f"  {case}\n    argv: aw {printable}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        code_summary = ", ".join(
            f"{self._exit_name(code)} ({count} row(s))"
            for code, count in sorted(by_code.items())
        )
        self.assertEqual(
            wrong,
            [],
            f"the run CLI gave the wrong verdict for {len(wrong)} of {len(self.INVOCATIONS)} "
            f"invocations. Wrong exit codes were expected in: {code_summary or 'none'}. THE EXIT "
            "CODES ARE CONSUMED BY MACHINES, so read the grouping before editing a row. Several "
            "rows expecting the SAME code failing together means that code was renumbered or its "
            "meaning moved; several DIFFERENT codes failing on commands that share a helper "
            "(`_build_engine`, the runnability check, the terminal-refusal gate) means the helper "
            "changed which class it maps a condition onto. FIX: if a row expecting EXIT_OK is "
            "failing, fix that FIRST, because every refusal row is vacuous against a CLI that "
            "refuses everything, and a refusal row passing beside a broken positive row proves "
            "nothing. A substring failure alone (right code, missing phrase) is the milder case: "
            "the verdict is intact and only the one identifying phrase a user or an agent greps "
            f"for moved.\n" + "\n".join(wrong),
        )

    @staticmethod
    def _exit_name(code: int) -> str:
        """Name an exit code, so a failure reads `EXIT_BLOCKED` rather than a bare `3`."""
        names = {
            value: name
            for name, value in vars(run_cli).items()
            if name.startswith("EXIT_") and isinstance(value, int)
        }
        return names.get(code, f"UNNAMED({code})")

    def _materialize(
        self, template: "tuple[str, ...]", seed_dir: Path, seed: str
    ) -> "list[str]":
        """Seed a ledger of the requested shape and substitute the LEDGER/WORKFLOW placeholders."""
        self.ledger = seed_dir / "run.jsonl"
        if seed == "incomplete":
            self._seed_incomplete()
        elif seed == "complete":
            self._seed_complete()
        elif seed == "root-performed":
            self._seed_root_performed()
        elif seed == "bad-evidence":
            self._seed_invalid_evidence()
        elif seed == "corrupt":
            self._seed_complete()
            self._corrupt_chain()
        else:
            assert seed == "none", f"unknown seed {seed!r}"
        workflow = str(seed_dir / "wf.json")
        (seed_dir / "wf.json").write_text(json.dumps(_WORKFLOW), encoding="utf-8")
        return [
            str(self.ledger)
            if arg == "LEDGER"
            else (workflow if arg == "WORKFLOW" else arg)
            for arg in template
        ]

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

    def _seed_root_performed(self) -> None:
        """Seed a run whose only root step is performed, leaving S-02 gated on deploy_gate."""
        self._seed_incomplete()
        self._store().append(
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

    def _seed_invalid_evidence(self) -> None:
        """Seed an otherwise-complete run carrying a tool_event that exited nonzero."""
        self._seed_root_performed()
        store = self._store()
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

    def _corrupt_chain(self) -> None:
        """Break the hash chain by hand-appending a line with a wrong prev_hash."""
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

    def _cli(self, *argv: str) -> "tuple[int, str]":
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    def test_a_recorded_attempt_is_durable_in_the_ledger(self) -> None:
        """Kept separate: asserts a DURABLE EFFECT read back through a fresh engine, not an exit code.

        The table's `record performed` row proves the command exits 0. This proves the append
        actually happened, by reconstructing the step's state from the ledger with an engine that
        shares no memory with the CLI process. That is a different claim over a different object,
        and a table row cannot make it without carrying an unused engine for every other row.
        """
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
            "performed",
        )
        self.assertEqual(rc, run_cli.EXIT_OK)
        eng = run_engine.RunEngine(_WORKFLOW, self._store(), run_id=RUN_ID)
        self.assertEqual(
            eng.step_state("S-01"),
            "performed",
            "the CLI exited 0 but a fresh engine over the same ledger does not see the attempt, so "
            "the append was not durable",
        )

    def test_resume_cli_reports_unknown_outcome_condition(self) -> None:
        """The resume CLI surfaces the UNKNOWN_OUTCOME sentinel when a side effect is interrupted."""
        self._seed_incomplete()

        # Force the interrupted-side-effect branch: patch detection + resume to raise as if a step
        # were left running mid-flight (running state is ephemeral and not persisted across procs).
        def _fake_detect(_engine: Any) -> "tuple[str, ...]":
            return ("S-01",)

        def _fake_resume(_engine: Any) -> Any:
            raise run_recovery.UnknownOutcomeError("S-01")

        with (
            patch.object(run_recovery, "detect_unknown_outcomes", _fake_detect),
            patch.object(run_recovery, "resume", _fake_resume),
        ):
            rc, out = self._cli(
                "runs",
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

    # ---- machine output is ANSI-free across all mutating subcommands ------------------------------

    def test_all_machine_modes_ansi_free(self) -> None:
        self._seed_complete()
        # `status`, `next` and `resume` are READ verbs, so they live under `aw runs` after the
        # runnamecollapse 0soncw split (`next`/`resume` only reconstruct state and report).
        for sub in ("status", "next", "resume"):
            _, out = self._cli("runs", sub, str(self.ledger), "--agent")
            self.assertNotIn("\x1b", out, f"ANSI leaked in `runs {sub} --agent`")
            _, out2 = self._cli("runs", sub, str(self.ledger), "--json")
            self.assertNotIn("\x1b", out2, f"ANSI leaked in `runs {sub} --json`")


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

    #: (case, the target to resolve, what to seed first, expected resolution, why this row exists)
    #:
    #: `expect` is a CHECK-MODE column rather than one value, because the three old tests made
    #: DIFFERENT KINDS of claim about the resolver: one that it returns NOTHING, two that it returns
    #: a SPECIFIC path. Collapsing those into one comparison would have meant weakening the
    #: must-not-resolve row to something like "not the event log", which a resolver returning any
    #: other wrong path would satisfy.
    #:   ("none",)             resolution must be None
    #:   ("path", attribute)   resolution must equal that seeded path, RESOLVED
    RESOLUTIONS = (
        (
            "a bare run id when the directory holds only the driver's event log",
            "run-id",
            "nothing",
            ("none",),
            "e6b9kt, THE ORIGINAL BUG: a bare run id resolved to `events.jsonl`, a file the ledger "
            "does not own, and the caller then reported eight findings of corruption about a "
            "perfectly healthy log. Resolving to NOTHING is the correct answer, because there is "
            "no ledger here",
        ),
        (
            "a bare run id when a real ledger exists beside the event log",
            "run-id",
            "ledger",
            ("path", "ledger"),
            "POSITIVE, and what keeps the row above honest: a resolver that returned None "
            "unconditionally would satisfy it while making `aw runs show <id>` useless. The event "
            "log is STILL PRESENT in this row, so the resolver must pick the ledger over it rather "
            "than merely finding the only file in the directory",
        ),
        (
            "an explicit path to a file that is not a ledger at all",
            "explicit",
            "odd-file",
            ("path", "odd"),
            "an operator naming a file VERBATIM keeps working; the resolver's job is to find a "
            "path, not to judge it. The shape check downstream is what returns the wrong-format "
            "verdict, which is why this row expects the odd file back rather than None",
        ),
    )

    def test_every_target_resolves_to_the_path_it_should(self) -> None:
        """One table over ledger-path resolution, replacing three tests.

        Each of the three seeded a run directory, called `resolve_ledger_path` once, and asserted
        one thing about the result. The table beats the three because resolution is ONE lookup with
        a precedence order (an explicit path wins; otherwise a run id finds `ledger.jsonl` and
        nothing else), and the bug it exists to prevent (e6b9kt) was that order picking up a file it
        does not own. Seeing all three answers together is what shows whether the precedence moved
        or a single case broke.
        """
        wrong = []
        for case, target_kind, seed, expect, why in self.RESOLUTIONS:
            paths = {}
            if seed == "ledger":
                ledger = self.run_dir / ledger_store.LEDGER_FILENAME
                ledger_store.RunLedgerStore(ledger).append(_run_record())
                paths["ledger"] = ledger
            elif seed == "odd-file":
                odd = self.tmp / "somewhere-else.jsonl"
                odd.write_text("{}\n", encoding="utf-8")
                paths["odd"] = odd
            target = (
                self.run_id
                if target_kind == "run-id"
                else str(paths[next(iter(paths))])
            )
            resolved = run_cli.resolve_ledger_path(target, self.tmp)
            if expect[0] == "none":
                if resolved is not None:
                    wrong.append(
                        f"  {case}: expected NO resolution, got {str(resolved)!r}\n"
                        f"    this row exists because: {why}"
                    )
            else:
                expected = paths[expect[1]].resolve()
                if resolved != expected:
                    wrong.append(
                        f"  {case}:\n    expected {str(expected)!r}\n"
                        f"    got      {str(resolved)!r}\n"
                        f"    this row exists because: {why}"
                    )
            # Each row gets a clean directory so a seeded ledger cannot leak into the next row.
            for made in paths.values():
                made.unlink()
        self.assertEqual(
            wrong,
            [],
            f"run_cli.resolve_ledger_path resolved {len(wrong)} of {len(self.RESOLUTIONS)} targets "
            "wrongly. One lookup with one precedence order produces all three answers, so several "
            "rows failing together means that order changed rather than three independent bugs. "
            "FIX: if the FIRST row now resolves to something, check WHAT it resolved to. Resolving "
            "to `events.jsonl` is e6b9kt returning, and the caller will then report a healthy "
            "driver log as a corrupted ledger, which is the exact user-visible symptom this whole "
            "class was written for. If the POSITIVE row is the one failing, `aw runs show <run-id>` "
            f"can no longer find a real ledger at all.\n" + "\n".join(wrong),
        )

    # ---- the verdict --------------------------------------------------------------------------

    #: (case, target, extra argv, expected exit code, checks, why this row exists)
    #:
    #: `target` is the ledger argument: "event-log" (a healthy driver log), "run-id" (a bare id
    #: resolving to nothing), "tampered" (a real ledger with a broken hash chain) or "healthy" (a
    #: real, complete ledger). The SUBCOMMAND and the OUTPUT MODE are columns of `verb`/`extra`, not
    #: reasons for separate tables: the whole claim is that one shape check produces one verdict
    #: everywhere, so rows must sit side by side to express it.
    VERDICTS = (
        # ---- the wrong-format verdict, across the four verbs that read a ledger ----------------
        (
            "show on the driver's event log",
            "show",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (
                ("itext-in", "not a run ledger"),
                ("itext-not-in", "corrupt"),
            ),
            "e6b9kt: a healthy `events.jsonl` is the WRONG FORMAT (7), not corruption (5). It must "
            "say `not a run ledger` and must NOT use the word corrupt at all, because telling a "
            "user their log is corrupted sends them hunting for tampering that never happened",
        ),
        (
            "verify-ledger on the driver's event log",
            "verify-ledger",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the verb whose ENTIRE JOB is judging integrity is the one most likely to call a "
            "wrong-format file corrupt, so it needs its own row",
        ),
        (
            "evidence on the driver's event log",
            "evidence",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the evidence reader shares the shape check rather than carrying its own copy",
        ),
        (
            "status on the driver's event log",
            "status",
            "event-log",
            (),
            run_cli.EXIT_NOT_A_LEDGER,
            (("itext-not-in", "corrupt"),),
            "the MUTATING family reaches the same verdict through `_build_engine`, which is a "
            "different code path from the read verbs above; without this row the check could be "
            "installed on only half the CLI",
        ),
        (
            "show --agent on the driver's event log",
            "show",
            "event-log",
            ("--agent",),
            run_cli.EXIT_NOT_A_LEDGER,
            (
                ("json-eq", "not_a_ledger", True),
                ("json-eq", "corrupted", False),
                ("json-eq", "exit_code", run_cli.EXIT_NOT_A_LEDGER),
            ),
            "MODE COLUMN, and the load-bearing half: an agent reads the KEYS, so the payload must "
            "both assert the wrong format AND explicitly DENY corruption. `corrupted: false` is a "
            "positive claim, not an omission, so a consumer cannot default it to true",
        ),
        (
            "show on a bare run id with no ledger anywhere",
            "show",
            "run-id",
            (),
            run_cli.EXIT_INVALID_INVOCATION,
            (("itext-not-in", "corruption"),),
            "A THIRD DISTINCT VERDICT: nothing was found, so this is an invocation error (2), not "
            "wrong-format (7) and not corruption (5). Reporting corruption for a file that was "
            "never even opened is the original e6b9kt symptom",
        ),
        # ---- ADVERSARIAL: real corruption must still be reported as corruption -----------------
        (
            "show on a ledger whose hash chain was tampered with",
            "show",
            "tampered",
            (),
            run_cli.EXIT_INVALID_INVOCATION,
            (("itext-in", "corruption"),),
            "THE ADVERSARIAL ROW: the wrong-format path must not become a blanket excuse. A "
            "tampered ledger must still be NAMED as corruption, or the fix for a cosmetic "
            "misdiagnosis would have silenced the one verdict that matters. MEASURED, NOT ASSUMED: "
            "`runs show` reports corruption with exit 2 (`run_cli.py:295-308` hard-codes it) while "
            "`run finalize` uses EXIT_CORRUPTED_LEDGER (5) for the same condition. That asymmetry "
            "is pinned here rather than wished away; if it is ever unified, THIS row is the one to "
            "update, and the prose claim below it is what must not weaken",
        ),
        (
            "show --agent on a tampered ledger",
            "show",
            "tampered",
            ("--agent",),
            run_cli.EXIT_INVALID_INVOCATION,
            (
                ("json-eq", "corrupted", True),
                ("json-eq", "ok", False),
            ),
            "THE MACHINE HALF OF THE ADVERSARIAL ROW, and the load-bearing one given the exit-code "
            "asymmetry noted above: whatever the code, the payload must say `corrupted: true`. This "
            "is the exact mirror of the event-log row's `corrupted: false`, so the two rows "
            "together prove the flag is a real signal rather than a constant in either direction",
        ),
        # ---- POSITIVE: a real, healthy ledger must pass all the same verbs ----------------------
        (
            "show on a real, complete ledger",
            "show",
            "healthy",
            (),
            run_cli.EXIT_OK,
            (("text-in", "Run:"),),
            "POSITIVE: every row above is vacuous against a CLI that refuses every file. This is "
            "the row that proves the shape check ACCEPTS a genuine ledger rather than rejecting "
            "everything and coincidentally satisfying the negative rows",
        ),
        (
            "verify-ledger --agent on a real, healthy ledger",
            "verify-ledger",
            "healthy",
            ("--agent",),
            run_cli.EXIT_OK,
            (
                ("json-eq", "chain_clean", True),
                ("json-eq", "ok", True),
            ),
            "POSITIVE in the machine mode: a clean chain is reported as clean. Paired with the "
            "tampered row, this is what makes `chain_clean` a real signal rather than a constant",
        ),
    )

    def test_every_verb_reaches_the_same_verdict_for_each_file_shape(self) -> None:
        """One table over the wrong-format verdict, replacing six tests and folding in two positives.

        Each of the six ran one subcommand against `events.jsonl` and asserted an exit code plus the
        absence of the word "corrupt". The SUBCOMMAND and the OUTPUT MODE were the only differences,
        so they are columns here.

        Why the table beats the six. The claim is not about any one verb: it is that ONE shape check
        produces ONE verdict across every verb that reads a ledger, including the mutating family
        that reaches it by a different path (`_build_engine`). Six tests can only assert that
        separately; the table asserts it as the pattern it is, and a failure that hits every verb at
        once reads as "the check moved" rather than as six coincidences.

        THREE DISTINCT VERDICTS ARE IN THE SAME TABLE ON PURPOSE (wrong format 7; a target that
        resolves to no file 2; real corruption, which `show` also reports as 2 but with
        `corrupted: true` and the word corruption in its prose) because the bug being guarded is
        precisely a CONFLATION of them. Asserting them apart is what lets the fix for the cosmetic
        misdiagnosis be checked against the adversarial rows that must keep firing.

        THE POSITIVE ROWS ARE NOT DECORATION: a shape check that rejected every file would satisfy
        all six original tests. Their failure message says so.
        """
        wrong = []
        for case, verb, target, extra, expected_rc, checks, why in self.VERDICTS:
            argv = ["runs", verb, *self._target_argv(target), *extra]
            rc, out = self._cli(*argv)
            problems = []
            if rc != expected_rc:
                problems.append(
                    f"exit code expected {expected_rc} "
                    f"({TestRunCliSubcommands._exit_name(expected_rc)}), got {rc} "
                    f"({TestRunCliSubcommands._exit_name(rc)})"
                )
            problems.extend(_stdout_problems(out, checks))
            if "\x1b[" in out:
                problems.append("ANSI escape leaked into machine-consumed output")
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the ledger-shape verdict is wrong for {len(wrong)} of {len(self.VERDICTS)} "
            "invocations. One shape check serves every verb here, so read the grouping. EVERY "
            "event-log row failing together means the check itself changed; ONE verb failing while "
            "its siblings pass means that verb stopped routing through the shared check (most "
            "likely `status`, which reaches it through `_build_engine` rather than directly). FIX: "
            "if the TAMPERED row is failing, stop and fix that first, whatever else is red: the "
            "wrong-format path has become a blanket excuse and real tamper evidence is now being "
            "swallowed at the CLI boundary, which is strictly worse than the cosmetic misdiagnosis "
            "this class was written to fix. If a POSITIVE row is failing, the check now rejects "
            "genuine ledgers and every negative row above is passing vacuously. A row that has the "
            "right exit code but leaks the word `corrupt` is the mild case: the machine verdict is "
            f"correct and only the human prose is misleading.\n" + "\n".join(wrong),
        )

    def _target_argv(self, target: str) -> "list[str]":
        """Build the ledger argument (and `--dir` where needed) for one `VERDICTS` target."""
        if target == "event-log":
            return [str(self.run_dir / "events.jsonl")]
        if target == "run-id":
            return [self.run_id, "--dir", str(self.tmp)]
        ledger = self.run_dir / f"{target}-ledger.jsonl"
        store = ledger_store.RunLedgerStore(ledger)
        if target == "tampered":
            store.append(_run_record())
            store.append(_requirement_set(["R-01"]))
            lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
            tampered = json.loads(lines[1])
            tampered["prev_hash"] = "f" * 64
            lines[1] = json.dumps(tampered, sort_keys=True) + "\n"
            ledger.write_text("".join(lines), encoding="utf-8")
        else:
            assert target == "healthy", f"unknown target {target!r}"
            for rec in _complete_run_records():
                store.append(rec)
        return [str(ledger)]


if __name__ == "__main__":
    unittest.main()
