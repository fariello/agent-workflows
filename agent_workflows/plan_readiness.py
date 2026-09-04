"""The SINGLE shared plan-readiness predicate the runners' auto-approve gate consumes.

Set fullauto, Order 01 (plan 97df1z). This module exists for two reasons, and the second one is the
bug the plan was written to fix.

1. DE-DUPLICATION. ``is_plan_review_approved`` and its history helper lived TWICE, once in
   ``oc_runipd`` and once in ``agy_runipd``, and the copies had ALREADY drifted (the agy copies had
   lost their docstrings). Two copies of a safety gate is one copy too many: fixing only one would
   have left ``aw agy run --full-auto`` broken. Both drivers now import from here.

2. THE HISTORY SECTION IS BOUNDED AND NEWEST-FIRST, and the shipped reader honored neither.
   The old ``extract_last_history_entry`` did ``text[text.rfind("## Workflow history"):]`` with NO
   upper bound, so the slice ran to END OF FILE across every later section (measured: 15,654 chars
   over 13 headings on one real plan), and then returned the LAST ``- `` bullet in it - typically a
   final-section trailer such as ``- Cohesion rationale: ...``. Measured before the fix: for 35 of 35
   plans in ``.aw/records/plans/pending/`` the returned string was not a history record at all, so
   the gate returned False for EVERY plan regardless of what any review had written.

   Even bounded, "last" would still be wrong. ``aw set`` PREPENDS each new record directly under the
   heading (``status_set.py:799``, ``new_lines.insert(i + 1, hist_entry)``), so the section is
   NEWEST-FIRST and the CURRENT state is the FIRST record. The surrounding comment there said
   "Append" and ``.aw/records/plans/README.md`` said "an appended, dated line"; both were corrected
   to say newest-first (E-07) precisely so a future reader does not "fix" this back into the bug.

   The bounding and the record grammar are REUSED, not re-implemented: ``attention._history_section_lines``
   already bounds the section at the next ``## `` heading and ``attention_contract.HISTORY_RECORD_RE``
   already defines the ``- YYYY-MM-DD <text>`` record grammar. A fourth hand-rolled history parser
   would have been the wrong move.

DECISION ORDER (field first, prose only as a bounded fallback):

- ``- Readiness: go`` or ``go-pending-approval`` -> approvable. ``no-go`` -> refused.
- Field ABSENT -> fall back to the CORRECTED newest history record, accepting only verdict
  ``APPROVE`` / ``APPROVE WITH REVISIONS APPLIED`` with no negative readiness token and no
  unresolved blocking open question.
- Field PRESENT but OUT-OF-VOCAB (e.g. ``Readiness: bogus``) -> refused OUTRIGHT, with no fallback.
  This case is deliberately NOT treated as absence: the review DID try to record a readiness and we
  cannot tell what it meant, so falling back to prose could approve a plan whose author was trying
  to say ``no-go``. Absence means "no signal was recorded"; a bad value means "the signal is
  corrupt", and only the former is safe to fall back from.
- Anything unparseable, unreadable, or unrecognized -> ``False``. The gate FAILS CLOSED; absence of
  evidence is never treated as evidence of approval.

The predicate answers exactly one question: has review CLEARED this plan? It deliberately does NOT
read ``Status:``. Gating on ``Status: reviewed`` stays with the caller, so this module cannot widen
what ``--full-auto`` is allowed to approve.

--------------------------------------------------------------------------------------------------
Set apprvguard, Order 01 (plan d7bnhc) EXTENDED this module with the APPROVAL gate, which is a
DIFFERENT question from the auto-approve gate above, asked by a different caller for a different
reason. Keep the two straight, because they deliberately disagree:

- :func:`is_plan_review_approved` answers "may AUTOMATION approve this with no human in the loop?"
  It FAILS CLOSED. A false negative merely means ``--full-auto`` leaves the plan for a human, which
  costs nothing.
- :func:`approval_refusals` answers "must this HUMAN-DRIVEN approval be REFUSED?" Its verdict half
  has NO override by design, so a false POSITIVE is a hard lockout that no flag can clear. It is
  therefore deliberately LOOSER about prose than the predicate above (see :func:`newest_verdict`).

The vocabulary itself now lives in ONE place, :data:`VERDICTS` and :data:`READINESS_TOKENS`, with
:func:`history_verdict_approves` rebuilt on top of it. It used to be three separate private regexes;
two independent encodings of one vocabulary is how two gates end up giving two answers about the
same plan, so they were replaced rather than added to (d7bnhc D1).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from agent_workflows import ipd_schema as _schema
from agent_workflows.attention import _history_section_lines
from agent_workflows.attention_contract import HISTORY_RECORD_RE

__all__ = [
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
    "VERDICTS",
    "READINESS_TOKENS",
    "approval_refusals",
    "classify_verdict",
    "extract_newest_history_entry",
    "history_verdict_approves",
    "has_unresolved_blocking_question",
    "is_plan_review_approved",
    "is_review_history_entry",
    "newest_verdict",
]

# ------------------------------------------------------------------------------------------------
# The ONE encoding of `/plan-review`'s two closed vocabularies (apprvguard d7bnhc E-02).
# ------------------------------------------------------------------------------------------------
# Polarity labels. Deliberately three, not a bool: `REVIEWED - OPEN QUESTIONS` is neither a clearance
# nor a rejection, and collapsing it either way loses the distinction both gates need.
POSITIVE = "positive"
NEUTRAL = "neutral"
NEGATIVE = "negative"

# The VERDICT vocabulary, verbatim from the plan-review workflow's verdict list
# (`.aw/system/workflows/plan-review/plan-review.md`, "Verdict and readiness"). Exactly four values.
VERDICTS: Dict[str, str] = {
    "APPROVE": POSITIVE,
    "APPROVE WITH REVISIONS APPLIED": POSITIVE,
    "REVIEWED - OPEN QUESTIONS": NEUTRAL,
    "REJECT - NEEDS REPLAN": NEGATIVE,
}

# The READINESS vocabulary, which the same workflow section defines as SEPARATE from the verdict.
# `CONDITIONAL-GO` appears in NEITHER documented vocabulary (d7bnhc F-4) but the shipped gate has
# always treated it as not-ready, so it is kept negative for backward compatibility and marked
# UNDOCUMENTED here rather than silently propagated as if the workflow defined it.
READINESS_TOKENS: Dict[str, str] = {
    "GO": POSITIVE,
    "GO - PENDING HUMAN APPROVAL": POSITIVE,
    "NO-GO": NEGATIVE,
    "CONDITIONAL-GO": NEGATIVE,  # UNDOCUMENTED: in no workflow vocabulary; negative for compat.
}


def _vocabulary_scan_re(vocabulary: Sequence[str]) -> "re.Pattern[str]":
    """One scanning regex over ``vocabulary``, LONGEST ALTERNATIVE FIRST.

    The ordering is the whole point and is why this is derived rather than hand-written: Python's
    ``|`` is first-match-wins, so with ``APPROVE`` ahead of ``APPROVE WITH REVISIONS APPLIED`` the
    longer verdict could never be recognized as itself. Internal runs of spaces and the ``-`` in
    ``REVIEWED - OPEN QUESTIONS`` are relaxed to flexible whitespace so a reviewer's spacing does not
    change the classification.
    """
    parts = []
    for phrase in sorted(vocabulary, key=len, reverse=True):
        pattern = re.escape(phrase)
        pattern = re.sub(r"(?:\\\s|\s)+", r"\\s+", pattern)
        pattern = pattern.replace(r"\s+\-\s+", r"\s*-\s*")
        parts.append(pattern)
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.IGNORECASE)


_VERDICT_SCAN_RE = _vocabulary_scan_re(tuple(VERDICTS))
_READINESS_SCAN_RE = _vocabulary_scan_re(tuple(READINESS_TOKENS))
_NEGATIVE_READINESS_SCAN_RE = _vocabulary_scan_re(
    tuple(k for k, v in READINESS_TOKENS.items() if v == NEGATIVE)
)


def _normalize_token(raw: str) -> str:
    """A matched phrase folded to its canonical vocabulary key (upper, single-spaced, ``-`` tight)."""
    token = re.sub(r"\s+", " ", raw.strip()).upper()
    return (
        re.sub(r"\s*-\s*", " - ", token) if " - " in token or "- " in token else token
    )


def classify_verdict(text: str) -> Tuple[Optional[str], Optional[str]]:
    """The FIRST verdict token stated in ``text`` and its polarity, or ``(None, None)``.

    FIRST, not strongest and not last: a reviewer states their verdict at the head of the record and
    spends the rest of it on rationale, so a later mention is nearly always narration. Measured over
    all 577 review history records in this repository, 11 state more than one verdict token and in
    every case the leading one is the record's own verdict (d7bnhc D2).

    Pure. ``text`` is a single history record's message, not a whole plan.
    """
    m = _VERDICT_SCAN_RE.search(text or "")
    if not m:
        return None, None
    token = _normalize_token(m.group(0))
    # `VERDICTS` keys use the canonical `REVIEWED - OPEN QUESTIONS` spacing; fold anything else in.
    for key in VERDICTS:
        if _normalize_token(key) == token:
            return key, VERDICTS[key]
    return None, None


# Whether a `- Readiness:` bullet is PRESENT AT ALL, regardless of value. Needed because
# `read_readiness` collapses "absent" and "out-of-vocab" to None, and the two must be distinguished:
# absent falls back to prose, corrupt refuses outright (see `is_plan_review_approved`).
_READINESS_FIELD_PRESENT_RE = re.compile(r"(?m)^-[ \t]*Readiness:")

_OQ_HEADING_RE = _schema.OQ_HEADING_RE
_OQ_FIELD_RE = re.compile(r"^-[ \t]*([A-Za-z][A-Za-z /-]*?):[ \t]?(.*)$")


def extract_newest_history_entry(text: str) -> Optional[str]:
    """The NEWEST ``## Workflow history`` record of ``text``, or None when there is none.

    The FIRST record is the newest: ``aw set`` prepends each new record directly under the heading
    (``status_set.py:799``, ``new_lines.insert(i + 1, hist_entry)``), so the section is newest-first
    despite the word "append" that used to appear in its comment and in the plans README. Do NOT
    "fix" this to return the last record; that is the bug this function replaced.

    The section is BOUNDED at the next ``## `` heading (via the existing
    ``attention._history_section_lines``), so a bullet in a later section can never be returned, and
    a bullet must match the ``- YYYY-MM-DD ...`` record grammar (``HISTORY_RECORD_RE``) to count, so
    an undated stray bullet inside the section is skipped rather than returned.

    Pure. Returns the record with surrounding whitespace stripped.
    """
    for line in _history_section_lines(text):
        candidate = line.strip()
        if HISTORY_RECORD_RE.match(candidate):
            return candidate
    return None


def history_verdict_approves(entry: Optional[str]) -> bool:
    """Whether a history RECORD states a review verdict that clears the plan (fallback path only).

    True only for ``APPROVE`` or ``APPROVE WITH REVISIONS APPLIED`` with NO negative readiness token
    (``NO-GO`` / ``CONDITIONAL-GO``) ANYWHERE in the record and no other verdict token anywhere in
    it. Fails closed on None.

    THE ANY-MENTION RULE IS DELIBERATE HERE AND DELIBERATELY NOT SHARED with
    :func:`newest_verdict`, which classifies from the FIRST verdict token only. This function gates
    UNATTENDED approval, where a false negative costs one deferral to a human; that one refuses a
    human's own approval with no override, where a false positive is a lockout. Measured: 6 review
    records in this repository state a POSITIVE verdict and also contain the word ``NO-GO`` while
    narrating a readiness transition ("readiness moves NO-GO -> GO - PENDING HUMAN APPROVAL"), so
    this rule declines 6 plans that the approval gate must NOT refuse (d7bnhc D2).

    Rebuilt at apprvguard d7bnhc E-02 on :data:`VERDICTS` / :data:`READINESS_TOKENS`; the truth table
    is unchanged from the three private regexes it replaced.
    """
    if not entry:
        return False
    if _NEGATIVE_READINESS_SCAN_RE.search(entry):
        return False
    # ANY verdict token that is not itself a clearance disqualifies, wherever it appears, so a record
    # stating both (e.g. "REVIEWED - OPEN QUESTIONS ... will be APPROVE once decided") is refused.
    for m in _VERDICT_SCAN_RE.finditer(entry):
        token = _normalize_token(m.group(0))
        for key, polarity in VERDICTS.items():
            if _normalize_token(key) == token and polarity is not POSITIVE:
                return False
    return bool(_VERDICT_SCAN_RE.search(entry))


def _open_question_blocks(text: str) -> List[List[str]]:
    """The raw line groups under each ``### OQ-NN:`` heading in the ``## Open questions`` section."""
    blocks: List[List[str]] = []
    current: Optional[List[str]] = None
    in_section = False
    for line in text.split("\n"):
        if line.startswith("## "):
            if current is not None:
                blocks.append(current)
                current = None
            in_section = line.strip() == "## " + _schema.H_OPEN_QUESTIONS
            continue
        if not in_section:
            continue
        if line.startswith("### "):
            if current is not None:
                blocks.append(current)
            current = [line] if _OQ_HEADING_RE.match(line.rstrip()) else None
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def has_unresolved_blocking_question(text: str) -> bool:
    """Whether the plan carries an UNRESOLVED BLOCKING open question, decided MECHANICALLY.

    The test is the one the shipped pre-execution gate already uses (``ipd_lint.py``'s checkpoint
    rule): an ``### OQ-*`` block whose ``- Blocking:`` is ``yes`` and whose ``- Status:`` is not
    ``resolved``. It is deliberately NOT a prose judgement.

    FAIL-CLOSED RULE: an OQ block whose ``Blocking``/``Status`` fields cannot be parsed counts as
    BLOCKING. A question we cannot read is not a question we may assume was answered.
    """
    for block in _open_question_blocks(text):
        blocking: Optional[str] = None
        status: Optional[str] = None
        for line in block[1:]:
            m = _OQ_FIELD_RE.match(line.strip())
            if not m:
                continue
            field = m.group(1).strip().lower()
            value = m.group(2).strip().lower()
            if field == "blocking" and blocking is None:
                blocking = value
            elif field == "status" and status is None:
                status = value
        if blocking is None or status is None:
            return True  # unparseable -> treat as blocking
        if blocking not in _schema.OQ_BLOCKING_VALUES:
            return True  # unrecognized -> treat as blocking
        if blocking == "yes" and status != "resolved":
            return True
    return False


