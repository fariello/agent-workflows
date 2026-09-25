"""The runner-facing SELECTION POLICY: per-type classification, the action preview, and the
mixed-type confirmation gate (spec `25kzda` 2.5).

`aw oc run` / `aw agy run` accept ONE selector that may sweep up several KINDS of work item, and
each kind dispatches a different action. An operator who types one ambiguous word can therefore
authorize far more than they intended. Spec 25kzda 2.5 fixes the remedy: after resolution and
BEFORE any lease or host session, print a sorted count and action preview, and refuse to proceed
until the mixing is explicitly acknowledged (the exact phrase `run mixed` interactively, or
`--allow-mixed` unattended).

WHAT THIS MODULE IS NOT. It is not a resolver and not a dispatcher.

* RESOLUTION is owned by :mod:`agent_workflows.selectors`, whose :func:`selectors.resolve` is the
  ONE selector-to-file resolver for the package. Its `_PRECEDENCE` already implements spec 2.3
  step 3, and `UNIQUE_KINDS` + `Resolution.is_ambiguous` already implement spec 2.3 step 4 (an id6
  or canonical stem matching several files is repository corruption, not a multi-item selection).
  This module CONSUMES that; it re-derives neither precedence nor ambiguity.
* TYPING a path is owned by :func:`status_set.detect_artifact_type`.
* DISPATCH (actually performing review/plan/execute) belongs to the runners. This module only
  COUNTS what dispatch would do, which is what keeps the preview cheap and pure.

Pure + stdlib-only apart from those two in-package readers: every function here is a deterministic
function of its inputs, so no branch needs a TTY, a host, or a live run to test.

SCOPE LIMIT, stated so it is not mistaken for a claim: nothing consults this gate yet. It lands
tested and importable; wiring it into `oc_runipd.py` / `agy_runipd.py` is a deliberate follow-up
(IPD 6lu3rq OQ-01), as is WRITING the spec 2.5 bullet 4 ledger record. :func:`decide` RETURNS the
four facts that bullet requires (counts, preview, response-or-flag, queue digest) so the caller
that owns a live run can record them without re-deriving anything.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

from agent_workflows import selectors as _sel
from agent_workflows import status_set as _status_set

# --------------------------------------------------------------------------------------------------
# Type vocabulary: ONE data table mapping resolver type -> spec type
# --------------------------------------------------------------------------------------------------

# The two vocabularies differ in SPELLING for the same concept: `selectors.KNOWN_PRIMARY_TYPES` uses
# records-tree DIRECTORY names (`plans`, `specs`, ...), while spec 25kzda 2.2 uses SINGULAR canonical
# type names (`ipd`, `spec`, ...). Keeping two vocabularies for one concept is drift this repository
# repeatedly pays for, so the mapping lives here ONCE, as data, and every function below goes through
# it. A `None` value means the resolver type has NO spec type (it is not in spec 2.2's table at all).
SPEC_TYPE_BY_RESOLVER_TYPE: Mapping[str, Optional[str]] = {
    "plans": "ipd",
    "specs": "spec",
    "backlog": "backlog",
    "prompts": "prompt",
    "research": "research",
    "releases": "release",
    "walkthroughs": "walkthrough",
    # No spec 2.2 type. `comms` is inter-agent messaging and `roadmaps` is planning narrative;
    # neither is a runnable work item, so a selection containing one carries no spec type name.
    "comms": None,
    "roadmaps": None,
}

RESOLVER_TYPE_BY_SPEC_TYPE: Mapping[str, str] = {
    spec_type: resolver_type
    for resolver_type, spec_type in SPEC_TYPE_BY_RESOLVER_TYPE.items()
    if spec_type is not None
}

# Spec 2.2 declares exactly these seven canonical types, in this order. The ORDER is load-bearing:
# it is the deterministic sort key for the preview, and it is the order spec 2.5's own example
# renders (IPDs, Specs, Prompts), so reproducing it is what makes the preview comparable to the spec.
SPEC_TYPE_ORDER: Tuple[str, ...] = (
    "ipd",
    "spec",
    "backlog",
    "prompt",
    "research",
    "release",
    "walkthrough",
)

# Operator-facing plural labels for the preview (spec 2.5's example uses `IPDs:`, `Specs:`,
# `Prompts:`, so those three are transcribed from the spec rather than generated).
TYPE_LABELS: Mapping[str, str] = {
    "ipd": "IPDs",
    "spec": "Specs",
    "backlog": "Backlog items",
    "prompt": "Prompts",
    "research": "Research",
    "release": "Releases",
    "walkthrough": "Walkthroughs",
}

# --------------------------------------------------------------------------------------------------
# Action vocabulary
# --------------------------------------------------------------------------------------------------

ACTION_REVIEW = "review"
ACTION_PLAN = "plan"
ACTION_EXECUTE = "execute"
ACTION_SKIP = "skip"
# NOT an action: the honest answer when the action cannot be derived from STATUS alone, because the
# spec's dispatch tables branch on something this module deliberately does not see (a completeness
# check, `--full-auto`, `--action`, or a parsed run contract). A preview that guessed would be worse
# than one that admits the limit, and silently bucketing an undetermined item into `skip` or
# `execute` would misreport what the operator is authorizing.
ACTION_UNDETERMINED = "undetermined"

# Deterministic render order within a type. Matches spec 2.5's example on both of its rows
# (`2 review, 2 execute` and `1 review, 1 plan`).
ACTION_ORDER: Tuple[str, ...] = (
    ACTION_REVIEW,
    ACTION_PLAN,
    ACTION_EXECUTE,
    ACTION_SKIP,
    ACTION_UNDETERMINED,
)

# Per-type status -> action tables, transcribed from spec 25kzda Sections 3.2 through 3.6. These are
# DATA, not branching logic, so the whole preview policy is readable in one place. A status ABSENT
# from a table maps to ACTION_UNDETERMINED (see _action_for), which is also where an unknown status
# lands: spec 3.2/3.3/3.4 make an unknown status a red abort before sessions start, and this module
# must not pretend to know what such an item would do.
_IPD_ACTIONS: Mapping[str, str] = {
    # `draft` is deliberately absent: spec 3.2 splits it on a deterministic authoring-completeness
    # check (skip when it fails, review when it passes), which is content, not status.
    "to-review": ACTION_REVIEW,
    # `reviewed` is deliberately absent: spec 3.2 dispatches it on `--full-auto` (approval gate by
    # default, execute under full-auto), a flag this module does not see.
    "approved": ACTION_EXECUTE,
    "auto-approved": ACTION_EXECUTE,
    "reusable": ACTION_EXECUTE,
    "executed": ACTION_SKIP,
    "superseded": ACTION_SKIP,
    "not-executed": ACTION_SKIP,
}

_SPEC_ACTIONS: Mapping[str, str] = {
    # `draft` absent: split on a deterministic completeness check (spec 3.3).
    "to-review": ACTION_REVIEW,
    # `reviewed` absent: default is the human approval gate (needs input, not a runnable action);
    # only `--action review` makes it a review (spec 3.3).
    "approved": ACTION_PLAN,  # author conformant IPDs linked by From-Spec
    # `implementing` absent: it dispatches its From-Spec children as child queue items rather than
    # taking one action of its own (spec 3.3).
    "implemented": ACTION_SKIP,
    "deferred": ACTION_SKIP,
    "parked": ACTION_SKIP,
    "superseded": ACTION_SKIP,
}

_BACKLOG_ACTIONS: Mapping[str, str] = {
    "open": ACTION_PLAN,  # graduate: author the spec/IPDs it needs (spec 3.4)
    "blocked": ACTION_SKIP,
    "parked": ACTION_SKIP,
    "graduated": ACTION_SKIP,
    "done": ACTION_SKIP,
}

# Spec 3.6: research artifacts, release records, and walkthroughs are a GRAY SKIP at every valid
# status. They are inspectable dependencies and evidence, never executable payloads, so the action
# follows from the TYPE alone and no status table is needed.
_ALWAYS_SKIP_TYPES: frozenset = frozenset({"research", "release", "walkthrough"})

# Spec 3.5 dispatches a prompt on its parsed RUN CONTRACT, not on a status: a valid contract
# executes, a missing contract executes only after `run unverifiable` / `--allow-unverifiable`, and
# an invalid contract is a red fail. All three are content, not status. What they share is that a
# non-terminal prompt is an ATTEMPT to execute, which is what spec 2.5's example preview shows
# (`Prompts: 1 (1 execute)`), so a non-terminal prompt previews as `execute` and a terminal one as a
# skip. The limit is real and stated: this preview cannot distinguish the red-fail contract case.
_PROMPT_TERMINAL_SKIP: frozenset = frozenset({"executed", "superseded", "not-executed"})

_ACTION_TABLES: Mapping[str, Mapping[str, str]] = {
    "ipd": _IPD_ACTIONS,
    "spec": _SPEC_ACTIONS,
    "backlog": _BACKLOG_ACTIONS,
}


# --------------------------------------------------------------------------------------------------
# Structured results
# --------------------------------------------------------------------------------------------------


class ClassifiedItem(NamedTuple):
    """One resolved file, typed and given its previewed action."""

    path: Path
    spec_type: Optional[
        str
    ]  # spec 2.2 canonical type; None when the file has no spec type
    resolver_type: Optional[str]  # `selectors`/records-tree directory name
    status: Optional[str]
    action: str  # one of ACTION_ORDER


class TypeCount(NamedTuple):
    """The per-type half of the preview: how many items, and how many take each action."""

    spec_type: str
    label: str
    total: int  # NOT named `count`: that would shadow tuple.count on a NamedTuple
    by_action: Tuple[Tuple[str, int], ...]  # (action, count), in ACTION_ORDER


class Classification(NamedTuple):
    """A frozen, classified selection.

    ``counts`` is ordered by :data:`SPEC_TYPE_ORDER`, so it is stable, diffable, and testable.
    ``untyped`` holds resolved paths with no spec 2.2 type (a `comms`/`roadmaps` record, or a file
    whose type could not be determined); they are reported rather than dropped, and they never make
    a selection "mixed", because an unrunnable record is not a kind of work.
    """

    items: Tuple[ClassifiedItem, ...]
    counts: Tuple[TypeCount, ...]
    untyped: Tuple[Path, ...]

    @property
    def spec_types(self) -> Tuple[str, ...]:
        return tuple(c.spec_type for c in self.counts)

    @property
    def type_count(self) -> int:
        return len(self.counts)

    @property
    def is_mixed(self) -> bool:
        """True when the selection spans MORE THAN ONE spec 2.2 type (what 2.5 gates)."""
        return self.type_count > 1


class MixedTypeRecord(NamedTuple):
    """The four facts spec 25kzda 2.5 bullet 4 requires to be recorded in the run ledger.

    This module RETURNS them; it does not write them. Writing needs a live run's context (the ledger
    store), which is the runner surface IPD 6lu3rq deliberately does not touch. Returning them is
    the seam that makes that wiring trivial rather than archaeological, and it is what makes an
    `--allow-mixed` run auditable: without it there is no durable evidence of the counts that were
    waved through.

    * ``type_counts``      - the confirmed per-type counts, as {spec_type: count}.
    * ``action_preview``   - the rendered preview text the operator saw (or would have seen).
    * ``response_or_flag`` - what satisfied (or failed) the gate: the literal typed response, or
                             ``--allow-mixed``, or ``None`` when no gate applied.
    * ``queue_digest``     - the deterministic digest of the frozen selection.
    """

    type_counts: Mapping[str, int]
    action_preview: str
    response_or_flag: Optional[str]
    queue_digest: str

    def as_dict(self) -> Dict[str, object]:
        """A JSON-ready mapping, for a caller appending to the run ledger."""
        return {
            "type_counts": dict(self.type_counts),
            "action_preview": self.action_preview,
            "response_or_flag": self.response_or_flag,
            "queue_digest": self.queue_digest,
        }


class Verdict(NamedTuple):
    """The definite outcome of the mixed-type gate.

    ``proceed`` is the whole decision; ``reason`` is a caller-printable explanation; ``code`` and
    ``message`` carry the spec's finding code and verbatim refusal on a refusal (both None on a
    proceed); ``record`` always carries the spec 2.5 bullet 4 facts.
    """

    proceed: bool
    reason: str
    gate_applied: bool
    code: Optional[str]
    message: Optional[str]
    record: MixedTypeRecord

    # `--allow-mixed` acknowledges type mixing ONLY (spec 2.5, third bullet). The EXHAUSTIVE set of
    # gates this decision can satisfy, exposed so a caller (and a test) can prove the flag is not a
    # general override seam: every status, approval, prompt-verifiability, scope, and safety gate
    # still applies and is enforced elsewhere. Deliberately UNANNOTATED: an annotation would make it
    # a seventh NamedTuple FIELD instead of a class constant.
    WAIVES = ("type-mixing",)


# --------------------------------------------------------------------------------------------------
# E-04: the finding code and its VERBATIM refusal text
# --------------------------------------------------------------------------------------------------

# A cross-artifact contract string (one of spec 25kzda 4.2's `RUN-*` codes). Do NOT rename it.
RUN_MIXED_TYPES = "RUN-MIXED-TYPES"

# Transcribed CHARACTER-FOR-CHARACTER from spec 25kzda 2.5's "Exact refusal" block. Do not compose
# your own wording: the code prefix, the counts, the `No work started.` claim, and the recovery
# command are all fixed by the spec. `<counts>`, `<host>`, and `<selector>` are the substitution
# points; `--type <type> ...` is LITERAL spec text (the operator is being shown the shape of the
# narrowing flag, not a resolved value).
#
# `No work started.` is a BEHAVIORAL GUARANTEE, not decoration. This gate runs after resolution and
# before leases or sessions (spec 2.5), and every function in this module is pure, so a refusal is
# provably incapable of having started work: there is nothing here that could open a session, take a
# lease, or write to the repository.
REFUSAL_TEMPLATE = (
    "[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, "
    "then run: aw <host> run <selector> --type <type> ... --allow-mixed"
)

# The exact phrase an interactive operator must type (spec 2.5, first bullet). `y`, an empty
# response, and any generic confirmation are rejected.
CONFIRM_PHRASE = "run mixed"

ALLOW_MIXED_FLAG = "--allow-mixed"


# --------------------------------------------------------------------------------------------------
# E-01: classification
# --------------------------------------------------------------------------------------------------


def _action_for(spec_type: Optional[str], status: Optional[str]) -> str:
    """The previewed action for one item, from its TYPE and STATUS only (spec Sections 3.2-3.6)."""

    if spec_type is None:
        # No spec 2.2 type: not a runnable work item, so nothing would be dispatched for it.
        return ACTION_SKIP
    if spec_type in _ALWAYS_SKIP_TYPES:
        return ACTION_SKIP  # spec 3.6 gray skip, from the type alone
    if spec_type == "prompt":
        if status is not None and status in _PROMPT_TERMINAL_SKIP:
            return ACTION_SKIP
        return ACTION_EXECUTE  # spec 3.5; contract validity is content, not status
    table = _ACTION_TABLES.get(spec_type)
    if table is None or status is None:
        return ACTION_UNDETERMINED
    return table.get(status, ACTION_UNDETERMINED)


def classify_paths(
    repo_root: Path,
    paths: Sequence[Path],
    *,
    statuses: Optional[Mapping[Path, str]] = None,
) -> Classification:
    """Group an ALREADY-RESOLVED selection by canonical type, with per-type and per-action counts.

    Typing defers to :func:`status_set.detect_artifact_type` (the shipped authority) and the type
    name is mapped through :data:`SPEC_TYPE_BY_RESOLVER_TYPE`; status is read by
    :func:`status_set.read_artifact_record`. Nothing here re-derives resolution or typing.

    ``statuses`` optionally supplies a status per path, so a caller that already parsed the files
    (and a test) need not touch the filesystem twice.
    """

    repo_root = Path(repo_root)
    items: List[ClassifiedItem] = []
    untyped: List[Path] = []

    for raw in paths:
        p = Path(raw)
        resolver_type = _status_set.detect_artifact_type(p, repo_root)
        spec_type = (
            SPEC_TYPE_BY_RESOLVER_TYPE.get(resolver_type) if resolver_type else None
        )
        status: Optional[str] = None
        if statuses is not None and p in statuses:
            status = statuses[p]
        elif spec_type is not None:
            rec = _status_set.read_artifact_record(p, repo_root)
            status = rec.status if rec is not None else None
        item = ClassifiedItem(
            path=p,
            spec_type=spec_type,
            resolver_type=resolver_type,
            status=status,
            action=_action_for(spec_type, status),
        )
        items.append(item)
        if spec_type is None:
            untyped.append(p)

    return Classification(
        items=tuple(items),
        counts=_counts_for(items),
        untyped=tuple(untyped),
    )


def _counts_for(items: Sequence[ClassifiedItem]) -> Tuple[TypeCount, ...]:
    """Per-type counts with the per-action breakdown, ordered by :data:`SPEC_TYPE_ORDER` (E-02)."""

    per_type: Dict[str, List[ClassifiedItem]] = {}
    for it in items:
        if it.spec_type is None:
            continue
        per_type.setdefault(it.spec_type, []).append(it)

    out: List[TypeCount] = []
    for spec_type in SPEC_TYPE_ORDER:
        group = per_type.get(spec_type)
        if not group:
            continue
        by_action: Dict[str, int] = {}
        for it in group:
            by_action[it.action] = by_action.get(it.action, 0) + 1
        ordered = tuple(
            (action, by_action[action])
            for action in ACTION_ORDER
            if action in by_action
        )
        out.append(
            TypeCount(
                spec_type=spec_type,
                label=TYPE_LABELS[spec_type],
                total=len(group),
                by_action=ordered,
            )
        )
    return tuple(out)


def resolve_selection(
    repo_root: Path,
    selector: str,
    *,
    spec_types: Sequence[str],
) -> Tuple[Classification, Tuple[str, ...]]:
    """Resolve ONE selector across the named spec types by CALLING :func:`selectors.resolve`, then
    classify the union.

    Returns ``(classification, errors)``. ``errors`` is non-empty when a selector matched a
    UNIQUE-kind (path/id6/stem) collision, which spec 2.3 step 4 defines as repository corruption
    rather than a multi-item selection; that policy is :mod:`selectors`' own
    (``UNIQUE_KINDS`` + ``Resolution.is_ambiguous``) and is applied, not reimplemented, here.

    Deduplicates by resolved path (spec 2.3 step 5 dedupes by identity, never by the spelling of the
    selector).
    """

    repo_root = Path(repo_root)
    errors: List[str] = []
    ordered: List[Path] = []
    seen: set = set()

    for spec_type in spec_types:
        resolver_type = RESOLVER_TYPE_BY_SPEC_TYPE.get(spec_type)
        if resolver_type is None:
            errors.append("unknown type {0!r}".format(spec_type))
            continue
        res = _sel.resolve(repo_root, resolver_type, selector)
        if res.is_ambiguous and res.kind in _sel.UNIQUE_KINDS:
            errors.append(
                "selector {0!r} is a {1} collision matching multiple {2} files".format(
                    selector, res.kind, resolver_type
                )
            )
            continue
        for p in res.paths:
            key = str(p)
            if key not in seen:
                seen.add(key)
                ordered.append(p)

    return classify_paths(repo_root, ordered), tuple(errors)


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-02/E-05: THE ONE needs-review PREDICATE (spec 25kzda 2.4a property 2)
# --------------------------------------------------------------------------------------------------
#
# WHY IT LIVES HERE AND WHY THERE IS EXACTLY ONE. Spec 2.4a property 2 is normative: an item is in the
# `reviews` sweep IF AND ONLY IF Section 3's dispatch table gives it a review action at its current
# status, and "there is exactly one implementation of that predicate, shared by every host and by the
# preview". That rule exists because the repository already paid for its absence: each host runner's
# `expand_selectors` carried its OWN `_needs_review` closure testing `status == "to-review"`, while
# `determine_action` routed `to-review` AND `draft` to `review`. So a complete draft named EXPLICITLY
# was reviewed and the SAME draft was silently absent from the sweep, and because the closure was
# duplicated VERBATIM in both runners (differing only in a loop variable name), fixing one host would
# have left the other wrong.
#
# MEMBERSHIP IS DERIVED, NOT RESTATED. The predicate asks `_action_for` - the same function the
# preview uses - whether the row's action is :data:`ACTION_REVIEW`. A corrected copy of the
# `to-review` string comparison would still be a copy, and the next status added would diverge again.
#
# THE ONE THING STATUS CANNOT ANSWER, so it is an INPUT and never a guess: `_IPD_ACTIONS` and
# `_SPEC_ACTIONS` deliberately OMIT `draft`, because spec 3.2/3.3 split a draft on a deterministic
# AUTHORING-COMPLETENESS check (incomplete -> skip with findings, complete -> promote and review), and
# completeness is CONTENT. The caller supplies the answer (from `ipd_authoring
# .authoring_placeholders_resolved`, the shipped anchored check the `check.ipd-draft-ready-to-review`
# rule already uses); a second completeness heuristic here would make the nudge and the sweep disagree
# about the same draft. Absent that input a draft is NOT swept, which is the fail-safe direction.
#
# `ACTION_UNDETERMINED` IS NOT "NEEDS REVIEW". `reviewed` is also undetermined (it branches on
# `--full-auto`/`--action`), so treating undetermined as review-worthy would sweep up plans that are
# past review entirely. Only the `draft` row consults the completeness input; every other undetermined
# row answers False.


#: The DISPOSITION directories whose contents are past (or outside) the pending lifecycle. Checked in
#: ADDITION to status, never instead of it: a directory and a `- Status:` line CAN disagree, and spec
#: 3.2 makes that mismatch a red abort rather than a review, so an item in a terminal directory must
#: not be swept into a review turn no matter what its front matter claims. Both deleted `_needs_review`
#: closures performed exactly this check; it is preserved here rather than dropped as redundant.
TERMINAL_DIRECTORY_SEGMENTS: Tuple[str, ...] = (
    "/executed/",
    "/superseded/",
    "/not-executed/",
    "/reusable/",
)


def is_in_terminal_directory(file_path: object) -> bool:
    """True when a repository-relative (or absolute) artifact path sits in a terminal disposition."""

    text = str(file_path or "").replace("\\", "/")
    if not text:
        return False
    if not text.startswith("/"):
        text = "/" + text
    return any(seg in text for seg in TERMINAL_DIRECTORY_SEGMENTS)


def review_depends_on_completeness(
    spec_type: Optional[str], status: Optional[str]
) -> bool:
    """True when this (type, status) row's review answer needs the COMPLETENESS input.

    Exposed so a caller can read plan TEXT for exactly the candidates that need it and no others.
    The alternative - the caller hardcoding `status == "draft"` - would put a second copy of the
    dispatch table's one content-dependent row at the call site, which is the shape of defect this
    whole module exists to remove. Today only `draft` qualifies, on both the `ipd` and `spec` tables.
    """

    norm = (status or "").strip().lower()
    if norm != "draft":
        return False
    return spec_type in _ACTION_TABLES


def needs_review(
    spec_type: Optional[str],
    status: Optional[str],
    *,
    authoring_complete: Optional[bool] = None,
    file_path: object = None,
) -> bool:
    """THE needs-review predicate (spec 25kzda 2.4a property 2). One implementation, both hosts.

    ``spec_type`` is a spec 2.2 canonical type name (`ipd`, `spec`, ...). TYPE-AWARE BY SIGNATURE AND
    IPD-ONLY BY REACH (E-05): the tables consulted include `spec`, so handed a spec this answers
    correctly, but NOTHING IN THE PACKAGE CAN CURRENTLY HAND IT ONE - `runner_shared.discover_plans`
    walks only the two plans trees and neither host registers `--type`, so every live caller passes
    `"ipd"`. That gap is real and is owned by `5slbpi` (cross-type discovery); it is stated HERE, at
    the definition, so a later reader does not conclude from this signature that cross-type sweeping
    works.

    ``authoring_complete`` answers the ONE question status cannot (see the section note above). It is
    consulted only for the rows :func:`review_depends_on_completeness` names. `None` means "not
    determined", and an undetermined draft is NOT swept: an unreadable file or an absent repo must
    fail toward excluding an item, never toward promoting a stub through `to-review`.

    ``file_path`` applies the terminal-directory exclusion when supplied.
    """

    if file_path is not None and is_in_terminal_directory(file_path):
        return False
    norm = (status or "").strip().lower() or None
    action = _action_for(spec_type, norm)
    if action == ACTION_REVIEW:
        return True
    if action == ACTION_UNDETERMINED and review_depends_on_completeness(
        spec_type, norm
    ):
        # spec 3.2/3.3's draft split, decided by the caller's deterministic completeness check.
        # `bool(None)` is False on purpose: undetermined completeness excludes.
        return bool(authoring_complete)
    # Every other ACTION_UNDETERMINED row (notably `reviewed`) answers False. Treating undetermined
    # as review-worthy is the failure mode that would sweep up plans already past review.
    return False


# --------------------------------------------------------------------------------------------------
# E-02: the action preview
# --------------------------------------------------------------------------------------------------


def render_action_preview(
    classification: Classification,
    *,
    header: str = "Mixed work-item selection:",
    action_labels: Optional[Mapping[str, str]] = None,
) -> str:
    """Render the sorted count + action preview in spec 25kzda 2.5's exact shape::

        Mixed work-item selection:
          IPDs:    4 (2 review, 2 execute)
          Specs:   2 (1 review, 1 plan)
          Prompts: 1 (1 execute)

    Deterministic: type order is :data:`SPEC_TYPE_ORDER` and action order is
    :data:`ACTION_ORDER`, so two renders of the same selection are byte-identical.

    ``header`` and ``action_labels`` GENERALIZE this one renderer for spec 2.5a's draft preview,
    whose header differs and whose breakdown reads `2 draft -> to-review -> review` rather than
    `2 review`. Both default to spec 2.5's wording, so every existing caller is unchanged. A SECOND
    renderer was the alternative and was rejected: the alignment rule, the type order, the action
    order, and the untyped-tail line would then exist twice and drift once.
    """

    if not classification.counts:
        return header + "\n  (nothing selected)"

    labels = dict(action_labels or {})
    width = max(len(c.label) + 1 for c in classification.counts) + 1
    lines = [header]
    for c in classification.counts:
        breakdown = ", ".join(
            "{0} {1}".format(n, labels.get(action, action)) for action, n in c.by_action
        )
        lines.append(
            "  {0}{1} ({2})".format((c.label + ":").ljust(width), c.total, breakdown)
        )
    if classification.untyped:
        lines.append(
            "  (plus {0} selected file(s) with no runnable type)".format(
                len(classification.untyped)
            )
        )
    return "\n".join(lines)


def render_counts_inline(classification: Classification) -> str:
    """The compact `<counts>` substitution for the refusal message, e.g.
    ``IPDs: 4, Specs: 2, Prompts: 1``. Same deterministic type order as the preview."""

    if not classification.counts:
        return "nothing"
    return ", ".join("{0}: {1}".format(c.label, c.total) for c in classification.counts)


# --------------------------------------------------------------------------------------------------
# Queue digest (spec 2.5 bullet 4)
# --------------------------------------------------------------------------------------------------


def queue_digest(classification: Classification) -> str:
    """A deterministic sha256 over the FROZEN selection: the sorted (spec_type, path, action)
    triples. Independent of input ordering, machine, and run, so the same selection always yields
    the same digest and a later ledger reader can prove which queue was acknowledged."""

    payload = sorted(
        [
            str(it.spec_type or ""),
            str(it.path),
            it.action,
        ]
        for it in classification.items
    )
    blob = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------------
# E-03 / E-04: the gate
# --------------------------------------------------------------------------------------------------


def is_confirmation_accepted(
    response: Optional[str], *, phrase: str = CONFIRM_PHRASE
) -> bool:
    """True only for the EXACT confirmation phrase (spec 2.5 first bullet; 2.5a for `run drafts`).

    Surrounding whitespace is stripped, because a terminal read includes the newline the operator
    pressed; nothing else is normalized. Case is NOT folded and no synonym is accepted, so `y`,
    `yes`, `Y`, an empty response, `run`, and `run mixed types` are all rejected. The point of an
    exact phrase is that it cannot be produced by a reflex keystroke.

    ``phrase`` PARAMETERIZES the expected phrase rather than admitting a second implementation for
    spec 2.5a's `run drafts`. That matters more than it looks: a parallel matcher is precisely how
    `y` eventually becomes acceptable SOMEWHERE, since the two copies are then free to relax
    independently. Default unchanged, so every existing caller keeps spec 2.5's phrase.
    """

    if response is None:
        return False
    return response.strip() == phrase


def render_refusal(
    classification: Classification,
    *,
    host: str = "<host>",
    selector: str = "<selector>",
) -> str:
    """The spec's VERBATIM refusal with `<counts>` (and optionally `<host>`/`<selector>`) filled in.

    Defaults keep the placeholders literal so the rendered string can be compared character-for-
    character against spec 2.5's exact refusal block.
    """

    return (
        REFUSAL_TEMPLATE.replace("<counts>", render_counts_inline(classification))
        .replace("<host>", host)
        .replace("<selector>", selector)
    )


def decide(
    classification: Classification,
    *,
    interactive: bool,
    allow_mixed: bool = False,
    response: Optional[str] = None,
    host: str = "<host>",
    selector: str = "<selector>",
) -> Verdict:
    """Decide whether a selection may proceed through the mixed-type gate (spec 25kzda 2.5).

    PURE: no TTY, no host, no filesystem, no ledger. The caller performs the actual prompt and hands
    the typed ``response`` in, which is what makes every branch testable.

    The three cases spec 2.5 fixes:

    * a SINGLE-type selection proceeds with NO gate at all;
    * an INTERACTIVE multi-type selection requires the exact phrase `run mixed` (`y`, an empty
      response, and any generic confirmation are rejected);
    * an UNATTENDED multi-type selection is refused unless ``--allow-mixed`` was on the original
      command.

    ``allow_mixed`` acknowledges TYPE MIXING ONLY (spec 2.5, third bullet). It is deliberately the
    only override this function accepts, so this predicate can never become the place another gate
    is waived; see :data:`Verdict.WAIVES`.

    The returned :class:`Verdict` always carries a :class:`MixedTypeRecord` with the four facts spec
    2.5 bullet 4 requires to be recorded in the run ledger.
    """

    preview = render_action_preview(classification)
    digest = queue_digest(classification)
    type_counts = {c.spec_type: c.total for c in classification.counts}

    def _verdict(
        proceed: bool,
        reason: str,
        gate_applied: bool,
        response_or_flag: Optional[str],
        refuse: bool = False,
    ) -> Verdict:
        return Verdict(
            proceed=proceed,
            reason=reason,
            gate_applied=gate_applied,
            code=RUN_MIXED_TYPES if refuse else None,
            message=(
                render_refusal(classification, host=host, selector=selector)
                if refuse
                else None
            ),
            record=MixedTypeRecord(
                type_counts=type_counts,
                action_preview=preview,
                response_or_flag=response_or_flag,
                queue_digest=digest,
            ),
        )

    if not classification.is_mixed:
        # Single-type (or empty) selection: the gate does not apply at all. Not "passed", ungated.
        return _verdict(
            True,
            "selection spans a single work-item type; the mixed-type gate does not apply",
            gate_applied=False,
            response_or_flag=None,
        )

    if allow_mixed:
        return _verdict(
            True,
            "type mixing acknowledged by {0} (and only type mixing: every status, approval, "
            "prompt-verifiability, scope, and safety gate still applies)".format(
                ALLOW_MIXED_FLAG
            ),
            gate_applied=True,
            response_or_flag=ALLOW_MIXED_FLAG,
        )

    if interactive:
        if is_confirmation_accepted(response):
            return _verdict(
                True,
                "type mixing acknowledged by the exact phrase {0!r}".format(
                    CONFIRM_PHRASE
                ),
                gate_applied=True,
                response_or_flag=response,
            )
        return _verdict(
            False,
            "interactive confirmation requires the exact phrase {0!r}; got {1!r}".format(
                CONFIRM_PHRASE, response
            ),
            gate_applied=True,
            response_or_flag=response,
            refuse=True,
        )

    return _verdict(
        False,
        "unattended mixed-type selection refused: {0} was not present on the original "
        "command".format(ALLOW_MIXED_FLAG),
        gate_applied=True,
        response_or_flag=None,
        refuse=True,
    )


# --------------------------------------------------------------------------------------------------
# revsweep-02 (`6ypimw`) E-03: THE DRAFT ADMISSION GATE (spec 25kzda 2.5a)
# --------------------------------------------------------------------------------------------------
#
# WHAT IT DECIDES AND WHY IT IS A SEPARATE FUNCTION. Promoting a `draft` to `to-review` is a lifecycle
# WRITE the operator did not literally name, so spec 2.5a admits a complete draft reached through a
# STATUS selector (`reviews`/`all`) only through an explicit acknowledgement - and, like the Section
# 2.5 mixed-type gate, asks it ONCE after resolution and BEFORE any lease or session, so a batch never
# stops to ask halfway through.
#
# NOT A PARAMETER ON `decide`. `Verdict.WAIVES` and `decide`'s docstring record that `allow_mixed` is
# deliberately the ONLY override that predicate accepts, "so this predicate can never become the place
# another gate is waived". Bolting `--allow-drafts` on would break exactly that property, so this is a
# SIBLING decision function that reuses `decide`'s primitives (`is_confirmation_accepted`,
# `render_action_preview`) rather than its signature.
#
# TWO ASYMMETRIES ARE DELIBERATE, and both are spec 2.5a's. They look like inconsistencies and will
# invite a "simplification", so each is commented at its branch with the reason.

#: Spec 4.2 finding code for the unattended exclusion. A cross-artifact contract string; do NOT rename.
RUN_DRAFTS_EXCLUDED = "RUN-DRAFTS-EXCLUDED"

#: Transcribed CHARACTER-FOR-CHARACTER from spec 25kzda 2.5a's "Exact refusal" block. `<count>`,
#: `<remaining>`, `<host>`, and `<selector>` are the substitution points; do not recompose the wording.
#: Note this text says the drafts were EXCLUDED and that other items PROCEEDED - it is not a
#: "No work started." refusal, because this gate excludes items rather than refusing the run.
DRAFTS_EXCLUDED_TEMPLATE = (
    "[RUN-DRAFTS-EXCLUDED] Selection included <count> complete draft item(s), excluded because "
    "--allow-drafts was absent. <remaining> item(s) proceeded. To include them, run: "
    "aw <host> run <selector> --allow-drafts"
)

#: The exact phrase an interactive operator must type (spec 2.5a). `y` and an empty response are
#: rejected, by the same matcher spec 2.5's phrase uses.
DRAFTS_CONFIRM_PHRASE = "run drafts"

ALLOW_DRAFTS_FLAG = "--allow-drafts"

#: The draft preview's header and its per-action label, both transcribed from spec 2.5a's example
#: block (`IPDs:  2 (2 draft -> to-review -> review)`).
DRAFTS_PREVIEW_HEADER = (
    "Selection includes complete drafts that will be promoted to to-review:"
)
DRAFTS_ACTION_LABELS: Mapping[str, str] = {
    ACTION_REVIEW: "draft -> to-review -> review"
}


class DraftAdmissionRecord(NamedTuple):
    """The four facts spec 25kzda 2.5a's last bullet requires in the run ledger.

    RETURNED, NEVER WRITTEN, exactly as :class:`MixedTypeRecord` is and for the same reason: writing
    needs a live run's ledger store, which this pure module has no business holding. The runner
    persists this; that seam is also what makes an `--allow-drafts` run auditable, since without it
    there is no durable evidence of which drafts were waved through.

    * ``draft_counts``     - complete-draft counts per spec type, as {spec_type: count}.
    * ``preview``          - the rendered preview the operator saw (or would have seen); "" when the
                             gate did not apply, because there was nothing to preview.
    * ``response_or_flag`` - the literal typed response, or ``--allow-drafts``, or ``None``.
    * ``admitted``         - the identities of the drafts actually admitted (empty when excluded).
    """

    draft_counts: Mapping[str, int]
    preview: str
    response_or_flag: Optional[str]
    admitted: Tuple[str, ...]

    def as_dict(self) -> Dict[str, object]:
        """A JSON-ready mapping, for a caller appending to the run ledger."""
        return {
            "draft_counts": dict(self.draft_counts),
            "preview": self.preview,
            "response_or_flag": self.response_or_flag,
            "admitted": list(self.admitted),
        }


class DraftCandidate(NamedTuple):
    """One `draft`-status item the caller resolved, with the completeness answer it read.

    ``identity`` is whatever the caller uses to name the item (an id6 for the runners). ``complete``
    is the deterministic authoring-completeness answer, `None` when it could not be determined -
    which is treated as INCOMPLETE, the fail-safe direction.
    """

    identity: str
    spec_type: Optional[str]
    complete: Optional[bool]


class DraftVerdict(NamedTuple):
    """The outcome of the draft admission gate.

    ``admitted`` are the identities that may proceed to a review turn; ``excluded_complete`` are the
    complete drafts the gate withheld; ``skipped_incomplete`` are the drafts spec 2.5a's first bullet
    keeps out at EVERY flag setting. ``message`` carries the verbatim `RUN-DRAFTS-EXCLUDED` text on an
    unattended exclusion and is `None` otherwise. There is NO `proceed` field, deliberately: this gate
    can never refuse a run (see the asymmetry note in :func:`decide_draft_admission`).
    """

    admitted: Tuple[str, ...]
    excluded_complete: Tuple[str, ...]
    skipped_incomplete: Tuple[str, ...]
    gate_applied: bool
    reason: str
    code: Optional[str]
    message: Optional[str]
    record: DraftAdmissionRecord

    #: The EXHAUSTIVE set of gates `--allow-drafts` satisfies (spec 2.1: "It waives no other gate").
    #: Mirrors `Verdict.WAIVES` so neither flag can quietly become a general override seam. In
    #: particular a promoted draft still faces the approval gate, unchanged.
    WAIVES = ("draft-admission",)


def render_drafts_preview(
    classification: Classification,
    *,
    incomplete_count: int = 0,
) -> str:
    """Spec 2.5a's draft preview, rendered by the SAME renderer spec 2.5's preview uses::

        Selection includes complete drafts that will be promoted to to-review:
          IPDs:  2 (2 draft -> to-review -> review)
          Specs: 1 (1 draft -> to-review -> review)
        Also skipping 1 incomplete draft (findings will be reported).

    The trailing incomplete line is spec 2.5a's own, and it is printed because an operator deciding
    whether to admit drafts must see that some drafts CANNOT be admitted; omitting it would let them
    read the count as complete.
    """

    text = render_action_preview(
        classification,
        header=DRAFTS_PREVIEW_HEADER,
        action_labels=DRAFTS_ACTION_LABELS,
    )
    if incomplete_count:
        text += "\nAlso skipping {0} incomplete draft{1} (findings will be reported).".format(
            incomplete_count, "" if incomplete_count == 1 else "s"
        )
    return text


def render_drafts_exclusion(
    *,
    excluded_count: int,
    remaining_count: int,
    host: str = "<host>",
    selector: str = "<selector>",
) -> str:
    """Spec 2.5a's VERBATIM exclusion notice with its substitution points filled in."""

    return (
        DRAFTS_EXCLUDED_TEMPLATE.replace("<count>", str(excluded_count))
        .replace("<remaining>", str(remaining_count))
        .replace("<host>", host)
        .replace("<selector>", selector)
    )


