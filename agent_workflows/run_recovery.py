"""Bounded retry/correction and resume/cancel/crash-recovery over the append-only run ledger.

awoptimize Order 07 (`7yqm1v`) E-01 (bounded retry + correction keyed by failure class) and
E-02 (resume / cancel / crash recovery).

This module never DEFINES the state machine (Order 05 owns `run_state`/`run_engine`), the completion
predicate (Order 04 owns `run_evidence`), the persistence substrate (Order 03 owns
`run_ledger_store`), or the packet renderers (Order 06). It composes those existing APIs into two
deterministic recovery behaviours:

  * E-01 bounded retry / correction. Every failed attempt is PRESERVED in the append-only ledger
    (never deleted or rewritten). A retry is keyed by a `failure_class` and carries an
    `idempotency_key`; recording the SAME idempotency key twice does NOT append a second retry (an
    idempotent action already recorded is not duplicated). The retry BUDGET is read back from the
    ledger, so a retry cannot convert failure into success by mere repetition: once the configured
    limit is exhausted the planner ESCALATES (raises `RetryLimitExceededError`) instead of looping.
    Because a retry follows a repository/plan change, prior evidence bound to the retried step is
    marked INVALIDATED so a stale green result cannot be reused.

  * E-02 resume / cancel / crash recovery. State is reconstructed PURELY from the ledger via
    `RunEngine.reconstruct_state()`. A side effect interrupted mid-flight (a step left in `running`
    with no terminal `step_attempt`) is an explicit `unknown_outcome`: `resume()` refuses to silently
    rerun it and REQUIRES explicit reconciliation (`reconcile_unknown_outcome`). `cancel()` records a
    terminal cancellation through the engine.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

from agent_workflows import run_engine, run_state
from agent_workflows import run_ledger_schema as schema

# ---- configuration --------------------------------------------------------------------------------

DEFAULT_RETRY_LIMIT: int = 3

# The unknown-outcome sentinel: a side effect was interrupted mid-flight and its result is unknown.
# This is NOT a run_state value; it is a recovery-layer classification requiring reconciliation.
UNKNOWN_OUTCOME: str = "unknown_outcome"


# ---- typed errors (fail closed) -------------------------------------------------------------------


class RecoveryError(Exception):
    """Base class for all recovery-layer errors (fail closed)."""


class RetryLimitExceededError(RecoveryError):
    """Raised when a step's retry budget is exhausted; escalate instead of looping."""

    def __init__(self, step_id: str, attempts: int, limit: int) -> None:
        self.step_id = step_id
        self.attempts = attempts
        self.limit = limit
        super().__init__(
            f"retry budget exhausted for step {step_id!r}: {attempts} retries recorded "
            f"meets/exceeds limit {limit}; escalate rather than loop"
        )


class UnknownOutcomeError(RecoveryError):
    """Raised when a resume encounters an interrupted side effect that must be reconciled first."""

    def __init__(self, step_id: str) -> None:
        self.step_id = step_id
        super().__init__(
            f"step {step_id!r} was interrupted mid-flight (running with no recorded terminal "
            f"attempt): outcome is unknown and requires explicit reconciliation, not a silent rerun"
        )


class NoRetryableStateError(RecoveryError):
    """Raised when a retry is planned for a step that is not in a retryable (failed/blocked) state."""


# ---- result structures ----------------------------------------------------------------------------


class RetryPlan(NamedTuple):
    step_id: str
    failure_class: str
    idempotency_key: str
    attempt_number: int
    limit: int
    duplicate: bool  # True if this idempotency_key was already recorded (no-op append)
    invalidated_evidence: Tuple[int, ...]  # ledger seqs of evidence marked invalidated


class ResumeReport(NamedTuple):
    run_id: str
    run_state: str
    resumable_steps: Tuple[str, ...]  # runnable steps that may proceed
    unknown_outcome_steps: Tuple[
        str, ...
    ]  # interrupted side effects awaiting reconciliation
    terminal: bool


class CrashReport(NamedTuple):
    run_id: str
    recovered_torn_line: bool
    truncated_bytes: int
    unknown_outcome_steps: Tuple[str, ...]
    run_state: str


# ---- ledger read helpers --------------------------------------------------------------------------


def _read_records(engine: run_engine.RunEngine) -> List[Dict[str, Any]]:
    """Read the full verified ledger (fails closed on corruption)."""
    return engine.store.read_records(verify=True)


def count_retries(engine: run_engine.RunEngine, step_id: str) -> int:
    """Count `retry` records already recorded for a step (the consumed retry budget)."""
    records = _read_records(engine)
    return sum(
        1
        for rec in records
        if rec.get("kind") == "retry" and rec.get("retries_step") == step_id
    )


def recorded_idempotency_keys(
    engine: run_engine.RunEngine, step_id: str
) -> Tuple[str, ...]:
    """Return the idempotency keys of retries already recorded for a step (dedup source of truth)."""
    records = _read_records(engine)
    keys: List[str] = []
    for rec in records:
        if rec.get("kind") == "retry" and rec.get("retries_step") == step_id:
            k = rec.get("idempotency_key")
            if isinstance(k, str):
                keys.append(k)
    return tuple(keys)


