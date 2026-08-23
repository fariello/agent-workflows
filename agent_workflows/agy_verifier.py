"""Fresh-session agy verifier mode contract and model-free test doubles.

awoptimize Order 11 (`bmd1ur`) E-04:

Replace the same-session agy audit as the COMPLETION path with a fresh-session verifier
mode that consumes the Order-08 verifier packet. Execution and verification MUST use
DIFFERENT session identities. The same-session audit is retained ONLY as an optional
diagnostic, explicitly recorded as non-authoritative, and it CANNOT finalize a run.

This module is PURE and model-free (D138 stdlib only). It defines:
- the fresh-session verifier contract (session identity, mode, finalization authority);
- deterministic test doubles that stand in for a live ``agy`` binary/session WITHOUT
  calling any network/model/agy process.

It CONSUMES the Order-08 verifier packet (:mod:`agent_workflows.verify_roles`
``VerifierPacket``, ``validate_verifier_packet``, ``compute_verifier_packet_digest``) and
the Order-08 role contract that only an independent verifier authors verifier decisions.
"""

from __future__ import annotations

import datetime
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent_workflows import verify_roles
from agent_workflows.verify_roles import (
    ROLE_EXECUTOR,
    ROLE_VERIFIER,
    SelfVerificationForbiddenError,
    VerifierPacket,
    compute_verifier_packet_digest,
    validate_verifier_packet,
)

# ==================================================================================================
# Constants
# ==================================================================================================

# Verifier session modes.
MODE_FRESH_SESSION: str = "fresh_session"  # authoritative completion path
MODE_SAME_SESSION_AUDIT: str = "same_session_audit"  # diagnostic-only, cannot finalize

ALL_MODES = (MODE_FRESH_SESSION, MODE_SAME_SESSION_AUDIT)

# Verifier finalization outcomes.
FINAL_VERIFIED: str = "verified"
FINAL_CORRECTION_REQUIRED: str = "correction_required"
FINAL_NOT_FINALIZED: str = "not_finalized"  # a diagnostic audit cannot finalize


class AgyVerifierError(ValueError):
    """Raised on a fresh-session verifier contract violation."""


class SameSessionCannotFinalizeError(AgyVerifierError):
    """Raised when a same-session diagnostic audit attempts to finalize a run."""


class SessionIdentityCollisionError(AgyVerifierError):
    """Raised when the verifier session identity equals the execution session identity."""


# ==================================================================================================
# Session identity
# ==================================================================================================


@dataclass(frozen=True)
class SessionIdentity:
    """A deterministic, model-free stand-in for an agy conversation/process identity.

    Two sessions are the SAME iff their ``session_id`` values are equal. A fresh-session
    verifier MUST carry a session_id different from the execution session's.
    """

    session_id: str
    role: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "role": self.role, "label": self.label}


def new_session_identity(role: str, seed: str, label: str = "") -> SessionIdentity:
    """Derive a deterministic session identity from a role + seed (no live agy call)."""
    digest = hashlib.sha256(f"{role}\x00{seed}".encode("utf-8")).hexdigest()[:16]
    return SessionIdentity(session_id=f"agy-{role}-{digest}", role=role, label=label)


# ==================================================================================================
# Verifier mode contract
# ==================================================================================================


@dataclass
class FreshVerifierResult:
    """Outcome of a verifier run under a declared mode."""

    mode: str
    execution_session: SessionIdentity
    verifier_session: SessionIdentity
    packet_digest: str
    is_authoritative: bool
    can_finalize: bool
    finalization: str
    reasons: List[str] = field(default_factory=list)
    diagnostic_only: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "execution_session": self.execution_session.to_dict(),
            "verifier_session": self.verifier_session.to_dict(),
            "packet_digest": self.packet_digest,
            "is_authoritative": self.is_authoritative,
            "can_finalize": self.can_finalize,
            "finalization": self.finalization,
            "reasons": list(self.reasons),
            "diagnostic_only": self.diagnostic_only,
            "timestamp": self.timestamp,
        }


def assert_distinct_sessions(
    execution_session: SessionIdentity, verifier_session: SessionIdentity
) -> None:
    """Fail closed if the verifier reuses the execution session identity."""
    if execution_session.session_id == verifier_session.session_id:
        raise SessionIdentityCollisionError(
            "Fresh-session verifier requires a DIFFERENT session identity from execution "
            f"(both are '{verifier_session.session_id}')."
        )


