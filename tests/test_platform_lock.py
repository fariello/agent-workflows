"""The ONE file lock: mutual exclusion, non-re-entrancy, probe safety, and import portability.

IPD `y6mfgo` E-04/E-05/E-07. Every test here exercises a property a refactor can break SILENTLY,
which is why several of them use REAL SUBPROCESSES rather than mocks: the properties under test are
OS behaviors (a kernel lock excludes another process; the kernel drops a lock when its holder dies),
and a mock would assert our beliefs about the OS instead of the OS.

WHY A CROSS-PROCESS TEST IS MANDATORY AND A SAME-PROCESS ONE IS NOT SUFFICIENT: the Windows
primitive `msvcrt.locking` locks a BYTE RANGE from the current file position rather than the whole
file, so a naive port lets two processes lock DISJOINT ranges of one file and BOTH believe they hold
it. That is a silent mutual-exclusion failure, and it is the hazard that decided this code should use
`filelock` rather than a hand-rolled abstraction (`y6mfgo` F3).

WHY A SAME-PROCESS TEST IS ALSO MANDATORY AND THE CROSS-PROCESS ONE CANNOT REPLACE IT: `filelock` is
RE-ENTRANT per lock object, via an internal counter, where `fcntl.flock` is not. The counter is
process-local, so a cross-process test cannot see it at all. `runner_stop._sidecar_lock` DEPENDS on a
same-process second acquire being REFUSED, because that refusal is what diverts a signal handler to
its process-local slot instead of letting it re-enter a monotonic read-modify-write (`y6mfgo` F7).
Neither test substitutes for the other; both are required.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import platform_lock, run_viewer, runner_shutdown
from tests.support import REPO_ROOT

_CHILD_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
# Every subprocess probe is bounded, so a reintroduced deadlock FAILS the suite rather than hanging it.
_CHILD_TIMEOUT = 30.0


def _run_child(source: str, *args: str, timeout: float = _CHILD_TIMEOUT):
    with tempfile.TemporaryDirectory() as temp:
        script = Path(temp) / "probe.py"
        script.write_text(textwrap.dedent(source), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script), *args],
            env=_CHILD_ENV,
            text=True,
            capture_output=True,
            timeout=timeout,
        )


# A child that TAKES the lock through the helper and holds it until its stdin closes, so the parent
# controls the contention window precisely.
_HOLDER = """
import sys
from pathlib import Path
from agent_workflows import platform_lock