def _draft_classification(candidates: Sequence[DraftCandidate]) -> Classification:
    """A Classification over the COMPLETE drafts only, so the shared renderer can count them."""

    items = [
        ClassifiedItem(
            path=Path(c.identity),
            spec_type=c.spec_type,
            resolver_type=None,
            status="draft",
            action=ACTION_REVIEW,
        )
        for c in candidates
        if c.complete
    ]
    return Classification(
        items=tuple(items),
        counts=_counts_for(items),
        untyped=tuple(i.path for i in items if i.spec_type is None),
    )


def decide_draft_admission(
    candidates: Sequence[DraftCandidate],
    *,
    interactive: bool,
    allow_drafts: bool = False,
    response: Optional[str] = None,
    remaining_count: int = 0,
    host: str = "<host>",
    selector: str = "<selector>",
) -> DraftVerdict:
    """Decide which `draft` items a STATUS selector may admit (spec 25kzda 2.5a).

    PURE: no TTY, no filesystem, no ledger. The caller performs the prompt (if it has any way to) and
    hands the typed ``response`` in, which is what makes every branch testable - the same discipline
    :func:`decide` follows.

    ``candidates`` are the `draft`-status items the caller RESOLVED, each already carrying its
    deterministic completeness answer. ``remaining_count`` is how many NON-draft items are in the
    queue, used only to fill spec 2.5a's `<remaining>` substitution honestly.

    THE FIRST DELIBERATE ASYMMETRY (spec 2.5a bullet 1): an INCOMPLETE draft is a SKIP WITH FINDINGS
    at EVERY setting of every flag. `--allow-drafts` cannot admit one, and it is never an abort,
    because one unfinished draft must not deny review to the finished items beside it, and never an
    error, because `draft` is a legitimate resting state. It does not even reach the gate.

    THE SECOND DELIBERATE ASYMMETRY (spec 2.5a bullet 4): an ungated COMPLETE draft is EXCLUDED and
    the REST OF THE QUEUE PROCEEDS. That differs from :func:`decide`'s mixed-type refusal, which
    starts no work at all, and the difference is intentional rather than an oversight: a MIXED
    selection means the operator's intent is genuinely unclear, so starting any work risks doing the
    wrong thing, whereas an ungated draft is ONE item's admission and the remaining items' intent is
    not in doubt. Refusing the whole run would punish the clear items for the unclear one. Do NOT
    "fix" this into a uniform rule; that is why :class:`DraftVerdict` has no `proceed` field at all.
    """

    incomplete = tuple(sorted(c.identity for c in candidates if not c.complete))
    complete = tuple(sorted(c.identity for c in candidates if c.complete))
    classification = _draft_classification(candidates)
    draft_counts = {c.spec_type: c.total for c in classification.counts}

    def _verdict(
        admitted: Tuple[str, ...],
        excluded: Tuple[str, ...],
        reason: str,
        gate_applied: bool,
        response_or_flag: Optional[str],
        preview: str = "",
        message: Optional[str] = None,
    ) -> DraftVerdict:
        return DraftVerdict(
            admitted=admitted,
            excluded_complete=excluded,
            skipped_incomplete=incomplete,
            gate_applied=gate_applied,
            reason=reason,
            code=RUN_DRAFTS_EXCLUDED if message else None,
            message=message,
            record=DraftAdmissionRecord(
                draft_counts=draft_counts,
                preview=preview,
                response_or_flag=response_or_flag,
                admitted=admitted,
            ),
        )

    if not complete:
        # Nothing to gate. Note the incomplete drafts are still REPORTED (they are in
        # `skipped_incomplete`), because spec 2.5a requires their findings, not their silence.
        return _verdict(
            (),
            (),
            "no complete draft in the selection; the draft admission gate does not apply",
            gate_applied=False,
            response_or_flag=None,
        )

    preview = render_drafts_preview(classification, incomplete_count=len(incomplete))

    if allow_drafts:
        return _verdict(
            complete,
            (),
            "complete draft promotion acknowledged by {0} (and only that: the approval gate a "
            "promoted draft still has to pass is unaffected)".format(ALLOW_DRAFTS_FLAG),
            gate_applied=True,
            response_or_flag=ALLOW_DRAFTS_FLAG,
            preview=preview,
        )

    if interactive and is_confirmation_accepted(response, phrase=DRAFTS_CONFIRM_PHRASE):
        return _verdict(
            complete,
            (),
            "complete draft promotion acknowledged by the exact phrase {0!r}".format(
                DRAFTS_CONFIRM_PHRASE
            ),
            gate_applied=True,
            response_or_flag=response,
            preview=preview,
        )

    # EXCLUDE-AND-PROCEED, both interactively (phrase absent or wrong) and unattended (flag absent).
    # See the second asymmetry above: this is not a refusal and must never become one.
    return _verdict(
        (),
        complete,
        "complete draft(s) excluded: {0}".format(
            "the exact phrase {0!r} was not given".format(DRAFTS_CONFIRM_PHRASE)
            if interactive
            else "{0} was not present on the original command".format(ALLOW_DRAFTS_FLAG)
        ),
        gate_applied=True,
        response_or_flag=response if interactive else None,
        preview=preview,
        message=render_drafts_exclusion(
            excluded_count=len(complete),
            remaining_count=remaining_count,
            host=host,
            selector=selector,
        ),
    )


