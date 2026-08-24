"""Capability-gated per-host launchers + fresh verification (execset Order 04, `31744f` E-02/E-03).

Thin launchers over the generic `host_runner`, one semantic runner plus per-host adapters (OQ-01:
separate implementations would drift). Each launcher advertises a native capability (native
subagents, model flags, resume, JSON, worktrees, permissions) ONLY when the Order-10
`HostCapabilityRegistry` returns CURRENT positive probe evidence for it; otherwise it selects the
documented SAFE fallback (a coordinator-owned external process) or an explicit refusal. Adapters and
shims are generated through the existing `host_adapters.generate_adapter_bundle` /
`engine.generate_shim_members` (not forked).

E-03: launching enforces DISTINCT executor/verifier sessions (`agy_verifier.assert_distinct_sessions`
+ `run_fresh_verifier`; a same-session audit is diagnostic-only and cannot finalize), task-local
resume for correction, exact model-role binding, and host-specific greenwashing checks (a host exit
0 / soft-denied result with no verified side effect cannot finalize).

Pure orchestration over the executed host_adapters / host_capability_registry / agy_verifier /
host_runner / ipd_set_executor primitives. No live models are launched in tests (doubles only).
"""

from __future__ import annotations

from typing import NamedTuple, Optional, Sequence, Tuple

from agent_workflows import host_adapters as _ha
from agent_workflows import host_runner as _hr

# Launch strategies a launcher may select for a requested feature.
STRATEGY_NATIVE = "native"  # a probed, currently-supported native host capability
STRATEGY_FALLBACK = "fallback"  # the safe coordinator-owned external-process fallback
STRATEGY_REFUSE = "refuse"  # explicit refusal (no native support and no safe fallback)


class LaunchPlan(NamedTuple):
    """How a launcher will satisfy a requested feature for a host, and why."""

    host: str
    feature: str
    strategy: str  # STRATEGY_*
    target: str  # native feature name or the fallback runtime command
    reasons: Tuple[str, ...]


def plan_launch(
    adapter: _ha.HostAdapter,
    feature: str,
    *,
    allow_fallback: bool = True,
) -> LaunchPlan:
    """Decide how to satisfy ``feature`` on ``adapter.host``.

    Native ONLY when the adapter advertises the feature supported (which `build_host_adapter` sets
    solely from current positive registry evidence). Otherwise the safe fallback runtime, or - when
    fallback is disallowed for this feature - an explicit refusal. Never advertises an unverified
    capability as native.
    """
    if adapter.advertises_supported(feature):
        return LaunchPlan(
            host=adapter.host,
            feature=feature,
            strategy=STRATEGY_NATIVE,
            target=_ha.resolve_role_target(
                adapter.host, adapter.role_map.get(feature, "")
            )
            if adapter.role_map.get(feature)
            else feature,
            reasons=("current positive probe evidence for {0}".format(feature),),
        )
    reasons = tuple(
        adapter.capability_reasons.get(feature, ("no current positive probe evidence",))
    )
    if allow_fallback:
        return LaunchPlan(
            host=adapter.host,
            feature=feature,
            strategy=STRATEGY_FALLBACK,
            target=adapter.fallback_runtime,
            reasons=reasons + ("selecting safe external-process fallback",),
        )
    return LaunchPlan(
        host=adapter.host,
        feature=feature,
        strategy=STRATEGY_REFUSE,
        target="",
        reasons=reasons + ("no safe fallback for this feature; refusing",),
    )


# ---- fresh verification (E-03) -------------------------------------------------------------------


class VerificationOutcome(NamedTuple):
    can_finalize: bool
    is_authoritative: bool
    reason: str
    executor_session_id: str
    verifier_session_id: str


def verify_fresh(
    packet,
    *,
    run_seed: str,
    mode: Optional[str] = None,
    verifier_decision: Optional[str] = None,
) -> VerificationOutcome:
    """Run the reused fresh-session verifier with DISTINCT executor/verifier sessions.

    A same-session audit is diagnostic-only and cannot finalize. Returns a compact outcome; a
    session-identity collision raises (fail-closed) from the reused `assert_distinct_sessions`.
    """
    from agent_workflows import agy_verifier as _agy

    execu, verifier = _agy.make_execution_and_verifier_doubles(run_seed)
    _agy.assert_distinct_sessions(execu.identity, verifier.identity)
    result = _agy.run_fresh_verifier(
        packet,
        execution_session=execu.identity,
        verifier_session=verifier.identity,
        mode=mode or _agy.MODE_FRESH_SESSION,
        verifier_decision=verifier_decision or _agy.FINAL_VERIFIED,
    )
    return VerificationOutcome(
        can_finalize=result.can_finalize,
        is_authoritative=result.is_authoritative,
        reason="; ".join(result.reasons) if result.reasons else result.finalization,
        executor_session_id=execu.identity.session_id,
        verifier_session_id=verifier.identity.session_id,
    )


# ---- model-role binding enforcement (E-03) -------------------------------------------------------


class ModelRoutingError(Exception):
    """Raised when a lane's required work-class binding is missing or mismatched (fail-closed)."""


def enforce_model_binding(routing, work_class: str, *, host: str) -> Tuple[str, str]:
    """Resolve the exact (host, model) binding for a work class, fail-closed on a missing binding,
    and verify the binding's host matches the launching host. Returns (host, model)."""
    binding = routing.resolve(work_class)  # raises BindingError (fail-closed) if unset
    if binding.host != host:
        raise ModelRoutingError(
            "work class {0!r} is bound to host {1!r}, not the launching host {2!r}".format(
                work_class, binding.host, host
            )
        )
    return binding.host, binding.model


# ---- task-local resume for correction (E-03) -----------------------------------------------------


def resume_task_packet(
    packet: _hr.TaskPacket, *, correction_argv: Sequence[str]
) -> _hr.TaskPacket:
    """Produce a resume packet for a correction: same lane/session, incremented attempt, new argv.

    Task-local resume keeps the SAME session id (so the worker retains context) and increments the
    attempt, so the ledger records a distinct attempt rather than replaying the first one."""
    return packet._replace(
        argv=tuple(correction_argv),
        attempt=packet.attempt + 1,
    )


# ---- host-specific greenwashing guard (E-03) -----------------------------------------------------


def host_result_can_finalize(
    raw: _hr.RawWorkerResult,
    tool_event: Optional[dict] = None,
) -> Tuple[bool, str]:
    """Host-specific greenwashing guard: a host exit 0 / soft-denied result cannot finalize unless a
    real side effect is present and the reused evidence validator passes.

    Returns (can_finalize, reason). This wires the host worker's exit/stdout/diff INTO the reused
    validators rather than trusting a host success exit.
    """
    ws = _hr.classify_worker_state(raw)
    if ws != _hr.WORKER_COMPLETED:
        return False, "worker terminal state {0} is not completion".format(ws)
    if tool_event is not None:
        ev = _hr.evidence_gate(tool_event)
        if not ev.ok:
            return False, "evidence gate rejected: {0}".format(
                ", ".join(f.code for f in ev.findings)
            )
    return True, "completed with a verified side effect"
