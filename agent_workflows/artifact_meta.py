"""The single metadata authority for artifacts: registry, event schema, replay, cache, legacy loader, and writes.

Spec 4sd62s Phase A Step 1 (IPD tve77h).

This module is the ONLY reader and writer of artifact metadata.
All read operations query the SQLite cache (.aw/state/index.db), which is brought up to date
via the two-check freshness check (directory membership and working-tree content digest)
before any query answers.
"""

from __future__ import annotations

import contextlib
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
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
)

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import attention_contract as _att
from agent_workflows import ipd_lifecycle as _ipd_life
from agent_workflows import ipd_schema as _ipd_schema
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
    },
    "spec": {
        **_COMMON_FIELDS,
        "set": FieldDef("set", "string", "generic"),
        "order": FieldDef("order", "integer", "generic"),
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "work_kind": FieldDef("work_kind", "string", "generic"),
        "priority": FieldDef("priority", "string", "generic"),
        "blocks_release": FieldDef("blocks_release", "reference", "generic"),
        "from_backlog": FieldDef("from_backlog", "reference", "generic"),
        "from_spec": FieldDef("from_spec", "reference", "generic"),
        "supersedes": FieldDef("supersedes", "reference", "generic"),
        "gate_kind": FieldDef("gate_kind", "string", "generic"),
        "gate_ref": FieldDef("gate_ref", "string", "generic"),
        "gate_summary": FieldDef("gate_summary", "string", "generic"),
    },
    "backlog": {
        **_COMMON_FIELDS,
        "status": FieldDef("status", "closed enum", "transition-owned"),
        "priority": FieldDef("priority", "string", "generic"),
        "work_kind": FieldDef("work_kind", "string", "generic"),
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
        "consumed_by": FieldDef("consumed_by", "string list", "generic"),
        "topic": FieldDef("topic", "string", "generic"),
    },
    "release": {
        **_COMMON_FIELDS,
        "status": FieldDef("status", "closed enum", "transition-owned"),
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

    if artifact_type == "walkthrough":
        return False, "walkthrough artifacts have no status and accept no transitions"

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
            if to_status in ("open", "draft"):
                return True, ""
            return False, f"backlog must start at open or draft, not {to_status!r}"
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
                    if op in ("create", "checkpoint") and f in ("id", "type", "status"):
                        continue
                    if f not in reg:
                        raise ValueError(
                            f"unknown field '{f}' for type '{artifact_type}'"
                        )


# --------------------------------------------------------------------------------------
# 4. Writer-Side Refusals (E-03)
# --------------------------------------------------------------------------------------

_ABSOLUTE_POSIX_PATH_RE = re.compile(r"/(?:[^/\s]+/)+[^/\s]+")
_WINDOWS_DRIVE_RE = re.compile(r"\b[a-zA-Z]:[/\\]")


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


def _check_no_absolute_paths_in_text(token_source: str, text: str) -> None:
    # Check POSIX paths with two or more segments, e.g. /opt/x or /home/user/a.md
    # but allowing single-segment tool commands like /plan-review or /spec-review
    for token in text.split():
        if _WINDOWS_DRIVE_RE.search(token):
            raise ValueError(
                f"{token_source} must not contain absolute Windows drive path: {token!r}"
            )
        if token.startswith("/") and token.count("/") >= 2:
            raise ValueError(
                f"{token_source} must not contain absolute multi-segment path: {token!r}"
            )


def _check_leak_sanitizer(text: str, prefix: str, ruleset: _leak.Ruleset) -> None:
    findings = _leak.scan_text(text, prefix, ruleset, include_warn=True)
    if findings:
        first = findings[0]
        raise ValueError(
            f"leak sanitizer refusal ({first.rule}) in {prefix}: {first.snippet!r}"
        )


def _check_path_safety(p_str: str, records_root: Path, label: str) -> None:
    if not isinstance(p_str, str):
        raise ValueError(f"{label} must be a string")
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
        resolved = (records_root / p).resolve()
        resolved_root = records_root.resolve()
        if not (resolved == resolved_root or resolved_root in resolved.parents):
            raise ValueError(f"{label} must resolve inside records root: {p_str!r}")
    except Exception as exc:
        raise ValueError(f"failed to resolve {label} {p_str!r}: {exc}") from exc


#: Field values that are prose or carry a list, so they take the prose length class rather than the
#: 300-character single-line bound: `approval` embeds the approval `--message` (2xwb9b D-03), and
#: `item_dependencies`/`graduated_to` grow with their edge count.
_PROSE_FIELDS: FrozenSet[str] = frozenset(
    ("close_evidence", "gate_summary", "approval", "item_dependencies", "graduated_to")
)


def _writer_ruleset(repo_root: Path) -> "_leak.Ruleset":
    """The leak ruleset the writer scans with: every `fail` rule plus every auto-derived `warn`
    token EXCEPT, inside a runner lane (`.aw/worktrees/<lane>`), the sibling LANE directory names
    (2xwb9b D-02).

    Spec 4.2 lists what the writer refuses: session ids, command lines, absolute or home paths, user
    names and host names. A sibling directory name is none of those; in a runner lane the siblings
    are the OTHER lanes, which are named by plan id6, so keeping them would refuse every message or
    `Item-Dependencies` value that cites a plan that happens to have a lane (measured: 39 tracked
    history lines would be refused for this reason alone)."""
    ruleset = _leak.build_ruleset(repo_root, include_warn=True)
    try:
        in_lane = Path(repo_root).resolve().parent.name == "worktrees"
        derived = _leak.derive_warn_tokens(repo_root) if in_lane else {}
    except Exception:
        return ruleset
    for tok, reason in derived.items():
        if reason == "sibling checkout dir name":
            ruleset.warn.pop(f"derived:{tok}", None)
    return ruleset


def validate_new_events(
    artifact_type: str,
    events: List[Dict[str, Any]],
    *,
    records_root: Path,
    repo_root: Optional[Path] = None,
    migration_import: bool = False,
) -> None:
    """Run writer-side refusals on events to be committed."""
    records_root = Path(records_root)
    if repo_root is None:
        repo_root = _proj_ctx.record_git_root(records_root) or records_root
    repo_root = Path(repo_root)

    # Build ruleset with include_warn=True once per call
    ruleset = _writer_ruleset(repo_root)

    for ev in events:
        validate_event(ev, artifact_type)

        # Actor checks
        actor = ev["actor"]
        for ak, av in actor.items():
            if isinstance(av, str):
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

        # Path checks on event envelope
        ev_path = ev.get("path")
        if ev_path:
            _check_path_safety(ev_path, records_root, f"{ev['op']}.path")

        # Payload checks
        if ev["op"] == "legacy":
            line_val = ev.get("line")
            if isinstance(line_val, str):
                # leak scan still runs on imported legacy lines
                _check_leak_sanitizer(line_val, "legacy.line", ruleset)
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
                _check_leak_sanitizer(leg_verdict, "legacy_verdict", ruleset)
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
                    if isinstance(fv, list):
                        for item in fv:
                            p_val = (
                                item.get("path")
                                if isinstance(item, dict)
                                else str(item)
                            )
                            _check_path_safety(p_val, records_root, f"fields.{fk}")
                elif fk == "path":
                    _check_path_safety(str(fv), records_root, "fields.path")
                elif isinstance(fv, str):
                    is_prose = fk in _PROSE_FIELDS
                    _check_string_safety(
                        fk, fv, prose=is_prose, migration_import=migration_import
                    )
                    _check_leak_sanitizer(fv, f"fields.{fk}", ruleset)


# --------------------------------------------------------------------------------------
# 5. Structured Relationships (E-04)
# --------------------------------------------------------------------------------------


def parse_item_dependencies_field(
    value: Optional[str],
) -> Tuple[str, List[Dict[str, Any]]]:
    """Parse Item-Dependencies into (declaration, conditions).

    Distinguishes absent (None), 'none', 'unresolved', and listed edges.
    """
    if value is None:
        return "absent", []
    v = value.strip()
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
    dep_decl, dep_edges = parse_item_dependencies_field(
        current_fields.get("item_dependencies")
    )
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


def parse_artifact_mirror(text: str) -> Dict[str, Any]:
    """Parse standard artifact front matter (id and status).

    Strict line grammar: exactly two keys 'id' and 'status' in that order.
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
    if len(fmlines) != 2:
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
LEGACY_LOADER_VERSION = "legacy_v3"

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
            defect TEXT
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
    with conn:
        conn.executescript(schema_sql)
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

    need_rebuild = False
    if not db_path.exists():
        need_rebuild = True
    else:
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            row_hash = conn.execute(
                "SELECT value FROM meta WHERE key = 'schema_hash'"
            ).fetchone()
            row_root = conn.execute(
                "SELECT value FROM meta WHERE key = 'records_root'"
            ).fetchone()
            if (
                not row_hash
                or row_hash[0] != shash
                or not row_root
                or row_root[0] != str(records_root)
            ):
                need_rebuild = True
                conn.close()
            else:
                return conn
        except Exception:
            need_rebuild = True
            with contextlib.suppress(Exception):
                conn.close()

    if need_rebuild:
        try:
            if db_path.exists():
                if db_path.is_dir():
                    shutil.rmtree(db_path)
                else:
                    db_path.unlink()
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            init_cache(conn, records_root, registry)
            return conn
        except Exception:
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
_YAML_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*)$")


def _parse_bullet_metadata(
    text: str,
) -> Tuple[Dict[str, str], Optional[str], List[str]]:
    """Parse bullet block before first ## heading. Returns (bullets, title, history_lines).

    THE BULLET REGION STARTS AT THE TOP OF THE FILE, not after a `# ` title (backlog `suth7l`).
    It is the same region `selectors.metadata_region` bounds every other reader to: everything
    before the first `##` heading, with an optional leading `# ` title inside it. Backlog items
    carry no title line at all (they open with `- Id:`), so a loader that started reading only
    after a title dropped every backlog item's bullets; measured on this repository on 2026-11-07,
    that cost 1146 backlog records their status in the cache.
    """
    lines = text.splitlines()
    bullets: Dict[str, str] = {}
    title: Optional[str] = None
    in_bullets = True
    first_h1_done = False
    history_lines: List[str] = []
    in_history = False

    for line in lines:
        stripped = line.strip()
        if not first_h1_done and in_bullets and stripped.startswith("# "):
            title = stripped[2:].strip()
            first_h1_done = True
            continue

        if stripped.startswith("## Workflow history"):
            in_history = True
            in_bullets = False
            continue
        elif in_history and stripped.startswith("## "):
            in_history = False

        if in_history:
            if stripped.startswith("- "):
                history_lines.append(stripped)
            continue

        if in_bullets:
            if stripped.startswith("## "):
                in_bullets = False
                continue
            m = _BULLET_RE.match(line)
            if m:
                k = m.group(1).strip()
                v = m.group(2).strip()
                bullets[k] = v

    return bullets, title, history_lines


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
            data[m.group(1).strip()] = m.group(2).strip()
    title: Optional[str] = None
    if closing_idx != -1:
        for j in range(closing_idx + 1, len(lines)):
            if lines[j].strip().startswith("# "):
                title = lines[j].strip()[2:].strip()
                break
    return data, title


#: Per-process id6 collision pools for the legacy loader's fallback mint, keyed by resolved records
#: root (see `load_legacy_artifact`).
_LEGACY_MINT_POOLS: Dict[str, Set[str]] = {}


def load_legacy_artifact(
    path: Path,
    records_root: Path,
    text: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load an existing legacy .md artifact into cache projection rows."""
    if text is None:
        text = path.read_text(encoding="utf-8")

    filename = path.name
    rel_path = str(path.relative_to(records_root)).replace("\\", "/")
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
    rel_parts = path.relative_to(records_root).parts
    top_dir = rel_parts[0] if rel_parts else ""
    type_map = {
        "plans": "ipd",
        "specs": "spec",
        "backlog": "backlog",
        "research": "research",
        "releases": "release",
        "prompts": "prompt",
        "walkthroughs": "walkthrough",
    }
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
    if art_type not in REGISTRY:
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
    if _yaml_probe and not _BULLET_RE.search(_after_fence):
        yaml_data, title = _parse_yaml_front_matter(text)
        bullets = dict(yaml_data)
        if "id" in bullets and not id6:
            id6 = bullets["id"]
        if "set" in bullets and not set_id:
            set_id = bullets["set"]
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
        if m_prompt:
            for item in m_prompt.group(1).split("|"):
                if ":" in item:
                    k, v = item.split(":", 1)
                    bullets[k.strip()] = v.strip()
        else:
            # Check for legacy <!-- aw-prompt: ... -->
            m_aw = re.match(r"\A<!--\s*aw-prompt:\s*(.*?)\s*-->", first_line, re.DOTALL)
            if m_aw:
                for item in m_aw.group(1).split("|"):
                    if ":" in item:
                        k, v = item.split(":", 1)
                        bullets[k.strip()] = v.strip()
        for ln in lines:
            if ln.strip().startswith("# "):
                title = ln.strip()[2:].strip()
                break
    else:
        bullets, title, history_lines = _parse_bullet_metadata(text)

    # In-file Id override
    if "Id" in bullets:
        id6 = bullets["Id"]
    elif "id" in bullets and not id6:
        id6 = bullets["id"]

    if not id6:
        # Default fallback id6 for grandfathered legacy files. The repository-wide collision pool
        # is scanned ONCE per records root per process and extended with every id minted here
        # (1ajqaa): calling `mint_id6` per file re-scanned the whole repository each time, which
        # measured 70 scans and about 5 minutes for one cold cache build of this repository.
        _pool_key = str(Path(records_root).resolve())
        _pool = _LEGACY_MINT_POOLS.get(_pool_key)
        if _pool is None:
            _pool = set(
                _core.global_id6s(
                    _proj_ctx.record_git_root(records_root) or records_root
                )
            )
            _LEGACY_MINT_POOLS[_pool_key] = _pool
        id6 = _core.generate_id6(_pool)
        _pool.add(id6)

    validate_id6(id6)

    # Status handling (OQ-03):
    # Only single-token status sets artifacts.status (matches selectors._STATUS_RE)
    raw_status = bullets.get("Status") or bullets.get("status")
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
        target_k = field_map.get(bk, bk.lower().replace("-", "_"))
        reg = REGISTRY.get(art_type, {})
        if target_k in reg:
            mapped_fields[target_k] = bv
        else:
            # Unregistered legacy bullet (OQ-02): keep in mapped_fields but mark legacy
            mapped_fields[target_k] = bv

    # Item-Dependencies
    raw_deps = bullets.get("Item-Dependencies") or bullets.get("item-dependencies")
    if raw_deps:
        mapped_fields["item_dependencies"] = raw_deps

    # Newest history day
    last_hist_day: Optional[str] = None
    if history_lines:
        newest = _att.newest_history_record(history_lines)
        if newest:
            last_hist_day = _att.last_history_at([newest])

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
        "created_day": None,
        "created_at": None,
        "updated_at": None,
        "last_history_day": last_hist_day,
        "last_seq": len(history_lines),
        "valid": 1,
        "defect": None,
        # The registry-typed field values, for the per-type table (backlog `suth7l`: the loader
        # computed these and then dropped them, so every per-type table held 0 rows). Only fields
        # the REGISTRY declares for this type are carried; unregistered legacy bullets (OQ-02) stay
        # out of the typed table, exactly as the log branch's replay keeps them out.
        "fields": {
            k: v for k, v in mapped_fields.items() if k in REGISTRY.get(art_type, {})
        },
    }

    # History rows
    hist_rows: List[Dict[str, Any]] = []
    for i, hline in enumerate(history_lines, start=1):
        hist_rows.append(
            {
                "id6": id6,
                "seq": i,
                "line": hline,
                "observed_day": _att.last_history_at([hline]),
            }
        )

    return artifact_row, hist_rows


