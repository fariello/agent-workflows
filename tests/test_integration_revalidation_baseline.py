#!/usr/bin/env python3
"""revalbase 01 (`tgyfs2`): the post-merge revalidation verdict is RELATIVE to the measured baseline.

WHAT THIS FILE OWNS, and the division of labour that keeps it from duplicating a sibling.
`tests/test_suite_adjudication.py` owns the exit-code-is-the-authority contract for
`integration_is_earned`, the PRE-merge trust signal, and its
`TheExitCodeIsTheAuthorityAndNotTheList` class is the canonical statement of that principle. THIS
file owns the same principle for the POST-merge revalidation gate
(`runner_shared.make_integration_validation_runner`) and for the comparison it now performs. The
cases are deliberately NOT copied across: one behavior, one file to update.

THE DEFECT, MEASURED RATHER THAN REASONED (run `run-20260922T024054Z-2245533`). The gate asked an
ABSOLUTE question ("is the merged tree green?") when the only sound question is a RELATIVE one ("did
this lane introduce a failure that was not already there?"). Items `ld8lb3` and `65cuw0` both ended
`merge-refused` for `integration_failed_combined_red`, and in BOTH the post-merge failing SET was
exactly the one id their own `attempt["suite_baseline"]` already recorded as failing before the work
existed (`FAILED tests/test_defect_report.py::ValidatorTests::
test_no_bare_except_was_introduced_around_the_new_code`), with the passing count risen by exactly the
tests each lane adds: baseline `1 failed, 8042 passed` against post-merge `1 failed, 8064 passed` for
`ld8lb3`, and `1 failed, 8063 passed` against `1 failed, 8084 passed` for `65cuw0`. Two verified
lanes were stranded across an 8.5-hour unattended run, three further items cascaded to
`dependency-blocked`, and a human re-merged them by hand where the combined suite passed on the first
attempt.

THIS CHANGE MAKES A SAFETY GATE MORE PERMISSIVE, WHICH IS WHY THE ANTI-FAIL-OPEN CONTROLS OUTNUMBER
THE VERDICT CASES HERE. The subtraction it performs is the comparison that already inverted this
repository's integration gate once: plan `32ij2j` compared failing SETS as a subset and derived them
from an always-empty string, so every lane passed INCLUDING one that broke everything. Four hazards
are therefore pinned, each shown FAILING when it is forced:

  1. An ABSENT baseline read as an empty failing set (which would mean "nothing was failing").
  2. THE `32ij2j` INVERSION: a NON-PASSING suite whose merged failing list is EMPTY. The single most
     important case in this file.
  3. THE TRUNCATION CASE: either list at the 40-id `SUITE_FAILURE_LINE_LIMIT` cap, where the
     extractor's first-seen order plus `-n auto --dist=worksteal` and random ordering let two runs of
     one red tree keep DIFFERENT subsets.
  4. THE CACHE CASE: a verdict cached for one baseline served to an item whose baseline differs.

AND THE FIVE PATHS THAT MUST NOT MOVE are pinned with their `measured` flags, because the risk of this
change is what it touches by accident: `validate=True` skips, no `suite_check` refuses, an
unresolvable base/head refuses, an unmaterializable merge refuses, a suite exception refuses. The
`measured` flag is asserted alongside each boolean so a path cannot be silently reclassified from
harness-fault to code-red, which is the distinction `l2mzxn` added after a near-identical incident.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent_workflows import oc_runipd as OC  # noqa: E402
from agent_workflows import runner_shared as R  # noqa: E402

#: The REAL failing id from the measured incident, used verbatim so the replay cases are a replay and
#: not a paraphrase.
MEASURED_BASELINE_FAILURE = (
    "FAILED tests/test_defect_report.py::ValidatorTests::"
    "test_no_bare_except_was_introduced_around_the_new_code"
)

#: The two REAL base commits from run `run-20260922T024054Z-2245533`. They DIFFER, which is the fact
#: that makes the tree-keyed cache a correctness trap once the verdict is baseline-relative.
LD8LB3_BASE = "301a1d8fbc15"
CU_BASE = "ee20e831f5f1"


def _suite_result(
    *,
    passing: bool = False,
    exit_code: int = 1,
    summary: str = "1 failed, 8064 passed, 3 skipped, 2 xfailed",
    reason: str = "the driver-run suite did not pass",
    failures: tuple[str, ...] = (MEASURED_BASELINE_FAILURE,),
) -> Any:
    """A `SuiteCheckResult`, built through the SHIPPED type so a field rename fails here."""

    return OC.SuiteCheckResult(
        passing=passing,
        exit_code=exit_code,
        summary=summary,
        reason=reason,
        cwd=".",
        timeout_seconds=600.0,
        elapsed_seconds=1.0,
        failures=failures,
    )


def _completed_baseline(
    failures: tuple[str, ...] = (MEASURED_BASELINE_FAILURE,),
    *,
    base_commit: str = LD8LB3_BASE,
    summary: str = "1 failed, 8042 passed, 3 skipped, 2 xfailed",
) -> R.SuiteBaseline:
    return R.SuiteBaseline(
        state=R.SUITE_BASELINE_COMPLETED,
        base_commit=base_commit,
        failures=failures,
        reason="",
        summary=summary,
        exit_code=1,
    )


def _item_with_baseline(
    base: str,
    branch: str,
    baseline: R.SuiteBaseline | None,
    *,
    id6: str = "ld8lb3",
    extra_attempts: int = 0,
) -> dict[str, Any]:
    """An item in the shape a LIVE run presents: the lane on the attempt, the baseline beside it.

    `extra_attempts` prepends EARLIER attempts carrying a deliberately WRONG baseline, so a reader of
    `attempts[0]` instead of `attempts[-1]` is caught.
    """

    attempts: list[dict[str, Any]] = []
    for index in range(extra_attempts):
        attempts.append(
            {
                "worktree_base": base,
                "worktree_branch": branch,
                "suite_baseline": R.SuiteBaseline(
                    state=R.SUITE_BASELINE_COMPLETED,
                    base_commit=f"stale{index}",
                    failures=("FAILED tests/test_stale.py::T::test_stale",),
                ).as_record(),
            }
        )
    current: dict[str, Any] = {"worktree_base": base, "worktree_branch": branch}
    if baseline is not None:
        current["suite_baseline"] = baseline.as_record()
    attempts.append(current)
    return {"id6": id6, "attempts": attempts}


def _revalidation(item: dict[str, Any]) -> dict[str, Any]:
    record = item.get("post_merge_revalidation")
    assert isinstance(record, dict), "the runner must record what it did"
    return record


def _repo_with_a_lane(root: pathlib.Path) -> tuple[pathlib.Path, str, str]:
    """A repo whose lane work is NOT in main, returning `(repo, base_commit, branch)`."""

    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    def git(*args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
        assert proc.returncode == 0, f"{args}: {proc.stderr}"
        return proc.stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    (repo / "base_file.py").write_text("BASE = 1\n", encoding="utf-8")
    git("add", "base_file.py")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    git("checkout", "-q", "-b", "aw/lane/ld8lb3")
    (repo / "lane_work.py").write_text("LANE = 2\n", encoding="utf-8")
    git("add", "lane_work.py")
    git("commit", "-qm", "the lane's work")
    git("checkout", "-q", "main")
    return repo, base, "aw/lane/ld8lb3"


# ==================================================================================================
# E-01 / V-01: the pure predicate, including the three ways the subtraction would lie
# ==================================================================================================
class TheComparisonIsRelativeAndRefusesToBeTheAuthority(unittest.TestCase):
    """E-01/E-02. The predicate answers "what is NEW", and says `unknown` when it cannot."""

    def test_the_MEASURED_no_regression_case_answers_no_regression(self) -> None:
        """`ld8lb3`'s real inputs: the failing SET is unchanged, so nothing was introduced."""

        verdict = R.new_failures_since_baseline(
            (MEASURED_BASELINE_FAILURE,), _completed_baseline(), suite_passed=False
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_NO_REGRESSION)
        self.assertEqual(verdict.new_ids, ())
        self.assertTrue(verdict.introduced_nothing)
        self.assertIn(LD8LB3_BASE, verdict.reason)

    def test_ONE_added_id_regresses_and_names_ONLY_that_id(self) -> None:
        """A refusal must be SPECIFIC: the list narrows the message, it does not decide the verdict."""

        added = "FAILED tests/test_new.py::T::test_broken_by_this_lane"
        verdict = R.new_failures_since_baseline(
            (MEASURED_BASELINE_FAILURE, added),
            _completed_baseline(),
            suite_passed=False,
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_REGRESSED)
        self.assertEqual(
            verdict.new_ids, ("FAILED tests/test_new.py::T::test_broken_by_this_lane",)
        )
        self.assertFalse(verdict.introduced_nothing)
        self.assertIn("test_broken_by_this_lane", verdict.reason)
        self.assertNotIn("test_no_bare_except", verdict.reason)

    def test_ANTI_FAIL_OPEN_1_an_ABSENT_baseline_is_UNKNOWN_and_never_an_empty_set(
        self,
    ) -> None:
        """CONTROL 1. "Nobody measured" must never read as "nothing was failing".

        This is the inversion `SuiteBaseline.failures`' own docstring and `suite_baseline_context`
        both exist to prevent, restated for this comparison. If it ever answers `no-regression`, every
        item WITHOUT a baseline integrates on a red tree, which is strictly worse than the defect this
        plan removes.
        """

        for baseline in (
            None,
            R.suite_baseline_absent(
                "the baseline suite had not finished when the turn ended"
            ),
            R.SuiteBaseline(state=R.SUITE_BASELINE_NOT_STARTED, base_commit=""),
        ):
            with self.subTest(baseline=baseline):
                verdict = R.new_failures_since_baseline(
                    (MEASURED_BASELINE_FAILURE,), baseline, suite_passed=False
                )
                self.assertEqual(
                    verdict.judgement,
                    R.REVALIDATION_UNKNOWN,
                    "an unmeasured baseline must be UNKNOWN; reading its empty tuple as 'nothing "
                    "was failing' integrates every red tree nobody measured",
                )
                self.assertFalse(verdict.introduced_nothing)

    def test_ANTI_FAIL_OPEN_2_THE_32ij2j_INVERSION_an_empty_list_on_a_RED_suite(
        self,
    ) -> None:
        """CONTROL 2, AND THE SINGLE MOST IMPORTANT CASE IN THIS FILE.

        `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` records what
        happens when this is wrong: plan `32ij2j` compared failing sets as a subset and derived them
        from an ALWAYS-EMPTY string (the shipped `h5pyqa` defect, where `SuiteCheckResult.summary` was
        always `""`), so the empty set was a subset of everything and every lane passed INCLUDING one
        that broke the whole suite.

        Reached here unchanged, `merged - baseline` over an empty merged list is EMPTY, a naive
        predicate answers `no-regression`, and a tree that broke everything integrates. So an empty
        merged list on a NON-PASSING suite is UNKNOWN, forever.
        """

        verdict = R.new_failures_since_baseline(
            (), _completed_baseline(), suite_passed=False
        )
        self.assertEqual(
            verdict.judgement,
            R.REVALIDATION_UNKNOWN,
            "a RED suite reporting NO ids must be UNKNOWN, never 'no regression'; this is the exact "
            "inversion that sank plan 32ij2j and would integrate a lane that broke everything",
        )
        self.assertFalse(verdict.introduced_nothing)
        self.assertIn("32ij2j", verdict.reason)

    def test_a_GREEN_suite_with_an_empty_list_is_NOT_the_inversion_case(self) -> None:
        """The complement, so control 2 is a DISCRIMINATION and not a blanket refusal.

        A green suite legitimately reports no failing ids. Refusing that too would make the predicate
        useless rather than safe, and the EXIT CODE is what tells the two apart - which is the same
        ordering `integration_is_earned` uses.
        """

        verdict = R.new_failures_since_baseline(
            (), _completed_baseline(), suite_passed=True
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_NO_REGRESSION)

    def test_ANTI_FAIL_OPEN_3_either_list_at_the_TRUNCATION_CAP_is_UNKNOWN(
        self,
    ) -> None:
        """CONTROL 3. A truncated list is not a set you may subtract.

        `oc_runipd.extract_suite_failures` stops at `SUITE_FAILURE_LINE_LIMIT` (40) in FIRST-SEEN
        order, while this repository's `addopts` carry `-n auto --dist=worksteal` plus random
        ordering, so two runs of the SAME red tree can retain DIFFERENT 40-line subsets. MEASURED at
        review: 60 identical pre-existing failures reported in reverse order yield 20 FALSELY NEW ids.
        """

        cap = R.SUITE_FAILURE_LIST_CAP
        sixty = tuple(f"FAILED tests/test_many.py::T::test_{i:03d}" for i in range(60))
        # What the extractor would ACTUALLY have kept on each side: the first 40 seen, in the order
        # each run happened to see them. The second run reports in reverse.
        baseline_kept = sixty[:cap]
        merged_kept = tuple(reversed(sixty))[:cap]

        naive_new = [i for i in merged_kept if i not in set(baseline_kept)]
        self.assertEqual(
            len(naive_new),
            20,
            "the fixture must reproduce the measured hazard: a naive subtraction of two truncated "
            "lists of the SAME 60 failures fabricates 20 regressions",
        )

        verdict = R.new_failures_since_baseline(
            merged_kept,
            _completed_baseline(failures=baseline_kept),
            suite_passed=False,
        )
        self.assertEqual(
            verdict.judgement,
            R.REVALIDATION_UNKNOWN,
            "with either list at the cap the subtraction is unsound and must refuse to judge; "
            "otherwise it fabricates 20 regressions from a tree that regressed nothing",
        )
        self.assertNotEqual(verdict.judgement, R.REVALIDATION_REGRESSED)
        self.assertIn(str(cap), verdict.reason)

    def test_the_cap_is_detected_by_LENGTH_on_EITHER_side(self) -> None:
        """Both sides, because a truncated BASELINE lies in the opposite direction (false pass)."""

        cap = R.SUITE_FAILURE_LIST_CAP
        many = tuple(f"FAILED tests/test_many.py::T::test_{i:03d}" for i in range(cap))
        self.assertEqual(
            R.new_failures_since_baseline(
                many,
                _completed_baseline(failures=(MEASURED_BASELINE_FAILURE,)),
                suite_passed=False,
            ).judgement,
            R.REVALIDATION_UNKNOWN,
        )
        self.assertEqual(
            R.new_failures_since_baseline(
                (MEASURED_BASELINE_FAILURE,),
                _completed_baseline(failures=many),
                suite_passed=False,
            ).judgement,
            R.REVALIDATION_UNKNOWN,
        )
        # And one BELOW the cap on both sides still judges, so the guard is a cap check and not an
        # excuse to never compare.
        under = many[: cap - 1]
        self.assertEqual(
            R.new_failures_since_baseline(
                under, _completed_baseline(failures=under), suite_passed=False
            ).judgement,
            R.REVALIDATION_NO_REGRESSION,
        )

    def test_the_cap_CONSTANT_matches_the_extractor_it_describes(self) -> None:
        """A drift between the two makes the cap check silently miss.

        `runner_shared` may not import a driver (`NoRunnerImportTests` AST-walks it), so the value is
        duplicated rather than imported - which is exactly why it must be pinned equal here.
        """

        self.assertEqual(R.SUITE_FAILURE_LIST_CAP, OC.SUITE_FAILURE_LINE_LIMIT)

    def test_the_predicate_is_PURE(self) -> None:
        """No I/O, no git, no suite: it must be safe to call anywhere, including inside a `finally`."""

        import ast
        import inspect
        import textwrap

        fn = ast.parse(
            textwrap.dedent(inspect.getsource(R.new_failures_since_baseline))
        )
        called = {
            ast.unparse(node.func)
            for node in ast.walk(fn)
            if isinstance(node, ast.Call)
        }
        for forbidden in ("_run_git", "subprocess.run", "open", "Path"):
            self.assertNotIn(forbidden, called)


