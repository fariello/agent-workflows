"""A self-commit must not let ``pre-commit`` stash the SHARED tree and destroy a peer's edit.

THE MEASURED DATA LOSS (2026-09-06). ``pre-commit`` stashes unstaged changes in the tree it runs in,
executes the hooks, then restores the stash OVER whatever is on disk. A peer process that WRITES a
tracked file during that window loses the write entirely: not on disk, not in ``git stash``, not in
pre-commit's own patch file.

WHY A WRITER LOCK IS NOT THE FIX, stated here because the first attempt got this wrong. A lock
serializes COMMITTERS. The peer in the real incident was not committing, it was editing a records file
mid-review, and requiring every file write in the repo to take a commit lock is not feasible. So the
COMMITTER has to stop endangering writers: it is the only party that can be made to cooperate.

THE FIX these tests pin: perform the commit in a throwaway DETACHED worktree, so pre-commit stashes
and restores THERE, then advance the branch under a compare-and-swap.

Every test drives REAL git and REAL pre-commit hooks. Mocks would be worthless here: the bug was a
wrong belief about what pre-commit does to a working tree, and a mock encoding that same belief would
pass while the bug stayed.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from agent_workflows import commit_lock

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")

SLOW_HOOK = """\
repos:
  - repo: local
    hooks:
      - id: slow
        name: slow hook
        entry: python3 -c "import time; time.sleep(2); print('hook ran')"
        language: system
        pass_filenames: false
        always_run: true
"""

FAILING_HOOK = """\
repos:
  - repo: local
    hooks:
      - id: reject
        name: always reject
        entry: python3 -c "import sys; print('REJECTED BY HOOK'); sys.exit(1)"
        language: system
        pass_filenames: false
        always_run: true
