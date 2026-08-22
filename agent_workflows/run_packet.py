"""Bounded just-in-time step-packet rendering and structured outcome envelopes.

awoptimize Order 06 (`ptsfjn`) E-01, E-02.

Releases only bounded, just-in-time work for the currently released step and accepts
only structured, evidence-linked outcome envelopes, preventing attention degradation,
context loss, and false completion.

Key capabilities:
  * E-01: Render bounded JIT step packets carrying immutable run metadata, current requirements,
          scope fence, allowed tools/files, exact action, expected artifacts, evidence contract,
          stop conditions, dependencies, exit checklist, source-to-requirement trace, and a deterministic
          packet digest, bounded strictly by a size budget.
  * E-02: Structured outcome envelopes (performed | blocked | failed), artifact references,
          and captured evidence IDs. Unsupported prose is ignored and cannot mutate durable state;
          missing evidence IDs, wrong attempt numbers, or foreign actors are rejected.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import (
    Any,
    NamedTuple,
)

from agent_workflows import run_engine, run_freeze
from agent_workflows import run_ledger_schema as schema

# Default packet budget in bytes (16 KB)
DEFAULT_PACKET_BUDGET_BYTES: int = 16384

# Default allowed tools for step execution
DEFAULT_ALLOWED_TOOLS: tuple[str, ...] = (
    "run_command",
    "view_file",
    "replace_file_content",
    "write_to_file",
    "grep_search",
    "find_by_name",
    "list_dir",
)

_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.strip())


# ---- Exceptions ----------------------------------------------------------------------------------


class RunPacketError(Exception):
    """Base exception for step-packet and outcome-envelope errors."""


class PacketBudgetExceededError(RunPacketError):
    """Raised when a rendered step packet exceeds its size/token budget."""


class OutcomeEnvelopeError(RunPacketError):
    """Base exception for outcome envelope validation and application errors."""


class InvalidOutcomeEnvelopeError(OutcomeEnvelopeError):
    """Raised when an outcome envelope is malformed or missing required schema fields."""


class UnsupportedProseError(OutcomeEnvelopeError):
    """Raised when free-form model prose is submitted in lieu of a structured outcome envelope."""


class WrongAttemptError(OutcomeEnvelopeError):
    """Raised when an outcome envelope specifies an attempt number that does not match expected state."""


class ForeignActorError(OutcomeEnvelopeError):
    """Raised when an outcome envelope is authored by an unauthorized or foreign actor."""


class MissingEvidenceError(OutcomeEnvelopeError):
    """Raised when an outcome envelope claims 'performed' without required captured evidence IDs."""


# ---- Data Structures: Step Packet (E-01) ---------------------------------------------------------


class BoundRequirement(NamedTuple):
    id: str
    category: str
    text: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "text": self.text,
            "digest": self.digest,
        }


class StepPacket(NamedTuple):
    run_id: str
    workflow_id: str
    step_id: str
    attempt: int
    timestamp: str
    action: str
    bound_requirements: tuple[BoundRequirement, ...]
    scope_fence: dict[str, Any]
    allowed_tools: tuple[str, ...]
    allowed_files: tuple[str, ...]
    expected_artifacts: tuple[str, ...]
    evidence_contract: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    depends_on: tuple[str, ...]
    exit_checklist: tuple[str, ...]
    trace: dict[str, list[str]]
    packet_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "attempt": self.attempt,
            "timestamp": self.timestamp,
            "action": self.action,
            "bound_requirements": [r.to_dict() for r in self.bound_requirements],
            "scope_fence": dict(self.scope_fence),
            "allowed_tools": list(self.allowed_tools),
            "allowed_files": list(self.allowed_files),
            "expected_artifacts": list(self.expected_artifacts),
            "evidence_contract": list(self.evidence_contract),
            "stop_conditions": list(self.stop_conditions),
            "depends_on": list(self.depends_on),
            "exit_checklist": list(self.exit_checklist),
            "trace": {k: list(v) for k, v in self.trace.items()},
            "packet_digest": self.packet_digest,
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(
            self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False
        )

    def render_prompt(self) -> str:
        """Render a concise, ANSI-free, bounded markdown prompt for model execution."""
        lines: list[str] = [
            f"# Step Packet: {self.step_id} (Attempt {self.attempt})",
            "",
            "## Execution Context",
            f"- Run ID: `{self.run_id}`",
            f"- Workflow ID: `{self.workflow_id}`",
            f"- Step ID: `{self.step_id}`",
            f"- Packet Digest: `{self.packet_digest}`",
            f"- Timestamp: `{self.timestamp}`",
            "",
            "## Exact Action to Perform",
            self.action,
            "",
        ]

        if self.bound_requirements:
            lines.extend(["## Bound Requirements & Success Criteria"])
            for req in self.bound_requirements:
                lines.append(f"- **[{req.id}]** ({req.category}): {req.text}")
            lines.append("")

        if self.expected_artifacts:
            lines.extend(["## Expected Artifacts"])
            for art in self.expected_artifacts:
                lines.append(f"- `{art}`")
            lines.append("")

        if self.evidence_contract:
            lines.extend(["## Required Evidence Contract"])
            for ev in self.evidence_contract:
                lines.append(f"- Evidence Kind: `{ev}`")
            lines.append("")

        if self.allowed_tools or self.allowed_files:
            lines.extend(["## Allowed Scope & Tools"])
            if self.allowed_tools:
                lines.append(f"- Allowed Tools: {', '.join(self.allowed_tools)}")
            if self.allowed_files:
                lines.append(
                    f"- Allowed Files / Paths: {', '.join(self.allowed_files)}"
                )
            if self.scope_fence:
                for k, v in sorted(self.scope_fence.items()):
                    if k not in ("allowed_paths", "forbidden_paths"):
                        lines.append(f"- {k}: {v}")
            lines.append("")

        if self.stop_conditions:
            lines.extend(["## Stop Conditions"])
            for cond in self.stop_conditions:
                lines.append(f"- {cond}")
            lines.append("")

        if self.exit_checklist:
            lines.extend(["## Step Exit Checklist"])
            for item in self.exit_checklist:
                lines.append(f"- [ ] {item}")
            lines.append("")

        return "\n".join(lines)


def _compute_packet_digest(payload: Mapping[str, Any]) -> str:
    """Compute deterministic SHA-256 digest of packet payload excluding packet_digest field."""
    norm_dict = dict(payload)
    norm_dict.pop("packet_digest", None)
    encoded = json.dumps(
        norm_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_step_packet(
    workflow: Mapping[str, Any],
    step_id: str,
    run_id: str = "run-00000001",
    attempt: int = 1,
    *,
    timestamp: str | None = None,
    frozen_requirements: run_freeze.RequirementSet | None = None,
    budget_bytes: int = DEFAULT_PACKET_BUDGET_BYTES,
    allowed_tools: Sequence[str] | None = None,
) -> StepPacket:
    """Build a bounded, traceable JIT step packet for a specific step.

    Omits unrelated bulk workflow context, maps only current step requirements,
    binds scope fence, computes deterministic digest, and enforces size budget.
    """
    wf_dict: dict[str, Any] = {}
    if "workflow" in workflow and isinstance(workflow["workflow"], Mapping):
        wf_dict = dict(workflow["workflow"])
    else:
        wf_dict = dict(workflow)

    wf_id = str(wf_dict.get("id", "workflow"))
    steps = wf_dict.get("steps", [])
    perms = wf_dict.get("permissions", {})
    if not isinstance(perms, Mapping):
        perms = {}

    target_step: dict[str, Any] | None = None
    for s in steps:
        if isinstance(s, Mapping) and str(s.get("id")) == step_id:
            target_step = dict(s)
            break

    if target_step is None:
        raise KeyError(f"Step '{step_id}' not found in workflow '{wf_id}'")

    action = str(target_step.get("action", ""))
    satisfies = tuple(
        str(r) for r in target_step.get("satisfies", []) if isinstance(r, str)
    )
    depends_on = tuple(
        str(d) for d in target_step.get("depends_on", []) if isinstance(d, str)
    )
    evidence_contract = tuple(
        str(e) for e in target_step.get("evidence", []) if isinstance(e, str)
    )
    stop_conditions = tuple(
        str(c) for c in target_step.get("stop_conditions", []) if isinstance(c, str)
    )
    expected_artifacts = tuple(
        str(a) for a in target_step.get("expected_artifacts", []) if isinstance(a, str)
    )

    # Resolve scope fence and allowed files
    allowed_paths = tuple(
        str(p) for p in perms.get("allowed_paths", []) if isinstance(p, str)
    )
    forbidden_paths = tuple(
        str(p) for p in perms.get("forbidden_paths", []) if isinstance(p, str)
    )
    scope_fence: dict[str, Any] = {
        "mutation_boundary": str(wf_dict.get("mutation_boundary", "product")),
        "allowed_paths": list(allowed_paths),
        "forbidden_paths": list(forbidden_paths),
    }

    # Resolve bound requirements
    raw_reqs = wf_dict.get("requirements", [])
    raw_by_id = {
        str(r.get("id")): r for r in raw_reqs if isinstance(r, Mapping) and "id" in r
    }

    bound_reqs: list[BoundRequirement] = []
    trace_req_ids: list[str] = []

    # Map satisfies IDs to frozen items or raw requirement items
    frozen_by_id = (
        {item.id: item for item in frozen_requirements.items}
        if frozen_requirements
        else {}
    )
    frozen_must_items = (
        [item for item in frozen_requirements.items if item.category == "must"]
        if frozen_requirements
        else []
    )

    for idx, rid in enumerate(satisfies):
        if rid in frozen_by_id:
            item = frozen_by_id[rid]
            bound_reqs.append(
                BoundRequirement(
                    id=rid,
                    category=item.category,
                    text=item.text,
                    digest=item.digest,
                )
            )
            trace_req_ids.append(rid)
        elif raw_by_id.get(rid):
            rdata = raw_by_id[rid]
            r_text = str(rdata.get("text", rdata.get("description", rid)))
            # Check if there is a matching frozen item
            matched_frozen: run_freeze.FrozenItem | None = None
            if frozen_requirements:
                norm_target = _normalize(r_text)
                for f_item in frozen_requirements.items:
                    if _normalize(f_item.text) == norm_target:
                        matched_frozen = f_item
                        break
                if matched_frozen is None and idx < len(frozen_must_items):
                    matched_frozen = frozen_must_items[idx]

            if matched_frozen is not None:
                bound_reqs.append(
                    BoundRequirement(
                        id=rid,
                        category=matched_frozen.category,
                        text=matched_frozen.text,
                        digest=matched_frozen.digest,
                    )
                )
            else:
                r_digest = hashlib.sha256(r_text.encode("utf-8")).hexdigest()
                bound_reqs.append(
                    BoundRequirement(
                        id=rid,
                        category="must",
                        text=r_text,
                        digest=r_digest,
                    )
                )
            trace_req_ids.append(rid)
        elif frozen_requirements and idx < len(frozen_must_items):
            f_item = frozen_must_items[idx]
            bound_reqs.append(
                BoundRequirement(
                    id=rid,
                    category=f_item.category,
                    text=f_item.text,
                    digest=f_item.digest,
                )
            )
            trace_req_ids.append(rid)

    tools = tuple(allowed_tools) if allowed_tools is not None else DEFAULT_ALLOWED_TOOLS
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Construct exit checklist
    exit_checklist = [
        f"Execute action: {action}",
    ]
    if bound_reqs:
        exit_checklist.append(
            f"Satisfy bound requirements: {', '.join(r.id for r in bound_reqs)}"
        )
    if expected_artifacts:
        exit_checklist.append(
            f"Produce expected artifacts: {', '.join(expected_artifacts)}"
        )
    if evidence_contract:
        exit_checklist.append(
            f"Capture required evidence: {', '.join(evidence_contract)}"
        )
    exit_checklist.append("Adhere strictly to scope boundaries and stop conditions")

    trace = {step_id: sorted(trace_req_ids or list(satisfies))}

    # Prepare payload to compute digest
    payload_for_digest = {
        "run_id": run_id,
        "workflow_id": wf_id,
        "step_id": step_id,
        "attempt": attempt,
        "timestamp": ts,
        "action": action,
        "bound_requirements": [r.to_dict() for r in bound_reqs],
        "scope_fence": scope_fence,
        "allowed_tools": list(tools),
        "allowed_files": list(allowed_paths),
        "expected_artifacts": list(expected_artifacts),
        "evidence_contract": list(evidence_contract),
        "stop_conditions": list(stop_conditions),
        "depends_on": list(depends_on),
        "exit_checklist": exit_checklist,
        "trace": trace,
    }
    packet_digest = _compute_packet_digest(payload_for_digest)

    packet = StepPacket(
        run_id=run_id,
        workflow_id=wf_id,
        step_id=step_id,
        attempt=attempt,
        timestamp=ts,
        action=action,
        bound_requirements=tuple(bound_reqs),
        scope_fence=scope_fence,
        allowed_tools=tools,
        allowed_files=allowed_paths,
        expected_artifacts=expected_artifacts,
        evidence_contract=evidence_contract,
        stop_conditions=stop_conditions,
        depends_on=depends_on,
        exit_checklist=tuple(exit_checklist),
        trace=trace,
        packet_digest=packet_digest,
    )

    # Size budget validation
    rendered_json_bytes = len(packet.to_json().encode("utf-8"))
    rendered_prompt_bytes = len(packet.render_prompt().encode("utf-8"))
    max_rendered_bytes = max(rendered_json_bytes, rendered_prompt_bytes)

    if max_rendered_bytes > budget_bytes:
        raise PacketBudgetExceededError(
            f"Step packet for '{step_id}' size {max_rendered_bytes} bytes exceeds budget of {budget_bytes} bytes"
        )

    return packet


# ---- Data Structures: Outcome Envelope (E-02) ----------------------------------------------------


class OutcomeFinding(NamedTuple):
    code: str
    where: str
    message: str


class OutcomeValidationResult(NamedTuple):
    ok: bool
    findings: tuple[OutcomeFinding, ...]
    envelope: StepOutcomeEnvelope | None = None


class StepOutcomeEnvelope(NamedTuple):
    run_id: str
    step_id: str
    attempt: int
    status: str
    actor: str = "executor"
    evidence_ids: tuple[str, ...] = ()
    artifacts: tuple[dict[str, str], ...] = ()
    prose: str | None = None
    block_reason: str | None = None
    failure_reason: str | None = None
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "attempt": self.attempt,
            "status": self.status,
            "actor": self.actor,
            "evidence_ids": list(self.evidence_ids),
            "artifacts": [dict(a) for a in self.artifacts],
        }
        if self.prose:
            d["prose"] = self.prose
        if self.block_reason:
            d["block_reason"] = self.block_reason
        if self.failure_reason:
            d["failure_reason"] = self.failure_reason
        if self.timestamp:
            d["timestamp"] = self.timestamp
        return d


def validate_outcome_envelope(
    raw_envelope: Any,
    *,
    expected_run_id: str | None = None,
    expected_step_id: str | None = None,
    expected_attempt: int | None = None,
    required_evidence_kinds: Sequence[str] | None = None,
    authorized_actors: frozenset[str] = frozenset(
        ("executor", "coordinator", "runtime")
    ),
) -> OutcomeValidationResult:
    """Validate a step outcome envelope against schema rules and false-completion constraints."""
    findings: list[OutcomeFinding] = []

    if isinstance(raw_envelope, StepOutcomeEnvelope):
        raw_dict: dict[str, Any] = raw_envelope.to_dict()
    elif isinstance(raw_envelope, Mapping):
        raw_dict = dict(raw_envelope)
    else:
        # Plain text / unsupported prose
        return OutcomeValidationResult(
            False,
            (
                OutcomeFinding(
                    "OE-UNSUPPORTED-PROSE",
                    "",
                    "Outcome must be a structured StepOutcomeEnvelope mapping, got raw text or invalid object",
                ),
            ),
            None,
        )

    # Check for free-form prose alone
    if "status" not in raw_dict and (
        "prose" in raw_dict or "message" in raw_dict or "result" in raw_dict
    ):
        findings.append(
            OutcomeFinding(
                "OE-UNSUPPORTED-PROSE",
                "status",
                "Unsupported prose submitted without structured status field",
            )
        )
        return OutcomeValidationResult(False, tuple(findings), None)

    # Required fields
    for field in ("run_id", "step_id", "attempt", "status"):
        if field not in raw_dict:
            findings.append(
                OutcomeFinding(
                    "OE-INVALID-STRUCTURE",
                    field,
                    f"Missing required envelope field '{field}'",
                )
            )

    if findings:
        return OutcomeValidationResult(False, tuple(findings), None)

    run_id = str(raw_dict["run_id"])
    step_id = str(raw_dict["step_id"])
    attempt = raw_dict["attempt"]
    status = str(raw_dict["status"])
    actor = str(raw_dict.get("actor", "executor"))

    if not isinstance(attempt, int) or isinstance(attempt, bool):
        findings.append(
            OutcomeFinding(
                "OE-INVALID-STRUCTURE", "attempt", "attempt must be an integer"
            )
        )

    if status not in schema.ATTEMPT_STATES:
        findings.append(
            OutcomeFinding(
                "OE-INVALID-STATUS",
                "status",
                f"Status '{status}' must be one of {sorted(schema.ATTEMPT_STATES)}",
            )
        )

    if actor not in authorized_actors:
        findings.append(
            OutcomeFinding(
                "OE-FOREIGN-ACTOR",
                "actor",
                f"Actor '{actor}' is not authorized to author outcome (authorized: {sorted(authorized_actors)})",
            )
        )

    if expected_run_id is not None and run_id != expected_run_id:
        findings.append(
            OutcomeFinding(
                "OE-RUN-MISMATCH",
                "run_id",
                f"Outcome run_id '{run_id}' does not match expected '{expected_run_id}'",
            )
        )

    if expected_step_id is not None and step_id != expected_step_id:
        findings.append(
            OutcomeFinding(
                "OE-STEP-MISMATCH",
                "step_id",
                f"Outcome step_id '{step_id}' does not match expected '{expected_step_id}'",
            )
        )

    if expected_attempt is not None and attempt != expected_attempt:
        findings.append(
            OutcomeFinding(
                "OE-WRONG-ATTEMPT",
                "attempt",
                f"Outcome attempt '{attempt}' does not match expected '{expected_attempt}'",
            )
        )

    raw_ev_ids = raw_dict.get("evidence_ids", ())
    ev_ids: tuple[str, ...] = tuple(str(e) for e in raw_ev_ids if isinstance(e, str))

    if status == "performed" and required_evidence_kinds:
        if not ev_ids:
            findings.append(
                OutcomeFinding(
                    "OE-MISSING-EVIDENCE",
                    "evidence_ids",
                    f"Step '{step_id}' requires evidence kinds {list(required_evidence_kinds)}, but no evidence_ids were provided",
                )
            )

    raw_artifacts = raw_dict.get("artifacts", ())
    artifacts_list: list[dict[str, str]] = []
    if isinstance(raw_artifacts, (list, tuple)):
        for a in raw_artifacts:
            if isinstance(a, Mapping):
                artifacts_list.append({str(k): str(v) for k, v in a.items()})

    envelope = StepOutcomeEnvelope(
        run_id=run_id,
        step_id=step_id,
        attempt=attempt if isinstance(attempt, int) else 1,
        status=status,
        actor=actor,
        evidence_ids=ev_ids,
        artifacts=tuple(artifacts_list),
        prose=raw_dict.get("prose"),
        block_reason=raw_dict.get("block_reason"),
        failure_reason=raw_dict.get("failure_reason"),
        timestamp=raw_dict.get("timestamp"),
    )

    return OutcomeValidationResult(len(findings) == 0, tuple(findings), envelope)


def apply_outcome_envelope(
    engine: run_engine.RunEngine,
    raw_envelope: Any,
    *,
    required_evidence_kinds: Sequence[str] | None = None,
    authorized_actors: frozenset[str] = frozenset(
        ("executor", "coordinator", "runtime")
    ),
) -> run_engine.StepSnapshot:
    """Validate and apply an outcome envelope to the durable state engine.

    Fails closed on unsupported prose, wrong attempts, foreign actors, or missing evidence IDs.
    """
    # Peek at step to determine expected parameters
    target_step_id: str | None = None
    if isinstance(raw_envelope, StepOutcomeEnvelope):
        target_step_id = raw_envelope.step_id
    elif isinstance(raw_envelope, Mapping) and "step_id" in raw_envelope:
        target_step_id = str(raw_envelope["step_id"])

    expected_attempt: int | None = None
    if target_step_id is not None:
        try:
            snapshot = engine.reconstruct_state()
            step_snap = snapshot.steps.get(target_step_id)
            if step_snap is not None:
                # If step is already running, expected attempt is current attempts + 1 (or 1 if 0)
                expected_attempt = (
                    step_snap.attempts + 1 if step_snap.attempts > 0 else 1
                )
        except Exception:
            pass

    val_res = validate_outcome_envelope(
        raw_envelope,
        expected_run_id=engine.run_id,
        expected_step_id=target_step_id,
        expected_attempt=expected_attempt,
        required_evidence_kinds=required_evidence_kinds,
        authorized_actors=authorized_actors,
    )

    if not val_res.ok or val_res.envelope is None:
        first_finding = val_res.findings[0] if val_res.findings else None
        code = first_finding.code if first_finding else "OE-INVALID"
        msg = first_finding.message if first_finding else "Invalid outcome envelope"

        if code == "OE-UNSUPPORTED-PROSE":
            raise UnsupportedProseError(msg)
        elif code == "OE-FOREIGN-ACTOR":
            raise ForeignActorError(msg)
        elif code == "OE-WRONG-ATTEMPT":
            raise WrongAttemptError(msg)
        elif code == "OE-MISSING-EVIDENCE":
            raise MissingEvidenceError(msg)
        else:
            raise InvalidOutcomeEnvelopeError(msg)

    envelope = val_res.envelope

    # Record attempt on single-writer engine (record_step_attempt manages its own store lock)
    snapshot = engine.record_step_attempt(
        step_id=envelope.step_id,
        state=envelope.status,
        actor=envelope.actor,
        attempt=envelope.attempt,
    )

    # Record any produced artifacts
    for art in envelope.artifacts:
        art_path = art.get("path")
        art_sha = art.get("sha256")
        if art_path and art_sha:
            engine.store.append(
                {
                    "schema_version": schema.LEDGER_SCHEMA_VERSION,
                    "kind": "artifact_ref",
                    "run_id": engine.run_id,
                    "actor": envelope.actor,
                    "parent": "",
                    "path": art_path,
                    "sha256": art_sha,
                }
            )

    return snapshot
