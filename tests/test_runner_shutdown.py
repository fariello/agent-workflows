#!/usr/bin/env python3
"""Tests for the shared clean-shutdown routine (runstop Phase 0, plan `2ouj70`).

Two kinds of test live here, and the distinction matters:

1. UNIT tests of `runner_shutdown.clean_shutdown` and its four invariants (spec `c4gd2h`
   R1-R4, R6, R23). These assert the routine's real behavior against the process table, the
   filesystem, and `git status` output, never against code structure.
2. CHARACTERIZATION tests that PIN TODAY's behavior so a later phase changing it must do so
   consciously. Each carries a comment naming the defect it pins (backlog `kjzlgw` observation,
   spec section 0.1). Two of these deliberately record the CURRENT, BROKEN state, so they are
   expected to be UPDATED (not deleted) by Phases 1-5.

Subprocess-spawning tests carry the `slow` marker, because `pyproject.toml` `addopts` is
`-m 'not slow'` by default; run this file with `-m ''` (or via `make test-all`).
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agent_workflows import agy_runipd as agy
from agent_workflows import oc_runipd as oc
from agent_workflows import runner_shutdown as rs

# A child that ignores the polite signals, so only the SIGKILL escalation can reap it. This is
# how "the driver left an orphan" is reproduced without a real `opencode`.
_STUBBORN_CHILD = (
    "import signal, time\n"
    "signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    "print('up', flush=True)\n"
    "time.sleep(600)\n"
)

# A child that spawns a GRANDCHILD in the same process group, then reports both pids. Reaping the
# direct child alone leaves the grandchild alive and reparented, which is spec R1's actual target.
_CHILD_WITH_GRANDCHILD = (
    "import subprocess, sys, time\n"
    "kid = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
    "print(kid.pid, flush=True)\n"
    "time.sleep(600)\n"
)

# Holds an flock on a path until killed; used to observe real lock state.
_LOCK_HOLDER = (
    "import fcntl, os, sys, time\n"
    "h = open(sys.argv[1], 'a+')\n"
    "fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "h.seek(0); h.truncate()\n"
    "h.write('pid=%d started=test\\n' % os.getpid()); h.flush()\n"
    "print('locked', flush=True)\n"
    "time.sleep(600)\n"
)


def _pid_alive(pid: int) -> bool:
    """Is ``pid`` present in the process table (any state except fully reaped)?

    Observed via `os.kill(pid, 0)`, which is the process table, not a code claim.
    """

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_gone(pid: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.05)
    return not _pid_alive(pid)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout


def _init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    (repo / "tracked.txt").write_text("original\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _write_state(run_dir: Path, queue: list[dict], repo: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": run_dir.name,
                "repo": str(repo),
                "queue": queue,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _take_lock(run_dir: Path) -> rs.RunLockHandle:
    lock_path = run_dir / "driver.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()} started=test\n")
    handle.flush()
    return rs.RunLockHandle(path=lock_path, handle=handle)


class SingleReaperTests(unittest.TestCase):
    """Spec R5: exactly ONE reaper implementation, which both drivers delegate to."""

    def test_both_drivers_delegate_to_the_shared_reaper(self):
        """CID-1, repo-wide: neither driver may carry its own escalation loop.

        Asserted structurally on PURPOSE here (this is the anti-duplication invariant), by
        checking each driver's `terminate_process` body calls into `runner_shutdown` and does
        not itself signal. The behavioral proof that the reaper works lives in the R1 tests.
        """

        import inspect

        for mod in (oc, agy):
            src = inspect.getsource(mod.terminate_process)
            self.assertIn(
                "runner_shutdown.terminate_process",
                src,
                f"{mod.__name__}.terminate_process must delegate to the shared reaper",
            )
            for banned in ("killpg", "SIGKILL", "send_signal"):
                self.assertNotIn(
                    banned,
                    src,
                    f"{mod.__name__}.terminate_process must not re-implement signalling",
                )

    def test_driver_grace_constants_are_honored_through_the_delegation(self):
        """A test tuning the driver's module constants must still affect the shared reaper."""

        seen: dict[str, float | None] = {}
        real = rs.terminate_process

        def spy(process, *, sigint_grace=None, sigterm_grace=None):
            seen["sigint"] = sigint_grace
            seen["sigterm"] = sigterm_grace
            return real(process, sigint_grace=sigint_grace, sigterm_grace=sigterm_grace)

        orig_int, orig_term = oc._SIGINT_GRACE_SECONDS, oc._SIGTERM_GRACE_SECONDS
        rs.terminate_process = spy  # type: ignore[assignment]
        try:
            oc._SIGINT_GRACE_SECONDS = 0.11
            oc._SIGTERM_GRACE_SECONDS = 0.22
            proc = subprocess.Popen([sys.executable, "-c", "pass"])
            proc.wait()
            oc.terminate_process(proc)
        finally:
            rs.terminate_process = real  # type: ignore[assignment]
            oc._SIGINT_GRACE_SECONDS, oc._SIGTERM_GRACE_SECONDS = orig_int, orig_term
        self.assertEqual(seen, {"sigint": 0.11, "sigterm": 0.22})

    def test_ledger_status_vocabulary_covers_both_drivers(self):
        """R3's coherence check must know every status a driver can persist."""

        for mod in (oc, agy):
            self.assertEqual(
                set(mod.TERMINAL_STATES) - set(rs.KNOWN_ITEM_STATUSES),
                set(),
                f"{mod.__name__} can persist a status the R3 check would call undefined",
            )