def load_legacy_review(
    path: Path,
    records_root: Path,
    text: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load a legacy .review.md file into review_files and reviews rows."""
    if text is None:
        text = path.read_text(encoding="utf-8")

    filename = path.name
    rel_path = str(path.relative_to(records_root)).replace("\\", "/")
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


def _load_sources(
    conn: sqlite3.Connection,
    changed_sources: List[Dict[str, Any]],
    records_root: Path,
) -> None:
    """One loader entry point: validate, replay and project changed sources."""
    records_root = Path(records_root)
    with conn:
        for item in changed_sources:
            path_str = item["path"]
            abs_p = records_root / path_str
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
                conn.execute("DELETE FROM artifacts WHERE id6 = ?", (id6,))
                for t in SUPPORTED_TYPES:
                    conn.execute(f'DELETE FROM "{t}" WHERE id6 = ?', (id6,))
                conn.execute("DELETE FROM scope_paths WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM artifact_paths WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM scope_exceptions WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM dependencies WHERE dependent_id6 = ?", (id6,))
                conn.execute("DELETE FROM lineage WHERE child_id6 = ?", (id6,))
                conn.execute(
                    "DELETE FROM graduation_targets WHERE source_id6 = ?", (id6,)
                )
                conn.execute("DELETE FROM release_gates WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM gates WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM events WHERE id6 = ?", (id6,))
                conn.execute("DELETE FROM field_changes WHERE id6 = ?", (id6,))

            if not abs_p.exists():
                # Removed file. A removed source arrives with role "removed", so its former role
                # is read from the files table (1ajqaa: a deleted review file kept its row).
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
            st = abs_p.stat()
            digest = _compute_digest(abs_p)
            now_str = datetime.datetime.now(timezone.utc).isoformat()

            if role == "log":
                # Load jsonl log
                try:
                    lines = abs_p.read_text(encoding="utf-8").splitlines(keepends=True)
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
                            last_history_day, last_seq, valid, defect
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                            id6, type, path, valid, defect
                        ) VALUES (?, ?, ?, ?, ?)""",
                        (id6, item.get("type", "unknown"), path_str, 0, err_msg),
                    )

            elif role == "review":
                try:
                    rf_row, rev_rows = load_legacy_review(abs_p, records_root)
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
                    art_row, h_rows = load_legacy_artifact(abs_p, records_root)
                    # A mirror of a logged artifact does not replace the log's projection
                    # (1ajqaa): the log is the authority once `meta/<id6>.jsonl` exists.
                    _has_log = (
                        records_root / "meta" / f"{art_row['id6']}.jsonl"
                    ).exists()
                    _verb = "INSERT OR IGNORE" if _has_log else "INSERT OR REPLACE"
                    conn.execute(
                        _verb
                        + """ INTO artifacts (
                            id6, type, path, disposition, status, title, short_description,
                            set_id, order_nn, filename_date, created_day, created_at, updated_at,
                            last_history_day, last_seq, valid, defect
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                        ),
                    )
                    if not _has_log:
                        # The per-type row (backlog `suth7l`), written with exactly the column
                        # layout and value encoding the log branch uses, so a reader of a typed
                        # field sees one representation whichever format the record is in.
                        _lt = art_row["type"]
                        if _lt in REGISTRY:
                            _reg_fields = registry_fields(_lt)
                            _fv = art_row.get("fields") or {}
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
                                id6, type, path, valid, defect
                            ) VALUES (?, ?, ?, ?, ?)""",
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


def check_freshness(
    conn: sqlite3.Connection,
    records_root: Path,
    *,
    force: bool = False,
    project_context: Any = None,
) -> None:
    """Run directory membership and file content freshness checks before read operations."""
    records_root = Path(records_root)
    _require_schema(project_context, records_root)
    if not records_root.exists():
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

    # Discover directories and files
    for root, dirs, files in os.walk(records_root):
        rel_dir = str(Path(root).relative_to(records_root)).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""
        st_dir = os.stat(root)
        current_mtime = st_dir.st_mtime_ns
        prev_mtime = known_dirs.get(rel_dir)
        if prev_mtime != current_mtime:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO directories (path, mtime_ns) VALUES (?, ?)",
                    (rel_dir, current_mtime),
                )

        for fname in files:
            if (
                fname.startswith(".")
                or fname.startswith("INDEX.")
                or fname == "STATUS.md"
            ):
                continue
            fpath = Path(root) / fname
            rel_f = str(fpath.relative_to(records_root)).replace("\\", "/")
            current_files_set.add(rel_f)

            # Determine file role
            role: Optional[str] = None
            f_id6: Optional[str] = None
            f_type: Optional[str] = None

            if rel_f.startswith("meta/") and fname.endswith(".jsonl"):
                role = "log"
                f_id6 = fname[:-6]
            elif fname.endswith(".review.md"):
                role = "review"
            elif fname.endswith(".walkthrough.md"):
                role = "walkthrough"
            elif fname.endswith(".md"):
                role = "artifact"
                m_attr = _naming.parse_attributed(fname)
                if m_attr:
                    f_id6 = m_attr.id6
                    f_type = m_attr.type
                else:
                    m_clust = _naming.parse_clustered(fname)
                    if m_clust:
                        f_id6 = m_clust.group("id6")
                        f_type = m_clust.group("type")

            if not role:
                continue

            st_f = fpath.stat()
            prev_info = known_files.get(rel_f)
            must_load = force
            if prev_info is None:
                must_load = True
            else:
                prev_size, prev_mtime_f, prev_digest = prev_info
                if prev_size != st_f.st_size or prev_mtime_f != st_f.st_mtime_ns:
                    must_load = True
                else:
                    # Content check: digest working-tree bytes to detect same-size same-mtime replacements
                    curr_digest = _compute_digest(fpath)
                    if curr_digest != prev_digest:
                        must_load = True

            if must_load:
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

    if changed_sources:
        _load_sources(conn, changed_sources, records_root)

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
            rel_outcome = _releases.resolve_release_outcome(records_root.parent, "next")
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


