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

WHAT THIS MODULE GREW INTO (recorded so the section boundaries stay legible). As authored by Phase 1
it deliberately implemented no level BEHAVIOR, registered no signal handler, and exposed no CLI verb.
Later phases of Set `runstop` added their pieces here so both drivers consult ONE mechanism
(orchestrator CID-3), each under its own clearly marked section: levels 1-2 (`1qxuke`), level 3
(`foi1b3`), level 4 (`m0z0ti`), and the TRIGGER UX (`71vjbn`) - the SIGINT ladder, the SIGTERM
handler, the out-of-band `stop` command's decision logic, the spec-R16 progress report, and the
budget-breach ESCALATION. What still does NOT live here is any reaping: the ONE shared reaper is
`runner_shutdown.clean_shutdown` (spec R5).

PLATFORM SUPPORT: the SIGNAL TRIGGERS are POSIX ONLY, stated plainly rather than aspirationally
(spec A10; orchestrator OQ-02). What changed, and what did not (IPD `y6mfgo`): this module no longer
imports `fcntl`, and neither do the drivers. The lock now comes from `platform_lock`, the one
cross-platform helper, so this module and both drivers IMPORT on a non-POSIX host, where previously
they could not load at all. That removes the import-time barrier and nothing else. The SIGINT/SIGTERM
ladder still needs POSIX signal semantics, and the process-tree kill (`os.killpg`/`getpgid`) still has
no Windows equivalent, so the honest claim remains: the signal triggers require a POSIX host, and NO
text here may promise a working Windows subset. What IS implemented for A10's second half is LOUD
failure rather than a silent no-op: `install_stop_signal_handlers` returns a per-trigger status and
`render_trigger_support` renders whatever could not be installed, for the caller to print. The Windows
process-tree kill remains owned by Set `wtiso` Phase 5 (`2c122z`); do not build a second one here
(GUIDING_PRINCIPLES P8).

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
calls this writer from SIGINT/SIGTERM handlers, a BLOCKING lock acquire is a deadlock: the lock
attaches to the open file description, so a second acquire from the same process fails or waits,
and a signal arriving while the main thread already holds the sidecar lock re-enters on the SAME
thread. Measured directly: the handler entered and then hung until a 10s timeout killed it.
`request_stop_nowait` therefore makes ONE non-blocking attempt and, on contention, records the
level in a process-local slot that the already-required polling loop drains durably at its next
checkpoint. `request_stop` likewise never issues a blocking acquire; it retries the non-blocking
acquire under a bounded deadline and fails loudly instead of hanging.

THIS DEPENDS ON THE LOCK BEING NON-RE-ENTRANT, which is why `platform_lock.acquire` guarantees it
(IPD `y6mfgo` F7). `filelock`, which backs that helper, is re-entrant PER LOCK OBJECT, so the helper
constructs a fresh object per acquisition and a same-process second acquire is refused exactly as a
second acquire from another process would be. If that ever regresses, the handler would be ALLOWED
into the read-modify-write below while the main thread is mid-update, silently losing a stop level
and breaking the R9 monotonicity guarantee this module exists to provide.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import errno
import json
import os
import signal
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Container, Iterable, Iterator, Sequence, TextIO, Tuple

from agent_workflows import platform_lock, runner_shutdown

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
    # level 4 (runstop Phase 4, `m0z0ti`): the IMMEDIATE interrupt, the INDETERMINATE record, and
    # the resume REFUSAL. Cleanliness is identical to level 3; only CERTAINTY differs.
    "CERTAINTY_INDETERMINATE",
    "FORCED_DISPOSITION",
    "FORCED_STOP_EVENT",
    "RECONCILIATION_ACTION",
    "StopNowForce",
    "ForceStopWatch",
    "forced_disposition",
    "forced_stop_event",
    "is_indeterminate",
    "indeterminate_items",
    "resume_refusal_message",
    "refused_resume_event",
    # trigger UX (runstop Phase 5, `71vjbn`): the surfaces a HUMAN actually touches. Everything
    # above only becomes reachable through these.
    "SIGINT_LADDER",
    "SIGTERM_LEVEL",
    "LEVEL_FLAGS",
    "AWAITING",
    "ESCALATION_HINT",
    "CLEANUP_IS_UNCONDITIONAL",
    "escalation_target",
    "render_request_accepted",
    "report_request",
    "install_stop_signal_handlers",
    "render_trigger_support",
    "reset_signal_ladder",
    "signal_presses",
    "run_liveness",
    "LIVENESS_LIVE",
    "LIVENESS_FINISHED",
    "LIVENESS_UNDETERMINED",
    "STOP_VERB_HELP",
    "STOP_VERB_DESCRIPTION",
    "STOP_PLATFORM_NOTE",
    "STOP_LEVEL_FLAG_HELP",
    "stop_verb_epilog",
    "add_stop_parser",
    "StopCommandResult",
    "stop_command",
    "ESCALATION_EVENT",
    "escalation_event",
    "EscalationWatch",
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
    held = None
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        try:
            # NON-BLOCKING, always. `platform_lock.acquire` defaults to non-blocking and is NOT
            # re-entrant, which this code REQUIRES: a signal handler re-entering on the same
            # thread must be REFUSED so the level is diverted to the process-local slot. A
            # re-entrant lock would let the handler walk into the monotonic read-modify-write
            # mid-update and silently lose a stop level (IPD `y6mfgo` F7).
            held = platform_lock.acquire(lock_path)
            break
        except OSError as exc:
            if isinstance(exc, platform_lock.LockBusy) or exc.errno in (
                errno.EACCES,
                errno.EAGAIN,
                errno.EWOULDBLOCK,
            ):
                if timeout <= 0 or time.monotonic() >= deadline:
                    raise _LockBusy(str(lock_path)) from exc
                time.sleep(_LOCK_RETRY_SLEEP_SECONDS)
                continue
            raise
    try:
        yield
    finally:
        held.release()


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


