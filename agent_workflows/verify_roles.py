"""Verifier roles, clean verifier packet procedures, and corrective routing.

awoptimize Order 08 (`5hu6bd`) E-01..E-04.

This module establishes independent verification as an architectural ROLE with least
privilege and fresh, primary-artifact evidence:
  * E-01: Role contracts (coordinator, executor, investigator, verifier, corrector, human, runtime)
          with explicit inputs, outputs, permissions, state authority, and forbidden actions.
          Enforces that the executor and corrector cannot verify their own work, the verifier cannot
          mutate product code, and only the coordinator holds terminal completion authority.
  * E-02: Clean verifier packet builder containing frozen requirements, base/head commit identity,
          actual diff, untracked inventory, raw evidence manifest, declared scope, test diff,
          prior attempts, and verification rubric, while strictly EXCLUDING executor conclusion prose.
  * E-03: Requirement-by-requirement verification procedures: requirement inspection, scope audit,
          symbol-wiring check, negative cases check, test falsifiability check, targeted + full suite
          checks, artifact presence check, residual search, and evidence validation.
  * E-04: Corrective routing: every verifier finding produces either a bounded in-scope correction
          or an explicit pending corrective-IPD artifact, preserving the original failure immutably
          and rerunning all invalidated checks before completion.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
import fnmatch
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

from agent_workflows import run_ledger_schema as schema

# ==================================================================================================
# Constants & Vocabularies (E-01)
# ==================================================================================================

ROLE_COORDINATOR: str = "coordinator"
ROLE_EXECUTOR: str = "executor"
ROLE_INVESTIGATOR: str = "investigator"
ROLE_VERIFIER: str = "verifier"
ROLE_CORRECTOR: str = "corrector"
ROLE_HUMAN: str = "human"
ROLE_RUNTIME: str = "runtime"

ALL_ROLES: frozenset[str] = frozenset(
    (
        ROLE_COORDINATOR,
        ROLE_EXECUTOR,
        ROLE_INVESTIGATOR,
        ROLE_VERIFIER,
        ROLE_CORRECTOR,
        ROLE_HUMAN,
        ROLE_RUNTIME,
    )
)

# Verification Procedure Names (E-03)
PROC_REQUIREMENT_INSPECTION: str = "inspect_requirements"
PROC_SCOPE_AUDIT: str = "scope_audit"
PROC_SYMBOL_WIRING: str = "symbol_wiring"
PROC_NEGATIVE_CASES: str = "negative_cases"
PROC_TEST_FALSIFIABILITY: str = "test_falsifiability"
PROC_TARGETED_AND_FULL_CHECKS: str = "targeted_and_full_checks"
PROC_ARTIFACT_PRESENCE: str = "artifact_presence"
PROC_RESIDUAL_SEARCH: str = "residual_search"
PROC_EVIDENCE_VALIDATION: str = "evidence_validation"

ALL_PROCEDURES: tuple[str, ...] = (
    PROC_REQUIREMENT_INSPECTION,
    PROC_SCOPE_AUDIT,
    PROC_SYMBOL_WIRING,
    PROC_NEGATIVE_CASES,
    PROC_TEST_FALSIFIABILITY,
    PROC_TARGETED_AND_FULL_CHECKS,
    PROC_ARTIFACT_PRESENCE,
    PROC_RESIDUAL_SEARCH,
    PROC_EVIDENCE_VALIDATION,
)

# Result Vocabulary (mirrors schema.VERIFIER_RESULTS)
RESULT_SATISFIED: str = "satisfied"
RESULT_PARTIAL: str = "partial"
RESULT_FAILED: str = "failed"
RESULT_NOT_VERIFIABLE: str = "not_verifiable"

VERIFIER_RESULTS: frozenset[str] = frozenset(
    (RESULT_SATISFIED, RESULT_PARTIAL, RESULT_FAILED, RESULT_NOT_VERIFIABLE)
)

# Corrective Routing Kinds (E-04)
ROUTING_IN_SCOPE_CORRECTION: str = "in_scope_correction"
ROUTING_CORRECTIVE_IPD: str = "corrective_ipd"

# ==================================================================================================
# Exceptions
# ==================================================================================================


class VerifyRolesError(Exception):
    """Base exception for verifier roles, packets, procedures, and corrective routing."""


class RolePermissionError(VerifyRolesError):
    """Raised when an actor attempts an unauthorized action for their role."""


class ForbiddenActionError(RolePermissionError):
    """Raised when an actor attempts an explicitly forbidden role action."""


class ProductMutationForbiddenError(ForbiddenActionError):
    """Raised when a verifier, coordinator, or investigator attempts to mutate product code."""


class SelfVerificationForbiddenError(ForbiddenActionError):
    """Raised when an executor or corrector attempts to verify their own work."""


class TerminalAuthorityError(ForbiddenActionError):
    """Raised when an unauthorized role attempts a terminal lifecycle transition."""


class VerifierPacketError(VerifyRolesError):
    """Base exception for verifier packet builder and validation errors."""


class MismatchedIdentityError(VerifierPacketError):
    """Raised when base/head commit identity or worktree does not match expected state."""


class MissingPacketFieldError(VerifierPacketError):
    """Raised when a required primary artifact or field is missing from the verifier packet."""


class ExecutorProseLeakError(VerifierPacketError):
    """Raised when executor conclusion prose leaks into the clean verifier packet."""


class VerificationProcedureError(VerifyRolesError):
    """Base exception for verification procedure failures."""


class CorrectiveRoutingError(VerifyRolesError):
    """Base exception for corrective routing errors."""


# ==================================================================================================
# Data Structures: Roles & Permissions (E-01)
# ==================================================================================================


class RoleContract(NamedTuple):
    role: str
    description: str
    allowed_inputs: tuple[str, ...]
    allowed_outputs: tuple[str, ...]
    allowed_actions: frozenset[str]
    state_authority: frozenset[str]
    forbidden_actions: frozenset[str]
    can_mutate_product_code: bool
    can_mutate_test_code: bool
    can_author_step_attempt: bool
    can_author_verifier_decision: bool
    can_author_terminal_transaction: bool
    can_release_steps: bool
    can_record_human_approval: bool
    can_author_correction: bool
    can_execute_commands: bool
    can_read_workspace: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "description": self.description,
            "allowed_inputs": list(self.allowed_inputs),
            "allowed_outputs": list(self.allowed_outputs),
            "allowed_actions": sorted(self.allowed_actions),
            "state_authority": sorted(self.state_authority),
            "forbidden_actions": sorted(self.forbidden_actions),
            "can_mutate_product_code": self.can_mutate_product_code,
            "can_mutate_test_code": self.can_mutate_test_code,
            "can_author_step_attempt": self.can_author_step_attempt,
            "can_author_verifier_decision": self.can_author_verifier_decision,
            "can_author_terminal_transaction": self.can_author_terminal_transaction,
            "can_release_steps": self.can_release_steps,
            "can_record_human_approval": self.can_record_human_approval,
            "can_author_correction": self.can_author_correction,
            "can_execute_commands": self.can_execute_commands,
            "can_read_workspace": self.can_read_workspace,
        }


# Explicit Role Contracts Definition (E-01)
ROLE_CONTRACTS: dict[str, RoleContract] = {
    ROLE_COORDINATOR: RoleContract(
        role=ROLE_COORDINATOR,
        description=(
            "Orchestrates execution, releases step packets, manages run lifecycle, "
            "authors terminal transactions, and records human approvals."
        ),
        allowed_inputs=(
            "run_plan",
            "step_outcomes",
            "verifier_reports",
            "human_decisions",
        ),
        allowed_outputs=(
            "step_packets",
            "run_state_transitions",
            "terminal_transactions",
        ),
        allowed_actions=frozenset(
            (
                "release_step",
                "apply_outcome",
                "author_terminal_transaction",
                "record_human_approval",
                "read_workspace",
                "read_ledger",
            )
        ),
        state_authority=frozenset(
            (
                "pending -> runnable",
                "runnable -> running",
                "running -> performed",
                "running -> blocked",
                "running -> failed",
                "verified -> complete",
                "* -> cancelled",
            )
        ),
        forbidden_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "author_verifier_decision",
                "self_verify",
                "bypass_human_gate",
                "execute_mutating_tool",
            )
        ),
        can_mutate_product_code=False,
        can_mutate_test_code=False,
        can_author_step_attempt=False,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=True,
        can_release_steps=True,
        can_record_human_approval=True,
        can_author_correction=False,
        can_execute_commands=False,
        can_read_workspace=True,
    ),
    ROLE_EXECUTOR: RoleContract(
        role=ROLE_EXECUTOR,
        description=(
            "Executes released step packets and attempts work within scope fence."
        ),
        allowed_inputs=("step_packet", "workspace_files", "frozen_requirements"),
        allowed_outputs=("step_outcome_envelope", "tool_events", "artifact_refs"),
        allowed_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "execute_commands",
                "author_step_attempt",
                "read_workspace",
                "emit_artifacts",
            )
        ),
        state_authority=frozenset(
            (
                "running -> performed",
                "running -> blocked",
                "running -> failed",
            )
        ),
        forbidden_actions=frozenset(
            (
                "author_verifier_decision",
                "self_verify",
                "author_terminal_transaction",
                "release_steps",
                "record_human_approval",
                "synthesize_human_consent",
                "bypass_scope_fence",
            )
        ),
        can_mutate_product_code=True,
        can_mutate_test_code=True,
        can_author_step_attempt=True,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=False,
        can_release_steps=False,
        can_record_human_approval=False,
        can_author_correction=False,
        can_execute_commands=True,
        can_read_workspace=True,
    ),
    ROLE_INVESTIGATOR: RoleContract(
        role=ROLE_INVESTIGATOR,
        description=(
            "Read-only investigator for diagnostics, audits, codebase searches, and inspection."
        ),
        allowed_inputs=("read_only_request", "workspace_files", "ledger_records"),
        allowed_outputs=("inspection_report", "evidence_envelope"),
        allowed_actions=frozenset(
            (
                "read_workspace",
                "read_ledger",
                "execute_read_only_commands",
                "author_evidence_envelope",
            )
        ),
        state_authority=frozenset(),
        forbidden_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "author_step_attempt",
                "author_verifier_decision",
                "author_terminal_transaction",
                "release_steps",
                "author_correction",
            )
        ),
        can_mutate_product_code=False,
        can_mutate_test_code=False,
        can_author_step_attempt=False,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=False,
        can_release_steps=False,
        can_record_human_approval=False,
        can_author_correction=False,
        can_execute_commands=True,
        can_read_workspace=True,
    ),
    ROLE_VERIFIER: RoleContract(
        role=ROLE_VERIFIER,
        description=(
            "Independent verifier evaluating primary-artifact evidence in clean packet."
        ),
        allowed_inputs=(
            "clean_verifier_packet",
            "raw_evidence_manifest",
            "primary_artifacts",
        ),
        allowed_outputs=(
            "verifier_decision",
            "verification_report",
            "procedure_results",
        ),
        allowed_actions=frozenset(
            (
                "author_verifier_decision",
                "read_workspace",
                "read_evidence",
                "execute_read_only_checks",
                "author_verification_report",
            )
        ),
        state_authority=frozenset(
            (
                "performed -> verifying",
                "verifying -> verified",
                "verifying -> correction_required",
            )
        ),
        forbidden_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "self_verify",
                "author_terminal_transaction",
                "release_steps",
                "author_step_attempt",
                "author_correction",
                "synthesize_evidence",
            )
        ),
        can_mutate_product_code=False,
        can_mutate_test_code=False,
        can_author_step_attempt=False,
        can_author_verifier_decision=True,
        can_author_terminal_transaction=False,
        can_release_steps=False,
        can_record_human_approval=False,
        can_author_correction=False,
        can_execute_commands=True,
        can_read_workspace=True,
    ),
    ROLE_CORRECTOR: RoleContract(
        role=ROLE_CORRECTOR,
        description=(
            "Applies bounded in-scope corrections following verifier findings."
        ),
        allowed_inputs=(
            "verifier_finding",
            "bounded_correction",
            "failed_requirements",
        ),
        allowed_outputs=(
            "correction_record",
            "corrective_step_outcome",
            "updated_diff",
        ),
        allowed_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "execute_commands",
                "author_correction",
                "author_step_attempt",
                "read_workspace",
            )
        ),
        state_authority=frozenset(
            (
                "correction_required -> runnable",
                "running -> performed",
            )
        ),
        forbidden_actions=frozenset(
            (
                "author_verifier_decision",
                "self_verify",
                "author_terminal_transaction",
                "release_steps",
                "record_human_approval",
                "bypass_scope_fence",
            )
        ),
        can_mutate_product_code=True,
        can_mutate_test_code=True,
        can_author_step_attempt=True,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=False,
        can_release_steps=False,
        can_record_human_approval=False,
        can_author_correction=True,
        can_execute_commands=True,
        can_read_workspace=True,
    ),
    ROLE_HUMAN: RoleContract(
        role=ROLE_HUMAN,
        description=("Human approver at review and decision gates."),
        allowed_inputs=("gate_prompt", "ipd_plan", "verification_report"),
        allowed_outputs=("human_approval", "gate_decision", "review_authorization"),
        allowed_actions=frozenset(
            (
                "record_human_approval",
                "author_terminal_transaction",
                "release_step",
                "read_workspace",
                "read_ledger",
            )
        ),
        state_authority=frozenset(
            (
                "pending -> runnable",
                "verified -> complete",
                "* -> cancelled",
            )
        ),
        forbidden_actions=frozenset(
            (
                "author_step_attempt",
                "author_verifier_decision",
                "synthesize_consent",
            )
        ),
        can_mutate_product_code=False,
        can_mutate_test_code=False,
        can_author_step_attempt=False,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=True,
        can_release_steps=True,
        can_record_human_approval=True,
        can_author_correction=False,
        can_execute_commands=False,
        can_read_workspace=True,
    ),
    ROLE_RUNTIME: RoleContract(
        role=ROLE_RUNTIME,
        description=("Deterministic workflow engine and single-writer ledger manager."),
        allowed_inputs=("ledger_event", "state_command", "packet_request"),
        allowed_outputs=("ledger_record", "run_state_snapshot", "packet_envelope"),
        allowed_actions=frozenset(
            (
                "release_step",
                "apply_outcome",
                "author_terminal_transaction",
                "read_workspace",
                "read_ledger",
                "author_step_attempt",
                "author_correction",
            )
        ),
        state_authority=frozenset(
            (
                "pending -> runnable",
                "runnable -> running",
                "running -> performed",
                "running -> blocked",
                "running -> failed",
                "performed -> verifying",
                "verifying -> verified",
                "verifying -> correction_required",
                "correction_required -> runnable",
                "verified -> complete",
                "* -> cancelled",
            )
        ),
        forbidden_actions=frozenset(
            (
                "mutate_product_code",
                "mutate_test_code",
                "author_verifier_decision",
                "self_verify",
            )
        ),
        can_mutate_product_code=False,
        can_mutate_test_code=False,
        can_author_step_attempt=True,
        can_author_verifier_decision=False,
        can_author_terminal_transaction=True,
        can_release_steps=True,
        can_record_human_approval=False,
        can_author_correction=True,
        can_execute_commands=True,
        can_read_workspace=True,
    ),
}


class RolePolicyResult(NamedTuple):
    allowed: bool
    actor: str
    action: str
    message: str


def get_role_contract(role: str) -> RoleContract:
    """Retrieve the explicit role contract for a given role."""
    if role not in ROLE_CONTRACTS:
        raise RolePermissionError(f"Unknown role '{role}'")
    return ROLE_CONTRACTS[role]


def check_role_action(actor_role: str, action: str, **kwargs: Any) -> RolePolicyResult:
    """Evaluate whether an actor role is permitted to perform a specified action."""
    if actor_role not in ROLE_CONTRACTS:
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Unknown actor role '{actor_role}'",
        )

    contract = ROLE_CONTRACTS[actor_role]

    # Check explicit forbidden actions
    if action in contract.forbidden_actions:
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Action '{action}' is explicitly forbidden for role '{actor_role}'",
        )

    # Specific role constraints
    if action == "mutate_product_code" and not contract.can_mutate_product_code:
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Role '{actor_role}' has least-privilege read-only status and cannot mutate product code",
        )

    if (
        action == "author_verifier_decision"
        and not contract.can_author_verifier_decision
    ):
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Only the 'verifier' role may author verifier decisions (RL-E032 violation by '{actor_role}')",
        )

    if action == "self_verify":
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Role '{actor_role}' cannot verify its own work",
        )

    if (
        action == "author_terminal_transaction"
        and not contract.can_author_terminal_transaction
    ):
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Role '{actor_role}' lacks terminal lifecycle authority (only coordinator/runtime/human)",
        )

    if action == "release_step" and not contract.can_release_steps:
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Role '{actor_role}' cannot release steps for execution",
        )

    if action not in contract.allowed_actions:
        return RolePolicyResult(
            allowed=False,
            actor=actor_role,
            action=action,
            message=f"Action '{action}' is not in allowed actions for role '{actor_role}'",
        )

    return RolePolicyResult(
        allowed=True,
        actor=actor_role,
        action=action,
        message=f"Action '{action}' permitted for role '{actor_role}'",
    )


def enforce_role_action(actor_role: str, action: str, **kwargs: Any) -> None:
    """Enforce role permissions, raising specific typed exceptions on refusal."""
    res = check_role_action(actor_role, action, **kwargs)
    if not res.allowed:
        if action == "mutate_product_code":
            raise ProductMutationForbiddenError(res.message)
        elif action in ("author_verifier_decision", "self_verify") and actor_role in (
            ROLE_EXECUTOR,
            ROLE_CORRECTOR,
        ):
            raise SelfVerificationForbiddenError(res.message)
        elif action == "author_terminal_transaction":
            raise TerminalAuthorityError(res.message)
        elif (
            action
            in ROLE_CONTRACTS.get(
                actor_role, ROLE_CONTRACTS[ROLE_EXECUTOR]
            ).forbidden_actions
        ):
            raise ForbiddenActionError(res.message)
        else:
            raise RolePermissionError(res.message)


def check_self_verification(
    verifier_role: str, author_role: str, requirement_id: str = ""
) -> None:
    """Refuse self-verification: an executor or corrector cannot act as verifier on own work."""
    if verifier_role != ROLE_VERIFIER:
        raise SelfVerificationForbiddenError(
            f"Verification must be performed by independent role '{ROLE_VERIFIER}', not '{verifier_role}'"
        )
    if author_role in (ROLE_EXECUTOR, ROLE_CORRECTOR) and verifier_role == author_role:
        req_msg = f" for requirement '{requirement_id}'" if requirement_id else ""
        raise SelfVerificationForbiddenError(
            f"Self-verification refused{req_msg}: actor '{author_role}' cannot verify its own work"
        )


def check_code_mutation_allowed(
    actor_role: str, file_path: str = "", is_product_code: bool = True
) -> None:
    """Refuse code mutation if actor role is not permitted (e.g. verifier mutating product code)."""
    contract = get_role_contract(actor_role)
    if is_product_code and not contract.can_mutate_product_code:
        raise ProductMutationForbiddenError(
            f"Role '{actor_role}' cannot mutate product code (attempted write to '{file_path}')"
        )
    if not is_product_code and not contract.can_mutate_test_code:
        raise RolePermissionError(
            f"Role '{actor_role}' cannot mutate test code (attempted write to '{file_path}')"
        )


# ==================================================================================================
# Data Structures: Clean Verifier Packet (E-02)
# ==================================================================================================


class VerifierPacket(NamedTuple):
    run_id: str
    workflow_id: str
    base_commit: str
    head_commit: str
    worktree_path: str
    frozen_requirements: dict[str, Any]
    declared_scope: dict[str, Any]
    actual_diff: str
    untracked_inventory: tuple[str, ...]
    test_diff: str
    raw_evidence_manifest: tuple[dict[str, Any], ...]
    prior_attempts: tuple[dict[str, Any], ...]
    verification_rubric: dict[str, Any]
    timestamp: str
    packet_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "worktree_path": self.worktree_path,
            "frozen_requirements": dict(self.frozen_requirements),
            "declared_scope": dict(self.declared_scope),
            "actual_diff": self.actual_diff,
            "untracked_inventory": list(self.untracked_inventory),
            "test_diff": self.test_diff,
            "raw_evidence_manifest": [dict(e) for e in self.raw_evidence_manifest],
            "prior_attempts": [dict(a) for a in self.prior_attempts],
            "verification_rubric": dict(self.verification_rubric),
            "timestamp": self.timestamp,
            "packet_digest": self.packet_digest,
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class PacketFinding(NamedTuple):
    code: str
    field: str
    message: str


class PacketValidationResult(NamedTuple):
    ok: bool
    findings: tuple[PacketFinding, ...]
    packet: VerifierPacket | None


def compute_verifier_packet_digest(payload: Mapping[str, Any]) -> str:
    """Compute deterministic SHA256 digest over verifier packet content (excluding packet_digest)."""
    canonical_dict = {
        "run_id": str(payload.get("run_id", "")),
        "workflow_id": str(payload.get("workflow_id", "")),
        "base_commit": str(payload.get("base_commit", "")),
        "head_commit": str(payload.get("head_commit", "")),
        "worktree_path": str(payload.get("worktree_path", "")),
        "frozen_requirements": payload.get("frozen_requirements", {}),
        "declared_scope": payload.get("declared_scope", {}),
        "actual_diff": str(payload.get("actual_diff", "")),
        "untracked_inventory": sorted(
            str(x) for x in payload.get("untracked_inventory", ())
        ),
        "test_diff": str(payload.get("test_diff", "")),
        "raw_evidence_manifest": payload.get("raw_evidence_manifest", []),
        "prior_attempts": payload.get("prior_attempts", []),
        "verification_rubric": payload.get("verification_rubric", {}),
        "timestamp": str(payload.get("timestamp", "")),
    }
    encoded = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


# Forbidden conclusion prose field names that must never leak into verifier packet
_FORBIDDEN_PROSE_KEYS: frozenset[str] = frozenset(
    (
        "prose",
        "conclusion",
        "conclusion_prose",
        "verdict",
        "narrative",
        "summary_prose",
        "audit_narrative",
        "self_audit",
        "executor_prose",
    )
)


def _strip_executor_prose(obj: Any) -> Any:
    """Recursively strip any executor narrative/conclusion prose from data structures."""
    if isinstance(obj, Mapping):
        cleaned: dict[str, Any] = {}
        for k, v in obj.items():
            if str(k).lower() in _FORBIDDEN_PROSE_KEYS:
                continue
            cleaned[str(k)] = _strip_executor_prose(v)
        return cleaned
    elif isinstance(obj, (list, tuple)):
        return [_strip_executor_prose(item) for item in obj]
    return obj


def _detect_executor_prose_leak(obj: Any, path: str = "") -> list[PacketFinding]:
    """Scan data structure to verify no executor conclusion prose leaked into the packet."""
    findings: list[PacketFinding] = []
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else str(k)
            if str(k).lower() in _FORBIDDEN_PROSE_KEYS and v not in (None, "", {}, []):
                findings.append(
                    PacketFinding(
                        "VP-PROSE-LEAK",
                        current_path,
                        f"Forbidden executor conclusion prose detected in field '{current_path}'",
                    )
                )
            findings.extend(_detect_executor_prose_leak(v, current_path))
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            findings.extend(_detect_executor_prose_leak(item, f"{path}[{idx}]"))
    return findings


def build_verifier_packet(
    run_id: str,
    workflow_id: str,
    base_commit: str,
    head_commit: str,
    worktree_path: str,
    frozen_requirements: Mapping[str, Any] | Sequence[Any],
    declared_scope: Mapping[str, Any],
    actual_diff: str,
    untracked_inventory: Sequence[str] = (),
    test_diff: str = "",
    raw_evidence_manifest: Sequence[Mapping[str, Any]] = (),
    prior_attempts: Sequence[Mapping[str, Any]] = (),
    verification_rubric: Mapping[str, Any] | None = None,
    raw_step_outcomes: Sequence[Mapping[str, Any]] | None = None,
    timestamp: str | None = None,
) -> VerifierPacket:
    """Build a clean verifier packet containing primary artifacts and excluding executor conclusion prose."""
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Clean raw evidence manifest and prior attempts of any prose leaks
    cleaned_evidence = [_strip_executor_prose(e) for e in raw_evidence_manifest]
    cleaned_attempts = [_strip_executor_prose(a) for a in prior_attempts]

    # If raw step outcomes provided, extract factual attempt metadata and strip prose
    if raw_step_outcomes:
        for out in raw_step_outcomes:
            cleaned_attempts.append(
                {
                    "step_id": str(out.get("step_id", "")),
                    "attempt": out.get("attempt", 1),
                    "status": str(out.get("status", "")),
                    "actor": str(out.get("actor", "")),
                    "evidence_ids": list(out.get("evidence_ids", ())),
                }
            )

    # Normalize frozen requirements
    req_dict: dict[str, Any] = {}
    if isinstance(frozen_requirements, Mapping):
        req_dict = _strip_executor_prose(dict(frozen_requirements))
    elif hasattr(frozen_requirements, "to_dict"):
        req_dict = _strip_executor_prose(frozen_requirements.to_dict())  # type: ignore
    else:
        req_dict = {"requirements": _strip_executor_prose(list(frozen_requirements))}

    # Default verification rubric if omitted
    rubric = (
        dict(verification_rubric)
        if verification_rubric
        else {"procedures": list(ALL_PROCEDURES)}
    )

    payload: dict[str, Any] = {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "worktree_path": worktree_path,
        "frozen_requirements": req_dict,
        "declared_scope": _strip_executor_prose(dict(declared_scope)),
        "actual_diff": actual_diff,
        "untracked_inventory": tuple(sorted(untracked_inventory)),
        "test_diff": test_diff,
        "raw_evidence_manifest": tuple(cleaned_evidence),
        "prior_attempts": tuple(cleaned_attempts),
        "verification_rubric": rubric,
        "timestamp": ts,
    }

    digest = compute_verifier_packet_digest(payload)

    return VerifierPacket(
        run_id=run_id,
        workflow_id=workflow_id,
        base_commit=base_commit,
        head_commit=head_commit,
        worktree_path=worktree_path,
        frozen_requirements=req_dict,
        declared_scope=dict(declared_scope),
        actual_diff=actual_diff,
        untracked_inventory=tuple(sorted(untracked_inventory)),
        test_diff=test_diff,
        raw_evidence_manifest=tuple(cleaned_evidence),
        prior_attempts=tuple(cleaned_attempts),
        verification_rubric=rubric,
        timestamp=ts,
        packet_digest=digest,
    )


def validate_verifier_packet(raw_packet: Any) -> PacketValidationResult:
    """Validate a verifier packet's structural integrity, bindings, and prose exclusion."""
    findings: list[PacketFinding] = []

    if isinstance(raw_packet, VerifierPacket):
        raw_dict = raw_packet.to_dict()
    elif isinstance(raw_packet, Mapping):
        raw_dict = dict(raw_packet)
    else:
        return PacketValidationResult(
            False,
            (
                PacketFinding(
                    "VP-NOT-MAPPING",
                    "",
                    "Verifier packet must be a mapping or VerifierPacket",
                ),
            ),
            None,
        )

    # Validate required primary identity bindings
    run_id = raw_dict.get("run_id")
    if not run_id or not isinstance(run_id, str):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD", "run_id", "Missing or non-string 'run_id'"
            )
        )
    elif not schema.is_run_id(run_id):
        findings.append(
            PacketFinding(
                "VP-INVALID-IDENTITY", "run_id", f"Invalid run_id format '{run_id}'"
            )
        )

    base_commit = raw_dict.get("base_commit")
    if not base_commit or not isinstance(base_commit, str):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD", "base_commit", "Missing or empty 'base_commit'"
            )
        )

    head_commit = raw_dict.get("head_commit")
    if not head_commit or not isinstance(head_commit, str):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD", "head_commit", "Missing or empty 'head_commit'"
            )
        )

    worktree_path = raw_dict.get("worktree_path")
    if not worktree_path or not isinstance(worktree_path, str):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD", "worktree_path", "Missing or empty 'worktree_path'"
            )
        )

    # Frozen requirements check
    reqs = raw_dict.get("frozen_requirements")
    if not reqs or not isinstance(reqs, (Mapping, list, tuple)):
        findings.append(
            PacketFinding(
                "VP-EMPTY-REQUIREMENTS",
                "frozen_requirements",
                "Missing or empty 'frozen_requirements'",
            )
        )

    # Declared scope check
    scope = raw_dict.get("declared_scope")
    if not isinstance(scope, Mapping) or not scope:
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD",
                "declared_scope",
                "Missing or non-mapping 'declared_scope'",
            )
        )

    # Actual diff check
    if "actual_diff" not in raw_dict or not isinstance(
        raw_dict.get("actual_diff"), str
    ):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD",
                "actual_diff",
                "Missing or non-string 'actual_diff'",
            )
        )

    # Scan for forbidden prose leaks
    prose_leaks = _detect_executor_prose_leak(raw_dict)
    findings.extend(prose_leaks)

    # Check digest integrity
    given_digest = raw_dict.get("packet_digest")
    if not given_digest or not isinstance(given_digest, str):
        findings.append(
            PacketFinding(
                "VP-MISSING-FIELD", "packet_digest", "Missing 'packet_digest'"
            )
        )
    else:
        expected_digest = compute_verifier_packet_digest(raw_dict)
        if given_digest != expected_digest:
            findings.append(
                PacketFinding(
                    "VP-CORRUPTED-DIGEST",
                    "packet_digest",
                    f"Digest mismatch: given '{given_digest}' vs expected '{expected_digest}'",
                )
            )

    if findings:
        return PacketValidationResult(False, tuple(findings), None)

    packet = VerifierPacket(
        run_id=str(run_id),
        workflow_id=str(raw_dict.get("workflow_id", "")),
        base_commit=str(base_commit),
        head_commit=str(head_commit),
        worktree_path=str(worktree_path),
        frozen_requirements=dict(raw_dict.get("frozen_requirements", {})),
        declared_scope=dict(raw_dict.get("declared_scope", {})),
        actual_diff=str(raw_dict.get("actual_diff", "")),
        untracked_inventory=tuple(raw_dict.get("untracked_inventory", ())),
        test_diff=str(raw_dict.get("test_diff", "")),
        raw_evidence_manifest=tuple(
            dict(e) for e in raw_dict.get("raw_evidence_manifest", ())
        ),
        prior_attempts=tuple(dict(a) for a in raw_dict.get("prior_attempts", ())),
        verification_rubric=dict(raw_dict.get("verification_rubric", {})),
        timestamp=str(raw_dict.get("timestamp", "")),
        packet_digest=str(given_digest),
    )
    return PacketValidationResult(True, (), packet)