held = platform_lock.acquire(Path(sys.argv[1]))
sys.stdout.write("locked\\n")
sys.stdout.flush()
sys.stdin.read()
held.release()
"""


class _HolderProcess:
    """A live subprocess holding the lock, as a context manager."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._proc: subprocess.Popen | None = None

    def __enter__(self) -> subprocess.Popen:
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "holder.py"
            script.write_text(textwrap.dedent(_HOLDER), encoding="utf-8")
            self._proc = subprocess.Popen(
                [sys.executable, str(script), str(self._path)],
                env=_CHILD_ENV,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            assert self._proc.stdout is not None
            line = self._proc.stdout.readline().strip()
            assert line == "locked", f"holder failed to take the lock: {line!r}"
            return self._proc

    def __exit__(self, *_exc: object) -> None:
        proc = self._proc
        if proc is None:
            return
        if proc.poll() is None:
            assert proc.stdin is not None
            with open(os.devnull):
                try:
                    proc.stdin.close()
                except OSError:
                    pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


class MutualExclusionTests(unittest.TestCase):
    """E-04: the lock EXCLUDES, proven across two real PROCESSES."""

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def test_a_second_process_is_refused_immediately(self):
        """TWO PROCESSES, not two handles: the second acquire must fail fast, not hang or succeed."""

        path = self.tmp / "excl.lock"
        with _HolderProcess(path) as holder:
            self.assertIsNone(holder.poll(), "the holder must still be alive")
            started = time.monotonic()
            with self.assertRaises(platform_lock.LockBusy):
                platform_lock.acquire(path)
            elapsed = time.monotonic() - started
            # "Immediately" is part of the contract: several callers convert this refusal into an
            # operator-facing message, so a silent wait would be a hang, not a refusal.
            self.assertLess(elapsed, 5.0, "a non-blocking refusal must not wait")
            print(
                f"second PROCESS refused in {elapsed:.4f}s with LockBusy "
                f"(holder pid {holder.pid} still alive)"
            )

    def test_release_frees_the_lock_for_another_process(self):
        path = self.tmp / "rel.lock"
        held = platform_lock.acquire(path)
        probe_while_held = _run_child(
            """
            import sys
            from pathlib import Path
            from agent_workflows import platform_lock
            try:
                platform_lock.acquire(Path(sys.argv[1]))
                print("ACQUIRED")
            except platform_lock.LockBusy:
                print("REFUSED")
            """,
            str(path),
        )
        self.assertEqual(
            probe_while_held.stdout.strip(), "REFUSED", probe_while_held.stderr
        )
        held.release()
        probe_after = _run_child(
            """
            import sys
            from pathlib import Path
            from agent_workflows import platform_lock
            try:
                platform_lock.acquire(Path(sys.argv[1]))
                print("ACQUIRED")
            except platform_lock.LockBusy:
                print("REFUSED")
            """,
            str(path),
        )
        self.assertEqual(probe_after.stdout.strip(), "ACQUIRED", probe_after.stderr)
        print("while held: REFUSED; after release: ACQUIRED (from a separate process)")

    def test_the_lock_is_dropped_when_its_holder_dies(self):
        """The property every liveness probe in this package depends on."""

        path = self.tmp / "death.lock"
        with _HolderProcess(path) as holder:
            self.assertFalse(platform_lock.probe_free(path))
            holder.kill()
            holder.wait(timeout=10)
        for _ in range(100):
            if platform_lock.probe_free(path):
                break
            time.sleep(0.05)
        self.assertTrue(
            platform_lock.probe_free(path), "the OS must drop the lock on holder death"
        )
        print("lock free after the holder was SIGKILLed")

    def test_release_is_idempotent(self):
        path = self.tmp / "idem.lock"
        held = platform_lock.acquire(path)
        held.release()
        held.release()  # must not raise
        self.assertFalse(held.is_held)


class NonReentrancyTests(unittest.TestCase):
    """E-04 / F7: a SAME-PROCESS second acquire is refused, exactly as a foreign one is.

    This is the case the cross-process test structurally cannot reach, and the one `runner_stop`'s
    signal-handler safety depends on.
    """

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def test_a_second_acquire_in_the_same_process_is_refused(self):
        path = self.tmp / "reentry.lock"
        first = platform_lock.acquire(path)
        self.addCleanup(first.release)
        with self.assertRaises(platform_lock.LockBusy):
            platform_lock.acquire(path)
        print("same-process second acquire: refused with LockBusy (NOT re-entrant)")

    def test_the_refusal_is_the_shape_runner_stop_dispatches_on(self):
        """`runner_stop._sidecar_lock` catches OSError and checks errno; both must hold."""

        import errno

        path = self.tmp / "shape.lock"
        first = platform_lock.acquire(path)
        self.addCleanup(first.release)
        try:
            platform_lock.acquire(path)
            self.fail("expected a refusal")
        except (
            OSError
        ) as exc:  # the base class every migrated call site already handled
            self.assertIsInstance(exc, platform_lock.LockBusy)
            self.assertIsInstance(exc, BlockingIOError)
            self.assertIn(
                exc.errno, (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK), exc.errno
            )
            print(
                f"refusal shape: {type(exc).__name__} -> BlockingIOError -> OSError, "
                f"errno={errno.errorcode.get(exc.errno, exc.errno)}"
            )

    def test_the_raw_filelock_object_would_have_been_reentrant(self):
        """CHARACTERIZATION of the hazard, so this suite proves it guards a REAL difference.

        If a future `filelock` stops being re-entrant per object, this test fails and the reasoning
        in `platform_lock` (construct a fresh object per acquire) can be revisited deliberately
        instead of being carried as folklore.
        """

        import filelock

        path = self.tmp / "raw.lock"
        shared = filelock.FileLock(str(path), timeout=0)
        shared.acquire()
        try:
            shared.acquire()  # SUCCEEDS: the per-object counter
            reentrant = True
            shared.release()
        except filelock.Timeout:
            reentrant = False
        finally:
            shared.release()
        self.assertTrue(
            reentrant,
            "PREMISE CHANGED: filelock is no longer re-entrant per object, so "
            "platform_lock's fresh-object-per-acquire rule can be reconsidered",
        )
        print(
            f"characterization: a SHARED filelock object IS re-entrant "
            f"(filelock {filelock.__version__}); platform_lock avoids it with a fresh object"
        )


class BlockingRegistryCallerTests(unittest.TestCase):
    """E-07 option (a): the ONE blocking caller still WAITS, and nothing else does."""

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def test_a_blocking_acquire_waits_for_the_holder_and_then_succeeds(self):
        """TWO PROCESSES: the second must WAIT and then SUCCEED, not raise.

        This is the semantics `project_registry.save_registry` had with its bare `fcntl.LOCK_EX`.
        A test that only showed the uncontended happy path would not demonstrate it.
        """

        path = self.tmp / "registry.json.lock"
        with _HolderProcess(path) as holder:
            # The lock really is held by a DIFFERENT, live process, which is the precondition that
            # makes the wait below meaningful rather than a wait on nothing.
            self.assertIsNone(holder.poll(), "the holder must be alive")
            self.assertNotEqual(holder.pid, os.getpid())
            self.assertEqual(platform_lock.probe_free(path), False)
            # The waiter starts while the lock is HELD, so it must block rather than fail.
            waiter = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import sys, time\n"
                    "from pathlib import Path\n"
                    "from agent_workflows import platform_lock\n"
                    "sys.stdout.write('waiting\\n'); sys.stdout.flush()\n"
                    "start = time.monotonic()\n"
                    "held = platform_lock.acquire(Path(sys.argv[1]), blocking=True)\n"
                    "sys.stdout.write('acquired-after-%.3fs\\n' % (time.monotonic() - start))\n"
                    "sys.stdout.flush()\n"
                    "held.release()\n",
                    str(path),
                ],
                env=_CHILD_ENV,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert waiter.stdout is not None
                self.assertEqual(waiter.stdout.readline().strip(), "waiting")
                # Give it a real chance to wrongly fail fast. If blocking were broken, it would
                # have exited by now with an exception.
                time.sleep(1.0)
                self.assertIsNone(
                    waiter.poll(),
                    "the blocking acquire FAILED FAST instead of waiting: this is the "
                    "semantic change `y6mfgo`'s Scope forbids",
                )
                print(
                    "blocking waiter is still blocked while the holder holds the lock"
                )
            except BaseException:
                waiter.kill()
                raise
        # The holder has now released (its context manager exited), so the waiter must proceed.
        out = waiter.stdout.readline().strip()
        waiter.wait(timeout=15)
        self.assertEqual(waiter.returncode, 0)
        self.assertTrue(
            out.startswith("acquired-after-"),
            f"the waiter must ACQUIRE after the holder releases, got {out!r}",
        )
        print(f"blocking waiter then succeeded: {out}")

    def test_the_default_is_non_blocking(self):
        """The default must refuse, or a driver could hang where it used to report cleanly."""

        path = self.tmp / "default.lock"
        with _HolderProcess(path):
            with self.assertRaises(platform_lock.LockBusy):
                platform_lock.acquire(path)
        print("default acquire (no blocking= argument): refused, did not wait")

    def test_project_registry_writes_survive_real_contention(self):
        """The real caller, exercised end to end: concurrent writers must all complete."""

        from agent_workflows import project_registry

        registry = self.tmp / "registry.json"
        writers = [
            subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import sys\n"
                    "from agent_workflows import project_registry\n"
                    "project_registry.save_registry(\n"
                    "    {'registry_version': 1, 'projects': {sys.argv[2]: {}}}, sys.argv[1]\n"
                    ")\n"
                    "print('wrote')\n",
                    str(registry),
                    f"p{n}",
                ],
                env=_CHILD_ENV,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for n in range(4)
        ]
        for writer in writers:
            out, err = writer.communicate(timeout=30)
            self.assertEqual(writer.returncode, 0, err)
            self.assertEqual(out.strip(), "wrote")
        # Every writer completed and the file is intact valid JSON (last writer wins; the point is
        # that nobody was refused and nothing was torn).
        loaded = project_registry.load_registry(str(registry))
        self.assertIn("projects", loaded)
        print(f"4 concurrent registry writers all completed; final: {loaded}")


