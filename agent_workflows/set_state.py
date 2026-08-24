"""Set-level coordination state machine (execset Order 02, `3m4e54` E-01).

A SEPARATE, closed state machine for a coordinator that runs a whole IPD Set, deliberately kept
distinct from ``run_state.py`` (which models ONE run/step). Per the approved OQ-02 (human decision):

  (a) The Set-state tokens are ``set_``-prefixed so they never collide with ``run_state``'s bare
      ``running|complete|failed|cancelled``.
  (b) Each Set state DERIVES from its children's run states: a Set is ``set_complete`` ONLY when
      every required child run reached verified terminal lifecycle, and ``set_partial`` when any
      required node is deferred.

The coordinator ALONE holds authority over Set-state transitions (coordinator/runtime only; the
human role authorizes cancellation). The Set can only reach ``set_complete`` when there is no
unresolved required node; a completion attempt with any unresolved required node is REFUSED.

Pure + stdlib-only. No filesystem, model, or network side effects: this module only DEFINES and
VALIDATES Set-state shapes and transitions. Mirrors the shape of ``run_state.py`` (TransitionRule,
validate_transition, check_transition) so callers use a familiar API.
"""

from __future__ import annotations

from typing import Mapping, NamedTuple, Optional

# ---- Set states (all `set_`-prefixed to disambiguate from run_state, per OQ-02) ------------------

SET_PLANNED: str = "set_planned"
SET_RUNNING: str = "set_running"
SET_WAITING_INPUT: str = "set_waiting_input"
SET_PARTIAL: str = "set_partial"
SET_COMPLETE: str = "set_complete"
SET_FAILED: str = "set_failed"
SET_CANCELLED: str = "set_cancelled"

ALL_SET_STATES: frozenset = frozenset(
    (
        SET_PLANNED,
        SET_RUNNING,
        SET_WAITING_INPUT,
        SET_PARTIAL,
        SET_COMPLETE,
        SET_FAILED,
        SET_CANCELLED,
    )
)

# Active (non-terminal) Set states.
ACTIVE_SET_STATES: frozenset = frozenset(
    (SET_PLANNED, SET_RUNNING, SET_WAITING_INPUT, SET_PARTIAL)
)

# Terminal Set states (no outgoing edge except identity).
TERMINAL_SET_STATES: frozenset = frozenset((SET_COMPLETE, SET_FAILED, SET_CANCELLED))

# Actor roles (mirrors run_ledger_schema.ROLES, including the reconciled `investigator`).
ROLES: frozenset = frozenset(
    (
        "coordinator",
        "executor",
        "investigator",
        "verifier",
        "corrector",
        "human",
        "runtime",
    )
)


# ---- Transition rules and table ------------------------------------------------------------------


class SetTransitionRule(NamedTuple):
    source: str
    target: str
    authorized_actors: frozenset
    required_predicate: str
    description: str


