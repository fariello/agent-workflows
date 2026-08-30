"""Canonical IPD structural schema: the single source of truth for the IPD contract.

This module OWNS the machine-checkable IPD structural contract defined by the specification
``.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md``. The linter (Order 02),
the authoring tools (Order 03), the templates + ``ipd-spec`` (Order 04), and the review/lifecycle
integration (Order 05) all derive from or are checked against THIS module so the structural
contract cannot fork or drift.

Scope (Set ``ipd-structure`` Order 01): definitions + pure validation helpers ONLY. This module has
no side effects: it does not read the filesystem, call a model, use the network, or write anything.
It is stdlib-only (zero runtime dependencies, D46) and Python 3.9 compatible.

Readiness vocabulary is NOT re-defined here; it is imported from ``agent_workflows.plans`` (the
existing single source of truth, D52/D65) so the two can never diverge.
"""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import backlog as _backlog
from agent_workflows import plans as _plans

# --------------------------------------------------------------------------------------
# Plan kinds
# --------------------------------------------------------------------------------------

KIND_CHILD = "child"
KIND_ORCHESTRATOR = "orchestrator"
KINDS: FrozenSet[str] = frozenset((KIND_CHILD, KIND_ORCHESTRATOR))

# --------------------------------------------------------------------------------------
# H2 heading orders per kind (spec Section 4.3), using the LIVE template heading names
# (verified 2026-08-03 against .agents/workflows/assess/templates/ipd.md): bare "## Findings",
# "## Deferred / out of scope (with reason)", and "## Project conventions discovered (Step 0)".
# In BOTH kinds the execution checklist is the H2 immediately after "## Goal" and the validation
# checklist is the H2 immediately before "## Approval and execution gate" (spec Section 4.2).
# --------------------------------------------------------------------------------------

H_WORKFLOW_HISTORY = "Workflow history"
H_GOAL = "Goal"
H_EXECUTION = "Detailed Implementation Checklist (TODO)"
H_PROJECT_CONVENTIONS = "Project conventions discovered (Step 0)"
H_FINDINGS = "Findings"
H_PROPOSED = "Proposed changes (ordered, validatable)"
H_DEFERRED = "Deferred / out of scope (with reason)"
H_SCOPE_CHECK = "Scope check"
H_REQUIRED_TESTS = "Required tests / validation"
H_SPEC_SYNC = "Spec / documentation sync"
H_OPEN_QUESTIONS = "Open questions"
H_VALIDATION_CHILD = "Validation and cross-check (verify before reporting done)"
H_VALIDATION_ORCH = (
    "Validation and cross-check (verify before reporting the Set complete)"
)
H_APPROVAL_GATE = "Approval and execution gate"
# Orchestrator-only headings:
H_CHILD_IPDS = "Child IPDs, sequence, and dependencies"
H_COMPLETION = "Completion criteria (the whole Set is done only when)"
H_CROSS_IPD = "Cross-IPD validation"

CHILD_H2_ORDER: Tuple[str, ...] = (
    H_WORKFLOW_HISTORY,
    H_GOAL,
    H_EXECUTION,
    H_PROJECT_CONVENTIONS,
    H_FINDINGS,
    H_PROPOSED,
    H_DEFERRED,
    H_SCOPE_CHECK,
    H_REQUIRED_TESTS,
    H_SPEC_SYNC,
    H_OPEN_QUESTIONS,
    H_VALIDATION_CHILD,
    H_APPROVAL_GATE,
)

ORCHESTRATOR_H2_ORDER: Tuple[str, ...] = (
    H_WORKFLOW_HISTORY,
    H_GOAL,
    H_EXECUTION,
    H_CHILD_IPDS,
    H_COMPLETION,
    H_CROSS_IPD,
    H_DEFERRED,
    H_SCOPE_CHECK,
    H_REQUIRED_TESTS,
    H_OPEN_QUESTIONS,
    H_VALIDATION_ORCH,
    H_APPROVAL_GATE,
)

H2_ORDER_BY_KIND: Dict[str, Tuple[str, ...]] = {
    KIND_CHILD: CHILD_H2_ORDER,
    KIND_ORCHESTRATOR: ORCHESTRATOR_H2_ORDER,
}

# The validation heading text differs by kind (kind-specific, spec Section 4.3).
VALIDATION_HEADING_BY_KIND: Dict[str, str] = {
    KIND_CHILD: H_VALIDATION_CHILD,
    KIND_ORCHESTRATOR: H_VALIDATION_ORCH,
}


def execution_follows_goal(kind: str) -> bool:
    """True when the schema places the execution checklist as the H2 immediately after Goal.

    True for both kinds (spec Section 4.2). Encoded as a helper so the linter reads the rule from
    the schema rather than restating it.
    """
    order = H2_ORDER_BY_KIND[kind]
    return order.index(H_EXECUTION) == order.index(H_GOAL) + 1


def validation_precedes_gate(kind: str) -> bool:
    """True when the validation checklist is the H2 immediately before the approval gate."""
    order = H2_ORDER_BY_KIND[kind]
    return (
        order.index(VALIDATION_HEADING_BY_KIND[kind])
        == order.index(H_APPROVAL_GATE) - 1
    )


# --------------------------------------------------------------------------------------
# Metadata block (spec Section 4.4). Bullet "- Field: value" lines after the H1, NOT YAML.
# --------------------------------------------------------------------------------------