# --- level 4: STOP-NOW-FORCE (spec `c4gd2h` R18-R19, R21-R22, A2/A6) ------------------------------
#
# Owned by Set `runstop` Phase 4 (`m0z0ti`).
#
# CLEANLINESS IS IDENTICAL TO LEVEL 3. Spec `c4gd2h` section 3 says so in as many words: "The only
# difference between 3 and 4 is outcome CERTAINTY, not cleanliness." So level 4 runs the SAME
# `runner_shutdown.clean_shutdown` and the SAME process-group escalation. DO NOT "optimize" level 4
# into a bare `kill`/`SIGKILL`: spec R5 forbids a second reaper, and the spec describes level 4 as
# "interrupt + the reconciliation routine", never a raw kill.
#
# THE ONE DIFFERENCE, and why it is load-bearing. Level 3 waits for an OBSERVED completed event
# before cutting the turn, so it can honestly name the last completed operation. Level 4 cuts the
# turn at an UNOBSERVED point, so:
#
#   | what the driver knows after an immediate interrupt   | consequence                            |
#   |-----------------------------------------------------|----------------------------------------|
#   | the turn was cut at an unobserved point             | last completed operation is NOT knowable|
#   | the tree may hold a partial edit                   | git state must be CAPTURED, not assumed |
#   | the outcome artifact may be absent or half-written  | its presence proves nothing            |
#
# Recording anything definite would therefore be a FABRICATION, which is precisely what spec R22
# forbids and what this level exists to prevent. Hence `certainty: "indeterminate"`.
#
# THE RECONCILIATION ROUTINE IS NOT DEFINED HERE. Research `ud28vy`
# (`.aw/records/research/20260827-activework-00-ud28vy-active-work-lifecycle-and-toolset-redirect.findings.md`,
# finding 6) owns the model: "a killed `executing` is `unknown_outcome` until a deterministic check
# reconciles actually-changed paths vs frozen scope ... only then resume or roll back". The in-repo
# realization of that model is `agent_workflows/run_recovery` (`UNKNOWN_OUTCOME`,
# `detect_unknown_outcomes`, `resume` raising `UnknownOutcomeError`, `reconcile_unknown_outcome`).
# This module CONSUMES the term and the stance (record, refuse, require explicit reconciliation) and
# must NOT reimplement the algorithm (spec c4gd2h non-goal + GUIDING_PRINCIPLES P8).
#
# ------------------------------------------------------------------------------------------------
# THE STATUS REPRESENTATION, DECIDED AND RECORDED (spec R18/R19; plan E-02)
# ------------------------------------------------------------------------------------------------
# A future reader will be tempted to "normalize" the `certainty` flag below into a per-item
# `status: "unknown_outcome"`. DO NOT. Both naive options are broken, and this was VERIFIED against
# the drivers rather than reasoned about:
#
#   (i)  a NEW per-item status `unknown_outcome` makes the item INERT. `reconcile_interrupted` only
#        inspects items whose status is `running`; `requeue_interrupted` only requeues `interrupted`;
#        the dequeue only selects `queued`; and `TERMINAL_STATES` /
#        `runner_shutdown.KNOWN_ITEM_STATUSES` do not contain it, so Phase 0's R3 ledger-coherence
#        check would call the ledger incoherent. The item would never be reconciled, never refused,
#        never reported, and never run.
#   (ii) reusing `interrupted` ALONE hands the item to `requeue_interrupted`, which flips every
#        `interrupted` item straight back to `queued` with `recovery_next = True` and NO operator
#        gate. The indeterminate item would be silently re-run, violating R19.
#
# THE DECISION: carry the indeterminacy as an EXPLICIT PER-ITEM FLAG (`certainty` ==
# `CERTAINTY_INDETERMINATE`, plus the stop level) ALONGSIDE the status `interrupted`, which the
# existing state machine already understands. That keeps the ledger coherent (R3) and keeps the item
# VISIBLE to reconcile/refuse/report, while `is_indeterminate` below is the ONE predicate the gates
# branch on. The word `unknown_outcome` still appears - as the recorded DISPOSITION and the
# operator-facing vocabulary - it is simply not the per-item `status` field.

# The certainty vocabulary's INDETERMINATE value. Level 3's `CERTAINTY_KNOWN` is its sibling; the two
# are the only values, and they are what separates the two levels (spec section 0).
CERTAINTY_INDETERMINATE = "indeterminate"

# The DISPOSITION recorded for a force-interrupted item. Deliberately the same token research
# `ud28vy` and `run_recovery.UNKNOWN_OUTCOME` use, because it is the same concept; see the status
# note above for why this is a disposition/certainty field and NOT the item's `status`.
FORCED_DISPOSITION = "unknown_outcome"

# The ledger event name for a level-4 stop, on the drivers' established append-only `events.jsonl`
# channel. Distinct from level 3's `deliberate-stop-at-checkpoint` precisely so an operator (and a
# test) can tell the two levels apart in history.
FORCED_STOP_EVENT = "deliberate-stop-now-force"

# What a resume MUST do first (spec R18's "what a resume must do first", R19's refusal message).
# Prose on purpose: the ACTION belongs to research `ud28vy` / `run_recovery`, so this names that
# routine rather than describing a second one.
RECONCILIATION_ACTION = (
    "reconcile before resuming: this turn was interrupted IMMEDIATELY (level 4), at a point the "
    "driver did not observe, so its outcome is indeterminate. Inspect the recorded git state and "
    "the actually-changed paths against the plan's frozen scope (the `ud28vy` reconciliation model, "
    "implemented by `aw`'s run-recovery layer), decide whether the work landed, was partial, or "
    "never happened, and only then either resume the item explicitly or roll it back. Do NOT let a "
    "resume re-run it blindly."
)


class StopNowForce(Exception):
    """Raised to cut the current turn IMMEDIATELY for a level-4 stop (spec R7's level 4).

    THE MECHANISM, stated so it is not overstated or "simplified". Like level 3 (see
    :class:`StopAtCheckpoint`) this is a TERMINATION, because the child is a one-shot
    ``opencode run``/``agy`` subprocess with NO cooperative stop channel. Levels 3 and 4 SHARE that
    mechanism and the SAME `runner_shutdown.clean_shutdown` endpoint; they differ ONLY in WHEN it is
    issued. Level 3 waits for an observed completed event. Level 4 does not wait at all - not for a
    checkpoint, not for the next line, not for a budget.

    Raising (rather than reaping in place) is deliberate and identical to level 3's choice: it unwinds
    into the driver's existing ``except BaseException`` teardown, which already routes to the ONE
    shared reaper, so no second teardown path and no second reaper is introduced (spec R5).

    ``events_seen`` is the honest denominator: how many stream lines had been consumed when the cut
    happened. It is NOT a claim about what completed. ``last_completed_index``/``label`` are carried
    only when the driver had ALREADY observed a completed event before the request arrived, and they
    are recorded as PRIOR observations, never as "the operation that finished last".
    """

    def __init__(
        self,
        *,
        level: int = LEVEL_NOW_FORCE,
        requester: str = "",
        events_seen: int = 0,
        prior_completed_index: int | None = None,
        prior_completed_label: str | None = None,
    ) -> None:
        self.level = level
        self.requester = requester
        self.events_seen = events_seen
        self.prior_completed_index = prior_completed_index
        self.prior_completed_label = prior_completed_label
        super().__init__(
            f"level-{level} stop honored IMMEDIATELY after {events_seen} observed event(s); "
            f"outcome is indeterminate"
        )