# ==================================================================================================
# Data Structures: Verification Procedures (E-03)
# ==================================================================================================


class ProcedureFinding(NamedTuple):
    code: str
    procedure: str
    requirement_id: str
    where: str
    message: str
    gap_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "procedure": self.procedure,
            "requirement_id": self.requirement_id,
            "where": self.where,
            "message": self.message,
            "gap_class": self.gap_class,
        }


class ProcedureResult(NamedTuple):
    procedure_name: str
    requirement_id: str
    result: str  # satisfied | partial | failed | not_verifiable
    evidence_ids: tuple[str, ...]
    findings: tuple[ProcedureFinding, ...]
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "procedure_name": self.procedure_name,
            "requirement_id": self.requirement_id,
            "result": self.result,
            "evidence_ids": list(self.evidence_ids),
            "findings": [f.to_dict() for f in self.findings],
            "details": self.details,
        }


class VerificationReport(NamedTuple):
    run_id: str
    packet_digest: str
    overall_result: str  # satisfied | partial | failed | not_verifiable
    procedure_results: tuple[ProcedureResult, ...]
    requirement_results: dict[str, str]
    evidence_map: dict[str, list[str]]
    is_verified: bool
    blocking_gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "packet_digest": self.packet_digest,
            "overall_result": self.overall_result,
            "procedure_results": [p.to_dict() for p in self.procedure_results],
            "requirement_results": dict(self.requirement_results),
            "evidence_map": {k: list(v) for k, v in self.evidence_map.items()},
            "is_verified": self.is_verified,
            "blocking_gaps": list(self.blocking_gaps),
        }

    def to_verifier_decisions(
        self,
        actor: str = ROLE_VERIFIER,
        base_seq: int = 0,
        timestamp: str | None = None,
        parent: str = "",
    ) -> list[dict[str, Any]]:
        """Convert per-requirement results into conforming ledger verifier_decision records."""
        enforce_role_action(actor, "author_verifier_decision")
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        records: list[dict[str, Any]] = []
        for idx, (req_id, res) in enumerate(sorted(self.requirement_results.items())):
            records.append(
                {
                    "schema_version": schema.LEDGER_SCHEMA_VERSION,
                    "kind": "verifier_decision",
                    "seq": base_seq + idx,
                    "run_id": self.run_id,
                    "actor": actor,
                    "timestamp": ts,
                    "parent": parent,
                    "requirement": req_id,
                    "result": res,
                }
            )
        return records


