"""Set lifecycle + recovery driving for the coordinator (execset Order 03, `m2wwns` E-03).

Drives the truthful lifecycle over the run ledger + `run_recovery`, WITHOUT forking either:

  * integration-triggered evidence invalidation (net-new WIRING of a reused primitive): after an
    integration advances the combined HEAD, evidence bound to the now-stale HEAD is invalidated by
    appending a `correction` record carrying `invalidates_seq` (the exact idiom `run_recovery` uses;
    no parallel invalidation kind is introduced). Invalidated evidence can no longer satisfy a later
    terminal transition.
  * combined-HEAD validation gate: a terminal transition is permitted ONLY after the integrated HEAD
    re-passes validation; a per-lane-green-but-combined-red result fails closed.
  * partial outcomes: a deferred required node keeps its IPD pending (never marked executed) and
    derives a `set_partial` Set state.
  * resume: delegates to `run_recovery.resume`/`recover_crash`, which fail closed on unknown outcomes
    rather than replaying completed side effects.

Pure orchestration logic over the reused engine/recovery/state primitives; no model or network side
effects. The heavy lifting (merge, revalidation, ledger append, state reconstruction) lives in the
already-executed modules; this module only sequences and gates them.
"""

from __future__ import annotations

from typing import List, Mapping, NamedTuple, Sequence, Tuple

from agent_workflows import set_state as _ss


# ---- integration-triggered evidence invalidation -------------------------------------------------


def stale_evidence_seqs_after_integration(
    records: Sequence[Mapping],
    *,
    new_head: str,
) -> Tuple[int, ...]:
    """Ledger seqs of evidence envelopes bound to a HEAD other than ``new_head`` (now stale).

    After an integration advances the combined HEAD, any evidence_envelope whose `head` differs from
    the integrated HEAD is stale and must be invalidated before it can satisfy a terminal transition.
    Already-invalidated seqs (named by a prior `correction.invalidates_seq`) are excluded.
    """
    already: set = set()
    for r in records:
        if (
            r.get("kind") == "correction"
            and isinstance(r.get("invalidates_seq"), int)
            and not isinstance(r.get("invalidates_seq"), bool)
        ):
            already.add(r["invalidates_seq"])
    out: List[int] = []
    for r in records:
        if r.get("kind") != "evidence_envelope":
            continue
        seq = r.get("seq")
        head = r.get("head")
        if not isinstance(seq, int) or isinstance(seq, bool):
            continue
        if seq in already:
            continue
        if head not in (new_head, "", None, "unversioned"):
            out.append(seq)
    return tuple(sorted(out))


def make_invalidation_records(
    records: Sequence[Mapping],
    *,
    run_id: str,
    new_head: str,
    corrects_requirement: str = "integration",
    actor: str = "coordinator",
    timestamp: str = "",
) -> Tuple[dict, ...]:
    """Build one `correction` record per stale evidence seq (reusing the `invalidates_seq` idiom).

    The caller appends these to the ledger after an integration; they mark the stale-HEAD evidence
    invalidated so it cannot satisfy a later terminal transition. Returns () when nothing is stale.
    """
    stale = stale_evidence_seqs_after_integration(records, new_head=new_head)
    out: List[dict] = []
    for seq in stale:
        out.append(
            {
                "schema_version": 2,
                "kind": "correction",
                "run_id": run_id,
                "actor": actor,
                "timestamp": timestamp,
                "parent": "",
                "corrects_requirement": corrects_requirement,
                "description": "evidence seq {0} invalidated: bound to a pre-integration HEAD".format(
                    seq
                ),
                "invalidates_seq": seq,
            }
        )
    return tuple(out)


# ---- combined-HEAD validation gate ---------------------------------------------------------------


class TerminalGateResult(NamedTuple):
    allowed: bool
    reason: str


def terminal_transition_allowed(
    *,
    integration_passed: bool,
    combined_head_revalidated: bool,
    unresolved_required_nodes: Sequence[str],
    all_required_verified_terminal: bool,
) -> TerminalGateResult:
    """Gate a Set terminal transition. Permitted ONLY when integration passed, the combined HEAD
    re-passed validation, no required node is unresolved, and every required child is verified
    terminal. Fails closed otherwise (a per-lane-green-but-combined-red run is refused)."""
    if not integration_passed:
        return TerminalGateResult(False, "integration did not pass")
    if not combined_head_revalidated:
        return TerminalGateResult(
            False, "combined HEAD failed revalidation (per-lane green is not enough)"
        )
    if unresolved_required_nodes:
        return TerminalGateResult(
            False,
            "unresolved required nodes remain: {0}".format(
                sorted(unresolved_required_nodes)
            ),
        )
    if not all_required_verified_terminal:
        return TerminalGateResult(
            False, "not every required child reached verified terminal lifecycle"
        )
    return TerminalGateResult(True, "all terminal preconditions satisfied")


# ---- lane-outcome aggregation + Set-state derivation ---------------------------------------------


class SetProgress(NamedTuple):
    """The aggregate progress the coordinator derives from lane outcomes + questions."""

    set_state: str
    unresolved_required: Tuple[str, ...]
    deferred: Tuple[str, ...]


def derive_progress(
    *,
    required_nodes: Sequence[str],
    verified_terminal_nodes: Sequence[str],
    deferred_nodes: Sequence[str],
    waiting_on_human: bool,
    unrecoverable: bool,
    started: bool = True,
    cancelled: bool = False,
) -> SetProgress:
    """Derive the Set state + the unresolved-required set from lane progress.

    A required node is unresolved if it is neither verified-terminal nor a resolved deferral. The
    Set state is derived via `set_state.derive_set_state` (set_complete only when all required nodes
    verified-terminal and none deferred; set_partial when any required node is deferred)."""
    req = list(required_nodes)
    verified = set(verified_terminal_nodes)
    deferred = set(deferred_nodes)
    unresolved = tuple(
        sorted(n for n in req if n not in verified and n not in deferred)
    )
    any_deferred = any(n in deferred for n in req)
    all_verified = all(n in verified for n in req) and bool(req)
    state = _ss.derive_set_state(
        started=started,
        any_required_deferred=any_deferred,
        all_required_verified_terminal=all_verified,
        waiting_on_human=waiting_on_human,
        unrecoverable=unrecoverable,
        cancelled=cancelled,
    )
    return SetProgress(
        set_state=state,
        unresolved_required=unresolved,
        deferred=tuple(sorted(deferred & set(req))),
    )


# ---- resume (delegates to run_recovery; fails closed on unknown outcomes) -------------------------


def resume_or_report(engine) -> Tuple[bool, object]:
    """Attempt to resume via `run_recovery.resume`. Returns (ok, report_or_error).

    On an unknown outcome, `run_recovery.resume` raises `UnknownOutcomeError` (fail-closed, no
    replay); we surface it rather than advancing, so the coordinator reconciles first. This is a thin
    seam so tests and the CLI can resume without duplicating the recovery contract."""
    from agent_workflows import run_recovery

    try:
        report = run_recovery.resume(engine)
        return True, report
    except run_recovery.UnknownOutcomeError as exc:
        return False, exc
