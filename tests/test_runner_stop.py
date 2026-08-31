#!/usr/bin/env python3
"""Tests for the durable, monotonic stop-request record and the cooperative stop poll.

Set `runstop` Phase 1 (`gq6m2u`), spec `c4gd2h` R7-R9/R11.

Two of these test classes exist because of MEASURED failures, not from reading the code, and they
are the reason the implementation looks more complicated than "write a JSON file":

- `MonotonicityUnderConcurrencyTests` runs MANY racing pairs, because the naive
  atomic-write-only implementation loses the higher level in roughly half of all trials. A
  single-trial test would pass ~50% of the time by luck and prove nothing.
- `SignalHandlerSafetyTests` delivers a REAL signal while the sidecar lock is held, because a
  BLOCKING lock acquire reached from a signal handler deadlocks the process outright. Every test
  here that can hang is bounded by a subprocess timeout so a regression FAILS the suite instead of
  hanging it.

Both concurrency and signal tests are marked `slow` (they spawn subprocesses), so run this file
with `-m ''` or via `make test-all`; the default `addopts` deselects `-m 'not slow'`.
"""

from __future__ import annotations

import datetime as dt
import errno
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import runner_stop
from tests.support import REPO_ROOT

_CHILD_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
# Every subprocess probe is bounded so a reintroduced deadlock FAILS rather than hangs the suite.
_CHILD_TIMEOUT = 30.0


def _run_child(script: str, *args: str, timeout: float = _CHILD_TIMEOUT):
    """Run a probe script in a child interpreter under a hard timeout."""

    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "probe.py"
        path.write_text(textwrap.dedent(script), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(path), *args],
            capture_output=True,
            text=True,
            env=_CHILD_ENV,
            timeout=timeout,
        )