# ==================================================================================================
# Procedure Implementations (E-03)
# ==================================================================================================


def _extract_requirements_list(frozen_reqs: Any) -> list[dict[str, Any]]:
    """Extract flat list of requirement dictionaries from frozen requirement data."""
    if isinstance(frozen_reqs, Mapping):
        if "requirements" in frozen_reqs and isinstance(
            frozen_reqs["requirements"], (list, tuple)
        ):
            return [
                dict(r) for r in frozen_reqs["requirements"] if isinstance(r, Mapping)
            ]
        items: list[dict[str, Any]] = []
        for cat in ("must", "validation", "scope", "output"):
            raw_list = frozen_reqs.get(cat, [])
            if isinstance(raw_list, (list, tuple)):
                for idx, text in enumerate(raw_list):
                    prefix = (
                        "M"
                        if cat == "must"
                        else (
                            "V"
                            if cat == "validation"
                            else ("S" if cat == "scope" else "O")
                        )
                    )
                    items.append(
                        {
                            "id": f"{prefix}-{idx + 1:02d}",
                            "category": cat,
                            "text": str(text),
                        }
                    )
        return items
    elif isinstance(frozen_reqs, (list, tuple)):
        return [dict(r) for r in frozen_reqs if isinstance(r, Mapping)]
    return []