class ProbeDoesNotMutateTests(unittest.TestCase):
    """D1: the PROBE observes without creating, truncating, or otherwise touching the file.

    These three assertions exist because routing the probes through `filelock` (the plan's literal
    "all fifteen sites" reading) would have broken all three: `filelock` opens with
    `O_CREAT | O_TRUNC`, so a probe through it CREATES an absent lock file and BLANKS a live
    holder's record even when the probe correctly reports the lock as held.
    """

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def test_probing_does_not_create_an_absent_lock_file(self):
        path = self.tmp / "absent.lock"
        self.assertFalse(path.exists())
        self.assertTrue(platform_lock.probe_free(path))
        self.assertFalse(
            path.exists(),
            "probing must not resurrect a lock file that was deliberately removed",
        )
        print("probe of an absent lock file: reported free, created nothing")

    def test_probing_a_live_holder_preserves_its_record(self):
        """The driver records `pid=` INSIDE driver.lock and `aw runs` reads it back."""

        path = self.tmp / "driver.lock"
        with _HolderProcess(path) as holder:
            path.write_text(f"pid={holder.pid} started=now\n", encoding="utf-8")
            recorded = path.read_text(encoding="utf-8")
            self.assertEqual(platform_lock.probe_free(path), False)
            after = path.read_text(encoding="utf-8")
            self.assertEqual(
                after,
                recorded,
                "the probe BLANKED the live holder's record; `aw runs` would lose the pid",
            )
            print(f"probe reported held and left the record intact: {after.strip()!r}")

    def test_probing_a_free_file_preserves_its_content(self):
        path = self.tmp / "stale.lock"
        path.write_text("pid=999999 started=then\n", encoding="utf-8")
        self.assertTrue(platform_lock.probe_free(path))
        self.assertEqual(path.read_text(encoding="utf-8"), "pid=999999 started=then\n")
        print("probe of a free-but-stale lock file: reported free, content preserved")

    def test_the_shared_probe_backs_both_public_probes(self):
        """One probe implementation, consumed by both callers (GUIDING_PRINCIPLES P8)."""

        path = self.tmp / "driver.lock"
        run_dir = self.tmp
        path.write_text("pid=1 started=now\n", encoding="utf-8")
        self.assertTrue(runner_shutdown.lock_is_free(path))
        self.assertEqual(
            run_viewer.driver_holder_state(run_dir), run_viewer.HOLDER_NONE
        )
        with _HolderProcess(path):
            self.assertFalse(runner_shutdown.lock_is_free(path))
            self.assertEqual(
                run_viewer.driver_holder_state(run_dir), run_viewer.HOLDER_LIVE
            )
        print("runner_shutdown.lock_is_free and run_viewer.driver_holder_state agree")


