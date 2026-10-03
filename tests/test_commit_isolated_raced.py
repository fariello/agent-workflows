"""Tests for retaining stranded compare-and-swap commits and accurate reporting.

Pins for IPD a1ygjp (set: isoraced).
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import commit_lock
from agent_workflows import git_commit_helper


def _run_git(cwd: Path, args: list) -> tuple[int, str, str]:
    res = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return res.returncode, res.stdout, res.stderr


class CommitIsolatedRacedTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = Path(self.td.name)
        _run_git(self.repo, ["init", "-b", "main"])
        _run_git(self.repo, ["config", "user.name", "Tester"])
        _run_git(self.repo, ["config", "user.email", "tester@example.com"])
        _run_git(self.repo, ["config", "commit.gpgsign", "false"])
        (self.repo / "init.txt").write_text("initial\n")
        _run_git(self.repo, ["add", "init.txt"])
        _run_git(self.repo, ["commit", "-m", "initial commit"])

    def tearDown(self):
        self.td.cleanup()

    def test_case_1_raced_commit_retained_and_survives_gc(self):
        """Case (1): Retained commit is reachable from refs/aw/abandoned/isolated/<sha12>,

        fsck does not report it dangling, and it survives git gc --prune=now.
        """
        orig_git = commit_lock._git
        peer_committed = False

        def patched_git(wt, args):
            nonlocal peer_committed
            if args and args[0] == "update-ref" and not peer_committed:
                peer_committed = True
                (self.repo / "peer.txt").write_text("peer commit\n")
                _run_git(self.repo, ["add", "peer.txt"])
                _run_git(self.repo, ["commit", "-m", "peer commit", "--", "peer.txt"])
            return orig_git(wt, args)

        (self.repo / "mine.txt").write_text("my work\n")
        with mock.patch("agent_workflows.commit_lock._git", side_effect=patched_git):
            res = commit_lock.commit_isolated(
                self.repo, ["mine.txt"], message="isolated work"
            )

        self.assertEqual(res.status, commit_lock.ISO_RACED)
        self.assertIsNotNone(res.commit)
        sha = res.commit
        ref_name = f"refs/aw/abandoned/isolated/{sha[:12]}"

        # Assert ref exists
        rc_ref, out_ref, _ = _run_git(self.repo, ["rev-parse", "--verify", ref_name])
        self.assertEqual(
            rc_ref,
            0,
            f"expected retained ref {ref_name} to exist, rev-parse failed: {out_ref}",
        )
        self.assertEqual(out_ref.strip(), sha)

        # Assert cat-file succeeds
        rc_cat, _, _ = _run_git(self.repo, ["cat-file", "-e", sha])
        self.assertEqual(rc_cat, 0, "commit object must exist")

        # Assert fsck does not report dangling commit
        _, out_fsck, _ = _run_git(self.repo, ["fsck"])
        self.assertNotIn(
            f"dangling commit {sha}",
            out_fsck,
            f"retained commit {sha} must not be reported dangling by fsck",
        )

        # Run gc --prune=now and assert commit and ref still survive
        _run_git(self.repo, ["gc", "--prune=now"])
        rc_cat_after, _, _ = _run_git(self.repo, ["cat-file", "-e", sha])
        self.assertEqual(rc_cat_after, 0, "commit must survive gc --prune=now")
        rc_ref_after, out_ref_after, _ = _run_git(
            self.repo, ["rev-parse", "--verify", ref_name]
        )
        self.assertEqual(rc_ref_after, 0, f"ref {ref_name} must survive gc --prune=now")
        self.assertEqual(out_ref_after.strip(), sha)

    def test_case_2_every_stranded_sha_is_reported_on_exhaustion(self):
        """Case (2): After driving offer_commit to exhaustion, the outcome's new

        field lists ALL stranded shas and each one resolves.
        """
        orig_git = commit_lock._git
        attempt = 0

        def patched_git(wt, args):
            nonlocal attempt
            if args and args[0] == "update-ref":
                attempt += 1
                (self.repo / f"peer_{attempt}.txt").write_text(f"peer {attempt}\n")
                _run_git(self.repo, ["add", f"peer_{attempt}.txt"])
                _run_git(
                    self.repo,
                    [
                        "commit",
                        "-m",
                        f"peer commit {attempt}",
                        "--",
                        f"peer_{attempt}.txt",
                    ],
                )
            return orig_git(wt, args)

        (self.repo / "record.txt").write_text("my record\n")
        with mock.patch("agent_workflows.commit_lock._git", side_effect=patched_git):
            outcome = git_commit_helper.offer_commit(
                self.repo,
                ["record.txt"],
                message="record commit",
                assume_yes=True,
                interactive=False,
            )

        self.assertEqual(outcome.status, git_commit_helper.STATUS_ERROR)
        abandoned = getattr(outcome, "abandoned", ())
        self.assertEqual(
            len(abandoned),
            git_commit_helper.ISO_RACED_MAX_ATTEMPTS,
            f"outcome.abandoned must contain all {git_commit_helper.ISO_RACED_MAX_ATTEMPTS} stranded shas, got {len(abandoned)}: {abandoned}",
        )
        for sha in abandoned:
            rc, out, _ = _run_git(
                self.repo,
                ["rev-parse", "--verify", f"refs/aw/abandoned/isolated/{sha[:12]}"],
            )
            self.assertEqual(rc, 0, f"retained ref for sha {sha} must resolve")
            self.assertEqual(out.strip(), sha)

    def test_case_3_committed_path_retains_nothing(self):
        """Case (3): Preservation pin.

        An ordinary successful commit_isolated writes NO refs/aw/abandoned/isolated/
        ref, because the commit is already reachable and a ref would be permanent litter.
        """
        (self.repo / "clean.txt").write_text("clean work\n")
        res = commit_lock.commit_isolated(
            self.repo, ["clean.txt"], message="clean commit"
        )
        self.assertEqual(res.status, commit_lock.ISO_COMMITTED)

        # Assert no refs/aw/abandoned/isolated/ refs exist
        rc, out, _ = _run_git(
            self.repo, ["for-each-ref", "refs/aw/abandoned/isolated/"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(
            out.strip(),
            "",
            f"successful commit must write no abandoned refs, found: {out.strip()}",
        )

    def test_case_4_message_makes_no_false_promise(self):
        """Case (4): Neither the ISO_RACED detail nor the exhaustion message contains

        an unqualified 'is preserved as commit' or advises a bare 'cherry-pick' as remedy,
        while both still name the sha.
        """
        orig_git = commit_lock._git
        attempt = 0

        def patched_git(wt, args):
            nonlocal attempt
            if args and args[0] == "update-ref":
                attempt += 1
                (self.repo / f"peer_{attempt}.txt").write_text(f"peer {attempt}\n")
                _run_git(self.repo, ["add", f"peer_{attempt}.txt"])
                _run_git(
                    self.repo,
                    [
                        "commit",
                        "-m",
                        f"peer commit {attempt}",
                        "--",
                        f"peer_{attempt}.txt",
                    ],
                )
            return orig_git(wt, args)

        (self.repo / "work.txt").write_text("my work\n")
        with mock.patch("agent_workflows.commit_lock._git", side_effect=patched_git):
            outcome = git_commit_helper.offer_commit(
                self.repo,
                ["work.txt"],
                message="work commit",
                assume_yes=True,
                interactive=False,
            )

        msg = outcome.message
        self.assertNotIn(
            "is preserved as commit",
            msg,
            "message must not promise unqualified preservation",
        )
        self.assertNotIn(
            "cherry-pick",
            msg,
            "message must not advise cherry-pick as remedy",
        )
        # Verify it still names a stranded sha or ref
        self.assertTrue(
            any(c in msg for c in ("refs/aw/abandoned/isolated/", "stranded")),
            f"message should name the retained ref or stranded commit: {msg}",
        )

    def test_case_5_retained_ref_invisible_to_operator_views(self):
        """Case (5): Preservation pin.

        Retention under refs/aw/ is invisible to git branch -a, git status --porcelain,
        and for-each-ref refs/heads/.
        """
        # Create a sample abandoned ref
        sha = _run_git(self.repo, ["rev-parse", "HEAD"])[1].strip()
        ref_name = f"refs/aw/abandoned/isolated/{sha[:12]}"
        _run_git(self.repo, ["update-ref", ref_name, sha])

        _, out_branch, _ = _run_git(self.repo, ["branch", "-a"])
        self.assertNotIn(
            "abandoned",
            out_branch,
            f"git branch -a must not list abandoned refs: {out_branch}",
        )

        _, out_status, _ = _run_git(self.repo, ["status", "--porcelain"])
        self.assertEqual(
            out_status.strip(),
            "",
            f"git status must be unaffected by refs/aw/ refs: {out_status}",
        )

        _, out_heads, _ = _run_git(
            self.repo, ["for-each-ref", "--format=%(refname)", "refs/heads/"]
        )
        self.assertEqual(
            out_heads.strip(),
            "refs/heads/main",
            f"for-each-ref refs/heads/ must show only heads: {out_heads}",
        )

    def test_case_6_overlapping_path_race_keeps_agent_bytes_recoverable(self):
        """Case (6): Overlapping-path race keeps agent's bytes recoverable.

        With the peer committing the same path:
        1. Agent content is absent from disk and absent from HEAD.
        2. Retained ref resolves.
        3. git show <ref>:<path> yields the agent's exact bytes.
        4. Content survives git gc --prune=now.
        """
        (self.repo / "shared.txt").write_text("initial\n")
        _run_git(self.repo, ["add", "shared.txt"])
        _run_git(self.repo, ["commit", "-m", "init shared"])

        orig_git = commit_lock._git
        peer_committed = False

        def patched_git(wt, args):
            nonlocal peer_committed
            if args and args[0] == "update-ref" and not peer_committed:
                peer_committed = True
                (self.repo / "shared.txt").write_text("PEER CONTENT\n")
                _run_git(self.repo, ["add", "shared.txt"])
                _run_git(self.repo, ["commit", "-m", "peer edit", "--", "shared.txt"])
            return orig_git(wt, args)

        agent_content = "AGENT SPECIFIC BYTES 42\n"
        (self.repo / "shared.txt").write_text(agent_content)

        with mock.patch("agent_workflows.commit_lock._git", side_effect=patched_git):
            res = commit_lock.commit_isolated(
                self.repo, ["shared.txt"], message="agent edit"
            )

        self.assertEqual(res.status, commit_lock.ISO_RACED)
        sha = res.commit
        self.assertIsNotNone(sha)
        ref_name = f"refs/aw/abandoned/isolated/{sha[:12]}"

        # Assert agent bytes ABSENT from disk
        disk_content = (self.repo / "shared.txt").read_text()
        self.assertEqual(disk_content, "PEER CONTENT\n")
        self.assertNotIn(agent_content, disk_content)

        # Assert agent bytes ABSENT from HEAD
        _, head_content, _ = _run_git(self.repo, ["show", "HEAD:shared.txt"])
        self.assertEqual(head_content, "PEER CONTENT\n")
        self.assertNotIn(agent_content, head_content)

        # Assert retained ref resolves
        rc_ref, out_ref, _ = _run_git(self.repo, ["rev-parse", "--verify", ref_name])
        self.assertEqual(
            rc_ref,
            0,
            f"retained ref {ref_name} must resolve on overlapping-path race",
        )

        # Assert git show <ref>:shared.txt yields AGENT bytes specifically
        rc_show, show_content, _ = _run_git(
            self.repo, ["show", f"{ref_name}:shared.txt"]
        )
        self.assertEqual(rc_show, 0)
        self.assertEqual(
            show_content,
            agent_content,
            f"retained ref must carry agent bytes '{agent_content}', got '{show_content}'",
        )

        # Assert it survives gc --prune=now
        _run_git(self.repo, ["gc", "--prune=now"])
        rc_show_after, show_after, _ = _run_git(
            self.repo, ["show", f"{ref_name}:shared.txt"]
        )
        self.assertEqual(rc_show_after, 0)
        self.assertEqual(show_after, agent_content)
