"""The ONE semantic source for lifecycle presentation (spec ``uonrjg`` R10.1).

This module is the canonical, stdlib-only answer to one question: given an artifact status, a
runner item state, a durable ledger state, or a live activity, WHICH semantic presentation stage
does a human view show? It owns the stage vocabulary of spec Section 5, the native artifact
mappings of Sections 6.1 to 6.7, the runner/ledger/set mappings of Sections 7.1 to 7.4, the
resolution precedence of Section 8, and the self-validation R10.1 demands.

WHAT THIS MODULE DELIBERATELY DOES NOT DO, because R10.1 forbids it: it EMITS NO TERMINAL ESCAPES.
It returns immutable presentation DATA (a stage name plus its glyph, fallback character, color
index and bold flag) and leaves every capability decision, every fallback selection and every byte
of styling to ``agent_workflows.term`` or another renderer. That separation is what makes
resolution testable without a terminal, and it is why this module imports only the standard
library: a semantic table that reaches for a renderer stops being a table.

WHY IT EXISTS AT ALL (spec Section 1, measured in code before this landed): four independent
lifecycle palettes were live and disagreed, so the same semantic stage could be a different color
in two commands, green meant both "ready" and "complete" in different views, and adding one status
meant finding several partial tables. This module is the single table those consumers converge on.

THE NATIVE WORD REMAINS AUTHORITATIVE (Section 0). A stage is a redundant scanning aid, never the
carrier of meaning, so MANY NATIVE WORDS SHARING ONE STAGE IS THE DESIGN rather than a table
defect (Section 4.4a): ``blocked``, ``dependency-blocked``, ``integration-blocked`` and
``merge-conflict`` all render one glyph while each printing its own word. Callers MUST keep
printing the word.

STORED STATUS AND LIVE ACTIVITY ARE DISTINCT (Section 0). A plan may stay ``approved`` while a
runner executes it: the live view shows the activity glyph and the word ``executing``, and nothing
mutates the artifact to produce that display. ``resolve`` therefore returns the native status and
the activity as SEPARATE fields and mutates neither input (Section 8).

WORK-KIND IS EXCLUDED BY CONSTRUCTION (Section 0, criterion A19). ``resolve`` has no work-kind
parameter, so ``feature``, ``bug`` and ``docs`` cannot reach lifecycle presentation even by
accident. That is a structural guarantee rather than a convention a caller must remember.

Python 3.9 compatible, no runtime dependency, no filesystem/network/model access.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

# An integrity input is EITHER a word a renderer read off a record (``"ok"``, ``"invalid"``) OR a
# bare bool from a caller that already decided. Both are accepted because both occur in practice and
# forcing a caller to stringify its own boolean buys nothing.
IntegrityInput = Union[str, bool, None]

# ======================================================================================
# Errors
# ======================================================================================


class LifecycleStyleError(ValueError):
    """A contract violation in this module's own tables, or a caller passing an unknown family.

    Deliberately a ``ValueError`` subclass so a caller that only wants "bad input" semantics needs
    no import from here, while a caller that wants to distinguish a table defect can catch this.
    """


class UnknownFamily(LifecycleStyleError):
    """The caller named an artifact/record family this module has no policy for.

    This RAISES rather than degrading to the ``unknown`` stage, and the distinction is deliberate
    (R10.4). An unrecognized STATUS inside a known family is a data condition the spec requires be
    displayed (``unknown``, plus a diagnostic). An unrecognized FAMILY is a PROGRAMMING error: the
    caller asked for a policy that was never written, and silently painting it gray would hide a
    missing mapping table behind a plausible-looking glyph.
    """


# ======================================================================================
# 1. The stage vocabulary (spec Section 5)
# ======================================================================================

# The twenty semantic stages, as named constants so a consumer never spells one as a bare literal.
FORMATIVE = "formative"
REVIEW_QUEUED = "review-queued"
AUTHORITY_QUEUED = "authority-queued"
READY = "ready"
REVIEWING = "reviewing"
EXECUTING = "executing"
VERIFYING = "verifying"
INTEGRATING = "integrating"
RECOVERING = "recovering"
ACTIVE = "active"
WAITING_INPUT = "waiting-input"
BLOCKED = "blocked"
FAILED = "failed"
DONE = "done"
REUSABLE = "reusable"
PARKED = "parked"
SUPERSEDED = "superseded"
ABANDONED = "abandoned"
UNKNOWN = "unknown"
NONE = "none"

# The two graphemes that carry a TEXT-PRESENTATION variation selector (U+FE0E), written as explicit
# escapes rather than as literals. The escapes are not decoration: the selector is invisible, so a
# literal would be indistinguishable by eye from the EMOJI form the spec forbids (A5), and an
# editor or a paste that dropped it would silently ship the wrong glyph. Section 5 requires these
# exact forms because the emoji forms bring colorful platform rendering, a variable baseline and
# unexpectedly wide cells.
GLYPH_BLOCKED = "\u26a0\ufe0e"  # U+26A0 WARNING SIGN + U+FE0E VARIATION SELECTOR-15
GLYPH_RECOVERING = "\u21a9\ufe0e"  # U+21A9 LEFTWARDS ARROW WITH HOOK + U+FE0E

# Section 4.5: several selected graphemes are ONE visible representation made of TWO code points.
# Code MUST NOT use len() as a proxy for display width. Exposed as data so a renderer can assert it.
MULTI_CODEPOINT_GLYPHS: FrozenSet[str] = frozenset((GLYPH_BLOCKED, GLYPH_RECOVERING))


class StageStyle(NamedTuple):
    """The immutable presentation data for one semantic stage (spec Section 5, one row).

    ``color`` is an xterm-256 FOREGROUND INDEX and nothing more: it is a number this module hands
    to a renderer, never an escape sequence. ``bold`` applies to the glyph, the id6 and the status
    word when those elements are styled, and no other terminal attribute is used (Section 5).
    """

    stage: str
    unicode: str
    ascii: str
    color: int
    bold: bool
    meaning: str


# The NORMATIVE table, transcribed row for row from spec Section 5 IN SPEC ORDER. The order is
# load-bearing twice over: Section 11 item 6 requires a legend to use lifecycle order rather than
# color names, and a stable order keeps dense boards and golden output deterministic.
#
# HELD AS A TUPLE OF ROWS RATHER THAN A DICT LITERAL, deliberately. A dict literal SILENTLY keeps
# the last of two identical keys, which is exactly the duplicate-key defect R10.1 requires this
# module to REJECT. Building from rows is what makes that rejection possible at all.
_STAGE_ROWS: Tuple[StageStyle, ...] = (
    StageStyle(
        FORMATIVE, "○", "D", 245, False, "Draft, incomplete, or not yet admitted"
    ),
    StageStyle(REVIEW_QUEUED, "◔", "Q", 39, False, "Awaiting review"),
    StageStyle(
        AUTHORITY_QUEUED,
        "◑",
        "A",
        135,
        False,
        "Reviewed and awaiting approval or authority",
    ),
    StageStyle(
        READY,
        "◕",
        ">",
        45,
        True,
        "Approved, planned, open, pending, or otherwise actionable",
    ),
    StageStyle(REVIEWING, "◎", "R", 220, True, "A review turn is active"),
    StageStyle(EXECUTING, "▶", "E", 220, True, "Implementation or execution is active"),
    StageStyle(
        VERIFYING, "◆", "V", 220, True, "Tests or other verification are active"
    ),
    StageStyle(INTEGRATING, "⇄", "M", 220, True, "Merge or integration work is active"),
    StageStyle(
        RECOVERING,
        GLYPH_RECOVERING,
        "T",
        220,
        True,
        "Retry, correction, resume, or recovery is active or required",
    ),
    StageStyle(ACTIVE, "●", "*", 220, True, "Active work whose subtype is unavailable"),
    StageStyle(
        WAITING_INPUT,
        "…",
        ".",
        214,
        True,
        "Waiting for human input or another non-failure response",
    ),
    StageStyle(
        BLOCKED,
        GLYPH_BLOCKED,
        "!",
        208,
        True,
        "Work cannot advance until a named condition clears",
    ),
    StageStyle(
        FAILED, "✘", "X", 196, True, "Terminal failure or invalid/inconsistent state"
    ),
    StageStyle(
        DONE,
        "✓",
        "+",
        46,
        True,
        "Successfully completed, implemented, executed, or shipped",
    ),
    StageStyle(
        REUSABLE,
        "↻",
        "~",
        81,
        False,
        "Completed reusable artifact that remains intentionally available",
    ),
    StageStyle(
        PARKED,
        "◇",
        "P",
        244,
        False,
        "Intentionally inactive, deferred from current work, or archived",
    ),
    StageStyle(
        SUPERSEDED, "↪", "S", 244, False, "Replaced by a newer artifact or decision"
    ),
    StageStyle(
        ABANDONED,
        "∅",
        "N",
        244,
        False,
        "Intentionally not executed, cancelled, expired, or abandoned",
    ),
    StageStyle(UNKNOWN, "?", "?", 244, False, "State cannot be determined safely"),
    StageStyle(
        NONE, "·", "-", 244, False, "Artifact type has no lifecycle at this location"
    ),
)


def _build_stage_table(rows: Iterable[StageStyle]) -> Mapping[str, StageStyle]:
    """Index the stage rows by name, REFUSING a duplicate rather than letting the last win.

    This is half of R10.1's validation requirement and it lives here rather than in ``validate``
    because the rejection must happen while the duplicate is still VISIBLE. Once rows collapse into
    a dict the evidence is gone.
    """
    table: Dict[str, StageStyle] = {}
    for row in rows:
        if row.stage in table:
            raise LifecycleStyleError(
                "duplicate semantic stage key {0!r}: spec Section 5 defines each stage exactly "
                "once, so two rows for one key means one of them is wrong".format(
                    row.stage
                )
            )
        table[row.stage] = row
    return MappingProxyType(table)


STAGES: Mapping[str, StageStyle] = _build_stage_table(_STAGE_ROWS)

# Spec Section 5 order. Derived from the rows so it can never drift from the table.
STAGE_ORDER: Tuple[str, ...] = tuple(row.stage for row in _STAGE_ROWS)

ALL_STAGES: FrozenSet[str] = frozenset(STAGE_ORDER)

# The five ACTIVE SUBTYPES plus generic ``active`` and ``waiting-input``: the stages a live runner
# or ledger may overlay on a stored status (Section 7.1). Section 5 gives the five subtypes one
# amber treatment on purpose, so SHAPE carries the subtype and the adjacent word states it.
ACTIVITY_STAGES: FrozenSet[str] = frozenset(
    (REVIEWING, EXECUTING, VERIFYING, INTEGRATING, RECOVERING, ACTIVE, WAITING_INPUT)
)

# The stages Section 11 item 4 permits bold, kept as data so an accessibility test can assert the
# restraint rule rather than re-listing it.
BOLD_STAGES: FrozenSet[str] = frozenset(
    stage for stage, style in STAGES.items() if style.bold
)


def style_for(stage: str) -> StageStyle:
    """Return the immutable presentation row for ``stage``, raising on an undefined stage."""
    try:
        return STAGES[stage]
    except KeyError:
        raise LifecycleStyleError(
            "unknown semantic stage {0!r}; the defined stages are: {1}".format(
                stage, ", ".join(STAGE_ORDER)
            )
        ) from None


def glyph_for(stage: str, *, unicode: bool = True) -> str:
    """Return the one-character representation for ``stage``.

    ``unicode=False`` selects the exact Section 5 ASCII fallback. The CHOICE between the two is the
    RENDERER's (it owns stream capability, ``AW_ASCII_ONLY`` and ``FORCE_ASCII``); this function
    only supplies whichever was chosen, because a semantic table that sniffed the terminal would be
    making a capability decision R10.2 assigns elsewhere.
    """
    style = style_for(stage)
    return style.unicode if unicode else style.ascii


# ======================================================================================
# 2. Native artifact mappings (spec Sections 6.1 to 6.7)
# ======================================================================================

# Family keys. These name the ARTIFACT/RECORD FAMILY whose native vocabulary is being resolved, and
# they intentionally match the tracked-tree names already used by `attention_contract.TREE_POLICY`
# so a caller never has to translate between two naming schemes.
FAMILY_PLANS = "plans"
FAMILY_SPECS = "specs"
FAMILY_BACKLOG = "backlog"
FAMILY_RESEARCH = "research"
FAMILY_PROMPTS = "prompts"
FAMILY_RELEASES = "releases"
FAMILY_REVIEWS = "reviews"
FAMILY_WALKTHROUGHS = "walkthroughs"
FAMILY_ROADMAPS = "roadmaps"
FAMILY_PROMPT_LIBRARY = "prompt-library"
FAMILY_RUNNER_ITEM = "runner-item"
FAMILY_RUN_LEDGER = "run-ledger"
FAMILY_SET_STATE = "set-state"
FAMILY_COMMS_ACK = "comms-ack"


def _build_map(family: str, pairs: Iterable[Tuple[str, str]]) -> Mapping[str, str]:
    """Index one family's ``native status -> stage`` pairs, refusing duplicates and unknown stages.

    Same reasoning as ``_build_stage_table``: pairs rather than a dict literal, so a status written
    twice (most plausibly with two different stages during an edit) is an ERROR instead of a silent
    last-wins. The stage check catches a typo'd stage name at import rather than at the first render.
    """
    table: Dict[str, str] = {}
    for status, stage in pairs:
        if status in table:
            raise LifecycleStyleError(
                "duplicate native status {0!r} in family {1!r} (already mapped to {2!r}, "
                "re-mapped to {3!r})".format(status, family, table[status], stage)
            )
        if stage not in ALL_STAGES:
            raise LifecycleStyleError(
                "family {0!r} maps {1!r} to {2!r}, which is not a defined semantic "
                "stage".format(family, status, stage)
            )
        table[status] = stage
    return MappingProxyType(table)


# --- 6.1 Plans and IPDs ---------------------------------------------------------------
# `reviewing` and `executing` are LIVE ACTIVITIES, not stored plan statuses, so they are absent
# here by design and arrive through the activity overlay instead.
_PLANS_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("draft", FORMATIVE),
    ("to-review", REVIEW_QUEUED),
    ("reviewed", AUTHORITY_QUEUED),
    ("approved", READY),
    ("auto-approved", READY),
    ("executed", DONE),
    ("reusable", REUSABLE),
    ("superseded", SUPERSEDED),
    ("not-executed", ABANDONED),
)

# --- 6.2 Specs ------------------------------------------------------------------------
_SPECS_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("draft", FORMATIVE),
    ("to-review", REVIEW_QUEUED),
    ("reviewed", AUTHORITY_QUEUED),
    ("approved", READY),
    ("implementing", EXECUTING),
    ("implemented", DONE),
    ("deferred", BLOCKED),
    ("parked", PARKED),
    ("superseded", SUPERSEDED),
)

# --- 6.3 Backlog items ----------------------------------------------------------------
# `graduated` is GENERIC active rather than `executing`: graduation can lead to more than one
# artifact type and does not prove that execution is running (Section 6.3).
_BACKLOG_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("open", READY),
    ("graduated", ACTIVE),
    ("blocked", BLOCKED),
    ("parked", PARKED),
    ("done", DONE),
)

# --- 6.4 Research ---------------------------------------------------------------------
# Research OUTCOME values (`adopted`, `rejected`, `informational`, `none-yet`) are a SEPARATE
# dimension and MUST NOT replace the lifecycle glyph, so they are deliberately absent from this map.
_RESEARCH_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("todo", READY),
    ("intake", READY),  # legacy alias, kept so a pre-migration label keeps its stage
    ("active", ACTIVE),
    ("reference", DONE),
    ("archive", PARKED),
    ("archived", PARKED),  # legacy/prose spelling of the same state
)

# --- 6.5 Prompts ----------------------------------------------------------------------
# PROMPT STATUS IS CARRIED BY DIRECTORY, not by a status enum: `prompts.py` defines only
# `DEFAULT_STATUS` and `PROMPT_KINDS`. These five keys are therefore the five lane names
# (`ipd_lint._dir_of`'s anchors, matching the live `.aw/records/prompts/` subdirectories). Prompt
# KIND (`run-once`, `research`, `session-handoff`) is not a lifecycle stage and is absent.
_PROMPTS_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("pending", READY),
    ("executed", DONE),
    ("reusable", REUSABLE),
    ("superseded", SUPERSEDED),
    ("not-executed", ABANDONED),
)

# --- 6.6 Releases ---------------------------------------------------------------------
_RELEASES_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("planned", READY),
    ("blocked", BLOCKED),
    ("shipped", DONE),
)

# --- 7.2 Runner item outcomes ---------------------------------------------------------
# `running` maps to GENERIC active here and is UPGRADED to a specific subtype by the activity
# overlay when the runner knows the action (Section 7.2's "action-aware activity from 7.1,
# otherwise active").
#
# SIX ROWS HERE WERE NOT IN A NAIVE READING OF THE TABLE and each closes a word that would
# otherwise have fallen through to gray, which Section 6's preamble calls a defect:
#   - `needs_input` and `awaiting-human` -> waiting-input (D12). Both mean a human is required.
#     Note 214 is distinct from `blocked`'s 208, which is what keeps `6kwd2e` R4a.6 satisfied.
#   - `ran` -> recovering, NOT done (D13). `25kzda` makes a `ran` item contribute non-success and
#     exit 1, and Section 7.2 forbids styling unverified completion as verified success, so green
#     would paint an exit-1 item as success.
#   - `unknown_outcome` -> failed, NOT this module's generic `unknown` (D14). It is a real, named,
#     terminal disposition owned by spec `c4gd2h`; mapping it onto the lookup-failure glyph would
#     erase the very distinction that spec's Section 0.0 exists to protect.
#   - `quarantined` -> parked (D15). Also reachable as a CONDITION input (see `CONDITION_STAGES`),
#     because it is carried by a `- Quarantine:` FIELD rather than a `- Status:` value. It is listed
#     here too so a lint view can show it without calling it a pass.
#   - `integration-deferred` -> recovering. THE SIXTH ORPHAN, resolved by plan `udgilu` OQ-02 from
#     code evidence rather than preference: `runner_shutdown` files it under "in-flight /
#     recoverable" and says the item "is awaiting a re-attempt", `oc_runipd` records it as
#     DELIBERATELY absent from `TERMINAL_STATES` because "absence is what makes a re-attempt
#     possible", and `retry_deferred_integrations` actually SCHEDULES that re-attempt on the next
#     loop iteration at zero cost. Work here advances BY ITSELF, which is `recovering`'s meaning
#     ("Retry, correction, resume, or recovery is active or required") and is exactly NOT
#     `blocked`'s ("Work cannot advance until a named condition clears"). Every row Section 7.2
#     maps to `blocked` (`dependency-blocked`, `integration-blocked`, `merge-conflict`) leaves the
#     item NOT integrated with NO scheduled retry; this one is the opposite case.
_RUNNER_ITEM_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("queued", READY),
    ("running", ACTIVE),
    ("interrupted", RECOVERING),
    ("partial", RECOVERING),
    ("substantially-complete", RECOVERING),
    ("correction_required", RECOVERING),
    ("reviewed", AUTHORITY_QUEUED),
    ("approved", READY),
    ("executed", DONE),
    ("verified", DONE),
    ("complete", DONE),
    ("blocked", BLOCKED),
    ("dependency-blocked", BLOCKED),
    ("integration-blocked", BLOCKED),
    ("merge-conflict", BLOCKED),
    ("failed", FAILED),
    ("failed-safely", FAILED),
    ("not-attempted", ABANDONED),
    ("cancelled", ABANDONED),
    ("needs_input", WAITING_INPUT),
    ("awaiting-human", WAITING_INPUT),
    ("ran", RECOVERING),
    ("unknown_outcome", FAILED),
    ("quarantined", PARKED),
    ("integration-deferred", RECOVERING),
    # The STALE PROJECTED form Section 7.2's last row names. It is an INFERENCE rather than a
    # durable state, so it resolves `unknown` on purpose: the trailing `?` is the projection's own
    # admission that it does not know.
    ("abandoned?", UNKNOWN),
)

# --- 7.3 Run ledger and set state -----------------------------------------------------
# Section 7.3 is ONE table in the spec and TWO maps here, because it has TWO OWNERS whose key sets
# are disjoint by construction: `run_state` owns the bare words and `set_state` deliberately
# `set_`-prefixes its own so they "never collide with run_state's bare running|complete|failed|
# cancelled" (that module's OQ-02). Splitting on the owner boundary is what lets criterion A2
# assert totality against each owner enum separately; merging them would only be able to assert a
# union, which is a weaker claim.
#
# `performed` maps to VERIFYING, not to done, and that is the spec's point: an item presently
# verifying displays `verifying` even when its last durable ledger event is `performed`, because
# unverified completion MUST NOT be styled as verified success.
_RUN_LEDGER_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("pending", READY),
    ("runnable", READY),
    ("running", ACTIVE),
    ("performed", VERIFYING),
    ("verifying", VERIFYING),
    ("verified", DONE),
    ("complete", DONE),
    ("correction_required", RECOVERING),
    ("blocked", BLOCKED),
    ("failed", FAILED),
    ("cancelled", ABANDONED),
)

_SET_STATE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("set_planned", READY),
    ("set_running", ACTIVE),
    ("set_partial", RECOVERING),
    ("set_waiting_input", WAITING_INPUT),
    ("set_complete", DONE),
    ("set_failed", FAILED),
    ("set_cancelled", ABANDONED),
)

# --- 7.4 Communication acknowledgements -----------------------------------------------
# Acknowledgement states are NOT an artifact lifecycle, and Section 7.4 is permissive ("dense status
# tables MAY use this same semantic vocabulary"). The map is provided so a table that opts in reads
# from this one source instead of inventing a sixth palette. The native acknowledgement word
# remains mandatory.
_COMMS_ACK_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("scheduled", READY),
    ("queued", READY),
    ("delivered", READY),
    ("read", AUTHORITY_QUEUED),
    ("in-progress", ACTIVE),
    ("done", DONE),
    ("executed", DONE),
    ("agent-not-running", BLOCKED),
    ("agent-not-responding", BLOCKED),
    ("expired", ABANDONED),
    ("not-done", ABANDONED),
    ("not-executed", ABANDONED),
)


NATIVE_MAPS: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        FAMILY_PLANS: _build_map(FAMILY_PLANS, _PLANS_PAIRS),
        FAMILY_SPECS: _build_map(FAMILY_SPECS, _SPECS_PAIRS),
        FAMILY_BACKLOG: _build_map(FAMILY_BACKLOG, _BACKLOG_PAIRS),
        FAMILY_RESEARCH: _build_map(FAMILY_RESEARCH, _RESEARCH_PAIRS),
        FAMILY_PROMPTS: _build_map(FAMILY_PROMPTS, _PROMPTS_PAIRS),
        FAMILY_RELEASES: _build_map(FAMILY_RELEASES, _RELEASES_PAIRS),
        FAMILY_RUNNER_ITEM: _build_map(FAMILY_RUNNER_ITEM, _RUNNER_ITEM_PAIRS),
        FAMILY_RUN_LEDGER: _build_map(FAMILY_RUN_LEDGER, _RUN_LEDGER_PAIRS),
        FAMILY_SET_STATE: _build_map(FAMILY_SET_STATE, _SET_STATE_PAIRS),
        FAMILY_COMMS_ACK: _build_map(FAMILY_COMMS_ACK, _COMMS_ACK_PAIRS),
    }
)

# --- 6.7 Records with no lifecycle of their own ----------------------------------------
# These resolve `none` (`·`) rather than `unknown` (`?`), and R10.4 makes the distinction
# load-bearing: `unknown` says "this family HAS a lifecycle and I could not read it", while `none`
# says "this family HAS no lifecycle here". Collapsing them would turn a missing mapping into a
# shrug. Section 6.7 also prefers OMITTING the lifecycle column when every row would be `none`.
#
# `reviews` is here because a review record owns no independent lifecycle: where a review row
# identifies its SUBJECT it must use the subject artifact's stage (resolve the subject's family
# instead), and review READINESS is a separate, explicitly-labeled axis (see `REVIEW_READINESS`).
NO_LIFECYCLE_FAMILIES: FrozenSet[str] = frozenset(
    (
        FAMILY_REVIEWS,
        FAMILY_WALKTHROUGHS,
        FAMILY_ROADMAPS,
        FAMILY_PROMPT_LIBRARY,
    )
)

FAMILIES: FrozenSet[str] = frozenset(NATIVE_MAPS) | NO_LIFECYCLE_FAMILIES

# Section 6.7 review READINESS, kept in its own map and behind its own label so it can NEVER be
# mistaken for the subject's stored status. A caller that renders this MUST label the column
# `readiness` (that is the spec's word, exposed here so the label has one spelling).
READINESS_LABEL = "readiness"
REVIEW_READINESS: Mapping[str, str] = _build_map(
    "review-readiness",
    (
        ("go", READY),
        ("go-pending-approval", AUTHORITY_QUEUED),
        ("no-go", BLOCKED),
    ),
)


# ======================================================================================
# 3. Activity, integrity and condition inputs (Sections 4.3, 4.4, 7.1)
# ======================================================================================

# Section 7.1: when a live runner KNOWS the action, it MUST choose the specific activity rather
# than generic `active`. The spec states the facts in prose ("review turn is running"); this is the
# machine form, keyed on the ACTION WORDS the runners and ledgers actually use. A generic `running`
# is allowed only when the subtype is genuinely unavailable, which is why `run`/`running` are the
# only keys that land on `active`.
ACTIVITY_FROM_ACTION: Mapping[str, str] = _build_map(
    "activity-from-action",
    (
        ("review", REVIEWING),
        ("reviewing", REVIEWING),
        ("execute", EXECUTING),
        ("executing", EXECUTING),
        ("implement", EXECUTING),
        ("implementing", EXECUTING),
        ("verify", VERIFYING),
        ("verifying", VERIFYING),
        ("test", VERIFYING),
        ("testing", VERIFYING),
        ("merge", INTEGRATING),
        ("merging", INTEGRATING),
        ("rebase", INTEGRATING),
        ("rebasing", INTEGRATING),
        ("integrate", INTEGRATING),
        ("integrating", INTEGRATING),
        ("retry", RECOVERING),
        ("retrying", RECOVERING),
        ("correct", RECOVERING),
        ("correcting", RECOVERING),
        ("resume", RECOVERING),
        ("resuming", RECOVERING),
        ("recover", RECOVERING),
        ("recovering", RECOVERING),
        ("run", ACTIVE),
        ("running", ACTIVE),
        ("await-human", WAITING_INPUT),
        ("awaiting-human", WAITING_INPUT),
        ("needs-input", WAITING_INPUT),
        ("needs_input", WAITING_INPUT),
        ("waiting-input", WAITING_INPUT),
    ),
)

# Section 4.4: integrity values a renderer may report. An integrity input that is NOT recognized as
# sound is treated as a FAILURE, which is the fail-closed direction: the cost of showing `✘` for a
# healthy record is a visible, correctable mistake, while the cost of the reverse is a plausible
# active glyph sitting on invalid state, which Section 4.4 calls "actively misleading".
INTEGRITY_SOUND_VALUES: FrozenSet[str] = frozenset(
    ("ok", "valid", "conforming", "conforms", "sound", "clean", "pass", "passed")
)

# Condition inputs that are carried by a FIELD rather than by a `- Status:` value, and therefore
# reach the resolver as a condition rather than as a native status (D15). `quarantined` is the one
# the spec names.
CONDITION_STAGES: Mapping[str, str] = _build_map(
    "condition", (("quarantined", PARKED),)
)


# ======================================================================================
# 4. The resolver (spec Section 8)
# ======================================================================================


class Resolved(NamedTuple):
    """One resolved lifecycle presentation: an immutable answer, plus every input it was given.

    THE INPUTS ARE ECHOED BACK SEPARATELY ON PURPOSE (Section 8): "The resolver MUST return the
    native status and activity separately so a caller can render both when space permits." A caller
    that receives only a stage cannot print the authoritative word, and Section 0 makes the word the
    authority. ``obstruction`` and ``integrity`` follow the same rule for the same reason: a row
    reading "blocked: gate D-021" is strictly more useful than one reading "blocked", and the
    resolver is the only place that knew the name.

    ``diagnostic`` is non-None exactly when the resolution is one a validation boundary should
    complain about, which is criterion A20's requirement that an unrecognized status in a KNOWN
    family "produce a validation diagnostic" rather than merely rendering a shrug.
    """

    stage: str
    style: StageStyle
    family: str
    native_status: Optional[str] = None
    activity: Optional[str] = None
    obstruction: Optional[str] = None
    integrity: Optional[str] = None
    diagnostic: Optional[str] = None


def _normalize(value: Optional[str]) -> Optional[str]:
    """Trim and lowercase a status-like token, mapping empty/None to None. Never mutates a caller's
    object: strings are immutable, and nothing else is accepted."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.lower()


