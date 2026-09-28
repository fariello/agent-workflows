import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import contention_wait


class ContentionWaitHelperTests(unittest.TestCase):
    def test_case_a_succeeds_on_fourth_try_reports_once_per_60s_with_holder(self):
        """(a) wait_until succeeds on the 4th try and reports once per 60 simulated seconds with holder named."""
        sim_time = [0.0]
        reports = []

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        tries = [0]

        def try_once():
            tries[0] += 1
            if tries[0] == 4:
                return True, "acquired"
            return False, None

        def holder():
            return "PID 42 (owner: runner)"

        res = contention_wait.wait_until(
            try_once,
            what="test-resource",
            holder=holder,
            poll=20.0,
            report_every=60.0,
            report=reports.append,
            sleep=fake_sleep,
            now=fake_now,
        )

        self.assertTrue(res.ok)
        self.assertEqual("acquired", res.value)
        self.assertEqual(4, res.attempts)
        self.assertEqual(60.0, res.waited)
        self.assertEqual(1, len(reports))
        self.assertIn(
            "still waiting for test-resource held by PID 42 (owner: runner)", reports[0]
        )
        self.assertIn("(60s of 1800s)", reports[0])

    def test_case_b_gives_up_at_exactly_1800s_with_detail_naming_what_and_who(self):
        """(b) gives up at exactly 1800 simulated seconds with a detail naming what and who."""
        sim_time = [0.0]
        reports = []

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        def try_once():
            return False, None

        def holder():
            return "PID 9999"

        res = contention_wait.wait_until(
            try_once,
            what="exclusive-lock",
            holder=holder,
            timeout=1800.0,
            poll=10.0,
            report=reports.append,
            sleep=fake_sleep,
            now=fake_now,
        )

        self.assertFalse(res.ok)
        self.assertIsNone(res.value)
        self.assertEqual(1800.0, res.waited)
        self.assertIn("exclusive-lock", res.detail)
        self.assertIn("PID 9999", res.detail)
        self.assertIn("1800s", res.detail)

    def test_case_c_holder_callable_returning_none_renders_no_held_by_clause(self):
        """(c) a holder callable returning None renders a line with no 'held by' clause."""
        sim_time = [0.0]
        reports = []

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        tries = [0]

        def try_once():
            tries[0] += 1
            if tries[0] == 2:
                return True, "done"
            return False, None

        res = contention_wait.wait_until(
            try_once,
            what="unheld-resource",
            holder=lambda: None,
            poll=60.0,
            report_every=60.0,
            report=reports.append,
            sleep=fake_sleep,
            now=fake_now,
        )

        self.assertTrue(res.ok)
        self.assertEqual(1, len(reports))
        self.assertNotIn("held by", reports[0])
        self.assertIn("still waiting for unheld-resource (60s of 1800s)", reports[0])

    def test_case_d_silent_fast_path_not_called_before_first_report_boundary(self):
        """(d) report is NOT called before the first report_every boundary, so a wait resolving in 0.2s is SILENT."""
        sim_time = [0.0]
        reports = []

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        tries = [0]

        def try_once():
            tries[0] += 1
            if tries[0] == 3:  # 0s (1st), 0.1s (2nd), 0.2s (3rd)
                return True, "fast"
            return False, None

        res = contention_wait.wait_until(
            try_once,
            what="fast-lock",
            poll=0.1,
            report_every=60.0,
            report=reports.append,
            sleep=fake_sleep,
            now=fake_now,
        )

        self.assertTrue(res.ok)
        self.assertEqual("fast", res.value)
        self.assertEqual(3, res.attempts)
        self.assertAlmostEqual(0.2, res.waited)
        self.assertEqual(0, len(reports), "0.2s resolve must be completely silent")

    def test_case_e_poll_and_report_cadence_independent(self):
        """(e) poll and report_every are independent: a 0.1s poll with a 60s report cadence yields ~600 attempts and 1 report line."""
        sim_time = [0.0]
        reports = []

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        tries = [0]

        def try_once():
            tries[0] += 1
            if sim_time[0] >= 60.0:
                return True, "resolved"
            return False, None

        res = contention_wait.wait_until(
            try_once,
            what="contended-lock",
            poll=0.1,
            report_every=60.0,
            report=reports.append,
            sleep=fake_sleep,
            now=fake_now,
        )

        self.assertTrue(res.ok)
        self.assertEqual(1, len(reports))
        self.assertEqual(601, res.attempts)
        self.assertAlmostEqual(60.0, res.waited)
        self.assertIn("still waiting for contended-lock (60s of 1800s)", reports[0])