def is_plan_review_approved(plan_path: Path) -> bool:
    """Whether REVIEW has cleared this plan for automated approval. FAILS CLOSED.

    Decision order (see the module docstring): the structured ``- Readiness:`` field wins; when it is
    absent or out-of-vocab, a bounded back-compat fallback reads the CORRECTED newest history record
    and accepts only an approving verdict with no unresolved blocking open question.

    This function does NOT read ``- Status:``. The caller must independently require
    ``Status: reviewed`` before acting, which is what keeps this from widening the gate.
    """
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return False

    readiness = _schema.read_readiness(text)
    if readiness is not None:
        # The STRUCTURED signal is authoritative and beats any prose in the history line.
        return readiness in _schema.READINESS_APPROVABLE
    if _READINESS_FIELD_PRESENT_RE.search(text):
        # PRESENT but out-of-vocab (`read_readiness` normalizes that to None). Refuse OUTRIGHT: the
        # review tried to record a readiness and we cannot tell what it meant, so falling back to
        # prose could approve a plan whose author meant `no-go`. Absence -> fall back; corrupt -> no.
        return False

    # Back-compat fallback for a plan reviewed before the field existed.
    if not history_verdict_approves(extract_newest_history_entry(text)):
        return False
    if has_unresolved_blocking_question(text):
        return False
    return True


