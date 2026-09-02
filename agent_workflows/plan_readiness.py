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
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from agent_workflows import ipd_schema as _schema
from agent_workflows.attention import _history_section_lines
from agent_workflows.attention_contract import HISTORY_RECORD_RE

__all__ = [
    "extract_newest_history_entry",
    "history_verdict_approves",
    "has_unresolved_blocking_question",
    "is_plan_review_approved",
]

# The review verdicts that CLEAR a plan, from `/plan-review`'s closed verdict vocabulary
# (`.aw/system/workflows/plan-review/plan-review.md`: APPROVE, APPROVE WITH REVISIONS APPLIED,
# REVIEWED - OPEN QUESTIONS, REJECT - NEEDS REPLAN). Only the first two clear. Anchored to the
# verdict's position after the workflow/actor prefix rather than matched anywhere in the line, so a
# record NARRATING some other plan's verdict is far less likely to be misread as its own.
_VERDICT_APPROVE_RE = re.compile(
    r"\bAPPROVE(?:\s+WITH\s+REVISIONS\s+APPLIED)?\b", re.IGNORECASE
)
# Negative readiness tokens that VETO the fallback even when a verdict word is present. `NO-GO` and
# `CONDITIONAL-GO` are the workflow's own not-ready vocabulary; the shipped gate already looked for
# exactly these two, and that behavior is preserved deliberately.
_NEGATIVE_READINESS_RE = re.compile(r"\b(?:NO-GO|CONDITIONAL-GO)\b", re.IGNORECASE)
# The other two verdicts. Present explicitly so a record that states BOTH (e.g. "REVIEWED - OPEN
# QUESTIONS ... will be APPROVE once decided") is refused rather than accepted on the stray word.
_VERDICT_NEGATIVE_RE = re.compile(
    r"\b(?:REVIEWED\s*-\s*OPEN\s+QUESTIONS|REJECT\s*-\s*NEEDS\s+REPLAN)\b",
    re.IGNORECASE,
)

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
    (``NO-GO`` / ``CONDITIONAL-GO``) and no competing negative verdict. Fails closed on None.
    """
    if not entry:
        return False
    if _NEGATIVE_READINESS_RE.search(entry):
        return False
    if _VERDICT_NEGATIVE_RE.search(entry):
        return False
    return bool(_VERDICT_APPROVE_RE.search(entry))


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