def run_fresh_verifier(
    packet: VerifierPacket,
    execution_session: SessionIdentity,
    verifier_session: SessionIdentity,
    mode: str = MODE_FRESH_SESSION,
    verifier_decision: str = FINAL_VERIFIED,
) -> FreshVerifierResult:
    """Run the fresh-session verifier over an Order-08 verifier packet (model-free).

    Contract:
    - the packet is validated (Order-08 ``validate_verifier_packet``) and its digest
      recomputed for parity;
    - in ``fresh_session`` mode the verifier session MUST differ from the execution
      session, else :class:`SessionIdentityCollisionError`; this run is authoritative and
      CAN finalize;
    - in ``same_session_audit`` mode the run is diagnostic-only, non-authoritative, and
      CANNOT finalize (finalization is forced to ``not_finalized``);
    - only the verifier role may author a verifier decision (Order-08 role gate).
    """
    if mode not in ALL_MODES:
        raise AgyVerifierError(f"Unknown verifier mode '{mode}'")

    if verifier_session.role != ROLE_VERIFIER:
        raise SelfVerificationForbiddenError(
            f"Verifier session must carry role '{ROLE_VERIFIER}', got '{verifier_session.role}'"
        )

    # Order-08 gate: only the verifier role may author a verifier decision.
    verify_roles.enforce_role_action(verifier_session.role, "author_verifier_decision")

    validation = validate_verifier_packet(packet)
    reasons: List[str] = []
    if not validation.ok:
        reasons.extend(f.message for f in validation.findings)

    expected_digest = compute_verifier_packet_digest(packet.to_dict())
    if expected_digest != packet.packet_digest:
        reasons.append(
            f"packet digest parity mismatch: expected {expected_digest}, got {packet.packet_digest}"
        )

    if mode == MODE_SAME_SESSION_AUDIT:
        # A same-session audit is a labeled diagnostic: non-authoritative, cannot finalize.
        return FreshVerifierResult(
            mode=mode,
            execution_session=execution_session,
            verifier_session=verifier_session,
            packet_digest=packet.packet_digest,
            is_authoritative=False,
            can_finalize=False,
            finalization=FINAL_NOT_FINALIZED,
            reasons=reasons
            + [
                "same-session audit is diagnostic-only and cannot finalize a run "
                "(a fresh-session verifier is required for completion)."
            ],
            diagnostic_only=True,
        )

    # fresh_session mode: enforce distinct session identity.
    assert_distinct_sessions(execution_session, verifier_session)

    finalization = verifier_decision if not reasons else FINAL_CORRECTION_REQUIRED
    return FreshVerifierResult(
        mode=mode,
        execution_session=execution_session,
        verifier_session=verifier_session,
        packet_digest=packet.packet_digest,
        is_authoritative=True,
        can_finalize=True,
        finalization=finalization,
        reasons=reasons
        or ["fresh-session verifier validated the packet and finalized."],
        diagnostic_only=False,
    )


def finalize_run(result: FreshVerifierResult) -> str:
    """Attempt to finalize a run from a verifier result.

    A diagnostic (same-session) audit cannot finalize: raises
    :class:`SameSessionCannotFinalizeError`. A fresh-session result returns its
    finalization outcome.
    """
    if not result.can_finalize or result.diagnostic_only:
        raise SameSessionCannotFinalizeError(
            "A same-session diagnostic audit cannot finalize a run; run a fresh-session "
            "verifier (distinct session identity) to complete."
        )
    return result.finalization


# ==================================================================================================
# Model-free test doubles (no live agy / network / model)
# ==================================================================================================


@dataclass
class AgySessionDouble:
    """A deterministic stand-in for a live agy session. Records calls; never spawns agy."""

    identity: SessionIdentity
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def invoke(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Record an invocation and return a canned, deterministic response.

        This NEVER calls a network, model, or the agy binary. The response is derived
        purely from the prompt hash so tests are reproducible.
        """
        response_id = hashlib.sha256(
            f"{self.identity.session_id}\x00{prompt}".encode("utf-8")
        ).hexdigest()[:12]
        record = {
            "session_id": self.identity.session_id,
            "role": self.identity.role,
            "prompt": prompt,
            "response_id": response_id,
            "kwargs": dict(kwargs),
        }
        self.calls.append(record)
        return record


def make_execution_and_verifier_doubles(
    run_seed: str,
) -> "tuple[AgySessionDouble, AgySessionDouble]":
    """Build an execution double and a DISTINCT fresh-session verifier double.

    The verifier session identity is derived from a different role + a distinct seed, so
    the two ``session_id`` values differ by construction (mirroring a real fresh session).
    """
    exec_identity = new_session_identity(
        ROLE_EXECUTOR, seed=f"{run_seed}:exec", label="execution"
    )
    verifier_identity = new_session_identity(
        ROLE_VERIFIER, seed=f"{run_seed}:verify", label="fresh-verifier"
    )
    return AgySessionDouble(exec_identity), AgySessionDouble(verifier_identity)


__all__ = [
    "MODE_FRESH_SESSION",
    "MODE_SAME_SESSION_AUDIT",
    "ALL_MODES",
    "FINAL_VERIFIED",
    "FINAL_CORRECTION_REQUIRED",
    "FINAL_NOT_FINALIZED",
    "AgyVerifierError",
    "SameSessionCannotFinalizeError",
    "SessionIdentityCollisionError",
    "SessionIdentity",
    "new_session_identity",
    "FreshVerifierResult",
    "assert_distinct_sessions",
    "run_fresh_verifier",
    "finalize_run",
    "AgySessionDouble",
    "make_execution_and_verifier_doubles",
]