class CombinedGateVerdict(NamedTuple):
    """Spec 2.5a bullet 5: BOTH gates decided in ONE interaction, before any work starts.

    ``mixed`` is :func:`decide`'s verdict and ``drafts`` is :func:`decide_draft_admission`'s.
    ``proceed`` is the mixed gate's alone, because the draft gate excludes items and never refuses a
    run (the asymmetry documented on :func:`decide_draft_admission`).

    WHY THE COMBINATION IS ITS OWN FUNCTION rather than two calls at the call site: spec 2.5a requires
    the two previews printed TOGETHER and both confirmations collected in ONE interaction, since
    "front-loading every question is the point; a second prompt after the first item has run defeats
    it". Two independent calls sequenced by a caller is exactly how the second question drifts later
    in the run, so the ordering is encoded here once.
    """

    proceed: bool
    mixed: Verdict
    drafts: DraftVerdict

    @property
    def combined_preview(self) -> str:
        """Both previews, mixed first, joined by a blank line; only the parts that applied."""
        parts = [
            p
            for p in (
                self.mixed.record.action_preview if self.mixed.gate_applied else "",
                self.drafts.record.preview,
            )
            if p
        ]
        return "\n\n".join(parts)


def decide_selection_gates(
    classification: Classification,
    draft_candidates: Sequence[DraftCandidate],
    *,
    interactive: bool,
    allow_mixed: bool = False,
    allow_drafts: bool = False,
    mixed_response: Optional[str] = None,
    drafts_response: Optional[str] = None,
    remaining_count: int = 0,
    host: str = "<host>",
    selector: str = "<selector>",
) -> CombinedGateVerdict:
    """Decide spec 2.5's and 2.5a's gates TOGETHER, in one interaction (spec 2.5a bullet 5).

    Both responses are taken as INPUTS, which is what makes "one interaction" achievable at all: a
    caller that had to call one gate, print, prompt, then call the other could not collect both
    answers before either decision. Pure, like everything else in this module.
    """

    mixed = decide(
        classification,
        interactive=interactive,
        allow_mixed=allow_mixed,
        response=mixed_response,
        host=host,
        selector=selector,
    )
    drafts = decide_draft_admission(
        draft_candidates,
        interactive=interactive,
        allow_drafts=allow_drafts,
        response=drafts_response,
        remaining_count=remaining_count,
        host=host,
        selector=selector,
    )
    return CombinedGateVerdict(proceed=mixed.proceed, mixed=mixed, drafts=drafts)


