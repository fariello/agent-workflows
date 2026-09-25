#!/usr/bin/env python3
"""ONE exclusive file lock for the whole package, replacing every raw ``fcntl.flock`` call site.

WHY THIS MODULE EXISTS. ``fcntl`` is a POSIX-only stdlib module, and six modules used to
``import fcntl`` at TOP LEVEL. On a host without it the package could not be imported at all,
so nothing downstream of that import could run - including any code whose job is to report the
limitation. This module owns the lock primitive once so no other module needs a POSIX-only
import, and it is backed by ``filelock`` rather than a hand-rolled abstraction. That choice was
deliberate: a hand-rolled Windows port has to use ``msvcrt.locking``, which locks a BYTE RANGE
from the current file position rather than the whole file, so two processes can lock DISJOINT
ranges of one file and both believe they hold an exclusive lock. That is a silent mutual-exclusion
failure, and it is the single decisive argument for taking the dependency (IPD ``y6mfgo`` F3;
DECISIONS D138 permits a justified runtime dependency).

TWO OPERATIONS, DELIBERATELY SEPARATE. They are not interchangeable and collapsing them into one
call would corrupt live state:

* :func:`acquire` HOLDS a lock this process intends to keep. It is backed by ``filelock``.
* :func:`probe_free` OBSERVES whether some OTHER process holds a lock, and changes nothing.

``filelock`` MUST NOT be used for the probe, measured rather than assumed with ``filelock``
3.29.7. Its POSIX backend opens the lock file with ``O_CREAT | O_TRUNC``, which means (a) a
SUCCESSFUL acquire truncates the file's existing content, and worse (b) a FAILED acquire
truncates it too, destroying the record of the LIVE holder that just refused us, and (c) an
acquire CREATES a lock file that was absent. All three are fatal for a probe: the drivers record
``pid=<n> started=<t>`` inside ``driver.lock`` for diagnostics, ``agy_sessions`` probes lock files
owned by a foreign application entirely, and ``runner_shutdown.lock_is_free`` documents that it
never creates the file so that probing cannot resurrect a lock that was just removed. So the
probe uses the raw primitive behind ONE guarded import, right here, and reports UNDETERMINED where
it cannot answer.

NOT RE-ENTRANT, ON PURPOSE. ``filelock`` and ``fcntl.flock`` differ here and the difference is
load-bearing. Measured with ``filelock`` 3.29.7: a second ``acquire()`` on the SAME ``FileLock``
object SUCCEEDS via an internal per-object counter, whereas a second ``flock(LOCK_EX | LOCK_NB)``
from the same process RAISES. ``runner_stop._sidecar_lock`` DEPENDS on the refusal: a signal
handler re-entering on the same thread must be REFUSED so the stop level is diverted to a
process-local slot, and a re-entrant lock would let the handler walk into the monotonic
read-modify-write mid-update and silently lose a stop level, which is exactly the R9 monotonicity
property that code exists to guarantee. :func:`acquire` therefore constructs a FRESH lock object
per call and never shares one, which was verified to refuse correctly. Note that
``thread_local=False`` does NOT fix this, because the counter is per-object and not per-thread.
Do not "optimize" this by caching lock objects per path.

BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER. Every acquisition in this package is
non-blocking except one: ``project_registry.save_registry`` acquires a bare ``LOCK_EX`` and WAITS
for the registry lock. That behavior is preserved via ``blocking=True``, and it is the ONLY
caller permitted to pass it. Adding a second blocking caller needs its own justification,
because several callers turn the already-held case into an operator-facing refusal and an
accidental block would HANG a driver rather than fail it.

A CALLER THAT GENUINELY NEEDS TO WAIT SHOULD POLL THIS NON-BLOCKING ACQUIRE, NOT PASS
``blocking=True``, and the reason is the warning directly above. ``runner_shared.integration_lock``
(runconcur-01 ``vddpml``) is the case that established this: policy B serializes two concurrent
drivers' publishes to ``main``, so it MUST wait, yet an integration runs a full test suite, which
means an unbounded wait is operationally indistinguishable from the hang this rule exists to
prevent. It therefore loops on ``acquire`` (no ``blocking``), reports progress to the operator while
waiting, expires at a stated bound, and DEFERS the work on expiry rather than failing it. The
sentence above stays TRUE - ``save_registry`` remains the only ``blocking=True`` caller - and the
waiting requirement is met without a second caller acquiring the power to hang a driver silently. A
future caller that wants an UNBOUNDED, SILENT wait is the thing still forbidden here; a bounded,
reporting, deferring wait built from the non-blocking primitive needs no exception to this rule.

PLATFORM REACH, STATED HONESTLY. :func:`acquire` works wherever ``filelock`` works.
:func:`probe_free` answers on POSIX (``fcntl.flock``) and on Windows (``msvcrt.locking`` on the
same one-byte range at offset 0 that ``filelock``'s Windows backend locks, so the two genuinely
conflict), and returns ``None`` (undetermined) anywhere else, which is the same conservative
answer the probe callers already documented: failing to prove a holder is alive is not proof that
it is dead. This module makes NO claim that the runners work on a non-POSIX host; the signal ladder
and the process-tree kill remain POSIX-only for unrelated reasons.

WINDOWS LOCKS ARE MANDATORY, NOT ADVISORY, and callers must not assume otherwise. A held byte-range
lock makes the locked range unreadable and unwritable through every OTHER handle, and the holder's
open handle refuses delete/rename of the file. So on Windows a ``pid=`` record written INSIDE a
held lock file can be read only through the holder's own descriptor; a separate reader gets
``PermissionError`` (every reader in this package already treats that as "unrecorded"). Also note
``msvcrt.locking`` locks from the CURRENT file position, and a ``dup``ed descriptor shares that
position, which is why :meth:`LockHandle.release` rewinds before unlocking.
"""

