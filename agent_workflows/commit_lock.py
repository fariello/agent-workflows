"""One repo-wide writer lock shared by EVERY ``aw`` verb that self-commits.

WHY THIS MODULE EXISTS, and what it does NOT claim.

MEASURED DATA LOSS (2026-09-06, reproduced in a scratch repo with a slow hook). ``pre-commit``
stashes unstaged changes, runs the hooks, then restores the stash. If any other process writes a
tracked file DURING that window, the restore puts the stashed content back ON TOP of that write and
the write is GONE: not in ``git stash``, not in pre-commit's patch file. Observed sequence:

1. A co-worker has ``coworker.txt`` = ``v2`` uncommitted.
2. We run ``git commit -- owned.txt``; pre-commit stashes ``v2``.
3. The co-worker writes ``v3`` while the hooks run.
4. pre-commit restores ``v2`` over ``v3`` and reports
   ``[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes``.
5. Our commit FAILS, and ``v3`` is destroyed.

That is strictly worse than a failed commit, and it is exactly the class of harm the shared-checkout
rules in ``AGENTS.md`` exist to prevent ("uncommitted changes you did not create are NOT yours").

THE FIX AND ITS HONEST LIMIT. Serializing our OWN self-committing verbs removes the agent-vs-agent
collision, which is the case that actually bites in this repo (two drivers plus interactive agents in
one checkout). It CANNOT make the race impossible: a human running ``git commit`` by hand, an editor
writing on save, or any tool outside this package is not holding this lock. The stash window belongs
to pre-commit's design. So this module narrows a real, measured window; it is not a guarantee, and
callers must keep failing closed rather than assuming exclusivity.

WHY NOT ``--no-verify``. Bypassing the hooks does avoid the stash entirely (verified), but the hooks
are the repo's leak/secret/lifecycle gates. Trading enforcement for concurrency is not a fix.

RELATIONSHIP TO ``ipd_lifecycle``'s LOCK. ``ipd_lifecycle`` already had a repo-wide
``ipd_finalize_writer.lock`` with a sound stale-PID reclaim, but it was acquired ONLY by finalize, so
``git_commit_helper.offer_commit`` (behind ``aw set``, ``aw rename``, ``aw commit``, and the runners)
was unprotected and could collide with a finalize. This module holds the SAME lock file so the two
surfaces genuinely exclude each other; a second lock would have serialized each surface against
itself and none against the other, which is the bug wearing a hat.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

# The lock file is SHARED with `ipd_lifecycle.finalize_lock_path`. Kept as a literal here rather than
# imported to avoid a module cycle (`ipd_lifecycle` -> `git_commit_helper` -> here); a test asserts
# the two paths are identical so they cannot drift apart silently.
_LOCK_RELPATH = ("locks", "ipd_finalize_writer.lock")


class CommitLockBusy(RuntimeError):
    """Raised when another LIVE process holds the writer lock and the wait budget expired."""


def _runtime_dir(repo_root: Path) -> Path:
    """The runtime state dir, resolved the same way `ipd_lifecycle` resolves it."""
    from agent_workflows import ipd_lifecycle as _life

    return _life.finalize_lock_path(repo_root).parent.parent


def lock_path(repo_root: Path) -> Path:
    """The shared writer lock path (identical to `ipd_lifecycle.finalize_lock_path`)."""
    return _runtime_dir(repo_root).joinpath(*_LOCK_RELPATH)


def _pid_alive(pid: Any) -> bool:
    """True iff ``pid`` names a live process. Mirrors `ipd_lifecycle`'s classification exactly."""
    try:
        os.kill(int(pid), 0)
    except ValueError:
        return False
    except PermissionError:
        return True  # EPERM: the process EXISTS (owned by another user), so it is alive
    except ProcessLookupError:
        return False  # ESRCH: no such process -> stale
    except OSError:
        return False
    return True


def read_owner(repo_root: Path) -> Optional[Dict[str, Any]]:
    """The lock's recorded owner payload, or None when unheld/unreadable."""
    lock = lock_path(repo_root)
    if not lock.exists():
        return None
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_lock(lock: Path, payload: Dict[str, Any]) -> None:
    lock.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(lock.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp, str(lock))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def try_acquire(repo_root: Path, *, owner: str) -> bool:
    """Take the lock if free or STALE. Returns False when a LIVE process holds it.

    A stale lock (recorded PID not alive) is RECLAIMED rather than blindly deleted, matching the
    existing finalize behavior: a crashed writer must not wedge the repo forever.
    """
    lock = lock_path(repo_root)
    data = read_owner(repo_root)
    if data is not None:
        pid = data.get("pid")
        if pid and pid != os.getpid() and _pid_alive(pid):
            return False
    _write_lock(
        lock,
        {
            "owner": owner,
            "pid": os.getpid(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        },
    )
    return True


def release(repo_root: Path) -> None:
    """Release the lock iff THIS process owns it (never steal another live owner's lock)."""
    lock = lock_path(repo_root)
    if not lock.exists():
        return
    data = read_owner(repo_root)
    try:
        if data is None or data.get("pid") == os.getpid():
            lock.unlink()
    except OSError:
        pass


@contextlib.contextmanager
def writer_lock(
    repo_root: Path,
    *,
    owner: str,
    timeout: float = 5.0,
    poll: float = 0.05,
    required: bool = False,
) -> Iterator[bool]:
    """Hold the shared writer lock for the duration of a self-committing operation.

    Yields True when the lock is HELD by this block and False when it could not be taken and
    ``required`` is False. WAITING is the point: a self-commit is short, so a peer verb briefly
    queueing behind another is strictly better than two of them interleaving inside pre-commit's
    stash window and destroying an uncommitted edit.

    ``required=False`` (the default) DEGRADES rather than refuses: if the wait budget expires we
    proceed WITHOUT the lock and yield False, so a stuck or unreclaimable lock can never make a
    commit impossible. The caller can surface that to the operator. ``required=True`` raises
    :class:`CommitLockBusy` instead, for a caller that would rather refuse than risk it.

    ON THE DEFAULT TIMEOUT, because the obvious choice is the wrong one. A self-commit holds the lock
    for well under a second, so a peer should virtually never wait long. A LONG budget is therefore
    counterproductive: it converts a fast collision into a long stall and STILL ends in the unsafe
    unserialized path when it expires. A SHORT budget is better on both counts: it absorbs the real
    case (a peer mid-commit) and surfaces an abnormal holder quickly instead of hiding it behind a
    30-second pause. Measured while building this: peer B waited a full 10s budget behind a
    deliberately stuck lock and then proceeded unserialized anyway, which is the worst of both.

    Re-entrant within one process: if we already own the lock (the common case of finalize calling a
    helper that also commits), we do NOT release it on exit, so the outer holder keeps it.
    """
    existing = read_owner(repo_root)
    already_ours = bool(existing and existing.get("pid") == os.getpid())
    if already_ours:
        # Re-entrant: someone up the stack owns it. Do not touch the file at all.
        yield True
        return

    deadline = time.monotonic() + max(0.0, timeout)
    acquired = False
    while True:
        if try_acquire(repo_root, owner=owner):
            acquired = True
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.01, poll))

    if not acquired and required:
        data = read_owner(repo_root) or {}
        raise CommitLockBusy(
            f"the shared aw writer lock is held by live PID {data.get('pid')} "
            f"(owner: {data.get('owner')}); waited {timeout:.0f}s. Wait for it to finish, or if that "
            f"process is dead remove {lock_path(repo_root)}"
        )

    try:
        yield acquired
    finally:
        if acquired:
            release(repo_root)
