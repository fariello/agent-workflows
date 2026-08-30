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
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Tuple

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