from __future__ import annotations

import contextlib
import errno
import os
import re
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import filelock

__all__ = [
    "LockBusy",
    "LockHandle",
    "acquire",
    "held",
    "probe_free",
    "release_raw",
    "posix_primitive",
    "windows_primitive",
    "pid_alive",
    "read_lock_record",
    "read_lock_record_pid",
]

PathLike = Union[str, "os.PathLike[str]", Path]

# Non-blocking is expressed as ``timeout=0`` rather than ``blocking=False`` on purpose: a zero
# timeout gives up on the first attempt with no wait, and it is supported by far older
# ``filelock`` releases than the ``blocking=`` keyword is. That keeps the declared version floor
# honest and low rather than pinned to a keyword we do not need.
_TIMEOUT_IMMEDIATE = 0.0
# A negative timeout means "wait indefinitely", which is what the one blocking caller's bare
# ``LOCK_EX`` did.
_TIMEOUT_FOREVER = -1.0


class LockBusy(BlockingIOError):
    """Another holder has the lock, so this non-blocking acquisition failed. Not an error state.

    Deliberately a ``BlockingIOError`` subclass, which makes it an ``OSError`` carrying
    ``errno.EAGAIN``. That is not cosmetic: every migrated call site already handled the
    already-held case as ``BlockingIOError``, as plain ``OSError``, or by dispatching on
    ``errno in (EACCES, EAGAIN, EWOULDBLOCK)``, and all three keep working unchanged against this
    class. It is still a DISTINCT type, so a caller that wants to tell "busy" apart from a real
    I/O failure can catch it specifically, and a permission or filesystem error is NOT reported as
    busy.
    """

    def __init__(self, path: PathLike, detail: str = "") -> None:
        self.path = Path(path)
        message = f"lock is held by another process: {self.path}"
        if detail:
            message = f"{message} ({detail})"
        super().__init__(errno.EAGAIN, message)


def posix_primitive() -> Optional[Any]:
    """Return the ``fcntl`` module, or ``None`` where this platform has no such thing.

    THE ONE guarded import in the package. It is deliberately a function rather than a module-level
    ``try: import fcntl``, so that no import-time state can go stale and a test can simulate the
    module's absence honestly by blocking the import rather than by patching a cached global.
    """

    try:
        import fcntl
    except ImportError:  # pragma: no cover - exercised only on a non-POSIX host
        return None
    return fcntl