class RecordRoundTripTests(unittest.TestCase):
    """E-01: the record round-trips, and a malformed control file reads as ABSENT, not as a crash."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def test_absent_file_reads_as_none(self):
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))

    def test_round_trip_preserves_level_and_metadata(self):
        result = runner_stop.request_stop(self.run_dir, runner_stop.LEVEL_NOW, "tester")
        self.assertTrue(result.accepted)
        loaded = runner_stop.read_stop_request(self.run_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.level, runner_stop.LEVEL_NOW)
        self.assertEqual(loaded.level_name, "now")
        self.assertEqual(loaded.requester, "tester")
        self.assertEqual(loaded.requested_at, result.request.requested_at)
        self.assertEqual(loaded.first_requested_at, result.request.requested_at)
        self.assertEqual(len(loaded.history), 1)

    def test_truncated_file_reads_as_none(self):
        runner_stop.request_stop(self.run_dir, runner_stop.LEVEL_NOW, "tester")
        path = runner_stop.stop_request_path(self.run_dir)
        text = path.read_text(encoding="utf-8")
        path.write_text(text[: len(text) // 2], encoding="utf-8")
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))

    def test_garbage_file_reads_as_none(self):
        runner_stop.stop_request_path(self.run_dir).write_text(
            "\x00\x01 not json at all", encoding="utf-8"
        )
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))

    def test_valid_json_with_unusable_level_reads_as_none(self):
        # A structurally valid file whose level is out of range must not be honored: an unusable
        # control file is "no stop requested", never a guess.
        for bogus in (0, 5, -1, "3", None, True):
            runner_stop.stop_request_path(self.run_dir).write_text(
                json.dumps(
                    {"level": bogus, "requested_at": "2026-08-30T00:00:00+00:00"}
                ),
                encoding="utf-8",
            )
            self.assertIsNone(
                runner_stop.read_stop_request(self.run_dir), f"level={bogus!r}"
            )

    def test_directory_in_place_of_record_reads_as_none(self):
        runner_stop.stop_request_path(self.run_dir).mkdir()
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))

    def test_poll_on_malformed_file_returns_none_and_does_not_raise(self):
        runner_stop.stop_request_path(self.run_dir).write_text("{", encoding="utf-8")
        self.assertIsNone(runner_stop.poll_stop(self.run_dir))


class MonotonicityTests(unittest.TestCase):
    """E-02, sequential half: a request may only RAISE the level (spec R9)."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def test_one_then_three_then_one_stays_three_with_two_entry_history(self):
        self.assertTrue(runner_stop.request_stop(self.run_dir, 1, "a").accepted)
        self.assertTrue(runner_stop.request_stop(self.run_dir, 3, "b").accepted)
        third = runner_stop.request_stop(self.run_dir, 1, "c")
        self.assertFalse(
            third.accepted, "a lower request must be a no-op, not a downgrade"
        )
        record = runner_stop.read_stop_request(self.run_dir)
        self.assertEqual(record.level, 3)
        self.assertEqual(len(record.history), 2)
        self.assertEqual([e["level"] for e in record.history], [1, 3])

    def test_escalation_to_four(self):
        runner_stop.request_stop(self.run_dir, 3, "a")
        self.assertTrue(runner_stop.request_stop(self.run_dir, 4, "b").accepted)
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)

    def test_no_sequence_can_lower_the_level(self):
        runner_stop.request_stop(self.run_dir, 4, "hard")
        for level in (1, 2, 3, 4):
            result = runner_stop.request_stop(self.run_dir, level, f"try-{level}")
            self.assertFalse(
                result.accepted, f"level {level} must not be accepted after 4"
            )
            self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)

    def test_equal_level_is_a_no_op_leaving_the_file_untouched(self):
        runner_stop.request_stop(self.run_dir, 3, "a")
        path = runner_stop.stop_request_path(self.run_dir)
        before = path.read_bytes()
        self.assertFalse(runner_stop.request_stop(self.run_dir, 3, "b").accepted)
        self.assertEqual(path.read_bytes(), before)

    def test_first_requested_at_is_preserved_across_escalation(self):
        first = runner_stop.request_stop(self.run_dir, 1, "a").request
        runner_stop.request_stop(self.run_dir, 4, "b")
        record = runner_stop.read_stop_request(self.run_dir)
        self.assertEqual(record.first_requested_at, first.requested_at)
        self.assertNotEqual(record.requested_at, first.requested_at)

    def test_invalid_level_is_rejected_loudly(self):
        for bogus in (0, 5, -1, "3", None, True):
            with self.assertRaises(ValueError):
                runner_stop.request_stop(self.run_dir, bogus, "x")

    def test_serialization_uses_a_sidecar_lock_not_the_record_file(self):
        # The lock MUST be a separate file: the record is swapped by os.replace, so a lock held on
        # the replaced inode would protect nothing.
        runner_stop.request_stop(self.run_dir, 1, "a")
        record = runner_stop.stop_request_path(self.run_dir)
        lock = runner_stop.stop_request_lock_path(self.run_dir)
        self.assertNotEqual(record, lock)
        self.assertTrue(lock.is_file(), "sidecar lock file should exist after a write")
        self.assertEqual(lock.name, "stop-request.lock")

    def test_record_survives_os_replace_swapping_the_inode(self):
        runner_stop.request_stop(self.run_dir, 1, "a")
        path = runner_stop.stop_request_path(self.run_dir)
        first_inode = path.stat().st_ino
        runner_stop.request_stop(self.run_dir, 4, "b")
        self.assertNotEqual(
            path.stat().st_ino, first_inode, "escalation should replace the record file"
        )
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)


