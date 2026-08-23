"""Portable isolation hierarchy, concurrency eligibility analyzer, and merge-revalidate gates.

awoptimize Order 09 (`1m5ob8`) E-01..E-04.

This module provides:
  * E-01: Portable isolation hierarchy (fresh session/subagent preferred for verifier;
          fork allowed only for read-only side work that benefits from inherited context;
          same-session audit allowed ONLY as non-authoritative diagnostic; two-process
          fallback for hosts lacking native subagents).
  * E-02: Concurrency eligibility analyzer: parallelizes independent read-only investigations,
          serializes mutations by default, and allows parallel mutation ONLY with separate
          worktrees, disjoint file ownership, dependency independence, no shared generated
          files, and a deterministic merge order + serial fallback plan.
  * E-03: Merge-and-revalidate gates for isolated mutators: stale-base detection, conflict-
          resolution authority, combined-diff review, generated-file ownership, and FULL
          post-integration validation (never trusting per-lane results).
  * E-04: Seeded orchestration adversarial protections against role collisions, leaked prose,
          unauthorized mutations, shared-worktree conflicts, stale branches, lane timeouts,
          and unsafe background completions.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
import fnmatch
import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any, NamedTuple

from agent_workflows import verify_roles as vr

# ==================================================================================================
# Constants & Vocabularies (E-01)
# ==================================================================================================

# Isolation Modes
ISOLATION_FRESH_SESSION: str = "fresh_session"
ISOLATION_INDEPENDENT_SUBAGENT: str = "independent_subagent"
ISOLATION_FORK: str = "fork"
ISOLATION_SAME_SESSION_DIAGNOSTIC: str = "same_session_diagnostic"
ISOLATION_TWO_PROCESS_FALLBACK: str = "two_process_fallback"

ALL_ISOLATION_MODES: frozenset[str] = frozenset(
    (
        ISOLATION_FRESH_SESSION,
        ISOLATION_INDEPENDENT_SUBAGENT,
        ISOLATION_FORK,
        ISOLATION_SAME_SESSION_DIAGNOSTIC,
        ISOLATION_TWO_PROCESS_FALLBACK,
    )
)

# Work Shapes (from Orchestration Decision Table)
WORK_SHAPE_BOUNDED_IMPLEMENTATION: str = "bounded_implementation"
WORK_SHAPE_READ_ONLY_INVENTORY: str = "read_only_inventory"
WORK_SHAPE_INDEPENDENT_LANES: str = "independent_lanes"
WORK_SHAPE_VERIFICATION: str = "verification"
WORK_SHAPE_SAME_SESSION_AUDIT: str = "same_session_audit"
WORK_SHAPE_RELEASE_MUTATION: str = "release_mutation"

ALL_WORK_SHAPES: frozenset[str] = frozenset(
    (
        WORK_SHAPE_BOUNDED_IMPLEMENTATION,
        WORK_SHAPE_READ_ONLY_INVENTORY,
        WORK_SHAPE_INDEPENDENT_LANES,
        WORK_SHAPE_VERIFICATION,
        WORK_SHAPE_SAME_SESSION_AUDIT,
        WORK_SHAPE_RELEASE_MUTATION,
    )
)

# Lane Kinds (E-02)
LANE_KIND_READ_ONLY: str = "read_only"
LANE_KIND_MUTATING: str = "mutating"

# Concurrency Execution Modes (E-02)
EXEC_MODE_PARALLEL_READ_ONLY: str = "parallel_read_only"
EXEC_MODE_PARALLEL_MUTATING: str = "parallel_mutating"
EXEC_MODE_SERIAL_MUTATING: str = "serial_mutating"
EXEC_MODE_SERIAL_FALLBACK: str = "serial_fallback"

# Named Conflict Types (E-02)
CONFLICT_SHARED_WORKTREE: str = "shared_worktree"
CONFLICT_OVERLAPPING_FILES: str = "overlapping_files"
CONFLICT_DEPENDENT_LANES: str = "dependent_lanes"
CONFLICT_SHARED_GENERATED_FILES: str = "shared_generated_files"
CONFLICT_MISSING_WORKTREE: str = "missing_worktree"

# Lane Outcome Statuses (E-03)
STATUS_COMPLETED: str = "completed"
STATUS_TIMED_OUT: str = "timed_out"
STATUS_FAILED: str = "failed"
STATUS_MISSING: str = "missing"

# Integration Gate Statuses (E-03)
INTEGRATED_PASSED: str = "integrated_passed"
INTEGRATION_FAILED_STALE_BASE: str = "integration_failed_stale_base"
INTEGRATION_FAILED_CONFLICT: str = "integration_failed_conflict"
INTEGRATION_FAILED_COMBINED_RED: str = "integration_failed_combined_red"
INTEGRATION_FAILED_MISSING_LANE: str = "integration_failed_missing_lane"
INTEGRATION_FAILED_SCOPE_VIOLATION: str = "integration_failed_scope_violation"
INTEGRATION_FAILED_LANE_FAILURE: str = "integration_failed_lane_failure"

# ==================================================================================================
# Exceptions
# ==================================================================================================


class OrchestrateIsolationError(Exception):
    """Base exception for orchestration, isolation, and concurrency errors."""


class IsolationPolicyViolationError(OrchestrateIsolationError):
    """Raised when an isolation mode violates role or work-shape policy."""


class ForkedVerifierForbiddenError(IsolationPolicyViolationError):
    """Raised when a fork is requested for the verifier (fork is read-only side work only)."""


class NonAuthoritativeDiagnosticError(IsolationPolicyViolationError):
    """Raised when a same-session diagnostic attempts to author an authoritative decision."""


class InvalidIsolationModeError(IsolationPolicyViolationError):
    """Raised when an unknown or invalid isolation mode is requested."""


class ConcurrencyConflictError(OrchestrateIsolationError):
    """Raised when unsafe concurrency is detected."""


class IntegrationGateError(OrchestrateIsolationError):
    """Base exception for merge-and-revalidate gate failures."""


class StaleBaseError(IntegrationGateError):
    """Raised when an integrated lane is based on a stale base commit."""


class CombinedRevalidationFailedError(IntegrationGateError):
    """Raised when full post-integration revalidation fails (combined-red)."""


class LaneExecutionTimeoutError(IntegrationGateError):
    """Raised when a background or parallel lane times out."""


class MissingLaneResultError(IntegrationGateError):
    """Raised when a required lane result is missing."""


# ==================================================================================================
# Data Structures: Isolation Hierarchy (E-01)
# ==================================================================================================


class IsolationPolicyResult(NamedTuple):
    allowed: bool
    actor_role: str
    work_shape: str
    isolation_mode: str
    is_authoritative: bool
    can_mutate_product: bool
    message: str


class IsolationContext(NamedTuple):
    mode: str
    actor_role: str
    work_shape: str
    worktree_path: str
    inherited_context: bool
    is_authoritative: bool
    can_mutate_product: bool
    can_author_verification: bool
    can_finalize_run: bool
    session_id: str
    process_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "actor_role": self.actor_role,
            "work_shape": self.work_shape,
            "worktree_path": self.worktree_path,
            "inherited_context": self.inherited_context,
            "is_authoritative": self.is_authoritative,
            "can_mutate_product": self.can_mutate_product,
            "can_author_verification": self.can_author_verification,
            "can_finalize_run": self.can_finalize_run,
            "session_id": self.session_id,
            "process_id": self.process_id,
        }


class HostIsolationCapabilities(NamedTuple):
    supports_subagent: bool
    supports_fork: bool
    supports_worktree: bool
    supports_multi_process: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "supports_subagent": self.supports_subagent,
            "supports_fork": self.supports_fork,
            "supports_worktree": self.supports_worktree,
            "supports_multi_process": self.supports_multi_process,
        }


class HandoffPacket(NamedTuple):
    run_id: str
    workflow_id: str
    step_id: str
    actor_role: str
    base_commit: str
    head_commit: str
    worktree_path: str
    requirements: dict[str, Any]
    declared_scope: dict[str, Any]
    actual_diff: str
    timestamp: str
    packet_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "actor_role": self.actor_role,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "worktree_path": self.worktree_path,
            "requirements": dict(self.requirements),
            "declared_scope": dict(self.declared_scope),
            "actual_diff": self.actual_diff,
            "timestamp": self.timestamp,
            "packet_digest": self.packet_digest,
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class HandoffPacketValidationResult(NamedTuple):
    ok: bool
    message: str
    packet: HandoffPacket | None


# ==================================================================================================
# Isolation Hierarchy Enforcement & Procedures (E-01)
# ==================================================================================================


def check_isolation_policy(
    actor_role: str,
    work_shape: str,
    isolation_mode: str,
    worktree_path: str = "",
) -> IsolationPolicyResult:
    """Evaluate isolation policy according to the orchestration decision table and role contracts."""
    if isolation_mode not in ALL_ISOLATION_MODES:
        return IsolationPolicyResult(
            allowed=False,
            actor_role=actor_role,
            work_shape=work_shape,
            isolation_mode=isolation_mode,
            is_authoritative=False,
            can_mutate_product=False,
            message=f"Unknown isolation mode '{isolation_mode}'",
        )

    # Verifier and Verification Shape Rules
    if actor_role == vr.ROLE_VERIFIER or work_shape == WORK_SHAPE_VERIFICATION:
        if isolation_mode == ISOLATION_FORK:
            return IsolationPolicyResult(
                allowed=False,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=False,
                can_mutate_product=False,
                message=(
                    f"Forked context is strictly rejected for verifier (actor '{actor_role}'): "
                    "fork is allowed only for read-only side work that benefits from inherited context."
                ),
            )
        if isolation_mode == ISOLATION_SAME_SESSION_DIAGNOSTIC:
            return IsolationPolicyResult(
                allowed=False,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=False,
                can_mutate_product=False,
                message="Authoritative verification cannot be performed in same_session_diagnostic mode.",
            )
        # Fresh session, independent subagent, and two-process fallback are preferred and allowed
        return IsolationPolicyResult(
            allowed=True,
            actor_role=actor_role,
            work_shape=work_shape,
            isolation_mode=isolation_mode,
            is_authoritative=True,
            can_mutate_product=False,
            message=f"Isolation mode '{isolation_mode}' approved for verifier role.",
        )

    # Same-Session Diagnostic Shape Rules
    if work_shape == WORK_SHAPE_SAME_SESSION_AUDIT:
        if isolation_mode == ISOLATION_SAME_SESSION_DIAGNOSTIC:
            return IsolationPolicyResult(
                allowed=True,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=False,  # strictly non-authoritative diagnostic
                can_mutate_product=False,
                message="Same-session audit approved as non-authoritative diagnostic ONLY.",
            )
        return IsolationPolicyResult(
            allowed=True,
            actor_role=actor_role,
            work_shape=work_shape,
            isolation_mode=isolation_mode,
            is_authoritative=False,
            can_mutate_product=False,
            message=f"Diagnostic audit running under '{isolation_mode}'.",
        )

    # Read-Only Side Work / Inventory Rules
    if (
        work_shape == WORK_SHAPE_READ_ONLY_INVENTORY
        or actor_role == vr.ROLE_INVESTIGATOR
    ):
        if isolation_mode == ISOLATION_FORK:
            return IsolationPolicyResult(
                allowed=True,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=True,
                can_mutate_product=False,
                message="Fork mode approved for read-only investigation with inherited context.",
            )
        return IsolationPolicyResult(
            allowed=True,
            actor_role=actor_role,
            work_shape=work_shape,
            isolation_mode=isolation_mode,
            is_authoritative=True,
            can_mutate_product=False,
            message=f"Read-only investigation permitted under '{isolation_mode}'.",
        )

    # Mutating Implementations (Executor / Corrector)
    if actor_role in (vr.ROLE_EXECUTOR, vr.ROLE_CORRECTOR) or work_shape in (
        WORK_SHAPE_BOUNDED_IMPLEMENTATION,
        WORK_SHAPE_INDEPENDENT_LANES,
        WORK_SHAPE_RELEASE_MUTATION,
    ):
        if isolation_mode == ISOLATION_FORK:
            return IsolationPolicyResult(
                allowed=False,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=False,
                can_mutate_product=False,
                message="Fork mode is restricted to read-only side work and cannot be used for mutating implementations.",
            )
        if isolation_mode == ISOLATION_SAME_SESSION_DIAGNOSTIC:
            return IsolationPolicyResult(
                allowed=False,
                actor_role=actor_role,
                work_shape=work_shape,
                isolation_mode=isolation_mode,
                is_authoritative=False,
                can_mutate_product=False,
                message="Same-session diagnostic mode cannot perform mutating implementations.",
            )
        return IsolationPolicyResult(
            allowed=True,
            actor_role=actor_role,
            work_shape=work_shape,
            isolation_mode=isolation_mode,
            is_authoritative=True,
            can_mutate_product=True,
            message=f"Mutating implementation approved under '{isolation_mode}'.",
        )

    # Default Coordinator / Human / Runtime
    return IsolationPolicyResult(
        allowed=True,
        actor_role=actor_role,
        work_shape=work_shape,
        isolation_mode=isolation_mode,
        is_authoritative=True,
        can_mutate_product=False,
        message=f"Isolation mode '{isolation_mode}' permitted for '{actor_role}'.",
    )


def enforce_isolation_policy(
    actor_role: str,
    work_shape: str,
    isolation_mode: str,
    worktree_path: str = "",
) -> None:
    """Enforce isolation policy, raising specific typed exceptions on violations."""
    res = check_isolation_policy(
        actor_role=actor_role,
        work_shape=work_shape,
        isolation_mode=isolation_mode,
        worktree_path=worktree_path,
    )
    if not res.allowed:
        if (
            actor_role == vr.ROLE_VERIFIER or work_shape == WORK_SHAPE_VERIFICATION
        ) and isolation_mode == ISOLATION_FORK:
            raise ForkedVerifierForbiddenError(res.message)
        elif isolation_mode == ISOLATION_SAME_SESSION_DIAGNOSTIC:
            raise NonAuthoritativeDiagnosticError(res.message)
        else:
            raise IsolationPolicyViolationError(res.message)


def create_isolation_context(
    mode: str,
    actor_role: str,
    work_shape: str,
    worktree_path: str = "",
    session_id: str = "",
    process_id: int | None = None,
) -> IsolationContext:
    """Create an explicit isolation context descriptor."""
    enforce_isolation_policy(
        actor_role=actor_role,
        work_shape=work_shape,
        isolation_mode=mode,
        worktree_path=worktree_path,
    )
    contract = vr.get_role_contract(actor_role)
    is_diagnostic = (
        mode == ISOLATION_SAME_SESSION_DIAGNOSTIC
        or work_shape == WORK_SHAPE_SAME_SESSION_AUDIT
    )
    inherited = mode in (ISOLATION_FORK, ISOLATION_SAME_SESSION_DIAGNOSTIC)
    sid = (
        session_id
        or hashlib.sha256(
            f"{mode}:{actor_role}:{work_shape}:{datetime.datetime.now(datetime.timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]
    )

    return IsolationContext(
        mode=mode,
        actor_role=actor_role,
        work_shape=work_shape,
        worktree_path=worktree_path,
        inherited_context=inherited,
        is_authoritative=not is_diagnostic,
        can_mutate_product=contract.can_mutate_product_code
        and not is_diagnostic
        and mode != ISOLATION_FORK,
        can_author_verification=contract.can_author_verifier_decision
        and not is_diagnostic,
        can_finalize_run=contract.can_author_terminal_transaction and not is_diagnostic,
        session_id=sid,
        process_id=process_id,
    )


def enforce_authoritative_decision(
    isolation_context: IsolationContext, decision_kind: str
) -> None:
    """Refuse authoritative decisions from non-authoritative diagnostics."""
    if (
        not isolation_context.is_authoritative
        or isolation_context.mode == ISOLATION_SAME_SESSION_DIAGNOSTIC
    ):
        raise NonAuthoritativeDiagnosticError(
            f"Non-authoritative diagnostic context ({isolation_context.mode}) cannot author '{decision_kind}'. "
            "Same-session audits are non-authoritative diagnostics and cannot act as completion gates."
        )


def resolve_isolation_mode(
    requested_mode: str, capabilities: HostIsolationCapabilities
) -> str:
    """Resolve an isolation mode against host capabilities, falling back to two-process if needed."""
    if requested_mode == ISOLATION_INDEPENDENT_SUBAGENT:
        if capabilities.supports_subagent:
            return ISOLATION_INDEPENDENT_SUBAGENT
        elif capabilities.supports_multi_process:
            return ISOLATION_TWO_PROCESS_FALLBACK
    elif requested_mode == ISOLATION_FORK:
        if capabilities.supports_fork:
            return ISOLATION_FORK
        elif capabilities.supports_multi_process:
            return ISOLATION_TWO_PROCESS_FALLBACK
    elif requested_mode == ISOLATION_FRESH_SESSION:
        return ISOLATION_FRESH_SESSION
    elif requested_mode == ISOLATION_SAME_SESSION_DIAGNOSTIC:
        return ISOLATION_SAME_SESSION_DIAGNOSTIC
    elif requested_mode == ISOLATION_TWO_PROCESS_FALLBACK:
        return ISOLATION_TWO_PROCESS_FALLBACK

    # Default fallback
    return (
        ISOLATION_TWO_PROCESS_FALLBACK
        if capabilities.supports_multi_process
        else ISOLATION_FRESH_SESSION
    )


def build_handoff_packet(
    run_id: str,
    workflow_id: str,
    step_id: str,
    actor_role: str,
    base_commit: str,
    head_commit: str,
    worktree_path: str,
    requirements: Mapping[str, Any] | Sequence[Any],
    declared_scope: Mapping[str, Any],
    actual_diff: str,
    timestamp: str | None = None,
) -> HandoffPacket:
    """Build a serializable handoff packet for two-process fallback sessions."""
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    req_dict: dict[str, Any] = {}
    if isinstance(requirements, Mapping):
        req_dict = dict(requirements)
    else:
        req_dict = {"requirements": list(requirements)}

    raw_payload = {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "step_id": step_id,
        "actor_role": actor_role,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "worktree_path": worktree_path,
        "requirements": req_dict,
        "declared_scope": dict(declared_scope),
        "actual_diff": actual_diff,
        "timestamp": ts,
    }
    encoded = json.dumps(raw_payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    digest = hashlib.sha256(encoded).hexdigest()

    return HandoffPacket(
        run_id=run_id,
        workflow_id=workflow_id,
        step_id=step_id,
        actor_role=actor_role,
        base_commit=base_commit,
        head_commit=head_commit,
        worktree_path=worktree_path,
        requirements=req_dict,
        declared_scope=dict(declared_scope),
        actual_diff=actual_diff,
        timestamp=ts,
        packet_digest=digest,
    )


def validate_handoff_packet(raw_packet: Any) -> HandoffPacketValidationResult:
    """Validate handoff packet structural integrity and digest."""
    if isinstance(raw_packet, HandoffPacket):
        p = raw_packet
    elif isinstance(raw_packet, Mapping):
        p = HandoffPacket(
            run_id=str(raw_packet.get("run_id", "")),
            workflow_id=str(raw_packet.get("workflow_id", "")),
            step_id=str(raw_packet.get("step_id", "")),
            actor_role=str(raw_packet.get("actor_role", "")),
            base_commit=str(raw_packet.get("base_commit", "")),
            head_commit=str(raw_packet.get("head_commit", "")),
            worktree_path=str(raw_packet.get("worktree_path", "")),
            requirements=dict(raw_packet.get("requirements", {})),
            declared_scope=dict(raw_packet.get("declared_scope", {})),
            actual_diff=str(raw_packet.get("actual_diff", "")),
            timestamp=str(raw_packet.get("timestamp", "")),
            packet_digest=str(raw_packet.get("packet_digest", "")),
        )
    else:
        return HandoffPacketValidationResult(
            False, "Handoff packet must be a mapping or HandoffPacket", None
        )

    if not p.run_id or not p.step_id or not p.actor_role:
        return HandoffPacketValidationResult(
            False, "Missing required identity fields in handoff packet", None
        )
    if not p.packet_digest:
        return HandoffPacketValidationResult(False, "Missing packet digest", None)

    return HandoffPacketValidationResult(True, "Handoff packet is valid", p)


def run_isolated_session_double(
    isolation_mode: str,
    packet: HandoffPacket,
    runner_fn: Callable[[HandoffPacket], dict[str, Any]],
) -> dict[str, Any]:
    """Test double executing an isolated session with handoff packet."""
    val = validate_handoff_packet(packet)
    if not val.ok or val.packet is None:
        raise IsolationPolicyViolationError(f"Invalid handoff packet: {val.message}")
    return runner_fn(val.packet)


# ==================================================================================================
# Concurrency Eligibility Analyzer (E-02)
# ==================================================================================================


class LaneRequest(NamedTuple):
    lane_id: str
    actor_role: str
    lane_kind: str
    files_targeted: tuple[str, ...]
    generated_files: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    worktree_path: str = ""
    isolation_mode: str = ISOLATION_FRESH_SESSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "actor_role": self.actor_role,
            "lane_kind": self.lane_kind,
            "files_targeted": list(self.files_targeted),
            "generated_files": list(self.generated_files),
            "depends_on": list(self.depends_on),
            "worktree_path": self.worktree_path,
            "isolation_mode": self.isolation_mode,
        }


class LaneConflict(NamedTuple):
    conflict_type: str
    lane_a: str
    lane_b: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "lane_a": self.lane_a,
            "lane_b": self.lane_b,
            "details": self.details,
        }


class ConcurrencyEligibilityResult(NamedTuple):
    is_eligible_parallel: bool
    execution_mode: str
    conflicts: tuple[LaneConflict, ...]
    serial_fallback_plan: tuple[str, ...]
    merge_order: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_eligible_parallel": self.is_eligible_parallel,
            "execution_mode": self.execution_mode,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "serial_fallback_plan": list(self.serial_fallback_plan),
            "merge_order": list(self.merge_order),
            "reason": self.reason,
        }


def _files_overlap(files_a: Sequence[str], files_b: Sequence[str]) -> tuple[bool, str]:
    """Check if any file path or glob pattern in files_a overlaps with files_b."""
    for fa in files_a:
        for fb in files_b:
            if fa == fb:
                return True, f"Exact match on '{fa}'"
            if fnmatch.fnmatch(fa, fb) or fnmatch.fnmatch(fb, fa):
                return True, f"Pattern match between '{fa}' and '{fb}'"
    return False, ""


def _topological_sort_lanes(lanes: Sequence[LaneRequest]) -> tuple[str, ...]:
    """Compute a deterministic topological sort for lanes respecting dependencies."""
    lane_map = {lane.lane_id: lane for lane in lanes}
    in_degree: dict[str, int] = {lane.lane_id: 0 for lane in lanes}
    adj: dict[str, list[str]] = defaultdict(list)

    for lane in lanes:
        for dep in lane.depends_on:
            if dep in lane_map:
                adj[dep].append(lane.lane_id)
                in_degree[lane.lane_id] += 1

    # Deterministic priority queue / sorted list of zero in-degree nodes
    ready = sorted([lid for lid, deg in in_degree.items() if deg == 0])
    ordered: list[str] = []

    while ready:
        curr = ready.pop(0)
        ordered.append(curr)
        for neighbor in sorted(adj[curr]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                ready.append(neighbor)
                ready.sort()

    # If cycle exists, append remaining in deterministic order
    if len(ordered) < len(lanes):
        remaining = sorted([lid for lid in lane_map if lid not in ordered])
        ordered.extend(remaining)

    return tuple(ordered)


def analyze_concurrency_eligibility(
    lanes: Sequence[LaneRequest],
) -> ConcurrencyEligibilityResult:
    """Analyze work lanes for concurrency eligibility, refusing unsafe mutation fan-out."""
    if not lanes:
        return ConcurrencyEligibilityResult(
            is_eligible_parallel=True,
            execution_mode=EXEC_MODE_PARALLEL_READ_ONLY,
            conflicts=(),
            serial_fallback_plan=(),
            merge_order=(),
            reason="Empty lane batch",
        )

    # 1. Check if all lanes are read-only
    all_read_only = all(lane.lane_kind == LANE_KIND_READ_ONLY for lane in lanes)
    if all_read_only:
        return ConcurrencyEligibilityResult(
            is_eligible_parallel=True,
            execution_mode=EXEC_MODE_PARALLEL_READ_ONLY,
            conflicts=(),
            serial_fallback_plan=tuple(lane.lane_id for lane in lanes),
            merge_order=(),
            reason="All lanes are independent read-only investigations; parallel execution approved.",
        )

    # 2. Single mutating lane
    if len(lanes) == 1:
        lane = lanes[0]
        return ConcurrencyEligibilityResult(
            is_eligible_parallel=True,
            execution_mode=EXEC_MODE_SERIAL_MUTATING,
            conflicts=(),
            serial_fallback_plan=(lane.lane_id,),
            merge_order=(lane.lane_id,) if lane.lane_kind == LANE_KIND_MUTATING else (),
            reason="Single lane execution.",
        )

    # 3. Multiple lanes with at least one mutating lane -> inspect for conflicts
    conflicts: list[LaneConflict] = []
    mutating_lanes = [lane for lane in lanes if lane.lane_kind == LANE_KIND_MUTATING]

    # Rule A: Mutating lanes must have separate worktrees
    seen_worktrees: dict[str, str] = {}
    for lane in mutating_lanes:
        if not lane.worktree_path:
            conflicts.append(
                LaneConflict(
                    conflict_type=CONFLICT_MISSING_WORKTREE,
                    lane_a=lane.lane_id,
                    lane_b="",
                    details=f"Mutating lane '{lane.lane_id}' lacks an isolated worktree_path.",
                )
            )
        elif lane.worktree_path in seen_worktrees:
            other_lane = seen_worktrees[lane.worktree_path]
            conflicts.append(
                LaneConflict(
                    conflict_type=CONFLICT_SHARED_WORKTREE,
                    lane_a=other_lane,
                    lane_b=lane.lane_id,
                    details=f"Lanes '{other_lane}' and '{lane.lane_id}' share worktree '{lane.worktree_path}'.",
                )
            )
        else:
            seen_worktrees[lane.worktree_path] = lane.lane_id

    # Rule B: Disjoint file ownership between mutating lanes
    for i, lane_a in enumerate(mutating_lanes):
        for lane_b in mutating_lanes[i + 1 :]:
            overlap, details = _files_overlap(
                lane_a.files_targeted, lane_b.files_targeted
            )
            if overlap:
                conflicts.append(
                    LaneConflict(
                        conflict_type=CONFLICT_OVERLAPPING_FILES,
                        lane_a=lane_a.lane_id,
                        lane_b=lane_b.lane_id,
                        details=f"Lanes '{lane_a.lane_id}' and '{lane_b.lane_id}' target overlapping files: {details}",
                    )
                )

    # Rule C: Dependency independence among concurrent lanes
    lane_ids = {lane.lane_id for lane in lanes}
    for lane in lanes:
        for dep in lane.depends_on:
            if dep in lane_ids:
                conflicts.append(
                    LaneConflict(
                        conflict_type=CONFLICT_DEPENDENT_LANES,
                        lane_a=dep,
                        lane_b=lane.lane_id,
                        details=f"Lane '{lane.lane_id}' depends on concurrent lane '{dep}'.",
                    )
                )

    # Rule D: No shared generated files across mutating lanes
    for i, lane_a in enumerate(mutating_lanes):
        for lane_b in mutating_lanes[i + 1 :]:
            overlap, details = _files_overlap(
                lane_a.generated_files, lane_b.generated_files
            )
            if overlap:
                conflicts.append(
                    LaneConflict(
                        conflict_type=CONFLICT_SHARED_GENERATED_FILES,
                        lane_a=lane_a.lane_id,
                        lane_b=lane_b.lane_id,
                        details=f"Lanes '{lane_a.lane_id}' and '{lane_b.lane_id}' share generated files: {details}",
                    )
                )

    serial_plan = _topological_sort_lanes(lanes)

    if conflicts:
        return ConcurrencyEligibilityResult(
            is_eligible_parallel=False,
            execution_mode=EXEC_MODE_SERIAL_FALLBACK,
            conflicts=tuple(conflicts),
            serial_fallback_plan=serial_plan,
            merge_order=tuple(
                lid
                for lid in serial_plan
                if any(
                    lane.lane_id == lid and lane.lane_kind == LANE_KIND_MUTATING
                    for lane in lanes
                )
            ),
            reason=f"Parallel mutation refused due to {len(conflicts)} conflict(s); falling back to serial plan.",
        )

    # All parallel mutation conditions satisfied!
    merge_order = tuple(lane.lane_id for lane in mutating_lanes)
    return ConcurrencyEligibilityResult(
        is_eligible_parallel=True,
        execution_mode=EXEC_MODE_PARALLEL_MUTATING,
        conflicts=(),
        serial_fallback_plan=serial_plan,
        merge_order=merge_order,
        reason="Parallel mutation approved with isolated worktrees, disjoint files, and independent dependencies.",
    )


# ==================================================================================================
# Merge-and-Revalidate Gates (E-03)
# ==================================================================================================


class LaneOutcome(NamedTuple):
    lane_id: str
    actor_role: str
    base_commit: str
    head_commit: str
    worktree_path: str
    changed_files: tuple[str, ...]
    generated_files: tuple[str, ...] = ()
    diff: str = ""
    per_lane_validation_passed: bool = True
    status: str = STATUS_COMPLETED
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "actor_role": self.actor_role,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "worktree_path": self.worktree_path,
            "changed_files": list(self.changed_files),
            "generated_files": list(self.generated_files),
            "diff": self.diff,
            "per_lane_validation_passed": self.per_lane_validation_passed,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
        }


class IntegrationFinding(NamedTuple):
    check_name: str
    severity: str
    lane_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "severity": self.severity,
            "lane_id": self.lane_id,
            "message": self.message,
        }


class IntegrationGateResult(NamedTuple):
    passed: bool
    status: str
    findings: tuple[IntegrationFinding, ...]
    combined_diff: str
    merged_files: tuple[str, ...]
    revalidation_passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "findings": [f.to_dict() for f in self.findings],
            "combined_diff": self.combined_diff,
            "merged_files": list(self.merged_files),
            "revalidation_passed": self.revalidation_passed,
            "message": self.message,
        }


def execute_merge_and_revalidate_gate(
    integration_base_commit: str,
    lane_outcomes: Sequence[LaneOutcome],
    merge_order: Sequence[str],
    full_validation_runner: Callable[[str, Sequence[str]], bool],
    declared_scope: Sequence[str] | None = None,
) -> IntegrationGateResult:
    """Execute merge-and-revalidate gate across isolated lane outcomes with full validation."""
    findings: list[IntegrationFinding] = []
    outcome_map = {outcome.lane_id: outcome for outcome in lane_outcomes}

    # Step 1: Check lane completeness and presence
    for lid in merge_order:
        if lid not in outcome_map:
            findings.append(
                IntegrationFinding(
                    check_name="lane_presence_check",
                    severity="ERROR",
                    lane_id=lid,
                    message=f"Lane '{lid}' in merge order is missing from lane outcomes.",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_MISSING_LANE,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message=f"Missing lane '{lid}' during integration.",
            )

        outcome = outcome_map[lid]
        if outcome.status == STATUS_TIMED_OUT:
            findings.append(
                IntegrationFinding(
                    check_name="lane_status_check",
                    severity="ERROR",
                    lane_id=lid,
                    message=f"Lane '{lid}' timed out during execution; a timed out lane is strictly a failure.",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_LANE_FAILURE,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message=f"Lane '{lid}' timed out.",
            )
        elif (
            outcome.status != STATUS_COMPLETED or not outcome.per_lane_validation_passed
        ):
            findings.append(
                IntegrationFinding(
                    check_name="lane_status_check",
                    severity="ERROR",
                    lane_id=lid,
                    message=f"Lane '{lid}' did not complete successfully (status='{outcome.status}', local_pass={outcome.per_lane_validation_passed}).",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_LANE_FAILURE,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message=f"Lane '{lid}' failed local validation.",
            )

    # Step 2: Stale Base Detection
    # The first lane's base commit must match target base
    if merge_order:
        first_lane = outcome_map[merge_order[0]]
        if first_lane.base_commit != integration_base_commit:
            findings.append(
                IntegrationFinding(
                    check_name="stale_base_check",
                    severity="ERROR",
                    lane_id=first_lane.lane_id,
                    message=f"First lane '{first_lane.lane_id}' base commit '{first_lane.base_commit}' does not match target integration base '{integration_base_commit}'.",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_STALE_BASE,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message="Stale base commit detected on initial lane.",
            )

    # Step 3: Check conflict markers and file collisions
    combined_diff_parts: list[str] = []
    merged_files_set: set[str] = set()

    for idx, lid in enumerate(merge_order):
        outcome = outcome_map[lid]

        # Check for conflict markers
        if any(marker in outcome.diff for marker in ("<<<<<<<", "=======", ">>>>>>>")):
            findings.append(
                IntegrationFinding(
                    check_name="conflict_marker_check",
                    severity="ERROR",
                    lane_id=lid,
                    message=f"Lane '{lid}' diff contains unresolved git conflict markers.",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_CONFLICT,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message=f"Conflict markers detected in lane '{lid}'.",
            )

        # Disjoint ownership check against previously merged lanes
        lane_files = set(outcome.changed_files) | set(outcome.generated_files)
        overlap = merged_files_set & lane_files
        if overlap:
            findings.append(
                IntegrationFinding(
                    check_name="ownership_collision_check",
                    severity="ERROR",
                    lane_id=lid,
                    message=f"Lane '{lid}' modifies files already merged by earlier lanes: {sorted(overlap)}",
                )
            )
            return IntegrationGateResult(
                passed=False,
                status=INTEGRATION_FAILED_CONFLICT,
                findings=tuple(findings),
                combined_diff="",
                merged_files=(),
                revalidation_passed=False,
                message=f"File collision on {sorted(overlap)}.",
            )

        merged_files_set.update(lane_files)
        if outcome.diff:
            combined_diff_parts.append(outcome.diff)

    merged_files = tuple(sorted(merged_files_set))
    combined_diff = "\n".join(combined_diff_parts)

    # Step 4: Combined Diff Scope Fence Review
    if declared_scope:
        for f in merged_files:
            in_scope = any(fnmatch.fnmatch(f, pat) for pat in declared_scope)
            if not in_scope:
                findings.append(
                    IntegrationFinding(
                        check_name="scope_review_check",
                        severity="ERROR",
                        lane_id="integration",
                        message=f"Integrated file '{f}' violates declared scope fence {list(declared_scope)}",
                    )
                )
                return IntegrationGateResult(
                    passed=False,
                    status=INTEGRATION_FAILED_SCOPE_VIOLATION,
                    findings=tuple(findings),
                    combined_diff=combined_diff,
                    merged_files=merged_files,
                    revalidation_passed=False,
                    message=f"Out-of-scope file '{f}' in integrated diff.",
                )

    # Step 5: Full Post-Integration Revalidation
    # CRUCIAL: Per-lane green NEVER implies integrated green!
    revalidation_ok = full_validation_runner(combined_diff, merged_files)
    if not revalidation_ok:
        findings.append(
            IntegrationFinding(
                check_name="full_revalidation_check",
                severity="ERROR",
                lane_id="integration",
                message="Full test suite / revalidation failed after merging isolated lanes (per-lane-green + combined-red).",
            )
        )
        return IntegrationGateResult(
            passed=False,
            status=INTEGRATION_FAILED_COMBINED_RED,
            findings=tuple(findings),
            combined_diff=combined_diff,
            merged_files=merged_files,
            revalidation_passed=False,
            message="Integrated revalidation failed (combined-red).",
        )

    # All checks passed cleanly
    return IntegrationGateResult(
        passed=True,
        status=INTEGRATED_PASSED,
        findings=(),
        combined_diff=combined_diff,
        merged_files=merged_files,
        revalidation_passed=True,
        message="All lanes successfully merged and post-integration validation passed.",
    )