def procedure_inspect_requirements(
    packet: VerifierPacket,
    evidence_manifest: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[ProcedureResult, ...]:
    """Requirement-by-requirement inspection against primary evidence."""
    manifest = (
        packet.raw_evidence_manifest if evidence_manifest is None else evidence_manifest
    )
    reqs = _extract_requirements_list(packet.frozen_requirements)

    evidence_by_req: dict[str, list[dict[str, Any]]] = {}
    for ev in manifest:
        binds = ev.get("binds", ())
        if isinstance(binds, (list, tuple)):
            for b in binds:
                evidence_by_req.setdefault(str(b), []).append(dict(ev))

    results: list[ProcedureResult] = []
    for r in reqs:
        req_id = str(r.get("id", ""))
        matched_ev = evidence_by_req.get(req_id, [])
        ev_ids = tuple(
            str(e.get("evidence_id", e.get("id", f"ev-{idx}")))
            for idx, e in enumerate(matched_ev)
        )

        if not matched_ev:
            finding = ProcedureFinding(
                code="VP-REQ-MISSING-EVIDENCE",
                procedure=PROC_REQUIREMENT_INSPECTION,
                requirement_id=req_id,
                where="raw_evidence_manifest",
                message=f"Requirement '{req_id}' has no matching evidence envelopes in manifest",
                gap_class="missing_evidence",
            )
            results.append(
                ProcedureResult(
                    procedure_name=PROC_REQUIREMENT_INSPECTION,
                    requirement_id=req_id,
                    result=RESULT_FAILED,
                    evidence_ids=(),
                    findings=(finding,),
                    details=f"Requirement {req_id} failed: missing evidence",
                )
            )
            continue

        # Inspect evidence status
        has_failure = any(
            e.get("exit_code", 0) != 0 or e.get("status") == "failed"
            for e in matched_ev
        )
        has_partial = any(e.get("status") == "partial" for e in matched_ev)

        if has_failure:
            finding = ProcedureFinding(
                code="VP-REQ-EVIDENCE-FAILED",
                procedure=PROC_REQUIREMENT_INSPECTION,
                requirement_id=req_id,
                where="raw_evidence_manifest",
                message=f"Requirement '{req_id}' evidence contains failure exit code or status",
                gap_class="evidence_failure",
            )
            results.append(
                ProcedureResult(
                    procedure_name=PROC_REQUIREMENT_INSPECTION,
                    requirement_id=req_id,
                    result=RESULT_FAILED,
                    evidence_ids=ev_ids,
                    findings=(finding,),
                    details=f"Requirement {req_id} failed: evidence indicates failure",
                )
            )
        elif has_partial:
            results.append(
                ProcedureResult(
                    procedure_name=PROC_REQUIREMENT_INSPECTION,
                    requirement_id=req_id,
                    result=RESULT_PARTIAL,
                    evidence_ids=ev_ids,
                    findings=(),
                    details=f"Requirement {req_id} partially satisfied",
                )
            )
        else:
            results.append(
                ProcedureResult(
                    procedure_name=PROC_REQUIREMENT_INSPECTION,
                    requirement_id=req_id,
                    result=RESULT_SATISFIED,
                    evidence_ids=ev_ids,
                    findings=(),
                    details=f"Requirement {req_id} satisfied with {len(ev_ids)} evidence bindings",
                )
            )

    return tuple(results)


def _extract_diff_paths(diff_text: str) -> set[str]:
    """Extract touched file paths from standard unified diff text."""
    paths: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith(("+++ b/", "--- a/")):
            paths.add(line[6:].strip())
        elif line.startswith("diff --git a/"):
            parts = line.split()
            if len(parts) >= 4:
                b_path = parts[3]
                if b_path.startswith("b/"):
                    paths.add(b_path[2:])
    return paths


def procedure_scope_audit(packet: VerifierPacket) -> ProcedureResult:
    """Audit diff and untracked inventory strictly against declared scope fence."""
    scope = packet.declared_scope
    allowed_patterns = scope.get("allowed_paths", ["*"])
    forbidden_patterns = scope.get("forbidden_paths", [])

    diff_paths = _extract_diff_paths(packet.actual_diff)
    all_touched = set(diff_paths).union(set(packet.untracked_inventory))

    findings: list[ProcedureFinding] = []
    for path in sorted(all_touched):
        if not path or path == "/dev/null":
            continue

        # Check forbidden patterns
        for f_pat in forbidden_patterns:
            if fnmatch.fnmatch(path, f_pat):
                findings.append(
                    ProcedureFinding(
                        code="VP-SCOPE-FORBIDDEN-PATH",
                        procedure=PROC_SCOPE_AUDIT,
                        requirement_id="SCOPE",
                        where=path,
                        message=f"Touched path '{path}' matches forbidden scope pattern '{f_pat}'",
                        gap_class="scope_violation",
                    )
                )

        # Check allowed patterns
        is_allowed = any(fnmatch.fnmatch(path, a_pat) for a_pat in allowed_patterns)
        if not is_allowed and allowed_patterns != ["*"]:
            findings.append(
                ProcedureFinding(
                    code="VP-SCOPE-UNAUTHORIZED-PATH",
                    procedure=PROC_SCOPE_AUDIT,
                    requirement_id="SCOPE",
                    where=path,
                    message=f"Touched path '{path}' is outside declared allowed scope {allowed_patterns}",
                    gap_class="scope_violation",
                )
            )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_SCOPE_AUDIT,
            requirement_id="SCOPE",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details=f"Scope audit failed: {len(findings)} scope violations detected",
        )

    return ProcedureResult(
        procedure_name=PROC_SCOPE_AUDIT,
        requirement_id="SCOPE",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Scope audit satisfied: {len(all_touched)} touched files conform to scope fence",
    )