def failed_attempts(
    engine: run_engine.RunEngine, step_id: str
) -> Tuple[Dict[str, Any], ...]:
    """Return every failed/blocked step_attempt for a step, in ledger order (never deleted)."""
    records = _read_records(engine)
    return tuple(
        rec
        for rec in records
        if rec.get("kind") == "step_attempt"
        and rec.get("step") == step_id
        and rec.get("state") in (run_state.STATE_FAILED, run_state.STATE_BLOCKED)
    )


def _step_evidence_seqs(
    records: Sequence[Mapping[str, Any]], step_id: str
) -> Tuple[int, ...]:
    """Ledger seqs of evidence envelopes / tool events bound to a step that are not yet invalidated."""
    seqs: List[int] = []
    invalidated: set[int] = set()
    for rec in records:
        # Evidence invalidation is recorded as a `correction` carrying an `invalidates_seq`
        # extra field (the closed record-kind set has no dedicated invalidation kind).
        if rec.get("kind") == "correction" and "invalidates_seq" in rec:
            tgt = rec.get("invalidates_seq")
            if isinstance(tgt, int) and not isinstance(tgt, bool):
                invalidated.add(tgt)
    for rec in records:
        kind = rec.get("kind")
        if kind not in ("evidence_envelope", "tool_event"):
            continue
        binds = rec.get("binds", [])
        if isinstance(binds, list) and step_id in binds:
            seq = rec.get("seq")
            if (
                isinstance(seq, int)
                and not isinstance(seq, bool)
                and seq not in invalidated
            ):
                seqs.append(seq)
    return tuple(seqs)


# ---- E-01: bounded retry + correction --------------------------------------------------------------


def plan_retry(
    engine: run_engine.RunEngine,
    step_id: str,
    failure_class: str,
    *,
    idempotency_key: Optional[str] = None,
    limit: int = DEFAULT_RETRY_LIMIT,
    actor: str = "corrector",
) -> RetryPlan:
    """Plan a bounded retry of a failed/blocked step keyed by failure class.

    Guarantees:
      1. The step MUST currently be in a retryable state (`failed` or `blocked`). Otherwise raise
         `NoRetryableStateError` (fail closed; do not retry a green or in-flight step).
      2. Prior failed attempts are PRESERVED (this function never deletes; it only appends).
      3. The retry budget is read from the ledger. If the number of retries already recorded meets or
         exceeds `limit`, raise `RetryLimitExceededError` (escalate, do not loop -> a retry cannot turn
         failure into success by mere repetition).
      4. Idempotency: if `idempotency_key` was already recorded for this step, this is a no-op append
         (returns `duplicate=True`) so a replayed deterministic action is not duplicated.
      5. Evidence bound to the retried step is INVALIDATED (a change precedes a retry), so a stale
         green result cannot be reused across the retry boundary.
    """
    snapshot = engine.reconstruct_state()
    step = snapshot.steps.get(step_id)
    if step is None:
        raise KeyError(f"unknown step {step_id!r}")

    if step.state not in (run_state.STATE_FAILED, run_state.STATE_BLOCKED):
        raise NoRetryableStateError(
            f"step {step_id!r} is in state {step.state!r}; only "
            f"{run_state.STATE_FAILED!r}/{run_state.STATE_BLOCKED!r} steps are retryable"
        )

    existing_keys = recorded_idempotency_keys(engine, step_id)
    retries_used = len(existing_keys)

    key = (
        idempotency_key
        if idempotency_key is not None
        else f"{step_id}-retry-{retries_used + 1}"
    )

    # Idempotency: a deterministic action already recorded is not duplicated.
    if key in existing_keys:
        return RetryPlan(
            step_id=step_id,
            failure_class=failure_class,
            idempotency_key=key,
            attempt_number=existing_keys.index(key) + 1,
            limit=limit,
            duplicate=True,
            invalidated_evidence=(),
        )

    # Budget check: escalate rather than loop once the limit is reached.
    if retries_used >= limit:
        raise RetryLimitExceededError(step_id, retries_used, limit)

    records = _read_records(engine)
    # Invalidate any live evidence bound to the step: a change precedes the retry.
    invalidated: List[int] = []
    for seq in _step_evidence_seqs(records, step_id):
        engine.store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "correction",
                "run_id": engine.run_id,
                "actor": actor,
                "corrects_requirement": step_id,
                "description": (
                    f"evidence invalidation: seq {seq} bound to {step_id} is stale after "
                    f"retry (failure_class={failure_class})"
                ),
                "invalidates_seq": seq,
                "parent": "",
            }
        )
        invalidated.append(seq)

    # Assert the retry edge is a LEGAL, corrector-authorized transition before recording it. This
    # fails closed (raising a run_state error) if the reset is not permitted by the transition table;
    # it never mutates the engine's reconstructed step state (the failed attempt is preserved).
    run_state.check_transition(
        step.state,
        run_state.STATE_RUNNABLE,
        actor,
        predicate_values={"correction_or_retry_planned": True},
    )

    attempt_number = retries_used + 1
    engine.store.append(
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "retry",
            "run_id": engine.run_id,
            "actor": actor,
            "retries_step": step_id,
            "failure_class": str(failure_class),
            "idempotency_key": key,
            "parent": "",
        }
    )

    return RetryPlan(
        step_id=step_id,
        failure_class=str(failure_class),
        idempotency_key=key,
        attempt_number=attempt_number,
        limit=limit,
        duplicate=False,
        invalidated_evidence=tuple(invalidated),
    )