class ForceStopWatch:
    """Out-of-band watch that notices a level-4 request IMMEDIATELY, without waiting for a line.

    WHY THIS IS NECESSARY AND NOT DECORATION (the same measured hazard Phase 3 hit with its budget
    watch). "Immediately" is only true if the driver can NOTICE the request immediately, and the
    drivers consume the child with a BLOCKING ``for line in process.stdout``. A poll placed in that
    loop only runs when the NEXT LINE ARRIVES, so on a silent or slow child a level-4 stop would wait
    an unbounded time for an event - the exact opposite of "not at a checkpoint". That silent case is
    also precisely the escalation TARGET of Phase 3's budget breach (spec A7), i.e. the case where no
    further line is coming by definition.

    So the level-4 observation takes the out-of-band supervisor shape ``StallWatchdog`` and
    ``BudgetBreachWatch`` already use: a daemon thread polling the durable record on a short interval.
    On observing level >= 4 it invokes ``on_force`` ONCE and stops. It performs no reaping itself: the
    reap is the ONE shared ``runner_shutdown.clean_shutdown`` (spec R5), reached through the driver's
    existing teardown.

    NOTE this adds no second REQUEST channel and no second reaper: it reads the same
    :func:`poll_stop` and hands off to the same shutdown routine. It is an extra OBSERVER of one
    record, which is what makes the interrupt prompt rather than line-driven.
    """

    def __init__(
        self,
        run_dir: Path | str,
        *,
        on_force: Callable[[int, str], None],
        check_interval: float = 0.05,
        is_alive: Callable[[], bool] | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self._on_force = on_force
        self.check_interval = max(0.005, check_interval)
        self._is_alive = is_alive
        self._stop = threading.Event()
        self._fired = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def fired(self) -> bool:
        return self._fired.is_set()

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            if self._is_alive is not None and not self._is_alive():
                return
            try:
                level = poll_stop(self.run_dir)
            except Exception:  # noqa: BLE001 - an observer must never crash the turn
                continue
            if level is not None and level >= LEVEL_NOW_FORCE:
                request = read_stop_request(self.run_dir)
                requester = request.requester if request is not None else "unknown"
                self._fired.set()
                with contextlib.suppress(Exception):
                    self._on_force(level, requester)
                return

    def __enter__(self) -> "ForceStopWatch":
        thread = threading.Thread(target=self._run, daemon=True)
        self._thread = thread
        thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def forced_disposition(
    *,
    level: int = LEVEL_NOW_FORCE,
    requester: str,
    git_state: str = "",
    events_seen: int | None = None,
    prior_completed_index: int | None = None,
    prior_completed_label: str | None = None,
    at: str = "",
) -> dict:
    """The INDETERMINATE record for an item cut by a level-4 stop (spec R18, R21, R22).

    Uses Phase 3's record SHAPE (`stopped_disposition`) so there is one schema and not two, with
    three deliberate differences:

    * ``certainty`` is :data:`CERTAINTY_INDETERMINATE` and ``disposition`` is
      :data:`FORCED_DISPOSITION`, so the ledger says plainly that the result is unknown.
    * ``last_completed_event``/``last_completed_event_index`` are ALWAYS ``None``. This is the point
      of the level: the driver did not observe where the turn was cut, so naming a last completed
      operation would be a fabricated field. Anything it HAD observed earlier is carried under the
      explicit ``prior_observed_*`` keys instead, which cannot be misread as "this finished last".
    * ``requires_reconciliation`` is True and ``resume_action`` names the reconciliation routine
      (spec R19), so a resume cannot treat the item as ordinarily retryable.

    ``stopped_deliberately`` is True and ``failure`` is False for spec R21: the history must show the
    OPERATOR'S INTENT, not imply a crash. ``git_state`` is the git state OBSERVED at stop time and
    must be passed by the caller; it is never inferred here.
    """

    return {
        "stopped_deliberately": True,
        "failure": False,
        "level": level,
        "level_name": LEVEL_NAMES.get(level, "unknown"),
        "requester": requester,
        "certainty": CERTAINTY_INDETERMINATE,
        "disposition": FORCED_DISPOSITION,
        "requires_reconciliation": True,
        # NEVER invented for level 4: the cut point was not observed (spec R22). Kept present and
        # explicitly None so a reader sees the absence was deliberate rather than a missing field.
        "last_completed_event_index": None,
        "last_completed_event": None,
        # What HAD been observed before the request, labelled so it cannot be mistaken for the above.
        "prior_observed_completed_index": prior_completed_index,
        "prior_observed_completed_event": prior_completed_label,
        "events_observed": events_seen,
        "git_state": git_state,
        "resume_action": RECONCILIATION_ACTION,
        "at": at,
    }


def forced_stop_event(record: dict, *, id6: str, at: str) -> dict:
    """The ledger event for a level-4 stop: DELIBERATE, non-failure, and INDETERMINATE (R21/R22).

    Rides the drivers' established append-only ``events.jsonl`` channel exactly as
    `deliberate_stop_event` (levels 1-2) and `stopped_stop_event` (level 3) do. No new substrate.

    ``deliberate: True`` is what distinguishes this from a CRASH in the history (spec R21): a crash
    is unrequested and produces the drivers' pre-existing ``interrupted-detected`` event with no
    ``deliberate`` key and no stop level, so the two are trivially separable by a reader or a test.
    """

    return {
        "at": at,
        "event": FORCED_STOP_EVENT,
        "deliberate": True,
        "failure": False,
        "id6": id6,
        "level": record.get("level"),
        "level_name": record.get("level_name"),
        "requester": record.get("requester"),
        "certainty": record.get("certainty"),
        "disposition": record.get("disposition"),
        "requires_reconciliation": True,
        "events_observed": record.get("events_observed"),
        "reconciliation_required": RECONCILIATION_ACTION,
    }


def is_indeterminate(item: Any) -> bool:
    """Is this queue item flagged as having an INDETERMINATE outcome (spec R18/R19)?

    THE ONE PREDICATE every level-4 gate branches on, so the gates cannot drift apart or disagree
    with the recorder. It reads the explicit ``certainty`` flag on the item's ``stopped`` record
    rather than the item's ``status``, for the reasons recorded in the status-representation note
    above (a bare ``unknown_outcome`` status would make the item inert).

    Fail SAFE: any shape that is not clearly a flagged record reads as False, so an ordinary item is
    never mistaken for an indeterminate one and ordinary recovery keeps working unchanged.
    """

    if not isinstance(item, dict):
        return False
    stopped = item.get("stopped")
    if not isinstance(stopped, dict):
        return False
    return stopped.get("certainty") == CERTAINTY_INDETERMINATE


def indeterminate_items(queue: Iterable[Any]) -> list[dict]:
    """Every item in the queue flagged indeterminate, in queue order."""

    return [item for item in queue if is_indeterminate(item)]


def resume_refusal_message(item: dict) -> str:
    """The operator-facing REFUSAL for a resume over an indeterminate item (spec R19, A6).

    Refusing must not be indistinguishable from an opaque error: the operator needs to know WHICH
    item, WHY, and WHAT TO DO. So the message names the item id, its indeterminate state and the stop
    level that produced it, and the reconciliation action required.
    """

    stopped = item.get("stopped") if isinstance(item, dict) else None
    stopped = stopped if isinstance(stopped, dict) else {}
    level = stopped.get("level", LEVEL_NOW_FORCE)
    return (
        f"refusing to resume {item.get('id6', '?')}: its turn was force-interrupted by a level "
        f"{level} ({LEVEL_NAMES.get(level, 'unknown')}) stop, so its outcome is "
        f"{FORCED_DISPOSITION} (certainty {CERTAINTY_INDETERMINATE}) and this run will NOT re-run it "
        f"blindly (spec c4gd2h R19). {RECONCILIATION_ACTION}"
    )


def refused_resume_event(item: dict, *, at: str) -> dict:
    """The ledger event recording that a resume REFUSED an indeterminate item (spec R19)."""

    stopped = item.get("stopped") if isinstance(item, dict) else None
    stopped = stopped if isinstance(stopped, dict) else {}
    return {
        "at": at,
        "event": "resume-refused-unknown-outcome",
        "id6": item.get("id6", ""),
        "level": stopped.get("level"),
        "certainty": CERTAINTY_INDETERMINATE,
        "disposition": FORCED_DISPOSITION,
        "requires_reconciliation": True,
        "reason": resume_refusal_message(item),
    }


# --- TRIGGER UX (spec `c4gd2h` R11-R17, A5/A7/A10) -------------------------------------------------
#
# Owned by Set `runstop` Phase 5 (`71vjbn`). Everything above this line makes four stop levels
# EXPRESSIBLE and gives each one a behavior. Nothing above makes any of them REACHABLE by a human:
# Phases 2-4 were exercised by writing the Phase-1 record directly, and the drivers install no signal
# handler of their own. This section is the whole operator-facing surface:
#
#   * the SIGINT escalation ladder 1 -> 3 -> 4 (spec R12), each press via the HANDLER-SAFE writer;
#   * SIGTERM -> level 3 (spec R13);
#   * the out-of-band `stop <run-id> --<level>` command (spec R14) and its honest error path (R17);
#   * the progress report every accepted request must print (spec R16);
#   * the wind-down BUDGET-BREACH ESCALATION that Phase 3 only RECORDED (spec R11, A7).
#
# WHY THIS LIVES HERE AND NOT IN THE DRIVERS. Orchestrator CID-3 requires both drivers to expose the
# same levels and the same `stop` verb, and the two drivers already carry byte-identical duplicates of
# other logic (`terminate_process`). So the DECISIONS (which level a press maps to, what the report
# says, how liveness is probed, what the exit code is) live once here and each driver only wires them.
#
# PLATFORM SUPPORT, STATED HONESTLY AND NOT ASPIRATIONALLY (spec A10; orchestrator OQ-02). The
# import-time barrier is GONE: this module and both drivers no longer import `fcntl`, taking the lock
# from `platform_lock` instead (IPD `y6mfgo`), so they now LOAD on a non-POSIX host. But loading is not
# supporting. The SIGINT/SIGTERM ladder needs POSIX signal semantics and the process-tree kill has no
# Windows equivalent, so this Set's honest platform claim for the TRIGGERS remains POSIX-ONLY, and no
# text in this module may promise a working Windows subset. The Windows process-tree kill is owned by
# Set `wtiso` Phase 5 (`2c122z`); building a second one here is forbidden (GUIDING_PRINCIPLES P8).
# What IS implemented for A10's second half is the LOUD failure: `install_stop_signal_handlers`
# reports each trigger it could not install rather than silently no-opping, and the caller prints it.


# Spec R12: the escalation LADDER. The Nth SIGINT requests `SIGINT_LADDER[N-1]`; further presses hold
# at the last (terminal) rung. Level 2 is deliberately absent: the spec's ladder is 1 -> 3 -> 4 and
# there is no free key position for a second between-turn level, so level 2 is reachable ONLY
# out-of-band via `stop --after-set` (spec R14). That is a decision, not an omission.
SIGINT_LADDER: Tuple[int, ...] = (LEVEL_AFTER_CALL, LEVEL_NOW, LEVEL_NOW_FORCE)

# Spec R13: a single SIGTERM is the scriptable one-shot, and it means level 3.
SIGTERM_LEVEL = LEVEL_NOW

# Spec R14/R15: the four out-of-band flags. The names describe INTERRUPTION FORCE only. None of them
# implies cleanup is optional, because cleanup never is (spec R15 forbids a flag that suggests
# otherwise, and `runner_shutdown.clean_shutdown` runs unconditionally at every level).
LEVEL_FLAGS = {
    "after_call": LEVEL_AFTER_CALL,
    "after_set": LEVEL_AFTER_SET,
    "now": LEVEL_NOW,
    "now_force": LEVEL_NOW_FORCE,
}

# The single sentence every `stop` surface repeats, so R15's honesty cannot drift between the help
# text, the module docstring, and the accepted-request report.
CLEANUP_IS_UNCONDITIONAL = (
    "These flags control only HOW FORCEFULLY the in-flight agent turn is interrupted. Cleanup is "
    "UNCONDITIONAL at every level: children are always reaped, the lock always released, the ledger "
    "always left coherent, and the working tree never silently contaminated. No flag makes cleanup "
    "optional."
)

# Spec R16: WHAT the driver is waiting for, per level. Printing "stopping" alone is a defect; the
# operator has to know which boundary is being awaited or they cannot tell a wind-down from a hang.
AWAITING = {
    LEVEL_AFTER_CALL: "the in-flight agent turn to finish; no further item will be started",
    LEVEL_AFTER_SET: "the rest of the current set's queue to finish; no next set will be started",
    LEVEL_NOW: "the current agent turn's next OBSERVED safe checkpoint",
    LEVEL_NOW_FORCE: "nothing: the current agent turn is being interrupted immediately",
}


def escalation_target(level: int) -> int | None:
    """The next level up the SIGINT ladder from `level`, or None when already terminal.

    Used for BOTH halves of spec R12/R16: the "press again to stop harder" hint, and the budget-breach
    escalation's target (spec R11/A7). One function so the two cannot disagree about what "harder"
    means.
    """

    _validate_level(level)
    for rung in SIGINT_LADDER:
        if rung > level:
            return rung
    return None


def _escalation_hint(level: int, *, command: str = "aw oc run") -> str:
    """The "how to escalate" half of spec R16's required report."""

    target = escalation_target(level)
    if target is None:
        return (
            f"this is the highest level ({level}, {LEVEL_NAMES[level]}); there is nothing harder to "
            f"escalate to (a SIGKILL bypasses this protocol entirely and is not part of it)"
        )
    return (
        f"to stop harder, press Ctrl-C again (or run `{command} stop <run-id> "
        f"--{LEVEL_NAMES[target].replace('-', '-')}`) to request level {target} "
        f"({LEVEL_NAMES[target]})"
    )


def ESCALATION_HINT(level: int, *, command: str = "aw oc run") -> str:  # noqa: N802
    """Public alias for the escalation hint (named as a constant-like accessor for the report)."""

    return _escalation_hint(level, command=command)


def render_request_accepted(
    level: int,
    *,
    requester: str = "",
    accepted: bool = True,
    command: str = "aw oc run",
) -> str:
    """The report spec R16 REQUIRES on every accepted request: level, awaited boundary, escalation.

    All three parts are mandatory. Silence during wind-down is explicitly a defect, and so is a
    message that says only "stopping": an operator who cannot see WHICH boundary is being awaited
    cannot distinguish a correct wind-down from a hang, which is the exact confusion this spec
    section exists to remove.

    A request at or below the level already in force is reported too (`accepted=False`), because a
    monotonic no-op still needs an answer - otherwise a second press looks like it was dropped.
    """

    _validate_level(level)
    verb = "accepted" if accepted else "already at or above the requested level"
    who = f" (requested by {requester})" if requester else ""
    return (
        f"stop {verb}: level {level} ({LEVEL_NAMES[level]}){who}; "
        f"waiting for {AWAITING[level]}; {_escalation_hint(level, command=command)}"
    )


def report_request(
    level: int,
    *,
    requester: str = "",
    accepted: bool = True,
    command: str = "aw oc run",
    stream: TextIO | None = None,
) -> str:
    """Print (and return) the spec-R16 report. Writes to stderr by default.

    stderr on purpose: the driver's stdout carries the child's event stream under `--raw`, and a
    control message must not be interleaved into a machine-read stream.
    """

    text = render_request_accepted(
        level, requester=requester, accepted=accepted, command=command
    )
    handle = stream if stream is not None else sys.stderr
    with contextlib.suppress(Exception):
        print(text, file=handle, flush=True)
    return text


# --- the SIGINT / SIGTERM handlers (spec R12/R13) --------------------------------------------------
#
# THE HANDLER CONTRACT, and why each clause is load-bearing rather than defensive boilerplate:
#
# 1. IT USES THE HANDLER-SAFE WRITER, never `request_stop`. Phase 1 measured both failure modes: a
#    blocking sidecar-lock acquire reached from a handler DEADLOCKS the process (the handler entered
#    and hung until a 10s timeout killed it, exit 124), and a lockless atomic write LOSES the higher
#    level in ~50% of two-writer races. `request_stop_nowait` is the one path that is neither.
# 2. IT DOES ONLY RECORD-AND-RETURN. No teardown, no reaping, no ledger write. The existing poll acts
#    on the recorded level (spec R7), which is also what keeps a handler async-signal-safe in
#    practice.
# 3. IT COUNTS PRESSES IN PROCESS-LOCAL STATE, not by reading the record back. The record's level can
#    also be raised out-of-band by `stop`, so deriving "which press was this" from the record would
#    make a concurrent out-of-band request silently consume a rung of the operator's ladder.
# 4. IT PRESERVES THE PRE-EXISTING `KeyboardInterrupt` CONTRACT. See `install_stop_signal_handlers`.

_SIGINT_PRESSES = 0
_HANDLER_RUN_DIR: Path | None = None


def reset_signal_ladder() -> None:
    """Reset the process-local SIGINT press counter (for tests and for a fresh run in-process)."""

    global _SIGINT_PRESSES, _HANDLER_RUN_DIR
    _SIGINT_PRESSES = 0
    _HANDLER_RUN_DIR = None


def signal_presses() -> int:
    """How many SIGINTs this process has observed through the installed handler."""

    return _SIGINT_PRESSES


def install_stop_signal_handlers(
    run_dir: Path | str,
    *,
    command: str = "aw oc run",
    requester: str = "",
    on_terminal: Callable[[int, str], None] | None = None,
    stream: TextIO | None = None,
) -> dict[str, str]:
    """Install the SIGINT ladder and the SIGTERM handler for `run_dir` (spec R12/R13).

    Returns a per-trigger status map (`{"SIGINT": "installed", "SIGTERM": "unsupported: ..."}`) so an
    unsupported trigger FAILS LOUDLY through the caller's report rather than silently no-opping
    (spec A10's second half). It never raises: a driver that cannot install a handler must still run.

    WHAT HAPPENS TO THE PRE-EXISTING `KeyboardInterrupt` BEHAVIOR (decided deliberately, because
    registering a SIGINT handler SUPPRESSES the default that two existing handlers depend on):

    * `main`'s ``except KeyboardInterrupt`` prints the summary table and returns 130
      (``oc_runipd`` / ``agy_runipd``), and
    * ``execute_item``'s ``except KeyboardInterrupt`` marks the in-flight item ``interrupted``,
      appends an ``ipd-interrupted`` event, re-raises, and (via ``run_queue``) reclaims lanes.

    Phases 3 and 4 depend on that item-level bookkeeping, so it is PRESERVED rather than replaced:
    the FIRST two rungs (levels 1 and 3) record a request and return, letting the cooperative poll
    stop at its proper boundary, while the TERMINAL rung (level 4) additionally raises
    ``KeyboardInterrupt`` from the handler through `on_terminal`. That keeps a third Ctrl-C behaving
    like the old single Ctrl-C did - immediate unwind, exit 130, item recorded ``interrupted`` - which
    is the behavior an operator pressing three times is asking for, and is why the exit-130 path and
    the ``ipd-interrupted`` event are still reachable.

    SIGTERM keeps its EXISTING contract too. `render_stream.install_exit_signal_handler` currently
    raises ``KeyboardInterrupt("Terminated by SIGTERM")``, which `main` maps to exit 143. Spec R13
    makes SIGTERM request level 3 instead, so this handler RECORDS level 3 and returns, letting the
    turn stop at its next observed safe checkpoint (spec A3) rather than killing the driver and
    orphaning the child, which is the defect spec section 0.1 describes.
    """

    global _HANDLER_RUN_DIR
    _HANDLER_RUN_DIR = Path(run_dir)
    status: dict[str, str] = {}

    def _record(level: int) -> None:
        result = request_stop_nowait(
            _HANDLER_RUN_DIR or Path(run_dir), level, requester
        )
        # `deferred` is not a failure: the poll performs the durable write at its next checkpoint.
        # Report the level we ASKED for either way, so the operator's press is never silent.
        report_request(
            level,
            requester=requester,
            accepted=result.accepted or result.deferred,
            command=command,
            stream=stream,
        )

    def _sigint(signum: int, frame: Any) -> None:  # noqa: ARG001 - signal handler signature
        global _SIGINT_PRESSES
        _SIGINT_PRESSES += 1
        index = min(_SIGINT_PRESSES, len(SIGINT_LADDER)) - 1
        level = SIGINT_LADDER[index]
        _record(level)
        if level == SIGINT_LADDER[-1] and on_terminal is not None:
            # The TERMINAL rung, and the only place the handler does more than record. See the
            # docstring: this is what preserves the pre-existing exit-130 path and `execute_item`'s
            # `interrupted` bookkeeping that Phases 3-4 rely on.
            on_terminal(level, requester)

    def _sigterm(signum: int, frame: Any) -> None:  # noqa: ARG001 - signal handler signature
        _record(SIGTERM_LEVEL)

    for name, handler in (("SIGINT", _sigint), ("SIGTERM", _sigterm)):
        sig = getattr(signal, name, None)
        if (
            sig is None
        ):  # pragma: no cover - exercised only on a host lacking the signal
            status[name] = f"unsupported: this platform has no {name}"
            continue
        if threading.current_thread() is not threading.main_thread():
            status[name] = (
                f"unsupported: {name} can only be installed on the main thread"
            )
            continue
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError, AttributeError, RuntimeError) as exc:
            # LOUD, not silent (spec A10): the caller prints this map.
            status[name] = f"unsupported: {exc}"
        else:
            status[name] = "installed"
    return status


