"""Exact no-stop classifier for the IPD Set coordinator (execset Order 02, `3m4e54` E-02).

A PURE decision function implementing the human's two-condition stop rule. Given one runtime
question's situation, it decides, in strict order:

  1. If a robust autonomous decision exists -> DECIDE and record it (no stop).
  2. Else if the affected SUBGRAPH can be safely deferred -> defer the subgraph (no stop).
  3. Else if the whole IPD can be safely deferred -> defer the IPD (no stop).
  4. Else -> drain every independent frontier node first, and ONLY THEN emit hard_stop_needs_input.

The hard-stop predicate is exactly the four-clause conjunction from the approved plan:

    hard_stop = needs_human AND no_robust_decision AND cannot_defer_subgraph AND cannot_defer_ipd

An unresolved ``unknown_outcome`` (an interrupted lane whose terminal state is unknown) is NOT a
question for the human: it is routed through deterministic reconciliation and then re-run through
this same predicate, so a crash never silently becomes a stop.

Legacy child ``STOP and report`` instructions are LEXICALLY CONTAINED: this module recognises the
literal text and marks it as child-scoped (returns control to the Set coordinator) rather than
terminating the whole Set.

Pure + stdlib-only. No filesystem, model, or network side effects.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Sequence, Tuple

# Classifier outcomes (what the coordinator should DO with a raised question).
ACTION_DECIDE = "decide_autonomously"
ACTION_DEFER_SUBGRAPH = "defer_subgraph"
ACTION_DEFER_IPD = "defer_ipd"
ACTION_DRAIN_THEN_STOP = "drain_frontier_then_hard_stop"
ACTION_HARD_STOP = "hard_stop_needs_input"
ACTION_RECONCILE_UNKNOWN = "reconcile_unknown_outcome"

ALL_ACTIONS: frozenset = frozenset(
    (
        ACTION_DECIDE,
        ACTION_DEFER_SUBGRAPH,
        ACTION_DEFER_IPD,
        ACTION_DRAIN_THEN_STOP,
        ACTION_HARD_STOP,
        ACTION_RECONCILE_UNKNOWN,
    )
)


class QuestionSituation(NamedTuple):
    """The inputs the classifier needs to decide what to do with one raised question.

    All fields are deterministic facts the coordinator already knows; nothing here consults a model.
    """

    needs_human: (
        bool  # input is materially required (e.g. release approval, credentials, tone)
    )
    has_robust_decision: (
        bool  # a reversible, testable, repository-established default exists
    )
    can_defer_subgraph: (
        bool  # the affected subgraph can be skipped without blocking independents
    )
    can_defer_ipd: bool  # the whole IPD can be safely deferred
    independent_frontier: Tuple[
        str, ...
    ] = ()  # runnable nodes NOT blocked by this question
    is_unknown_outcome: bool = (
        False  # an interrupted lane awaiting reconciliation, not a question
    )


class ClassifierResult(NamedTuple):
    action: str
    hard_stop: bool
    reason: str
    # The frontier that must be drained BEFORE any hard stop (empty unless action drains-then-stops).
    drain_first: Tuple[str, ...] = ()


def hard_stop_predicate(
    *,
    needs_human: bool,
    no_robust_decision: bool,
    cannot_defer_subgraph: bool,
    cannot_defer_ipd: bool,
) -> bool:
    """The EXACT four-clause conjunction. True only when all four clauses hold simultaneously."""
    return bool(
        needs_human
        and no_robust_decision
        and cannot_defer_subgraph
        and cannot_defer_ipd
    )


def classify(situation: QuestionSituation) -> ClassifierResult:
    """Decide what to do with one raised question. Pure; deterministic; never stops prematurely.

    An ``unknown_outcome`` short-circuits to reconciliation (it is not a human question). Otherwise
    the ordered ladder decide -> defer-subgraph -> defer-ipd -> (drain then) hard-stop is applied,
    and ``hard_stop`` is set iff the exact four-clause predicate holds.
    """
    if situation.is_unknown_outcome:
        return ClassifierResult(
            action=ACTION_RECONCILE_UNKNOWN,
            hard_stop=False,
            reason="Unknown outcome is routed through deterministic reconciliation, not a human stop.",
        )

    # 1. A robust default beats a prompt.
    if situation.has_robust_decision:
        return ClassifierResult(
            action=ACTION_DECIDE,
            hard_stop=False,
            reason="A robust, reversible, testable decision exists; decide and record it.",
        )

    # If input is not materially required, a non-robust choice still does not stop the Set: the
    # coordinator proceeds with the least-disruptive default (recorded as an autonomous decision).
    if not situation.needs_human:
        return ClassifierResult(
            action=ACTION_DECIDE,
            hard_stop=False,
            reason="Human input is not materially required; proceed with the least-disruptive default.",
        )

    # 2. Defer the affected subgraph if independent work continues.
    if situation.can_defer_subgraph:
        return ClassifierResult(
            action=ACTION_DEFER_SUBGRAPH,
            hard_stop=False,
            reason="The affected subgraph can be deferred; independent siblings continue.",
        )

    # 3. Defer the whole IPD.
    if situation.can_defer_ipd:
        return ClassifierResult(
            action=ACTION_DEFER_IPD,
            hard_stop=False,
            reason="The IPD can be safely deferred; the Set continues other dependency-valid work.",
        )

    # 4. The four-clause predicate now holds. Drain the independent frontier FIRST, then stop.
    stop = hard_stop_predicate(
        needs_human=situation.needs_human,
        no_robust_decision=not situation.has_robust_decision,
        cannot_defer_subgraph=not situation.can_defer_subgraph,
        cannot_defer_ipd=not situation.can_defer_ipd,
    )
    # By construction stop is True here, but compute it explicitly so the predicate is the authority.
    if stop and situation.independent_frontier:
        return ClassifierResult(
            action=ACTION_DRAIN_THEN_STOP,
            hard_stop=True,
            reason="Four-clause hard_stop holds; drain the independent frontier before stopping.",
            drain_first=tuple(situation.independent_frontier),
        )
    if stop:
        return ClassifierResult(
            action=ACTION_HARD_STOP,
            hard_stop=True,
            reason="Four-clause hard_stop holds and no independent frontier remains; stop for input.",
        )
    # Defensive fallback (unreachable given the ladder above): never stop without the predicate.
    return ClassifierResult(
        action=ACTION_DECIDE,
        hard_stop=False,
        reason="No hard-stop condition met; proceed with the least-disruptive default.",
    )


# ---- Lexical containment of legacy child STOP-and-report instructions ----------------------------

# The literal instruction that exists on shared/always-loaded surfaces today. Recognised so a
# CHILD's "STOP and report" returns control to the Set coordinator instead of terminating the Set.
_STOP_AND_REPORT_RE = re.compile(r"\bSTOP\s+and\s+report\b", re.IGNORECASE)


class StopContainment(NamedTuple):
    is_stop_instruction: bool
    scope: str  # "child" (return control to coordinator) or "none"
    reason: str


def contain_child_stop(instruction_text: str) -> StopContainment:
    """Lexically detect a legacy child ``STOP and report`` instruction and mark it CHILD-scoped.

    A child-scoped stop returns control to the Set coordinator; it does NOT terminate the whole Set.
    Single-IPD (non-Set) execution is unaffected: the coordinator simply is the single run.
    """
    if _STOP_AND_REPORT_RE.search(instruction_text or ""):
        return StopContainment(
            is_stop_instruction=True,
            scope="child",
            reason="Legacy 'STOP and report' is child-scoped: return control to the Set coordinator.",
        )
    return StopContainment(
        is_stop_instruction=False,
        scope="none",
        reason="No STOP-and-report instruction present.",
    )


def frontier_after_drain(
    frontier: Sequence[str], drained: Sequence[str]
) -> Tuple[str, ...]:
    """Deterministic helper: the frontier remaining after draining ``drained`` (sorted, stable)."""
    remaining = [n for n in frontier if n not in set(drained)]
    return tuple(sorted(remaining))