class OperatorMessageTests(unittest.TestCase):
    """F9: the operator-facing refusal message, which NO test asserted before this plan.

    V-03 promises this string is unchanged by the migration, so it needs a real regression net
    rather than a one-off manual paste.
    """

    EXPECTED = "Run is already controlled by another process"

    def test_oc_run_lock_refuses_a_second_holder_with_the_documented_message(self):
        from agent_workflows import oc_runipd

        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-x"
            with oc_runipd.run_lock(run_dir):
                with self.assertRaises(oc_runipd.DriverError) as caught:
                    with oc_runipd.run_lock(run_dir):
                        pass
            message = str(caught.exception)
            self.assertIn(self.EXPECTED, message)
            self.assertIn(run_dir.name, message)
            print(f"oc_runipd.run_lock refusal: {message!r}")

    def test_agy_run_lock_refuses_a_second_holder_with_the_documented_message(self):
        from agent_workflows import agy_runipd

        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-y"
            with agy_runipd.run_lock(run_dir):
                with self.assertRaises(agy_runipd.DriverError) as caught:
                    with agy_runipd.run_lock(run_dir):
                        pass
            message = str(caught.exception)
            self.assertIn(self.EXPECTED, message)
            print(f"agy_runipd.run_lock refusal: {message!r}")

    def test_the_run_lock_still_records_the_pid_inside_the_lock_file(self):
        """The `pid=` record `run_viewer` parses must survive the migration."""

        from agent_workflows import oc_runipd

        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-z"
            with oc_runipd.run_lock(run_dir):
                content = (run_dir / "driver.lock").read_text(encoding="utf-8")
            self.assertIn(f"pid={os.getpid()}", content)
            print(f"driver.lock content while held: {content.strip()!r}")