def _integrity_failed(integrity: IntegrityInput) -> bool:
    if integrity is None:
        return False
    if isinstance(integrity, bool):
        # `integrity=True` means "integrity is sound"; `integrity=False` means "it is not".
        return not integrity
    token = _normalize(integrity)
    if token is None:
        return False
    return token not in INTEGRITY_SOUND_VALUES


def resolve(
    family: str,
    native_status: Optional[str] = None,
    *,
    activity: Optional[str] = None,
    integrity: IntegrityInput = None,
    obstruction: Optional[str] = None,
    condition: Optional[str] = None,
) -> Resolved:
    """Resolve exactly ONE semantic stage for a display, in spec Section 8's precedence order.

    The order, highest first, and WHY each rung sits where it does:

    1. INVALID, CONTRADICTORY OR TERMINALLY FAILED state -> ``failed``. Above activity because a
       plausible active glyph on invalid state is actively misleading (Section 4.4), and a stale
       runtime field claiming activity is exactly how that happens (criterion A8).
    2. A CURRENT NAMED OBSTRUCTION -> ``blocked``. Above the native mapping so a blocked item shows
       the obstruction even when its stored status would otherwise read ready (criterion A9).
    3. A CONDITION carried by a field rather than a status -> that condition's stage. NOT ONE OF
       SECTION 8'S SIX NUMBERED RUNGS, and named as an addition rather than smuggled in: Section
       7.2's ``quarantined`` commentary and D15 introduced this input AFTER Section 8 was written,
       and D15 says outright that a resolver "reads it as an integrity/condition input per Section
       8". It is placed here because a quarantined artifact is deliberately SET ASIDE, so it is not
       active and its own stored status is not the interesting fact, while a genuine integrity
       failure or a named obstruction still outranks it.
    4. A CURRENT LIVE ACTIVITY from Section 7.1, including ``waiting-input``. Above the native
       mapping because activity is a DISPLAY OVERLAY (D7): an approved plan under execution shows
       ``executing`` while its stored status stays ``approved`` (criterion A7).
    5. The NATIVE artifact or durable run status mapping.
    6. ``unknown`` when a lifecycle is expected but cannot be resolved safely.
    7. ``none`` when the family has no lifecycle here.

    This is DISPLAY precedence, not STATE precedence: nothing here transitions, stores, or implies
    an artifact change (D7). No input is mutated.

    There is deliberately NO work-kind parameter (criterion A19). Work-kind cannot alter lifecycle
    presentation, and the cheapest way to guarantee that is to make it unrepresentable.
    """
    if family not in FAMILIES:
        raise UnknownFamily(
            "unknown artifact/record family {0!r}; known families are: {1}".format(
                family, ", ".join(sorted(FAMILIES))
            )
        )

    status_token = _normalize(native_status)
    activity_token = _normalize(activity)
    obstruction_token = _normalize(obstruction)
    condition_token = _normalize(condition)
    integrity_token = (
        None
        if integrity is None or isinstance(integrity, bool)
        else _normalize(integrity)
    )

    # The echoed native status keeps the caller's ORIGINAL spelling, because Section 0 makes the
    # word authoritative and a lowercased echo would quietly rewrite the authority.
    echoed_status = native_status if status_token is not None else None
    echoed_obstruction = obstruction if obstruction_token is not None else None

    def _result(
        stage: str,
        *,
        activity_out: Optional[str] = None,
        diagnostic: Optional[str] = None,
    ) -> Resolved:
        return Resolved(
            stage=stage,
            style=style_for(stage),
            family=family,
            native_status=echoed_status,
            activity=activity_out,
            obstruction=echoed_obstruction,
            integrity=integrity_token,
            diagnostic=diagnostic,
        )

    # Rung 1: integrity failure.
    if _integrity_failed(integrity):
        return _result(FAILED)

    # Rung 2: a named obstruction.
    if obstruction_token is not None:
        return _result(BLOCKED)

    # Rung 3: a field-carried condition (D15).
    if condition_token is not None:
        condition_stage = CONDITION_STAGES.get(condition_token)
        if condition_stage is not None:
            return _result(condition_stage)
        return _result(
            UNKNOWN,
            diagnostic="unrecognized condition {0!r} for family {1!r}".format(
                condition, family
            ),
        )

    # Rung 4: a live activity overlay.
    if activity_token is not None:
        if activity_token in ACTIVITY_STAGES:
            activity_stage = activity_token
        else:
            activity_stage = ACTIVITY_FROM_ACTION.get(activity_token)
        if activity_stage is not None:
            return _result(activity_stage, activity_out=activity_stage)
        return _result(
            UNKNOWN,
            diagnostic="unrecognized activity {0!r} for family {1!r}".format(
                activity, family
            ),
        )

    # Rung 7 (checked before 5/6 because it is a property of the FAMILY, not of the status): a
    # family with no lifecycle here is `none`, whether or not a status-shaped value was passed.
    if family in NO_LIFECYCLE_FAMILIES:
        return _result(NONE)

    # Rung 5: the native mapping.
    if status_token is not None:
        stage = NATIVE_MAPS[family].get(status_token)
        if stage is not None:
            return _result(stage)
        # Rung 6: a KNOWN family with an unrecognized status. `unknown` plus a diagnostic, never
        # parked gray (R10.4, criterion A20).
        return _result(
            UNKNOWN,
            diagnostic="unrecognized native status {0!r} for family {1!r}".format(
                native_status, family
            ),
        )

    # Rung 6 again: a lifecycle is expected here and no status was supplied at all.
    return _result(
        UNKNOWN,
        diagnostic="no native status supplied for family {0!r}, which has a lifecycle".format(
            family
        ),
    )