def correction_required(
    engine: run_engine.RunEngine,
    requirement_id: str,
    description: str,
    *,
    actor: str = "corrector",
) -> Dict[str, Any]:
    """Append a `correction` record for a requirement whose verifier decision demands correction.

    Preserves history (append-only). The completion predicate (Order 04) treats a logged correction
    as an unresolved blocker until a LATER passing verifier decision supersedes it, so a correction
    cannot be silently swept away.
    """
    rec = engine.store.append(
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "correction",
            "run_id": engine.run_id,
            "actor": actor,
            "corrects_requirement": str(requirement_id),
            "description": str(description),
            "parent": "",
        }
    )
    return rec


def retry_budget_remaining(
    engine: run_engine.RunEngine, step_id: str, *, limit: int = DEFAULT_RETRY_LIMIT
) -> int:
    """Return how many retries remain in the budget for a step (never negative)."""
    used = count_retries(engine, step_id)
    return max(0, limit - used)


# ---- E-02: resume / cancel / crash recovery -------------------------------------------------------


def detect_unknown_outcomes(engine: run_engine.RunEngine) -> Tuple[str, ...]:
    """Detect steps whose side effect was interrupted mid-flight.

    A step reconstructed as `running` with NO terminal `step_attempt` (performed/blocked/failed) is an
    interrupted side effect: the runtime crashed after starting it but before recording its outcome.
    The outcome is UNKNOWN and must be reconciled, never silently rerun.
    """
    snapshot = engine.reconstruct_state()
    unknown: List[str] = []
    for sid, step in sorted(snapshot.steps.items()):
        if step.state == run_state.STATE_RUNNING and step.last_attempt_state is None:
            unknown.append(sid)
    return tuple(unknown)


def resume(engine: run_engine.RunEngine) -> ResumeReport:
    """Reconstruct run state from the ledger and report what may safely proceed.

    Refuses to advance if any step is in an `unknown_outcome` condition (interrupted side effect):
    those require explicit reconciliation via `reconcile_unknown_outcome` before resuming. This is the
    fail-closed guarantee against a silent rerun of a possibly-completed side effect.
    """
    snapshot = engine.reconstruct_state()
    unknown = detect_unknown_outcomes(engine)
    if unknown:
        # Surface the first unknown outcome as the blocking condition.
        raise UnknownOutcomeError(unknown[0])

    terminal = snapshot.state in run_state.TERMINAL_STATES
    runnable = tuple(s.step_id for s in engine.get_runnable_steps())
    return ResumeReport(
        run_id=snapshot.run_id,
        run_state=snapshot.state,
        resumable_steps=runnable,
        unknown_outcome_steps=(),
        terminal=terminal,
    )


def reconcile_unknown_outcome(
    engine: run_engine.RunEngine,
    step_id: str,
    resolved_state: str,
    *,
    actor: str = "coordinator",
) -> run_engine.StepSnapshot:
    """Explicitly reconcile an interrupted side effect to a determined terminal attempt state.

    The caller MUST supply the reconciled outcome (`performed`/`blocked`/`failed`) after inspecting the
    real side effect; the recovery layer never guesses. Records the reconciled `step_attempt` so the
    interrupted step is no longer `unknown_outcome`.
    """
    if resolved_state not in schema.ATTEMPT_STATES:
        raise NoRetryableStateError(
            f"reconciled outcome must be one of {sorted(schema.ATTEMPT_STATES)}, got {resolved_state!r}"
        )
    if step_id not in detect_unknown_outcomes(engine):
        raise RecoveryError(
            f"step {step_id!r} is not in an unknown-outcome condition; nothing to reconcile"
        )
    return engine.record_step_attempt(step_id, state=resolved_state, actor=actor)


def cancel(
    engine: run_engine.RunEngine,
    *,
    reason: str = "cancelled",
    actor: str = "coordinator",
) -> run_engine.RunStateSnapshot:
    """Cancel an active run through the engine (records a terminal cancellation transaction)."""
    return engine.cancel_run(reason=reason, actor=actor)


def recover_crash(engine: run_engine.RunEngine) -> CrashReport:
    """Recover from a crash: truncate any torn trailing line, then reconstruct and classify.

    Combines the store's torn-line recovery with unknown-outcome detection so an interrupted side
    effect is surfaced rather than silently rerun.
    """
    rec_res = engine.store.recover()
    snapshot = engine.reconstruct_state()
    unknown = detect_unknown_outcomes(engine)
    return CrashReport(
        run_id=snapshot.run_id,
        recovered_torn_line=rec_res.recovered,
        truncated_bytes=rec_res.truncated_bytes,
        unknown_outcome_steps=unknown,
        run_state=snapshot.state,
    )