class LockHandleDescriptorTests(unittest.TestCase):
    """D4: the handle exposes the LOCKED descriptor, which the inode-identity check needs.

    `runner_shutdown.RunLockHandle` unlinks the lock file only while it provably still names the
    inode it locked. That check must compare against the descriptor the lock is actually held on; a
    fresh `open()` of the same path would compare the path against itself and always pass, silently
    turning a safety check into a tautology.

    These tests also fail LOUDLY if a future `filelock` moves the internal attribute, instead of
    letting the inode check degrade to "unknown".
    """

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def test_fileno_returns_the_descriptor_the_lock_is_held_on(self):
        path = self.tmp / "fd.lock"
        held = platform_lock.acquire(path)
        self.addCleanup(held.release)
        fd = held.fileno()
        self.assertIsInstance(
            fd,
            int,
            "PREMISE CHANGED: filelock no longer exposes its descriptor where "
            "platform_lock.LockHandle.fileno looks; the RunLockHandle inode check needs it",
        )
        locked = os.fstat(fd)
        on_disk = os.stat(path)
        self.assertEqual(
            (locked.st_dev, locked.st_ino), (on_disk.st_dev, on_disk.st_ino)
        )
        print(f"locked inode {(locked.st_dev, locked.st_ino)} == path inode")

    def test_dup_stream_writes_without_dropping_the_lock(self):
        path = self.tmp / "dup.lock"
        held = platform_lock.acquire(path)
        self.addCleanup(held.release)
        stream = held.dup_stream()
        self.assertIsNotNone(stream)
        assert stream is not None
        stream.seek(0)
        stream.truncate()
        stream.write("pid=4242 started=now\n")
        stream.flush()
        stream.close()  # closing the DUP must NOT release the lock
        self.assertEqual(path.read_text(encoding="utf-8"), "pid=4242 started=now\n")
        self.assertEqual(
            platform_lock.probe_free(path),
            False,
            "closing the duplicated descriptor must not drop the lock",
        )
        print("wrote through a dup'd descriptor; lock still held after closing it")

    def test_the_run_lock_inode_check_still_detects_a_replaced_file(self):
        """End to end: `holds_current_path` must be FALSE when the path names another inode."""

        from agent_workflows import oc_runipd

        with TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run-i"
            with oc_runipd.run_lock(run_dir) as lock:
                self.assertTrue(lock.holds_current_path())
                # Replace the file at that path with a DIFFERENT inode.
                lock_path = run_dir / "driver.lock"
                replacement = run_dir / "other"
                replacement.write_text("someone else\n", encoding="utf-8")
                os.replace(replacement, lock_path)
                self.assertFalse(
                    lock.holds_current_path(),
                    "the inode check must notice the path no longer names our locked inode",
                )
                print("inode-identity check correctly reported a REPLACED lock file")