def resolve_readiness(readiness: Optional[str]) -> Resolved:
    """Resolve a review READINESS value (Section 6.7), which is NOT a subject status.

    Kept as its own entry point rather than as a family of ``resolve`` so a caller cannot pass a
    readiness word where a stored status belongs. The rendering obligation travels with it: a
    readiness column MUST be labeled (``READINESS_LABEL``) so it cannot be mistaken for the
    subject's stored state.
    """
    token = _normalize(readiness)
    stage = REVIEW_READINESS.get(token) if token is not None else None
    if stage is None:
        return Resolved(
            stage=UNKNOWN,
            style=style_for(UNKNOWN),
            family=FAMILY_REVIEWS,
            native_status=readiness if token is not None else None,
            diagnostic="unrecognized review readiness {0!r}".format(readiness),
        )
    return Resolved(
        stage=stage,
        style=style_for(stage),
        family=FAMILY_REVIEWS,
        native_status=readiness,
    )


# ======================================================================================
# 5. Self-validation (R10.1)
# ======================================================================================

# The statuses this module CLAIMS to cover per family. This is the module's own declaration, and it
# exists so `validate()` can check coverage WITHOUT importing an owner module (R10.1 makes this
# module stdlib-only, so it may not reach into `plans`, `runner_shutdown` and friends). The test
# suite closes the loop from the other side: criterion A2 enumerates the real OWNER ENUMS and
# fails when one grows a member no map covers. Both halves are needed, and neither substitutes for
# the other: this one catches a table edited inconsistently, that one catches an owner that moved.
KNOWN_STATUSES: Mapping[str, FrozenSet[str]] = MappingProxyType(
    {family: frozenset(table) for family, table in NATIVE_MAPS.items()}
)