def procedure_symbol_wiring(
    packet: VerifierPacket,
    declared_symbols: Sequence[str] | None = None,
    codebase_content: Mapping[str, str] | None = None,
) -> ProcedureResult:
    """Verify that all new/changed symbols are actively wired into consumers and tests, not dead vocabulary."""
    symbols_to_check: list[str] = []
    if declared_symbols is not None:
        symbols_to_check.extend(declared_symbols)
    else:
        # Scan diff for class and def definitions
        for line in packet.actual_diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                match = re.search(r"^\+\s*(?:class|def)\s+([A-Za-z0-9_]+)", line)
                if match:
                    sym = match.group(1)
                    if not sym.startswith("_") or sym.startswith("__"):
                        symbols_to_check.append(sym)

    if not symbols_to_check:
        return ProcedureResult(
            procedure_name=PROC_SYMBOL_WIRING,
            requirement_id="SYMBOLS",
            result=RESULT_SATISFIED,
            evidence_ids=(),
            findings=(),
            details="Symbol wiring check satisfied: no declared or extracted symbols to check",
        )

    # Search for consumers in test diff, actual diff, or codebase content
    search_space = packet.actual_diff + "\n" + packet.test_diff
    if codebase_content:
        search_space += "\n" + "\n".join(codebase_content.values())

    findings: list[ProcedureFinding] = []
    for sym in set(symbols_to_check):
        # Match symbol references outside its own definition
        occurrences = len(re.findall(r"\b" + re.escape(sym) + r"\b", search_space))
        # A defined symbol must appear at least twice (definition + at least 1 consumer or test assertion)
        if occurrences < 2:
            findings.append(
                ProcedureFinding(
                    code="VP-SYMBOL-UNWIRED",
                    procedure=PROC_SYMBOL_WIRING,
                    requirement_id="SYMBOLS",
                    where=sym,
                    message=f"Symbol '{sym}' appears only in definition without active consumers or tests (dead vocabulary)",
                    gap_class="unwired_symbol",
                )
            )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_SYMBOL_WIRING,
            requirement_id="SYMBOLS",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details=f"Symbol wiring check failed: {len(findings)} unwired symbols detected",
        )

    return ProcedureResult(
        procedure_name=PROC_SYMBOL_WIRING,
        requirement_id="SYMBOLS",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Symbol wiring check satisfied: all {len(set(symbols_to_check))} symbols are actively wired",
    )


