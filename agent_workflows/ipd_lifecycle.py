"""Single-IPD execution lifecycle: the fail-closed `aw ipd begin` execution-start receipt.

IPD ipdgates Order 03 (`xjbvu2`). Before an approved IPD's execution begins, there must be a durable,
independently-inspectable proof that the plan passed the `pre-execution` gate at a known base HEAD,
with its requirements and `Scope-Paths` FROZEN. `aw ipd begin <plan> --actor <agent/model>` produces
that proof: a LOCAL, gitignored receipt under ``.aw/state/ipd-lifecycle/<id6>.receipt.json``.

Fail-closed contract (the whole point): ANY failure mode - a non-conforming `pre-execution` lint
(exit 1) or an unrunnable lint (exit 2), a dirty/ambiguous baseline, a missing/empty ``--actor``, an
unresolvable/duplicate plan selector, or an interrupted write - MUST leave NO valid receipt and
therefore NO execution authority. The receipt is written ATOMICALLY (temp file + ``os.replace``) so an
interrupted write can never leave a partial/valid receipt, and it is RESUMABLE (re-reading returns the
same receipt deterministically).

Receipt binding (OQ-01 resolved): {plan Id, plan content digest, frozen requirement/scope digest,
base HEAD, actor/model, timestamp, frozen ``Scope-Paths``}. LIFETIME (OQ-01, human-resolved): the
receipt PERSISTS across unrelated intervening commits (HEAD movement does NOT invalidate it, so a
concurrent multi-agent workflow on disjoint file sets never needs a needless re-``begin``); it is
invalidated only by (a) a change to the plan's own content digest, or (b) an intervening commit that
touched a path INSIDE this plan's ``Scope-Paths``. This module records the base HEAD + frozen
``Scope-Paths`` that make (b)'s path-overlap collision check possible; ENFORCING that check is Order 04
(`aw ipd finalize`), not here.

Scope fence (Order 03): this module produces ONLY the begin receipt. It does NOT finalize, transition,
or remove any bypass; it does not mutate the plan or any tracked file.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

# Receipt schema version (bump on an incompatible receipt-shape change).
RECEIPT_SCHEMA_VERSION = 1

# Exit-code convention shared with `aw ipd lint` (0 ok / 1 findings / 2 cannot-run).
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CANNOT_RUN = 2

_RECEIPT_SUBDIR = ("state", "ipd-lifecycle")

# --------------------------------------------------------------------------------------
# Finalize transaction journal + lock (Order 3xh53a). Reuses the repository's canonical
# crash-safe pattern from layout_migration.MigrationManager: an exclusive writer lock + an
# atomically-checkpointed transaction journal under the gitignored .aw/state/runtime/ tree, with
# idempotent resume/rollback driven by the persisted phase (never volatile in-memory snapshots).
# --------------------------------------------------------------------------------------

FINALIZE_JOURNAL_SCHEMA_VERSION = 1

# Journal phases (a monotonic-ish enum; ``unknown-outcome`` is a fail-closed terminal-ambiguous
# state). BEFORE the lifecycle commit everything is recoverable to the pre-finalize state; AFTER a
# commit the transaction is either ``committed-incomplete`` (resumable, no history rewrite) or
# ``complete``.
PHASE_PREPARED = "prepared"  # journal written, no mutation yet
PHASE_MUTATING = (
    "mutating"  # plan bytes/status/move/index being written (working-tree only)
)
PHASE_READY_TO_COMMIT = (
    "ready-to-commit"  # all pre-commit mutations staged; about to commit
)
PHASE_COMMITTED_INCOMPLETE = (
    "committed-incomplete"  # lifecycle commit exists; post-lint pending
)
PHASE_UNKNOWN_OUTCOME = (
    "unknown-outcome"  # ambiguous/corrupt evidence; fail closed, never success
)
PHASE_COMPLETE = "complete"  # post-transition passed; receipt + journal finalized

_PRE_COMMIT_PHASES = frozenset((PHASE_PREPARED, PHASE_MUTATING, PHASE_READY_TO_COMMIT))


class TransactionLockError(RuntimeError):
    """Raised when the finalize writer lock is held by another live process."""


class _InjectedFault(RuntimeError):
    """Test-only fault injected at a named finalize checkpoint to exercise rollback/recovery."""


def _runtime_dir(repo_root: Path) -> Path:
    return repo_root.joinpath(".aw", "state", "runtime")


def finalize_lock_path(repo_root: Path) -> Path:
    """The exclusive finalize writer lock over the shared plan manifest."""
    return _runtime_dir(repo_root) / "locks" / "ipd_finalize_writer.lock"


def finalize_journal_path(repo_root: Path, plan_id: str) -> Path:
    """The per-plan finalize transaction journal under the runtime transaction area."""
    return _runtime_dir(repo_root) / "transactions" / f"ipd_finalize_{plan_id}.json"


def _atomic_write_json_at(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def acquire_finalize_lock(repo_root: Path, plan_id: str) -> None:
    """Acquire the exclusive finalize lock, reclaiming a STALE lock (dead PID) after consulting it.

    Raises TransactionLockError with an actionable owner/retry diagnostic when a LIVE process holds
    it. A stale lock (its recorded PID is not alive) is reclaimed rather than blindly deleted.
    """
    lock = finalize_lock_path(repo_root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    if lock.exists():
        try:
            data = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        pid = data.get("pid")
        if pid and pid != os.getpid():
            alive = True
            try:
                os.kill(int(pid), 0)
            except ValueError:
                alive = False
            except PermissionError:
                alive = True  # EPERM: the process EXISTS (owned by another user), so it is alive
            except ProcessLookupError:
                alive = False  # ESRCH: no such process -> stale
            except OSError:
                alive = False
            if alive:
                raise TransactionLockError(
                    "ipd finalize writer lock held by active PID {0} (plan {1}); wait for it to "
                    "finish or, if that process is dead, remove {2}".format(
                        pid, data.get("plan_id"), lock
                    )
                )
        # else: stale (dead PID) - reclaim below (recovery consults the journal, not this file).
    payload = {
        "plan_id": plan_id,
        "pid": os.getpid(),
        "timestamp": _utc_now(),
    }
    _atomic_write_json_at(lock, payload)


def release_finalize_lock(repo_root: Path) -> None:
    """Release the finalize lock iff this process owns it."""
    lock = finalize_lock_path(repo_root)
    if not lock.exists():
        return
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
        if data.get("pid") == os.getpid():
            lock.unlink()
    except (OSError, ValueError):
        try:
            lock.unlink()
        except OSError:
            pass


def read_finalize_journal(repo_root: Path, plan_id: str) -> Optional[Dict[str, Any]]:
    """Load the finalize journal for ``plan_id`` (None if absent/unreadable)."""
    p = finalize_journal_path(repo_root, plan_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_finalize_journal(repo_root: Path, journal: Dict[str, Any]) -> None:
    """Persist the journal atomically, appending the phase to a phase-history trail."""
    journal["updated_at"] = _utc_now()
    _atomic_write_json_at(finalize_journal_path(repo_root, journal["plan_id"]), journal)


def _clear_finalize_journal(repo_root: Path, plan_id: str) -> None:
    p = finalize_journal_path(repo_root, plan_id)
    try:
        p.unlink()
    except OSError:
        pass


def _git_index_entries(repo_root: Path, paths: List[str]) -> Dict[str, str]:
    """The exact staged Git-index entry line (`git ls-files --stage`) for each owned path.

    Captures ``<mode> <object> <stage>\\t<path>`` so rollback can restore precisely the prior index
    state for lifecycle-owned paths without touching any disjoint staged/dirty work.
    """
    out: Dict[str, str] = {}
    if not paths:
        return out
    rc, text, _err = _git(repo_root, ["ls-files", "--stage", "--", *paths])
    if rc != 0:
        return out
    for line in text.splitlines():
        if "\t" in line:
            _meta, p = line.split("\t", 1)
            out[p.strip()] = line
    return out


class BeginResult(NamedTuple):
    """The outcome of an `aw ipd begin` attempt.

    ``exit_code`` follows the shared convention. ``receipt`` is the written receipt dict on success
    (EXIT_OK), else None. ``receipt_path`` is where a receipt was (or would be) written. ``message``
    is a human-readable summary/diagnostic. ``findings`` carries structured lint findings when the
    gate failed.
    """

    exit_code: int
    receipt: Optional[Dict[str, Any]]
    receipt_path: Optional[Path]
    message: str
    findings: Tuple[str, ...] = ()


# --------------------------------------------------------------------------------------
# Pure helpers
# --------------------------------------------------------------------------------------


def _repo_root(start: Path) -> Path:
    """Resolve the git worktree top-level for ``start`` (falls back to ``start`` when not a repo)."""
    from agent_workflows.run_evidence import get_worktree_path

    return Path(get_worktree_path(str(start)))


def receipt_dir(repo_root: Path) -> Path:
    """The gitignored directory that holds begin receipts: ``<repo>/.aw/state/ipd-lifecycle/``."""
    return repo_root.joinpath(".aw", *_RECEIPT_SUBDIR)


def receipt_path_for(repo_root: Path, plan_id: str) -> Path:
    """The receipt path for a plan id6: ``.aw/state/ipd-lifecycle/<id6>.receipt.json``."""
    return receipt_dir(repo_root) / f"{plan_id}.receipt.json"


def plan_content_digest(text: str) -> str:
    """A stable sha256 over the plan's exact bytes (identity of the plan content at begin time)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _requirements_from_plan(text: str) -> Dict[str, List[str]]:
    """Extract the freezable requirement categories from an IPD's parsed structure.

    Maps the IPD's own structure onto the four `run_freeze` categories:
      * ``scope``      = the declared ``Scope-Paths`` entries (or the free-form ``Scope:`` prose when
                          the plan is grandfathered / declares no real allowlist), so the frozen scope
                          fence is bound into the receipt digest;
      * ``must``       = each execution leaf's action text (the E-* items);
      * ``validation`` = each validation leaf's row text (the V-* items).
    An ``output`` category is intentionally omitted (IPDs do not declare it structurally).
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    doc = _lint.parse(text)

    scope: List[str] = []
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if sp_value:
        paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
        if is_grandfathered:
            # Freeze the sentinel plus the free-form Scope: prose so the scope fence is still bound.
            scope.append("grandfathered")
            free_scope = doc.meta_fields.get("Scope")
            if free_scope:
                scope.append(free_scope)
        else:
            scope.extend(paths)
    else:
        free_scope = doc.meta_fields.get("Scope")
        if free_scope:
            scope.append(free_scope)

    must = [lf.text for lf in doc.exec_leaves if lf.kind == "E" and lf.text.strip()]
    validation = [
        lf.text for lf in doc.valid_leaves if lf.kind == "V" and lf.text.strip()
    ]

    requirements: Dict[str, List[str]] = {}
    if scope:
        requirements["scope"] = scope
    if must:
        requirements["must"] = must
    if validation:
        requirements["validation"] = validation
    return requirements


def _frozen_scope_paths(text: str) -> List[str]:
    """The plan's declared ``Scope-Paths`` entries (empty list for a grandfathered/absent value).

    This is the concrete path allowlist Order 04's finalize compares against; for a grandfathered
    plan there is no machine allowlist, so an empty list is recorded (finalize treats that as
    'no declared path fence to reconcile' and relies on the free-form scope in the frozen digest).
    """
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import ipd_lint as _lint

    doc = _lint.parse(text)
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if not sp_value:
        return []
    paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
    if is_grandfathered:
        return []
    return list(paths)


# --------------------------------------------------------------------------------------
# Event-derived lifecycle state (agentadhere Phase 3, IPD wqj1ne E-01).
#
# Findings bu9yij 7.3: a freely-editable `- Status:` is trivially hand-editable, so the lifecycle
# state should be DERIVED from a validated event stream. We build ON the EXISTING history (no
# parallel log, DECISION 16-wqj1ne-D1): for a PLAN the events are its inline `## Workflow history`
# records (record_history owns/defers to them; plans are excluded from the sidecar), for other
# trees they are the sidecar records. The derived status runs ALONGSIDE the authoritative
# `- Status:` read (OQ-01) - it validates/cross-checks, it does not replace the field this phase.
#
# HONEST LIMIT (findings 5.4/7.3): the local event stream is FORGEABLE by a privileged local agent
# (it can rewrite the inline history or the sidecar). This derivation is a consistency + validity
# check, NOT a tamper-proof authority boundary; non-forgeable provenance is the deferred
# external-signing set.

# The logical lifecycle stages (findings 7.3), mapped from the concrete plan status vocabulary.
LIFECYCLE_EVENTS: Tuple[str, ...] = (
    "IPD_CREATED",
    "WORK_STARTED",
    "TEST_EVIDENCE_RECORDED",
    "REVIEWED",
    "FINALIZED",
)

# The canonical plan status RANKS (a status may only advance forward through these ranks; the
# terminal `executed` state closes the sequence). Mirrors the plan status vocabulary used by
# `aw set`/`aw ipd set` and ipd_schema. `approved` and `auto-approved` share a rank (they are two
# ways to reach the ready-to-execute stage, NOT sequential steps), so `approved -> executed` is a
# valid single forward step, not a skip.
_PLAN_STATUS_RANKS: Dict[str, int] = {
    "draft": 0,
    "to-review": 1,
    "reviewed": 2,
    "approved": 3,
    "auto-approved": 3,
    "executed": 4,
}
# The rank-ordered status labels (one representative per rank) for skip-diagnostic messages.
_PLAN_STATUS_ORDER: Tuple[str, ...] = (
    "draft",
    "to-review",
    "reviewed",
    "approved",
    "executed",
)
# Terminal statuses whose transition is AUTHORITATIVE (only `aw ipd finalize` may perform it).
_TERMINAL_STATUSES: FrozenSet[str] = frozenset(("executed",))
# The actor `aw ipd finalize` records for the terminal transition; a terminal transition by any
# other actor path is an UNAUTHORIZED terminal transition (rejected).
_FINALIZE_ACTORS: FrozenSet[str] = frozenset(
    ("aw ipd finalize", "aw finalize", "ipd finalize")
)


class TransitionCheck(NamedTuple):
    """Result of validating one lifecycle transition (E-01)."""

    ok: bool
    reason: str  # "" when ok; else the specific rejection reason


def _status_rank(status: str) -> int:
    """The rank of a plan status, or -1 for an unknown/off-sequence status."""
    return _PLAN_STATUS_RANKS.get(status, -1)


def validate_transition(
    from_status: Optional[str],
    to_status: str,
    *,
    actor: Optional[str] = None,
    tree_id_current: Optional[str] = None,
    tree_id_evidence: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    require_evidence: bool = False,
) -> TransitionCheck:
    """Validate ONE lifecycle transition; return (ok, reason). Rejects (findings 7.3):

    * MISSING PREDECESSOR - a transition that skips a required earlier status (e.g. draft -> executed
      without the intervening reviewed/approved), or a backwards move.
    * STALE TREE ID - the transition cites evidence bound to a tree that is not the current tree.
    * INVALID ACTOR - an empty/malformed actor string.
    * MALFORMED EVIDENCE - ``require_evidence`` is set but the evidence is absent/not a mapping/lacks
      a bound ``git_tree``.
    * UNAUTHORIZED TERMINAL - a terminal (``executed``) transition performed by an actor that is not
      the finalize path.

    This is a pure validity predicate over ALREADY-known facts; it is NOT tamper-proof (the caller's
    inputs are locally forgeable). Order matters: actor and terminal-authority are checked first so
    an unauthorized terminal transition is reported as such rather than as a predecessor gap.
    """
    to_status = (to_status or "").strip()
    from_status = (from_status or "").strip() or None

    # INVALID ACTOR: an empty/whitespace actor is never a valid transition author.
    if actor is not None and not actor.strip():
        return TransitionCheck(False, "invalid actor: empty actor string")

    # UNAUTHORIZED TERMINAL: only the finalize path may perform the terminal transition.
    if to_status in _TERMINAL_STATUSES:
        if actor is not None and actor.strip() not in _FINALIZE_ACTORS:
            return TransitionCheck(
                False,
                f"unauthorized terminal transition to {to_status!r} by actor "
                f"{actor.strip()!r}: only `aw ipd finalize` may perform it",
            )

    # STALE TREE ID: evidence must be bound to the current tree.
    if tree_id_evidence is not None and tree_id_current is not None:
        if tree_id_evidence != tree_id_current:
            return TransitionCheck(
                False,
                f"stale tree id: evidence bound to {tree_id_evidence[:12]!r} but current tree is "
                f"{tree_id_current[:12]!r}",
            )

    # MALFORMED EVIDENCE: when evidence is required, it must be a mapping with a bound git_tree.
    if require_evidence:
        if not isinstance(evidence, dict) or not evidence.get("git_tree"):
            return TransitionCheck(
                False,
                "malformed evidence: missing or non-mapping evidence with no bound git_tree",
            )

    # MISSING PREDECESSOR: the lifecycle only moves FORWARD. A forward move MAY skip an optional
    # intermediate stage (real workflows go `draft -> reviewed` directly when `/plan-review` sets
    # reviewed without a separate `to-review` step), so a forward skip is ALLOWED; only a BACKWARDS
    # move is a missing-predecessor violation. The one exception is the terminal `executed`
    # transition, which additionally REQUIRES a sufficiently-advanced predecessor (at least
    # `reviewed`) so a raw `draft -> executed` jump is caught. An unknown target is off-sequence.
    to_rank = _status_rank(to_status)
    if to_rank < 0:
        return TransitionCheck(False, f"unknown target status {to_status!r}")
    from_rank = _status_rank(from_status) if from_status else -1
    if from_status is None:
        # A first recorded event must start at the sequence head (draft); starting mid-sequence with
        # no predecessor is a missing-predecessor violation.
        if to_rank != 0:
            return TransitionCheck(
                False,
                f"missing predecessor: cannot start the lifecycle at {to_status!r} "
                f"(expected {_PLAN_STATUS_ORDER[0]!r})",
            )
        return TransitionCheck(True, "")
    if to_rank < from_rank:
        return TransitionCheck(
            False,
            f"missing predecessor: backwards transition {from_status!r} -> {to_status!r}",
        )
    # Terminal `executed` requires a sufficiently-advanced predecessor (>= reviewed).
    if to_status in _TERMINAL_STATUSES and from_rank < _PLAN_STATUS_RANKS["reviewed"]:
        return TransitionCheck(
            False,
            f"missing predecessor: terminal transition {from_status!r} -> {to_status!r} "
            f"requires at least 'reviewed'",
        )
    return TransitionCheck(True, "")


# The full plan status vocabulary a history line's leading token may legitimately be (a STATUS
# transition). A history line whose token is NOT one of these is a workflow NOTE (e.g.
# `/plan-review:`, `authored`, `note`, `created`), NOT a status transition, and is IGNORED by the
# event derivation - so annotations never masquerade as (invalid) transitions.
_PLAN_STATUS_VOCAB: FrozenSet[str] = frozenset(
    (
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
        "parked",
    )
)


def _plan_status_events(text: str) -> List[Tuple[str, str, str]]:
    """The plan's STATUS-TRANSITION events as (date, status, actor), OLDEST-first, from its INLINE
    history.

    Reuses ``record_history``'s inline parser (no parallel log). A plan history line
    ``- <date> <status> (<actor>): <msg>`` yields (date, status, actor); the ``workflow`` token in
    that grammar is the new status ONLY when it is a known plan status (``_PLAN_STATUS_VOCAB``). A
    line whose token is a workflow NOTE (``/plan-review``, ``authored``, ``note``, ``created`` with a
    non-status shape, ...) is NOT a transition and is skipped, so annotations never masquerade as
    transitions.
    """
    from agent_workflows import record_history as _rh

    events: List[Tuple[str, str, str]] = []
    for line in _rh._inline_history_records(text):
        date, workflow, actor, _msg = _rh._parse_record_line(line)
        token = (workflow or "").strip()
        if token in _PLAN_STATUS_VOCAB:
            events.append((date, token, actor.strip()))
    # Inline history is stored newest-first; reverse to oldest-first for derivation.
    events.reverse()
    return events


def derive_status_from_events(events: List[Tuple[str, str, str]]) -> Optional[str]:
    """Derive the visible lifecycle status from an OLDEST-first (date, status, actor) event list.

    The derived status is the LAST status in the event stream that lies on the canonical plan-status
    sequence (an off-sequence token such as a `parked`/`superseded` note is ignored for the forward
    derivation). Returns None for an empty/derivation-less stream. This is the DERIVED cross-check of
    the authoritative `- Status:` field; it never mutates anything.
    """
    derived: Optional[str] = None
    for _date, status, _actor in events:
        if _status_rank(status) >= 0:
            derived = status
    return derived


def derive_plan_status(text: str) -> Optional[str]:
    """Convenience: derive a plan's status from its inline history events (E-01)."""
    return derive_status_from_events(_plan_status_events(text))


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write ``payload`` as pretty JSON atomically (temp file in the same dir + ``os.replace``).

    An interrupted write leaves the temp file (cleaned up) and NEVER a partial destination file, so
    a crash mid-write cannot produce a partial/valid receipt.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".receipt-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_receipt(repo_root: Path, plan_id: str) -> Optional[Dict[str, Any]]:
    """Return the stored receipt for ``plan_id`` (or None if absent/unreadable/corrupt)."""
    p = receipt_path_for(repo_root, plan_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def receipt_is_current(receipt: Dict[str, Any], plan_text: str) -> bool:
    """True when ``receipt`` still matches the plan's CURRENT content digest (digest-invalidation).

    A plan-digest change invalidates a prior receipt (OQ-01 rule (a)). The path-overlap collision
    rule (b) is enforced by Order 04's finalize, not here.
    """
    return receipt.get("plan_content_digest") == plan_content_digest(plan_text)


# --------------------------------------------------------------------------------------
# The begin transaction
# --------------------------------------------------------------------------------------


def begin(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    *,
    timestamp: str,
) -> BeginResult:
    """Run the fail-closed pre-execution gate and, on success, write the atomic begin receipt.

    Ordered fail-closed checks (each leaves NO valid receipt on failure):
      1. ``--actor`` is present and non-empty;
      2. the plan file exists and parses to a valid ``- Id:`` id6;
      3. the ``pre-execution`` lint disposition is ``conforming`` (else exit 1; an unrunnable lint or
         internal error is exit 2);
      4. the base HEAD is versioned and unambiguous (an unversioned/absent HEAD is refused);
      5. the plan requirements + ``Scope-Paths`` freeze successfully;
      6. the baseline is clean WITHIN this plan's frozen ``Scope-Paths`` (path-overlap rule,
         ipdgates-03 OQ-01): an uncommitted change to an in-scope path is refused, while disjoint
         uncommitted work elsewhere is IGNORED so a concurrent multi-agent workflow is not thrashed.
         The finalize scope reconciliation remains the enforcement point for the out-of-scope changes
         THIS execution owns (scopeattrib Order 01 aligned it with this same disjoint-unowned rule).
    Only when all pass is the receipt built and written atomically. Steps 5 and 6 are ordered so the
    baseline check can scope itself to the frozen ``Scope-Paths``.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import run_freeze
    from agent_workflows.run_evidence import dirty_within, get_git_head

    # 1. actor required (non-empty).
    if not actor or not actor.strip():
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            None,
            "aw ipd begin requires a non-empty --actor <agent/model> (no execution authority "
            "without an attributed actor).",
        )
    actor = actor.strip()

    # 2. plan file must exist and carry a valid id6.
    if not plan_path.is_file():
        return BeginResult(
            EXIT_CANNOT_RUN, None, None, f"plan file not found: {plan_path}"
        )
    try:
        plan_text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return BeginResult(
            EXIT_CANNOT_RUN, None, None, f"cannot read plan file {plan_path}: {exc}"
        )
    doc = _lint.parse(plan_text)
    plan_id = (doc.meta_fields.get("Id") or "").strip()
    if not plan_id or not _schema._core.is_valid_id6(plan_id):
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            None,
            f"plan {plan_path} has no valid 6-char '- Id:' handle; cannot bind a receipt.",
        )

    rcpt_path = receipt_path_for(repo_root, plan_id)

    # 3. pre-execution gate (invoke the linter; never reimplement it).
    try:
        lint_res = _lint.lint_file(plan_path, checkpoint="pre-execution")
    except Exception as exc:  # unrunnable/internal linter failure = cannot-run.
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            f"pre-execution lint could not run (treated as fail-closed): {exc}",
        )
    if not lint_res.passing:
        finding_lines = tuple(f"{d.code} {d.message}" for d in lint_res.diagnostics)
        return BeginResult(
            EXIT_FINDINGS,
            None,
            rcpt_path,
            f"pre-execution gate did NOT conform ({lint_res.disposition}); no receipt written. "
            "Repair the plan and re-run.",
            findings=finding_lines,
        )

    # 4. unambiguous, versioned base HEAD.
    head = get_git_head(str(repo_root))
    if head == "unversioned":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "cannot capture a base HEAD (not a git repo, or git unavailable); baseline is "
            "ambiguous, refusing to issue a receipt.",
        )

    # 5. freeze requirements + Scope-Paths (BEFORE the baseline check, which scopes to these paths).
    try:
        frozen = run_freeze.freeze_requirements(_requirements_from_plan(plan_text))
    except ValueError as exc:
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            f"cannot freeze the plan's requirements/scope: {exc}",
        )

    # 6. baseline clean WITHIN this plan's frozen Scope-Paths (path-overlap rule, ipdgates-03 OQ-01).
    #    Disjoint uncommitted work elsewhere is intentionally ignored so a concurrent multi-agent
    #    workflow is not thrashed. Finalize's scope reconciliation still catches the out-of-scope
    #    changes THIS EXECUTION made (its commits since the frozen base, plus dirty paths it can be
    #    shown to own); since scopeattrib Order 01 it no longer demands a reason for a disjoint
    #    UNOWNED dirty path, which is exactly the rule applied here, so the two gates now agree.
    scope_paths = _frozen_scope_paths(plan_text)
    in_scope_dirty = dirty_within(str(repo_root), scope_paths, _scope_match)
    if in_scope_dirty == "unversioned":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "cannot read the worktree status (not a git repo, or git unavailable); baseline is "
            "ambiguous, refusing to issue a receipt.",
        )
    if in_scope_dirty != "clean":
        offending = in_scope_dirty.replace("\n", ", ")
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "refusing to begin: uncommitted changes to paths INSIDE this plan's Scope-Paths make "
            f"the frozen base ambiguous: {offending}. Commit or stash these in-scope changes first, "
            "then re-run `aw ipd begin`. (Uncommitted work on paths OUTSIDE this plan's Scope-Paths "
            "is allowed and does not block begin.)",
        )

    receipt: Dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "kind": "ipd_begin_receipt",
        "plan_id": plan_id,
        "plan_path": _repo_relative(repo_root, plan_path),
        "plan_content_digest": plan_content_digest(plan_text),
        "requirement_digest": frozen.requirement_digest,
        "scope_paths": _frozen_scope_paths(plan_text),
        "base_head": head,
        "actor": actor,
        "timestamp": timestamp,
        "pre_execution": {
            "disposition": lint_res.disposition,
            "advisories": [f"{a.code} {a.message}" for a in lint_res.advisories],
        },
    }

    # Atomic write - an interrupted write leaves no valid receipt.
    _atomic_write_json(rcpt_path, receipt)

    return BeginResult(
        EXIT_OK,
        receipt,
        rcpt_path,
        f"begin receipt written for {plan_id} at base {head[:12]} (actor {actor}).",
    )


def _repo_relative(repo_root: Path, path: Path) -> str:
    """Return ``path`` relative to ``repo_root`` (POSIX), or the resolved absolute path if outside."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


# --------------------------------------------------------------------------------------
# The finalize transaction (Order v7e88a): atomic terminal transition + scope comparison
# --------------------------------------------------------------------------------------


class FinalizeResult(NamedTuple):
    """The outcome of an `aw ipd finalize` attempt.

    ``exit_code`` follows the shared 0/1/2 convention. ``commit`` is the lifecycle commit hash on
    success. ``evidence`` carries the captured pre-execution/pre-transition/post-transition gate
    outputs and the scope comparison. ``findings`` lists refusal reasons.
    """

    exit_code: int
    commit: Optional[str]
    message: str
    evidence: Dict[str, Any] = {}
    findings: Tuple[str, ...] = ()


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr).

    Delegates to the single canonical git-subprocess runner in ``git_commit_helper`` (the shared
    "commit-what-I-changed" leaf) so there is exactly one git wrapper across the codebase.
    """
    from .git_commit_helper import _git as _shared_git

    return _shared_git(repo_root, args)


class ChangedPathSources(NamedTuple):
    """The two SOURCES of "paths this execution changed", kept apart by OWNERSHIP EVIDENCE.

    They are not interchangeable, which is why they are no longer collapsed at the point of
    collection (scopeattrib Order 01, lbgzxg E-01):

    * ``committed`` - `git diff --name-only <base>..HEAD`. A commit EXISTS for each of these paths,
      so the change is durably attributable (to *someone*: see the honest bound below).
    * ``working_tree`` - `git status --porcelain` (staged + unstaged + untracked). Carries NO
      author at all. In a SHARED checkout a concurrent agent's dirty file is indistinguishable
      from this execution's own, which is the whole defect scopeattrib Order 01 fixes.

    HONEST BOUND: ``committed`` is attributable to a COMMIT, not to an AGENT. Every agent in a
    shared checkout may commit under one git identity, so this split does NOT let finalize tell a
    co-worker's commit from its own. That residual gap is deliberately out of Order 01's scope
    (backlog `a8eufb`) and is pinned by a characterization test in
    ``tests/test_finalize_scope_ownership.py``.
    """

    committed: Tuple[str, ...]
    working_tree: Tuple[str, ...]

    def union(self) -> List[str]:
        """The sorted union - byte-identical to the pre-split ``_paths_changed_by_this_execution``."""
        return sorted(set(self.committed) | set(self.working_tree))


def _changed_path_sources(repo_root: Path, base_head: str) -> ChangedPathSources:
    """Collect the committed and working-tree change sources SEPARATELY (no union here).

    Asks git for exactly what the pre-split implementation asked for; only the shape of the result
    changes. See :class:`ChangedPathSources` for why the two halves must stay distinguishable.
    """
    committed: set = set()
    rc, out, _err = _git(repo_root, ["diff", "--name-only", f"{base_head}..HEAD"])
    if rc == 0:
        committed.update(ln.strip() for ln in out.splitlines() if ln.strip())
    working_tree: set = set()
    rc, out, _err = _git(repo_root, ["status", "--porcelain"])
    if rc == 0:
        for ln in out.splitlines():
            # porcelain: 'XY <path>' or 'XY <old> -> <new>' for renames.
            body = ln[3:] if len(ln) > 3 else ln.strip()
            if " -> " in body:
                body = body.split(" -> ", 1)[1]
            p = body.strip().strip('"')
            if p:
                working_tree.add(p)
    return ChangedPathSources(tuple(sorted(committed)), tuple(sorted(working_tree)))


def _paths_changed_by_this_execution(repo_root: Path, base_head: str) -> List[str]:
    """Repo-relative paths this execution changed: committed since base + current working tree.

    Union of `git diff --name-only <base>..HEAD` (commits made since the frozen base) and
    `git status --porcelain` (staged + unstaged + untracked working-tree changes). This is the set
    of paths the CURRENT worktree presents relative to the frozen base - i.e. what THIS execution
    produced (unrelated concurrent commits on disjoint paths are handled by the intervening-commit
    collision check, not here).

    Kept as the UNION-returning surface so every existing caller (notably
    ``check_engine.check_scope_drift``) is unaffected by the E-01 split. Callers that must
    distinguish the two halves by ownership evidence use :func:`_changed_path_sources` instead.
    """
    return _changed_path_sources(repo_root, base_head).union()


def _intervening_commits_touching(
    repo_root: Path, base_head: str, scope_paths: List[str]
) -> List[str]:
    """Paths inside ``scope_paths`` that an intervening commit (base..HEAD) modified.

    Per OQ-01 rule (b): a commit made SINCE the frozen base that touched a path INSIDE the plan's
    Scope-Paths is a same-file collision (another actor edited this plan's declared territory), which
    finalize must refuse. Returns the offending in-scope paths (empty when none / no allowlist).
    """
    if not scope_paths:
        return []
    rc, out, _err = _git(repo_root, ["diff", "--name-only", f"{base_head}..HEAD"])
    if rc != 0:
        return []
    committed = [ln.strip() for ln in out.splitlines() if ln.strip()]
    hits = [p for p in committed if any(_scope_match(p, pat) for pat in scope_paths)]
    return sorted(set(hits))


def _scope_match(path: str, pattern: str) -> bool:
    """fnmatch a repo-relative path against a Scope-Paths entry (literal, dir-bounded, or glob).

    A trailing-slash directory entry (`tests/`) or a bare directory (`agent_workflows`) matches any
    path beneath it; an entry containing a glob is matched via fnmatch; a literal file matches
    exactly. This mirrors the Scope-Paths grammar (Order oorry1).
    """
    import fnmatch

    p = path.strip().replace("\\", "/")
    pat = pattern.strip().replace("\\", "/")
    if not pat:
        return False
    # Directory-bounded: `dir/` or `dir/**` matches anything under dir/.
    if pat.endswith("/"):
        return p == pat[:-1] or p.startswith(pat)
    if pat.endswith("/**"):
        base = pat[:-3]
        return p == base or p.startswith(base + "/")
    if "*" in pat or "?" in pat or "[" in pat:
        # A dir/* style also should match nested files, so try both fnmatch and prefix.
        if fnmatch.fnmatch(p, pat):
            return True
        # `dir/*.py` should not match nested, but `dir/**/*.py` should; fnmatch handles `**` loosely,
        # so also accept a leading-directory prefix match for `dir/**...`.
        if "**" in pat:
            prefix = pat.split("**", 1)[0].rstrip("/")
            return bool(prefix) and (p == prefix or p.startswith(prefix + "/"))
        return False
    # Literal path: exact match, or a directory prefix (a bare `agent_workflows` covers the tree).
    return p == pat or p.startswith(pat + "/")


def _is_implicitly_allowed(path: str, plan_rel: str) -> bool:
    """True when ``path`` is an implicit lifecycle-artifact allowance (Order oorry1) or the plan file.

    The plan's own file (moving through the lifecycle) and the plans/records index refresh are always
    in scope and need not be declared.
    """
    from agent_workflows import ipd_schema as _schema

    p = path.strip().replace("\\", "/")
    if p == plan_rel:
        return True
    # The plan file's destination (executed/…) and its pending origin both count as the plan itself.
    if p.startswith(".aw/records/plans/") and p.endswith(Path(plan_rel).name):
        return True
    for spec in _schema.scope_paths_implicit_allowances():
        if _scope_match(p, spec):
            return True
    return False


def _working_tree_path_is_owned(
    path: str,
    *,
    scope_paths: List[str],
    committed: Sequence[str],
    plan_rel: str,
) -> bool:
    """Is this WORKING-TREE (uncommitted) path attributable to THIS execution? (Order 01 E-02.)

    A `git status --porcelain` entry carries no author, so ownership has to be inferred from
    positive evidence. This execution OWNS a dirty path when any of the following holds:

    * it matches the plan's frozen ``Scope-Paths`` (the plan declared this territory);
    * it also appears in the COMMITTED half (this execution already committed that path, so the
      dirty entry is a further edit of its own work); or
    * it is an implicit lifecycle allowance (the plan file, the plans index).

    A dirty path matching NONE of those is UNOWNED: in a shared checkout it is almost certainly a
    concurrent agent's in-flight work, and demanding a ``--scope-reason`` for it would force this
    plan to either write a false claim into its permanent record or block on a condition it does
    not control. Note this only ever REMOVES paths from the out-of-scope set; it never adds any.

    ACCEPTED COST (Order 01 OQ-01/F3): an executor's OWN uncommitted out-of-scope edit is
    byte-identical to a co-worker's here, so it is disregarded too. The mitigation is the execution
    contract's path-scoped commits, which put the executor's real work in the COMMITTED half, where
    the reason requirement still fires. Disregarded paths are recorded in the evidence and surfaced
    in the human message rather than silently dropped.
    """
    if _is_implicitly_allowed(path, plan_rel):
        return True
    if path in set(committed):
        return True
    return any(_scope_match(path, pat) for pat in scope_paths)


def finalize_precheck(
    repo_root: Path, plan_path: Path
) -> Tuple[int, str, Dict[str, Any], Tuple[str, ...]]:
    """E-01: validate the begin receipt + pre-transition lint + scope comparison. No mutation.

    Returns ``(exit_code, message, evidence, findings)``. exit_code 0 means the precheck PASSED and
    the forward transition may proceed; 1 means a refusal (findings explain it); 2 means cannot-run.
    Leaves the plan unmoved in every case.
    """
    from agent_workflows import ipd_lint as _lint

    evidence: Dict[str, Any] = {}

    plan_text = plan_path.read_text(encoding="utf-8")
    doc = _lint.parse(plan_text)
    plan_id = (doc.meta_fields.get("Id") or "").strip()
    if not plan_id:
        return EXIT_CANNOT_RUN, f"plan {plan_path} has no '- Id:' handle.", evidence, ()

    # 1. matching begin receipt must exist and still match the plan digest.
    receipt = read_receipt(repo_root, plan_id)
    if receipt is None:
        return (
            EXIT_FINDINGS,
            f"no begin receipt for {plan_id}: run `aw ipd begin` first (fail-closed: no receipt = "
            "no execution authority).",
            evidence,
            (f"missing begin receipt at {receipt_path_for(repo_root, plan_id)}",),
        )
    if not receipt_is_current(receipt, plan_text):
        return (
            EXIT_FINDINGS,
            f"the begin receipt for {plan_id} is STALE: the plan content changed since begin; "
            "re-run `aw ipd begin`.",
            evidence,
            ("plan content digest no longer matches the receipt",),
        )
    evidence["pre_execution"] = receipt.get("pre_execution", {})
    base_head = str(receipt.get("base_head") or "").strip()
    if not base_head or base_head == "unversioned":
        return (
            EXIT_CANNOT_RUN,
            f"the begin receipt for {plan_id} has no usable base HEAD; cannot compute a scope delta.",
            evidence,
            (),
        )
    evidence["base_head"] = base_head
    scope_paths: List[str] = list(receipt.get("scope_paths") or [])
    evidence["scope_paths"] = scope_paths

    # 2. pre-transition lint (fail closed).
    try:
        lint_res = _lint.lint_file(plan_path, checkpoint="pre-transition")
    except Exception as exc:
        return (
            EXIT_CANNOT_RUN,
            f"pre-transition lint could not run (fail-closed): {exc}",
            evidence,
            (),
        )
    evidence["pre_transition"] = {
        "disposition": lint_res.disposition,
        "diagnostics": [f"{d.code} {d.message}" for d in lint_res.diagnostics],
    }
    if not lint_res.passing:
        return (
            EXIT_FINDINGS,
            f"pre-transition gate did NOT conform ({lint_res.disposition}); plan left unmoved.",
            evidence,
            tuple(f"{d.code} {d.message}" for d in lint_res.diagnostics),
        )

    # 3. scope comparison against the frozen base + literal Scope-Paths (OQ-01 path-overlap rule).
    plan_rel = _repo_relative(repo_root, plan_path)
    sources = _changed_path_sources(repo_root, base_head)
    changed = sources.union()
    evidence["changed_paths"] = changed

    # (a) OUT-OF-SCOPE paths: paths THIS execution changed that are outside Scope-Paths. Order 04
    #     refused these outright; Order 05 (qmt3yk) turns that into two-way RECONCILIATION - a
    #     recorded per-path REASON legitimizes the edit (proceed), an empty/missing reason refuses.
    #     A grandfathered plan (empty literal allowlist) has NO machine path fence, so there is no
    #     out-of-scope set (Order oorry1: grandfathered = advisory); only implicit lifecycle
    #     allowances + free-form scope apply.
    #
    #     ATTRIBUTE BY OWNERSHIP, NOT BY MERE DIRTINESS (scopeattrib Order 01, lbgzxg E-02). The two
    #     change sources are filtered DIFFERENTLY because they carry different ownership evidence:
    #       * COMMITTED half: treated exactly as before. A path this execution committed outside
    #         Scope-Paths still demands a reason (no weakening whatsoever).
    #       * WORKING-TREE half: an UNOWNED dirty path (see `_working_tree_path_is_owned`) is
    #         DISREGARDED instead of demanding a reason, because in a shared checkout it belongs to a
    #         concurrent agent and this plan can neither honestly justify it nor wait it out.
    #     This is also what makes finalize CONSISTENT with begin, which already ignores disjoint
    #     uncommitted work so a concurrent multi-agent workflow is not thrashed.
    out_of_scope: List[str] = []
    disregarded_unowned: List[str] = []
    if scope_paths:
        committed_set = set(sources.committed)
        for p in changed:
            if _is_implicitly_allowed(p, plan_rel):
                continue
            if any(_scope_match(p, pat) for pat in scope_paths):
                continue
            if p not in committed_set and not _working_tree_path_is_owned(
                p,
                scope_paths=scope_paths,
                committed=sources.committed,
                plan_rel=plan_rel,
            ):
                # Working-tree only AND unowned: not this execution's to justify.
                disregarded_unowned.append(p)
                continue
            out_of_scope.append(p)
    # (b') IN-SCOPE-UNMODIFIED paths (Order 05, the MISSING-work direction): a Scope-Paths entry the
    #      execution did NOT touch. Requires the receipt's LITERAL declared Scope-Paths (Order 03/04).
    #      Acknowledge-and-proceed (a declared-but-unneeded file is normal, not a failure).
    in_scope_unmodified: List[str] = []
    if scope_paths:
        for pat in scope_paths:
            if not any(_scope_match(c, pat) for c in changed):
                in_scope_unmodified.append(pat)
    # (b) intervening-commit COMPUTATION: which in-Scope-Paths paths were touched by a commit since
    #     base. Substrate for Order 06's authorship-aware collision enforcement; COMPUTED + surfaced
    #     here (not a blanket refusal, so the normal single-actor begin->commit->finalize flow works).
    collisions = _intervening_commits_touching(repo_root, base_head, scope_paths)
    collisions = [c for c in collisions if not _is_implicitly_allowed(c, plan_rel)]

    evidence["scope_audit"] = {
        "grandfathered": not scope_paths,
        "in_scope": bool(scope_paths) and not out_of_scope,
        "out_of_scope_paths": list(out_of_scope),
        "in_scope_unmodified": list(in_scope_unmodified),
        "intervening_in_scope_commits": collisions,
        # E-03: what the ownership filter DISREGARDED, kept visible rather than silently dropped.
        # These are uncommitted paths this execution cannot be shown to own (a concurrent agent's
        # in-flight work in a shared checkout). They demand no reason, but they stay on the record.
        "disregarded_unowned_paths": list(disregarded_unowned),
        "committed_paths": list(sources.committed),
        "working_tree_paths": list(sources.working_tree),
    }
    # The precheck itself no longer REFUSES on out-of-scope paths; that decision now belongs to the
    # two-way reconciliation in `finalize` (Order 05), which legitimizes an out-of-scope edit with a
    # recorded reason and refuses only a MISSING reason. The precheck returns EXIT_OK with the
    # computed two-way delta in evidence so `finalize` can reconcile it.
    msg = "precheck passed (receipt valid, pre-transition conforming; scope delta computed)."
    if disregarded_unowned:
        msg += (
            " Disregarded "
            + str(len(disregarded_unowned))
            + " uncommitted path(s) not owned by this execution (no reason required, recorded in "
            "the scope audit): " + ", ".join(disregarded_unowned) + "."
        )
    return (
        EXIT_OK,
        msg,
        evidence,
        (),
    )


def _refresh_plans_index_fail_loud(repo_root: Path) -> None:
    """Refresh the owned plans index FAIL-LOUD (never the status_set swallow).

    Regenerates the index, then verifies freshness via `--check`. Raises RuntimeError on any
    failure so finalize treats a stale/failed index as a TRANSACTION failure, not a silent success.
    """
    import argparse

    from agent_workflows import plans_index as _pidx

    # Regenerate (no swallow: any exception propagates).
    _pidx.run_index(
        argparse.Namespace(
            dir=str(repo_root),
            check=False,
            as_agent=False,
            agent=False,
            json=False,
            no_color=True,
            limit=None,
            quiet=True,
        )
    )
    # Verify it is now fresh.
    rc = _pidx.run_index(
        argparse.Namespace(
            dir=str(repo_root),
            check=True,
            agent=False,
            json=False,
            no_color=True,
            limit=None,
            quiet=True,
        )
    )
    if rc != 0:
        raise RuntimeError(
            "owned plans index refresh did not converge (aw index plans --check nonzero); "
            "finalize fails closed rather than committing a stale index."
        )


class ReconcileOutcome(NamedTuple):
    """The result of the two-way scope reconciliation (Order 05, qmt3yk).

    ``ok`` is True when every out-of-scope path has a recorded reason and every in-scope-unmodified
    path has an acknowledgment (so finalize may proceed). ``reasons``/``acks`` are the collected
    answers to write verbatim into the terminal record. ``missing`` lists the unanswered items when
    ``ok`` is False (headless fail-closed). ``needs_input_command`` is the exact re-invocation to
    supply them.
    """

    ok: bool
    reasons: Dict[str, str]
    acks: Dict[str, str]
    missing_reasons: Tuple[str, ...]
    missing_acks: Tuple[str, ...]
    needs_input_command: str


def _reconcile_scope(
    plan_selector: str,
    actor: str,
    message: str,
    out_of_scope: List[str],
    in_scope_unmodified: List[str],
    *,
    scope_reasons: Optional[Dict[str, str]] = None,
    scope_acks: Optional[Dict[str, str]] = None,
    interactive: bool = False,
    prompt=None,
) -> ReconcileOutcome:
    """Reconcile the two-way scope delta (Order 05 qmt3yk). SURFACES + ATTRIBUTES; does not judge.

    For each OUT-OF-SCOPE changed path a non-empty REASON is required (recorded -> proceed; empty ->
    refuse). For each IN-SCOPE-UNMODIFIED declared path a one-word ACKNOWLEDGMENT is required
    (acknowledge -> proceed). Answers come from the ``--scope-reason``/``--scope-ack`` flag maps
    (headless) or, on a TTY, from ONE batched ``prompt`` callback. A headless run with a non-empty
    delta and MISSING answers is fail-closed (``ok=False``) and names the exact re-invocation.
    """
    reasons: Dict[str, str] = dict(scope_reasons or {})
    acks: Dict[str, str] = dict(scope_acks or {})

    # Clean delta: nothing to reconcile.
    if not out_of_scope and not in_scope_unmodified:
        return ReconcileOutcome(True, {}, {}, (), (), "")

    # Interactive: collect any missing answers via ONE batched prompt (TTY).
    if interactive and prompt is not None:
        collected = prompt(list(out_of_scope), list(in_scope_unmodified))
        # prompt returns ({path: reason}, {path: ack}); empty/None reason means "not given".
        for p, why in (collected.get("reasons") or {}).items():
            if why is not None and str(why).strip():
                reasons[p] = str(why).strip()
        for p, note in (collected.get("acks") or {}).items():
            acks[p] = (
                str(note).strip()
                if note is not None and str(note).strip()
                else "acknowledged"
            )

    missing_reasons = tuple(p for p in out_of_scope if not reasons.get(p, "").strip())
    # An in-scope-unmodified path is acknowledge-and-proceed; a missing ack in headless mode is
    # still surfaced (fail-closed) so the deviation cannot be silently skipped, but any non-empty
    # note (default "not-needed"/"acknowledged") satisfies it.
    missing_acks = tuple(p for p in in_scope_unmodified if p not in acks)

    # Build the exact re-invocation to supply the missing answers headlessly.
    parts = [
        f"aw ipd finalize {plan_selector} --actor {actor!r} --message {message!r} --apply"
    ]
    for p in missing_reasons:
        parts.append(f"--scope-reason {p}=<why-this-out-of-scope-edit-was-needed>")
    for p in missing_acks:
        parts.append(f"--scope-ack {p}[=not-needed]")
    needs_cmd = " ".join(parts)

    ok = not missing_reasons and not missing_acks
    return ReconcileOutcome(ok, reasons, acks, missing_reasons, missing_acks, needs_cmd)


def _reconciliation_history_note(reasons: Dict[str, str], acks: Dict[str, str]) -> str:
    """Render the reconciliation answers as a compact, verbatim note for the terminal record."""
    bits: List[str] = []
    for p in sorted(reasons):
        bits.append(f"out-of-scope {p}: {reasons[p]}")
    for p in sorted(acks):
        bits.append(f"in-scope-unmodified {p}: {acks[p]}")
    if not bits:
        return ""
    return "Scope reconciliation - " + "; ".join(bits)


def _lifecycle_commit_exists(
    repo_root: Path, pre_head: str, plan_id: str
) -> Optional[str]:
    """Return the lifecycle commit hash if HEAD advanced past ``pre_head`` with our commit, else None.

    Observed-state classification (E-03): we identify OUR lifecycle commit by (a) HEAD != pre_head
    and (b) the tip commit's subject carrying the deterministic `lifecycle(<id>): finalize ...`
    marker. This reads repository evidence rather than trusting that the commit subprocess ran.
    """
    rc, head, _err = _git(repo_root, ["rev-parse", "HEAD"])
    if rc != 0:
        return None
    head = head.strip()
    if head == pre_head:
        return None
    rc, subj, _err = _git(repo_root, ["log", "-1", "--format=%s", head])
    if rc == 0 and subj.strip().startswith(f"lifecycle({plan_id})"):
        return head
    # HEAD moved but not via our marker: ambiguous - the caller classifies unknown-outcome.
    return None


def _rollback_precommit(repo_root: Path, journal: Dict[str, Any]) -> Tuple[bool, str]:
    """Idempotent pre-commit rollback driven by the journal (E-02). Returns (ok, message).

    Restores the plan to its original bytes+path, removes the moved destination, restores the exact
    prior Git-index entries for lifecycle-owned paths (never touching disjoint staged/dirty work),
    and regenerates the plans index from the CURRENT corpus. Byte-equality with the snapshot is
    required only when no concurrent plan-state change occurred; an incompatible concurrent change
    is classified `unknown-outcome` and stopped WITHOUT a destructive restore.
    """
    orig_rel = journal["original_path"]
    dest_rel = journal.get("dest_path")
    orig_abs = repo_root / orig_rel
    orig_bytes = journal["original_bytes"]

    # 1. Remove the moved destination (if the move happened) unless a concurrent change altered it.
    if dest_rel and dest_rel != orig_rel:
        dest_abs = repo_root / dest_rel
        if dest_abs.exists():
            # Only remove a destination that matches what THIS transaction wrote (our plan bytes),
            # so we never clobber a concurrent writer that legitimately owns that path.
            try:
                cur = dest_abs.read_text(encoding="utf-8")
            except OSError:
                cur = None
            expected = journal.get("moved_bytes")
            if expected is not None and cur is not None and cur != expected:
                return (
                    False,
                    "unknown-outcome: the finalize destination {0} changed since the checkpoint; "
                    "refusing a destructive restore.".format(dest_rel),
                )
            try:
                dest_abs.unlink()
            except OSError as exc:
                return (False, f"rollback could not remove {dest_rel}: {exc}")

    # 2. Restore the plan's original bytes at its original path (atomic).
    try:
        orig_abs.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=str(orig_abs.parent), prefix=".rb-", suffix=".md"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(orig_bytes)
        os.replace(tmp, str(orig_abs))
    except OSError as exc:
        return (False, f"rollback could not restore {orig_rel}: {exc}")

    # 3. Restore the exact prior Git-index entries for lifecycle-owned paths (no disjoint work).
    owned = journal.get("owned_paths", [])
    prior_index = journal.get("git_index_entries", {})
    for p in owned:
        # Reset the index entry for this owned path to its recorded state without staging others.
        if p in prior_index:
            _git(repo_root, ["restore", "--staged", "--", p])
        else:
            _git(repo_root, ["restore", "--staged", "--", p])

    # 4. Regenerate the plans index deterministically from the CURRENT corpus + verify.
    try:
        _refresh_plans_index_fail_loud(repo_root)
    except Exception as exc:
        return (False, f"rollback index regeneration failed: {exc}")

    return (
        True,
        "pre-commit state restored (plan bytes/path + owned Git-index; index regenerated).",
    )


def finalize(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    message: str,
    *,
    apply: bool = False,
    scope_reasons: Optional[Dict[str, str]] = None,
    scope_acks: Optional[Dict[str, str]] = None,
    interactive: bool = False,
    prompt=None,
    plan_selector: Optional[str] = None,
    fault_injection: Optional[str] = None,
) -> FinalizeResult:
    """The atomic terminal transaction for one IPD (precheck + two-way reconciliation + transition).

    On the happy path (``apply=True``): validate receipt + pre-transition lint + scope-delta
    computation (Order 04); reconcile the two-way scope delta (Order 05: out-of-scope edits need a
    recorded reason, in-scope-unmodified declared paths need an acknowledgment - via ``scope_reasons``
    / ``scope_acks`` or the TTY ``prompt``); then append the attributed history entry (INCLUDING the
    verbatim reconciliation note), set terminal status, move the plan, refresh the owned index
    fail-loud, create the path-scoped lifecycle commit, run post-transition lint, and report the
    commit + three-phase gate evidence. A missing reason/ack fails closed naming the exact
    re-invocation. (Rollback/failure semantics are Order 06.)
    """
    from agent_workflows import status_set as _ss

    evidence: Dict[str, Any] = {}
    if not actor or not actor.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --actor."
        )
    if not message or not message.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --message."
        )
    if not plan_path.is_file():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}"
        )

    # --- Early recovery: a prior interrupted/committed-incomplete transaction (Order 3xh53a). ---
    # Resolve the plan id from whatever path resolved (a committed-incomplete plan lives in
    # executed/, where precheck/begin do not apply), and resume/rollback BEFORE the fresh precheck.
    from agent_workflows import ipd_lint as _lint0

    _early_id = (
        _lint0.parse(plan_path.read_text(encoding="utf-8")).meta_fields.get("Id") or ""
    ).strip()
    if _early_id:
        _early_journal = read_finalize_journal(repo_root, _early_id)
        if _early_journal is not None:
            _phase = _early_journal.get("phase")
            if _phase == PHASE_COMMITTED_INCOMPLETE:
                try:
                    acquire_finalize_lock(repo_root, _early_id)
                except TransactionLockError as exc:
                    return FinalizeResult(EXIT_CANNOT_RUN, None, str(exc), evidence)
                try:
                    return _resume_post_commit(
                        repo_root, _early_journal, _early_id, evidence
                    )
                finally:
                    release_finalize_lock(repo_root)
            if _phase == PHASE_UNKNOWN_OUTCOME:
                return FinalizeResult(
                    EXIT_CANNOT_RUN,
                    None,
                    f"finalize journal for {_early_id} is in unknown-outcome (ambiguous prior "
                    f"attempt); resolve manually and clear "
                    f"{finalize_journal_path(repo_root, _early_id)}.",
                    evidence,
                    tuple(_early_journal.get("findings", ())),
                )
            # pre-commit phases fall through: the plan is still pending, precheck + the transaction's
            # own resume-rollback handle it.

    exit_code, msg, evidence, findings = finalize_precheck(repo_root, plan_path)
    if exit_code != EXIT_OK:
        return FinalizeResult(exit_code, None, msg, evidence, findings)

    # --- Order 05: two-way scope reconciliation (surfaces + attributes both deltas) ---
    audit = evidence.get("scope_audit", {})
    out_of_scope = list(audit.get("out_of_scope_paths", []))
    in_scope_unmodified = list(audit.get("in_scope_unmodified", []))
    reconcile = _reconcile_scope(
        plan_selector or (plan_path.name),
        actor,
        message,
        out_of_scope,
        in_scope_unmodified,
        scope_reasons=scope_reasons,
        scope_acks=scope_acks,
        interactive=interactive,
        prompt=prompt,
    )
    evidence["scope_reconciliation"] = {
        "reasons": reconcile.reasons,
        "acks": reconcile.acks,
        "resolved": reconcile.ok,
    }
    if not reconcile.ok:
        findings_list: List[str] = []
        for p in reconcile.missing_reasons:
            findings_list.append(f"out-of-scope path needs a --scope-reason: {p}")
        for p in reconcile.missing_acks:
            findings_list.append(
                f"declared-but-unmodified path needs a --scope-ack: {p}"
            )
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            "finalize needs scope reconciliation answers (plan left unmoved). Supply them with:\n  "
            + reconcile.needs_input_command,
            evidence,
            tuple(findings_list),
        )

    if not apply:
        return FinalizeResult(
            EXIT_OK,
            None,
            "precheck + reconciliation passed; re-run with --apply to perform the terminal transaction.",
            evidence,
            (),
        )

    # Fold the verbatim reconciliation note into the attributed history message so the deviation is
    # permanently on the record and attributable.
    recon_note = _reconciliation_history_note(reconcile.reasons, reconcile.acks)
    if recon_note:
        message = f"{message} [{recon_note}]"

    # --- E-02/E-03 forward transition, wrapped in the durable two-phase journal (Order 3xh53a) ---
    rec = _ss.read_artifact_record(plan_path, repo_root)
    if rec is None:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"could not read plan record for {plan_path}.",
            evidence,
        )
    plan_id = (rec.id6 or "").strip() or Path(plan_path).name
    plan_rel = _repo_relative(repo_root, plan_path)

    # Acquire the exclusive finalize lock (a live second finalizer fails with a retry diagnostic).
    try:
        acquire_finalize_lock(repo_root, plan_id)
    except TransactionLockError as exc:
        return FinalizeResult(EXIT_CANNOT_RUN, None, str(exc), evidence)

    try:
        return _finalize_transaction(
            repo_root,
            plan_path,
            plan_rel,
            plan_id,
            rec,
            actor,
            message,
            evidence,
            fault_injection,
        )
    finally:
        release_finalize_lock(repo_root)


def _finalize_transaction(
    repo_root: Path,
    plan_path: Path,
    plan_rel: str,
    plan_id: str,
    rec,
    actor: str,
    message: str,
    evidence: Dict[str, Any],
    fault_injection: Optional[str],
) -> FinalizeResult:
    """The journaled two-phase terminal transaction (called under the finalize lock).

    Phases: PREPARED (snapshot) -> MUTATING (status/move/index, working-tree only) ->
    READY_TO_COMMIT -> commit -> classify by OBSERVED state -> post-transition -> COMPLETE. Any
    pre-commit failure/interrupt rolls back idempotently; a committed-incomplete transaction resumes
    via the SAME command with no history rewrite; ambiguous evidence is unknown-outcome (fail closed).
    """
    import argparse

    from agent_workflows import status_set as _ss

    plans_dir = _plans_dir_of(repo_root, plan_path)
    index_json_rel = _repo_relative(repo_root, plans_dir / "INDEX.json")
    index_md_rel = _repo_relative(repo_root, plans_dir / "INDEX.md")
    dest_rel = _repo_relative(repo_root, plans_dir / "executed" / Path(plan_path).name)
    owned_paths = [plan_rel, dest_rel, index_json_rel, index_md_rel]

    def _fault(tag: str) -> None:
        if fault_injection == tag:
            raise _InjectedFault(tag)

    # --- RESUME: an existing journal means a prior attempt was interrupted. ---
    existing = read_finalize_journal(repo_root, plan_id)
    if existing is not None:
        phase = existing.get("phase")
        if phase in _PRE_COMMIT_PHASES:
            # Interrupted before the commit: finish rollback idempotently, then start fresh below.
            ok, msg = _rollback_precommit(repo_root, existing)
            if not ok:
                existing["phase"] = PHASE_UNKNOWN_OUTCOME
                existing["rollback_error"] = msg
                _write_finalize_journal(repo_root, existing)
                return FinalizeResult(
                    EXIT_CANNOT_RUN,
                    None,
                    f"prior interrupted finalize could not be rolled back ({msg}); journal retained "
                    "for recovery. NOT restored.",
                    evidence,
                )
            _clear_finalize_journal(repo_root, plan_id)
            # fall through to a fresh attempt
        elif phase == PHASE_COMMITTED_INCOMPLETE:
            return _resume_post_commit(repo_root, existing, plan_id, evidence)
        elif phase == PHASE_UNKNOWN_OUTCOME:
            return FinalizeResult(
                EXIT_CANNOT_RUN,
                None,
                f"finalize journal for {plan_id} is in unknown-outcome (ambiguous prior attempt); "
                f"resolve manually and clear {finalize_journal_path(repo_root, plan_id)}.",
                evidence,
                tuple(existing.get("findings", ())),
            )
        # PHASE_COMPLETE: a stale complete journal - clear and proceed fresh.
        else:
            _clear_finalize_journal(repo_root, plan_id)

    # --- PREPARED: snapshot everything needed to roll back, atomically, before any mutation. ---
    rc, pre_head, _err = _git(repo_root, ["rev-parse", "HEAD"])
    pre_head = pre_head.strip() if rc == 0 else "unversioned"
    try:
        original_bytes = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"cannot read plan: {exc}", evidence
        )

    def _read_or_none(rel: str) -> Optional[str]:
        p = repo_root / rel
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return None

    journal: Dict[str, Any] = {
        "schema_version": FINALIZE_JOURNAL_SCHEMA_VERSION,
        "plan_id": plan_id,
        "plan_digest": plan_content_digest(original_bytes),
        "original_path": plan_rel,
        "original_bytes": original_bytes,
        "dest_path": dest_rel,
        "pre_head": pre_head,
        "owned_paths": owned_paths,
        "index_json_before": _read_or_none(index_json_rel),
        "index_md_before": _read_or_none(index_md_rel),
        "git_index_entries": _git_index_entries(repo_root, owned_paths),
        "receipt_id": plan_id,
        "actor": actor,
        "message": message,
        "phase": PHASE_PREPARED,
        "created_at": _utc_now(),
    }
    _write_finalize_journal(repo_root, journal)

    def _rollback_and_return(
        reason: str, exit_code: int = EXIT_CANNOT_RUN
    ) -> FinalizeResult:
        cur = read_finalize_journal(repo_root, plan_id) or journal
        ok, msg = _rollback_precommit(repo_root, cur)
        if not ok:
            cur["phase"] = PHASE_UNKNOWN_OUTCOME
            cur["rollback_error"] = msg
            _write_finalize_journal(repo_root, cur)
            return FinalizeResult(
                exit_code,
                None,
                f"{reason}; rollback FAILED ({msg}); journal retained, repository NOT reported "
                "restored.",
                evidence,
            )
        _clear_finalize_journal(repo_root, plan_id)
        return FinalizeResult(
            exit_code, None, f"{reason}; rolled back to pre-finalize state.", evidence
        )

    # --- MUTATING: status write + file move (working-tree only), then owned-index refresh. ---
    journal["phase"] = PHASE_MUTATING
    _write_finalize_journal(repo_root, journal)
    try:
        _fault("before_mutation")
        ns = argparse.Namespace(actor=actor, message=message, by_human=False)
        dest_path, _norm = _ss.apply_status_change(rec, "executed", repo_root, ns)
        # Record the moved bytes so rollback can distinguish our write from a concurrent one.
        try:
            journal["moved_bytes"] = dest_path.read_text(encoding="utf-8")
        except OSError:
            journal["moved_bytes"] = None
        journal["dest_path"] = _repo_relative(repo_root, dest_path)
        _write_finalize_journal(repo_root, journal)
        _fault("after_move")
        _refresh_plans_index_fail_loud(repo_root)
        _fault("after_index")
    except _InjectedFault as exc:
        return _rollback_and_return(f"fault-injected finalize failure ({exc})")
    except Exception as exc:
        return _rollback_and_return(f"finalize mutation failed ({exc})")

    dest_path = repo_root / journal["dest_path"]

    # --- READY_TO_COMMIT: stage only owned paths, then the single lifecycle commit. ---
    stage = [p for p in owned_paths if (repo_root / p).exists() or p == plan_rel]
    rc, _out, err = _git(repo_root, ["add", "--", *stage])
    if rc != 0:
        return _rollback_and_return(f"git add failed ({err.strip()})")
    journal["phase"] = PHASE_READY_TO_COMMIT
    journal["staged"] = stage
    _write_finalize_journal(repo_root, journal)

    try:
        _fault("before_commit")
    except _InjectedFault as exc:
        return _rollback_and_return(f"fault-injected before commit ({exc})")

    commit_msg = (
        f"lifecycle({plan_id}): finalize {plan_id} -> executed\n\n{message}\n\n"
        f"Executed by {actor} via aw ipd finalize."
    )
    rc, _out, err = _git(repo_root, ["commit", "-m", commit_msg, "--", *stage])

    # --- CLASSIFY the commit boundary by OBSERVED repository state (E-03). ---
    lifecycle_commit = _lifecycle_commit_exists(repo_root, pre_head, plan_id)
    rc_head, cur_head, _e = _git(repo_root, ["rev-parse", "HEAD"])
    cur_head = cur_head.strip() if rc_head == 0 else pre_head
    if lifecycle_commit is None:
        if cur_head == pre_head:
            # No lifecycle commit: pure pre-commit failure -> rollback.
            return _rollback_and_return(
                f"lifecycle commit did not happen (git rc={rc}: {err.strip()})",
                EXIT_CANNOT_RUN,
            )
        # HEAD moved but not via our marker: ambiguous -> unknown-outcome (fail closed).
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        journal["observed_head"] = cur_head
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"unknown-outcome: HEAD moved to {cur_head[:12]} but not via this finalize's lifecycle "
            f"commit; journal retained at {finalize_journal_path(repo_root, plan_id)}.",
            evidence,
        )

    # The lifecycle commit exists -> committed-incomplete until post-transition passes.
    journal["phase"] = PHASE_COMMITTED_INCOMPLETE
    journal["lifecycle_commit"] = lifecycle_commit
    _write_finalize_journal(repo_root, journal)

    return _complete_after_commit(
        repo_root, dest_path, plan_id, lifecycle_commit, actor, evidence
    )


def _complete_after_commit(
    repo_root: Path,
    dest_path: Path,
    plan_id: str,
    commit_hash: str,
    actor: str,
    evidence: Dict[str, Any],
) -> FinalizeResult:
    """Run post-transition lint on the committed plan; mark COMPLETE on pass, else committed-incomplete."""
    from agent_workflows import ipd_lint as _lint

    try:
        post = _lint.lint_file(dest_path, checkpoint="post-transition")
        evidence["post_transition"] = {
            "disposition": post.disposition,
            "diagnostics": [f"{d.code} {d.message}" for d in post.diagnostics],
        }
        post_ok = post.passing
    except Exception as exc:
        evidence["post_transition"] = {"error": str(exc)}
        post_ok = False

    if not post_ok:
        # committed-incomplete: do NOT amend/reset/re-commit; report the same-command resume.
        return FinalizeResult(
            EXIT_FINDINGS,
            commit_hash,
            f"finalize is COMMITTED-INCOMPLETE for {plan_id}: the lifecycle commit {commit_hash[:12]} "
            "exists but post-transition validation failed. Re-run the SAME command "
            f"`aw ipd finalize {plan_id} --actor <a> --message <m> --apply` to resume (no second "
            "commit); if it still fails, open a corrective follow-up IPD citing it.",
            evidence,
            tuple(evidence.get("post_transition", {}).get("diagnostics", ())),
        )

    # COMPLETE: post-transition passed. Finalize the journal + consume the receipt.
    journal = read_finalize_journal(repo_root, plan_id)
    if journal is not None:
        journal["phase"] = PHASE_COMPLETE
        _write_finalize_journal(repo_root, journal)
    _clear_finalize_journal(repo_root, plan_id)
    # Consume the begin receipt (the transaction is cleanly complete).
    try:
        receipt_path_for(repo_root, plan_id).unlink()
    except OSError:
        pass

    return FinalizeResult(
        EXIT_OK,
        commit_hash,
        f"finalized {plan_id} -> executed at {commit_hash[:12]} (actor {actor})."
        + _disregarded_unowned_note(evidence),
        evidence,
        (),
    )


def _disregarded_unowned_note(evidence: Dict[str, Any]) -> str:
    """Render the E-03 disregarded-unowned paths for a human message (empty when there are none).

    Surfaces what the ownership filter set aside so it is visible in the terminal output, not only
    in the recorded scope audit. Says DISREGARDED, not "in scope": these paths were neither
    justified nor attributed to this execution.
    """
    paths = list(
        (evidence.get("scope_audit", {}) or {}).get("disregarded_unowned_paths", [])
        or []
    )
    if not paths:
        return ""
    return (
        " Disregarded "
        + str(len(paths))
        + " uncommitted path(s) not owned by this execution (left untouched, recorded in the scope "
        "audit): " + ", ".join(paths) + "."
    )


def _resume_post_commit(
    repo_root: Path, journal: Dict[str, Any], plan_id: str, evidence: Dict[str, Any]
) -> FinalizeResult:
    """Resume a COMMITTED-INCOMPLETE transaction by the SAME command: verify + re-run post-transition.

    Performs NO second lifecycle mutation/commit. Verifies the recorded commit still exists, then
    reruns only post-transition validation on the executed plan; marks complete on pass.
    """
    commit_hash = journal.get("lifecycle_commit")
    dest_rel = journal.get("dest_path")
    if not commit_hash or not dest_rel:
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"committed-incomplete journal for {plan_id} is missing commit/dest evidence; "
            "unknown-outcome (fail closed).",
            evidence,
        )
    # Verify the recorded lifecycle commit still exists in history.
    rc, _out, _err = _git(repo_root, ["cat-file", "-e", f"{commit_hash}^{{commit}}"])
    if rc != 0:
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"recorded lifecycle commit {commit_hash[:12]} for {plan_id} not found; unknown-outcome.",
            evidence,
        )
    dest_path = repo_root / dest_rel
    if not dest_path.is_file():
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"executed plan {dest_rel} not found on resume; unknown-outcome.",
            evidence,
        )
    return _complete_after_commit(
        repo_root,
        dest_path,
        plan_id,
        commit_hash,
        journal.get("actor", "unknown"),
        evidence,
    )


def _plans_dir_of(repo_root: Path, plan_path: Path) -> Path:
    """The plans root (parent of the disposition dir) for ``plan_path``."""
    return plan_path.parent.parent


# --------------------------------------------------------------------------------------
# CLI entry (`aw ipd begin`)
# --------------------------------------------------------------------------------------


def run_begin(args) -> int:
    """Entry point for `aw ipd begin <plan> --actor <agent/model>`. Returns 0/1/2."""
    from agent_workflows import selectors
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic as OutDiag,
        select_output,
    )

    ctx = select_output(args)

    selector = getattr(args, "plan", None)
    actor = getattr(args, "actor", None)
    repo_root = _repo_root(Path(getattr(args, "dir", None) or "."))
    now = getattr(args, "_now", None) or _utc_now()

    def _emit(exit_code: int, status: str, summary: str, diags=None, data=None) -> int:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd begin",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=list(diags or []),
                data=data or {},
            )
            return get_renderer(ctx).emit(res, ctx)
        prefix = {EXIT_OK: "", EXIT_FINDINGS: "findings: ", EXIT_CANNOT_RUN: "error: "}[
            exit_code
        ]
        print(f"{prefix}{summary}")
        for d in diags or []:
            print(f"  {d.rule} {d.detail}")
        return exit_code

    # Resolve the plan selector (must resolve to exactly one plan).
    if not selector:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", "aw ipd begin requires a <plan> selector."
        )
    resolution = selectors.resolve(repo_root, "plans", selector)
    if not resolution.paths:
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"no plan matched selector {selector!r}.",
        )
    if len(resolution.paths) > 1:
        cand = ", ".join(p.name for p in resolution.paths)
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"selector {selector!r} is ambiguous ({resolution.kind}); matched: {cand}.",
        )
    plan_path = resolution.paths[0]

    result = begin(repo_root, plan_path, actor or "", timestamp=now)

    if result.exit_code == EXIT_OK and result.receipt is not None:
        receipt = result.receipt
        rcpt_path = result.receipt_path or receipt_path_for(
            repo_root, receipt["plan_id"]
        )
        return _emit(
            EXIT_OK,
            "clean",
            result.message,
            data={
                "receipt_path": _repo_relative(repo_root, rcpt_path),
                "plan_id": receipt["plan_id"],
                "base_head": receipt["base_head"],
                "requirement_digest": receipt["requirement_digest"],
            },
        )
    if result.exit_code == EXIT_FINDINGS:
        diags = [
            OutDiag(
                location=str(plan_path), rule="IPD-BEGIN", detail=f, severity="error"
            )
            for f in result.findings
        ]
        return _emit(EXIT_FINDINGS, "findings", result.message, diags=diags)
    return _emit(EXIT_CANNOT_RUN, "cannot-run", result.message)


def _utc_now() -> str:
    """An ISO-8601 UTC timestamp (deterministic format; value depends on the clock)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------------------
# CLI entry (`aw ipd finalize`)
# --------------------------------------------------------------------------------------


def _parse_scope_reason_flags(values: Optional[List[str]]) -> Dict[str, str]:
    """Parse repeatable ``--scope-reason <path>=<why>`` flags into {path: why}."""
    out: Dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            continue
        path, why = raw.split("=", 1)
        path = path.strip()
        why = why.strip()
        if path and why:
            out[path] = why
    return out


def _parse_scope_ack_flags(values: Optional[List[str]]) -> Dict[str, str]:
    """Parse repeatable ``--scope-ack <path>[=<note>]`` flags into {path: note-or-'acknowledged'}."""
    out: Dict[str, str] = {}
    for raw in values or []:
        if "=" in raw:
            path, note = raw.split("=", 1)
            path = path.strip()
            note = note.strip() or "acknowledged"
        else:
            path = raw.strip()
            note = "acknowledged"
        if path:
            out[path] = note
    return out


def _tty_scope_prompt(
    out_of_scope: List[str], in_scope_unmodified: List[str]
) -> Dict[str, Any]:
    """ONE batched TTY prompt collecting all reasons (out-of-scope) + acks (in-scope-unmodified)."""
    reasons: Dict[str, str] = {}
    acks: Dict[str, str] = {}
    if out_of_scope:
        print(
            "Scope reconciliation - these paths were changed but are OUTSIDE the reviewed "
            "Scope-Paths. Give a short reason for each (empty = refuse):"
        )
        for p in out_of_scope:
            try:
                why = input(f"  reason for {p}: ").strip()
            except EOFError:
                why = ""
            if why:
                reasons[p] = why
    if in_scope_unmodified:
        print(
            "These paths were DECLARED in Scope-Paths but NOT modified. Acknowledge each "
            "(e.g. 'not-needed'; blank = 'acknowledged'):"
        )
        for p in in_scope_unmodified:
            try:
                note = input(f"  acknowledge {p}: ").strip()
            except EOFError:
                note = ""
            acks[p] = note or "acknowledged"
    return {"reasons": reasons, "acks": acks}


def run_finalize(args) -> int:
    """Entry point for `aw ipd finalize <plan> --actor --message [--apply]`. Returns 0/1/2."""
    from agent_workflows import selectors
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic as OutDiag,
        select_output,
    )

    ctx = select_output(args)
    selector = getattr(args, "plan", None)
    actor = getattr(args, "actor", None)
    message = getattr(args, "message", None)
    apply = bool(getattr(args, "apply", False))
    repo_root = _repo_root(Path(getattr(args, "dir", None) or "."))

    def _emit(exit_code: int, status: str, summary: str, diags=None, data=None) -> int:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd finalize",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=list(diags or []),
                data=data or {},
            )
            return get_renderer(ctx).emit(res, ctx)
        prefix = {EXIT_OK: "", EXIT_FINDINGS: "refused: ", EXIT_CANNOT_RUN: "error: "}[
            exit_code
        ]
        print(f"{prefix}{summary}")
        for d in diags or []:
            print(f"  {d.rule} {d.detail}")
        return exit_code

    if not selector:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", "aw ipd finalize requires a <plan> selector."
        )
    resolution = selectors.resolve(repo_root, "plans", selector)
    if not resolution.paths:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", f"no plan matched selector {selector!r}."
        )
    if len(resolution.paths) > 1:
        cand = ", ".join(p.name for p in resolution.paths)
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"selector {selector!r} is ambiguous ({resolution.kind}); matched: {cand}.",
        )
    plan_path = resolution.paths[0]

    # Order 05: collect the non-interactive reconciliation answers from repeatable flags.
    scope_reasons = _parse_scope_reason_flags(getattr(args, "scope_reason", None))
    scope_acks = _parse_scope_ack_flags(getattr(args, "scope_ack", None))
    # Interactive ONLY on a real TTY in the human (non-agent/json) output mode.
    #
    # ttywedge Order 01 (g40w37): stdin.isatty() ALONE is not consent. A driver spawns this command
    # with stdout/stderr piped but stdin INHERITED, so the child sees the operator's terminal, decides
    # it may prompt, and blocks on input() forever for an answer nobody can type, because the prompt
    # itself went into a pipe. That wedged a real finalize for 1h49m holding its run lock, leaving the
    # plan `approved` in pending/ while the run reported `complete`. Hence two extra conditions:
    #   - stdout must ALSO be a TTY: if the prompt is not readable by a human, do not ask.
    #   - an explicit AW_NONINTERACTIVE/CI signal forces non-interactive regardless of the streams.
    # These only ADD conditions, so a genuine human terminal session still prompts exactly as before.
    # Non-interactive here is fail-CLOSED: finalize returns the scope-reconciliation refusal naming the
    # required --scope-reason/--scope-ack flags, which is recoverable, instead of hanging, which is not.
    import os as _os
    import sys as _sys

    def _is_tty(stream: object) -> bool:
        try:
            return bool(getattr(stream, "isatty", None) and stream.isatty())  # type: ignore[union-attr]
        except (ValueError, OSError):
            # A detached/closed stream is not a terminal.
            return False

    forced_noninteractive = any(
        str(_os.environ.get(var, "")).strip().lower() not in ("", "0", "false", "no")
        for var in ("AW_NONINTERACTIVE", "CI")
    )
    interactive = (
        not (ctx.is_agent or ctx.is_json)
        and not forced_noninteractive
        and _is_tty(_sys.stdin)
        and _is_tty(_sys.stdout)
    )
    prompt = _tty_scope_prompt if interactive else None

    result = finalize(
        repo_root,
        plan_path,
        actor or "",
        message or "",
        apply=apply,
        scope_reasons=scope_reasons,
        scope_acks=scope_acks,
        interactive=interactive,
        prompt=prompt,
        plan_selector=selector,
    )

    if result.exit_code == EXIT_OK:
        return _emit(
            EXIT_OK,
            "clean",
            result.message,
            data={"commit": result.commit, "evidence": result.evidence},
        )
    if result.exit_code == EXIT_FINDINGS:
        diags = [
            OutDiag(
                location=str(plan_path), rule="IPD-FINALIZE", detail=f, severity="error"
            )
            for f in result.findings
        ]
        return _emit(EXIT_FINDINGS, "findings", result.message, diags=diags)
    return _emit(EXIT_CANNOT_RUN, "cannot-run", result.message)