# --------------------------------------------------------------------------------------
# 11. Public Read Interface (E-13, E-14, 4.3, 4.4)
# --------------------------------------------------------------------------------------


class QueryResult(list):
    """List of State objects with an incomplete attribute naming invalid/missing records."""

    def __init__(self, items: Iterable[State], incomplete: Optional[List[str]] = None):
        super().__init__(items)
        self.rows: List[State] = list(items)
        self.incomplete: List[str] = list(incomplete or [])


def read(id6: str, *, project_context: Any = None) -> State:
    """Read current state of an artifact. Fails closed on invalid record."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    conn = open_cache(records_root, state_root)
    try:
        check_freshness(conn, records_root, project_context=ctx)

        row = conn.execute(
            """SELECT id6, type, path, disposition, status, title, short_description,
                      set_id, order_nn, filename_date, created_day, created_at, updated_at,
                      last_history_day, last_seq, valid, defect
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
        conn.close()


def history(id6: str, *, project_context: Any = None) -> List[Dict[str, Any]]:
    """Return ordered event history of an artifact."""
    validate_id6(id6)
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    conn = open_cache(records_root, state_root)
    try:
        check_freshness(conn, records_root, project_context=ctx)

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
            abs_p = records_root / art[0]
            if abs_p.exists() and abs_p.suffix == ".md":
                _, legacy_rows = load_legacy_artifact(abs_p, records_root)

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
        conn.close()


