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

import argparse
import contextlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared

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


#: `_module_source` and `_effective_execute_item_body` USED TO LIVE HERE and are deleted with the last
#: of their callers. They existed only to feed source-TEXT assertions: the second one hand-extracted a
#: function body by `split("def execute_item", 1)`, followed the `execute_item_core` refactor with an
#: `if "execute_item_core" in body` branch, and then `replace("spawn_executor(", spawn_symbol)` so a
#: substring search would find the host's own spawn name in shared code. That machinery is exactly the
#: cost a source-text pin imposes: it had to be patched twice to chase refactors that changed no
#: behavior, and it still could not tell a real call from a comment. Every assertion that used it now
#: drives the code instead, so nothing needs a driver's source text.


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
    """R5.4's ordering clause: the guard runs BEFORE any worker process or lane is created.

    THIS CLASS NO LONGER COMPARES `body_text.find` OFFSETS, AND THAT MATTERS BEYOND THIS FILE.
    `tests/test_dirty_base_gate.py` cites "the `tests/test_lane_clean_base.py:158-190` method" as its
    precedent for establishing ordering structurally, in two places (its `NoSpawnAndNothingTouchedTests`
    docstring and `test_the_guard_still_PRECEDES_spawn_and_allocation_structurally`). THOSE CITATIONS
    ARE NOW STALE: the method they name no longer exists here, and the rationale they lean on (that a
    structural comparison is the acceptable way to state ordering) is the one this class rejected. That
    file was outside this change's scope so it is deliberately NOT edited here; a reader arriving from
    it should read the paragraphs below as the current position. Its own structural test is not
    redundant with what follows, because it drives a different fixture, but its stated JUSTIFICATION no
    longer has a home to point at.

    WHY THE OFFSET COMPARISON HAD TO GO, stated plainly because it was a deliberate choice once. It
    compared the character positions of three substrings inside a hand-extracted function body, so:
    a COMMENT mentioning the spawn symbol above the guard failed it while the code was correct; the
    guard appearing only in a docstring satisfied `find(...) != -1`; and the extraction itself (a
    `split("def execute_item")` plus a `replace()` that rewrote the spawn symbol) had already been
    patched to chase two refactors that changed no behavior. Textual position is also not the claim:
    "appears earlier in the source" is not "runs first", since either could sit in a branch the other
    path never reaches.

    WHAT REPLACES IT: the guard is made to RAISE, and the spawn and the lane allocator are patched to
    RECORD. If either recorded anything, it ran before the guard. That establishes ordering on the
    path an actual run takes, which is what R5.4 requires, and it is immune to renames, reformatting
    and comments alike. The honest limit, stated because the deleted test's docstring claimed the
    opposite trade: this drives ONE code path, so a reordering on a path no test drives is invisible
    here. The structural claim it cannot make is instead made by the two-host EVENT assertions below,
    which show that both hosts reach the same recorded outcomes through the same shared seam.
    """

    def _fixture(self, driver, *, isolate: bool):
        """A one-item run against a TemporaryDirectory repo, returning (run_dir, state, item)."""
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        _git(repo.parent, "init", "-q", str(repo))
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "t")
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "notes.md").write_text("v1\n", encoding="utf-8")
        plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260916-probe-01-prb001-probe.ipd.md"
        )
        plan.write_text(_PLAN.format(id6="prb001", order=1), encoding="utf-8")
        _git(repo, "add", ".gitignore", "notes.md", str(plan.relative_to(repo)))
        _git(repo, "commit", "-qm", "init")
        # The dirty tracked path the guard must observe, uncommitted.
        (repo / "notes.md").write_text("uncommitted edit\n", encoding="utf-8")

        run_dir = repo / ".aw" / "records" / "runs" / "run-probe"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        item = {
            "position": 1,
            "id6": "prb001",
            "setid": "probe",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-probe",
            "created_at": "2026-09-16T00:00:00+00:00",
            "updated_at": "2026-09-16T00:00:00+00:00",
            "selectors": ["probe"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "agy": "/bin/true",
                "model": "probe",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": isolate,
                "allow_dirty_base": False,
            },
        }
        return run_dir, state, item

    def test_nothing_is_spawned_or_allocated_before_the_guard_runs(self):
        """Behavioral ordering: the guard is made to RAISE and both later steps must not have run."""

        class _GuardReached(Exception):
            """Raised FROM the guard, so reaching it aborts the item at exactly that point."""

        for name, driver, spawn_symbol in _SPAWNS:
            with self.subTest(driver=name):
                run_dir, state, item = self._fixture(driver, isolate=True)
                spawned: list[object] = []
                allocated: list[object] = []

                def _guard(*_a, **_k):
                    raise _GuardReached()

                with (
                    mock.patch.object(driver, "evaluate_clean_base_for_launch", _guard),
                    mock.patch.object(
                        driver,
                        spawn_symbol,
                        lambda *a, **k: (
                            spawned.append((a, k))
                            or (0, "ses", str(run_dir / "log"), ["probe"])
                        ),
                    ),
                    mock.patch.object(
                        driver,
                        "allocate_isolation_worktree",
                        lambda *a, **k: allocated.append((a, k)),
                    ),
                    mock.patch.object(
                        driver, "driver_begin", lambda *a, **k: (0, "ok")
                    ),
                    mock.patch.object(
                        driver, "driver_finalize", lambda *a, **k: (0, "ok")
                    ),
                    mock.patch.object(
                        driver, "assert_child_tool_identity", lambda *a, **k: None
                    ),
                ):
                    with self.assertRaises(
                        _GuardReached,
                        msg=f"{name}: the clean-base guard was never reached at all, so R5.4 is "
                        "unwired on this host",
                    ):
                        driver.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    spawned,
                    [],
                    f"{name}: `{spawn_symbol}` ran BEFORE the clean-base guard. R5.4 requires the "
                    "decision to precede the spawn: a worker process started against an incomplete "
                    "base cannot be un-started",
                )
                self.assertEqual(
                    allocated,
                    [],
                    f"{name}: a lane worktree was allocated BEFORE the clean-base guard, so a "
                    "refusal would leave an orphan lane behind to clean up",
                )

    def test_the_dirty_paths_are_recorded_on_the_attempt_on_BOTH_dispositions(self):
        """The observation is auditable: the paths land in durable state, not only on stderr.

        REPLACES A SOURCE-TEXT PIN. This searched `execute_item`'s source for four literals
        (`attempt["clean_base_dirty_paths"]`, `attempt["clean_base_warning"]`, and the two
        `"event": "clean-base-..."` spellings). Every one of them is satisfied by a comment or by dead
        code in an unreachable branch, which is the opposite of "the paths reach durable state".

        BOTH DISPOSITIONS ARE STILL REQUIRED, which is what makes this a split rather than a rename,
        and now each is DRIVEN: the ISOLATED path must record a `clean-base-warning` event and the
        warning text on the attempt, and the SHARED-TREE path over the SAME dirt must record a
        `clean-base-refused` event and block the item. If the refusal disappears, the obligation
        approved plan `3i0aaz` E-03 owns has been dropped; if the warning disappears, the operator
        lost the signal that replaced it. Reading them out of the written `events.jsonl` and the
        written attempt is what proves they are DURABLE, which no source search can.
        """
        for name, driver, spawn_symbol in _SPAWNS:
            for isolate, want_event, want_field, want_status in (
                (True, "clean-base-warning", "clean_base_warning", "not-blocked"),
                (False, "clean-base-refused", "clean_base_refused", "blocked"),
            ):
                with self.subTest(driver=name, isolate=isolate):
                    run_dir, state, item = self._fixture(driver, isolate=isolate)
                    with (
                        mock.patch.object(
                            driver,
                            spawn_symbol,
                            lambda *a, **k: (
                                0,
                                "ses",
                                str(run_dir / "log"),
                                ["probe"],
                            ),
                        ),
                        mock.patch.object(
                            driver, "driver_begin", lambda *a, **k: (0, "ok")
                        ),
                        mock.patch.object(
                            driver, "driver_finalize", lambda *a, **k: (0, "ok")
                        ),
                        mock.patch.object(
                            driver, "assert_child_tool_identity", lambda *a, **k: None
                        ),
                    ):
                        driver.execute_item(run_dir, state, item, recovery=False)

                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    matching = [e for e in events if e.get("event") == want_event]
                    self.assertEqual(
                        len(matching),
                        1,
                        f"{name} (isolate={isolate}): expected exactly one {want_event!r} event in "
                        f"durable run state, got {[e.get('event') for e in events]!r}",
                    )
                    self.assertEqual(
                        matching[0]["dirty_paths"],
                        ["notes.md"],
                        f"{name}: the event must NAME the dirty paths, not merely count them (R5.4)",
                    )
                    attempt = item["attempts"][-1]
                    self.assertEqual(
                        attempt["clean_base_dirty_paths"],
                        ["notes.md"],
                        f"{name} (isolate={isolate}): the paths must reach the ATTEMPT record, so an "
                        "audit after the run can see what the base was missing",
                    )
                    self.assertIn(
                        "notes.md",
                        attempt[want_field],
                        f"{name} (isolate={isolate}): the {want_field!r} sentence must name the path",
                    )
                    if want_status == "blocked":
                        self.assertEqual(item["status"], "blocked")
                    else:
                        self.assertNotEqual(item["status"], "blocked")