# --------------------------------------------------------------------------------------------------
# runnoop Order 02 (`m85gxh`): the PER-ARTIFACT DISPOSITION LINE
# --------------------------------------------------------------------------------------------------
#
# WHAT WAS ACTUALLY MISSING, stated precisely because the obvious reading of the defect is too strong
# and leads to building the wrong thing (plan F-8, re-measured at execution 2026-09-19 at HEAD
# `7562ca6c`). TWO shipped surfaces ALREADY name every matched artifact:
#
#   * `render_stream.format_run_order_announcement`, printed unconditionally at queue freeze, lists
#     every matched id6 in execution order; and
#   * `render_stream.render_run_summary_table` renders ONE ROW PER MATCHED ARTIFACT carrying its id6,
#     set, action and disposition, INCLUDING an item with ZERO attempts.
#
# So the line is not missing. What is missing is the REASON. Measured by rendering the real summary
# with a single `reviewed`/zero-attempt item: the row `01 | 01 | abc123 | wtiso | execute | reviewed`
# is present, the progress line reads `1/1 [##########] 100% (1 reviewed)`, and the string `approval`
# appears ZERO times, because that renderer's diagnostics block emits a reason only for an item
# carrying a `Refusal` record or one of four legacy fields. A reader therefore sees `reviewed` and has
# to already know it means "frozen, needing human approval, never dispatched".
#
# THIS IS THEREFORE A REASON RENDERER, NOT A THIRD QUEUE LISTING. An implementation that re-lists the
# queue without a reason satisfies the words "one line per matched artifact" and fixes NOTHING.
#
# WHY IT LIVES HERE. This module is the established PURE-RENDERER home for run-selection output
# (`render_action_preview`, `render_counts_inline`, `render_refusal`, `render_drafts_preview`,
# `render_drafts_exclusion`), and `render_action_preview`'s docstring already records the
# anti-duplication rule this follows ("the alignment rule, the type order, the action order, and the
# untyped-tail line would then exist twice and drift once"). `render_stream` is NOT an alternative
# home for anything that must read runner-computed selection data: `runner_shared` imports
# `render_stream` at module level, so the reverse edge would be a cycle.
#
# WHY IT COEXISTS WITH `render_stream`'s DIAGNOSTICS BLOCK rather than replacing it. That block is
# owned by `orchprobe` `r2i1b1` (executed) and renders a `Refusal` record's reason and REMEDY for any
# status. It only fires when a producer RECORDED a refusal, and nothing records one for an artifact
# the run never dispatched, which is exactly this plan's case. The two surfaces are deliberately
# complementary: the diagnostics block explains an item the run ACTED on and refused, while this line
# explains every matched artifact including the ones no code ever touched. See
# `reason_from_refusal` for how this renderer CONSUMES that record rather than formatting a parallel
# reason string when one exists.