# ------------------------------------------------------------------------------------------------
# The APPROVAL gate (Set apprvguard, Order 01 / plan d7bnhc).
#
# `aw set approved` used to read STATUS ALONE. On 2026-08-30 a blanket "I APPROVE all the reviewed
# IPDs" therefore swept five plans whose own newest review said `REJECT - NEEDS REPLAN` into
# `approved`, the state that licenses execution, and only an unrelated pre-execution gate firing for
# an unrelated reason stopped them from rebuilding shipped subsystems. Everything below exists so
# that `approved` is UNREACHABLE for a plan whose own review said do not build it.
# ------------------------------------------------------------------------------------------------

# A history record's "middle" is the status/workflow token between the date and the `(actor)`, e.g.
# `- 2026-09-03 reviewed (opencode/...): ...` or `- 2026-08-30 /plan-review pass 2 (OpenCode ...): `.
_HISTORY_RECORD_PARTS_RE = re.compile(
    r"^-\s*(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<mid>[^(]*?)\s*\((?P<actor>[^)]*)\):\s*(?P<msg>.*)$"
)

# The tokens that mark a record as a REVIEW record. Derived from a census of every history record in
# this repository: the review-bearing middles are `reviewed`, `/plan-review` (with many suffixes such
# as ` pass 2`, ` focused`, ` RE-REVIEW`), `re-reviewed /plan-review`, `re-review`, and
# `/plan-review-long`. A prefix test on `/plan-review` covers the whole family without enumerating
# suffixes that reviewers keep inventing.
_REVIEW_WORDS = frozenset(("reviewed", "re-reviewed", "review", "re-review"))
_REVIEW_PREFIX = "/plan-review"