def render_trigger_support(status: dict[str, str]) -> str | None:
    """Render the UNSUPPORTED triggers from `install_stop_signal_handlers`, or None when all installed.

    Spec A10 requires an unsupported trigger to fail LOUDLY rather than silently do nothing, so this
    returns text the caller prints. It deliberately names the still-available out-of-band path, since
    that is the actionable half for an operator whose signal trigger is missing.
    """

    missing = {name: why for name, why in status.items() if why != "installed"}
    if not missing:
        return None
    detail = "; ".join(f"{name}: {why}" for name, why in sorted(missing.items()))
    return (
        f"stop-trigger support is INCOMPLETE on this host ({detail}). The out-of-band "
        f"`stop <run-id> --after-call|--after-set|--now|--now-force` command is unaffected and "
        f"remains the way to request any level here. NOTE: the signal triggers require POSIX "
        f"signal semantics, so on a host without them the out-of-band command is the ONLY way to "
        f"request a stop."
    )


# --- the out-of-band `stop` command (spec R14/R17, A5) ---------------------------------------------
#
# THE THREE STATES R17 NAMES, and the PROBE each one actually has. This mattered because two of the
# three were free and the third was not:
#
#   UNKNOWN          - the driver's own `resolve_run_dir` already raises for a missing run.
#   ALREADY-STOPPING - `read_stop_request(run_dir)` is not None.
#   LIVE vs FINISHED - there is NO run-complete marker in the ledger, and `driver.lock` EXISTING is
#                      provably not liveness: the `2ouj70` review measured a stale lock file
#                      outliving its holder while the `flock` was already free. So liveness is probed
#                      by ACQUIRABILITY (`runner_shutdown.lock_is_free`, which attempts a
#                      non-blocking `flock` and never creates the file), exactly as
#                      `run_viewer.driver_holder_state` already documents. Do not "simplify" this
#                      into a `Path.exists()` check; that reintroduces the false positive.

