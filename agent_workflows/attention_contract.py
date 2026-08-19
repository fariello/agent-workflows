"""Frozen contracts for the cross-tree attention view (Set attnview, Order 01).

This module is the SINGLE HOME for the machine-usable contracts the attention view rests on. It is
data + validators only; it contains no scanner, no CLI, and no writer (those are Orders 02/03). It is
stdlib-only and Python 3.9 compatible (D46).

It freezes the design of the approved spec
``.agents/docs/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md``:

- Section 6: the five-value attention-class enum + the PURE, TOTAL per-tree ``class_of`` mapping.
- Section 6/8.6: the tree POLICY inventory (each tree tracked-with-owner+mapping or excluded-with-reason).
- Section 7: the spec status lifecycle + the transition/authority table + the anti-self-approval floor.
- Section 8.3/8.4/8.8: the gate fields + per-kind validators + output-safety rules.
- Section 8.3: the closed catalog of stable ``--check``/``--agent`` rule ids + the record shape.
- Section 8.2/8.5: the ``## Workflow history`` record grammar + the ``last_history_at`` derivation.

The human-readable contract prose lives in THIS module docstring and the per-object docstrings below;
the machine-usable shapes live in the module-level data structures. There is deliberately no second
home (Order 01 finding L1-06).

Attention classes (Section 6):

- ``ready``   a concrete action can be taken now.
- ``active``  work is EXPLICITLY in progress (a native state says so); never inferred.
- ``blocked`` work is intended to continue but a named GATE prevents progress.
- ``done``    successfully complete, or a standing accepted reference.
- ``parked``  intentionally inactive, archived, superseded, abandoned, or not executed.

Mapping purity (Section 6): ``class_of(tree, native_status)`` depends ONLY on ``(tree, native_status)``.
It NEVER infers activity or gate state from prose, dates, mtime, lock files, or agent context. Every
native enum value of every tracked tree maps to exactly one class; an unknown value is a violation,
never a default. ``last_history_at`` derivation (Section 8.5): parse the ``## Workflow history`` records
(``HISTORY_RECORD_RE``); ``last_history_at`` is the date of the LAST record in file order; empty history
yields ``None`` (not a violation here; the scanner decides whether absence is a per-tree violation);
NEVER file mtime.
"""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple

# --------------------------------------------------------------------------------------
# The five-value attention-class enum (spec Section 6)
# --------------------------------------------------------------------------------------

READY = "ready"
ACTIVE = "active"
BLOCKED = "blocked"
DONE = "done"
PARKED = "parked"

ATTENTION_CLASSES: FrozenSet[str] = frozenset((READY, ACTIVE, BLOCKED, DONE, PARKED))

# Fixed display/sort order for the human board and deterministic output (attention umbrella first).
ATTENTION_CLASS_ORDER: Tuple[str, ...] = (ACTIVE, READY, BLOCKED, DONE, PARKED)

# The umbrella heading groups the three that need attention; machine output keeps the distinct values.
ATTENTION_UMBRELLA: Tuple[str, ...] = (READY, ACTIVE, BLOCKED)


# --------------------------------------------------------------------------------------
# Tree policy inventory (spec Section 6/8.6; OQ3/OQ8 resolved)
# --------------------------------------------------------------------------------------


class TreePolicy(NamedTuple):
    """A tree's disposition in the attention view: ``tracked`` (with an owner + mapping) or
    ``excluded`` (with a rationale). A scanned path under no inventoried tree is a violation
    (``attention.unclassified-tree``)."""

    name: str
    root: str  # repo-relative directory (or file) prefix
    tracked: bool
    owner: (
        str  # the verb/module that owns writes for a tracked tree, or "" when excluded
    )
    reason: str  # rationale, esp. for excluded trees