#: The closed, documented set of reasons a matched artifact was NOT acted on (`m85gxh` E-02).
#:
#: NAMES COME FROM SPEC `25kzda`, NOT FROM THIS MODULE. Every name below is transcribed from that
#: approved spec so the run's human output and its machine reason codes cannot use two vocabularies
#: for one fact:
#:
#:   * `needs_human_approval`          spec 5.4 "Stable dependency reason codes" (source outcome for
#:                                     "Human gate stopped prerequisite") and 5.7 ("Human gate |
#:                                     Required human receipt absent | Persist and stop").
#:   * `dependency_not_met`            spec 5.4 (the direct/transitive dependent outcome) and 5.7.
#:   * `dependency_not_met_external`   spec 5.4 ("Dependency omitted from queue and currently
#:                                     unsatisfied").
#:   * `ipd_already_executed`          spec 6's worked example, item 8 (`done08`): "Status/directory,
#:                                     dependency statement, and terminal evidence are checked. No
#:                                     session or mutation occurs." -> `skipped`,
#:                                     `ipd_already_executed`.
#:   * `type_or_status_not_runnable`   spec 5.7 ("Non-runnable state/type | Valid terminal/gated/
#:                                     narrative record | Skip without a session").
#:   * `host_capability_unavailable`   spec 5.4 and 5.7 ("Host guarantee unavailable ... Refuse the
#:                                     item before session start").
#:
#: NOTHING IS MINTED HERE. The backlog item (`em0z50`) named six reasons in prose and the plan
#: expected two of them ("already executed", "status not runnable") to need new names because spec
#: 5.4's table is dependency-scoped. Re-measured at execution: both ARE named by the spec, just in
#: OTHER sections (6's example and 5.7's failure-class table), so no coinage is required and none is
#: made.
#:
#: HONEST BINDING LIMIT, so a reader does not over-trust the alignment: most of these strings are not
#: bound to a shipped constant anywhere else (measured 2026-09-19: `needs_human_approval` and
#: `type_or_status_not_runnable` each grep to ZERO other occurrences under `agent_workflows/`;
#: `dependency_not_met` exists only as a `run_evidence.AggregatedItem` boolean field;
#: `host_capability_unavailable` IS bound, at `host_sandbox_profile.REASON_HOST_CAPABILITY_UNAVAILABLE`).
#: So no contract test would go red if these diverged from the spec; they follow it anyway, and the
#: authority is cited above so the next reader can check rather than guess.
SKIP_NEEDS_HUMAN_APPROVAL = "needs_human_approval"
SKIP_DEPENDENCY_NOT_MET = "dependency_not_met"
SKIP_DEPENDENCY_NOT_MET_EXTERNAL = "dependency_not_met_external"
SKIP_ALREADY_EXECUTED = "ipd_already_executed"
SKIP_NOT_RUNNABLE = "type_or_status_not_runnable"
SKIP_HOST_CAPABILITY_UNAVAILABLE = "host_capability_unavailable"