def resolve(
    path_or_id6: Union[str, Path], *, project_context: Any = None
) -> Optional[str]:
    """Resolve a path or id6 to its canonical records-root-relative path."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    conn = open_cache(records_root, state_root)
    try:
        check_freshness(conn, records_root, project_context=ctx)

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
        conn.close()


def query(*, project_context: Any = None, **filters) -> QueryResult:
    """Query metadata cache with typed filters. Returns QueryResult."""
    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    conn = open_cache(records_root, state_root)
    try:
        check_freshness(conn, records_root, project_context=ctx)

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
                         a.last_history_day, a.last_seq, a.valid, a.defect
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
            )
            states.append(st)

        # Check for invalid records that matched the domain
        incomplete_rows = conn.execute(
            "SELECT id6 FROM artifacts WHERE valid = 0"
        ).fetchall()
        incomplete = [ir[0] for ir in incomplete_rows]

        return QueryResult(states, incomplete)
    finally:
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
    conn = open_cache(records_root, state_root)
    try:
        check_freshness(conn, records_root, project_context=ctx)
        rows = conn.execute(
            "SELECT path, parse_ok, round_count FROM review_files WHERE subject_id6 = ? ORDER BY path",
            (subject_id6,),
        ).fetchall()
    finally:
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


def read_at(id6: str, rev: str, *, project_context: Any = None) -> ReadAtResult:
    """Read metadata state at a git revision (HEAD, SHA, branch, etc.)."""
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

    conn = open_cache(records_root, state_root)
    try:
        # Verify revision exists
        res = subprocess.run(
            ["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
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
            rel_repo = str(records_root.relative_to(repo_dir)).replace("\\", "/")
        except Exception:
            rel_repo = ""
        log_path = f"meta/{id6}.jsonl"
        rel_log = (
            log_path if not rel_repo or rel_repo == "." else f"{rel_repo}/{log_path}"
        )

        res_log = subprocess.run(
            ["git", "ls-tree", rev, "--", rel_log],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if res_log.returncode == 0 and res_log.stdout.strip():
            parts = res_log.stdout.strip().split()
            log_blob_sha = parts[2]

            # Lookup in rev_log_states
            cached = conn.execute(
                "SELECT id6, status, last_seq, state_json FROM rev_log_states WHERE log_blob_sha = ?",
                (log_blob_sha,),
            ).fetchone()
            if cached:
                s_dict = json.loads(cached[3])
                st = State(**s_dict)
                return ReadAtResult(kind="ok", state=st)

            # Read blob with git cat-file
            cat = subprocess.run(
                ["git", "cat-file", "-p", log_blob_sha],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )
            if cat.returncode != 0:
                return ReadAtResult(
                    kind="corrupt", error=f"cannot read git blob {log_blob_sha}"
                )

            try:
                lines = cat.stdout.splitlines(keepends=True)
                state, _, _, _ = replay(id6, "ipd", lines, records_root=records_root)
                # Cache valid state
                conn.execute(
                    "INSERT OR REPLACE INTO rev_log_states VALUES (?, ?, ?, ?, ?)",
                    (
                        log_blob_sha,
                        id6,
                        state.status,
                        state.last_seq,
                        json.dumps(dataclasses.asdict(state)),
                    ),
                )
                return ReadAtResult(kind="ok", state=state)
            except Exception as exc:
                return ReadAtResult(kind="corrupt", error=str(exc))

        # Phase B legacy check: search for artifact .md containing id6 at revision
        # `-e` is required: the pattern starts with `-`, so without it git reads it as an option and
        # exits 129, which made every phase-B record read `absent`.
        # Use POSIX character classes (`[[:blank:]]` / `[[:space:]]`) rather than `\t` / `\r`:
        # BSD/Windows POSIX ERE may treat `\t`/`\r` as literal chars, and Windows blobs with CRLF
        # retain `\r` before `$` when `git grep` splits lines on `\n`.
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
        )
        if find_md.returncode == 0 and find_md.stdout.strip():
            md_entry = find_md.stdout.strip().splitlines()[0]
            # format: <rev>:<repo-relative path>
            md_file_path = (
                md_entry[len(rev) + 1 :] if md_entry.startswith(f"{rev}:") else md_entry
            )
            cat_md = subprocess.run(
                ["git", "show", f"{rev}:{md_file_path}"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )
            if cat_md.returncode != 0:
                return ReadAtResult(kind="corrupt", error="failed to read md blob")
            try:
                in_records = (
                    md_file_path[len(rel_repo) + 1 :]
                    if rel_repo and rel_repo != "."
                    else md_file_path
                )
                art_row, _ = load_legacy_artifact(
                    records_root / in_records, records_root, text=cat_md.stdout
                )
                st = State(
                    id6=art_row["id6"],
                    type=art_row["type"],
                    path=art_row["path"],
                    status=art_row["status"],
                    title=art_row["title"],
                    short_description=art_row["short_description"],
                    set_id=art_row["set_id"],
                    order_nn=art_row["order_nn"],
                )
                return ReadAtResult(kind="ok", state=st)
            except Exception as exc:
                return ReadAtResult(kind="corrupt", error=str(exc))

        return ReadAtResult(
            kind="absent", error=f"record {id6} not found in revision {rev}"
        )
    finally:
        conn.close()


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
}

#: Registry field -> YAML front-matter key for `research` records.
_RESEARCH_YAML_KEY: Dict[str, str] = {
    "id": "id",
    "status": "status",
    "set": "set",
    "order": "order",
    "research_kind": "kind",
    "outcome": "outcome",
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

_YAML_FENCE_OPEN_RE = re.compile(r"\A---[ \t]*\r?\n")

_META_BULLET_LINE_RE = re.compile(r"(?m)^-\s*[A-Za-z][A-Za-z0-9 /-]*:[^\n]*(?:\n|$)")


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
    state: Optional[Path] = None
    with contextlib.suppress(Exception):
        resolved = _proj_ctx.resolve_project_context(target_repo=str(root))
        if Path(resolved.logical_roots["records"]).resolve() == records.resolve():
            state = Path(resolved.logical_roots["state"])
    if state is None:
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
                unset_fields.add(fk)
    if leaving_approved and record_type == "ipd" and "approval" not in unset_fields:
        raise ValueError(
            "approval must be unset in the append containing a transition away from approved"
        )
    if backward and "readiness" not in unset_fields:
        raise ValueError(
            "readiness must be unset in the append of a backward plan transition"
        )


def _set_bullet(
    text: str, label: str, value: Optional[str], *, anchors: Tuple[str, ...]
) -> str:
    """Replace or remove `- <label>:` inside the metadata region, else insert after an anchor.

    D-2 / a88210: tries ``anchors`` in order, then falls back to the end of an existing metadata
    bullet block before the first ``## ``; writes nothing when the file has no metadata bullet block.
    """
    from agent_workflows import selectors as _sel

    region = _sel.metadata_region(text)
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
        from agent_workflows import prompts as _prompts

        if _prompts.has_metadata_comment(text):
            return _prompts.update_metadata_status(text, status), notes
        notes.append(
            f"aw set: note: prompt {label} has no metadata comment; status lives in directory only\n"
        )
        return text, notes

    status_updated = False
    new_lines: List[str] = []
    in_front = True
    fenced = bool(lines and lines[0].strip() == "---")
    status_bullet = re.compile(r"^-\s*Status:\s*(\S+)\s*$")
    for line in lines:
        if fenced:
            if in_front and line.strip() == "---" and new_lines:
                in_front = False
            if (
                in_front
                and not status_updated
                and re.match(r"^status:\s*\S+", line, re.IGNORECASE)
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

    if not status_updated:
        res: List[str] = []
        inserted = False
        if fenced:
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


def _format_yaml_value(value: Any) -> str:
    """Format a scalar or list value for YAML front matter."""
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(str(x) for x in value) + "]" if value else "[]"
    return str(value)


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
    formatted = _format_yaml_value(value)
    if key_idx is not None:
        newline = "\n" if lines[key_idx].endswith("\n") else ""
        lines[key_idx] = f"{yaml_key}: {formatted}{newline}"
    else:
        lines.insert(last_content_idx + 1, f"{yaml_key}: {formatted}\n")
    return "".join(lines)


def _split_prompt_comment(first_line: str) -> Optional[Tuple[str, str, str, str]]:
    """Return `(prefix, fields_part, trailer_part, suffix)` for an `<!-- aw-prompt: ... -->` line."""
    m = re.match(r"^(<!--\s*aw-prompt:\s*)(.*?)(\s*-->)\s*$", first_line)
    if not m:
        return None
    prefix, inner, suffix = m.group(1), m.group(2), m.group(3)
    from agent_workflows import prompts as _prompts

    trailer_marker = f" . {_prompts._METADATA_TRAILER}"
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

    Leaves comment-less legacy prompts unchanged (`prompts.inject_metadata_id6` parity)."""
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
        from agent_workflows import prompts as _prompts

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
        comment = (
            f"<!-- aw-prompt: {' | '.join(segs)} . {_prompts._METADATA_TRAILER} -->"
        )
        comment = " ".join(comment.split())
        if not text:
            return comment
        if text.startswith("\n"):
            return comment + text
        return comment + "\n" + text

    if plural == "research":
        if _YAML_FENCE_OPEN_RE.match(text):
            out = text
            for fk, fv in fields.items():
                if fk == "type" or fv is None:
                    continue
                yk = _RESEARCH_YAML_KEY.get(fk)
                if yk is not None:
                    out = _render_yaml_field(out, yk, fv)
            return out
        ordered_yaml = (
            "id",
            "created_day",
            "set",
            "order",
            "research_kind",
            "status",
            "outcome",
            "priority",
            "consumed_by",
            "topic",
            "short_description",
            "model",
            "ace",
        )
        fm_lines = ["---"]
        for fk in ordered_yaml:
            if fk in fields and fields[fk] is not None:
                fm_lines.append(
                    f"{_RESEARCH_YAML_KEY[fk]}: {_format_yaml_value(fields[fk])}"
                )
        fm_lines.append("---")
        fm = "\n".join(fm_lines)
        if not text:
            return fm
        if text.startswith("\n"):
            return fm + text
        return fm + "\n\n" + text

    from agent_workflows import selectors as _sel

    region = _sel.metadata_region(text)
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
        from agent_workflows import prompts as _prompts

        if _prompts.has_metadata_comment(text):
            key_label = _PROMPT_COMMENT_KEY.get(field)
            if key_label is None:
                if field == "order":
                    return text
                raise ValueError(
                    f"legacy writer has no prompt comment key for field {field!r}"
                )
            return _render_prompt_field(text, key_label, value)
        from agent_workflows import selectors as _sel

        region = _sel.metadata_region(text)
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
        val = (
            None if (value is None or (field == "priority" and value == "-")) else value
        )
        return _render_yaml_field(text, _RESEARCH_YAML_KEY[field], val)

    from agent_workflows import backlog as _backlog

    writers = {
        "blocks_release": ("Blocks-Release", _releases.set_blocks_release_line),
        "priority": ("Priority", _releases.set_priority_line),
        "work_kind": ("Work-Kind", _releases.set_work_kind_line),
        "from_backlog": ("From-Backlog", _releases.set_from_backlog_line),
        "from_spec": ("From-Spec", _releases.set_from_spec_line),
        "item_dependencies": (
            "Item-Dependencies",
            _releases.set_item_dependencies_line,
        ),
        "graduated_to": ("Graduated-To", _releases.set_graduated_to_line),
        "release_exempt_kind": (
            "Release-Exempt-Kind",
            _backlog.set_release_exempt_kind_line,
        ),
        "release_exempt_ref": (
            "Release-Exempt-Ref",
            _backlog.set_release_exempt_ref_line,
        ),
    }
    if field in writers:
        wlabel, wfn = writers[field]
        formatted = _format_legacy_value(field, value) if value is not None else "-"
        if value is not None and formatted != "-":
            from agent_workflows import selectors as _sel

            region = _sel.metadata_region(text)
            matches = re.findall(r"(?m)^-\s*" + re.escape(wlabel) + r":", region)
            if len(matches) == 1:
                return _set_bullet(text, wlabel, formatted, anchors=("Status", "Id"))
        return wfn(text, formatted)
    if field == "close_evidence":
        formatted = _format_legacy_value(field, value) if value is not None else "-"
        return _backlog.set_close_evidence_line(text, formatted, repo_root=repo_root)
    label = _LEGACY_BULLET_LABEL.get(field)
    if label is None:
        raise ValueError(f"legacy writer has no bullet form for field {field!r}")
    if value is None:
        if field in _LEGACY_REMOVE_RE:
            pat = _LEGACY_REMOVE_RE[field]
            return "\n".join(ln for ln in text.split("\n") if not pat.match(ln))
        return _set_bullet(text, label, None, anchors=("Status", "Id"))
    anchors = {
        "review_depth": ("Readiness", "Status", "Id"),
        "coverage": ("Readiness", "Status", "Id"),
        "order": ("Set", "Status", "Id"),
    }.get(field, ("Status", "Id"))
    return _set_bullet(text, label, _format_legacy_value(field, value), anchors=anchors)


