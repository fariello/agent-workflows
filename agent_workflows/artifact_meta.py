"""The single metadata authority for artifacts: registry, event schema, replay, cache, legacy loader, and writes.

Spec 4sd62s Phase A Step 1 (IPD tve77h).

This module is the ONLY reader and writer of artifact metadata.
All read operations query the SQLite cache (.aw/state/index.db), which is brought up to date
via the two-check freshness check (directory membership and working-tree content digest)
before any query answers.
"""

from __future__ import annotations

import contextlib
import contextvars
import dataclasses
import datetime
from datetime import timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import time
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import attention_contract as _att
from agent_workflows import ipd_lifecycle as _ipd_life
from agent_workflows import ipd_schema as _ipd_schema
from agent_workflows import layout as _layout
from agent_workflows import leak_sanitizer as _leak
from agent_workflows import lifecycle_dirs as _life_dirs
from agent_workflows import plan_readiness as _plan_read
from agent_workflows import plans as _plans
from agent_workflows import platform_lock as _lock
from agent_workflows import project_context as _proj_ctx
from agent_workflows import releases as _releases
from agent_workflows import research_contract as _res_contract
from agent_workflows import review_findings as _rev_findings

# --------------------------------------------------------------------------------------
# 1. Field Registry and Constants (E-01, E-18, 4.2c, 4.5c)
# --------------------------------------------------------------------------------------

SUPPORTED_TYPES: Tuple[str, ...] = (
    "ipd",
    "spec",
    "backlog",
    "research",
    "release",
    "prompt",
    "walkthrough",
    "roadmap",
)

RESERVED_OPS: Tuple[str, ...] = ("finalize", "turn")

COVERED_OPS: Tuple[str, ...] = (
    "create",
    "set",
    "unset",
    "transition",
    "note",
    "checkpoint",
    "legacy",
    "review",
    "coverage",
    "rename",
)

RENAME_VERBS: FrozenSet[str] = frozenset(("rename", "group", "archive"))

SUPPORTED_OVERRIDES: FrozenSet[str] = frozenset(
    (
        "allow-open-questions",
        "allow-terminal-reopen",
        "allow-unreviewed",
        "allow-unresolvable-release-sentinel",
    )
)

REFINEMENT_VERDICTS: Tuple[str, ...] = (
    "REVIEWED - MATERIAL CHANGES APPLIED",
    "REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION",
)

GATE_VERDICTS: Tuple[str, ...] = tuple(_plan_read.VERDICTS.keys())

VALID_VALUE_TYPES: FrozenSet[str] = frozenset(
    (
        "string",
        "integer",
        "closed enum",
        "string list",
        "structured dependency list",
        "path-with-reason list",
        "reference",
    )
)

VALID_OWNERSHIP: FrozenSet[str] = frozenset(
    (
        "generic",
        "transition-owned",
        "review-owned",
        "coverage-owned",
        "finalize-owned",
        "path-event",
        "migration-only",
    )
)


class FieldDef(NamedTuple):
    name: str
    value_type: str
    ownership: str
    allowed_values: Optional[FrozenSet[str]] = None


# Per-op payload schemas (E-18): maps op -> dict of {payload_key: (type, required)}
OP_PAYLOAD_SCHEMAS: Dict[str, Dict[str, Tuple[type, bool]]] = {
    "create": {
        "fields": (dict, False),
        "path": (str, True),
    },
    "set": {
        "fields": (dict, True),
    },
    "unset": {
        "fields": (list, True),
    },
    "transition": {
        "from": (str, False),
        "to": (str, True),
        "path": (str, False),
    },
    "note": {
        "message": (str, False),
    },
    "checkpoint": {
        "fields": (dict, False),
        "path": (str, True),
    },
    "legacy": {
        "source": (str, True),
        "observed_day": (str, False),
        "position": (int, False),
        "ordering_confidence": (str, False),
        "line": (object, False),
    },
    "review": {
        "round": (int, True),
        "verdict": (str, False),
        "legacy_verdict": (object, False),
        "review_kind": (str, True),
        "reviewer": (str, False),
        "review_ref": (str, False),
        "findings_summary": (str, False),
        "review_depth": (str, False),
        "readiness": (str, False),
        "observed_day": (str, False),
    },
    "coverage": {
        "coverage": (str, True),
        "coverage_fingerprint": (str, True),
    },
    "rename": {
        "verb": (str, True),
        "path": (str, True),
    },
}

# The Field Registry (E-01, 4.2c, 4.5c)
_COMMON_FIELDS: Dict[str, FieldDef] = {
    "title": FieldDef("title", "string", "generic"),
    "short_description": FieldDef("short_description", "string", "generic"),
    "ace": FieldDef("ace", "string", "generic"),
    "model": FieldDef("model", "string", "generic"),
    "path": FieldDef("path", "string", "path-event"),
    "created_day": FieldDef("created_day", "string", "migration-only"),
    "last_history_day": FieldDef("last_history_day", "string", "migration-only"),
    "description_source": FieldDef("description_source", "string", "migration-only"),
    "description_model": FieldDef("description_model", "string", "migration-only"),
    "description_prompt_version": FieldDef(
        "description_prompt_version", "string", "migration-only"
    ),
}

REGISTRY: Dict[str, Dict[str, FieldDef]] = {
    "ipd": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "plan_role": FieldDef(
            "plan_role",
            "closed enum",
            "generic",
            frozenset(("child", "orchestrator", "tool-defect", "different-approach")),
        ),
        "work_kind": FieldDef("work_kind", "string", "generic"),
        "priority": FieldDef("priority", "string", "generic"),
        "readiness": FieldDef(
            "readiness",
            "closed enum",
            "review-owned",
            frozenset(("go", "caution", "hold", "replan"))
            | frozenset(_plan_read.VERDICTS.keys()),
        ),
        "approval": FieldDef("approval", "string", "transition-owned"),
        "coverage": FieldDef("coverage", "string", "coverage-owned"),
        "coverage_fingerprint": FieldDef(
            "coverage_fingerprint", "string", "coverage-owned"
        ),
        "coverage_checked": FieldDef("coverage_checked", "string", "migration-only"),
        "review_depth": FieldDef("review_depth", "string", "review-owned"),
        "pipeline": FieldDef(
            "pipeline",
            "closed enum",
            "generic",
            frozenset(("standard", "quick")),
        ),
        "scope_result": FieldDef(
            "scope_result",
            "closed enum",
            "finalize-owned",
            frozenset(("within", "widened", "exceeded")),
        ),
        "attended": FieldDef("attended", "string", "generic"),
        "dependency_declaration": FieldDef(
            "dependency_declaration",
            "closed enum",
            "generic",
            frozenset(("listed", "none", "unresolved")),
        ),
        "item_dependencies": FieldDef(
            "item_dependencies", "structured dependency list", "generic"
        ),
        "blocks_release": FieldDef("blocks_release", "reference", "generic"),
        "from_backlog": FieldDef("from_backlog", "reference", "generic"),
        "from_spec": FieldDef("from_spec", "reference", "generic"),
        "from_plan": FieldDef("from_plan", "reference", "generic"),
        "supersedes": FieldDef("supersedes", "reference", "generic"),
        "scope_paths": FieldDef("scope_paths", "string list", "generic"),
        "out_of_scope_paths": FieldDef(
            "out_of_scope_paths", "path-with-reason list", "finalize-owned"
        ),
        "widened_paths": FieldDef(
            "widened_paths", "path-with-reason list", "finalize-owned"
        ),
        "scope_exceeded_raw": FieldDef(
            "scope_exceeded_raw", "string", "migration-only"
        ),
        "author": FieldDef("author", "string", "generic"),
        "highest_e_allocated": FieldDef("highest_e_allocated", "string", "generic"),
    },
    "spec": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "work_kind": FieldDef("work_kind", "string", "generic"),
        "priority": FieldDef("priority", "string", "generic"),
        "dependency_declaration": FieldDef(
            "dependency_declaration",
            "closed enum",
            "generic",
            frozenset(("listed", "none", "unresolved")),
        ),
        "item_dependencies": FieldDef(
            "item_dependencies", "structured dependency list", "generic"
        ),
        "blocks_release": FieldDef("blocks_release", "reference", "generic"),
        "from_backlog": FieldDef("from_backlog", "reference", "generic"),
        "from_spec": FieldDef("from_spec", "reference", "generic"),
        "supersedes": FieldDef("supersedes", "reference", "generic"),
        "gate_kind": FieldDef("gate_kind", "string", "generic"),
        "gate_ref": FieldDef("gate_ref", "string", "generic"),
        "gate_summary": FieldDef("gate_summary", "string", "generic"),
        "author": FieldDef("author", "string", "generic"),
        "canonical": FieldDef("canonical", "string", "generic"),
        "implemented": FieldDef("implemented", "string", "migration-only"),
    },
    "backlog": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "priority": FieldDef("priority", "string", "generic"),
        "work_kind": FieldDef("work_kind", "string", "generic"),
        "dependency_declaration": FieldDef(
            "dependency_declaration",
            "closed enum",
            "generic",
            frozenset(("listed", "none", "unresolved")),
        ),
        "item_dependencies": FieldDef(
            "item_dependencies", "structured dependency list", "generic"
        ),
        "summary": FieldDef("summary", "string", "migration-only"),
        "close_evidence": FieldDef("close_evidence", "string", "transition-owned"),
        "release_exempt_kind": FieldDef("release_exempt_kind", "string", "generic"),
        "release_exempt_ref": FieldDef("release_exempt_ref", "string", "generic"),
        "gate_kind": FieldDef("gate_kind", "string", "generic"),
        "gate_ref": FieldDef("gate_ref", "string", "generic"),
        "gate_summary": FieldDef("gate_summary", "string", "generic"),
        "blocks_release": FieldDef("blocks_release", "reference", "generic"),
        "graduated_to": FieldDef("graduated_to", "string list", "generic"),
    },
    "research": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "research_kind": FieldDef("research_kind", "string", "generic"),
        "outcome": FieldDef("outcome", "string", "generic"),
        "priority": FieldDef("priority", "string", "generic"),
        "dependency_declaration": FieldDef(
            "dependency_declaration",
            "closed enum",
            "generic",
            frozenset(("listed", "none", "unresolved")),
        ),
        "item_dependencies": FieldDef(
            "item_dependencies", "structured dependency list", "generic"
        ),
        "blocks_release": FieldDef("blocks_release", "reference", "generic"),
        "consumed_by": FieldDef("consumed_by", "string list", "generic"),
        "topic": FieldDef("topic", "string list", "generic"),
        "created": FieldDef("created", "string", "migration-only"),
        "summary": FieldDef("summary", "string", "migration-only"),
    },
    "release": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "version": FieldDef("version", "string", "generic"),
    },
    "prompt": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "prompt_kind": FieldDef("prompt_kind", "string", "generic"),
        "author": FieldDef("author", "string", "generic"),
        "targets": FieldDef("targets", "string list", "generic"),
        "concerns": FieldDef("concerns", "string list", "generic"),
        "results_go_to": FieldDef("results_go_to", "string list", "generic"),
        "results": FieldDef("results", "string list", "generic"),
        "grounding": FieldDef("grounding", "string", "generic"),
        "goal": FieldDef("goal", "string", "generic"),
        "reviews_spec": FieldDef("reviews_spec", "reference", "generic"),
        "basis": FieldDef("basis", "string", "generic"),
        "relation": FieldDef("relation", "string", "generic"),
    },
    "walkthrough": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "target_id": FieldDef("target_id", "reference", "generic"),
    },
    "roadmap": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "target_id": FieldDef("target_id", "reference", "generic"),
    },
}


def registry_fields(record_type: str) -> List[str]:
    """Return the sorted list of registry field names for ``record_type``."""
    if record_type not in REGISTRY:
        raise ValueError(f"unknown record type {record_type!r}")
    return sorted(REGISTRY[record_type].keys())


def get_field_def(record_type: str, field: str) -> Optional[FieldDef]:
    """Lookup the FieldDef for a given record type and field."""
    return REGISTRY.get(record_type, {}).get(field)


# --------------------------------------------------------------------------------------
# 2. Lifecycle Transition Rules by Type (E-01, E-05)
# --------------------------------------------------------------------------------------


def validate_transition_edge(
    artifact_type: str,
    from_status: Optional[str],
    to_status: str,
    *,
    overrides: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Validate a lifecycle transition edge for an artifact type.

    Returns (is_legal, reason).
    """
    to_status = (to_status or "").strip()
    from_status = (from_status or "").strip() if from_status else None
    overrides_set = frozenset(overrides or ())

    if artifact_type in ("walkthrough", "roadmap"):
        return (
            False,
            f"{artifact_type} artifacts have no status and accept no transitions",
        )

    if artifact_type == "ipd":
        # Check retirement statuses accepted by status_set.TYPE_STATUSES["plans"]
        plan_retirement_targets = frozenset(("superseded", "not-executed", "reusable"))
        if to_status in plan_retirement_targets:
            if from_status and from_status not in _plans.TERMINAL:
                return True, ""
            if from_status in _plans.TERMINAL:
                if "allow-terminal-reopen" in overrides_set:
                    return True, ""
                return (
                    False,
                    f"cannot transition from terminal {from_status!r} without allow-terminal-reopen",
                )

        # Check terminal reopen override
        if from_status in _plans.TERMINAL:
            if "allow-terminal-reopen" in overrides_set:
                to_rank = _ipd_life._status_rank(to_status)
                if to_rank >= 0:
                    return True, ""
                return False, f"unknown target status {to_status!r}"
            return False, f"cannot transition out of terminal status {from_status!r}"

        # Standard plan transition check
        check = _ipd_life.validate_transition(from_status, to_status)
        if not check.ok:
            return False, check.reason
        return True, ""

    elif artifact_type == "spec":
        if from_status is None:
            if to_status == "draft":
                return True, ""
            return False, f"spec must start at draft, not {to_status!r}"
        allowed = _att.SPEC_TRANSITIONS.get(from_status, frozenset())
        if to_status in allowed:
            return True, ""
        return False, f"illegal spec transition from {from_status!r} to {to_status!r}"

    elif artifact_type == "backlog":
        if from_status is None:
            initial = frozenset(_att.BACKLOG_TRANSITIONS.keys()) | {"draft"}
            if to_status in initial:
                return True, ""
            return (
                False,
                f"backlog must start in {sorted(initial)}, not {to_status!r}",
            )
        allowed = _att.BACKLOG_TRANSITIONS.get(from_status, frozenset())
        if to_status in allowed:
            return True, ""
        return (
            False,
            f"illegal backlog transition from {from_status!r} to {to_status!r}",
        )

    elif artifact_type == "research":
        if to_status in _res_contract.STATUSES or to_status in (
            "active",
            "reference",
            "archive",
            "todo",
            "draft",
        ):
            return True, ""
        return False, f"illegal research status {to_status!r}"

    elif artifact_type == "prompt":
        prompt_subdirs = _life_dirs.LIFECYCLE_SUBDIRS.get("prompts", {})
        valid_prompt_statuses = frozenset(prompt_subdirs.keys()) | frozenset(
            ("pending", "reusable", "executed", "archived", "draft")
        )
        if to_status in valid_prompt_statuses:
            return True, ""
        return False, f"illegal prompt status {to_status!r}"

    elif artifact_type == "release":
        if to_status in _releases.RELEASE_STATUSES or to_status in (
            "planned",
            "shipped",
            "cancelled",
            "draft",
        ):
            return True, ""
        return False, f"illegal release status {to_status!r}"

    return False, f"unknown artifact type {artifact_type!r}"


# --------------------------------------------------------------------------------------
# 3. Envelope Encoding, Decoding and Event Validation (E-02, E-18)
# --------------------------------------------------------------------------------------

_RFC3339_RE = re.compile(
    r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\Z"
)


def validate_id6(id6: str) -> None:
    """Validate id6 strictly with re.fullmatch."""
    if not isinstance(id6, str) or not _core.ID6_RE.fullmatch(id6):
        raise ValueError(
            f"invalid id6: {id6!r} (must match ID6_RE with no trailing newline)"
        )


def encode_event(event: Dict[str, Any]) -> str:
    """Encode an event dict into a canonical JSON line (sorted keys, UTF-8, no trailing ws, final LF)."""
    return (
        json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    )


def decode_line(line: str) -> Dict[str, Any]:
    """Decode a canonical event JSON line."""
    if not line.endswith("\n"):
        raise ValueError("canonical line must end with LF")
    cleaned = line[:-1]
    if cleaned.endswith(" ") or cleaned.endswith("\r") or cleaned.endswith("\t"):
        raise ValueError("canonical line must have no trailing whitespace")
    try:
        data = json.loads(cleaned)
    except Exception as exc:
        raise ValueError(f"malformed JSON line: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("event line must decode to a JSON object")
    return data


def validate_envelope(event: Dict[str, Any]) -> None:
    """Validate the version-1 event envelope."""
    # Required keys: v, seq, append, at, actor, op
    required = ("v", "seq", "append", "at", "actor", "op")
    for req in required:
        if req not in event:
            raise ValueError(f"missing required envelope key: {req!r}")

    # Version
    v = event["v"]
    if v != 1:
        raise ValueError(f"unsupported-version: expected version 1, got {v!r}")

    # Sequence numbers
    seq = event["seq"]
    if not isinstance(seq, int) or seq < 0:
        raise ValueError(f"seq must be non-negative integer, got {seq!r}")

    append_val = event["append"]
    if not isinstance(append_val, int) or append_val < 0:
        raise ValueError(f"append must be non-negative integer, got {append_val!r}")

    # Timestamp
    at_val = event["at"]
    if not isinstance(at_val, str) or not _RFC3339_RE.match(at_val):
        raise ValueError(
            f"at must be RFC 3339 UTC timestamp with time of day, got {at_val!r}"
        )

    # Actor
    actor = event["actor"]
    if not isinstance(actor, dict):
        raise ValueError(f"actor must be an object, got {type(actor).__name__}")
    if (
        "tool" not in actor
        or not isinstance(actor["tool"], str)
        or not actor["tool"].strip()
    ):
        raise ValueError("actor.tool is required and must be non-empty string")
    for k, val in actor.items():
        if val is None:
            raise ValueError(f"actor key {k!r} must be omitted, not null")
        if k not in ("tool", "ace", "host", "model", "variant", "run_id", "attempt"):
            raise ValueError(f"unknown actor key {k!r}")

    # Op
    op = event["op"]
    if not isinstance(op, str):
        raise ValueError("op must be a string")

    # Optional envelope keys: by_human, overrides, message
    if "by_human" in event:
        if event["by_human"] is not True:
            raise ValueError("by_human must be True when present (omit when false)")

    if "overrides" in event:
        overrides = event["overrides"]
        if not isinstance(overrides, list) or len(overrides) == 0:
            raise ValueError("overrides must be a non-empty list when present")
        for ov in overrides:
            if ov not in SUPPORTED_OVERRIDES:
                raise ValueError(f"unknown override {ov!r}")


def validate_event(
    event: Dict[str, Any],
    artifact_type: Optional[str] = None,
) -> None:
    """Validate envelope and op payload schema for an event."""
    validate_envelope(event)
    op = event["op"]

    if op in RESERVED_OPS:
        raise ValueError(f"no registered payload schema for reserved op '{op}'")

    if op not in COVERED_OPS:
        raise ValueError(f"unknown op: {op!r}")

    schema = OP_PAYLOAD_SCHEMAS[op]
    envelope_keys = {
        "v",
        "seq",
        "append",
        "at",
        "actor",
        "op",
        "by_human",
        "overrides",
        "message",
    }
    for k, val in event.items():
        if k in envelope_keys:
            continue
        if k not in schema:
            raise ValueError(f"unknown payload key '{k}' for op '{op}'")

    # Op-specific validations
    if op == "rename":
        verb = event.get("verb")
        if verb not in RENAME_VERBS:
            raise ValueError(
                f"invalid rename verb {verb!r}; expected one of {sorted(RENAME_VERBS)}"
            )
        if not event.get("path"):
            raise ValueError("rename op must include 'path'")

    elif op == "review":
        rkind = event.get("review_kind")
        if rkind not in ("gate", "refinement"):
            raise ValueError(
                f"invalid review_kind {rkind!r}; expected 'gate' or 'refinement'"
            )
        if rkind == "refinement":
            if "readiness" in event:
                raise ValueError("refinement review must not carry 'readiness'")
            verdict = event.get("verdict")
            if verdict is not None and verdict not in REFINEMENT_VERDICTS:
                raise ValueError(f"invalid refinement verdict {verdict!r}")
        elif rkind == "gate":
            verdict = event.get("verdict")
            if (
                verdict is not None
                and verdict not in GATE_VERDICTS
                and "legacy_verdict" not in event
            ):
                raise ValueError(f"invalid gate verdict {verdict!r}")

    elif op == "coverage":
        if not event.get("coverage"):
            raise ValueError("coverage op requires 'coverage' payload")
        if not event.get("coverage_fingerprint"):
            raise ValueError("coverage op requires 'coverage_fingerprint' payload")

    # Fields validation if present
    if "fields" in event:
        fields = event["fields"]
        if op == "unset":
            if not isinstance(fields, list):
                raise ValueError("unset fields must be a list of field names")
            if artifact_type:
                reg = REGISTRY.get(artifact_type, {})
                for f in fields:
                    if f not in reg:
                        raise ValueError(
                            f"unknown field '{f}' for type '{artifact_type}'"
                        )
        else:
            if not isinstance(fields, dict):
                raise ValueError(f"{op} fields must be a dict")
            if artifact_type:
                reg = REGISTRY.get(artifact_type, {})
                for f in fields:
                    if op in ("create", "checkpoint") and f in (
                        "id",
                        "type",
                        "status",
                        "filename_date",
                    ):
                        continue
                    if f not in reg:
                        raise ValueError(
                            f"unknown field '{f}' for type '{artifact_type}'"
                        )
            if "scope_result" in fields:
                sr = fields["scope_result"]
                if sr not in ("within", "widened", "exceeded"):
                    raise ValueError(
                        f"invalid scope_result {sr!r}; expected one of ('exceeded', 'widened', 'within')"
                    )


# --------------------------------------------------------------------------------------
# 4. Writer-Side Refusals (E-03)
# --------------------------------------------------------------------------------------

_WINDOWS_DRIVE_RE = re.compile(r"\b[a-zA-Z]:[/\\]")
_TEXT_LEADING_PUNCT = "`\"'([{<"
_TEXT_TRAILING_PUNCT = "`\"'.,;:!?)]}>"

#: Real POSIX OS filesystem root prefixes refused in free-text event fields (`message`, `actor`,
#: `short_description`). Matching known OS roots instead of every `/a/b` token avoids rejecting
#: HTTP/REST API routes such as `/api/contracts/:id` or `/contracts/:id/request-audit` while
#: continuing to block machine-local POSIX filesystem paths alongside `_check_leak_sanitizer`.
POSIX_OS_ROOT_PREFIXES: tuple[str, ...] = (
    "/home/",
    "/Users/",
    "/opt/",
    "/etc/",
    "/var/",
    "/tmp/",
    "/usr/",
    "/root/",
    "/srv/",
    "/mnt/",
    "/media/",
    "/private/",
    "/Volumes/",
    "/Library/",
    "/System/",
    "/Applications/",
    "/bin/",
    "/sbin/",
    "/lib/",
    "/lib64/",
    "/proc/",
    "/sys/",
    "/dev/",
    "/run/",
    "/boot/",
)


#: Where `artifact_meta` puts its per-record write locks, relative to the repository's state root.
#: Named so the runner's lane inventory can recognize them as driver-written (a lock file is an empty
#: coordination artifact holding no work) without a second hardcoded path.
META_LOCK_SUBDIR = "locks"
META_LOCK_PREFIX = "meta-"


def is_meta_lock_relpath(path: str) -> bool:
    """True for a repository-relative `.aw/state/locks/meta-<key>.lock` path (an `artifact_meta` lock)."""

    p = (path or "").strip().strip('"').removeprefix("./")
    head, _, name = p.rpartition("/")
    return (
        head == f".aw/state/{META_LOCK_SUBDIR}"
        and name.startswith(META_LOCK_PREFIX)
        and name.endswith(".lock")
    )


def _check_string_safety(
    field_name: str,
    value: str,
    *,
    prose: bool = False,
    migration_import: bool = False,
) -> None:
    if migration_import:
        return
    refusal = _att.refuse_unsafe_descriptive(
        verb="artifact_meta",
        flag=field_name,
        value=value,
        bound_length=True,
        prose=prose,
    )
    if refusal:
        raise ValueError(refusal)


def find_absolute_path_in_text(text: str) -> Optional[Tuple[str, str]]:
    """Return ``('windows' | 'posix', token)`` if free text contains a local OS absolute path.

    Checks whitespace-separated tokens (stripping wrapping quotes/punctuation and inspecting the
    value side of ``key=value`` pairs) for Windows drive paths and multi-segment POSIX paths rooted
    under :data:`POSIX_OS_ROOT_PREFIXES`. Single-segment slash commands (``/plan-review``) and
    HTTP/REST route literals (``/api/contracts/:id``, ``/users/:id/profile``) are permitted.
    """
    for token in text.split():
        stripped = token.lstrip(_TEXT_LEADING_PUNCT).rstrip(_TEXT_TRAILING_PUNCT)
        if not stripped:
            continue
        raw_parts = (
            (stripped, stripped.split("=", 1)[1]) if "=" in stripped else (stripped,)
        )
        for raw_part in raw_parts:
            cand = raw_part.lstrip(_TEXT_LEADING_PUNCT).rstrip(_TEXT_TRAILING_PUNCT)
            if not cand:
                continue
            if _WINDOWS_DRIVE_RE.search(cand):
                return ("windows", token)
            if cand.startswith("/") and not cand.startswith("//"):
                for prefix in POSIX_OS_ROOT_PREFIXES:
                    if cand.startswith(prefix) and len(cand) > len(prefix):
                        return ("posix", token)
    return None


def _check_no_absolute_paths_in_text(token_source: str, text: str) -> None:
    hit = find_absolute_path_in_text(text)
    if hit is None:
        return
    kind, token = hit
    if kind == "windows":
        raise ValueError(
            f"{token_source} must not contain absolute Windows drive path: {token!r}"
        )
    raise ValueError(
        f"{token_source} must not contain absolute multi-segment path: {token!r}"
    )


def _check_leak_sanitizer(
    text: str,
    prefix: str,
    ruleset: _leak.Ruleset,
    *,
    include_warn: bool = True,
) -> None:
    findings = _leak.scan_text(text, prefix, ruleset, include_warn=include_warn)
    if findings:
        first = findings[0]
        raise ValueError(
            f"leak sanitizer refusal ({first.rule}) in {prefix}: {first.snippet!r}"
        )


def _check_path_safety(
    p_str: str,
    root: Path,
    label: str,
    *,
    root_label: str = "records root",
) -> None:
    if not isinstance(p_str, str):
        raise ValueError(f"{label} must be a string")
    if not p_str or not p_str.strip() or p_str == ".":
        raise ValueError(f"{label} must be a non-empty relative path (not '.')")
    p = Path(p_str)
    if (
        p.is_absolute()
        or p_str.startswith("/")
        or p_str.startswith("\\")
        or _WINDOWS_DRIVE_RE.match(p_str)
    ):
        raise ValueError(f"{label} must be relative: {p_str!r}")
    if ".." in p.parts:
        raise ValueError(f"{label} must not contain '..' segments: {p_str!r}")
    try:
        resolved = (root / p).resolve()
        resolved_root = root.resolve()
        if resolved_root not in resolved.parents:
            raise ValueError(f"{label} must resolve inside {root_label}: {p_str!r}")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"failed to resolve {label} {p_str!r}: {exc}") from exc


def _resolve_repo_root(
    records_root: Path,
    repo_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve repository root from explicit arg, standard .aw/.agents layout, owner, or git root."""
    if repo_root is not None:
        return Path(repo_root)
    abs_records = Path(os.path.abspath(records_root))
    if abs_records.name == "records" and abs_records.parent.name in (".aw", ".agents"):
        return abs_records.parent.parent
    return (
        _proj_ctx.record_owner_root(records_root)
        or _proj_ctx.record_git_root(records_root)
        or records_root
    )


def _validate_path_value(
    p_str: Any,
    root: Path,
    label: str,
    *,
    root_label: str,
    ruleset: "_leak.Ruleset",
    migration_import: bool,
) -> None:
    """Validate one path string against single-line safety, root containment, and leak rules."""
    if not isinstance(p_str, str):
        raise ValueError(f"{label} must be a string")
    _check_string_safety(label, p_str, prose=False, migration_import=migration_import)
    _check_path_safety(p_str, root, label, root_label=root_label)
    _check_leak_sanitizer(p_str, label, ruleset)


#: Field values that are prose or carry a list, so they take the prose length class rather than the
#: 300-character single-line bound: `approval` embeds the approval `--message` (2xwb9b D-03), and
#: `item_dependencies`/`graduated_to` grow with their edge count.
_PROSE_FIELDS: FrozenSet[str] = frozenset(
    ("close_evidence", "gate_summary", "approval", "item_dependencies", "graduated_to")
)


_GENERIC_FIXTURE_GIT_TOKENS: FrozenSet[str] = frozenset(
    {
        "test",
        "tester",
        "test user",
        "test runner",
        "test agent",
        "test committer",
        "test@example.com",
    }
)


_WRITER_RULESET_CACHE: Dict[Tuple[Any, ...], "_leak.Ruleset"] = {}
_WRITER_RULESET_CACHE_MAX = 64


def _stat_sig(path: Path) -> Optional[Tuple[int, int]]:
    try:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _writer_ruleset_cache_key(repo_root: Path) -> Tuple[Any, ...]:
    import socket as _socket

    resolved = _core._resolved_root(repo_root)
    git_entry = resolved / ".git"
    git_cfg_sig = _stat_sig(git_entry / "config")
    git_entry_sig: Any = None
    if git_cfg_sig is None and git_entry.is_file():
        try:
            raw_gd = git_entry.read_text(encoding="utf-8").strip()
            if raw_gd.startswith("gitdir:"):
                gd_path = Path(raw_gd.split(":", 1)[1].strip())
                if not gd_path.is_absolute():
                    gd_path = (resolved / gd_path).resolve()
                git_entry_sig = (
                    _stat_sig(git_entry),
                    _stat_sig(gd_path / "config"),
                    _stat_sig(gd_path.parent.parent / "config"),
                )
        except OSError:
            git_entry_sig = _stat_sig(git_entry)
    allowlist_path = _leak.resolve_allowlist_path(resolved)
    hints_path = _leak._config_dir() / _leak.USER_HINTS_FILENAME
    try:
        home_dir = Path.home()
    except Exception:
        home_dir = None
    home_gitconfig = _stat_sig(home_dir / ".gitconfig") if home_dir else None
    xdg_cfg = os.environ.get("XDG_CONFIG_HOME")
    xdg_gitconfig = (
        _stat_sig(Path(xdg_cfg) / "git" / "config")
        if xdg_cfg
        else (_stat_sig(home_dir / ".config" / "git" / "config") if home_dir else None)
    )
    try:
        hostname = _socket.gethostname()
    except Exception:
        hostname = ""
    return (
        str(resolved),
        hostname,
        os.environ.get("HOME"),
        os.environ.get("USERPROFILE"),
        os.environ.get("USER"),
        os.environ.get("USERNAME"),
        os.environ.get("XDG_CONFIG_HOME"),
        os.environ.get("AW_CONFIG_DIR"),
        os.environ.get("AW_HOME"),
        os.environ.get("GIT_CONFIG"),
        os.environ.get("GIT_CONFIG_GLOBAL"),
        os.environ.get("GIT_CONFIG_SYSTEM"),
        os.environ.get("GIT_CONFIG_NOSYSTEM"),
        os.environ.get("GIT_CONFIG_PARAMETERS"),
        os.environ.get("GIT_CONFIG_COUNT"),
        git_cfg_sig,
        git_entry_sig,
        str(allowlist_path),
        _stat_sig(allowlist_path),
        str(hints_path),
        _stat_sig(hints_path),
        home_gitconfig,
        xdg_gitconfig,
    )


def _writer_ruleset(repo_root: Path) -> "_leak.Ruleset":
    """The leak ruleset the writer scans with: every `fail` rule plus every auto-derived `warn`
    token EXCEPT sibling checkout directory names and synthetic test-fixture git identities
    (e.g. `tests/support.py::init_repo` setting `git user.name = "Test"`).

    Spec 4.2 lists what the writer refuses: session ids, command lines, absolute or home paths, user
    names and host names. A sibling directory name is none of those - whether inside `.aw/worktrees/`
    (where siblings are plan id6 lane dirs, 2xwb9b D-02) or in a normal workspace (where a sibling
    repo such as `../uri` would otherwise substring-refuse valid model identifiers like
    `uri/its_direct/...` and ordinary words like `during` or `security`). Sibling names remain
    advisory-only in `leak_sanitizer.derive_warn_tokens` for `aw check-local-leaks`."""
    cache_key: Optional[Tuple[Any, ...]] = None
    try:
        cache_key = _writer_ruleset_cache_key(repo_root)
        cached = _WRITER_RULESET_CACHE.get(cache_key)
        if cached is not None:
            return _leak.Ruleset(
                fail=dict(cached.fail),
                warn=dict(cached.warn),
                allow_line_substrings=cached.allow_line_substrings,
            )
    except Exception:
        cache_key = None

    try:
        derived = _leak.derive_warn_tokens(repo_root)
    except Exception:
        derived = None
    ruleset = _leak.build_ruleset(repo_root, include_warn=True, derived_tokens=derived)
    if derived is not None:
        for tok, reason in derived.items():
            if reason == "sibling checkout dir name":
                ruleset.warn.pop(f"derived:{tok}", None)
            elif (
                reason in ("git user.name", "git user.email")
                and tok.lower() in _GENERIC_FIXTURE_GIT_TOKENS
            ):
                ruleset.warn.pop(f"derived:{tok}", None)
    if cache_key is not None:
        if len(_WRITER_RULESET_CACHE) >= _WRITER_RULESET_CACHE_MAX:
            _WRITER_RULESET_CACHE.clear()
        _WRITER_RULESET_CACHE[cache_key] = _leak.Ruleset(
            fail=dict(ruleset.fail),
            warn=dict(ruleset.warn),
            allow_line_substrings=ruleset.allow_line_substrings,
        )
    return ruleset


def validate_new_events(
    artifact_type: str,
    events: List[Dict[str, Any]],
    *,
    records_root: Path,
    repo_root: Optional[Union[str, Path]] = None,
    migration_import: bool = False,
    ruleset: Optional["_leak.Ruleset"] = None,
) -> None:
    """Run writer-side refusals on events to be committed."""
    records_root = Path(records_root)
    repo_root = _resolve_repo_root(records_root, repo_root)

    # Build ruleset with include_warn=True once per call (or reuse caller-supplied ruleset)
    if ruleset is None:
        ruleset = _writer_ruleset(repo_root)

    for ev in events:
        validate_event(ev, artifact_type)

        # Actor checks
        actor = ev["actor"]
        for ak, av in actor.items():
            if isinstance(av, str):
                _check_string_safety(
                    f"actor.{ak}", av, prose=False, migration_import=migration_import
                )
                _check_no_absolute_paths_in_text(f"actor.{ak}", av)
                _check_leak_sanitizer(av, f"actor.{ak}", ruleset)

        # Message checks
        msg = ev.get("message")
        if msg:
            _check_string_safety(
                "message", msg, prose=True, migration_import=migration_import
            )
            _check_no_absolute_paths_in_text("message", msg)
            _check_leak_sanitizer(msg, "message", ruleset)

        # Path checks on event envelope (records-root-relative)
        if "path" in ev and ev["path"] is not None:
            _validate_path_value(
                ev["path"],
                records_root,
                f"{ev['op']}.path",
                root_label="records root",
                ruleset=ruleset,
                migration_import=migration_import,
            )

        # Payload checks
        if ev["op"] == "legacy":
            line_val = ev.get("line")
            if isinstance(line_val, str):
                # leak scan still runs on imported legacy lines (warn rules do not refuse import)
                _check_leak_sanitizer(
                    line_val,
                    "legacy.line",
                    ruleset,
                    include_warn=not migration_import,
                )
                if not migration_import:
                    _check_string_safety(
                        "legacy.line", line_val, prose=True, migration_import=False
                    )
        elif ev["op"] == "review":
            verdict = ev.get("verdict")
            if verdict:
                _check_string_safety(
                    "verdict", verdict, prose=False, migration_import=migration_import
                )
            leg_verdict = ev.get("legacy_verdict")
            if leg_verdict and isinstance(leg_verdict, str):
                _check_leak_sanitizer(
                    leg_verdict,
                    "legacy_verdict",
                    ruleset,
                    include_warn=not migration_import,
                )
                if not migration_import:
                    _check_string_safety(
                        "legacy_verdict",
                        leg_verdict,
                        prose=False,
                        migration_import=False,
                    )
            fs = ev.get("findings_summary")
            if fs:
                _check_string_safety(
                    "findings_summary",
                    fs,
                    prose=True,
                    migration_import=migration_import,
                )

        # Fields string safety
        fields = ev.get("fields")
        if isinstance(fields, dict):
            for fk, fv in fields.items():
                if fk in ("out_of_scope_paths", "widened_paths"):
                    if not isinstance(fv, list):
                        raise ValueError(f"fields.{fk} must be a list")
                    for item in fv:
                        if isinstance(item, dict):
                            p_val = item.get("path")
                            if "reason" in item and item["reason"] is not None:
                                r_val = item["reason"]
                                if not isinstance(r_val, str):
                                    raise ValueError(
                                        f"fields.{fk} item 'reason' must be a string"
                                    )
                                _check_leak_sanitizer(
                                    r_val, f"fields.{fk}.reason", ruleset
                                )
                        elif isinstance(item, str):
                            p_val = item
                        else:
                            raise ValueError(
                                f"fields.{fk} entries must be dict or str, got {type(item).__name__}"
                            )
                        _validate_path_value(
                            p_val,
                            repo_root,
                            f"fields.{fk}",
                            root_label="repository root",
                            ruleset=ruleset,
                            migration_import=migration_import,
                        )
                elif fk == "path":
                    _validate_path_value(
                        fv,
                        records_root,
                        "fields.path",
                        root_label="records root",
                        ruleset=ruleset,
                        migration_import=migration_import,
                    )
                elif isinstance(fv, str):
                    is_prose = fk in _PROSE_FIELDS
                    _check_string_safety(
                        fk, fv, prose=is_prose, migration_import=migration_import
                    )
                    _check_leak_sanitizer(
                        fv,
                        f"fields.{fk}",
                        ruleset,
                        include_warn=(
                            not migration_import or fk == "short_description"
                        ),
                    )
                elif isinstance(fv, list):
                    is_prose = fk in _PROSE_FIELDS
                    for elem in fv:
                        if isinstance(elem, str):
                            _check_string_safety(
                                fk,
                                elem,
                                prose=is_prose,
                                migration_import=migration_import,
                            )
                            _check_leak_sanitizer(
                                elem,
                                f"fields.{fk}",
                                ruleset,
                                include_warn=(
                                    not migration_import or fk == "short_description"
                                ),
                            )
                        elif isinstance(elem, dict) and fk == "item_dependencies":
                            raw_val = elem.get("raw")
                            if isinstance(raw_val, str):
                                _check_string_safety(
                                    fk,
                                    raw_val,
                                    prose=is_prose,
                                    migration_import=migration_import,
                                )
                                _check_leak_sanitizer(
                                    raw_val,
                                    f"fields.{fk}",
                                    ruleset,
                                    include_warn=not migration_import,
                                )
                        else:
                            raise ValueError(
                                f"fields.{fk} entries must be strings, got {type(elem).__name__}"
                            )


# --------------------------------------------------------------------------------------
# 5. Structured Relationships (E-04)
# --------------------------------------------------------------------------------------


def parse_item_dependencies_field(
    value: Any,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Parse Item-Dependencies into (declaration, conditions).

    Distinguishes absent (None), 'none', 'unresolved', and listed edges (string or parsed list).
    """
    if value is None:
        return "absent", []
    if isinstance(value, list):
        stored_list: List[Dict[str, Any]] = []
        for entry in value:
            if not isinstance(entry, dict):
                raise ValueError(
                    f"malformed Item-Dependencies list entry: expected dict, got {type(entry).__name__}"
                )
            cond = entry.get("condition")
            ttype = entry.get("target_type")
            tid6 = entry.get("target_id6")
            raw = entry.get("raw")
            if (
                cond not in ("executed", "exists", "state")
                or not isinstance(ttype, str)
                or not isinstance(tid6, str)
                or not isinstance(raw, str)
            ):
                raise ValueError(f"malformed Item-Dependencies edge dict: {entry!r}")
            stored_list.append(
                {
                    "condition": cond,
                    "target_type": ttype,
                    "required_status": entry.get("required_status"),
                    "target_id6": tid6,
                    "raw": raw,
                }
            )
        return ("listed", stored_list) if stored_list else ("none", [])
    v = str(value).strip()
    if v == "none":
        return "none", []
    if v == "unresolved":
        return "unresolved", []
    edges, ready, err = _ipd_schema.parse_item_dependencies(v)
    if err:
        raise ValueError(f"malformed Item-Dependencies: {err}")
    stored_edges = [
        {
            "condition": e.kind,
            "target_type": e.target_type,
            "required_status": e.status,
            "target_id6": e.id6,
            "raw": e.canonical(),
        }
        for e in edges
    ]
    return "listed", stored_edges


def parse_graduated_to(value: Any) -> List[str]:
    """Parse graduated_to preserving duplicate and malformed declarations for diagnosis."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        return [tok.strip() for tok in v.split(",") if tok.strip()]
    return [str(value)]


# --------------------------------------------------------------------------------------
# 6. Replay Engine (E-05, E-06, 4.3, 4.4)
# --------------------------------------------------------------------------------------


@dataclasses.dataclass
class State:
    id6: str
    type: str
    status: Optional[str] = None
    path: Optional[str] = None
    title: Optional[str] = None
    short_description: Optional[str] = None
    set_id: Optional[str] = None
    order_nn: Optional[int] = None
    filename_date: Optional[str] = None
    created_day: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_history_day: Optional[str] = None
    last_seq: int = 0
    valid: int = 1
    defect: Optional[str] = None
    fields: Dict[str, Any] = dataclasses.field(default_factory=dict)
    disposition: Optional[str] = None
    id_derived: bool = False
    legacy_raw_status: Optional[str] = None
    legacy_raw_set: Optional[str] = None
    loose_id: Optional[str] = None
    loose_status: Optional[str] = None
    loose_blocks_release: Optional[str] = None


def replay(
    id6: str,
    artifact_type: str,
    lines: Iterable[Union[str, Dict[str, Any]]],
    *,
    records_root: Optional[Path] = None,
    migration_import: bool = False,
) -> Tuple[
    State, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]
]:
    """Replay an event log for an artifact.

    Returns:
      (State, field_changes, artifact_paths, projection_data)
    """
    validate_id6(id6)
    if artifact_type not in SUPPORTED_TYPES:
        raise ValueError(f"unknown artifact type: {artifact_type!r}")

    # Parse and sort lines by seq
    events: List[Dict[str, Any]] = []
    for raw in lines:
        ev = decode_line(raw) if isinstance(raw, str) else raw
        validate_envelope(ev)
        events.append(ev)

    events.sort(key=lambda e: e["seq"])

    # Initial shape check
    if not events:
        raise ValueError("bad-initial-event: empty event log")

    first = events[0]
    if first["seq"] == 0:
        if first["op"] != "checkpoint":
            raise ValueError(
                f"bad-initial-event: seq 0 must be checkpoint, got {first['op']!r}"
            )
    elif first["seq"] == 1:
        if first["op"] != "create":
            raise ValueError(
                f"bad-initial-event: seq 1 must be create, got {first['op']!r}"
            )
    else:
        raise ValueError(
            f"bad-initial-event: initial event must be seq 0 (checkpoint) or seq 1 (create), got seq {first['seq']}"
        )

    # Check for duplicate seq, seq gaps, later create/checkpoint
    expected_seq = first["seq"]
    seen_seqs: Set[int] = set()
    for ev in events:
        s = ev["seq"]
        if s in seen_seqs:
            raise ValueError(f"seq-duplicate: duplicate sequence number {s}")
        if s != expected_seq:
            raise ValueError(
                f"seq-gap: expected sequence number {expected_seq}, got {s}"
            )
        seen_seqs.add(s)
        expected_seq += 1
        if ev is not first and ev["op"] in ("create", "checkpoint"):
            raise ValueError(f"bad-initial-event: later {ev['op']} event at seq {s}")

    # Check append runs
    # Contiguous runs sharing append, at, and actor must have append == first seq of run
    idx = 0
    while idx < len(events):
        run_append = events[idx]["append"]
        run_at = events[idx]["at"]
        run_actor = events[idx]["actor"]
        first_seq = events[idx]["seq"]
        if run_append != first_seq:
            raise ValueError(
                f"append-mismatch: event at seq {first_seq} has append {run_append} != {first_seq}"
            )
        # Advance while sharing append
        j = idx + 1
        while j < len(events) and events[j]["append"] == run_append:
            if events[j]["at"] != run_at or events[j]["actor"] != run_actor:
                raise ValueError(
                    f"append-mismatch: events in append {run_append} have differing at/actor"
                )
            j += 1
        idx = j

    # Replay state
    state = State(id6=id6, type=artifact_type)
    field_changes: List[Dict[str, Any]] = []
    artifact_paths: List[Dict[str, Any]] = []
    reviews_rows: List[Dict[str, Any]] = []
    coverage_rows: List[Dict[str, Any]] = []
    scope_exceptions: List[Dict[str, Any]] = []
    dependencies_rows: List[Dict[str, Any]] = []
    lineage_rows: List[Dict[str, Any]] = []
    graduation_targets_rows: List[Dict[str, Any]] = []
    release_gates_rows: List[Dict[str, Any]] = []
    gates_row: Optional[Dict[str, Any]] = None
    actors_map: Dict[str, Dict[str, Any]] = {}

    current_fields: Dict[str, Any] = {}
    current_status: Optional[str] = None
    created_at_val: Optional[str] = None
    updated_at_val: Optional[str] = None

    # Track appends to validate event-owned fields across appends
    append_events: Dict[int, List[Dict[str, Any]]] = {}
    for ev in events:
        append_events.setdefault(ev["append"], []).append(ev)

    for app_id, app_evs in append_events.items():
        # Look ahead in this append for transitions
        trans_ev = next((e for e in app_evs if e["op"] == "transition"), None)
        to_approved = trans_ev is not None and trans_ev.get("to") == "approved"
        from_approved = trans_ev is not None and trans_ev.get("from") == "approved"
        to_executed = trans_ev is not None and trans_ev.get("to") == "executed"
        backward_to_draft_or_review = (
            trans_ev is not None
            and trans_ev.get("to") in ("draft", "to-review")
            and trans_ev.get("from") in ("reviewed", "approved", "executed")
        )

        for ev in app_evs:
            s = ev["seq"]
            op = ev["op"]
            at_str = ev["at"]
            actor_obj = ev["actor"]
            by_human = bool(ev.get("by_human", False))
            overrides = ev.get("overrides", [])

            # Actor registration
            actor_canon = json.dumps(actor_obj, sort_keys=True)
            actor_id = hashlib.sha256(actor_canon.encode("utf-8")).hexdigest()[:16]
            if actor_id not in actors_map:
                actors_map[actor_id] = {
                    "actor_id": actor_id,
                    "tool": actor_obj.get("tool"),
                    "ace": actor_obj.get("ace"),
                    "host": actor_obj.get("host"),
                    "model": actor_obj.get("model"),
                    "variant": actor_obj.get("variant"),
                    "run_id": actor_obj.get("run_id"),
                    "attempt": actor_obj.get("attempt"),
                }

            if s == 1 and op == "create":
                created_at_val = at_str
            if s > 0:
                updated_at_val = at_str

            # Op payload validation against schema
            validate_event(ev, artifact_type)

            # Path-bearing ops
            if op in ("create", "checkpoint", "rename"):
                if "path" not in ev:
                    raise ValueError(f"path-bearing op '{op}' without path")
                ev_path = ev["path"]
                verb_val = ev.get("verb") if op == "rename" else None
                artifact_paths.append(
                    {
                        "id6": id6,
                        "seq": s,
                        "path": ev_path,
                        "at": at_str,
                        "actor_id": actor_id,
                        "by_human": 1 if by_human else 0,
                        "op": op,
                        "verb": verb_val,
                    }
                )
                state.path = ev_path

            # Handling ops
            if op in ("create", "checkpoint"):
                fdict = ev.get("fields", {})
                # Check identity if given
                if "id" in fdict and fdict["id"] != id6:
                    raise ValueError(
                        f"identity-changed: declared id {fdict['id']!r} != {id6!r}"
                    )
                if "type" in fdict and fdict["type"] != artifact_type:
                    raise ValueError(
                        f"identity-changed: declared type {fdict['type']!r} != {artifact_type!r}"
                    )
                if "status" in fdict:
                    current_status = fdict["status"]
                    state.status = current_status

                for fk, fv in fdict.items():
                    if fk in ("id", "type"):
                        continue
                    old_v = current_fields.get(fk)
                    current_fields[fk] = fv
                    field_changes.append(
                        {
                            "id6": id6,
                            "seq": s,
                            "field": fk,
                            "old_value": json.dumps(old_v)
                            if old_v is not None
                            else None,
                            "new_value": json.dumps(fv),
                            "unset": 0,
                        }
                    )

            elif op == "transition":
                from_s = ev.get("from")
                to_s = ev["to"]
                if from_s != current_status:
                    raise ValueError(
                        f"transition-from-mismatch: expected from={current_status!r}, got {from_s!r}"
                    )
                ok, reason = validate_transition_edge(
                    artifact_type, from_s, to_s, overrides=overrides
                )
                if not ok:
                    raise ValueError(f"illegal-transition: {reason}")

                old_s = current_status
                current_status = to_s
                state.status = current_status
                field_changes.append(
                    {
                        "id6": id6,
                        "seq": s,
                        "field": "status",
                        "old_value": json.dumps(old_s) if old_s is not None else None,
                        "new_value": json.dumps(to_s),
                        "unset": 0,
                    }
                )
                # If transition carries path
                if "path" in ev:
                    ev_path = ev["path"]
                    artifact_paths.append(
                        {
                            "id6": id6,
                            "seq": s,
                            "path": ev_path,
                            "at": at_str,
                            "actor_id": actor_id,
                            "by_human": 1 if by_human else 0,
                            "op": op,
                            "verb": None,
                        }
                    )
                    state.path = ev_path

            elif op == "set":
                fdict = ev["fields"]
                for fk, fv in fdict.items():
                    if fk in ("status", "id", "type"):
                        raise ValueError(
                            f"refuse generic set of identity/status field: {fk!r}"
                        )
                    # Event-owned field checks
                    if fk in ("readiness", "review_depth"):
                        raise ValueError(f"refuse set of review-owned field {fk!r}")
                    if fk in ("coverage", "coverage_fingerprint"):
                        raise ValueError(f"refuse set of coverage-owned field {fk!r}")
                    if fk == "approval":
                        if not to_approved:
                            raise ValueError(
                                "set of approval outside transition to approved append"
                            )
                    if fk in ("scope_result", "out_of_scope_paths", "widened_paths"):
                        if not to_executed:
                            raise ValueError(
                                f"set of {fk!r} outside transition to executed append"
                            )

                    old_v = current_fields.get(fk)
                    current_fields[fk] = fv
                    field_changes.append(
                        {
                            "id6": id6,
                            "seq": s,
                            "field": fk,
                            "old_value": json.dumps(old_v)
                            if old_v is not None
                            else None,
                            "new_value": json.dumps(fv),
                            "unset": 0,
                        }
                    )

            elif op == "unset":
                fnames = ev["fields"]
                for fk in fnames:
                    if fk in ("status", "id", "type"):
                        raise ValueError(
                            f"refuse generic unset of identity/status field: {fk!r}"
                        )
                    if fk in ("readiness", "review_depth"):
                        if not backward_to_draft_or_review:
                            raise ValueError(
                                f"refuse unset of {fk!r} outside backward transition append"
                            )
                    if fk == "approval":
                        if not from_approved:
                            raise ValueError(
                                "refuse unset of approval outside transition away from approved"
                            )
                    if fk in ("scope_result", "out_of_scope_paths", "widened_paths"):
                        raise ValueError(f"refuse unset of finalize-owned field {fk!r}")

                    old_v = current_fields.pop(fk, None)
                    field_changes.append(
                        {
                            "id6": id6,
                            "seq": s,
                            "field": fk,
                            "old_value": json.dumps(old_v)
                            if old_v is not None
                            else None,
                            "new_value": None,
                            "unset": 1,
                        }
                    )

            elif op == "review":
                # Gate or refinement review
                rkind = ev["review_kind"]
                r_rnd = ev["round"]
                r_ref = ev.get("review_ref")
                verdict = ev.get("verdict")
                leg_verdict = ev.get("legacy_verdict")
                obs_day = ev.get("observed_day")
                readiness = ev.get("readiness")
                rdepth = ev.get("review_depth")
                fsummary = ev.get("findings_summary")
                reviewer = ev.get("reviewer")

                reviews_rows.append(
                    {
                        "subject_id6": id6,
                        "seq": s,
                        "review_ref": r_ref,
                        "round": r_rnd,
                        "review_kind": rkind,
                        "verdict": verdict,
                        "legacy_verdict": leg_verdict,
                        "observed_day": obs_day,
                        "readiness": readiness,
                        "review_depth": rdepth,
                        "findings_summary": fsummary,
                        "reviewer": reviewer,
                    }
                )

                if rkind == "gate":
                    if readiness:
                        current_fields["readiness"] = readiness
                    if rdepth:
                        current_fields["review_depth"] = rdepth

            elif op == "coverage":
                cov = ev["coverage"]
                cov_fp = ev["coverage_fingerprint"]
                current_fields["coverage"] = cov
                current_fields["coverage_fingerprint"] = cov_fp
                coverage_rows.append(
                    {
                        "id6": id6,
                        "seq": s,
                        "coverage": cov,
                        "coverage_fingerprint": cov_fp,
                    }
                )

            elif op in ("note", "legacy"):
                # note and legacy change no field
                pass

        # Post-append invariants check:
        # 1. If transitioning away from approved, approval must not survive!
        if from_approved and "approval" in current_fields:
            raise ValueError(
                "approval must be unset in the append containing a transition away from approved"
            )
        # 2. If backward transition to draft or to-review, readiness must be unset!
        if backward_to_draft_or_review and "readiness" in current_fields:
            raise ValueError(
                "readiness must be unset in the append of a backward plan transition"
            )

    # Set final state properties
    state.status = current_status
    state.fields = current_fields
    state.last_seq = events[-1]["seq"]
    state.created_at = created_at_val
    state.updated_at = updated_at_val
    state.filename_date = current_fields.get("filename_date")
    state.created_day = current_fields.get("created_day")
    state.last_history_day = current_fields.get("last_history_day")
    state.short_description = current_fields.get("short_description")
    state.title = current_fields.get("title")
    state.set_id = current_fields.get("set")
    ord_val = current_fields.get("order")
    if ord_val is not None:
        try:
            state.order_nn = int(ord_val)
        except (ValueError, TypeError):
            state.order_nn = None

    # Relationship and child table projections
    # scope_paths
    if "scope_paths" in current_fields:
        sp = current_fields["scope_paths"]
        if isinstance(sp, list):
            for i, p_val in enumerate(sp, start=1):
                scope_exceptions.append({})  # not exception
        # Let's project scope_paths
    raw_sp = current_fields.get("scope_paths")
    sp_list: List[Dict[str, Any]] = []
    if isinstance(raw_sp, list):
        for i, p_val in enumerate(raw_sp, start=1):
            sp_list.append({"id6": id6, "ordinal": i, "path": str(p_val)})
    elif isinstance(raw_sp, str) and raw_sp.strip():
        for i, p_val in enumerate(
            [tok.strip() for tok in raw_sp.split(",") if tok.strip()], start=1
        ):
            sp_list.append({"id6": id6, "ordinal": i, "path": p_val})

    # scope_exceptions (from out_of_scope_paths and widened_paths or scope_exceeded_raw)
    se_list: List[Dict[str, Any]] = []
    ordinal = 1
    for item in current_fields.get("out_of_scope_paths", []):
        p_val = item.get("path") if isinstance(item, dict) else str(item)
        r_val = item.get("reason", "") if isinstance(item, dict) else ""
        se_list.append(
            {
                "id6": id6,
                "ordinal": ordinal,
                "path": p_val,
                "reason": r_val,
                "exception_kind": "out-of-scope",
                "source": "finalize" if events[-1]["seq"] > 0 else "checkpoint",
            }
        )
        ordinal += 1
    for item in current_fields.get("widened_paths", []):
        p_val = item.get("path") if isinstance(item, dict) else str(item)
        r_val = item.get("reason", "") if isinstance(item, dict) else ""
        se_list.append(
            {
                "id6": id6,
                "ordinal": ordinal,
                "path": p_val,
                "reason": r_val,
                "exception_kind": "widened",
                "source": "finalize" if events[-1]["seq"] > 0 else "checkpoint",
            }
        )
        ordinal += 1

    # dependencies
    raw_dep_val = current_fields.get("item_dependencies")
    explicit_decl = current_fields.get("dependency_declaration")
    dep_decl, dep_edges = parse_item_dependencies_field(raw_dep_val)
    if (
        raw_dep_val is None or (isinstance(raw_dep_val, list) and not raw_dep_val)
    ) and explicit_decl in ("none", "unresolved"):
        dep_decl = explicit_decl
    current_fields["dependency_declaration"] = dep_decl
    for i, e in enumerate(dep_edges, start=1):
        dependencies_rows.append(
            {
                "dependent_id6": id6,
                "ordinal": i,
                "condition": e["condition"],
                "target_type": e["target_type"],
                "required_status": e["required_status"],
                "target_raw": e["raw"],
                "target_id6": e["target_id6"],
            }
        )

    # lineage (from_backlog, from_spec, from_plan, supersedes)
    for rel_field in ("from_backlog", "from_spec", "from_plan", "supersedes"):
        rel_raw = current_fields.get(rel_field)
        if rel_raw:
            raw_s = str(rel_raw).strip()
            # If formatted like [id6](...) or bare id6
            m_id6 = _core.ID6_RE.search(raw_s)
            p_id6 = m_id6.group(0) if m_id6 else None
            lineage_rows.append(
                {
                    "child_id6": id6,
                    "relation": rel_field,
                    "parent_raw": raw_s,
                    "parent_id6": p_id6,
                }
            )

    # graduation_targets
    grad_to = parse_graduated_to(current_fields.get("graduated_to"))
    for i, g_raw in enumerate(grad_to, start=1):
        graduation_targets_rows.append(
            {
                "source_id6": id6,
                "ordinal": i,
                "target_raw": g_raw,
                "target_set_id": g_raw,  # resolved dynamically later
            }
        )

    # release_gates
    br_raw = current_fields.get("blocks_release")
    if br_raw:
        br_str = str(br_raw).strip()
        release_gates_rows.append(
            {
                "id6": id6,
                "release_raw": br_str,
                "release_id6": None,  # resolved dynamically later
            }
        )

    # gates
    gk = current_fields.get("gate_kind")
    gr = current_fields.get("gate_ref")
    gs = current_fields.get("gate_summary")
    if gk or gr or gs:
        gates_row = {
            "id6": id6,
            "gate_kind": gk,
            "gate_ref": gr,
            "gate_summary": gs,
        }

    projection_data: Dict[str, Any] = {
        "scope_paths": sp_list,
        "scope_exceptions": se_list,
        "dependencies": dependencies_rows,
        "lineage": lineage_rows,
        "graduation_targets": graduation_targets_rows,
        "release_gates": release_gates_rows,
        "gates": [gates_row] if gates_row else [],
        "reviews": reviews_rows,
        "coverage": coverage_rows,
        "actors": list(actors_map.values()),
        "events": [
            {
                "id6": id6,
                "seq": e["seq"],
                "append": e["append"],
                "op": e["op"],
                "at": e["at"],
                "actor_id": hashlib.sha256(
                    json.dumps(e["actor"], sort_keys=True).encode("utf-8")
                ).hexdigest()[:16],
                "by_human": 1 if e.get("by_human") else 0,
                "from_status": e.get("from"),
                "to_status": e.get("to"),
                "path": e.get("path"),
                "message": e.get("message"),
                "raw": encode_event(e),
            }
            for e in events
        ],
    }

    return state, field_changes, artifact_paths, projection_data


# --------------------------------------------------------------------------------------
# 7. Mirror Parsers (E-07)
# --------------------------------------------------------------------------------------

_MANAGED_PROMPT_COMMENT_RE = re.compile(
    r"\A<!--\s*aw-managed-prompt:\s*(.*?)\s*-->", re.DOTALL
)
_MANAGED_BANNER_LINE_RE = re.compile(r"\A<!--\s*aw-managed:.*?-->\r?\n?", re.DOTALL)
_LEADING_PROMPT_COMMENT_LINE_RE = re.compile(
    r"\A<!--\s*(?:aw-managed-prompt|aw-prompt):.*?-->\r?\n?", re.DOTALL
)


def render_in_file_mirror(
    id6: str,
    artifact_type: str,
    status: Optional[str] = None,
) -> str:
    """Render the canonical 4.1 / OQ-25 in-file mirror and banner for ``artifact_type``."""
    validate_id6(id6)
    if artifact_type == "prompt":
        eff_status = (status or "pending").strip()
        return (
            f"<!-- aw-managed-prompt: id: {id6} | status: {eff_status} "
            f". Pipeline metadata only; not part of the prompt. "
            f"Metadata: .aw/records/meta/{id6}.jsonl -->\n"
        )
    banner = (
        f"<!-- aw-managed: metadata lives in .aw/records/meta/{id6}.jsonl; "
        f"use `aw show {id6}`; agents read .aw/AGENT_QUICKSTART.md -->\n"
    )
    if artifact_type in ("walkthrough", "roadmap") or (
        artifact_type == "research" and not (status or "").strip()
    ):
        return f"---\nid: {id6}\n---\n{banner}"
    eff_status = (status or "draft").strip()
    return f"---\nid: {id6}\nstatus: {eff_status}\n---\n{banner}"


def render_review_mirror(
    subject_id: str,
    subject_type: str,
    review_ref: Optional[str] = None,
) -> str:
    """Render the canonical 4.1 / 4.1a in-file mirror and banner for a review file."""
    validate_id6(subject_id)
    stype = (subject_type or "").strip().lower()
    if not stype:
        raise ValueError("review mirror requires non-empty subject_type")
    fm_lines = [
        "---",
        f"subject: {subject_id}",
        f"subject_type: {stype}",
    ]
    if review_ref is not None and str(review_ref).strip():
        fm_lines.append(f"ref: {str(review_ref).strip()}")
    fm_lines.append("---")
    banner = (
        f"<!-- aw-managed: review metadata lives in .aw/records/meta/{subject_id}.jsonl; "
        f"use aw show {subject_id}; agents read .aw/AGENT_QUICKSTART.md -->\n"
    )
    return "\n".join(fm_lines) + "\n" + banner


def _strip_leading_yaml_mirror(text: str) -> str:
    """Strip a leading ``---`` front-matter block and any immediately following ``aw-managed`` banner."""
    rest = text
    if rest.startswith("---\n") or rest.startswith("---\r\n"):
        lines = rest.splitlines(keepends=True)
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                rest = "".join(lines[idx + 1 :])
                break
    rest = _MANAGED_BANNER_LINE_RE.sub("", rest, count=1)
    return rest


def apply_in_file_mirror(
    text: str,
    id6: str,
    artifact_type: str,
    status: Optional[str] = None,
) -> str:
    """Replace or prepend the canonical 4.1 in-file mirror and banner on ``text``."""
    prefix = render_in_file_mirror(id6, artifact_type, status)
    if artifact_type == "prompt":
        body = _LEADING_PROMPT_COMMENT_LINE_RE.sub("", text.lstrip("\ufeff"), count=1)
        return prefix + body
    body = _strip_leading_yaml_mirror(text)
    return prefix + body


def parse_artifact_mirror(
    text: str, *, allow_statusless: bool = False
) -> Dict[str, Any]:
    """Parse standard artifact front matter (id and status, or id-only when opted in).

    Strict line grammar: by default, requires exactly two keys 'id' and 'status' in that
    order. When ``allow_statusless=True`` (used for research records), accepts either a
    1-key 'id' mirror (returning ``status: None``) or the standard 2-key 'id' and
    'status' mirror.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("artifact must start with '---' front matter")
    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx == -1:
        raise ValueError("unclosed '---' front matter")

    fmlines = lines[1:closing_idx]
    if allow_statusless:
        if len(fmlines) not in (1, 2):
            raise ValueError(
                f"mirror parse error: expected 1 or 2 front-matter keys, got {len(fmlines)}"
            )
    elif len(fmlines) != 2:
        raise ValueError(
            f"mirror parse error: expected exactly 2 front-matter keys, got {len(fmlines)}"
        )

    m1 = re.match(r"^id:\s*(\S+)$", fmlines[0].strip())
    if not m1:
        raise ValueError(
            f"mirror parse error: line 1 must be 'id: <id6>', got {fmlines[0]!r}"
        )
    id_val = m1.group(1)
    validate_id6(id_val)

    if len(fmlines) == 1:
        return {"id": id_val, "status": None}

    m2 = re.match(r"^status:\s*(\S+)$", fmlines[1].strip())
    if not m2:
        raise ValueError(
            f"mirror parse error: line 2 must be 'status: <status>', got {fmlines[1]!r}"
        )
    status_val = m2.group(1)

    return {"id": id_val, "status": status_val}


def parse_walkthrough_mirror(text: str) -> Dict[str, Any]:
    """Parse walkthrough front matter (exactly one key: id)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("walkthrough must start with '---' front matter")
    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx == -1:
        raise ValueError("unclosed '---' front matter")

    fmlines = lines[1:closing_idx]
    if len(fmlines) != 1:
        raise ValueError(
            f"mirror parse error: walkthrough front matter must have exactly 1 key, got {len(fmlines)}"
        )
    m = re.match(r"^id:\s*(\S+)$", fmlines[0].strip())
    if not m:
        raise ValueError(
            f"mirror parse error: line must be 'id: <id6>', got {fmlines[0]!r}"
        )
    id_val = m.group(1)
    validate_id6(id_val)
    return {"id": id_val, "status": None}


def parse_review_mirror(text: str) -> Dict[str, Any]:
    """Parse review front matter: subject, subject_type, and optional ref."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("review must start with '---' front matter")
    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx == -1:
        raise ValueError("unclosed '---' front matter")

    fmlines = lines[1:closing_idx]
    if len(fmlines) not in (2, 3):
        raise ValueError(
            f"mirror parse error: review front matter must have 2 or 3 keys, got {len(fmlines)}"
        )
    data: Dict[str, str] = {}
    for line in fmlines:
        m = re.match(r"^([a-z_]+):\s*(\S+)$", line.strip())
        if not m:
            raise ValueError(
                f"mirror parse error: invalid review front matter line: {line!r}"
            )
        data[m.group(1)] = m.group(2)

    if "subject" not in data or "subject_type" not in data:
        raise ValueError("review front matter requires 'subject' and 'subject_type'")
    validate_id6(data["subject"])
    return data


def parse_staged_prompt_mirror(text: str) -> Dict[str, Any]:
    """Parse the single leading HTML comment on a staged prompt:

    <!-- aw-managed-prompt: id: <id> | status: <status> ... -->
    """
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty prompt file")
    m = _MANAGED_PROMPT_COMMENT_RE.match(lines[0].strip())
    if not m:
        raise ValueError(
            "staged prompt line 1 must be <!-- aw-managed-prompt: ... --> comment"
        )
    inner = m.group(1)
    parts = [p.strip() for p in inner.split("|")]
    result: Dict[str, Any] = {}
    for part in parts:
        if ":" in part:
            k, v = part.split(":", 1)
            k = k.strip()
            v = v.strip().split()[0]  # token
            if k in ("id", "status"):
                result[k] = v
    if "id" not in result or "status" not in result:
        raise ValueError(f"managed prompt comment missing id or status: {lines[0]!r}")
    validate_id6(result["id"])
    return result


def read_mirror_id6(text: str) -> Optional[str]:
    """Read the declared ``id`` from a post-cutover in-file mirror, or ``None``.

    Handles an optional leading UTF-8 BOM (``\\ufeff``), a YAML front-matter mirror
    (``---\\nid: <id6>...``), and a staged-prompt mirror
    (``<!-- aw-managed-prompt: id: <id6> ... -->``).
    """
    if not text:
        return None
    stripped = text.lstrip("\ufeff")
    if stripped.startswith("---"):
        try:
            parsed = parse_artifact_mirror(stripped, allow_statusless=True)
            return str(parsed["id"])
        except ValueError:
            pass
        m = re.match(r"\A---\r?\nid:\s*([0-9a-z]{6})\s*(?:\r?\n|\Z)", stripped)
        if m:
            return m.group(1)
        return None
    if stripped.startswith("<!--"):
        try:
            parsed_prompt = parse_staged_prompt_mirror(stripped)
            return str(parsed_prompt["id"])
        except ValueError:
            pass
        first_line = stripped.splitlines()[0] if stripped.splitlines() else ""
        if _MANAGED_PROMPT_COMMENT_RE.match(first_line):
            cand = _first_token(_parse_metadata_comment(first_line).get("id"))
            if cand and _core.ID6_RE.fullmatch(cand):
                return cand
        return None
    return None


# --------------------------------------------------------------------------------------
# 8. Cache Schema & SQLite Storage (E-08, E-09, 4.5, 4.5a)
# --------------------------------------------------------------------------------------

LAYOUT_VERSION = "layout_v1"

#: The legacy loader's own version, folded into the schema hash so that a change to WHAT THE LOADER
#: READS rebuilds every existing cache (backlog `suth7l`). Without it the hash covers only the field
#: registry, so a loader fix leaves each cache built by the old loader in place: rows are reloaded
#: only when their source FILE changes, and a loader change touches no source file. Bump it whenever
#: `load_legacy_artifact` or its parsers change what they produce for an unchanged file.
#: "legacy_v3" (2026-11-07, suth7l): bullet blocks without a `# ` title are read; YAML front matter
#: is read for every record that opens with `---`; per-type fields are written to their tables.
#: "legacy_v4" (2026-11-17, 1dvb08): parse `- Scope-Exceeded:` in metadata_region into `scope_result`
#: / `out_of_scope_paths` / `scope_exceeded_raw` and project unlogged `scope_exceptions`.
#: "legacy_v5" (2026-11-17, 6oi2nu): scan extra roots from `selectors.record_dirs` as `@repo/...`,
#: derive deterministic `id6` values for id-less records (`id_derived`), and add `artifacts.id_derived`.
#: "legacy_v6" (2026-11-18, cdglt1): add `artifacts.legacy_raw_status` and `artifacts.legacy_raw_set`,
#: enforce strict `^- <Key>:` bullet matching and lowercase scalar normalization for YAML front matter.
#: "legacy_v7" (2026-11-18, r81uvz): map legacy backlog `- Kind:` bullets to `work_kind` when `- Work-Kind:` is absent.
#: "legacy_v8" (2026-11-19, xxdzcq): map prompt `Kind`/`kind` to `prompt_kind` and `Created`/`created` to `created_day`, and set `artifact_row["created_day"]` for prompts.
#: "legacy_v9" (2026-11-21, dqutt8): extract workflow history via the shared history-block reader (now `history_records`) for both bullet and YAML records (fixing indented-line leaks and YAML research history), and register `blocks_release` on `research`.
#: "legacy_v10" (2026-11-21): register `item_dependencies` and `dependency_declaration` on `backlog`, `spec`, and `research` so non-IPD dependency edges reach the cache and `attention.scan()`.
LEGACY_LOADER_VERSION = "legacy_v10"

# The 4.5a Table Set as listed in E-08: exactly 26 tables
CACHE_TABLES_4_5A: Tuple[str, ...] = (
    "actors",
    "artifact_paths",
    "artifacts",
    "backlog",
    "dependencies",
    "directories",
    "events",
    "field_changes",
    "files",
    "gates",
    "graduation_targets",
    "ipd",
    "lineage",
    "meta",
    "prompt",
    "release",
    "release_gates",
    "research",
    "rev_log_states",
    "rev_mirrors",
    "review_files",
    "reviews",
    "roadmap",
    "scope_exceptions",
    "scope_paths",
    "spec",
    "walkthrough",
)


def compute_schema_hash(
    registry: Optional[Dict[str, Dict[str, FieldDef]]] = None,
) -> str:
    """Compute the SHA-256 hash of the canonical registry + layout version constant."""
    reg = registry if registry is not None else REGISTRY
    items = []
    for t in sorted(reg.keys()):
        field_items = []
        for f in sorted(reg[t].keys()):
            fdef = reg[t][f]
            vals = sorted(list(fdef.allowed_values)) if fdef.allowed_values else []
            field_items.append((f, fdef.value_type, fdef.ownership, vals))
        items.append((t, field_items))
    canon_bytes = json.dumps(
        {"version": LAYOUT_VERSION, "loader": LEGACY_LOADER_VERSION, "registry": items},
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canon_bytes).hexdigest()


def generate_schema(registry: Optional[Dict[str, Dict[str, FieldDef]]] = None) -> str:
    """Generate DDL for the 4.5a cache tables and indexes from the field registry."""
    reg = registry if registry is not None else REGISTRY
    statements: List[str] = [
        """CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS directories (
            path TEXT PRIMARY KEY,
            mtime_ns INTEGER
        );""",
        """CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            file_role TEXT,
            id6 TEXT,
            size INTEGER,
            mtime_ns INTEGER,
            content_digest TEXT,
            loaded_at TEXT,
            load_error TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS artifacts (
            id6 TEXT PRIMARY KEY,
            type TEXT,
            path TEXT,
            disposition TEXT,
            status TEXT,
            title TEXT,
            short_description TEXT,
            set_id TEXT,
            order_nn INTEGER,
            filename_date TEXT,
            created_day TEXT,
            created_at TEXT,
            updated_at TEXT,
            last_history_day TEXT,
            last_seq INTEGER,
            valid INTEGER,
            defect TEXT,
            id_derived INTEGER DEFAULT 0,
            legacy_raw_status TEXT,
            legacy_raw_set TEXT
        );""",
    ]

    # Per-type tables
    for record_type in sorted(SUPPORTED_TYPES):
        col_defs = ["id6 TEXT PRIMARY KEY"]
        type_fields = reg.get(record_type, {})
        for fname in sorted(type_fields.keys()):
            fdef = type_fields[fname]
            sql_type = "INTEGER" if fdef.value_type == "integer" else "TEXT"
            col_defs.append(f'"{fname}" {sql_type}')
        cols_sql = ",\n            ".join(col_defs)
        statements.append(
            f"""CREATE TABLE IF NOT EXISTS "{record_type}" (\n            {cols_sql}\n        );"""
        )

    # Child and relationship tables
    statements.extend(
        [
            """CREATE TABLE IF NOT EXISTS scope_paths (
            id6 TEXT,
            ordinal INTEGER,
            path TEXT,
            PRIMARY KEY (id6, ordinal)
        );""",
            """CREATE TABLE IF NOT EXISTS artifact_paths (
            id6 TEXT,
            seq INTEGER,
            path TEXT,
            at TEXT,
            actor_id TEXT,
            by_human INTEGER,
            op TEXT,
            verb TEXT,
            PRIMARY KEY (id6, seq)
        );""",
            """CREATE TABLE IF NOT EXISTS scope_exceptions (
            id6 TEXT,
            ordinal INTEGER,
            path TEXT,
            reason TEXT,
            exception_kind TEXT,
            source TEXT,
            PRIMARY KEY (id6, ordinal)
        );""",
            """CREATE TABLE IF NOT EXISTS dependencies (
            dependent_id6 TEXT,
            ordinal INTEGER,
            condition TEXT,
            target_type TEXT,
            required_status TEXT,
            target_raw TEXT,
            target_id6 TEXT,
            PRIMARY KEY (dependent_id6, ordinal)
        );""",
            """CREATE TABLE IF NOT EXISTS lineage (
            child_id6 TEXT,
            relation TEXT,
            parent_raw TEXT,
            parent_id6 TEXT,
            PRIMARY KEY (child_id6, relation, parent_raw)
        );""",
            """CREATE TABLE IF NOT EXISTS graduation_targets (
            source_id6 TEXT,
            ordinal INTEGER,
            target_raw TEXT,
            target_set_id TEXT,
            PRIMARY KEY (source_id6, ordinal)
        );""",
            """CREATE TABLE IF NOT EXISTS release_gates (
            id6 TEXT,
            release_raw TEXT,
            release_id6 TEXT,
            PRIMARY KEY (id6, release_raw)
        );""",
            """CREATE TABLE IF NOT EXISTS gates (
            id6 TEXT PRIMARY KEY,
            gate_kind TEXT,
            gate_ref TEXT,
            gate_summary TEXT
        );""",
            """CREATE TABLE IF NOT EXISTS actors (
            actor_id TEXT PRIMARY KEY,
            tool TEXT,
            ace TEXT,
            host TEXT,
            model TEXT,
            variant TEXT,
            run_id TEXT,
            attempt INTEGER
        );""",
            """CREATE TABLE IF NOT EXISTS events (
            id6 TEXT,
            seq INTEGER,
            append INTEGER,
            op TEXT,
            at TEXT,
            actor_id TEXT,
            by_human INTEGER,
            from_status TEXT,
            to_status TEXT,
            path TEXT,
            message TEXT,
            raw TEXT,
            PRIMARY KEY (id6, seq)
        );""",
            """CREATE TABLE IF NOT EXISTS field_changes (
            id6 TEXT,
            seq INTEGER,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            unset INTEGER,
            PRIMARY KEY (id6, seq, field)
        );""",
            """CREATE TABLE IF NOT EXISTS review_files (
            path TEXT PRIMARY KEY,
            subject_id6 TEXT,
            review_ref TEXT,
            round_count INTEGER,
            parse_ok INTEGER
        );""",
            """CREATE TABLE IF NOT EXISTS reviews (
            subject_id6 TEXT,
            seq INTEGER,
            review_ref TEXT,
            round INTEGER,
            review_kind TEXT,
            verdict TEXT,
            legacy_verdict TEXT,
            observed_day TEXT,
            readiness TEXT,
            review_depth TEXT,
            findings_summary TEXT,
            reviewer TEXT,
            PRIMARY KEY (subject_id6, seq)
        );""",
            """CREATE TABLE IF NOT EXISTS rev_log_states (
            log_blob_sha TEXT PRIMARY KEY,
            id6 TEXT,
            status TEXT,
            last_seq INTEGER,
            state_json TEXT
        );""",
            """CREATE TABLE IF NOT EXISTS rev_mirrors (
            md_blob_sha TEXT PRIMARY KEY,
            id6 TEXT,
            status TEXT
        );""",
            # Indexes
            "CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);",
            "CREATE INDEX IF NOT EXISTS idx_artifacts_type_status ON artifacts(type, status);",
            "CREATE INDEX IF NOT EXISTS idx_artifacts_set_order ON artifacts(set_id, order_nn);",
            "CREATE INDEX IF NOT EXISTS idx_dependencies_target_id6 ON dependencies(target_id6);",
            "CREATE INDEX IF NOT EXISTS idx_lineage_parent_id6 ON lineage(parent_id6);",
            "CREATE INDEX IF NOT EXISTS idx_graduation_targets_set_id ON graduation_targets(target_set_id);",
            "CREATE INDEX IF NOT EXISTS idx_release_gates_release_id6 ON release_gates(release_id6);",
            "CREATE INDEX IF NOT EXISTS idx_events_id6_op ON events(id6, op);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_subject_kind_seq ON reviews(subject_id6, review_kind, seq);",
            "CREATE INDEX IF NOT EXISTS idx_artifact_paths_path ON artifact_paths(path);",
        ]
    )
    return "\n\n".join(statements)


def init_cache(
    conn: sqlite3.Connection,
    records_root: Path,
    registry: Optional[Dict[str, Dict[str, FieldDef]]] = None,
) -> None:
    """Initialize or reset the SQLite cache schema and metadata."""
    schema_sql = generate_schema(registry)
    # Wrap DDL statements in a single explicit transaction so `executescript` does not
    # issue a separate disk fsync per CREATE TABLE / CREATE INDEX statement.
    conn.executescript(f"BEGIN;\n{schema_sql}\nCOMMIT;")
    with conn:
        shash = compute_schema_hash(registry)
        now_str = datetime.datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("schema_hash", shash),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("records_root", str(records_root.resolve())),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("built_at", now_str),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("tool_version", "1.0.0"),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", ("runs_root", "")
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("run_reader_version", "1.0.0"),
        )


_SQLITE_CONNECT_TIMEOUT = 30.0
_SQLITE_BUSY_TIMEOUT_MS = 30000
_CACHE_REFRESH_LOCK_TIMEOUT = 30.0


def _is_sqlite_lock_error(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    msg = str(exc).lower()
    return "locked" in msg or "busy" in msg


def _db_file_path(conn: sqlite3.Connection) -> Optional[Path]:
    try:
        rows = conn.execute("PRAGMA database_list").fetchall()
    except Exception:
        return None
    for row in rows:
        if len(row) >= 3 and row[1] == "main" and row[2]:
            return Path(str(row[2]))
    return None


@contextlib.contextmanager
def _cache_refresh_lock(
    db_path: Path, *, timeout: float = _CACHE_REFRESH_LOCK_TIMEOUT
) -> Any:
    """Serialize persistent `index.db` rebuild/refresh writes across concurrent processes."""
    lock_path = db_path.parent / f"{db_path.name}.lock"
    deadline = time.monotonic() + max(0.0, timeout)
    held = None
    while True:
        try:
            held = _lock.acquire(lock_path)
            break
        except _lock.LockBusy:
            if time.monotonic() >= deadline:
                break
            time.sleep(0.02)
        except OSError:
            break
    try:
        yield held is not None
    finally:
        if held is not None:
            with contextlib.suppress(Exception):
                held.release()


def open_cache(
    records_root: Path,
    state_root: Optional[Path] = None,
    *,
    in_memory: bool = False,
    registry: Optional[Dict[str, Dict[str, FieldDef]]] = None,
) -> sqlite3.Connection:
    """Open or rebuild the SQLite cache. Falls back to in-memory on error."""
    records_root = Path(records_root).resolve()
    shash = compute_schema_hash(registry)

    if in_memory or state_root is None:
        conn = sqlite3.connect(":memory:")
        init_cache(conn, records_root, registry)
        return conn

    db_path = Path(state_root) / "index.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if db_path is an unopenable directory (portable test case for failure)
    if db_path.is_dir():
        conn = sqlite3.connect(":memory:")
        init_cache(conn, records_root, registry)
        return conn

    def _try_open_existing() -> Tuple[Optional[sqlite3.Connection], bool, bool]:
        """Return (conn, need_rebuild, lock_contended)."""
        if not db_path.exists():
            return None, True, False
        conn_local: Optional[sqlite3.Connection] = None
        try:
            conn_local = sqlite3.connect(str(db_path), timeout=_SQLITE_CONNECT_TIMEOUT)
            conn_local.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS};")
            conn_local.execute("PRAGMA journal_mode=WAL;")
            row_hash = conn_local.execute(
                "SELECT value FROM meta WHERE key = 'schema_hash'"
            ).fetchone()
            row_root = conn_local.execute(
                "SELECT value FROM meta WHERE key = 'records_root'"
            ).fetchone()
            if (
                not row_hash
                or row_hash[0] != shash
                or not row_root
                or row_root[0] != str(records_root)
            ):
                conn_local.close()
                return None, True, False
            return conn_local, False, False
        except Exception as exc:
            if conn_local is not None:
                with contextlib.suppress(Exception):
                    conn_local.close()
            if _is_sqlite_lock_error(exc):
                # Lock contention is NOT corruption: never unlink an index.db actively held
                # by another process/worker; fall back to an in-memory cache instead.
                return None, False, True
            return None, True, False

    conn_ok, need_rebuild, lock_contended = _try_open_existing()
    if conn_ok is not None:
        return conn_ok
    if lock_contended:
        conn = sqlite3.connect(":memory:")
        init_cache(conn, records_root, registry)
        return conn

    if need_rebuild:
        try:
            with _cache_refresh_lock(db_path) as acquired:
                if acquired:
                    # Another worker may have already rebuilt index.db while we waited.
                    conn_rechecked, still_rebuild, still_locked = _try_open_existing()
                    if conn_rechecked is not None:
                        return conn_rechecked
                    if still_locked or not still_rebuild:
                        conn = sqlite3.connect(":memory:")
                        init_cache(conn, records_root, registry)
                        return conn
                    if db_path.exists():
                        if db_path.is_dir():
                            shutil.rmtree(db_path)
                        else:
                            with contextlib.suppress(FileNotFoundError):
                                db_path.unlink()
                            for suffix in ("-wal", "-shm"):
                                with contextlib.suppress(OSError):
                                    Path(f"{db_path}{suffix}").unlink()
                    conn = sqlite3.connect(
                        str(db_path), timeout=_SQLITE_CONNECT_TIMEOUT
                    )
                    conn.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS};")
                    conn.execute("PRAGMA journal_mode=WAL;")
                    init_cache(conn, records_root, registry)
                    return conn
        except Exception:
            pass
        # Fallback to in-memory
        conn = sqlite3.connect(":memory:")
        init_cache(conn, records_root, registry)
        return conn

    conn = sqlite3.connect(":memory:")
    init_cache(conn, records_root, registry)
    return conn


# --------------------------------------------------------------------------------------
# 9. Legacy Loader (E-11, E-12, Section 7 Phase B)
# --------------------------------------------------------------------------------------

_BULLET_RE = re.compile(r"^\s*-\s*([A-Za-z0-9_-]+):\s*(.*)$")
_STRICT_BULLET_RE = re.compile(r"^- ([A-Za-z0-9_-]+):[ \t]*(.*)$")
_LOOSE_BULLET_RE = re.compile(r"^-[ \t]*([A-Za-z0-9_-]+):[ \t]*(.*)$")
_YAML_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*)$")
_HEADING2_RE = re.compile(r"^#{2,}(?:[ \t]|$)")


def _normalize_yaml_scalar(value: str) -> str:
    """Strip symmetric outer quotes/backticks from a YAML scalar string."""
    out = value.strip()
    while len(out) >= 2 and out[0] == out[-1] and out[0] in "`\"'":
        out = out[1:-1].strip()
    return out


def _first_token(value: Optional[str]) -> Optional[str]:
    """Return the first whitespace-delimited token of ``value``, or None."""
    if not value:
        return None
    parts = value.strip().split()
    return parts[0] if parts else None


def _first_set_token(value: Optional[str]) -> Optional[str]:
    """Return the terse set-id before any '(' comment, matching plans_index."""
    if not value or not value.strip():
        return None
    head = value.split("(", 1)[0].strip()
    parts = head.split()
    return parts[0] if parts else None


#: The IPD metadata-block LINE grammar, owned here (moved with `parse_metadata_block` by ad86ym).
_IPD_META_LINE_RE = re.compile(r"^- (?P<field>[A-Za-z][A-Za-z /-]*?):\s?(?P<value>.*)$")


def _parse_metadata_block(
    lines: Sequence[str],
) -> Tuple[Dict[str, str], List[_ipd_schema.MetaError]]:
    """Parse the contiguous ``- Field: value`` run given the lines BETWEEN the H1 and the first H2.

    Returns (fields, errors). Duplicate fields and unknown fields are recorded as errors. Pure;
    the caller is responsible for locating the block.
    """
    fields: Dict[str, str] = {}
    errors: List[_ipd_schema.MetaError] = []
    seen: Dict[str, int] = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        m = _IPD_META_LINE_RE.match(line)
        if not m:
            # A non-bullet, non-blank line inside the metadata run ends the block for our purposes.
            continue
        field = m.group("field").strip()
        value = m.group("value").strip()
        seen[field] = seen.get(field, 0) + 1
        if seen[field] == 2:
            errors.append(_ipd_schema.MetaError(field, "duplicate field"))
        if field not in _ipd_schema.META_RECOGNIZED:
            errors.append(_ipd_schema.MetaError(field, "unknown field"))
        # First occurrence wins for the value map; duplicates already flagged.
        fields.setdefault(field, value)
    return fields, errors


def parse_metadata_block(
    lines: Sequence[str],
) -> Tuple[Dict[str, str], List[_ipd_schema.MetaError]]:
    """Public wrapper for callers that need the line-level error list (``ipd_lint.parse``).

    The duplicate and unknown field diagnostics (IPD-M102/M103) are not part of `State`, so the
    linter reads them here rather than through `read_text`.
    """
    return _parse_metadata_block(lines)


_TOP_BULLET_KEY_RE = re.compile(r"^- ([A-Za-z0-9_-]+):(?:\s*(.*))?$")


def list_metadata_bullets(
    text: str, *, leading_block_only: bool = False
) -> List[Tuple[str, str]]:
    """Return top-level ``- Key: value`` metadata bullets in file order.

    Preserves original key spelling and every duplicate occurrence as ``(key, raw_value)``
    tuples. Normalizes ``\\r\\n`` to ``\\n`` and splits on ``\\n`` (never ``str.splitlines()``,
    which splits on bare ``\\r`` or U+2028).

    When ``leading_block_only`` is ``False`` (default, for specs and general metadata blocks),
    scans every line before the first ``## `` heading, skipping titles, blank lines, and
    non-bullet prose.

    When ``leading_block_only`` is ``True`` (for backlog items), stops at the first ``## ``
    heading or the first non-blank line that does not start with ``"- "`` (including indented
    sub-bullets).
    """
    out: List[Tuple[str, str]] = []
    if not text:
        return out
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            break
        if leading_block_only and line.strip() and not line.startswith("- "):
            break
        m = _TOP_BULLET_KEY_RE.match(line)
        if m:
            out.append((m.group(1), m.group(2) or ""))
    return out


PROMPT_METADATA_TRAILER: str = (
    "This HTML comment is pipeline metadata only; it is invisible when pasted "
    "into a chat and is not part of the prompt."
)

_AW_PROMPT_OPEN_RE = re.compile(r"\A<!--\s*aw-prompt:")


def has_prompt_metadata_comment(text: str) -> bool:
    """Return True iff ``text`` opens with a leading ``<!-- aw-prompt: ... -->`` comment."""
    if not text:
        return False
    return bool(_AW_PROMPT_OPEN_RE.match(text.split("\n", 1)[0]))


def inject_prompt_metadata_id6(
    text: str, *, id6: str, set_id: Optional[str] = None
) -> str:
    """Return ``text`` with ``Id:`` (and optionally ``Set:``) written into its metadata comment.

    Idempotent: a comment that already declares a valid ``Id:`` is returned unchanged.
    Commentless prompts (and prompts whose only ``aw-prompt`` comment appears after line 1)
    are returned unchanged to preserve prompt purity (no comment is ever minted).
    """
    if not has_prompt_metadata_comment(text):
        return text
    lines = text.split("\n")
    first = lines[0]
    parsed_fields = _parse_metadata_comment(first)
    existing_id = _first_token(parsed_fields.get("Id"))
    if existing_id and _core.ID6_RE.fullmatch(existing_id):
        return text

    additions = [f"Id: {id6}"]
    set_text = (set_id or "").strip()
    has_set = bool(parsed_fields.get("Set") or parsed_fields.get("set"))
    if set_text and not has_set:
        additions.append(f"Set: {set_text}")
    insert = " | ".join(additions)

    m_kind = re.search(r"(Kind:\s*[^|]+?)(\s*\|)", first)
    if m_kind:
        updated = first[: m_kind.end(1)] + f" | {insert}" + first[m_kind.end(1) :]
    else:
        updated = first.replace(
            f" . {PROMPT_METADATA_TRAILER}",
            f" | {insert} . {PROMPT_METADATA_TRAILER}",
            1,
        )
        if updated == first:
            updated = re.sub(r"\s*-->\s*\Z", f" | {insert} -->", first)
    lines[0] = " ".join(updated.split())
    return "\n".join(lines)


def update_prompt_metadata_status(text: str, status: str) -> str:
    """Return ``text`` with ``Status: <status>`` updated or inserted in its metadata comment.

    Idempotent: if the comment already declares ``status``, returns ``text`` unchanged.
    Commentless prompts (and prompts whose only ``aw-prompt`` comment appears after line 1)
    are returned unchanged to preserve prompt purity (no comment is ever minted).
    """
    if not has_prompt_metadata_comment(text):
        return text
    lines = text.split("\n")
    first = lines[0]
    current = read_text(first, record_type="prompt").legacy_raw_status
    if current == status:
        return text

    if current is not None:
        updated = re.sub(
            r"((?:\A|<!--\s*aw-prompt:|\|)\s*Status:\s*)(?:(?!-->)[^|.\s])+",
            rf"\g<1>{status}",
            first,
            count=1,
        )
    else:
        m_set = re.search(r"(Set:\s*[^|]+?)(\s*\|)", first)
        if m_set:
            updated = (
                first[: m_set.end(1)] + f" | Status: {status}" + first[m_set.end(1) :]
            )
        else:
            m_id = re.search(r"(Id:\s*[^|]+?)(\s*\|)", first)
            if m_id:
                updated = (
                    first[: m_id.end(1)] + f" | Status: {status}" + first[m_id.end(1) :]
                )
            else:
                m_kind = re.search(r"(Kind:\s*[^|]+?)(\s*\|)", first)
                if m_kind:
                    updated = (
                        first[: m_kind.end(1)]
                        + f" | Status: {status}"
                        + first[m_kind.end(1) :]
                    )
                else:
                    updated = first.replace(
                        f" . {PROMPT_METADATA_TRAILER}",
                        f" | Status: {status} . {PROMPT_METADATA_TRAILER}",
                        1,
                    )
                    if updated == first:
                        updated = re.sub(
                            r"\s*-->\s*\Z", f" | Status: {status} -->", first
                        )

    lines[0] = " ".join(updated.split())
    return "\n".join(lines)


def _parse_metadata_comment(first_line: str) -> Dict[str, str]:
    """Key/value pairs of a prompt's leading ``<!-- aw-managed-prompt: ... -->`` or
    ``<!-- aw-prompt: ... -->`` metadata comment, or ``{}`` when ``first_line`` carries neither.

    The trailing ``. This HTML comment is ...`` pipeline trailer is not part of the field list.
    """
    comment_bullets: Dict[str, str] = {}
    m_prompt = _MANAGED_PROMPT_COMMENT_RE.match(first_line)
    if m_prompt:
        for item in m_prompt.group(1).split("|"):
            if ":" in item:
                k, v = item.split(":", 1)
                comment_bullets[k.strip()] = v.strip()
        return comment_bullets
    m_aw = re.match(r"\A<!--\s*aw-prompt:\s*(.*?)\s*-->", first_line, re.DOTALL)
    if not m_aw:
        return comment_bullets
    inner = m_aw.group(1)
    split_aw = _split_prompt_comment(first_line)
    if split_aw is not None and split_aw[2]:
        inner = split_aw[1]
    else:
        for marker in (
            f" . {PROMPT_METADATA_TRAILER}",
            " . This HTML comment is",
            PROMPT_METADATA_TRAILER,
        ):
            if marker in inner:
                inner = inner.split(marker, 1)[0].strip()
                break
    for item in inner.split("|"):
        if ":" in item:
            k, v = item.split(":", 1)
            comment_bullets[k.strip()] = v.strip()
    return comment_bullets


# --------------------------------------------------------------------------------------
# Workflow-history grammar (IPD `bxupy8`, spec `4sd62s` C5). Private copies, unchanged in
# behavior, of the ``attention_contract`` history-block reader (with its ``HistoryBlock`` result and
# the record pattern), newest-record rule and ``last_history_at`` derivation, so the one metadata
# reader owns the one history grammar. IPD ``csobg7`` deleted those originals.
# A caller holding only TEXT reaches it through :func:`history_records`.
# --------------------------------------------------------------------------------------

_HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")
_HISTORY_HEADING_RE = re.compile(r"(?m)^## Workflow history[ \t]*\r?$")
_HISTORY_SECTION_HEADING_RE = re.compile(r"^##[ \t]+Workflow history[ \t]*$")
_HISTORY_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class HistoryBlock(NamedTuple):
    records: List[str]
    record_lines: List[str]
    body: str


class HistorySection(NamedTuple):
    before_heading: str
    block: HistoryBlock
    has_heading: bool


def _iter_unfenced_lines(text: str) -> List[Tuple[int, int, int, str]]:
    """Return ``(lineno, start, next_start, line)`` for lines outside fenced code blocks.

    ``lineno`` is 1-based; ``start`` and ``next_start`` are character offsets into ``text``.
    Splits only on ``\\n`` (stripping a trailing ``\\r``) so offsets remain exact and bare
    control characters never fabricate synthetic lines.
    """
    if not text:
        return []
    out: List[Tuple[int, int, int, str]] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    lineno = 0
    pos = 0
    n = len(text)
    while pos < n:
        nl = text.find("\n", pos)
        if nl == -1:
            raw_with_eol = text[pos:]
            next_pos = n
        else:
            raw_with_eol = text[pos : nl + 1]
            next_pos = nl + 1
        lineno += 1
        line = raw_with_eol.rstrip("\r\n")
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                ch = stripped[0]
                flen = len(stripped) - len(stripped.lstrip(ch))
                # CommonMark: backtick fence info strings cannot contain backticks.
                if not (ch == "`" and "`" in stripped[flen:]):
                    in_fence = True
                    fence_char = ch
                    fence_len = flen
                    pos = next_pos
                    continue
        else:
            if (
                stripped.startswith(fence_char * fence_len)
                and stripped.lstrip(fence_char) == ""
            ):
                in_fence = False
                fence_char = ""
                fence_len = 0
            pos = next_pos
            continue
        out.append((lineno, pos, next_pos, line))
        pos = next_pos
    return out


def _history_block_from_after(after: str, *, need_body: bool = True) -> HistoryBlock:
    """Parse a :class:`HistoryBlock` from the slice immediately following the heading line."""
    records: List[str] = []
    record_lines: List[str] = []

    continuing = False
    current_bullet_is_record = False

    if (
        not need_body
        and "\r" not in after
        and "\x85" not in after
        and "\u2028" not in after
        and "\u2029" not in after
    ):
        # Fast path when caller only needs records/record_lines: avoid splitting the entire
        # remainder of large documents after the terminating heading.
        pos = 0
        n = len(after)
        while pos < n:
            nl = after.find("\n", pos)
            if nl == -1:
                line = after[pos:]
                pos = n
            else:
                line = after[pos:nl]
                pos = nl + 1
            if line.startswith("## "):
                break
            is_indented = line.startswith(" ") or line.startswith("\t")
            is_blank = not line.strip()
            if not is_blank and not is_indented and not line.startswith("- "):
                break
            if not is_blank and is_indented and not continuing:
                break

            if is_blank:
                continuing = False
                current_bullet_is_record = False
            elif not is_indented and line.startswith("- "):
                stripped_line = line.rstrip()
                if _HISTORY_RECORD_RE.match(stripped_line):
                    records.append(stripped_line)
                    record_lines.append(stripped_line)
                    continuing = True
                    current_bullet_is_record = True
                else:
                    continuing = True
                    current_bullet_is_record = False
            elif is_indented:
                if current_bullet_is_record:
                    record_lines.append(line.rstrip())
        return HistoryBlock(records, record_lines, "")

    lines = after.splitlines(keepends=True)
    terminating_idx: Optional[int] = None

    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")
        if line.startswith("## "):
            terminating_idx = idx
            break
        is_indented = line.startswith(" ") or line.startswith("\t")
        is_blank = not line.strip()
        if not is_blank and not is_indented and not line.startswith("- "):
            terminating_idx = idx
            break
        if not is_blank and is_indented and not continuing:
            terminating_idx = idx
            break

        if is_blank:
            continuing = False
            current_bullet_is_record = False
        elif not is_indented and line.startswith("- "):
            stripped_line = line.rstrip()
            if _HISTORY_RECORD_RE.match(stripped_line):
                records.append(stripped_line)
                record_lines.append(stripped_line)
                continuing = True
                current_bullet_is_record = True
            else:
                continuing = True
                current_bullet_is_record = False
        elif is_indented:
            if current_bullet_is_record:
                record_lines.append(line.rstrip())

    if not need_body or terminating_idx is None:
        body = ""
    else:
        rem_lines = [ln.rstrip("\r\n") for ln in lines[terminating_idx:]]
        while rem_lines and not rem_lines[0].strip():
            rem_lines.pop(0)
        body = "\n".join(rem_lines).rstrip()

    return HistoryBlock(records, record_lines, body)


def _history_block(text: str, *, need_body: bool = True) -> HistoryBlock:
    """The canonical, pure reader for an artifact's ``## Workflow history`` block.

    States the bounding rule ONCE and returns a :class:`HistoryBlock` with:
      - ``records``: column-zero records matching :data:`_HISTORY_RECORD_RE` against ``line.rstrip()``
        (never ``strip()``), returned with trailing whitespace stripped, in file order (newest-first).
      - ``record_lines``: flat, file-order list of every record line FOLLOWED BY its indented
        continuation lines (each ``rstrip()``ed, indentation KEPT, blank lines dropped; non-record
        bullets and their continuations excluded). `"\n".join(record_lines)` re-emits each record
        with its wrapped text.
      - ``body``: remaining text from the terminating line on with leading blank lines removed and
        trailing whitespace ``rstrip()``ed, but the first line's indentation PRESERVED (never
        ``.strip()``/``.lstrip()``; ``""`` when there is none).

    THE BOUNDING RULE (plan ``kgv213``, Set ``histdedup``):
    1. Locate the heading with ``(?m)^## Workflow history[ \t]*$`` (missing heading yields
       ``HistoryBlock([], [], "")``).
    2. Scan subsequent lines. The block ENDS at:
       - the next line starting with ``## ``, OR
       - the first non-blank line starting at COLUMN ZERO that is not a ``- `` bullet, OR
       - an INDENTED non-blank line that does not directly continue a bullet (a blank line ends
         continuation, so a blank-separated indented quotation is NOT part of the block).
    3. Inside the block, a record is a column-zero line matching :data:`_HISTORY_RECORD_RE` against
       ``line.rstrip()``. Any following indented line directly continuing it is part of ``record_lines``.
       Non-record bullets and their continuations are dropped from both ``records`` and ``record_lines``.

    CANONICAL NEWEST RECORD:
    ``_newest_history_record(_history_block(t).records)`` is the canonical newest record.

    WHY THIS RULE WAS CHOSEN (findings F-01..F-07):
    - F-01: Disagreement between readers (column-zero bounding vs. heading-only section slicing)
      caused `status_set` to judge an indented-only line as a duplicate while the writer could not
      preserve it, suppressing writes.
    - F-02..F-04: Strict bounding was wrong for plans wrapping records onto continuation lines (155 plans,
      F-03), while loose bounding re-opened the `tk1gqo` defect where indented prose quotations in bodies
      were counted as records (F-04). This rule agrees with today's answers across all 2489 tracked
      artifacts carrying history, changing zero consumer answers.
    - F-06: Writers need `record_lines` (not `records` alone) and a shared body boundary (`_extract_body`,
      E-06) so wrapped records and their following records are not duplicated on reattachment.
    - F-07: De-indenting a blank-separated indented quotation in `body` turns it into a column-zero record
      on the next rewrite (`tk1gqo` defect by another route); preserving leading indentation prevents this.
    """
    m = _HISTORY_HEADING_RE.search(text)
    if not m:
        return HistoryBlock([], [], "")

    after = text[m.end() :]
    if after.startswith("\r\n"):
        after = after[2:]
    elif after.startswith("\n"):
        after = after[1:]

    return _history_block_from_after(after, need_body=need_body)


def _newest_history_record(history_lines: List[str]) -> Optional[str]:
    """THE ONE RULE for "which of these ``## Workflow history`` lines is the newest": the FIRST one
    matching :data:`_HISTORY_RECORD_RE`, or ``None`` when there is no record.

    NEWEST-FIRST IS THE WRITER'S CONTRACT, not an assumption. Every history writer PREPENDS its new
    record directly under the heading: ``status_set.apply_status_change`` does it with
    ``new_lines.insert(i + 1, hist_entry)`` and documents it at length, and
    ``ipd_lifecycle._plan_status_events`` REVERSES a plan's inline records to get oldest-first on
    exactly that premise. So the first record in file order is the most recent one.

    WHY THIS FUNCTION EXISTS AT ALL, since the answer is a measured bug and not a tidy-up. There used
    to be TWO readers of this one question and they DISAGREED: ``plan_readiness
    .extract_newest_history_entry`` took the FIRST record (and carries an explicit warning that
    taking the last one "is the bug this function replaced"), while ``last_history_at`` right below
    took the LAST. Measured over this repository at ``2362b102`` with the production parser, the
    last-in-file-order rule reported a date that was NOT the artifact's newest record for 373 of 679
    multi-record plans, 153 of 200 backlog items and 8 of 21 specs. The defect was invisible for
    specs and backlog only because their inline history had been slimmed to a single line, where the
    first and last record coincide - which is why plan ``vhbvwz`` had to fix this reader BEFORE
    E-08 let those two trees keep a second line again.

    DELIBERATELY POSITIONAL, NOT MAX-BY-DATE, and this is a safety property rather than a style
    choice. A "newest = greatest date" scan was measured and REJECTED: it changes which record
    ``extract_newest_history_entry`` returns for 67 plans, and for 20 of those it flips
    ``plan_readiness.history_verdict_approves`` from False to True, because a plan's final dated
    ``approved``/``executed`` line would start being read as its newest REVIEW verdict. That function
    gates UNATTENDED promotion to an executable tier, so a date-max rule would silently widen a live
    approval gate. A record out of date order on disk is a data problem to report, never a licence
    for the reader to reorder history it cannot see the intent of.

    Pure and total; ``history_lines`` is an already-bounded section (see
    :func:`history_records` and :func:`history_section_lines`), never whole file text.
    """

    for line in history_lines:
        if _HISTORY_RECORD_RE.match(line):
            return line
    return None


def _last_history_at(
    history_lines: Sequence[Union[str, Dict[str, Any]]],
) -> Optional[str]:
    """Derive ``last_history_at`` from parsed ``## Workflow history`` lines or ``artifact_meta.history``
    event dicts: the date of the NEWEST record, or ``None`` when there is no record. Never uses file
    mtime (Section 8.5).

    The NAME is historical and is kept because it is the published field name in
    ``aw attention --format json`` and in the spec's Section 8.5; it means "the date this artifact was
    last touched", never "the date on the last line". :func:`_newest_history_record` is the single
    shared rule that decides which record that is, so no two readers in this toolkit can disagree
    about the answer.
    """

    if not history_lines:
        return None
    if isinstance(history_lines[0], dict):
        str_lines = [
            ev["line"]
            for ev in history_lines
            if isinstance(ev, dict) and isinstance(ev.get("line"), str) and ev["line"]
        ]
        if str_lines:
            newest = _newest_history_record(str_lines)
            if newest is None:
                return None
            m = _HISTORY_RECORD_RE.match(newest)
            return m.group("date") if m else None
        # Log-format events without legacy line records: newest event date (seq ASC -> last event).
        for ev in reversed(history_lines):
            if not isinstance(ev, dict):
                continue
            obs = ev.get("observed_day")
            if isinstance(obs, str) and _HISTORY_DATE_RE.match(obs.strip()):
                return obs.strip()
            at_val = ev.get("at")
            if isinstance(at_val, str) and len(at_val) >= 10:
                day = at_val[:10]
                if _HISTORY_DATE_RE.match(day):
                    return day
        return None
    newest = _newest_history_record(list(history_lines))  # type: ignore[arg-type]
    if newest is None:
        return None
    m = _HISTORY_RECORD_RE.match(newest)
    return m.group("date") if m else None


# A spec's status is a single front-matter bullet ``- Status: <bare-enum-token>`` with NO trailing
# prose. Moved here from ``attention_contract`` (IPD `csobg7`, spec `4sd62s` C5); a caller reaches
# it through :func:`spec_status_bullet`.
_SPEC_STATUS_RE = re.compile(r"^- Status:[ \t]*(?P<value>\S+)[ \t]*$")


def spec_status_bullet(line: str) -> Optional[str]:
    """Return the bare status token when ``line`` is a spec ``- Status: <token>`` bullet, else ``None``.

    A bullet carrying trailing prose (``- Status: approved (2026-09-25)``) is not a bare-enum status
    and answers ``None``. For a caller that needs the LINE INDEX of the status bullet (for example a
    rewriter), which :func:`read_text` does not report.
    """

    m = _SPEC_STATUS_RE.match(line)
    return m.group("value") if m else None


def history_records(text: str) -> HistoryBlock:
    """Return the ``## Workflow history`` block of artifact ``text`` as a :class:`HistoryBlock`.

    THE SINGLE HISTORY GRAMMAR for a caller that holds only TEXT (for example staged text with no
    id6, or a migration rewriting a file). A caller that has an id6 uses :func:`history` or
    :func:`read` instead. See :func:`_history_block` for the bounding rule and
    :func:`_newest_history_record` for which record is newest.
    """

    return _history_block(text)


def split_history_section(text: str) -> HistorySection:
    """Split ``text`` at its first unfenced column-zero ``## Workflow history`` heading.

    Locates an unfenced column-zero heading matching ``^##[ \\t]+Workflow history[ \\t]*$``
    and returns ``HistorySection(before_heading, block, has_heading)``. When no unfenced
    heading is present, returns ``HistorySection(text, HistoryBlock([], [], ""), False)``.
    """

    for _lineno, start, next_start, line in _iter_unfenced_lines(text):
        if _HISTORY_SECTION_HEADING_RE.match(line):
            return HistorySection(
                before_heading=text[:start],
                block=_history_block_from_after(text[next_start:]),
                has_heading=True,
            )
    return HistorySection(text, HistoryBlock([], [], ""), False)


def history_record_blocks(text: str) -> List[List[str]]:
    """Split the unfenced ``## Workflow history`` section into blank-line-separated record blocks.

    Scans from the first unfenced column-zero ``## Workflow history`` heading through the next
    unfenced ``## `` heading. Each returned block is a contiguous list of column-zero
    ``- YYYY-MM-DD ...`` records; indented continuation lines stay attached to the current block
    without splitting it.
    """

    in_hist = False
    blocks: List[List[str]] = []
    current_block: List[str] = []

    for _lineno, _start, _next_start, line in _iter_unfenced_lines(text):
        if not in_hist:
            if _HISTORY_SECTION_HEADING_RE.match(line):
                in_hist = True
            continue
        if line.startswith("## "):
            break
        if not line.strip():
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        stripped_right = line.rstrip()
        if _HISTORY_RECORD_RE.match(stripped_right):
            current_block.append(stripped_right)

    if current_block:
        blocks.append(current_block)
    return blocks


def history_section_lines(text: str) -> List[Tuple[int, str]]:
    """Return 1-based ``(lineno, raw_line)`` tuples for ``- `` bullets in ``## Workflow history``.

    Scans the first unfenced column-zero ``## Workflow history`` section through the next
    unfenced ``## `` heading, skipping fenced code blocks and collecting every bullet line
    matching ``raw_line.lstrip().startswith("- ")``.
    """

    in_hist = False
    out: List[Tuple[int, str]] = []

    for lineno, _start, _next_start, line in _iter_unfenced_lines(text):
        if not in_hist:
            if _HISTORY_SECTION_HEADING_RE.match(line):
                in_hist = True
            continue
        if line.startswith("## "):
            break
        if line.lstrip().startswith("- "):
            out.append((lineno, line))

    return out


def history_record_date(line: str) -> Optional[str]:
    """The ``YYYY-MM-DD`` date of ``line`` when it is one ``## Workflow history`` record
    (``- YYYY-MM-DD <text>``), else ``None``.

    The record grammar for a caller that already holds a single line (for example a line-by-line
    scanner, or a test filtering lines). It is the grammar :func:`history_records` applies; it does
    not bound the section, so a caller holding whole text uses :func:`history_records` instead.
    """

    m = _HISTORY_RECORD_RE.match(line)
    return m.group("date") if m else None


def is_history_record(line: str) -> bool:
    """True iff ``line`` is one ``## Workflow history`` record (see :func:`history_record_date`)."""

    return history_record_date(line) is not None


def _parse_bullet_metadata_with_loose(
    text: str,
) -> Tuple[Dict[str, str], Dict[str, str], Optional[str], List[str]]:
    """Parse strict `^- <Key>:` and loose `^-[ \\t]*<Key>:` bullets before first ##+ heading.

    Lines break only at `\\n` (after `\\r\\n` is normalized), as the deleted `specs._read_*` readers
    did. `str.splitlines()` also breaks at a bare `\\r`, C1 NEL, U+2028 and other separators, which
    would cut a bullet value short (hiding an unsafe control character from the descriptive-safety
    checks) and let text after it be read as a forged bullet.
    """
    bullets: Dict[str, str] = {}
    loose_bullets: Dict[str, str] = {}
    title: Optional[str] = None
    first_h1_done = False
    in_fence = False
    fence_char = ""
    fence_len = 0

    pos = 0
    n = len(text)
    while pos <= n:
        nl = text.find("\n", pos)
        if nl == -1:
            line = text[pos:]
            pos = n + 1
        else:
            line = text[pos:nl]
            if line.endswith("\r"):
                line = line[:-1]
            pos = nl + 1

        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                ch = stripped[0]
                in_fence = True
                fence_char = ch
                fence_len = len(stripped) - len(stripped.lstrip(ch))
                continue
        else:
            if (
                stripped.startswith(fence_char * fence_len)
                and stripped.lstrip(fence_char) == ""
            ):
                in_fence = False
                fence_char = ""
                fence_len = 0
            continue

        if not first_h1_done and stripped.startswith("# "):
            title = stripped[2:].strip()
            first_h1_done = True
            continue

        if stripped.startswith("##") and _HEADING2_RE.match(stripped):
            break

        if line.startswith("-"):
            m_strict = _STRICT_BULLET_RE.match(line)
            if m_strict:
                k = m_strict.group(1).strip()
                v = m_strict.group(2).strip()
                bullets.setdefault(k, v)
                loose_bullets.setdefault(k, v)
            else:
                m_loose = _LOOSE_BULLET_RE.match(line)
                if m_loose:
                    k_l = m_loose.group(1).strip()
                    v_l = m_loose.group(2).strip()
                    loose_bullets.setdefault(k_l, v_l)

    history_lines = _history_block(text, need_body=False).records
    return bullets, loose_bullets, title, history_lines


def _parse_bullet_metadata(
    text: str,
) -> Tuple[Dict[str, str], Optional[str], List[str]]:
    """Parse strict bullet block before first ## heading. Returns (bullets, title, history_lines).

    THE BULLET REGION STARTS AT THE TOP OF THE FILE, not after a `# ` title (backlog `suth7l`).
    It is the same region `artifact_meta.metadata_region` bounds every other reader to: everything
    before the first `##` heading, with an optional leading `# ` title inside it. Backlog items
    carry no title line at all (they open with `- Id:`), so a loader that started reading only
    after a title dropped every backlog item's bullets; measured on this repository on 2026-11-07,
    that cost 1146 backlog records their status in the cache.
    """
    bullets, _, title, history_lines = _parse_bullet_metadata_with_loose(text)
    return bullets, title, history_lines


def _parse_frontmatter(text: str) -> Optional[Dict[str, object]]:
    """Parse a leading ``---`` frontmatter block into a mapping, or None if absent/malformed.

    Copy of ``research_contract.parse_frontmatter`` with unchanged behavior (IPD `sq6v7i`), so the
    original can be deleted (IPD `bxupy8`) while its exact framing stays available here: scalars
    become ``str`` (empty string for an empty value), ``[a, b]`` becomes a ``list`` of trimmed
    strings (``[]`` for empty), a repeated key keeps its LAST value, and a block with no closing
    ``---`` is malformed (None). The loader's own `_parse_yaml_front_matter` differs (first value
    wins, lists stay strings) and is not replaced by this.
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: Dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [x.strip() for x in inner.split(",")] if inner else []
        else:
            data[key] = val
    return None


def front_matter_mapping(text: str) -> Optional[Dict[str, object]]:
    """Return ``text``'s leading ``---`` block as a raw key/value mapping, or None.

    For a caller that holds only TEXT and needs the verbatim research front-matter keys and their
    last-wins values (record creation, adoption and the m0001 migration), rather than the normalized
    `State` that `read_text` returns. See `_parse_frontmatter` for the exact framing.
    """

    return _parse_frontmatter(text)


def _parse_yaml_front_matter(text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Parse YAML front matter (research reports)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, None
    data: Dict[str, str] = {}
    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
        m = _YAML_KEY_RE.match(lines[i])
        if m:
            data.setdefault(m.group(1).strip(), m.group(2).strip())
    if closing_idx == -1:
        return {}, None
    title: Optional[str] = None
    for j in range(closing_idx + 1, len(lines)):
        if lines[j].strip().startswith("# "):
            title = lines[j].strip()[2:].strip()
            break
    return data, title


#: Per-process id6 collision pools for the legacy loader's fallback mint, keyed by resolved records
#: root (see `load_legacy_artifact`).
_LEGACY_MINT_POOLS: Dict[str, Set[str]] = {}


def stored_path(
    abs_path: Union[str, Path],
    records_root: Union[str, Path],
    repo_root: Optional[Union[str, Path]] = None,
) -> str:
    """Return the cache-stored path for ``abs_path``: records-relative or ``@repo/...``."""
    rec_resolved = _core._resolved_root(Path(records_root))
    abs_p = Path(abs_path)
    # Fast path: when abs_path is already normalized under rec_resolved with no symlink
    # component (the common case inside os.walk loops), avoid repeating realpath().
    if not abs_p.is_symlink():
        abs_str = str(abs_p)
        rec_str = str(rec_resolved)
        sep = os.sep
        rec_prefix = rec_str if rec_str.endswith(sep) else rec_str + sep
        if abs_str.startswith(rec_prefix) and ".." not in abs_str:
            rel = abs_str[len(rec_prefix) :]
            if rel:
                return rel.replace("\\", "/") if sep == "\\" else rel
    resolved = abs_p.resolve()
    try:
        return resolved.relative_to(rec_resolved).as_posix()
    except ValueError:
        pass
    if repo_root is not None:
        repo_resolved = _core._resolved_root(Path(repo_root))
        try:
            return "@repo/" + resolved.relative_to(repo_resolved).as_posix()
        except ValueError:
            pass
    raise ValueError(
        f"path {abs_path!r} is inside neither records_root {records_root!r} nor repo_root {repo_root!r}"
    )


def source_path(
    stored: Union[str, Path],
    records_root: Union[str, Path],
    repo_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Map a cache-stored path (records-relative or ``@repo/...``) back to a filesystem Path."""
    s = str(stored).replace("\\", "/")
    if s.startswith("@repo/"):
        if repo_root is None:
            raise ValueError(f"repo_root is required to resolve stored path {s!r}")
        rel = s[len("@repo/") :]
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise ValueError(f"unsafe @repo/ stored path: {s!r}")
        return Path(repo_root) / rel
    if not s or Path(s).is_absolute() or ".." in Path(s).parts:
        raise ValueError(f"unsafe stored path: {s!r}")
    return Path(records_root) / s


def _scan_repo_root(ctx: Any, records_root: Path) -> Optional[Path]:
    """Return the repository root for extra-root scanning and ``@repo/`` resolution."""
    if ctx is not None:
        raw_repo = getattr(ctx, "repo_root", None)
        if raw_repo:
            return Path(raw_repo).resolve()
        raw_target = getattr(ctx, "target_repo", None)
        if raw_target:
            return Path(raw_target).resolve()
    return _proj_ctx.record_git_root(records_root)


def derive_id6(stored: str, taken: Iterable[str]) -> str:
    """Derive a deterministic 6-char base36 id6 from ``stored`` avoiding ``taken``."""
    taken_set = taken if isinstance(taken, (set, frozenset)) else set(taken)
    alphabet = _core.ID6_ALPHABET
    base = len(alphabet)
    k = 0
    while True:
        digest = hashlib.sha256(f"{stored}\0{k}".encode("utf-8")).digest()
        val = int.from_bytes(digest[:8], "big")
        chars: List[str] = []
        for _ in range(_core.ID6_LENGTH):
            val, rem = divmod(val, base)
            chars.append(alphabet[rem])
        cand = "".join(reversed(chars))
        if cand not in taken_set:
            return cand
        k += 1


def _parse_scope_exceeded_bullet(raw_text: str) -> Tuple[List[Dict[str, str]], bool]:
    """Parse `- Scope-Exceeded:` bullet text into `{path, reason}` entries and a malformed flag."""
    entries: List[Dict[str, str]] = []
    malformed = False
    stripped = raw_text.strip()
    if not stripped:
        return entries, True
    for segment in raw_text.split(";"):
        seg = segment.strip()
        if not seg:
            malformed = True
            continue
        m = re.match(r"^(?P<path>[^()\s]+)\s+\((?P<reason>.*)\)$", seg)
        if not m:
            malformed = True
            continue
        entries.append({"path": m.group("path"), "reason": m.group("reason")})
    return entries, malformed


_LINEAGE_BULLET_KEYS: Dict[str, str] = {
    "From-Backlog": "from_backlog",
    "From-Spec": "from_spec",
    "From-Plan": "from_plan",
    "Supersedes": "supersedes",
}


def _extract_legacy_lineage(
    text: str,
    id6: str,
    *,
    is_yaml: bool = False,
    yaml_data: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Collect all metadata-region lineage bullets (preserving multi-bullet declarations)."""
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    if is_yaml and yaml_data is not None:
        for rel in ("from_backlog", "from_spec", "from_plan", "supersedes"):
            raw = yaml_data.get(rel)
            if not raw:
                continue
            raw_s = _normalize_yaml_scalar(str(raw))
            if raw_s and (rel, raw_s) not in seen:
                seen.add((rel, raw_s))
                m_id6 = _core.ID6_RE.search(raw_s)
                rows.append(
                    {
                        "child_id6": id6,
                        "relation": rel,
                        "parent_raw": raw_s,
                        "parent_id6": m_id6.group(0) if m_id6 else None,
                    }
                )
        return rows

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Workflow history") or re.match(
            r"^#{2,}(?:[ \t]|$)", stripped
        ):
            break
        m_strict = _STRICT_BULLET_RE.match(line)
        key: Optional[str] = None
        val: str = ""
        if m_strict:
            cand_k = m_strict.group(1).strip()
            if cand_k in _LINEAGE_BULLET_KEYS:
                key = cand_k
                val = m_strict.group(2).strip()
        if key is None:
            m_loose = _LOOSE_BULLET_RE.match(line)
            if m_loose and m_loose.group(1).strip() == "From-Spec":
                key = "From-Spec"
                val = m_loose.group(2).strip()
        if key is None or not val:
            continue
        rel = _LINEAGE_BULLET_KEYS[key]
        if (rel, val) in seen:
            continue
        seen.add((rel, val))
        m_id6 = _core.ID6_RE.search(val)
        rows.append(
            {
                "child_id6": id6,
                "relation": rel,
                "parent_raw": val,
                "parent_id6": m_id6.group(0) if m_id6 else None,
            }
        )
    return rows


def load_legacy_artifact(
    path: Path,
    records_root: Path,
    text: Optional[str] = None,
    *,
    repo_root: Optional[Path] = None,
    extra_taken: Optional[Iterable[str]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load an existing legacy .md artifact into cache projection rows."""
    if text is None:
        text = path.read_text(encoding="utf-8")

    filename = path.name
    scan_repo = (
        Path(repo_root)
        if repo_root is not None
        else _scan_repo_root(None, records_root)
    )
    rel_path = stored_path(path, records_root, scan_repo)
    disposition = path.parent.name

    # Identity detection order:
    # 1. _LEGACY_TIMESTAMP_RE first
    # 2. _CLUSTERED_PREFIX_RE
    # 3. parse_attributed
    id6: Optional[str] = None
    art_type: str = "ipd"
    set_id: Optional[str] = None
    order_nn: Optional[int] = None
    filename_date: Optional[str] = None
    ace_val: Optional[str] = None
    model_val: Optional[str] = None

    # Determine type from parent folder or facet
    type_map = {
        "plans": "ipd",
        "specs": "spec",
        "backlog": "backlog",
        "research": "research",
        "releases": "release",
        "prompts": "prompt",
        "walkthroughs": "walkthrough",
        "roadmaps": "roadmap",
    }
    if rel_path.startswith("@repo/"):
        from agent_workflows import status_set as _status_set

        detected = (
            _status_set.detect_artifact_type(path, scan_repo)
            if scan_repo is not None
            else None
        )
        top_dir = detected or ""
        art_type = _LEGACY_PLURAL_TO_TYPE.get(top_dir, "ipd")
    else:
        rel_parts = Path(rel_path).parts
        top_dir = rel_parts[0] if rel_parts else ""
        art_type = type_map.get(top_dir, "ipd")

    m_legacy = _naming._LEGACY_TIMESTAMP_RE.match(filename)
    if m_legacy:
        filename_date = m_legacy.group("date")
        try:
            order_nn = int(m_legacy.group("nn"))
        except Exception:
            order_nn = None
        # id6 is not in legacy timestamp name
    else:
        m_attr = _naming.parse_attributed(filename)
        if m_attr:
            filename_date = m_attr.date
            set_id = m_attr.set
            id6 = m_attr.id6
            try:
                order_nn = int(m_attr.nn)
            except Exception:
                order_nn = None
            ace_val = m_attr.ace
            model_val = m_attr.model
            if m_attr.type:
                art_type = m_attr.type
        else:
            m_clust = _naming.parse_clustered(filename)
            if m_clust:
                filename_date = m_clust.group("date")
                set_id = m_clust.group("set")
                id6 = m_clust.group("id6")
                try:
                    order_nn = int(m_clust.group("nn"))
                except Exception:
                    order_nn = None
                ftype = m_clust.group("type")
                if ftype:
                    art_type = ftype

    # A FILENAME FACET IS NOT ALWAYS A REGISTRY TYPE (backlog `suth7l`). Research records are named
    # by their KIND (`findings`, `research-report`, `roadmap`, `assessment`, ...), which
    # `parse_clustered`/`parse_attributed` return in the `type` slot, so `art_type` used to become
    # that kind: 21 distinct "types" were cached on this repository, none of them `research`, and
    # every per-type table lookup (keyed on the REGISTRY type) failed. The registry type is decided
    # by the records tree the file lives in when the facet is not itself a registry type, and the
    # facet is kept as the record's `research_kind`.
    facet_kind: Optional[str] = None
    if top_dir == "research" and art_type != "research":
        facet_kind = art_type
        art_type = "research"
    elif art_type not in REGISTRY:
        facet_kind = art_type
        # A roadmap is research-shaped (YAML front matter, a `kind`), so it shares that table.
        art_type = type_map.get(top_dir, "research")
        if art_type not in REGISTRY:
            art_type = "research"

    bullets: Dict[str, str] = {}
    title: Optional[str] = None
    history_lines: List[str] = []

    # ANY record that opens with a YAML fence is read as YAML front matter (backlog `suth7l`), not
    # only one whose type resolved to the literal "research". Research records carry a type FACET
    # (`findings`, `research-report`, `roadmap`, ...) that `parse_clustered` returns as the type,
    # so the old `art_type == "research"` test never matched them: their YAML `status:` reached
    # no column, which measured as 156 research and roadmap records with no cached status. A
    # bullet-format record in this repository never opens with `---` (measured: 166 tracked records
    # do, all YAML), but a fixture or another repository can open a bullet block with a bare `---`
    # rule, so the YAML branch is taken only when the fence actually yields YAML keys and no
    # bullet block follows; otherwise the bullet parser runs as before.
    _yaml_probe: Dict[str, str] = {}
    if text.startswith("---"):
        _yaml_probe, _ = _parse_yaml_front_matter(text)
    _after_fence = text.split("\n", 1)[1][:200] if "\n" in text else ""
    is_yaml_record = bool(_yaml_probe and not _BULLET_RE.search(_after_fence))
    raw_status_legacy: Optional[str] = None
    legacy_raw_set: Optional[str] = None
    yaml_id: Optional[str] = None
    yaml_status: Optional[str] = None

    if is_yaml_record:
        yaml_data, title = _parse_yaml_front_matter(text)
        bullets = dict(yaml_data)
        history_lines = _history_block(text).records
        raw_y_id = bullets.get("id")
        if raw_y_id:
            yaml_id = _first_token(_normalize_yaml_scalar(raw_y_id))
            if yaml_id and _core.ID6_RE.fullmatch(yaml_id) and not id6:
                id6 = yaml_id
        raw_y_set = bullets.get("set")
        if raw_y_set:
            norm_y_set = _normalize_yaml_scalar(raw_y_set)
            tok_y_set = _first_set_token(norm_y_set)
            legacy_raw_set = (
                _normalize_yaml_scalar(tok_y_set) or None if tok_y_set else None
            )
            if legacy_raw_set and not set_id:
                set_id = legacy_raw_set
        raw_y_status = bullets.get("status")
        if raw_y_status:
            yaml_status = _normalize_yaml_scalar(raw_y_status) or None
        if "order" in bullets and order_nn is None:
            with contextlib.suppress(Exception):
                order_nn = int(bullets["order"])
        if "kind" in bullets:
            bullets["research_kind"] = bullets["kind"]
    elif art_type == "prompt" and text.startswith("<!--"):
        # Staged prompt
        lines = text.splitlines()
        first_line = lines[0].strip()
        m_prompt = _MANAGED_PROMPT_COMMENT_RE.match(first_line)
        comment_bullets: Dict[str, str] = _parse_metadata_comment(first_line)
        explicit_bullets, _, bullet_title, bullet_history = (
            _parse_bullet_metadata_with_loose(text)
        )
        history_lines = bullet_history
        bullets = dict(explicit_bullets)
        bullets.update(comment_bullets)
        if explicit_bullets.get("Status") or explicit_bullets.get("status"):
            bullets["Status"] = (
                explicit_bullets.get("Status") or explicit_bullets["status"]
            )
        title = bullet_title
        if not title:
            for ln in lines:
                if ln.strip().startswith("# "):
                    title = ln.strip()[2:].strip()
                    break
        raw_status_legacy = (
            explicit_bullets.get("Status")
            or explicit_bullets.get("status")
            or (comment_bullets.get("status") if m_prompt else None)
        )
        raw_set_p = (
            comment_bullets.get("Set")
            or comment_bullets.get("set")
            or explicit_bullets.get("Set")
        )
        legacy_raw_set = _first_set_token(raw_set_p)
    else:
        bullets, _, title, history_lines = _parse_bullet_metadata_with_loose(text)
        raw_status_legacy = bullets.get("Status") or bullets.get("status")
        raw_set_b = bullets.get("Set")
        legacy_raw_set = _first_set_token(raw_set_b)

    # In-file Id override (accept only valid 6-char id6s; invalid/placeholder tokens stay ignored)
    if not is_yaml_record:
        id_cand = _first_token(bullets.get("Id"))
        if id_cand and _core.ID6_RE.fullmatch(id_cand):
            id6 = id_cand
        else:
            id_cand_lower = _first_token(bullets.get("id"))
            if id_cand_lower and _core.ID6_RE.fullmatch(id_cand_lower) and not id6:
                id6 = id_cand_lower

    if not set_id and legacy_raw_set and not legacy_raw_set.startswith(("`", "'", '"')):
        set_id = legacy_raw_set

    id_derived = False
    if not id6:
        # Derive a stable path-keyed id6 for id-less legacy files. The repository-wide collision
        # pool is scanned ONCE per records root per process from declared ids only; derived ids are
        # never added to it so warm/edited/rebuilt caches derive the same id6.
        _pool_key = str(Path(records_root).resolve())
        _pool = _LEGACY_MINT_POOLS.get(_pool_key)
        if _pool is None:
            _pool = set(
                _core.global_id6s(
                    _proj_ctx.record_git_root(records_root) or records_root
                )
            )
            _LEGACY_MINT_POOLS[_pool_key] = _pool
        taken = _pool | set(extra_taken) if extra_taken else _pool
        id6 = derive_id6(rel_path, taken)
        id_derived = True

    validate_id6(id6)

    # Status handling (OQ-03):
    # Only single-token status sets artifacts.status; legacy_raw_status preserves exact/multi-word token
    if is_yaml_record:
        raw_status = yaml_status
        raw_status_legacy = yaml_status
    else:
        raw_status = bullets.get("Status") or bullets.get("status")
        if raw_status_legacy is not None:
            raw_status_legacy = raw_status_legacy.strip() or None
    clean_status: Optional[str] = None
    if raw_status:
        st_parts = raw_status.strip().split()
        if len(st_parts) == 1:
            clean_status = st_parts[0].lower()

    # Legacy field mappings (4.2, 4.5c)
    field_map = {
        "Kind": "plan_role",
        "kind": "research_kind",
        "Work-Kind": "work_kind",
        "Gate-Kind": "gate_kind",
        "Gate-Ref": "gate_ref",
        "Gate-Summary": "gate_summary",
        "Blocks-Release": "blocks_release",
        "From-Backlog": "from_backlog",
        "From-Spec": "from_spec",
        "From-Plan": "from_plan",
        "Supersedes": "supersedes",
        "Graduated-To": "graduated_to",
        "Scope-Paths": "scope_paths",
        "Coverage": "coverage",
        "Coverage-Fingerprint": "coverage_fingerprint",
        "Coverage-Checked": "coverage_checked",
        "Review-Depth": "review_depth",
        "Pipeline": "pipeline",
        "Attended": "attended",
        "Close-Evidence": "close_evidence",
        "Release-Exempt-Kind": "release_exempt_kind",
        "Release-Exempt-Ref": "release_exempt_ref",
        "Short-Description": "short_description",
        "Priority": "priority",
        "Readiness": "readiness",
        "Approval": "approval",
        "Author": "author",
        "Targets": "targets",
        "Concerns": "concerns",
        "Results": "results",
        "Results-go-to": "results_go_to",
        "Grounding": "grounding",
        "Goal": "goal",
        "Reviews-spec": "reviews_spec",
        "Basis": "basis",
        "Relation": "relation",
    }

    mapped_fields: Dict[str, Any] = {}
    if facet_kind and "research_kind" in REGISTRY.get(art_type, {}):
        mapped_fields["research_kind"] = facet_kind
    if ace_val:
        mapped_fields["ace"] = ace_val
    if model_val:
        mapped_fields["model"] = model_val
    if set_id:
        mapped_fields["set"] = set_id
    if order_nn is not None:
        mapped_fields["order"] = order_nn
    if title:
        mapped_fields["title"] = title

    for bk, bv in bullets.items():
        if bk in ("Id", "id", "Status", "status"):
            continue
        if bk == "Kind" and art_type == "backlog":
            if "Work-Kind" in bullets:
                continue
            target_k = "work_kind"
        elif art_type == "prompt" and bk in ("Kind", "kind"):
            target_k = "prompt_kind"
        elif art_type == "prompt" and bk in ("Created", "created"):
            target_k = "created_day"
        else:
            target_k = field_map.get(bk, bk.lower().replace("-", "_"))
        if bv == "" and target_k in mapped_fields:
            continue
        reg = REGISTRY.get(art_type, {})
        if target_k in reg:
            mapped_fields[target_k] = bv
        else:
            # Unregistered legacy bullet (OQ-02): keep in mapped_fields but mark legacy
            mapped_fields[target_k] = bv

    if art_type == "ipd" and not is_yaml_record:
        meta_region = metadata_region(text)
        se_match = re.search(r"(?m)^-\s*Scope-Exceeded:\s*(.*)$", meta_region)
        if se_match is not None:
            raw_se = se_match.group(1).strip()
            parsed_oos, se_malformed = _parse_scope_exceeded_bullet(raw_se)
            mapped_fields["scope_result"] = "exceeded"
            mapped_fields["out_of_scope_paths"] = parsed_oos
            if se_malformed:
                mapped_fields["scope_exceeded_raw"] = raw_se

    # Item-Dependencies
    raw_deps = bullets.get("Item-Dependencies") or bullets.get("item-dependencies")
    if raw_deps:
        mapped_fields["item_dependencies"] = raw_deps

    # Newest history day
    last_hist_day: Optional[str] = None
    if history_lines:
        newest = _newest_history_record(history_lines)
        if newest:
            last_hist_day = _last_history_at([newest])

    artifact_row = {
        "id6": id6,
        "type": art_type,
        "path": rel_path,
        "disposition": disposition,
        "status": clean_status,
        "title": title,
        "short_description": mapped_fields.get("short_description"),
        "set_id": set_id,
        "order_nn": order_nn,
        "filename_date": filename_date,
        "created_day": mapped_fields.get("created_day")
        if art_type == "prompt"
        else None,
        "created_at": None,
        "updated_at": None,
        "last_history_day": last_hist_day,
        "last_seq": len(history_lines),
        "valid": 1,
        "defect": None,
        "id_derived": id_derived,
        "legacy_raw_status": raw_status_legacy,
        "legacy_raw_set": legacy_raw_set,
        # The registry-typed field values, for the per-type table (backlog `suth7l`: the loader
        # computed these and then dropped them, so every per-type table held 0 rows). Only fields
        # the REGISTRY declares for this type are carried; unregistered legacy bullets (OQ-02) stay
        # out of the typed table, exactly as the log branch's replay keeps them out.
        "fields": {
            k: v for k, v in mapped_fields.items() if k in REGISTRY.get(art_type, {})
        },
        "lineage": _extract_legacy_lineage(
            text,
            id6,
            is_yaml=is_yaml_record,
            yaml_data=bullets if is_yaml_record else None,
        ),
    }

    # History rows
    hist_rows: List[Dict[str, Any]] = []
    for i, hline in enumerate(history_lines, start=1):
        hist_rows.append(
            {
                "id6": id6,
                "seq": i,
                "line": hline,
                "observed_day": _last_history_at([hline]),
            }
        )

    return artifact_row, hist_rows


def load_legacy_review(
    path: Path,
    records_root: Path,
    text: Optional[str] = None,
    *,
    repo_root: Optional[Path] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load a legacy .review.md file into review_files and reviews rows."""
    if text is None:
        text = path.read_text(encoding="utf-8")

    filename = path.name
    scan_repo = (
        Path(repo_root)
        if repo_root is not None
        else _scan_repo_root(None, records_root)
    )
    rel_path = stored_path(path, records_root, scan_repo)
    bullets, _, _ = _parse_bullet_metadata(text)

    subject_id = bullets.get("Subject-Id") or bullets.get("Subject") or ""
    # Try parsing subject from filename if absent
    if not subject_id:
        m_attr = _naming.parse_attributed(filename)
        if m_attr:
            subject_id = m_attr.id6
        else:
            m_clust = _naming.parse_clustered(filename)
            if m_clust:
                subject_id = m_clust.group("id6")

    validate_id6(subject_id)

    # Round count
    round_matches = re.findall(r"^## Round (\d+)", text, re.MULTILINE)
    rounds = [int(r) for r in round_matches] if round_matches else [1]
    round_count = max(rounds) if rounds else 1

    # Check parse_ok via review_findings
    parse_ok = 1
    try:
        _rev_findings.parse_review_text(text)
    except Exception:
        parse_ok = 0

    # Binding ref (4.1a K4):
    # If review file filename id6 != subject_id, review_ref is filename id6
    m_attr = _naming.parse_attributed(filename)
    filename_id = m_attr.id6 if m_attr else None
    if not filename_id:
        m_c = _naming.parse_clustered(filename)
        filename_id = m_c.group("id6") if m_c else None

    review_ref: Optional[str] = None
    if filename_id and filename_id != subject_id:
        review_ref = filename_id
    elif "Ref" in bullets:
        review_ref = bullets["Ref"]

    review_kind = review_kind_of_file(rel_path)

    review_file_row = {
        "path": rel_path,
        "subject_id6": subject_id,
        "review_ref": review_ref,
        "round_count": round_count,
        "parse_ok": parse_ok,
    }

    # One row per round. Verdict, Reviewer, Reviewed-At on LAST round only (K5a)
    reviews_list: List[Dict[str, Any]] = []
    verdict_raw = bullets.get("Verdict")
    reviewer_raw = bullets.get("Reviewer")
    reviewed_at_raw = bullets.get("Reviewed-At") or bullets.get("Date")
    readiness_raw = bullets.get("Readiness")
    rdepth_raw = bullets.get("Review-Depth")
    fsummary_raw = bullets.get("Findings")

    for r in range(1, round_count + 1):
        is_last = r == round_count
        reviews_list.append(
            {
                "subject_id6": subject_id,
                "seq": r,
                "review_ref": review_ref,
                "round": r,
                "review_kind": review_kind,
                "verdict": verdict_raw
                if is_last and verdict_raw in GATE_VERDICTS
                else None,
                "legacy_verdict": verdict_raw if is_last else None,
                "observed_day": reviewed_at_raw if is_last else None,
                "readiness": readiness_raw if is_last else None,
                "review_depth": rdepth_raw if is_last else None,
                "findings_summary": fsummary_raw if is_last else None,
                "reviewer": reviewer_raw if is_last else None,
            }
        )

    return review_file_row, reviews_list


# --------------------------------------------------------------------------------------
# 10. Freshness Check & Source Loader (E-07, E-10, 4.3)
# --------------------------------------------------------------------------------------


def _compute_digest(path: Path) -> str:
    """Compute SHA-256 digest of working-tree bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _delete_artifact_projection(conn: sqlite3.Connection, id6: str) -> None:
    """Remove all cached projection rows for ``id6``."""
    conn.execute("DELETE FROM artifacts WHERE id6 = ?", (id6,))
    for t in SUPPORTED_TYPES:
        conn.execute(f'DELETE FROM "{t}" WHERE id6 = ?', (id6,))
    conn.execute("DELETE FROM scope_paths WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM artifact_paths WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM scope_exceptions WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM dependencies WHERE dependent_id6 = ?", (id6,))
    conn.execute("DELETE FROM lineage WHERE child_id6 = ?", (id6,))
    conn.execute("DELETE FROM graduation_targets WHERE source_id6 = ?", (id6,))
    conn.execute("DELETE FROM release_gates WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM gates WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM events WHERE id6 = ?", (id6,))
    conn.execute("DELETE FROM field_changes WHERE id6 = ?", (id6,))


def _store_legacy_artifact_projection(
    conn: sqlite3.Connection,
    art_row: Dict[str, Any],
    path_str: str,
    role: str,
    st: os.stat_result,
    digest: str,
    now_str: str,
    records_root: Path,
) -> None:
    """Insert or update the cache projection rows for one legacy artifact or walkthrough."""
    _has_log = (records_root / "meta" / f"{art_row['id6']}.jsonl").exists()
    _verb = "INSERT OR IGNORE" if _has_log else "INSERT OR REPLACE"
    conn.execute(
        _verb
        + """ INTO artifacts (
            id6, type, path, disposition, status, title, short_description,
            set_id, order_nn, filename_date, created_day, created_at, updated_at,
            last_history_day, last_seq, valid, defect, id_derived,
            legacy_raw_status, legacy_raw_set
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            art_row["id6"],
            art_row["type"],
            art_row["path"],
            art_row["disposition"],
            art_row["status"],
            art_row["title"],
            art_row["short_description"],
            art_row["set_id"],
            art_row["order_nn"],
            art_row["filename_date"],
            art_row["created_day"],
            art_row["created_at"],
            art_row["updated_at"],
            art_row["last_history_day"],
            art_row["last_seq"],
            1,
            None,
            1 if art_row.get("id_derived") else 0,
            art_row.get("legacy_raw_status"),
            art_row.get("legacy_raw_set"),
        ),
    )
    if not _has_log:
        _lt = art_row["type"]
        _fv = art_row.get("fields") or {}
        if _lt in REGISTRY:
            _reg_fields = registry_fields(_lt)
            conn.execute(
                f"""INSERT OR REPLACE INTO "{_lt}" ({", ".join(["id6"] + [f'"{f}"' for f in _reg_fields])}) VALUES ({", ".join(["?"] * (len(_reg_fields) + 1))})""",
                [art_row["id6"]]
                + [
                    json.dumps(_fv[f])
                    if isinstance(_fv.get(f), (list, dict))
                    else _fv.get(f)
                    for f in _reg_fields
                ],
            )
        for idx, oos_item in enumerate(_fv.get("out_of_scope_paths") or [], start=1):
            p_val = (
                oos_item.get("path") if isinstance(oos_item, dict) else str(oos_item)
            )
            r_val = oos_item.get("reason", "") if isinstance(oos_item, dict) else ""
            conn.execute(
                "INSERT OR REPLACE INTO scope_exceptions VALUES (?, ?, ?, ?, ?, ?)",
                (
                    art_row["id6"],
                    idx,
                    p_val,
                    r_val,
                    "out-of-scope",
                    "checkpoint",
                ),
            )
        conn.execute("DELETE FROM lineage WHERE child_id6 = ?", (art_row["id6"],))
        for lin in art_row.get("lineage") or []:
            conn.execute(
                "INSERT OR REPLACE INTO lineage VALUES (?, ?, ?, ?)",
                (
                    lin["child_id6"],
                    lin["relation"],
                    lin["parent_raw"],
                    lin["parent_id6"],
                ),
            )
    conn.execute(
        """INSERT OR REPLACE INTO files (
            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            path_str,
            role,
            art_row["id6"],
            st.st_size,
            st.st_mtime_ns,
            digest,
            now_str,
            None,
        ),
    )


def _load_sources(
    conn: sqlite3.Connection,
    changed_sources: List[Dict[str, Any]],
    records_root: Path,
    *,
    repo_root: Optional[Path] = None,
) -> None:
    """One loader entry point: validate, replay and project changed sources."""
    records_root = Path(records_root)
    scan_repo = (
        Path(repo_root)
        if repo_root is not None
        else _scan_repo_root(None, records_root)
    )
    pre_reads: Dict[str, Tuple[os.stat_result, str, bytes]] = {}
    for item in changed_sources:
        p_s = item["path"]
        if item.get("role") == "removed" or p_s in pre_reads:
            continue
        ap = source_path(p_s, records_root, scan_repo)
        if not ap.exists():
            continue
        st_i = ap.stat()
        raw_b = ap.read_bytes()
        dig_i = hashlib.sha256(raw_b).hexdigest()
        pre_reads[p_s] = (st_i, dig_i, raw_b)

    _pool_key = str(records_root.resolve())
    if _pool_key not in _LEGACY_MINT_POOLS and any(
        it.get("role") in ("artifact", "walkthrough") and not it.get("id6")
        for it in changed_sources
    ):
        pool: Set[str] = {
            r[0]
            for r in conn.execute(
                "SELECT id6 FROM artifacts WHERE id_derived = 0"
            ).fetchall()
        }
        from agent_workflows import artifact_adopt as _adopt
        from agent_workflows import check_engine as _check

        cached_files_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        changed_paths_abs: Set[Path] = set()
        for it in changed_sources:
            p_s = it["path"]
            if cached_files_count > 0:
                ap = source_path(p_s, records_root, scan_repo)
                with contextlib.suppress(OSError):
                    changed_paths_abs.add(ap.resolve())
            if it.get("id6"):
                pool.add(it["id6"])
            if p_s in pre_reads:
                _, _, raw_b = pre_reads[p_s]
                with contextlib.suppress(UnicodeDecodeError):
                    pool.update(_adopt.scan_declared_identities(raw_b.decode("utf-8")))
        if cached_files_count > 0:
            for rt in _check.SUPPORTED:
                for tp in _check._iter_type_files(scan_repo, rt, include_retired=True):
                    with contextlib.suppress(OSError):
                        if tp.resolve() in changed_paths_abs:
                            continue
                    with contextlib.suppress(ValueError):
                        rel_tp = stored_path(tp, records_root, scan_repo)
                        if conn.execute(
                            "SELECT 1 FROM files WHERE path = ?", (rel_tp,)
                        ).fetchone():
                            continue
                    with contextlib.suppress(OSError, UnicodeDecodeError):
                        pool.update(
                            _adopt.scan_declared_identities(
                                tp.read_text(encoding="utf-8")
                            )
                        )
        _LEGACY_MINT_POOLS[_pool_key] = pool

    # Track (id6 <-> path) in memory across this batch so legacy loading does not run an
    # O(N^2) `SELECT id6 FROM artifacts WHERE path != ?` full table scan on every file.
    _art_id_by_path: Dict[str, str] = {}
    _art_path_by_id: Dict[str, str] = {}
    for _r_id, _r_p in conn.execute("SELECT id6, path FROM artifacts").fetchall():
        _art_id_by_path[_r_p] = _r_id
        _art_path_by_id[_r_id] = _r_p

    def _track_del_id(removed_id: str) -> None:
        old_p = _art_path_by_id.pop(removed_id, None)
        if old_p is not None and _art_id_by_path.get(old_p) == removed_id:
            _art_id_by_path.pop(old_p, None)

    def _track_put(put_id: str, put_path: str) -> None:
        _track_del_id(put_id)
        old_id_for_path = _art_id_by_path.get(put_path)
        if old_id_for_path is not None and old_id_for_path != put_id:
            _track_del_id(old_id_for_path)
        _art_id_by_path[put_path] = put_id
        _art_path_by_id[put_id] = put_path

    def _other_ids_for(cur_path: str) -> Iterable[str]:
        cur_id = _art_id_by_path.get(cur_path)
        if cur_id is None:
            return _art_path_by_id.keys()
        return set(_art_path_by_id.keys()) - {cur_id}

    with conn:
        for item in changed_sources:
            path_str = item["path"]
            abs_p = source_path(path_str, records_root, scan_repo)
            role = item["role"]
            id6 = item.get("id6")

            # If id6 was not provided (e.g. for removed file), fetch it from files table
            if not id6:
                row = conn.execute(
                    "SELECT id6 FROM files WHERE path = ?", (path_str,)
                ).fetchone()
                if row and row[0]:
                    id6 = row[0]

            # Remove prior projection of this file/artifact, but ONLY when this source is the one
            # that owns the projection (1ajqaa, fixing three measured clobbers): a review file is
            # keyed by its SUBJECT's id6 and owns no artifact row; an in-file mirror (`.md`) whose
            # `meta/<id6>.jsonl` log exists is a mirror, and the log is the authority (4.3); and a
            # removed path only owns the row if that row still points at it, since a `git mv`
            # loads the new path first and the old path's removal must not delete it.
            owns_projection = bool(id6)
            if id6 and role == "review":
                owns_projection = False
            elif id6 and role in ("artifact", "walkthrough"):
                if (records_root / "meta" / f"{id6}.jsonl").exists():
                    owns_projection = False
                else:
                    cur = conn.execute(
                        "SELECT path FROM artifacts WHERE id6 = ?", (id6,)
                    ).fetchone()
                    if cur is not None and cur[0] != path_str:
                        owns_projection = False
            elif id6 and role == "removed":
                if path_str.startswith("meta/") and path_str.endswith(".jsonl"):
                    owns_projection = True
                elif (records_root / "meta" / f"{id6}.jsonl").exists():
                    owns_projection = False
                else:
                    prior = conn.execute(
                        "SELECT file_role FROM files WHERE path = ?", (path_str,)
                    ).fetchone()
                    cur = conn.execute(
                        "SELECT path FROM artifacts WHERE id6 = ?", (id6,)
                    ).fetchone()
                    if prior is not None and prior[0] == "review":
                        owns_projection = False
                    elif cur is not None and cur[0] != path_str:
                        owns_projection = False
            if owns_projection:
                _delete_artifact_projection(conn, id6)
                _track_del_id(id6)

            if role == "removed" or not abs_p.exists():
                # Removed or newly-excluded file (e.g. comms/, runs/, .data/ pruned by
                # check_freshness). A removed source arrives with role "removed", so its former
                # role is read from the files table (1ajqaa: a deleted review file kept its row).
                # Checking `role == "removed"` BEFORE `abs_p.exists()` is critical: files in
                # excluded directories still exist on disk, and falling through would re-read and
                # SHA-256 hash them on every query without ever deleting their zombie rows.
                prior_role = role
                if role == "removed":
                    pr = conn.execute(
                        "SELECT file_role FROM files WHERE path = ?", (path_str,)
                    ).fetchone()
                    prior_role = pr[0] if pr else role
                conn.execute("DELETE FROM files WHERE path = ?", (path_str,))
                if prior_role == "review":
                    rf = conn.execute(
                        "SELECT subject_id6, review_ref FROM review_files WHERE path = ?",
                        (path_str,),
                    ).fetchone()
                    if rf is not None:
                        conn.execute(
                            "DELETE FROM reviews WHERE subject_id6 = ? AND review_ref IS ?",
                            (rf[0], rf[1]),
                        )
                    conn.execute("DELETE FROM review_files WHERE path = ?", (path_str,))
                continue

            # Update files table
            if path_str in pre_reads:
                st, digest, pre_bytes = pre_reads[path_str]
            else:
                st = abs_p.stat()
                pre_bytes = abs_p.read_bytes()
                digest = hashlib.sha256(pre_bytes).hexdigest()
            now_str = datetime.datetime.now(timezone.utc).isoformat()

            if role == "log":
                # Load jsonl log (normalize CRLF -> LF like read_text() in append/repair so
                # Windows checkouts with core.autocrlf=true do not trip decode_line).
                try:
                    lines = (
                        pre_bytes.decode("utf-8")
                        .replace("\r\n", "\n")
                        .splitlines(keepends=True)
                    )
                    art_type = item.get("type")
                    if not art_type and lines:
                        ev0 = decode_line(lines[0])
                        art_type = ev0.get("fields", {}).get("type", "ipd")
                    if not art_type:
                        art_type = "ipd"
                    state, f_changes, a_paths, proj = replay(
                        id6, art_type, lines, records_root=records_root
                    )

                    # Insert artifacts row
                    conn.execute(
                        """INSERT OR REPLACE INTO artifacts (
                            id6, type, path, disposition, status, title, short_description,
                            set_id, order_nn, filename_date, created_day, created_at, updated_at,
                            last_history_day, last_seq, valid, defect, id_derived,
                            legacy_raw_status, legacy_raw_set
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            state.id6,
                            state.type,
                            state.path,
                            state.disposition,
                            state.status,
                            state.title,
                            state.short_description,
                            state.set_id,
                            state.order_nn,
                            state.filename_date,
                            state.created_day,
                            state.created_at,
                            state.updated_at,
                            state.last_history_day,
                            state.last_seq,
                            1,
                            None,
                            0,
                            state.status,
                            state.set_id,
                        ),
                    )

                    # Insert per-type table row
                    reg_fields = registry_fields(art_type)
                    col_names = ["id6"] + [f'"{f}"' for f in reg_fields]
                    placeholders = ["?"] * len(col_names)
                    col_values = [state.id6] + [
                        json.dumps(state.fields[f])
                        if isinstance(state.fields.get(f), (list, dict))
                        else state.fields.get(f)
                        for f in reg_fields
                    ]
                    conn.execute(
                        f"""INSERT OR REPLACE INTO "{art_type}" ({", ".join(col_names)}) VALUES ({", ".join(placeholders)})""",
                        col_values,
                    )

                    # Insert projection data
                    for sp in proj["scope_paths"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO scope_paths VALUES (?, ?, ?)",
                            (sp["id6"], sp["ordinal"], sp["path"]),
                        )
                    for ap in a_paths:
                        conn.execute(
                            "INSERT OR REPLACE INTO artifact_paths VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                ap["id6"],
                                ap["seq"],
                                ap["path"],
                                ap["at"],
                                ap["actor_id"],
                                ap["by_human"],
                                ap["op"],
                                ap["verb"],
                            ),
                        )
                    for se in proj["scope_exceptions"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO scope_exceptions VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                se["id6"],
                                se["ordinal"],
                                se["path"],
                                se["reason"],
                                se["exception_kind"],
                                se["source"],
                            ),
                        )
                    for dep in proj["dependencies"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO dependencies VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                dep["dependent_id6"],
                                dep["ordinal"],
                                dep["condition"],
                                dep["target_type"],
                                dep["required_status"],
                                dep["target_raw"],
                                dep["target_id6"],
                            ),
                        )
                    for lin in proj["lineage"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO lineage VALUES (?, ?, ?, ?)",
                            (
                                lin["child_id6"],
                                lin["relation"],
                                lin["parent_raw"],
                                lin["parent_id6"],
                            ),
                        )
                    for gt in proj["graduation_targets"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO graduation_targets VALUES (?, ?, ?, ?)",
                            (
                                gt["source_id6"],
                                gt["ordinal"],
                                gt["target_raw"],
                                gt["target_set_id"],
                            ),
                        )
                    for rg in proj["release_gates"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO release_gates VALUES (?, ?, ?)",
                            (rg["id6"], rg["release_raw"], rg["release_id6"]),
                        )
                    for g in proj["gates"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO gates VALUES (?, ?, ?, ?)",
                            (
                                g["id6"],
                                g["gate_kind"],
                                g["gate_ref"],
                                g["gate_summary"],
                            ),
                        )
                    for act in proj["actors"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO actors VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                act["actor_id"],
                                act["tool"],
                                act["ace"],
                                act["host"],
                                act["model"],
                                act["variant"],
                                act["run_id"],
                                act["attempt"],
                            ),
                        )
                    for ev in proj["events"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                ev["id6"],
                                ev["seq"],
                                ev["append"],
                                ev["op"],
                                ev["at"],
                                ev["actor_id"],
                                ev["by_human"],
                                ev["from_status"],
                                ev["to_status"],
                                ev["path"],
                                ev["message"],
                                ev["raw"],
                            ),
                        )
                    for fc in f_changes:
                        conn.execute(
                            "INSERT OR REPLACE INTO field_changes VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                fc["id6"],
                                fc["seq"],
                                fc["field"],
                                fc["old_value"],
                                fc["new_value"],
                                fc["unset"],
                            ),
                        )

                    conn.execute(
                        """INSERT OR REPLACE INTO files (
                            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            path_str,
                            role,
                            id6,
                            st.st_size,
                            st.st_mtime_ns,
                            digest,
                            now_str,
                            None,
                        ),
                    )

                except Exception as exc:
                    err_msg = str(exc)
                    conn.execute(
                        """INSERT OR REPLACE INTO files (
                            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            path_str,
                            role,
                            id6,
                            st.st_size,
                            st.st_mtime_ns,
                            digest,
                            now_str,
                            err_msg,
                        ),
                    )
                    conn.execute(
                        """INSERT OR REPLACE INTO artifacts (
                            id6, type, path, valid, defect, id_derived
                        ) VALUES (?, ?, ?, ?, ?, 0)""",
                        (id6, item.get("type", "unknown"), path_str, 0, err_msg),
                    )

            elif role == "review":
                try:
                    rf_row, rev_rows = load_legacy_review(
                        abs_p,
                        records_root,
                        text=pre_bytes.decode("utf-8"),
                        repo_root=scan_repo,
                    )
                    # Replace this file's rounds rather than overlaying them (1ajqaa): a review
                    # edited to fewer rounds must not keep the old ones.
                    conn.execute(
                        "DELETE FROM reviews WHERE subject_id6 = ? AND review_ref IS ?",
                        (rf_row["subject_id6"], rf_row["review_ref"]),
                    )
                    conn.execute(
                        """INSERT OR REPLACE INTO review_files (
                            path, subject_id6, review_ref, round_count, parse_ok
                        ) VALUES (?, ?, ?, ?, ?)""",
                        (
                            rf_row["path"],
                            rf_row["subject_id6"],
                            rf_row["review_ref"],
                            rf_row["round_count"],
                            rf_row["parse_ok"],
                        ),
                    )
                    for rrow in rev_rows:
                        conn.execute(
                            """INSERT OR REPLACE INTO reviews (
                                subject_id6, seq, review_ref, round, review_kind, verdict,
                                legacy_verdict, observed_day, readiness, review_depth, findings_summary, reviewer
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                rrow["subject_id6"],
                                rrow["seq"],
                                rrow["review_ref"],
                                rrow["round"],
                                rrow["review_kind"],
                                rrow["verdict"],
                                rrow["legacy_verdict"],
                                rrow["observed_day"],
                                rrow["readiness"],
                                rrow["review_depth"],
                                rrow["findings_summary"],
                                rrow["reviewer"],
                            ),
                        )
                    conn.execute(
                        """INSERT OR REPLACE INTO files (
                            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            path_str,
                            role,
                            rf_row["subject_id6"],
                            st.st_size,
                            st.st_mtime_ns,
                            digest,
                            now_str,
                            None,
                        ),
                    )
                except Exception as exc:
                    conn.execute(
                        """INSERT OR REPLACE INTO files (
                            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            path_str,
                            role,
                            id6,
                            st.st_size,
                            st.st_mtime_ns,
                            digest,
                            now_str,
                            str(exc),
                        ),
                    )

            elif role in ("artifact", "walkthrough"):
                # Phase B legacy loader
                try:
                    other_ids = _other_ids_for(path_str)
                    art_row, _h_rows = load_legacy_artifact(
                        abs_p,
                        records_root,
                        text=pre_bytes.decode("utf-8"),
                        repo_root=scan_repo,
                        extra_taken=other_ids,
                    )
                    loaded_id6 = art_row["id6"]
                    loaded_derived = bool(art_row.get("id_derived"))
                    if not loaded_derived:
                        _pool_key = str(Path(records_root).resolve())
                        if _pool_key in _LEGACY_MINT_POOLS:
                            _LEGACY_MINT_POOLS[_pool_key].add(loaded_id6)
                        existing_row = conn.execute(
                            "SELECT path, id_derived FROM artifacts WHERE id6 = ?",
                            (loaded_id6,),
                        ).fetchone()
                        if existing_row is not None and existing_row[0] != path_str:
                            old_path_str, old_derived = (
                                existing_row[0],
                                bool(existing_row[1]),
                            )
                            if old_derived:
                                _delete_artifact_projection(conn, loaded_id6)
                                _track_del_id(loaded_id6)
                                old_abs = source_path(
                                    old_path_str, records_root, scan_repo
                                )
                                if old_abs.exists():
                                    old_taken = set(_other_ids_for(old_path_str))
                                    old_taken.add(loaded_id6)
                                    old_art_row, _ = load_legacy_artifact(
                                        old_abs,
                                        records_root,
                                        repo_root=scan_repo,
                                        extra_taken=old_taken,
                                    )
                                    old_file_row = conn.execute(
                                        "SELECT file_role FROM files WHERE path = ?",
                                        (old_path_str,),
                                    ).fetchone()
                                    old_role = (
                                        old_file_row[0] if old_file_row else "artifact"
                                    )
                                    old_st = old_abs.stat()
                                    old_digest = _compute_digest(old_abs)
                                    _store_legacy_artifact_projection(
                                        conn,
                                        old_art_row,
                                        old_path_str,
                                        old_role,
                                        old_st,
                                        old_digest,
                                        now_str,
                                        records_root,
                                    )
                                    _track_put(old_art_row["id6"], old_path_str)
                            elif (
                                path_str.startswith("@repo/")
                                and (
                                    not old_path_str.startswith("@repo/")
                                    or (
                                        path_str.startswith("@repo/.agents/")
                                        and old_path_str.startswith(
                                            "@repo/.aw/records/"
                                        )
                                    )
                                )
                                and source_path(
                                    old_path_str, records_root, scan_repo
                                ).exists()
                            ):
                                conn.execute(
                                    """INSERT OR REPLACE INTO files (
                                        path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (
                                        path_str,
                                        role,
                                        loaded_id6,
                                        st.st_size,
                                        st.st_mtime_ns,
                                        digest,
                                        now_str,
                                        None,
                                    ),
                                )
                                continue
                    _store_legacy_artifact_projection(
                        conn, art_row, path_str, role, st, digest, now_str, records_root
                    )
                    _track_put(loaded_id6, path_str)
                except Exception as exc:
                    conn.execute(
                        """INSERT OR REPLACE INTO files (
                            path, file_role, id6, size, mtime_ns, content_digest, loaded_at, load_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            path_str,
                            role,
                            id6,
                            st.st_size,
                            st.st_mtime_ns,
                            digest,
                            now_str,
                            str(exc),
                        ),
                    )
                    if id6:
                        conn.execute(
                            """INSERT OR REPLACE INTO artifacts (
                                id6, type, path, valid, defect, id_derived
                            ) VALUES (?, ?, ?, ?, ?, 0)""",
                            (id6, item.get("type", "unknown"), path_str, 0, str(exc)),
                        )


def _require_schema(project_context: Any, records_root: Path) -> None:
    """Enforce the repository metadata_schema gate before reading metadata."""
    from agent_workflows.migrations import chain as _chain

    records_path = Path(records_root)
    repo: Any = getattr(project_context, "target_repo", None) or getattr(
        project_context, "repo_root", None
    )
    if not repo:
        owner = _proj_ctx.record_owner_root(records_path)
        if owner is not None:
            repo = owner
        elif records_path.name == "records" and records_path.parent.name in (
            ".aw",
            ".agents",
        ):
            repo = records_path.parent.parent
        else:
            repo = records_path
    physical = getattr(project_context, "physical_classes", None) or {}
    config_project = (
        physical.get("config_project") if isinstance(physical, dict) else None
    )
    _chain.require_current_schema(
        repo,
        config_project=config_project,
        records_root=records_path,
    )


def _detect_file_role(
    fname: str, *, is_meta: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if is_meta and fname.endswith(".jsonl"):
        return "log", fname[:-6], None
    if fname.endswith(".review.md"):
        return "review", None, None
    if fname.endswith(".walkthrough.md"):
        return "walkthrough", None, None
    if fname.endswith(".md"):
        if not _naming._LEGACY_TIMESTAMP_RE.match(fname):
            m_attr = _naming.parse_attributed(fname)
            if m_attr:
                return "artifact", m_attr.id6, m_attr.type
            m_clust = _naming.parse_clustered(fname)
            if m_clust:
                return "artifact", m_clust.group("id6"), m_clust.group("type")
        return "artifact", None, None
    return None, None, None


_FRESHNESS_EXCLUDED_DIRS: FrozenSet[str] = frozenset(
    _layout.TRAVERSAL_EXCLUSIONS
) | frozenset({"comms"})


_RACY_MTIME_WINDOW_NS = 2_000_000_000


def _is_source_stale(
    fpath: Path,
    prev_info: Optional[Tuple[int, int, str]],
    force: bool,
    *,
    now_ns: Optional[int] = None,
) -> bool:
    if force or prev_info is None:
        return True
    st_f = fpath.stat()
    prev_size, prev_mtime_f, prev_digest = prev_info
    if prev_size != st_f.st_size or prev_mtime_f != st_f.st_mtime_ns:
        return True
    # Standard racy-git fast path: when size and mtime_ns match and the file has not been
    # modified within the last 2 seconds, skip re-hashing its full contents on every check.
    if now_ns is not None and (now_ns - st_f.st_mtime_ns) > _RACY_MTIME_WINDOW_NS:
        return False
    return _compute_digest(fpath) != prev_digest


def check_freshness(
    conn: sqlite3.Connection,
    records_root: Path,
    *,
    force: bool = False,
    project_context: Any = None,
    repo_root: Optional[Path] = None,
) -> None:
    """Run directory membership and file content freshness checks before read operations."""
    records_root = Path(records_root)
    _require_schema(project_context, records_root)

    scan_repo = (
        Path(repo_root).resolve()
        if repo_root is not None
        else (
            _scan_repo_root(project_context, records_root)
            if project_context is not None
            else None
        )
    )

    extra_root_dirs: List[Tuple[str, Path]] = []
    if scan_repo is not None:
        from agent_workflows import selectors as _sel

        rec_resolved = records_root.resolve()
        seen_extra_dirs: Set[Path] = set()
        with _sel.scan_once():
            for etype in (
                "plans",
                "specs",
                "prompts",
                "backlog",
                "releases",
                "research",
                "walkthroughs",
                "roadmaps",
                "other",
            ):
                for d in _sel.record_dirs(scan_repo, etype):
                    try:
                        d_res = d.resolve()
                    except OSError:
                        continue
                    if d_res == rec_resolved or d_res.is_relative_to(rec_resolved):
                        continue
                    if d_res in seen_extra_dirs or not d.is_dir():
                        continue
                    seen_extra_dirs.add(d_res)
                    extra_root_dirs.append((etype, d))

    if not records_root.exists() and not extra_root_dirs:
        return

    # Check 1: Directory membership
    known_dirs: Dict[str, int] = dict(
        conn.execute("SELECT path, mtime_ns FROM directories").fetchall()
    )
    known_files: Dict[str, Tuple[int, int, str]] = {
        row[0]: (row[1], row[2], row[3])
        for row in conn.execute(
            "SELECT path, size, mtime_ns, content_digest FROM files"
        ).fetchall()
    }

    changed_sources: List[Dict[str, Any]] = []
    current_files_set: Set[str] = set()
    seen_files: Set[str] = set()
    dirty_dirs: List[Tuple[str, int]] = []
    need_seen_files = bool(extra_root_dirs)
    now_ns = time.time_ns()

    # Discover directories and files inside records_root using os.scandir so unchanged
    # files skip Path construction, _detect_file_role/parse_attributed, and redundant stat joins.
    if records_root.exists():
        records_root_str = str(records_root)
        dir_stack: List[Tuple[str, str]] = [(records_root_str, "")]
        while dir_stack:
            cur_dir, rel_dir = dir_stack.pop()
            try:
                st_dir = os.stat(cur_dir)
            except OSError:
                continue
            current_mtime = st_dir.st_mtime_ns
            if known_dirs.get(rel_dir) != current_mtime:
                dirty_dirs.append((rel_dir, current_mtime))

            is_meta_dir = rel_dir == "meta" or rel_dir.startswith("meta/")
            rel_prefix = f"{rel_dir}/" if rel_dir else ""
            try:
                with os.scandir(cur_dir) as it:
                    entries = list(it)
            except OSError:
                continue
            subdirs: List[Tuple[str, str]] = []
            for entry in entries:
                fname = entry.name
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                    continue
                if is_dir:
                    if (
                        not fname.startswith(".")
                        and fname not in _FRESHNESS_EXCLUDED_DIRS
                        and not fname.endswith(".data")
                    ):
                        subdirs.append((entry.path, f"{rel_prefix}{fname}"))
                    continue
                if (
                    fname.startswith(".")
                    or fname.startswith("INDEX.")
                    or fname == "STATUS.md"
                ):
                    continue
                rel_f = f"{rel_prefix}{fname}"
                current_files_set.add(rel_f)
                if need_seen_files:
                    with contextlib.suppress(OSError):
                        seen_files.add(os.path.realpath(entry.path))

                known = known_files.get(rel_f)
                if known is not None and not force:
                    try:
                        st_f = entry.stat(follow_symlinks=True)
                    except OSError:
                        st_f = None
                    if (
                        st_f is not None
                        and st_f.st_size == known[0]
                        and st_f.st_mtime_ns == known[1]
                        and (now_ns - st_f.st_mtime_ns) >= _RACY_MTIME_WINDOW_NS
                    ):
                        continue

                role, f_id6, f_type = _detect_file_role(fname, is_meta=is_meta_dir)
                if not role:
                    continue

                if _is_source_stale(Path(entry.path), known, force, now_ns=now_ns):
                    changed_sources.append(
                        {
                            "path": rel_f,
                            "role": role,
                            "id6": f_id6,
                            "type": f_type,
                        }
                    )
            if subdirs:
                dir_stack.extend(reversed(subdirs))

    # Discover directories and files in extra roots (e.g., legacy .agents/ trees)
    if extra_root_dirs:
        from agent_workflows import research_contract as _rc
        from agent_workflows import selectors as _sel

        for extra_type, extra_dir in extra_root_dirs:
            for root, dirs, files in os.walk(extra_dir):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in _FRESHNESS_EXCLUDED_DIRS
                    and not d.endswith(".data")
                ]
                root_p = Path(root)
                try:
                    dir_stored = stored_path(root_p, records_root, scan_repo)
                except ValueError:
                    continue
                st_dir = os.stat(root)
                current_mtime = st_dir.st_mtime_ns
                if known_dirs.get(dir_stored) != current_mtime:
                    dirty_dirs.append((dir_stored, current_mtime))

                for fname in files:
                    if (
                        fname.startswith(".")
                        or fname.startswith("INDEX.")
                        or fname == "STATUS.md"
                        or not fname.endswith(".md")
                    ):
                        continue
                    fpath = root_p / fname
                    try:
                        resolved_f = os.path.realpath(str(fpath))
                    except OSError:
                        continue
                    if resolved_f in seen_files:
                        continue
                    seen_files.add(resolved_f)

                    if fname in _sel._SKIP_NAMES:
                        continue
                    if (
                        extra_type == "research"
                        and _rc.companion_owner_stem(fpath, extra_dir) is not None
                    ):
                        continue

                    try:
                        rel_f = stored_path(fpath, records_root, scan_repo)
                    except ValueError:
                        continue
                    current_files_set.add(rel_f)

                    role, f_id6, f_type = _detect_file_role(fname, is_meta=False)
                    if not role:
                        continue

                    if _is_source_stale(
                        fpath, known_files.get(rel_f), force, now_ns=now_ns
                    ):
                        changed_sources.append(
                            {
                                "path": rel_f,
                                "role": role,
                                "id6": f_id6,
                                "type": f_type,
                            }
                        )

    # Detect deleted files
    for old_path in known_files:
        if old_path not in current_files_set:
            changed_sources.append(
                {
                    "path": old_path,
                    "role": "removed",
                    "id6": None,
                }
            )

    if not dirty_dirs and not changed_sources:
        return

    def _apply_refresh_writes(
        dirs_to_write: List[Tuple[str, int]],
        sources_to_load: List[Dict[str, Any]],
    ) -> None:
        if dirs_to_write:
            with conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO directories (path, mtime_ns) VALUES (?, ?)",
                    dirs_to_write,
                )
        if sources_to_load:
            _load_sources(conn, sources_to_load, records_root, repo_root=scan_repo)

            # Recompute resolved references after target inventory change
            with conn:
                # 1. dependencies.target_id6: resolve if NULL or if target_raw was a path/set
                conn.execute(
                    """UPDATE dependencies
                       SET target_id6 = (
                           SELECT a.id6 FROM artifacts a
                           WHERE a.path = dependencies.target_raw
                              OR EXISTS (SELECT 1 FROM artifact_paths ap WHERE ap.id6 = a.id6 AND ap.path = dependencies.target_raw)
                       )
                       WHERE target_id6 IS NULL"""
                )
                # 2. lineage.parent_id6: resolve if NULL or if parent_raw was a path/citation
                conn.execute(
                    """UPDATE lineage
                       SET parent_id6 = (
                           SELECT a.id6 FROM artifacts a
                           WHERE a.path = lineage.parent_raw
                              OR EXISTS (SELECT 1 FROM artifact_paths ap WHERE ap.id6 = a.id6 AND ap.path = lineage.parent_raw)
                       )
                       WHERE parent_id6 IS NULL"""
                )
                # 3. release_gates.release_id6
                try:
                    rel_outcome = _releases.resolve_release_outcome(
                        records_root.parent, "next"
                    )
                    next_release_id: Optional[str] = None
                    if (
                        rel_outcome.status == _releases.SENTINEL_RESOLVED
                        and rel_outcome.candidates
                    ):
                        cand_p = rel_outcome.candidates[0]
                        cand_attr = _naming.parse_attributed(cand_p.name)
                        if cand_attr:
                            next_release_id = cand_attr.id6
                    if next_release_id:
                        conn.execute(
                            "UPDATE release_gates SET release_id6 = ? WHERE release_raw = 'next'",
                            (next_release_id,),
                        )
                except Exception:
                    pass

    db_file = _db_file_path(conn)
    if db_file is None:
        _apply_refresh_writes(dirty_dirs, changed_sources)
        return

    with _cache_refresh_lock(db_file):
        # Re-read DB state inside the refresh lock: if a peer worker just completed
        # refreshing index.db while we waited, skip already-applied directories and files.
        fresh_dirs: Dict[str, int] = dict(
            conn.execute("SELECT path, mtime_ns FROM directories").fetchall()
        )
        fresh_files: Dict[str, Tuple[int, int, str]] = {
            row[0]: (row[1], row[2], row[3])
            for row in conn.execute(
                "SELECT path, size, mtime_ns, content_digest FROM files"
            ).fetchall()
        }
        remaining_dirs = [
            (d_path, m_ns)
            for d_path, m_ns in dirty_dirs
            if fresh_dirs.get(d_path) != m_ns
        ]
        remaining_sources: List[Dict[str, Any]] = []
        now_ns_locked = time.time_ns()
        for src in changed_sources:
            p_str = src["path"]
            if src["role"] == "removed":
                if p_str in fresh_files:
                    remaining_sources.append(src)
            else:
                abs_p = source_path(p_str, records_root, scan_repo)
                if not abs_p.exists() or _is_source_stale(
                    abs_p, fresh_files.get(p_str), force, now_ns=now_ns_locked
                ):
                    remaining_sources.append(src)
        if remaining_dirs or remaining_sources:
            _apply_refresh_writes(remaining_dirs, remaining_sources)


# --------------------------------------------------------------------------------------
# 11. Public Read Interface (E-13, E-14, 4.3, 4.4)
# --------------------------------------------------------------------------------------


_SCAN_ONCE_FRESH: contextvars.ContextVar[Optional[Set[Tuple[str, str]]]] = (
    contextvars.ContextVar("_SCAN_ONCE_FRESH", default=None)
)
_SCAN_ONCE_CONNS: contextvars.ContextVar[
    Optional[Dict[Tuple[str, str], sqlite3.Connection]]
] = contextvars.ContextVar("_SCAN_ONCE_CONNS", default=None)
_EPHEMERAL_IF_ABSENT: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_EPHEMERAL_IF_ABSENT", default=False
)


@contextlib.contextmanager
def ephemeral_if_uninitialized() -> Any:
    """Use an in-memory cache during read queries if neither state dir nor meta/ exists."""
    token = _EPHEMERAL_IF_ABSENT.set(True)
    try:
        yield
    finally:
        _EPHEMERAL_IF_ABSENT.reset(token)


@contextlib.contextmanager
def scan_once() -> Any:
    """Coalesce repeated freshness scans across `read`/`query`/`resolve` within a call."""
    existing = _SCAN_ONCE_FRESH.get()
    if existing is not None:
        yield
        return
    token_f = _SCAN_ONCE_FRESH.set(set())
    conns_map: Dict[Tuple[str, str], sqlite3.Connection] = {}
    token_c = _SCAN_ONCE_CONNS.set(conns_map)
    try:
        yield
    finally:
        for conn in conns_map.values():
            with contextlib.suppress(Exception):
                conn.close()
        _SCAN_ONCE_CONNS.reset(token_c)
        _SCAN_ONCE_FRESH.reset(token_f)


def drop_scan_freshness() -> None:
    """Clear the active `scan_once()` freshness set so the next read re-checks disk."""
    fresh_set = _SCAN_ONCE_FRESH.get()
    if fresh_set is not None:
        fresh_set.clear()


def _open_for_read(
    records_root: Path, state_root: Path
) -> Tuple[sqlite3.Connection, bool]:
    """Open or reuse a cache connection for a read operation; returns (conn, should_close)."""
    key = (str(records_root.resolve()), str(state_root.resolve()))
    conns_map = _SCAN_ONCE_CONNS.get()
    if conns_map is not None and key in conns_map:
        return conns_map[key], False
    use_mem = _EPHEMERAL_IF_ABSENT.get() and not (state_root / "index.db").exists()
    conn = open_cache(records_root, state_root, in_memory=use_mem)
    if conns_map is not None:
        conns_map[key] = conn
        return conn, False
    return conn, True


def _maybe_check_freshness(
    conn: sqlite3.Connection,
    records_root: Path,
    state_root: Path,
    *,
    project_context: Any = None,
    repo_root: Optional[Path] = None,
) -> None:
    fresh_set = _SCAN_ONCE_FRESH.get()
    key = (str(records_root.resolve()), str(state_root.resolve()))
    if fresh_set is not None and key in fresh_set:
        return
    check_freshness(
        conn,
        records_root,
        project_context=project_context,
        repo_root=repo_root,
    )
    if fresh_set is not None:
        fresh_set.add(key)


class QueryResult(list):
    """List of State objects with an incomplete attribute naming invalid/missing records."""

    def __init__(self, items: Iterable[State], incomplete: Optional[List[str]] = None):
        super().__init__(items)
        self.rows: List[State] = list(items)
        self.incomplete: List[str] = list(incomplete or [])


def read_text(text: str, *, record_type: Optional[str] = None) -> State:
    """Parse an in-memory record's metadata region using the phase-B two-dialect loader.

    Runs the same front-matter region and two-dialect rules as `read_at`, caches nothing,
    and returns a `State` carrying `legacy_raw_status`, `legacy_raw_set`, and separate strict
    vs loose (`loose_id`, `loose_status`, `loose_blocks_release`) bullet fields.
    """
    art_type = record_type or "ipd"
    if not text:
        return State(id6="", type=art_type)

    lines = text.splitlines()
    _yaml_probe: Dict[str, str] = {}
    yaml_title: Optional[str] = None
    if lines and lines[0].strip() == "---":
        _yaml_probe, yaml_title = _parse_yaml_front_matter(text)
    _after_fence = text.split("\n", 1)[1][:200] if "\n" in text else ""
    is_yaml_record = bool(_yaml_probe and not _BULLET_RE.search(_after_fence))

    if is_yaml_record:
        raw_y_id = _yaml_probe.get("id")
        y_id = _first_token(_normalize_yaml_scalar(raw_y_id)) if raw_y_id else None
        raw_y_status = _yaml_probe.get("status")
        y_status = (
            _normalize_yaml_scalar(raw_y_status) or None if raw_y_status else None
        )
        clean_status: Optional[str] = None
        if y_status and len(y_status.split()) == 1:
            clean_status = y_status.split()[0].lower()
        raw_y_set = _yaml_probe.get("set")
        tok_y_set = (
            _first_set_token(_normalize_yaml_scalar(raw_y_set)) if raw_y_set else None
        )
        legacy_raw_set = (
            _normalize_yaml_scalar(tok_y_set) or None if tok_y_set else None
        )
        order_nn: Optional[int] = None
        if "order" in _yaml_probe:
            with contextlib.suppress(Exception):
                order_nn = int(_normalize_yaml_scalar(_yaml_probe["order"]))
        fields = {
            k.lower().replace("-", "_"): _normalize_yaml_scalar(v)
            for k, v in _yaml_probe.items()
        }
        if "kind" in _yaml_probe:
            fields["research_kind"] = _normalize_yaml_scalar(_yaml_probe["kind"])
        yaml_history = _history_block(text).records
        return State(
            id6=y_id or "",
            type=art_type,
            status=clean_status,
            title=yaml_title,
            short_description=fields.get("short_description"),
            set_id=legacy_raw_set,
            order_nn=order_nn,
            last_history_day=_last_history_at(yaml_history),
            last_seq=len(yaml_history),
            fields=fields,
            legacy_raw_status=y_status,
            legacy_raw_set=legacy_raw_set,
            loose_id=None,
            loose_status=None,
            loose_blocks_release=None,
        )

    comment_bullets: Dict[str, str] = {}
    if art_type == "prompt" and text.startswith("<!--"):
        first_line = lines[0].strip() if lines else ""
        comment_bullets = _parse_metadata_comment(first_line)

    bullets, loose_bullets, title, history_lines = _parse_bullet_metadata_with_loose(
        text
    )
    if comment_bullets:
        merged_bullets = dict(bullets)
        merged_bullets.update(comment_bullets)
        if bullets.get("Status") or bullets.get("status"):
            merged_bullets["Status"] = bullets.get("Status") or bullets["status"]
        bullets = merged_bullets
    strict_id = _first_token(bullets.get("Id") or bullets.get("id"))
    raw_status = bullets.get("Status") or (
        bullets.get("status") if comment_bullets else None
    )
    raw_status_legacy = raw_status.strip() or None if raw_status else None
    clean_bullet_status: Optional[str] = None
    if raw_status_legacy and len(raw_status_legacy.split()) == 1:
        clean_bullet_status = raw_status_legacy.split()[0].lower()
    legacy_raw_set = _first_set_token(bullets.get("Set"))

    raw_l_id = (loose_bullets.get("Id") or "").strip()
    loose_id = raw_l_id if _core.ID6_RE.fullmatch(raw_l_id) else None
    raw_l_st = (loose_bullets.get("Status") or "").strip()
    loose_status = raw_l_st if (raw_l_st and len(raw_l_st.split()) == 1) else None
    raw_l_br = (loose_bullets.get("Blocks-Release") or "").strip()
    loose_blocks_release = (
        raw_l_br if (raw_l_br and len(raw_l_br.split()) == 1) else None
    )

    fields_out: Dict[str, Any] = {}
    for bk, bv in bullets.items():
        if bk == "Kind":
            if art_type == "backlog":
                if "Work-Kind" not in bullets:
                    fields_out["work_kind"] = bv
            else:
                fields_out["plan_role"] = bv
        elif bk.lower() == "kind" and art_type == "ipd":
            fields_out.setdefault("plan_role", bv)
        else:
            fields_out[bk.lower().replace("-", "_")] = bv
    for loose_key in (
        "Subject-Id",
        "Target-Id",
        "References",
        "From-Backlog",
        "From-Spec",
        "Reviewed-Id",
    ):
        fk = loose_key.lower().replace("-", "_")
        if fk not in fields_out and loose_key in loose_bullets:
            fields_out[fk] = loose_bullets[loose_key]

    return State(
        id6=strict_id or "",
        type=art_type,
        status=clean_bullet_status,
        title=title,
        short_description=bullets.get("Short-Description") or None,
        set_id=legacy_raw_set,
        last_history_day=_last_history_at(history_lines),
        fields=fields_out,
        last_seq=len(history_lines),
        legacy_raw_status=raw_status_legacy,
        legacy_raw_set=legacy_raw_set,
        loose_id=loose_id,
        loose_status=loose_status,
        loose_blocks_release=loose_blocks_release,
    )


def read_loose_id(text: str) -> Optional[str]:
    """Return the declared id6 from a post-cutover mirror or loose `- Id:` bullet, or ``None``.

    Checks `read_mirror_id6(text)` first so post-cutover YAML front-matter and staged-prompt
    mirrors resolve cleanly, then falls back to the loose `- Id:` bullet (`^-\\s*Id:`) bounded
    to `metadata_region` (so a QUOTED `- Id:` in a body is not read). The permissive spelling
    the host runners re-export as `_read_id` (both hosts bind this one function).
    """
    mirror_id = read_mirror_id6(text)
    if mirror_id is not None:
        return mirror_id
    return read_text(metadata_region(text)).loose_id


def read_loose_status(text: str) -> Optional[str]:
    """Return the single-token loose `- Status:` value from `text`'s metadata region, or ``None``.

    A multi-word status (e.g. ``EXECUTED (approved ...)``) yields ``None``; a YAML-only record
    yields ``None`` (bullet dialect only, like `read_loose_id`).
    """
    return read_text(metadata_region(text)).loose_status


def read_loose_blocks_release(text: str) -> Optional[str]:
    """Return the loose `- Blocks-Release:` value from `text`'s metadata region, or ``None``.

    The value is a release id6 or the literal `next`; `-` means ABSENT at every consumer. A
    QUOTED `- Blocks-Release:` in a body is not read as a declaration.
    """
    return read_text(metadata_region(text)).loose_blocks_release


_DETAIL_FIELD_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("summary", re.compile(r"(?mi)^-\s*Summary:\s*(.+)$")),
    ("scope", re.compile(r"(?mi)^-\s*Scope:\s*(.+)$")),
    ("concern", re.compile(r"(?mi)^-\s*Concern:\s*(.+)$")),
    ("question", re.compile(r"(?mi)^-\s*Question:\s*(.+)$")),
    ("title", re.compile(r"(?mi)^-\s*Title:\s*(.+)$")),
)

_FRONT_MATTER_BULLET_FORGE_RE: re.Pattern[str] = re.compile(
    r"^(-\s*[A-Za-z0-9_-]+:.*)$", re.MULTILINE
)


_DETAIL_KEY_RANK: Dict[str, int] = {
    "summary": 0,
    "scope": 1,
    "concern": 2,
    "question": 3,
    "title": 4,
}
_DETAIL_KEY_ORDER: Tuple[str, ...] = (
    "summary",
    "scope",
    "concern",
    "question",
    "title",
)
_DETAIL_FIRST_CHARS: frozenset[str] = frozenset("sScCqQtT")


def extract_detail_fields(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract ``(detail_kind, detail_text)`` using the metadata detail cascade.

    Checks ``Summary -> Scope -> Concern -> Question -> Title`` case-insensitively. At each
    step, a bulleted ``- <Key>: <value>`` entry wins over an unbulleted leading YAML
    front-matter ``<key>: <value>`` entry. Returns ``(None, None)`` when none of the five
    fields has a non-empty value.
    """
    if not text:
        return None, None
    best_rank = 99
    best_pair: Tuple[Optional[str], Optional[str]] = (None, None)
    n = len(text)
    pos = 0 if text.startswith("-") else text.find("\n-")
    while pos != -1:
        ls = pos if pos == 0 else pos + 1
        i = ls + 1
        while i < n and text[i] in " \t":
            i += 1
        if i < n and text[i] in _DETAIL_FIRST_CHARS:
            colon = text.find(":", i, i + 10)
            if colon != -1:
                key = text[i:colon].lower()
                rank = _DETAIL_KEY_RANK.get(key)
                if rank is not None and rank < best_rank:
                    nl = text.find("\n", colon + 1)
                    val = (
                        text[colon + 1 :] if nl == -1 else text[colon + 1 : nl]
                    ).strip()
                    if val:
                        best_rank = rank
                        best_pair = (key, val)
                        if rank == 0:
                            return best_pair
        pos = text.find("\n-", ls + 1)
    if text.startswith("---"):
        yaml_fields = read_text(metadata_region(text), record_type="research").fields
        for rank, tag in enumerate(_DETAIL_KEY_ORDER):
            if rank >= best_rank:
                break
            uval = str(yaml_fields.get(tag) or "").strip()
            if uval:
                return tag, uval
    return best_pair


def read_multiline_bullets(text: str, keys: Sequence[str]) -> List[str]:
    """Extract each top-level ``- <Key>:`` bullet value plus its continuation lines.

    Captures the text after ``:`` on each matching header line and all immediately following
    continuation lines until the next ``- `` bullet, ``#`` heading, or blank line. Returns one
    ``"\\n"``-joined string per matched bullet in document order.
    """
    cleaned_keys = [k for k in keys if k]
    if not text or not cleaned_keys:
        return []
    pat = re.compile(
        r"^-\s*(?:" + "|".join(re.escape(k) for k in cleaned_keys) + r"):[ \t]*(.*)$"
    )
    blocks: List[str] = []
    current: Optional[List[str]] = None
    for line in text.splitlines():
        m = pat.match(line)
        if m:
            if current is not None:
                blocks.append("\n".join(current))
            current = [m.group(1)]
            continue
        if current is not None:
            if line.startswith("- ") or line.startswith("#") or not line.strip():
                blocks.append("\n".join(current))
                current = None
            else:
                current.append(line)
    if current is not None:
        blocks.append("\n".join(current))
    return blocks


def read_review_subject_id(text: str) -> Optional[str]:
    """Return the 6-character ``Subject-Id`` declared in a review record's front matter, or None."""
    if not text:
        return None
    raw = str(read_text(metadata_region(text)).fields.get("subject_id") or "").strip()
    return raw if _core.ID6_RE.fullmatch(raw) else None


def neutralize_front_matter_bullets(text: str) -> str:
    """Indent any top-level ``- <Key>:`` line by two spaces to prevent front-matter forgery.

    Any line starting with ``-`` and optional whitespace followed by ``<Key>:`` (for example
    ``- Status:``, ``- Readiness:``, ``- Id:``, or ``- Blocks-Release:``) is indented by two
    spaces so untrusted text cannot be parsed as a front-matter field when appended to a record.
    """
    if not text:
        return text
    return _FRONT_MATTER_BULLET_FORGE_RE.sub(r"  \1", text)


def read(id6: str, *, project_context: Any = None) -> State:
    """Read current state of an artifact. Fails closed on invalid record."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=_scan_repo_root(ctx, records_root),
        )

        row = conn.execute(
            """SELECT id6, type, path, disposition, status, title, short_description,
                      set_id, order_nn, filename_date, created_day, created_at, updated_at,
                      last_history_day, last_seq, valid, defect, id_derived,
                      legacy_raw_status, legacy_raw_set
               FROM artifacts WHERE id6 = ?""",
            (id6,),
        ).fetchone()

        if not row:
            raise ValueError(f"artifact not found: {id6}")

        valid = row[15]
        defect = row[16]
        if valid == 0 or defect:
            raise ValueError(f"invalid record {id6}: {defect}")

        st = State(
            id6=row[0],
            type=row[1],
            path=row[2],
            disposition=row[3],
            status=row[4],
            title=row[5],
            short_description=row[6],
            set_id=row[7],
            order_nn=row[8],
            filename_date=row[9],
            created_day=row[10],
            created_at=row[11],
            updated_at=row[12],
            last_history_day=row[13],
            last_seq=row[14],
            valid=valid,
            defect=defect,
            id_derived=bool(row[17]),
            legacy_raw_status=row[18],
            legacy_raw_set=row[19],
        )

        # Populate type-specific fields
        t = row[1]
        if t in SUPPORTED_TYPES:
            t_row = conn.execute(
                f'SELECT * FROM "{t}" WHERE id6 = ?', (id6,)
            ).fetchone()
            if t_row:
                cursor = conn.execute(f'SELECT * FROM "{t}" LIMIT 0')
                col_names = [d[0] for d in cursor.description]
                for col, val in zip(col_names, t_row):
                    if col == "id6":
                        continue
                    if isinstance(val, str) and (
                        val.startswith("{") or val.startswith("[")
                    ):
                        with contextlib.suppress(Exception):
                            val = json.loads(val)
                    st.fields[col] = val

        return st
    finally:
        if should_close:
            conn.close()


def last_history(
    id6: str,
    *,
    project_context: Any = None,
    state: Optional[State] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Post-cutover `last_history_at` of a log-format record (spec 4.4): ``(value, precision)``.

    The value is the `at` of the newest event written after the cutover, precision ``time``. The
    migration's own append (`append` 0: the seq-0 checkpoint and its imported events) does not count,
    because every migrated event carries the migration's `at`. With no later event, the value is the
    checkpoint's `last_history_day`, precision ``day``; with neither, ``(None, None)``."""
    validate_id6(id6)
    for ev in reversed(history(id6, project_context=project_context)):
        if not isinstance(ev, dict) or ev.get("append") == 0:
            continue
        if ev.get("op") in ("legacy", "checkpoint"):
            continue
        at_val = ev.get("at")
        if isinstance(at_val, str) and _RFC3339_RE.match(at_val):
            return at_val, "time"
    st = state if state is not None else read(id6, project_context=project_context)
    day = getattr(st, "last_history_day", None)
    if isinstance(day, str) and day:
        return day, "day"
    return None, None


def history(id6: str, *, project_context: Any = None) -> List[Dict[str, Any]]:
    """Return ordered event history of an artifact."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    scan_repo = _scan_repo_root(ctx, records_root)
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=scan_repo,
        )

        # Check if we have events
        events = conn.execute(
            """SELECT seq, append, op, at, actor_id, by_human, from_status, to_status, path, message, raw
               FROM events WHERE id6 = ? ORDER BY seq ASC""",
            (id6,),
        ).fetchall()

        if events:
            res: List[Dict[str, Any]] = []
            for r in events:
                raw_json = r[10]
                if raw_json:
                    res.append(json.loads(raw_json))
                else:
                    res.append(
                        {
                            "seq": r[0],
                            "append": r[1],
                            "op": r[2],
                            "at": r[3],
                            "actor_id": r[4],
                            "by_human": bool(r[5]),
                            "from": r[6],
                            "to": r[7],
                            "path": r[8],
                            "message": r[9],
                        }
                    )
            return res

        # Otherwise return legacy history lines
        art = conn.execute(
            "SELECT path, last_history_day, valid, defect FROM artifacts WHERE id6 = ?",
            (id6,),
        ).fetchone()
        if art and (art[2] == 0 or art[3]):
            # Fail closed on an invalid record rather than re-parsing its source as a
            # legacy `.md` file (1ajqaa): never return stale or misparsed history.
            raise ValueError(f"invalid record {id6}: {art[3]}")
        legacy_rows: List[Dict[str, Any]] = []
        if art and art[0]:
            abs_p = source_path(art[0], records_root, scan_repo)
            if abs_p.exists() and abs_p.suffix == ".md":
                _, legacy_rows = load_legacy_artifact(
                    abs_p, records_root, repo_root=scan_repo
                )

        # Phase B: each review ROUND of a legacy review file is a `review` event of its SUBJECT
        # (4.1a), appended after the history lines in file order, with no inferred ordering.
        for rv in conn.execute(
            """SELECT r.seq, r.round, r.review_kind, r.verdict, r.legacy_verdict, r.observed_day,
                      r.readiness, r.review_depth, r.reviewer, r.review_ref
               FROM reviews r
               WHERE r.subject_id6 = ? ORDER BY r.seq""",
            (id6,),
        ).fetchall():
            row: Dict[str, Any] = {
                "id6": id6,
                "op": "review",
                "round": rv[1],
                "review_kind": rv[2],
                "observed_day": rv[5],
                "source": "review-file",
            }
            for k, v in (
                ("verdict", rv[3]),
                ("legacy_verdict", rv[4]),
                ("readiness", rv[6]),
                ("review_depth", rv[7]),
                ("reviewer", rv[8]),
                ("review_ref", rv[9]),
            ):
                if v is not None:
                    row[k] = v
            legacy_rows.append(row)

        return legacy_rows
    finally:
        if should_close:
            conn.close()


def resolve(
    path_or_id6: Union[str, Path], *, project_context: Any = None
) -> Optional[str]:
    """Resolve a path or id6 to its canonical records-root-relative path."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    scan_repo = _scan_repo_root(ctx, records_root)
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=scan_repo,
        )

        val = str(path_or_id6).strip()
        if _core.ID6_RE.fullmatch(val):
            row = conn.execute(
                "SELECT path FROM artifacts WHERE id6 = ?", (val,)
            ).fetchone()
            return row[0] if row else None

        # Path lookup
        clean = val.replace("\\", "/")
        # Exact path in artifacts
        row = conn.execute(
            "SELECT path FROM artifacts WHERE path = ?", (clean,)
        ).fetchone()
        if row:
            return row[0]

        # Check artifact_paths historical paths
        row = conn.execute(
            "SELECT path FROM artifact_paths WHERE path = ? ORDER BY seq DESC LIMIT 1",
            (clean,),
        ).fetchone()
        if row:
            return row[0]

        return None
    finally:
        if should_close:
            conn.close()


def query(
    *,
    project_context: Any = None,
    include_fields: bool = False,
    **filters,
) -> QueryResult:
    """Query metadata cache with typed filters. Returns QueryResult."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    scan_repo = _scan_repo_root(ctx, records_root)
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=scan_repo,
        )

        where_clauses: List[str] = ["a.valid = 1"]
        params: List[Any] = []

        # Map supported filters
        if "id6" in filters:
            where_clauses.append("a.id6 = ?")
            params.append(filters["id6"])

        if "type" in filters:
            where_clauses.append("a.type = ?")
            params.append(filters["type"])

        if "status" in filters:
            where_clauses.append("a.status = ?")
            params.append(filters["status"])

        if "set_id" in filters:
            where_clauses.append("a.set_id = ?")
            params.append(filters["set_id"])
        elif "set" in filters:
            where_clauses.append("a.set_id = ?")
            params.append(filters["set"])

        if "order_nn" in filters:
            where_clauses.append("a.order_nn = ?")
            params.append(int(filters["order_nn"]))
        elif "order" in filters:
            where_clauses.append("a.order_nn = ?")
            params.append(int(filters["order"]))

        if "path" in filters:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM artifact_paths ap WHERE ap.id6 = a.id6 AND ap.path = ?)"
            )
            params.append(filters["path"])

        if "depends_on" in filters:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM dependencies d WHERE d.dependent_id6 = a.id6 AND d.target_id6 = ?)"
            )
            params.append(filters["depends_on"])

        if "latest_gate_review_of" in filters:
            subj_id = filters["latest_gate_review_of"]
            where_clauses.append(
                "EXISTS (SELECT 1 FROM reviews r WHERE r.subject_id6 = a.id6 AND r.subject_id6 = ? AND r.review_kind = 'gate')"
            )
            params.append(subj_id)

        sql = f"""SELECT a.id6, a.type, a.path, a.disposition, a.status, a.title, a.short_description,
                         a.set_id, a.order_nn, a.filename_date, a.created_day, a.created_at, a.updated_at,
                         a.last_history_day, a.last_seq, a.valid, a.defect, a.id_derived,
                         a.legacy_raw_status, a.legacy_raw_set
                  FROM artifacts a
                  WHERE {" AND ".join(where_clauses)}
                  ORDER BY a.set_id, a.order_nn, a.id6"""

        rows = conn.execute(sql, params).fetchall()
        states: List[State] = []
        for r in rows:
            st = State(
                id6=r[0],
                type=r[1],
                path=r[2],
                disposition=r[3],
                status=r[4],
                title=r[5],
                short_description=r[6],
                set_id=r[7],
                order_nn=r[8],
                filename_date=r[9],
                created_day=r[10],
                created_at=r[11],
                updated_at=r[12],
                last_history_day=r[13],
                last_seq=r[14],
                valid=r[15],
                defect=r[16],
                id_derived=bool(r[17]),
                legacy_raw_status=r[18],
                legacy_raw_set=r[19],
            )
            states.append(st)

        if include_fields and states:
            by_type: Dict[str, Dict[str, State]] = {}
            for st in states:
                if st.type in SUPPORTED_TYPES and st.id6:
                    by_type.setdefault(st.type, {})[st.id6] = st
            for t, state_by_id in by_type.items():
                cur = conn.execute(f'SELECT * FROM "{t}"')
                col_names = [d[0] for d in cur.description]
                try:
                    id_idx = col_names.index("id6")
                except ValueError:
                    continue
                for t_row in cur.fetchall():
                    st_obj = state_by_id.get(t_row[id_idx])
                    if st_obj is None:
                        continue
                    for idx, col in enumerate(col_names):
                        if idx == id_idx:
                            continue
                        val = t_row[idx]
                        if isinstance(val, str) and (
                            val.startswith("{") or val.startswith("[")
                        ):
                            with contextlib.suppress(Exception):
                                val = json.loads(val)
                        st_obj.fields[col] = val

        # Check for invalid records that matched the domain
        incomplete_rows = conn.execute(
            "SELECT id6 FROM artifacts WHERE valid = 0"
        ).fetchall()
        incomplete = [ir[0] for ir in incomplete_rows]

        return QueryResult(states, incomplete)
    finally:
        if should_close:
            conn.close()


def query_lineage(
    *,
    relation: Optional[str] = None,
    child_type: Optional[str] = None,
    project_context: Any = None,
) -> List[Dict[str, Any]]:
    """Query cached lineage rows joined with valid artifact metadata."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    scan_repo = _scan_repo_root(ctx, records_root)
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=scan_repo,
        )
        where_clauses = ["a.valid = 1"]
        params: List[Any] = []
        if relation is not None:
            where_clauses.append("l.relation = ?")
            params.append(relation)
        if child_type is not None:
            where_clauses.append("a.type = ?")
            params.append(child_type)
        sql = f"""SELECT l.child_id6, l.relation, l.parent_raw, l.parent_id6,
                         a.type, a.path, a.status, a.id_derived,
                         a.legacy_raw_status, a.legacy_raw_set, a.set_id
                  FROM lineage l
                  JOIN artifacts a ON a.id6 = l.child_id6
                  WHERE {" AND ".join(where_clauses)}
                  ORDER BY a.type, a.path, l.relation, l.parent_raw"""
        rows = conn.execute(sql, params).fetchall()
        return [
            {
                "child_id6": r[0],
                "relation": r[1],
                "parent_raw": r[2],
                "parent_id6": r[3],
                "type": r[4],
                "path": r[5],
                "status": r[6],
                "id_derived": bool(r[7]),
                "legacy_raw_status": r[8],
                "legacy_raw_set": r[9],
                "set_id": r[10],
            }
            for r in rows
        ]
    finally:
        if should_close:
            conn.close()


def review_rows(
    subject_id6: str, *, project_context: Any = None
) -> List[Dict[str, Any]]:
    """One row per cached review FILE of ``subject_id6``: `path`, `parse_ok`, `review_kind`.

    The read behind the `->reviewed` attestation (plan 2xwb9b E-12, spec 4.4 SR-601). It reads the
    `review_files` table, which has one row per file, rather than joining `reviews`: two files that
    are both named by the subject's own id6 share a NULL `review_ref` and so collide in `reviews`
    (backlog filed by 2xwb9b), which would let one file's kind stand in for the other's. The kind is
    the loader's own per-file rule (:func:`review_kind_of_file`). The freshness check runs first, so a
    review file that is still uncommitted in a lane worktree is seen exactly as it is on disk."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    scan_repo = _scan_repo_root(ctx, records_root)
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        _maybe_check_freshness(
            conn,
            records_root,
            state_root,
            project_context=ctx,
            repo_root=scan_repo,
        )
        rows = conn.execute(
            "SELECT path, parse_ok, round_count FROM review_files WHERE subject_id6 = ? ORDER BY path",
            (subject_id6,),
        ).fetchall()
    finally:
        if should_close:
            conn.close()
    return [
        {
            "path": r[0],
            "parse_ok": bool(r[1]),
            "round_count": r[2],
            "review_kind": review_kind_of_file(r[0]),
        }
        for r in rows
    ]


def review_kind_of_file(path: Union[str, Path]) -> str:
    """The `review_kind` the legacy loader assigns a review file (`load_legacy_review`'s rule)."""
    p = str(path).replace("\\", "/")
    return (
        "refinement"
        if "spec-refinement" in Path(p).name or "refinement" in p
        else "gate"
    )


@dataclasses.dataclass
class ReadAtResult:
    kind: str  # ok, absent, invalid-revision, unversioned, corrupt
    state: Optional[State] = None
    error: Optional[str] = None
    history: List[Dict[str, Any]] = dataclasses.field(default_factory=list)


def _norm_git_rel_path(path: str) -> str:
    norm = path.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    return norm.lstrip("/")


def _index_stage_of(rev: str) -> Optional[str]:
    """Return index stage digit ('0'..'3') for ':<stage>:' revisions, else None."""
    if (
        len(rev) == 3
        and rev[0] == ":"
        and rev[2] == ":"
        and rev[1] in ("0", "1", "2", "3")
    ):
        return rev[1]
    return None


def _git_blob_sha(repo_dir: Path, rev: str, repo_rel_path: str) -> Optional[str]:
    """Return the git blob SHA for ``repo_rel_path`` at commit/tree ``rev`` or index stage ``:<stage>:``."""
    norm = _norm_git_rel_path(repo_rel_path)
    if not norm:
        return None
    stage = _index_stage_of(rev)
    if stage is not None:
        res = subprocess.run(
            ["git", "ls-files", "-s", "--", norm],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0 or not res.stdout.strip():
            return None
        for line in res.stdout.splitlines():
            meta_part, sep, path_part = line.partition("\t")
            if not sep or path_part.strip() != norm:
                continue
            cols = meta_part.split()
            if len(cols) >= 3 and cols[2] == stage:
                return cols[1]
        return None

    res = subprocess.run(
        ["git", "rev-parse", "--verify", f"{rev}:{norm}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        return None
    sha = res.stdout.strip()
    return sha or None


def _read_git_blob_bytes(repo_dir: Path, blob_sha: str) -> Optional[bytes]:
    """Read exact raw bytes of git object ``blob_sha`` via ``git cat-file -p``."""
    cat = subprocess.run(
        ["git", "cat-file", "-p", blob_sha],
        cwd=repo_dir,
        capture_output=True,
    )
    return cat.stdout if cat.returncode == 0 else None


def _read_git_blob(repo_dir: Path, blob_sha: str) -> Optional[str]:
    """Read strict UTF-8 text of git object ``blob_sha`` via ``git cat-file -p``.

    Returns ``None`` when the object cannot be read or contains invalid UTF-8 bytes so
    ``read_at`` / ``read_path_at`` fail closed as ``corrupt`` without caching a valid row.
    """
    raw = _read_git_blob_bytes(repo_dir, blob_sha)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _cache_rev_write(
    conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...]
) -> None:
    """Commit a single revision-cache row, tolerating transient SQLite lock contention."""
    try:
        with conn:
            conn.execute(sql, params)
    except sqlite3.OperationalError as exc:
        if not _is_sqlite_lock_error(exc):
            raise


def resolve_mirror_at(
    rel_path: str,
    rev: str,
    *,
    project_context: Any = None,
) -> Tuple[Optional[str], Optional[str], bool]:
    """Return ``(declared_id6, status, exists_at_rev)`` for ``rel_path`` at commit ``rev`` or ``:0:``.

    Uses the git blob SHA keyed against ``rev_mirrors`` and feeds misses to ``read_text`` (the
    same phase-B / v2 mirror loader), never falling back to the working tree.
    """
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    repo_dir = _proj_ctx.record_git_root(records_root)
    if repo_dir is None:
        return None, None, False

    if _index_stage_of(rev) is None:
        chk = subprocess.run(
            ["git", "rev-parse", "--verify", f"{rev}^{{tree}}"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if chk.returncode != 0:
            return None, None, False

    blob_sha = _git_blob_sha(repo_dir, rev, rel_path)
    if blob_sha is None:
        return None, None, False

    conn, should_close = _open_for_read(records_root, state_root)
    try:
        cached = conn.execute(
            "SELECT id6, status FROM rev_mirrors WHERE md_blob_sha = ?",
            (blob_sha,),
        ).fetchone()
        if cached is not None:
            cid = (
                cached[0] if (cached[0] and _core.ID6_RE.fullmatch(cached[0])) else None
            )
            return cid, cached[1], True

        text = _read_git_blob(repo_dir, blob_sha)
        if text is None:
            return None, None, False

        rt = read_text(text)
        declared = rt.id6 if (rt.id6 and _core.ID6_RE.fullmatch(rt.id6)) else None
        mirror_status = rt.status or (
            rt.legacy_raw_status.strip().split()[0].lower()
            if rt.legacy_raw_status and rt.legacy_raw_status.strip()
            else None
        )
        _cache_rev_write(
            conn,
            "INSERT OR REPLACE INTO rev_mirrors VALUES (?, ?, ?)",
            (blob_sha, declared or "", mirror_status),
        )
        return declared, mirror_status, True
    finally:
        if should_close:
            conn.close()


def resolve_id_at(
    rel_path: str,
    rev: str,
    *,
    project_context: Any = None,
) -> Optional[str]:
    """Resolve the declared ``id6`` of ``rel_path`` inside commit ``rev`` or staged index ``:0:``."""
    declared, _status, _exists = resolve_mirror_at(
        rel_path, rev, project_context=project_context
    )
    return declared


def _load_legacy_at_blob(
    conn: sqlite3.Connection,
    repo_dir: Path,
    records_root: Path,
    rel_repo: str,
    rev: str,
    md_file_path: str,
    *,
    require_id6: Optional[str] = None,
) -> Optional[ReadAtResult]:
    """Load and mirror-cache a Phase B Markdown blob at ``rev`` via ``load_legacy_artifact``."""
    md_blob_sha = _git_blob_sha(repo_dir, rev, md_file_path)
    if md_blob_sha is None:
        return None
    blob_text = _read_git_blob(repo_dir, md_blob_sha)
    if blob_text is None:
        return ReadAtResult(kind="corrupt", error="failed to read md blob")
    if require_id6 is not None:
        rt = read_text(blob_text)
        if rt.id6 != require_id6:
            return None
    try:
        if rel_repo and rel_repo != "." and md_file_path.startswith(f"{rel_repo}/"):
            in_records = md_file_path[len(rel_repo) + 1 :]
            target_path = records_root / in_records
        elif not rel_repo or rel_repo == ".":
            target_path = records_root / md_file_path
        else:
            target_path = repo_dir / md_file_path
        art_row, hist_rows = load_legacy_artifact(
            target_path, records_root, text=blob_text, repo_root=repo_dir
        )
        _cache_rev_write(
            conn,
            "INSERT OR REPLACE INTO rev_mirrors VALUES (?, ?, ?)",
            (md_blob_sha, art_row["id6"], art_row["status"]),
        )
        st = State(
            id6=art_row["id6"],
            type=art_row["type"],
            path=art_row["path"],
            disposition=art_row.get("disposition"),
            status=art_row["status"],
            title=art_row["title"],
            short_description=art_row["short_description"],
            set_id=art_row["set_id"],
            order_nn=art_row["order_nn"],
            filename_date=art_row.get("filename_date"),
            created_day=art_row.get("created_day"),
            last_history_day=art_row.get("last_history_day"),
            last_seq=art_row.get("last_seq", 0),
            id_derived=bool(art_row.get("id_derived", False)),
            fields=dict(art_row.get("fields") or {}),
            legacy_raw_status=art_row.get("legacy_raw_status"),
            legacy_raw_set=art_row.get("legacy_raw_set"),
        )
        return ReadAtResult(kind="ok", state=st, history=hist_rows)
    except Exception as exc:
        return ReadAtResult(kind="corrupt", error=str(exc))


def read_path_at(
    rel_path: str,
    rev: str,
    *,
    project_context: Any = None,
) -> ReadAtResult:
    """Read metadata state for a path at ``rev`` (``:0:`` or commit) when no valid id6 is declared."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    _require_schema(ctx, records_root)

    repo_dir = _proj_ctx.record_git_root(records_root)
    if repo_dir is None:
        return ReadAtResult(
            kind="unversioned", error="unversioned placement: no git repository found"
        )

    stage = _index_stage_of(rev)
    if stage is None:
        res = subprocess.run(
            ["git", "rev-parse", "--verify", f"{rev}^{{tree}}"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            return ReadAtResult(
                kind="invalid-revision", error=f"invalid revision {rev!r}"
            )

    try:
        rel_repo = str(records_root.resolve().relative_to(repo_dir.resolve())).replace(
            "\\", "/"
        )
    except Exception:
        rel_repo = ""

    conn, should_close = _open_for_read(records_root, state_root)
    try:
        norm = _norm_git_rel_path(rel_path)
        hit = _load_legacy_at_blob(
            conn, repo_dir, records_root, rel_repo, rev, norm, require_id6=None
        )
        if hit is not None:
            return hit
        return ReadAtResult(
            kind="absent", error=f"path {rel_path!r} not found in revision {rev}"
        )
    finally:
        if should_close:
            conn.close()


def read_at(
    id6: str,
    rev: str,
    *,
    project_context: Any = None,
    path_hint: Optional[str] = None,
) -> ReadAtResult:
    """Read metadata state at a git revision (``:0:`` staged index, HEAD, SHA, branch, etc.)."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    _require_schema(ctx, records_root)

    repo_dir = _proj_ctx.record_git_root(records_root)
    if repo_dir is None:
        return ReadAtResult(
            kind="unversioned", error="unversioned placement: no git repository found"
        )

    stage = _index_stage_of(rev)
    is_index = stage is not None
    conn, should_close = _open_for_read(records_root, state_root)
    try:
        # Verify tree-ish revision exists (index stages `:0:`..`:3:` are valid even with unborn HEAD)
        if not is_index:
            res = subprocess.run(
                ["git", "rev-parse", "--verify", f"{rev}^{{tree}}"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                return ReadAtResult(
                    kind="invalid-revision", error=f"invalid revision {rev!r}"
                )

        # Find the log file or artifact file in revision
        try:
            rel_repo = str(
                records_root.resolve().relative_to(repo_dir.resolve())
            ).replace("\\", "/")
        except Exception:
            rel_repo = ""
        log_path = f"meta/{id6}.jsonl"
        rel_log = (
            log_path if not rel_repo or rel_repo == "." else f"{rel_repo}/{log_path}"
        )

        log_blob_sha = _git_blob_sha(repo_dir, rev, rel_log)
        if log_blob_sha:
            # Lookup in rev_log_states
            cached = conn.execute(
                "SELECT id6, status, last_seq, state_json FROM rev_log_states WHERE log_blob_sha = ?",
                (log_blob_sha,),
            ).fetchone()
            if cached:
                s_dict = json.loads(cached[3])
                st = State(**s_dict)
                hist_events: List[Dict[str, Any]] = []
                raw_log = _read_git_blob(repo_dir, log_blob_sha)
                if raw_log is not None:
                    for raw_ln in raw_log.splitlines(keepends=True):
                        if raw_ln.strip():
                            with contextlib.suppress(Exception):
                                hist_events.append(decode_line(raw_ln))
                return ReadAtResult(kind="ok", state=st, history=hist_events)

            raw_log = _read_git_blob(repo_dir, log_blob_sha)
            if raw_log is None:
                return ReadAtResult(
                    kind="corrupt", error=f"cannot read git blob {log_blob_sha}"
                )

            try:
                lines = raw_log.splitlines(keepends=True)
                decoded_events = [decode_line(ln) for ln in lines if ln.strip()]
                art_type = "ipd"
                if decoded_events:
                    cand_type = (decoded_events[0].get("fields") or {}).get("type")
                    if cand_type in SUPPORTED_TYPES:
                        art_type = cand_type
                state, _, _, _ = replay(id6, art_type, lines, records_root=records_root)
                # Cache valid state
                _cache_rev_write(
                    conn,
                    "INSERT OR REPLACE INTO rev_log_states VALUES (?, ?, ?, ?, ?)",
                    (
                        log_blob_sha,
                        id6,
                        state.status,
                        state.last_seq,
                        json.dumps(dataclasses.asdict(state)),
                    ),
                )
                return ReadAtResult(kind="ok", state=state, history=decoded_events)
            except Exception as exc:
                return ReadAtResult(kind="corrupt", error=str(exc))

        # Phase B legacy check: resolve artifact .md containing declared `- Id: <id6>` at revision.
        candidates: List[str] = []
        if path_hint:
            hint_norm = _norm_git_rel_path(path_hint)
            if hint_norm:
                candidates.append(hint_norm)

        for cand in candidates:
            hit = _load_legacy_at_blob(
                conn, repo_dir, records_root, rel_repo, rev, cand, require_id6=id6
            )
            if hit is not None:
                return hit

        if stage in ("1", "2", "3"):
            ls_cmd = ["git", "ls-files", "-u"]
            if rel_repo and rel_repo != ".":
                ls_cmd += ["--", rel_repo]
            ls_unmerged = subprocess.run(
                ls_cmd,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if ls_unmerged.returncode == 0 and ls_unmerged.stdout.strip():
                seen_cands = set(candidates)
                for line in ls_unmerged.stdout.splitlines():
                    meta_part, sep, path_part = line.partition("\t")
                    if not sep:
                        continue
                    cols = meta_part.split()
                    if len(cols) < 3 or cols[2] != stage:
                        continue
                    md_file_path = path_part.strip()
                    if not md_file_path or md_file_path in seen_cands:
                        continue
                    seen_cands.add(md_file_path)
                    hit = _load_legacy_at_blob(
                        conn,
                        repo_dir,
                        records_root,
                        rel_repo,
                        rev,
                        md_file_path,
                        require_id6=id6,
                    )
                    if hit is not None:
                        return hit
            return ReadAtResult(
                kind="absent", error=f"record {id6} not found in revision {rev}"
            )

        # `-e` is required: the pattern starts with `-`, so without it git reads it as an option and
        # exits 129, which made every phase-B record read `absent`.
        # Use POSIX character classes (`[[:blank:]]` / `[[:space:]]`) rather than `\t` / `\r`:
        # BSD/Windows POSIX ERE may treat `\t`/`\r` as literal chars, and Windows blobs with CRLF
        # retain `\r` before `$` when `git grep` splits lines on `\n`.
        if is_index:
            grep_cmd = [
                "git",
                "grep",
                "--cached",
                "-l",
                "-E",
                "-e",
                f"^- Id:[[:blank:]]*{id6}[[:space:]]*$",
            ]
        else:
            grep_cmd = [
                "git",
                "grep",
                "-l",
                "-E",
                "-e",
                f"^- Id:[[:blank:]]*{id6}[[:space:]]*$",
                rev,
            ]
        if rel_repo and rel_repo != ".":
            grep_cmd += ["--", rel_repo]
        find_md = subprocess.run(
            grep_cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if find_md.returncode == 0 and find_md.stdout.strip():
            seen_cands = set(candidates)
            for md_entry in find_md.stdout.strip().splitlines():
                if is_index:
                    md_file_path = md_entry
                else:
                    md_file_path = (
                        md_entry[len(rev) + 1 :]
                        if md_entry.startswith(f"{rev}:")
                        else md_entry
                    )
                if md_file_path in seen_cands:
                    continue
                seen_cands.add(md_file_path)
                hit = _load_legacy_at_blob(
                    conn,
                    repo_dir,
                    records_root,
                    rel_repo,
                    rev,
                    md_file_path,
                    require_id6=id6,
                )
                if hit is not None:
                    return hit

        return ReadAtResult(
            kind="absent", error=f"record {id6} not found in revision {rev}"
        )
    finally:
        if should_close:
            conn.close()


def check_staged_log_append(
    id6: str,
    *,
    project_context: Any = None,
) -> List[str]:
    """Validate that a staged ``meta/<id6>.jsonl`` change only appends valid whole event lines.

    Reads the HEAD and staged (``:0:``) log blobs through ``read_at``'s blob path and the
    ``artifact_meta`` loader so no caller outside ``artifact_meta`` opens log bytes (spec
    ``4sd62s`` 4.3, 4.8).

    Returns a list of teaching refusal messages naming the log path; an empty list means
    the staged log change is acceptable (or no staged log change exists for ``id6``).
    """
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    _require_schema(ctx, records_root)

    repo_dir = _proj_ctx.record_git_root(records_root)
    if repo_dir is None:
        return [
            f"meta/{id6}.jsonl: unversioned placement (no git repository found); "
            "cannot validate staged append rules."
        ]

    try:
        rel_repo = str(records_root.resolve().relative_to(repo_dir.resolve())).replace(
            "\\", "/"
        )
    except Exception:
        rel_repo = ""
    log_path = f"meta/{id6}.jsonl"
    rel_log = log_path if not rel_repo or rel_repo == "." else f"{rel_repo}/{log_path}"

    head_blob_sha = _git_blob_sha(repo_dir, "HEAD", rel_log)
    staged_blob_sha = _git_blob_sha(repo_dir, ":0:", rel_log)

    if head_blob_sha is None and staged_blob_sha is None:
        return []

    if head_blob_sha is not None and staged_blob_sha is None:
        return [
            f"{rel_log}: staged commit deletes an existing metadata event log; "
            "metadata event logs are append-only. Restore the HEAD log with "
            f"`git checkout HEAD -- {rel_log}` and record changes through aw tools."
        ]

    if head_blob_sha is not None and staged_blob_sha == head_blob_sha:
        return []

    assert staged_blob_sha is not None
    staged_bytes = _read_git_blob_bytes(repo_dir, staged_blob_sha)
    if staged_bytes is None:
        return [f"{rel_log}: cannot read staged git blob {staged_blob_sha}."]

    try:
        staged_text = staged_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [
            f"{rel_log}: staged metadata event log is not valid UTF-8 ({exc}); "
            "append valid canonical JSONL events through aw tools."
        ]

    if head_blob_sha is not None:
        head_bytes = _read_git_blob_bytes(repo_dir, head_blob_sha)
        if head_bytes is None:
            return [f"{rel_log}: cannot read HEAD git blob {head_blob_sha}."]

        if not staged_bytes.startswith(head_bytes):
            head_lines = head_bytes.splitlines(keepends=True)
            staged_lines = staged_bytes.splitlines(keepends=True)
            first_diff = 0
            while (
                first_diff < len(head_lines)
                and first_diff < len(staged_lines)
                and head_lines[first_diff] == staged_lines[first_diff]
            ):
                first_diff += 1
            if len(staged_lines) < len(head_lines) and (
                staged_lines == head_lines[: len(staged_lines)]
                or all(ln in head_lines for ln in staged_lines)
            ):
                return [
                    f"{rel_log}: staged log deleted line(s) from HEAD "
                    f"(HEAD has {len(head_lines)} line(s), staged has {len(staged_lines)}); "
                    "metadata event logs are append-only. Restore the HEAD lines unchanged "
                    "and append new events through aw tools instead of editing the log by hand."
                ]
            if first_diff < len(head_lines):
                return [
                    f"{rel_log}: staged log rewrote earlier line {first_diff + 1} "
                    "(staged bytes do not preserve the HEAD prefix verbatim); "
                    "metadata event logs are append-only. Restore the HEAD bytes unchanged "
                    "and append new events through aw tools instead of editing the log by hand."
                ]
            return [
                f"{rel_log}: staged bytes do not preserve the HEAD log prefix verbatim; "
                "metadata event logs are append-only. Restore HEAD and append new events "
                "through aw tools."
            ]

        if head_bytes and not head_bytes.endswith(b"\n"):
            return [
                f"{rel_log}: HEAD log does not end with LF, so staged bytes cannot append "
                "whole new lines; repair the log before appending."
            ]

        appended_bytes = staged_bytes[len(head_bytes) :]
        if not appended_bytes.endswith(b"\n"):
            return [
                f"{rel_log}: appended line in staged log does not end with LF "
                "(whole new lines only); append canonical JSONL events through aw tools."
            ]

        appended_text = appended_bytes.decode("utf-8")
        appended_lines = appended_text.splitlines(keepends=True)
        appended_events: List[Dict[str, Any]] = []
        for offset, raw_ln in enumerate(appended_lines, start=1):
            try:
                ev = decode_line(raw_ln)
            except Exception as exc:
                return [
                    f"{rel_log}: invalid appended event at new line {offset} ({exc}); "
                    "append valid canonical JSONL events through aw tools."
                ]
            appended_events.append(ev)

        head_res = read_at(id6, "HEAD", project_context=ctx)
        if head_res.kind == "ok" and head_res.state is not None:
            expected_seq = head_res.state.last_seq + 1
            for offset, ev in enumerate(appended_events, start=1):
                ev_seq = ev.get("seq")
                if isinstance(ev_seq, bool) or ev_seq != expected_seq:
                    return [
                        f"{rel_log}: appended event at new line {offset} has seq {ev_seq!r}, "
                        f"expected consecutive seq {expected_seq} after HEAD seq "
                        f"{head_res.state.last_seq}; append events with consecutive seq "
                        "numbers through aw tools."
                    ]
                expected_seq += 1
            if appended_events and appended_events[0].get("append") != appended_events[
                0
            ].get("seq"):
                first_app = appended_events[0]
                return [
                    f"{rel_log}: first appended event at seq {first_app.get('seq')!r} "
                    f"has append {first_app.get('append')!r} (a new staged write must start "
                    "a fresh append run with append == seq); append events through aw tools."
                ]
    else:
        if not staged_bytes:
            return [
                f"{rel_log}: new metadata event log is empty; a new log must start with "
                "a `create` event (seq 1) or a `checkpoint` event (seq 0)."
            ]
        if not staged_bytes.endswith(b"\n"):
            return [
                f"{rel_log}: new staged log does not end with LF (whole canonical JSONL "
                "lines only); create metadata event logs through aw tools."
            ]
        staged_lines = staged_text.splitlines(keepends=True)
        try:
            first_ev = decode_line(staged_lines[0])
        except Exception as exc:
            return [
                f"{rel_log}: invalid first event in new log ({exc}); a new log must start "
                "with a `create` event (seq 1) or a `checkpoint` event (seq 0)."
            ]
        first_op = first_ev.get("op")
        first_seq = first_ev.get("seq")
        if not (
            (
                first_op == "create"
                and not isinstance(first_seq, bool)
                and first_seq == 1
            )
            or (
                first_op == "checkpoint"
                and not isinstance(first_seq, bool)
                and first_seq == 0
            )
        ):
            return [
                f"{rel_log}: bad first event in new log (got op={first_op!r}, "
                f"seq={first_seq!r}); a new metadata event log must start with `create` "
                "at seq 1 or `checkpoint` at seq 0."
            ]
        expected_seq = first_seq
        for line_no, raw_ln in enumerate(staged_lines, start=1):
            try:
                ev = decode_line(raw_ln)
            except Exception as exc:
                return [
                    f"{rel_log}: invalid event at line {line_no} ({exc}); "
                    "write valid canonical JSONL events through aw tools."
                ]
            ev_seq = ev.get("seq")
            if isinstance(ev_seq, bool) or ev_seq != expected_seq:
                return [
                    f"{rel_log}: event at line {line_no} has seq {ev_seq!r}, "
                    f"expected consecutive seq {expected_seq}; events in a staged log "
                    "must have consecutive seq numbers."
                ]
            expected_seq += 1

    staged_res = read_at(id6, ":0:", project_context=ctx)
    if staged_res.kind != "ok":
        detail = staged_res.error or f"staged log validation failed ({staged_res.kind})"
        return [
            f"{rel_log}: loader refused staged log ({detail}); "
            "append only valid events with consecutive seq and valid append values through aw tools."
        ]
    if staged_res.state is None or staged_res.state.id6 != id6:
        declared = staged_res.state.id6 if staged_res.state is not None else None
        return [
            f"{rel_log}: loader refused staged log (identity-changed: declared id "
            f"{declared!r} != {id6!r}); append only valid events for `{id6}` through aw tools."
        ]
    return []


# --------------------------------------------------------------------------------------
# 12. Write Path, Journal & Repair (E-15, E-16, 4.3, 4.7)
# --------------------------------------------------------------------------------------


def _atomic_replace_fsync(path: Path, content: str) -> None:
    """Write content to temporary file in path.parent, fsync, and replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.parent / f".tmp-{path.name}-{os.getpid()}"
    with open(temp_path, "wb") as f:
        f.write(content.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, path)


def _journal_dir(state_root: Path) -> Path:
    d = state_root / "operation_journal"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------------------
# 12a. Phase-B LEGACY write branch (plan 2xwb9b E-03..E-06; spec 4sd62s 4.3, 4.4, C10a)
#
# Until the cutover (Order 13, `cxxmyv`) no record in a live repository has a `meta/<id6>.jsonl`
# log, so every write must keep today's bullet format byte for byte (C10a). `append` therefore
# dispatches on the TARGET's storage format: a record with a log takes the log branch above (still
# exercised by tve77h's synthetic-log tests), and a record without one takes this branch, which
# renders the SAME events into the Markdown file instead of appending them to a log. The event
# validation (envelope, payload schema, writer-side refusals) and the event-owned field rules are the
# same ones the log branch and `replay` apply, so the rules cannot differ between the two formats.
#
# Everything in this section except `WritePreview` is phase-B only and is deleted with the legacy
# branch at the cutover (`LegacyRender`, the path-keyed target, `legacy_context`).
# --------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class LegacyRender:
    """The exact history-line tokens today's bullet format writes (`- <day> <tag> (<actor>): <msg>`).

    The event schema has no home for the `same-status` tag, a back-dated `--date` day or the
    `--allow-*` actor suffixes (2xwb9b OQ-02), so phase B carries them beside the events. `tag=None`
    with `history=False` writes no history line (a duplicate same-status re-assertion)."""

    tag: str
    day: str
    actor_label: str
    history: bool = True
    is_prompt: bool = False
    #: The status the file's mirror must show after the write. Today's setter rewrites the mirror
    #: even on a same-status write (normalizing an alias or an annotated legacy value), which a
    #: `note` event cannot express; `None` means "the transition's target, if any".
    status: Optional[str] = None
    #: Model attribution for `- Coverage-Checked: <day> by <checked_by>` on `op == "coverage"`,
    #: decoupled from `actor_label` (which labels the `## Workflow history` entry).
    checked_by: Optional[str] = None
    #: When True and `## Workflow history` is absent, append the created heading at EOF
    #: (preserving pre-history header prose containing `## ` subheadings).
    history_at_end: bool = False


@dataclasses.dataclass(frozen=True)
class SidecarRecord:
    """The values of the gitignored history sidecar record a specs/backlog setter writes today."""

    tree: str
    workflow: str
    actor: str
    message: str
    date: Optional[str] = None


@dataclasses.dataclass
class WritePreview:
    """What a write WOULD do: the rendered text, its destination and whether anything changes."""

    text: str
    destination: Path
    source: Path
    changed: bool
    events: List[Dict[str, Any]]


@dataclasses.dataclass(frozen=True)
class LegacyTarget:
    """A path-keyed write target (2xwb9b OQ-03): the record's file, its type and optional id6.

    An id-less legacy record (14 specs measured, F-03) has no id6 to key a log or a cache row, so
    phase B addresses it by path; `key` is what the per-artifact lock is named after."""

    path: Path
    record_type: str
    id6: Optional[str] = None
    source_digest: Optional[str] = None

    @property
    def key(self) -> str:
        if self.id6:
            return self.id6
        return "path-" + hashlib.sha256(str(self.path).encode("utf-8")).hexdigest()[:12]


#: `status_set` plural record types -> registry types (walkthroughs/roadmaps/other have no registry
#: entry; they are written without field validation, exactly as the setter wrote them before).
_LEGACY_PLURAL_TO_TYPE: Dict[str, str] = {
    "plans": "ipd",
    "specs": "spec",
    "backlog": "backlog",
    "research": "research",
    "releases": "release",
    "prompts": "prompt",
    "walkthroughs": "walkthrough",
}

_TYPE_TO_PLURAL: Dict[str, str] = {v: k for k, v in _LEGACY_PLURAL_TO_TYPE.items()}

#: Registry field -> today's bullet label, for the fields the setter and phase-B writers edit.
_LEGACY_BULLET_LABEL: Dict[str, str] = {
    "approval": "Approval",
    "readiness": "Readiness",
    "review_depth": "Review-Depth",
    "gate_kind": "Gate-Kind",
    "gate_ref": "Gate-Ref",
    "gate_summary": "Gate-Summary",
    "coverage": "Coverage",
    "coverage_fingerprint": "Coverage-Fingerprint",
    "coverage_checked": "Coverage-Checked",
    "attended": "Attended",
    "plan_role": "Kind",
    "set": "Set",
    "order": "Order",
    "version": "Version",
    "short_description": "Short-Description",
    "pipeline": "Pipeline",
    "from_plan": "From-Plan",
    "supersedes": "Supersedes",
    "scope_paths": "Scope-Paths",
    "highest_e_allocated": "Highest E allocated",
    "author": "Author",
    "canonical": "Canonical",
    "summary": "Summary",
    "target_id": "Target-Id",
}

#: Registry field -> YAML front-matter key for `research` records.
_RESEARCH_YAML_KEY: Dict[str, str] = {
    "id": "id",
    "created": "created",
    "status": "status",
    "set": "set",
    "order": "order",
    "research_kind": "kind",
    "outcome": "outcome",
    "summary": "summary",
    "priority": "priority",
    "consumed_by": "consumed-by",
    "topic": "topic",
    "short_description": "short-description",
    "model": "model",
    "ace": "ace",
    "created_day": "created",
}

#: Registry field -> `<!-- aw-prompt: ... -->` comment key for `prompt` records.
_PROMPT_COMMENT_KEY: Dict[str, str] = {
    "prompt_kind": "Kind",
    "id": "Id",
    "set": "Set",
    "status": "Status",
    "created_day": "Created",
    "author": "Author",
    "targets": "Targets",
    "concerns": "Concerns",
    "results_go_to": "Results-go-to",
    "results": "Results",
    "grounding": "Grounding",
    "goal": "Goal",
    "reviews_spec": "Reviews-spec",
    "basis": "Basis",
    "relation": "Relation",
    "short_description": "Short-Description",
}

# A YAML-fenced document's metadata region is its LEADING `---` block, not "everything before the
# first `##`". The distinction is not cosmetic: measured on this corpus, exactly one record
# (`effzzi`, a roadmap) opens with a YAML fence and then carries `- Key: value` BODY PROSE bullets
# under its H1 (`- Plans: one orchestrator plus eight children`, `- Authoring state: ...`) before
# its first `## ` heading. Those bullets are narrative, not metadata, and the fence is the record's
# real declaration site, so the fence is where the region ends.
_YAML_FENCE_OPEN_RE = re.compile(r"\A---[ \t]*\r?\n")

_METADATA_END_RE = re.compile(r"(?m)^#{2,}\s")

_META_BULLET_LINE_RE = re.compile(r"(?m)^-\s*[A-Za-z][A-Za-z0-9 /-]*:[^\n]*(?:\n|$)")


def metadata_region(text: str) -> str:
    """Return the leading METADATA REGION of a record: where it DECLARES its own identity."""

    if not text:
        return text or ""
    m_open = _YAML_FENCE_OPEN_RE.match(text)
    if m_open is not None:
        pos = m_open.end()
        for line in text[pos:].splitlines(keepends=True):
            stripped = line.rstrip("\r\n")
            pos += len(line)
            if stripped.rstrip(" \t") == "---":
                return text[: pos - (len(line) - len(stripped))]
        return text  # fence unterminated within the input -> the region continues
    m_end = _METADATA_END_RE.search(text)
    if m_end is None:
        return text  # no `##` in the input -> the region continues (the common 25-record case)
    return text[: m_end.start()]


def _normalize_legacy_types(
    record_type: Optional[str],
    target_path: Optional[Path] = None,
    records_root: Optional[Path] = None,
) -> Tuple[Optional[str], str]:
    """Map a singular or plural record type (or target path) to `(registry_type, plural_dir)`."""
    if record_type:
        if record_type in _LEGACY_PLURAL_TO_TYPE:
            return _LEGACY_PLURAL_TO_TYPE[record_type], record_type
        if record_type in _TYPE_TO_PLURAL:
            return record_type, _TYPE_TO_PLURAL[record_type]
        return record_type, record_type
    if target_path is not None:
        if records_root is not None:
            with contextlib.suppress(ValueError):
                rel_parts = (
                    target_path.resolve().relative_to(records_root.resolve()).parts
                )
                if rel_parts and rel_parts[0] in _LEGACY_PLURAL_TO_TYPE:
                    plural = rel_parts[0]
                    return _LEGACY_PLURAL_TO_TYPE[plural], plural
        name = target_path.name
        suffix_map = (
            (".ipd.md", "plans"),
            (".spec.md", "specs"),
            (".backlog.md", "backlog"),
            (".release.md", "releases"),
            (".prompt.md", "prompts"),
            (".walkthrough.md", "walkthroughs"),
        )
        for suf, plural in suffix_map:
            if name.endswith(suf):
                return _LEGACY_PLURAL_TO_TYPE[plural], plural
        if "research" in target_path.parts or name.endswith(
            (".research-report.md", ".research-prompt.md", ".findings.md", ".survey.md")
        ):
            return "research", "research"
    return "ipd", "plans"


_GATE_FIELDS: Tuple[str, ...] = ("gate_kind", "gate_ref", "gate_summary")

#: The exact removal patterns today's setter uses (whole-file, as before), so a strip removes the
#: same lines it removed before the move.
_LEGACY_REMOVE_RE: Dict[str, "re.Pattern[str]"] = {
    "gate_kind": re.compile(r"^-\s*Gate-Kind:\s*(\S+)\s*$"),
    "gate_ref": re.compile(r"^-\s*Gate-Ref:\s*(.+?)\s*$"),
    "gate_summary": re.compile(r"^-\s*Gate-Summary:\s*(.+?)\s*$"),
    "approval": re.compile(r"^- Approval:\s*"),
    "readiness": re.compile(r"^- Readiness:\s*"),
    "implemented": re.compile(r"^-\s*Implemented:.*$"),
}


def legacy_context(repo_root: Union[str, Path]) -> Any:
    """The `project_context` a phase-B setter passes for ``repo_root``: the records root every record
    verb reads (`project_context.project_records_dir`) and the repository's own `.aw/state`.

    The full resolver can place a bare repository's records under the AW_HOME companion directory
    while the setter reads `<repo>/.aw/records` (backlog `ggp2pf`), so the setter builds this context
    from the SAME records root it resolved the record from. The cache therefore always describes the
    tree the setter edits."""
    root = Path(repo_root).resolve()
    records = Path(_proj_ctx.project_records_dir(root))
    records_res = records.resolve()
    state: Optional[Path] = None
    with contextlib.suppress(Exception):
        resolved = _proj_ctx.resolve_project_context(target_repo=str(root))
        if Path(resolved.logical_roots["records"]).resolve() == records_res:
            cand_state = Path(resolved.logical_roots["state"])
            cand_state_res = cand_state.resolve()
            # When records live under AW_HOME (`records_backend == "home"`), keep meta
            # locks/cache beside the external home records root instead of creating
            # untracked `.aw/state/` inside the target repo. For companion repos, honor
            # the resolved state root so we never create untracked `state/` inside the
            # companion git repository.
            if not (
                getattr(resolved, "records_backend", None) == "home"
                and not records_res.is_relative_to(root)
                and cand_state_res.is_relative_to(root)
            ):
                state = cand_state
    if state is None:
        if not records_res.is_relative_to(root):
            # External records root whose resolved state would land inside the target repo
            # (e.g. home backend with tracked delivery_mode): keep meta locks/cache beside
            # the external records root rather than creating untracked `.aw/state/` inside
            # a clean target repo.
            state = records_res.parent / "state"
        else:
            state = root / ".aw" / "state"
    return type(
        "LegacyContext",
        (),
        {
            "logical_roots": {"records": str(records), "state": str(state)},
            "repo_root": root,
        },
    )()


def _storage_format(records_root: Path, target: Any) -> str:
    """`log` when the target has `<records_root>/meta/<id6>.jsonl`, else `legacy` (phase B)."""
    id6 = target if isinstance(target, str) else getattr(target, "id6", None)
    if id6 and (Path(records_root) / "meta" / f"{id6}.jsonl").exists():
        return "log"
    return "legacy"


def _bullet_re(label: str) -> "re.Pattern[str]":
    return re.compile(r"^-\s*" + re.escape(label) + r":")


def _check_owned_fields(
    record_type: str, events: List[Dict[str, Any]], from_status: Optional[str]
) -> None:
    """The event-owned field rules of 4.2/4.4 (AC-15, AC-14a (1)-(3)), applied to ONE append before
    any write. These are the rules `replay` enforces for a log, stated over a single append so the
    legacy branch refuses the same appends the log branch would refuse."""
    trans = next((e for e in events if e.get("op") == "transition"), None)
    to_s = trans.get("to") if trans else None
    from_s = trans.get("from") if trans else from_status
    to_approved = to_s == "approved"
    leaving_approved = trans is not None and from_s == "approved" and to_s != "approved"
    # `approval` may only be cleared by an append that leaves the record NOT approved: a transition
    # to another status, or (cleanup of a stale value, 2xwb9b D-05) a write to a record that is not
    # approved. It can never be cleared from a record that stays or ends approved.
    ends_approved = to_approved or (trans is None and from_status == "approved")
    backward = (
        record_type == "ipd"
        and trans is not None
        and (from_s, to_s) in _ipd_life._LEGAL_BACKWARD_EDGES
        and to_s in ("draft", "to-review")
    )
    unset_fields: Set[str] = set()
    for ev in events:
        op = ev.get("op")
        if op == "set":
            for fk in ev.get("fields", {}):
                if fk in ("status", "id", "type"):
                    raise ValueError(
                        f"refuse generic set of identity/status field: {fk!r}"
                    )
                if fk in ("readiness", "review_depth"):
                    raise ValueError(f"refuse set of review-owned field {fk!r}")
                if fk in ("coverage", "coverage_fingerprint"):
                    raise ValueError(f"refuse set of coverage-owned field {fk!r}")
                # A same-status write to a plan that IS approved but lacks the bullet keeps today's
                # backfill (2xwb9b D-06); any other append outside a transition to approved is refused.
                if fk == "approval" and not ends_approved:
                    raise ValueError(
                        "set of approval outside transition to approved append"
                    )
                if (
                    fk in ("scope_result", "out_of_scope_paths", "widened_paths")
                    and to_s != "executed"
                ):
                    raise ValueError(
                        f"set of {fk!r} outside transition to executed append"
                    )
        elif op == "unset":
            for fk in ev.get("fields", []):
                if fk in ("status", "id", "type"):
                    raise ValueError(
                        f"refuse generic unset of identity/status field: {fk!r}"
                    )
                if fk in ("readiness", "review_depth") and not backward:
                    raise ValueError(
                        f"refuse unset of {fk!r} outside backward transition append"
                    )
                if fk == "approval" and ends_approved:
                    raise ValueError(
                        "refuse unset of approval outside transition away from approved"
                    )
                if fk in ("scope_result", "out_of_scope_paths", "widened_paths"):
                    raise ValueError(f"refuse unset of finalize-owned field {fk!r}")
                unset_fields.add(fk)
    if leaving_approved and record_type == "ipd" and "approval" not in unset_fields:
        raise ValueError(
            "approval must be unset in the append containing a transition away from approved"
        )
    if backward and "readiness" not in unset_fields:
        raise ValueError(
            "readiness must be unset in the append of a backward plan transition"
        )


def set_legacy_bullet_line(
    text: str,
    label: str,
    value: Optional[str],
    *,
    anchors: Tuple[Union[str, Tuple[str, str]], ...] = (
        ("Status", "after"),
        ("Id", "after"),
    ),
) -> str:
    """Update, heal duplicates of, or strip ``- <label>:`` inside ``artifact_meta.metadata_region``.

    Preserves the bounded ``releases.set_*_line`` contract (``3466h8`` D-2): ``'-'`` and
    ``None`` strip matching lines in the metadata region with zero residue; existing matches
    replace the first occurrence in place and heal any duplicates to one line; absent bullets
    insert relative to the first matching anchor in ``anchors`` (supporting ``(label, 'before')``
    or ``(label, 'after')``); and anchor-less or YAML-fenced regions return ``text`` unchanged.
    """

    region = metadata_region(text)
    rest = text[len(region) :]
    pat = re.compile(r"(?m)^-\s*" + re.escape(label) + r":[^\n]*\n?")
    if value in (None, "-"):
        return pat.sub("", region) + rest
    new_line = f"- {label}: {value}\n"
    matches = list(pat.finditer(region))
    if matches:
        first = matches[0]
        tail = pat.sub("", region[first.end() :])
        return region[: first.start()] + new_line + tail + rest
    for anchor_spec in anchors:
        if isinstance(anchor_spec, tuple):
            anchor_label, pos = anchor_spec
        else:
            anchor_label, pos = anchor_spec, "after"
        am = re.search(
            r"(?m)^-\s*" + re.escape(anchor_label) + r":[^\n]*(?:\n|$)",
            region,
        )
        if am:
            if pos == "before":
                return region[: am.start()] + new_line + region[am.start() :] + rest
            if am.group(0).endswith("\n"):
                return region[: am.end()] + new_line + region[am.end() :] + rest
            return region[: am.end()] + "\n" + new_line + region[am.end() :] + rest
    return region + rest


# Private copies of the `releases` value writers (metastore 6bxlzb, `k6jd6l` E-08 copy step).
# They keep the exact behavior of the `releases` originals so callers can be retargeted onto
# `artifact_meta` (Orders 281 to 283) before Order 284 (`zs7a45`) deletes the originals.


def _legacy_in_metadata_region(
    text: str,
    label: str,
    value: Optional[str],
    *,
    anchors: Tuple[Tuple[str, str], ...] = (("Status", "after"), ("Id", "after")),
) -> str:
    """Bounded bullet surgery inside ``artifact_meta.metadata_region`` for the value writers below.

    Copy of ``releases._set_bullet_via_meta``, which replaced ``releases._in_metadata_region`` in
    ``3466h8``: bounding edits to the metadata region stops a QUOTED field bullet in a record's body
    from being deleted during stripping or matched as an insertion anchor (b92m14 E-07, 7afjyu).
    For YAML-fenced records the region is the leading fence, and a region with no valid anchor
    yields the documented 'leave unchanged' fallback without searching into the body.
    """
    return set_legacy_bullet_line(text, label, value, anchors=anchors)


def _legacy_set_blocks_release_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Blocks-Release:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged). Tolerates any value so an existing
    malformed line is still replaced. Copy of ``releases.set_blocks_release_line``."""
    return _legacy_in_metadata_region(text, "Blocks-Release", value)


def _legacy_set_priority_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Priority:` metadata line set to `value`, or removed when `value` is
    '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:` (falling back
    to after `- Id:`, or leaving unchanged). The ENUM check (value in backlog.PRIORITIES) is enforced
    by `aw check`, not here; any value is tolerated so an existing malformed line is still replaced.
    Copy of ``releases.set_priority_line``."""
    return _legacy_in_metadata_region(text, "Priority", value)


def _legacy_set_work_kind_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Work-Kind:` metadata line set to `value`, or removed when `value` is
    '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:` (falling back
    to after `- Id:`, or leaving unchanged). Mirrors `_legacy_set_priority_line` exactly, so the two
    optional fields cannot drift on anchor or clearing semantics. The ENUM check (value in
    backlog.KINDS) is enforced by `aw check` / validate_spec, not here. Never touches
    `- Gate-Kind:` or `- Kind:`. Copy of ``releases.set_work_kind_line``."""
    return _legacy_in_metadata_region(text, "Work-Kind", value)


def _legacy_set_from_backlog_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- From-Backlog:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged). Mirrors `_legacy_set_blocks_release_line`
    and `_legacy_set_from_spec_line`; tolerates any value so an existing malformed line is still
    replaced. Copy of ``releases.set_from_backlog_line``."""
    return _legacy_in_metadata_region(text, "From-Backlog", value)


def _legacy_set_from_spec_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- From-Spec:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged). Spec-side sibling of
    `_legacy_set_from_backlog_line`; tolerates any value so an existing malformed or empty-valued
    line is still replaced. Copy of ``releases.set_from_spec_line``."""
    return _legacy_in_metadata_region(text, "From-Spec", value)


def _legacy_set_item_dependencies_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Item-Dependencies:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one.

    ANCHOR: spec 25kzda 2.7 places this field IMMEDIATELY AFTER `- Scope-Paths:` (and before
    `Blocks-Release`/`From-Backlog`), DELIBERATELY unlike the after-`- Status:` siblings, because in
    the real block order (`... Scope-Paths, Status, Set, Order ...`) after Status is the wrong place.
    When `- Scope-Paths:` is absent, insert BEFORE `- Status:`, then after `- Id:`, else leave the
    text unchanged. Copy of ``releases.set_item_dependencies_line``."""
    return _legacy_in_metadata_region(
        text,
        "Item-Dependencies",
        value,
        anchors=(("Scope-Paths", "after"), ("Status", "before"), ("Id", "after")),
    )


def _legacy_set_graduated_to_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Graduated-To:` metadata line set to `value`, or removed when `value`
    is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:` (falling
    back to after `- Id:`, or leaving unchanged). Mirrors `_legacy_set_from_backlog_line` on anchor
    and clearing semantics. The value (a comma-separated setid list) is written VERBATIM; the shape
    check lives in the setter and in `aw check`. Copy of ``releases.set_graduated_to_line``."""
    return _legacy_in_metadata_region(text, "Graduated-To", value)


_LEGACY_RELEASE_EXEMPT_KIND_LINE_RE = re.compile(
    r"(?m)^- Release-Exempt-Kind:[ \t]*[^\n]*$\n?"
)
_LEGACY_RELEASE_EXEMPT_REF_LINE_RE = re.compile(
    r"(?m)^- Release-Exempt-Ref:[ \t]*[^\n]*$\n?"
)
_LEGACY_CLOSE_EVIDENCE_LINE_RE = re.compile(r"(?m)^- Close-Evidence:[ \t]*[^\n]*$\n?")


def _legacy_insert_after_status_or_id(text: str, new_line: str) -> str:
    """Insert ``new_line`` after the first `- Status:` line, else after `- Id:`, else leave unchanged."""
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


def _legacy_set_release_exempt_kind_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Release-Exempt-Kind:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged). Copy of
    ``backlog.set_release_exempt_kind_line``."""
    text = _LEGACY_RELEASE_EXEMPT_KIND_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    return _legacy_insert_after_status_or_id(text, f"- Release-Exempt-Kind: {value}\n")


def _legacy_set_release_exempt_ref_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Release-Exempt-Ref:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged). Copy of
    ``backlog.set_release_exempt_ref_line``."""
    text = _LEGACY_RELEASE_EXEMPT_REF_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    return _legacy_insert_after_status_or_id(text, f"- Release-Exempt-Ref: {value}\n")


def _legacy_set_close_evidence_line(
    text: str,
    value: Optional[str],
    repo_root: Optional[Union[Path, str]] = None,
) -> str:
    """Return `text` with the `- Close-Evidence:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged).

    Normalizes an absolute `value` to a repo-relative POSIX path against `repo_root` (gh409m byzkr7
    E-02); an already-relative value is preserved byte-identical. Copy of
    ``backlog.set_close_evidence_line``."""
    text = _LEGACY_CLOSE_EVIDENCE_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    val_str = str(value).strip()
    if Path(val_str).is_absolute() or val_str.startswith(("/", "\\")):
        if repo_root is None:
            raise ValueError(
                f"cannot normalize absolute evidence citation '{val_str}' without repo_root"
            )
        root_path = Path(repo_root).resolve()
        target_path = Path(val_str).resolve()
        try:
            norm_value = target_path.relative_to(root_path).as_posix()
        except ValueError:
            raise ValueError(
                f"evidence citation '{val_str}' is outside repository root '{repo_root}'"
            )
    else:
        norm_value = val_str
    return _legacy_insert_after_status_or_id(text, f"- Close-Evidence: {norm_value}\n")


def _legacy_research_set_priority_line(text: str, value: Optional[str]) -> str:
    """Return ``text`` with an optional `priority:` frontmatter line set to ``value`` or removed.

    `priority` is OPTIONAL (xprio 6vgd0k), so this INSERTS the line when absent and REMOVES it on
    clear. Operates ONLY inside the FIRST `--- ... ---` block; inserts after the last content line
    (before the closing fence). `value` None/'-' clears. Preserves every other line and the body
    byte-for-byte; a text with no complete leading block is returned unchanged. Copy of
    ``research_cmd._set_priority_line``."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    fm_end = None
    prio_idx = None
    last_content_idx = 0
    for i in range(1, len(lines)):
        stripped = lines[i].strip()
        if stripped == "---":
            fm_end = i
            break
        if stripped.startswith("priority:"):
            prio_idx = i
        if stripped:
            last_content_idx = i
    if fm_end is None:
        return text
    if value in (None, "-"):
        if prio_idx is not None:
            del lines[prio_idx]
        return "".join(lines)
    if prio_idx is not None:
        newline = "\n" if lines[prio_idx].endswith("\n") else ""
        lines[prio_idx] = f"priority: {value}{newline}"
    else:
        lines.insert(last_content_idx + 1, f"priority: {value}\n")
    return "".join(lines)


def _set_bullet(
    text: str, label: str, value: Optional[str], *, anchors: Tuple[str, ...]
) -> str:
    """Replace or remove `- <label>:` inside the metadata region, else insert after an anchor.

    D-2 / a88210: tries ``anchors`` in order, then falls back to the end of an existing metadata
    bullet block before the first ``## ``; writes nothing when the file has no metadata bullet block.
    """

    region = metadata_region(text)
    rest = text[len(region) :]
    pat = re.compile(r"(?m)^-\s*" + re.escape(label) + r":[^\n]*\n?")
    if value is None:
        return pat.sub("", region) + rest
    new_line = f"- {label}: {value}\n"
    m = pat.search(region)
    if m:
        return region[: m.start()] + new_line + region[m.end() :] + rest
    for anchor in anchors:
        am = re.search(r"(?m)^-\s*" + re.escape(anchor) + r":[^\n]*(?:\n|$)", region)
        if am:
            if am.group(0).endswith("\n"):
                return region[: am.end()] + new_line + region[am.end() :] + rest
            return region[: am.end()] + "\n" + new_line + region[am.end() :] + rest
    last_bullet = None
    for bm in _META_BULLET_LINE_RE.finditer(region):
        last_bullet = bm
    if last_bullet is not None:
        if last_bullet.group(0).endswith("\n"):
            return (
                region[: last_bullet.end()]
                + new_line
                + region[last_bullet.end() :]
                + rest
            )
        return (
            region[: last_bullet.end()]
            + "\n"
            + new_line
            + region[last_bullet.end() :]
            + rest
        )
    return region + rest


def _render_status(
    text: str, plural: str, status: str, *, quiet: bool, label: str
) -> Tuple[str, List[str]]:
    """Write the status mirror in today's three forms: prompt comment, `---` YAML, bullet."""
    notes: List[str] = []
    lines = text.splitlines()
    if plural == "prompts":
        if has_prompt_metadata_comment(text):
            return update_prompt_metadata_status(text, status), notes
        notes.append(
            f"aw set: note: prompt {label} has no metadata comment; status lives in directory only\n"
        )
        return text, notes

    status_updated = False
    new_lines: List[str] = []
    in_front = True
    fenced = bool(lines and lines[0].strip() == "---")
    status_bullet = re.compile(r"^-\s*Status:\s*(\S+)\s*$")
    status_pat = r"^status:(?:\s.*|\s*$)" if plural == "research" else r"^status:\s*\S+"
    for line in lines:
        if fenced:
            if in_front and line.strip() == "---" and new_lines:
                in_front = False
            if (
                in_front
                and not status_updated
                and re.match(status_pat, line, re.IGNORECASE)
            ):
                new_lines.append(f"status: {status}")
                status_updated = True
            else:
                new_lines.append(line)
        else:
            if in_front and line.startswith("## "):
                in_front = False
            if in_front and not status_updated and status_bullet.match(line):
                new_lines.append(f"- Status: {status}")
                status_updated = True
            else:
                new_lines.append(line)

    if not status_updated and not fenced and plural == "plans":
        # The annotated legacy status (`- Status: approved (2026-09-25; executing)`, plan `9en4fy`).
        for i, line in enumerate(new_lines):
            if line.startswith("## "):
                break
            m_ann = re.match(r"^-\s*Status:\s*([A-Za-z][A-Za-z-]*)(\W.*)$", line)
            if not m_ann:
                continue
            if _plans.normalize_status(m_ann.group(1)) not in _plans.RECOGNIZED:
                continue
            old_value = line.split(":", 1)[1].strip()
            new_lines[i : i + 1] = [
                f"- Status: {status}",
                f"- Prior-Status: {old_value}",
            ]
            status_updated = True
            break

    if not status_updated and not fenced and plural == "specs":
        # Replace an in-front free-form `- Status: <prose>` bullet in place, or drop a bare
        # `Status:` line before inserting `- Status: <status>`.
        for i, line in enumerate(new_lines):
            if line.startswith("## "):
                break
            if re.match(r"^-\s*Status:\s*(.*)$", line):
                new_lines[i] = f"- Status: {status}"
                status_updated = True
                break
        if not status_updated:
            for i, line in enumerate(new_lines):
                if line.startswith("Status:"):
                    del new_lines[i]
                    break

    if not status_updated:
        res: List[str] = []
        inserted = False
        if fenced:
            if plural == "research":
                fm_end_idx: Optional[int] = None
                kind_idx: Optional[int] = None
                outcome_idx: Optional[int] = None
                in_fm = False
                for i, line in enumerate(new_lines):
                    stripped = line.strip()
                    if i == 0 and stripped == "---":
                        in_fm = True
                        continue
                    if in_fm and stripped == "---":
                        fm_end_idx = i
                        break
                    if in_fm:
                        if stripped.startswith("kind:"):
                            kind_idx = i
                        elif stripped.startswith("outcome:"):
                            outcome_idx = i
                res = list(new_lines)
                if fm_end_idx is not None:
                    if kind_idx is not None:
                        insert_at = kind_idx + 1
                    elif outcome_idx is not None:
                        insert_at = outcome_idx
                    else:
                        insert_at = fm_end_idx
                    res.insert(insert_at, f"status: {status}")
            else:
                for line in new_lines:
                    if not inserted and line.strip() == "---" and res:
                        res.append(f"status: {status}")
                        inserted = True
                    res.append(line)
        else:
            for line in new_lines:
                res.append(line)
                if not inserted and line.startswith(("# ", "- Date:")):
                    res.append(f"- Status: {status}")
                    inserted = True
            if not inserted:
                res.insert(0, f"- Status: {status}")
        new_lines = res
    return "\n".join(new_lines), notes


def _format_legacy_value(field: str, value: Any) -> str:
    """Format a structured or scalar field value for legacy Markdown/YAML/comment rendering."""
    if isinstance(value, (list, tuple)):
        if field == "item_dependencies":
            parts = [
                str(item["raw"])
                if isinstance(item, dict) and "raw" in item
                else str(item)
                for item in value
            ]
            return ", ".join(parts)
        return ", ".join(str(x) for x in value)
    return str(value)


def _format_yaml_value(value: Any, *, key: str = "") -> str:
    """Format a scalar or list value for YAML front matter."""
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(str(x) for x in value) + "]" if value else "[]"
    if key == "order":
        if isinstance(value, int) and not isinstance(value, bool):
            return f"{value:02d}"
        if isinstance(value, str) and value.isdigit() and len(value) < 2:
            return f"{int(value):02d}"
    if value is None:
        return ""
    return str(value)


def _split_yaml_frontmatter_block(text: str) -> Optional[Tuple[str, str]]:
    """Split a leading ``--- ... ---`` YAML block from its post-fence body verbatim."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[: i + 1]), "".join(lines[i + 1 :])
    return None


def _render_yaml_field(text: str, yaml_key: str, value: Optional[Any]) -> str:
    """Replace, insert (before closing `---`), or remove a key in a leading `---` YAML block."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    fm_end: Optional[int] = None
    key_idx: Optional[int] = None
    last_content_idx = 0
    for i in range(1, len(lines)):
        stripped = lines[i].strip()
        if stripped == "---":
            fm_end = i
            break
        if re.match(r"^" + re.escape(yaml_key) + r"\s*:", stripped):
            key_idx = i
        if stripped:
            last_content_idx = i
    if fm_end is None:
        return text
    if value is None:
        if key_idx is not None:
            del lines[key_idx]
        return "".join(lines)
    formatted = _format_yaml_value(value, key=yaml_key)
    if key_idx is not None:
        newline = "\n" if lines[key_idx].endswith("\n") else ""
        lines[key_idx] = f"{yaml_key}: {formatted}{newline}"
    else:
        if last_content_idx < len(lines) and not lines[last_content_idx].endswith("\n"):
            lines[last_content_idx] += "\n"
        lines.insert(last_content_idx + 1, f"{yaml_key}: {formatted}\n")
    return "".join(lines)


def _split_prompt_comment(first_line: str) -> Optional[Tuple[str, str, str, str]]:
    """Return `(prefix, fields_part, trailer_part, suffix)` for an `<!-- aw-prompt: ... -->` line."""
    m = re.match(r"^(<!--\s*aw-prompt:\s*)(.*?)(\s*-->)\s*$", first_line)
    if not m:
        return None
    prefix, inner, suffix = m.group(1), m.group(2), m.group(3)
    trailer_marker = f" . {PROMPT_METADATA_TRAILER}"
    if trailer_marker in inner:
        fields_part, tail = inner.split(trailer_marker, 1)
        return prefix, fields_part, trailer_marker + tail, suffix
    m_tr = re.search(r"(\s*\.\s*This HTML comment is pipeline metadata only.*)$", inner)
    if m_tr:
        return (
            prefix,
            inner[: m_tr.start()],
            m_tr.group(1),
            suffix,
        )
    return prefix, inner, "", suffix


def _render_prompt_field(text: str, key_label: str, value: Optional[Any]) -> str:
    """Edit, insert, or remove one key in a leading `<!-- aw-prompt: ... -->` comment.

    Leaves comment-less legacy prompts unchanged (`inject_prompt_metadata_id6` parity)."""
    lines = text.split("\n")
    if not lines or "<!-- aw-prompt:" not in lines[0]:
        return text
    parsed = _split_prompt_comment(lines[0])
    if parsed is None:
        return text
    prefix, fields_part, trailer_part, suffix = parsed
    raw_segments = [s.strip() for s in fields_part.split("|") if s.strip()]
    key_pat = re.compile(r"^" + re.escape(key_label) + r":\s*(.*)$")
    clean_val = (
        " ".join(_format_legacy_value(key_label, value).split())
        if value is not None
        else None
    )
    new_segments: List[str] = []
    found = False
    for seg in raw_segments:
        km = key_pat.match(seg)
        if km:
            found = True
            if clean_val is not None:
                if km.group(1).strip() == clean_val:
                    new_segments.append(seg)
                else:
                    new_segments.append(f"{key_label}: {clean_val}")
        else:
            new_segments.append(seg)
    if not found and clean_val is not None:
        new_seg = f"{key_label}: {clean_val}"
        if key_label == "Id":
            idx = next(
                (i + 1 for i, s in enumerate(new_segments) if s.startswith("Kind:")),
                len(new_segments),
            )
            new_segments.insert(idx, new_seg)
        elif key_label == "Set":
            idx = next(
                (i + 1 for i, s in enumerate(new_segments) if s.startswith("Id:")),
                None,
            )
            if idx is None:
                idx = next(
                    (
                        i + 1
                        for i, s in enumerate(new_segments)
                        if s.startswith("Kind:")
                    ),
                    len(new_segments),
                )
            new_segments.insert(idx, new_seg)
        else:
            new_segments.append(new_seg)
    if not new_segments:
        return text
    lines[0] = f"{prefix}{' | '.join(new_segments)}{trailer_part}{suffix}"
    return "\n".join(lines)


def _render_create_fields(
    text: str, plural: str, fields: Dict[str, Any], *, repo_root: Optional[Path]
) -> str:
    """Render initial `create` event fields onto `text` in the type's legacy mirror format."""
    if plural == "prompts":
        lines = text.split("\n") if text else []
        if lines and "<!-- aw-prompt:" in lines[0]:
            out = text
            for fk, fv in fields.items():
                if fk == "type":
                    continue
                label = _PROMPT_COMMENT_KEY.get(fk)
                if label is not None and fv is not None:
                    out = _render_prompt_field(out, label, fv)
            return out

        ordered_keys = (
            "prompt_kind",
            "id",
            "set",
            "status",
            "created_day",
            "author",
            "targets",
            "concerns",
            "results_go_to",
            "results",
            "grounding",
            "goal",
            "reviews_spec",
            "basis",
            "relation",
            "short_description",
        )
        segs: List[str] = []
        for fk in ordered_keys:
            if fk == "prompt_kind":
                val = fields.get("prompt_kind")
                if val is None:
                    continue
            else:
                val = fields.get(fk)
            if val is None or val == "":
                continue
            label = _PROMPT_COMMENT_KEY[fk]
            clean_val = " ".join(_format_legacy_value(fk, val).split())
            if clean_val:
                segs.append(f"{label}: {clean_val}")
        comment = f"<!-- aw-prompt: {' | '.join(segs)} . {PROMPT_METADATA_TRAILER} -->"
        comment = " ".join(comment.split())
        if not text:
            return comment
        if text.startswith("\n"):
            return comment + text
        return comment + "\n" + text

    if plural == "research":
        if _split_yaml_frontmatter_block(text) is not None:
            out = text
            for fk, fv in fields.items():
                if fk == "type" or fv is None:
                    continue
                if fk == "short_description" and not str(fv).strip():
                    continue
                yk = _RESEARCH_YAML_KEY.get(fk)
                if yk is not None:
                    out = _render_yaml_field(out, yk, fv)
            return out
        kind_val = fields.get("research_kind")
        created_val = (
            fields.get("created")
            if fields.get("created") is not None
            else fields.get("created_day")
        )
        fm_lines = ["---"]
        if fields.get("id") is not None:
            fm_lines.append(f"id: {fields['id']}")
        if created_val is not None:
            fm_lines.append(f"created: {created_val}")
        if fields.get("set") is not None:
            fm_lines.append(f"set: {fields['set']}")
        if fields.get("order") is not None:
            fm_lines.append(
                f"order: {_format_yaml_value(fields['order'], key='order')}"
            )
        topic_val = fields.get("topic") if fields.get("topic") is not None else []
        fm_lines.append(f"topic: {_format_yaml_value(topic_val, key='topic')}")
        model_val = fields.get("model") if fields.get("model") is not None else ""
        fm_lines.append(f"model: {model_val}")
        if kind_val is not None:
            fm_lines.append(f"kind: {kind_val}")
        status_val = fields.get("status")
        if kind_val == "research-prompt":
            if status_val not in (None, ""):
                fm_lines.append(f"status: {status_val}")
        else:
            fm_lines.append(
                f"status: {status_val if status_val is not None else 'todo'}"
            )
        outcome_val = (
            fields.get("outcome") if fields.get("outcome") is not None else "none-yet"
        )
        fm_lines.append(f"outcome: {outcome_val}")
        summary_val = fields.get("summary") if fields.get("summary") is not None else ""
        fm_lines.append(f"summary: {summary_val}")
        cb_val = (
            fields.get("consumed_by") if fields.get("consumed_by") is not None else []
        )
        fm_lines.append(f"consumed-by: {_format_yaml_value(cb_val, key='consumed-by')}")
        if fields.get("priority"):
            fm_lines.append(f"priority: {fields['priority']}")
        if fields.get("ace") is not None:
            fm_lines.append(
                f"{_RESEARCH_YAML_KEY['ace']}: {_format_yaml_value(fields['ace'])}"
            )
        sd_val = fields.get("short_description")
        if sd_val is not None and str(sd_val).strip():
            fm_lines.append(
                f"{_RESEARCH_YAML_KEY['short_description']}: {_format_yaml_value(sd_val)}"
            )
        fm_lines.append("---")
        fm = "\n".join(fm_lines) + "\n"
        return fm + text

    if plural == "walkthroughs":
        out = text
        region = metadata_region(out)
        id_val = fields.get("id")
        target_id = fields.get("target_id")
        has_id = bool(re.search(r"(?m)^-\s*Id:", region))
        has_target = bool(re.search(r"(?m)^-\s*Target-Id:", region))
        if has_id and id_val is not None:
            out = _set_bullet(out, "Id", str(id_val), anchors=("Set",))
        if has_target and target_id is not None:
            out = _set_bullet(out, "Target-Id", str(target_id), anchors=("Id", "Set"))
        missing_lines: List[str] = []
        if id_val is not None and not has_id:
            missing_lines.append(f"- Id: {id_val}")
        if target_id is not None and not has_target:
            missing_lines.append(f"- Target-Id: {target_id}")
        if not missing_lines:
            return out
        meta = "\n".join(missing_lines)
        region = metadata_region(out)
        set_m = re.search(r"(?m)^(-[ \t]*Set:[ \t]*[^\n]*)$", region)
        if set_m:
            idx = set_m.end(1)
            return out[:idx] + "\n" + meta + out[idx:]
        head_m = re.search(r"(?m)^(# [^\n]*)", region)
        if head_m:
            idx = head_m.end(1)
            after_head = out[idx:].lstrip("\n")
            if not after_head:
                return out[:idx] + "\n\n" + meta
            sep = "\n" if after_head.startswith("- ") else "\n\n"
            return out[:idx] + "\n\n" + meta + sep + after_head
        stripped = out.lstrip("\n")
        if not stripped:
            return meta
        sep = "\n" if stripped.startswith("- ") else "\n\n"
        return meta + sep + stripped

    region = metadata_region(text)
    if _META_BULLET_LINE_RE.search(region):
        out = text
        if "status" in fields and fields["status"] is not None:
            out, _ = _render_status(
                out, plural, str(fields["status"]), quiet=True, label=""
            )
        if "id" in fields and fields["id"] is not None:
            out = _set_bullet(out, "Id", str(fields["id"]), anchors=("Status",))
        for fk, fv in fields.items():
            if fk in ("id", "type", "status") or fv is None:
                continue
            out = _render_field(out, plural, fk, fv, repo_root=repo_root)
        return out

    ordered_bullets = (
        "id",
        "status",
        "plan_role",
        "version",
        "set",
        "order",
        "work_kind",
        "priority",
        "summary",
        "short_description",
        "pipeline",
        "from_backlog",
        "from_spec",
        "from_plan",
        "supersedes",
        "blocks_release",
        "scope_paths",
        "item_dependencies",
        "highest_e_allocated",
        "graduated_to",
        "gate_kind",
        "gate_ref",
        "gate_summary",
        "release_exempt_kind",
        "release_exempt_ref",
        "attended",
        "close_evidence",
    )
    label_map = {
        **_LEGACY_BULLET_LABEL,
        "id": "Id",
        "status": "Status",
        "work_kind": "Work-Kind",
        "priority": "Priority",
        "from_backlog": "From-Backlog",
        "from_spec": "From-Spec",
        "blocks_release": "Blocks-Release",
        "item_dependencies": "Item-Dependencies",
        "graduated_to": "Graduated-To",
        "release_exempt_kind": "Release-Exempt-Kind",
        "release_exempt_ref": "Release-Exempt-Ref",
        "close_evidence": "Close-Evidence",
    }
    bullet_lines: List[str] = []
    seen_keys: Set[str] = set()
    for fk in list(ordered_bullets) + list(fields.keys()):
        if fk in seen_keys or fk == "type":
            continue
        seen_keys.add(fk)
        fv = fields.get(fk)
        if fv is None:
            continue
        lbl = label_map.get(fk)
        if lbl is not None:
            bullet_lines.append(f"- {lbl}: {_format_legacy_value(fk, fv)}")
    if not bullet_lines:
        return text
    block = "\n".join(bullet_lines)
    if not text:
        return block
    lines = text.split("\n")
    if lines[0].startswith("# "):
        rest_lines = lines[1:]
        while rest_lines and rest_lines[0] == "":
            rest_lines.pop(0)
        head = lines[0] + "\n\n" + block
        if rest_lines:
            return head + "\n\n" + "\n".join(rest_lines)
        return head
    return block + "\n\n" + text.lstrip("\n")


def _render_field(
    text: str,
    plural: str,
    field: str,
    value: Optional[Any],
    *,
    repo_root: Optional[Path],
) -> str:
    """One field edit across bullet, research `---` YAML, or `aw-prompt` comment forms."""
    if plural == "prompts":
        if has_prompt_metadata_comment(text):
            key_label = _PROMPT_COMMENT_KEY.get(field)
            if key_label is None:
                if field == "order":
                    return text
                raise ValueError(
                    f"legacy writer has no prompt comment key for field {field!r}"
                )
            return _render_prompt_field(text, key_label, value)

        region = metadata_region(text)
        if _META_BULLET_LINE_RE.search(region):
            label = _LEGACY_BULLET_LABEL.get(field)
            if label is None:
                raise ValueError(
                    f"legacy writer has no bullet form for field {field!r}"
                )
            if value is None:
                return _set_bullet(text, label, None, anchors=("Status", "Id"))
            anchors = ("Set", "Status", "Id") if field == "order" else ("Status", "Id")
            return _set_bullet(
                text, label, _format_legacy_value(field, value), anchors=anchors
            )
        return text

    if field in _RESEARCH_YAML_KEY and _YAML_FENCE_OPEN_RE.match(text):
        if value is None:
            val: Any = [] if field in ("consumed_by", "topic") else None
        elif field == "priority" and value == "-":
            val = None
        else:
            val = value
        if (
            plural == "research"
            and field == "order"
            and isinstance(val, int)
            and not isinstance(val, bool)
        ):
            val = f"{val:02d}"
        return _render_yaml_field(text, _RESEARCH_YAML_KEY[field], val)

    bullet_writers: Dict[str, Callable[[str, Optional[str]], str]] = {
        "blocks_release": _legacy_set_blocks_release_line,
        "priority": _legacy_set_priority_line,
        "work_kind": _legacy_set_work_kind_line,
        "from_backlog": _legacy_set_from_backlog_line,
        "from_spec": _legacy_set_from_spec_line,
        "item_dependencies": _legacy_set_item_dependencies_line,
        "graduated_to": _legacy_set_graduated_to_line,
    }
    if field in bullet_writers:
        formatted = _format_legacy_value(field, value) if value is not None else "-"
        return bullet_writers[field](text, formatted)

    writers = {
        "release_exempt_kind": (
            "Release-Exempt-Kind",
            _legacy_set_release_exempt_kind_line,
        ),
        "release_exempt_ref": (
            "Release-Exempt-Ref",
            _legacy_set_release_exempt_ref_line,
        ),
    }
    if field in writers:
        wlabel, wfn = writers[field]
        formatted = _format_legacy_value(field, value) if value is not None else "-"
        if value is not None and formatted != "-":
            region = metadata_region(text)
            matches = re.findall(r"(?m)^-\s*" + re.escape(wlabel) + r":", region)
            if len(matches) == 1:
                return _set_bullet(text, wlabel, formatted, anchors=("Status", "Id"))
        return wfn(text, formatted)
    if field == "close_evidence":
        formatted = _format_legacy_value(field, value) if value is not None else "-"
        return _legacy_set_close_evidence_line(text, formatted, repo_root=repo_root)
    if value is None and field in _LEGACY_REMOVE_RE:
        pat = _LEGACY_REMOVE_RE[field]
        return "\n".join(ln for ln in text.split("\n") if not pat.match(ln))
    label = _LEGACY_BULLET_LABEL.get(field)
    if label is None:
        raise ValueError(f"legacy writer has no bullet form for field {field!r}")
    if value is None:
        return _set_bullet(text, label, None, anchors=("Status", "Id"))
    anchors = {
        "review_depth": ("Readiness", "Status", "Id"),
        "coverage": ("Readiness", "Status", "Id"),
        "order": ("Set", "Status", "Id"),
        "author": ("Id", "Status"),
        "gate_ref": ("Gate-Kind", "Status", "Id"),
        "gate_summary": ("Gate-Ref", "Gate-Kind", "Status", "Id"),
    }.get(field, ("Status", "Id"))
    return _set_bullet(text, label, _format_legacy_value(field, value), anchors=anchors)


def _render_checkpoint(text: str, plural: str, fields: Dict[str, Any]) -> str:
    """Render an idempotent `checkpoint` `"id"` (and prompt `"set"`) into legacy metadata.

    On `prompts`, delegates to `inject_prompt_metadata_id6` (leaving comment-less prompts
    untouched). On non-prompts, inserts `- Id:` after `- Status:` else `- Date:` inside the
    metadata region with zero H1/body fallback (`a88210`).
    """
    id_val = fields.get("id")
    set_val = fields.get("set")
    if plural == "prompts":
        if id_val is not None:
            return inject_prompt_metadata_id6(
                text,
                id6=str(id_val),
                set_id=str(set_val) if set_val is not None else None,
            )
        return text
    if id_val is None:
        return text

    region = metadata_region(text)
    if re.search(r"(?m)^-\s*Id:\s*\S+", region):
        return text
    region_lines = region.split("\n")
    rest = text[len(region) :]
    insert_at: Optional[int] = None
    for i, line in enumerate(region_lines):
        if re.match(r"^-\s*Status:\s*.+?\s*$", line):
            insert_at = i + 1
            break
    if insert_at is None:
        for i, line in enumerate(region_lines):
            if re.match(r"^-\s*Date:\s*.+?\s*$", line):
                insert_at = i + 1
                break
    if insert_at is None:
        return text
    region_lines.insert(insert_at, f"- Id: {id_val}")
    return "\n".join(region_lines) + rest


def _render_gate(text: str, fields: Dict[str, Any]) -> str:
    """Gate bullets are written as a block directly after `- Status:` (Kind, Ref, Summary)."""
    lines = [
        ln
        for ln in text.split("\n")
        if not any(_LEGACY_REMOVE_RE[g].match(ln) for g in _GATE_FIELDS)
    ]
    st_idx = -1
    for i, ln in enumerate(lines):
        if re.match(r"^-\s*Status:\s*(\S+)\s*$", ln):
            st_idx = i
            break
    pos = st_idx + 1 if st_idx >= 0 else 1
    block = [
        f"- {_LEGACY_BULLET_LABEL[g]}: {fields[g]}"
        for g in _GATE_FIELDS
        if fields.get(g)
    ]
    for gl in reversed(block):
        lines.insert(pos, gl)
    return "\n".join(lines)


def _render_approval(text: str, value: str) -> str:
    """`- Approval:` directly after `- Id:`, else after `- Status:`, else before the first `## `."""
    lines = text.split("\n")
    if any(re.match(r"^- Approval:\s*", ln) for ln in lines):
        return text
    line = f"- Approval: {value}"
    idx: Optional[int] = None
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            break
        if re.match(r"^- Id:\s*", ln):
            idx = i + 1
    if idx is None:
        for i, ln in enumerate(lines):
            if ln.startswith("## "):
                break
            if re.match(r"^-\s*Status:\s*(\S+)\s*$", ln):
                idx = i + 1
    if idx is None:
        idx = next(
            (i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines)
        )
    lines.insert(idx, line)
    return "\n".join(lines)


def _render_history(
    text: str, entry: str, *, is_prompt: bool, history_at_end: bool = False
) -> str:
    """Prepend a newest-first record under `## Workflow history`, creating the heading if absent.

    D-1: preserves an existing single blank line directly under `## Workflow history` when present
    (inserting after it), and inserts directly under the heading otherwise."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"^##\s*Workflow history\s*$", ln):
            insert_at = i + 2 if (i + 1 < len(lines) and lines[i + 1] == "") else i + 1
            lines.insert(insert_at, entry)
            return "\n".join(lines)
    if history_at_end:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(["## Workflow history", entry])
        return "\n".join(lines)
    idx = len(lines)
    if not is_prompt:
        idx = next(
            (i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines)
        )
    lines[idx:idx] = ["## Workflow history", entry, ""]
    return "\n".join(lines)


def _format_scope_exceeded_value(
    reasons_or_items: Union[Mapping[str, str], Sequence[Any]],
) -> str:
    """Format the - Scope-Exceeded: field value from out-of-scope paths and reasons."""
    pairs: List[Tuple[str, str]] = []
    if isinstance(reasons_or_items, Mapping):
        for p in sorted(reasons_or_items.keys()):
            pairs.append((str(p), str(reasons_or_items[p] or "")))
    else:
        for item in reasons_or_items:
            if isinstance(item, Mapping):
                p = str(item.get("path") or "")
                r = str(item.get("reason") or "")
            else:
                p = str(item)
                r = ""
            pairs.append((p, r))
        pairs.sort(key=lambda pr: pr[0])
    entries: List[str] = []
    for p, raw in pairs:
        clean = (
            re.sub(r"[\r\n]+", " ", raw)
            .replace(";", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
        )
        if len(clean) > 200:
            clean = clean[:200] + "..."
        entries.append(f"{p} ({clean})")
    return "; ".join(entries)


def render_legacy(
    text: str,
    plural: str,
    events: List[Dict[str, Any]],
    render: LegacyRender,
    *,
    label: str = "",
    repo_root: Optional[Path] = None,
    quiet: bool = True,
    _trailing_body_only: bool = False,
) -> Tuple[str, List[str]]:
    """Render ONE append's events into a record's legacy Markdown text. Pure.

    Event order is the append's order; the history line is written last. Returns the rendered text
    (ending in exactly one newline) and the notes the setter prints."""

    notes: List[str] = []
    is_research_create = (
        plural == "research"
        and not render.history
        and any(e.get("op") == "create" for e in events)
    )
    research_yaml_split = (
        _split_yaml_frontmatter_block(text)
        if (plural == "research" and not render.history and not is_research_create)
        else None
    )
    if is_research_create:
        out = text
        post_fence_body = ""
    elif research_yaml_split is not None:
        out, post_fence_body = research_yaml_split
    else:
        # Today's setter worked on `text.splitlines()` and re-split after every value writer, so the
        # renderer normalizes the same way (no trailing empty line, CRLF folded) between edits.
        out = "\n".join(text.splitlines())
        post_fence_body = ""
    is_backlog_create = plural == "backlog" and any(
        e.get("op") == "create" for e in events
    )
    trailing_body = ""
    is_headerless_backlog = False
    if is_backlog_create and (
        _trailing_body_only
        or (
            not render.history_at_end
            and not _META_BULLET_LINE_RE.search(metadata_region(out))
        )
    ):
        is_headerless_backlog = True
        pointer = _core.writing_standard_pointer("backlog item")
        hist_m = re.search(r"(?m)^##\s*Workflow history\s*$", out)
        if hist_m:
            pre_part = out[: hist_m.start()].strip()
            trailing_body = out[hist_m.end() :].lstrip("\r\n").rstrip()
            out = pre_part if pre_part else pointer
        elif pointer in out:
            before_ptr, after_ptr = out.split(pointer, 1)
            out = (before_ptr.strip() + "\n\n" + pointer).strip()
            trailing_body = after_ptr.lstrip("\r\n").rstrip()
        else:
            trailing_body = out.lstrip("\r\n").rstrip()
            out = pointer
    elif plural == "backlog":
        out = _canonicalize_work_kind(out)

    trans = next((e for e in events if e.get("op") == "transition"), None)
    mirror = render.status or (trans.get("to") if trans else None)
    if mirror and not is_headerless_backlog and not is_research_create:
        if research_yaml_split is not None:
            fm_had_nl = out.endswith("\n")
            out, n = _render_status(out, plural, mirror, quiet=quiet, label=label)
            if fm_had_nl and not out.endswith("\n"):
                out += "\n"
        else:
            out, n = _render_status(out, plural, mirror, quiet=quiet, label=label)
        notes.extend(n)
    legacy_history_lines: List[str] = []
    for ev in events:
        op = ev["op"]
        if op == "create":
            fields = dict(ev.get("fields") or {})
            if is_headerless_backlog:
                if mirror and "status" not in fields:
                    fields["status"] = mirror
                bullet_block = _render_create_fields(
                    "", plural, fields, repo_root=repo_root
                )
                if bullet_block:
                    out = f"{bullet_block}\n\n{out}" if out else bullet_block
            else:
                out = _render_create_fields(out, plural, fields, repo_root=repo_root)
        elif op == "transition":
            pass
        elif op == "set":
            fields = dict(ev["fields"])
            gate = {g: fields.pop(g) for g in _GATE_FIELDS if g in fields}
            if gate:
                out = _render_gate(out, gate)
            if "approval" in fields:
                out = _render_approval(out, fields.pop("approval"))
            fields.pop("scope_result", None)
            fields.pop("widened_paths", None)
            if "out_of_scope_paths" in fields:
                oos_val = fields.pop("out_of_scope_paths")
                if oos_val:
                    formatted_oos = _format_scope_exceeded_value(oos_val)
                    if formatted_oos:
                        out = "\n".join(
                            _set_bullet(
                                out,
                                "Scope-Exceeded",
                                formatted_oos,
                                anchors=("Scope-Paths", "Status", "Id"),
                            ).splitlines()
                        )
            for fk, fv in fields.items():
                rendered_field = _render_field(out, plural, fk, fv, repo_root=repo_root)
                out = (
                    rendered_field
                    if research_yaml_split is not None
                    else "\n".join(rendered_field.splitlines())
                )
        elif op == "unset":
            for fk in ev["fields"]:
                rendered_field = _render_field(
                    out, plural, fk, None, repo_root=repo_root
                )
                out = (
                    rendered_field
                    if research_yaml_split is not None
                    else "\n".join(rendered_field.splitlines())
                )
        elif op == "review":
            if ev.get("review_kind") == "gate":
                for fk in ("readiness", "review_depth"):
                    if ev.get(fk):
                        out = _render_field(
                            out, plural, fk, ev[fk], repo_root=repo_root
                        )
        elif op == "coverage":
            out = _render_field(
                out, plural, "coverage", ev["coverage"], repo_root=repo_root
            )
            out = _set_bullet(
                out,
                "Coverage-Fingerprint",
                ev["coverage_fingerprint"],
                anchors=("Coverage",),
            )
            checked_by_label = (
                render.checked_by
                or (ev.get("actor") or {}).get("model")
                or render.actor_label
            )
            out = _set_bullet(
                out,
                "Coverage-Checked",
                f"{render.day} by {checked_by_label}",
                anchors=("Coverage-Fingerprint",),
            )
        elif op == "note":
            pass
        elif op == "checkpoint":
            out = _render_checkpoint(out, plural, dict(ev.get("fields") or {}))
        elif op == "legacy":
            if ev.get("source") == "history":
                ln = ev.get("line")
                if isinstance(ln, str) and ln.strip():
                    legacy_history_lines.append(ln.rstrip("\n"))
        else:
            raise ValueError(f"legacy writer cannot render op {op!r}")
    if plural == "backlog":
        out = _canonicalize_work_kind(out)
    hist_at_end = render.history_at_end or is_headerless_backlog
    for hline in reversed(legacy_history_lines):
        out = _render_history(
            out, hline, is_prompt=render.is_prompt, history_at_end=hist_at_end
        )
    if render.history:
        has_non_legacy_hist_event = any(
            ev.get("op") in ("note", "transition", "review", "coverage", "create")
            for ev in events
        )
        msg = (
            next(
                (
                    e.get("message")
                    for e in events
                    if e.get("op") != "legacy" and e.get("message")
                ),
                "",
            )
            or ""
        )
        if has_non_legacy_hist_event or msg or not legacy_history_lines:
            entry = f"- {render.day} {render.tag} ({render.actor_label}): {msg}"
            out = _render_history(
                out, entry, is_prompt=render.is_prompt, history_at_end=hist_at_end
            )
    if is_research_create:
        return out, notes
    if research_yaml_split is not None:
        return out + post_fence_body, notes
    if trailing_body:
        out = out.rstrip() + "\n\n" + trailing_body
    return out.rstrip() + "\n", notes


def _canonicalize_work_kind(text: str) -> str:
    """Backlog `- Kind:` becomes `- Work-Kind:`; a second spelling is dropped (only canonical written)."""
    lines = text.split("\n")
    has_wk = any(re.match(r"^- Work-Kind:\s*", ln) for ln in lines)
    out: List[str] = []
    for ln in lines:
        m = re.match(r"^- Kind:\s*(.*)", ln)
        if m:
            if not has_wk:
                out.append(f"- Work-Kind: {m.group(1).strip()}")
                has_wk = True
        else:
            out.append(ln)
    return "\n".join(out)


def _prepare_legacy_events(
    record_type: Optional[str],
    events: List[Dict[str, Any]],
    *,
    records_root: Path,
    repo_root: Optional[Path] = None,
    actor: Optional[Dict[str, Any]],
    by_human: bool,
    overrides: Optional[List[str]],
    migration_import: bool = False,
) -> List[Dict[str, Any]]:
    """Give the events a v1 envelope and run the SAME writer-side refusals as the log branch."""
    now_utc = datetime.datetime.now(timezone.utc).isoformat()
    prepared: List[Dict[str, Any]] = []
    for i, ev in enumerate(events):
        e = dict(ev)
        e.update(
            {
                "v": 1,
                "seq": 1 + i,
                "append": 1,
                "at": now_utc,
                "actor": actor or {"tool": "artifact_meta"},
            }
        )
        if by_human:
            e["by_human"] = True
        if overrides:
            e["overrides"] = list(overrides)
        if e.get("message") == "":
            e.pop("message")
        prepared.append(e)
    # Field names: the type's registry, plus the setter vocabulary today's bullet/YAML/comment
    # formats accept (2xwb9b D-04, 7yr827 E-01). Unknown names are refused.
    legacy_vocab = (
        set(_LEGACY_BULLET_LABEL)
        | set(_RESEARCH_YAML_KEY)
        | set(_PROMPT_COMMENT_KEY)
        | {
            "id",
            "blocks_release",
            "priority",
            "work_kind",
            "from_backlog",
            "from_spec",
            "item_dependencies",
            "graduated_to",
            "release_exempt_kind",
            "release_exempt_ref",
            "close_evidence",
            "implemented",
        }
    )
    reg = REGISTRY.get(record_type or "", {})
    for e in prepared:
        op = e.get("op")
        f = e.get("fields")
        names = f if isinstance(f, list) else list(f or {})
        for fk in names:
            if op in ("create", "checkpoint") and fk in ("id", "type", "status"):
                continue
            if fk not in reg and fk not in legacy_vocab:
                raise ValueError(f"unknown field '{fk}' for type '{record_type}'")
    validate_new_events(
        "",
        prepared,
        records_root=records_root,
        repo_root=repo_root,
        migration_import=migration_import,
    )
    return prepared


def validate_actor_string(
    field_name: str,
    value: str,
    *,
    repo_root: Path,
    ruleset: Optional["_leak.Ruleset"] = None,
) -> "_leak.Ruleset":
    """Validate a raw actor or display attribution string against safety, path, and leak rules."""
    _check_string_safety(field_name, value, prose=False, migration_import=False)
    _check_no_absolute_paths_in_text(field_name, value)
    resolved_ruleset = ruleset if ruleset is not None else _writer_ruleset(repo_root)
    _check_leak_sanitizer(value, field_name, resolved_ruleset)
    return resolved_ruleset


def _validate_legacy_render(render: LegacyRender, *, repo_root: Path) -> None:
    """Validate LegacyRender actor attribution fields before rendering or writing."""
    ruleset: Optional["_leak.Ruleset"] = None

    if render.history or render.actor_label:
        if not isinstance(render.actor_label, str):
            raise ValueError("LegacyRender.actor_label must be a string")
        ruleset = validate_actor_string(
            "LegacyRender.actor_label",
            render.actor_label,
            repo_root=repo_root,
            ruleset=ruleset,
        )

    checked_by = getattr(render, "checked_by", None)
    if checked_by:
        if not isinstance(checked_by, str):
            raise ValueError("LegacyRender.checked_by must be a string")
        validate_actor_string(
            "LegacyRender.checked_by",
            checked_by,
            repo_root=repo_root,
            ruleset=ruleset,
        )


def render_legacy_text(
    text: str,
    events: List[Dict[str, Any]],
    *,
    record_type: str = "ipd",
    render: LegacyRender,
    repo_root: Optional[Union[str, Path]] = None,
    from_status: Optional[str] = None,
    actor: Optional[Dict[str, Any]] = None,
    by_human: bool = False,
    overrides: Optional[List[str]] = None,
    migration_import: bool = False,
    quiet: bool = True,
    label: str = "",
) -> str:
    """Validate and render ``events`` over an in-memory legacy string without file I/O.

    Runs ``validate_new_events`` and ``_check_owned_fields`` before rendering through the same
    ``render_legacy`` primitives used by :func:`write_legacy`."""
    reg_type, plural = _normalize_legacy_types(record_type)
    rroot = Path(repo_root) if repo_root is not None else Path.cwd()
    records_root = Path(_proj_ctx.project_records_dir(rroot))
    _validate_legacy_render(render, repo_root=rroot)
    prepared = _prepare_legacy_events(
        reg_type,
        events,
        records_root=records_root,
        repo_root=rroot,
        actor=actor,
        by_human=by_human,
        overrides=overrides,
        migration_import=migration_import,
    )
    _check_owned_fields(reg_type or plural, prepared, from_status)
    rendered, _notes = render_legacy(
        text,
        plural,
        prepared,
        render,
        label=label,
        repo_root=rroot,
        quiet=quiet,
    )
    return rendered


def restore_legacy_snapshot(
    current_text: str,
    pre_pass_text: str,
    *,
    record_type: str = "ipd",
    drop_history_predicate: Optional[Callable[[str], bool]] = None,
) -> str:
    """Restore pre-pass `- Status:`, `- Readiness:`, and review history lines in memory (D-5).

    Uses `_render_status`, `_set_bullet`, and the history-block primitives rather than
    `validate_new_events` and emits no `set readiness` event."""
    _, plural = _normalize_legacy_types(record_type)
    try:
        from agent_workflows import ipd_lint as _lint

        doc_pre = _lint.parse(pre_pass_text or "")
        st_pre = doc_pre.meta_fields.get("Status") or "to-review"
    except Exception:
        bullets_pre, _, _ = _parse_bullet_metadata(pre_pass_text or "")
        st_pre = bullets_pre.get("Status") or "to-review"

    rd_pre = _ipd_schema.read_readiness(pre_pass_text)
    pre_history = set(_history_block(pre_pass_text or "").records)

    out = "\n".join((current_text or "").splitlines())

    if re.search(r"(?m)^-\s*Status\s*:", metadata_region(out)):
        out, _ = _render_status(out, plural, st_pre, quiet=True, label="")
    if plural == "plans":
        if rd_pre is not None:
            out = _set_bullet(out, "Readiness", rd_pre, anchors=("Status", "Id"))
        else:
            out = _set_bullet(out, "Readiness", None, anchors=("Status", "Id"))

    if drop_history_predicate is None:

        def _default_drop(stripped: str) -> bool:
            return (
                _plan_read.is_review_history_entry(stripped)
                or "reviewed" in stripped.lower()
                or "(aw set): status set to reviewed" in stripped
            )

        pred = _default_drop
    else:
        pred = drop_history_predicate

    lines = out.split("\n")
    in_history = False
    out_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_history = stripped.startswith("## Workflow history")
        elif in_history and stripped.startswith("- "):
            if stripped not in pre_history and pred(stripped):
                continue
        out_lines.append(line)

    result = "\n".join(out_lines)
    if (current_text or "").endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _git_target_root(path: Path, repo_root: Path) -> Path:
    """The git root a move is staged in: the companion records repository when it owns the record."""
    owner = _proj_ctx.record_owner_root(path)
    if owner is not None:
        with contextlib.suppress(Exception):
            c = _proj_ctx.resolve_project_context(target_repo=str(owner))
            if c.records_backend == _proj_ctx.RecordsBackend.COMPANION.value:
                gr = _proj_ctx.record_git_root(path)
                if gr is not None:
                    return gr
    return repo_root


def write_legacy(
    target: Union[Path, str, LegacyTarget],
    events: List[Dict[str, Any]],
    *,
    record_type: Optional[str] = None,
    render: LegacyRender,
    repo_root: Optional[Union[str, Path]] = None,
    project_context: Any = None,
    destination: Optional[Path] = None,
    dry_run: bool = False,
    overwrite: Optional[bool] = None,
    actor: Optional[Dict[str, Any]] = None,
    by_human: bool = False,
    overrides: Optional[List[str]] = None,
    migration_import: bool = False,
    sidecar: Optional[SidecarRecord] = None,
    quiet: bool = True,
    from_status: Optional[str] = None,
    notes_out: Optional[List[str]] = None,
    initial_text: Optional[str] = None,
    _trailing_body_only: bool = False,
) -> WritePreview:
    """The single phase-B legacy writer: validate, render, lock, move, atomic-write, sidecar.

    Accepts a :class:`Path` (or ``str``) or a :class:`LegacyTarget`. Write order matches
    ``2xwb9b`` F-07: disposition ``git mv`` first, then ``artifact_core.atomic_write``, then
    belt-and-braces source unlink, then optional specs/backlog sidecar record. Writes nothing on
    refusal or ``dry_run=True``."""
    if isinstance(target, LegacyTarget):
        ltarget = target
        r_type = record_type or ltarget.record_type
    else:
        tpath = Path(target)
        r_type = record_type
        ltarget = LegacyTarget(tpath, r_type or "plans")

    if repo_root is not None:
        rroot = Path(repo_root)
    elif project_context is not None and getattr(project_context, "repo_root", None):
        rroot = Path(project_context.repo_root)
    elif project_context is not None and getattr(project_context, "target_repo", None):
        rroot = Path(project_context.target_repo)
    else:
        rroot = _proj_ctx.record_git_root(ltarget.path) or _core.repo_root_of(
            ltarget.path
        )

    ctx = project_context or legacy_context(rroot)
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    reg_type, plural = _normalize_legacy_types(r_type, ltarget.path, records_root)

    _validate_legacy_render(render, repo_root=rroot)
    prepared = _prepare_legacy_events(
        reg_type,
        events,
        records_root=records_root,
        repo_root=rroot,
        actor=actor,
        by_human=by_human,
        overrides=overrides,
        migration_import=migration_import,
    )
    _check_owned_fields(reg_type or plural, prepared, from_status)

    src = Path(ltarget.path)
    if ltarget.source_digest is not None:
        if src.is_file():
            if _compute_digest(src) != ltarget.source_digest:
                raise ValueError(
                    f"refused: {src} changed since it was read (source digest differs); re-read and retry"
                )
        elif ltarget.source_digest != "":
            raise ValueError(
                f"refused: {src} does not exist (source digest mismatch); re-read and retry"
            )
    is_create = any(e.get("op") == "create" for e in prepared)
    if overwrite is False and is_create and src.is_file():
        raise FileExistsError(f"refusing to overwrite existing path: {src}")
    disk_text: Optional[str] = None
    if src.is_file():
        disk_text = src.read_text(encoding="utf-8")
    if initial_text is not None and (overwrite is True or disk_text is None):
        text = initial_text
    elif disk_text is not None:
        text = disk_text
    elif initial_text is not None:
        text = initial_text
    else:
        text = ""
    rendered, notes = render_legacy(
        text,
        plural,
        prepared,
        render,
        label=ltarget.id6 or src.name,
        repo_root=rroot,
        quiet=quiet,
        _trailing_body_only=_trailing_body_only,
    )
    if notes_out is not None:
        notes_out.extend(notes)
    dest = Path(destination) if destination is not None else src
    moving = dest.resolve() != src.resolve()
    baseline_text = disk_text if disk_text is not None else text
    preview = WritePreview(
        text=rendered,
        destination=dest,
        source=src,
        changed=moving or (disk_text is None) or rendered != baseline_text,
        events=prepared,
    )
    if dry_run:
        return preview

    lock_path = state_root / "locks" / f"meta-{ltarget.key}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _lock.held(lock_path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if moving and src.exists():
            git_root = _git_target_root(src, rroot)
            try:
                rel_src = str(src.relative_to(git_root))
                rel_dst = str(dest.relative_to(git_root))
            except ValueError:
                rel_src, rel_dst = str(src), str(dest)
            _core.git_mv(git_root, rel_src, rel_dst)
        if preview.changed:
            _core.atomic_write(dest, rendered)
        if moving and src.exists():
            with contextlib.suppress(OSError):
                src.unlink()
        if sidecar is not None:
            sid = ltarget.id6
            if not sid:
                sid = read_loose_id(rendered)
            if sid:
                from agent_workflows import record_history as _rh

                _rh.append_advisory(
                    rroot,
                    id6=sid,
                    tree=sidecar.tree,
                    workflow=sidecar.workflow,
                    actor=sidecar.actor,
                    message=sidecar.message,
                    date=sidecar.date,
                    artifact=dest.name,
                )
        # No cache refresh here: the two-check freshness rule (4.3) reloads the changed files on the
        # next read, and a refresh on every write would cost a whole cold build (measured about 14 s
        # on this repository) in a fresh checkout or lane, where most setter calls run.
    return preview


def append_legacy(
    target: LegacyTarget,
    events: List[Dict[str, Any]],
    *,
    render: LegacyRender,
    repo_root: Path,
    project_context: Any = None,
    destination: Optional[Path] = None,
    dry_run: bool = False,
    actor: Optional[Dict[str, Any]] = None,
    by_human: bool = False,
    overrides: Optional[List[str]] = None,
    migration_import: bool = False,
    sidecar: Optional[SidecarRecord] = None,
    quiet: bool = True,
    from_status: Optional[str] = None,
    notes_out: Optional[List[str]] = None,
) -> WritePreview:
    """Thin compatibility delegate for ``2xwb9b`` callers; delegates to :func:`write_legacy`."""
    return write_legacy(
        target,
        events,
        record_type=target.record_type,
        render=render,
        repo_root=repo_root,
        project_context=project_context,
        destination=destination,
        dry_run=dry_run,
        actor=actor,
        by_human=by_human,
        overrides=overrides,
        migration_import=migration_import,
        sidecar=sidecar,
        quiet=quiet,
        from_status=from_status,
        notes_out=notes_out,
    )


def append(
    id6: Union[str, "LegacyTarget"],
    events: List[Dict[str, Any]],
    *,
    expect_seq: Optional[int] = None,
    dry_run: bool = False,
    project_context: Any = None,
    actor: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    by_human: bool = False,
    overrides: Optional[List[str]] = None,
    migration_import: bool = False,
    _from_create: bool = False,
    legacy_render: Optional[LegacyRender] = None,
    **legacy_kwargs: Any,
) -> Any:
    """Append events to an artifact under lock.

    Dispatches on the TARGET's storage format (2xwb9b E-03, `_storage_format`): a record with a
    `meta/<id6>.jsonl` log appends to the log (the tve77h path below); a record without one, which in
    phase B is every real record, renders the events into its bullet-format file through
    :func:`write_legacy` and returns a :class:`WritePreview`. The legacy branch needs a
    :class:`LegacyTarget` (or an id6 whose file the cache resolves) and a :class:`LegacyRender`."""
    if isinstance(id6, LegacyTarget) or legacy_render is not None:
        target = id6
        ctx = project_context or (
            legacy_context(legacy_kwargs["repo_root"])
            if "repo_root" in legacy_kwargs
            else _proj_ctx.resolve_project_context()
        )
        records_root = Path(ctx.logical_roots["records"])
        if _storage_format(records_root, target) == "legacy":
            if not isinstance(target, LegacyTarget):
                rel = resolve(target, project_context=ctx)
                if rel is None:
                    raise ValueError(f"artifact not found: {target}")
                st = read(target, project_context=ctx)
                plural = {v: k for k, v in _LEGACY_PLURAL_TO_TYPE.items()}.get(
                    st.type, "other"
                )
                scan_repo = legacy_kwargs.get("repo_root") or _scan_repo_root(
                    ctx, records_root
                )
                target_id = None if st.id_derived else target
                target = LegacyTarget(
                    source_path(rel, records_root, scan_repo), plural, target_id
                )
            if legacy_render is None:
                raise ValueError("a legacy-format append requires legacy_render")
            repo_root = (
                legacy_kwargs.pop("repo_root", None)
                or getattr(ctx, "repo_root", None)
                or getattr(ctx, "target_repo", None)
                or _resolve_repo_root(records_root)
            )
            return write_legacy(
                target,
                events,
                record_type=target.record_type,
                render=legacy_render,
                repo_root=repo_root,
                project_context=ctx,
                dry_run=dry_run,
                actor=actor,
                by_human=by_human,
                overrides=overrides,
                migration_import=migration_import,
                **legacy_kwargs,
            )
        id6 = (target.id6 or "") if isinstance(target, LegacyTarget) else str(target)
    assert isinstance(id6, str)
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    log_path = records_root / "meta" / f"{id6}.jsonl"
    lock_path = state_root / "locks" / f"meta-{id6}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Check for pending repair/recovery before mutation
    j_file = _journal_dir(state_root) / f"{id6}.json"
    if j_file.exists() and not _from_create:
        raise RuntimeError(
            f"cannot mutate artifact {id6}: recovery is pending; run repair first"
        )

    # Hold artifact lock
    with _lock.held(lock_path):
        existing_lines: List[str] = []
        current_seq = 0
        if log_path.exists():
            existing_lines = log_path.read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            if existing_lines:
                last_ev = decode_line(existing_lines[-1])
                current_seq = last_ev["seq"]

        if expect_seq is not None and current_seq != expect_seq:
            raise ValueError(
                f"optimistic concurrency failure: expected seq {expect_seq}, log is at {current_seq}"
            )

        # Assign consecutive seq, single append, at, and actor
        now_utc = datetime.datetime.now(timezone.utc).isoformat()
        append_seq = current_seq + 1
        default_actor = actor or {"tool": "artifact_meta"}

        prepared_events: List[Dict[str, Any]] = []
        for i, ev in enumerate(events):
            e = dict(ev)
            e["v"] = 1
            e["seq"] = current_seq + 1 + i
            e["append"] = append_seq
            e["at"] = now_utc
            e["actor"] = default_actor
            if by_human:
                e["by_human"] = True
            if overrides:
                e["overrides"] = overrides
            if message and "message" not in e:
                e["message"] = message
            prepared_events.append(e)

        # Validate with writer-side refusals
        art_type = "ipd"
        if existing_lines:
            ev0 = decode_line(existing_lines[0])
            f0 = ev0.get("fields", {})
            art_type = f0.get("type", "ipd")
        elif prepared_events and prepared_events[0].get("op") == "create":
            art_type = prepared_events[0].get("fields", {}).get("type", "ipd")

        validate_new_events(
            art_type,
            prepared_events,
            records_root=records_root,
            repo_root=(
                getattr(ctx, "repo_root", None) or getattr(ctx, "target_repo", None)
            ),
            migration_import=migration_import,
        )

        # Replay full log before dry_run or commit so illegal transitions/owned-field
        # mutations raise ValueError before touching meta/<id6>.jsonl.
        all_lines = existing_lines + [encode_event(e) for e in prepared_events]
        state, _, _, _ = replay(
            id6,
            art_type,
            all_lines,
            records_root=records_root,
            migration_import=migration_import,
        )

        # Dry run check
        if dry_run:
            return {"committed": False, "dry_run": True, "events": prepared_events}

        # Step 1: Write log via temp file, fsync, os.replace (THE COMMIT POINT)
        log_content = "".join(all_lines)
        try:
            _atomic_replace_fsync(log_path, log_content)
        except Exception as exc:
            return {"committed": False, "error": f"no change; write failed: {exc}"}

        # After step 1: Change is recorded. Subsequent steps are best effort/recovery
        try:
            scan_repo = _scan_repo_root(ctx, records_root)
            # Step 2: In-file mirror
            if state.path:
                art_abs_p = source_path(state.path, records_root, scan_repo)
                if art_abs_p.exists():
                    txt = art_abs_p.read_text(encoding="utf-8")
                    new_txt = apply_in_file_mirror(txt, id6, art_type, state.status)
                    _core.atomic_write(art_abs_p, new_txt)

            # Step 3: Disposition move if needed
            # (Handled if path changed)

            # Step 4: Cache update
            conn = open_cache(records_root, state_root)
            try:
                _load_sources(
                    conn,
                    [
                        {
                            "path": f"meta/{id6}.jsonl",
                            "role": "log",
                            "id6": id6,
                            "type": art_type,
                        }
                    ],
                    records_root,
                    repo_root=scan_repo,
                )
            finally:
                conn.close()

            return {"committed": True, "seq": state.last_seq, "status": state.status}

        except Exception as step_exc:
            return {
                "committed": True,
                "warning": f"change recorded; run repair ({step_exc})",
            }


def create(
    id6: str,
    artifact_type: str,
    fields: Dict[str, Any],
    body: str,
    *,
    destination: Optional[Union[str, Path]] = None,
    dry_run: bool = False,
    project_context: Any = None,
    actor: Optional[Dict[str, Any]] = None,
    migration_import: bool = False,
    legacy_render: Optional[LegacyRender] = None,
    **legacy_kwargs: Any,
) -> Any:
    """Create a new artifact with an initial create event and retain recovery journal (log branch),
    or render legacy metadata + body through :func:`write_legacy` when ``legacy_render`` is given
    on a legacy root."""
    validate_id6(id6)
    if legacy_render is not None:
        ctx = project_context or (
            legacy_context(legacy_kwargs["repo_root"])
            if "repo_root" in legacy_kwargs
            else _proj_ctx.resolve_project_context()
        )
        records_root = Path(ctx.logical_roots["records"])
        if _storage_format(records_root, id6) == "legacy":
            if not destination:
                destination = f"{artifact_type}s/pending/{id6}.md"
            dest_input = Path(destination)
            if dest_input.is_absolute():
                dest_path = dest_input
                try:
                    ev_path = (
                        dest_path.resolve()
                        .relative_to(records_root.resolve())
                        .as_posix()
                    )
                except (OSError, ValueError):
                    ev_path = str(destination).replace("\\", "/")
            else:
                dest_path = records_root / dest_input
                ev_path = str(destination).replace("\\", "/")
            _, plural = _normalize_legacy_types(artifact_type, dest_path, records_root)
            source_digest = legacy_kwargs.pop("source_digest", None)
            repo_root = (
                legacy_kwargs.pop("repo_root", None)
                or getattr(ctx, "repo_root", None)
                or getattr(ctx, "target_repo", None)
                or _resolve_repo_root(records_root)
            )
            create_ev: Dict[str, Any] = {
                "op": "create",
                "path": ev_path,
                "fields": {**fields, "id": id6, "type": artifact_type},
            }
            msg = legacy_kwargs.pop("message", None)
            if msg:
                create_ev["message"] = msg
            target = LegacyTarget(dest_path, plural, id6, source_digest=source_digest)
            return write_legacy(
                target,
                [create_ev],
                record_type=plural,
                render=legacy_render,
                repo_root=repo_root,
                project_context=ctx,
                dry_run=dry_run,
                actor=actor,
                migration_import=migration_import,
                initial_text=body,
                _trailing_body_only=(plural == "backlog"),
                **legacy_kwargs,
            )

    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    if not destination:
        destination = f"{artifact_type}s/pending/{id6}.md"
    dest_str = str(destination).replace("\\", "/")
    if Path(destination).is_absolute():
        try:
            dest_str = (
                Path(destination)
                .resolve()
                .relative_to(records_root.resolve())
                .as_posix()
            )
        except (OSError, ValueError):
            pass

    # Retain operation journal before step 1
    j_dir = _journal_dir(state_root)
    j_file = j_dir / f"{id6}.json"
    journal_data = {
        "op": "create",
        "id6": id6,
        "type": artifact_type,
        "destination": dest_str,
        "body": body,
    }
    j_file.write_text(json.dumps(journal_data, indent=2), encoding="utf-8")

    try:
        # Create event
        create_ev = {
            "op": "create",
            "path": dest_str,
            "fields": {**fields, "id": id6, "type": artifact_type},
        }
        res = append(
            id6,
            [create_ev],
            expect_seq=0,
            dry_run=dry_run,
            project_context=ctx,
            actor=actor,
            migration_import=migration_import,
            _from_create=True,
        )

        if dry_run or not res.get("committed"):
            j_file.unlink(missing_ok=True)
            return res

        # Materialize artifact body
        dest_path = records_root / dest_str
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        mirror_prefix = render_in_file_mirror(id6, artifact_type, fields.get("status"))
        _core.atomic_write(dest_path, mirror_prefix + body)

        # Clear journal on success
        j_file.unlink(missing_ok=True)
        return res
    except Exception:
        # Journal remains on failure
        raise


def repair(
    id6: str, *, confirm: Optional[bool] = None, project_context: Any = None
) -> Dict[str, Any]:
    """Repair drift, journaled incomplete operations, or diverged tails for an artifact."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    log_path = records_root / "meta" / f"{id6}.jsonl"
    lock_path = state_root / "locks" / f"meta-{id6}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    scan_repo = _scan_repo_root(ctx, records_root)
    with _lock.held(lock_path):
        # 1. Check operation journal
        j_file = _journal_dir(state_root) / f"{id6}.json"
        if j_file.exists():
            j_data = json.loads(j_file.read_text(encoding="utf-8"))
            if j_data.get("op") == "create":
                body = j_data.get("body")
                dest = j_data.get("destination")
                if not body:
                    raise RuntimeError(
                        "refused repair: missing recovery source (empty body)"
                    )
                dest_path = source_path(dest, records_root, scan_repo)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                _core.atomic_write(dest_path, body)
                j_file.unlink(missing_ok=True)

        if not log_path.exists():
            return {"status": "no log", "repaired": False}

        lines = log_path.read_text(encoding="utf-8").splitlines(keepends=True)
        events = [decode_line(line) for line in lines]

        # Check for diverged merge (duplicate seq)
        seqs = [e["seq"] for e in events]
        has_duplicate_seq = len(seqs) != len(set(seqs))

        if has_duplicate_seq:
            if not confirm:
                return {
                    "diverged": True,
                    "repaired": False,
                    "message": "tail divergence detected; confirm=True required to resequence tail",
                }
            # Confirmed tail repair
            # Find the winning prefix: consecutive unique seqs starting at 0 or 1
            winning_prefix: List[Dict[str, Any]] = []
            seen: Set[int] = set()
            tail_events: List[Dict[str, Any]] = []
            for ev in events:
                s = ev["seq"]
                if s not in seen and not tail_events:
                    seen.add(s)
                    winning_prefix.append(ev)
                else:
                    tail_events.append(ev)

            # Resequence tail
            last_k = winning_prefix[-1]["seq"] if winning_prefix else 0
            resequenced: List[Dict[str, Any]] = []
            for i, ev in enumerate(tail_events, start=1):
                ev_copy = dict(ev)
                ev_copy["seq"] = last_k + i
                ev_copy["append"] = last_k + i
                resequenced.append(ev_copy)

            repaired_events = winning_prefix + resequenced
            # Validate replay of whole sequence
            art_type = winning_prefix[0].get("fields", {}).get("type", "ipd")
            replay(id6, art_type, repaired_events, records_root=records_root)

            # Write reconciled log
            new_log_text = "".join(encode_event(e) for e in repaired_events)
            _atomic_replace_fsync(log_path, new_log_text)
            lines = new_log_text.splitlines(keepends=True)

        # Deterministic mirror repair
        art_type = "ipd"
        ev0 = decode_line(lines[0])
        f0 = ev0.get("fields", {})
        art_type = f0.get("type", "ipd")
        state, _, _, _ = replay(id6, art_type, lines, records_root=records_root)

        if state.path:
            p = source_path(state.path, records_root, scan_repo)
            if p.exists():
                txt = p.read_text(encoding="utf-8")
                new_txt = apply_in_file_mirror(txt, id6, art_type, state.status)
                _core.atomic_write(p, new_txt)

        # Update cache
        conn = open_cache(records_root, state_root)
        try:
            _load_sources(
                conn,
                [
                    {
                        "path": f"meta/{id6}.jsonl",
                        "role": "log",
                        "id6": id6,
                        "type": art_type,
                    }
                ],
                records_root,
                repo_root=scan_repo,
            )
        finally:
            conn.close()

        return {"repaired": True, "status": state.status, "seq": state.last_seq}