def windows_primitive() -> Optional[Any]:
    """Return the ``msvcrt`` module on Windows, or ``None`` anywhere else.

    The probe's Windows counterpart to :func:`posix_primitive`, guarded the same way. It is only
    consulted where ``fcntl`` is absent, so a POSIX host never reaches it.
    """

    if os.name != "nt":
        return None
    try:
        import msvcrt
    except ImportError:  # pragma: no cover - a Windows build without msvcrt
        return None
    return msvcrt


def pid_alive(pid: int) -> Optional[bool]:
    """Does ``pid`` name a running process? ``True``/``False``, or ``None`` when undeterminable.

    NEVER ``os.kill(pid, 0)`` ON WINDOWS. There, ``os.kill`` with any signal other than the two
    console control events calls ``TerminateProcess``, so the "is it alive?" idiom KILLS the process
    it asks about (and a stale-lock check would terminate the live lock holder). Windows is answered
    with ``OpenProcess`` + ``GetExitCodeProcess`` instead, which only observes.

    POSIX keeps the classic classification: ``ESRCH`` is gone, ``EPERM`` is alive (it exists but is
    another user's), any other ``OSError`` is undeterminable. Caveat on Windows: a process that EXITED
    with code 259 (``STILL_ACTIVE``) reads as alive, which errs in the safe direction for a lock.
    """

    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except (OSError, OverflowError):
            return None
        return True
    try:  # pragma: no cover - exercised only on a Windows host
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        process_query_limited_information = 0x1000
        still_active = 259
        error_access_denied = 5
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            # ACCESS_DENIED: it exists but is not ours to query. Anything else (typically
            # ERROR_INVALID_PARAMETER) means no process has this id.
            return ctypes.get_last_error() == error_access_denied
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return None
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    except Exception:  # pragma: no cover - ctypes unavailable or pid out of DWORD range
        return None


#: Matches a ``pid=<n>`` record even when its FIRST byte was unreadable (see
#: :func:`read_lock_record`), so a Windows reader that sees ``id=<n>`` still recovers the pid.
LOCK_RECORD_PID_RE = re.compile(r"(?<!\w)p?id=(\d+)")


def read_lock_record(path: PathLike) -> Optional[str]:
    """The diagnostic text a holder recorded INSIDE its lock file, or ``None`` if unreadable.

    On POSIX this is simply the file's text: ``flock`` is advisory, so anyone may read it.

    On Windows the lock is MANDATORY over the one byte ``filelock`` locks (offset 0, length 1), so
    reading from offset 0 through any handle but the holder's raises ``PermissionError`` while a
    holder is live. Everything AFTER that byte stays readable, so the fallback reads the remainder.
    The first character is therefore missing from a LIVE holder's record on Windows (``pid=42``
    reads as ``id=42``); :data:`LOCK_RECORD_PID_RE` tolerates exactly that. Read-only either way:
    no ``O_CREAT``, no ``O_TRUNC``, no write.
    """

    target = Path(path)
    try:
        return target.read_text(encoding="utf-8", errors="ignore")
    except PermissionError:
        if os.name != "nt":
            return None
    except OSError:
        return None
    try:  # pragma: no cover - exercised only on a Windows host
        with open(target, "rb") as stream:
            stream.seek(1)
            return stream.read().decode("utf-8", errors="ignore")
    except OSError:  # pragma: no cover
        return None


def read_lock_record_pid(path: PathLike) -> Optional[int]:
    """The ``pid=`` a holder recorded inside ``path``, or ``None``. DIAGNOSTIC ONLY, never liveness."""

    text = read_lock_record(path)
    if not text:
        return None
    match = LOCK_RECORD_PID_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _probe_free_windows(msvcrt: Any, target: Path) -> Optional[bool]:
    """The Windows half of :func:`probe_free`: try the SAME byte ``filelock`` locks, then let go.

    ``filelock``'s Windows backend locks ONE byte at offset 0 (``msvcrt.locking`` in older releases,
    ``LockFileEx`` in newer ones; both are the same NT byte-range lock), so a non-blocking
    ``msvcrt.locking`` of byte 0 through a fresh handle conflicts with a live holder in any process,
    including this one, because Windows byte-range locks are per HANDLE. The OS drops the lock when
    the holder's handle closes, which includes process death, so acquirability stays authoritative.

    Opened with ``O_RDWR`` only: no ``O_CREAT`` and no ``O_TRUNC``, so observing a lock authors and
    destroys nothing, exactly as on POSIX.
    """

    try:
        fd = os.open(str(target), os.O_RDWR | getattr(os, "O_BINARY", 0))
    except OSError:
        return None
    try:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            if exc.errno in (
                errno.EACCES,
                errno.EAGAIN,
                getattr(errno, "EDEADLK", errno.EACCES),
                getattr(errno, "EDEADLOCK", errno.EACCES),
            ):
                return False
            return None
        # Acquired, so nothing else held it. Unlock the same byte and leave the file alone.
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return True
    except OSError:
        return None
    finally:
        os.close(fd)