#: Where each reason's VALUE is read from in a live run, as data rather than as prose, so a caller
#: never recomputes a fact the runner already decided. Each entry names the shipped producer.
#:
#: The two deliberate ABSENCES from the backlog item's list of six, each with the measurement:
#:
#:   * "GATE REFUSED" IS NOT ONE REASON AND MOSTLY IS NOT PER-ARTIFACT AT ALL. Measured at HEAD
#:     `7562ca6c` by reading `runner_shared.initialize_run_core`: of the five gates it runs before the
#:     run directory exists, FOUR refuse the WHOLE RUN by raising `DriverError` (the mixed-type gate,
#:     the requested-action legality check, the dependency preflight, and `refuse_unimplemented_run_flags`),
#:     so no artifact of that run ever reaches a per-artifact line and a reason value for them could
#:     never render. They are excluded for that reason. The FIFTH, the draft-admission gate, genuinely
#:     excludes PER ARTIFACT (`enforce_draft_admission_gate` returns a filtered `queue_ids` and
#:     contains no `raise`) - but it runs at offset 70 of `initialize_run_core` while the run directory
#:     is not created until offset 134, so an excluded draft never enters the queue, has no queue entry
#:     and no disposition. Its exclusion is ALREADY reported, verbatim from spec 2.5a, by
#:     `render_drafts_exclusion` above, which is the renderer this module already owns and which this
#:     one therefore does NOT duplicate.
#:   * `host_capability_unavailable` IS per-artifact by construction
#:     (`host_sandbox_profile.preflight_host_capabilities` returns `aborts_run=False`,
#:     `cascade_dependents=True`) and IS spec-named, so it is KEPT in the vocabulary above. But
#:     measured: neither driver nor `runner_shared` calls that preflight (zero occurrences of
#:     `preflight_host_capabilities` in all three files), so no run can produce it TODAY. It is listed
#:     so the reason exists when the preflight is wired, and this note exists so nobody reports it as
#:     a reason a current run can emit.
SKIP_REASON_SOURCES: Mapping[str, str] = {
    SKIP_NEEDS_HUMAN_APPROVAL: (
        "the durable queue-entry flag `runner_shared.NEEDS_INPUT_KEY`, frozen at queue-build time by "
        "`runner_shared.item_needs_approval` (runnoop Order 01, `zz5yxq` E-03)"
    ),
    SKIP_DEPENDENCY_NOT_MET: (
        "`item['unsatisfied_dependencies']` plus `item['unsatisfied_dependency_reasons']`, written by "
        "each driver's drain path from `dependency_status_detailed`/`edge_satisfied`"
    ),
    SKIP_DEPENDENCY_NOT_MET_EXTERNAL: (
        "the same two keys; `edge_satisfied`'s EXTERNAL branch marks a target that is not in the queue "
        "and cannot become satisfied in this run ('it is not in this run, so it cannot become "
        "satisfied here')"
    ),
    SKIP_ALREADY_EXECUTED: (
        "the queue entry's own status, preserved verbatim as `executed` by "
        "`runner_shared.initial_queue_status` via `TERMINAL_QUEUE_STATUSES`"
    ),
    SKIP_NOT_RUNNABLE: (
        "the queue entry's frozen `initial_status` plus its queue `status`: a plan whose on-disk status "
        "is terminal-but-not-`executed` (`superseded`, `not-executed`) or absent falls back to the "
        "queue status `reviewed` without being approval-blocked (`initial_queue_status`, and "
        "`item_needs_approval` returning False)"
    ),
    SKIP_HOST_CAPABILITY_UNAVAILABLE: (
        "`host_sandbox_profile.preflight_host_capabilities`' refusal "
        "(`REASON_HOST_CAPABILITY_UNAVAILABLE`). NOT REACHABLE TODAY: neither driver calls that "
        "preflight (measured zero call sites), so no current run emits this reason"
    ),
}

#: The reason vocabulary as a tuple, in the render/documentation order above. CLOSED: a caller may
#: pass any reason TEXT it likes to :func:`render_item_disposition`, but a reason CODE outside this set
#: is a programming error, so :func:`skip_reason_text` refuses one rather than inventing a label.
SKIP_REASONS: Tuple[str, ...] = (
    SKIP_NEEDS_HUMAN_APPROVAL,
    SKIP_DEPENDENCY_NOT_MET,
    SKIP_DEPENDENCY_NOT_MET_EXTERNAL,
    SKIP_ALREADY_EXECUTED,
    SKIP_NOT_RUNNABLE,
    SKIP_HOST_CAPABILITY_UNAVAILABLE,
)

#: The human gloss rendered beside each reason code, so the line explains itself to a reader who does
#: not know the code. The CODE is always printed too (it is the machine-stable half and the thing a
#: later `aw runs` surface can key on); the gloss is what makes `reviewed` legible without the reader
#: already knowing what `reviewed` means, which is this plan's whole point.
SKIP_REASON_LABELS: Mapping[str, str] = {
    SKIP_NEEDS_HUMAN_APPROVAL: (
        "frozen awaiting human approval; reviewed but not approved, so it was never dispatched"
    ),
    SKIP_DEPENDENCY_NOT_MET: "a declared dependency was not satisfied in this run",
    SKIP_DEPENDENCY_NOT_MET_EXTERNAL: (
        "a declared dependency is outside this run's queue and unsatisfied, so it cannot be met here"
    ),
    SKIP_ALREADY_EXECUTED: "already executed on disk, so there was nothing to do",
    SKIP_NOT_RUNNABLE: "its status is not runnable, so no session was appropriate",
    SKIP_HOST_CAPABILITY_UNAVAILABLE: (
        "the host could not prove a capability this action requires"
    ),
}

#: The label used when an artifact WAS acted on, so the acted-on and skipped lines are the same shape.
#: Deliberately a fixed word rather than an empty string: a reader scanning a column of lines must be
#: able to see that the run DID act on this one, and a blank reads as missing information.
ACTED_REASON_LABEL = "acted on by this run"


def skip_reason_text(code: str) -> str:
    """The human gloss for one CLOSED skip-reason code. Raises `ValueError` on an unknown code.

    FAILS CLOSED ON PURPOSE. A renderer that silently accepted an unknown code would let a caller
    invent a seventh reason at a call site, which is precisely the "a reason is a value rather than an
    ad-hoc string" property E-02 exists to establish.
    """

    norm = str(code or "").strip()
    if norm not in SKIP_REASON_LABELS:
        raise ValueError(
            "unknown skip reason code {0!r}; the closed set (spec 25kzda 5.4/5.7/6) is: {1}".format(
                code, ", ".join(SKIP_REASONS)
            )
        )
    return SKIP_REASON_LABELS[norm]


def reason_from_refusal(refusal: object) -> Optional[str]:
    """The reason text carried by a `render_stream.Refusal`, or ``None`` when there is none.

    E-05's INTEGRATION SEAM WITH `orchprobe` `r2i1b1` (executed; read at execution time, as this
    plan's E-05 requires). That plan ships the per-item refusal RECORD (`code`/`reason`/`remedy`) and
    owns it; this plan defines no record type and must not. Where a run DID record a refusal for an
    item, this line reports THAT record's reason rather than formatting a parallel string, so the two
    surfaces cannot disagree about why one item was refused.

    DUCK-TYPED RATHER THAN IMPORTED, deliberately: importing `render_stream` here would add a
    first-party import to a module whose two-import purity is a property other plans depend on, for no
    gain, since all this needs is the `reason` attribute. The remedy is deliberately NOT rendered
    here; the summary's diagnostics block already prints it on its own line and duplicating it would
    put the same remedy on the operator's screen twice.
    """

    if refusal is None:
        return None
    reason = getattr(refusal, "reason", None)
    if isinstance(reason, str) and reason.strip():
        return reason.strip()
    return None


def render_item_disposition(
    identity: str,
    action: Optional[str],
    disposition: Optional[str],
    reason: Optional[str] = None,
    *,
    position: Optional[int] = None,
    setid: Optional[str] = None,
) -> str:
    """ONE line describing what happened to ONE matched artifact (`m85gxh` E-01).

    THE SAME FUNCTION RENDERS BOTH CASES, acted-on and skipped, which is the requirement: the backlog
    item asks that a skipped artifact be reported "in the SAME shape as an acted-on one", and two
    renderers would drift exactly as `render_action_preview`'s docstring records. ``reason`` is the
    only field that differs, and it is never blank: an acted-on artifact carries
    :data:`ACTED_REASON_LABEL`, so every line has the same fields in the same order and a reader can
    scan the column.

    PURE. Builds and returns a string; prints nothing, opens nothing, imports no runner. Every input
    is a plain value the caller already has, which is what makes each branch testable without a run.

    ``reason`` is free TEXT, not a code, because three different kinds of thing legitimately fill it:
    :func:`skip_reason_text`'s gloss for a closed code, a `Refusal` record's own reason (via
    :func:`reason_from_refusal`), and a dependency reason string naming the unmet edge. Compose it
    with :func:`render_item_disposition_for_reason` when you have a CLOSED code, which is the path
    that keeps the vocabulary closed.

    Shape::

        - 01 abc123 [wtiso] execute -> reviewed: needs_human_approval (frozen awaiting human ...)
        - 02 def456 [wtiso] execute -> executed: acted on by this run
    """

    ident = str(identity or "?").strip() or "?"
    head = "- "
    if position is not None:
        head += "{0:02d} ".format(int(position))
    head += ident
    if setid:
        head += " [{0}]".format(str(setid).strip())
    act = str(action or "?").strip() or "?"
    disp = str(disposition or "?").strip() or "?"
    text = str(reason or "").strip() or ACTED_REASON_LABEL
    return "{0} {1} -> {2}: {3}".format(head, act, disp, text)


def render_item_disposition_for_reason(
    identity: str,
    action: Optional[str],
    disposition: Optional[str],
    code: str,
    *,
    detail: Optional[str] = None,
    position: Optional[int] = None,
    setid: Optional[str] = None,
) -> str:
    """:func:`render_item_disposition` for a CLOSED reason code, printing the code AND its gloss.

    The code is what a later machine surface can key on; the gloss is what makes the line legible to a
    reader who does not already know the code. ``detail`` appends run-specific specifics, which is how
    the dependency reasons NAME the unmet dependency (the backlog item requires that specifically)
    without a second renderer.

    Raises `ValueError` for a code outside :data:`SKIP_REASONS`, via :func:`skip_reason_text`.
    """

    gloss = skip_reason_text(code)
    if detail and str(detail).strip():
        gloss = "{0}; {1}".format(gloss, str(detail).strip())
    return render_item_disposition(
        identity,
        action,
        disposition,
        "{0} ({1})".format(str(code).strip(), gloss),
        position=position,
        setid=setid,
    )


#: The header printed above the per-artifact block, so a reader knows the list is EVERY artifact the
#: selector matched rather than only the interesting ones. Worded to state the guarantee, because the
#: guarantee (nothing matched is omitted) is what makes the block answerable to "what did the run
#: ignore, and why?".
DISPOSITION_HEADER = "Per-artifact disposition (every artifact this selector matched):"


class ItemDisposition(NamedTuple):
    """What ONE matched artifact's disposition WAS, derived once and consumed by every surface.

    THE REASON THIS TYPE EXISTS IS THAT TWO SURFACES MUST NOT DERIVE THE SAME FACT TWICE (`bsc457`
    E-01). The per-artifact LINE (`m85gxh`) and the per-disposition COUNTS (this plan) are the same
    judgement rendered two ways, so the judgement is made ONCE, here, and both callers read it. Had
    the counts re-derived it, the line and the count could disagree about the same artifact, which is
    exactly the drift `render_action_preview`'s docstring records as the reason this module forbids a
    second renderer.

    Fields:
      ``code``   the disposition key the counts group by: a member of :data:`SKIP_REASONS`, a
                 `Refusal` record's own ``code``, or :data:`DISPOSITION_ACTED_ON` when the run acted.
      ``reason`` the human reason TEXT for the line (already composed, including any gloss/detail).
      ``remedy`` the remedy carried BY A RECORDED REFUSAL, when there was one, or ``None``. Only a
                 `Refusal` supplies this; everything else resolves through
                 :func:`remedy_for_disposition`, so this plan maintains no second copy of the
                 remedies `orchprobe` `r2i1b1` already records per item.
    """

    code: str
    reason: Optional[str]
    remedy: Optional[str] = None


