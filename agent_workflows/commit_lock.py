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
    """True iff ``pid`` names a live process. Mirrors `ipd_lifecycle`'s classification exactly.

    Delegates to `platform_lock.pid_alive` rather than `os.kill(pid, 0)`, because on Windows
    `os.kill` calls TerminateProcess and would KILL the lock holder it is asking about. EPERM is
    alive, ESRCH is stale, and an undeterminable answer is stale, as before.
    """
    from agent_workflows import platform_lock

    return platform_lock.pid_alive(pid) is True


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

    ``hook_fixed`` names the repo-relative paths a MUTATING hook rewrote during the (single) retry,
    and ``hook_fixed_diverged`` the subset whose SHARED-tree copy could not be reconciled with the
    committed bytes because a peer had written it meanwhile (see the write-back in
    :func:`commit_isolated`). Both DEFAULT EMPTY and are APPENDED, because this is a ``NamedTuple``
    whose positional contract existing callers rely on: a field inserted in the middle would silently
    reassign every unpack.

    NEITHER FIELD IS COSMETIC. A retry commits content the CALLER DID NOT WRITE (the hook's fix), so
    a silent absorption would hide a mutation, which is the class of harm the research README records.
    """

    status: str
    commit: Optional[str]
    detail: str
    hook_fixed: tuple = ()
    hook_fixed_diverged: tuple = ()


ISO_COMMITTED = "committed"
ISO_NOTHING = "nothing-to-commit"
ISO_HOOK_REJECTED = "hook-rejected"
ISO_RACED = "raced"
ISO_ERROR = "error"


def _git(repo_root: Path, args: list) -> tuple:
    """Delegate to the canonical git runner (kept as one definition, not a second copy)."""
    from agent_workflows.git_commit_helper import _git as _shared

    return _shared(repo_root, args)


def _content_hash(path: Path) -> Optional[str]:
    """A content hash for ``path``, or ``None`` when the path does not exist.

    THE ``None`` SENTINEL IS LOAD-BEARING, NOT DEFENSIVE. :func:`commit_isolated` deliberately
    supports a DELETION, and the FINALIZE caller really passes a path that no longer exists on disk
    (``ipd_lifecycle`` stages ``[plan_rel, dest_rel]`` and keeps ``plan_rel`` after the plan was moved
    to ``dest_rel``). Hashing such a path raises ``FileNotFoundError``, which would escape as an
    exception instead of an :class:`IsolatedCommitResult` and turn a recoverable whitespace rejection
    into a crash on the lifecycle path (measured). Absent-to-absent therefore compares EQUAL, so a
    deletion is never misread as a hook rewrite.
    """
    import hashlib

    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError):
        return None


def _in_worktree_index(wt: Path, rel_path: str) -> bool:
    """Whether ``wt``'s index still holds an entry for ``rel_path``.

    Mirrors ``git_commit_helper._in_index``: a tracked file the caller DELETED is still in the index
    (so ``git add`` correctly stages the deletion), while a path whose deletion is ALREADY staged is
    gone from it and naming it makes ``git add`` fail AND stage nothing else in the same invocation.
    """
    rc, _out, _err = _git(wt, ["ls-files", "--error-unmatch", "--", rel_path])
    return rc == 0


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Write ``payload`` to ``path`` via temp-then-rename, preserving the existing mode.

    The same discipline every other writer in this codebase uses: a crash mid-write must never leave
    a half-written artifact where a whole one was.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mode: Optional[int] = None
    try:
        mode = path.stat().st_mode
    except OSError:
        mode = None
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".aw-hookfix-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
        if mode is not None:
            os.chmod(tmp, mode & 0o7777)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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

    ONE BOUNDED RETRY WHEN A HOOK REWROTE OUR OWN PATHS, and NEVER when a hook merely refused.
    Four of this repository's pre-commit hooks (``trailing-whitespace``, ``end-of-file-fixer``,
    ``ruff --fix``, ``ruff-format``) FIX a staged file and then exit nonzero, so a single stripped
    trailing space cost a whole commit round trip. This function therefore hashes our paths INSIDE the
    isolated worktree right after the ``git add`` and re-hashes them on rejection:

    * ANY of our paths changed on disk -> the hooks REWROTE our own content. Re-``git add`` their fix
      and run the SAME commit EXACTLY ONCE more. A second rejection fails, whatever its cause: one
      retry, never a loop (measured: repeated attempts against this shape make no progress, and a
      nondeterministic hook would spin forever).
    * NOTHING changed -> a genuine REFUSAL (the leak, lifecycle and gate hooks never rewrite).
      Behavior is BYTE-FOR-BYTE what it was before the retry existed, which is what keeps the
      "a deliberately failing hook rejected the commit and nothing landed" property above true.
    * The hook's fix can erase our ENTIRE diff (the commonest shape: a whitespace-only edit). The
      re-add then stages nothing and the retry commit would exit 1 with "nothing to commit", so the
      staged set is re-probed first and an empty one returns ``nothing-to-commit`` -- the honest
      answer -- rather than a spurious ``hook-rejected``.

    THE RETRY MUST NOT LEAVE THE SHARED TREE DIRTY, which is the one hazard the retry itself creates.
    A retry commits the HOOK's bytes while the shared tree still holds ours, so the tree would read
    dirty on the path just committed, re-present the same whitespace to the same hook next time, and
    could block a later lane integration (``runner_shared.dirty_tree_overlap`` refuses when a dirty
    main path overlaps an incoming lane's changed files). So the hook-fixed bytes are written BACK to
    the shared path under a CONTENT COMPARE-AND-SWAP: only when the shared file still holds exactly
    the bytes we copied in. A peer that edited it during the window WINS, its content is never
    overwritten, and the path is reported in ``hook_fixed_diverged`` instead.

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

        # Baseline the WORKTREE copies (not `repo_root / r`: hashing the shared tree is exactly the
        # mistake that makes a hook's rewrite undetectable, since the rewrite happens in here). Taken
        # AFTER the `add`, because `shutil.copy2` above is what put our content there.
        pre: Dict[str, Optional[str]] = {r: _content_hash(wt / r) for r in rel}

        # The REAL commit, hooks included, in a worktree nothing else writes to.
        attempts = 0
        rc, out, err = _git(wt, ["commit", "-m", message, "--", *rel])
        attempts += 1
        hook_fixed: tuple = ()
        if rc != 0:
            hook_fixed = tuple(r for r in rel if _content_hash(wt / r) != pre[r])
            if not hook_fixed:
                # A genuine REFUSAL: the hook touched none of our paths. Unchanged behavior.
                combined = (out + "\n" + err).strip()
                return IsolatedCommitResult(
                    ISO_HOOK_REJECTED,
                    None,
                    f"commit rejected in isolated worktree (hooks ran): {combined}",
                )

            # A SELF-REWRITE: pick up the hook's own fix and try EXACTLY once more.
            #
            # RE-ADD ONLY THE REWRITTEN PATHS, which is both the minimal correct set and a strict
            # SUBSET of `rel`, so the shared-checkout property is preserved by construction (nothing
            # of a peer's can enter, and the private worktree holds nothing of theirs anyway).
            #
            # NAMING ALL OF `rel` HERE IS A REAL BUG, NOT A STYLE CHOICE, and it was MEASURED while
            # building this: `git add` on an ALREADY-STAGED DELETION fails "pathspec did not match any
            # files" (the path is gone from disk AND, once the deletion is staged, gone from the index
            # too), and `git add` stages NOTHING AT ALL on failure. A mixed set of one deleted path plus
            # one hook-rewritten path therefore returned `error` with the whole retry lost. That is the
            # same trap `git_commit_helper` documents at its own `add_paths` filter. A path the hook did
            # not touch needs no re-add, so excluding it is correct as well as safe.
            readd = [
                r for r in hook_fixed if (wt / r).exists() or _in_worktree_index(wt, r)
            ]
            if readd:
                rc, _o, add_err = _git(wt, ["add", "--", *readd])
                if rc != 0:
                    return IsolatedCommitResult(
                        ISO_ERROR,
                        None,
                        f"git add failed re-staging hook-fixed paths: {add_err.strip()}",
                        hook_fixed,
                    )
            # The hook's fix can erase our whole diff; committing an empty index would be a second
            # rejection reading `nothing to commit`, so answer honestly instead.
            rc, staged_out, _e = _git(wt, ["diff", "--cached", "--name-only"])
            if rc == 0 and not staged_out.strip():
                return IsolatedCommitResult(
                    ISO_NOTHING,
                    None,
                    (
                        "nothing left to commit: the hooks' own fix to "
                        f"{', '.join(hook_fixed)} erased the entire staged diff"
                    ),
                    hook_fixed,
                )
            rc, out, err = _git(wt, ["commit", "-m", message, "--", *rel])
            attempts += 1
            if rc != 0:
                combined = (out + "\n" + err).strip()
                return IsolatedCommitResult(
                    ISO_HOOK_REJECTED,
                    None,
                    (
                        f"commit rejected in isolated worktree after {attempts} attempts (the hooks "
                        f"rewrote {', '.join(hook_fixed)} and rejected it again): {combined}"
                    ),
                    hook_fixed,
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
                hook_fixed,
            )

        # RECONCILE THE SHARED TREE WITH WHAT WAS ACTUALLY COMMITTED, for the hook-fixed paths only.
        # Without this the retry leaves the shared file holding OUR bytes while the commit holds the
        # HOOK's, so the path reads ` M` right after being committed, re-presents the same whitespace
        # to the same hook next time, and can block a later integration.
        #
        # A CONTENT COMPARE-AND-SWAP, deliberately NOT a blind copy: a blind clobber is exactly what
        # the isolated-commit design removed. We write only when the shared file still holds the bytes
        # we copied in, which proves no peer wrote it during the window. A peer's content WINS.
        diverged: list = []
        for r in hook_fixed:
            fixed = _content_hash(wt / r)
            if fixed is None or fixed == pre[r]:
                continue  # nothing to write back (deleted, or unchanged after all)
            shared = repo_root / r
            if _content_hash(shared) != pre[r]:
                diverged.append(
                    r
                )  # a peer edited it meanwhile: leave THEIR bytes alone
                continue
            try:
                _atomic_write_bytes(shared, (wt / r).read_bytes())
            except OSError:
                diverged.append(r)

        # The shared index still holds our staged copy from the caller's `git add`; drop it so the
        # tree reads clean for our paths.
        #
        # THIS IS NOW CONDITIONAL, and saying so matters more than brevity: the file CONTENT on disk
        # matches the new commit EITHER because nothing rewrote it, OR because the write-back above
        # reconciled a hook-fixed path. The ONE case where it does not match is a path in
        # ``hook_fixed_diverged``: a peer wrote it during the window and their content was correctly
        # preserved, so that path legitimately still reads dirty and the caller is told which.
        _git(repo_root, ["reset", "--quiet", "HEAD", "--", *rel])
        detail = f"committed {len(rel)} path(s) as {new[:12]}"
        if hook_fixed:
            detail += f" (the hooks fixed {', '.join(hook_fixed)}; committed on a single retry)"
        if diverged:
            detail += (
                f" NOTE: {', '.join(diverged)} was changed by another writer during the commit, so "
                "the working tree keeps THEIR content and still reads dirty"
            )
        return IsolatedCommitResult(
            ISO_COMMITTED, new, detail, hook_fixed, tuple(diverged)
        )
    finally:
        _git(repo_root, ["worktree", "remove", "--force", str(wt)])
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        _git(repo_root, ["worktree", "prune"])


class WorktreeCommit(NamedTuple):
    """A coordinator-owned branch worktree in which a caller performs and commits its mutations.

    ``path`` is the worktree directory, ``branch`` the short-lived branch it is checked out on, and
    ``base`` the commit it was created at. Nothing about it is advanced on the caller's branch: the
    caller lands the work with its own ``git merge --ff-only <commit>`` and can therefore see (and
    report) a refusal instead of clobbering a peer.
    """

    path: Path
    branch: str
    base: str


COORDINATOR_WORKTREE_PREFIX = "aw/coordinator/"


@contextlib.contextmanager
def coordinator_worktree(
    repo_root: Path, *, label: str, base: Optional[str] = None
) -> Iterator[WorktreeCommit]:
    """Yield a throwaway worktree ON ITS OWN BRANCH, owned by the COORDINATOR, and clean it up.

    WHY A SIBLING OF :func:`commit_isolated` RATHER THAN A PARAMETER ON IT (plan `u23gbn` OQ-04,
    resolved by the maintainer). ``commit_isolated`` exists to commit onto the branch the operator's
    OWN checkout has checked out, and git permits only ONE worktree per branch, so it must use
    ``--detach``, which leaves it no branch to commit onto, which is why it then moves the ref itself
    under a compare-and-swap. That CAS is exactly the step a caller which wants to reconcile the
    shared tree by fast-forward must NOT have already performed (measured: after a CAS the
    ``--ff-only`` merge prints "Already up to date." and never touches the working tree, so the
    peer-protecting refusal becomes unreachable). Minting a NEW branch removes all of that: the
    one-worktree-per-branch rule is satisfied for free, the commit is an ordinary commit, and the
    branch advance becomes the CALLER's single ``git merge --ff-only``.

    ``commit_isolated`` IS DELIBERATELY LEFT UNTOUCHED. It backs ``git_commit_helper.offer_commit``,
    the one shared self-commit path behind ``aw set``/``aw rename``/``aw commit``/``aw archive``/
    ``aw specs``/``work_cmd`` and the runners, which ``AGENTS.md`` names as immune by construction to
    sweeping a co-worker's work into a commit. Teaching it a caller-supplied worktree plus a
    no-advance mode would put that guarantee behind a combination no existing caller exercises.

    THE MUTATION HAPPENS HERE, NOT IN THE SHARED TREE, which is the whole point: unlike
    ``commit_isolated`` this helper copies NOTHING in. The caller performs its edits and its
    relocation inside ``path`` and commits there. So a caller must NOT assume the shared tree's
    uncommitted content is present; mirror in whatever it needs first (see
    ``ipd_lifecycle._finalize_transaction``, which mirrors the plan's CURRENT bytes so an executing
    agent's uncommitted evidence edits still ride the lifecycle commit, as they do today).

    CLEANUP is unconditional and removes the worktree AND the branch. That is safe here BECAUSE the
    caller has already landed (or deliberately abandoned) the commit: a landed commit is reachable
    from the caller's branch and survives the branch deletion, while an unlanded one is intentionally
    discarded. Do not use this helper to hold work across invocations.
    """
    import shutil
    import tempfile

    rc, head, err = _git(repo_root, ["rev-parse", "HEAD"])
    if rc != 0:
        raise RuntimeError(
            f"cannot resolve HEAD for a coordinator worktree: {err.strip()}"
        )
    base_sha = (base or head).strip()

    # A unique branch per invocation: two retirements (or a retirement and a finalize) can be in
    # flight in one checkout, and a shared branch name would make the second `worktree add` fail.
    suffix = f"{os.getpid()}-{int(time.time() * 1000) % 1_000_000}"
    branch = f"{COORDINATOR_WORKTREE_PREFIX}{label}-{suffix}"
    wt = Path(tempfile.mkdtemp(prefix=".aw-coordinator-", dir=str(repo_root.parent)))
    created_branch = False
    try:
        rc, _o, err = _git(
            repo_root, ["worktree", "add", "-q", "-b", branch, str(wt), base_sha]
        )
        if rc != 0:
            raise RuntimeError(
                f"could not create the coordinator worktree on {branch}: {err.strip()}"
            )
        created_branch = True
        yield WorktreeCommit(path=wt, branch=branch, base=base_sha)
    finally:
        _git(repo_root, ["worktree", "remove", "--force", str(wt)])
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        _git(repo_root, ["worktree", "prune"])
        if created_branch:
            _git(repo_root, ["branch", "-D", branch])


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
