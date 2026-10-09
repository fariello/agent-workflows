"""Behavioral tests for the plan-scoped live-holder predicate (lifegate urv602, E-06).

Exercises the plan-scoped holder predicate against real run directories and real locks under a
temporary root, verifying all three verdicts (HELD, NOT HELD, UNDETERMINABLE) across all 12 arms
mandated by IPD urv602 V-06.
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import unittest
from pathlib import Path

from agent_workflows import platform_lock, runner_shared


class PlanHolderPredicateTests(unittest.TestCase):
    """Behavioral tests for runner_shared.plan_holder and lock record reader."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._temp_dir.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir(parents=True)
        self.addCleanup(self._temp_dir.cleanup)

    def _create_run_dir(
        self,
        run_id: str,
        id6: str,
        status: str,
        *,
        extra_queue: list[dict] | None = None,
    ) -> Path:
        """Create a realistic run directory with state.json."""
        run_dir = self.repo / ".aw" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        queue = [{"id6": id6, "status": status}]
        if extra_queue:
            queue.extend(extra_queue)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir

    def test_01_lock_acquired_reports_holder(self) -> None:
        """Arm (1): A lock actually acquired through run_lock reports the holder as HELD."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100001", "urv001", "running"
        )
        with runner_shared.run_lock(run_dir):
            res = runner_shared.plan_holder(self.repo, "urv001")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_HELD)
            self.assertEqual(res.run_id, "run-20261009T010000Z-100001")
            self.assertEqual(res.status, "running")
            self.assertEqual(res.host, socket.gethostname())
            self.assertEqual(res.reason_code, "held")
            self.assertIn("holds plan urv001", res.reason)

    def test_02_lock_released_reports_not_held(self) -> None:
        """Arm (2): The same lock released reports NOT HELD."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100002", "urv002", "running"
        )
        with runner_shared.run_lock(run_dir):
            pass  # Acquired and released
        res = runner_shared.plan_holder(self.repo, "urv002")
        self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_NOT_HELD)
        self.assertIsNone(res.run_id)
        self.assertEqual(res.reason_code, "not-held")
        self.assertIn("no live run holds plan urv002", res.reason)

    def test_03_foreign_machine_reports_undeterminable(self) -> None:
        """Arm (3): A record naming a foreign machine reports UNDETERMINABLE with that machine named."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100003", "urv003", "running"
        )
        lock_file = run_dir / "driver.lock"
        foreign_host = "remote-node-09"
        lock_file.write_text(
            f"pid=12345 host={foreign_host} started=2026-10-09T01:00:00Z\n",
            encoding="utf-8",
        )
        res = runner_shared.plan_holder(self.repo, "urv003")
        self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
        self.assertEqual(res.reason_code, "foreign-machine")
        self.assertEqual(res.run_id, "run-20261009T010000Z-100003")
        self.assertEqual(res.host, foreign_host)
        expected_phrase = f"run run-20261009T010000Z-100003 on machine {foreign_host} may still be working on this plan"
        self.assertIn(expected_phrase, res.reason)

    def test_04_legacy_record_no_host_falls_through_to_same_machine(self) -> None:
        """Arm (4): A legacy record with no host= falls through to the same-machine rule."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100004", "urv004", "running"
        )
        lock_file = run_dir / "driver.lock"
        held = platform_lock.acquire(lock_file)
        stream = held.dup_stream()
        assert stream is not None
        stream.seek(0)
        stream.truncate()
        stream.write(f"pid={os.getpid()} started=2026-10-09T01:00:00Z\n")
        stream.flush()
        try:
            res = runner_shared.plan_holder(self.repo, "urv004")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_HELD)
            self.assertEqual(res.run_id, "run-20261009T010000Z-100004")
            self.assertEqual(res.status, "running")
            self.assertEqual(res.reason_code, "held")
        finally:
            stream.close()
            held.release()

        # After release: falls through to not held
        res_after = runner_shared.plan_holder(self.repo, "urv004")
        self.assertEqual(res_after.verdict, runner_shared.PLAN_HOLDER_NOT_HELD)

    def test_05_queue_status_queued_reports_held(self) -> None:
        """Arm (5): A queue entry whose status is merely queued reports HELD (dvonrn D2)."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100005", "urv005", "queued"
        )
        with runner_shared.run_lock(run_dir):
            res = runner_shared.plan_holder(self.repo, "urv005")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_HELD)
            self.assertEqual(res.status, "queued")
            self.assertEqual(res.reason_code, "held")

    def test_06_queue_status_executed_and_legacy_alias_reports_not_held(self) -> None:
        """Arm (6): A queue entry whose status is genuinely finished (executed or alias) reports NOT HELD."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100006", "urv006", "executed"
        )
        with runner_shared.run_lock(run_dir):
            res = runner_shared.plan_holder(self.repo, "urv006")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_NOT_HELD)

        # Legacy alias status (e.g. not-attempted, fail-gate) also reads as finished / not held
        for finished in ["not-attempted", "fail-gate", "dependency-blocked"]:
            self._create_run_dir("run-20261009T010000Z-100006", "urv006", finished)
            with runner_shared.run_lock(run_dir):
                res = runner_shared.plan_holder(self.repo, "urv006")
                self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_NOT_HELD)

    def test_07_excluded_run_id_reports_not_held(self) -> None:
        """Arm (7): Passing the holder's own run id as excluded reports NOT HELD."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100007", "urv007", "running"
        )
        with runner_shared.run_lock(run_dir):
            # Excluded:
            res_excl = runner_shared.plan_holder(
                self.repo, "urv007", exclude_run_id="run-20261009T010000Z-100007"
            )
            self.assertEqual(res_excl.verdict, runner_shared.PLAN_HOLDER_NOT_HELD)

            # Not excluded:
            res_incl = runner_shared.plan_holder(
                self.repo, "urv007", exclude_run_id="other-run"
            )
            self.assertEqual(res_incl.verdict, runner_shared.PLAN_HOLDER_HELD)

    def test_unreadable_lock_reports_undeterminable(self) -> None:
        """Unreadable lock arm: reports UNDETERMINABLE where permissions allow, skips if root."""
        if os.getuid() == 0:
            self.skipTest("Running as root bypasses file permission bits")
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100008u", "urv008u", "running"
        )
        lock_file = run_dir / "driver.lock"
        lock_file.write_text("pid=1234\n", encoding="utf-8")
        lock_file.chmod(0)
        try:
            res = runner_shared.plan_holder(self.repo, "urv008u")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
            self.assertEqual(res.reason_code, "unreadable-lock")
            self.assertIn(
                "driver.lock in run-20261009T010000Z-100008u is present but unreadable",
                res.reason,
            )
        finally:
            lock_file.chmod(0o644)

    def test_08_queue_status_interrupted_reports_held(self) -> None:
        """Arm (8): A queue entry whose status is interrupted reports HELD.

        interrupted IS in TERMINAL_STATES, but is resumable in the runner: requeue_interrupted
        calls item['recovery_next'] = True and flips it to queued on every start/resume.
        Testing status not in TERMINAL_STATES would falsely report NOT HELD (F-11).
        """
        self.assertIn("interrupted", runner_shared.TERMINAL_STATES)
        self.assertIn("interrupted", runner_shared.IN_FLIGHT_QUEUE_STATUSES)
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100008", "urv008", "interrupted"
        )
        with runner_shared.run_lock(run_dir):
            res = runner_shared.plan_holder(self.repo, "urv008")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_HELD)
            self.assertEqual(res.status, "interrupted")
            self.assertEqual(res.reason_code, "held")

    def test_09_remaining_in_flight_statuses_report_held(self) -> None:
        """Arm (9): Each remaining in-flight status (running, integration-deferred, merge-retry) reports HELD."""
        for st in ["running", "integration-deferred", "merge-retry"]:
            run_dir = self._create_run_dir(
                f"run-20261009T010000Z-100009-{st}", "urv009", st
            )
            with runner_shared.run_lock(run_dir):
                res = runner_shared.plan_holder(self.repo, "urv009")
                self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_HELD)
                self.assertEqual(res.status, st)
                self.assertEqual(res.reason_code, "held")

    def test_10_unrecognized_status_token_reports_undeterminable(self) -> None:
        """Arm (10): An UNRECOGNIZED status token reports UNDETERMINABLE, not NOT HELD (fail-closed)."""
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100010", "urv010", "custom-unrecognized-token-xyz"
        )
        with runner_shared.run_lock(run_dir):
            res = runner_shared.plan_holder(self.repo, "urv010")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
            self.assertEqual(res.reason_code, "unrecognized-status")
            self.assertEqual(res.status, "custom-unrecognized-token-xyz")
            self.assertIn("unrecognized queue status", res.reason)

    def test_11_unreadable_runs_tree_discovery_failure_reports_undeterminable(
        self,
    ) -> None:
        """Arm (11): A runs tree that cannot be read reports UNDETERMINABLE (discovery failure, F-12)."""
        if os.getuid() == 0:
            self.skipTest("Running as root bypasses directory permission bits")
        runs_dir = self.repo / ".aw" / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        runs_dir.chmod(0)
        try:
            res = runner_shared.plan_holder(self.repo, "urv011")
            self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
            self.assertEqual(res.reason_code, "discovery-failed")
            self.assertIn("Discovery of run directories", res.reason)
        finally:
            runs_dir.chmod(0o755)

    def test_12_unclassifiable_process_or_unparseable_pid_reports_undeterminable(
        self,
    ) -> None:
        """Arm (12): A held lock whose process cannot be classified or has unparseable pid reports UNDETERMINABLE."""
        # 12a: pid_alive returning None
        run_dir = self._create_run_dir(
            "run-20261009T010000Z-100012a", "urv012a", "running"
        )
        with runner_shared.run_lock(run_dir):
            orig_pid_alive = platform_lock.pid_alive
            try:
                platform_lock.pid_alive = lambda pid: None
                res = runner_shared.plan_holder(self.repo, "urv012a")
                self.assertEqual(res.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
                self.assertEqual(res.reason_code, "unverifiable-process")
                self.assertIn("could not be verified", res.reason)
            finally:
                platform_lock.pid_alive = orig_pid_alive

        # 12b: unparseable pid in held lock
        run_dir_b = self._create_run_dir(
            "run-20261009T010000Z-100012b", "urv012b", "running"
        )
        lock_file_b = run_dir_b / "driver.lock"
        held = platform_lock.acquire(lock_file_b)
        stream = held.dup_stream()
        assert stream is not None
        stream.seek(0)
        stream.truncate()
        stream.write("no-pid-here started=now\n")
        stream.flush()
        try:
            res_b = runner_shared.plan_holder(self.repo, "urv012b")
            self.assertEqual(res_b.verdict, runner_shared.PLAN_HOLDER_UNDETERMINABLE)
            self.assertEqual(res_b.reason_code, "unparseable-pid")
            self.assertIn("carries no parseable pid", res_b.reason)
        finally:
            stream.close()
            held.release()

    def test_pid_reader_unharmed_by_new_record_shape(self) -> None:
        """Verification that read_lock_record_pid recovers the pid from new and legacy shapes."""
        p = self.tmp / "test_pid.lock"

        # New shape: pid=<n> host=<machine> started=<t>
        p.write_text(
            "pid=4242 host=mybox started=2026-10-09T01:00:00Z\n", encoding="utf-8"
        )
        self.assertEqual(platform_lock.read_lock_record_pid(p), 4242)
        self.assertEqual(platform_lock.read_lock_record_host(p), "mybox")

        # Windows byte-0-truncated new shape: id=<n> host=<machine> started=<t>
        p.write_text(
            "id=4242 host=mybox started=2026-10-09T01:00:00Z\n", encoding="utf-8"
        )
        self.assertEqual(platform_lock.read_lock_record_pid(p), 4242)
        self.assertEqual(platform_lock.read_lock_record_host(p), "mybox")

        # Legacy shape: pid=<n> started=<t> (no host=)
        p.write_text("pid=4242 started=2026-10-09T01:00:00Z\n", encoding="utf-8")
        self.assertEqual(platform_lock.read_lock_record_pid(p), 4242)
        self.assertIsNone(platform_lock.read_lock_record_host(p))

        # Windows byte-0-truncated legacy shape: id=<n> started=<t>
        p.write_text("id=4242 started=2026-10-09T01:00:00Z\n", encoding="utf-8")
        self.assertEqual(platform_lock.read_lock_record_pid(p), 4242)
        self.assertIsNone(platform_lock.read_lock_record_host(p))

        # Host with hyphen and digits
        p.write_text(
            "pid=4242 host=my-host-99.example.com started=2026-10-09T01:00:00Z\n",
            encoding="utf-8",
        )
        self.assertEqual(platform_lock.read_lock_record_pid(p), 4242)
        self.assertEqual(
            platform_lock.read_lock_record_host(p), "my-host-99.example.com"
        )


if __name__ == "__main__":
    unittest.main()