#: The count key for an artifact the run DID act on (or is still acting on). A real key rather than
#: the absence of one, because the counts must SUM to the number matched, which they cannot do if the
#: acted-on artifacts fall outside the partition.
DISPOSITION_ACTED_ON = "acted_on"


def derive_item_disposition(
    entry: Mapping[str, object],
    refusal_reader: Optional[Callable[..., object]] = None,
) -> ItemDisposition:
    """Decide ONE matched artifact's disposition from the facts the runner already computed.

    Extracted from :func:`render_queue_dispositions` by `bsc457` E-01 with its precedence UNCHANGED,
    so the per-artifact line's behavior is byte-identical and the counts cannot key on a different
    judgement than the line displays. Precedence, and why (unchanged from `m85gxh`):

      1. A recorded `Refusal` (`orchprobe` `r2i1b1`) wins, because a producer that explicitly said why
         it refused THIS item is more specific than anything inferable from its status. Its own
         ``code`` becomes the count key and its own ``remedy`` travels with it.
      2. Then the durable needs-approval flag (`runnoop` `zz5yxq`), which is the measured case this
         whole Set exists for.
      3. Then the dependency reasons, which NAME the unmet edge.
      4. Then `executed`, which is a real disposition and not a defect.
      5. Then a queue status that is terminal without the run having acted, which is the honest
         "not runnable" answer.
      6. Otherwise the artifact was acted on (or is still in flight) and carries
         :data:`DISPOSITION_ACTED_ON`, whose line text is :data:`ACTED_REASON_LABEL`.
    """

    get = entry.get
    status = str(get("status") or "").strip()

    refusal = refusal_reader(entry) if refusal_reader is not None else None
    refusal_reason = reason_from_refusal(refusal)
    if refusal_reason:
        # THE REFUSAL'S OWN CODE AND REMEDY ARE SOURCED, NOT RE-DERIVED (`bsc457` E-06's executed
        # branch). `r2i1b1` is `- Status: executed`, so its record carries `code`/`reason`/`remedy`
        # and is the authority for an item it refused; this plan defines no second remedy for such an
        # item. Duck-typed for the same reason `reason_from_refusal` is: importing `render_stream`
        # here would add a first-party import to a module whose two-import purity other plans depend
        # on, for no gain.
        code = getattr(refusal, "code", None)
        remedy = getattr(refusal, "remedy", None)
        return ItemDisposition(
            str(code).strip() if isinstance(code, str) and code.strip() else "refused",
            refusal_reason,
            str(remedy).strip() if isinstance(remedy, str) and remedy.strip() else None,
        )

    if bool(get("needs_input")):
        return ItemDisposition(
            SKIP_NEEDS_HUMAN_APPROVAL,
            "{0} ({1})".format(
                SKIP_NEEDS_HUMAN_APPROVAL, skip_reason_text(SKIP_NEEDS_HUMAN_APPROVAL)
            ),
        )

    raw_deps = get("unsatisfied_dependencies")
    if isinstance(raw_deps, (list, tuple)) and raw_deps:
        deps = [str(d) for d in raw_deps]
        raw_why = get("unsatisfied_dependency_reasons")
        why: Mapping[str, object] = raw_why if isinstance(raw_why, Mapping) else {}
        # NO PLACEHOLDER WHEN NO REASON WAS RECORDED, because the two producers of this key
        # write DIFFERENT shapes and a blanket fallback double-reports. Measured at HEAD
        # `7562ca6c`: the drain path writes a BARE token plus a separate
        # `unsatisfied_dependency_reasons` map, while `cascade_dependency_blocked` writes the
        # reason INTO the token (`executed:aaa111 (target reviewed)`) and writes NO map at all.
        # A `reasons.get(d, "unsatisfied")` fallback therefore renders the cascade's already-
        # explained token as `executed:aaa111 (target reviewed) (unsatisfied)`, which reads as
        # two contradictory reasons. `render_stream`'s diagnostics block carries the same fallback
        # shape (`reasons.get(d, "blocked")`) and the same wart; that block is outside this
        # plan's fence, so the divergence is REPORTED rather than edited here.
        named = ", ".join(
            "{0} ({1})".format(d, why[d]) if d in why else str(d) for d in deps
        )
        # The EXTERNAL variant is distinguished by the reason text `edge_satisfied` already
        # writes for a target outside the queue, rather than by a second computation here.
        code = (
            SKIP_DEPENDENCY_NOT_MET_EXTERNAL
            if "not in this run" in named
            else SKIP_DEPENDENCY_NOT_MET
        )
        return ItemDisposition(
            code,
            "{0} ({1}; unmet: {2})".format(code, skip_reason_text(code), named),
        )

    if status == "executed" and not get("attempts"):
        return ItemDisposition(
            SKIP_ALREADY_EXECUTED,
            "{0} ({1})".format(
                SKIP_ALREADY_EXECUTED, skip_reason_text(SKIP_ALREADY_EXECUTED)
            ),
        )

    if status in ("reviewed", "not-attempted", "not-run") and not get("attempts"):
        return ItemDisposition(
            SKIP_NOT_RUNNABLE,
            "{0} ({1})".format(SKIP_NOT_RUNNABLE, skip_reason_text(SKIP_NOT_RUNNABLE)),
        )

    return ItemDisposition(DISPOSITION_ACTED_ON, None)


def render_queue_dispositions(
    entries: Sequence[Mapping[str, object]],
    *,
    header: str = DISPOSITION_HEADER,
    # Typed loosely on PURPOSE: the shipped reader this is designed to receive
    # (`render_stream.refusal_of_item`) is annotated `dict[str, Any] -> Refusal | None`, and a
    # narrower parameter type here would make the real call site a type error for no behavioral gain.
    # This module must not import `render_stream` to name that type (see `reason_from_refusal`).
    refusal_reader: Optional[Callable[..., object]] = None,
) -> List[str]:
    """Render ONE line per matched artifact, from the facts the runner already computed.

    ``entries`` are the run's queue entries (or any mapping carrying the same keys), which is what
    makes the once-per-artifact property structural rather than a discipline the caller has to
    remember: the queue holds exactly one entry per matched artifact no matter how many ATTEMPTS an
    item accumulated, so iterating it once cannot produce two lines for one artifact.

    Returns a LIST OF LINES rather than printing, and rather than one joined string, so the caller
    owns the stream and an empty selection renders as an empty list instead of a stray header.

    ``refusal_reader`` is how E-05's integration with `orchprobe` `r2i1b1` is wired without this
    module importing `render_stream`: the caller passes that plan's shipped ONE READER
    (`render_stream.refusal_of_item`), which is the function every other surface goes through, so a
    recorded refusal's reason reaches this line through the same seam rather than through a second
    reading of the same key. Omitted, no refusal is consulted, which is the correct behavior for a
    caller that has no run state.

    THE REASON IS DERIVED ONCE, BY :func:`derive_item_disposition`, from the shipped producers named
    in :data:`SKIP_REASON_SOURCES`; nothing is recomputed here and nothing is recomputed by the
    per-disposition SUMMARY either (`bsc457` E-01), which reads the same derivation. That shared
    judgement is what makes the line and the counts structurally unable to disagree about one
    artifact. See that function for the precedence and for why each step is ordered as it is.
    """

    lines: List[str] = []
    for entry in entries:
        get = entry.get
        decided = derive_item_disposition(entry, refusal_reader)
        lines.append(
            render_item_disposition(
                str(get("id6") or get("identity") or "?"),
                str(get("action") or ""),
                str(get("status") or "").strip(),
                decided.reason,
                position=(
                    int(get("position"))  # type: ignore[arg-type]
                    if isinstance(get("position"), int)
                    else None
                ),
                setid=str(get("setid") or "") or None,
            )
        )
    if not lines:
        return []
    return [header] + lines


# --------------------------------------------------------------------------------------------------
# The END-OF-RUN DISPOSITION SUMMARY: counts, and the REMEDY for each actionable disposition
# (`runnoop` Order 03, `bsc457`)
# --------------------------------------------------------------------------------------------------
#
# WHAT THIS BLOCK IS FOR, AND WHAT IT IS DELIBERATELY NOT. The obvious reading is that it duplicates
# the exit summary TABLE, and that reading is why this note is long. Measured at execution time by
# rendering the real `render_stream.render_run_summary_table` with one `reviewed`/zero-attempt item:
# it ALREADY prints a bordered table containing a per-artifact row
# (`01 | 01 | abc123 | wtiso | execute | reviewed`), a count line (`Progress: 1/1 [##...] 100%
# (1 reviewed)`) and a totals row. So a THIRD listing of the queue would satisfy the words "a line per
# matched artifact and a per-disposition count line" while fixing nothing an operator cares about
# (this plan's F-8, and the specific failure its review exists to prevent).
#
# The three things the table genuinely lacks, which are therefore this block's whole content:
#
#   1. AN HONEST VERDICT. That same render says `Outcome: COMPLETED` at `100%` for a run that
#      performed ZERO work, because the COMPLETED tuple contains `reviewed`. This block states what
#      the run actually DID, so a reader is not told a no-op succeeded. The table's own `Outcome:` is
#      NOT edited here: that expression belongs to `orchprobe` `r2i1b1`'s fence (this plan's OQ-02),
#      and if the two visibly disagree that is a finding to report, not a quiet cross-fence edit.
#   2. THE REMEDY. A count without one tells an operator they are stuck. `AGENTS.md` and `r2i1b1`'s
#      OQ-01 both record the measured failure mode: a message saying only "X is not allowed" gets
#      complied with by DELETING the thing, when a correct non-destructive fix exists.
#   3. COUNTS THAT KEY ON A DISPOSITION rather than on a queue STATUS. The table's count line groups
#      by queue status, a different denominator: `reviewed` is one status covering both "frozen
#      awaiting approval" and "not runnable", and it is silent about WHY.
#
# SELF-CONTAINED ON PURPOSE (this plan's OQ-01, resolved from the maintainer's four-place ruling
# recorded in `r2i1b1`'s OQ-01). The block repeats its own counts and remedies rather than referring
# upward to the table, because readers pipe runner output through `head` or `tail`; a `tail` reader
# must need nothing above it. The START side is already satisfied by shipped code
# (`announce_run_order` prints the matched order unconditionally, and a start-side print cannot carry
# dispositions that do not exist yet), so this plan adds only the END.


