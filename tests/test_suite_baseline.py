#!/usr/bin/env python3
"""integearn-05 (`9lyg5h`): the PRE-WORK SUITE BASELINE, and the proof it is not a gate.

WHAT THIS FILE PROVES, and why each case earns its place rather than merely passing.

THE DEFECT BEING CLOSED IS STRUCTURAL, not a bug. Sibling `daexj1`/`h5pyqa` stopped the runner
silently refusing integration over a red suite and instead ASKS the executing agent to adjudicate,
where `not-mine` means (among other things) "it was already failing before my turn". But to know a
failure is PRE-EXISTING the agent must know the test was already failing before it started, and
nothing told it: `run_suite_check` is called exactly ONCE per attempt, AFTER the work, and no prior
result was persisted anywhere. So an agent that broke something subtly, and genuinely believes the
failure is unrelated, answered `not-mine` in GOOD FAITH and was WRONG. This plan supplies the
missing half.

THE ONE PROPERTY A FUTURE READER IS MOST LIKELY TO ERODE, and the reason this module exists at all:

    THE BASELINE IS INFORMATION, NOT A GATE.

The maintainer ruled that explicitly (2026-09-08, reaffirmed 2026-09-20) and REJECTED the
originally-proposed constraint ("refuse `not-mine` for any failing id absent from the baseline") in
as many words, on the reasoning that a gate cannot detect deception, a capable model can simply make
tests pass, a genuinely malicious agent would rewrite the gate, and the target is SLOPPINESS rather
than malice. A baseline sitting in a run record LOOKS like something to check, so
`NothingRefusesOnTheBaseline` asserts the absence of such a path rather than trusting a comment.

THE CASES, mapped to the plan's E-07 (a)-(g):

  (a) A baseline COMPLETES and its failing set reaches the prompt.
  (b) The baseline TIMES OUT and the item proceeds with an UNKNOWN baseline, never an empty one.
  (c) The checkout CANNOT BE CREATED and the item proceeds unaffected.
  (d) A crashed turn leaves NO stray worktree.
  (e) The verdict outcome is IDENTICAL with and without the failing id in the baseline.
  (f) BOTH hosts persist the identical shape.
  (g) THE LANE-SAFETY CASE. With the agent's lane present and EMPTY, the baseline's allocation and
      cleanup leave that lane's branch, reflog and worktree INTACT; and with the agent's lane holding
      a commit, no `_attempt2` lane and no bogus owner record are created. This case is NOT optional:
      review MEASURED the plan's original prescription (allocate through
      `worktree_lease.allocate_worktree` keyed on the item's own id6, then tear down unconditionally)
      ADOPTING the agent's own lane at the same path and then DELETING its branch, its reflog and its
      commits. It is the one case whose absence would let a work-destroying implementation pass.

NO REAL SUITE IS RUN. An ~2-3 minute suite per case would make this module unusable and would make
the tests depend on this repository being green; every suite invocation is a stub script, exactly as
the sibling `tests/test_gate_answer_wiring.py` stubs its host calls.

NO REAL WORKTREE IS CREATED IN THIS REPOSITORY. Several lanes and live runs exist concurrently here
and this repository has already lost work to stranded worktrees, so every git case builds a throwaway
repo in a `tempfile` directory.

NOTHING READS `.aw/records/runs/`, which is gitignored: a test asserting against it passes on one
machine and fails in CI.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from typing import Any

from agent_workflows import agy_runipd as AGY
from agent_workflows import oc_runipd as OC
from agent_workflows import runner_shared as R
from agent_workflows import worktree_lease

HOSTS = (("oc_runipd", OC), ("agy_runipd", AGY))


# ---- helpers -------------------------------------------------------------------------------------


def _git(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def _throwaway_repo(root: pathlib.Path) -> pathlib.Path:
    """A real git repository with one commit. Used instead of THIS repository, deliberately."""

    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-qm", "seed")
    return repo


def _fake_suite(root: pathlib.Path, *, stdout: str, exit_code: int = 1) -> list[str]:
    """An argv that prints canned pytest-shaped output. THE STUB that keeps this module free."""

    script = root / "fake_suite.py"
    script.write_text(
        "import sys\n"
        f"sys.stdout.write({stdout!r})\n"
        f"raise SystemExit({int(exit_code)})\n",
        encoding="utf-8",
    )
    return [sys.executable, str(script)]


def _hanging_suite(root: pathlib.Path) -> list[str]:
    """An argv that never exits, for the TIMEOUT case. Killed by the collector, never awaited."""

    script = root / "hanging_suite.py"
    script.write_text(
        "import time\nwhile True:\n    time.sleep(3600)\n", encoding="utf-8"
    )
    return [sys.executable, str(script)]


_SUITE_OUTPUT = (
    "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2\n"
    "ERROR tests/test_broken_import.py\n"
    "1 failed, 4 passed, 1 error in 3.21s\n"
)


def _suite_result(
    failures: tuple[str, ...] = (
        "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
    ),
) -> OC.SuiteCheckResult:
    return OC.SuiteCheckResult(
        passing=False,
        exit_code=1,
        summary="1 failed, 7830 passed, 3 skipped, 2 xfailed in 198.60s",
        reason="stub",
        cwd="/primary",
        timeout_seconds=OC.SUITE_CHECK_TIMEOUT_SECONDS,
        elapsed_seconds=198.6,
        failures=failures,
    )


def _completed(
    failures: tuple[str, ...] = (
        "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
    ),
    *,
    base_commit: str = "0123456789abcdef",
) -> R.SuiteBaseline:
    return R.SuiteBaseline(
        state=R.SUITE_BASELINE_COMPLETED,
        base_commit=base_commit,
        failures=failures,
        reason="",
        summary="1 failed, 4 passed in 3.21s",
        exit_code=1,
        elapsed_seconds=3.21,
    )


def _core_source() -> str:
    return inspect.getsource(R.execute_item_core)


def _code_only(source: str) -> str:
    """`source` with every COMMENT and DOCSTRING removed, leaving only executable code.

    WHY THIS EXISTS, and it is not incidental to what this module asserts. Several assertions here are
    of the form "this name/call must NOT appear", and the implementation DELIBERATELY names the
    forbidden things in its PROSE: `remove_suite_baseline_checkout`'s docstring explains at length that
    it is not `worktree_lease.teardown_worktree`, and the producer's header comment quotes the
    `FAILED`/`ERROR` lines it must not itself parse. Grepping raw source would therefore fail on the
    very documentation that makes the constraint legible, which would push a future maintainer to
    DELETE the explanation in order to make the test pass - exactly backwards.

    So the absence is asserted over CODE, where it is a real property, and the prose is asserted
    SEPARATELY and POSITIVELY (see `test_the_ruling_is_recorded_at_the_code`).
    """

    tree = ast.parse(textwrap.dedent(source))
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)
    return ast.unparse(tree)


# ==================================================================================================
# E-01 / V-01: the two measurements are comparable, and the divergence is GONE
# ==================================================================================================
class TheTwoMeasurementsAreComparable(unittest.TestCase):
    """V-01. THE REGRESSION TEST FOR A DIVERGENCE THAT IS CURRENTLY ZERO.

    E-01's honest outcome was a MEASUREMENT, not code. Measured 2026-09-21 at `24aa8d41`, in a real
    linked worktree (`git worktree add --detach`) of a fresh clone holding ZERO run directories, which
    is exactly the condition the historically-cited defect (backlog `dh0uno`) describes:

        primary  tests/test_run_viewer.py -> 91 passed
        lane     tests/test_run_viewer.py -> 91 passed
        primary  bare suite -> 1 failed, 7830 passed, 3 skipped, 2 xfailed in 118.47s
        lane     bare suite -> 1 failed, 7830 passed, 3 skipped, 2 xfailed in 107.20s

    IDENTICAL, including the single environmental failure. So NO neutralization layer and NO
    subtraction list is built, deliberately: `dh0uno` is `done` and its own history retracts the
    acceptance claim that ~15 `test_run_viewer` failures were that bug, and building a subtraction
    list from the stale fifteen ids would MASK fifteen real failures rather than remove fifteen
    phantom ones. A hand-maintained list would also ROT.

    WHAT IS ASSERTED HERE INSTEAD is the PROPERTY that makes the two results comparable, so a
    regression is caught by a red test rather than by an incident: both sides run the SAME argv over
    the SAME repository, and their failing ids are extracted by the SAME function. If someone gives
    the baseline its own argv, its own flags or its own parser, these fail.
    """

    def test_both_sides_extract_failing_ids_with_the_SAME_function(self) -> None:
        """One extractor, or the two id sets are not comparable and the context is misleading."""

        self.assertIs(OC.extract_suite_failures, AGY.extract_suite_failures)
        core = _core_source()
        self.assertIn("extract_suite_failures", core)
        self.assertNotIn(
            "FAILED|ERROR",
            inspect.getsource(R.SuiteBaselineRun),
            "the baseline must NOT carry its own failure-line pattern; a second parser is how the "
            "pre-work and post-work id sets stop being comparable",
        )

    def test_the_baseline_runs_the_SAME_argv_as_the_post_work_check(self) -> None:
        core = _core_source()
        self.assertIn('getattr(driver_module, "SUITE_CHECK_ARGV")', core)
        self.assertEqual(tuple(OC.SUITE_CHECK_ARGV), tuple(AGY.SUITE_CHECK_ARGV))

    def test_the_baseline_builds_NO_neutralization_or_subtraction_layer(self) -> None:
        """A layer guarding a condition nobody can measure is dead code that masks real failures."""

        src = inspect.getsource(R)
        section = src[
            src.index("# THE PRE-WORK SUITE BASELINE") : src.index(
                "# THE INTEGRATION-REFUSAL ANSWER"
            )
        ]
        for forbidden in ("KNOWN_DIVERGENT", "PHANTOM_FAILURES", "_SUBTRACT"):
            self.assertNotIn(
                forbidden,
                section,
                f"{forbidden}: no subtraction list may be built; the divergence measured ZERO and a "
                "stale list would mask real failures",
            )

    def test_the_comparability_decision_is_DOCUMENTED_at_the_producer(self) -> None:
        """A future maintainer must be able to tell a real difference from a measurement artifact."""

        src = inspect.getsource(R)
        section = src[
            src.index("# THE PRE-WORK SUITE BASELINE") : src.index(
                "# THE INTEGRATION-REFUSAL ANSWER"
            )
        ]
        self.assertIn("WHY THE MEASUREMENT IS COMPARABLE", section)
        self.assertIn("dh0uno", section)


# ==================================================================================================
# E-02 / V-02 case (g): THE LANE-SAFETY CASE. The one that must not destroy work.
# ==================================================================================================
class TheBaselineCannotTouchTheAgentsLane(unittest.TestCase):
    """E-07 case (g). MEASURED destructive alternative, asserted against.

    Review measured the plan's ORIGINAL prescription doing this, end to end: allocate the baseline via
    `worktree_lease.allocate_worktree` with the item's own id6 -> disposition `adopted` AT THE SAME
    PATH as the agent's lane -> the agent commits -> unconditional `teardown_worktree` deletes the
    agent's BRANCH and its REFLOG, leaving the commit reachable from no ref. Unrecoverable.

    The documented liveness gate does not stop it (`lane_is_safe_to_adopt` returns
    `no owner record; unclaimed`, and same-PID is treated as allowed self-reallocation). So this class
    asserts the implemented route CANNOT reach the lane, by construction AND adversarially.
    """

    def test_the_baseline_path_is_OUTSIDE_the_lane_namespace_by_construction(
        self,
    ) -> None:
        """Route (b): a detached checkout, not a lane. No lane classifier can mistake it for one."""

        with tempfile.TemporaryDirectory() as temp:
            repo = pathlib.Path(temp) / "repo"
            baseline = R.suite_baseline_checkout_path(repo, "abc123", 1)
            lane = (repo / worktree_lease.WORKTREES_SUBDIR / "abc123").resolve()
            self.assertNotEqual(baseline, lane)
            self.assertNotIn(
                worktree_lease.WORKTREES_SUBDIR,
                str(baseline),
                "a baseline under `.aw/worktrees/` could be adopted, attempt-scoped or reclaimed as "
                "a lane; it must live outside that namespace entirely",
            )
            self.assertIn(R.SUITE_BASELINE_SUBDIR, str(baseline).replace(os.sep, "/"))

    def test_the_producer_calls_NEITHER_allocate_worktree_NOR_teardown_worktree(
        self,
    ) -> None:
        """The two functions that did the damage. Their absence is the fix, so it is asserted."""

        for symbol in (
            R.start_suite_baseline,
            R.remove_suite_baseline_checkout,
            R.SuiteBaselineRun,
        ):
            code = _code_only(inspect.getsource(symbol))
            with self.subTest(symbol=getattr(symbol, "__name__", str(symbol))):
                self.assertNotIn("allocate_worktree", code)
                self.assertNotIn("teardown_worktree", code)
                self.assertNotIn("worktree_lease", code)

    def test_the_removal_path_can_delete_NO_REF_AT_ALL(self) -> None:
        """`teardown_worktree` deletes the lane BRANCH and its REFLOG. This must not be able to."""

        code = _code_only(inspect.getsource(R.remove_suite_baseline_checkout))
        for forbidden in ("branch", "-D", "update-ref", "reflog"):
            self.assertNotIn(
                forbidden,
                code,
                f"the baseline's removal path must not be able to touch a ref ({forbidden!r}); a "
                "detached checkout has nothing to delete but a directory",
            )

    def test_ADVERSARIAL_an_EMPTY_agent_lane_survives_allocation_and_cleanup(
        self,
    ) -> None:
        """Case (g), first half: the exact sequence review measured DESTROYING an agent's branch."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            # The driver allocates the agent's lane, exactly as `execute_item_core` does.
            agent = worktree_lease.allocate_worktree(repo, "abc123", base_commit="HEAD")
            self.assertTrue(agent.path.exists())
            reflog_before = _git(repo, "reflog", "show", agent.branch).stdout

            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_fake_suite(root, stdout=_SUITE_OUTPUT),
                extract_failures=OC.extract_suite_failures,
                parse_summary=OC.parse_suite_summary,
            )
            self.assertIsNone(absent, "the baseline should have started")
            assert run is not None
            self.assertNotEqual(
                run.checkout,
                agent.path,
                "THE MEASURED DEFECT: the baseline must never resolve to the agent's own lane path",
            )
            run.collect(wait_seconds=30.0)
            R.remove_suite_baseline_checkout(repo, run.checkout)

            # The lane must be byte-for-byte as it was: worktree, branch, reflog.
            self.assertTrue(agent.path.exists(), "the agent's WORKTREE was destroyed")
            self.assertIn(
                agent.branch,
                _git(repo, "branch", "--list", "aw/lane/*").stdout,
                "the agent's BRANCH was deleted",
            )
            self.assertEqual(
                reflog_before,
                _git(repo, "reflog", "show", agent.branch).stdout,
                "the agent's REFLOG was emptied",
            )
            self.assertFalse(
                run.checkout.exists(), "the baseline checkout was left behind"
            )

    def test_ADVERSARIAL_a_lane_HOLDING_A_COMMIT_gains_no_attempt2_and_no_owner_record(
        self,
    ) -> None:
        """Case (g), second half: the other timing, which attempt-scoped and polluted lane state."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            agent = worktree_lease.allocate_worktree(repo, "abc123", base_commit="HEAD")
            (agent.path / "agent_work.txt").write_text("real work\n", encoding="utf-8")
            _git(agent.path, "add", "agent_work.txt")
            _git(agent.path, "commit", "-qm", "the agent's work")
            agent_tip = _git(repo, "rev-parse", agent.branch).stdout.strip()

            owners_before = sorted(
                p.name for p in (repo / worktree_lease.OWNERS_SUBDIR).glob("*.json")
            )
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_fake_suite(root, stdout=_SUITE_OUTPUT),
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(absent)
            assert run is not None
            run.collect(wait_seconds=30.0)
            R.remove_suite_baseline_checkout(repo, run.checkout)

            branches = _git(repo, "branch", "--list", "aw/lane/*").stdout
            self.assertNotIn(
                "_attempt2",
                branches,
                "no attempt-scoped lane may be created; `rl67b0`/`pr5b0t` exist to REDUCE this "
                "clutter and this plan must not add to it",
            )
            self.assertEqual(
                owners_before,
                sorted(
                    p.name for p in (repo / worktree_lease.OWNERS_SUBDIR).glob("*.json")
                ),
                "no owner record may be written under a bogus lane identity; `resolve_prior_lane` "
                "reads that state",
            )
            self.assertEqual(
                agent_tip,
                _git(repo, "rev-parse", agent.branch).stdout.strip(),
                "the agent's commit must still be reachable from its branch",
            )

    def test_the_baseline_NEVER_READS_the_agents_lane(self) -> None:
        """Reading a lane the agent is writing would sample half-written files."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            agent = worktree_lease.allocate_worktree(repo, "abc123", base_commit="HEAD")
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_fake_suite(root, stdout=_SUITE_OUTPUT),
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(absent)
            assert run is not None
            try:
                self.assertNotEqual(run.checkout, agent.path)
                self.assertFalse(
                    str(run.checkout).startswith(str(agent.path)),
                    "the baseline must not run inside the agent's lane",
                )
            finally:
                run.abandon()
                R.remove_suite_baseline_checkout(repo, run.checkout)


