"""The Windows lock file must SURVIVE release and keep its content, on every filelock version.

filelock's default Windows release unlinks the lock file (and < 4.0 also truncates it on acquire),
which breaks mutual exclusion for a contended lock and erases the holder's `pid=` record.
`platform_lock` therefore passes `preserve_lock_file=True` on filelock 4+, and on older filelock
(only reachable on Python 3.9) uses its own `_PreservingWindowsLock`.

These tests run on EVERY OS: the fallback is driven through a fake `msvcrt` whose byte-0 lock is
backed by a real per-process table, so its never-unlink / never-truncate / non-re-entrant contract is
checked on Linux and macOS too, not only on the one CI cell that selects it for real.
"""

from __future__ import annotations

import errno
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import filelock

from agent_workflows import platform_lock as PL


class _FakeMsvcrt:
    """Byte-0 exclusive lock keyed by (device, inode), per HANDLE, as NT byte-range locks are."""

    LK_NBLCK = 2
    LK_UNLCK = 0

    def __init__(self) -> None:
        self.held: dict = {}

    def locking(self, fd: int, mode: int, nbytes: int) -> None:
        assert nbytes == 1
        assert (
            os.lseek(fd, 0, os.SEEK_CUR) == 0
        ), "must lock/unlock byte 0 (lseek first)"
        st = os.fstat(fd)
        key = (st.st_dev, st.st_ino)
        if mode == self.LK_NBLCK:
            if key in self.held:
                raise OSError(errno.EACCES, "locked")
            self.held[key] = fd
        elif mode == self.LK_UNLCK:
            if self.held.get(key) != fd:
                raise OSError(errno.EACCES, "not the holder")
            del self.held[key]


class PreservingWindowsLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "sub" / "driver.lock"
        self.fake = _FakeMsvcrt()
        patcher = mock.patch.object(PL, "windows_primitive", return_value=self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_release_keeps_the_file_and_acquire_keeps_its_content(self) -> None:
        lock = PL._PreservingWindowsLock(str(self.path), 0.0)
        lock.acquire()
        self.assertTrue(lock.is_locked)
        os.write(lock._context.lock_file_fd, b"pid=4242 started=x\n")
        lock.release()
        self.assertFalse(lock.is_locked)
        self.assertTrue(self.path.is_file(), "release must NOT unlink the lock file")
        again = PL._PreservingWindowsLock(str(self.path), 0.0)
        again.acquire()
        self.addCleanup(again.release)
        self.assertEqual(
            self.path.read_bytes(),
            b"pid=4242 started=x\n",
            "acquire must NOT truncate the record",
        )

    def test_a_second_lock_object_is_refused_even_in_this_process(self) -> None:
        first = PL._PreservingWindowsLock(str(self.path), 0.0)
        first.acquire()
        self.addCleanup(first.release)
        second = PL._PreservingWindowsLock(str(self.path), 0.0)
        with self.assertRaises(filelock.Timeout):
            second.acquire()
        self.assertFalse(second.is_locked)

    def test_a_released_lock_is_reacquirable_and_release_is_idempotent(self) -> None:
        a = PL._PreservingWindowsLock(str(self.path), 0.0)
        a.acquire()
        a.release()
        a.release()
        b = PL._PreservingWindowsLock(str(self.path), 0.0)
        b.acquire()
        self.assertTrue(b.is_locked)
        b.release()

    def test_lock_handle_works_over_the_fallback(self) -> None:
        handle = PL.LockHandle(
            PL._PreservingWindowsLock(str(self.path), 0.0), self.path
        )
        handle._lock.acquire()
        self.assertTrue(handle.is_held)
        self.assertIsInstance(handle.fileno(), int)
        handle.release()
        self.assertFalse(handle.is_held)
        self.assertTrue(self.path.is_file())


class LockSelectionTests(unittest.TestCase):
    def test_posix_uses_plain_filelock(self) -> None:
        with mock.patch.object(PL.os, "name", "posix"):
            lock = PL._new_lock(Path("x.lock"), 0.0)
        self.assertIsInstance(lock, filelock.BaseFileLock)

    def test_windows_with_modern_filelock_asks_it_to_preserve(self) -> None:
        with mock.patch.object(PL.os, "name", "nt"), mock.patch.object(
            PL, "_filelock_can_preserve", return_value=True
        ), mock.patch.object(PL.filelock, "FileLock") as fl:
            PL._new_lock(Path("x.lock"), 0.0)
        fl.assert_called_once_with("x.lock", timeout=0.0, preserve_lock_file=True)

    def test_windows_with_old_filelock_uses_the_preserving_fallback(self) -> None:
        with mock.patch.object(PL.os, "name", "nt"), mock.patch.object(
            PL, "_filelock_can_preserve", return_value=False
        ):
            lock = PL._new_lock(Path("x.lock"), 0.0)
        self.assertIsInstance(lock, PL._PreservingWindowsLock)

    def test_the_installed_filelock_is_detected_consistently(self) -> None:
        major = int(filelock.__version__.split(".")[0])
        self.assertEqual(PL._filelock_can_preserve(), major >= 4)


if __name__ == "__main__":
    unittest.main()
