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


# ==================================================================================================
# `coordinator_worktree`: the SIBLING for a caller that MUTATES in the worktree (plan `u23gbn`)
# ==================================================================================================
#
# WHY A SIBLING AND NOT A PARAMETER. `commit_isolated`'s copy direction is SHARED -> WORKTREE, so a
# mutation performed in a different worktree is invisible to it (measured: it returns
# `error` / "pathspec did not match any files"), and it advances the ref ITSELF under a CAS, which is
# precisely the step a caller reconciling by fast-forward must NOT have already taken. Extending it
# would put `offer_commit`'s documented safety guarantee behind a parameter combination no existing
# caller exercises, so `commit_isolated` is left untouched and every test above still pins it.


def test_the_coordinator_worktree_is_on_its_own_branch_at_the_requested_base(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        assert coord.base == base
        assert coord.branch.startswith(commit_lock.COORDINATOR_WORKTREE_PREFIX)
        # It is a real checkout, ON A BRANCH (not detached), at the base commit.
        assert (coord.path / "owned.txt").read_text(encoding="utf-8") == "owned v1\n"
        assert (
            _git(coord.path, "symbolic-ref", "--short", "HEAD").stdout.strip()
            == coord.branch
        )
        assert _git(coord.path, "rev-parse", "HEAD").stdout.strip() == base
        # The shared checkout is still on its own branch and has NOT moved.
        assert _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() == "main"
        assert _git(repo, "rev-parse", "HEAD").stdout.strip() == base


def test_a_commit_in_the_coordinator_worktree_does_NOT_advance_the_shared_branch(
    tmp_path: Path,
) -> None:
    """The whole point: the CALLER lands it, so the caller can see (and report) a refusal."""
    repo = _repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        (coord.path / "owned.txt").write_text("owned v2\n", encoding="utf-8")
        _git(coord.path, "add", "--", "owned.txt")
        _git(coord.path, "commit", "-q", "-m", "in the worktree")
        landed = _git(coord.path, "rev-parse", "HEAD").stdout.strip()
        assert landed != base
        # NOT advanced, and the shared working tree still holds the old content.
        assert _git(repo, "rev-parse", "HEAD").stdout.strip() == base
        assert (repo / "owned.txt").read_text(encoding="utf-8") == "owned v1\n"
        # The caller lands it, in ONE step that moves the ref and the tree together.
        merged = _git(repo, "merge", "--ff-only", landed)
        assert merged.returncode == 0, merged.stderr
        assert "Fast-forward" in merged.stdout
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == landed
    assert (repo / "owned.txt").read_text(encoding="utf-8") == "owned v2\n"
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


def test_the_worktree_and_its_branch_are_cleaned_up_but_a_landed_commit_survives(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        (coord.path / "owned.txt").write_text("owned v2\n", encoding="utf-8")
        _git(coord.path, "add", "--", "owned.txt")
        _git(coord.path, "commit", "-q", "-m", "landed")
        landed = _git(coord.path, "rev-parse", "HEAD").stdout.strip()
        _git(repo, "merge", "--ff-only", landed)
        wt_path = coord.path
        branch = coord.branch
    # Worktree gone, branch gone, path gone; the landed commit is still reachable from main.
    assert "aw-coordinator-" not in _git(repo, "worktree", "list").stdout
    assert branch not in _git(repo, "branch", "--list").stdout
    assert not wt_path.exists()
    assert _git(repo, "merge-base", "--is-ancestor", landed, "HEAD").returncode == 0


def test_cleanup_happens_even_when_the_caller_raises(tmp_path: Path) -> None:
    """A failed transaction must not leak a worktree or a branch that claims a path."""
    repo = _repo(tmp_path)

    class Boom(RuntimeError):
        pass

    seen: dict[str, object] = {}
    with pytest.raises(Boom):
        with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
            seen["path"] = coord.path
            seen["branch"] = coord.branch
            raise Boom("the caller failed mid-transaction")

    assert "aw-coordinator-" not in _git(repo, "worktree", "list").stdout
    assert str(seen["branch"]) not in _git(repo, "branch", "--list").stdout
    assert not Path(str(seen["path"])).exists()


def test_two_coordinator_worktrees_can_be_live_at_once(tmp_path: Path) -> None:
    """Git allows only ONE worktree per branch, so a shared branch name would break the second.

    That is the exact constraint that forces `commit_isolated` to use `--detach`; minting a unique
    branch per invocation is what removes it.
    """
    repo = _repo(tmp_path)
    with commit_lock.coordinator_worktree(repo, label="aaa111") as first:
        with commit_lock.coordinator_worktree(repo, label="bbb222") as second:
            assert first.branch != second.branch
            assert first.path != second.path
            assert (
                _git(first.path, "symbolic-ref", "--short", "HEAD").stdout.strip()
                == first.branch
            )
            assert (
                _git(second.path, "symbolic-ref", "--short", "HEAD").stdout.strip()
                == second.branch
            )


def test_it_copies_NOTHING_in_so_the_caller_owns_what_the_commit_contains(
    tmp_path: Path,
) -> None:
    """Unlike `commit_isolated`, this helper mirrors no path: the shared tree's dirt is not present.

    Stated as a test because it is the one behavioral difference a caller MUST know: a caller that
    needs the shared tree's uncommitted bytes has to write them in itself (which
    `ipd_lifecycle._finalize_transaction` does, deliberately, so an executing agent's uncommitted
    evidence edits still ride the lifecycle commit).
    """
    repo = _repo(tmp_path)
    (repo / "owned.txt").write_text("owned DIRTY UNCOMMITTED\n", encoding="utf-8")
    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        assert (coord.path / "owned.txt").read_text(encoding="utf-8") == "owned v1\n"
        assert _git(coord.path, "status", "--porcelain").stdout.strip() == ""
    # And the shared tree's dirt was never touched.
    assert (repo / "owned.txt").read_text(
        encoding="utf-8"
    ) == "owned DIRTY UNCOMMITTED\n"


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit is required")
def test_hooks_run_in_the_coordinator_worktree_and_still_gate(tmp_path: Path) -> None:
    """Not `--no-verify` in disguise here either: a failing hook blocks the worktree commit."""
    repo = _repo(tmp_path, FAILING_HOOK)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        (coord.path / "owned.txt").write_text("owned v2\n", encoding="utf-8")
        _git(coord.path, "add", "--", "owned.txt")
        res = _git(coord.path, "commit", "-m", "should be rejected")
        assert res.returncode != 0
        assert "REJECTED BY HOOK" in (res.stdout + res.stderr)
        assert _git(coord.path, "rev-parse", "HEAD").stdout.strip() == base
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == base


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit is required")
def test_a_peer_write_during_the_worktree_hook_window_survives(tmp_path: Path) -> None:
    """THE REGRESSION THE WHOLE MECHANISM EXISTS FOR, on this helper's path.

    `pre-commit` stashes the tree it runs in, so a commit in the SHARED tree destroys a peer write
    landing inside that window. Committing in the coordinator worktree must leave the shared tree
    alone.
    """
    repo = _repo(tmp_path, SLOW_HOOK)
    (repo / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

    result: dict[str, object] = {}

    def committer() -> None:
        with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
            (coord.path / "owned.txt").write_text("owned v2\n", encoding="utf-8")
            _git(coord.path, "add", "--", "owned.txt")
            result["res"] = _git(coord.path, "commit", "-m", "slow hook, in a worktree")

    t = threading.Thread(target=committer)
    t.start()
    time.sleep(1.0)  # inside the hook window
    (repo / "peer.txt").write_text("peer v3 WRITTEN DURING WINDOW\n", encoding="utf-8")
    t.join(timeout=120)
    assert not t.is_alive(), "the worktree commit hung"

    res = result["res"]
    assert res.returncode == 0, res.stdout + res.stderr  # type: ignore[union-attr]
    assert (
        (repo / "peer.txt").read_text(encoding="utf-8")
        == "peer v3 WRITTEN DURING WINDOW\n"
    ), "the peer's in-flight write was destroyed: the stash window still touches the shared tree"


def test_commit_isolated_CANNOT_see_a_mutation_made_in_another_worktree(
    tmp_path: Path,
) -> None:
    """Pins F-11, the measurement that forced the sibling: the reuse route genuinely does not work.

    Recorded as a test rather than only as prose so a later reader who proposes "just call
    `commit_isolated`" sees the mechanism fail rather than having to trust a finding.
    """
    repo = _repo(tmp_path)
    (repo / "pending").mkdir()
    (repo / "pending" / "plan.md").write_text("plan v1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add the plan")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()

    with commit_lock.coordinator_worktree(repo, label="abc123") as coord:
        (coord.path / "executed").mkdir()
        _git(coord.path, "mv", "pending/plan.md", "executed/plan.md")
        res = commit_lock.commit_isolated(
            repo, ["pending/plan.md", "executed/plan.md"], message="cannot work"
        )

    # It cannot see the other worktree's mutation, so it fails; nothing was committed.
    assert res.status == commit_lock.ISO_ERROR, res.detail
    assert "did not match any files" in res.detail
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == base