def procedure_negative_cases(
    packet: VerifierPacket,
    test_evidence: Sequence[Mapping[str, Any]] | None = None,
) -> ProcedureResult:
    """Verify that negative/failure test cases exist and assert proper rejection."""
    tests_text = packet.test_diff
    if test_evidence:
        tests_text += "\n" + "\n".join(str(e.get("content", "")) for e in test_evidence)

    # Look for negative assertion patterns (assertRaises, pytest.raises, status!=0, refused, etc.)
    negative_patterns = (
        r"assertRaises",
        r"pytest\.raises",
        r"assert\s+not\s+",
        r"assertFalse",
        r"exit_code\s*!=\s*0",
        r"returncode\s*!=\s*0",
        r"except\s+",
        r"raises\s+",
        r"Forbidden",
        r"Error",
    )

    matches = sum(len(re.findall(pat, tests_text)) for pat in negative_patterns)
    if matches == 0 and ("def test_" in tests_text or "class Test" in tests_text):
        finding = ProcedureFinding(
            code="VP-NEGATIVE-CASES-MISSING",
            procedure=PROC_NEGATIVE_CASES,
            requirement_id="TESTS",
            where="test_diff",
            message="Test suite lacks negative/failure test cases or exception assertions",
            gap_class="missing_negative_cases",
        )
        return ProcedureResult(
            procedure_name=PROC_NEGATIVE_CASES,
            requirement_id="TESTS",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=(finding,),
            details="Negative cases check failed: no negative/failure condition assertions found",
        )

    return ProcedureResult(
        procedure_name=PROC_NEGATIVE_CASES,
        requirement_id="TESTS",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Negative cases check satisfied: {matches} negative assertion patterns found",
    )


def procedure_test_falsifiability(
    packet: VerifierPacket,
    falsifiability_evidence: Sequence[Mapping[str, Any]] | None = None,
) -> ProcedureResult:
    """Verify that tests have proof of falsifiability (red-then-green evidence or negative test verification)."""
    manifest = (
        packet.raw_evidence_manifest
        if falsifiability_evidence is None
        else falsifiability_evidence
    )

    has_falsifiability_proof = False
    for ev in manifest:
        if ev.get("falsifiable") is True or ev.get("red_green_verified") is True:
            has_falsifiability_proof = True
            break
        # Check command output references to red-green runs
        if "RED" in str(ev.get("stdout", "")) and "GREEN" in str(ev.get("stdout", "")):
            has_falsifiability_proof = True
            break

    # If test diff contains negative tests or explicit falsifiability evidence is present, consider verified
    if not has_falsifiability_proof and not any(
        k in packet.test_diff for k in ("assertRaises", "pytest.raises")
    ):
        finding = ProcedureFinding(
            code="VP-FALSIFIABILITY-GAP",
            procedure=PROC_TEST_FALSIFIABILITY,
            requirement_id="TESTS",
            where="raw_evidence_manifest",
            message="No red-then-green or falsifiable test verification evidence found",
            gap_class="unfalsifiable_tests",
        )
        return ProcedureResult(
            procedure_name=PROC_TEST_FALSIFIABILITY,
            requirement_id="TESTS",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=(finding,),
            details="Test falsifiability check failed: missing proof that tests fail when broken",
        )

    return ProcedureResult(
        procedure_name=PROC_TEST_FALSIFIABILITY,
        requirement_id="TESTS",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details="Test falsifiability check satisfied",
    )


def procedure_targeted_and_full_checks(
    packet: VerifierPacket,
    test_runs: Sequence[Mapping[str, Any]] | None = None,
) -> ProcedureResult:
    """Verify that targeted tests AND canonical full suite (make test) ran green."""
    manifest = packet.raw_evidence_manifest if test_runs is None else test_runs

    has_targeted_green = False
    has_full_suite_green = False
    findings: list[ProcedureFinding] = []

    for ev in manifest:
        argv = ev.get("argv", [])
        exit_code = ev.get("exit_code", -1)
        argv_str = (
            " ".join(str(a) for a in argv)
            if isinstance(argv, (list, tuple))
            else str(argv)
        )

        if exit_code == 0:
            if "make test" in argv_str or ("pytest" in argv_str and "-n" in argv_str):
                has_full_suite_green = True
            elif "test" in argv_str or "pytest" in argv_str or "unittest" in argv_str:
                has_targeted_green = True

    # If full suite evidence is missing or not green
    if not has_full_suite_green:
        findings.append(
            ProcedureFinding(
                code="VP-FULL-SUITE-GAP",
                procedure=PROC_TARGETED_AND_FULL_CHECKS,
                requirement_id="FULL_SUITE",
                where="raw_evidence_manifest",
                message="Canonical full test suite (`make test`) evidence is missing or failed",
                gap_class="full_suite_gap",
            )
        )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_TARGETED_AND_FULL_CHECKS,
            requirement_id="FULL_SUITE",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details="Targeted and full checks failed: canonical full suite did not pass cleanly",
        )

    return ProcedureResult(
        procedure_name=PROC_TARGETED_AND_FULL_CHECKS,
        requirement_id="FULL_SUITE",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Targeted and full checks satisfied: canonical full test suite passed cleanly (targeted_verified={has_targeted_green})",
    )


def procedure_artifact_presence(
    packet: VerifierPacket,
    expected_artifacts: Sequence[str] | None = None,
    worktree_files: Mapping[str, str] | None = None,
) -> ProcedureResult:
    """Verify presence and validity of declared expected artifacts."""
    artifacts_to_check: list[str] = []
    if expected_artifacts is not None:
        artifacts_to_check.extend(expected_artifacts)
    else:
        # Check scope output or rubric expected artifacts
        rubric_arts = packet.verification_rubric.get("expected_artifacts", [])
        if isinstance(rubric_arts, (list, tuple)):
            artifacts_to_check.extend(str(a) for a in rubric_arts)

    if not artifacts_to_check:
        return ProcedureResult(
            procedure_name=PROC_ARTIFACT_PRESENCE,
            requirement_id="ARTIFACTS",
            result=RESULT_SATISFIED,
            evidence_ids=(),
            findings=(),
            details="Artifact presence check satisfied: no specific artifacts required",
        )

    findings: list[ProcedureFinding] = []
    diff_paths = _extract_diff_paths(packet.actual_diff)
    all_known_files = set(diff_paths).union(set(packet.untracked_inventory))
    if worktree_files:
        all_known_files.update(worktree_files.keys())

    for art in artifacts_to_check:
        if art not in all_known_files:
            findings.append(
                ProcedureFinding(
                    code="VP-ARTIFACT-MISSING",
                    procedure=PROC_ARTIFACT_PRESENCE,
                    requirement_id="ARTIFACTS",
                    where=art,
                    message=f"Required artifact '{art}' not found in diff or worktree inventory",
                    gap_class="missing_artifact",
                )
            )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_ARTIFACT_PRESENCE,
            requirement_id="ARTIFACTS",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details=f"Artifact presence check failed: {len(findings)} missing artifacts",
        )

    return ProcedureResult(
        procedure_name=PROC_ARTIFACT_PRESENCE,
        requirement_id="ARTIFACTS",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Artifact presence check satisfied: all {len(artifacts_to_check)} artifacts present",
    )