@pytest.mark.slow
class MonotonicityUnderConcurrencyTests(unittest.TestCase):
    """E-02, the half that actually matters: monotonicity under REAL concurrent writers.

    MEASURED (re-verified independently while executing this plan, 200 trials each):
      - atomic write only, read-modify-write UNSERIALIZED: the higher level was LOST in 87/200
        trials (~44%).
      - read-compare-write serialized under the sidecar lock: LOST in 0/200.

    So the trial count is the point. A single-trial test would pass about half the time against
    the broken implementation and would therefore prove nothing at all.
    """

    TRIALS = 120  # >= 100 required by V-02; each trial is two racing processes

    def test_racing_writers_never_lose_the_higher_level(self):
        script = """
        import json, sys, os
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        level = int(sys.argv[2])
        gate = Path(sys.argv[3])
        # Spin on a file gate so both children reach the write as simultaneously as possible.
        # This is a RACE PROBE (widening a window), not a checkpoint definition: no test here
        # uses a sleep to decide when something is safe.
        while not gate.exists():
            pass
        runner_stop.request_stop(run_dir, level, f"racer-{level}", timeout=30.0)
        """
        lost = 0
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "probe.py"
            probe.write_text(textwrap.dedent(script), encoding="utf-8")
            for trial in range(self.TRIALS):
                run_dir = root / f"trial-{trial}"
                run_dir.mkdir()
                gate = run_dir / "gate"
                procs = [
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(probe),
                            str(run_dir),
                            str(level),
                            str(gate),
                        ],
                        env=_CHILD_ENV,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    # High level FIRST, low level second: the ordering that loses the update.
                    for level in (4, 1)
                ]
                gate.touch()
                for proc in procs:
                    _out, err = proc.communicate(timeout=_CHILD_TIMEOUT)
                    self.assertEqual(proc.returncode, 0, f"racer failed: {err}")
                record = runner_stop.read_stop_request(run_dir)
                self.assertIsNotNone(record, f"trial {trial} left no record")
                if record.level != 4:
                    lost += 1
        self.assertEqual(
            lost,
            0,
            f"the higher level was lost in {lost}/{self.TRIALS} trials (a lost update is "
            "exactly the silent downgrade spec R9 forbids)",
        )

    def test_many_concurrent_escalators_converge_on_the_maximum(self):
        script = """
        import sys
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        level = int(sys.argv[2])
        gate = Path(sys.argv[3])
        while not gate.exists():
            pass
        runner_stop.request_stop(run_dir, level, f"racer-{level}", timeout=30.0)
        """
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            probe = root / "probe.py"
            probe.write_text(textwrap.dedent(script), encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            gate = run_dir / "gate"
            procs = [
                subprocess.Popen(
                    [sys.executable, str(probe), str(run_dir), str(level), str(gate)],
                    env=_CHILD_ENV,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for level in (1, 2, 3, 4, 3, 2, 1, 2)
            ]
            gate.touch()
            for proc in procs:
                _out, err = proc.communicate(timeout=_CHILD_TIMEOUT)
                self.assertEqual(proc.returncode, 0, f"racer failed: {err}")
            self.assertEqual(runner_stop.read_stop_request(run_dir).level, 4)


class TornWriteTests(unittest.TestCase):
    """E-02: an interrupted write must never be readable as a valid LOWER level."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def test_failure_mid_write_leaves_the_previous_valid_record(self):
        runner_stop.request_stop(self.run_dir, 3, "first")
        before = runner_stop.stop_request_path(self.run_dir).read_bytes()

        boom = OSError("injected failure between write and rename")
        with mock.patch.object(runner_stop.os, "replace", side_effect=boom):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")

        self.assertEqual(
            runner_stop.stop_request_path(self.run_dir).read_bytes(), before
        )
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 3)

    def test_failed_write_leaves_no_temp_file_behind(self):
        runner_stop.request_stop(self.run_dir, 1, "first")
        with mock.patch.object(runner_stop.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")
        leftovers = [
            p.name
            for p in self.run_dir.iterdir()
            if p.name.startswith(".") and p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [], f"temp files leaked: {leftovers}")

    def test_first_write_failing_leaves_no_readable_request(self):
        with mock.patch.object(runner_stop.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                runner_stop.request_stop(self.run_dir, 4, "interrupted")
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))


class PathResolutionTests(unittest.TestCase):
    """E-03: the flag rides the driver's OWN run-dir accessor, with no second root."""

    def test_path_is_stop_request_json_inside_the_run_dir(self):
        self.assertEqual(
            runner_stop.stop_request_path(Path("/x/runs/run-1")),
            Path("/x/runs/run-1/stop-request.json"),
        )

    def test_resolution_follows_a_monkeypatched_state_root(self):
        # Proves there is no hardcoded root: when the accessor's answer moves (which is exactly
        # what `wtiso` Phase 4 does by relocating the run root out of the repo), the flag moves.
        with tempfile.TemporaryDirectory() as temp:
            relocated = Path(temp) / "elsewhere" / "runs"

            def fake_state_root(_repo: Path) -> Path:
                return relocated

            resolved = runner_stop.resolve_stop_request_path(
                Path("/some/repo"), "run-42", state_root=fake_state_root
            )
            self.assertEqual(resolved, relocated / "run-42" / "stop-request.json")
            self.assertFalse(
                str(resolved).startswith("/some/repo"),
                "the flag must not be pinned under the repo",
            )

    def test_both_drivers_state_root_accessors_compose(self):
        from agent_workflows import agy_runipd, oc_runipd

        for driver in (oc_runipd, agy_runipd):
            resolved = runner_stop.resolve_stop_request_path(
                Path("/repo"), "run-7", state_root=driver.state_root
            )
            self.assertEqual(
                resolved, Path("/repo/.aw/records/runs/run-7/stop-request.json")
            )

    def test_module_constructs_no_state_root_of_its_own(self):
        # Orchestrator CID-2 / `wtiso` Phase 3 guard: this module must not build a raw state root.
        source = (REPO_ROOT / "agent_workflows" / "runner_stop.py").read_text(
            encoding="utf-8"
        )
        code_lines = [
            line for line in source.splitlines() if not line.strip().startswith("#")
        ]
        for needle in ('".aw"', "'.aw'", '".aw/state"', "'.aw/state'"):
            self.assertNotIn(
                needle,
                "\n".join(code_lines),
                f"runner_stop must not construct a state root itself (found {needle})",
            )


class BudgetTests(unittest.TestCase):
    """E-05: the per-level wind-down budget and its absolute deadline (spec R11)."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def test_every_level_has_a_budget(self):
        for level in runner_stop.LEVELS:
            self.assertIsInstance(runner_stop.budget_for_level(level), float)

    def test_level_four_has_a_zero_budget(self):
        # "Interrupt immediately" has no wind-down phase by definition.
        self.assertEqual(runner_stop.budget_for_level(runner_stop.LEVEL_NOW_FORCE), 0.0)

    def test_deadline_is_requested_at_plus_the_levels_budget(self):
        for level in runner_stop.LEVELS:
            with tempfile.TemporaryDirectory() as temp:
                run_dir = Path(temp)
                record = runner_stop.request_stop(run_dir, level, "tester").request
                expected = dt.datetime.fromisoformat(
                    record.requested_at
                ) + dt.timedelta(seconds=runner_stop.budget_for_level(level))
                self.assertEqual(
                    dt.datetime.fromisoformat(record.deadline),
                    expected,
                    f"level {level} deadline must be requested_at + budget",
                )
                self.assertEqual(
                    record.budget_seconds, runner_stop.budget_for_level(level)
                )

    def test_reading_the_deadline_twice_is_stable(self):
        runner_stop.request_stop(self.run_dir, 3, "tester")
        first = runner_stop.read_stop_request(self.run_dir)
        second = runner_stop.read_stop_request(self.run_dir)
        self.assertEqual(first.deadline, second.deadline)
        self.assertEqual(first.budget_seconds, second.budget_seconds)

    def test_escalation_rebases_the_budget_on_the_new_level(self):
        runner_stop.request_stop(self.run_dir, 1, "a")
        record = runner_stop.request_stop(self.run_dir, 3, "b").request
        self.assertEqual(record.budget_seconds, runner_stop.budget_for_level(3))
        expected = dt.datetime.fromisoformat(record.requested_at) + dt.timedelta(
            seconds=runner_stop.budget_for_level(3)
        )
        self.assertEqual(dt.datetime.fromisoformat(record.deadline), expected)

    def test_this_child_enforces_no_budget(self):
        # R11 is ACCOUNTED here and ENFORCED by the phases owning each level. A record whose
        # deadline is long past must still read back normally.
        past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()
        runner_stop.stop_request_path(self.run_dir).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "level": 3,
                    "requested_at": past,
                    "requester": "old",
                    "first_requested_at": past,
                    "budget_seconds": 1.0,
                    "deadline": past,
                    "history": [],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 3)


class PollTests(unittest.TestCase):
    """E-04: the poll REPORTS the level and never consumes the request (spec R8)."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def test_poll_is_none_when_no_request_exists(self):
        self.assertIsNone(runner_stop.poll_stop(self.run_dir))

    def test_repeated_polls_are_idempotent_and_leave_the_record_unchanged(self):
        runner_stop.request_stop(self.run_dir, 3, "tester")
        path = runner_stop.stop_request_path(self.run_dir)
        before_bytes = path.read_bytes()
        before_stat = path.stat()
        levels = [runner_stop.poll_stop(self.run_dir) for _ in range(25)]
        self.assertEqual(levels, [3] * 25, "the poll must not consume the request")
        self.assertEqual(path.read_bytes(), before_bytes)
        self.assertEqual(path.stat().st_mtime_ns, before_stat.st_mtime_ns)

    def test_poll_observes_an_escalation(self):
        runner_stop.request_stop(self.run_dir, 1, "a")
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 1)
        runner_stop.request_stop(self.run_dir, 4, "b")
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 4)