META_REQUIRED: Tuple[str, ...] = (
    "Date",
    "Kind",
    "Concern",
    "Scope",
    "Status",
    "Author",
    "Id",
)
# Fields REQUIRED together (all-or-none groups):
META_PAIRED_SET_ORDER: Tuple[str, ...] = ("Set", "Order")
META_QUARANTINE_TRIO: Tuple[str, ...] = (
    "Quarantine",
    "Quarantine owner",
    "Quarantine follow-up",
)
META_WATERMARK = "Highest E allocated"
META_APPROVAL = "Approval"
# Scope-Paths (Order oorry1): a machine-readable allowlist of the repo-relative paths a plan may
# change, so a later finalize transaction (Order v7e88a) can compare declared vs actually-changed
# paths. Recognized-but-OPTIONAL: it is NOT in META_REQUIRED (adding it there would fail every
# existing pending plan at the always-on `author` metadata check and defeat the grandfather
# guarantee). Its requirement is CONDITIONAL and lives in the checkpoint layer (ipd_lint,
# check_checkpoint) at the ready-to-execute gate, not here.
META_SCOPE_PATHS = "Scope-Paths"
# The reserved sentinel value that grandfathers a pre-cutoff plan (OQ-01): a plan carrying
# `Scope-Paths: grandfathered` is advisory-satisfied at the gate (non-blocking) instead of
# declaring a real allowlist. It is stored IN the plan's metadata block so it travels with the plan.
SCOPE_PATHS_GRANDFATHERED = "grandfathered"
# Item-Dependencies (Order g69y23, ipddeps Set; spec 25kzda 2.7): the machine-readable, id6-grounded
# statement of a plan's CROSS-IPD prerequisites - a DIFFERENT layer from the intra-plan `Depends on:`
# E-item field (`parse_depends_on`), which orders steps WITHIN one plan. Recognized-but-OPTIONAL at
# the schema layer (NOT in META_REQUIRED, mirroring META_SCOPE_PATHS / META_BLOCKS_RELEASE /
# META_FROM_BACKLOG): recognition here only stops the IPD-M103 "unknown field" lint error so existing
# plans are not mass-failed (the grandfather guarantee). Its CONDITIONAL mandatoriness, edge-target
# resolution, and the DAG (dangling / cycle / ambiguity) live in child 02's shared predicate + the
# phased `aw ipd lint` / `aw check` rules, NOT here. Positioned immediately after `Scope-Paths`
# (spec 2.7). The canonical field position for the write primitive is enforced in
# `releases.set_item_dependencies_line` (Order g69y23 E-02).
META_ITEM_DEPENDENCIES = "Item-Dependencies"
# The reserved scaffold sentinel: a freshly scaffolded plan carries `Item-Dependencies: unresolved`
# (never blank, never `none`) so a not-yet-triaged plan is an HONEST not-ready draft. `unresolved`
# parses as "declared-but-not-ready" (outside the execution edge grammar): it is a legal, recognized
# value that child 02's ready-to-execute gate treats as unsatisfied, distinct from `none` (an
# explicit assertion of zero dependencies).
ITEM_DEPENDENCIES_UNRESOLVED = "unresolved"
# The explicit "no cross-IPD prerequisites" value (distinct from the `unresolved` scaffold sentinel).
ITEM_DEPENDENCIES_NONE = "none"
# Blocks-Release (Order si3mmt): an optional, single-valued release-gate field (a release id6 or the
# sentinel `next`) declaring that this plan must be done before that release ships, matching the
# semantics the field already has on backlog items and specs (AGENTS.md "Release gates"). Recognized
# but OPTIONAL (NOT in META_REQUIRED), mirroring META_SCOPE_PATHS: recognition here only stops the
# IPD-M103 "unknown field" lint error; value validation (does the target resolve to a release
# record) lives in the `aw check` surface (child 03), not the schema layer.
META_BLOCKS_RELEASE = "Blocks-Release"
# From-Backlog (Order ku93tn): an optional, single-valued link field naming the backlog item id6
# this plan graduated from, so the backlog->plan graduation relationship is machine-readable (the
# bklggrad close-legitimacy predicate in child 02 consumes it to confirm a blocking backlog item's
# release gate was handed off to a plan). Recognized but OPTIONAL (NOT in META_REQUIRED), mirroring
# META_SCOPE_PATHS/META_BLOCKS_RELEASE: recognition here only stops the IPD-M103 "unknown field"
# lint error; value validation (does the target resolve to a backlog item id6) lives in the
# `aw check` surface (check.from-backlog-dangling), not the schema layer.
META_FROM_BACKLOG = "From-Backlog"
# xprio Order 1b45el (graduated from backlog p9o1oo): a UNIFORM, recognized-but-OPTIONAL `Priority`
# field (the shared low/medium/high vocab is backlog.PRIORITIES; do NOT fork it). Recognition here
# only stops the IPD-M103 "unknown field" lint error; the ENUM value check lives in the `aw check`
# surface (check.priority-invalid), NOT the schema layer, mirroring Scope-Paths/Blocks-Release/
# From-Backlog. Absent = unprioritized (no forced default; existing plans are not mass-failed).
META_PRIORITY = "Priority"
# The full set of recognized field names (unknown fields are errors for new IPDs).
META_RECOGNIZED: FrozenSet[str] = frozenset(
    META_REQUIRED
    + META_PAIRED_SET_ORDER
    + META_QUARANTINE_TRIO
    + (
        META_WATERMARK,
        META_APPROVAL,
        META_SCOPE_PATHS,
        META_ITEM_DEPENDENCIES,
        META_BLOCKS_RELEASE,
        META_FROM_BACKLOG,
        META_PRIORITY,
    )
)

# Readiness vocabulary imported from the existing single source of truth (no fork).
PRE_TERMINAL: Tuple[str, ...] = tuple(_plans.PRE_TERMINAL)
TERMINAL: Tuple[str, ...] = tuple(_plans.TERMINAL)
STANDING: Tuple[str, ...] = tuple(_plans.STANDING)
RECOGNIZED_STATUS: FrozenSet[str] = frozenset(_plans.RECOGNIZED)
# Statuses that require (and only they may carry) an Approval field.
APPROVAL_STATUSES: FrozenSet[str] = frozenset(("approved",))
# `auto-approved` is a sibling ready-to-execute tier (D65); it records an automated clear, NOT human
# approval, so it does NOT require the human `Approval` field.
READY_TO_EXECUTE: FrozenSet[str] = frozenset(("approved", "auto-approved"))

_META_LINE_RE = re.compile(r"^- (?P<field>[A-Za-z][A-Za-z /-]*?):\s?(?P<value>.*)$")


class MetaError(NamedTuple):
    field: str
    message: str


def parse_metadata_block(
    lines: Sequence[str],
) -> Tuple[Dict[str, str], List[MetaError]]:
    """Parse the contiguous ``- Field: value`` run given the lines BETWEEN the H1 and the first H2.

    Returns (fields, errors). Duplicate fields and unknown fields are recorded as errors. Pure;
    the caller is responsible for locating the block (the parser in Order 02 supplies the slice).
    """
    fields: Dict[str, str] = {}
    errors: List[MetaError] = []
    seen: Dict[str, int] = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        m = _META_LINE_RE.match(line)
        if not m:
            # A non-bullet, non-blank line inside the metadata run ends the block for our purposes.
            continue
        field = m.group("field").strip()
        value = m.group("value").strip()
        seen[field] = seen.get(field, 0) + 1
        if seen[field] == 2:
            errors.append(MetaError(field, "duplicate field"))
        if field not in META_RECOGNIZED:
            errors.append(MetaError(field, "unknown field"))
        # First occurrence wins for the value map; duplicates already flagged.
        fields.setdefault(field, value)
    return fields, errors