def is_review_history_entry(entry: str) -> bool:
    """Whether a history RECORD is itself a review record, as opposed to one merely mentioning review.

    THIS DISCRIMINATOR IS THE CENTRAL CORRECTNESS REQUIREMENT of the approval gate, and skipping it
    is the obvious wrong implementation. A naive "the newest entry contains REJECT" test would refuse
    exactly the plans that CORRECTLY REPLACED the rejected ones: measured, every pending plan matching
    ``grep 'REJECT - NEEDS REPLAN'`` is a successor whose newest record is a ``to-review`` entry
    NARRATING its retired predecessor's rejection (d7bnhc F-5). A verdict may only be read from a
    record that is a review record's own stated verdict.

    Pure. False for an unparseable record, which is the safe answer: an unreadable record states no
    verdict, so no refusal is derived from it.
    """
    m = _HISTORY_RECORD_PARTS_RE.match((entry or "").strip())
    if not m:
        return False
    for token in m.group("mid").replace(",", " ").split():
        lowered = token.lower()
        if lowered in _REVIEW_WORDS or lowered.startswith(_REVIEW_PREFIX):
            return True
    return False


def newest_verdict(text: str) -> Tuple[Optional[str], str]:
    """The polarity of the NEWEST REVIEW record's own verdict, and the raw record it was read from.

    Returns ``(polarity, raw_entry)`` where polarity is one of :data:`POSITIVE` / :data:`NEUTRAL` /
    :data:`NEGATIVE`, or ``None`` when no verdict could be read at all (no history, no review record,
    or a review record stating no verdict token). ``raw_entry`` is ``""`` when nothing was read, so a
    caller can quote the evidence in its refusal message.

    TWO RULES, both measured rather than guessed (d7bnhc D2):

    1. Only REVIEW records are consulted (:func:`is_review_history_entry`), and only the NEWEST one.
       The newest record of ANY kind is the wrong input; see that function for the measured reason.
    2. Within that record, the FIRST verdict token wins (:func:`classify_verdict`), and a negative
       READINESS token decides only when the record states no verdict token at all. This is
       deliberately looser than :func:`history_verdict_approves`'s any-mention rule, because a false
       refusal here cannot be overridden by any flag: measured, 6 review records state a positive
       verdict and also contain ``NO-GO`` while narrating a readiness change, and refusing those
       would lock out legitimate approvals.

    THIS IS THE PROSE PATH ONLY. It deliberately does NOT read the structured ``- Readiness:`` field,
    so that the field-versus-prose decision order lives in exactly one place. :func:`approval_refusals`
    consults the field FIRST and reaches this function only as a fallback, matching the three-way rule
    :func:`is_plan_review_approved` already implements (valid field is authoritative / absent field
    falls back to prose / out-of-vocab field refuses outright). Two gates disagreeing about the same
    plan is worse than either rule alone, which is why the ordering is stated in both docstrings.

    Pure; takes whole plan text.
    """
    for line in _history_section_lines(text or ""):
        candidate = line.strip()
        if not HISTORY_RECORD_RE.match(candidate):
            continue
        if not is_review_history_entry(candidate):
            continue  # a non-review record states no verdict of its own; keep looking backwards.
        m = _HISTORY_RECORD_PARTS_RE.match(candidate)
        message = m.group("msg") if m else candidate
        _, polarity = classify_verdict(message)
        if polarity is not None:
            return polarity, candidate
        # No verdict token at all. A negative READINESS token is then the only signal present, and it
        # is unambiguous precisely BECAUSE no verdict competes with it for the reader's attention.
        if _NEGATIVE_READINESS_SCAN_RE.search(message):
            return NEGATIVE, candidate
        return None, candidate
    return None, ""