LIVENESS_LIVE = "live"
LIVENESS_FINISHED = "finished"
LIVENESS_UNDETERMINED = "undetermined"

# The `stop` verb's HELP TEXT, declared ONCE here and installed onto both runners' own parsers by
# `add_stop_parser` below. Two byte-identical copies is what the drivers already did with
# `terminate_process`, and orchestrator CID-3 requires the two `stop` verbs to be the same verb - not
# two verbs that happen to agree today. Each level's help repeats that it controls interruption FORCE
# only (spec R15): an operator reading a single `--now-force` line must not be able to conclude that
# cleanup is skipped, because it never is.
STOP_VERB_HELP = "Request a graceful stop of a LIVE run, out-of-band (from a second terminal or a script)"

STOP_PLATFORM_NOTE = (
    "PLATFORM SUPPORT: POSIX only. The SIGINT/SIGTERM triggers require POSIX signal semantics, and "
    "the process-tree reap has no non-POSIX equivalent, so a stop is only fully supported on a POSIX "
    "host. A trigger that cannot be installed is reported loudly rather than silently ignored."
)

STOP_VERB_DESCRIPTION = (
    "Request that a live run stop, at one of four levels. The levels differ ONLY in how much "
    "in-flight work is allowed to COMPLETE first.\n\n"
    + CLEANUP_IS_UNCONDITIONAL
    + "\n\nEscalation is MONOTONIC: a request may only RAISE the level in force, never lower it, so "
    "asking again more forcefully is always honored and a weaker request afterwards cannot undo it.\n\n"
    + STOP_PLATFORM_NOTE
)