def _render_checkpoint(text: str, plural: str, fields: Dict[str, Any]) -> str:
    """Render an idempotent `checkpoint` `"id"` (and prompt `"set"`) into legacy metadata.

    On `prompts`, delegates to `prompts.inject_metadata_id6` (leaving comment-less prompts
    untouched). On non-prompts, inserts `- Id:` after `- Status:` else `- Date:` inside the
    metadata region with zero H1/body fallback (`a88210`).
    """
    id_val = fields.get("id")
    set_val = fields.get("set")
    if plural == "prompts":
        if id_val is not None:
            from agent_workflows import prompts as _prompts

            return _prompts.inject_metadata_id6(
                text,
                id6=str(id_val),
                set_id=str(set_val) if set_val is not None else None,
            )
        return text
    if id_val is None:
        return text
    from agent_workflows import selectors as _sel

    region = _sel.metadata_region(text)
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


def _render_history(text: str, entry: str, *, is_prompt: bool) -> str:
    """Prepend a newest-first record under `## Workflow history`, creating the heading if absent.

    D-1: preserves an existing single blank line directly under `## Workflow history` when present
    (inserting after it), and inserts directly under the heading otherwise."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"^##\s*Workflow history\s*$", ln):
            insert_at = i + 2 if (i + 1 < len(lines) and lines[i + 1] == "") else i + 1
            lines.insert(insert_at, entry)
            return "\n".join(lines)
    idx = len(lines)
    if not is_prompt:
        idx = next(
            (i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines)
        )
    lines[idx:idx] = ["## Workflow history", entry, ""]
    return "\n".join(lines)


def render_legacy(
    text: str,
    plural: str,
    events: List[Dict[str, Any]],
    render: LegacyRender,
    *,
    label: str = "",
    repo_root: Optional[Path] = None,
    quiet: bool = True,
) -> Tuple[str, List[str]]:
    """Render ONE append's events into a record's legacy Markdown text. Pure.

    Event order is the append's order; the history line is written last. Returns the rendered text
    (ending in exactly one newline) and the notes the setter prints."""
    notes: List[str] = []
    # Today's setter worked on `text.splitlines()` and re-split after every value writer, so the
    # renderer normalizes the same way (no trailing empty line, CRLF folded) between edits.
    out = "\n".join(text.splitlines())
    trans = next((e for e in events if e.get("op") == "transition"), None)
    mirror = render.status or (trans.get("to") if trans else None)
    if mirror:
        out, n = _render_status(out, plural, mirror, quiet=quiet, label=label)
        notes.extend(n)
    legacy_history_lines: List[str] = []
    for ev in events:
        op = ev["op"]
        if op == "create":
            fields = dict(ev.get("fields") or {})
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
            for fk, fv in fields.items():
                out = "\n".join(
                    _render_field(out, plural, fk, fv, repo_root=repo_root).splitlines()
                )
        elif op == "unset":
            for fk in ev["fields"]:
                out = "\n".join(
                    _render_field(
                        out, plural, fk, None, repo_root=repo_root
                    ).splitlines()
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
            out = _set_bullet(
                out,
                "Coverage-Checked",
                f"{render.day} by {render.actor_label}",
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
    for hline in reversed(legacy_history_lines):
        out = _render_history(out, hline, is_prompt=render.is_prompt)
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
            out = _render_history(out, entry, is_prompt=render.is_prompt)
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
    actor: Optional[Dict[str, Any]],
    by_human: bool,
    overrides: Optional[List[str]],
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
    validate_new_events("", prepared, records_root=records_root)
    return prepared


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
    quiet: bool = True,
    label: str = "",
) -> str:
    """Validate and render ``events`` over an in-memory legacy string without file I/O.

    Runs ``validate_new_events`` and ``_check_owned_fields`` before rendering through the same
    ``render_legacy`` primitives used by :func:`write_legacy`."""
    reg_type, plural = _normalize_legacy_types(record_type)
    rroot = Path(repo_root) if repo_root is not None else Path.cwd()
    records_root = Path(_proj_ctx.project_records_dir(rroot))
    prepared = _prepare_legacy_events(
        reg_type,
        events,
        records_root=records_root,
        actor=actor,
        by_human=by_human,
        overrides=overrides,
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
    pre_history = set(_plan_read.history_block(pre_pass_text or "").records)

    out = "\n".join((current_text or "").splitlines())
    from agent_workflows import selectors as _sel

    if re.search(r"(?m)^-\s*Status\s*:", _sel.metadata_region(out)):
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
    actor: Optional[Dict[str, Any]] = None,
    by_human: bool = False,
    overrides: Optional[List[str]] = None,
    sidecar: Optional[SidecarRecord] = None,
    quiet: bool = True,
    from_status: Optional[str] = None,
    notes_out: Optional[List[str]] = None,
    initial_text: Optional[str] = None,
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
    else:
        rroot = _proj_ctx.record_git_root(ltarget.path) or _core.repo_root_of(
            ltarget.path
        )

    ctx = project_context or legacy_context(rroot)
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])
    reg_type, plural = _normalize_legacy_types(r_type, ltarget.path, records_root)

    prepared = _prepare_legacy_events(
        reg_type,
        events,
        records_root=records_root,
        actor=actor,
        by_human=by_human,
        overrides=overrides,
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
    if src.is_file():
        text = src.read_text(encoding="utf-8")
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
    )
    if notes_out is not None:
        notes_out.extend(notes)
    dest = Path(destination) if destination is not None else src
    moving = dest.resolve() != src.resolve()
    preview = WritePreview(
        text=rendered,
        destination=dest,
        source=src,
        changed=moving or (not src.is_file()) or rendered != text,
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
        _core.atomic_write(dest, rendered)
        if moving and src.exists():
            with contextlib.suppress(OSError):
                src.unlink()
        if sidecar is not None:
            sid = ltarget.id6
            if not sid:
                from agent_workflows import selectors as _sel

                sid = _sel.read_front_matter_id(rendered)
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
                target = LegacyTarget(records_root / rel, plural, target)
            if legacy_render is None:
                raise ValueError("a legacy-format append requires legacy_render")
            repo_root = (
                legacy_kwargs.pop("repo_root", None)
                or getattr(ctx, "repo_root", None)
                or records_root.parent.parent
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
            migration_import=migration_import,
        )

        # Dry run check
        if dry_run:
            return {"committed": False, "dry_run": True, "events": prepared_events}

        # Step 1: Write log via temp file, fsync, os.replace (THE COMMIT POINT)
        all_lines = existing_lines + [encode_event(e) for e in prepared_events]
        log_content = "".join(all_lines)
        try:
            _atomic_replace_fsync(log_path, log_content)
        except Exception as exc:
            return {"committed": False, "error": f"no change; write failed: {exc}"}

        # After step 1: Change is recorded. Subsequent steps are best effort/recovery
        try:
            # Replay full log to get current state
            state, _, _, _ = replay(id6, art_type, all_lines, records_root=records_root)

            # Step 2: In-file mirror
            if state.path:
                art_abs_p = records_root / state.path
                if art_abs_p.exists():
                    txt = art_abs_p.read_text(encoding="utf-8")
                    if art_type == "walkthrough":
                        new_txt = (
                            f"---\nid: {id6}\n---\n" + txt.split("---\n", 2)[-1]
                            if "---" in txt
                            else f"---\nid: {id6}\n---\n" + txt
                        )
                    elif art_type == "prompt" and txt.startswith("<!--"):
                        new_txt = re.sub(
                            r"status:\s*\S+",
                            f"status: {state.status}",
                            txt,
                            count=1,
                        )
                    else:
                        new_fm = f"---\nid: {id6}\nstatus: {state.status}\n---\n"
                        new_txt = (
                            new_fm + txt.split("---\n", 2)[-1]
                            if "---" in txt
                            else new_fm + txt
                        )
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
    destination: Optional[str] = None,
    dry_run: bool = False,
    project_context: Any = None,
    actor: Optional[Dict[str, Any]] = None,
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
            dest_path = (
                Path(destination)
                if Path(destination).is_absolute()
                else (records_root / destination)
            )
            _, plural = _normalize_legacy_types(artifact_type, dest_path, records_root)
            source_digest = legacy_kwargs.pop("source_digest", None)
            repo_root = (
                legacy_kwargs.pop("repo_root", None)
                or getattr(ctx, "repo_root", None)
                or records_root.parent.parent
            )
            create_ev: Dict[str, Any] = {
                "op": "create",
                "path": str(destination).replace("\\", "/"),
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
                initial_text=body,
                **legacy_kwargs,
            )

    ctx = project_context or _proj_ctx.resolve_project_context()
    records_root = Path(ctx.logical_roots["records"])
    state_root = Path(ctx.logical_roots["state"])

    if not destination:
        destination = f"{artifact_type}s/pending/{id6}.md"

    # Retain operation journal before step 1
    j_dir = _journal_dir(state_root)
    j_file = j_dir / f"{id6}.json"
    journal_data = {
        "op": "create",
        "id6": id6,
        "type": artifact_type,
        "destination": destination,
        "body": body,
    }
    j_file.write_text(json.dumps(journal_data, indent=2), encoding="utf-8")

    try:
        # Create event
        create_ev = {
            "op": "create",
            "path": destination,
            "fields": {**fields, "id": id6, "type": artifact_type},
        }
        res = append(
            id6,
            [create_ev],
            expect_seq=0,
            dry_run=dry_run,
            project_context=ctx,
            actor=actor,
            _from_create=True,
        )

        if dry_run or not res.get("committed"):
            j_file.unlink(missing_ok=True)
            return res

        # Materialize artifact body
        dest_path = records_root / destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        mirror_prefix = (
            f"---\nid: {id6}\nstatus: {fields.get('status', 'draft')}\n---\n"
        )
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
                dest_path = records_root / dest
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
            p = records_root / state.path
            if p.exists():
                txt = p.read_text(encoding="utf-8")
                mirror_prefix = f"---\nid: {id6}\nstatus: {state.status}\n---\n"
                new_txt = (
                    mirror_prefix + txt.split("---\n", 2)[-1]
                    if "---" in txt
                    else mirror_prefix + txt
                )
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
            )
        finally:
            conn.close()

        return {"repaired": True, "status": state.status, "seq": state.last_seq}