def approval_refusals(
    repo_root,
    plan_path,
    plan_text: Optional[str] = None,
    *,
    allow_open_questions: bool = False,
) -> List[str]:
    """Every reason this artifact may NOT be moved to a ready-to-execute status. Empty means allowed.

    THE ONE PREDICATE EVERY APPROVAL SURFACE CONSUMES. There are two such surfaces
    (``status_set.validate_transition_allowed`` and the forked ``specs.run_set``, reached by a
    different CLI spelling), and a gate installed in one of them is simply bypassed by choosing the
    other, so both call HERE rather than implementing this twice.

    It COMPOSES three shipped sources and reimplements none of them:

    1. THE PROSE VERDICT, via :func:`newest_verdict`, but only after the structured
       ``- Readiness:`` field has been consulted, in the SAME three-way order
       :func:`is_plan_review_approved` uses: a valid field is authoritative and prose is never read;
       an ABSENT field falls back to prose; an OUT-OF-VOCAB field refuses outright with no fallback,
       because absence means "no signal recorded" while a bad value means "the signal is corrupt".
    2. THE TYPED REVIEW ARTIFACT, via ``review_findings.plan_gating_blocks``, reused UNCHANGED so the
       one severity comparison (``review_findings.is_gating``) is not forked - there is an explicit
       anti-fork guard test at ``tests/test_review_findings_gate.py``. An ABSENT review artifact is
       SILENT, not blocking, which is that function's documented contract and is required for safety
       rather than laziness: only 34 ``.review.md`` files exist against 400+ plans.
    3. UNRESOLVED BLOCKING OPEN QUESTIONS, via :func:`has_unresolved_blocking_question`, the SHIPPED
       predicate rather than a third copy. Note it is STRICTER than ``ipd_lint``'s checkpoint form
       (``Status != "resolved"`` versus ``Status == "open"``) and fails closed on an unparseable
       block; the stricter rule is chosen deliberately, since this half IS overridable and the
       override is where an unreadable question gets a human's attention.

    OVERRIDE ASYMMETRY, which is the design's core: ``allow_open_questions`` suppresses ONLY the
    open-question refusals. A negative verdict and a typed gating finding have NO override at all,
    because the whole point is that no flag should be able to turn "do not build this" into
    "executable". A caller wanting to approve anyway must get the review's verdict changed.

    ``plan_text`` is accepted so a caller that already holds the text does not re-read it. Never
    raises: an unreadable path yields no refusals, matching the shipped absent-is-silent precedent
    (a crashing gate is a disabled gate, and one that refuses everything is worse than none).
    """
    path = Path(plan_path)
    if plan_text is None:
        try:
            plan_text = path.read_text(encoding="utf-8")
        except OSError:
            return []

    refusals: List[str] = []

    # (1) Structured field FIRST, prose only as a bounded fallback.
    readiness = _schema.read_readiness(plan_text)
    if readiness is not None:
        if readiness not in _schema.READINESS_APPROVABLE:
            refusals.append(
                "review recorded `- Readiness: {0}`, which does not clear this plan for "
                "execution. This refusal has NO override: get the review's readiness changed "
                "(re-run /plan-review) rather than forcing the approval.".format(
                    readiness
                )
            )
    elif _READINESS_FIELD_PRESENT_RE.search(plan_text):
        refusals.append(
            "a `- Readiness:` field is present but its value is not one of {0}. A CORRUPT "
            "readiness is not treated as an absent one: the review tried to record a readiness "
            "and we cannot tell what it meant. Fix the field.".format(
                ", ".join(sorted(_schema.READINESS_VALUES))
            )
        )
    else:
        polarity, entry = newest_verdict(plan_text)
        if polarity == NEGATIVE:
            refusals.append(
                "the newest review record states a verdict that does not clear this plan, so "
                "approving it would license execution of a plan its own review rejected. This "
                "refusal has NO override. Record: {0}".format(_one_line(entry))
            )

    # (2) The TYPED review artifact, reused unchanged. Absent artifact -> silent, by contract.
    id6_match = re.search(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$", plan_text)
    if id6_match is not None:
        try:
            from agent_workflows import review_findings as _rf

            for block in _rf.plan_gating_blocks(repo_root, id6_match.group(1)):
                refusals.append(
                    "the typed review artifact records an unresolved gating finding: {0}".format(
                        block.describe()
                    )
                )
        except Exception:
            # A crashing gate is a disabled gate; never let an unreadable review tree refuse an
            # approval on its own. The prose half above still applies.
            pass

    # (3) Blocking open questions - the ONLY overridable half.
    if not allow_open_questions and has_unresolved_blocking_question(plan_text):
        refusals.append(
            "an unresolved BLOCKING open question remains ({0}). Resolve it, or pass "
            "--allow-open-questions to approve over it (the override is recorded in the "
            "artifact's history).".format(_blocking_question_ids(plan_text) or "OQ")
        )

    return refusals


def _blocking_question_ids(text: str) -> str:
    """The ``OQ-NN`` ids of every unresolved blocking question, comma-joined, for a refusal message.

    A refusal that does not name its cause is the failure mode this whole area exists to remove, so
    the message quotes the ids rather than saying "a blocking question".
    """
    ids: List[str] = []
    for block in _open_question_blocks(text):
        heading = _OQ_HEADING_RE.match(block[0].rstrip())
        if not heading:
            continue
        single = "\n".join(block)
        if has_unresolved_blocking_question(
            "## " + _schema.H_OPEN_QUESTIONS + "\n" + single + "\n"
        ):
            ids.append(heading.group(1))
    return ", ".join(ids)


def _one_line(text: str, limit: int = 220) -> str:
    """``text`` collapsed to one bounded line, so a refusal cannot dump a 2000-char history record."""
    flat = re.sub(r"\s+", " ", (text or "").strip())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."
