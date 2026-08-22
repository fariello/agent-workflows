"""Human decision gates, headless needs_input stop, and consent enforcement.

awoptimize Order 06 (`ptsfjn`) E-03.

Implements human decision gates with explicit options, declared defaults, timeout policies,
non-interactive refusal, and recorded authorization. Guarantees that consent is NEVER synthesized:
a headless/non-interactive run reaching a gate stops with a stable `needs_input` result before
any gated side effect is executed.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import (
    Any,
    NamedTuple,
    TypeVar,
)

from agent_workflows import run_engine

T = TypeVar("T")

# ---- Gate Status Constants -----------------------------------------------------------------------

GATE_STATUS_APPROVED: str = "approved"
GATE_STATUS_REJECTED: str = "rejected"
GATE_STATUS_NEEDS_INPUT: str = "needs_input"
GATE_STATUS_TIMED_OUT: str = "timed_out"
GATE_STATUS_REFUSED: str = "refused"
GATE_STATUS_ABORTED: str = "aborted"

ALL_GATE_STATUSES: frozenset[str] = frozenset(
    (
        GATE_STATUS_APPROVED,
        GATE_STATUS_REJECTED,
        GATE_STATUS_NEEDS_INPUT,
        GATE_STATUS_TIMED_OUT,
        GATE_STATUS_REFUSED,
        GATE_STATUS_ABORTED,
    )
)

_APPROVAL_TOKENS: frozenset[str] = frozenset(
    ("approve", "proceed", "yes", "confirm", "allow", "continue")
)
_REJECTION_TOKENS: frozenset[str] = frozenset(
    ("reject", "no", "deny", "refuse", "disallow")
)
_ABORT_TOKENS: frozenset[str] = frozenset(("abort", "cancel", "stop", "exit"))


# ---- Exceptions ----------------------------------------------------------------------------------


class RunGateError(Exception):
    """Base exception for run gate errors."""


class GateRefusalError(RunGateError):
    """Raised when a gate is refused or execution cannot proceed through gate."""


class GateTimeoutError(RunGateError):
    """Raised when a gate wait exceeds timeout under a fail/refuse policy."""


class SynthesizedConsentError(RunGateError):
    """Raised when an attempt is made to invent or synthesize human consent."""


# ---- Data Structures -----------------------------------------------------------------------------


class DecisionGate(NamedTuple):
    gate_id: str
    prompt: str
    options: tuple[str, ...] = ("approve", "reject", "abort")
    default_option: str | None = "abort"
    timeout_seconds: float | None = None
    timeout_policy: str = "refuse"  # "refuse", "fail", "abort", "apply_default"
    requires_human: bool = True
    metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "prompt": self.prompt,
            "options": list(self.options),
            "default_option": self.default_option,
            "timeout_seconds": self.timeout_seconds,
            "timeout_policy": self.timeout_policy,
            "requires_human": self.requires_human,
            "metadata": dict(self.metadata),
        }


class GateDecision(NamedTuple):
    gate_id: str
    status: str
    selected_option: str | None
    approver: str | None
    actor: str
    timestamp: str
    interactive: bool
    reason: str | None = None

    @property
    def is_approved(self) -> bool:
        """True if and only if the gate was explicitly approved by an authorized human."""
        return self.status == GATE_STATUS_APPROVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "status": self.status,
            "selected_option": self.selected_option,
            "approver": self.approver,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "interactive": self.interactive,
            "reason": self.reason,
            "is_approved": self.is_approved,
        }


# ---- Gate Evaluation & Execution -----------------------------------------------------------------


def evaluate_gate(
    gate: DecisionGate,
    *,
    interactive: bool = False,
    input_handler: Callable[[DecisionGate], str] | None = None,
    approver: str = "human",
    current_time: str | None = None,
) -> GateDecision:
    """Evaluate a human decision gate.

    Guarantees:
      1. Non-interactive (headless) runs stop with status 'needs_input' before any side effect.
      2. Consent is NEVER synthesized, even if default_option='approve'.
      3. Interactive choices are recorded with approver and timestamp.
      4. Timeouts adhere to declared policy without inventing default consent.
    """
    ts = current_time or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # 1. Non-interactive / Headless check: STOP AT needs_input
    if not interactive:
        return GateDecision(
            gate_id=gate.gate_id,
            status=GATE_STATUS_NEEDS_INPUT,
            selected_option=None,
            approver=None,
            actor="runtime",
            timestamp=ts,
            interactive=False,
            reason="Headless execution halted: gate requires interactive human authorization",
        )

    # 2. Interactive evaluation
    selected_option: str | None = None
    timed_out = False

    if input_handler is not None:
        try:
            raw_choice = input_handler(gate)
            selected_option = str(raw_choice).strip()
        except TimeoutError:
            timed_out = True
        except Exception as exc:
            return GateDecision(
                gate_id=gate.gate_id,
                status=GATE_STATUS_REFUSED,
                selected_option=None,
                approver=None,
                actor="runtime",
                timestamp=ts,
                interactive=True,
                reason=f"Error reading human input: {exc}",
            )
    else:
        # Fallback to stdin prompt if interactive and no custom handler
        try:
            options_str = "/".join(gate.options)
            prompt_text = f"\n[GATE {gate.gate_id}] {gate.prompt} ({options_str}) "
            if gate.default_option:
                prompt_text += f"[{gate.default_option}]: "
            else:
                prompt_text += ": "
            user_in = input(prompt_text).strip()
            if not user_in and gate.default_option:
                selected_option = gate.default_option
            else:
                selected_option = user_in
        except (EOFError, KeyboardInterrupt):
            selected_option = "abort"
        except Exception:
            timed_out = True

    # Handle timeout
    if timed_out:
        if gate.timeout_policy == "apply_default" and gate.default_option:
            norm_def = gate.default_option.lower()
            # Guard: Never synthesize approval consent on timeout!
            if norm_def in _APPROVAL_TOKENS:
                return GateDecision(
                    gate_id=gate.gate_id,
                    status=GATE_STATUS_NEEDS_INPUT,
                    selected_option=None,
                    approver=None,
                    actor="runtime",
                    timestamp=ts,
                    interactive=True,
                    reason="Timeout occurred; refusing to synthesize approval consent",
                )
            elif norm_def in _ABORT_TOKENS:
                return GateDecision(
                    gate_id=gate.gate_id,
                    status=GATE_STATUS_ABORTED,
                    selected_option=gate.default_option,
                    approver=None,
                    actor="runtime",
                    timestamp=ts,
                    interactive=True,
                    reason=f"Gate timed out after {gate.timeout_seconds}s; applied default '{gate.default_option}'",
                )
            else:
                return GateDecision(
                    gate_id=gate.gate_id,
                    status=GATE_STATUS_REJECTED,
                    selected_option=gate.default_option,
                    approver=None,
                    actor="runtime",
                    timestamp=ts,
                    interactive=True,
                    reason=f"Gate timed out after {gate.timeout_seconds}s; applied default '{gate.default_option}'",
                )
        else:
            return GateDecision(
                gate_id=gate.gate_id,
                status=GATE_STATUS_TIMED_OUT,
                selected_option=None,
                approver=None,
                actor="runtime",
                timestamp=ts,
                interactive=True,
                reason=f"Gate timed out waiting for human authorization (policy: {gate.timeout_policy})",
            )

    if not selected_option:
        return GateDecision(
            gate_id=gate.gate_id,
            status=GATE_STATUS_REFUSED,
            selected_option=None,
            approver=None,
            actor="runtime",
            timestamp=ts,
            interactive=True,
            reason="Empty response provided at human gate",
        )

    norm_choice = selected_option.lower()

    # Determine outcome from selected option
    if norm_choice in _APPROVAL_TOKENS or norm_choice in [
        o.lower() for o in gate.options if o.lower() in _APPROVAL_TOKENS
    ]:
        return GateDecision(
            gate_id=gate.gate_id,
            status=GATE_STATUS_APPROVED,
            selected_option=selected_option,
            approver=approver,
            actor="human",
            timestamp=ts,
            interactive=True,
            reason="Explicit human approval granted",
        )
    elif norm_choice in _ABORT_TOKENS or norm_choice in [
        o.lower() for o in gate.options if o.lower() in _ABORT_TOKENS
    ]:
        return GateDecision(
            gate_id=gate.gate_id,
            status=GATE_STATUS_ABORTED,
            selected_option=selected_option,
            approver=approver,
            actor="human",
            timestamp=ts,
            reason="Execution aborted by human at decision gate",
            interactive=True,
        )
    elif norm_choice in _REJECTION_TOKENS or norm_choice in [
        o.lower() for o in gate.options if o.lower() in _REJECTION_TOKENS
    ]:
        return GateDecision(
            gate_id=gate.gate_id,
            status=GATE_STATUS_REJECTED,
            selected_option=selected_option,
            approver=approver,
            actor="human",
            timestamp=ts,
            reason="Human rejected gate authorization",
            interactive=True,
        )
    else:
        # Check if option is explicitly present in gate.options
        if selected_option in gate.options:
            return GateDecision(
                gate_id=gate.gate_id,
                status=GATE_STATUS_APPROVED,
                selected_option=selected_option,
                approver=approver,
                actor="human",
                timestamp=ts,
                reason=f"Option '{selected_option}' chosen by human",
                interactive=True,
            )
        else:
            return GateDecision(
                gate_id=gate.gate_id,
                status=GATE_STATUS_REFUSED,
                selected_option=selected_option,
                approver=approver,
                actor="human",
                timestamp=ts,
                reason=f"Invalid option '{selected_option}' chosen; valid options are {list(gate.options)}",
                interactive=True,
            )


def execute_gated_action(
    gate: DecisionGate,
    action: Callable[[], T],
    *,
    engine: run_engine.RunEngine | None = None,
    interactive: bool = False,
    input_handler: Callable[[DecisionGate], str] | None = None,
    approver: str = "human",
) -> tuple[GateDecision, T | None]:
    """Execute an action strictly behind a human decision gate.

    Guarantees:
      1. Action is ONLY executed if human explicitly grants approval.
      2. If decision is 'needs_input', 'rejected', 'aborted', or 'timed_out',
         action is NEVER called (no gated side effects occur).
      3. When engine is provided and gate is approved, records 'human_approval' in ledger.
    """
    decision = evaluate_gate(
        gate=gate,
        interactive=interactive,
        input_handler=input_handler,
        approver=approver,
    )

    if not decision.is_approved:
        return decision, None

    # Gate is explicitly approved
    if engine is not None:
        engine.record_approval(
            gate=gate.gate_id,
            approver=decision.approver or approver,
            actor=decision.actor if decision.actor in ("human", "runtime") else "human",
        )

    result = action()
    return decision, result