def validate_metadata(
    fields: Dict[str, str], *, directory: Optional[str] = None
) -> List[MetaError]:
    """Validate a parsed metadata field map against the spec Section 4.4 contract.

    ``directory`` is the plan's disposition directory name (e.g. ``pending``, ``executed``) when
    known, used for the path/status combination checks; pass None to skip those.
    """
    errors: List[MetaError] = []
    # Required fields present.
    for req in META_REQUIRED:
        if req not in fields:
            errors.append(MetaError(req, "required field missing"))

    kind = fields.get("Kind")
    if kind is not None and kind not in KINDS:
        errors.append(
            MetaError("Kind", "unknown kind (expected child or orchestrator)")
        )

    status = fields.get("Status")
    if status is not None and status not in RECOGNIZED_STATUS:
        errors.append(MetaError("Status", "unrecognized readiness status"))

    # Id: the stable plan citation handle (6-char base36 lowercase, from the shared core).
    plan_id = fields.get("Id")
    if plan_id is not None and not _core.is_valid_id6(plan_id.strip()):
        errors.append(MetaError("Id", "Id must be a 6-char base36-lowercase token"))

    # Set/Order pairing + Order rules.
    has_set = "Set" in fields
    has_order = "Order" in fields
    if has_set != has_order:
        errors.append(MetaError("Set/Order", "Set and Order are required together"))
    if has_order:
        order_raw = fields.get("Order", "").strip()
        try:
            order_val: Optional[int] = int(order_raw)
        except ValueError:
            order_val = None
            errors.append(MetaError("Order", "Order must be an integer"))
        if order_val is not None and kind == KIND_ORCHESTRATOR and order_val != 0:
            errors.append(MetaError("Order", "orchestrator Order must be 0"))
        if order_val is not None and kind == KIND_CHILD and order_val < 1:
            errors.append(MetaError("Order", "child Order must be an integer >= 1"))

    # Approval iff Status is approved (auto-approved does NOT carry human Approval).
    has_approval = META_APPROVAL in fields
    if status == "approved" and not has_approval:
        errors.append(
            MetaError(META_APPROVAL, "Approval is required when Status is approved")
        )
    if status != "approved" and has_approval:
        errors.append(
            MetaError(
                META_APPROVAL, "Approval must be absent unless Status is approved"
            )
        )

    # Quarantine trio: all-or-none, nonterminal only.
    present_q = [f for f in META_QUARANTINE_TRIO if f in fields]
    if present_q and len(present_q) != len(META_QUARANTINE_TRIO):
        errors.append(
            MetaError(
                "Quarantine",
                "Quarantine, Quarantine owner, and Quarantine follow-up are required together",
            )
        )
    if present_q and status is not None and status in TERMINAL:
        errors.append(
            MetaError("Quarantine", "only nonterminal plans may be quarantined")
        )

    # Path/status combination (when directory known).
    if status is not None and directory is not None:
        errors.extend(_check_path_status(status, directory))

    return errors


def _check_path_status(status: str, directory: str) -> List[MetaError]:
    errors: List[MetaError] = []
    if status in TERMINAL:
        # For terminal statuses the disposition directory name equals the status
        # (executed/superseded/not-executed); `done` is an accepted alias handled upstream.
        if directory != status:
            errors.append(
                MetaError(
                    "Status",
                    "terminal Status must live in the matching terminal directory",
                )
            )
    elif status in STANDING:
        if directory != "reusable":
            errors.append(
                MetaError(
                    "Status", "reusable Status must live in the reusable directory"
                )
            )
    else:  # pre-terminal
        if directory not in ("pending", ""):
            errors.append(
                MetaError("Status", "pre-terminal Status must live under pending/")
            )
    return errors


# --------------------------------------------------------------------------------------
# Scope-Paths allowlist grammar (Order oorry1)
# --------------------------------------------------------------------------------------
#
# A plan's `Scope-Paths` value is EITHER the reserved sentinel `grandfathered` OR a
# comma-separated allowlist of repo-relative literal paths / bounded pathspecs the plan may
# change. The grammar is deliberately conservative so a later finalize transaction can compare
# it against the real changed paths without ambiguity:
#
#   * repo-relative only: an absolute path (leading `/`) or a Windows drive/UNC path is rejected;
#   * no parent escape: any `..` path segment is rejected (a plan cannot scope outside the repo);
#   * no repo-wide blast radius: a bare `*`/`**`, a root-level `**`/`*` (e.g. `**`, `**/x`,
#     `*.py` at the root, `*`), or the repo root `.`/`/` is rejected;
#   * a directory-bounded pathspec IS allowed (e.g. `tests/`, `agent_workflows/**`,
#     `agent_workflows/*.py`, `docs/**/*.md`) because its blast radius is bounded by a leading
#     concrete directory segment;
#   * the plan's OWN lifecycle artifacts are IMPLICIT and need not be listed: the plan file
#     itself under `.aw/records/plans/**` and its manifest/index refresh
#     (`.aw/records/plans/INDEX.md`, `.aw/records/**/index.md`) are always allowed (see
#     `scope_paths_implicit_allowances`);
#   * a GENERATED file that a plan produces MUST be declared like any other path (there is no
#     implicit generated-file exception beyond the lifecycle artifacts above).
#
# `grandfathered` is a whole-value sentinel: it may not be mixed with real entries.

# Repo-relative lifecycle artifacts every plan may touch without declaring them.
SCOPE_PATHS_IMPLICIT_ALLOWANCES: Tuple[str, ...] = (
    ".aw/records/plans/**",  # the plan file itself moving through the lifecycle
    ".aw/records/plans/INDEX.md",  # the plans index refresh
    ".aw/records/**/index.md",  # a records-tree manifest/index refresh
)

# A path SEGMENT that is a bare repo-wide glob (rejected at the ROOT position only).
_SCOPE_ROOT_GLOB_SEGMENTS: FrozenSet[str] = frozenset(("*", "**"))
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def scope_paths_implicit_allowances() -> Tuple[str, ...]:
    """Return the repo-relative lifecycle-artifact pathspecs every plan may touch implicitly."""
    return SCOPE_PATHS_IMPLICIT_ALLOWANCES


def _scope_path_entry_error(entry: str) -> Optional[str]:
    """Validate ONE Scope-Paths allowlist entry (not the `grandfathered` sentinel).

    Returns an error string, or None when the entry is a legal repo-relative literal path or
    bounded pathspec. Pure; performs no filesystem access.
    """
    raw = entry.strip()
    if not raw:
        return "empty path entry"
    # Reject absolute / drive / UNC paths.
    if raw.startswith("/") or raw.startswith("\\"):
        return "absolute paths are not allowed (use a repo-relative path): {0}".format(
            raw
        )
    if _WINDOWS_DRIVE_RE.match(raw):
        return "absolute paths are not allowed (use a repo-relative path): {0}".format(
            raw
        )
    # Normalize separators for segment analysis (a stored pathspec may use `/`).
    norm = raw.replace("\\", "/")
    if norm in (".", "./", "/"):
        return "the repo root is too broad to be a scope path: {0}".format(raw)
    segments = [seg for seg in norm.split("/") if seg != ""]
    if not segments:
        return "empty path entry"
    # No parent escape anywhere in the path.
    if any(seg == ".." for seg in segments):
        return "parent-directory escape ('..') is not allowed: {0}".format(raw)
    # No repo-wide blast radius at the ROOT position (first segment). A `**`/`*` deeper in the
    # path is bounded by the concrete leading directory and is allowed.
    if segments[0] in _SCOPE_ROOT_GLOB_SEGMENTS:
        return "repo-wide glob is too broad (bound it under a directory): {0}".format(
            raw
        )
    # A root-level filename glob (e.g. `*.py`, `*.md` at the repo root) is also too broad.
    if len(segments) == 1 and "*" in segments[0]:
        return "root-level glob is too broad (bound it under a directory): {0}".format(
            raw
        )
    return None


