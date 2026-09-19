"""The R5.4 clean-base rule, on BOTH host drivers.

Covers spec `7ckptx` R5.4 and CID-3 (criterion A14) for plan `nna8yz` E-05, as AMENDED by dirtygates
Order 01 (`d7qoxv`) so the obligation is SPLIT BY PATH.

THE FOUR CASES R5.4 AND A14 NOW REQUIRE, and the last two are the ones most likely to be "fixed"
wrongly:

  1. a dirty TRACKED path is CLASSIFIED not-clean and NAMED, by the shared rule, on both hosts;
  2. a clean tree PROCEEDS;
  3. an UNTRACKED file does NOT refuse and is not even reported here. This is deliberate (spec R5.4,
     plan finding F-4): a lane is created from a COMMIT, so an untracked file's absence from the lane
     is CORRECT, and refusing on it would make an unattended run unstartable in essentially any
     working checkout;
  4. the CONSEQUENCE of (1) DEPENDS ON THE PATH: a turn SHARING the checkout is REFUSED, while an
     ISOLATED turn is REPORTED and PROCEEDS.

THE RULE-VERSUS-CALLER DISTINCTION IS THE WHOLE DESIGN OF (4), and a test that blurs it hides a
regression, so this file asserts both halves separately. The RULE still answers "is HEAD a complete
base?" with `clean=False` for a dirty tracked tree, on BOTH paths, and still names the paths. What
moved is the CALLER's disposition on the isolated path only. If a change here makes
`evaluate_clean_base` report `clean=True` for a dirty isolated tree, that is a regression and not a
simplification: it would discard the dirty-path list the report exists to print.

WHY (4) IS NOT A SAFETY REGRESSION, recorded here because the refusal will look worth restoring.
MEASURED 2026-09-13: a lane cut from HEAD that lacked an uncommitted change failed its validation in
EXACTLY the way committing that change with no lane involved failed, so the refusal prevented nothing
and only deferred the failure to whenever the operator committed. It cost 27 of 42, 23 of 41 and 18 of
43 queue items on three consecutive runs, each naming ONE uncommitted markdown file, cascading 36 more
into `dependency-blocked`. The merge-and-revalidate gate is what actually catches a stale base.

PARAMETERIZED OVER BOTH DRIVERS rather than duplicated, because a containment rule present on one host
only is a defect (CID-3). Both are asserted to consume the SAME shared predicate, so the hosts cannot
drift.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd

#: The two host drivers and the guard entry point each exposes. Both must satisfy every assertion.
DRIVERS = (
    ("oc", oc_runipd),
    ("agy", agy_runipd),
)

#: The same two drivers WITH the spawn symbol each one launches a turn through (`d7qoxv` E-05).
#:
#: Separate from `DRIVERS` so every pre-existing case keeps its exact two-tuple shape; the behavioral
#: cases below need the spawn name in order to patch it and count launches.
_SPAWNS = (
    ("oc", oc_runipd, "run_opencode"),
    ("agy", agy_runipd, "run_agy_turn"),
)


def _module_source(module: object) -> str:
    """A module's own source text. Wrapped because `__file__` is `str | None` to a type checker."""
    path = getattr(module, "__file__", None)
    assert path is not None, f"{module!r} has no __file__"
    return Path(path).read_text(encoding="utf-8")