# v1 scope (OQ3): specs + plans + research tracked; prompts/comms deferred to Phase 3; walkthroughs +
# roadmaps excluded (no real lifecycle semantics yet, OQ8). READMEs and index files are not artifacts.
TREE_POLICY: Tuple[TreePolicy, ...] = (
    TreePolicy(
        "specs",
        ".agents/docs/specs",
        True,
        "aw specs",
        "design specs; owner writes via aw specs",
    ),
    TreePolicy(
        "plans",
        ".agents/plans",
        True,
        "aw ipd",
        "IPDs; owner writes via the aw ipd + noun-verb plan verbs",
    ),
    TreePolicy(
        "research",
        ".agents/docs/research",
        True,
        "aw research",
        "research corpus; owner writes via aw research",
    ),
    TreePolicy(
        "backlog",
        ".agents/backlog",
        True,
        "aw backlog",
        "attention-visible backlog tier; owner writes via aw backlog (records-class, dual-path with .aw/records/backlog)",
    ),
    TreePolicy(
        "walkthroughs",
        ".agents/docs/walkthroughs",
        False,
        "",
        "narrative records; no lifecycle status in v1 (OQ8)",
    ),
    TreePolicy(
        "roadmaps",
        ".agents/docs/roadmaps",
        False,
        "",
        "intent, not commitment; no lifecycle status in v1 (OQ8)",
    ),
    TreePolicy(
        "prompts",
        ".agents/prompts",
        False,
        "",
        "deferred to Phase 3 (OQ3); own lifecycle not yet contracted here",
    ),
    TreePolicy(
        "comms",
        ".agents/comms",
        False,
        "",
        "deferred to Phase 3 (OQ3); own ack lifecycle not contracted here",
    ),
    TreePolicy(
        "docs-prompts",
        ".agents/docs/prompts",
        False,
        "",
        "the evergreen copy-paste prompt LIBRARY, not a lifecycle-tracked artifact tree",
    ),
    TreePolicy(
        "releases",
        ".agents/releases",
        True,
        "aw releases",
        "release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped (awrelease)",
    ),
)

TRACKED_TREES: Tuple[str, ...] = tuple(p.name for p in TREE_POLICY if p.tracked)


def is_nonartifact_name(name: str) -> bool:
    """True for files that live INSIDE a tracked tree but are not lifecycle artifacts (generated
    boards, templates, indexes, READMEs). They carry no status and are excluded from the view rather
    than flagged. Kept deliberately narrow and name-based so it is predictable."""

    lower = name.lower()
    if name in ("README.md", "INDEX.md", "INDEX.json", "STATUS.md"):
        return True
    if lower.endswith("-template.md") or lower.endswith("-index.md"):
        return True
    if lower.endswith("readme.md"):
        return True
    return False


# --------------------------------------------------------------------------------------
# Per-tree native-status enums and the PURE, TOTAL class mapping (spec Section 6/7)
# --------------------------------------------------------------------------------------

# Specs (spec Section 7). The canonical spec status enum, pinned here so the coverage test diffs one
# symbol per tree.
SPEC_STATUSES: FrozenSet[str] = frozenset(
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
)

# Per-tree mapping fragments. Keyed by the canonical native enum for each tree:
#   plans   -> plans.RECOGNIZED
#   research-> research_contract.STATUSES
#   specs   -> SPEC_STATUSES (above)
# The plans/research enums are imported lazily by the coverage test to avoid a hard import cycle and to
# keep this module dependency-light; the mapping keys below MUST equal those enums exactly.

_SPEC_MAP: Dict[str, str] = {
    "draft": READY,
    "to-review": READY,
    "reviewed": READY,
    "approved": READY,
    "implementing": ACTIVE,
    "implemented": DONE,
    "deferred": BLOCKED,
    "parked": PARKED,
    "superseded": PARKED,
}

# Plans (over plans.RECOGNIZED). No native "executing" state exists yet (OQ5), so approved/auto-approved
# map to ready, NOT active; the scanner never infers execution. If the plans owner later adds a native
# executing state, add it here.
_PLANS_MAP: Dict[str, str] = {
    "draft": READY,
    "to-review": READY,
    "reviewed": READY,
    "approved": READY,
    "auto-approved": READY,
    "executed": DONE,
    "superseded": PARKED,
    "not-executed": PARKED,
    "reusable": READY,
}

