#!/usr/bin/env python3
"""The durable, monotonic STOP-REQUEST record and the driver's cooperative stop poll.

Spec `c4gd2h` (runner lifecycle: graceful-quit protocol) requires that a stop be REQUESTED
durably and honored at cooperative checkpoints, never delivered as a raw kill. This module owns
that request mechanism and nothing else:

- R7  the driver POLLS a stop-request flag at cooperative checkpoints (see `poll_stop`).
- R8  a request is DURABLE and IDEMPOTENT: recorded once, re-reading never re-triggers, and it
      survives the driver being between checkpoints.
- R9  escalation is MONOTONIC: a request may only RAISE the level, never lower it, so an operator
      "pressing harder" is always honored.
- R11 each level carries a bounded wind-down BUDGET (recorded here, ENFORCED per level by the
      phases that own each level's behavior).

WHAT THIS MODULE DELIBERATELY DOES NOT DO. It implements no level's BEHAVIOR (what actually
completes before shutdown), registers no signal handler, and exposes no CLI verb. Those belong to
the later phases of Set `runstop`. This module only makes a stop request expressible and
observable.

WHERE THE FLAG LIVES (spec `c4gd2h` OQ-03, RESOLVED). The stop request is per-machine CONTROL
state and lives INSIDE the driver's run directory, as `<run_dir>/stop-request.json`, beside the
existing `driver.lock`. It is resolved from the SAME accessor the drivers already use for
`run_dir` (`oc_runipd.state_root` / `agy_runipd.state_root`), never from a root constructed here.
That is deliberate: Set `wtiso` Phase 4 relocates the driver run root OUT of the repository to
`platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/`, and because this module
resolves through the shared accessor it inherits that relocation automatically. DO NOT "fix" this
back into `<repo>/.aw/state` and do not resolve it from a worktree-relative path: an inner `aw`
would fork a second state tree the driver cannot see, and worktree teardown would destroy it
(backlog `dh0uno`).

WHY THERE IS A SIDECAR LOCK (do not "simplify" this away). Writing the record with
`tempfile.mkstemp` + `os.replace` makes each WRITE atomic, but it does NOT serialize the
READ-MODIFY-WRITE that monotonicity requires (read current level -> compare -> write). Two
writers exist by design (a signal handler and the out-of-band `stop` command), and a measured
200-trial two-writer harness (levels 4 vs 1) LOST the higher level in 100/200 trials, i.e. 50%,
with atomic writes alone. Serializing the read-compare-write under an exclusive lock on a
SEPARATE sidecar file measured 0/200 lost. The lock MUST be the sidecar, never the record itself,
because the record is swapped by `os.replace` and a lock held on the replaced inode protects
nothing. Removing the sidecar lock silently reintroduces the exact operator-visible downgrade
that R9 exists to prevent.

WHY THE HANDLER PATH NEVER BLOCKS (do not "simplify" this away either). Because a later phase
calls this writer from SIGINT/SIGTERM handlers, a BLOCKING lock acquire is a deadlock: `flock`
locks attach to the open file description, so a second acquire from the same process fails or
waits, and a signal arriving while the main thread already holds the sidecar lock re-enters on the
SAME thread. Measured directly: the handler entered and then hung until a 10s timeout killed it.
`request_stop_nowait` therefore makes ONE `LOCK_EX | LOCK_NB` attempt and, on contention, records
the level in a process-local slot that the already-required polling loop drains durably at its
next checkpoint. `request_stop` likewise never issues a blocking `flock`; it retries the
non-blocking acquire under a bounded deadline and fails loudly instead of hanging.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import errno
import fcntl
import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Container, Iterable, Iterator, Sequence, Tuple

__all__ = [
    "STOP_REQUEST_FILENAME",
    "STOP_REQUEST_LOCK_FILENAME",
    "SCHEMA_VERSION",
    "LEVELS",
    "LEVEL_AFTER_CALL",
    "LEVEL_AFTER_SET",
    "LEVEL_NOW",
    "LEVEL_NOW_FORCE",
    "LEVEL_NAMES",
    "WIND_DOWN_BUDGET_SECONDS",
    "StopRequestError",
    "StopRequest",
    "StopRequestResult",
    "stop_request_path",
    "stop_request_lock_path",
    "resolve_stop_request_path",
    "budget_for_level",
    "read_stop_request",
    "request_stop",
    "request_stop_nowait",
    "poll_stop",
    "pending_deferred_request",
    "reset_deferred_request",
    "BETWEEN_TURN_LEVELS",
    "WindDown",
    "deliberate_stop_event",
    "deliberate_stop_exit_code",
    # level 3 (runstop Phase 3, `foi1b3`): the observed safe checkpoint, the KNOWN disposition,
    # and the bounded-wait breach DETECTOR (escalation itself is Phase 5's).
    "OC_STEP_COMPLETE_TYPE",
    "OC_TOOL_EVENT_TYPE",
    "OC_COMPLETED_STATUS",
    "AGY_STEP_EVENT_TYPE",
    "AGY_COMPLETED_STATE",
    "is_oc_safe_checkpoint",
    "is_agy_safe_checkpoint",
    "event_label",
    "CheckpointObserver",
    "StopAtCheckpoint",
    "STOPPED_DISPOSITION",
    "CERTAINTY_KNOWN",
    "stopped_disposition",
    "stopped_stop_event",
    "BUDGET_BREACH_EVENT",
    "budget_breach_event",
    "deadline_seconds_remaining",
    "BudgetBreachWatch",
]

# --- the record's on-disk identity ----------------------------------------------------------------

STOP_REQUEST_FILENAME = "stop-request.json"
# The sidecar lock. NEVER lock `STOP_REQUEST_FILENAME` itself: it is replaced by `os.replace`, so a
# lock on the replaced inode would protect nothing (see the module docstring).
STOP_REQUEST_LOCK_FILENAME = "stop-request.lock"
SCHEMA_VERSION = 1

# --- the four levels (spec `c4gd2h` section 3; the levels are the maintainer's design) ------------
#
# The levels differ ONLY in how much in-flight work is permitted to COMPLETE before shutdown
# begins. None of them makes cleanup optional (spec R15).

LEVEL_AFTER_CALL = (
    1  # the in-flight IPD's agent turn finishes; the next item is not dequeued
)
LEVEL_AFTER_SET = 2  # the rest of THIS set's queue finishes; stops before any next set
LEVEL_NOW = 3  # the current agent turn stops at its next SAFE checkpoint
LEVEL_NOW_FORCE = (
    4  # the current agent turn is interrupted IMMEDIATELY, outcome indeterminate
)

LEVELS: Tuple[int, ...] = (
    LEVEL_AFTER_CALL,
    LEVEL_AFTER_SET,
    LEVEL_NOW,
    LEVEL_NOW_FORCE,
)

LEVEL_NAMES = {
    LEVEL_AFTER_CALL: "after-call",
    LEVEL_AFTER_SET: "after-set",
    LEVEL_NOW: "now",
    LEVEL_NOW_FORCE: "now-force",
}

# Spec R11: each level has a BOUNDED wind-down budget, so a hung turn cannot make a stop hang
# forever. Recorded here as the ONE authoritative value so the phases owning levels 1-4 read it
# instead of each inventing a timeout. This module does NOT enforce it.
#
# Derivation of the defaults (recorded so a later reader can argue with the numbers, not guess at
# them):
#   level 4: 0 by definition. "Interrupt immediately" has no wind-down phase at all.
#   level 3: 600s, deliberately equal to the drivers' `DEFAULT_STALL_TIMEOUT`. A safe checkpoint is
#            observed from the child's event stream, and the existing StallWatchdog already
#            declares the turn stalled if no line arrives within that window, so a checkpoint must
#            occur inside it or the turn is already a stall case.
#   level 1: 7200s (2h), sized from ONE observed agent turn with headroom (a turn in this Set's own
#            driver run took ~70 minutes wall clock).
#   level 2: 28800s (8h), sized for the remainder of a set under the unattended overnight posture
#            these drivers are run in.
WIND_DOWN_BUDGET_SECONDS = {
    LEVEL_AFTER_CALL: 7200.0,
    LEVEL_AFTER_SET: 28800.0,
    LEVEL_NOW: 600.0,
    LEVEL_NOW_FORCE: 0.0,
}

# How long `request_stop` will retry its NON-BLOCKING acquire before failing loudly. This is a
# bounded retry, never a blocking `flock` (see the module docstring).
DEFAULT_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_RETRY_SLEEP_SECONDS = 0.001


class StopRequestError(RuntimeError):
    """A stop request could not be recorded durably (e.g. the sidecar lock stayed contended)."""


class _LockBusy(Exception):
    """Internal: the sidecar lock was held by someone else and we refused to block for it."""


# --- the record -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class StopRequest:
    """A durable stop request. `level` is the CURRENT (highest ever requested) level.

    `requested_at` is the timestamp of the request that established the current level, so
    `deadline == requested_at + budget_seconds` holds for the level in force (spec R11).
    `first_requested_at` and `history` preserve the escalation audit trail (spec R9/R21).
    """

    level: int
    requested_at: str
    requester: str
    first_requested_at: str
    budget_seconds: float
    deadline: str
    history: Tuple[dict, ...] = field(default_factory=tuple)
    schema_version: int = SCHEMA_VERSION

    @property
    def level_name(self) -> str:
        return LEVEL_NAMES.get(self.level, "unknown")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "level": self.level,
            "level_name": self.level_name,
            "requested_at": self.requested_at,
            "requester": self.requester,
            "first_requested_at": self.first_requested_at,
            "budget_seconds": self.budget_seconds,
            "deadline": self.deadline,
            "history": [dict(entry) for entry in self.history],
        }


@dataclass(frozen=True)
class StopRequestResult:
    """The outcome of asking for a stop.

    `accepted` is True when this call RAISED the recorded level. A request at or below the stored
    level is a recorded NO-OP (`accepted=False`), never a downgrade (spec R9). `deferred` is True
    when a handler-safe call could not take the sidecar lock and left the level for the polling
    loop to write durably; `request` is then the last durable state, which may be None.
    """

    request: StopRequest | None
    accepted: bool
    deferred: bool = False


def _validate_level(level: Any) -> int:
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError(f"stop level must be an int in {LEVELS}, got {level!r}")
    if level not in LEVELS:
        raise ValueError(f"stop level must be one of {LEVELS}, got {level!r}")
    return level


def budget_for_level(level: int) -> float:
    """The bounded wind-down budget for `level`, in seconds (spec R11)."""

    return WIND_DOWN_BUDGET_SECONDS[_validate_level(level)]


# --- path resolution (spec OQ-03: follow the driver's own run-dir accessor) ------------------------


def stop_request_path(run_dir: Path | str) -> Path:
    """The stop-request record for a run directory: `<run_dir>/stop-request.json`."""

    return Path(run_dir) / STOP_REQUEST_FILENAME


def stop_request_lock_path(run_dir: Path | str) -> Path:
    """The SIDECAR lock serializing read-modify-write on the record (never the record itself)."""

    return Path(run_dir) / STOP_REQUEST_LOCK_FILENAME


def resolve_stop_request_path(
    repo: Path | str,
    run_id: str,
    *,
    state_root: Callable[[Path], Path],
) -> Path:
    """Resolve the flag through the caller's OWN `state_root` accessor.

    `state_root` must be the driver's accessor (`oc_runipd.state_root` /
    `agy_runipd.state_root`). Taking it as a parameter is what keeps this module from constructing
    a second run root: when Set `wtiso` Phase 4 moves that accessor's answer out of the
    repository, the flag moves with it and nothing here changes (spec OQ-03).
    """

    return stop_request_path(state_root(Path(repo)) / run_id)


# --- reading ---------------------------------------------------------------------------------------


def _parse(payload: Any) -> StopRequest | None:
    """Build a StopRequest from decoded JSON, or None if it is not a usable record."""

    if not isinstance(payload, dict):
        return None
    level = payload.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or level not in LEVELS:
        return None
    requested_at = payload.get("requested_at")
    if not isinstance(requested_at, str) or not requested_at:
        return None
    budget = payload.get("budget_seconds")
    if isinstance(budget, bool) or not isinstance(budget, (int, float)):
        budget = WIND_DOWN_BUDGET_SECONDS[level]
    deadline = payload.get("deadline")
    if not isinstance(deadline, str) or not deadline:
        deadline = _deadline_for(requested_at, float(budget))
    raw_history = payload.get("history")
    history: Tuple[dict, ...] = ()
    if isinstance(raw_history, list):
        history = tuple(dict(e) for e in raw_history if isinstance(e, dict))
    first = payload.get("first_requested_at")
    if not isinstance(first, str) or not first:
        first = requested_at
    requester = payload.get("requester")
    if not isinstance(requester, str):
        requester = ""
    schema = payload.get("schema_version")
    if isinstance(schema, bool) or not isinstance(schema, int):
        schema = SCHEMA_VERSION
    return StopRequest(
        level=level,
        requested_at=requested_at,
        requester=requester,
        first_requested_at=first,
        budget_seconds=float(budget),
        deadline=deadline,
        history=history,
        schema_version=schema,
    )


def read_stop_request(run_dir: Path | str) -> StopRequest | None:
    """The current durable stop request, or None when there is none.

    FAIL SAFE, never fail loud: an absent, unreadable, truncated, or otherwise malformed control
    file reads as None (no stop requested) rather than raising. A corrupt control file must never
    crash the driver, and a torn file must never be readable as a valid LOWER level. Because
    `request_stop` writes via temp + `os.replace`, a reader sees either the previous complete
    record or the new one, never a partial one.
    """

    path = stop_request_path(run_dir)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError):
        return None
    except OSError:
        return None
    try:
        payload = json.loads(text)
    except (ValueError, UnicodeDecodeError):
        return None
    return _parse(payload)


# --- writing (monotonic, serialized by the sidecar lock) ------------------------------------------


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _deadline_for(requested_at: str, budget_seconds: float) -> str:
    try:
        base = dt.datetime.fromisoformat(requested_at)
    except ValueError:
        return requested_at
    return (base + dt.timedelta(seconds=budget_seconds)).isoformat()


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Write-to-temp-then-rename so an interrupted write never leaves a partial record.

    Same shape as `ipd_authoring._atomic_write`. NOTE: this makes the WRITE atomic and nothing
    more; it does NOT serialize read-modify-write. Callers must already hold the sidecar lock.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


@contextlib.contextmanager
def _sidecar_lock(run_dir: Path, *, timeout: float) -> Iterator[None]:
    """Hold the sidecar lock, acquired with NON-BLOCKING attempts only.

    `timeout <= 0` means a SINGLE attempt (the handler-safe path); a positive timeout retries the
    non-blocking acquire until the deadline. There is deliberately no blocking `flock` anywhere in
    this module: a blocking acquire reached from a signal handler deadlocks the process (measured;
    see the module docstring). Raises `_LockBusy` when the lock could not be taken.
    """

    lock_path = stop_request_lock_path(run_dir)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    try:
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
                if timeout <= 0 or time.monotonic() >= deadline:
                    raise _LockBusy(str(lock_path)) from exc
                time.sleep(_LOCK_RETRY_SLEEP_SECONDS)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        with contextlib.suppress(OSError):
            handle.close()


def _apply_request(run_dir: Path, level: int, requester: str) -> StopRequestResult:
    """The MONOTONIC read-modify-write. The caller MUST already hold the sidecar lock."""

    current = read_stop_request(run_dir)
    if current is not None and level <= current.level:
        # Spec R9: a request at or below the stored level is a recorded NO-OP, never a downgrade.
        # The file is left byte-for-byte untouched, which is also what keeps repeated identical
        # requests idempotent (spec R8).
        return StopRequestResult(request=current, accepted=False)

    now = _utc_now()
    requested_at = now.isoformat()
    budget = WIND_DOWN_BUDGET_SECONDS[level]
    entry = {"level": level, "at": requested_at, "requester": requester}
    history = tuple(current.history) + (entry,) if current is not None else (entry,)
    request = StopRequest(
        level=level,
        requested_at=requested_at,
        requester=requester,
        first_requested_at=(
            current.first_requested_at if current is not None else requested_at
        ),
        budget_seconds=budget,
        deadline=(now + dt.timedelta(seconds=budget)).isoformat(),
        history=history,
    )
    _atomic_write_json(stop_request_path(run_dir), request.to_dict())
    return StopRequestResult(request=request, accepted=True)


def request_stop(
    run_dir: Path | str,
    level: int,
    requester: str,
    *,
    timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> StopRequestResult:
    """Durably record a stop request, raising the level MONOTONICALLY (spec R7-R9).

    Never lowers the recorded level: a request at or below the stored level returns
    `accepted=False` and leaves the record untouched. The read-compare-write runs under the
    sidecar lock, without which a concurrent lower-level writer measurably clobbers a higher one
    ~50% of the time.

    NOT for use from a signal handler: use `request_stop_nowait`. This call retries the
    non-blocking acquire for up to `timeout` seconds and raises `StopRequestError` if the lock
    stays contended, so it fails loudly rather than hanging.
    """

    _validate_level(level)
    run_dir = Path(run_dir)
    try:
        with _sidecar_lock(run_dir, timeout=timeout):
            return _apply_request(run_dir, level, requester)
    except _LockBusy as exc:
        raise StopRequestError(
            f"could not record stop request: sidecar lock still held after {timeout}s ({exc})"
        ) from exc


# --- signal-handler-safe entry point --------------------------------------------------------------
#
# THE ENTRY POINT A SIGNAL HANDLER MUST USE. A handler may not risk the sidecar lock: the signal
# lands on the main thread, which may already hold it, and a blocking acquire then hangs the
# process outright (measured: the handler entered, then hung until a 10s timeout killed it, exit
# 124). So the handler makes ONE non-blocking attempt and, on contention, only ASSIGNS to the
# module-level slot below (a single store, which is what makes it async-signal-safe); the
# already-required polling loop performs the durable write at its next checkpoint.

_DEFERRED_REQUEST: Tuple[int, str] | None = None


def _defer(level: int, requester: str) -> None:
    """Record a stop level process-locally. Kept to a single store so a handler may call it."""

    global _DEFERRED_REQUEST
    pending = _DEFERRED_REQUEST
    if pending is None or level > pending[0]:
        _DEFERRED_REQUEST = (level, requester)


def pending_deferred_request() -> Tuple[int, str] | None:
    """The process-local stop level a signal handler could not write durably, if any."""

    return _DEFERRED_REQUEST


def reset_deferred_request() -> None:
    """Clear the process-local deferred slot (for tests and for a fresh run in-process)."""

    global _DEFERRED_REQUEST
    _DEFERRED_REQUEST = None


def request_stop_nowait(
    run_dir: Path | str, level: int, requester: str
) -> StopRequestResult:
    """SIGNAL-HANDLER-SAFE stop request. Makes ONE non-blocking attempt; never blocks.

    On success this behaves exactly like `request_stop`. On sidecar-lock contention it does NOT
    wait: it records the level in a process-local slot and returns `deferred=True`, and
    `poll_stop` writes it durably at the next cooperative checkpoint (spec R7's polling loop is
    the documented durable-write point). The request is therefore never lost and never deadlocks.
    """

    _validate_level(level)
    run_dir = Path(run_dir)
    try:
        with _sidecar_lock(run_dir, timeout=0.0):
            return _apply_request(run_dir, level, requester)
    except _LockBusy:
        _defer(level, requester)
        return StopRequestResult(request=None, accepted=False, deferred=True)
    except OSError:
        # Even a filesystem failure must not lose the operator's intent or propagate out of a
        # signal handler: keep it process-local and let the poll retry.
        _defer(level, requester)
        return StopRequestResult(request=None, accepted=False, deferred=True)


# --- the cooperative poll -------------------------------------------------------------------------


def poll_stop(run_dir: Path | str) -> int | None:
    """The driver's cooperative-checkpoint poll: the currently requested level, or None.

    SIDE-EFFECT FREE and IDEMPOTENT with respect to the request (spec R8): it reports the current
    level and never consumes the request, so repeated polls return the same level and leave the
    record byte-for-byte unchanged. The driver acts on a level TRANSITION, not on the presence of
    a file.

    The ONE mandated side effect is draining a signal-deferred request (see `request_stop_nowait`):
    the poll is the documented durable-write point for a level a handler could not write itself. A
    drain that fails leaves the request pending for the next poll rather than dropping it.
    """

    global _DEFERRED_REQUEST

    run_dir = Path(run_dir)
    pending = _DEFERRED_REQUEST
    if pending is not None:
        try:
            request_stop(run_dir, pending[0], pending[1], timeout=0.05)
        except (StopRequestError, OSError, ValueError):
            pass  # stays pending; the next checkpoint retries it
        else:
            if _DEFERRED_REQUEST == pending:
                # Only clear what we actually wrote: a handler may have escalated in between.
                _DEFERRED_REQUEST = None
    request = read_stop_request(run_dir)
    return request.level if request is not None else None


# --- levels 1 and 2: the BETWEEN-TURN wind-down (spec `c4gd2h` R20/R21, A1/A4) ---------------------
#
# Owned by Set `runstop` Phase 2 (`1qxuke`). Levels 1 and 2 are the two levels that never interrupt
# a running turn, so their entire correctness argument is about the DEQUEUE decision: which items
# the driver still consents to start. That decision is expressed here, ONCE, so both drivers
# consult one implementation instead of each re-deriving the boundary (spec R5's single-source
# discipline; orchestrator CID-3 requires the two drivers to expose the same levels).
#
# Level 1 = STOP-AFTER-CALL (R20/A1): the in-flight turn finishes, then NO further item starts.
# Level 2 = STOP-AFTER-SET  (R20/A4): the rest of the CURRENT set finishes, then nothing else.
#
# WHY THE CURRENT SET MUST BE CAPTURED, NOT RE-DERIVED (the subtle part). The drivers' dequeue is
# DEPENDENCY-ordered, not set-ordered: `run_queue` picks the first `queued` item whose dependencies
# are satisfied by scanning the WHOLE queue, even though the queue is BUILT set-contiguously. So
# sets INTERLEAVE. Measured against the real `dependency_status`: with the queue
# `A/a1 (executed), A/a2 (blocked on an unmet dep), B/b1 (ready)`, the next dequeue is `B/b1` - the
# in-flight set jumps A -> B while set A still holds a queued item. Consequences encoded below:
#   * "the current set" is the setid of the item in flight when the request was OBSERVED, captured
#     ONCE (`WindDown.setid`) and held for the whole wind-down;
#   * a "stop when the setid changes" rule would be wrong in BOTH directions (it can stop early on
#     an interleave, or resume set A after B and never stop at all);
#   * during a level-2 wind-down an item of ANOTHER set is out of scope and stays `queued` EVEN IF
#     it is the only runnable item, so a level-2 stop can legitimately end with runnable work
#     outstanding. That is correct: the operator asked to wind down, not to drain the queue.

BETWEEN_TURN_LEVELS: Tuple[int, ...] = (LEVEL_AFTER_CALL, LEVEL_AFTER_SET)


@dataclass(frozen=True)
class WindDown:
    """An OBSERVED level-1/2 stop request, with the set boundary frozen at observation time.

    `setid` is the set that was in flight when the request was first observed, or None when the
    request was observed before any item had run. It is captured once precisely because the
    dependency-ordered dequeue lets sets interleave (see the module comment above).
    """

    level: int
    requester: str
    setid: str | None

    @property
    def level_name(self) -> str:
        return LEVEL_NAMES.get(self.level, "unknown")

    def permits(self, item_setid: str | None) -> bool:
        """May the driver still START an item belonging to `item_setid` during this wind-down?

        Level 1 permits nothing further (the boundary is the next ITEM). Level 2 permits only the
        captured set (the boundary is the next SET). A wind-down observed before any item ran has
        no captured set, so level 2 has no set to finish and permits nothing either: that is the
        conservative direction, and it can never run an item the operator asked to skip.
        """

        if self.level == LEVEL_AFTER_CALL:
            return False
        if self.level == LEVEL_AFTER_SET:
            return self.setid is not None and item_setid == self.setid
        # Levels 3 and 4 interrupt the turn itself and are owned by later phases; they are not
        # between-turn boundaries and must not be silently treated as permissive here.
        return False


def deliberate_stop_event(
    wind_down: WindDown,
    *,
    at: str,
    remaining: Sequence[str] = (),
) -> dict:
    """The ledger event recording a DELIBERATE stop, as a NON-FAILURE (spec R21).

    Written to the driver's established append-only `events.jsonl` channel. It names the level and
    the requester so history shows the operator's INTENT rather than implying breakage, and lists
    the items deliberately not started so the record is self-describing. Un-run items keep their
    existing `queued` status: no per-item status is invented, and nothing is marked
    `unknown_outcome`, because no turn was interrupted (spec R20).
    """

    return {
        "at": at,
        "event": "deliberate-stop",
        "deliberate": True,
        "failure": False,
        "level": wind_down.level,
        "level_name": wind_down.level_name,
        "requester": wind_down.requester,
        "boundary": "next-item" if wind_down.level == LEVEL_AFTER_CALL else "next-set",
        "current_setid": wind_down.setid,
        "not_started": list(remaining),
    }


def deliberate_stop_exit_code(
    statuses: Iterable[str],
    *,
    success_states: Container[str],
    stopped: bool,
) -> int:
    """The run's exit code, honest about BOTH a deliberate stop and a real failure.

    The drivers' normal predicate is "every item reached a success state, else 1". A deliberate
    stop intentionally leaves items `queued`, which is NOT a success state, so that predicate
    returns 1 for a correct, operator-requested wind-down (verified by direct evaluation:
    `['executed', 'queued', 'queued']` -> 1). Spec A1 and A4 both require exit 0.

    So when `stopped` is true, the run exits 0 iff every item that actually RAN reached a success
    state; items still `queued` are ignored BECAUSE THEY NEVER RAN, not because they succeeded.
    Their status is left untouched: rewriting them to buy the 0 is exactly the fabricated
    disposition spec R22 forbids. A stop whose last run item genuinely FAILED still exits nonzero.
    """

    remaining = list(statuses)
    if not stopped:
        return 0 if all(status in success_states for status in remaining) else 1
    return (
        0
        if all(status in success_states for status in remaining if status != "queued")
        else 1
    )


# --- level 3: the OBSERVED safe checkpoint (spec `c4gd2h` R10/R18, A3) -----------------------------
#
# Owned by Set `runstop` Phase 3 (`foi1b3`). Level 3 is the first level that interrupts the RUNNING
# turn, so unlike levels 1-2 its correctness is not about the dequeue decision but about WHEN the
# turn is cut. Spec R10 forbids defining that instant by elapsed time, so it is defined by an
# OBSERVATION of the child's own event stream.
#
# THE DEFINITION (spec OQ-01's resolution, which this module implements). A SAFE CHECKPOINT is the
# instant AFTER a COMPLETED tool/step event has been consumed and BEFORE the next one is dispatched.
# That is observable from the per-line loop the drivers already run, so no agent cooperation, prompt
# change, or per-agent capability handshake is required (all three were explicitly rejected by that
# resolution; do not reintroduce them).
#
# VERIFIED AGAINST A REAL SESSION, not assumed (2026-08-29, re-verified 2026-08-30 while executing
# this phase, parsing `.aw/records/runs/run-20260829T053827Z-2084502/sessions/01-jolfpj-attempt-1.jsonl`):
# that file holds 122 `step_start`, 122 `step_finish`, 135 `tool_use` (EVERY ONE carrying
# `part.state.status == "completed"`), and 85 `text` records. So "completed" is an OBSERVED field
# rather than an inference, and `step_finish` is the cleaner completion signal than `step_start`.
#
# WHY THE PARSE LIVES HERE AND NOT IN `render_event`. `render_event` (`render_stream.py`) is invoked
# ONLY under `output_mode == "clean"` (`oc_runipd.py`, the `elif output_mode == "clean"` branch). In
# `raw` and `quiet` modes NOTHING parses the event line, so a checkpoint detector built on
# `render_event` would silently never fire in two of the three output modes - the feature would
# appear to work and not work depending on an unrelated display flag. The detector below therefore
# does its own minimal `json.loads` + type/status read, reusing only the FIELD NAMES, never the
# rendering. Do not route it back through `render_event`.
#
# THE TWO DRIVERS HAVE DIFFERENT EVENT SCHEMAS (orchestrator CID-3 requires the same SEMANTICS in
# both, not the same field reads). `oc` emits `{"type": "tool_use", "part": {"state": {"status":
# "completed"}}}` plus `step_start`/`step_finish`; `agy` emits `{"type": "step_update",
# "step_update": {"state": "DONE"}}` (see `agy_runipd.render_agy_event`). Hence two detectors with
# one shared meaning.
#
# WHAT "SAFE" HONESTLY MEANS, stated so a reader does not overstate it. The driver cannot see INSIDE
# a tool call, so it cannot promise nothing was mid-flight; it can only promise that no PREVIOUSLY
# OBSERVED operation was cut mid-flight. Anything the agent began after emitting its last event is
# unobserved, and uncommitted work is not covered at all (the runbook has the agent commit and write
# its outcome JSON at turn END). That limit is exactly why `stopped_disposition` below must intercept
# the disposition path rather than trust it.

# The oc event types that can carry a completion. `step_finish` is a completion by definition;
# `tool_use` is one only when its `part.state.status` says so.
OC_STEP_COMPLETE_TYPE = "step_finish"
OC_TOOL_EVENT_TYPE = "tool_use"
OC_COMPLETED_STATUS = "completed"

# The agy counterpart: a `step_update` whose `state` is DONE.
AGY_STEP_EVENT_TYPE = "step_update"
AGY_COMPLETED_STATE = "DONE"


def _decode_event(line: str) -> dict | None:
    """Decode ONE stream line as a JSON object, or None when it is not one.

    Returns None for a blank line, a partial/interleaved line, or any non-object payload. This is
    the whole reason a partial line cannot be mistaken for a checkpoint: an incomplete JSON line
    does not decode, so it reports nothing rather than defaulting to "safe".
    """

    text = line.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def is_oc_safe_checkpoint(line: str) -> bool:
    """Does this `oc` stream line END at a safe checkpoint (spec R10)?

    True for a `step_finish`, and for a `tool_use` whose `part.state.status` is `completed`. Any
    other status (`running`, `error`, `pending`, absent) is NOT a checkpoint: the operation it
    describes is not known to have finished, so stopping there would cut it mid-flight.

    Deliberately independent of `output_mode` and of `render_event` (see the module comment above).
    """

    event = _decode_event(line)
    if event is None:
        return False
    event_type = event.get("type")
    if event_type == OC_STEP_COMPLETE_TYPE:
        return True
    if event_type != OC_TOOL_EVENT_TYPE:
        return False
    part = event.get("part")
    if not isinstance(part, dict):
        return False
    state = part.get("state")
    if not isinstance(state, dict):
        return False
    return state.get("status") == OC_COMPLETED_STATUS


def is_agy_safe_checkpoint(line: str) -> bool:
    """Does this `agy` stream line END at a safe checkpoint (spec R10)?

    The agy schema is NOT the oc schema: completion is `{"type": "step_update", "step_update":
    {"state": "DONE"}}`, so this reads `step_update.state`, never oc's `part.state.status`. `ACTIVE`,
    `ERROR`, and `FAILED` are not checkpoints.
    """

    event = _decode_event(line)
    if event is None:
        return False
    if event.get("type") != AGY_STEP_EVENT_TYPE:
        return False
    step = event.get(AGY_STEP_EVENT_TYPE)
    if not isinstance(step, dict):
        return False
    return str(step.get("state", "")).upper() == AGY_COMPLETED_STATE


def event_label(line: str) -> str:
    """A short, human-readable name for the operation an event line describes.

    Recorded on the interrupted item so the ledger names the LAST COMPLETED OPERATION rather than
    only its index (spec R18). Best-effort by design: an unrecognized line yields a generic label
    instead of raising, because a stop must never fail on a cosmetic detail.
    """

    event = _decode_event(line)
    if event is None:
        return "unknown"
    event_type = str(event.get("type") or "unknown")
    part = event.get("part")
    if isinstance(part, dict):
        tool = part.get("tool")
        if isinstance(tool, str) and tool:
            return f"{event_type}:{tool}"
    step = event.get(AGY_STEP_EVENT_TYPE)
    if isinstance(step, dict):
        info = step.get("tool_info")
        name = None
        if isinstance(info, dict):
            name = info.get("name")
        name = name or step.get("tool_name") or step.get("step_type")
        if isinstance(name, str) and name:
            return f"{event_type}:{name}"
    return event_type


@dataclass
class CheckpointObserver:
    """Tracks whether a level-3 stop is pending and whether a safe checkpoint has been reached.

    Fed ONE stream line at a time from the driver's existing per-line loop, so it adds no new
    observation channel (spec R5's single-source discipline: the loop that already touches the
    statusline, the stall watchdog, and the stop poll).

    `detector` is the per-driver completion predicate (`is_oc_safe_checkpoint` /
    `is_agy_safe_checkpoint`), injected rather than branched on so the two drivers share this
    control flow while reading their own schemas.

    THIS CLASS DECIDES *WHEN*, NOT *HOW*. The actual stop is a TERMINATION performed by the caller
    through `runner_shutdown.clean_shutdown` (spec R5). See `StopAtCheckpoint` for why there is no
    cooperative alternative.
    """

    detector: Callable[[str], bool]
    requested_level: int | None = None
    requester: str = ""
    # Every line consumed, whether or not it was a checkpoint. This is the honest denominator for
    # "the turn stopped after event N".
    events_seen: int = 0
    # The 1-based index and label of the last COMPLETED event observed. `None` means no completed
    # event has been seen yet, so no checkpoint is reachable from what we have observed.
    last_checkpoint_index: int | None = None
    last_checkpoint_label: str | None = None
    stop_at_checkpoint: bool = False

    def request(self, level: int, requester: str = "") -> None:
        """Record that a level-3 stop is in force; the next checkpoint becomes the stop point.

        Monotonic in the same spirit as the durable record: a level already at or above `level`
        is not lowered here either.
        """

        if self.requested_level is None or level > self.requested_level:
            self.requested_level = level
            self.requester = requester or self.requester

    @property
    def pending(self) -> bool:
        return self.requested_level is not None

    def observe(self, line: str) -> bool:
        """Consume one stream line; return True when the turn must stop NOW.

        Order matters: the line is classified FIRST, so the checkpoint the driver stops at is one it
        has actually observed completing, and the recorded position is that event's - never the
        position of a line that merely arrived after the request.
        """

        self.events_seen += 1
        if self.detector(line):
            self.last_checkpoint_index = self.events_seen
            self.last_checkpoint_label = event_label(line)
            if self.pending:
                self.stop_at_checkpoint = True
                return True
        return False


class StopAtCheckpoint(Exception):
    """Raised inside the per-line loop when a level-3 stop reached its safe checkpoint.

    THE MECHANISM, STATED PLAINLY SO IT IS NOT OVERSTATED. The child is a ONE-SHOT
    `opencode run` / `agy` subprocess with NO cooperative stop channel: the driver's only controls
    over a running turn are reading its stdout and signalling it. There is no "please wind down"
    input, and adding one (a prompt change or a per-agent handshake) was explicitly rejected by spec
    `c4gd2h` OQ-01's resolution.

    So "stopping the turn at a checkpoint" IS TERMINATION - at an instant chosen by observation. The
    in-repo precedent does exactly the same thing: `StallWatchdog._run` calls `terminate_process`
    when it fires. Levels 3 and 4 therefore SHARE this mechanism and differ ONLY in WHEN it is
    issued: level 3 waits for an observed completed-event boundary, level 4 does not wait at all.

    Consequently "KNOWN" certainty means "no PREVIOUSLY OBSERVED operation was cut mid-flight", NOT
    "the agent finished tidily". The agent may still have had unflushed intent, and anything it began
    after its last emitted event is unobserved.

    Raising is deliberate: it unwinds to the driver's existing `except BaseException` handler, which
    already routes to the shared reaper, so no second teardown path is introduced (spec R5).
    """

    def __init__(self, observer: CheckpointObserver) -> None:
        self.observer = observer
        level = observer.requested_level
        super().__init__(
            f"level-{level} stop honored at safe checkpoint after event "
            f"{observer.last_checkpoint_index} ({observer.last_checkpoint_label})"
        )


# --- level 3: the KNOWN disposition (spec R18/R21/R22) --------------------------------------------
#
# WHY THIS EXISTS AT ALL, measured rather than assumed. A level-3 stop leaves NO per-item outcome
# JSON (the runbook has the AGENT write `outcomes/<NN>-<id6>.json` at turn END, so a mid-turn stop
# never produces it), the plan is still in `pending/`, and the terminated child exits NONZERO.
# `reconcile_disposition` in both drivers therefore falls through every branch to its final
# `return ("partial" if exit_code == 0 else "failed-safely")` and labels a DELIBERATE OPERATOR STOP
# as `failed-safely`. That is precisely the crash-versus-intent conflation spec R21 forbids and the
# unearned verdict R22 forbids. So the drivers must consult this BEFORE that fallback.
#
# It must equally NOT be recorded `unknown_outcome` (that term is spec-owned and reserved for
# level 4's INDETERMINATE case) and NOT be recorded executed/complete/successful (R22).

# The status a level-3-interrupted item carries. `interrupted` is deliberately an EXISTING status in
# both drivers' vocabulary and in `runner_shutdown.KNOWN_ITEM_STATUSES`, so the ledger stays coherent
# (spec R3) and `resume` already re-queues it in recovery mode. Inventing a new status would have
# broken Phase 0's coherence check and the resume path at once.
STOPPED_DISPOSITION = "interrupted"

# The certainty vocabulary. `known` is level 3's; level 4's INDETERMINATE value is owned by Phase 4
# and deliberately not defined here.
CERTAINTY_KNOWN = "known"


def stopped_disposition(
    *,
    level: int,
    requester: str,
    last_completed_index: int | None,
    last_completed_label: str | None,
    git_state: str = "",
    events_seen: int | None = None,
    at: str = "",
) -> dict:
    """The KNOWN-certainty record for an item interrupted by a level-3 stop (spec R18).

    Records the level that interrupted it, the certainty, the last COMPLETED operation observed,
    the observed git state, and what a resume must do first - so a reader never has to guess whether
    the item broke or was deliberately stopped.

    `resume_action` is prose on purpose: the driver's existing `requeue_interrupted` already
    re-queues an `interrupted` item in recovery mode, so this describes that mechanism rather than
    inventing a second one.
    """

    return {
        "stopped_deliberately": True,
        "failure": False,
        "level": level,
        "level_name": LEVEL_NAMES.get(level, "unknown"),
        "requester": requester,
        "certainty": CERTAINTY_KNOWN,
        "last_completed_event_index": last_completed_index,
        "last_completed_event": last_completed_label,
        "events_observed": events_seen,
        "git_state": git_state,
        "resume_action": (
            "re-run this item in recovery mode; it was interrupted at an observed safe checkpoint "
            "after the operation named above, so re-read the plan and the repository state before "
            "continuing (no previously observed operation was cut mid-flight, but work the agent "
            "began after its last emitted event is unobserved and may be uncommitted)"
        ),
        "at": at,
    }


def stopped_stop_event(record: dict, *, id6: str, at: str) -> dict:
    """The ledger event for a level-3 stop, recorded as a NON-FAILURE (spec R21).

    Rides the drivers' established append-only `events.jsonl` channel, exactly as
    `deliberate_stop_event` does for levels 1-2. No new ledger substrate.
    """

    return {
        "at": at,
        "event": "deliberate-stop-at-checkpoint",
        "deliberate": True,
        "failure": False,
        "id6": id6,
        "level": record.get("level"),
        "level_name": record.get("level_name"),
        "requester": record.get("requester"),
        "certainty": record.get("certainty"),
        "last_completed_event_index": record.get("last_completed_event_index"),
        "last_completed_event": record.get("last_completed_event"),
    }


# --- level 3: the BOUNDED wait (spec R11; this phase DETECTS, Phase 5 ENFORCES) --------------------
#
# THE R10 BOUNDARY, STATED DELIBERATELY so a later reader does not "simplify" the checkpoint into a
# timeout. R10 forbids defining the SAFE CHECKPOINT by elapsed time, and nothing below does that:
# the checkpoint is still and only an observed completed event. This deadline defines the GIVE-UP
# point - the instant after which no checkpoint will be AWAITED any longer - which is a different
# question and is necessarily time-based (spec R11's bounded wind-down budget).
#
# WHY IT NEEDS ITS OWN THREAD. The drivers consume the child with a BLOCKING `for line in
# process.stdout`. When a child goes silent that iteration simply does not return, so a deadline
# check placed "after the next line arrives" would never run in the exact scenario it exists for. The
# breach detector therefore takes the out-of-band supervisor shape `StallWatchdog` already uses: a
# daemon thread observing the process independently of the read loop.
#
# WHAT THIS PHASE DELIBERATELY DOES NOT DO: escalate. Escalation spans levels 3 and 4 and spec A7
# validates it in Phase 5 (`71vjbn`), so this records ONE authoritative breach signal for Phase 5 to
# act on, and takes no action itself.

BUDGET_BREACH_EVENT = "stop-budget-breached"


def deadline_seconds_remaining(
    request: StopRequest, *, now: dt.datetime | None = None
) -> float:
    """Seconds left on `request`'s recorded wind-down deadline; <= 0 means already breached.

    Reads the deadline the durable record already carries (written by Phase 1 as
    `requested_at + budget_seconds`), so the budget is not re-derived here. An unparseable deadline
    reads as breached: failing toward "bounded" can never hang, whereas failing toward "infinite"
    could.
    """

    current = now or _utc_now()
    try:
        deadline = dt.datetime.fromisoformat(request.deadline)
    except (ValueError, TypeError):
        return 0.0
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=dt.timezone.utc)
    return (deadline - current).total_seconds()


def budget_breach_event(
    request: StopRequest,
    *,
    at: str,
    id6: str = "",
    observed_events: int | None = None,
    last_completed_index: int | None = None,
) -> dict:
    """The ledger record of a wind-down BUDGET BREACH: escalation REQUIRED, not performed.

    `escalation_required` is the single signal Phase 5 (`71vjbn`) acts on. `escalation_performed` is
    recorded explicitly False so the history cannot be misread as claiming this phase escalated
    (spec R23's never-claim-what-you-did-not-do discipline, and spec A7's placement of enforcement in
    Phase 5).
    """

    return {
        "at": at,
        "event": BUDGET_BREACH_EVENT,
        "deliberate": True,
        "failure": False,
        "id6": id6,
        "level": request.level,
        "level_name": request.level_name,
        "requester": request.requester,
        "budget_seconds": request.budget_seconds,
        "deadline": request.deadline,
        "reason": "no safe checkpoint observed before the wind-down deadline",
        "observed_events": observed_events,
        "last_completed_event_index": last_completed_index,
        "escalation_required": True,
        "escalation_to_level": LEVEL_NOW_FORCE,
        # This phase DETECTS only. Phase 5 owns the action (spec A7).
        "escalation_performed": False,
    }


class BudgetBreachWatch:
    """Out-of-band watch that RECORDS a level-3 wind-down budget breach and returns (spec R11).

    Same shape as `StallWatchdog` and for the same reason: the driver's read loop blocks, so a
    silent child can only be noticed from another thread. On breach it invokes `on_breach` ONCE and
    stops; it does NOT terminate the child and does NOT escalate, because the escalation ACTION
    belongs to Phase 5 (spec A7). Bounded by construction: the thread wakes on an interval, so it
    cannot wait indefinitely for a line that will never arrive.
    """

    def __init__(
        self,
        *,
        deadline_monotonic: float,
        on_breach: Callable[[], None],
        check_interval: float = 0.05,
        is_alive: Callable[[], bool] | None = None,
    ) -> None:
        self.deadline_monotonic = deadline_monotonic
        self._on_breach = on_breach
        # Never sleep past the deadline: with a sub-second injected budget a fixed 1s interval would
        # report the breach a second late and a bounded-time assertion would fail.
        remaining = max(0.0, deadline_monotonic - time.monotonic())
        self.check_interval = max(
            0.005, min(check_interval, remaining if remaining else check_interval)
        )
        self._is_alive = is_alive
        self._stop = threading.Event()
        self._breached = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def breached(self) -> bool:
        return self._breached.is_set()

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            if self._is_alive is not None and not self._is_alive():
                return
            if time.monotonic() >= self.deadline_monotonic:
                self._breached.set()
                with contextlib.suppress(Exception):
                    self._on_breach()
                return

    def __enter__(self) -> "BudgetBreachWatch":
        thread = threading.Thread(target=self._run, daemon=True)
        self._thread = thread
        thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
