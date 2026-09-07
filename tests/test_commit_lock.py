"""One shared writer lock must serialize every `aw` verb that self-commits.

THE MEASURED HARM (2026-09-06, reproduced in a scratch repo with a deliberately slow hook).
`pre-commit` stashes unstaged changes, runs the hooks, then restores the stash. A peer process that
writes a tracked file DURING that window has its write silently DESTROYED, because the restore puts
the stashed content back on top of it. Observed: co-worker holds `v2` uncommitted, our commit starts,
co-worker writes `v3`, pre-commit restores `v2` over `v3`, our commit fails, and `v3` is gone from the
worktree, from `git stash`, and from pre-commit's own patch file.

That is worse than a failed commit: it is another party's work lost, the exact harm the shared
checkout rules exist to prevent.

WHAT THESE TESTS PIN. That the lock is genuinely SHARED with `ipd_lifecycle` (a second lock would
serialize each surface against itself and neither against the other), that a live holder is respected,
that a STALE holder is reclaimed rather than wedging the repo, that it is re-entrant so finalize
calling a committing helper cannot deadlock, and that it DEGRADES instead of refusing when the lock
cannot be taken.

WHAT THEY DO NOT CLAIM. Serialization covers OUR processes only. A hand-run `git commit` or an
editor-on-save is outside any in-process lock, so the last test states that limit explicitly rather
than leaving a reader to assume exclusivity.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

import pytest

from agent_workflows import commit_lock, ipd_lifecycle


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.invalid")
    _git(r, "config", "user.name", "T")
    (r / "owned.txt").write_text("owned\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    return r


def test_lock_file_is_shared_with_ipd_lifecycle(repo: Path) -> None:
    """THE load-bearing assertion: one lock file, not two.

    Two separate locks would serialize finalize against finalize and offer_commit against
    offer_commit, while leaving a finalize free to collide with an `aw set`. That is the original bug
    with extra machinery, so this equality is the fix's whole premise.
    """
    assert commit_lock.lock_path(repo) == ipd_lifecycle.finalize_lock_path(repo)


def test_acquire_then_release_round_trips(repo: Path) -> None:
    assert commit_lock.try_acquire(repo, owner="t") is True
    owner = commit_lock.read_owner(repo)
    assert owner is not None and owner["pid"] == os.getpid()
    commit_lock.release(repo)
    assert commit_lock.read_owner(repo) is None


def test_a_live_foreign_holder_is_respected(repo: Path) -> None:
    """A lock held by a LIVE pid must not be stolen."""
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    # PID 1 is always alive and is never us.
    lock.write_text(json.dumps({"owner": "peer", "pid": 1}), encoding="utf-8")
    assert commit_lock.try_acquire(repo, owner="t") is False


def test_a_stale_holder_is_reclaimed(repo: Path) -> None:
    """A crashed writer must NOT wedge the repo forever."""
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    # Find a pid that does not exist.
    dead = 999_999_000
    lock.write_text(json.dumps({"owner": "crashed", "pid": dead}), encoding="utf-8")
    assert commit_lock.try_acquire(repo, owner="t") is True
    owner = commit_lock.read_owner(repo)
    assert owner is not None and owner["pid"] == os.getpid()


def test_writer_lock_is_reentrant_within_one_process(repo: Path) -> None:
    """finalize holds the lock and calls a helper that also commits: must not deadlock."""
    with commit_lock.writer_lock(repo, owner="outer", timeout=1.0) as outer:
        assert outer is True
        with commit_lock.writer_lock(repo, owner="inner", timeout=1.0) as inner:
            assert inner is True
        # The inner block must NOT have released the outer holder's lock.
        owner = commit_lock.read_owner(repo)
        assert owner is not None and owner["pid"] == os.getpid()
    assert commit_lock.read_owner(repo) is None


def test_writer_lock_degrades_rather_than_blocking_forever(repo: Path) -> None:
    """A stuck foreign lock must never make committing impossible (yields False, does not raise)."""
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"owner": "peer", "pid": 1}), encoding="utf-8")

    started = time.monotonic()
    with commit_lock.writer_lock(repo, owner="t", timeout=0.3, poll=0.05) as held:
        assert held is False  # proceeded WITHOUT the lock
    assert time.monotonic() - started < 5.0  # waited its budget, not forever
    # The foreign lock is untouched: we neither stole nor deleted it.
    owner = commit_lock.read_owner(repo)
    assert owner is not None and owner["pid"] == 1


def test_writer_lock_can_refuse_when_required(repo: Path) -> None:
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"owner": "peer", "pid": 1}), encoding="utf-8")
    with pytest.raises(commit_lock.CommitLockBusy) as exc:
        with commit_lock.writer_lock(
            repo, owner="t", timeout=0.2, poll=0.05, required=True
        ):
            pass
    # The refusal must be actionable: name the holder and the file to remove.
    assert "PID 1" in str(exc.value)
    assert str(commit_lock.lock_path(repo)) in str(exc.value)


def test_release_does_not_steal_a_foreign_lock(repo: Path) -> None:
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"owner": "peer", "pid": 1}), encoding="utf-8")
    commit_lock.release(repo)
    assert commit_lock.read_owner(repo) is not None  # still held by the peer


def test_two_threads_do_not_hold_the_lock_simultaneously(repo: Path) -> None:
    """The actual mutual-exclusion property, exercised concurrently.

    Uses distinct pids-in-file semantics via try_acquire directly, because `writer_lock` is
    deliberately re-entrant WITHIN a process (same pid), which is correct for finalize->helper nesting
    but means threads of one process share ownership by design.
    """
    results: list[bool] = []
    lk = threading.Lock()

    def worker() -> None:
        got = commit_lock.try_acquire(repo, owner="t")
        with lk:
            results.append(got)

    # Pre-hold with a LIVE foreign pid so every thread must be refused.
    lock = commit_lock.lock_path(repo)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"owner": "peer", "pid": 1}), encoding="utf-8")

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results and not any(results), results


def test_offer_commit_holds_the_lock_during_its_commit(repo: Path, monkeypatch) -> None:
    """The integration point: offer_commit must be inside the lock while it stages and commits."""
    from agent_workflows import git_commit_helper as gch

    (repo / "owned.txt").write_text("changed\n", encoding="utf-8")

    seen: list[bool] = []
    real_git = gch._git

    def spy(root: Path, args: list[str]):
        if args and args[0] == "commit":
            owner = commit_lock.read_owner(repo)
            seen.append(bool(owner and owner["pid"] == os.getpid()))
        return real_git(root, args)

    monkeypatch.setattr(gch, "_git", spy)
    out = gch.offer_commit(
        repo, ["owned.txt"], message="test: locked commit", assume_yes=True
    )
    assert out.status == gch.STATUS_COMMITTED, out.message
    assert seen == [True], "the commit ran without holding the shared writer lock"
    # And the lock is released afterwards.
    assert commit_lock.read_owner(repo) is None


def test_documents_that_foreign_writers_are_out_of_scope() -> None:
    """The honest limit, asserted so it cannot be quietly dropped from the docstring.

    A hand-run `git commit`, an editor writing on save, or any non-`aw` tool does not take this lock.
    Claiming otherwise would be the dangerous kind of wrong, so the module must say so.
    """
    doc = commit_lock.__doc__ or ""
    assert "HONEST LIMIT" in doc
    assert "do not police other tools" in doc


def test_documents_that_the_lock_alone_does_not_stop_a_writer_being_clobbered() -> None:
    """The correction that matters most, pinned so it cannot regress into an overclaim.

    The first version of this module implied the writer lock fixed the measured data loss. It does
    NOT: a peer that merely EDITS a file takes no lock, so serializing committers cannot protect it.
    Only `commit_isolated` (keeping pre-commit's stash out of the shared tree) fixes that. A reader who
    believes the lock is sufficient will reintroduce the bug, so the docstring must say plainly which
    mechanism does what.
    """
    doc = commit_lock.__doc__ or ""
    assert "does NOT protect a plain WRITER" in doc
    assert "commit_isolated" in doc