# Research (over research_contract.STATUSES). Research has a genuine native ``active`` -> the live source
# of the attention ``active`` class in v1.
_RESEARCH_MAP: Dict[str, str] = {
    "intake": READY,
    "active": ACTIVE,
    "reference": DONE,
    "archive": PARKED,
}

# Actions (AW operational actions). Map open -> ready, completed -> done, dismissed/superseded -> parked (spec Section 12.7).
_ACTIONS_MAP: Dict[str, str] = {
    "open": READY,
    "completed": DONE,
    "dismissed": PARKED,
    "superseded": PARKED,
}

# Backlog (attention-visible backlog tier; spec 20260813-1833-01). open -> ready (committed,
# actionable), blocked -> blocked (committed but gated; carries a typed Gate-Kind/Gate-Ref),
# parked -> parked (uncommitted "maybe"; auto-hidden from the default board), done -> done.
_BACKLOG_MAP: Dict[str, str] = {
    "open": READY,
    "blocked": BLOCKED,
    "parked": PARKED,
    "done": DONE,
}

# Release records (ship-gate anchors, awrelease): planned -> ready, blocked -> blocked, shipped -> done.
_RELEASES_MAP: Dict[str, str] = {
    "planned": READY,
    "blocked": BLOCKED,
    "shipped": DONE,
}

# The registry of mapping fragments, one per tracked tree.
CLASS_MAPS: Dict[str, Dict[str, str]] = {
    "specs": _SPEC_MAP,
    "plans": _PLANS_MAP,
    "research": _RESEARCH_MAP,
    "actions": _ACTIONS_MAP,
    "backlog": _BACKLOG_MAP,
    "releases": _RELEASES_MAP,
}


class UnknownNativeStatus(KeyError):
    """Raised by ``class_of`` when ``(tree, native_status)`` has no mapping. The scanner turns this into
    the ``attention.unknown-status`` / ``attention.unmapped-status`` violation, never a default class."""


def class_of(tree: str, native_status: str) -> str:
    """Return the attention class for ``(tree, native_status)``. PURE and TOTAL over each tracked tree's
    native enum; raises ``UnknownNativeStatus`` for an unmapped value (the caller renders a violation)."""

    fragment = CLASS_MAPS.get(tree)
    if fragment is None:
        raise UnknownNativeStatus(f"tree not tracked: {tree!r}")
    try:
        return fragment[native_status]
    except KeyError as exc:
        raise UnknownNativeStatus(
            f"no mapping for {tree!r} status {native_status!r}"
        ) from exc


# --------------------------------------------------------------------------------------
# Spec metadata + transition/authority contract (spec Section 7; OQ10 + the anti-self-approval floor)
# --------------------------------------------------------------------------------------

# A spec's status is a single front-matter bullet ``- Status: <bare-enum-token>`` with NO trailing prose.
SPEC_STATUS_RE = re.compile(r"^- Status:[ \t]*(?P<value>\S+)[ \t]*$")

# Legal spec transitions (spec Section 7). Backward moves (e.g. reviewed -> to-review) are permitted and
# recorded; ``implemented``/``superseded`` are terminal-forward. Keyed old -> set of allowed new.
SPEC_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    "draft": frozenset(("to-review", "deferred", "parked", "superseded")),
    "to-review": frozenset(("reviewed", "draft", "deferred", "parked", "superseded")),
    "reviewed": frozenset(
        ("approved", "to-review", "deferred", "parked", "superseded")
    ),
    "approved": frozenset(
        ("implementing", "reviewed", "deferred", "parked", "superseded")
    ),
    "implementing": frozenset(
        ("implemented", "approved", "deferred", "parked", "superseded")
    ),
    "implemented": frozenset(
        ("superseded", "deferred")
    ),  # terminal-forward; corrective only
    "deferred": frozenset(
        (
            "draft",
            "to-review",
            "reviewed",
            "approved",
            "implementing",
            "parked",
            "superseded",
        )
    ),
    "parked": frozenset(("draft", "to-review", "reviewed", "superseded")),
    "superseded": frozenset(("draft",)),  # corrective un-supersede only
}