class ImportsWithoutFcntlTests(unittest.TestCase):
    """E-05: the package IMPORTS with `fcntl` unavailable, which is the whole point.

    Run in a SUBPROCESS with an import hook that makes `fcntl` unavailable BEFORE
    `agent_workflows` is imported. That ordering is essential: the defect was an import-time
    failure, so a patch applied after import could not detect it, and monkeypatching
    `sys.platform` never could either.
    """

    # The six modules that carried a top-level `import fcntl`, plus the two probe consumers.
    AFFECTED = (
        "agent_workflows.oc_runipd",
        "agent_workflows.agy_runipd",
        "agent_workflows.agy_sessions",
        "agent_workflows.project_registry",
        "agent_workflows.run_ledger_store",
        "agent_workflows.runner_stop",
        "agent_workflows.runner_shutdown",
        "agent_workflows.run_viewer",
        "agent_workflows.platform_lock",
    )

    _BLOCK_FCNTL = """
    import builtins, importlib, sys, warnings

    warnings.simplefilter("ignore")

    # Make `import fcntl` fail for EVERYTHING from here on, including inside dependencies.
    class _Blocker:
        def find_module(self, name, path=None):
            if name == "fcntl":
                raise ImportError("simulated non-POSIX host: no fcntl")
            return None

        def find_spec(self, name, path=None, target=None):
            if name == "fcntl":
                raise ImportError("simulated non-POSIX host: no fcntl")
            return None

    sys.modules.pop("fcntl", None)
    sys.meta_path.insert(0, _Blocker())

    try:
        import fcntl
    except ImportError:
        pass
    else:
        print("SETUP-FAILED: fcntl was still importable")
        raise SystemExit(2)

    names = sys.argv[1:]
    for name in names:
        importlib.import_module(name)
    print("IMPORTED-ALL")

    # And a lock must still WORK, not merely import.
    import tempfile
    from pathlib import Path
    from agent_workflows import platform_lock

    d = Path(tempfile.mkdtemp())
    held = platform_lock.acquire(d / "x.lock")
    try:
        platform_lock.acquire(d / "x.lock")
        print("NOT-EXCLUSIVE")
        raise SystemExit(3)
    except platform_lock.LockBusy:
        print("STILL-EXCLUSIVE")
    held.release()

    # And the PROBE must report UNDETERMINED rather than guessing "free".
    probe_path = d / "probe.lock"
    probe_path.write_text("x\\n")
    print("PROBE=%r" % (platform_lock.probe_free(probe_path),))
    """

    def test_all_affected_modules_import_without_fcntl(self):
        result = _run_child(self._BLOCK_FCNTL, *self.AFFECTED)
        self.assertEqual(
            result.returncode, 0, f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        self.assertIn("IMPORTED-ALL", result.stdout, result.stderr)
        print(
            f"with fcntl BLOCKED, all {len(self.AFFECTED)} modules imported: "
            f"{result.stdout.strip()}"
        )

    def test_the_lock_still_excludes_without_fcntl(self):
        result = _run_child(self._BLOCK_FCNTL, *self.AFFECTED)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STILL-EXCLUSIVE", result.stdout, result.stderr)

    def test_the_probe_reports_undetermined_without_the_posix_primitive(self):
        """`None`, never `True`: failing to prove a holder is alive is not proof it is dead."""

        result = _run_child(self._BLOCK_FCNTL, *self.AFFECTED)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "PROBE=None",
            result.stdout,
            "the probe must report UNDETERMINED, not free, when it cannot answer",
        )
        print("with fcntl BLOCKED, probe_free reported None (undetermined), not True")

    def test_this_test_would_have_FAILED_before_the_fix(self):
        """FALSIFIABILITY: the same simulation against the PRE-FIX code must fail.

        Reconstructs the old shape (a module with a top-level `import fcntl`) under the same import
        blocker and asserts it raises. Without this, a test that passes on Linux would prove nothing
        about the fix, because the defect is invisible on Linux by construction.
        """

        result = _run_child(
            """
            import sys, types

            class _Blocker:
                def find_spec(self, name, path=None, target=None):
                    if name == "fcntl":
                        raise ImportError("simulated non-POSIX host: no fcntl")
                    return None

            sys.modules.pop("fcntl", None)
            sys.meta_path.insert(0, _Blocker())

            # Exactly the pre-fix pattern: a module whose top-level body imports fcntl.
            source = "import fcntl\\nVALUE = fcntl.LOCK_EX\\n"
            module = types.ModuleType("prefix_shaped_module")
            try:
                exec(compile(source, "prefix_shaped_module", "exec"), module.__dict__)
            except ImportError as exc:
                print("PRE-FIX-SHAPE-FAILED: %s" % exc)
            else:
                print("PRE-FIX-SHAPE-IMPORTED")
            """
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "PRE-FIX-SHAPE-FAILED",
            result.stdout,
            "the import blocker is not actually blocking; the E-05 tests would be vacuous",
        )
        print(f"falsifiability: {result.stdout.strip()}")