def _effective_execute_item_body(
    driver: object, spawn_symbol: str | None = None
) -> str:
    source = _module_source(driver)
    body = source.split("def execute_item", 1)[1]
    if "execute_item_core" in body:
        from agent_workflows import runner_shared

        core_body = inspect.getsource(runner_shared.execute_item_core)
        if spawn_symbol:
            core_body = core_body.replace("spawn_executor(", spawn_symbol)
        return core_body
    return body


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        # The MESSAGE matters more than the traceback here: a fixture whose git call fails otherwise
        # surfaces as a bare `CalledProcessError` naming only the argv, which says nothing about WHY.
        raise AssertionError(
            f"git {' '.join(args)} failed in {repo} (rc={proc.returncode})\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
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

    def test_case_1_a_dirty_tracked_file_is_classified_not_clean_and_named(self):
        """The RULE's half of case 1, RETARGETED by `d7qoxv` E-05 from "refuses" to "classifies".

        WHAT DID NOT CHANGE, which is the point: a dirty tracked path still makes the base not-clean
        and is still NAMED. The rule's answer to "is HEAD a complete base?" is untouched on both
        paths, so this test still fails if the tracked scope is narrowed or the paths stop being
        listed. Only the isolated CALLER's disposition moved, which
        `IsolatedPathReportsRatherThanRefusesTests` below asserts separately.
        """
        (self.repo / "tracked.txt").write_text("v2\n", encoding="utf-8")
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertFalse(result.clean)
                self.assertIn("tracked.txt", result.dirty_paths)
                self.assertIn("tracked.txt", result.reason)
                # And the ISOLATED default does not refuse (`d7qoxv`), while the classification above
                # is unchanged. Both halves are pinned in one place so they cannot drift apart.
                self.assertFalse(result.refuses)

    def test_case_1_a_staged_tracked_change_is_also_not_clean(self):
        """Staged-but-uncommitted counts too. RETARGETED with its sibling above (`d7qoxv` E-05)."""
        (self.repo / "tracked.txt").write_text("v3\n", encoding="utf-8")
        _git(self.repo, "add", "tracked.txt")
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                result = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertFalse(result.clean)
                self.assertIn("tracked.txt", result.dirty_paths)
                self.assertFalse(result.refuses)
                # The SHARED-TREE path over the same dirt DOES refuse, which is what makes the split
                # a split rather than a removal.
                shared = driver.evaluate_clean_base_for_launch(
                    self.repo, shared_tree=True
                )
                self.assertTrue(shared.refuses)
                self.assertEqual(shared.dirty_paths, result.dirty_paths)

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
                body_text = _effective_execute_item_body(
                    driver, spawn_symbol=spawn_symbol
                )

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

    def test_the_dirty_paths_are_recorded_on_the_attempt_on_BOTH_dispositions(self):
        """The observation is auditable: the paths land in durable state, not only on stderr.

        RETARGETED, NOT DELETED, by `d7qoxv` E-05. This is the only thing pinning that the dirty paths
        reach DURABLE state rather than only a stderr line, so it survives the rename: the refusal
        event still exists (the shared-tree path), and the new warning event is asserted beside it so
        the isolated path cannot silently stop recording.

        BOTH EVENT NAMES ARE REQUIRED, which is what makes this a split rather than a rename. If the
        refusal event disappears, the shared-tree obligation approved plan `3i0aaz` E-03 owns has been
        dropped; if the warning event disappears, the operator lost the signal that replaced it.
        """
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                body = _effective_execute_item_body(driver)
                self.assertIn('attempt["clean_base_dirty_paths"]', body)
                self.assertIn('"event": "clean-base-refused"', body)
                self.assertIn('"event": "clean-base-warning"', body)
                self.assertIn('attempt["clean_base_warning"]', body)


class SharedPredicateTests(unittest.TestCase):
    """R6.1: neither driver re-decides what "dirty" means, and neither forks the parser."""

    def test_both_guards_delegate_to_the_shared_rule(self):
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                source = _module_source(driver)
                fn = source.split("def evaluate_clean_base_for_launch", 1)
                self.assertEqual(len(fn), 2, f"{name}: guard helper missing")
                body = fn[1].split("\ndef ", 1)[0]
                if "runner_shared.evaluate_clean_base_for_launch" in body:
                    from agent_workflows import runner_shared

                    body = inspect.getsource(
                        runner_shared.evaluate_clean_base_for_launch
                    )
                self.assertIn("lane_containment.evaluate_clean_base(", body)
                # The scope is the R5.4 one: tracked paths only.
                self.assertIn("--untracked-files=no", body)

    def test_dirty_tree_overlap_no_longer_forks_the_parser(self):
        """The pre-existing duplicate parser is gone from BOTH drivers (R6.1).

        TWO SHAPES SATISFY R6.1 AND BOTH ARE ACCEPTED, because the rule is "no FORKED parser",
        not "a local function must exist". Originally each driver kept its own
        `dirty_tree_overlap` that delegated the PARSING to
        `lane_containment.parse_porcelain_paths`. Integration of `6sb3yu` then went further and
        moved the whole predicate into `runner_shared`, so a driver may now simply RE-EXPORT the
        shared object instead of defining anything. The stronger shape is the imported one: an
        identity re-export cannot drift at all, whereas two delegating copies can still diverge
        around the delegation. Asserting a local `def` would therefore have failed the better
        outcome, which is why this test checks the PROPERTY (one parser, reached by both hosts)
        rather than the syntax.
        """
        from agent_workflows import runner_shared as _shared

        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                # SHAPE A (preferred): the driver exposes the shared object itself.
                if (
                    getattr(driver, "dirty_tree_overlap", None)
                    is _shared.dirty_tree_overlap
                ):
                    continue
                # SHAPE B: a local wrapper that delegates the parsing to the one shared parser.
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
        """A dirty file OUTSIDE the incoming change: the clean-base RULE reports it not-clean, the
        overlap check reports no overlap.

        DOCSTRING CORRECTED BY `d7qoxv` E-05, ASSERTIONS DELIBERATELY UNTOUCHED. It used to say
        "clean-base REFUSES", which after the R5.4 path split is true only of the SHARED-TREE caller:
        the RULE classifies not-clean on both paths, the shared-tree caller refuses, and the ISOLATED
        caller now reports and proceeds. The assertions below are all on the RULE, which is unchanged,
        so this test stays green - and that is exactly why the docstring had to be fixed by hand. A
        test that stays green while its stated purpose becomes false is how the next reader is misled.

        IF THIS GOES RED, the RULE was changed rather than the caller, which `d7qoxv` E-03 forbids.

        The distinction is still asserted as behaviour so the two checks cannot quietly collapse into
        one; after the split the contrast is sharper, since one side reports while the other refuses.
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


#: A minimal approved plan, so a queue entry has a real plan file to resolve (`d7qoxv` E-05).
_PLAN = """# IPD: clean-base warning probe {id6}

- Date: 2026-09-16
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: probe
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-16 approved (test): probe.
"""


class IsolatedPathReportsRatherThanRefusesTests(unittest.TestCase):
    """`d7qoxv` E-05: the isolated path REPORTS and LAUNCHES, and the whole queue survives one dirty
    file.

    THE DIRECT REGRESSION FOR THE MEASURED INCIDENT. Run `run-20260913T031148Z-1722898` blocked 23 of
    41 queue items over ONE uncommitted markdown file that no plan declared, and two sibling runs did
    the same to 27 of 42 and 18 of 43. The old suite could not have caught that, because every case it
    drove was a SINGLE item: nothing asserted that a queue SURVIVES a dirty tree. That is what
    `test_a_whole_queue_of_isolated_items_survives_one_out_of_scope_dirty_path` establishes.

    RUNS AGAINST A `TemporaryDirectory` FIXTURE, never this checkout, following the pattern the class
    above established: every case here needs a DIRTY tree, and dirtying a shared checkout that other
    agents and humans are working in is precisely the harm this plan is about.
    """

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir(parents=True)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "t@example.invalid")
        _git(self.repo, "config", "user.name", "t")
        (self.repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        # The dirty path is a NOTES file no plan declares, mirroring the measured incident's
        # uncommitted backlog markdown.
        (self.repo / "notes.md").write_text("v1\n", encoding="utf-8")
        (self.repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        _git(self.repo, "add", ".gitignore", "notes.md", "src.py")
        _git(self.repo, "commit", "-qm", "init")

    def _queue(self, count: int) -> tuple[Path, dict, list[dict]]:
        pending = self.repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        items = []
        plan_paths: list[str] = []
        for index in range(1, count + 1):
            id6 = f"prb{index:03d}"
            plan = pending / f"20260916-probe-{index:02d}-{id6}-probe.ipd.md"
            plan.write_text(_PLAN.format(id6=id6, order=index), encoding="utf-8")
            plan_paths.append(str(plan.relative_to(self.repo)))
            items.append(
                {
                    "position": index,
                    "id6": id6,
                    "setid": "probe",
                    "status": "queued",
                    "configured_file": str(plan.relative_to(self.repo)),
                    "action": "execute",
                }
            )
        # Added BY EXPLICIT PATH, never `git add -A`: the fixture's own `.gitignore` excludes
        # `.aw/state/` and friends, so a broad add stages nothing and the commit then fails. Naming
        # the plans also keeps the fixture honest about what it is committing.
        #
        # COMMITTED ONLY IF SOMETHING IS ACTUALLY STAGED. Each test drives BOTH hosts against the same
        # fixture repository, so `_queue` runs twice and the second call finds the identical plan files
        # already committed; `git commit` with an empty index exits 1. Checking `--cached` keeps the
        # fixture idempotent instead of depending on being called once.
        _git(self.repo, "add", *plan_paths)
        if _git(self.repo, "diff", "--cached", "--name-only").strip():
            _git(self.repo, "commit", "-qm", "add plans")

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-probe"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        state = {
            "run_id": "run-probe",
            "created_at": "2026-09-16T00:00:00+00:00",
            "updated_at": "2026-09-16T00:00:00+00:00",
            "selectors": ["probe"],
            "repo": str(self.repo),
            "queue": items,
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "agy": "/bin/true",
                "model": "probe",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": True,
                "allow_dirty_base": False,
            },
        }
        return run_dir, state, items

    def _drive(self, driver, spawn_name, run_dir, state, item) -> int:
        """Run `execute_item` with the spawn and lifecycle patched; return the spawn count."""
        spawned: list[object] = []

        def fake_spawn(*a, **k):
            spawned.append((a, k))
            return 0, "ses", str(run_dir / "log"), ["probe"]

        with (
            mock.patch.object(driver, spawn_name, fake_spawn),
            mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok")),
            mock.patch.object(driver, "driver_finalize", lambda *a, **k: (0, "ok")),
            mock.patch.object(
                driver, "assert_child_tool_identity", lambda *a, **k: None
            ),
        ):
            driver.execute_item(run_dir, state, item, recovery=False)
        return len(spawned)

    def _dirty_the_tree(self) -> None:
        (self.repo / "notes.md").write_text("uncommitted edit\n", encoding="utf-8")

    def test_an_isolated_item_LAUNCHES_over_a_dirty_tracked_path(self):
        for name, driver, spawn in _SPAWNS:
            with self.subTest(driver=name):
                run_dir, state, items = self._queue(1)
                self._dirty_the_tree()

                spawns = self._drive(driver, spawn, run_dir, state, items[0])

                # LAUNCHED, where the old contract refused before any spawn. `>= 1` rather than `== 1`
                # for the reason `tests/test_dirty_base_gate.py` records: `b7xarm` adds one bounded
                # same-session re-ask when a turn returns no conforming defect report, and this
                # fixture's fake spawn returns none. The property pinned is launch versus refusal.
                self.assertGreaterEqual(spawns, 1, "the isolated turn must launch")
                self.assertNotEqual(items[0]["status"], "blocked")
                self.assertNotIn("clean_base_refusal", items[0])

    def test_the_warning_NAMES_the_dirty_path_in_durable_state(self):
        """Removing the refusal must not remove the operator's signal (`d7qoxv` E-05)."""
        for name, driver, spawn in _SPAWNS:
            with self.subTest(driver=name):
                run_dir, state, items = self._queue(1)
                self._dirty_the_tree()

                self._drive(driver, spawn, run_dir, state, items[0])

                attempt = items[0]["attempts"][-1]
                self.assertIn("notes.md", attempt["clean_base_dirty_paths"])
                self.assertIn("notes.md", attempt["clean_base_warning"])
                # NON-VACUITY: it must have launched because the guard RAN and reported, not because
                # the guard was skipped. Without this, the test could not tell the two apart.
                self.assertNotIn("clean_base_consented", attempt)

    def test_the_warning_is_recorded_as_an_EVENT_naming_the_paths(self):
        for name, driver, spawn in _SPAWNS:
            with self.subTest(driver=name):
                run_dir, state, items = self._queue(1)
                self._dirty_the_tree()
                # COUNTED PER HOST, not cumulatively. Both hosts drive the SAME fixture repository and
                # therefore the same `events.jsonl`, so a raw count would see the oc host's event again
                # while checking agy and read as a duplicate. Truncating isolates each host's turn.
                (run_dir / "events.jsonl").write_text("", encoding="utf-8")

                self._drive(driver, spawn, run_dir, state, items[0])

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                warnings = [e for e in events if e.get("event") == "clean-base-warning"]
                self.assertEqual(len(warnings), 1, events)
                self.assertEqual(warnings[0]["dirty_paths"], ["notes.md"])
                # And NO refusal was recorded for this isolated item.
                self.assertEqual(
                    [e for e in events if e.get("event") == "clean-base-refused"], []
                )

    def test_a_whole_queue_of_isolated_items_survives_one_out_of_scope_dirty_path(self):
        """THE REGRESSION FOR `run-20260913T031148Z-1722898`: 23 of 41 items blocked by one file.

        Three items, one dirty tracked path OUTSIDE every plan's declared scope (each declares
        `src/`, the dirt is `notes.md`). EVERY item must launch and none may be `blocked`. The old
        contract blocked all three.
        """
        for name, driver, spawn in _SPAWNS:
            with self.subTest(driver=name):
                run_dir, state, items = self._queue(3)
                self._dirty_the_tree()

                launched = [
                    self._drive(driver, spawn, run_dir, state, item) for item in items
                ]

                self.assertEqual(len(items), 3)
                for index, item in enumerate(items):
                    self.assertGreaterEqual(
                        launched[index], 1, f"item {item['id6']} did not launch"
                    )
                    self.assertNotEqual(
                        item["status"], "blocked", f"item {item['id6']} was blocked"
                    )
                    self.assertIn(
                        "notes.md", item["attempts"][-1]["clean_base_dirty_paths"]
                    )
                self.assertEqual(
                    [i for i in items if i["status"] == "blocked"],
                    [],
                    "no item may be blocked by a dirty path no plan declares",
                )

    def test_the_operator_facing_line_is_ONCE_PER_RUN_not_once_per_item(self):
        """The plan's OQ-01: the RECORD is per attempt, the human-facing SENTENCE is per run.

        ASSERTED STRUCTURALLY, because "how many times does an operator see this?" is a question about
        WHERE the print lives. The per-item `execute_item` block must contain no print of the warning
        (a print there repeats N times, the exact defect `3i0aaz`'s review rejected in its PR-005),
        and the once-per-run seam must be `initialize_run`.
        """
        from agent_workflows import runner_shared

        for name, driver, _spawn in _SPAWNS:
            with self.subTest(driver=name):
                body = _effective_execute_item_body(driver)
                warn_block = body.split("if decision.warned:", 1)
                self.assertEqual(len(warn_block), 2, f"{name}: warn branch missing")
                warn_block_text = warn_block[1].split("elif decision.consented:", 1)[0]
                self.assertNotIn(
                    "print(",
                    warn_block_text,
                    "the per-item branch must RECORD only; the operator line is once per run",
                )
                # The once-per-run seam exists and is reached from `initialize_run`.
                init = _module_source(driver).split("def initialize_run", 1)[1]
                self.assertIn("report_untracked_dirt_at_run_start", init)

        # And that shared run-start report is what emits the tracked-dirt sentence, from ONE git call.
        emitter = inspect.getsource(runner_shared.report_untracked_dirt_at_run_start)
        self.assertIn("evaluate_tracked_dirt(out)", emitter)
        self.assertEqual(
            emitter.count("runner(Path(repo)"), 1, "exactly one git status, not two"
        )

    def test_the_run_start_line_names_the_paths_and_promises_no_refusal(self):
        """The report must name the dirt, and must NOT claim an isolated turn will be refused."""
        from agent_workflows import runner_shared

        notice = runner_shared.evaluate_tracked_dirt(
            " M notes.md\nM  staged.py\n"
        ).notice
        self.assertIn("notes.md", notice)
        self.assertIn("staged.py", notice)
        self.assertIn("2 dirty TRACKED path(s)", notice)
        self.assertIn("does NOT refuse an isolated turn", notice)
        # The shared-tree half is still stated, so the operator learns the split rather than
        # concluding no dirty-base refusal exists anywhere.
        self.assertIn("--no-isolate-worktree", notice)
        # And it never tells anyone to touch work that may not be theirs.
        for forbidden in ("git stash", "git reset", "git clean", "delete"):
            self.assertNotIn(forbidden, notice)

    def test_the_run_start_report_excludes_UNTRACKED_and_IGNORED_entries(self):
        """The tracked report answers the base question; untracked is its sibling's business."""
        from agent_workflows import runner_shared

        report = runner_shared.evaluate_tracked_dirt(
            " M tracked.py\n?? new.py\n!! build/\n"
        )
        self.assertEqual(report.total, 1)
        self.assertEqual(report.sample, ("tracked.py",))
        self.assertTrue(runner_shared.evaluate_tracked_dirt("?? only.py\n").clean)


class SharedTreePathStillRefusesTests(unittest.TestCase):
    """The other half of the R5.4 split: `--no-isolate-worktree` is STILL refused (`d7qoxv` E-05).

    THE ONE TEST THAT PROVES THE SPLIT WAS HONORED RATHER THAN DESCRIBED. `d7qoxv` removes the
    isolated refusal only; the shared-tree refusal belongs to approved release-blocking plan `3i0aaz`
    E-03 and must survive this change intact. Its own suite
    (`tests/test_dirty_base_gate.py`) covers it end to end; this asserts the property from THIS plan's
    side so a future edit here cannot quietly take both paths down together.
    """

    def test_a_dirty_shared_tree_still_REFUSES_on_both_hosts(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            _git(repo, "init", "-q")
            _git(repo, "config", "user.email", "t@example.invalid")
            _git(repo, "config", "user.name", "t")
            (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
            _git(repo, "add", "tracked.txt")
            _git(repo, "commit", "-qm", "init")
            (repo / "tracked.txt").write_text("v2\n", encoding="utf-8")

            for name, driver in DRIVERS:
                with self.subTest(driver=name):
                    shared = driver.evaluate_clean_base_for_launch(
                        repo, shared_tree=True
                    )
                    self.assertFalse(shared.clean)
                    self.assertTrue(
                        shared.refuses, "the shared-tree refusal must survive"
                    )
                    self.assertIn("refusing to launch", shared.reason)
                    # The isolated path over the SAME dirt does not refuse: that is the split.
                    isolated = driver.evaluate_clean_base_for_launch(repo)
                    self.assertFalse(isolated.clean)
                    self.assertFalse(isolated.refuses)
                    # Only the disposition differs; the classification is identical.
                    self.assertEqual(isolated.dirty_paths, shared.dirty_paths)

    def test_the_spec_still_carries_a_shared_tree_obligation(self):
        """V-04's requirement as a test: the amendment must leave `3i0aaz` E-03 something to build on.

        Read from the spec text rather than asserted in prose, because an amendment that silently
        dropped the non-isolated obligation would negate an approved release blocker, and `aw specs
        check` cannot tell that a requirement lost half its meaning.
        """
        spec = sorted(
            Path(".aw/records/specs").glob("*7ckptx*worker-lane-containment.spec.md")
        )
        if (
            not spec
        ):  # pragma: no cover - the spec is tracked; skip only if run out of tree
            self.skipTest("spec file not present in this checkout")
        text = spec[0].read_text(encoding="utf-8")
        self.assertIn("R5.4", text)
        # The shared-tree refusal obligation, in the REQUIREMENT: still normative, still MUST.
        self.assertRegex(text, r"R5\.4[\s\S]{0,1500}?MUST be REFUSED")
        # And in the CRITERION, which must still demand the shared-tree refusal be asserted, so a plan
        # cannot satisfy A14 by testing the isolated path alone.
        criterion = text.split("- A14.", 1)
        self.assertEqual(len(criterion), 2, "A14 must still exist")
        a14 = criterion[1].split("\n- A1", 1)[0]
        self.assertIn("REFUSED", a14)
        self.assertIn("no-isolate-worktree", a14)
        # The isolated half must be an explicit PROCEEDS obligation, not merely an absent refusal.
        self.assertIn("PROCEEDS", a14)


if __name__ == "__main__":
    unittest.main()