def parse_scope_paths(value: str) -> Tuple[List[str], bool, List[str]]:
    """Parse a `Scope-Paths` metadata value.

    Returns ``(paths, is_grandfathered, errors)`` where ``paths`` is the list of declared
    allowlist entries (empty when grandfathered), ``is_grandfathered`` is True iff the value is
    exactly the reserved sentinel, and ``errors`` lists grammar violations. Pure.
    """
    v = value.strip()
    if v == SCOPE_PATHS_GRANDFATHERED:
        return [], True, []
    if v == "":
        return [], False, ["Scope-Paths must not be empty"]
    entries = [tok.strip() for tok in v.split(",")]
    errors: List[str] = []
    # The sentinel may not be mixed with real entries.
    if any(tok == SCOPE_PATHS_GRANDFATHERED for tok in entries):
        errors.append(
            "the 'grandfathered' sentinel must be the whole Scope-Paths value, not one entry"
        )
    paths = [tok for tok in entries if tok]
    if not paths:
        errors.append("Scope-Paths must list at least one path")
    for entry in paths:
        if entry == SCOPE_PATHS_GRANDFATHERED:
            continue
        err = _scope_path_entry_error(entry)
        if err:
            errors.append(err)
    return paths, False, errors


# --------------------------------------------------------------------------------------
# Item-Dependencies grammar (Order g69y23, ipddeps Set; spec 25kzda 2.7-2.8)
# --------------------------------------------------------------------------------------
#
# A whole-plan, id6-grounded statement of CROSS-IPD prerequisites. The value is one of:
#   * `none`        - an explicit assertion of zero cross-IPD dependencies (parses to []).
#   * `unresolved`  - the reserved scaffold sentinel: declared-but-not-ready (parses to [] with
#                     ``ready=False``; a legal recognized value, NOT an execution edge).
#   * a comma-separated list of typed edges, each one of:
#         executed:<id6>              (target is an IPD that must be in the executed state)
#         exists:<type>:<id6>         (target of <type> must simply exist)
#         state:<type>:<status>:<id6> (target of <type> must be in <status>)
#     where <type> in {ipd, spec, backlog}. `state:ipd:executed:<id6>` is ILLEGAL and must be
#     written as `executed:<id6>` (so the "must be executed" edge has ONE canonical spelling).
#
# This parser validates SYNTAX only (Order g69y23 scope). Edge-target RESOLUTION (does the id6
# name a real artifact) and the DAG (dangling / cycle / ambiguity) live in child 02's shared
# predicate. Kept deliberately disjoint from the intra-plan `parse_depends_on` (E-ids): an E-id is
# never a legal Item-Dependencies token, and an id6 is never a legal `Depends on:` token.

ITEM_DEP_TYPES: Tuple[str, ...] = ("ipd", "spec", "backlog")
# Valid target statuses per type (used only to reject an obviously wrong pairing at the syntax
# layer; the authoritative status vocabulary lives in the plans/specs/backlog modules and is
# re-checked at resolution time by child 02). `ipd` deliberately omits `executed` here because
# `state:ipd:executed:` is redirected to the canonical `executed:` edge.
_ITEM_DEP_STATE_STATUSES: Dict[str, FrozenSet[str]] = {
    "ipd": frozenset(
        ("draft", "to-review", "reviewed", "approved", "auto-approved", "reusable")
    ),
    "spec": frozenset(
        (
            "draft",
            "to-review",
            "reviewed",
            "approved",
            "implementing",
            "implemented",
            "deferred",
            "parked",
            "superseded",
        )
    ),
    # bklgrad Order 01 (v58bvy) E-08: DERIVED from `backlog.STATUSES`, never re-listed. A second
    # hardcoded copy here is what made `state:backlog:graduated:<id6>` unparseable when `graduated`
    # was added to the backlog vocabulary, so the two sets are now provably identical by construction
    # (GUIDING_PRINCIPLES P8) and a future status addition cannot silently desync this gate.
    "backlog": _backlog.STATUSES,
}
# Kind rank for canonical ordering: executed < exists < state, then type, then status, then id6.
_ITEM_DEP_KIND_RANK: Dict[str, int] = {"executed": 0, "exists": 1, "state": 2}


class ItemDependency(NamedTuple):
    """One parsed cross-IPD dependency edge.

    ``kind`` is ``executed`` | ``exists`` | ``state``. ``target_type`` is the artifact type
    (``ipd``/``spec``/``backlog``; always ``ipd`` for an ``executed`` edge). ``status`` is the
    required status for a ``state`` edge (else None). ``id6`` is the target's stable handle.
    """

    kind: str
    target_type: str
    status: Optional[str]
    id6: str

    def canonical(self) -> str:
        """Render this edge back to its canonical token form."""
        if self.kind == "executed":
            return "executed:{0}".format(self.id6)
        if self.kind == "exists":
            return "exists:{0}:{1}".format(self.target_type, self.id6)
        return "state:{0}:{1}:{2}".format(self.target_type, self.status, self.id6)

    def _sort_key(self) -> Tuple[int, str, str, str]:
        return (
            _ITEM_DEP_KIND_RANK.get(self.kind, 99),
            self.target_type,
            self.status or "",
            self.id6,
        )


