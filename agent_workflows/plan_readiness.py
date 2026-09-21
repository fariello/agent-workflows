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

- ``- Readiness: go`` or ``go-pending-approval`` -> approvable, BUT ONLY IF the plan's own
  ``## Workflow history`` contains a REVIEW RECORD that could have produced it
  (:func:`history_has_review_record`). ``no-go`` -> refused. A valid field with NO review behind it
  is refused too: it asserts a clearance that never happened (rdattest ``8v5pwa``; see
  :func:`is_plan_review_approved` for the measured forgery). The field still decides WHAT the answer
  is when it is attested, so prose is never consulted to overrule an attested field.
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
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import ipd_schema as _schema
from agent_workflows.attention import _history_section_lines
from agent_workflows.attention_contract import HISTORY_RECORD_RE

__all__ = [
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
    "VERDICTS",
    "READINESS_TOKENS",
    "RECHECK_SOURCE_READINESS",
    "RECHECK_TARGET_READINESS",
    "ConditionResult",
    "RecheckResult",
    "approval_refusals",
    "classify_verdict",
    "extract_newest_history_entry",
    "format_recheck_history_entry",
    "history_has_review_record",
    "history_verdict_approves",
    "has_unresolved_blocking_question",
    "is_plan_review_approved",
    "is_review_history_entry",
    "newest_verdict",
    "recheck_conditions",
    "recheck_readiness",
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

#: A negative readiness token that the SAME SENTENCE reports CLEARING rather than asserting.
#:
#: MEASURED IN PRODUCTION 2026-09-19, and the cost was a whole run. Three `reaskscore` plans recorded
#: "clearing this plan's only blocking question and with it its `no-go`", which is a statement that the
#: no-go is GONE. `_NEGATIVE_READINESS_SCAN_RE` is a plain substring scan, so it matched the token
#: inside that clause and `newest_verdict` returned NEGATIVE for three plans that had just been
#: cleared. That reddened `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests
#: ::test_no_pending_plan_is_refused_on_a_verdict_today`, which reads the LIVE pending tree; the red
#: test failed the driver-run suite in every lane of run `run-20260919T194413Z-2056285`; a failed suite
#: made `integration_is_earned` return `suite-failed`; and that gates self-finalize, so nothing
#: integrated, three lanes were preserved unmerged, and eight further items cascaded to
#: `dependency-blocked`. Total: 2h10m and $55.02 for zero integrated work.
#:
#: TWO SHAPES, both observed in this repository's own history lines:
#:   1. a CLEARING VERB before the token ("clearing ... its `no-go`", "resolved ... the no-go");
#:   2. an ARROW TRANSITION away from it ("CHANGED `no-go` -> `go-pending-approval`").
#:
#: WHAT THIS DELIBERATELY DOES NOT DO: it does not relax the gate for a real rejection. A bare
#: "readiness no-go", a "REJECT - NEEDS REPLAN ... no-go", and a REGRESSION *to* no-go
#: ("go-pending-approval -> no-go") all still refuse, because none of them matches. The 80-character
#: bound and the `[^.]` class keep the clearing verb and the token inside ONE SENTENCE, so a record
#: that resolves one question and separately reports a new no-go is still refused.
_CLEARED_NEGATIVE_READINESS_RE = re.compile(
    r"(?:clear(?:ing|ed|s)?|resolv(?:ing|ed|es)?|lift(?:ing|ed|s)?|remov(?:ing|ed|es)?|"
    r"no longer|with it its|and with it)\b[^.]{0,80}?\b(?:no-go)\b"
    r"|\b(?:no-go)\b\s*`?\s*(?:->|-->|\u2192)\s*`?\s*(?:go|go-pending-approval)\b",
    re.IGNORECASE,
)


def negative_readiness_asserted(message: str) -> bool:
    """Whether ``message`` ASSERTS a negative readiness, as against reporting one CLEARED.

    Pure and side-effect free, so the distinction is testable without a plan on disk. Returns False
    for an empty message. See `_CLEARED_NEGATIVE_READINESS_RE` for the measured incident that made
    the plain substring scan insufficient and for what this intentionally still refuses.
    """

    if not message:
        return False
    if not _NEGATIVE_READINESS_SCAN_RE.search(message):
        return False
    return not _CLEARED_NEGATIVE_READINESS_RE.search(message)


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
    # DELIBERATELY THE PLAIN SCAN, NOT `negative_readiness_asserted`. This is the STRICTER
    # auto-approve rule, and it disqualifies on ANY mention of a negative readiness token, including
    # one a record narrates as CLEARED. The asymmetry with `newest_verdict` is intentional and pinned
    # by `ReviewEntryDiscriminatorTests::test_the_newest_review_records_verdict_is_read_from_every_
    # history_shape`: this rule's false negative costs ONE deferral to a human, while the approval
    # gate's false positive is an UNOVERRIDABLE LOCKOUT, so the two accept opposite risks on purpose.
    # Relaxing this line is a policy change about which risk we accept, not a bug fix.
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

    Decision order (see the module docstring): a valid structured ``- Readiness:`` field decides WHAT
    the answer is, but only once the plan's own ``## Workflow history`` shows a review PRODUCED it;
    when the field is absent, a bounded back-compat fallback reads the CORRECTED newest history record
    and accepts only an approving verdict with no unresolved blocking open question; when the field is
    present but out-of-vocab, the plan is refused outright with no fallback.

    THE FIELD IS NO LONGER BELIEVED ON ITS OWN (rdattest ``8v5pwa``). ``IPD-M107`` already refuses a
    hand-written ``- Readiness:`` at LINT time, but this PREDICATE accepted one, and it is the
    predicate that ``--full-auto`` consults to clear a `reviewed` plan to `auto-approved` (a shipped
    READY-TO-EXECUTE tier) and flip its queue action to `execute`. MEASURED at `b83a6cd9`: a plan
    carrying ``- Readiness: go`` whose whole history is one `to-review` record returned True, so a
    field typed at authoring time was a route from unreviewed to executable. The field and the history
    must now AGREE: :func:`history_has_review_record` must find a record whose own status/workflow
    middle marks it a review, which a MENTION of `plan-review`/`APPROVE`/`REJECT` in a non-review
    record does not satisfy.

    WHAT THIS DELIBERATELY DOES NOT CHECK: that the review's verdict was POSITIVE. The question here
    is PROVENANCE ("did a review write this field"), and the verdict question is already owned by
    :func:`newest_verdict` / :func:`approval_refusals`; asking it twice gives one plan two verdict
    gates that can disagree. So a plan whose review said NO-GO while its field says ``go`` is caught by
    the field's own vocabulary, by ``approval_refusals``, and by human approval, not here.

    This function does NOT read ``- Status:``. The caller must independently require
    ``Status: reviewed`` before acting, which is what keeps this from widening the gate.
    """
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return False

    readiness = _schema.read_readiness(text)
    if readiness is not None:
        # The STRUCTURED signal decides the ANSWER and beats any prose verdict in the history, but it
        # must first be ATTESTED: a field no review produced asserts a clearance that never happened.
        if not history_has_review_record(text):
            return False
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
#
# BOTH THE MIDDLE AND THE ACTOR CAPTURE LAZILY (plan fn2l1u E-08a), AND THIS PATTERN BACKED A GATE
# THAT FAILED OPEN. With `(?P<mid>[^(]*?)` plus `(?P<actor>[^)]*)`, a record whose actor CONTAINED
# parentheses did not match at all, so `is_review_history_entry` returned False, so `newest_verdict`
# returned None, so `approval_refusals` emitted ZERO refusals for a plan whose own newest review said
# `REJECT - NEEDS REPLAN`. Reproduced end to end through the real CLI before the fix: with a
# parenthesized actor, `aw set reviewed <id6> -m "/plan-review: REJECT - NEEDS REPLAN"` followed by
# `aw set approved <id6> --by-human` EXITED 0 and wrote `- Status: approved`; with a slash-form actor
# the identical second command EXITED 1 with "This refusal has NO override." A formatting accident
# therefore silently disabled the one un-overridable refusal this whole section exists to enforce.
#
# The widening is strictly ADDITIVE, measured over all 3073 tracked history records: ZERO
# previously-parsing records have any capture changed, and 336 newly parse. Note the actor guard at
# `status_set` now also refuses NEW records of that shape (fn2l1u E-07), so the hole is closed from
# both ends; this half is what makes the records ALREADY on disk readable, which a setter guard cannot
# do. Widen IN PLACE: `tests/test_plan_readiness.py` asserts there is only ONE encoding of this
# vocabulary, so do not add a third parser.
_HISTORY_RECORD_PARTS_RE = re.compile(
    r"^-\s*(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<mid>.*?)\s*\((?P<actor>.*?)\):\s*(?P<msg>.*)$"
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


def history_has_review_record(text: str) -> bool:
    """Whether ANY record in the plan's bounded ``## Workflow history`` is a REVIEW record.

    THE PROVENANCE QUESTION, and it is deliberately a different question from
    :func:`newest_verdict`'s. This answers "did a review ever run on this plan", not "what is the
    current verdict"; the latter is already owned by :func:`newest_verdict` / :func:`approval_refusals`
    and duplicating it here would give one plan two verdict gates that can disagree. Its sole consumer
    is :func:`is_plan_review_approved`, which uses it to require that a PRESENT ``- Readiness:`` field
    be accounted for by a review in the plan's own history (rdattest ``8v5pwa`` E-01).

    ANY RECORD, NOT THE NEWEST, and that choice is measured rather than aesthetic. A plan's newest
    record is routinely a LATER lifecycle transition (`approved`, `executed`, a maintainer note) that
    legitimately post-dates the review which wrote the field, so a newest-record test would refuse a
    correctly reviewed plan for having progressed. MEASURED over all 694 tracked plans on 2026-09-20:
    the any-record rule flips ZERO auto-approve verdicts while a newest-record rule would flip 237 of
    the 238 that answer True, i.e. it would disable the gate's positive half almost entirely. Refusing
    a forgery does not need the stricter rule either, because a forged plan has NO review record
    anywhere.

    IT REUSES :func:`is_review_history_entry` RATHER THAN A MENTION-MATCHER, which is the whole point
    of the fix. ``ipd_lint._REVIEW_EVIDENCE_RE`` scans the WHOLE history text for `/plan-review`,
    `APPROVE`, `NO-GO` or `REJECT`, so it matches a bare MENTION in a non-review record: a `to-review`
    line saying "I mention plan-review in passing", a `draft` line containing the word `APPROVE`, and a
    successor narrating its predecessor's `REJECT` all satisfy it, and each is exactly the forged field
    this gate must refuse. The discriminator instead requires a review token in the record's OWN
    status/workflow middle, so it refuses all three. That is also why `plan_readiness` does NOT import
    `ipd_lint` for this (`ipd_lint` reaches `attention`, `check_engine`, `renderers` and the CLI stack
    through function-scoped imports, and both host drivers import this module).

    Pure. False for text with no history section, which is the fail-closed answer.
    """
    for line in _history_section_lines(text or ""):
        candidate = line.strip()
        if not HISTORY_RECORD_RE.match(candidate):
            continue
        if is_review_history_entry(candidate):
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
    :func:`is_plan_review_approved` also implements (valid field decides / absent field falls back to
    prose / out-of-vocab field refuses outright). Two gates disagreeing about the same plan is worse
    than either rule alone, which is why the ordering is stated in both docstrings.

    ONE DIFFERENCE, AND IT IS DELIBERATE (rdattest ``8v5pwa``): :func:`is_plan_review_approved`
    additionally requires the FIELD to be ATTESTED by a review record in the plan's history before
    honoring it, and THIS gate does not. That is not drift. This half backs a HUMAN's approval and its
    verdict refusal has NO override, so a false positive here is a lockout; the auto-approve predicate
    gates UNATTENDED promotion to an executable tier, where a forged field is the worse risk. The
    field-versus-prose ORDER is identical in both; only the provenance requirement differs.

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
        # BUT ONLY WHEN IT IS ASSERTED: a record stating that a no-go was CLEARED contains the token
        # while saying the opposite, which is what `negative_readiness_asserted` separates. Measured
        # 2026-09-19: the plain scan returned NEGATIVE for three just-cleared plans and cost a run.
        if negative_readiness_asserted(message):
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
       THIS GATE DOES NOT ADD THE PROVENANCE REQUIREMENT the auto-approve predicate now applies
       (rdattest ``8v5pwa``): an unattested field there refuses UNATTENDED promotion, which costs one
       deferral, while refusing it here would be an un-overridable lockout on a human's own approval.
       The ORDER is shared; only that extra requirement is not, and the difference is a risk choice.
    2. THE TYPED REVIEW ARTIFACT, via ``review_findings.subject_gating_blocks``, reused UNCHANGED so the
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

            for block in _rf.subject_gating_blocks(repo_root, id6_match.group(1)):
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


# ------------------------------------------------------------------------------------------------
# The READINESS RE-CHECK (Set rdyrecheck, Order 01 / plan qhy3i3).
#
# THE DEFECT. A `- Readiness: no-go` records a MOMENT, not a condition. Nothing re-evaluates it when
# the cause it was set for is removed, so a plan whose blocking question has been answered stays
# permanently unapprovable behind a refusal that, by design, has NO override (see the message in
# `approval_refusals` above: "get the review's readiness changed (re-run /plan-review)"). The only
# sanctioned remedy was therefore a FULL RE-REVIEW of a document whose findings were already swept.
#
# WHY A COMPUTATION AND NOT AN EDITING LICENCE. `AGENTS.md` forbids an agent hand-writing a
# `- Readiness:` value, because the auto-approve predicate reads that FIELD FIRST and a hand-written
# value asserts a review that never happened. That prohibition is NOT relaxed here. What makes this
# verb legitimate is three properties, each pinned by a test:
#   1. It COMPUTES the value from the three conditions the plan-review contract already enumerates,
#      using the SHIPPED predicates (no fork).
#   2. It can only ever write `no-go` -> `go-pending-approval`, a state that STILL REQUIRES a human.
#      `go` is unreachable from here; only a review may set it.
#   3. It RECORDS its computed evidence in the plan's own history, labelled a re-check, so the new
#      value carries its basis exactly as a review's verdict does.
#
# WHY THE RESULT IS PER-CONDITION AND NOT A BOOLEAN. The whole defect is that a verdict lost its
# reason. A re-check that also collapses to one bit reintroduces the same defect one layer down, so
# the caller must be able to say WHICH condition still holds and the record must name it.
# ------------------------------------------------------------------------------------------------

#: The ONLY readiness value this re-check will read as its input, and the ONLY one it will write as
#: its output. Named constants rather than inline literals because E-02's pinning test asserts the
#: write target by NAME: a future edit that widens the target has to change a constant every test in
#: `tests/test_plan_readiness_recheck.py` reads, instead of a bare string buried in a function.
RECHECK_SOURCE_READINESS = "no-go"
RECHECK_TARGET_READINESS = "go-pending-approval"


class ConditionResult(NamedTuple):
    """One of the three `no-go` conditions, recomputed: whether it HOLDS and the reason why.

    ``holds`` True means the condition is STILL TRUE and therefore still justifies `no-go`.
    ``reason`` is a human-readable clause naming the specific cause when it holds, and the evidence
    of clearance when it does not; it is never empty, because a condition result that does not state
    its basis is the failure mode this whole module exists to remove.
    """

    name: str
    holds: bool
    reason: str


class RecheckResult(NamedTuple):
    """The full per-condition recomputation for one plan, plus whether a write is permitted.

    ``conditions`` is always the three results in a stable order (blocking question, gating finding,
    negative verdict), so a caller renders a fixed table rather than discovering fields.

    ``refusals`` is every reason NOT to write, which is deliberately WIDER than "a condition holds":
    it also carries the precondition refusals (an absent field, an out-of-vocab field, a readiness
    that is not `no-go`). Empty ``refusals`` is the ONE state in which a write is permitted, and the
    write is then unconditionally to :data:`RECHECK_TARGET_READINESS`.
    """

    id6: str
    readiness: Optional[str]
    readiness_present: bool
    conditions: Tuple[ConditionResult, ...]
    refusals: Tuple[str, ...]

    @property
    def may_write(self) -> bool:
        """Whether the re-check is permitted to write. Empty refusals and nothing else."""
        return not self.refusals

    def holding(self) -> Tuple[ConditionResult, ...]:
        """Only the conditions that STILL HOLD, for a caller naming the surviving cause."""
        return tuple(c for c in self.conditions if c.holds)


C_BLOCKING_QUESTION = "unresolved-blocking-question"
C_GATING_FINDING = "unresolved-gating-finding"
C_NEGATIVE_VERDICT = "negative-review-verdict"


def recheck_conditions(
    repo_root, plan_path, plan_text: Optional[str] = None
) -> RecheckResult:
    """Recompute the three `no-go` conditions INDIVIDUALLY, composing the shipped predicates.

    THE THREE CONDITIONS ARE THE CONTRACT'S OWN, not new policy: `/plan-review` enumerates them
    (`.aw/system/workflows/plan-review/plan-review.md`, the readiness vocabulary) and this module
    already computes all three inside :func:`approval_refusals`. The gap this function closes is that
    nothing recomputed them AFTER the fact.

    IT FORKS NOTHING. Condition 1 is :func:`has_unresolved_blocking_question`, condition 2 is
    ``review_findings.subject_gating_blocks``, condition 3 is :func:`newest_verdict`; each is the
    shipped predicate :func:`approval_refusals` itself composes, called here rather than copied.
    ``tests/test_review_findings_gate.py`` carries an explicit anti-fork guard for the second.

    CONDITION 1 IS BLOCKING-ONLY, AND THAT IS A DELIBERATE DEPARTURE recorded as the maintainer's
    2026-09-10 ruling on this plan's OQ-01: a NON-BLOCKING open question does NOT make a plan
    not-ready, because the `- Blocking:` flag exists precisely to record which questions must stop
    work and treating both kinds alike discards the distinction. Measured scale behind the ruling: 43
    of 104 pending plans carried ONLY non-blocking questions, so the contract's former literal
    wording ("any open question") was holding 43 plans for reasons their own authors judged
    non-stopping. The contract wording was amended in the same change (this plan's E-05), so the code
    and the document agree rather than drift.

    HOW THE OVERRIDABLE HALF IS CONSUMED, stated rather than inherited silently. :func:`approval_refusals`
    applies the STRICTER ``Status != "resolved"`` rule to open questions and exposes
    ``allow_open_questions`` to suppress exactly that half. This function calls
    :func:`has_unresolved_blocking_question` DIRECTLY for condition 1, which is the blocking-only test
    the ruling requires, and it does NOT consult ``allow_open_questions`` at all: there is no override
    here, because a re-check that could be told to ignore a blocking question would be a bypass of the
    very gate it is recomputing. A caller wanting to approve over a blocking question uses
    ``aw ipd set approved --allow-open-questions``, which records the override in the artifact.

    Never raises. An unreadable plan yields a refusal naming that, not an exception: this function is
    consulted to decide whether to WRITE, and a crash would strand the plan exactly as the stale field
    does.
    """
    path = Path(plan_path)
    if plan_text is None:
        try:
            plan_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return RecheckResult(
                id6="",
                readiness=None,
                readiness_present=False,
                conditions=(),
                refusals=(
                    "the plan file could not be read ({0}), so nothing was recomputed".format(
                        exc
                    ),
                ),
            )

    id6_match = re.search(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$", plan_text)
    id6 = id6_match.group(1) if id6_match else ""

    # ---- Condition 1: an unresolved BLOCKING open question (the shipped, blocking-only predicate).
    blocking = has_unresolved_blocking_question(plan_text)
    if blocking:
        ids = _blocking_question_ids(plan_text) or "OQ"
        c1_reason = (
            "an unresolved BLOCKING open question remains ({0}); `has_unresolved_blocking_question` "
            "-> True".format(ids)
        )
    else:
        c1_reason = (
            "no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False "
            "(a NON-blocking open question is deliberately not counted, per the maintainer's "
            "2026-09-10 ruling on qhy3i3 OQ-01)"
        )
    c1 = ConditionResult(C_BLOCKING_QUESTION, blocking, c1_reason)

    # ---- Condition 2: an unresolved GATING finding in the TYPED review record.
    #
    # ABSENT REVIEW ARTIFACT IS SILENT, which is `subject_gating_blocks`'s documented contract and is
    # required for safety rather than laziness (only a minority of plans have a `.review.md`). A plan
    # with no review record therefore clears THIS condition, and the other two still apply.
    #
    # AN UNREADABLE REVIEW TREE IS A REFUSAL HERE, and that asymmetry with `approval_refusals` is
    # deliberate. There, a crashing review tree is swallowed because a crashing gate is a DISABLED
    # gate and swallowing it only makes the gate more permissive about refusing a human. Here the
    # output is a WRITE to an attestation field, so failing open would clear a plan on the strength of
    # an exception rather than on evidence. Fail closed instead.
    gating_blocks: Tuple = ()
    gating_error: Optional[str] = None
    if id6:
        try:
            from agent_workflows import review_findings as _rf

            gating_blocks = tuple(_rf.subject_gating_blocks(repo_root, id6))
        except Exception as exc:  # pragma: no cover - defensive
            gating_error = str(exc)
    if gating_error is not None:
        c2 = ConditionResult(
            C_GATING_FINDING,
            True,
            "the typed review artifact could not be evaluated ({0}); treated as HOLDING, because "
            "clearing a readiness on the strength of an exception would be fail-open".format(
                gating_error
            ),
        )
    elif not id6:
        c2 = ConditionResult(
            C_GATING_FINDING,
            True,
            "the plan carries no `- Id:` bullet, so no typed review record can be matched to it; "
            "treated as HOLDING, since an unidentifiable plan cannot be shown clear",
        )
    elif gating_blocks:
        c2 = ConditionResult(
            C_GATING_FINDING,
            True,
            "the typed review artifact records an unresolved gating finding: "
            + "; ".join(b.describe() for b in gating_blocks),
        )
    else:
        c2 = ConditionResult(
            C_GATING_FINDING,
            False,
            "no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty "
            "(an ABSENT review artifact is silent by that predicate's documented contract)",
        )

    # ---- Condition 3: a NEGATIVE verdict in the newest REVIEW history record.
    polarity, entry = newest_verdict(plan_text)
    if polarity == NEGATIVE:
        c3 = ConditionResult(
            C_NEGATIVE_VERDICT,
            True,
            "the newest review record states a verdict that does not clear this plan; "
            "`newest_verdict` -> negative. Record: {0}".format(_one_line(entry)),
        )
    else:
        c3 = ConditionResult(
            C_NEGATIVE_VERDICT,
            False,
            "the newest review record's verdict is not negative; `newest_verdict` -> {0}".format(
                polarity if polarity is not None else "none (no verdict token read)"
            ),
        )

    conditions = (c1, c2, c3)

    # ---- Preconditions on the FIELD ITSELF. These are refusals, not conditions: they are reasons the
    # re-check may not act at all, as distinct from reasons the plan is not ready.
    refusals: List[str] = []
    readiness = _schema.read_readiness(plan_text)
    present = bool(_READINESS_FIELD_PRESENT_RE.search(plan_text))
    if readiness is None and not present:
        # ABSENT. Refuse rather than mint: absence means NO REVIEW RECORDED A SIGNAL, and writing one
        # here would be exactly the forgery `AGENTS.md` forbids. Absence is also a LEGITIMATE state
        # that `approval_refusals` falls back to prose for, so it is not a defect to repair.
        refusals.append(
            "the plan has NO `- Readiness:` field. A re-check RE-EVALUATES a recorded readiness; it "
            "does not mint one. Absence means no review recorded a signal, and writing a value here "
            "would assert a review that never happened."
        )
    elif readiness is None:
        # PRESENT but out-of-vocab. `read_readiness` normalizes that to None, matching its fail-closed
        # contract; refuse, mirroring `approval_refusals`'s treatment of a CORRUPT field.
        refusals.append(
            "a `- Readiness:` field is present but its value is not one of {0}. A CORRUPT readiness "
            "is not treated as an absent one: fix the field, then re-check.".format(
                ", ".join(sorted(_schema.READINESS_VALUES))
            )
        )
    elif readiness != RECHECK_SOURCE_READINESS:
        refusals.append(
            "the plan's readiness is `{0}`, not `{1}`. This verb only ever re-evaluates a `{1}`; it "
            "has no path that lowers or re-asserts a readiness.".format(
                readiness, RECHECK_SOURCE_READINESS
            )
        )

    refusals.extend(c.reason for c in conditions if c.holds)

    return RecheckResult(
        id6=id6,
        readiness=readiness,
        readiness_present=present,
        conditions=conditions,
        refusals=tuple(refusals),
    )


#: The four `/plan-review` VERDICT tokens, which a re-check history entry must NOT contain.
#:
#: WHY THIS MATTERS MECHANICALLY: :func:`newest_verdict` scans history prose for exactly these tokens
#: and reads the NEWEST review record. A re-check entry containing one would either be read as a
#: review verdict itself or shadow the real review's, so the entry is checked against this tuple
#: before it is written and the assertion is pinned by a test.
REVIEW_VERDICT_TOKENS: Tuple[str, ...] = tuple(VERDICTS)

#: The finding ids a review record mentions, e.g. `PR-001..PR-008` or `PR-801`. Used to cite a review
#: by its FINDING SPAN rather than by quoting its text.
_FINDING_ID_RE = re.compile(r"\b([A-Z]{1,4}-\d{1,4})\b")


def cite_review_entry(entry: str) -> str:
    """A review record cited by its DATE and FINDING SPAN, carrying NO verdict token.

    QUOTING THE RECORD VERBATIM IS THE OBVIOUS WRONG IMPLEMENTATION, and it was the first one written
    here: a review record almost always states its verdict in its own message, so copying that message
    into the re-check entry imports the token, and :func:`newest_verdict` would then read the RE-CHECK
    as the newest review. The failure was caught by this plan's own V-03 assertion rather than in
    production, which is what that assertion exists for.

    So the citation is DERIVED, not copied: the record's date plus the span of finding ids it mentions,
    which is exactly what E-03 asks for ("its date and its finding span") and is enough for a reader to
    find the record being re-checked without re-running anything.

    Pure. Returns the empty string when nothing citable can be read.
    """
    if not entry:
        return ""
    m = _HISTORY_RECORD_PARTS_RE.match(entry.strip())
    if m is None:
        return ""
    date = m.group("date")
    ids = _FINDING_ID_RE.findall(m.group("msg") or "")
    # De-dupe preserving order, then state the SPAN rather than every id, so a 14-finding review cites
    # compactly and a reader still knows which rows were swept.
    seen: List[str] = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    if not seen:
        return "the review of {0} (no finding ids stated in its record)".format(date)
    if len(seen) == 1:
        span = seen[0]
    else:
        span = "{0}..{1}".format(seen[0], seen[-1])
    return "the review of {0}, findings {1}".format(date, span)


def format_recheck_history_entry(
    result: RecheckResult,
    *,
    date: str,
    actor: str,
    reviewed_entry: str = "",
    head: str = "",
) -> str:
    """Render the `## Workflow history` record for a performed re-check, carrying its evidence.

    THE ENTRY IS THE ATTESTATION, so it names the three conditions it evaluated, states that each was
    found clear, and cites the review it re-checked. A reader must be able to tell a re-check from a
    review AT A GLANCE and audit the claim WITHOUT re-running anything, which is the standard a
    review's own verdict record meets.

    IT MUST NOT READ AS A REVIEW VERDICT. The entry is labelled ``readiness re-check`` in the record's
    status/workflow middle, which :func:`is_review_history_entry` does NOT classify as a review, and it
    contains none of :data:`REVIEW_VERDICT_TOKENS`, which :func:`newest_verdict` scans for. Both
    properties are asserted by this function's caller before the write and pinned by tests, so
    `newest_verdict` keeps resolving to the REVIEW's record rather than to this one.

    Pure: builds a string, touches no disk. ``reviewed_entry`` is the review record being re-checked;
    it is CITED by date and finding span via :func:`cite_review_entry` and never quoted, because a
    review states its verdict in its own message and copying that would import the token. ``head`` is
    the commit the recomputation was performed at.
    """
    parts: List[str] = [
        "- {0} readiness re-check ({1}): `- Readiness:` CHANGED `{2}` -> `{3}`.".format(
            date, actor, RECHECK_SOURCE_READINESS, RECHECK_TARGET_READINESS
        ),
        "THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was "
        "re-critiqued.",
        "The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found "
        "clear:",
    ]
    clauses = []
    for cond in result.conditions:
        clauses.append("{0} -> clear ({1})".format(cond.name, cond.reason))
    parts.append("; ".join(clauses) + ".")
    # CITED BY DATE AND FINDING SPAN, NEVER QUOTED. A review record states its own verdict in its
    # message, so quoting it would import a verdict token and make `newest_verdict` read THIS entry as
    # the newest review. See `cite_review_entry`.
    citation = cite_review_entry(reviewed_entry)
    if citation:
        parts.append("RE-CHECKED REVIEW: {0}.".format(citation))
    if head:
        parts.append("Recomputed at HEAD `{0}`.".format(head))
    parts.append(
        "HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `{0}` means the plan awaits sign-off, "
        "and nothing here approves it or clears it to execute. Only a review may set `go`.".format(
            RECHECK_TARGET_READINESS
        )
    )
    return " ".join(parts)


def recheck_readiness(
    repo_root,
    plan_path,
    *,
    apply: bool = False,
    date: str,
    actor: str,
    head: str = "",
) -> Tuple[RecheckResult, Optional[str]]:
    """Recompute, and when permitted rewrite `no-go` -> `go-pending-approval` WITH its evidence.

    Returns ``(result, new_text)``. ``new_text`` is the amended plan text when a write is PERMITTED
    (whether or not ``apply`` wrote it, so a dry run can diff), and ``None`` when it is refused.

    THE WRITE TARGET IS PINNED, not merely documented. The value written is
    :data:`RECHECK_TARGET_READINESS` unconditionally: there is no parameter, no branch, and no caller
    input that can change it, so `go` is unreachable through this function by construction rather than
    by discipline. That matters because the field is read FIRST by the auto-approve predicate, making a
    silent widening the highest-consequence regression this area could carry.

    AN ASSERTION GUARDS THE ENTRY TOO, because the history record is the other half of the
    attestation: if the rendered entry ever contained a review verdict token, :func:`newest_verdict`
    would read this re-check as a review. That is checked here rather than trusted.
    """
    path = Path(plan_path)
    result = recheck_conditions(repo_root, path)
    if not result.may_write:
        return result, None

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:  # pragma: no cover - recheck_conditions already read it
        return result, None

    _, reviewed_entry = newest_verdict(text)
    entry = format_recheck_history_entry(
        result, date=date, actor=actor, reviewed_entry=reviewed_entry, head=head
    )
    # GUARD THE ENTRY, NOT JUST THE FIELD, because the history record is the other half of the
    # attestation: an entry `newest_verdict` could read as a review would forge the very verdict this
    # design refuses to write.
    #
    # THE GUARD USES THE CONSUMER'S OWN SCANNERS, NOT A SUBSTRING SEARCH, and that distinction is
    # measured rather than stylistic. A naive `"APPROVE" in entry.upper()` matched the word
    # "approves" inside this entry's own closing sentence ("nothing here approves it"), which is not a
    # verdict token at all: `_VERDICT_SCAN_RE` is word-bounded, so the consumer would never have read
    # it as one. Guarding on a stricter rule than the consumer applies produces false alarms on
    # correct output, which is how a guard gets deleted.
    assert classify_verdict(entry) == (None, None), (
        "a re-check history entry must state no /plan-review verdict token; `classify_verdict` read "
        + repr(classify_verdict(entry)[0])
    )
    assert not is_review_history_entry(entry), (
        "a re-check history entry must not be classified as a REVIEW record; its status/workflow "
        "middle must remain `readiness re-check`"
    )

    new_text, n = _READINESS_LINE_SUB_RE.subn(
        "- Readiness: " + RECHECK_TARGET_READINESS, text, count=1
    )
    if n != 1:  # pragma: no cover - the field was proven present by recheck_conditions
        return result, None
    # Guard the WRITE TARGET. Re-read the amended text through the same reader every consumer uses,
    # so the assertion tests the OBSERVABLE value rather than the string we intended to write.
    written = _schema.read_readiness(new_text)
    assert (
        written == RECHECK_TARGET_READINESS
    ), "the re-check may write ONLY {0}; refusing to write {1!r}".format(
        RECHECK_TARGET_READINESS, written
    )

    new_text = _prepend_history_entry(new_text, entry)
    if apply:
        path.write_text(new_text, encoding="utf-8")
    return result, new_text


_READINESS_LINE_SUB_RE = re.compile(r"(?m)^-[ \t]*Readiness:[ \t]*.*$")


def _prepend_history_entry(text: str, entry: str) -> str:
    """Insert ``entry`` as the NEWEST record directly under ``## Workflow history``.

    NEWEST-FIRST, matching `aw set`'s own writer (`status_set.py`, ``new_lines.insert(i + 1, ...)``)
    and therefore matching what :func:`extract_newest_history_entry` reads. Appending instead would
    make the newest record unreadable by every consumer in this module.

    When the section is absent the entry is placed after the front matter, before the first ``## ``
    heading, so the file stays conformant rather than growing a trailing orphan section.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "## Workflow history":
            insert_at = i + 1
            # Keep the customary blank line directly under the heading intact.
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            lines.insert(insert_at, entry)
            return "\n".join(lines)
    for i, line in enumerate(lines):
        if line.startswith("## "):
            lines[i:i] = ["## Workflow history", "", entry, ""]
            return "\n".join(lines)
    return "\n".join(lines + ["", "## Workflow history", "", entry, ""])