# The complete legal transition table for the Set coordinator. The coordinator (or runtime) drives
# every transition; the human role additionally authorizes cancellation. `set_complete` is guarded
# by the `all_required_children_verified_terminal` predicate (completion refusal otherwise).
SET_TRANSITION_RULES: tuple = (
    # planned -> running: the Set graph is compiled and the first lane is claimable.
    SetTransitionRule(
        SET_PLANNED,
        SET_RUNNING,
        frozenset(("coordinator", "runtime")),
        "manifest_compiled_and_frontier_nonempty",
        "Set graph compiled; runnable frontier is non-empty.",
    ),
    # running -> waiting_input: the exact four-clause hard_stop predicate fired (needs human).
    SetTransitionRule(
        SET_RUNNING,
        SET_WAITING_INPUT,
        frozenset(("coordinator", "runtime")),
        "hard_stop_needs_input_after_frontier_drained",
        "Independent frontier drained and hard_stop_needs_input is true.",
    ),
    # waiting_input -> running: a human answer arrived; resume the drained frontier.
    SetTransitionRule(
        SET_WAITING_INPUT,
        SET_RUNNING,
        frozenset(("coordinator", "runtime")),
        "human_answer_recorded",
        "A recorded human answer unblocks the waiting Set.",
    ),
    # running -> partial: some required node is deferred; independent work is complete.
    SetTransitionRule(
        SET_RUNNING,
        SET_PARTIAL,
        frozenset(("coordinator", "runtime")),
        "some_required_node_deferred_independent_drained",
        "A required node is deferred and all independent work drained; Set is partial.",
    ),
    # partial -> running: a deferral was resolved (e.g. answered); more work is now runnable.
    SetTransitionRule(
        SET_PARTIAL,
        SET_RUNNING,
        frozenset(("coordinator", "runtime")),
        "deferral_resolved_frontier_nonempty",
        "A previously deferred node became runnable; resume.",
    ),
    # running -> complete: EVERY required child reached verified terminal lifecycle.
    SetTransitionRule(
        SET_RUNNING,
        SET_COMPLETE,
        frozenset(("coordinator", "runtime")),
        "all_required_children_verified_terminal",
        "Every required child run reached verified terminal lifecycle.",
    ),
    # running -> failed: an unrecoverable error (no safe runnable work remains).
    SetTransitionRule(
        SET_RUNNING,
        SET_FAILED,
        frozenset(("coordinator", "runtime")),
        "unrecoverable_error_no_safe_work",
        "Unrecoverable error; no safe runnable work remains.",
    ),
    # partial -> failed: a partial Set hit an unrecoverable error.
    SetTransitionRule(
        SET_PARTIAL,
        SET_FAILED,
        frozenset(("coordinator", "runtime")),
        "unrecoverable_error_no_safe_work",
        "A partial Set hit an unrecoverable error.",
    ),
    # any active -> cancelled: coordinator or human aborts.
    SetTransitionRule(
        SET_PLANNED,
        SET_CANCELLED,
        frozenset(("coordinator", "human")),
        "explicit_cancellation",
        "Set cancelled while planned.",
    ),
    SetTransitionRule(
        SET_RUNNING,
        SET_CANCELLED,
        frozenset(("coordinator", "human")),
        "explicit_cancellation",
        "Set cancelled while running.",
    ),
    SetTransitionRule(
        SET_WAITING_INPUT,
        SET_CANCELLED,
        frozenset(("coordinator", "human")),
        "explicit_cancellation",
        "Set cancelled while waiting for input.",
    ),
    SetTransitionRule(
        SET_PARTIAL,
        SET_CANCELLED,
        frozenset(("coordinator", "human")),
        "explicit_cancellation",
        "Set cancelled while partial.",
    ),
)

_RULE_INDEX: dict = {(r.source, r.target): r for r in SET_TRANSITION_RULES}


def get_set_transition_rule(source: str, target: str) -> Optional[SetTransitionRule]:
    """Return the rule for source->target, or None when the edge is illegal."""
    return _RULE_INDEX.get((source, target))


# ---- Findings, results, exceptions ---------------------------------------------------------------


class SetStateFinding(NamedTuple):
    code: str
    where: str
    message: str
    reason: str


class SetStateValidationResult(NamedTuple):
    ok: bool
    findings: tuple
    rule: Optional[SetTransitionRule] = None


class SetStateError(Exception):
    """Base for Set state machine errors."""


class IllegalSetTransitionError(SetStateError):
    """An illegal Set-state edge (unknown state, terminal escape, or missing edge)."""


class UnauthorizedSetActorError(SetStateError):
    """An actor lacked authority for a Set-state transition."""


class SetCompletionRefusedError(SetStateError):
    """A `set_complete` transition was attempted with an unresolved required node."""