class SingleOwnerTests(unittest.TestCase):
    """The primitive is owned in exactly ONE place (GUIDING_PRINCIPLES P8)."""

    def test_no_module_carries_a_top_level_fcntl_import(self):
        offenders = []
        for path in sorted((REPO_ROOT / "agent_workflows").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            if "\nimport fcntl\n" in source:
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            f"top-level `import fcntl` makes the package unimportable on a non-POSIX host: "
            f"{offenders}",
        )
        print("no top-level `import fcntl` anywhere in agent_workflows/")

    def test_only_platform_lock_touches_the_primitive(self):
        users = []
        for path in sorted((REPO_ROOT / "agent_workflows").glob("*.py")):
            if path.name == "platform_lock.py":
                continue
            source = path.read_text(encoding="utf-8")
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"'):
                    continue
                if "fcntl." in stripped or stripped == "import fcntl":
                    users.append(f"{path.name}: {stripped}")
        self.assertEqual(
            users, [], f"only platform_lock may touch the POSIX primitive: {users}"
        )
        print("platform_lock is the only module that touches fcntl")

    def test_platform_lock_has_no_posix_only_import_of_its_own(self):
        """Its `fcntl` access must be behind the guard, never at module import time."""

        source = (REPO_ROOT / "agent_workflows" / "platform_lock.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("\nimport fcntl\n", source)
        self.assertIn("except ImportError:", source)
        print("platform_lock's fcntl access is guarded, not a top-level import")

    def test_no_blocking_mode_leaked_to_a_second_caller(self):
        """E-07: exactly ONE caller may pass `blocking=True`."""

        # Asserted on the FILE SET, not on line numbers: the property is "which modules may block",
        # and pinning a line would make an unrelated edit above it fail this test for no reason.
        callers = set()
        located = []
        for path in sorted((REPO_ROOT / "agent_workflows").glob("*.py")):
            if path.name == "platform_lock.py":
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if "blocking=True" in line and not line.strip().startswith("#"):
                    callers.add(path.name)
                    located.append(f"{path.name}:{number}")
        self.assertEqual(
            callers,
            {"project_registry.py"},
            "the project registry is the ONLY permitted blocking caller (E-07); a new one "
            f"needs its own justification. Found: {located}",
        )
        print(f"blocking callers: {located}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