def _parse_item_dependency_edge(
    tok: str,
) -> Tuple[Optional[ItemDependency], Optional[str]]:
    """Parse ONE edge token. Returns (edge, error). Pure."""
    parts = tok.split(":")
    kind = parts[0]
    if kind == "executed":
        if len(parts) != 2:
            return None, "executed edge must be 'executed:<id6>' in {0!r}".format(tok)
        id6 = parts[1]
        if not _core.is_valid_id6(id6):
            return None, "executed target {0!r} is not a 6-char base36 id6".format(id6)
        return ItemDependency("executed", "ipd", None, id6), None
    if kind == "exists":
        if len(parts) != 3:
            return None, "exists edge must be 'exists:<type>:<id6>' in {0!r}".format(
                tok
            )
        target_type, id6 = parts[1], parts[2]
        if target_type not in ITEM_DEP_TYPES:
            return None, "exists edge type {0!r} must be one of {1} in {2!r}".format(
                target_type, list(ITEM_DEP_TYPES), tok
            )
        if not _core.is_valid_id6(id6):
            return None, "exists target {0!r} is not a 6-char base36 id6".format(id6)
        return ItemDependency("exists", target_type, None, id6), None
    if kind == "state":
        if len(parts) != 4:
            return (
                None,
                "state edge must be 'state:<type>:<status>:<id6>' in {0!r}".format(tok),
            )
        target_type, status, id6 = parts[1], parts[2], parts[3]
        if target_type not in ITEM_DEP_TYPES:
            return None, "state edge type {0!r} must be one of {1} in {2!r}".format(
                target_type, list(ITEM_DEP_TYPES), tok
            )
        if target_type == "ipd" and status == "executed":
            return (
                None,
                "state:ipd:executed:<id6> is illegal; use the canonical 'executed:<id6>' "
                "edge in {0!r}".format(tok),
            )
        if status not in _ITEM_DEP_STATE_STATUSES.get(target_type, frozenset()):
            return (
                None,
                "state edge status {0!r} is not valid for type {1!r} in {2!r}".format(
                    status, target_type, tok
                ),
            )
        if not _core.is_valid_id6(id6):
            return None, "state target {0!r} is not a 6-char base36 id6".format(id6)
        return ItemDependency("state", target_type, status, id6), None
    if E_ID_STRICT.match(tok):
        return (
            None,
            "{0!r} is an E-* id (intra-plan 'Depends on:'), not a cross-IPD "
            "Item-Dependencies edge".format(tok),
        )
    return (
        None,
        "unrecognized Item-Dependencies edge {0!r} (expected "
        "executed:/exists:/state:)".format(tok),
    )


def parse_item_dependencies(
    value: str,
) -> Tuple[List[ItemDependency], bool, Optional[str]]:
    """Parse an `Item-Dependencies` metadata value (spec 25kzda 2.7).

    Returns ``(edges, ready, error)``:
      * ``edges``  - the parsed edges in CANONICAL order (empty for `none`/`unresolved`/empty).
      * ``ready``  - False iff the value is the `unresolved` scaffold sentinel (or an error);
                     True for `none` and for any well-formed edge list.
      * ``error``  - a specific message for the FIRST violation, else None.

    Rejects: a self-edge is NOT detectable here (the parser does not know the plan's own id6 -
    that check lives in child 02's resolver, which has the owning plan). This function rejects
    duplicate edges, `none`/`unresolved` mixed with edges, malformed tokens, bad type/status
    pairings, E-ids, and `state:ipd:executed:`. Pure.
    """
    v = value.strip()
    if v == "":
        # An empty value is treated as an explicit `none` for tolerance, but is NOT ready-blocking.
        return [], True, None
    if v == ITEM_DEPENDENCIES_UNRESOLVED:
        return [], False, None
    if v == ITEM_DEPENDENCIES_NONE:
        return [], True, None
    tokens = [tok.strip() for tok in v.split(",")]
    # A sentinel may not be mixed with real edges.
    if any(tok == ITEM_DEPENDENCIES_NONE for tok in tokens):
        return (
            [],
            True,
            "'none' must be the whole Item-Dependencies value, not one edge",
        )
    if any(tok == ITEM_DEPENDENCIES_UNRESOLVED for tok in tokens):
        return (
            [],
            False,
            "'unresolved' must be the whole Item-Dependencies value, not one edge",
        )
    edges: List[ItemDependency] = []
    seen: set = set()
    for tok in tokens:
        if not tok:
            return [], True, "empty Item-Dependencies edge (stray comma)"
        edge, err = _parse_item_dependency_edge(tok)
        if err:
            return [], True, err
        assert edge is not None
        canon = edge.canonical()
        if canon in seen:
            return [], True, "duplicate Item-Dependencies edge {0!r}".format(canon)
        seen.add(canon)
        edges.append(edge)
    edges.sort(key=lambda e: e._sort_key())
    return edges, True, None