#: The remedy for each disposition that an operator can ACT on, as data beside the disposition rather
#: than a string at a call site, so a new disposition cannot be added without an author noticing its
#: remedy is missing.
#:
#: EVERY COMMAND HERE WAS VERIFIED BY RUNNING ITS `--help` AT EXECUTION TIME, not written from memory
#: (this plan's E-02 requires it and V-02 pastes the output). What was checked:
#:
#:   * `aw ipd set approved <id6> --by-human` - `aw ipd set --help` lists `--by-human` and its
#:     positional syntax is `<status> <selector...>`.
#:   * `--full-auto` - `aw oc run start --help` states it "Clear[s] a plan that is already
#:     'Status: reviewed' to 'auto-approved'" and, verbatim, "This records an AUTOMATED clear, NOT
#:     human approval: no --by-human attestation is asserted". The wording below therefore does NOT
#:     claim it grants human approval; overstating what a remedy grants is worse than omitting it
#:     (executed plan `97df1z`, and the shipped provenance string "auto-approved by --full-auto:
#:     review readiness cleared (not human approval)").
#:   * `aw host capabilities` - exists, "Print[s] the host capability contract and the per-action
#:     verdicts derived from it".
#:   * `aw find plans <id6>` - `aw find --help` takes `[type] [selector ...]`.
#:
#: A DISPOSITION ABSENT FROM THIS MAPPING IS NOT AUTOMATICALLY "no remedy": see
#: :func:`remedy_for_disposition`, which distinguishes the three cases (a known remedy, a disposition
#: that legitimately needs none, and one whose remedy is UNKNOWN) rather than rendering the last two
#: alike.
DISPOSITION_REMEDIES: Mapping[str, str] = {
    SKIP_NEEDS_HUMAN_APPROVAL: (
        "approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. "
        "`--full-auto` instead clears a `reviewed` plan to `auto-approved` (an AUTOMATED clear, "
        "NOT human approval)"
    ),
    SKIP_DEPENDENCY_NOT_MET: (
        "run the dependency to its declared state first, or include it in the same selector so this "
        "run can satisfy the edge"
    ),
    SKIP_DEPENDENCY_NOT_MET_EXTERNAL: (
        "the dependency is outside this run's queue, so widen the selector to include it (or run it "
        "first); this run cannot satisfy the edge no matter how often it is resumed"
    ),
    SKIP_NOT_RUNNABLE: (
        "check the artifact's `- Status:` with `aw find plans <id6>`: a terminal status "
        "(`superseded`, `not-executed`) is correctly skipped, while a MISSING status is a defect in "
        "the artifact worth fixing"
    ),
    SKIP_HOST_CAPABILITY_UNAVAILABLE: (
        "inspect the refused capability with `aw host capabilities`, then run the item on a host that "
        "satisfies it"
    ),
}


#: The dispositions that need NO remedy because nothing is wrong with them. Distinguished from an
#: unknown remedy deliberately: printing a fabricated remedy beside a correct, terminal outcome is
#: noise, and printing nothing beside an UNRECOGNIZED disposition would hide a gap in this table.
DISPOSITIONS_NEEDING_NO_REMEDY: frozenset = frozenset(
    {
        # The run acted on it. Whatever happened next is the item's own outcome, not a selection
        # refusal an operator must unblock.
        DISPOSITION_ACTED_ON,
        # Already executed on disk. A correct, terminal disposition: there was nothing to do, and
        # "fixing" it would mean re-executing finished work.
        SKIP_ALREADY_EXECUTED,
    }
)

#: Rendered in place of a remedy for a disposition this table does not know. NOT an empty string, and
#: not silence: an unrecognized disposition is a GAP (a new refusal reason shipped without its
#: remedy), and the operator-visible admission of ignorance is what makes that gap get fixed instead
#: of quietly reading as "nothing to do here".
REMEDY_UNKNOWN_TEXT = (
    "no remedy is recorded for this disposition; this is a gap in the runner's remedy table, "
    "please report it"
)


def remedy_for_disposition(code: str) -> Optional[str]:
    """The remedy text for ONE disposition code, or ``None`` when it legitimately needs none.

    THREE OUTCOMES, NOT TWO, which is the point of this function existing rather than a bare
    `DISPOSITION_REMEDIES.get(code)`:

      * a known actionable disposition -> its verified remedy;
      * a disposition in :data:`DISPOSITIONS_NEEDING_NO_REMEDY` -> ``None``, meaning "nothing to do,
        and that is correct";
      * anything else -> :data:`REMEDY_UNKNOWN_TEXT`, meaning "this disposition SHOULD have a remedy
        and nobody wrote one".

    Collapsing the last two would render a gap in the table identically to a correct terminal
    outcome, which is the specific mistake E-02 forbids.

    A refusal record's OWN remedy never reaches here: `orchprobe` `r2i1b1` stores `remedy` on the
    item, and :func:`derive_item_disposition` carries it through, so the record stays the authority
    for an item it refused and this plan maintains no second copy of it.
    """

    norm = str(code or "").strip()
    if norm in DISPOSITION_REMEDIES:
        return DISPOSITION_REMEDIES[norm]
    if norm in DISPOSITIONS_NEEDING_NO_REMEDY:
        return None
    return REMEDY_UNKNOWN_TEXT


#: The header of the closing block. States the QUESTION it answers, because "what did this invocation
#: actually do?" is the question backlog `em0z50` records an operator being unable to answer.
SUMMARY_HEADER = "What this run did (every artifact its selector matched):"

#: The verdict line for a run that matched artifacts and acted on NONE of them. THE MEASURED
#: INCIDENT: `aw oc run wtiso` matched 8 plans, acted on none, exited 0, and its closing words were
#: `No OpenCode session was captured for this run.` while the summary table said `COMPLETED` at 100%.
#: This sentence is the honest answer that was missing.
SUMMARY_NO_ACTION_VERDICT = (
    "NO WORK WAS PERFORMED: this run matched {matched} artifact(s) and acted on NONE of them. "
    "This is not a failed launch; nothing was dispatched. See the remedies below."
)

#: The verdict line for a run that acted on some but not all of what it matched.
SUMMARY_PARTIAL_VERDICT = "This run matched {matched} artifact(s) and acted on {acted}; {skipped} were not acted on."

#: The verdict line for a run that acted on everything it matched.
SUMMARY_ALL_ACTED_VERDICT = (
    "This run acted on all {matched} artifact(s) its selector matched."
)


def summarize_dispositions(
    entries: Sequence[Mapping[str, object]],
    refusal_reader: Optional[Callable[..., object]] = None,
) -> "Tuple[Tuple[str, int, Optional[str]], ...]":
    """Count matched artifacts per DISPOSITION, with each disposition's remedy, in render order.

    Returns ``((code, count, remedy_or_None), ...)``. THE COUNTS SUM TO THE NUMBER OF ENTRIES, which
    is the property worth asserting rather than any individual number: every entry lands in exactly
    one bucket because :func:`derive_item_disposition` returns exactly one code per entry and
    :data:`DISPOSITION_ACTED_ON` is a real bucket rather than the absence of one.

    ``remedy`` is the per-disposition remedy from :func:`remedy_for_disposition`, EXCEPT where a
    recorded `Refusal` supplied its own (`orchprobe` `r2i1b1`), in which case that record's remedy is
    reported for its code. First record wins for a given code, so a second item refused under the
    same code cannot silently replace the remedy the reader is shown.

    Ordered by :data:`SKIP_REASONS` first (the documented reason order), then any refusal codes in
    first-seen order, then :data:`DISPOSITION_ACTED_ON` LAST, so the things needing attention are
    read first and the acted-on total closes the list.
    """

    counts: Dict[str, int] = {}
    remedies: Dict[str, Optional[str]] = {}
    seen_order: List[str] = []
    for entry in entries:
        decided = derive_item_disposition(entry, refusal_reader)
        code = decided.code
        if code not in counts:
            counts[code] = 0
            seen_order.append(code)
            remedies[code] = decided.remedy or remedy_for_disposition(code)
        counts[code] += 1

    ordered: List[str] = [code for code in SKIP_REASONS if code in counts]
    ordered += [
        code
        for code in seen_order
        if code not in ordered and code != DISPOSITION_ACTED_ON
    ]
    if DISPOSITION_ACTED_ON in counts:
        ordered.append(DISPOSITION_ACTED_ON)
    return tuple((code, counts[code], remedies[code]) for code in ordered)


def render_disposition_summary(
    entries: Sequence[Mapping[str, object]],
    *,
    header: str = SUMMARY_HEADER,
    refusal_reader: Optional[Callable[..., object]] = None,
) -> List[str]:
    """The closing block: an honest verdict, per-disposition counts, and each remedy.

    PURE. Returns a list of LINES; prints nothing, opens nothing, imports no runner, exactly as
    :func:`render_action_preview` and :func:`render_refusal` do in this module. The caller owns the
    stream, which is what lets both hosts print it at their own exit site.

    Returns ``[]`` for an EMPTY selection, and that is not the zero-action case this plan exists to
    fix: nothing matched means there is nothing to report a disposition for, and a stray header would
    be noise. The case that matters is a run that matched N artifacts and acted on ZERO, which yields
    the full block with :data:`SUMMARY_NO_ACTION_VERDICT`.

    The per-artifact lines are NOT re-formatted here: :func:`render_queue_dispositions` (`m85gxh`
    E-01) owns that shape and this block's counts come from the SAME
    :func:`derive_item_disposition`, so one disposition vocabulary spans the line and the summary by
    construction rather than by test.
    """

    rows = summarize_dispositions(entries, refusal_reader)
    if not rows:
        return []

    matched = sum(count for _code, count, _remedy in rows)
    acted = sum(count for code, count, _remedy in rows if code == DISPOSITION_ACTED_ON)
    skipped = matched - acted
    if acted == 0:
        verdict = SUMMARY_NO_ACTION_VERDICT.format(matched=matched)
    elif skipped:
        verdict = SUMMARY_PARTIAL_VERDICT.format(
            matched=matched, acted=acted, skipped=skipped
        )
    else:
        verdict = SUMMARY_ALL_ACTED_VERDICT.format(matched=matched)

    lines: List[str] = [header, verdict]
    for code, count, remedy in rows:
        label = (
            ACTED_REASON_LABEL
            if code == DISPOSITION_ACTED_ON
            else SKIP_REASON_LABELS.get(code, "")
        )
        head = "  {0} ({1})".format(code, count)
        lines.append("{0}: {1}".format(head, label) if label else head)
        if remedy:
            lines.append("    remedy: {0}".format(remedy))
    # The counts are RESTATED as a total rather than left for the reader to add up, so the block's own
    # guarantee (nothing matched is omitted) is checkable on its face by a `tail` reader.
    lines.append(
        "  total: {0} matched, {1} acted on, {2} not acted on".format(
            matched, acted, skipped
        )
    )
    return lines
