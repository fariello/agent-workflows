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
(``HISTORY_RECORD_RE``); ``last_history_at`` is the date of the NEWEST record, and the section is
NEWEST-FIRST, so that is the FIRST record in file order (see :func:`newest_history_record`; corrected
by plan ``vhbvwz`` E-02, which measured 534 artifacts reporting a date that was not their newest);
empty history yields ``None`` (not a violation here; the scanner decides whether absence is a per-tree
violation); NEVER file mtime.
"""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple

from agent_workflows import lifecycle_dirs as _LD

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
# The closed ordering vocabulary for `aw next --order-by` (worksequence i6015i, E-03)
# --------------------------------------------------------------------------------------

# The CLOSED set of sort keys `aw next -o/--order-by` accepts. Declared as DATA here (one home) so
# the CLI `choices`, the shell completion list and the tests all read this tuple instead of each
# re-typing a list that would then drift.
#
# WHY THE DEFAULT IS `class` AND NOT `depth`: the `xprio` Set pinned "the shared attention sort key
# is UNCHANGED (priority not added to the sort tuple)" as required evidence in all four of its
# plans. Making `class` (the historical `(class, path, id)` tuple) the default and every other order
# an explicit opt-in is what keeps that contract LITERALLY true rather than merely approximately so.
#
# PURITY (see the mapping-purity clause above): a caller NAMING one of these keys does not violate
# this module's purity, because the selection is explicit and the key is a single declared field. A
# HEURISTIC BLEND of keys would violate it (it would infer importance from context and be
# unexplainable to the user), so this vocabulary deliberately contains no composite/scored key.
#
# Every key is a PARTIAL order on its own: the items that carry no value for the selected key sort
# LAST, and every key falls through to the `(class, path, id)` default tail so the resulting order is
# TOTAL and deterministic. Ordering NEVER filters; selection stays the job of the filter flags.
ORDER_CLASS = "class"
ORDER_KEYS: Tuple[str, ...] = (
    ORDER_CLASS,  # the DEFAULT: the historical (class order, path, id) tuple
    "priority",  # high > medium > low, then unprioritized
    "date",  # last_history_at, newest first
    "set",  # Set id from the filename grammar
    "setid",  # alias for set
    "order",  # Order number from the filename grammar
    "blocking",  # items carrying Blocks-Release first
    "depth",  # declared dependency depth: prerequisites BEFORE dependents
    "id6",  # the stable 6-char handle
    "path",  # repo-relative POSIX path
    "file",  # filename / basename
    "status",  # native status
    "tree",  # records tree / artifact type
    "type",  # alias for tree
    "readiness",  # review readiness: go > go-pending-approval > no-go
    "oqs",  # unresolved open questions count (descending)
    "rqs",  # resolved questions count (descending)
    "ctime",  # filesystem creation time (newest first)
    "mtime",  # filesystem modification time (newest first)
    "runs",  # runner session status: running > merging > queued > done > blocked > failed
    "run",  # alias for runs
)

# The priority ranks used by `-o priority`. DERIVED from one shared vocabulary rather than forked:
# `backlog.PRIORITIES` is the enum and `check_engine._PRIORITY_RANK` is the existing rank; this maps
# the rank into DESCENDING sort position (high first) without introducing a second rank table.
PRIORITY_ORDER: Tuple[str, ...] = ("high", "medium", "low")
READINESS_ORDER: Tuple[str, ...] = ("go", "go-pending-approval", "no-go")
RUN_SORT_ORDER: Tuple[str, ...] = (
    "running",
    "merging",
    "queued",
    "done",
    "blocked",
    "failed",
)


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


# v1 scope (OQ3): specs + plans + research + prompts tracked; comms deferred to Phase 3; walkthroughs +
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
        True,
        "aw prompts",
        "staged prompts; lifecycle tracked by disposition directory (aw prompts)",
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
    # durablecapture-02 (`m867ox`) E-03: `reviews` was the only consequential tree that was ABSENT
    # from this inventory rather than DECIDED, which spec 20260808-1945-01 Section 8.6 calls a
    # violation ("every known tree is `tracked` ... or `excluded` (with rationale)"). It is EXCLUDED,
    # and the reason is decisive rather than a preference:
    #
    #   1. A REVIEW RECORD CARRIES NO `- Status:` FIELD AT ALL (measured over the whole live corpus:
    #      zero of 231 `.review.md` files contain one; the front matter is `Subject-Id`/`Subject-Type`/
    #      `Reviewed-At`/`Reviewer`/`Verdict`). This contract maps `(tree, native_status) -> class` and
    #      Section 6 requires that mapping be PURE and TOTAL over the tree's native enum while
    #      FORBIDDING the scanner to infer state from prose. A tree with no status field has no enum to
    #      be total over, so tracking it would need either a lifecycle the `reviews` owner has not
    #      defined or a class inferred from `Verdict`, and Section 6 forbids the second. This is the
    #      same rationale walkthroughs and roadmaps already carry ("no lifecycle status in v1").
    #   2. EXCLUSION LOSES NO ENFORCEMENT. `check.review-finding-unescalated` (severity `error`) and
    #      `check.review-decision-unescalated` (severity `warning`) already police review findings and
    #      decisions, so `aw attention` would add surfacing only, never a gate.
    #
    # NO SCAN ROOT IS ADDED FOR REVIEWS: `attention.scan` filters an excluded tree AFTER reading it
    # (`if not pol.tracked: continue`), so a root would cost 231 file reads per invocation for records
    # that are then discarded. Tracking the tree later is a CONTRACT change (a new native status
    # vocabulary plus an amendment to an `implemented` spec) and is maintainer scope, not a drive-by.
    TreePolicy(
        "reviews",
        ".agents/reviews",
        False,
        "",
        "review records carry NO `- Status:` field (Subject-Id/Subject-Type/Reviewed-At/Reviewer/Verdict only), so there is no native enum for the pure+total mapping Section 6 requires and inferring one from Verdict is forbidden; their findings are already policed as errors/warnings by check.review-finding-unescalated + check.review-decision-unescalated, so exclusion loses no enforcement",
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
# symbol per tree. Derived from lifecycle_dirs.LIFECYCLE_SUBDIRS["specs"].
SPEC_STATUSES: FrozenSet[str] = frozenset(_LD.LIFECYCLE_SUBDIRS["specs"])

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
    "todo": READY,  # rstodo p3o9je: canonical hot not-yet-worked state (renamed from `intake`)
    "active": ACTIVE,
    "reference": DONE,
    "archive": PARKED,
}

# Pipeline position mapping for research prompts (IPD 5e3nj2).
# Kept separate from _RESEARCH_MAP so MappingTotalityTests' assertion
# set(A.CLASS_MAPS["research"].keys()) == set(research_contract.STATUSES) remains exact.
_PROMPT_PIPELINE_MAP: Dict[str, str] = {
    "unrun": READY,
    "partial": ACTIVE,
    "synthesized": DONE,
}


# setupmarker Order 01: the AW operational-action ledger (and its _ACTIONS_MAP) was DELETED; it was
# redundant with the backlog tier and its scan stamped `.aw/state/` on read. The one reminder it held
# (setup-repo) is now the derived `.aw/setup-repo-needed.md` marker, not an attention tree.

# Backlog (attention-visible backlog tier; spec 20260813-1833-01). open -> ready (committed,
# actionable), blocked -> blocked (committed but gated; carries a typed Gate-Kind/Gate-Ref),
# parked -> parked (uncommitted "maybe"; auto-hidden from the default board), done -> done.
# bklgrad Order 01 (v58bvy) E-02: graduated -> ACTIVE. The item's design was handed off to a
# plan/spec and implementation work explicitly exists, which is exactly this contract's definition of
# `active` ("work is EXPLICITLY in progress (a native state says so); never inferred"). It is NOT
# `ready` (no action is owed on the ITEM; the action lives on its linked plans), NOT `done` (nothing is
# implemented), and NOT `parked` (the work is intentionally live). This choice also PRESERVES the
# release gate for free: `attention.release_blockers` skips an item only when its class is `done`, so a
# graduated item carrying `Blocks-Release` stays in the outstanding blocker set. Mapping it to `done`
# would have silently dropped it from that set.
_BACKLOG_MAP: Dict[str, str] = {
    "open": READY,
    "graduated": ACTIVE,
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

# Prompts (staging tree; plan `dx0u4s`): pending -> ready, executed -> done,
# superseded -> parked, not-executed -> parked, reusable -> parked (OQ-01).
_PROMPTS_MAP: Dict[str, str] = {
    "pending": READY,
    "executed": DONE,
    "superseded": PARKED,
    "not-executed": PARKED,
    "reusable": PARKED,
}

# lanestrand-01 (`pr5b0t`) E-03: LANES, the one attention-visible thing that is NOT A FILE.
#
# THE TREE IS SYNTHETIC AND HAS NO `TreePolicy` ENTRY, DELIBERATELY. Every other fragment here keys a
# tracked directory that `iter_scan_files` walks; a lane exists only as a git branch plus a run-record
# field, so no scanned FILE may ever classify as `lanes` and adding it to `TREE_POLICY` would invite a
# `SCAN_ROOTS` growth over `.aw/worktrees`, which `nuanaw` ask 4 and `xtklpd`'s measured ruling both
# forbid (a filesystem-derived verdict rewrites history). The fragment lives HERE anyway, rather than
# as a parallel lookup in `attention.py`, so a lane state nobody mapped raises `UnknownNativeStatus`
# through the SAME `class_of` every other tree uses: a new lane state is then LOUD instead of silently
# `ready`. This adds NO sixth attention class.
#
# THE KEYS ARE `runner_shared.LANE_REPORT_STATES`, and `tests/test_attention_contract.py` pins the two
# sets equal so a state added there cannot silently go unmapped here. They are not imported at module
# level because this module is deliberately dependency-light and must not pull the runner library into
# every attention scan.
#
# THE MAPPING IS PER PREDICATE OUTCOME, NOT ONE BLANKET CLASS (plan `pr5b0t` OQ-01, resolved):
#
#   STRANDED -> blocked  Work exists and has not reached the integration target. It cannot proceed
#                        without a human act (merge it, or decide to drop it), which is what `blocked`
#                        means everywhere else in this view.
#   UNKNOWN  -> blocked  The landing question could not be answered. Fail closed: a human must look.
#                        Classing it `ready` would print a green verdict the data does not support.
#   LIVE     -> active   A live process owns the lane, so work is EXPLICITLY in progress, which is this
#                        contract's own definition of `active` ("never inferred"). It is NOT `blocked`:
#                        nothing is owed by a human, and a view that reds during every normal driver run
#                        is a view operators learn to ignore.
#   LANDED   -> done     The work is reachable from the integration target. Nothing is owed ON THE LANE.
#                        This stays `done` even when the lane's PLAN is not yet `executed`: the plan has
#                        its own row in the `plans` tree and is already reported there, so classing the
#                        lane `active` too would double-count one piece of work as two attention items.
#   EMPTY    -> done     The lane holds no commits beyond its base and its tree is clean. There is
#                        nothing to lose and nothing to do.
#   SUPERSEDED -> done   The lane's OWN commits never reached the target, but its PLAN has reached a
#                        terminal directory, so a later attempt redid the work and landed it. `done` is
#                        correct for the same reason LANDED is: nothing is OWED, and nothing is at risk.
#                        It is deliberately NOT `blocked`: no human act is required to save anything,
#                        and classing it `blocked` is exactly what held this board at `VIEW INVALID` on
#                        ten already-landed lanes (2026-09-22), which is how a gate teaches operators to
#                        stop reading it. Pruning the husk is tidy-up, not owed work, so it is reported
#                        at `info` severity rather than carried as an attention item.
_LANES_MAP: Dict[str, str] = {
    "STRANDED": BLOCKED,
    "UNKNOWN": BLOCKED,
    "LIVE": ACTIVE,
    "LANDED": DONE,
    "EMPTY": DONE,
    "SUPERSEDED": DONE,
}

# The registry of mapping fragments, one per tracked tree (plus the synthetic `lanes` tree above).
CLASS_MAPS: Dict[str, Dict[str, str]] = {
    "specs": _SPEC_MAP,
    "plans": _PLANS_MAP,
    "research": _RESEARCH_MAP,
    "backlog": _BACKLOG_MAP,
    "releases": _RELEASES_MAP,
    "prompts": _PROMPTS_MAP,
    "lanes": _LANES_MAP,
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
#
# ``review_record`` (revsweep ``5slbpi`` E-04, spec ``6m4kow`` R-11) is a THIRD requirement kind and a
# variety of ``evidence``: the citation is not passed on the command line but must EXIST in the reviews
# tree as a conforming ``.review.md`` naming this artifact. It is enforced by the one shared predicate
# ``review_findings.review_attestation_missing``, consulted by BOTH spec-setting surfaces (the forked
# ``specs.run_set`` and ``status_set.validate_transition_allowed``) and by ``aw check``.
#
# WHY ``->reviewed`` NEEDED AN ENTRY AT ALL. It had none, so ``aw specs set reviewed <id6>`` succeeded
# with no review, no findings, and no record, while the SAME claim on a plan is policed by
# ``check.review-finding-unescalated`` and the approval verdict guard. Specs AUTHORIZE plans, so the
# least-attested transition in the tree sat at the top of the authority chain.
#
# HONEST LIMIT, and the reason this is the ``evidence`` kind rather than something stronger: presence,
# type, and parseability of the record are enforced; that the review was COMPETENT is not, and cannot
# be. See APPROVAL_FLOOR's identical caveat and spec ``25kzda`` Section 6.1. Do not describe this as a
# quality guarantee.
TRANSITION_AUTHORITY: Dict[str, Dict[str, object]] = {
    "->reviewed": {
        "who": "reviewer",
        "by_human": False,
        "human_token": False,
        "evidence": False,  # not a --evidence citation; see `review_record` below.
        "review_record": True,
    },
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
    "format + resolvability, NOT semantic verification that the work truly happened. The "
    "to-review -> reviewed transition requires a CONFORMING REVIEW RECORD naming the spec as its "
    "Subject-Id (revsweep 5slbpi); like the evidence citation it proves a review OCCURRED and was "
    "RECORDED, and it does NOT prove the review was competent."
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
# ``last_history_at`` is the date of the NEWEST record, which is the FIRST one in file order because
# every writer PREPENDS (see :func:`newest_history_record` for the measured reason this is not "last").
HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")


def newest_history_record(history_lines: List[str]) -> Optional[str]:
    """THE ONE RULE for "which of these ``## Workflow history`` lines is the newest": the FIRST one
    matching :data:`HISTORY_RECORD_RE`, or ``None`` when there is no record.

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
    ``attention._history_section_lines``), never whole file text.
    """

    for line in history_lines:
        if HISTORY_RECORD_RE.match(line):
            return line
    return None


def last_history_at(history_lines: List[str]) -> Optional[str]:
    """Derive ``last_history_at`` from parsed ``## Workflow history`` lines: the date of the NEWEST
    record, or ``None`` when there is no record. Never uses file mtime (Section 8.5).

    The NAME is historical and is kept because it is the published field name in
    ``aw attention --format json`` and in the spec's Section 8.5; it means "the date this artifact was
    last touched", never "the date on the last line". :func:`newest_history_record` is the single
    shared rule that decides which record that is, so no two readers in this toolkit can disagree
    about the answer.
    """

    newest = newest_history_record(history_lines)
    if newest is None:
        return None
    m = HISTORY_RECORD_RE.match(newest)
    return m.group("date") if m else None


# The ONE definition of "is this actor writable into a history line" (plan fn2l1u E-01).
#
# WHY IT LIVES HERE, since the placement was the one real constraint on this refactor. The check was
# born inside `ipd_lifecycle.retire_orchestrator`, but `status_set.apply_status_change` is the SINGLE
# writer of every artifact's history line and must call it too (E-07), and `ipd_lifecycle` already
# imports `status_set` (as `_ss`), so a helper hosted in `ipd_lifecycle` would force a cycle. This
# module is stdlib-only with ZERO package imports, already OWNS the history-record grammar
# (`HISTORY_RECORD_RE` directly above), and is already imported by both readers of that grammar
# (`plan_readiness`, `record_history`), so every caller can reach it and no cycle is possible.
#
# WHY THE REFUSAL SURVIVES THE READER WIDENING, which is the question a later reader will ask. Plan
# fn2l1u E-03/E-08 made the three readers TOLERANT of a parenthesized actor (lazy captures), so this
# guard is no longer propping up a parser limitation. It now enforces the CONVENTION: every writer in
# the toolkit emits the parenthesis-free `key=value` shape (`oc_runipd.driver_actor`), one shape is
# cheaper to read and grep than two, and a nested-paren actor is still ambiguous to a human skimming
# `- <date> <status> (<actor>): <msg>`. Refusing at the setter also keeps the failure BEFORE the
# lifecycle commit, which is the whole point: the alternative was a post-commit lint failure that
# left finalize `committed-incomplete` with a resume instruction that could not succeed.
ACTOR_PARENTHESIS_REMEDY = (
    "Render qualifiers as key=value (see oc_runipd.driver_actor), e.g. "
    "'opencode model=its_direct/some-model' rather than 'opencode (its_direct/some-model)'."
)


def actor_refusal(actor: Optional[str]) -> Optional[str]:
    """The reason ``actor`` may NOT be written into a ``## Workflow history`` line, or ``None`` if it may.

    Pure and total. Two refusals, in this order: an EMPTY (or whitespace-only) actor, and an actor
    containing a parenthesis. Callers must invoke this BEFORE any mutation - that ordering is the
    defect this helper exists to close (plan fn2l1u).

    The returned string is operator-facing documentation: it names the accepted shape rather than only
    rejecting the bad one, because the caller who tripped it needs to know what to type instead.
    """

    if actor is None or not actor.strip():
        return "a non-empty actor is required."
    stripped = actor.strip()
    if "(" in stripped or ")" in stripped:
        return (
            f"actor {stripped!r} contains a parenthesis. The history line is "
            "'- <date> <status> (<actor>): <msg>', and every writer in this toolkit emits a "
            f"parenthesis-free actor, so a nested parenthesis is ambiguous. {ACTOR_PARENTHESIS_REMEDY}"
        )
    return None


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