"""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )


def _repo(tmp_path: Path, hook_config: str | None = None) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.invalid")
    _git(r, "config", "user.name", "T")
    (r / "owned.txt").write_text("owned v1\n", encoding="utf-8")
    (r / "peer.txt").write_text("peer v1\n", encoding="utf-8")
    if hook_config is not None:
        (r / ".pre-commit-config.yaml").write_text(hook_config, encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    if hook_config is not None:
        subprocess.run(
            ["pre-commit", "install"], cwd=str(r), capture_output=True, check=False
        )
    return r


def test_commits_only_the_requested_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")
    (repo / "peer.txt").write_text("peer DIRTY\n", encoding="utf-8")

    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="only ours")

    assert res.status == commit_lock.ISO_COMMITTED, res.detail
    stat = _git(repo, "show", "--stat", "--format=", "HEAD").stdout
    assert "owned.txt" in stat
    assert "peer.txt" not in stat, "a peer's dirty file was swept into our commit"
    # The peer's uncommitted edit is still there, untouched.
    assert (repo / "peer.txt").read_text(encoding="utf-8") == "peer DIRTY\n"


def test_the_commit_content_is_ours(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")
    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="content check")
    assert res.status == commit_lock.ISO_COMMITTED, res.detail
    assert _git(repo, "show", "HEAD:owned.txt").stdout == "owned v2\n"


def test_branch_advances_and_worktree_is_cleaned_up(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")

    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="advance")

    assert res.status == commit_lock.ISO_COMMITTED, res.detail
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert after != before
    assert after == res.commit
    # Still on the branch, not detached, and no stray worktrees left behind.
    assert _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() == "main"
    assert "isocommit" not in _git(repo, "worktree", "list").stdout


def test_index_is_left_clean_for_our_paths(tmp_path: Path) -> None:
    """After committing, our path must not still read as staged in the shared index."""
    repo = _repo(tmp_path)
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")
    _git(repo, "add", "--", "owned.txt")  # caller staged it, as offer_commit does

    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="index check")

    assert res.status == commit_lock.ISO_COMMITTED, res.detail
    staged = _git(repo, "diff", "--cached", "--name-only").stdout.split()
    assert "owned.txt" not in staged


def test_nothing_to_commit_when_unchanged(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="no change")
    assert res.status == commit_lock.ISO_NOTHING, res.detail


def test_propagates_a_deletion(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "owned.txt").unlink()
    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="delete it")
    assert res.status == commit_lock.ISO_COMMITTED, res.detail
    assert _git(repo, "cat-file", "-e", "HEAD:owned.txt").returncode != 0


def test_cas_refuses_when_the_branch_moved_under_us(
    tmp_path: Path, monkeypatch
) -> None:
    """A peer commit landing mid-flight must NOT be discarded (the hazard was reproduced).

    A blind `update-ref` would silently overwrite the peer's commit. The CAS must fail instead, and
    must preserve our work as a reachable commit so nothing is lost either way.
    """
    repo = _repo(tmp_path)
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")

    real_git = commit_lock._git
    peer_sha: dict[str, str] = {}

    def sneak(root: Path, args: list):
        # Land a peer commit on main right BEFORE our ref update is attempted.
        if args and args[0] == "update-ref" and "peer" not in peer_sha:
            (repo / "peer.txt").write_text("peer committed\n", encoding="utf-8")
            real_git(repo, ["add", "--", "peer.txt"])
            real_git(
                repo, ["commit", "-q", "-m", "peer landed first", "--", "peer.txt"]
            )
            peer_sha["peer"] = real_git(repo, ["rev-parse", "HEAD"])[1].strip()
        return real_git(root, args)

    monkeypatch.setattr(commit_lock, "_git", sneak)
    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="racy")

    assert res.status == commit_lock.ISO_RACED, res.detail
    # The peer's commit is still HEAD: we did not clobber it.
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == peer_sha["peer"]
    # And our work survives as a named commit the operator can recover.
    assert res.commit
    assert _git(repo, "cat-file", "-e", res.commit).returncode == 0
    assert "retry" in res.detail.lower()


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit is required")
def test_a_peer_write_during_the_hook_window_survives(tmp_path: Path) -> None:
    """THE REGRESSION TEST FOR THE ACTUAL DATA LOSS.

    With the commit running in the shared tree, pre-commit stashes the peer's `v2`, the peer writes
    `v3` while the slow hook runs, and the restore puts `v2` back over `v3`, destroying it. Committing
    in an isolated worktree must leave the shared tree alone, so `v3` survives.
    """
    repo = _repo(tmp_path, SLOW_HOOK)
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")
    (repo / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

    result: dict[str, object] = {}

    def committer() -> None:
        result["res"] = commit_lock.commit_isolated(
            repo, ["owned.txt"], message="isolated with slow hook"
        )

    t = threading.Thread(target=committer)
    t.start()
    time.sleep(1.0)  # inside the hook window
    (repo / "peer.txt").write_text("peer v3 WRITTEN DURING WINDOW\n", encoding="utf-8")
    t.join(timeout=120)
    assert not t.is_alive(), "isolated commit hung"

    res = result["res"]
    assert res.status == commit_lock.ISO_COMMITTED, res.detail  # type: ignore[union-attr]
    assert (
        (repo / "peer.txt").read_text(encoding="utf-8")
        == "peer v3 WRITTEN DURING WINDOW\n"
    ), "the peer's in-flight write was destroyed: the stash window still touches the shared tree"


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit is required")
def test_hooks_still_run_and_still_gate(tmp_path: Path) -> None:
    """Isolation must NOT be `--no-verify` in disguise: a failing hook must still block the commit."""
    repo = _repo(tmp_path, FAILING_HOOK)
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "owned.txt").write_text("owned v2\n", encoding="utf-8")

    res = commit_lock.commit_isolated(repo, ["owned.txt"], message="should be rejected")

    assert res.status == commit_lock.ISO_HOOK_REJECTED, res.detail
    assert "REJECTED BY HOOK" in res.detail
    # Nothing landed: the branch did not move.
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before