# ==================================================================================================
# E-02 / V-02: COMMIT-PINNING, and the field that exists at dispatch
# ==================================================================================================
class TheBaselineIsPinnedToACommit(unittest.TestCase):
    """V-02. Pinned to a COMMIT, never a branch, and read from a field that EXISTS at dispatch."""

    def test_the_base_commit_is_read_from_the_field_written_AT_ALLOCATION(self) -> None:
        """F-15: `item["preserved_base"]` is written only AFTER the turn. Reading it yields nothing."""

        core = _core_source()
        start = core.index("suite_baseline_run, suite_baseline = start_suite_baseline(")
        call = core[start : start + 700]
        self.assertIn('attempt.get("worktree_base")', call)
        self.assertNotIn(
            "preserved_base",
            call,
            'item["preserved_base"] is written on the POST-turn preservation path and only when the '
            "item did NOT reach executed, so it is ABSENT at dispatch for a first attempt",
        )

    def test_a_MOVED_main_does_not_change_what_the_baseline_describes(self) -> None:
        """The maintainer's own requirement: a mid-turn merge must not re-point the baseline."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            base = _git(repo, "rev-parse", "HEAD").stdout.strip()

            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit=base,
                argv=_fake_suite(root, stdout=_SUITE_OUTPUT),
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(absent)
            assert run is not None
            # Somebody merges to main WHILE the turn runs.
            (repo / "someone_elses.txt").write_text(
                "merged mid-turn\n", encoding="utf-8"
            )
            _git(repo, "add", "someone_elses.txt")
            _git(repo, "commit", "-qm", "a mid-turn merge by a human or another agent")
            moved = _git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertNotEqual(base, moved)

            result = run.collect(wait_seconds=30.0)
            self.assertEqual(
                base,
                result.base_commit,
                "the baseline must still describe the tree THIS item started from",
            )
            self.assertEqual(
                base,
                _git(run.checkout, "rev-parse", "HEAD").stdout.strip(),
                "the CHECKOUT itself must be at the base commit, not at the moved main",
            )
            self.assertFalse(
                (run.checkout / "someone_elses.txt").exists(),
                "the mid-turn commit must not be visible in a commit-pinned baseline",
            )
            R.remove_suite_baseline_checkout(repo, run.checkout)

    def test_a_NON_ISOLATED_turn_gets_an_ABSENT_baseline_and_says_so(self) -> None:
        """`--no-isolate-worktree` has no handle and so no recorded base. Absence is the honest answer."""

        with tempfile.TemporaryDirectory() as temp:
            repo = _throwaway_repo(pathlib.Path(temp))
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="",
                argv=["true"],
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(run)
            assert absent is not None
            self.assertEqual(R.SUITE_BASELINE_ABSENT, absent.state)
            self.assertIn("NON-ISOLATED", absent.reason)
            self.assertFalse(absent.known)


# ==================================================================================================
# E-03 / V-03: concurrency, the bound, and the two REGRESSION GUARDS
# ==================================================================================================
class TheBaselineRunsConcurrentlyAndCannotDelayTheTurn(unittest.TestCase):
    """V-03. The concurrency mechanism, and why it cannot deadlock or hang a driver."""

    def test_run_suite_check_could_NOT_have_been_reused_because_it_BLOCKS(self) -> None:
        """F-17, asserted rather than asserted-in-prose: it is synchronous by construction."""

        from agent_workflows import run_evidence

        self.assertIn(
            "subprocess.run(", inspect.getsource(run_evidence.capture_command)
        )
        self.assertIn("capture_command", inspect.getsource(OC.run_suite_check))
        for split in ("poll", "communicate", "Popen"):
            self.assertNotIn(
                split,
                inspect.getsource(OC.run_suite_check),
                "run_suite_check has no start/poll/collect split, which is why a NEW concurrent path "
                "was required rather than a reuse",
            )

    def test_the_concurrency_is_a_child_process_PLUS_a_DAEMON_drain_thread(
        self,
    ) -> None:
        """The drain thread is what makes the classic full-pipe deadlock impossible."""

        src = inspect.getsource(R.SuiteBaselineRun)
        self.assertIn("subprocess.PIPE", src)
        self.assertIn("daemon=True", src)
        self.assertIn("communicate(", src)

    def test_the_collection_wait_DEFAULTS_TO_ZERO(self) -> None:
        """OQ-02's answer. A zero-wait collection cannot delay a turn BY CONSTRUCTION."""

        sig = inspect.signature(R.SuiteBaselineRun.collect)
        self.assertEqual(0.0, sig.parameters["wait_seconds"].default)
        core = _core_source()
        self.assertIn("suite_baseline_run.collect(wait_seconds=0.0)", core)

    def test_REGRESSION_GUARD_a_TIMED_OUT_baseline_yields_UNKNOWN_and_not_an_empty_set(
        self,
    ) -> None:
        """E-07 case (b). The first of the two guards: the runner must not become MORE FRAGILE.

        An empty failing set would tell the agent NOTHING WAS FAILING BEFORE, which is the exact
        inversion `daexj1` E-02 exists to prevent on the other side of this feature.
        """

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_hanging_suite(root),
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(absent)
            assert run is not None
            result = run.collect(wait_seconds=0.0)
            self.assertEqual(R.SUITE_BASELINE_ABSENT, result.state)
            self.assertFalse(result.known)
            self.assertEqual((), result.failures)
            self.assertIn("UNKNOWN", result.reason)
            prompt = R.gate_answer_question(failing="x", baseline=result)
            self.assertIn("UNKNOWN", prompt)
            self.assertNotIn("NOTHING was failing", prompt)
            R.remove_suite_baseline_checkout(repo, run.checkout)
            self.assertFalse(run.checkout.exists())

    def test_REGRESSION_GUARD_a_CREATION_FAILURE_leaves_the_item_unaffected(
        self,
    ) -> None:
        """E-07 case (c). The second guard: a baseline that cannot be taken is not a failed item."""

        with tempfile.TemporaryDirectory() as temp:
            repo = _throwaway_repo(pathlib.Path(temp))
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                argv=["true"],
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(run)
            assert absent is not None
            self.assertEqual(R.SUITE_BASELINE_ABSENT, absent.state)
            self.assertTrue(absent.reason)

    def test_the_baseline_does_NOT_inherit_run_suite_checks_FAIL_CLOSED_stance(
        self,
    ) -> None:
        """`run_suite_check` turns an unrunnable suite into a FAILURE. A missing baseline is neither."""

        self.assertIn("FAIL CLOSED", inspect.getdoc(OC.run_suite_check) or "")
        doc = inspect.getdoc(R.suite_baseline_absent) or ""
        self.assertIn("NOT A FAILED ITEM", doc)
        absent = R.suite_baseline_absent("the suite could not be executed")
        self.assertIsNone(absent.exit_code)
        self.assertFalse(absent.known)

    def test_a_COMPLETED_baseline_carries_the_failing_ids_and_the_count_line(
        self,
    ) -> None:
        """E-07 case (a), the producer half: real ids parsed from real (stubbed) suite output."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_fake_suite(root, stdout=_SUITE_OUTPUT),
                extract_failures=OC.extract_suite_failures,
                parse_summary=OC.parse_suite_summary,
            )
            self.assertIsNone(absent)
            assert run is not None
            result = run.collect(wait_seconds=30.0)
            self.assertEqual(R.SUITE_BASELINE_COMPLETED, result.state)
            self.assertTrue(result.known)
            self.assertIn(
                "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
                result.failures,
            )
            self.assertIn("ERROR tests/test_broken_import.py", result.failures)
            self.assertEqual("1 failed, 4 passed, 1 error in 3.21s", result.summary)
            self.assertEqual(1, result.exit_code)
            R.remove_suite_baseline_checkout(repo, run.checkout)

    def test_a_GREEN_baseline_is_DISTINGUISHABLE_from_an_absent_one(self) -> None:
        """ "Nothing was failing" and "nobody measured" are different facts and must read differently."""

        green = R.SuiteBaseline(
            state=R.SUITE_BASELINE_COMPLETED,
            base_commit="abc123def456",
            failures=(),
            summary="7830 passed in 118.47s",
            exit_code=0,
        )
        absent = R.suite_baseline_absent("the baseline suite never finished")
        self.assertTrue(green.known)
        self.assertFalse(absent.known)
        self.assertIn("NOTHING was failing", R.suite_baseline_context(green))
        self.assertIn("UNKNOWN", R.suite_baseline_context(absent))
        self.assertNotEqual(green.as_record(), absent.as_record())


# ==================================================================================================
# E-02 / V-02 case (d): a crashed turn leaves NO stray worktree
# ==================================================================================================
class CleanupCoversEveryExitPath(unittest.TestCase):
    """E-07 case (d) and F-16. `execute_item_core` had ZERO `finally:` blocks before this plan."""

    FOUR_EXITS = (
        "StopNowForce",
        "StopAtCheckpoint",
        "KeyboardInterrupt",
        "StallTimeout",
    )

    def test_a_try_finally_was_ADDED_and_it_encloses_the_dispatch(self) -> None:
        """ "Tear it down on every path" is not buildable as a trailing call, so structure was added."""

        tree = ast.parse(inspect.getsource(R).replace("\n", "\n", 1))
        core = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "execute_item_core"
        )
        with_final = [
            n for n in ast.walk(core) if isinstance(n, ast.Try) and n.finalbody
        ]
        self.assertTrue(
            with_final,
            "execute_item_core must contain a `finally:`; there were ZERO before this plan, so the "
            "baseline's checkout and child process leaked on all four turn-ending paths",
        )
        cleanup = next(
            n
            for n in with_final
            if "remove_suite_baseline_checkout"
            in ast.unparse(ast.Module(n.finalbody, []))
        )
        body = ast.unparse(ast.Module(cleanup.body, []))
        self.assertIn("spawn_executor(", body)
        for exit_path in self.FOUR_EXITS:
            self.assertIn(
                exit_path,
                body,
                f"the {exit_path} path must be INSIDE the try, or the cleanup does not cover it",
            )

    def test_the_finally_abandons_the_child_AND_removes_the_checkout(self) -> None:
        core = _core_source()
        tail = core[core.rindex("finally:") :]
        self.assertIn("suite_baseline_run.abandon()", tail)
        self.assertIn("remove_suite_baseline_checkout", tail)
        self.assertIn(
            "contextlib.suppress",
            tail,
            "a raising `finally` would REPLACE the exception the turn was carrying, including a "
            "deliberate stop",
        )

    def test_a_CRASHED_turn_leaves_NO_STRAY_WORKTREE(self) -> None:
        """Case (d), performed rather than reasoned about: `git worktree list` before and after."""

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            repo = _throwaway_repo(root)
            before = _git(repo, "worktree", "list").stdout

            run, absent = R.start_suite_baseline(
                repo,
                id6="abc123",
                attempt=1,
                base_commit="HEAD",
                argv=_hanging_suite(root),
                extract_failures=OC.extract_suite_failures,
            )
            self.assertIsNone(absent)
            assert run is not None
            self.assertNotEqual(before, _git(repo, "worktree", "list").stdout)

            # Simulate the crash: the `finally` runs on a turn that never collected.
            try:
                raise KeyboardInterrupt("the operator pressed ctrl-c mid-turn")
            except KeyboardInterrupt:
                run.abandon()
                R.remove_suite_baseline_checkout(repo, run.checkout)

            self.assertEqual(
                before,
                _git(repo, "worktree", "list").stdout,
                "a crashed turn must leave the worktree list EXACTLY as it was",
            )
            self.assertFalse(run.checkout.exists())

    def test_removal_is_IDEMPOTENT_and_never_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = _throwaway_repo(pathlib.Path(temp))
            ghost = R.suite_baseline_checkout_path(repo, "never-existed", 9)
            R.remove_suite_baseline_checkout(repo, ghost)
            R.remove_suite_baseline_checkout(repo, ghost)


# ==================================================================================================
# E-04 / V-04: the prompt carries it as CONTEXT, and absence reads as UNKNOWN
# ==================================================================================================
class ThePromptCarriesTheBaselineAsContext(unittest.TestCase):
    """V-04. E-07 case (a), the consumer half."""

    def test_the_already_failing_set_REACHES_the_prompt(self) -> None:
        prompt = R.gate_answer_question(
            failing="FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
            changed_files=("agent_workflows/term.py",),
            baseline=_completed(),
        )
        self.assertIn("WHAT WAS ALREADY FAILING BEFORE YOUR TURN", prompt)
        self.assertIn("ALREADY FAILING before your work existed", prompt)
        self.assertIn("test_already_red", prompt)
        self.assertIn("0123456789ab", prompt)

    def test_it_is_stated_as_INFORMATION_and_not_as_an_ACCUSATION_or_a_CONSTRAINT(
        self,
    ) -> None:
        prompt = " ".join(
            R.gate_answer_question(failing="x", baseline=_completed()).split()
        )
        self.assertIn(
            "THIS IS INFORMATION TO HELP YOU JUDGE, NOT AN ACCUSATION AND NOT A CONSTRAINT",
            prompt,
        )
        self.assertIn("Nothing checks your answer against this list", prompt)
        self.assertIn(
            "may still genuinely be nothing to do with your work",
            prompt,
            "an agent must not read an unlisted failure as proof of its own fault",
        )

    def test_an_ABSENT_baseline_says_UNKNOWN_and_NEVER_implies_nothing_was_failing(
        self,
    ) -> None:
        """The inversion this must not commit, stated by `daexj1` E-02 for the other side."""

        for baseline in (
            None,
            R.suite_baseline_absent("the checkout could not be created"),
        ):
            with self.subTest(baseline=baseline):
                prompt = R.gate_answer_question(failing="x", baseline=baseline)
                self.assertIn("UNKNOWN", prompt)
                self.assertIn("it means nobody measured", prompt)
                self.assertNotIn("NOTHING was failing", prompt)
                self.assertNotIn("were ALREADY FAILING", prompt)

    def test_the_DEFAULT_is_the_UNKNOWN_wording_not_an_empty_list(self) -> None:
        """Every existing caller that passes no baseline must read as UNKNOWN, not as green."""

        self.assertIsNone(
            inspect.signature(R.gate_answer_question).parameters["baseline"].default
        )
        self.assertIn("UNKNOWN", R.gate_answer_question(failing="x"))

    def test_daexj1s_PROMPT_STRUCTURE_and_THREE_SENTINELS_are_UNCHANGED(self) -> None:
        """This plan adds ONE block of context; it does not own the question or its vocabulary."""

        with_baseline = R.gate_answer_question(failing="x", baseline=_completed())
        for answer in R.GATE_ANSWERS:
            self.assertIn(answer, with_baseline)
        self.assertIn(R.GATE_ANSWER_KEY, with_baseline)
        for anchor in (
            "This is a question, not an accusation",
            "YOUR LANE IS THEN INTEGRATED",
            "THE FILES YOUR TURN CHANGED",
            "CHOOSE THE ANSWER THAT IS TRUE",
        ):
            self.assertIn(anchor, with_baseline)

    def test_the_baseline_BLOCK_IS_THE_ONLY_DIFFERENCE_the_prompt_gains(self) -> None:
        """Proven by DIFF: removing the block returns the prompt to its pre-plan text."""

        without = R.gate_answer_question(failing="x", changed_files=("a.py",))
        with_it = R.gate_answer_question(
            failing="x", changed_files=("a.py",), baseline=_completed()
        )
        self.assertEqual(
            without.replace(R.suite_baseline_context(None), "@@"),
            with_it.replace(R.suite_baseline_context(_completed()), "@@"),
            "the ONLY textual difference may be the baseline context block itself",
        )


# ==================================================================================================
# E-05 / V-05: THE LOAD-BEARING PROPERTY. Nothing refuses on the baseline.
# ==================================================================================================
class NothingRefusesOnTheBaseline(unittest.TestCase):
    """V-05 and E-07 case (e). THE load-bearing assertion of this plan.

    The maintainer's binding constraint, ruled 2026-09-08 and reaffirmed 2026-09-20: no programmatic
    check may refuse a verdict on the strength of a baseline. The originally-proposed constraint
    ("refuse `not-mine` for any id absent from the baseline") was rejected in as many words, because
    a gate cannot detect deception, a capable model can make tests pass, a malicious agent would
    rewrite the gate, and the target is SLOPPINESS rather than malice.

    A baseline sitting in a run record LOOKS like something to check, which is exactly why this is
    asserted rather than intended.
    """

    def _perform(
        self, answer: dict[str, Any], baseline: R.SuiteBaseline | None
    ) -> R.GateAnswerOutcome:
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "outcome.json"

            def ask(prompt: str) -> tuple[int, str, pathlib.Path, list[str]]:
                path.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "disposition": "executed",
                            R.GATE_ANSWER_KEY: answer,
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses-1", path, ["stub"]

            return R.perform_gate_answer(
                suite_result=_suite_result(),
                changed_files=("agent_workflows/term.py",),
                ask=ask,
                outcome_path=path,
                session_id="ses-1",
                baseline=baseline,
            )

    def test_a_not_mine_verdict_is_IDENTICAL_with_and_without_the_id_in_the_baseline(
        self,
    ) -> None:
        """THE ASSERTION THIS PLAN EXISTS TO MAKE SAFE.

        The failing id is `test_already_red`. In one run the baseline CONTAINS it (so the claim is
        corroborated); in the other the baseline contains something else entirely (so the claim is
        contradicted by the evidence). EVERY outcome field must be the same, because the agent's
        answer is the authority and the baseline is only information.
        """

        answer = {"answer": "not-mine", "reason": "it fails in a file I never touched"}
        corroborated = self._perform(
            answer,
            _completed(
                (
                    "FAILED tests/test_pre_existing.py::T::test_already_red - assert 1 == 2",
                )
            ),
        )
        contradicted = self._perform(
            answer,
            _completed(("FAILED tests/test_something_else.py::T::test_other",)),
        )
        absent = self._perform(answer, R.suite_baseline_absent("no baseline was taken"))

        self.assertTrue(corroborated.release)
        self.assertTrue(
            contradicted.release,
            "A `not-mine` whose id is ABSENT from the baseline MUST still release. Refusing here is "
            "precisely the constraint the maintainer rejected on 2026-09-08.",
        )
        self.assertTrue(absent.release)
        for field in (
            "answer",
            "reason",
            "usable",
            "integrates",
            "refuses",
            "awaits_human_decision",
            "violation",
            "recheck_attempts",
            "recheck_passed",
            "failing_tests",
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    corroborated.record[field],
                    contradicted.record[field],
                    f"{field} differs when the baseline disagrees with the answer; the baseline must "
                    "change NOTHING but the prompt text and the audit record",
                )
                self.assertEqual(
                    corroborated.record[field], absent.record[field], f"{field} differs"
                )

    def test_the_ONLY_field_that_differs_is_the_RECORDED_baseline_itself(self) -> None:
        """A record is not a check: the audit field may differ, and nothing else may."""

        answer = {"answer": "not-mine", "reason": "unrelated"}
        a = self._perform(answer, _completed())
        b = self._perform(answer, R.suite_baseline_absent("none taken"))
        differing = {k for k in a.record if a.record[k] != b.record.get(k)}
        self.assertEqual(
            {"suite_baseline"},
            differing,
            "exactly one field may differ, and it must be the audit record",
        )

    def test_a_MINE_verdict_is_also_identical_either_way(self) -> None:
        """The property is symmetric: the baseline must not rescue a refusal either."""

        answer = {"answer": "mine", "reason": "I broke it"}
        with_it = self._perform(answer, _completed())
        without = self._perform(answer, None)
        self.assertFalse(with_it.release)
        self.assertFalse(without.release)
        self.assertEqual(with_it.record["answer"], without.record["answer"])

    def test_NO_CODE_PATH_compares_the_baseline_to_the_post_work_SET(self) -> None:
        """The grep V-05 demands, done structurally: `baseline` reaches no decision.

        Asserted by AST over `perform_gate_answer`: the name `baseline` may appear only inside the
        `gate_answer_question(...)` and `gate_answer_record(...)` calls. Any use in a test, a
        comparison or a boolean would be a gate.
        """

        fn = ast.parse(textwrap.dedent(inspect.getsource(R.perform_gate_answer))).body[
            0
        ]
        allowed: set[int] = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name in ("gate_answer_question", "gate_answer_record"):
                    for inner in ast.walk(node):
                        if isinstance(inner, ast.Name) and inner.id == "baseline":
                            allowed.add(id(inner))
        stray = [
            node.lineno
            for node in ast.walk(fn)
            if isinstance(node, ast.Name)
            and node.id == "baseline"
            and id(node) not in allowed
        ]
        self.assertEqual(
            [],
            stray,
            "`baseline` is used outside the question/record calls in perform_gate_answer (lines "
            f"{stray}); that is a GATE, which the maintainer forbade",
        )

    def test_the_baseline_reaches_NO_comparison_in_execute_item_core_either(
        self,
    ) -> None:
        core = _core_source()
        for forbidden in (
            "if suite_baseline.failures",
            "in suite_baseline.failures",
            "suite_baseline.failures ==",
            "suite_baseline.known and",
        ):
            self.assertNotIn(
                forbidden,
                core,
                f"{forbidden!r} would key an outcome on the baseline; nothing may refuse on it",
            )

    def test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning(self) -> None:
        """Without the reasoning the field reads as an unfinished check and the next reader finishes it."""

        src = inspect.getsource(R)
        section = src[
            src.index("# THE PRE-WORK SUITE BASELINE") : src.index(
                "# THE INTEGRATION-REFUSAL ANSWER"
            )
        ]
        self.assertIn(
            "INFORMATION FOR AN HONEST AGENT, NOT A CHECK ON A DISHONEST ONE", section
        )
        self.assertIn("A GATE CANNOT DETECT DECEPTION", section)
        self.assertIn("A CAPABLE MODEL CAN MAKE TESTS PASS", section)
        self.assertIn("WOULD REWRITE THE GATE", section)
        self.assertIn("SLOPPINESS, NOT MALICE", section)


# ==================================================================================================
# E-06 / V-06: persisted on the run record, IDENTICALLY on both hosts
# ==================================================================================================
class TheBaselineIsPersistedIdenticallyOnBothHosts(unittest.TestCase):
    """V-06 and E-07 case (f). An audit's answer must not depend on which runner ran the plan."""

    def test_the_record_carries_ALL_FOUR_FACTS(self) -> None:
        record = _completed().as_record()
        for key in ("base_commit", "failures", "state", "reason"):
            self.assertIn(key, record)
        self.assertEqual("0123456789abcdef", record["base_commit"])
        self.assertEqual(R.SUITE_BASELINE_COMPLETED, record["state"])
        self.assertTrue(record["failures"])

    def test_the_COMMIT_is_present_because_without_it_the_record_means_nothing(
        self,
    ) -> None:
        """A reader who cannot see the commit cannot tell which tree the baseline described."""

        self.assertIn("base_commit", R.suite_baseline_absent("x").as_record())
        self.assertIn("base_commit", _completed().as_record())

    def test_an_ABSENT_record_is_DISTINGUISHABLE_from_a_completed_green_one(
        self,
    ) -> None:
        absent = R.suite_baseline_absent("the suite never finished").as_record()
        green = R.SuiteBaseline(
            state=R.SUITE_BASELINE_COMPLETED, base_commit="abc", failures=()
        ).as_record()
        self.assertEqual([], absent["failures"])
        self.assertEqual([], green["failures"])
        self.assertNotEqual(absent["state"], green["state"])
        self.assertTrue(absent["reason"])
        self.assertFalse(green["reason"])

    def test_the_record_is_JSON_SERIALIZABLE(self) -> None:
        """It is written into `state.json`, so a non-serializable field would kill the turn."""

        json.dumps(_completed().as_record())
        json.dumps(R.suite_baseline_absent("x").as_record())

    def test_BOTH_HOSTS_write_it_at_the_SAME_SEAM(self) -> None:
        """ONE writer, in the shared core both hosts delegate to, beside the post-work result."""

        core = _core_source()
        self.assertIn('attempt["suite_baseline"] = suite_baseline.as_record()', core)
        self.assertLess(
            core.index('attempt["suite_check"]'),
            core.index('attempt["suite_baseline"]'),
            "the baseline must be recorded BESIDE the existing per-attempt suite result",
        )
        for name, module in HOSTS:
            with self.subTest(host=name):
                src = pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")
                self.assertIn("execute_item_core", src)
                self.assertNotIn(
                    'attempt["suite_baseline"]',
                    src,
                    f"{name} must NOT write its own copy; a second writer is how the two hosts "
                    "persist different shapes",
                )

    def test_BOTH_HOSTS_expose_the_SAME_injected_objects(self) -> None:
        """A name missing from one host would silently give that host NO baseline."""

        for name in (
            "SUITE_CHECK_ARGV",
            "extract_suite_failures",
            "parse_suite_summary",
        ):
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(OC, name), f"oc must expose {name}")
                self.assertTrue(hasattr(AGY, name), f"agy must expose {name}")
                self.assertIs(
                    getattr(OC, name),
                    getattr(AGY, name),
                    f"{name} must be ONE object on both hosts",
                )

    def test_the_gate_answer_record_carries_the_baseline_for_AUDIT(self) -> None:
        record = R.gate_answer_record(
            R.GateAnswerVerdict("not-mine", "unrelated", ""),
            asked=True,
            ask_reason="stub",
            baseline=_completed(),
        )
        self.assertEqual(R.SUITE_BASELINE_COMPLETED, record["suite_baseline"]["state"])
        self.assertEqual("0123456789abcdef", record["suite_baseline"]["base_commit"])

    def test_an_UNSUPPLIED_baseline_records_NOT_STARTED_rather_than_a_green_one(
        self,
    ) -> None:
        record = R.gate_answer_record(
            R.GateAnswerVerdict("mine", "", ""), asked=True, ask_reason="stub"
        )
        self.assertEqual(
            R.SUITE_BASELINE_NOT_STARTED, record["suite_baseline"]["state"]
        )