@pytest.mark.slow
class CrossProcessPollTests(unittest.TestCase):
    """E-04: the poll must see a level written by ANOTHER PROCESS (the out-of-band `stop` case)."""

    def test_poll_observes_a_level_written_by_a_separate_process(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            self.assertIsNone(runner_stop.poll_stop(run_dir))
            result = _run_child(
                """
                import sys
                from pathlib import Path
                from agent_workflows import runner_stop
                runner_stop.request_stop(Path(sys.argv[1]), 3, "other-process")
                """,
                str(run_dir),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # A genuinely separate process wrote it; this process never held the object.
            self.assertEqual(runner_stop.poll_stop(run_dir), 3)
            record = runner_stop.read_stop_request(run_dir)
            self.assertEqual(record.requester, "other-process")

    def test_driver_loop_observes_a_mid_run_request(self):
        """The realistic shape: a loop polling per line picks up an out-of-band request."""

        result = _run_child(
            """
            import subprocess, sys
            from pathlib import Path
            from agent_workflows import runner_stop

            run_dir = Path(sys.argv[1])
            seen = []
            for i in range(50):
                if i == 10:
                    subprocess.run(
                        [sys.executable, "-c",
                         "import sys;from pathlib import Path;"
                         "from agent_workflows import runner_stop;"
                         "runner_stop.request_stop(Path(sys.argv[1]), 4, 'oob')",
                         str(run_dir)],
                        check=True,
                    )
                seen.append(runner_stop.poll_stop(run_dir))
            print("before:", seen[0], "after:", seen[-1])
            assert seen[0] is None, seen[:3]
            assert seen[-1] == 4, seen[-3:]
            """,
            str(Path(tempfile.mkdtemp())),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("before: None after: 4", result.stdout)


class PollWiringTests(unittest.TestCase):
    """E-04: the poll is wired at BOTH checkpoints in BOTH drivers (four sites)."""

    def _source(self, module_name: str) -> str:
        return (REPO_ROOT / "agent_workflows" / module_name).read_text(encoding="utf-8")

    def test_each_driver_polls_at_exactly_two_sites(self):
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            count = source.count("runner_stop.poll_stop(run_dir)")
            self.assertEqual(
                count, 2, f"{module_name} should poll at 2 checkpoints, found {count}"
            )

    def test_in_turn_poll_sits_with_the_watchdog_touch(self):
        # The per-line in-turn checkpoint: beside the existing watchdog heartbeat, which is the
        # established precedent that the driver may act on stream observation alone.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            # Anchor on the LAST watchdog.touch(), not the first. stallfp (kaga7s) added an
            # EARLIER touch site (the `_subagent_progress` callback, oc_runipd only) after this
            # test was written, so `.index()` began measuring from a site that is not the
            # per-line stream checkpoint at all. `.rindex()` finds the in-turn touch in both
            # drivers regardless of how many earlier callback sites exist.
            idx = source.rindex("watchdog.touch()")
            # 1200, not 700: the window must survive COMMENT growth between the touch and the
            # poll. After merging lanetruth-01 (af7i6p, the parent-session-id learning block) and
            # this plan's own explanatory comment, the gap in oc_runipd is 825 chars of which
            # almost all is comment; the two statements are still only a few lines apart. The
            # window exists to prove the poll sits at the per-line stream checkpoint, not to
            # police comment length.
            window = source[idx : idx + 1200]
            self.assertIn(
                "runner_stop.poll_stop(run_dir)",
                window,
                f"{module_name}: in-turn poll should follow watchdog.touch()",
            )

    def test_between_item_poll_is_in_the_dequeue_loop(self):
        # The between-item checkpoint: inside run_queue's dequeue loop, BEFORE the next item is
        # selected, which is where levels 1-2 will branch.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            body = source[source.index("def run_queue(") :]
            loop = body.index("while True:")
            select = body.index('item["status"] == "queued"')
            poll = body.index("runner_stop.poll_stop(run_dir)")
            self.assertLess(loop, poll, f"{module_name}: poll must be inside the loop")
            self.assertLess(
                poll, select, f"{module_name}: poll must precede item selection"
            )

    def test_both_drivers_share_the_one_stop_mechanism(self):
        from agent_workflows import agy_runipd, oc_runipd

        self.assertIs(oc_runipd.runner_stop, runner_stop)
        self.assertIs(agy_runipd.runner_stop, runner_stop)

    def test_the_handler_safe_writer_is_the_only_writer_a_signal_handler_uses(self):
        # Scope fence, NARROWED TWICE now, each time by the phase it was reserving room for.
        #
        # Phase 1 (`gq6m2u`) authored it as "no level behavior exists yet", forbidding both any
        # consumption of the poll's return value and any signal handler. Phase 2 (`1qxuke`) removed the
        # first half, because levels 1-2 must consume that return value at the between-item checkpoint.
        # Phase 5 (`71vjbn`) now removes the second half, because the trigger UX is precisely the
        # SIGINT/SIGTERM registration this line was holding open.
        #
        # It is NOT simply deleted, and equally NOT left as written: Phase 5 registers from the SHARED
        # `runner_stop` module, so `assertNotIn("signal.signal(", driver_source)` would now pass
        # VACUOUSLY - green while asserting nothing. The invariant that was always the real point is
        # kept and asserted directly on the installer: a handler may only use the handler-SAFE writer
        # (`request_stop_nowait`), because Phase 1 MEASURED that a blocking sidecar-lock acquire reached
        # from a handler hangs the process outright (entered, hung, killed at a 10s timeout, exit 124).
        import inspect

        installer = inspect.getsource(runner_stop.install_stop_signal_handlers)
        self.assertIn("request_stop_nowait(", installer)
        self.assertNotIn(
            "request_stop(",
            installer.replace("request_stop_nowait(", ""),
            "a signal handler must never take the blocking-retry writer (measured deadlock)",
        )
        # The drivers must go through that installer rather than registering handlers of their own,
        # which is how two phases' handlers would silently race for the same signal.
        for module_name in ("oc_runipd.py", "agy_runipd.py"):
            source = self._source(module_name)
            self.assertIn(
                "runner_stop.install_stop_signal_handlers(", source, module_name
            )
            self.assertNotIn("signal.signal(", source, module_name)


@pytest.mark.slow
class SignalHandlerSafetyTests(unittest.TestCase):
    """E-06: the writer a signal handler calls must never block, and must never lose the request.

    MEASURED (re-verified while executing this plan): a BLOCKING `flock` reached from a SIGINT
    handler while the main thread holds the sidecar lock hangs the process outright (the handler
    printed "handler entered" and never returned; killed at a 10s timeout, exit 124). The
    non-blocking + defer-to-poll path exits 0 with the level preserved.

    Every probe below is bounded by a subprocess timeout, so a reintroduced blocking acquire FAILS
    this test instead of hanging the suite.
    """

    _HANDLER_PROBE = """
        import fcntl, os, signal, sys
        from pathlib import Path
        from agent_workflows import runner_stop

        run_dir = Path(sys.argv[1])
        mode = sys.argv[2]

        def blocking_request(level):
            # The naive implementation this test exists to forbid: a BLOCKING acquire.
            lock_path = runner_stop.stop_request_lock_path(run_dir)
            with lock_path.open("a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        def handler(signum, frame):
            print("handler entered", flush=True)
            if mode == "blocking":
                blocking_request(4)
            else:
                result = runner_stop.request_stop_nowait(run_dir, 4, "sighandler")
                print("deferred=%s" % result.deferred, flush=True)
            print("handler exited", flush=True)

        signal.signal(signal.SIGINT, handler)

        lock_path = runner_stop.stop_request_lock_path(run_dir)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as held:
            # Hold the sidecar lock on the MAIN thread, then deliver a REAL signal to ourselves,
            # which is precisely the re-entrancy the deadlock needs.
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            print("main holds lock", flush=True)
            os.kill(os.getpid(), signal.SIGINT)
            print("main resumed", flush=True)
            fcntl.flock(held.fileno(), fcntl.LOCK_UN)

        print("poll=%s" % runner_stop.poll_stop(run_dir), flush=True)
        """

    def test_real_signal_while_lock_held_neither_hangs_nor_loses_the_request(self):
        run_dir = Path(tempfile.mkdtemp())
        try:
            result = _run_child(
                self._HANDLER_PROBE, str(run_dir), "nowait", timeout=15.0
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "request_stop_nowait DEADLOCKED in a signal handler: it must make a "
                "non-blocking attempt and defer to the poll"
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handler entered", result.stdout)
        self.assertIn("handler exited", result.stdout)
        self.assertIn("deferred=True", result.stdout)
        self.assertIn("main resumed", result.stdout)
        # The level was NOT lost: the polling loop wrote it durably at the next checkpoint.
        self.assertIn("poll=4", result.stdout)

    def test_the_blocking_variant_really_does_hang(self):
        # Characterization: proves this test class exercises a REAL hazard rather than a
        # hypothetical one. If this ever stops timing out, the platform's lock semantics changed
        # and the reasoning behind request_stop_nowait must be re-examined.
        run_dir = Path(tempfile.mkdtemp())
        with self.assertRaises(subprocess.TimeoutExpired):
            _run_child(self._HANDLER_PROBE, str(run_dir), "blocking", timeout=8.0)

    def test_handler_path_takes_no_blocking_acquire(self):
        calls = []
        real_flock = fcntl.flock

        def recording_flock(fd, operation):
            calls.append(operation)
            return real_flock(fd, operation)

        run_dir = Path(tempfile.mkdtemp())
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)
        with mock.patch.object(runner_stop.fcntl, "flock", recording_flock):
            runner_stop.request_stop_nowait(run_dir, 3, "handler")
        acquires = [op for op in calls if op & fcntl.LOCK_EX]
        self.assertTrue(acquires, "expected an exclusive acquire attempt")
        for op in acquires:
            self.assertTrue(
                op & fcntl.LOCK_NB,
                "the handler-safe path must use LOCK_NB; a blocking acquire deadlocks",
            )

    def test_request_stop_also_never_issues_a_blocking_acquire(self):
        # Even the non-handler writer must not block indefinitely: it retries LOCK_NB under a
        # bounded deadline and fails loudly.
        calls = []
        real_flock = fcntl.flock

        def recording_flock(fd, operation):
            calls.append(operation)
            return real_flock(fd, operation)

        run_dir = Path(tempfile.mkdtemp())
        with mock.patch.object(runner_stop.fcntl, "flock", recording_flock):
            runner_stop.request_stop(run_dir, 3, "main")
        for op in [op for op in calls if op & fcntl.LOCK_EX]:
            self.assertTrue(op & fcntl.LOCK_NB, "request_stop must not block on flock")


class DeferredRequestTests(unittest.TestCase):
    """E-06: the process-local deferral slot, and the poll draining it durably."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        runner_stop.reset_deferred_request()
        self.addCleanup(runner_stop.reset_deferred_request)

    def _hold_lock(self):
        """Hold the sidecar lock so the next nowait attempt is forced to defer."""

        lock_path = runner_stop.stop_request_lock_path(self.run_dir)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.addCleanup(handle.close)
        return handle

    def test_nowait_writes_durably_when_the_lock_is_free(self):
        result = runner_stop.request_stop_nowait(self.run_dir, 3, "handler")
        self.assertTrue(result.accepted)
        self.assertFalse(result.deferred)
        self.assertIsNone(runner_stop.pending_deferred_request())
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 3)

    def test_nowait_defers_when_contended_and_the_poll_drains_it(self):
        handle = self._hold_lock()
        result = runner_stop.request_stop_nowait(self.run_dir, 4, "handler")
        self.assertTrue(result.deferred)
        self.assertFalse(result.accepted)
        self.assertEqual(runner_stop.pending_deferred_request(), (4, "handler"))
        # Nothing durable yet, and the poll cannot write while the lock is still held.
        self.assertIsNone(runner_stop.read_stop_request(self.run_dir))
        self.assertIsNone(runner_stop.poll_stop(self.run_dir))
        self.assertEqual(runner_stop.pending_deferred_request(), (4, "handler"))
        # Release the lock: the NEXT checkpoint makes the deferred request durable.
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 4)
        self.assertIsNone(runner_stop.pending_deferred_request())
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)

    def test_deferred_slot_keeps_the_highest_level(self):
        self._hold_lock()
        runner_stop.request_stop_nowait(self.run_dir, 1, "first")
        runner_stop.request_stop_nowait(self.run_dir, 4, "second")
        runner_stop.request_stop_nowait(self.run_dir, 2, "third")
        self.assertEqual(runner_stop.pending_deferred_request(), (4, "second"))

    def test_drained_request_still_respects_monotonicity(self):
        runner_stop.request_stop(self.run_dir, 4, "already-hard")
        handle = self._hold_lock()
        runner_stop.request_stop_nowait(self.run_dir, 1, "handler")
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        # Draining a LOWER deferred level must not downgrade the durable record.
        self.assertEqual(runner_stop.poll_stop(self.run_dir), 4)
        self.assertEqual(runner_stop.read_stop_request(self.run_dir).level, 4)

    def test_a_failing_drain_leaves_the_request_pending(self):
        self._hold_lock()
        runner_stop.request_stop_nowait(self.run_dir, 3, "handler")
        with mock.patch.object(
            runner_stop,
            "request_stop",
            side_effect=runner_stop.StopRequestError("busy"),
        ):
            self.assertIsNone(runner_stop.poll_stop(self.run_dir))
        self.assertEqual(
            runner_stop.pending_deferred_request(),
            (3, "handler"),
            "a failed drain must never drop the operator's request",
        )

    def test_nowait_defers_rather_than_raising_on_a_filesystem_failure(self):
        # A handler must never propagate an exception, even if the control dir is unusable.
        with mock.patch.object(
            runner_stop.Path, "mkdir", side_effect=OSError(errno.EROFS, "read-only")
        ):
            result = runner_stop.request_stop_nowait(self.run_dir, 4, "handler")
        self.assertTrue(result.deferred)
        self.assertEqual(runner_stop.pending_deferred_request(), (4, "handler"))

    def test_nowait_rejects_an_invalid_level(self):
        with self.assertRaises(ValueError):
            runner_stop.request_stop_nowait(self.run_dir, 9, "handler")


class LockContentionTests(unittest.TestCase):
    """`request_stop` fails LOUDLY on a stuck lock rather than hanging forever."""

    def test_request_stop_raises_when_the_lock_stays_contended(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            lock_path = runner_stop.stop_request_lock_path(run_dir)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                started = time.monotonic()
                with self.assertRaises(runner_stop.StopRequestError):
                    runner_stop.request_stop(run_dir, 3, "blocked", timeout=0.2)
                elapsed = time.monotonic() - started
            self.assertLess(elapsed, 10.0, "must fail fast, not hang")

    def test_the_run_lock_is_not_reused_for_stop_requests(self):
        # Scope fence: `driver.lock` is a DIFFERENT lock with a run-long lifetime. Reusing it
        # would make an out-of-band `stop` impossible while a run holds it.
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            runner_stop.request_stop(run_dir, 3, "tester")
            self.assertFalse((run_dir / "driver.lock").exists())
            self.assertTrue((run_dir / "stop-request.lock").exists())

    def test_a_held_driver_lock_does_not_prevent_a_stop_request(self):
        # The out-of-band `stop` case: a live run holds driver.lock; a stop must still be
        # recordable from another process.
        from agent_workflows import oc_runipd

        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            with oc_runipd.run_lock(run_dir):
                result = runner_stop.request_stop(run_dir, 4, "second-terminal")
            self.assertTrue(result.accepted)
            self.assertEqual(runner_stop.read_stop_request(run_dir).level, 4)


if __name__ == "__main__":
    unittest.main()
