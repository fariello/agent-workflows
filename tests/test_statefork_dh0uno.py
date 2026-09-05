"""Regression tests for backlog ``dh0uno``: control state must belong to the CHECKOUT, not the cwd.

THE DEFECT. ``aw`` composed its control paths as ``repo_root/".aw"/state/...``, where ``repo_root``
is the git worktree top-level of the caller. Under driver worktree isolation the agent runs with cwd
inside a lane (``.aw/worktrees/<id6>``), so an inner ``aw ipd begin``/``finalize`` resolved
``<lane>/.aw/state/...``: a SECOND receipt/lock/journal store that the driver (running from the main
tree) could not see, that ``git status`` could not show (gitignored), that no branch diff carried
(never committed), and that lane teardown deleted.

WHY THESE TESTS LOOK LIKE THIS. Each one allocates a REAL ``git worktree`` and compares the resolved
control path from the main tree against the same call from the lane. That is the falsifiable form of
the fix: the two must be byte-identical, and they were provably different before it. Deliberately NOT
used as evidence here: ``tests/test_run_viewer.py``. Those 15 failures in a fresh clone are a
gitignored-fixture artifact (``.aw/records/runs/`` is never committed, so the directory is simply
absent), they pass with run records present and NO fix applied, and that file's own module docstring
says not to read them as a regression.
"""

from __future__ import annotations

import errno
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import ipd_lifecycle


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