# ==================================================================================================
# E-02 / V-02: the normalization, which must never collapse two DIFFERENT failures into one
# ==================================================================================================
class TheNormalizationCannotCollapseTwoDifferentFailures(unittest.TestCase):
    """E-02. Every choice here is a chance to make two failures look like one, which reads as a pass."""

    def test_the_SAME_node_id_with_DIFFERENT_trailing_text_compares_EQUAL(self) -> None:
        """The reason raw-string comparison is insufficient: pytest's trailing message varies."""

        first = R.normalize_failure_id("FAILED tests/t.py::C::test_x - assert 1 == 2")
        second = R.normalize_failure_id(
            "FAILED tests/t.py::C::test_x - ValueError: a totally different message"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, "FAILED tests/t.py::C::test_x")

    def test_two_DIFFERENT_node_ids_compare_UNEQUAL(self) -> None:
        self.assertNotEqual(
            R.normalize_failure_id("FAILED tests/t.py::C::test_x"),
            R.normalize_failure_id("FAILED tests/t.py::C::test_y"),
        )

    def test_FAILED_and_ERROR_for_the_SAME_node_compare_UNEQUAL(self) -> None:
        """A test that now ERRORS where it previously FAILED has changed behavior."""

        self.assertNotEqual(
            R.normalize_failure_id("FAILED tests/t.py::C::test_x"),
            R.normalize_failure_id("ERROR tests/t.py::C::test_x"),
        )

    def test_a_PARAMETRIZATION_suffix_is_NOT_normalized_away(self) -> None:
        self.assertNotEqual(
            R.normalize_failure_id("FAILED tests/t.py::test_x[a]"),
            R.normalize_failure_id("FAILED tests/t.py::test_x[b]"),
        )

    def test_an_UNPARSEABLE_line_is_ALWAYS_NEW_and_never_DROPPED(self) -> None:
        """Dropping it would let a failure vanish from the difference: a silent fail-open."""

        self.assertEqual(
            R.normalize_failure_id("something that is not a pytest failure line"),
            R.UNPARSEABLE_FAILURE_ID,
        )
        verdict = R.new_failures_since_baseline(
            (MEASURED_BASELINE_FAILURE, "garbage that did not parse"),
            _completed_baseline(),
            suite_passed=False,
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_REGRESSED)
        self.assertIn(R.UNPARSEABLE_FAILURE_ID, verdict.new_ids)

    def test_an_ERROR_line_with_no_node_id_still_parses_to_its_path(self) -> None:
        """A collection error reports `ERROR <path>` with no `::`, and that is a real observation."""

        self.assertEqual(
            R.normalize_failure_id("ERROR tests/test_broken.py"),
            "ERROR tests/test_broken.py",
        )


