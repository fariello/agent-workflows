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

TWO DISTINCT MECHANISMS LIVE HERE, and conflating them is exactly the mistake this paragraph exists
to prevent (it was made once, in this module's first version):

* :func:`writer_lock` serializes COMMITTER against COMMITTER. It stops two ``aw`` verbs from
  interleaving their commits. It does NOT protect a plain WRITER, because a peer that merely edits a
  file takes no lock and never could: requiring every file write in the repo to acquire a commit lock
  is not feasible. So the lock alone does NOT fix the data loss described above, and claiming
  otherwise was wrong.
* :func:`commit_isolated` is the actual fix for the data loss. It performs the commit in a throwaway
  DETACHED worktree, so pre-commit stashes and restores THERE and the shared tree is never touched.
  The committer therefore stops endangering writers, which is the only workable direction: the
  committer is the one party that can be made to cooperate.

HONEST LIMIT of both. A human running ``git commit`` by hand in the shared tree still stashes it, and
two writers editing the same file still clobber each other (ordinary concurrent editing, not this
bug). These remove OUR verbs as a CAUSE of the loss; they do not police other tools, so callers must
keep failing closed rather than assuming exclusivity.

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
from typing import Any, Dict, Iterator, NamedTuple, Optional

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


class IsolatedCommitResult(NamedTuple):
    """Outcome of :func:`commit_isolated`.

    ``status`` is one of ``committed``, ``nothing-to-commit``, ``hook-rejected``, ``raced``, or
    ``error``. ``commit`` is the new sha on success. ``detail`` is operator-facing.
    """

    status: str
    commit: Optional[str]
    detail: str


ISO_COMMITTED = "committed"
ISO_NOTHING = "nothing-to-commit"
ISO_HOOK_REJECTED = "hook-rejected"
ISO_RACED = "raced"
ISO_ERROR = "error"


def _git(repo_root: Path, args: list) -> tuple:
    """Delegate to the canonical git runner (kept as one definition, not a second copy)."""
    from agent_workflows.git_commit_helper import _git as _shared

    return _shared(repo_root, args)


def commit_isolated(
    repo_root: Path,
    paths: list,
    *,
    message: str,
    branch: Optional[str] = None,
) -> IsolatedCommitResult:
    """Commit ``paths`` WITHOUT letting ``pre-commit`` stash the shared working tree.

    THE DEFECT THIS ACTUALLY FIXES, which the writer lock alone does NOT. ``pre-commit`` stashes
    unstaged changes in the tree it runs in, executes the hooks, then restores the stash OVER whatever
    is on disk. Any peer WRITE during that window is destroyed. A writer lock cannot help, because the
    peer is not committing: it is merely editing a file, and requiring every file write in the repo to
    take a commit lock is not feasible. So the COMMITTER must stop endangering writers, since the
    committer is the only party that can be made to cooperate.

    HOW: snapshot HEAD into a throwaway DETACHED worktree, copy in only our paths, and run the real
    ``git commit`` (hooks and all) THERE. pre-commit then stashes and restores inside that private
    worktree, where nothing else is writing, so the shared tree is never touched. Finally advance the
    branch ref with a COMPARE-AND-SWAP.

    ALL FOUR PROPERTIES WERE MEASURED before this was written, not assumed:

    * A peer write during the window SURVIVES (the shared tree is untouched).
    * The hooks STILL RUN and STILL GATE: a deliberately failing hook rejected the commit and nothing
      landed. This is emphatically NOT ``--no-verify`` in disguise.
    * Only our paths enter the commit; a peer's dirty file is not swept in.
    * A blind ``update-ref`` WOULD discard a peer commit that landed meanwhile, so the ref update is a
      CAS (``git update-ref <ref> <new> <expected-old>``), which fails loudly on a stale expectation
      instead of overwriting. That hazard is real: it was reproduced.

    THE HONEST RESIDUE. Two writers can still clobber each other directly (that is ordinary
    concurrent editing, not this bug), and a hand-run ``git commit`` in the shared tree still stashes
    it. This removes OUR verbs as a cause of the loss; it does not police other tools.
    """
    rel = [str(p) for p in paths if str(p).strip()]
    if not rel:
        return IsolatedCommitResult(ISO_NOTHING, None, "no paths requested")

    rc, head, err = _git(repo_root, ["rev-parse", "HEAD"])
    if rc != 0:
        return IsolatedCommitResult(
            ISO_ERROR, None, f"cannot resolve HEAD: {err.strip()}"
        )
    base = head.strip()

    if branch is None:
        rc, cur, _e = _git(repo_root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
        branch = cur.strip() if rc == 0 and cur.strip() else None
    if not branch:
        return IsolatedCommitResult(
            ISO_ERROR,
            None,
            "HEAD is detached; refusing to guess a branch to advance (commit directly instead)",
        )
    ref = f"refs/heads/{branch}"

    import shutil
    import tempfile

    wt = Path(tempfile.mkdtemp(prefix=".aw-isocommit-", dir=str(repo_root.parent)))
    try:
        # `--detach` is REQUIRED: git refuses a second worktree on a branch already checked out
        # elsewhere (measured: "fatal: 'main' is already used by worktree at ..."). So we commit
        # detached and move the ref ourselves, under CAS.
        rc, _o, err = _git(
            repo_root, ["worktree", "add", "-q", "--detach", str(wt), base]
        )
        if rc != 0:
            return IsolatedCommitResult(
                ISO_ERROR, None, f"could not create isolated worktree: {err.strip()}"
            )

        # Mirror our paths (content or deletion) into the isolated worktree.
        staged_any = False
        for r in rel:
            src = repo_root / r
            dst = wt / r
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                staged_any = True
            elif dst.exists():
                dst.unlink()  # propagate a deletion
                staged_any = True
        if not staged_any:
            return IsolatedCommitResult(
                ISO_NOTHING, None, "requested paths do not exist in the working tree"
            )

        rc, _o, err = _git(wt, ["add", "--", *rel])
        if rc != 0:
            return IsolatedCommitResult(
                ISO_ERROR, None, f"git add failed in isolated worktree: {err.strip()}"
            )
        rc, out, _e = _git(wt, ["diff", "--cached", "--name-only"])
        if rc == 0 and not out.strip():
            return IsolatedCommitResult(
                ISO_NOTHING, None, "requested paths have no staged changes"
            )

        # The REAL commit, hooks included, in a worktree nothing else writes to.
        rc, out, err = _git(wt, ["commit", "-m", message, "--", *rel])
        if rc != 0:
            combined = (out + "\n" + err).strip()
            return IsolatedCommitResult(
                ISO_HOOK_REJECTED,
                None,
                f"commit rejected in isolated worktree (hooks ran): {combined}",
            )

        rc, new_head, err = _git(wt, ["rev-parse", "HEAD"])
        if rc != 0:
            return IsolatedCommitResult(
                ISO_ERROR, None, f"cannot resolve isolated commit: {err.strip()}"
            )
        new = new_head.strip()

        # CAS the branch forward. A peer commit landing since our snapshot makes this FAIL rather
        # than silently discarding their work.
        rc, _o, err = _git(repo_root, ["update-ref", ref, new, base])
        if rc != 0:
            return IsolatedCommitResult(
                ISO_RACED,
                new,
                (
                    f"another commit landed on {branch} while this one was being prepared, so the "
                    f"branch was NOT moved (the work is preserved as commit {new[:12]}; cherry-pick "
                    f"or retry). git said: {err.strip()}"
                ),
            )

        # The shared index still holds our staged copy from the caller's `git add`; drop it so the
        # tree reads clean for our paths. The file CONTENT on disk already matches the new commit.
        _git(repo_root, ["reset", "--quiet", "HEAD", "--", *rel])
        return IsolatedCommitResult(
            ISO_COMMITTED, new, f"committed {len(rel)} path(s) as {new[:12]}"
        )
    finally:
        _git(repo_root, ["worktree", "remove", "--force", str(wt)])
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        _git(repo_root, ["worktree", "prune"])


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
