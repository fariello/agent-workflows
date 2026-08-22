"""Deterministic run state machine: legal states, transition table, and transition authority.

awoptimize Order 05 (`b1v3wl`) E-01.

Defines the closed set of run/step/attempt states, the complete legal transition table, and explicit
per-edge transition AUTHORITY. Moving state and sequencing out of model memory into a deterministic,
fail-closed state machine guarantees:
  1. No illegal skips or backward transitions are permitted.
  2. An executor cannot author terminal completion (`verified -> complete`) or verification findings
     (`verifying -> verified`).
  3. Every legal edge names its authorized actor role and required predicate.
  4. Missing prerequisites cause transitions to fail closed.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import (
    NamedTuple,
)

# ---- State Vocabularies -------------------------------------------------------------------------

STATE_PENDING: str = "pending"
STATE_RUNNABLE: str = "runnable"
STATE_RUNNING: str = "running"
STATE_PERFORMED: str = "performed"
STATE_BLOCKED: str = "blocked"
STATE_FAILED: str = "failed"
STATE_VERIFYING: str = "verifying"
STATE_VERIFIED: str = "verified"
STATE_CORRECTION_REQUIRED: str = "correction_required"
STATE_CANCELLED: str = "cancelled"
STATE_COMPLETE: str = "complete"

ALL_STATES: frozenset[str] = frozenset(
    (
        STATE_PENDING,
        STATE_RUNNABLE,
        STATE_RUNNING,
        STATE_PERFORMED,
        STATE_BLOCKED,
        STATE_FAILED,
        STATE_VERIFYING,
        STATE_VERIFIED,
        STATE_CORRECTION_REQUIRED,
        STATE_CANCELLED,
        STATE_COMPLETE,
    )
)

ACTIVE_STATES: frozenset[str] = frozenset(
    (
        STATE_PENDING,
        STATE_RUNNABLE,
        STATE_RUNNING,
        STATE_PERFORMED,
        STATE_VERIFYING,
        STATE_CORRECTION_REQUIRED,
    )
)

TERMINAL_STATES: frozenset[str] = frozenset((STATE_COMPLETE, STATE_CANCELLED))

RUN_TERMINAL_STATES: frozenset[str] = frozenset((STATE_COMPLETE, STATE_CANCELLED))

# Actor ROLES (mirrors schema.ROLES)
ROLES: frozenset[str] = frozenset(
    ("coordinator", "executor", "verifier", "corrector", "human", "runtime")
)


# ---- Transition Rules and Table -----------------------------------------------------------------


class TransitionRule(NamedTuple):
    source: str
    target: str
    authorized_actors: frozenset[str]
    required_predicate: str
    description: str


TRANSITION_RULES: tuple[TransitionRule, ...] = (
    # 1. pending -> runnable (runtime, coordinator)
    TransitionRule(
        STATE_PENDING,
        STATE_RUNNABLE,
        frozenset(("runtime", "coordinator")),
        "dependencies_and_approvals_satisfied",
        "Dependencies and required gate approvals are satisfied",
    ),
    # 2. runnable -> running (runtime, coordinator)
    TransitionRule(
        STATE_RUNNABLE,
        STATE_RUNNING,
        frozenset(("runtime", "coordinator")),
        "lease_acquired_and_packet_emitted",
        "Single-writer lease acquired and step packet emitted",
    ),
    # 3. running -> performed | blocked | failed (runtime, coordinator)
    TransitionRule(
        STATE_RUNNING,
        STATE_PERFORMED,
        frozenset(("runtime", "coordinator")),
        "valid_attempt_and_evidence",
        "Valid execution attempt and evidence references recorded",
    ),
    TransitionRule(
        STATE_RUNNING,
        STATE_BLOCKED,
        frozenset(("runtime", "coordinator")),
        "valid_attempt_and_evidence",
        "Execution blocked with recorded cause",
    ),
    TransitionRule(
        STATE_RUNNING,
        STATE_FAILED,
        frozenset(("runtime", "coordinator")),
        "valid_attempt_and_evidence",
        "Execution failed with recorded error",
    ),
    # 4. performed -> verifying (coordinator, runtime)
    TransitionRule(
        STATE_PERFORMED,
        STATE_VERIFYING,
        frozenset(("coordinator", "runtime")),
        "required_execution_events_complete",
        "Execution complete and submitted for independent verification",
    ),
    # 5. verifying -> verified | correction_required (verifier, runtime)
    TransitionRule(
        STATE_VERIFYING,
        STATE_VERIFIED,
        frozenset(("verifier", "runtime")),
        "verifier_authority_and_evidence_satisfied",
        "Independent verifier decision confirms all requirement predicates satisfied",
    ),
    TransitionRule(
        STATE_VERIFYING,
        STATE_CORRECTION_REQUIRED,
        frozenset(("verifier", "runtime")),
        "verifier_authority_and_findings_recorded",
        "Independent verifier finds unsatisfied requirements or failures",
    ),
    # 6. correction / retry transitions
    TransitionRule(
        STATE_CORRECTION_REQUIRED,
        STATE_RUNNABLE,
        frozenset(("corrector", "runtime", "coordinator")),
        "correction_or_retry_planned",
        "Corrective action planned and reset to runnable",
    ),
    TransitionRule(
        STATE_CORRECTION_REQUIRED,
        STATE_PENDING,
        frozenset(("corrector", "runtime", "coordinator")),
        "correction_or_retry_planned",
        "Corrective action planned and reset to pending",
    ),
    TransitionRule(
        STATE_FAILED,
        STATE_RUNNABLE,
        frozenset(("corrector", "runtime", "coordinator")),
        "correction_or_retry_planned",
        "Retry planned within budget and reset to runnable",
    ),
    TransitionRule(
        STATE_BLOCKED,
        STATE_RUNNABLE,
        frozenset(("corrector", "runtime", "coordinator")),
        "correction_or_retry_planned",
        "Blocker resolved and reset to runnable",
    ),
    # 7. verified -> complete (coordinator, runtime only; NEVER executor)
    TransitionRule(
        STATE_VERIFIED,
        STATE_COMPLETE,
        frozenset(("coordinator", "runtime")),
        "every_frozen_completion_predicate_true",
        "Coordinator/runtime verifies all frozen completion predicates true",
    ),
    # 8. any active state -> cancelled (coordinator, human)
    TransitionRule(
        STATE_PENDING,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while pending",
    ),
    TransitionRule(
        STATE_RUNNABLE,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while runnable",
    ),
    TransitionRule(
        STATE_RUNNING,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while running",
    ),
    TransitionRule(
        STATE_PERFORMED,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while performed",
    ),
    TransitionRule(
        STATE_VERIFYING,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while verifying",
    ),
    TransitionRule(
        STATE_CORRECTION_REQUIRED,
        STATE_CANCELLED,
        frozenset(("coordinator", "human")),
        "cancellation_event_recorded",
        "Run cancelled while correction required",
    ),
)

_EDGE_MAP: dict[tuple[str, str], TransitionRule] = {
    (rule.source, rule.target): rule for rule in TRANSITION_RULES
}

_SOURCE_MAP: dict[str, list[TransitionRule]] = {}
for rule in TRANSITION_RULES:
    _SOURCE_MAP.setdefault(rule.source, []).append(rule)


def get_transition_rule(source: str, target: str) -> TransitionRule | None:
    """Retrieve the TransitionRule for an edge, or None if the edge is not defined."""
    return _EDGE_MAP.get((source, target))


def get_legal_transitions(source: str) -> tuple[TransitionRule, ...]:
    """Return all legal transition rules originating from source state."""
    return tuple(_SOURCE_MAP.get(source, []))


def is_legal_edge(source: str, target: str, actor: str | None = None) -> bool:
    """Check if an edge exists and is authorized for actor (if specified)."""
    rule = _EDGE_MAP.get((source, target))
    if rule is None:
        return False
    return not (actor is not None and actor not in rule.authorized_actors)


# ---- Findings, Results, and Exceptions -----------------------------------------------------------


class StateFinding(NamedTuple):
    code: str
    where: str
    message: str
    reason: str


class StateValidationResult(NamedTuple):
    ok: bool
    findings: tuple[StateFinding, ...]
    rule: TransitionRule | None = None


class RunStateError(Exception):
    """Base exception for all run state machine errors."""


class IllegalTransitionError(RunStateError):
    """Raised when an illegal transition is attempted (e.g. skip or backward)."""


class UnauthorizedActorError(RunStateError):
    """Raised when an actor lacks authority for a state transition."""


class PredicateUnsatisfiedError(RunStateError):
    """Raised when a required transition predicate is not satisfied."""


def validate_transition(
    source: str,
    target: str,
    actor: str,
    *,
    predicate_values: Mapping[str, bool] | None = None,
) -> StateValidationResult:
    """Purely validate whether a state transition is legal, authorized, and satisfies predicates."""
    findings: list[StateFinding] = []

    if source not in ALL_STATES:
        findings.append(
            StateFinding(
                "ST-UNKNOWN-STATE",
                "source",
                f"Unknown source state '{source}'",
                "unknown source state",
            )
        )
    if target not in ALL_STATES:
        findings.append(
            StateFinding(
                "ST-UNKNOWN-STATE",
                "target",
                f"Unknown target state '{target}'",
                "unknown target state",
            )
        )
    if findings:
        return StateValidationResult(False, tuple(findings), None)

    if source in TERMINAL_STATES and target != source:
        findings.append(
            StateFinding(
                "ST-TERMINAL-STATE",
                "source",
                f"Cannot transition out of terminal state '{source}'",
                "terminal state immutable",
            )
        )
        return StateValidationResult(False, tuple(findings), None)

    rule = get_transition_rule(source, target)
    if rule is None:
        findings.append(
            StateFinding(
                "ST-ILLEGAL-TRANSITION",
                f"{source}->{target}",
                f"Illegal transition from '{source}' to '{target}'",
                "illegal transition edge",
            )
        )
        return StateValidationResult(False, tuple(findings), None)

    if actor not in rule.authorized_actors:
        findings.append(
            StateFinding(
                "ST-UNAUTHORIZED-ACTOR",
                "actor",
                f"Actor '{actor}' not authorized for transition '{source}' -> '{target}' (authorized: {sorted(rule.authorized_actors)})",
                "unauthorized actor",
            )
        )
        return StateValidationResult(False, tuple(findings), rule)

    if predicate_values is not None:
        pred_name = rule.required_predicate
        if not predicate_values.get(pred_name, False):
            findings.append(
                StateFinding(
                    "ST-PREDICATE-UNSATISFIED",
                    "predicate",
                    f"Required predicate '{pred_name}' is not satisfied for transition '{source}' -> '{target}'",
                    "unsatisfied predicate",
                )
            )
            return StateValidationResult(False, tuple(findings), rule)

    return StateValidationResult(True, (), rule)


def check_transition(
    source: str,
    target: str,
    actor: str,
    *,
    predicate_values: Mapping[str, bool] | None = None,
) -> TransitionRule:
    """Validate transition and raise specific subclass of RunStateError if invalid."""
    res = validate_transition(source, target, actor, predicate_values=predicate_values)
    if not res.ok:
        for f in res.findings:
            if f.code in (
                "ST-UNKNOWN-STATE",
                "ST-TERMINAL-STATE",
                "ST-ILLEGAL-TRANSITION",
            ):
                raise IllegalTransitionError(f.message)
            elif f.code == "ST-UNAUTHORIZED-ACTOR":
                raise UnauthorizedActorError(f.message)
            elif f.code == "ST-PREDICATE-UNSATISFIED":
                raise PredicateUnsatisfiedError(f.message)
        raise IllegalTransitionError("State transition rejected")
    assert res.rule is not None
    return res.rule