# ==================================================================================================
# E-03 / V-03: the wiring, applied at EXACTLY ONE return path
# ==================================================================================================
class TheGateConsumesTheComparisonAtExactlyOneReturnPath(unittest.TestCase):
    """E-03. The REAL factory, driven end to end. Not a reimplementation of its logic."""

    def _state(self, repo: pathlib.Path) -> dict[str, Any]:
        return {"repo": str(repo), "run_id": "r", "options": {"validate": False}}

    def test_a_MEASURED_RED_that_introduces_NOTHING_now_PASSES(self) -> None:
        """THE FIX. `ld8lb3`'s recorded inputs replayed through the real factory."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            verdict = R.make_integration_validation_runner(
                self._state(repo),
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("a diff", ("lane_work.py",))

            self.assertTrue(
                verdict,
                "a measured red whose failing SET is identical to the pre-work baseline introduced "
                "nothing; refusing it is the defect that stranded two verified lanes",
            )
            record = _revalidation(item)
            self.assertTrue(record["passed"])
            self.assertTrue(
                record["measured"], "this WAS a measurement and must say so"
            )
            self.assertIn(
                LD8LB3_BASE,
                record["reason"],
                "the reason must name the baseline commit the verdict was relative to",
            )

    def test_ONE_extra_failing_id_still_REFUSES(self) -> None:
        """The same inputs plus one synthetic new id. The gate must still be able to say no."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            verdict = R.make_integration_validation_runner(
                self._state(repo),
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False,
                    exit_code=1,
                    failures=(
                        MEASURED_BASELINE_FAILURE,
                        "FAILED tests/test_new.py::T::test_introduced_here",
                    ),
                ),
            )("a diff", ("lane_work.py",))

            self.assertFalse(verdict)
            record = _revalidation(item)
            self.assertFalse(record["passed"])
            self.assertTrue(record["measured"])
            self.assertIn("test_introduced_here", record["reason"])
            self.assertEqual(
                record["baseline_comparison"]["new_ids"],
                ["FAILED tests/test_new.py::T::test_introduced_here"],
            )

    def test_the_baseline_is_read_from_the_LAST_attempt_not_the_FIRST(self) -> None:
        """`execute_item_core` writes a baseline per ATTEMPT, so `attempts[0]` is a stale measurement."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            # Two earlier attempts carry a WRONG baseline naming a different failure entirely.
            item = _item_with_baseline(
                base, branch, _completed_baseline(), extra_attempts=2
            )
            verdict = R.make_integration_validation_runner(
                self._state(repo),
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("a diff", ("lane_work.py",))
            self.assertTrue(
                verdict,
                "reading attempts[0] would compare against a stale baseline and refuse a lane that "
                "introduced nothing",
            )
            self.assertIn(LD8LB3_BASE, _revalidation(item)["reason"])

    def test_an_item_with_NO_attempts_or_NO_baseline_key_REFUSES(self) -> None:
        """Both absences are UNKNOWN, which keeps the change a pure NARROWING of today's refusals."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            shapes: tuple[dict[str, Any], ...] = (
                # No baseline key on the attempt: exactly the shape every EXISTING fixture presents.
                _item_with_baseline(base, branch, None),
                # No attempts at all; the lane resolves from the preserved fields.
                {
                    "id6": "nobase",
                    "preserved_base": base,
                    "preserved_branch": branch,
                },
                # An ABSENT baseline record.
                _item_with_baseline(
                    base, branch, R.suite_baseline_absent("the baseline never finished")
                ),
            )
            for index, item in enumerate(shapes):
                with self.subTest(shape=index):
                    verdict = R.make_integration_validation_runner(
                        self._state(repo),
                        run_dir,
                        dict(item),
                        suite_check=lambda *_a: _suite_result(
                            passing=False,
                            exit_code=1,
                            failures=(MEASURED_BASELINE_FAILURE,),
                        ),
                    )("a diff", ("lane_work.py",))
                    self.assertFalse(
                        verdict,
                        "with no usable baseline the gate must behave exactly as it did before this "
                        "change: refuse",
                    )

    def test_ANTI_FAIL_OPEN_2_THROUGH_THE_REAL_GATE_a_red_tree_with_NO_ids_refuses(
        self,
    ) -> None:
        """CONTROL 2 at the gate, not only at the predicate. The `32ij2j` shape end to end."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            verdict = R.make_integration_validation_runner(
                self._state(repo),
                run_dir,
                item,
                # Exit 1 with NO parsed ids: precisely the shipped `h5pyqa` shape.
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, summary="", failures=()
                ),
            )("a diff", ("lane_work.py",))
            self.assertFalse(
                verdict,
                "a red tree reporting no ids must REFUSE; passing it is how plan 32ij2j would have "
                "integrated a lane that broke everything",
            )
            self.assertEqual(
                _revalidation(item)["baseline_comparison"]["judgement"],
                R.REVALIDATION_UNKNOWN,
            )

    def test_ANTI_FAIL_OPEN_4_a_verdict_cached_for_ONE_baseline_is_not_served_to_ANOTHER(
        self,
    ) -> None:
        """CONTROL 4. The cache is keyed on the merged TREE; the verdict is per-item RELATIVE.

        MEASURED in run `run-20260922T024054Z-2245533`: `ld8lb3`'s baseline is pinned to
        `301a1d8fbc15` and `65cuw0`'s to `ee20e831f5f1`. Two items in ONE run with DIFFERENT
        baselines is therefore not hypothetical, and serving one's relative verdict to the other is a
        wrong answer in whichever direction they differ.

        OQ-03 was resolved to (b): cache the MEASUREMENT and recompute the JUDGEMENT per item. So the
        suite must still run ONCE (the property the cache exists for) while the two items reach
        DIFFERENT verdicts.
        """

        calls: list[str] = []

        def _counting(path, _run_id):
            calls.append(str(path))
            return _suite_result(
                passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
            )

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            state = self._state(repo)

            # Item ONE's baseline CONTAINS the failing id, so it introduced nothing.
            first = _item_with_baseline(
                base, branch, _completed_baseline(), id6="ld8lb3"
            )
            # Item TWO reaches the SAME merge result but its baseline is a DIFFERENT commit and does
            # NOT contain that id, so for IT the failure is new.
            second = _item_with_baseline(
                base,
                branch,
                _completed_baseline(
                    failures=("FAILED tests/test_other.py::T::test_something_else",),
                    base_commit=CU_BASE,
                ),
                id6="65cuw0",
            )

            first_verdict = R.make_integration_validation_runner(
                state, run_dir, first, suite_check=_counting
            )("d", ("lane_work.py",))
            second_verdict = R.make_integration_validation_runner(
                state, run_dir, second, suite_check=_counting
            )("d", ("lane_work.py",))

            self.assertEqual(
                len(calls),
                1,
                "the cache must still measure one merge result ONCE; re-running a ~107s suite for a "
                "comparison that needs none defeats the property the cache exists for",
            )
            self.assertTrue(
                first_verdict, "for ld8lb3's baseline the failure is pre-existing"
            )
            self.assertFalse(
                second_verdict,
                "for 65cuw0's DIFFERENT baseline the same failure is NEW; serving the cached verdict "
                "wholesale would integrate a lane nothing cleared",
            )
            self.assertTrue(
                _revalidation(second)["cached"], "it must still be a cache HIT"
            )
            self.assertEqual(
                _revalidation(second)["baseline_comparison"]["judgement"],
                R.REVALIDATION_REGRESSED,
            )

    def test_the_exit_5_path_returns_True_WITHOUT_reaching_the_comparison(self) -> None:
        """A tree that collected NOTHING has no failing set, so the comparison must not see it.

        Feeding its empty list to the predicate would be read as the `32ij2j` shape and answered
        `unknown`, converting a deliberate pass back into a refusal.
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            self.assertTrue(
                R.make_integration_validation_runner(
                    self._state(repo),
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(
                        passing=False,
                        exit_code=5,
                        summary="",
                        reason="no tests ran",
                        failures=(),
                    ),
                )("d", ()),
            )
            record = _revalidation(item)
            self.assertIn("collected NO tests", record["reason"])
            self.assertNotIn(
                "baseline_comparison",
                record,
                "no comparison was made, and the record must not imply one was",
            )

    def test_a_GREEN_merged_tree_passes_with_NO_comparison_made(self) -> None:
        """There is nothing to attribute, so the added machinery must stay out of the way."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            self.assertTrue(
                R.make_integration_validation_runner(
                    self._state(repo),
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(
                        passing=True, exit_code=0, summary="8064 passed", failures=()
                    ),
                )("d", ("lane_work.py",))
            )
            self.assertNotIn("baseline_comparison", _revalidation(item))


class TheFiveFailClosedPathsAreUNCHANGED(unittest.TestCase):
    """The risk of this change is what it touches by accident, so each path is pinned with its flag.

    `measured` is asserted alongside every boolean because that flag decides the refusal KIND
    (`revalidation_was_unmeasured` -> `merge-unchecked` versus `merge-refused`), and silently
    reclassifying a harness fault as a code red restores the `l2mzxn` defect that stranded three
    verified lanes.
    """

    def test_VALIDATE_ON_still_skips_and_runs_NO_suite(self) -> None:
        ran: list[str] = []

        def _should_not_run(path, _run_id):
            ran.append(str(path))
            return _suite_result(passing=False, exit_code=1)

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            self.assertTrue(
                R.make_integration_validation_runner(
                    {"repo": str(repo), "run_id": "r", "options": {"validate": True}},
                    run_dir,
                    item,
                    suite_check=_should_not_run,
                )("d", ("lane_work.py",))
            )
            record = _revalidation(item)
            self.assertTrue(record["skipped"])
            self.assertEqual(ran, [], "the verifier mode must not gain a second gate")
            self.assertNotIn("baseline_comparison", record)

    def test_NO_suite_check_still_refuses_as_UNMEASURED(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, Any] = {"id6": "xx1111"}
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"options": {"validate": False}}, run_dir, item
                )("d", ())
            )
            record = _revalidation(item)
            self.assertIs(record["measured"], False)
            self.assertTrue(R.revalidation_was_unmeasured(item))

    def test_an_UNRESOLVABLE_base_or_head_still_refuses_as_UNMEASURED(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, Any] = {
                "id6": "xx1111",
                "preserved_base": "",
                "preserved_branch": "",
            }
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"repo": str(root), "options": {"validate": False}},
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(passing=True, exit_code=0),
                )("d", ())
            )
            record = _revalidation(item)
            self.assertIn("could not be resolved", record["reason"])
            self.assertIs(record["measured"], False)

    def test_an_UNMATERIALIZABLE_merge_still_refuses_as_UNMEASURED(self) -> None:
        """A CONFLICTING merge: `merge-tree` refuses, so there is no tree to test."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = root / "repo"
            repo.mkdir()

            def git(*args: str) -> str:
                proc = subprocess.run(
                    ["git", *args], cwd=repo, capture_output=True, text=True
                )
                return proc.stdout.strip()

            git("init", "-q", "-b", "main")
            git("config", "user.email", "t@example.invalid")
            git("config", "user.name", "t")
            (repo / "c.py").write_text("ORIGINAL\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "base")
            git("checkout", "-q", "-b", "lane")
            (repo / "c.py").write_text("LANE\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "lane")
            git("checkout", "-q", "main")
            (repo / "c.py").write_text("MAIN\n", encoding="utf-8")
            git("add", "c.py")
            git("commit", "-qm", "main diverges")
            main_head = git("rev-parse", "HEAD")

            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(main_head, "lane", _completed_baseline())
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(passing=True, exit_code=0),
                )("d", ())
            )
            record = _revalidation(item)
            self.assertIs(record["measured"], False)
            self.assertIn("fail-closed", record["reason"])

    def test_a_suite_EXCEPTION_still_refuses_as_UNMEASURED(self) -> None:
        """A baseline comparison against a measurement that never happened is meaningless."""

        def _explodes(*_a):
            raise RuntimeError("the suite process died")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                    run_dir,
                    item,
                    suite_check=_explodes,
                )("d", ())
            )
            record = _revalidation(item)
            self.assertIn("errored", record["reason"])
            self.assertIs(record["measured"], False)
            self.assertNotIn(
                "baseline_comparison",
                record,
                "nothing was measured, so nothing may be compared",
            )