def procedure_residual_search(packet: VerifierPacket) -> ProcedureResult:
    """Scan diff and untracked inventory for residual debug/temporary markers."""
    residual_patterns = (
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\bDEBUG_ONLY\b",
        r"\bDO NOT COMMIT\b",
        r"\bTEMP_HACK\b",
        r"\bWIP_MARKER\b",
    )

    findings: list[ProcedureFinding] = []
    for line in packet.actual_diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for pat in residual_patterns:
                if re.search(pat, line):
                    findings.append(
                        ProcedureFinding(
                            code="VP-RESIDUAL-MARKER",
                            procedure=PROC_RESIDUAL_SEARCH,
                            requirement_id="RESIDUALS",
                            where=line[:80],
                            message=f"Residual marker matching '{pat}' found in diff addition: {line[:60]}",
                            gap_class="residual_marker",
                        )
                    )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_RESIDUAL_SEARCH,
            requirement_id="RESIDUALS",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details=f"Residual search failed: {len(findings)} residual markers found",
        )

    return ProcedureResult(
        procedure_name=PROC_RESIDUAL_SEARCH,
        requirement_id="RESIDUALS",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details="Residual search satisfied: no residual debug/temporary markers found",
    )


def procedure_evidence_validation(packet: VerifierPacket) -> ProcedureResult:
    """Validate all raw captured evidence envelopes for authenticity and consistency."""
    findings: list[ProcedureFinding] = []
    for idx, ev in enumerate(packet.raw_evidence_manifest):
        ev_id = str(ev.get("evidence_id", ev.get("id", f"ev-{idx}")))

        # Check commit head binding
        ev_head = ev.get("head")
        if ev_head and ev_head != packet.head_commit:
            findings.append(
                ProcedureFinding(
                    code="VP-EVIDENCE-HEAD-MISMATCH",
                    procedure=PROC_EVIDENCE_VALIDATION,
                    requirement_id="EVIDENCE",
                    where=ev_id,
                    message=f"Evidence '{ev_id}' head '{ev_head}' does not match packet head '{packet.head_commit}'",
                    gap_class="stale_evidence",
                )
            )

        # Check exit codes on claims of success
        if ev.get("status") == "success" and ev.get("exit_code", 0) != 0:
            findings.append(
                ProcedureFinding(
                    code="VP-EVIDENCE-FAILED-EXIT",
                    procedure=PROC_EVIDENCE_VALIDATION,
                    requirement_id="EVIDENCE",
                    where=ev_id,
                    message=f"Evidence '{ev_id}' claims success but has non-zero exit code {ev.get('exit_code')}",
                    gap_class="invalid_evidence",
                )
            )

    if findings:
        return ProcedureResult(
            procedure_name=PROC_EVIDENCE_VALIDATION,
            requirement_id="EVIDENCE",
            result=RESULT_FAILED,
            evidence_ids=(),
            findings=tuple(findings),
            details=f"Evidence validation failed: {len(findings)} invalid evidence envelopes",
        )

    return ProcedureResult(
        procedure_name=PROC_EVIDENCE_VALIDATION,
        requirement_id="EVIDENCE",
        result=RESULT_SATISFIED,
        evidence_ids=(),
        findings=(),
        details=f"Evidence validation satisfied: {len(packet.raw_evidence_manifest)} envelopes valid",
    )


def run_verification_procedures(
    packet: VerifierPacket,
    *,
    declared_symbols: Sequence[str] | None = None,
    expected_artifacts: Sequence[str] | None = None,
    codebase_content: Mapping[str, str] | None = None,
    worktree_files: Mapping[str, str] | None = None,
) -> VerificationReport:
    """Run all verification procedures and synthesize deterministic VerificationReport."""
    proc_results: list[ProcedureResult] = []

    # 1. Requirement inspection
    req_results = procedure_inspect_requirements(packet)
    proc_results.extend(req_results)

    # 2. Scope audit
    proc_results.append(procedure_scope_audit(packet))

    # 3. Symbol wiring
    proc_results.append(
        procedure_symbol_wiring(
            packet, declared_symbols=declared_symbols, codebase_content=codebase_content
        )
    )

    # 4. Negative cases
    proc_results.append(procedure_negative_cases(packet))

    # 5. Test falsifiability
    proc_results.append(procedure_test_falsifiability(packet))

    # 6. Targeted + full checks
    proc_results.append(procedure_targeted_and_full_checks(packet))

    # 7. Artifact presence
    proc_results.append(
        procedure_artifact_presence(
            packet, expected_artifacts=expected_artifacts, worktree_files=worktree_files
        )
    )

    # 8. Residual search
    proc_results.append(procedure_residual_search(packet))

    # 9. Evidence validation
    proc_results.append(procedure_evidence_validation(packet))

    # Map per-requirement results
    req_map: dict[str, str] = {}
    ev_map: dict[str, list[str]] = {}
    for pr in req_results:
        req_map[pr.requirement_id] = pr.result
        ev_map[pr.requirement_id] = list(pr.evidence_ids)

    # Aggregate blocking gaps
    blocking_gaps: list[str] = []
    has_failure = False
    has_partial = False

    for pr in proc_results:
        if pr.result == RESULT_FAILED:
            has_failure = True
            for f in pr.findings:
                blocking_gaps.append(
                    f"[{f.gap_class}] {f.procedure}:{f.where} - {f.message}"
                )
        elif pr.result == RESULT_PARTIAL:
            has_partial = True
            blocking_gaps.append(
                f"[partial] {pr.procedure}:{pr.requirement_id} - {pr.details}"
            )

    overall_res = (
        RESULT_FAILED
        if has_failure
        else (RESULT_PARTIAL if has_partial else RESULT_SATISFIED)
    )
    is_verified = overall_res == RESULT_SATISFIED

    return VerificationReport(
        run_id=packet.run_id,
        packet_digest=packet.packet_digest,
        overall_result=overall_res,
        procedure_results=tuple(proc_results),
        requirement_results=req_map,
        evidence_map=ev_map,
        is_verified=is_verified,
        blocking_gaps=tuple(blocking_gaps),
    )


# ==================================================================================================
# Data Structures & Logic: Corrective Routing (E-04)
# ==================================================================================================


class BoundedCorrection(NamedTuple):
    correction_id: str
    requirement_id: str
    gap_class: str
    finding_code: str
    description: str
    affected_files: tuple[str, ...]
    invalidated_evidence_ids: tuple[str, ...]
    invalidated_procedures: tuple[str, ...]
    target_role: str
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "correction_id": self.correction_id,
            "requirement_id": self.requirement_id,
            "gap_class": self.gap_class,
            "finding_code": self.finding_code,
            "description": self.description,
            "affected_files": list(self.affected_files),
            "invalidated_evidence_ids": list(self.invalidated_evidence_ids),
            "invalidated_procedures": list(self.invalidated_procedures),
            "target_role": self.target_role,
            "status": self.status,
            "created_at": self.created_at,
        }


class CorrectiveIPDArtifact(NamedTuple):
    artifact_id: str
    plan_id: str
    title: str
    gap_summary: str
    failed_requirements: tuple[str, ...]
    target_scope: dict[str, Any]
    status: str
    created_at: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "plan_id": self.plan_id,
            "title": self.title,
            "gap_summary": self.gap_summary,
            "failed_requirements": list(self.failed_requirements),
            "target_scope": dict(self.target_scope),
            "status": self.status,
            "created_at": self.created_at,
            "content": self.content,
        }


class CorrectiveRoutingResult(NamedTuple):
    run_id: str
    report_digest: str
    in_scope_corrections: tuple[BoundedCorrection, ...]
    corrective_artifacts: tuple[CorrectiveIPDArtifact, ...]
    invalidated_evidence_ids: tuple[str, ...]
    invalidated_procedures: tuple[str, ...]
    is_clean: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "report_digest": self.report_digest,
            "in_scope_corrections": [c.to_dict() for c in self.in_scope_corrections],
            "corrective_artifacts": [a.to_dict() for a in self.corrective_artifacts],
            "invalidated_evidence_ids": list(self.invalidated_evidence_ids),
            "invalidated_procedures": list(self.invalidated_procedures),
            "is_clean": self.is_clean,
        }