STOP_LEVEL_FLAG_HELP = {
    "--after-call": (
        "Level 1: let the in-flight agent turn FINISH, then start nothing further. Interruption "
        "force only; cleanup still runs unconditionally."
    ),
    "--after-set": (
        "Level 2: let the rest of the CURRENT set's queue finish, then stop before any next set. "
        "Interruption force only; cleanup still runs unconditionally. (Only reachable this way: the "
        "Ctrl-C ladder is 1 -> 3 -> 4, which leaves no key position for level 2.)"
    ),
    "--now": (
        "Level 3: stop the current agent turn at its next OBSERVED safe checkpoint; its outcome "
        "stays KNOWN. Interruption force only; cleanup still runs unconditionally."
    ),
    "--now-force": (
        "Level 4: interrupt the current agent turn IMMEDIATELY; its outcome becomes indeterminate "
        "and needs reconciliation before a resume. Interruption force only; cleanup still runs "
        "unconditionally."
    ),
}

_FLAG_TO_DEST = {
    "--after-call": "after_call",
    "--after-set": "after_set",
    "--now": "now",
    "--now-force": "now_force",
}


def stop_verb_epilog(command: str) -> str:
    """Worked examples for the `stop` verb's `--help`, in the caller's own command vocabulary."""

    return (
        "EXAMPLES:\n"
        f"  # Wind down after the in-flight agent turn finishes (level 1):\n"
        f"  {command} stop <run-id> --after-call\n\n"
        f"  # Finish the current SET, then stop (level 2; not reachable by any signal):\n"
        f"  {command} stop <run-id> --after-set\n\n"
        f"  # Stop the current turn at its next observed safe checkpoint (level 3):\n"
        f"  {command} stop <run-id> --now\n\n"
        f"  # Interrupt the current turn immediately; its outcome becomes indeterminate (level 4):\n"
        f"  {command} stop <run-id> --now-force\n"
    )