def canonical_item_dependencies(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (canonical_value, error) for an `Item-Dependencies` input.

    The canonical value is `none`, `unresolved`, or the canonically-ordered comma+space-joined
    edge list. On error, returns (None, error). Used by the `aw ipd dependencies set` setter to
    normalize before writing. Pure.
    """
    edges, ready, err = parse_item_dependencies(value)
    if err:
        return None, err
    v = value.strip()
    if v == ITEM_DEPENDENCIES_UNRESOLVED:
        return ITEM_DEPENDENCIES_UNRESOLVED, None
    if not edges:
        return ITEM_DEPENDENCIES_NONE, None
    return ", ".join(e.canonical() for e in edges), None


# --------------------------------------------------------------------------------------
# Cross-IPD dependency RULE FAMILY (ipddeps Order ovbnyq; spec 25kzda 2.9-2.11).
# One shared rule-id vocabulary consumed by the check_engine evaluator, phased ipd lint, and the
# child-03 hook, so the surfaces cannot diverge.
# --------------------------------------------------------------------------------------

RULE_IPD_DEP_MISSING = "check.ipd-missing-dependency-statement"
RULE_IPD_DEP_UNRESOLVED = "check.ipd-dependency-unresolved"
RULE_IPD_DEP_MALFORMED = "check.ipd-dependency-malformed"
RULE_IPD_DEP_DANGLING = "check.ipd-dependency-dangling"
RULE_IPD_DEP_AMBIGUOUS = "check.ipd-dependency-ambiguous"
RULE_IPD_DEP_CYCLE = "check.ipd-dependency-cycle"

# The type token used in an edge maps to the artifact record_type used by the resolver.
ITEM_DEP_TYPE_TO_RECORD_TYPE: Dict[str, str] = {
    "ipd": "plans",
    "spec": "specs",
    "backlog": "backlog",
}


def item_dependency_cycles(edges_by_plan: Dict[str, List[str]]) -> List[List[str]]:
    """Detect directed cycles in the IPD->IPD dependency graph. Pure.

    ``edges_by_plan`` maps an owner id6 to the list of target IPD id6s it depends on (only the
    IPD-typed edges - ``executed:`` / ``exists:ipd:`` / ``state:ipd:`` - participate; spec/backlog
    targets are graph leaves). Returns each detected cycle as a list of id6s in visitation order
    (the first repeated node closes the cycle); returns [] when the graph is acyclic. Deterministic:
    nodes and neighbors are visited in sorted order so the reported cycles are stable.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    cycles: List[List[str]] = []
    nodes = sorted(edges_by_plan.keys())

    def visit(node: str, stack: List[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in sorted(edges_by_plan.get(node, [])):
            if nxt not in edges_by_plan:
                # target is not itself an owner in the graph (leaf / external) - no cycle through it
                continue
            state = color.get(nxt, WHITE)
            if state == GRAY:
                # found a back-edge: close the cycle from where nxt appears in the stack
                if nxt in stack:
                    idx = stack.index(nxt)
                    cycles.append(stack[idx:] + [nxt])
            elif state == WHITE:
                visit(nxt, stack)
        stack.pop()
        color[node] = BLACK

    for n in nodes:
        if color.get(n, WHITE) == WHITE:
            visit(n, [])
    # De-duplicate cycles by their normalized node set (a cycle may be discovered from several starts).
    seen: set = set()
    unique: List[List[str]] = []
    for cyc in cycles:
        key = frozenset(cyc)
        if key not in seen:
            seen.add(key)
            unique.append(cyc)
    return unique


# --------------------------------------------------------------------------------------
# Identifier grammar + allocation watermark (spec Sections 5.1, 5.6)
# --------------------------------------------------------------------------------------

# Execution / validation identifiers. `\b`-clean so `grep -E '\bE-01\b'` matches in name and prose.
E_ID_RE = re.compile(r"\bE-([0-9]{2,})\b")
V_ID_RE = re.compile(r"\bV-([0-9]{2,})\b")
# A validation row header: "- [ ] V-NN validates E-MM".
V_ROW_RE = re.compile(r"^- \[[ x]\] (V-[0-9]{2,}) validates (E-[0-9]{2,})\b")
# An execution leaf header: "- [ ] E-NN <action>".
E_ROW_RE = re.compile(r"^- \[[ x]\] (E-[0-9]{2,})\b")
_DEPENDS_TOKEN_RE = re.compile(r"^E-[0-9]{2,}$")

E_ID_STRICT = re.compile(r"^E-[0-9]{2,}$")
V_ID_STRICT = re.compile(r"^V-[0-9]{2,}$")


def suffix_of(identifier: str) -> Optional[int]:
    """Return the integer suffix of an E-*/V-* id, or None if malformed."""
    if E_ID_STRICT.match(identifier) or V_ID_STRICT.match(identifier):
        return int(identifier.split("-", 1)[1])
    return None


def next_suffix(watermark: int) -> int:
    """The next allocatable suffix is watermark + 1 (NOT max-present-id), so a deleted highest id
    is never reused (spec Section 5.6)."""
    return watermark + 1


def watermark_error(
    watermark: Optional[int], present_e_suffixes: Sequence[int]
) -> Optional[str]:
    """Validate the allocation watermark against the present E ids (spec Section 5.6).

    Returns an error string, or None if valid. If any E exists the watermark is REQUIRED and MUST be
    >= the largest present E suffix.
    """
    if present_e_suffixes:
        if watermark is None:
            return "Highest E allocated is required once any E-* item exists"
        if watermark < max(present_e_suffixes):
            return "Highest E allocated must be >= the largest present E-* suffix"
    return None


def parse_depends_on(value: str) -> Tuple[List[str], Optional[str]]:
    """Parse a ``Depends on:`` value. Returns (ids, error). ``none`` (or empty) -> []."""
    v = value.strip()
    if v == "" or v.lower() == "none":
        return [], None
    ids = [tok.strip() for tok in v.split(",") if tok.strip()]
    for tok in ids:
        if not _DEPENDS_TOKEN_RE.match(tok):
            return ids, "Depends on must be 'none' or comma-separated E-* ids"
    return ids, None


def dependency_errors(edges: Dict[str, List[str]]) -> List[str]:
    """Given {E-id: [dep E-ids]}, return errors for missing targets, self-refs, and cycles."""
    errors: List[str] = []
    known = set(edges)
    for node, deps in edges.items():
        for dep in deps:
            if dep == node:
                errors.append("{0} depends on itself".format(node))
            elif dep not in known:
                errors.append("{0} depends on missing {1}".format(node, dep))
    # Cycle detection (DFS).
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in edges}

    def visit(n: str) -> bool:
        color[n] = GRAY
        for d in edges.get(n, []):
            if d not in color:
                continue
            if color[d] == GRAY:
                return True
            if color[d] == WHITE and visit(d):
                return True
        color[n] = BLACK
        return False

    for n in edges:
        if color[n] == WHITE and visit(n):
            errors.append("dependency cycle detected involving {0}".format(n))
            break
    return errors


def bijection_errors(e_ids: Sequence[str], v_targets: Dict[str, str]) -> List[str]:
    """Verify the 1:1 E<->V bijection (spec Section 5.3).

    ``e_ids`` = the execution ids present; ``v_targets`` = {V-id: targeted E-id}.
    """
    errors: List[str] = []
    e_set = set(e_ids)
    targeted: Dict[str, int] = {}
    for v_id, e_target in v_targets.items():
        # Suffix match rule: V-NN validates E-NN.
        if suffix_of(v_id) != suffix_of(e_target):
            errors.append("{0} must validate the matching-suffix E item".format(v_id))
        if e_target not in e_set:
            errors.append("{0} targets missing {1}".format(v_id, e_target))
        targeted[e_target] = targeted.get(e_target, 0) + 1
    for e_id in e_ids:
        cnt = targeted.get(e_id, 0)
        if cnt == 0:
            errors.append("{0} has no validation item".format(e_id))
        elif cnt > 1:
            errors.append("{0} has more than one validation item".format(e_id))
    return errors


# --------------------------------------------------------------------------------------
# Execution / validation state tables (spec Sections 5.2, 5.3)
# --------------------------------------------------------------------------------------

EXEC_STATES: FrozenSet[str] = frozenset(("pending", "performed", "blocked", "failed"))
VALIDATION_RESULTS: FrozenSet[str] = frozenset(("pending", "pass", "blocked", "failed"))

# Execution state -> whether the checkbox must be checked.
_EXEC_CHECKBOX = {
    "pending": False,
    "performed": True,
    "blocked": False,
    "failed": False,
}
# Execution states that REQUIRE an Execution note.
_EXEC_NOTE_REQUIRED: FrozenSet[str] = frozenset(("blocked", "failed"))


def execution_row_error(state: str, checked: bool, has_note: bool) -> Optional[str]:
    if state not in EXEC_STATES:
        return "unknown execution state '{0}'".format(state)
    if _EXEC_CHECKBOX[state] != checked:
        return "execution checkbox does not agree with state '{0}'".format(state)
    if state in _EXEC_NOTE_REQUIRED and not has_note:
        return "state '{0}' requires an Execution note".format(state)
    return None


# Validation result -> (checkbox checked, observed-evidence must be nonempty).
_VALIDATION_RULES = {
    "pending": (False, False),
    "pass": (True, True),
    "blocked": (False, True),
    "failed": (False, True),
}


def validation_row_error(
    result: str, checked: bool, observed_nonempty: bool
) -> Optional[str]:
    if result not in VALIDATION_RESULTS:
        return "unknown validation result '{0}'".format(result)
    want_checked, want_obs = _VALIDATION_RULES[result]
    if want_checked != checked:
        return "validation checkbox does not agree with result '{0}'".format(result)
    if want_obs and not observed_nonempty:
        return "result '{0}' requires nonempty Observed evidence".format(result)
    if not want_obs and observed_nonempty:
        return "result 'pending' must have empty Observed evidence"
    return None


def cross_state_error(exec_state: str, validation_result: str) -> Optional[str]:
    """E/V cross-constraints (spec Section 5.3)."""
    if validation_result in ("pass", "failed") and exec_state != "performed":
        return "validation '{0}' requires execution state 'performed'".format(
            validation_result
        )
    if exec_state in ("blocked", "failed") and validation_result == "pass":
        return "execution '{0}' must not have validation result 'pass'".format(
            exec_state
        )
    return None


# --------------------------------------------------------------------------------------
# Lint checkpoints (spec Section 9)
# --------------------------------------------------------------------------------------

CHECKPOINTS: Tuple[str, ...] = (
    "author",
    "review-finalize",
    "pre-execution",
    "pre-transition",
    "post-transition",
)


def checkpoint_allows_status(
    checkpoint: str, status: str, directory: Optional[str] = None
) -> bool:
    """Coarse compatibility of a requested checkpoint with a persisted status/directory.

    An incompatible combination is an error (spec Section 9.1). This encodes the conservative,
    deterministic subset; the linter adds the per-row state checks of Section 9.2.
    """
    if checkpoint not in CHECKPOINTS:
        return False
    if checkpoint == "pre-transition":
        # Must not already be terminal.
        return status not in TERMINAL
    if checkpoint == "post-transition":
        # Only meaningful once terminal.
        return status in TERMINAL
    if checkpoint == "pre-execution":
        # Must be at a ready-to-execute readiness tier.
        return status in READY_TO_EXECUTE
    # author / review-finalize apply to pre-terminal drafting/review.
    return status in PRE_TERMINAL


# --------------------------------------------------------------------------------------
# Size thresholds (spec Section 8)
# --------------------------------------------------------------------------------------

MAX_TASK_GROUPS = 5  # warn when task-group H3 count exceeds this
MAX_E_LEAVES = 18  # warn when executable E-* leaf count exceeds this
SIZE_ASSESSMENTS: FrozenSet[str] = frozenset(("standard", "exception"))


def size_warning(task_group_count: int, e_leaf_count: int) -> bool:
    """True when either size threshold is exceeded (a warning + review trigger, not a cap)."""
    return task_group_count > MAX_TASK_GROUPS or e_leaf_count > MAX_E_LEAVES


# --------------------------------------------------------------------------------------
# Per-E-item density heuristic (spec Section 8.1, Order 07)
# --------------------------------------------------------------------------------------

DENSITY_DELIVERABLE_NOUNS: FrozenSet[str] = frozenset(
    (
        "ledger",
        "ledgers",
        "compiler",
        "compilers",
        "runtime",
        "runtimes",
        "engine",
        "engines",
        "validator",
        "validators",
        "suite",
        "suites",
        "schema",
        "schemas",
        "service",
        "services",
        "endpoint",
        "endpoints",
        "workflow",
        "workflows",
        "adapter",
        "adapters",
        "registry",
        "registries",
        "wizard",
        "wizards",
        "harness",
        "harnesses",
        "framework",
        "frameworks",
        "parser",
        "parsers",
        "generator",
        "generators",
        "cli",
        "subcommand",
        "subcommands",
        "database",
        "databases",
        "pipeline",
        "pipelines",
        "recovery",
        "controller",
        "controllers",
        "interface",
        "interfaces",
        "dashboard",
        "dashboards",
        "infrastructure",
        "subsystem",
        "subsystems",
        "gateway",
        "gateways",
        "management",
        "storage",
        "frontend",
        "backend",
        "documentation",
        "ui",
    )
)

DENSITY_ACTION_VERBS: FrozenSet[str] = frozenset(
    (
        "add",
        "create",
        "implement",
        "build",
        "define",
        "update",
        "refactor",
        "rewrite",
        "migrate",
        "wire",
        "enforce",
        "integrate",
        "support",
        "surface",
        "replace",
        "introduce",
        "deploy",
        "delete",
        "write",
    )
)

_E_LEAF_PREFIX_RE = re.compile(
    r"^(?:-\s*\[[ x]\]\s*)?(?:E-[0-9]{2,}\b\s*:?\s*)?(.*)$", re.DOTALL
)
_CODE_SPAN_RE = re.compile(r"`[^`]+`")
_ENUM_PARTS_RE = re.compile(
    r"(?:\((?:a|1|i)\)|1\)|a\))\s+(.*?)(?:\((?:b|2|ii)\)|2\)|b\))\s+(.*?)(?:\((?:c|3|iii)\)|3\)|c\))\s+(.*)",
    re.IGNORECASE | re.DOTALL,
)
_SINGLE_TEST_ITEM_RE = re.compile(
    r"^(?:add\s+)?(?:falsifiable\s+|regression\s+|unit\s+)?(?:tests?|test\s+suite)\b",
    re.IGNORECASE,
)
_TEST_SURFACES_RE = re.compile(
    r"\b(unit\s+tests?|integration\s+tests?|end-to-end\s+tests?|e2e\s+tests?|regression\s+tests?|benchmark\s+harness|performance\s+benchmarks?)\b",
    re.IGNORECASE,
)
_CLAUSE_SPLIT_RE = re.compile(
    r",\s*(?:and|plus|along with|as well as)\b|[,;]|\b(?:and|plus|along with|as well as)\b",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"\b[a-z]+\b")
_PREP_START_RE = re.compile(
    r"^(?:in|under|across|from|between|through|for|into|with)\s+", re.IGNORECASE
)


def e_item_density_advisory(action: str) -> Optional[str]:
    """Evaluate whether an E-item action text may bundle multiple independent concerns.

    Advisory only: returns a human-readable reason if the action text names multiple
    independent deliverables or test-surfaces, or None if single-concern. Uses the
    "one concern / executable-in-one-focused-pass" definition canonically stated in
    plan-review.md (Order 06 por1hi).
    """
    if not action or not action.strip():
        return None

    text = action.strip()
    if text.startswith("- [ ] ") or text.startswith("- [x] "):
        text = text[6:].strip()
    m = re.match(r"^E-[0-9]{2,}\b\s*:?\s*(.*)$", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    if not text:
        return None

    # Exclude code spans to analyze natural language structure
    cleaned = _CODE_SPAN_RE.sub("CODE", text)

    # 1. Multi-part explicit enumeration of distinct major actions / deliverables: (a)...(b)...(c)
    # Exclude single test file assertion breakdowns (e.g. "Add tests/test_x.py: (a) ... (b) ...")
    if not _SINGLE_TEST_ITEM_RE.match(cleaned):
        enum_match = _ENUM_PARTS_RE.search(cleaned)
        if enum_match:
            part_a, part_b, part_c = (
                enum_match.group(1),
                enum_match.group(2),
                enum_match.group(3),
            )

            def _has_action_clause(p: str) -> bool:
                w = set(_WORD_RE.findall(p.lower()))
                return bool(
                    w & DENSITY_ACTION_VERBS
                    and (w & DENSITY_DELIVERABLE_NOUNS or len(w) >= 4)
                )

            if (_has_action_clause(part_a) and _has_action_clause(part_b)) or (
                _has_action_clause(part_b) and _has_action_clause(part_c)
            ):
                return "explicit multi-part enumeration with multiple independent actions or deliverables"

    # 2. Multiple independent test surfaces across subsystems
    test_surface_matches = _TEST_SURFACES_RE.findall(cleaned)
    if (
        len(set(m.lower() for m in test_surface_matches)) >= 2
        and len(test_surface_matches) >= 3
    ):
        return "names multiple distinct test surfaces across subsystems"

    # 3. Three or more distinct action verb clauses targeting deliverables joined by commas/conjunctions/semicolons
    cleaned_no_parens = re.sub(r"\([^)]*\)", "", cleaned)
    segments = [
        s.strip() for s in _CLAUSE_SPLIT_RE.split(cleaned_no_parens) if s.strip()
    ]
    if len(segments) >= 3:
        matched_clauses = []
        for seg in segments:
            words = set(_WORD_RE.findall(seg.lower()))
            has_verb = bool(words & DENSITY_ACTION_VERBS)
            has_noun = bool(words & DENSITY_DELIVERABLE_NOUNS)
            is_prep = bool(_PREP_START_RE.match(seg))
            if (has_verb and has_noun and not is_prep) or (
                has_noun and len(words) >= 2 and not is_prep
            ):
                matched_clauses.append(seg)
        if len(matched_clauses) >= 3:
            snippets = ", ".join(
                f"'{c[:28]}...'" if len(c) > 28 else f"'{c}'"
                for c in matched_clauses[:3]
            )
            return f"names multiple independent deliverables or action clauses (likely multi-concern; {len(matched_clauses)} clauses: {snippets})"

    # 4. Semicolon-separated chain of 3+ distinct action verb clauses
    semi_parts = [p.strip() for p in cleaned.split(";") if p.strip()]
    if len(semi_parts) >= 3:
        verb_clauses = []
        for p in semi_parts:
            words = set(_WORD_RE.findall(p.lower()))
            if words & DENSITY_ACTION_VERBS and (
                words & DENSITY_DELIVERABLE_NOUNS or len(words) >= 4
            ):
                verb_clauses.append(p)
        if len(verb_clauses) >= 3:
            snippets = ", ".join(
                f"'{c[:28]}...'" if len(c) > 28 else f"'{c}'" for c in verb_clauses[:3]
            )
            return f"chains multiple semicolon-separated action clauses (likely multi-concern; {len(verb_clauses)} clauses: {snippets})"

    return None


# --------------------------------------------------------------------------------------
# Open-question grammar (spec Section 7)
# --------------------------------------------------------------------------------------

OQ_HEADING_RE = re.compile(r"^### (OQ-[0-9]{2,}):\s*(.+)$")
OQ_BLOCKING_VALUES: FrozenSet[str] = frozenset(("yes", "no"))
OQ_STATUS_VALUES: FrozenSet[str] = frozenset(("open", "resolved", "deferred"))
#: The open-question subfields this repo names. DOCUMENTATION, NOT ENFORCEMENT: verified that
#: `OQ_FIELDS` has NO consumer anywhere in the codebase (it is defined here and never read), and
#: `open_question_error` below validates its four arguments POSITIONALLY, so it is unaffected by any
#: extra subfield. The parser (`ipd_lint`, the `- Field: value` capture under an `### OQ-NN:` heading)
#: is deliberately OPEN-ENDED and carries any subfield into the parsed dict.
#:
#: `Finding` is the plqjt7 E-08 convention: a blocking question ESCALATING an unfixed review finding
#: names it as `- Finding: F-3` (comma-separate several). `check.review-finding-unescalated` matches
#: THIS TYPED FIELD, never the rationale prose - a substring search over prose would be spoofable by
#: any incidental mention and brittle against rewording. It is OPTIONAL: only a question escalating a
#: gating finding needs it.
#:
#: Because the tuple has no consumer, adding `Finding` here changes NO behavior; it is recorded so an
#: author reading the schema finds the convention. If a future change makes `OQ_FIELDS` a CLOSED
#: allowlist, `Finding` must stay in it or every escalation becomes a structural error.
OQ_FIELDS: Tuple[str, ...] = (
    "Blocking",
    "Status",
    "Owner",
    "Resolution or deferral rationale",
    "Finding",
)


def open_question_error(
    blocking: str, status: str, has_rationale: bool, has_owner: bool
) -> Optional[str]:
    """Structural consistency of an OQ item (spec Section 7). Semantics are the reviewer's job."""
    if blocking not in OQ_BLOCKING_VALUES:
        return "OQ Blocking must be yes or no"
    if status not in OQ_STATUS_VALUES:
        return "OQ Status must be open, resolved, or deferred"
    if blocking == "yes" and status == "deferred":
        return "a blocking question may not be deferred"
    if status == "resolved" and not has_rationale:
        return "a resolved question requires a rationale"
    if status == "deferred" and (
        blocking != "no" or not has_owner or not has_rationale
    ):
        return "a deferred question requires Blocking: no, an owner or trigger, and a rationale"
    return None


# --------------------------------------------------------------------------------------
# Quarantine + legacy dispositions (spec Sections 13.2, 13.3)
# --------------------------------------------------------------------------------------

# Non-passing dispositions the linter reports (distinct from a conforming pass).
DISPOSITION_CONFORMING = "conforming"
DISPOSITION_QUARANTINED = "quarantined"
DISPOSITION_LEGACY = "legacy/not evaluated"
DISPOSITION_ERROR = "error"
DISPOSITIONS: FrozenSet[str] = frozenset(
    (
        DISPOSITION_CONFORMING,
        DISPOSITION_QUARANTINED,
        DISPOSITION_LEGACY,
        DISPOSITION_ERROR,
    )
)
# Only `conforming` is a pass; the rest are non-passing (informational or error).
PASSING_DISPOSITIONS: FrozenSet[str] = frozenset((DISPOSITION_CONFORMING,))


def is_quarantined(fields: Dict[str, str]) -> bool:
    return "Quarantine" in fields