class SharedPredicateTests(unittest.TestCase):
    """R6.1: neither driver re-decides what "dirty" means, and neither forks the parser."""

    def setUp(self) -> None:
        # A DIRTY tracked tree, so the delegation test below has a non-trivial verdict to observe.
        # In a TemporaryDirectory, never this checkout, for the reason the file's header records.
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
        (self.repo / "tracked.txt").write_text("v2\n", encoding="utf-8")
        # An untracked file too, so the scope assertion is not vacuous: a guard that dropped
        # `--untracked-files=no` would see this and report it.
        (self.repo / "untracked.txt").write_text("u\n", encoding="utf-8")

    def test_both_guards_delegate_to_the_shared_rule(self):
        """Each host's guard CALLS `lane_containment.evaluate_clean_base` and asks git for the R5.4
        scope, proved by driving it rather than by reading its source.

        REPLACES A SOURCE-TEXT PIN. This searched each guard's source text for
        `"lane_containment.evaluate_clean_base("` and `"--untracked-files=no"`, with a hand-rolled
        `split("def ...")` body extractor that had already been patched once to follow the
        `runner_shared` refactor. Both searches are satisfied by a COMMENT (and this repository has
        measured exactly that failure twice, once on `env=pinned_child_env()`), and both break on a
        refactor that preserves behavior, which is why the extractor needed patching at all.

        WHAT IS ASSERTED INSTEAD, per host:
          1. the shared RULE is called, ONCE, with the porcelain text the host fetched and with
             `shared_tree` passed through rather than re-interpreted;
          2. the git invocation carries `--untracked-files=no`, read from the ARGV the host actually
             passes (so the R5.4 scope is observed, not spelled);
          3. the shared rule's RESULT is returned by identity, via a sentinel `CleanBaseResult` that
             no substring search could ever see. A host that re-decided anything would rebuild it.
        """
        SENTINEL = lane_containment.CleanBaseResult(
            clean=False,
            dirty_paths=("SENTINEL/only-the-shared-rule-can-produce-this.py",),
            shared_tree=True,
        )
        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                with (
                    mock.patch.object(
                        lane_containment,
                        "evaluate_clean_base",
                        wraps=lane_containment.evaluate_clean_base,
                    ) as rule,
                    # SPY ON THE SHARED `_run_git`, NOT THE DRIVER'S (hostdedup Order 01, `li44r9`,
                    # E-07). `evaluate_clean_base_for_launch` was byte-identical in both drivers and now
                    # has ONE definition in `runner_shared`, so that module's `_run_git` is the one that
                    # fetches the porcelain. EVERY ASSERTION BELOW IS UNCHANGED -- the one-call count,
                    # the `shared_tree` pass-through, the R5.4 `--untracked-files=no` scope read off the
                    # real argv, and the sentinel identity check -- because this spy observes the SAME
                    # single real call. It is `wraps=`, so git still really runs against the fixture.
                    mock.patch.object(
                        runner_shared, "_run_git", wraps=runner_shared._run_git
                    ) as git,
                ):
                    result = driver.evaluate_clean_base_for_launch(
                        self.repo, shared_tree=True
                    )

                # 1. ONE call into the shared rule, carrying the porcelain and the flag.
                self.assertEqual(
                    rule.call_count,
                    1,
                    f"{name}: the guard must reach the ONE shared rule exactly once; it called it "
                    f"{rule.call_count} times, so this host decides `dirty` itself and the two hosts "
                    "can drift on a containment guarantee (CID-3)",
                )
                self.assertEqual(
                    rule.call_args.kwargs.get("shared_tree"),
                    True,
                    f"{name}: `shared_tree` must be PASSED THROUGH, never interpreted here; "
                    "deciding the message locally forks the rule (R6.1)",
                )
                self.assertIn(
                    "tracked.txt",
                    rule.call_args.args[0],
                    f"{name}: the rule must be handed the porcelain this host just fetched",
                )

                # 2. The R5.4 SCOPE, read from the argv the host passes to git.
                statuses = [
                    list(c.args[1])
                    for c in git.call_args_list
                    if c.args[1] and c.args[1][0] == "status"
                ]
                self.assertTrue(
                    statuses, f"{name}: the guard ran no `git status` at all"
                )
                self.assertTrue(
                    all("--untracked-files=no" in argv for argv in statuses),
                    f"{name}: the R5.4 scope is TRACKED PATHS ONLY, and this host asked git for "
                    f"more: {statuses!r}. Including untracked content would make an unattended run "
                    "unstartable in essentially any working checkout (finding F-4)",
                )

                # 3. The shared rule's verdict is what comes back, unrebuilt.
                self.assertFalse(result.clean)
                with mock.patch.object(
                    lane_containment, "evaluate_clean_base", lambda *a, **k: SENTINEL
                ):
                    passed_through = driver.evaluate_clean_base_for_launch(self.repo)
                self.assertIs(
                    passed_through,
                    SENTINEL,
                    f"{name}: the shared rule's own result object must be returned; this host "
                    "rebuilt or post-processed it, which is where a per-host divergence hides",
                )

    def test_dirty_tree_overlap_is_ONE_predicate_reached_by_both_hosts(self):
        """R6.1 for the overlap check: ONE definition, reached by identity from both hosts.

        A WRONG EXPECTATION WAS FOUND HERE AND IS CORRECTED, which is why this test is renamed. The
        old `test_dirty_tree_overlap_no_longer_forks_the_parser` asserted, of any host that did NOT
        re-export the shared object, that its body contained
        `"lane_containment.parse_porcelain_paths("` and did NOT contain `'entry.split(" -> ", 1)'`.
        Two things were true of that, both measured in this worktree on 2026-09-19:

          1. IT WAS VACUOUS. `oc_runipd.dirty_tree_overlap` and `agy_runipd.dirty_tree_overlap` are
             BOTH `runner_shared.dirty_tree_overlap` by identity, so the `continue` fired for every
             host and the two source assertions never executed on anything.
          2. ITS CLAIM WAS FALSE. `runner_shared.dirty_tree_overlap` does NOT call
             `parse_porcelain_paths`; it still carries the hand-rolled loop, INCLUDING the literal
             `entry.split(" -> ", 1)` the test declared must be absent. So had the `continue` not
             hidden it, the test would have failed on shipped, correct code.

        The delegation was therefore never achieved for THIS predicate, and asserting it here would
        be asserting a refactor nobody performed. What R6.1 does buy today is a SINGLE DEFINITION
        reached by both hosts, which is asserted by identity (the strongest available form: an
        identity re-export cannot drift at all, whereas two delegating copies can still diverge
        around the delegation).

        AND THE PARSE IS PINNED BEHAVIORALLY INSTEAD, over the porcelain forms where a hand-rolled
        loop and the shared decoder could differ: rename and copy endpoints, staged versus unstaged
        columns, deletions, and unmerged entries. Measured agreement on all of them today, which is
        the honest statement of the situation: the two parsers agree, the duplication is real, and
        this table is what would catch them drifting apart. Removing the duplication is a separate
        change and would make this table go green from ONE parser rather than two.
        """
        from agent_workflows import runner_shared as _shared

        for name, driver in DRIVERS:
            with self.subTest(driver=name):
                self.assertIs(
                    getattr(driver, "dirty_tree_overlap", None),
                    _shared.dirty_tree_overlap,
                    f"{name} does not reach the ONE shared `dirty_tree_overlap`; a per-host copy "
                    "lets the two hosts refuse different integrations (R6.1 / CID-3)",
                )

        # THE DUPLICATED PARSE, pinned by AGREEMENT rather than by asserting a delegation that does
        # not exist. Each row is a porcelain form where the two decoders could plausibly differ.
        forms = (
            (" M a.py\n", "an unstaged modification"),
            (
                "M  a.py\n",
                "a STAGED modification: the columns are swapped, so a decoder that "
                "sliced the wrong width would lose the path",
            ),
            ("MM a.py\n", "staged AND unstaged, the two-column case"),
            (
                "R  old.py -> new.py\n",
                "a RENAME: BOTH endpoints must be dirty, or integrating over "
                "a rename clobbers whichever end the decoder dropped",
            ),
            (
                "C  a.py -> b.py\n",
                "a COPY, which uses the same ` -> ` rendering as a rename",
            ),
            ("D  gone.py\n", "a staged deletion"),
            (
                "UU conflict.py\n",
                "an unmerged entry, whose columns are neither of the usual pair",
            ),
            (
                "?? new.py\n",
                "an untracked path, which this check DOES include (unlike the R5.4 "
                "clean-base rule) because it asks a different question",
            ),
            (
                " M a.py\nR  o.py -> n.py\n?? u.py\n",
                "a MIXED transcript, which is what a real dirty "
                "tree looks like and the only row that exercises the loop across forms",
            ),
        )
        disagreed = []
        for porcelain, why in forms:
            shared_answer = lane_containment.parse_porcelain_paths(porcelain)
            overlap_answer = set()
            for path in shared_answer | {"a-path-that-is-never-dirty.py"}:
                # Drive the real predicate through a stub git so the PARSE is the only variable.
                with mock.patch.object(
                    _shared, "_run_git", lambda _r, _a: (0, porcelain, "")
                ):
                    if _shared.dirty_tree_overlap(Path("."), [path]):
                        overlap_answer.add(path)
            if overlap_answer != shared_answer:
                disagreed.append(
                    f"  {porcelain!r}: the shared decoder sees {sorted(shared_answer)!r} but "
                    f"`dirty_tree_overlap` treats {sorted(overlap_answer)!r} as dirty\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            disagreed,
            [],
            f"the two porcelain decoders disagree on {len(disagreed)} of {len(forms)} forms. THERE "
            "ARE GENUINELY TWO: `lane_containment.parse_porcelain_paths` is the declared single "
            "decoder, and `runner_shared.dirty_tree_overlap` still carries its own hand-rolled loop "
            "(measured 2026-09-19; the test that claimed otherwise was vacuous and its claim was "
            "false). This table is what catches them drifting. FIX: prefer deleting the duplicate "
            "loop in favour of the shared decoder over patching one side to match the other, since "
            "the overlap check REFUSES an integration and a decoder that loses a rename endpoint "
            "would let a merge clobber it.\n" + "\n".join(disagreed),
        )

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

        REPLACES A SOURCE-TEXT PIN, AND THE PIN COULD NOT ESTABLISH THIS CLAIM AT ALL. This is a
        CARDINALITY assertion: an operator sees the sentence ONCE however many items are queued. The
        old version asserted `assertNotIn("print(", <the warn branch's source text>)` plus
        `assertIn("report_untracked_dirt_at_run_start", <initialize_run's source>)` plus
        `emitter.count("runner(Path(repo)") == 1`. None of those counts EMISSIONS: a print reached
        through a helper, a logger, or a `sys.stderr.write` satisfies the `assertNotIn` while
        repeating N times, the `assertIn` is satisfied by the mention inside `initialize_run`'s own
        DOCSTRING (which is in fact the only place that literal appears in either driver today, since
        the call itself lives in `runner_shared.initialize_run_core`), and counting a call-expression's
        source spelling says nothing about how many times it executes.

        SO THE CARDINALITY IS MEASURED. A real run is driven with THREE queued items over one dirty
        tracked path, both streams are captured, and the run-start sentence must appear EXACTLY ONCE
        in the whole transcript. The sentence is not spelled out here: it is compared against the
        shared renderer's OWN output (`evaluate_tracked_dirt(...).notice`), so a reworded message stays
        green while a message emitted per item fails. Then the other half of the split is asserted
        from the same transcript: the PER-ATTEMPT record exists three times (once per item) while its
        text was never printed, which is what "record per item, sentence per run" actually means.

        WHY THE PER-ITEM PRINT MATTERS: it is the defect `3i0aaz`'s review rejected in its PR-005, and
        the measured incident behind this whole area had 41-item queues.
        """
        from agent_workflows import runner_shared

        for name, driver, spawn_symbol in _SPAWNS:
            with self.subTest(driver=name):
                repo, ids = self._three_item_repo()
                buf = io.StringIO()
                with (
                    contextlib.redirect_stdout(buf),
                    contextlib.redirect_stderr(buf),
                ):
                    run_dir = driver.initialize_run(self._start_args(repo, ids))
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    with (
                        mock.patch.object(
                            driver,
                            spawn_symbol,
                            lambda *a, **k: (
                                0,
                                "ses",
                                str(run_dir / "log"),
                                ["probe"],
                            ),
                        ),
                        mock.patch.object(
                            driver, "driver_begin", lambda *a, **k: (0, "ok")
                        ),
                        mock.patch.object(
                            driver, "driver_finalize", lambda *a, **k: (0, "ok")
                        ),
                        mock.patch.object(
                            driver, "assert_child_tool_identity", lambda *a, **k: None
                        ),
                    ):
                        for item in state["queue"]:
                            driver.execute_item(run_dir, state, item, recovery=False)
                transcript = buf.getvalue()

                self.assertEqual(
                    len(state["queue"]),
                    3,
                    "the fixture must queue MORE THAN ONE item, or 'once per run' and 'once per "
                    "item' are the same number and this test proves nothing",
                )

                # The sentence, taken from the shared renderer rather than spelled here, so a
                # rewording does not fail and a repetition does.
                notice = runner_shared.evaluate_tracked_dirt(" M notes.md\n").notice
                self.assertEqual(
                    transcript.count(notice),
                    1,
                    f"{name}: the run-start tracked-dirt sentence was emitted "
                    f"{transcript.count(notice)} times for a 3-item queue. ONE means once per run "
                    "(correct); THREE means it moved to the per-item seam, which is the PR-005 defect "
                    "and would have printed 41 identical paragraphs on the measured incident's queue; "
                    "ZERO means the operator now gets no warning at all, which is the silence the "
                    "report replaced.",
                )

                # The other half of the split: the RECORD is per item, and it was never PRINTED.
                warnings = [
                    item["attempts"][-1]["clean_base_warning"]
                    for item in state["queue"]
                ]
                self.assertEqual(
                    len(warnings),
                    3,
                    f"{name}: every item must carry its own durable warning record",
                )
                for warning in warnings:
                    self.assertIn("notes.md", warning)
                    self.assertNotIn(
                        warning,
                        transcript,
                        f"{name}: the PER-ITEM warning sentence was printed. It must be RECORDED "
                        "only; the operator-facing line is the once-per-run one asserted above",
                    )

    def _start_args(self, repo: Path, selectors: list[str]) -> argparse.Namespace:
        return argparse.Namespace(
            repo=str(repo),
            selectors=selectors,
            manifest=None,
            runbook=None,
            session=None,
            run_id=None,
            full_auto=False,
            opencode="/bin/true",
            agy="/bin/true",
            model=None,
            agent=None,
            auto=True,
            output_mode="clean",
            stall_timeout=600.0,
            validate=False,
            self_finalize=True,
            isolate_worktree=True,
            max_items_per_session=4,
        )

    def _three_item_repo(self) -> tuple[Path, list[str]]:
        """A fresh repo with THREE approved plans and ONE dirty tracked path outside every scope.

        MORE THAN ONE ITEM IS THE POINT: the cardinality claim above is unfalsifiable on a one-item
        queue, because once-per-run and once-per-item coincide there. Each plan declares `src/` while
        the dirt is `notes.md`, mirroring the measured incident's uncommitted markdown.
        """
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        _git(repo.parent, "init", "-q", str(repo))
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "t")
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "notes.md").write_text("v1\n", encoding="utf-8")
        ids: list[str] = []
        for index in (1, 2, 3):
            id6 = f"prb{index:03d}"
            ids.append(id6)
            (pending / f"20260916-probe-{index:02d}-{id6}-probe.ipd.md").write_text(
                _PLAN.format(id6=id6, order=index), encoding="utf-8"
            )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "init")
        (repo / "notes.md").write_text("uncommitted edit\n", encoding="utf-8")
        return repo, ids

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
