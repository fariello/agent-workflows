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
# E-02: the action preview
# --------------------------------------------------------------------------------------------------


def render_action_preview(classification: Classification) -> str:
    """Render the sorted count + action preview in spec 25kzda 2.5's exact shape::

        Mixed work-item selection:
          IPDs:    4 (2 review, 2 execute)
          Specs:   2 (1 review, 1 plan)
          Prompts: 1 (1 execute)

    Deterministic: type order is :data:`SPEC_TYPE_ORDER` and action order is
    :data:`ACTION_ORDER`, so two renders of the same selection are byte-identical.
    """

    if not classification.counts:
        return "Mixed work-item selection:\n  (nothing selected)"

    width = max(len(c.label) + 1 for c in classification.counts) + 1
    lines = ["Mixed work-item selection:"]
    for c in classification.counts:
        breakdown = ", ".join("{0} {1}".format(n, action) for action, n in c.by_action)
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


def is_confirmation_accepted(response: Optional[str]) -> bool:
    """True only for the EXACT phrase `run mixed` (spec 2.5, first bullet).

    Surrounding whitespace is stripped, because a terminal read includes the newline the operator
    pressed; nothing else is normalized. Case is NOT folded and no synonym is accepted, so `y`,
    `yes`, `Y`, an empty response, `run`, and `run mixed types` are all rejected. The point of an
    exact phrase is that it cannot be produced by a reflex keystroke.
    """

    if response is None:
        return False
    return response.strip() == CONFIRM_PHRASE


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
