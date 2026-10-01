"""Tests for agent_workflows.commit_lock (pins coordinator_worktree reachability and teardown)."""

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from agent_workflows import commit_lock
from tests import support


def _git(
    cwd: Path, args: list[str], check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _init_repo(root: Path) -> None:
    _git(root, ["init", "-b", "master"])
    _git(root, ["config", "user.name", "Test User"])
    _git(root, ["config", "user.email", "test@example.com"])
    _git(root, ["config", "commit.gpgsign", "false"])
    (root / "initial.txt").write_text("initial\n", encoding="utf-8")
    _git(root, ["add", "initial.txt"])
    _git(root, ["commit", "-m", "initial commit"])


class CoordinatorWorktreeTeardownTests(unittest.TestCase):
    """Presents the lower-layer contract for coordinator_worktree teardown.

    asserts the lower layer; test_git_commit_helper.py asserts what a CALLER observes.
    """

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_repo(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_01_abandoned_commit_is_retained_under_ref_and_survives_gc(self) -> None:
        """Case (1): an abandoned coordinator commit is retained under refs/aw/abandoned/ and survives gc.

        A commit made inside coordinator_worktree and never landed by the caller must remain
        reachable via its retained ref after the worktree context exits, not be reported
        dangling by git fsck, and survive git gc --prune=now.
        """
        sha: str = ""
        with commit_lock.coordinator_worktree(self.root, label="abandoned") as coord:
            (coord.path / "work.txt").write_text(
                "abandoned payload\n", encoding="utf-8"
            )
            _git(coord.path, ["add", "work.txt"])
            _git(coord.path, ["commit", "-m", "work in progress"])
            sha = _git(coord.path, ["rev-parse", "HEAD"]).stdout.strip()

        self.assertTrue(sha, "commit sha must be resolved")
        ref_name = commit_lock.abandoned_ref_name(sha)

        # 1. Retained ref must exist and resolve to the commit
        verify_res = _git(self.root, ["rev-parse", "--verify", ref_name], check=False)
        self.assertEqual(
            verify_res.returncode,
            0,
            f"retained ref {ref_name} must exist for abandoned commit {sha}: {verify_res.stderr.strip()}",
        )
        self.assertEqual(verify_res.stdout.strip(), sha)

        # 2. Commit must be an ancestor of the retained ref
        anc_res = _git(
            self.root, ["merge-base", "--is-ancestor", sha, ref_name], check=False
        )
        self.assertEqual(
            anc_res.returncode, 0, f"commit {sha} must be reachable from {ref_name}"
        )

        # 3. git fsck must not report the commit as dangling
        fsck_res = _git(self.root, ["fsck"], check=False)
        self.assertNotIn(
            f"dangling commit {sha}",
            fsck_res.stdout,
            f"commit {sha} must not be dangling under fsck",
        )

        # 4. Commit survives aggressive garbage collection
        _git(self.root, ["gc", "--prune=now"])
        cat_res = _git(self.root, ["cat-file", "-e", sha], check=False)
        self.assertEqual(
            cat_res.returncode,
            0,
            f"commit {sha} must survive gc --prune=now via {ref_name}",
        )

    def test_02_landed_commit_does_not_write_retained_ref(self) -> None:
        """Case (2): when the caller lands the commit via ff-only merge, no retained ref is written.

        Preservation test: a landed commit is already reachable from the branch, so writing a
        retained ref would be permanent litter. This test passes today and must fail if an
        implementation retains unconditionally.
        """
        sha: str = ""
        with commit_lock.coordinator_worktree(self.root, label="landed") as coord:
            (coord.path / "landed.txt").write_text("landed payload\n", encoding="utf-8")
            _git(coord.path, ["add", "landed.txt"])
            _git(coord.path, ["commit", "-m", "landed work"])
            sha = _git(coord.path, ["rev-parse", "HEAD"]).stdout.strip()
            # Caller lands the commit before exiting the context
            _git(self.root, ["merge", "--ff-only", sha])

        self.assertTrue(sha, "commit sha must be resolved")

        # The landed commit is reachable from HEAD
        anc_res = _git(
            self.root, ["merge-base", "--is-ancestor", sha, "HEAD"], check=False
        )
        self.assertEqual(
            anc_res.returncode, 0, f"landed commit {sha} must be reachable from HEAD"
        )

        # Crucial negative assertion: NO retained ref is written under refs/aw/abandoned/
        refs_res = _git(
            self.root,
            ["for-each-ref", "--format=%(refname)", "refs/aw/abandoned/"],
            check=False,
        )
        self.assertEqual(
            refs_res.stdout.strip(),
            "",
            f"no retained ref must be written when commit was landed; found: {refs_res.stdout.strip()}",
        )

    def test_03_nothing_committed_writes_no_retained_ref(self) -> None:
        """Case (3): when nothing was committed inside the worktree, no retained ref is written.

        Preservation test: tip still equals base, so no commit was created and no ref is written.
        Passes today.
        """
        with commit_lock.coordinator_worktree(self.root, label="nothing"):
            pass  # write nothing

        refs_res = _git(
            self.root,
            ["for-each-ref", "--format=%(refname)", "refs/aw/abandoned/"],
            check=False,
        )
        self.assertEqual(
            refs_res.stdout.strip(),
            "",
            f"no retained ref must be written when nothing was committed; found: {refs_res.stdout.strip()}",
        )

    def test_04_retained_ref_is_invisible_to_operator_ordinary_views(self) -> None:
        """Case (4): the retained ref namespace is invisible to standard operator git views.

        Preservation test: git branch -a, git branch --list 'aw/*', git status --porcelain,
        and for-each-ref refs/heads/ remain byte-identical before and after retention.
        Passes today.
        """
        # Baseline ordinary views
        branches_before = _git(self.root, ["branch", "-a"]).stdout
        aw_branches_before = _git(self.root, ["branch", "--list", "aw/*"]).stdout
        status_before = _git(self.root, ["status", "--porcelain"]).stdout
        heads_before = _git(
            self.root, ["for-each-ref", "--format=%(refname)", "refs/heads/"]
        ).stdout

        with commit_lock.coordinator_worktree(self.root, label="invisible") as coord:
            (coord.path / "inv.txt").write_text("payload\n", encoding="utf-8")
            _git(coord.path, ["add", "inv.txt"])
            _git(coord.path, ["commit", "-m", "inv work"])

        # Check views after context exits (with or without retained ref written)
        branches_after = _git(self.root, ["branch", "-a"]).stdout
        aw_branches_after = _git(self.root, ["branch", "--list", "aw/*"]).stdout
        status_after = _git(self.root, ["status", "--porcelain"]).stdout
        heads_after = _git(
            self.root, ["for-each-ref", "--format=%(refname)", "refs/heads/"]
        ).stdout

        self.assertEqual(
            branches_after, branches_before, "git branch -a must be unaffected"
        )
        self.assertEqual(
            aw_branches_after,
            aw_branches_before,
            "git branch --list 'aw/*' must be unaffected",
        )
        self.assertEqual(
            status_after, status_before, "git status --porcelain must be unaffected"
        )
        self.assertEqual(
            heads_after, heads_before, "for-each-ref refs/heads/ must be unaffected"
        )

    def test_05_prune_deletes_refs_older_than_retention_window_and_preserves_fresh(
        self,
    ) -> None:
        """E-05: retained refs older than the 14-day window are pruned, fresh refs survive."""
        tree = _git(self.root, ["write-tree"]).stdout.strip()

        # Create an old commit (30 days ago) and a fresh commit (now)
        env_old = os.environ.copy()
        old_time = int(time.time() - 30 * 86400)
        env_old["GIT_COMMITTER_DATE"] = f"{old_time} +0000"
        env_old["GIT_AUTHOR_DATE"] = f"{old_time} +0000"
        old_sha = subprocess.run(
            ["git", "commit-tree", tree, "-m", "old commit"],
            cwd=self.root,
            env=env_old,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        old_ref = commit_lock.abandoned_ref_name(old_sha)
        _git(self.root, ["update-ref", old_ref, old_sha])
        self.assertEqual(
            _git(self.root, ["rev-parse", "--verify", old_ref], check=False).returncode,
            0,
        )

        # Invoking coordinator_worktree triggers prune at invocation (pruning old_ref) and retains fresh_ref
        fresh_sha: str = ""
        with commit_lock.coordinator_worktree(self.root, label="fresh") as coord:
            (coord.path / "fresh.txt").write_text("fresh payload\n", encoding="utf-8")
            _git(coord.path, ["add", "fresh.txt"])
            _git(coord.path, ["commit", "-m", "fresh commit"])
            fresh_sha = _git(coord.path, ["rev-parse", "HEAD"]).stdout.strip()

        fresh_ref = commit_lock.abandoned_ref_name(fresh_sha)

        # Old ref pruned at invocation, fresh ref retained on abandoned exit
        self.assertNotEqual(
            _git(self.root, ["rev-parse", "--verify", old_ref], check=False).returncode,
            0,
        )
        self.assertEqual(
            _git(
                self.root, ["rev-parse", "--verify", fresh_ref], check=False
            ).returncode,
            0,
        )

        # gc --prune=now collects old commit and keeps fresh commit
        _git(self.root, ["gc", "--prune=now"])
        self.assertNotEqual(
            _git(self.root, ["cat-file", "-e", old_sha], check=False).returncode, 0
        )
        self.assertEqual(
            _git(self.root, ["cat-file", "-e", fresh_sha], check=False).returncode, 0
        )

    def test_06_prune_failure_does_not_fail_worktree_invocation(self) -> None:
        """E-05: a failure during pruning fails soft and does not fail the worktree invocation."""
        real_git = commit_lock._git

        def failing_git(repo_root: Path, args: list) -> tuple:
            if (
                args
                and args[0] == "for-each-ref"
                and any("refs/aw/abandoned/" in str(a) for a in args)
            ):
                raise RuntimeError("simulated prune failure")
            return real_git(repo_root, args)

        with unittest.mock.patch("agent_workflows.commit_lock._git", failing_git):
            # coordinator_worktree must not raise during prune
            with commit_lock.coordinator_worktree(self.root, label="fail-soft"):
                pass

    def test_07_retained_commit_date_matches_wall_clock_time(self) -> None:
        """F-15: committerdate:unix of coordinator commit matches retention wall-clock time."""
        t0 = time.time()
        sha: str = ""
        with commit_lock.coordinator_worktree(self.root, label="timecheck") as coord:
            (coord.path / "time.txt").write_text("time\n", encoding="utf-8")
            _git(coord.path, ["add", "time.txt"])
            _git(coord.path, ["commit", "-m", "time commit"])
            sha = _git(coord.path, ["rev-parse", "HEAD"]).stdout.strip()
        t1 = time.time()

        ref_name = commit_lock.abandoned_ref_name(sha)
        out = _git(
            self.root, ["for-each-ref", "--format=%(committerdate:unix)", ref_name]
        ).stdout.strip()
        commit_ts = float(out)
        self.assertGreaterEqual(commit_ts, int(t0) - 2)
        self.assertLessEqual(commit_ts, int(t1) + 2)