@pytest.mark.slow
class ReapTests(unittest.TestCase):
    """Spec R1: no descendant left alive; observed on the PROCESS TABLE."""

    def test_clean_shutdown_reaps_a_signal_ignoring_child(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", _STUBBORN_CHILD],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert proc.stdout is not None
        self.assertEqual(proc.stdout.readline().strip(), "up")
        pid = proc.pid
        self.assertTrue(_pid_alive(pid), "child must be alive before the shutdown")

        orig = (rs.DEFAULT_SIGINT_GRACE_SECONDS, rs.DEFAULT_SIGTERM_GRACE_SECONDS)
        rs.DEFAULT_SIGINT_GRACE_SECONDS = 0.3
        rs.DEFAULT_SIGTERM_GRACE_SECONDS = 0.3
        try:
            report = rs.clean_shutdown(process=proc)
        finally:
            rs.DEFAULT_SIGINT_GRACE_SECONDS, rs.DEFAULT_SIGTERM_GRACE_SECONDS = orig
        proc.wait(timeout=10)
        self.assertTrue(
            _wait_gone(pid),
            f"pid {pid} still in the process table after clean_shutdown",
        )
        children = report.result(rs.INVARIANT_CHILDREN)
        self.assertTrue(children.attempted)
        self.assertTrue(children.satisfied, report.render())
        self.assertIn(pid, report.reaped_pids)

    def test_clean_shutdown_reaps_a_grandchild_not_just_the_direct_child(self):
        """The whole process GROUP dies; a grandchild must not survive reparented."""

        proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD_WITH_GRANDCHILD],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert proc.stdout is not None
        grandchild = int(proc.stdout.readline().strip())
        self.assertTrue(_pid_alive(grandchild))
        try:
            rs.clean_shutdown(process=proc)
            proc.wait(timeout=10)
            self.assertTrue(_wait_gone(proc.pid), "direct child survived")
            self.assertTrue(
                _wait_gone(grandchild),
                f"grandchild {grandchild} survived and is now reparented (spec R1 violated)",
            )
        finally:
            for pid in (grandchild, proc.pid):
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGKILL)

    def test_tracked_children_are_reaped_without_being_passed_in(self):
        """R1 must hold at the lock-holding layer, which does not hold the Popen objects."""

        proc = subprocess.Popen(
            [sys.executable, "-c", _STUBBORN_CHILD],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert proc.stdout is not None
        proc.stdout.readline()
        rs.track_child(proc)
        orig = (rs.DEFAULT_SIGINT_GRACE_SECONDS, rs.DEFAULT_SIGTERM_GRACE_SECONDS)
        rs.DEFAULT_SIGINT_GRACE_SECONDS = 0.3
        rs.DEFAULT_SIGTERM_GRACE_SECONDS = 0.3
        try:
            # No `process=` argument: the routine must find the tracked child by itself.
            report = rs.clean_shutdown()
        finally:
            rs.DEFAULT_SIGINT_GRACE_SECONDS, rs.DEFAULT_SIGTERM_GRACE_SECONDS = orig
        proc.wait(timeout=10)
        self.assertTrue(_wait_gone(proc.pid))
        self.assertIn(proc.pid, report.reaped_pids, report.render())


class LockReleaseTests(unittest.TestCase):
    """Spec R2: the lock is released OBSERVABLY (flock dropped AND the file removed)."""

    def test_lock_file_is_gone_and_a_fresh_process_can_acquire(self):
        with TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            lock = _take_lock(run_dir)
            self.assertTrue((run_dir / "driver.lock").is_file())
            self.assertFalse(rs.lock_is_free(run_dir / "driver.lock"))

            report = rs.clean_shutdown(lock=lock)

            exists_after = (run_dir / "driver.lock").exists()
            free_after = rs.lock_is_free(run_dir / "driver.lock")
            # Print the R2 evidence BEFORE the probe below, because the probe legitimately
            # RE-CREATES the file by opening it 'a+'; printing afterwards would misreport the
            # post-shutdown state (plan `2ouj70` V-02).
            print(f"driver.lock exists after clean_shutdown: {exists_after}")
            print(f"lock_is_free after clean_shutdown: {free_after}")
            print(report.result(rs.INVARIANT_LOCK).line())

            self.assertFalse(
                exists_after, "driver.lock must not survive a clean shutdown"
            )
            self.assertTrue(free_after)
            # A genuinely FRESH process (not this one) must be able to take the lock.
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import fcntl, sys\n"
                    "h = open(sys.argv[1], 'a+')\n"
                    "fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
                    "print('acquired')\n",
                    str(run_dir / "driver.lock"),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertEqual(probe.stdout.strip(), "acquired")
            self.assertTrue(report.result(rs.INVARIANT_LOCK).satisfied, report.render())
            print(f"fresh process flock(LOCK_EX|LOCK_NB): {probe.stdout.strip()}")

    def test_release_is_idempotent(self):
        """`run_lock`'s finally and `clean_shutdown` may both release; that must be safe."""

        with TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            lock = _take_lock(run_dir)
            rs.clean_shutdown(lock=lock)
            lock.release()  # must not raise
            self.assertTrue(lock.released)

    @pytest.mark.slow
    def test_a_lock_held_by_another_live_process_is_never_unlinked(self):
        """Removing someone else's lock would be worse than leaving residue."""

        with TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            run_dir.mkdir(parents=True)
            lock_path = run_dir / "driver.lock"
            holder = subprocess.Popen(
                [sys.executable, "-c", _LOCK_HOLDER, str(lock_path)],
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert holder.stdout is not None
                self.assertEqual(holder.stdout.readline().strip(), "locked")
                # We do NOT hold this lock; a handle pointing at it must refuse to unlink.
                foreign = lock_path.open("a+")
                handle = rs.RunLockHandle(path=lock_path, handle=foreign)
                # Simulate the dangerous case: the path was replaced under us, so our fd is not
                # the file at that path any more.
                self.assertTrue(handle.holds_current_path())
                other = run_dir / "other.lock"
                other.write_text("x", encoding="utf-8")
                os.replace(other, lock_path)
                self.assertFalse(
                    handle.holds_current_path(),
                    "a replaced path must not look like ours",
                )
                handle.release()
                self.assertFalse(handle.unlinked)
                self.assertTrue(
                    lock_path.exists(), "another process's lock file was removed"
                )
                print(
                    "foreign lock: unlinked="
                    f"{handle.unlinked} exists={lock_path.exists()} (never removed)"
                )
            finally:
                holder.kill()
                holder.wait(timeout=10)

    def test_run_lock_still_releases_on_the_normal_path_in_both_drivers(self):
        for mod in (oc, agy):
            with TemporaryDirectory() as td:
                run_dir = Path(td) / "run"
                run_dir.mkdir(parents=True)
                with mod.run_lock(run_dir) as lock:
                    self.assertIsInstance(lock, rs.RunLockHandle)
                    self.assertTrue((run_dir / "driver.lock").is_file())
                    self.assertFalse(rs.lock_is_free(run_dir / "driver.lock"))
                self.assertTrue(lock.released)
                self.assertTrue(rs.lock_is_free(run_dir / "driver.lock"))

    def test_run_lock_still_refuses_a_second_live_holder_in_both_drivers(self):
        for mod in (oc, agy):
            with TemporaryDirectory() as td:
                run_dir = Path(td) / "run"
                run_dir.mkdir(parents=True)
                with mod.run_lock(run_dir):
                    with self.assertRaises(mod.DriverError):
                        with mod.run_lock(run_dir):
                            pass


class LedgerCoherenceTests(unittest.TestCase):
    """Spec R3: the ledger parses and every item is in a defined state; observed, not rewritten."""

    def test_coherent_ledger_is_reported_satisfied(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run"
            _write_state(
                run_dir,
                [
                    {"id6": "aaaaaa", "status": "executed"},
                    {"id6": "bbbbbb", "status": "interrupted"},
                ],
                root,
            )
            report = rs.clean_shutdown(run_dir=run_dir)
            ledger = report.result(rs.INVARIANT_LEDGER)
            self.assertTrue(ledger.satisfied, report.render())
            self.assertIn("2 item(s)", ledger.detail)

    def test_undefined_item_state_is_reported_not_hidden(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run"
            _write_state(run_dir, [{"id6": "cccccc", "status": "who-knows"}], root)
            report = rs.clean_shutdown(run_dir=run_dir)
            ledger = report.result(rs.INVARIANT_LEDGER)
            self.assertFalse(ledger.satisfied)
            self.assertIn("cccccc=who-knows", ledger.detail)

    def test_unparseable_ledger_is_reported_not_raised(self):
        with TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text("{not json", encoding="utf-8")
            report = rs.clean_shutdown(run_dir=run_dir)
            self.assertFalse(report.result(rs.INVARIANT_LEDGER).satisfied)
            self.assertIn("does not parse", report.result(rs.INVARIANT_LEDGER).detail)

    def test_clean_shutdown_does_not_rewrite_the_ledger(self):
        """Phase 0 only OBSERVES the ledger, so it cannot corrupt it mid-write."""

        with TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run"
            _write_state(run_dir, [{"id6": "aaaaaa", "status": "running"}], root)
            before = (run_dir / "state.json").read_bytes()
            mtime_before = (run_dir / "state.json").stat().st_mtime_ns
            rs.clean_shutdown(run_dir=run_dir)
            self.assertEqual(before, (run_dir / "state.json").read_bytes())
            self.assertEqual(mtime_before, (run_dir / "state.json").stat().st_mtime_ns)


class TreeObservationTests(unittest.TestCase):
    """Spec R4 as OBSERVE-AND-REPORT: dirty paths enumerated, tree byte-for-byte untouched."""

    def test_dirty_paths_are_enumerated_and_the_tree_is_not_modified(self):
        with TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "tracked.txt").write_text("edited by the agent\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("new file\n", encoding="utf-8")

            status_before = _git(repo, "status", "--porcelain")
            content_before = {
                p.name: p.read_bytes()
                for p in (repo / "tracked.txt", repo / "untracked.txt")
            }
            self.assertNotEqual(status_before.strip(), "")

            report = rs.clean_shutdown(repo=repo)

            status_after = _git(repo, "status", "--porcelain")
            content_after = {
                p.name: p.read_bytes()
                for p in (repo / "tracked.txt", repo / "untracked.txt")
            }
            # The R4 evidence is a before/after comparison proving NOTHING was relocated.
            self.assertEqual(status_before, status_after)
            self.assertEqual(content_before, content_after)
            self.assertEqual(
                _git(repo, "stash", "list").strip(), "", "cleanup must not stash"
            )

            # Print the R4 evidence so a validator can PASTE the before/after comparison rather
            # than trusting a green dot (plan `2ouj70` V-03).
            print("git status --porcelain BEFORE clean_shutdown:")
            print(status_before.rstrip("\n"))
            print("git status --porcelain AFTER clean_shutdown:")
            print(status_after.rstrip("\n"))
            print(f"identical: {status_before == status_after}")
            print(f"file contents identical: {content_before == content_after}")
            print(f"git stash list: {_git(repo, 'stash', 'list').strip()!r}")

            tree = report.result(rs.INVARIANT_TREE)
            self.assertTrue(tree.attempted)
            self.assertTrue(tree.satisfied, report.render())
            self.assertEqual(
                sorted(report.dirty_paths),
                sorted(line for line in status_before.splitlines() if line.strip()),
            )
            self.assertIn("tracked.txt", report.render())
            self.assertIn("nothing stashed, reset, or moved", tree.detail)
            print("ShutdownReport R4 section:")
            print(report.render())

    def test_clean_tree_reports_no_dirty_paths(self):
        with TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            report = rs.clean_shutdown(repo=repo)
            self.assertTrue(report.result(rs.INVARIANT_TREE).satisfied)
            self.assertEqual(report.dirty_paths, [])

    def test_non_repo_path_is_reported_not_raised(self):
        with TemporaryDirectory() as td:
            report = rs.clean_shutdown(repo=Path(td) / "not-a-repo")
            self.assertFalse(report.result(rs.INVARIANT_TREE).satisfied)
            self.assertTrue(report.result(rs.INVARIANT_TREE).attempted)


class BestEffortTests(unittest.TestCase):
    """Spec R6/R23: every invariant is attempted even when an earlier one fails, and reported."""

    def test_a_raising_reap_does_not_skip_the_other_three_invariants(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            repo = _init_repo(root)
            run_dir = root / "run"
            _write_state(run_dir, [{"id6": "aaaaaa", "status": "executed"}], repo)
            lock = _take_lock(run_dir)

            class Exploding:
                pid = -1

                def poll(self):
                    raise RuntimeError("injected reap failure")

            report = rs.clean_shutdown(
                process=Exploding(),  # type: ignore[arg-type]
                lock=lock,
                run_dir=run_dir,
                repo=repo,
            )

            rendered = report.render()
            children = report.result(rs.INVARIANT_CHILDREN)
            self.assertFalse(children.satisfied, rendered)
            self.assertIn("injected reap failure", children.error or "", rendered)
            # Steps 2-4 must still have been ATTEMPTED and satisfied.
            for name in (rs.INVARIANT_LOCK, rs.INVARIANT_LEDGER, rs.INVARIANT_TREE):
                inv = report.result(name)
                self.assertTrue(inv.attempted, f"{name} was skipped:\n{rendered}")
                self.assertTrue(inv.satisfied, f"{name} failed:\n{rendered}")
            self.assertFalse(report.all_satisfied)
            self.assertFalse((run_dir / "driver.lock").exists())
            # R23: the report names the unsatisfied invariant instead of claiming success.
            self.assertIn("children_reaped", rendered)
            self.assertIn("NOT satisfied", rendered)
            print("ShutdownReport:\n" + rendered)
            print(
                "ShutdownReport dict: " + json.dumps(report.to_dict(), sort_keys=True)
            )

    def test_missing_context_is_reported_as_skipped_not_as_success(self):
        """R23: an invariant with no inputs must not be claimed satisfied."""

        report = rs.clean_shutdown()
        for name in (rs.INVARIANT_LOCK, rs.INVARIANT_LEDGER, rs.INVARIANT_TREE):
            inv = report.result(name)
            self.assertFalse(inv.attempted)
            self.assertFalse(inv.satisfied)
            self.assertIn("SKIPPED", inv.line())
        self.assertFalse(report.all_satisfied)

    def test_all_four_invariants_satisfied_end_to_end(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            repo = _init_repo(root)
            run_dir = root / "run"
            _write_state(run_dir, [{"id6": "aaaaaa", "status": "executed"}], repo)
            lock = _take_lock(run_dir)
            report = rs.clean_shutdown(lock=lock, run_dir=run_dir, repo=repo)
            self.assertTrue(report.all_satisfied, report.render())
            self.assertEqual(report.unsatisfied(), [])


@pytest.mark.slow
class LockedRunWiringTests(unittest.TestCase):
    """E-04: the FULL routine runs at the lock-holding `main` layer in BOTH drivers."""

    def test_locked_run_releases_the_lock_and_reaps_on_the_success_path(self):
        for mod in (oc, agy):
            with TemporaryDirectory() as td:
                root = Path(td)
                repo = _init_repo(root)
                run_dir = root / "run"
                _write_state(run_dir, [{"id6": "aaaaaa", "status": "executed"}], repo)
                proc = subprocess.Popen(
                    [sys.executable, "-c", _STUBBORN_CHILD],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True,
                )
                assert proc.stdout is not None
                proc.stdout.readline()
                rs.track_child(proc)
                orig = (
                    rs.DEFAULT_SIGINT_GRACE_SECONDS,
                    rs.DEFAULT_SIGTERM_GRACE_SECONDS,
                )
                rs.DEFAULT_SIGINT_GRACE_SECONDS = 0.3
                rs.DEFAULT_SIGTERM_GRACE_SECONDS = 0.3
                try:
                    with mod.locked_run(run_dir):
                        self.assertTrue((run_dir / "driver.lock").is_file())
                finally:
                    (
                        rs.DEFAULT_SIGINT_GRACE_SECONDS,
                        rs.DEFAULT_SIGTERM_GRACE_SECONDS,
                    ) = orig
                proc.wait(timeout=10)
                self.assertTrue(
                    _wait_gone(proc.pid), f"{mod.__name__}: child survived locked_run"
                )
                self.assertFalse(
                    (run_dir / "driver.lock").exists(),
                    f"{mod.__name__}: lock file survived locked_run",
                )

    def test_locked_run_cleans_up_on_the_failure_path_too(self):
        """Spec R6: cleanup runs even when the wind-down phase raises."""

        for mod in (oc, agy):
            with TemporaryDirectory() as td:
                root = Path(td)
                repo = _init_repo(root)
                run_dir = root / "run"
                _write_state(run_dir, [{"id6": "aaaaaa", "status": "running"}], repo)
                proc = subprocess.Popen(
                    [sys.executable, "-c", _STUBBORN_CHILD],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True,
                )
                assert proc.stdout is not None
                proc.stdout.readline()
                rs.track_child(proc)
                orig = (
                    rs.DEFAULT_SIGINT_GRACE_SECONDS,
                    rs.DEFAULT_SIGTERM_GRACE_SECONDS,
                )
                rs.DEFAULT_SIGINT_GRACE_SECONDS = 0.3
                rs.DEFAULT_SIGTERM_GRACE_SECONDS = 0.3
                try:
                    with self.assertRaises(KeyboardInterrupt):
                        with mod.locked_run(run_dir):
                            raise KeyboardInterrupt
                finally:
                    (
                        rs.DEFAULT_SIGINT_GRACE_SECONDS,
                        rs.DEFAULT_SIGTERM_GRACE_SECONDS,
                    ) = orig
                proc.wait(timeout=10)
                self.assertTrue(
                    _wait_gone(proc.pid),
                    f"{mod.__name__}: child survived an aborted locked_run",
                )
                self.assertFalse(
                    (run_dir / "driver.lock").exists(),
                    f"{mod.__name__}: lock file survived an aborted locked_run",
                )

    def test_locked_run_does_not_modify_a_dirty_tree(self):
        for mod in (oc, agy):
            with TemporaryDirectory() as td:
                root = Path(td)
                repo = _init_repo(root)
                run_dir = root / "run"
                _write_state(run_dir, [{"id6": "aaaaaa", "status": "executed"}], repo)
                (repo / "tracked.txt").write_text("agent edit\n", encoding="utf-8")
                before = _git(repo, "status", "--porcelain")
                with mod.locked_run(run_dir):
                    pass
                self.assertEqual(before, _git(repo, "status", "--porcelain"))
                self.assertEqual(_git(repo, "stash", "list").strip(), "")


@pytest.mark.slow
class CharacterizationTests(unittest.TestCase):
    """PIN today's behavior so Phases 1-5 must consciously change these, not re-assert them.

    Each test names the defect it pins. Reference: backlog `kjzlgw` observation, spec `c4gd2h`
    section 0.1 (SIGTERM printed `Terminated`, the child was reparented to init and kept writing,
    `driver.lock` was left holding a dead PID, and the tree was left mid-edit).
    """

    def test_pins_a_bare_terminate_of_the_wrong_process_leaves_an_orphan(self):
        """DEFECT PINNED: reaping only the DIRECT child leaves the grandchild alive.

        This is spec R1's target and today's failure mode when a driver dies without running the
        shared routine: the surviving descendant is reparented and keeps writing the tree. The
        test drives the pre-fix behavior deliberately (`proc.kill()`, i.e. what a bare
        `SIGKILL`-the-driver does) rather than `clean_shutdown`, which fixes it.

        A later phase that makes an unrequested driver death also reap the tree MUST UPDATE this
        test, not delete it.
        """

        proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD_WITH_GRANDCHILD],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert proc.stdout is not None
        grandchild = int(proc.stdout.readline().strip())
        try:
            proc.kill()  # only the direct child: exactly what today's bare death does
            proc.wait(timeout=10)
            self.assertTrue(_wait_gone(proc.pid), "direct child should be gone")
            time.sleep(0.5)
            self.assertTrue(
                _pid_alive(grandchild),
                "PINNED BEHAVIOR CHANGED: the grandchild no longer survives a bare kill; "
                "update this characterization test consciously",
            )
            ppid = "unknown"
            stat = Path(f"/proc/{grandchild}/stat")
            if stat.is_file():  # Linux; the reparenting is visible in field 4 (ppid)
                ppid = stat.read_text(encoding="utf-8").rsplit(") ", 1)[-1].split()[1]
            print(
                f"orphan observed on the process table: grandchild pid {grandchild} is alive "
                f"after its parent pid {proc.pid} was killed; its ppid is now {ppid}"
            )
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.kill(grandchild, signal.SIGKILL)
            _wait_gone(grandchild)

    def test_pins_hard_abort_leaves_the_lock_file_while_the_lock_itself_is_free(self):
        """DEFECT PINNED (cosmetic, NOT a liveness bug): a hard-killed driver leaves
        `driver.lock` on disk holding a DEAD PID, while the `flock` is already released by the
        kernel.

        BOTH halves are asserted deliberately. The file surviving is the real, observable residue
        (`kjzlgw`). But it does NOT block a later run: the OS drops an `flock` on holder death,
        verified here by acquiring it from a fresh process. Asserting "a stale lock blocks the
        next run" would pin a defect that does not exist, and `run_viewer.driver_holder_state`
        already documents acquirability as the authoritative liveness signal.
        """

        with TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            run_dir.mkdir(parents=True)
            lock_path = run_dir / "driver.lock"
            holder = subprocess.Popen(
                [sys.executable, "-c", _LOCK_HOLDER, str(lock_path)],
                stdout=subprocess.PIPE,
                text=True,
            )
            assert holder.stdout is not None
            self.assertEqual(holder.stdout.readline().strip(), "locked")
            holder_pid = holder.pid
            self.assertFalse(rs.lock_is_free(lock_path), "live holder must be detected")

            holder.kill()  # a hard abort that bypasses every cleanup path
            holder.wait(timeout=10)
            self.assertTrue(_wait_gone(holder_pid))

            # HALF 1: the file survives, recording a now-dead PID.
            self.assertTrue(
                lock_path.is_file(),
                "PINNED BEHAVIOR CHANGED: driver.lock no longer survives a hard abort",
            )
            recorded = lock_path.read_text(encoding="utf-8").strip()
            self.assertIn(f"pid={holder_pid}", recorded)
            self.assertFalse(_pid_alive(holder_pid), "the recorded PID is dead")
            print(
                f"stale driver.lock contents: {recorded!r} (pid {holder_pid} is dead)"
            )

            # HALF 2: the lock itself is ALREADY FREE, so this residue blocks nothing.
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import fcntl, sys\n"
                    "h = open(sys.argv[1], 'a+')\n"
                    "fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
                    "print('acquired-by-fresh-process')\n",
                    str(lock_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertEqual(probe.stdout.strip(), "acquired-by-fresh-process")
            print(f"fresh flock on the stale file: {probe.stdout.strip()}")
            self.assertTrue(rs.lock_is_free(lock_path))

    def test_pins_that_a_hard_abort_leaves_the_tree_mid_edit(self):
        """DEFECT PINNED: a hard abort leaves the working tree dirty with no record of it.

        The Phase 0 fix is to ENUMERATE and REPORT those paths (R4 observe-and-report), never to
        stash or revert them. Later phases add the stop levels that reach this routine; they must
        not turn this into an auto-relocation.
        """

        with TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            (repo / "tracked.txt").write_text("half-written\n", encoding="utf-8")
            dirty = _git(repo, "status", "--porcelain")
            self.assertIn("tracked.txt", dirty)
            # Today nothing records this. The shared routine at least reports it now.
            report = rs.clean_shutdown(repo=repo)
            self.assertTrue(any("tracked.txt" in p for p in report.dirty_paths))
            self.assertEqual(dirty, _git(repo, "status", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