class LockHandle:
    """A HELD exclusive lock, plus the little that callers legitimately need from it.

    Release is idempotent, so a caller whose ``finally`` and whose explicit shutdown path both
    release is not a double-release.
    """

    __slots__ = ("_lock", "_path", "_released")

    def __init__(self, lock: "filelock.BaseFileLock", path: Path) -> None:
        self._lock = lock
        self._path = path
        self._released = False

    @property
    def path(self) -> Path:
        """The lock file this lock is held on."""

        return self._path

    @property
    def is_held(self) -> bool:
        return not self._released and bool(getattr(self._lock, "is_locked", False))

    def fileno(self) -> Optional[int]:
        """The descriptor the lock is actually held on, or ``None`` if it cannot be determined.

        Needed because ``runner_shutdown.RunLockHandle`` proves, by inode identity, that the path
        it is about to unlink still names the very inode it locked. That check is what makes it
        impossible to delete a lock file some OTHER live process now holds, so it must compare
        against the LOCKED inode and not merely against a fresh open of the same path.

        ``filelock`` does not publish this descriptor, so it is read from its internal state,
        tolerating both the modern ``_context.lock_file_fd`` spelling and the older
        ``_lock_file_fd`` one. ``tests/test_platform_lock.py`` asserts this accessor really
        returns a usable descriptor, so a future ``filelock`` that moves the attribute fails
        LOUDLY in the suite instead of silently degrading the inode check to "unknown".
        """

        context = getattr(self._lock, "_context", None)
        fd = getattr(context, "lock_file_fd", None)
        if fd is None:
            fd = getattr(self._lock, "_lock_file_fd", None)
        return fd if isinstance(fd, int) else None

    def dup_stream(self, mode: str = "r+") -> Any:
        """A writable stream on the LOCKED descriptor, or ``None`` when it cannot be determined.

        Uses ``os.dup``, so the returned stream shares the same open file description as the lock.
        Two consequences, both wanted: ``fstat`` on it reports the locked inode, and closing it
        does NOT drop the lock, because an ``flock`` lives on the open file description and
        survives until every descriptor referring to that description is closed.
        """

        fd = self.fileno()
        if fd is None:  # pragma: no cover - only if filelock moves its internals
            return None
        return os.fdopen(os.dup(fd), mode)

    def release(self) -> None:
        """Drop the lock. Idempotent, and never raises."""

        if self._released:
            return
        self._released = True
        # REWIND FIRST. Older ``filelock`` Windows backends (e.g. 3.19) unlock with
        # ``msvcrt.locking(fd, LK_UNLCK, 1)``, which targets the byte at the CURRENT position, and a
        # ``dup_stream`` write moves that shared position. Unlocking at the wrong offset raised,
        # which leaked the descriptor AND left the lock held (measured on the Windows CI runner).
        # Harmless on POSIX, where ``flock`` ignores the file position.
        fd = self.fileno()
        if fd is not None:
            with contextlib.suppress(Exception):
                os.lseek(fd, 0, os.SEEK_SET)
        with contextlib.suppress(Exception):
            self._lock.release()

    def __enter__(self) -> "LockHandle":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