def add_stop_parser(sub: Any, *, command: str = "aw oc run") -> Any:
    """Declare the `stop` subcommand on `sub` (spec R14/R15). ONE declaration, both drivers.

    It is declared on the RUNNER's own parser (where `start` already lives), never on `aw`'s host
    group, because `aw oc run` / `aw agy run` forward `argparse.REMAINDER` verbatim to the runner's
    `main`. Re-declaring the flags at the `aw` layer would drift AND would bypass the implicit-start
    shim that lives in `main()` rather than `build_parser()`.

    `argparse` is imported locally so this module stays a pure-logic dependency of the drivers rather
    than acquiring a CLI import at module top.
    """

    import argparse

    stop = sub.add_parser(
        "stop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=STOP_VERB_HELP,
        description=STOP_VERB_DESCRIPTION,
        epilog=stop_verb_epilog(command),
    )
    stop.add_argument(
        "run_id", help="Run ID or state directory path of the LIVE run to stop"
    )
    stop.add_argument("--repo", default=".", help="Target Git repository root")
    # `required=True` so a bare `stop <run-id>` is a usage error rather than a silent no-op: an
    # operator who forgot the level must be told, not left believing a stop was requested.
    levels = stop.add_mutually_exclusive_group(required=True)
    for flag, dest in _FLAG_TO_DEST.items():
        levels.add_argument(
            flag,
            dest="level_flag",
            action="store_const",
            const=dest,
            help=STOP_LEVEL_FLAG_HELP[flag],
        )
    stop.set_defaults(level_flag=None)
    return stop


def run_liveness(run_dir: Path | str) -> str:
    """Is a driver LIVE on `run_dir` right now? Probed by lock ACQUIRABILITY, never by file existence.

    Returns `LIVENESS_LIVE` (a holder has the lock), `LIVENESS_FINISHED` (the lock is free or absent,
    so no driver is controlling this run), or `LIVENESS_UNDETERMINED` (the platform or an OS error
    left it unknown - reported honestly rather than guessed).
    """

    free = runner_shutdown.lock_is_free(Path(run_dir) / "driver.lock")
    if free is None:
        return LIVENESS_UNDETERMINED
    return LIVENESS_FINISHED if free else LIVENESS_LIVE


@dataclass(frozen=True)
class StopCommandResult:
    """The outcome of an out-of-band `stop`, as data so both drivers report it identically."""

    exit_code: int
    message: str
    level: int | None = None
    liveness: str = LIVENESS_UNDETERMINED
    recorded: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def stop_command(
    run_dir: Path | str | None,
    level: int | None,
    *,
    run_id: str = "",
    requester: str = "",
    command: str = "aw oc run",
    unknown_reason: str = "",
) -> StopCommandResult:
    """Request `level` out-of-band for one run, or report honestly why it could not (spec R14/R17).

    `run_dir` is None when the caller's own resolver could not find the run; `unknown_reason` then
    carries its message. That split keeps run RESOLUTION in the driver (each has its own
    `resolve_run_dir`) while the DECISION about what to do lives here once, so the two drivers cannot
    diverge on the error contract (orchestrator CID-3).

    THE HONESTY RULES, each of which is a way this could otherwise appear to succeed:

    * an UNKNOWN run exits NONZERO and mutates NOTHING - in particular it does not create the run
      directory or the stop-request file as a side effect of asking (spec A5);
    * a FINISHED run (no live driver, probed by lock acquirability) exits NONZERO saying there is no
      live run, and writes nothing: recording a request no process will ever read would look like
      success and be useless;
    * an ALREADY-STOPPING run REPORTS the level in force. A higher request escalates and exits 0; an
      equal or lower one is a monotonic no-op that exits 0 and never downgrades (spec R9).
    """

    if run_dir is None:
        return StopCommandResult(
            exit_code=2,
            message=unknown_reason
            or f"no such run: {run_id or '<unspecified>'} (nothing was created or modified)",
            liveness=LIVENESS_UNDETERMINED,
        )
    run_dir = Path(run_dir)
    if level is None:
        return StopCommandResult(
            exit_code=2,
            message=(
                "stop requires exactly one level flag: "
                "--after-call | --after-set | --now | --now-force. "
                + CLEANUP_IS_UNCONDITIONAL
            ),
        )
    _validate_level(level)

    liveness = run_liveness(run_dir)
    existing = read_stop_request(run_dir)
    if liveness == LIVENESS_FINISHED:
        # NOT a file-existence check (see the section comment): the lock is free, so no driver is
        # controlling this run and nothing would ever read a request written now.
        note = (
            f" (a stop at level {existing.level} ({existing.level_name}) is already recorded)"
            if existing is not None
            else ""
        )
        return StopCommandResult(
            exit_code=1,
            message=(
                f"no live run to stop: {run_id or run_dir.name} has no driver holding its lock"
                f"{note}; nothing was recorded"
            ),
            liveness=liveness,
        )

    try:
        result = request_stop(run_dir, level, requester or "stop-command")
    except (StopRequestError, OSError) as exc:
        return StopCommandResult(
            exit_code=2,
            message=f"could not record the stop request for {run_id or run_dir.name}: {exc}",
            level=level,
            liveness=liveness,
        )

    current = result.request
    if not result.accepted and current is not None:
        # Spec R9: a monotonic no-op. Reported as the state in force, not as a failure - the operator
        # asked for something already guaranteed.
        return StopCommandResult(
            exit_code=0,
            message=(
                f"already stopping at level {current.level} ({current.level_name}), requested by "
                f"{current.requester or 'unknown'} at {current.requested_at}; level {level} "
                f"({LEVEL_NAMES[level]}) is not higher, so the recorded level is UNCHANGED "
                f"(escalation is monotonic and never downgrades). "
                + render_request_accepted(
                    current.level, accepted=False, command=command
                )
            ),
            level=current.level,
            liveness=liveness,
            recorded=False,
        )

    effective = current.level if current is not None else level
    return StopCommandResult(
        exit_code=0,
        message=render_request_accepted(
            effective,
            requester=requester or "stop-command",
            accepted=True,
            command=command,
        ),
        level=effective,
        liveness=liveness,
        recorded=True,
    )