def _map_gap_to_procedures(gap_class: str) -> tuple[str, ...]:
    """Map a gap class to the procedures that are invalidated and must be rerun."""
    if gap_class == "unwired_symbol":
        return (PROC_SYMBOL_WIRING, PROC_TARGETED_AND_FULL_CHECKS)
    elif gap_class in ("missing_negative_cases", "unfalsifiable_tests"):
        return (
            PROC_NEGATIVE_CASES,
            PROC_TEST_FALSIFIABILITY,
            PROC_TARGETED_AND_FULL_CHECKS,
        )
    elif gap_class == "full_suite_gap":
        return (PROC_TARGETED_AND_FULL_CHECKS,)
    elif gap_class == "missing_artifact":
        return (PROC_ARTIFACT_PRESENCE, PROC_REQUIREMENT_INSPECTION)
    elif gap_class == "residual_marker":
        return (PROC_RESIDUAL_SEARCH,)
    elif gap_class == "scope_violation":
        return (PROC_SCOPE_AUDIT,)
    elif gap_class in (
        "missing_evidence",
        "evidence_failure",
        "invalid_evidence",
        "stale_evidence",
    ):
        return (
            PROC_REQUIREMENT_INSPECTION,
            PROC_EVIDENCE_VALIDATION,
            PROC_TARGETED_AND_FULL_CHECKS,
        )
    return (PROC_REQUIREMENT_INSPECTION, PROC_TARGETED_AND_FULL_CHECKS)


def route_verifier_findings(
    report: VerificationReport,
    packet: VerifierPacket,
    *,
    scope_fence: Mapping[str, Any] | None = None,
) -> CorrectiveRoutingResult:
    """Route all verifier findings to bounded in-scope corrections or corrective-IPD artifacts."""
    if report.is_verified:
        return CorrectiveRoutingResult(
            run_id=report.run_id,
            report_digest=report.packet_digest,
            in_scope_corrections=(),
            corrective_artifacts=(),
            invalidated_evidence_ids=(),
            invalidated_procedures=(),
            is_clean=True,
        )

    fence = packet.declared_scope if scope_fence is None else scope_fence
    allowed_paths = fence.get("allowed_paths", ["*"])

    in_scope_corrections: list[BoundedCorrection] = []
    corrective_artifacts: list[CorrectiveIPDArtifact] = []
    all_invalidated_ev: set[str] = set()
    all_invalidated_procs: set[str] = set()

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for pr in report.procedure_results:
        if pr.result == RESULT_SATISFIED:
            continue

        # Check findings
        if not pr.findings:
            # Synthetic finding if result is failed/partial without explicit findings
            f_code = f"VP-{pr.procedure_name.upper()}-GAP"
            f_gap = "procedure_gap"
            f_where = pr.requirement_id
            f_msg = pr.details
        else:
            first_f = pr.findings[0]
            f_code = first_f.code
            f_gap = first_f.gap_class
            f_where = first_f.where
            f_msg = first_f.message

        inv_procs = _map_gap_to_procedures(f_gap)
        all_invalidated_procs.update(inv_procs)
        all_invalidated_ev.update(pr.evidence_ids)

        # Determine if finding is in-scope or requires a corrective IPD artifact
        is_scope_violation = f_gap == "scope_violation"
        is_file_path = bool(
            f_where
            and (
                "/" in f_where
                or (len(f_where.split(".")) > 1 and not f_where.startswith("."))
            )
            and f_where != "raw_evidence_manifest"
        )
        out_of_scope = False
        if is_file_path and not is_scope_violation:
            out_of_scope = (
                not any(fnmatch.fnmatch(f_where, a) for a in allowed_paths)
                if allowed_paths != ["*"]
                else False
            )

        if is_scope_violation or out_of_scope:
            # Create explicit pending Corrective-IPD artifact
            art_id = f"corr-ipd-{hashlib.sha256((f_code + f_where + ts).encode()).hexdigest()[:8]}"
            content = (
                f"# Corrective IPD: Scope/Architectural Gap Resolution\n\n"
                f"- Plan ID: {packet.workflow_id}\n"
                f"- Run ID: {packet.run_id}\n"
                f"- Status: pending\n"
                f"- Gap Class: {f_gap}\n"
                f"- Finding Code: {f_code}\n\n"
                f"## Gap Summary\n{f_msg}\n\n"
                f"## Affected Location\n{f_where}\n"
            )
            corrective_artifacts.append(
                CorrectiveIPDArtifact(
                    artifact_id=art_id,
                    plan_id=packet.workflow_id,
                    title=f"Corrective Plan for {f_code} ({f_where})",
                    gap_summary=f_msg,
                    failed_requirements=(pr.requirement_id,),
                    target_scope=dict(fence),
                    status="pending",
                    created_at=ts,
                    content=content,
                )
            )
        else:
            # Create bounded in-scope correction for corrector role
            corr_id = f"corr-{hashlib.sha256((f_code + f_where + ts).encode()).hexdigest()[:8]}"
            in_scope_corrections.append(
                BoundedCorrection(
                    correction_id=corr_id,
                    requirement_id=pr.requirement_id,
                    gap_class=f_gap,
                    finding_code=f_code,
                    description=f_msg,
                    affected_files=(f_where,) if f_where and "." in f_where else (),
                    invalidated_evidence_ids=pr.evidence_ids,
                    invalidated_procedures=inv_procs,
                    target_role=ROLE_CORRECTOR,
                    status="pending",
                    created_at=ts,
                )
            )

    return CorrectiveRoutingResult(
        run_id=report.run_id,
        report_digest=report.packet_digest,
        in_scope_corrections=tuple(in_scope_corrections),
        corrective_artifacts=tuple(corrective_artifacts),
        invalidated_evidence_ids=tuple(sorted(all_invalidated_ev)),
        invalidated_procedures=tuple(sorted(all_invalidated_procs)),
        is_clean=False,
    )


def invalidate_evidence_on_correction(
    evidence_manifest: Sequence[Mapping[str, Any]],
    changed_files: Sequence[str],
    invalidated_evidence_ids: Sequence[str] = (),
) -> tuple[dict[str, Any], ...]:
    """Immutably mark linked evidence stale or invalidated following file modifications."""
    changed_set = set(changed_files)
    inv_ids_set = set(invalidated_evidence_ids)

    updated_manifest: list[dict[str, Any]] = []
    for idx, ev in enumerate(evidence_manifest):
        ev_copy = dict(ev)
        ev_id = str(ev.get("evidence_id", ev.get("id", f"ev-{idx}")))

        # Check explicit ID invalidation
        if ev_id in inv_ids_set:
            ev_copy["invalidated"] = True
            ev_copy["stale"] = True
            ev_copy["invalidation_reason"] = "explicit_verifier_invalidation"

        # Check touched file linkage
        bound_files = ev.get("bound_files", ev.get("files", ()))
        if isinstance(bound_files, (list, tuple)) and any(
            f in changed_set for f in bound_files
        ):
            ev_copy["invalidated"] = True
            ev_copy["stale"] = True
            ev_copy["invalidation_reason"] = "source_file_modified"

        updated_manifest.append(ev_copy)

    return tuple(updated_manifest)


def rerun_verification_after_correction(
    original_packet: VerifierPacket,
    prior_report: VerificationReport,
    correction: BoundedCorrection,
    updated_diff: str,
    fresh_evidence: Sequence[Mapping[str, Any]],
    **kwargs: Any,
) -> VerificationReport:
    """Rerun verification procedures following a correction, preserving original report immutably."""
    # Build updated verifier packet with fresh diff and fresh evidence
    new_packet = build_verifier_packet(
        run_id=original_packet.run_id,
        workflow_id=original_packet.workflow_id,
        base_commit=original_packet.base_commit,
        head_commit=original_packet.head_commit,
        worktree_path=original_packet.worktree_path,
        frozen_requirements=original_packet.frozen_requirements,
        declared_scope=original_packet.declared_scope,
        actual_diff=updated_diff,
        untracked_inventory=original_packet.untracked_inventory,
        test_diff=original_packet.test_diff,
        raw_evidence_manifest=fresh_evidence,
        prior_attempts=original_packet.prior_attempts,
        verification_rubric=original_packet.verification_rubric,
    )

    # Re-run procedures
    return run_verification_procedures(new_packet, **kwargs)