def validate() -> None:
    """Raise unless this module's tables are internally complete and consistent (R10.1).

    Called at IMPORT (see the bottom of this file), so a table defect is a loud failure at the
    first import rather than a wrong glyph discovered later in a view. R10.1 permits either an
    import-time raise or an explicit call; doing both costs nothing and fails closed.

    WHAT IT CHECKS, and what each check would have caught:

    1. The stage table has the twenty Section 5 stages, with no duplicate key (enforced during
       construction by ``_build_stage_table``, re-asserted here so an explicit call is meaningful).
    2. Every stage row is well-formed: a non-empty Unicode grapheme, a single-character ASCII
       fallback, an xterm-256 index in range, a real bool.
    3. Every mapping value in every family is a DEFINED stage (a typo'd stage name).
    4. Every family this module admits has either a mapping table or a no-lifecycle policy, and
       never both (a family added to one list and forgotten in the other).
    5. Every family's declared ``KNOWN_STATUSES`` set is fully covered by its map (a status
       declared known but dropped from the table).
    6. The stage names ``unknown`` and ``none`` exist, since R10.4's whole distinction rests on
       them, and the activity stages are all real stages.
    """
    # 1 + 2: the stage table.
    if len(STAGES) != len(_STAGE_ROWS):
        raise LifecycleStyleError(
            "stage table lost rows during construction: {0} rows in, {1} keys out".format(
                len(_STAGE_ROWS), len(STAGES)
            )
        )
    if len(STAGE_ORDER) != len(set(STAGE_ORDER)):
        raise LifecycleStyleError("duplicate stage key in STAGE_ORDER")
    for stage, style in STAGES.items():
        if style.stage != stage:
            raise LifecycleStyleError(
                "stage row {0!r} is filed under key {1!r}".format(style.stage, stage)
            )
        if not style.unicode:
            raise LifecycleStyleError(
                "stage {0!r} has no Unicode grapheme".format(stage)
            )
        if len(style.ascii) != 1 or not style.ascii.isascii():
            raise LifecycleStyleError(
                "stage {0!r} has ASCII fallback {1!r}; Section 9.3 guarantees single-byte "
                "alignment in ASCII mode, so it must be exactly one ASCII character".format(
                    stage, style.ascii
                )
            )
        if not isinstance(style.color, int) or not 0 <= style.color <= 255:
            raise LifecycleStyleError(
                "stage {0!r} has color {1!r}, which is not an xterm-256 index".format(
                    stage, style.color
                )
            )
        if not isinstance(style.bold, bool):
            raise LifecycleStyleError(
                "stage {0!r} has non-bool bold flag {1!r}".format(stage, style.bold)
            )
        if not style.meaning.strip():
            raise LifecycleStyleError("stage {0!r} has no meaning text".format(stage))

    # 6: the stages R10.4 and Section 7.1 depend on by name.
    for required in (UNKNOWN, NONE):
        if required not in STAGES:
            raise LifecycleStyleError(
                "stage {0!r} is missing; R10.4's unknown-versus-none distinction requires "
                "both".format(required)
            )
    for stage in sorted(ACTIVITY_STAGES):
        if stage not in STAGES:
            raise LifecycleStyleError(
                "activity stage {0!r} is not a defined semantic stage".format(stage)
            )

    # 3: every mapped value is a real stage.
    for family, table in NATIVE_MAPS.items():
        for status, stage in table.items():
            if stage not in STAGES:
                raise LifecycleStyleError(
                    "family {0!r} maps {1!r} to undefined stage {2!r}".format(
                        family, status, stage
                    )
                )
    for label, table in (
        ("review-readiness", REVIEW_READINESS),
        ("condition", CONDITION_STAGES),
    ):
        for status, stage in table.items():
            if stage not in STAGES:
                raise LifecycleStyleError(
                    "{0} maps {1!r} to undefined stage {2!r}".format(
                        label, status, stage
                    )
                )
    for action, stage in ACTIVITY_FROM_ACTION.items():
        if stage not in ACTIVITY_STAGES:
            raise LifecycleStyleError(
                "action {0!r} maps to {1!r}, which is not an activity stage; Section 7.1 may "
                "only select an activity".format(action, stage)
            )

    # 4: families are partitioned, never overlapping and never orphaned.
    overlap = sorted(set(NATIVE_MAPS) & NO_LIFECYCLE_FAMILIES)
    if overlap:
        raise LifecycleStyleError(
            "families claim BOTH a mapping table and a no-lifecycle policy: {0}".format(
                ", ".join(overlap)
            )
        )
    unpoliced = sorted(FAMILIES - set(NATIVE_MAPS) - NO_LIFECYCLE_FAMILIES)
    if unpoliced:
        raise LifecycleStyleError(
            "families with no policy at all: {0}".format(", ".join(unpoliced))
        )

    # 5: declared coverage is actual coverage.
    for family, statuses in KNOWN_STATUSES.items():
        table = NATIVE_MAPS.get(family)
        if table is None:
            raise LifecycleStyleError(
                "KNOWN_STATUSES declares family {0!r}, which has no mapping table".format(
                    family
                )
            )
        missing = sorted(statuses - set(table))
        if missing:
            raise LifecycleStyleError(
                "family {0!r} declares known statuses it does not map: {1}".format(
                    family, ", ".join(missing)
                )
            )


# FAIL CLOSED AT IMPORT. A defect in the one canonical table must not wait for a view to render it.
validate()
