"""The R5.4 clean-base guard, on BOTH host drivers.

Covers spec `7ckptx` R5.4 and CID-3 (criterion A14) for plan `nna8yz` E-05.

THE THREE CASES R5.4 AND A14 REQUIRE, and the third is the one most likely to be "fixed" wrongly:

  1. a dirty TRACKED path REFUSES, names the paths, and does so BEFORE any worker process is spawned;
  2. a clean tree PROCEEDS;
  3. an UNTRACKED file does NOT refuse. This is deliberate (spec R5.4, plan finding F-4): a lane is
     created from a COMMIT, so an untracked file's absence from the lane is CORRECT, and refusing on it
     would make an unattended run unstartable in essentially any working checkout.

PARAMETERIZED OVER BOTH DRIVERS rather than duplicated, because a containment rule present on one host
only is a defect (CID-3). Both are asserted to consume the SAME shared predicate, so the hosts cannot
drift.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import agy_runipd, lane_containment, oc_runipd

#: The two host drivers and the guard entry point each exposes. Both must satisfy every assertion.
DRIVERS = (
    ("oc", oc_runipd),
    ("agy", agy_runipd),
)


def _module_source(module: object) -> str:
    """A module's own source text. Wrapped because `__file__` is `str | None` to a type checker."""
    path = getattr(module, "__file__", None)
    assert path is not None, f"{module!r} has no __file__"
    return Path(path).read_text(encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


class CleanBaseRuleTests(unittest.TestCase):
    """The shared RULE, driven directly by porcelain text so every case is reachable."""

    def test_empty_porcelain_is_clean(self):
        result = lane_containment.evaluate_clean_base("")
        self.assertTrue(result.clean)
        self.assertEqual(result.dirty_paths, ())

    def test_dirty_tracked_paths_are_named(self):
        result = lane_containment.evaluate_clean_base(
            " M agent_workflows/oc_runipd.py\nM  README.md\n"
        )
        self.assertFalse(result.clean)
        self.assertEqual(
            result.dirty_paths, ("README.md", "agent_workflows/oc_runipd.py")
        )
        # The refusal must NAME them, not merely count them (R5.4).
        self.assertIn("agent_workflows/oc_runipd.py", result.reason)
        self.assertIn("README.md", result.reason)

    def test_a_rename_dirties_both_endpoints(self):
        result = lane_containment.evaluate_clean_base("R  old/a.py -> new/b.py\n")
        self.assertEqual(result.dirty_paths, ("new/b.py", "old/a.py"))

    def test_the_parser_is_the_shared_one(self):
        """R6.1: the porcelain parsing is ONE predicate, not a third copy."""
        self.assertEqual(
            lane_containment.parse_porcelain_paths(" M a.py\nD  b.py\n"),
            {"a.py", "b.py"},
        )


class CleanBaseOnARealRepositoryTests(unittest.TestCase):
    """The three A14 cases against a real git checkout, for BOTH drivers."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "t@example.invalid")
        _git(self.repo, "config", "user.name", "t")
        (self.repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
        _git(self.repo, "add", "tracked.txt")
        _git(self.repo, "commit", "-qm", "init")

    def test_case_2_a_clean_tree_proceeds(self):
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertTrue(result.clean, result.reason)

    def test_case_1_a_dirty_tracked_file_refuses_and_names_it(self):
        (self.repo / "tracked.txt").write_text("v2\n", encoding="utf-8")
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertFalse(result.clean)
                self.assertIn("tracked.txt", result.dirty_paths)
                self.assertIn("tracked.txt", result.reason)

    def test_case_1_a_staged_tracked_change_also_refuses(self):
        (self.repo / "tracked.txt").write_text("v3\n", encoding="utf-8")
        _git(self.repo, "add", "tracked.txt")
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertFalse(result.clean)
                self.assertIn("tracked.txt", result.dirty_paths)

    def test_case_3_an_untracked_file_does_NOT_refuse(self):
        """Spec R5.4 / finding F-4: this exclusion is deliberate and must not be tightened."""
        (self.repo / "scratch.log").write_text("noise\n", encoding="utf-8")
        (self.repo / "notes.md").write_text("notes\n", encoding="utf-8")
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertTrue(result.clean, result.reason)
                self.assertEqual(result.dirty_paths, ())

    def test_both_drivers_agree_on_every_case(self):
        """CID-3 stated as an assertion: the two hosts return the SAME verdict throughout."""
        states: list[tuple[bool, tuple[str, ...]]] = []

        def snapshot() -> None:
            verdicts = [
                driver.evaluate_clean_base_for_launch(self.repo)
                for _n, driver in DRIVERS
            ]
            self.assertEqual(
                {(v.clean, v.dirty_paths) for v in verdicts},
                {(verdicts[0].clean, verdicts[0].dirty_paths)},
                f"hosts disagree: {[(v.clean, v.dirty_paths) for v in verdicts]}",
            )
            states.append((verdicts[0].clean, verdicts[0].dirty_paths))

        snapshot()  # clean
        (self.repo / "untracked.txt").write_text("x\n", encoding="utf-8")
        snapshot()  # untracked only
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        snapshot()  # dirty tracked

        self.assertEqual([s[0] for s in states], [True, True, False], states)


class NoSpawnBeforeRefusalTests(unittest.TestCase):
    """R5.4's ordering clause: the refusal happens BEFORE any worker process is spawned.

    Asserted STRUCTURALLY on each driver's `execute_item`, by position rather than by running a full
    turn: the guard block must appear before the launch call and before worktree allocation. A
    behavioural spawn-patch test would need a whole driver run harness; the ordering is what R5.4
    actually requires and position in the single function that does both is what establishes it.
    """

    CASES = (
        ("oc", oc_runipd, "run_opencode(", "allocate_isolation_worktree("),
        ("agy", agy_runipd, "run_agy_turn(", "allocate_isolation_worktree("),
    )

    def test_guard_precedes_spawn_and_allocation(self):
        for name, driver, spawn_symbol, alloc_symbol in self.CASES:
            with self.subTest(driver=name):
                source = _module_source(driver)
                body = source.split("def execute_item", 1)
                self.assertEqual(len(body), 2, f"{name}: execute_item not found")
                body_text = body[1]

                guard_at = body_text.find("evaluate_clean_base_for_launch(")
                spawn_at = body_text.find(spawn_symbol)
                alloc_at = body_text.find(alloc_symbol)

                self.assertNotEqual(guard_at, -1, f"{name}: guard not wired")
                self.assertNotEqual(spawn_at, -1, f"{name}: spawn call not found")
                self.assertNotEqual(alloc_at, -1, f"{name}: allocation not found")
                self.assertLess(guard_at, spawn_at, f"{name}: guard runs after spawn")
                self.assertLess(
                    guard_at, alloc_at, f"{name}: guard runs after lane allocation"
                )

    def test_refusal_records_the_dirty_paths_on_the_attempt(self):
        """The refusal is auditable: the paths land in durable state, not only on stderr."""
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                source = _module_source(driver)
                body = source.split("def execute_item", 1)[1]
                self.assertIn('attempt["clean_base_dirty_paths"]', body)
                self.assertIn('"event": "clean-base-refused"', body)


class SharedPredicateTests(unittest.TestCase):
    """R6.1: neither driver re-decides what "dirty" means, and neither forks the parser."""

    def test_both_guards_delegate_to_the_shared_rule(self):
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                source = _module_source(driver)
                fn = source.split("def evaluate_clean_base_for_launch", 1)
                self.assertEqual(len(fn), 2, f"{name}: guard helper missing")
                body = fn[1].split("\ndef ", 1)[0]
                self.assertIn("lane_containment.evaluate_clean_base(", body)
                # The scope is the R5.4 one: tracked paths only.
                self.assertIn("--untracked-files=no", body)

    def test_dirty_tree_overlap_no_longer_forks_the_parser(self):
        """The pre-existing duplicate parser is gone from BOTH drivers (R6.1)."""
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                source = _module_source(driver)
                fn = source.split("def dirty_tree_overlap", 1)
                self.assertEqual(len(fn), 2, f"{name}: dirty_tree_overlap missing")
                body = fn[1].split("\ndef ", 1)[0]
                self.assertIn("lane_containment.parse_porcelain_paths(", body)
                # The hand-rolled loop it replaced must not still be there.
                self.assertNotIn('entry.split(" -> ", 1)', body)

    def test_overlap_behaviour_is_preserved_after_the_refactor(self):
        """The delegation must not have changed what `dirty_tree_overlap` answers."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _git(repo, "init", "-q")
            _git(repo, "config", "user.email", "t@example.invalid")
            _git(repo, "config", "user.name", "t")
            (repo / "a.txt").write_text("1\n", encoding="utf-8")
            (repo / "b.txt").write_text("1\n", encoding="utf-8")
            _git(repo, "add", "a.txt", "b.txt")
            _git(repo, "commit", "-qm", "init")
            (repo / "a.txt").write_text("2\n", encoding="utf-8")

            for name, driver in DRIVERS:
                with self.subTest(driver=name):
                    # Overlapping: reported.
                    self.assertEqual(
                        driver.dirty_tree_overlap(repo, ["a.txt", "c.txt"]), ["a.txt"]
                    )
                    # Non-overlapping: empty, even though the tree IS dirty.
                    self.assertEqual(driver.dirty_tree_overlap(repo, ["b.txt"]), [])
                    # No incoming change: empty without consulting git.
                    self.assertEqual(driver.dirty_tree_overlap(repo, []), [])

    def test_the_two_checks_answer_different_questions(self):
        """A dirty file OUTSIDE the incoming change: clean-base REFUSES, overlap does not.

        This is the distinction the E-05 comment is required to state, asserted as behaviour so the
        two checks cannot quietly collapse into one.
        """
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _git(repo, "init", "-q")
            _git(repo, "config", "user.email", "t@example.invalid")
            _git(repo, "config", "user.name", "t")
            (repo / "a.txt").write_text("1\n", encoding="utf-8")
            (repo / "b.txt").write_text("1\n", encoding="utf-8")
            _git(repo, "add", "a.txt", "b.txt")
            _git(repo, "commit", "-qm", "init")
            (repo / "b.txt").write_text("dirty\n", encoding="utf-8")

            for name, driver in DRIVERS:
                with self.subTest(driver=name):
                    # Integration-time, incoming change is a.txt only: no overlap, permitted.
                    self.assertEqual(driver.dirty_tree_overlap(repo, ["a.txt"]), [])
                    # Pre-launch: the base is incomplete regardless of which paths a lane will touch.
                    result = driver.evaluate_clean_base_for_launch(repo)
                    self.assertFalse(result.clean)
                    self.assertIn("b.txt", result.dirty_paths)


if __name__ == "__main__":
    unittest.main()