# --- the wind-down BUDGET-BREACH ESCALATION (spec R11, A7) -----------------------------------------
#
# Phase 3 (`foi1b3`) DETECTED a breach and recorded `escalation_required: True` with
# `escalation_performed: False`, deliberately leaving the ACTION here (spec A7). This is that action.
#
# WHY IT IS AN ESCALATION AND NOT A KILL. Raising the durable level is exactly what an operator's
# extra Ctrl-C would do, so the breach reuses the ENTIRE existing mechanism: the record's monotonic
# writer, the poll, `ForceStopWatch`, and the ONE shared `clean_shutdown`. Nothing new reaps anything.
# That is what keeps R5 (one cleanup routine) and R11 (a bounded wind-down) true at the same time: a
# hung turn cannot make a stop hang forever, and the way it is un-hung is the same path every other
# level takes.
#
# WHY THE ESCALATION IS RECORDED. Spec R11 says "with that escalation RECORDED", and R23 forbids
# claiming what was not done. So the ledger event below says which level was in force, which level was
# escalated TO, and that the escalation was actually PERFORMED - the exact field Phase 3 wrote as
# False.

ESCALATION_EVENT = "stop-escalated"


def escalation_event(
    *,
    from_level: int,
    to_level: int,
    at: str,
    reason: str,
    id6: str = "",
    requester: str = "",
) -> dict:
    """The ledger record of an escalation this process actually PERFORMED (spec R11/R23).

    `escalation_performed: True` is the deliberate counterpart of `budget_breach_event`'s False: the
    two events together show a breach being detected and then acted on, and neither one claims the
    other's work.
    """

    return {
        "at": at,
        "event": ESCALATION_EVENT,
        "deliberate": True,
        "failure": False,
        "id6": id6,
        "from_level": from_level,
        "from_level_name": LEVEL_NAMES.get(from_level, "unknown"),
        "level": to_level,
        "level_name": LEVEL_NAMES.get(to_level, "unknown"),
        "requester": requester,
        "reason": reason,
        "escalation_required": True,
        "escalation_performed": True,
    }


class EscalationWatch:
    """Out-of-band watch that ESCALATES a wind-down whose budget expired (spec R11, A7).

    Same daemon-thread shape as `BudgetBreachWatch` and `ForceStopWatch`, and for the same measured
    reason: the drivers consume the child with a BLOCKING `for line in process.stdout`, so on a turn
    that has gone quiet a deadline can only be noticed from another thread. This one differs from
    `BudgetBreachWatch` in what it does when the deadline passes - it RAISES the durable level through
    the normal monotonic writer, which the existing poll and `ForceStopWatch` then act on.

    It performs no reaping and no teardown itself. The escalated level's own machinery does that,
    through the ONE shared `runner_shutdown.clean_shutdown` (spec R5).

    IT WALKS THE WHOLE LADDER, and that is deliberate rather than incidental. A single escalation is
    NOT sufficient to satisfy R11's "a hung turn cannot make a stop hang forever": escalating a
    breached level-1 wind-down to level 3 hands the turn to a level that is itself observed FROM THE
    CHILD'S EVENT STREAM, so on a child that has gone completely silent the escalated level-3 stop
    would never be noticed either and the stop would stall at the middle rung. Only level 4 is acted
    on unconditionally out-of-band (`ForceStopWatch` polls the record, and its reap is what unblocks
    the driver's blocking read). So this watch keeps checking and escalates again when the NEW level's
    own budget expires, until level 4 is reached or the child exits.

    THE BOUND IS THEREFORE THE SUM OF THE RUNGS' BUDGETS, not one budget, and it is stated plainly so
    nobody reads a level-1 stop as bounded by level 1's budget alone: worst case 1 -> 3 -> 4 waits
    `WIND_DOWN_BUDGET_SECONDS[1] + WIND_DOWN_BUDGET_SECONDS[3]`, because each rung gets the budget the
    spec assigns it (R11 gives every level its own) and the escalated request's deadline is written by
    the same monotonic writer every other request uses. Finite, recorded, and never infinite.

    Each rung's escalation is recorded exactly once, and only while a request is actually in force: an
    expired deadline for a request that was never made is not a breach.
    """

    def __init__(
        self,
        run_dir: Path | str,
        *,
        on_escalate: Callable[[int, int, str], None] | None = None,
        check_interval: float = 0.05,
        is_alive: Callable[[], bool] | None = None,
        now: Callable[[], dt.datetime] | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self._on_escalate = on_escalate
        self.check_interval = max(0.005, check_interval)
        self._is_alive = is_alive
        self._now = now or _utc_now
        self._stop = threading.Event()
        self._escalated = threading.Event()
        self._escalations: list[Tuple[int, int]] = []
        self._thread: threading.Thread | None = None

    @property
    def escalated(self) -> bool:
        return self._escalated.is_set()

    @property
    def escalations(self) -> Tuple[Tuple[int, int], ...]:
        """Every `(from, to)` escalation this watch performed, in order."""

        return tuple(self._escalations)

    def check_once(self) -> Tuple[int, int] | None:
        """Escalate if the level in force has passed its deadline. Returns `(from, to)` or None.

        Separated from the thread body so the decision is unit-testable without timing, and so the
        drivers may also call it from a checkpoint if they want a synchronous check.
        """

        request = read_stop_request(self.run_dir)
        if request is None:
            return None
        target = escalation_target(request.level)
        if target is None:
            # Already at the terminal level: there is nothing harder to escalate to, and saying so is
            # more honest than re-recording the same level as an "escalation".
            return None
        if deadline_seconds_remaining(request, now=self._now()) > 0.0:
            return None
        reason = (
            f"wind-down budget of {request.budget_seconds}s expired at {request.deadline} without "
            f"the level-{request.level} boundary being reached"
        )
        try:
            result = request_stop(
                self.run_dir,
                target,
                f"budget-escalation (from level {request.level})",
                timeout=1.0,
            )
        except (StopRequestError, OSError, ValueError):
            return (
                None  # left for the next tick; never crash the turn over an escalation
            )
        if not result.accepted:
            return None
        self._escalated.set()
        self._escalations.append((request.level, target))
        if self._on_escalate is not None:
            with contextlib.suppress(Exception):
                self._on_escalate(request.level, target, reason)
        return (request.level, target)

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            if self._is_alive is not None and not self._is_alive():
                return
            try:
                escalated = self.check_once()
            except Exception:  # noqa: BLE001 - an observer must never crash the turn
                continue
            if escalated is not None and escalated[1] >= SIGINT_LADDER[-1]:
                # The terminal rung. `ForceStopWatch` acts on it unconditionally and out-of-band, so
                # there is nothing further this watch could escalate to; keep going only while a
                # HIGHER rung still exists (see the class docstring on why one escalation is not
                # enough).
                return

    def __enter__(self) -> "EscalationWatch":
        thread = threading.Thread(target=self._run, daemon=True)
        self._thread = thread
        thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