# Transition authority (spec Section 7). ``by_human`` means the mechanism requires an explicit
# --by-human attestation (a conscious speed bump recording attributed human approval; NOT anti-malicious crypto;
# see APPROVAL_FLOOR). ``evidence`` means a resolvable implementation-evidence citation is required.
TRANSITION_AUTHORITY: Dict[str, Dict[str, object]] = {
    "->approved": {
        "who": "human",
        "by_human": True,
        "human_token": True,
        "evidence": False,
    },
    "->implementing": {
        "who": "executor",
        "by_human": False,
        "human_token": False,
        "evidence": False,
    },
    "->implemented": {
        "who": "executor",
        "by_human": False,
        "human_token": False,
        "evidence": True,
    },
    "->deferred": {
        "who": "any",
        "by_human": False,
        "human_token": False,
        "evidence": False,
        "requires_gate": True,
    },
}

# The anti-self-approval FLOOR (spec F11; Order 01 finding L2-01/L4-04; revised 2026-08-15).
# aw specs enforces that ``reviewed -> approved`` requires an explicit ``--by-human`` attestation.
APPROVAL_FLOOR = (
    "The reviewed -> approved mechanism requires an EXPLICIT --by-human attestation (a conscious speed "
    "bump recording attributed human approval; no TTY requirement, no false 'I am human' claim). A plain "
    "status set WITHOUT --by-human is INSUFFICIENT: it stops and refuses the transition. The "
    "implementing -> implemented transition requires a RESOLVABLE evidence citation (e.g. an existing "
    ".agents/plans/executed/ IPD path), not merely a well-formed string; aw specs enforces presence + "
    "format + resolvability, NOT semantic verification that the work truly happened."
)


def transition_allowed(old: str, new: str) -> bool:
    """True iff ``old -> new`` is a legal spec transition (Section 7)."""

    return new in SPEC_TRANSITIONS.get(old, frozenset())


# --------------------------------------------------------------------------------------
# Gate contract (spec Section 8.4; OQ6) + output-safety (Section 8.8)
# --------------------------------------------------------------------------------------

GATE_KINDS: FrozenSet[str] = frozenset(
    ("artifact", "decision", "todo", "issue", "date", "external")
)

# Gate fields are sibling front-matter bullets, one value per line, no trailing prose on kind/ref.
GATE_KIND_RE = re.compile(r"^- Gate-Kind:[ \t]*(?P<value>\S+)[ \t]*$")
GATE_REF_RE = re.compile(r"^- Gate-Ref:[ \t]*(?P<value>.+?)[ \t]*$")
GATE_SUMMARY_RE = re.compile(r"^- Gate-Summary:[ \t]*(?P<value>.+?)[ \t]*$")

# Output-safety (Section 8.8): descriptive fields are single-line, bounded, control-char-free.
MAX_DESCRIPTIVE_LEN = 300
# C0 (except we never allow tab/newline inside a field) + C1 + DEL; ANSI ESC included.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_HTTP_URL_RE = re.compile(r"^https?://\S+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TODO_ID_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
_DECISION_ID_RE = re.compile(r"^D\d+$")
# artifact: repo-relative POSIX path with an optional Markdown anchor; must not escape the repo.
_ARTIFACT_REF_RE = re.compile(r"^(?!/)(?!.*\.\.)[A-Za-z0-9._/-]+(#[A-Za-z0-9._-]+)?$")


