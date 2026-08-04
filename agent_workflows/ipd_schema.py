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
# The full set of recognized field names (unknown fields are errors for new IPDs).
META_RECOGNIZED: FrozenSet[str] = frozenset(
    META_REQUIRED
    + META_PAIRED_SET_ORDER
    + META_QUARANTINE_TRIO
    + (META_WATERMARK, META_APPROVAL)
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
# Open-question grammar (spec Section 7)
# --------------------------------------------------------------------------------------

OQ_HEADING_RE = re.compile(r"^### (OQ-[0-9]{2,}):\s*(.+)$")
OQ_BLOCKING_VALUES: FrozenSet[str] = frozenset(("yes", "no"))
OQ_STATUS_VALUES: FrozenSet[str] = frozenset(("open", "resolved", "deferred"))
OQ_FIELDS: Tuple[str, ...] = (
    "Blocking",
    "Status",
    "Owner",
    "Resolution or deferral rationale",
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
