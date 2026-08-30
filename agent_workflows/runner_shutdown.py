#!/usr/bin/env python3
"""The ONE shared clean-shutdown routine for the IPD runners (runstop Phase 0, plan `2ouj70`).

Spec `c4gd2h` requires that EVERY stop level, and crash recovery, converge on a single
unconditional cleanup. This module owns that routine so no per-level cleanup can drift
(spec R5). The requirement ids it satisfies:

- **R1** every descendant agent process of the driver is reaped (process GROUP, not just the
  direct child), so nothing is left running or reparented to init: :func:`terminate_process`
  plus the live-child registry (:func:`track_child`, :func:`live_children`).
- **R2** ``driver.lock`` is released, OBSERVABLY: the ``flock`` is dropped and the lock file is
  unlinked when it is still provably ours: :class:`RunLockHandle`.
- **R3** the run ledger is left coherent: ``state.json`` parses and every queue item carries a
  known status. This routine only OBSERVES the ledger, so it cannot corrupt it mid-write.
- **R4** partial worktree edits are never silently contaminated: the dirty paths are ENUMERATED
  and reported. They are deliberately NOT relocated (see :func:`observe_tree` for why).
- **R6** cleanup runs even when an earlier phase fails: every invariant is attempted
  best-effort and a failure is recorded, never propagated as an abort.
- **R23** the driver never claims cleanup it did not perform: :class:`ShutdownReport` records a
  per-invariant outcome that the caller reports verbatim.

Scope note (runstop Phase 0): this module adds NO stop level, flag, poll, signal handler, or CLI
verb. Phases 1-5 (`gq6m2u`, `1qxuke`, `foi1b3`, `m0z0ti`, `71vjbn`) own those and call in here.

MEASURED CORRECTION carried from the plan's Findings, so a reader does not over-claim R2: a
leftover ``driver.lock`` holding a dead PID is a COSMETIC/diagnostic residue, NOT a liveness
defect. The kernel drops an ``flock`` when its holder dies, so a stale lock FILE never blocks a
later run (verified 2026-08-29 by holding the lock, ``SIGKILL``-ing the holder, and re-acquiring
successfully). The unlink below exists for diagnostic honesty; it must not be sold as unblocking
a stuck run, and no later phase may depend on it for correctness. ``flock`` ACQUIRABILITY stays
the authoritative liveness signal, exactly as ``run_viewer.driver_holder_state`` documents.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

try:  # POSIX-only primitive; the module must stay importable without it.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts
    fcntl = None  # type: ignore[assignment]


# Per-signal grace before escalating. These are the DEFAULTS; each driver passes its own
# module-level constants explicitly so existing tests that tune them keep working.
DEFAULT_SIGINT_GRACE_SECONDS = 5.0
DEFAULT_SIGTERM_GRACE_SECONDS = 2.0

# Invariant names, used as the report's stable keys (spec R1-R4).
INVARIANT_CHILDREN = "children_reaped"
INVARIANT_LOCK = "lock_released"
INVARIANT_LEDGER = "ledger_coherent"
INVARIANT_TREE = "tree_observed"

# Every queue-item status the drivers can legitimately persist. R3 coherence means each item
# carries one of these; an unknown value means the ledger was left in an undefined state.
# `tests/test_runner_shutdown.py` asserts this set covers BOTH drivers' `TERMINAL_STATES`, so a
# driver adding a state without updating this set is caught instead of silently passing.
KNOWN_ITEM_STATUSES = frozenset(
    {
        # terminal
        "executed",
        "reviewed",
        "approved",
        "substantially-complete",
        "partial",
        "blocked",
        "dependency-blocked",
        "failed-safely",
        "not-attempted",
        "integration-blocked",
        "merge-conflict",
        # in-flight / recoverable
        "queued",
        "running",
        "interrupted",
    }
)


# --------------------------------------------------------------------------------------
# R1: one process reaper, shared by both drivers (spec R5 forbids a second implementation)
# --------------------------------------------------------------------------------------

# Live child agent processes, weakly referenced so a finished turn's Popen is collected
# normally and no unregister bookkeeping can leak. Already-exited entries are skipped, so a
# missing unregister is harmless by construction.
_LIVE_CHILDREN: "weakref.WeakSet[subprocess.Popen]" = weakref.WeakSet()


def track_child(process: subprocess.Popen) -> subprocess.Popen:
    """Record a spawned child agent process so a later clean shutdown can reap it (R1).

    Returns the process so the caller can use this inline at the spawn site. Tracking is
    weak and self-cleaning: :func:`live_children` skips anything already exited.
    """

    with contextlib.suppress(TypeError):
        _LIVE_CHILDREN.add(process)
    return process


def live_children() -> list[subprocess.Popen]:
    """Tracked child processes that are still running."""

    live: list[subprocess.Popen] = []
    for process in list(_LIVE_CHILDREN):
        with contextlib.suppress(Exception):
            if process.poll() is None:
                live.append(process)
    return live


def _close_process_streams(process: subprocess.Popen) -> None:
    for stream in (process.stdout, process.stderr, process.stdin):
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()


def terminate_process(
    process: subprocess.Popen,
    *,
    sigint_grace: float | None = None,
    sigterm_grace: float | None = None,
) -> None:
    """Reap a child agent process AND its process group without leaving orphans (spec R1).

    Escalates SIGINT -> SIGTERM -> SIGKILL, signalling the whole process group when the child
    was started in its own session (``start_new_session=True``) so grandchildren die too, and
    falling back to the single process where process groups are unavailable.

    This is the SINGLE reaper implementation for the toolkit: both drivers bind their own grace
    constants and delegate here rather than keeping a copy (spec R5, orchestrator CID-1).
    """

    sigint_wait = (
        DEFAULT_SIGINT_GRACE_SECONDS if sigint_grace is None else float(sigint_grace)
    )
    sigterm_wait = (
        DEFAULT_SIGTERM_GRACE_SECONDS if sigterm_grace is None else float(sigterm_grace)
    )

    if process.poll() is not None:
        _close_process_streams(process)
        return

    def _signal(sig: int) -> bool:
        if hasattr(os, "killpg") and hasattr(os, "getpgid") and hasattr(os, "getpgrp"):
            try:
                pgid = os.getpgid(process.pid)
                if pgid != os.getpgrp():
                    os.killpg(pgid, sig)
                    return True
            except (ProcessLookupError, OSError):
                pass
        try:
            process.send_signal(sig)
            return True
        except (ProcessLookupError, OSError):
            return False

    for sig, grace in (
        (signal.SIGINT, sigint_wait),
        (signal.SIGTERM, sigterm_wait),
    ):
        if not _signal(sig):
            break
        try:
            process.wait(timeout=grace)
            _close_process_streams(process)
            return
        except subprocess.TimeoutExpired:
            continue

    _signal(getattr(signal, "SIGKILL", signal.SIGTERM))
    with contextlib.suppress(Exception):
        process.wait(timeout=sigterm_wait)
    _close_process_streams(process)


# --------------------------------------------------------------------------------------
# R2: the run lock, released observably
# --------------------------------------------------------------------------------------


@dataclass
class RunLockHandle:
    """The driver's held ``driver.lock``: enough to release it OBSERVABLY (spec R2).

    Holds the open file object the ``flock`` sits on plus the path it was taken through, so
    :meth:`release` can drop the lock and remove the file without ever removing a lock some
    OTHER live process now holds (the inode identity check in :meth:`holds_current_path`).

    This is deliberately a HANDLE plus a release step, not a lock abstraction: acquisition stays
    in each driver's ``run_lock`` and the cross-platform ``platform_lock`` is owned elsewhere
    (`wtiso` Phase 5, `2c122z`), which this Set must not duplicate (orchestrator CID-5).
    """

    path: Path
    handle: Any
    released: bool = False
    unlinked: bool = False

    def _inode(self) -> tuple[int, int] | None:
        with contextlib.suppress(Exception):
            st = os.fstat(self.handle.fileno())
            return (st.st_dev, st.st_ino)
        return None

    def holds_current_path(self) -> bool:
        """Does :attr:`path` still name the very inode this handle locked?

        False means the file was unlinked or REPLACED between ``open()`` and ``flock()``, so the
        lock we hold is on an orphaned inode and would not exclude a driver that locks the file
        now at that path. Callers must treat that as "not locked".
        """

        mine = self._inode()
        if mine is None:
            return False
        try:
            st = os.stat(self.path)
        except OSError:
            return False
        return (st.st_dev, st.st_ino) == mine

    def release(self, unlink: bool = True) -> None:
        """Drop the ``flock``, remove the lock file when safe, and close the handle.

        Idempotent, so the shutdown routine and the ``run_lock`` context manager's own
        ``finally`` can both call it. The file is unlinked BEFORE the lock is dropped and only
        while :meth:`holds_current_path` is true, which is what makes it impossible to delete a
        lock another live process is holding: while we hold ``LOCK_EX`` on that inode nobody
        else can, and if the path names a different inode we leave it strictly alone.
        """

        if self.released:
            return
        if unlink and self.holds_current_path():
            try:
                os.unlink(self.path)
                self.unlinked = True
            except OSError:
                self.unlinked = False
        if fcntl is not None:
            with contextlib.suppress(Exception):
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        with contextlib.suppress(Exception):
            self.handle.close()
        self.released = True


def lock_is_free(lock_path: Path) -> bool | None:
    """Is ``lock_path`` free RIGHT NOW, observed without creating or modifying it?

    ``True`` when the file is absent (nothing can hold a lock on it) or present and lockable,
    ``False`` when a live holder has it, ``None`` when this platform or an OS error leaves it
    undetermined. Never creates the file, so probing cannot resurrect a lock we just removed.
    """

    if not Path(lock_path).exists():
        return True
    if fcntl is None:  # pragma: no cover - exercised only on non-POSIX hosts
        return None
    try:
        fd = os.open(str(lock_path), os.O_RDWR)
    except OSError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(fd, fcntl.LOCK_UN)
        return True
    except OSError:
        return None
    finally:
        os.close(fd)


# --------------------------------------------------------------------------------------
# R3 / R4: ledger and working-tree OBSERVATION
# --------------------------------------------------------------------------------------


def observe_ledger(run_dir: Path) -> tuple[bool, str]:
    """Is the run ledger coherent (spec R3)? Read-only; never rewrites ``state.json``.

    Coherent means the file parses and every queue item carries a status in
    :data:`KNOWN_ITEM_STATUSES`. Phase 0 deliberately does NOT record a stop LEVEL or CERTAINTY
    on an interrupted item: those fields are owned by Phases 2-4. Observation-only is also what
    guarantees this routine cannot corrupt the ledger mid-write.
    """

    state_path = Path(run_dir) / "state.json"
    if not state_path.is_file():
        return False, f"no ledger at {state_path}"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"ledger does not parse: {exc}"
    queue = state.get("queue")
    if not isinstance(queue, list):
        return False, "ledger has no queue list"
    undefined = [
        f"{item.get('id6', '?')}={item.get('status', '<missing>')}"
        for item in queue
        if not isinstance(item, dict) or item.get("status") not in KNOWN_ITEM_STATUSES
    ]
    if undefined:
        return False, "items in an undefined state: " + ", ".join(sorted(undefined))
    return True, f"{len(queue)} item(s), all in a defined state"


def observe_tree(repo: Path) -> tuple[bool, list[str], str]:
    """ENUMERATE the working tree's dirty paths, changing nothing (spec R4).

    Returns ``(observed, dirty_paths, detail)``. This is OBSERVE-AND-REPORT by design, not
    auto-quarantine: the house policy for un-owned dirty paths is REFUSE-AND-REPORT (see
    ``oc_runipd.dirty_tree_overlap`` and its caller, which refuse to integrate over a
    contaminated base), and `wtiso` Phase 5 (`2c122z`) requires never auto-stashing, resetting,
    or overwriting a dirty user main. An automatic ``git stash`` at stop time would also capture
    edits a HUMAN made in their own checkout while a run happened to be in flight, exactly the
    destructive, hard-to-reverse action GUIDING_PRINCIPLES 10 forbids. Any real relocation must
    therefore be opt-in and operator-triggered, which this child does not implement.
    """

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return False, [], f"could not observe {repo}: {exc}"
    if proc.returncode != 0:
        return False, [], f"git status failed in {repo}: {proc.stderr.strip()}"
    dirty = [line for line in proc.stdout.splitlines() if line.strip()]
    if not dirty:
        return True, [], "no dirty paths"
    return (
        True,
        dirty,
        f"{len(dirty)} dirty path(s) left exactly as found (nothing stashed, reset, or moved)",
    )


# --------------------------------------------------------------------------------------
# The report (spec R23) and the routine itself (spec R1-R6)
# --------------------------------------------------------------------------------------


@dataclass
class InvariantResult:
    """One clean-shutdown invariant: what was attempted, and what actually happened."""

    name: str
    requirement: str
    attempted: bool = False
    satisfied: bool = False
    detail: str = ""
    error: str | None = None

    def line(self) -> str:
        if not self.attempted:
            mark = "SKIPPED"
        elif self.satisfied:
            mark = "ok"
        else:
            mark = "NOT SATISFIED"
        parts = [f"{self.name} ({self.requirement}): {mark}"]
        if self.detail:
            parts.append(self.detail)
        if self.error:
            parts.append(f"error: {self.error}")
        return " - ".join(parts)


@dataclass
class ShutdownReport:
    """Per-invariant outcome of one clean shutdown (spec R23: never claim uncleaned cleanup)."""

    invariants: dict[str, InvariantResult] = field(default_factory=dict)
    dirty_paths: list[str] = field(default_factory=list)
    reaped_pids: list[int] = field(default_factory=list)

    def result(self, name: str) -> InvariantResult:
        return self.invariants[name]

    @property
    def all_satisfied(self) -> bool:
        return bool(self.invariants) and all(
            inv.satisfied for inv in self.invariants.values()
        )

    def unsatisfied(self) -> list[InvariantResult]:
        return [inv for inv in self.invariants.values() if not inv.satisfied]

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_satisfied": self.all_satisfied,
            "dirty_paths": list(self.dirty_paths),
            "reaped_pids": list(self.reaped_pids),
            "invariants": {
                name: {
                    "requirement": inv.requirement,
                    "attempted": inv.attempted,
                    "satisfied": inv.satisfied,
                    "detail": inv.detail,
                    "error": inv.error,
                }
                for name, inv in self.invariants.items()
            },
        }

    def render(self) -> str:
        """Operator-facing text. Reports every invariant, satisfied or not (spec R23)."""

        head = "clean shutdown: all invariants satisfied"
        if not self.all_satisfied:
            head = (
                "clean shutdown: "
                + ", ".join(inv.name for inv in self.unsatisfied())
                + " NOT satisfied"
            )
        lines = [head]
        lines.extend(f"  {inv.line()}" for inv in self.invariants.values())
        if self.dirty_paths:
            lines.append(
                "  working tree left untouched; dirty paths preserved in place:"
            )
            lines.extend(f"    {entry}" for entry in self.dirty_paths)
        return "\n".join(lines)


def clean_shutdown(
    process: subprocess.Popen | None = None,
    lock: RunLockHandle | None = None,
    run_dir: Path | None = None,
    repo: Path | None = None,
    *,
    extra_processes: Sequence[subprocess.Popen] = (),
) -> ShutdownReport:
    """Perform the four clean-shutdown invariants BEST-EFFORT, in order, and report each.

    Order is reap (R1) -> release lock (R2) -> observe ledger (R3) -> observe tree (R4). Every
    step is attempted even when an earlier one raises, because spec R6 requires cleanup to
    complete when the wind-down phase fails, and spec R23 forbids reporting cleanup that did not
    happen: a step that raises is recorded ``satisfied=False`` with its error rather than
    aborting the routine.

    All arguments are optional so a caller that legitimately has only some of the context (for
    example a per-turn handler with a child process but no lock) gets an honest SKIPPED entry
    instead of a fabricated success.
    """

    report = ShutdownReport()

    # R1: reap the child agent process tree.
    children = InvariantResult(INVARIANT_CHILDREN, "R1")
    report.invariants[INVARIANT_CHILDREN] = children
    try:
        targets: list[subprocess.Popen] = []
        for candidate in (process, *extra_processes, *live_children()):
            if candidate is None:
                continue
            if not any(candidate is seen for seen in targets):
                targets.append(candidate)
        children.attempted = True
        survivors: list[int] = []
        for target in targets:
            if target.poll() is not None:
                continue
            terminate_process(target)
            report.reaped_pids.append(getattr(target, "pid", -1))
            if target.poll() is None:
                survivors.append(getattr(target, "pid", -1))
        if survivors:
            children.satisfied = False
            children.detail = f"still alive after escalation: {survivors}"
        else:
            children.satisfied = True
            children.detail = (
                f"reaped {report.reaped_pids}"
                if report.reaped_pids
                else f"no live child agent process among {len(targets)} tracked"
            )
    except BaseException as exc:  # noqa: BLE001 - R6: never abort the remaining invariants
        children.satisfied = False
        children.error = f"{type(exc).__name__}: {exc}"

    # R2: release the run lock, observably.
    lock_result = InvariantResult(INVARIANT_LOCK, "R2")
    report.invariants[INVARIANT_LOCK] = lock_result
    try:
        if lock is None:
            lock_result.detail = "no run lock held by this caller"
        else:
            lock_result.attempted = True
            lock.release()
            free = lock_is_free(lock.path)
            exists = Path(lock.path).exists()
            # Our own release is authoritative for R2. ``free is False`` right after we unlinked
            # means a DIFFERENT driver already created and locked a fresh file at that path, which
            # is not our residue, so it must not be reported as a failure to release.
            lock_result.satisfied = lock.unlinked or free is not False
            lock_result.detail = (
                f"lock file {'removed' if not exists else 'left in place'}; "
                f"lock free={free}"
            )
            if free is False and not lock.unlinked:
                lock_result.detail += " (another live process holds it)"
    except BaseException as exc:  # noqa: BLE001 - R6
        lock_result.satisfied = False
        lock_result.error = f"{type(exc).__name__}: {exc}"

    # R3: the ledger must be coherent (observed, never rewritten here).
    ledger = InvariantResult(INVARIANT_LEDGER, "R3")
    report.invariants[INVARIANT_LEDGER] = ledger
    try:
        if run_dir is None:
            ledger.detail = "no run directory supplied"
        else:
            ledger.attempted = True
            ledger.satisfied, ledger.detail = observe_ledger(Path(run_dir))
    except BaseException as exc:  # noqa: BLE001 - R6
        ledger.satisfied = False
        ledger.error = f"{type(exc).__name__}: {exc}"

    # R4: enumerate the tree's dirty paths; change nothing.
    tree = InvariantResult(INVARIANT_TREE, "R4")
    report.invariants[INVARIANT_TREE] = tree
    try:
        if repo is None:
            tree.detail = "no repository supplied"
        else:
            tree.attempted = True
            tree.satisfied, dirty, tree.detail = observe_tree(Path(repo))
            report.dirty_paths = dirty
    except BaseException as exc:  # noqa: BLE001 - R6
        tree.satisfied = False
        tree.error = f"{type(exc).__name__}: {exc}"

    return report


@contextlib.contextmanager
def tracked_child(process: subprocess.Popen) -> Iterator[subprocess.Popen]:
    """Track ``process`` for the duration of a block (convenience over :func:`track_child`)."""

    track_child(process)
    try:
        yield process
    finally:
        with contextlib.suppress(KeyError):
            _LIVE_CHILDREN.discard(process)