class _RealWorktreeFixture(unittest.TestCase):
    """A real checkout with one real linked worktree; the only way to prove the collapse."""

    def setUp(self) -> None:
        # The checkout->control-root resolution is memoized (E-07), and this fixture builds a FRESH
        # checkout per case at a path the OS may well reuse. Clearing first is what stops a new tree
        # from reading the previous tree's cached answer.
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.addCleanup(ipd_lifecycle.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.main = root / "checkout"
        self.main.mkdir()
        _git(self.main, "init", "-q")
        _git(self.main, "config", "user.email", "test@example.invalid")
        _git(self.main, "config", "user.name", "Test")
        (self.main / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(self.main, "add", "seed.txt")
        _git(self.main, "commit", "-q", "-m", "seed")
        self.lane = root / "lane"
        _git(self.main, "worktree", "add", "-q", str(self.lane), "-b", "lane/test")
        self.assertTrue(
            (self.lane / "seed.txt").is_file(), "lane worktree did not materialize"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()


class ReceiptStoreIsCheckoutScopedTests(_RealWorktreeFixture):
    def test_receipt_dir_does_not_fork_per_worktree(self):
        """The begin-receipt store resolves to ONE directory from the main tree and from a lane."""
        self.assertEqual(
            ipd_lifecycle.receipt_dir(self.main),
            ipd_lifecycle.receipt_dir(self.lane),
            "dh0uno: a lane resolved its own receipt store, invisible to the driver",
        )

    def test_receipt_dir_anchors_on_the_main_worktree(self):
        """The single store lives under the MAIN worktree, not under the lane."""
        resolved = ipd_lifecycle.receipt_dir(self.lane)
        self.assertEqual(resolved, self.main / ".aw" / "state" / "ipd-lifecycle")
        # `relative_to` raises if `resolved` is not under the lane, so this is the falsifiable
        # form of "the lane is NOT the control anchor".
        with self.assertRaises(ValueError):
            resolved.relative_to(self.lane)

    def test_receipt_path_for_agrees_across_worktrees(self):
        """The per-plan receipt FILE (what begin writes and finalize reads) is one path."""
        self.assertEqual(
            ipd_lifecycle.receipt_path_for(self.main, "dh0uno"),
            ipd_lifecycle.receipt_path_for(self.lane, "dh0uno"),
        )

    def test_a_receipt_written_from_main_is_visible_from_the_lane(self):
        """END-TO-END: the driver writes from main; an inner `aw` in the lane must FIND it.

        This is the actual harm dh0uno caused - a good finalize refused with "no begin receipt"
        because the two halves looked in two places - expressed as a filesystem fact.
        """
        written = ipd_lifecycle.receipt_path_for(self.main, "dh0uno")
        written.parent.mkdir(parents=True, exist_ok=True)
        written.write_text('{"plan_id": "dh0uno"}\n', encoding="utf-8")
        from_lane = ipd_lifecycle.receipt_path_for(self.lane, "dh0uno")
        self.assertTrue(
            from_lane.is_file(), "the lane could not see the driver's receipt"
        )
        self.assertEqual(
            from_lane.read_text(encoding="utf-8"), '{"plan_id": "dh0uno"}\n'
        )


class RuntimeStateIsCheckoutScopedTests(_RealWorktreeFixture):
    def test_finalize_lock_is_exclusive_across_worktrees(self):
        """One lock path for the whole checkout, or the "exclusive" writer lock is not exclusive."""
        self.assertEqual(
            ipd_lifecycle.finalize_lock_path(self.main),
            ipd_lifecycle.finalize_lock_path(self.lane),
            "two lanes could each hold 'the' exclusive finalize lock simultaneously",
        )

    def test_finalize_journal_is_observable_across_worktrees(self):
        """An in-flight finalize transaction must be visible from any worktree, or recovery is blind."""
        self.assertEqual(
            ipd_lifecycle.finalize_journal_path(self.main, "dh0uno"),
            ipd_lifecycle.finalize_journal_path(self.lane, "dh0uno"),
        )


class ProductTreeStaysPerWorktreeTests(_RealWorktreeFixture):
    def test_repo_root_still_resolves_the_lane_for_product_work(self):
        """The fix must NOT collapse the PRODUCT tree: finalize has to commit into the lane.

        Guards the over-correction. If `_repo_root` were also collapsed to the main checkout, the
        path-scoped finalize commit and the plan's `git mv` would target the wrong tree.
        """
        self.assertEqual(ipd_lifecycle._repo_root(self.lane), self.lane)
        self.assertEqual(ipd_lifecycle._repo_root(self.main), self.main)
        self.assertNotEqual(
            ipd_lifecycle._repo_root(self.lane),
            ipd_lifecycle._repo_root(self.main),
        )


class NonGitFallbackTests(unittest.TestCase):
    """The honest limit: with no checkout identity there is nothing to collapse, so behavior is kept."""

    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.addCleanup(ipd_lifecycle.clear_checkout_control_root_cache)

    def test_plain_directory_keeps_the_caller_relative_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp)
            self.assertEqual(
                ipd_lifecycle.receipt_dir(plain),
                plain / ".aw" / "state" / "ipd-lifecycle",
            )
            self.assertEqual(
                ipd_lifecycle.checkout_control_root(plain),
                plain / ".aw",
            )

    def test_nonexistent_directory_does_not_raise(self):
        """A path that does not exist must degrade, not explode: callers pass temp roots freely."""
        missing = Path(tempfile.gettempdir()) / "aw-dh0uno-definitely-absent-dir"
        self.assertEqual(ipd_lifecycle.checkout_control_root(missing), missing / ".aw")


class GitSpawnFailureIsTotalTests(unittest.TestCase):
    """E-06: a control-path accessor must never RAISE because git could not be SPAWNED.

    ``receipt_dir``/``finalize_lock_path``/``finalize_journal_path`` were PURE string composition
    before ``dh0uno``. They are called from loops and from error-message formatting, so a raise
    surfaces where no caller expects one. The failure mode under test is deliberately a raise from
    the SPAWN itself (``FileNotFoundError`` when git is absent, ``BlockingIOError``/EAGAIN when the
    OS refuses a fork), NOT a nonzero return code: patching the return value proves nothing here,
    because the nonzero branch already fell back correctly.

    Measured before E-06: all three raised, and the ``release_finalize_lock`` case both LEAKED the
    writer lock and MASKED the real in-flight finalize exception with a git error.
    """

    SPAWN_FAILURES = (
        ("git-absent", FileNotFoundError(2, "No such file or directory: 'git'")),
        ("fork-refused", OSError(errno.EAGAIN, os.strerror(errno.EAGAIN))),
    )

    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.addCleanup(ipd_lifecycle.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "checkout"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")

    def test_accessors_return_the_fallback_instead_of_raising(self):
        for label, exc in self.SPAWN_FAILURES:
            with self.subTest(spawn_failure=label):
                ipd_lifecycle.clear_checkout_control_root_cache()
                with mock.patch("subprocess.run", side_effect=exc):
                    # Each of these RAISED before E-06.
                    self.assertEqual(
                        ipd_lifecycle.receipt_dir(self.repo),
                        self.repo / ".aw" / "state" / "ipd-lifecycle",
                    )
                    self.assertEqual(
                        ipd_lifecycle.finalize_lock_path(self.repo),
                        self.repo
                        / ".aw"
                        / "state"
                        / "runtime"
                        / "locks"
                        / "ipd_finalize_writer.lock",
                    )
                    self.assertEqual(
                        ipd_lifecycle.finalize_journal_path(self.repo, "dh0uno"),
                        self.repo
                        / ".aw"
                        / "state"
                        / "runtime"
                        / "transactions"
                        / "ipd_finalize_dh0uno.json",
                    )
                    # Called from a `finally:` during finalize, so this one matters most.
                    self.assertIsNone(ipd_lifecycle.release_finalize_lock(self.repo))

    def test_release_in_a_finally_neither_masks_the_real_error_nor_leaks_the_lock(self):
        """THE HARM, expressed as a test: a raise from `finally:` replaced the real exception."""

        class _Sentinel(RuntimeError):
            pass

        for label, exc in self.SPAWN_FAILURES:
            with self.subTest(spawn_failure=label):
                ipd_lifecycle.clear_checkout_control_root_cache()
                lock = ipd_lifecycle.finalize_lock_path(self.repo)
                ipd_lifecycle.acquire_finalize_lock(self.repo, "dh0uno")
                self.assertTrue(lock.is_file(), "fixture did not take the lock")

                ipd_lifecycle.clear_checkout_control_root_cache()
                with self.assertRaises(_Sentinel):
                    with mock.patch("subprocess.run", side_effect=exc):
                        try:
                            raise _Sentinel("THE REAL FINALIZE ERROR")
                        finally:
                            ipd_lifecycle.release_finalize_lock(self.repo)
                self.assertFalse(
                    lock.exists(),
                    "the writer lock leaked: a later finalize would refuse for no reason",
                )

    def test_a_programming_error_still_surfaces(self):
        """Only OSError is swallowed. A genuine bug must not be silently absorbed."""
        ipd_lifecycle.clear_checkout_control_root_cache()
        with mock.patch("subprocess.run", side_effect=TypeError("bad argv")):
            with self.assertRaises(TypeError):
                ipd_lifecycle.receipt_dir(self.repo)


class ControlRootResolutionIsMemoizedTests(unittest.TestCase):
    """E-07: a path lookup must not be a git fork.

    Measured before E-07: 15 lookups spawned 15 ``git rev-parse`` subprocesses at ~1.9 ms each.
    Correctness comes first, so this also pins that two checkouts never share an entry and that a
    transient fallback is NOT cached (a directory that is not a checkout yet must resolve correctly
    once it becomes one).
    """

    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.addCleanup(ipd_lifecycle.clear_checkout_control_root_cache)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _counting_git(self):
        """A ``subprocess.run`` wrapper that records only git argvs and still really runs them."""
        real_run = subprocess.run
        calls = []

        def counting_run(argv, *a, **kw):
            if argv and str(argv[0]) == "git":
                calls.append(tuple(str(x) for x in argv))
            return real_run(argv, *a, **kw)

        return counting_run, calls

    def test_repeated_lookups_spawn_exactly_one_git(self):
        repo = self.root / "checkout"
        repo.mkdir()
        _git(repo, "init", "-q")
        counting_run, calls = self._counting_git()
        with mock.patch("subprocess.run", side_effect=counting_run):
            for _ in range(15):
                ipd_lifecycle.receipt_dir(repo)
        self.assertEqual(
            len(calls),
            1,
            f"expected one git fork for 15 lookups, saw {len(calls)}: {calls}",
        )

    def test_every_control_accessor_shares_the_one_resolution(self):
        repo = self.root / "checkout"
        repo.mkdir()
        _git(repo, "init", "-q")
        ipd_lifecycle.receipt_dir(repo)  # warm
        counting_run, calls = self._counting_git()
        with mock.patch("subprocess.run", side_effect=counting_run):
            for _ in range(5):
                ipd_lifecycle.receipt_dir(repo)
                ipd_lifecycle.finalize_lock_path(repo)
                ipd_lifecycle.finalize_journal_path(repo, "dh0uno")
        self.assertEqual(len(calls), 0, f"warm lookups still forked git: {calls}")

    def test_two_checkouts_never_share_a_cache_entry(self):
        """The correctness half. A cache that collapses two checkouts would RE-CREATE dh0uno."""
        a = self.root / "a"
        b = self.root / "b"
        for d in (a, b):
            d.mkdir()
            _git(d, "init", "-q")
        self.assertNotEqual(
            ipd_lifecycle.receipt_dir(a),
            ipd_lifecycle.receipt_dir(b),
            "two distinct checkouts resolved one control store",
        )

    def test_a_lane_created_after_the_cache_warmed_still_collapses(self):
        """The lane path must not need its own git call to land on the already-known main root."""
        main = self.root / "checkout"
        main.mkdir()
        _git(main, "init", "-q")
        _git(main, "config", "user.email", "test@example.invalid")
        _git(main, "config", "user.name", "Test")
        (main / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(main, "add", "seed.txt")
        _git(main, "commit", "-q", "-m", "seed")
        warm = ipd_lifecycle.receipt_dir(main)
        lane = self.root / "lane"
        _git(main, "worktree", "add", "-q", str(lane), "-b", "lane/e07")
        self.assertEqual(ipd_lifecycle.receipt_dir(lane), warm)

    def test_a_fallback_is_not_cached_so_a_later_checkout_resolves(self):
        """A plain directory that BECOMES a checkout must not be pinned to its fallback answer."""
        plain = self.root / "later"
        plain.mkdir()
        self.assertEqual(
            ipd_lifecycle.checkout_control_root(plain),
            plain / ".aw",
            "a non-git directory should fall back to itself",
        )
        lane_host = self.root / "host"
        lane_host.mkdir()
        _git(lane_host, "init", "-q")
        _git(lane_host, "config", "user.email", "test@example.invalid")
        _git(lane_host, "config", "user.name", "Test")
        (lane_host / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(lane_host, "add", "seed.txt")
        _git(lane_host, "commit", "-q", "-m", "seed")
        # `plain` now becomes a linked worktree of `lane_host`, i.e. the same absolute path acquires
        # a checkout identity. A cached fallback would keep answering `plain/.aw` forever.
        plain.rmdir()
        _git(lane_host, "worktree", "add", "-q", str(plain), "-b", "lane/later")
        self.assertEqual(
            ipd_lifecycle.checkout_control_root(plain),
            lane_host / ".aw",
            "a stale cached fallback survived the directory becoming a checkout",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