# ==================================================================================================
# THE BOUNDARIES THIS PLAN MUST NOT CROSS
# ==================================================================================================
class TheBoundariesAreRespected(unittest.TestCase):
    """F-11 and the shared-module rule, asserted so a future edit cannot quietly cross them."""

    def test_NO_SECOND_ID_EXTRACTOR_WAS_WRITTEN(self) -> None:
        """`daexj1`/`h5pyqa` E-01 owns capture-time extraction; forking it would give two answers.

        THE HOME MOVED, THE CLAIM DID NOT (runnerlayer Order 02 `1f7xno`, backlog `cnwy8g`). This
        asserted `agent_workflows.oc_runipd` because that is where the ONE extractor was DEFINED; it is
        now defined in `runner_shared`, which both hosts bind. The property being pinned is
        "exactly one extractor, and every consumer reaches THAT one", and it is unchanged and in fact
        stronger: while the definition sat in a host driver, the other host reached it only by importing
        from a peer driver, which is the coupling `cnwy8g` exists to remove.
        """

        self.assertEqual(
            "agent_workflows.runner_shared", OC.extract_suite_failures.__module__
        )
        # And BOTH hosts must reach that same object, which is the half a `__module__` check cannot
        # make: a host could bind a copy whose `__module__` string is identical.
        self.assertIs(OC.extract_suite_failures, R.extract_suite_failures)
        for symbol in (
            R.SuiteBaselineRun,
            R.start_suite_baseline,
            R.suite_baseline_context,
        ):
            code = _code_only(inspect.getsource(symbol))
            with self.subTest(symbol=getattr(symbol, "__name__", str(symbol))):
                for forbidden in ("re.compile", "FAILED", "short test summary"):
                    self.assertNotIn(
                        forbidden,
                        code,
                        f"{forbidden!r}: the baseline must CONSUME the shared extractor, not parse "
                        "pytest output itself",
                    )

    def test_run_evidence_IS_UNMODIFIED_BY_THIS_PLAN(self) -> None:
        """F-11: `run_evidence.py` is deliberately ABSENT from this plan's Scope-Paths.

        Its absence is the VISIBLE BOUNDARY with `daexj1`/`h5pyqa`, which owns capture-time
        extraction. Asserted by checking the baseline reaches nothing in that module: if a future edit
        needs to touch it, the correct action is to stop and report, not to widen scope quietly.
        """

        for symbol in (R.SuiteBaselineRun, R.start_suite_baseline):
            code = _code_only(inspect.getsource(symbol))
            with self.subTest(symbol=getattr(symbol, "__name__", str(symbol))):
                self.assertNotIn("run_evidence", code)
                self.assertNotIn("capture_command", code)

    def test_runner_shared_STILL_IMPORTS_NO_HOST_DRIVER(self) -> None:
        """The existing anti-divergence rule, re-asserted because this plan adds to that module."""

        tree = ast.parse(pathlib.Path(str(R.__file__)).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("runipd", node.module or "")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("runipd", alias.name)

    def test_the_host_specifics_are_INJECTED_off_driver_module(self) -> None:
        core = _core_source()
        self.assertIn('getattr(driver_module, "extract_suite_failures", None)', core)
        self.assertIn('getattr(driver_module, "SUITE_CHECK_ARGV", None)', core)

    def test_the_shared_module_is_IMPORTABLE_STANDALONE(self) -> None:
        """No cycle: a fresh interpreter must import it without a runner."""

        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import agent_workflows.runner_shared as m; print(m.SUITE_BASELINE_SUBDIR)",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn(".aw/state/suite-baselines", proc.stdout)

    def test_the_baseline_root_is_GITIGNORED_RUNTIME_SCRATCH(self) -> None:
        """A baseline checkout must never be committable; it lives under the gitignored state root."""

        self.assertTrue(R.SUITE_BASELINE_SUBDIR.startswith(".aw/state/"))

    def test_run_suite_checks_PRIMARY_CHECKOUT_CONTRACT_is_UNCHANGED(self) -> None:
        """Explicitly out of scope: the post-work check still insists on the primary checkout."""

        doc = inspect.getdoc(OC.run_suite_check) or ""
        self.assertIn("PRIMARY CHECKOUT", doc)
        self.assertIn("Callers MUST pass the primary repo", doc)


if __name__ == "__main__":
    unittest.main()
