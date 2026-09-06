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
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

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