def validate_set_transition(
    source: str,
    target: str,
    actor: str,
    *,
    predicate_values: Optional[Mapping[str, bool]] = None,
) -> SetStateValidationResult:
    """Purely validate whether a Set-state transition is legal, authorized, and predicate-satisfied.

    When ``target`` is ``set_complete`` the ``all_required_children_verified_terminal`` predicate is
    REQUIRED (completion refusal): a completion with any unresolved required node fails closed.
    """
    findings: list = []

    if source not in ALL_SET_STATES:
        findings.append(
            SetStateFinding(
                "SS-UNKNOWN-STATE",
                "source",
                "Unknown source Set state '{0}'".format(source),
                "unknown source state",
            )
        )
    if target not in ALL_SET_STATES:
        findings.append(
            SetStateFinding(
                "SS-UNKNOWN-STATE",
                "target",
                "Unknown target Set state '{0}'".format(target),
                "unknown target state",
            )
        )
    if findings:
        return SetStateValidationResult(False, tuple(findings), None)

    if source in TERMINAL_SET_STATES and target != source:
        return SetStateValidationResult(
            False,
            (
                SetStateFinding(
                    "SS-TERMINAL-STATE",
                    "source",
                    "Cannot transition out of terminal Set state '{0}'".format(source),
                    "terminal state immutable",
                ),
            ),
            None,
        )

    rule = get_set_transition_rule(source, target)
    if rule is None:
        return SetStateValidationResult(
            False,
            (
                SetStateFinding(
                    "SS-ILLEGAL-TRANSITION",
                    "{0}->{1}".format(source, target),
                    "Illegal Set transition from '{0}' to '{1}'".format(source, target),
                    "illegal transition edge",
                ),
            ),
            None,
        )

    if actor not in rule.authorized_actors:
        return SetStateValidationResult(
            False,
            (
                SetStateFinding(
                    "SS-UNAUTHORIZED-ACTOR",
                    "actor",
                    "Actor '{0}' not authorized for Set transition '{1}' -> '{2}' (authorized: {3})".format(
                        actor, source, target, sorted(rule.authorized_actors)
                    ),
                    "unauthorized actor",
                ),
            ),
            rule,
        )

    if predicate_values is not None:
        pred_name = rule.required_predicate
        if not predicate_values.get(pred_name, False):
            code = (
                "SS-COMPLETION-REFUSED"
                if target == SET_COMPLETE
                else "SS-PREDICATE-UNSATISFIED"
            )
            return SetStateValidationResult(
                False,
                (
                    SetStateFinding(
                        code,
                        "predicate",
                        "Required predicate '{0}' is not satisfied for Set transition '{1}' -> '{2}'".format(
                            pred_name, source, target
                        ),
                        "unsatisfied predicate",
                    ),
                ),
                rule,
            )

    return SetStateValidationResult(True, (), rule)


def check_set_transition(
    source: str,
    target: str,
    actor: str,
    *,
    predicate_values: Optional[Mapping[str, bool]] = None,
) -> SetTransitionRule:
    """Validate; raise the specific SetStateError subclass on any violation. Returns the rule on ok."""
    res = validate_set_transition(
        source, target, actor, predicate_values=predicate_values
    )
    if not res.ok:
        for f in res.findings:
            if f.code in (
                "SS-UNKNOWN-STATE",
                "SS-TERMINAL-STATE",
                "SS-ILLEGAL-TRANSITION",
            ):
                raise IllegalSetTransitionError(f.message)
            if f.code == "SS-UNAUTHORIZED-ACTOR":
                raise UnauthorizedSetActorError(f.message)
            if f.code == "SS-COMPLETION-REFUSED":
                raise SetCompletionRefusedError(f.message)
            if f.code == "SS-PREDICATE-UNSATISFIED":
                raise SetStateError(f.message)
        raise IllegalSetTransitionError("Set state transition rejected")
    assert res.rule is not None
    return res.rule


# ---- Derivation: Set state from children run states ---------------------------------------------


def derive_set_state(
    *,
    started: bool,
    any_required_deferred: bool,
    all_required_verified_terminal: bool,
    waiting_on_human: bool,
    unrecoverable: bool,
    cancelled: bool = False,
) -> str:
    """Derive the Set state from the aggregate of its children's run states (OQ-02 (b)).

    Precedence (most terminal first): cancelled -> failed -> complete -> waiting_input -> partial
    -> running -> planned. ``set_complete`` requires EVERY required child verified-terminal;
    ``set_partial`` when any required node is deferred (and no completion).
    """
    if cancelled:
        return SET_CANCELLED
    if unrecoverable:
        return SET_FAILED
    if all_required_verified_terminal and not any_required_deferred:
        return SET_COMPLETE
    if waiting_on_human:
        return SET_WAITING_INPUT
    if any_required_deferred:
        return SET_PARTIAL
    if started:
        return SET_RUNNING
    return SET_PLANNED