def acquire(
    path: PathLike,
    *,
    blocking: bool = False,
    timeout: Optional[float] = None,
) -> LockHandle:
    """Take ``path`` exclusively and return the held lock.

    Non-blocking by DEFAULT: it fails immediately with :class:`LockBusy` when another holder has
    the lock, and never waits. That is what fourteen of the fifteen migrated call sites did, and
    several of them convert the refusal into an operator-facing message, so a silent wait here
    would turn a clean refusal into a hung driver.

    ``blocking=True`` waits for the holder instead, preserving the ONE pre-existing blocking
    acquisition (``project_registry.save_registry``). No other caller may use it; see the module
    docstring.

    NOT RE-ENTRANT: a second acquisition from this same process fails exactly as one from another
    process would. ``runner_stop``'s signal-handler safety depends on that refusal.

    Raises :class:`LockBusy` when the lock is held (and, in blocking mode, when this thread
    already holds it, which ``filelock`` detects and reports instead of deadlocking). Any other
    ``OSError`` - a permission or filesystem failure - propagates unchanged, so a real error is
    never misreported as mere contention.
    """

    target = Path(path)
    if timeout is None:
        timeout = _TIMEOUT_FOREVER if blocking else _TIMEOUT_IMMEDIATE

    # A FRESH lock object per acquisition. This is what makes the helper non-re-entrant; sharing
    # or caching one would re-enable filelock's per-object counter. See the module docstring.
    lock = filelock.FileLock(str(target), timeout=timeout)
    try:
        lock.acquire()
    except filelock.Timeout as exc:
        raise LockBusy(target) from exc
    except RuntimeError as exc:
        # filelock raises this instead of deadlocking when a DIFFERENT live instance already holds
        # this path on the current thread, which is only reachable in blocking mode. Reporting it
        # as busy keeps it an OSError, so the blocking caller's existing error mapping applies.
        raise LockBusy(target, "already held by this thread") from exc
    return LockHandle(lock, target)


@contextlib.contextmanager
def held(
    path: PathLike,
    *,
    blocking: bool = False,
    timeout: Optional[float] = None,
) -> Iterator[LockHandle]:
    """Hold ``path`` for the duration of the block. See :func:`acquire` for the semantics."""

    handle = acquire(path, blocking=blocking, timeout=timeout)
    try:
        yield handle
    finally:
        handle.release()


def probe_free(path: PathLike) -> Optional[bool]:
    """Is ``path`` free RIGHT NOW? Observed WITHOUT creating, truncating, or modifying anything.

    ``True`` when nothing holds it (including when the file is absent, since a lock cannot be held
    on a file that does not exist), ``False`` when a live holder has it, and ``None`` when this
    platform or an OS error leaves the question unanswered.

    ``None`` is a real answer and must not be collapsed into ``True``: failing to prove that a
    holder is alive is not proof that it is dead, and callers project runs as dead only on proof.

    THIS DOES NOT GO THROUGH ``filelock``, and that is a correctness requirement rather than a
    preference. ``filelock`` opens with ``O_CREAT | O_TRUNC``, so probing through it would create
    a lock file that was deliberately removed and would BLANK the live holder's record even when
    the probe correctly fails. Measured; see the module docstring.
    """

    target = Path(path)
    if not target.exists():
        return True
    fcntl = posix_primitive()
    if fcntl is None:  # pragma: no cover - exercised only on a non-POSIX host
        msvcrt = windows_primitive()
        if msvcrt is None:
            return None
        return _probe_free_windows(msvcrt, target)
    try:
        # No O_CREAT and no O_TRUNC: observing a lock must not author or destroy content.
        fd = os.open(str(target), os.O_RDWR)
    except OSError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                return False
            return None
        # Acquired, so nothing else held it. Drop it again immediately and leave the file alone.
        fcntl.flock(fd, fcntl.LOCK_UN)
        return True
    except OSError:
        return None
    finally:
        os.close(fd)


def release_raw(stream: Any) -> None:
    """Unlock a descriptor whose lock was taken with the RAW primitive, best-effort.

    Exists only for the legacy shape where a caller took the lock itself and handed the open file
    object over to be released elsewhere. Prefer :func:`acquire` and
    :meth:`LockHandle.release`; this is the compatibility path, and it is a no-op where the POSIX
    primitive is unavailable.
    """

    fcntl = posix_primitive()
    if fcntl is None:  # pragma: no cover - exercised only on a non-POSIX host
        return
    with contextlib.suppress(Exception):
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
