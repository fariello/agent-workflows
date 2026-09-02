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

import subprocess
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
