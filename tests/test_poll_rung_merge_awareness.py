"""Integration tests for runner_shared.poll_for_integration_window merge-awareness.

Exercises the real rung against real scratch git repositories (created outside
the repository checkout) under four scenarios:
(a) foreign merge staged, incoming change non-overlapping: rung does not clear,
    waits, and reports POLL_BOUND_MERGE with foreign commits cited and operator action.
(b) foreign merge concluded mid-poll: rung waits until conclusion and then clears.
(c) abandoned foreign merge: rung exits at staleness bound without waiting.
(d) clean base with neither merge nor dirt: clears immediately.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from agent_workflows import runner_shared


def _run_git(
    repo: Path, args: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def _init_repo_with_conflicting_foreign_merge(
    repo: Path,
    *,
    backdate_seconds: float = 0.0,
) -> tuple[str, str]:
    """Build a real scratch git repository where main has a conflicting staged merge.

    Main and foreign-branch both edit other.txt. lanefile.txt is present and committed.
    Returns (foreign_commit_id, main_commit_id).
    """
    env = None
    if backdate_seconds > 0.0:
        past_ts = str(int(time.time() - backdate_seconds))
        env = {**os.environ, "GIT_AUTHOR_DATE": past_ts, "GIT_COMMITTER_DATE": past_ts}

    _run_git(repo, ["init", "-b", "main"], env=env)
    _run_git(repo, ["config", "user.name", "Tester"], env=env)
    _run_git(repo, ["config", "user.email", "tester@example.com"], env=env)

    (repo / "other.txt").write_text("base other\n", encoding="utf-8")
    (repo / "lanefile.txt").write_text("lane file\n", encoding="utf-8")
    _run_git(repo, ["add", "other.txt", "lanefile.txt"], env=env)
    _run_git(repo, ["commit", "-m", "initial commit"], env=env)

    _run_git(repo, ["checkout", "-b", "foreign-branch"], env=env)
    (repo / "other.txt").write_text("foreign edit\n", encoding="utf-8")
    _run_git(repo, ["add", "other.txt"], env=env)
    _run_git(repo, ["commit", "-m", "foreign branch commit"], env=env)
    foreign_commit = _run_git(repo, ["rev-parse", "HEAD"]).stdout.strip()

    _run_git(repo, ["checkout", "main"], env=env)
    (repo / "other.txt").write_text("main edit\n", encoding="utf-8")
    _run_git(repo, ["add", "other.txt"], env=env)
    _run_git(repo, ["commit", "-m", "main branch commit"], env=env)
    main_commit = _run_git(repo, ["rev-parse", "HEAD"]).stdout.strip()

    # Attempt merge --no-ff, which stops on conflict in other.txt with MERGE_HEAD set
    res = subprocess.run(
        ["git", "merge", "--no-ff", "foreign-branch"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode != 0, "Merge was expected to conflict"
    return foreign_commit, main_commit


class TestPollRungMergeAwareness(unittest.TestCase):
    """Real git repository validation of poll_for_integration_window merge-awareness."""

    def test_case_a_foreign_merge_staged_does_not_clear(self) -> None:
        """Case (a): foreign merge staged does not report cleared, reports merge bound."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "scratch_repo"
            repo.mkdir()
            foreign_commit, _ = _init_repo_with_conflicting_foreign_merge(repo)

            commits_before = runner_shared.merge_head_commits(repo)
            status_before = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout

            sim_time = [0.0]

            def fake_now() -> float:
                return sim_time[0]

            def fake_sleep(sec: float) -> None:
                sim_time[0] += sec

            outcome = runner_shared.poll_for_integration_window(
                repo,
                ("lanefile.txt",),
                timeout=0.3,
                interval=0.1,
                sleep=fake_sleep,
                now=fake_now,
                activity_age=lambda _r: 10.0,
            )

            # Assert outcome properties
            self.assertFalse(outcome.cleared)
            self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_MERGE)
            self.assertEqual(outcome.bound, "merge-in-progress")
            self.assertEqual(outcome.polls, 3)

            # Assert detail carries required operator facts
            self.assertIn(foreign_commit, outcome.detail)
            self.assertIn("conclude or abort", outcome.detail)
            self.assertIn("waited its budget", outcome.detail)

            # Assert main repository is undisturbed
            commits_after = runner_shared.merge_head_commits(repo)
            status_after = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout
            self.assertEqual(commits_before, commits_after)
            self.assertEqual(status_before, status_after)

    def test_case_b_foreign_merge_concluded_mid_poll_clears(self) -> None:
        """Case (b): foreign merge concluded mid-poll allows the rung to clear."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "scratch_repo"
            repo.mkdir()
            _init_repo_with_conflicting_foreign_merge(repo)

            commits_before = runner_shared.merge_head_commits(repo)
            self.assertEqual(len(commits_before), 1)
            self.assertTrue(runner_shared.merge_in_progress(repo))

            sim_time = [0.0]
            poll_count = [0]

            def fake_now() -> float:
                return sim_time[0]

            def fake_sleep(sec: float) -> None:
                sim_time[0] += sec
                poll_count[0] += 1
                if poll_count[0] == 2:
                    # Conclude the foreign merge for real
                    (repo / "other.txt").write_text(
                        "resolved other\n", encoding="utf-8"
                    )
                    _run_git(repo, ["add", "other.txt"])
                    _run_git(repo, ["commit", "-m", "conclude foreign merge"])

            outcome = runner_shared.poll_for_integration_window(
                repo,
                ("lanefile.txt",),
                timeout=2.0,
                interval=0.1,
                sleep=fake_sleep,
                now=fake_now,
                activity_age=lambda _r: 10.0,
            )

            # Assert merge was concluded for real
            self.assertFalse(runner_shared.merge_in_progress(repo))
            self.assertEqual(runner_shared.merge_head_commits(repo), [])

            # Assert outcome cleared on dirt-cleared bound
            self.assertTrue(outcome.cleared)
            self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_CLEARED)
            self.assertEqual(outcome.bound, "dirt-cleared")
            self.assertEqual(outcome.polls, 2)
            self.assertIn(
                "the overlapping dirty path cleared after 2 poll(s)", outcome.detail
            )

    def test_case_c_abandoned_mid_merge_exits_at_staleness_bound(self) -> None:
        """Case (c): abandoned foreign merge exits at staleness bound without waiting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "scratch_repo"
            repo.mkdir()
            # Backdate both commit times and working-tree mtimes by 4 hours (14400s)
            foreign_commit, _ = _init_repo_with_conflicting_foreign_merge(
                repo, backdate_seconds=14400.0
            )

            past_ts = time.time() - 14400.0
            for root, _dirs, files in os.walk(repo):
                for f in files:
                    p = Path(root) / f
                    try:
                        os.utime(p, (past_ts, past_ts))
                    except OSError:
                        pass

            # Verify measured activity age exceeds staleness limit (3600.0s)
            measured_age = runner_shared.main_last_activity_age(repo)
            self.assertIsNotNone(measured_age)
            assert measured_age is not None  # type narrowing
            self.assertGreater(measured_age, 3600.0)

            commits_before = runner_shared.merge_head_commits(repo)
            status_before = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout

            outcome = runner_shared.poll_for_integration_window(
                repo,
                ("lanefile.txt",),
                timeout=1800.0,
                staleness_limit=3600.0,
            )

            # Assert staleness bound exit
            self.assertFalse(outcome.cleared)
            self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_STALE)
            self.assertEqual(outcome.bound, "main-inactive")
            self.assertEqual(outcome.polls, 0)

            # Assert detail carries operator facts
            self.assertIn(foreign_commit, outcome.detail)
            self.assertIn("ABANDONED", outcome.detail)
            self.assertIn("conclude or abort", outcome.detail)
            self.assertIn("staleness bound 3600s", outcome.detail)

            # Assert main repository is undisturbed
            commits_after = runner_shared.merge_head_commits(repo)
            status_after = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout
            self.assertEqual(commits_before, commits_after)
            self.assertEqual(status_before, status_after)

    def test_case_d_clean_base_clears_immediately(self) -> None:
        """Case (d): clean base with neither merge nor dirt clears immediately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "scratch_repo"
            repo.mkdir()
            _run_git(repo, ["init", "-b", "main"])
            _run_git(repo, ["config", "user.name", "Tester"])
            _run_git(repo, ["config", "user.email", "tester@example.com"])
            (repo / "lanefile.txt").write_text("clean lane\n", encoding="utf-8")
            _run_git(repo, ["add", "lanefile.txt"])
            _run_git(repo, ["commit", "-m", "clean commit"])

            commits_before = runner_shared.merge_head_commits(repo)
            status_before = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout
            self.assertEqual(commits_before, [])
            self.assertEqual(status_before, "")

            outcome = runner_shared.poll_for_integration_window(
                repo,
                ("lanefile.txt",),
            )

            self.assertTrue(outcome.cleared)
            self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_CLEARED)
            self.assertEqual(outcome.bound, "dirt-cleared")
            self.assertEqual(outcome.polls, 0)
            self.assertIn(
                "the overlapping dirty path cleared after 0 poll(s)", outcome.detail
            )

            commits_after = runner_shared.merge_head_commits(repo)
            status_after = _run_git(
                repo, ["status", "--short", "--untracked-files=all"]
            ).stdout
            self.assertEqual(commits_before, commits_after)
            self.assertEqual(status_before, status_after)


if __name__ == "__main__":
    unittest.main()