class ContentionWaitCallSiteTests(unittest.TestCase):
    """Call-site outcome tests (E-08 cases a-d)."""

    def test_case_a_held_finalize_lock_released_after_5_minutes_lets_finalize_proceed_both_hosts(
        self,
    ):
        """(a) a held finalize lock released after 5 simulated minutes lets finalize proceed, driven through finalize_with_contention_retry on BOTH hosts."""
        from agent_workflows import agy_runipd as agy_driver
        from agent_workflows import ipd_lifecycle
        from agent_workflows import oc_runipd as oc_driver
        from agent_workflows import runner_shared

        for driver in (oc_driver, agy_driver):
            with self.subTest(driver=driver.__name__):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir) / "repo"
                    repo.mkdir()
                    run_dir = Path(temp_dir) / "run"
                    run_dir.mkdir()
                    lock_file = ipd_lifecycle.finalize_lock_path(repo)
                    lock_file.parent.mkdir(parents=True, exist_ok=True)
                    foreign_pid = 402458
                    lock_file.write_text(
                        json.dumps(
                            {"pid": foreign_pid, "owner": "peer", "plan_id": "other"}
                        ),
                        encoding="utf-8",
                    )

                    sim_time = [0.0]

                    def fake_now():
                        return sim_time[0]

                    def fake_sleep(sec):
                        sim_time[0] += sec
                        if sim_time[0] >= 300.0:
                            # Released after 5 simulated minutes (300s)
                            if lock_file.exists():
                                lock_file.unlink()

                    def fake_pid_alive(pid):
                        return True if pid == foreign_pid else False

                    finalize_calls = [0]

                    def fake_driver_finalize(r, p, id6, actor, msg, attestation=None):
                        finalize_calls[0] += 1
                        ipd_lifecycle.acquire_finalize_lock(
                            r,
                            id6,
                            timeout=ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS,
                            sleep=fake_sleep,
                            now=fake_now,
                        )
                        ipd_lifecycle.release_finalize_lock(r)
                        return 0, "ok"

                    item = {"id6": "test01", runner_shared.FINALIZE_RETRY_COUNT_KEY: 0}
                    events = []

                    with mock.patch(
                        "agent_workflows.platform_lock.pid_alive",
                        side_effect=fake_pid_alive,
                    ):
                        rc, msg = runner_shared.finalize_with_contention_retry(
                            fake_driver_finalize,
                            repo,
                            repo / "plan.ipd.md",
                            item["id6"],
                            "actor",
                            "message",
                            item=item,
                            run_dir=run_dir,
                            append_jsonl=lambda p, ev: events.append(ev),
                            backoff_seconds=0.0,
                            sleep_fn=fake_sleep,
                        )

                    self.assertEqual(0, rc)
                    self.assertEqual("ok", msg)
                    self.assertEqual(1, finalize_calls[0])
                    self.assertGreaterEqual(
                        sim_time[0], 300.0, "waited 5 simulated minutes"
                    )

    def test_case_b_writer_lock_live_peer_raises_and_stale_peer_taken_over_with_zero_waiting(
        self,
    ):
        """(b) writer_lock held by a LIVE peer past timeout raises CommitLockBusy rather than yielding unlocked, and a STALE holder is taken over with zero waiting."""
        from agent_workflows import commit_lock

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            lock_path = commit_lock.lock_path(repo)
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Part 1: Live peer past timeout raises CommitLockBusy
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "owner": "live-peer",
                        "timestamp": "2026-09-27T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            reports = []
            with mock.patch(
                "agent_workflows.commit_lock._pid_alive", return_value=True
            ):
                with self.assertRaises(commit_lock.CommitLockBusy) as ctx:
                    with commit_lock.writer_lock(
                        repo,
                        owner="setter",
                        timeout=0.2,
                        poll=0.05,
                        report=reports.append,
                    ):
                        self.fail("must not execute body when lock is busy")
                self.assertIn("live PID 999999 (owner: live-peer)", str(ctx.exception))
                self.assertIn("ipd_finalize_writer.lock", str(ctx.exception))

            # Part 2: Stale (dead-pid) peer is taken over with zero waiting
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": 888888,
                        "owner": "dead-peer",
                        "timestamp": "2026-09-27T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            fake_sleep = mock.Mock()
            with mock.patch(
                "agent_workflows.commit_lock._pid_alive", return_value=False
            ):
                with commit_lock.writer_lock(
                    repo,
                    owner="setter-reclaim",
                    timeout=1800.0,
                    sleep=fake_sleep,
                ) as acquired:
                    self.assertTrue(acquired)
                    fake_sleep.assert_not_called()
                    owner_payload = commit_lock.read_owner(repo)
                    self.assertIsNotNone(owner_payload)
                    self.assertEqual("setter-reclaim", owner_payload["owner"])
                    self.assertEqual(os.getpid(), owner_payload["pid"])
            self.assertFalse(lock_path.exists())

    def test_writer_lock_progress_reaches_stderr(self):
        """writer_lock default report handler writes 60s progress lines to sys.stderr."""
        from agent_workflows import commit_lock

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            lock_path = commit_lock.lock_path(repo)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "owner": "holding-peer",
                        "timestamp": "2026-09-27T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            sim_time = [0.0]

            def fake_now():
                return sim_time[0]

            def fake_sleep(sec):
                sim_time[0] += sec
                if sim_time[0] >= 70.0:
                    lock_path.unlink()

            stderr_buf = io.StringIO()
            with mock.patch(
                "agent_workflows.commit_lock._pid_alive", return_value=True
            ):
                with mock.patch("sys.stderr", stderr_buf):
                    with commit_lock.writer_lock(
                        repo,
                        owner="caller",
                        poll=10.0,
                        report_every=60.0,
                        sleep=fake_sleep,
                        now=fake_now,
                    ) as acquired:
                        self.assertTrue(acquired)

            captured = stderr_buf.getvalue()
            self.assertIn(
                "still waiting for shared aw writer lock held by live PID 999999 (owner: holding-peer)",
                captured,
            )
            self.assertIn("(60s of 1800s)", captured)

    def test_case_c_setter_isolated_commit_raced_once_succeeds_with_peer_intact(self):
        """(c) a setter whose isolated commit returns ISO_RACED once then succeeds ends committed with exactly its own paths in the commit AND the peer's commit intact beneath it."""
        from agent_workflows import commit_lock, git_commit_helper

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            repo = temp_dir_path / "repo"
            repo.mkdir()
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Tester"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)

            (repo / "base.txt").write_text("base content\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "base commit"], cwd=repo, check=True
            )

            (repo / "mine.txt").write_text("setter content\n", encoding="utf-8")

            orig_commit_isolated = commit_lock.commit_isolated
            call_count = [0]

            def fake_commit_isolated(r, paths, *, message, branch=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    # Peer commits peer.txt in a detached worktree without touching repo's staged index
                    peer_wt = temp_dir_path / "peer_wt"
                    subprocess.run(
                        ["git", "worktree", "add", "--detach", str(peer_wt), "HEAD"],
                        cwd=repo,
                        check=True,
                    )
                    (peer_wt / "peer.txt").write_text(
                        "peer content\n", encoding="utf-8"
                    )
                    subprocess.run(["git", "add", "peer.txt"], cwd=peer_wt, check=True)
                    subprocess.run(
                        ["git", "commit", "-q", "-m", "peer commit"],
                        cwd=peer_wt,
                        check=True,
                    )
                    rc, peer_head, _ = git_commit_helper._git(
                        peer_wt, ["rev-parse", "HEAD"]
                    )
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(peer_wt)],
                        cwd=repo,
                        check=True,
                    )
                    # Advance repo's branch ref to the peer commit
                    rc, branch_name, _ = git_commit_helper._git(
                        repo, ["rev-parse", "--abbrev-ref", "HEAD"]
                    )
                    target_branch = branch_name.strip()
                    git_commit_helper._git(
                        repo,
                        [
                            "update-ref",
                            f"refs/heads/{target_branch}",
                            peer_head.strip(),
                        ],
                    )
                    return commit_lock.IsolatedCommitResult(
                        commit_lock.ISO_RACED, None, "raced: HEAD moved"
                    )
                return orig_commit_isolated(r, paths, message=message, branch=branch)

            with mock.patch(
                "agent_workflows.commit_lock.commit_isolated",
                side_effect=fake_commit_isolated,
            ):
                outcome = git_commit_helper.offer_commit(
                    repo,
                    ["mine.txt"],
                    message="setter commit",
                    assume_yes=True,
                )

            self.assertEqual(git_commit_helper.STATUS_COMMITTED, outcome.status)
            self.assertEqual(2, call_count[0])

            rc, log_out, _ = git_commit_helper._git(
                repo, ["log", "--oneline", "-n", "3"]
            )
            self.assertEqual(0, rc)
            lines = [line.strip() for line in log_out.strip().splitlines()]
            self.assertEqual(3, len(lines))
            self.assertIn("setter commit", lines[0])
            self.assertIn("peer commit", lines[1])
            self.assertIn("base commit", lines[2])

            rc, show_out, _ = git_commit_helper._git(
                repo, ["show", "--name-only", "--format=", "HEAD"]
            )
            self.assertEqual(0, rc)
            self.assertEqual(["mine.txt"], show_out.strip().splitlines())

            rc, show_peer, _ = git_commit_helper._git(
                repo, ["show", "--name-only", "--format=", "HEAD~1"]
            )
            self.assertEqual(0, rc)
            self.assertEqual(["peer.txt"], show_peer.strip().splitlines())

            self.assertTrue((repo / "mine.txt").exists())

    def test_case_d_poll_integration_window_wall_bound_and_staleness_short_circuits(
        self,
    ):
        """(d) poll_for_integration_window is bounded by wall time, and staleness bound short-circuits before first sleep and fires on unmeasurable age."""
        from agent_workflows import runner_shared

        # Half 1: Wall-time bound
        sim_time = [0.0]

        def fake_now():
            return sim_time[0]

        def fake_sleep(sec):
            sim_time[0] += sec

        outcome = runner_shared.poll_for_integration_window(
            Path("/fake/repo"),
            ("file.txt",),
            timeout=0.3,
            interval=0.1,
            staleness_limit=3600.0,
            sleep=fake_sleep,
            now=fake_now,
            overlap=lambda _r, _f: ["file.txt"],
            activity_age=lambda _r: 10.0,
        )
        self.assertFalse(outcome.cleared)
        self.assertEqual(runner_shared.POLL_BOUND_COUNT, outcome.bound)
        self.assertEqual(3, outcome.polls)
        self.assertAlmostEqual(0.3, sim_time[0])
        self.assertIn("0s bound", outcome.detail)

        # Half 2a: Staleness bound short-circuits before first sleep
        never_sleep = mock.Mock()
        outcome_stale = runner_shared.poll_for_integration_window(
            Path("/fake/repo"),
            ("file.txt",),
            timeout=1800.0,
            interval=0.1,
            staleness_limit=3600.0,
            sleep=never_sleep,
            overlap=lambda _r, _f: ["file.txt"],
            activity_age=lambda _r: 4000.0,
        )
        self.assertFalse(outcome_stale.cleared)
        self.assertEqual(runner_shared.POLL_BOUND_STALE, outcome_stale.bound)
        self.assertEqual(0, outcome_stale.polls)
        never_sleep.assert_not_called()
        self.assertIn("4000s ago", outcome_stale.detail)

        # Half 2b: Staleness bound fires on unmeasurable age (None) before first sleep
        outcome_unmeas = runner_shared.poll_for_integration_window(
            Path("/fake/repo"),
            ("file.txt",),
            timeout=1800.0,
            interval=0.1,
            staleness_limit=3600.0,
            sleep=never_sleep,
            overlap=lambda _r, _f: ["file.txt"],
            activity_age=lambda _r: None,
        )
        self.assertFalse(outcome_unmeas.cleared)
        self.assertEqual(runner_shared.POLL_BOUND_STALE, outcome_unmeas.bound)
        self.assertEqual(0, outcome_unmeas.polls)
        never_sleep.assert_not_called()
        self.assertIsNone(outcome_unmeas.last_activity_age)
        self.assertIn("unmeasurable", outcome_unmeas.detail)


if __name__ == "__main__":
    unittest.main()