# ==================================================================================================
# E-04 / V-04: the record carries the comparison, ADDITIVELY
# ==================================================================================================
class TheRecordLetsAnAuditorSeeTheComparison(unittest.TestCase):
    """E-04. A relative verdict an auditor must INFER is a refusal an operator cannot explain."""

    def test_every_PRE_EXISTING_key_survives_with_its_meaning(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            R.make_integration_validation_runner(
                {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("d", ("lane_work.py",))
            record = _revalidation(item)
            for key in (
                "passed",
                "reason",
                "failures",
                "measured",
                "skipped",
                "cached",
                "tree",
                "merged_files",
            ):
                self.assertIn(key, record, f"{key} is read by existing consumers")
            self.assertEqual(record["failures"], [MEASURED_BASELINE_FAILURE])
            self.assertEqual(record["merged_files"], ["lane_work.py"])
            self.assertTrue(record["tree"])

    def test_the_comparison_block_carries_the_FOUR_facts_an_audit_needs(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            R.make_integration_validation_runner(
                {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("d", ("lane_work.py",))
            block = _revalidation(item)["baseline_comparison"]
            self.assertEqual(block["judgement"], R.REVALIDATION_NO_REGRESSION)
            self.assertEqual(block["new_ids"], [])
            self.assertEqual(
                block["baseline_ids"],
                [R.normalize_failure_id(MEASURED_BASELINE_FAILURE)],
            )
            self.assertEqual(
                block["merged_ids"],
                [R.normalize_failure_id(MEASURED_BASELINE_FAILURE)],
            )
            self.assertTrue(block["reason"])

    def test_the_record_stays_JSON_SERIALIZABLE(self) -> None:
        """It is written into `state.json`, so a tuple or a NamedTuple leaking in would break a run."""

        import json

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            R.make_integration_validation_runner(
                {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("d", ("lane_work.py",))
            round_tripped = json.loads(json.dumps(_revalidation(item)))
            self.assertEqual(
                round_tripped["baseline_comparison"]["judgement"],
                R.REVALIDATION_NO_REGRESSION,
            )


class TheRefusalVOCABULARYGainsNoThirdKind(unittest.TestCase):
    """A no-regression red is a PASS, not a new refusal class (the plan's own scope rule).

    Asserted because the tempting implementation is a third `INTEGRATION_REFUSAL_*` kind, which would
    touch every renderer, attention mapping and analytics key for a case that needs no refusal at all.
    """

    def test_a_passing_relative_verdict_is_not_reclassified_as_a_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            R.make_integration_validation_runner(
                {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False, exit_code=1, failures=(MEASURED_BASELINE_FAILURE,)
                ),
            )("d", ("lane_work.py",))
            self.assertFalse(
                R.revalidation_was_unmeasured(item),
                "a PASSING record is not a refusal of any kind",
            )

    def test_a_REGRESSION_is_still_a_MEASURED_red_and_stays_TERMINAL(self) -> None:
        """A real regression must keep its terminality: repetition cannot fix a broken test."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item_with_baseline(base, branch, _completed_baseline())
            R.make_integration_validation_runner(
                {"repo": str(repo), "run_id": "r", "options": {"validate": False}},
                run_dir,
                item,
                suite_check=lambda *_a: _suite_result(
                    passing=False,
                    exit_code=1,
                    failures=("FAILED tests/test_new.py::T::test_new",),
                ),
            )("d", ("lane_work.py",))
            self.assertFalse(
                R.revalidation_was_unmeasured(item),
                "the suite RAN and the tree is red for a NEW reason; that is a verdict about the "
                "code and must stay terminal rather than becoming a deferrable harness fault",
            )


if __name__ == "__main__":
    unittest.main()