def is_safe_descriptive(value: str) -> bool:
    """Section 8.8: a descriptive field is a single, bounded, control-char-free line."""

    if value is None:
        return True
    if len(value) > MAX_DESCRIPTIVE_LEN:
        return False
    if "\n" in value or "\r" in value:
        return False
    if _CONTROL_CHAR_RE.search(value):
        return False
    return True


def validate_gate_ref(kind: str, ref: str) -> bool:
    """Per-kind ``Gate-Ref`` validator (Section 8.4). Returns False on any malformed ref."""

    if not ref or not is_safe_descriptive(ref):
        return False
    if kind == "date":
        return bool(_DATE_RE.match(ref))
    if kind == "issue":
        return bool(_HTTP_URL_RE.match(ref))  # http(s) only; no javascript:/file:/data:
    if kind == "artifact":
        return bool(_ARTIFACT_REF_RE.match(ref))
    if kind == "todo":
        return bool(_TODO_ID_RE.match(ref))
    if kind == "decision":
        return bool(_DECISION_ID_RE.match(ref))
    if kind == "external":
        return bool(ref.strip())  # nonempty opaque, treated as data
    return False


# --------------------------------------------------------------------------------------
# Workflow-history record grammar + last_history_at derivation (spec Section 8.2/8.5; OQ2)
# --------------------------------------------------------------------------------------

# One dated record per touch: ``- YYYY-MM-DD <free single line>``. The DATE is the machine field;
# ``last_history_at`` is the date of the LAST record in file order (empty history -> None; never mtime).
HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")


def last_history_at(history_lines: List[str]) -> Optional[str]:
    """Derive ``last_history_at`` from parsed ``## Workflow history`` lines: the date of the LAST matching
    record in file order, or ``None`` when there is no record. Never uses file mtime (Section 8.5)."""

    last: Optional[str] = None
    for line in history_lines:
        m = HISTORY_RECORD_RE.match(line)
        if m:
            last = m.group("date")
    return last


# --------------------------------------------------------------------------------------
# Stable rule-id catalog + the agent-record shape (spec Section 8.3; Order 01 finding L1-01)
# --------------------------------------------------------------------------------------

# The CLOSED catalog of stable ``--check``/``--agent`` rule identifiers, one per F3/8.8 violation class.
# Orders 02 and 03 MUST use these ids; they do NOT free-hand new ones. The agent record is the house
# ``location<TAB>rule<TAB>detail`` form (artifact_core.Drift): the third field is ``detail``, NOT severity.
RULE_IDS: FrozenSet[str] = frozenset(
    (
        "attention.missing-status",
        "attention.unknown-status",
        "attention.unmapped-status",
        "attention.gate-missing",  # deferred without a gate
        "attention.gate-malformed",  # bad Gate-Kind / Gate-Ref
        "attention.gate-forbidden",  # gate fields on a non-deferred status
        "attention.history-missing",
        "attention.history-malformed",
        "attention.duplicate-id",
        "attention.duplicate-path",
        "attention.disposition-mismatch",  # plans dir vs terminal status
        "attention.unstable-path",  # invalid/symlink-escaping repo-relative path
        "attention.unreadable",  # unreadable / unsupported-encoding / malformed front matter
        "attention.unclassified-tree",
        "attention.unsafe-field",  # control-char / over-length / newline / non-http issue url
        "attention.external-state-invalid",  # invalid, unreadable, or escaping external AW state root
    )
)

# The escaping policy for the agent record's ``detail`` field (tab/newline/backslash) so the
# ``location<TAB>rule<TAB>detail`` line stays one record. artifact_core.render_agent_drift owns emission;
# callers pass an already-escaped detail per this policy.
_AGENT_ESCAPES = (("\\", "\\\\"), ("\t", "\\t"), ("\n", "\\n"), ("\r", "\\r"))


def escape_detail(detail: str) -> str:
    """Escape a drift ``detail`` for the single-line ``location<TAB>rule<TAB>detail`` agent record."""

    out = detail
    for raw, rep in _AGENT_ESCAPES:
        out = out.replace(raw, rep)
    return out
