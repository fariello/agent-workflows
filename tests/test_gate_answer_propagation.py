#!/usr/bin/env python3
"""gateinert 01 (`n9na1c`): a usable `not-mine` gate answer reaches the POST-MERGE gate.

WHAT THIS FILE OWNS, and the division of labour that keeps it from duplicating two siblings.
`tests/test_gate_answer_wiring.py` owns the four-token vocabulary, the validator, the question and
GATE 1 (`integration_is_earned` / `integration.earned`), which the answer already governed.
`tests/test_integration_revalidation_baseline.py` owns the BASELINE arm of the post-merge verdict.
THIS file owns the ANSWER arm of that same verdict and the COMPOSITION of the two. The cases are
deliberately not copied across: one behavior, one file to update.

THE DEFECT, MEASURED RATHER THAN REASONED (item `ld8lb3`, run `run-20260922T024054Z-2245533`). A
lane's suite failure is adjudicated TWICE by two INDEPENDENT gates, and the agent's answer reached
only the first. The agent was asked, answered `not-mine`, and the record shows `answer: not-mine`
with `usable: True`; GATE 1 released exactly as documented (`integration_detail` ends "RELEASED by
the agent's gate answer (not-mine)", `finalized` is True, the plan genuinely reached `executed/` on
lane commit `78891bde`). GATE 2, the post-merge revalidation inside
`runner_shared.make_integration_validation_runner`, then re-ran the suite on the merged tree, saw the
SAME one id the agent had attributed away, consulted NEITHER the answer nor the baseline, and refused.
The item's final status is `merge-refused`. The answer was well-founded: the agent named the
introducing commit `894d7924`, proved the failure at its own base `301a1d8fbc15`, reproduced it with
its own changes stashed out, and filed backlog `p9ag41` rather than fixing another agent's code.

THIS CHANGE WIDENS WHEN AN INTEGRATION IS ALLOWED, WHICH IS THE FAIL-OPEN DIRECTION, so the
anti-fail-open controls outnumber the verdict cases here and are RANKED. THE THREE MOST IMPORTANT
CASES IN THIS FILE, each measured REACHABLE in the authored design rather than hypothesized, and each
therefore given a CONSTRUCTED FIXTURE rather than an assertion about intent:

  1. AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE. This is the `32ij2j` INVERSION, and it is
     the single most important case here. `tests/test_suite_adjudication.py::
     TheExitCodeIsTheAuthorityAndNotTheList` records that plan comparing failing sets as a subset
     over an ALWAYS-EMPTY string (the shipped `h5pyqa` defect) so that "every lane passed including
     one that broke everything". With a merged list of `()` the predicate "every failing id was
     attributed away" is VACUOUSLY TRUE and a tree that broke everything integrates.
  2. EITHER LIST AT THE 40-LINE TRUNCATION CAP. Measured: 45 attributed pre-existing failures plus
     ONE genuine lane regression both truncate at 40, the regression is truncated OUT of the merged
     list, the subtraction finds nothing new, and a lane that INTRODUCED a failure passes. Note the
     sign is OPPOSITE to the sibling baseline plan's, where the same cap causes over-refusal: there
     it is unreliable, here it is a safety hole, because this arm licenses a PASS.
  3. A `fixed` ANSWER. Measured by driving the real `perform_gate_answer`: a `fixed` record carries
     `release: True` AND a NON-EMPTY `failing_tests` set holding its PRE-REPAIR failures, because
     `failing_tests` records what the agent was SHOWN for every answer. An answer-agnostic read would
     clear exactly the ids whose repair did not survive the merge.

FOUR FURTHER CONTROLS complete the seven: `mine` releases nothing, `needs-human` releases nothing, an
UNUSABLE answer releases nothing, and an ABSENT answer leaves today's verdict byte-identical.

AND THE FIVE NON-MEASURED-RED RETURN PATHS ARE PINNED UNCHANGED WITH THEIR FLAGS, because the risk of
this change is what it touches by accident. `_runner` has SIX return paths and only ONE is a measured
red; the `measured` flag decides the refusal KIND (`revalidation_was_unmeasured` -> `merge-unchecked`
versus `merge-refused`), and silently reclassifying a harness fault as a code red restores the
`l2mzxn` defect that stranded three verified lanes.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent_workflows import oc_runipd as OC  # noqa: E402
from agent_workflows import runner_shared as R  # noqa: E402

#: The REAL failing id from the measured incident, used verbatim so the replay is a replay and not a
#: paraphrase. Carried WITH a trailing message, because that is how the extractor produces it and
#: normalizing the message away is what makes the two sides comparable at all.
MEASURED_ATTRIBUTED_FAILURE = (
    "FAILED tests/test_defect_report.py::ValidatorTests::"
    "test_no_bare_except_was_introduced_around_the_new_code - assert False"
)

#: The same id as the post-merge run reported it: SAME node id, DIFFERENT trailing text.
MEASURED_MERGED_FAILURE = (
    "FAILED tests/test_defect_report.py::ValidatorTests::"
    "test_no_bare_except_was_introduced_around_the_new_code - AssertionError: a bare except"
)

#: `ld8lb3`'s REAL base commit, from the measured run.
LD8LB3_BASE = "301a1d8fbc15"

#: An id the agent was never shown and therefore never attributed away.
UNATTRIBUTED = "FAILED tests/test_new.py::T::test_introduced_here"

#: Ids for the four-way composition matrix (E-07).
BASELINE_ONLY = "FAILED tests/test_base.py::T::test_in_baseline_only"
ANSWER_ONLY = "FAILED tests/test_answer.py::T::test_in_attributed_set_only"
IN_BOTH = "FAILED tests/test_both.py::T::test_in_both"
IN_NEITHER = "FAILED tests/test_neither.py::T::test_in_neither"


def _suite_result(
    *,
    passing: bool = False,
    exit_code: int = 1,
    summary: str = "1 failed, 8064 passed, 3 skipped, 2 xfailed",
    reason: str = "the driver-run suite did not pass",
    failures: tuple[str, ...] = (MEASURED_MERGED_FAILURE,),
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


def _real_gate_answer(
    answer: str,
    *,
    failures: tuple[str, ...] = (MEASURED_ATTRIBUTED_FAILURE,),
    rerun_passes: bool = True,
) -> Any:
    """A `GateAnswerOutcome` produced by the REAL `perform_gate_answer`, never hand-rolled.

    THIS IS THE POINT OF THE HELPER. A hand-written record could assert whatever shape this file
    finds convenient, and the `fixed` control specifically depends on a shape that is SURPRISING: a
    GATE-1 RELEASE beside a NON-EMPTY `failing_tests` list of PRE-REPAIR ids. Driving the shipped
    producer is what makes that control a measurement rather than a belief.

    NOTE WHERE THE GATE-1 RELEASE ACTUALLY LIVES, because it is not where a reader expects and this
    file learned it by measuring: `GateAnswerOutcome.release` is the field the integration decision
    reads, while the RECORD's `integrates` is the VERDICT's own field and is False for `fixed` (whose
    release is earned by the observed re-run, not by the claim). The record is what reaches gate 2, so
    the record is what this plan's reader consumes; the outcome is returned here so a control can
    assert the gate-1 release too.
    """

    with tempfile.TemporaryDirectory() as d:
        outcome = pathlib.Path(d) / "outcome.json"
        outcome.write_text(
            json.dumps(
                {R.GATE_ANSWER_KEY: {"answer": answer, "reason": "the agent's reason"}}
            ),
            encoding="utf-8",
        )
        return R.perform_gate_answer(
            suite_result=_suite_result(failures=failures),
            changed_files=("agent_workflows/runner_shared.py",),
            ask=lambda _prompt: None,
            outcome_path=outcome,
            rerun_suite=lambda: _suite_result(
                passing=rerun_passes,
                exit_code=0 if rerun_passes else 1,
                summary="8064 passed" if rerun_passes else "1 failed",
                failures=() if rerun_passes else failures,
            ),
            retry_budget=1,
        )


def _real_answer_record(
    answer: str,
    *,
    failures: tuple[str, ...] = (MEASURED_ATTRIBUTED_FAILURE,),
    rerun_passes: bool = True,
) -> dict[str, Any]:
    """Just the RECORD from :func:`_real_gate_answer`, which is what reaches gate 2."""

    return _real_gate_answer(
        answer, failures=failures, rerun_passes=rerun_passes
    ).record


def _completed_baseline(
    failures: tuple[str, ...] = (),
    *,
    base_commit: str = LD8LB3_BASE,
) -> R.SuiteBaseline:
    return R.SuiteBaseline(
        state=R.SUITE_BASELINE_COMPLETED,
        base_commit=base_commit,
        failures=failures,
        reason="",
        summary="1 failed, 8042 passed, 3 skipped, 2 xfailed",
        exit_code=1,
    )


def _item(
    base: str,
    branch: str,
    *,
    answer_record: dict[str, Any] | None = None,
    baseline: R.SuiteBaseline | None = None,
    id6: str = "ld8lb3",
) -> dict[str, Any]:
    """An item in the shape a LIVE run presents at the moment gate 2 runs.

    `execute_item_core` writes `item[GATE_ANSWER_RECORD_KEY]` strictly BEFORE the integration block
    builds its `val_runner`, so an answer record sitting on the item beside the lane fields is
    exactly what the real gate sees.
    """

    attempt: dict[str, Any] = {"worktree_base": base, "worktree_branch": branch}
    if baseline is not None:
        attempt["suite_baseline"] = baseline.as_record()
    item: dict[str, Any] = {"id6": id6, "attempts": [attempt]}
    if answer_record is not None:
        item[R.GATE_ANSWER_RECORD_KEY] = answer_record
    return item


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


def _revalidation(item: dict[str, Any]) -> dict[str, Any]:
    record = item.get("post_merge_revalidation")
    assert isinstance(record, dict), "the runner must record what it did"
    return record


class _GateCase(unittest.TestCase):
    """Shared driver for the REAL post-merge factory, so no case reimplements the predicate."""

    @staticmethod
    def _state(repo: pathlib.Path, run_id: str = "r") -> dict[str, Any]:
        return {"repo": str(repo), "run_id": run_id, "options": {"validate": False}}

    def _gate(
        self,
        item: dict[str, Any],
        *,
        merged_failures: tuple[str, ...] = (MEASURED_MERGED_FAILURE,),
        passing: bool = False,
        exit_code: int = 1,
        repo: pathlib.Path | None = None,
        root: pathlib.Path | None = None,
        state: dict[str, Any] | None = None,
        run_dir: pathlib.Path | None = None,
        suite_check: Any = None,
    ) -> bool:
        """Drive `make_integration_validation_runner` itself. Never a local copy of its logic."""

        assert repo is not None and root is not None
        rd = run_dir if run_dir is not None else (root / "run")
        rd.mkdir(parents=True, exist_ok=True)
        checker = (
            suite_check
            if suite_check is not None
            else (
                lambda *_a: _suite_result(
                    passing=passing, exit_code=exit_code, failures=merged_failures
                )
            )
        )
        return R.make_integration_validation_runner(
            state if state is not None else self._state(repo),
            rd,
            item,
            suite_check=checker,
        )("a combined diff", ("lane_work.py",))


# ==================================================================================================
# E-01 / V-01: the two-gate path is WRITTEN DOWN, including the never-asked-because-green case
# ==================================================================================================
class TheTwoGatePathIsDocumentedAtTheAnswerConsequenceBlock(unittest.TestCase):
    """E-01. The backlog item's original diagnosis was wrong because this was nowhere written down.

    These are SOURCE assertions rather than behavior assertions, deliberately: the defect they guard
    is a reader (human or agent) re-deriving a false conclusion from a block that describes gate 1 as
    though it described integration as a whole. A behavioral test cannot catch that.
    """

    @staticmethod
    def _source() -> str:
        import inspect

        return inspect.getsource(R)

    def test_the_block_names_BOTH_gates_by_SYMBOL(self) -> None:
        source = self._source()
        head = source[: source.index("GATE_ANSWER_RECORD_KEY: str")]
        for symbol in (
            "integration_is_earned",
            "integration.earned",
            "make_integration_validation_runner",
            "integrate_lane_branch",
        ):
            self.assertIn(
                symbol,
                head,
                f"the answer-consequence block must name {symbol}; a reader who cannot see the "
                "SECOND gate re-derives the false 'the release is inert' conclusion",
            )

    def test_the_PRE_EXISTING_not_mine_line_is_PRESERVED_and_not_rewritten(
        self,
    ) -> None:
        """That line is TRUE and scoped to gate 1. The defect was the ABSENCE of a second statement."""

        self.assertIn(
            "not-mine     -> RELEASE this attempt's `integration.earned`, so self-finalize "
            "and integration run.",
            self._source(),
            "the original line must survive verbatim; rewriting it would lose the accurate "
            "statement of what gate 1 does",
        )

    def test_the_NEVER_ASKED_BECAUSE_GREEN_case_is_named_EXPLICITLY(self) -> None:
        """`65cuw0`: an item can reach gate 2 having never been asked, because it never failed.

        Measured from the same `state.json`: its suite check is `passing: True` with `exit_code: 0`
        and an EMPTY failures list, and `gate_answer_is_warranted` answers "integration was earned;
        there is nothing to answer" for those values. Its `null` answer record is CORRECT, and the
        original filing read that `null` as an ask-reachability defect that does not exist.
        """

        source = self._source()
        head = source[: source.index("GATE_ANSWER_RECORD_KEY: str")]
        self.assertIn("65cuw0", head)
        self.assertIn("NEVER BEEN ASKED", head.upper())

    def test_the_REAL_predicate_CONFIRMS_65cuw0_was_correctly_never_asked(self) -> None:
        """Not a source claim: the shipped predicate, driven with `65cuw0`'s RECORDED values.

        This is what retracts the ask-reachability premise. If this ever returns True, the comment
        above is wrong and the removed E-item was needed after all.
        """

        warranted, why = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=True,
            integration_signal=R.INTEGRATION_EARNED_BY_SUITE,
            session_id="a-resumable-session",
        )
        self.assertFalse(warranted)
        self.assertIn("integration was earned", why)


# ==================================================================================================
# E-02 / V-02: the three guard rules are stated WITH their reasons
# ==================================================================================================
class TheThreeGuardsAreStatedWithTheReasonThatEstablishesThem(unittest.TestCase):
    """E-02. A guard stated without its reason is a guard the next refactor removes.

    Each of the three was measured REACHABLE in the authored design and two fail OPEN, so the
    citation is the load-bearing part: `32ij2j` and its pinning test for (a), the truncation cap
    constant for (b), the `not-mine` token requirement for (c).
    """

    @staticmethod
    def _head() -> str:
        import inspect

        source = inspect.getsource(R)
        return source[: source.index("GATE_ANSWER_RECORD_KEY: str")]

    def test_guard_a_cites_32ij2j_AND_its_pinning_test(self) -> None:
        head = self._head()
        self.assertIn("32ij2j", head)
        self.assertIn("TheExitCodeIsTheAuthorityAndNotTheList", head)

    def test_guard_b_cites_the_CAP_CONSTANT_and_the_measured_shape(self) -> None:
        head = self._head()
        self.assertIn("SUITE_FAILURE_LIST_CAP", head)
        self.assertIn(
            "45", head, "the measured 45-plus-1 shape is the evidence for guard (b)"
        )

    def test_guard_c_names_the_not_mine_TOKEN_and_why_fixed_is_excluded(self) -> None:
        head = self._head()
        self.assertIn("not-mine", head)
        self.assertIn("PRE-REPAIR", head.upper())

    def test_the_guards_sit_BESIDE_the_consumer_and_not_in_a_distant_file(self) -> None:
        """They are in `runner_shared`, which is where a refactor of this gate happens."""

        self.assertIn("gateinert 01 (`n9na1c`) E-02", self._head())


# ==================================================================================================
# E-03 / V-03: the reader, gated on the TOKEN and writing NOTHING
# ==================================================================================================
class TheAttributedSetIsReadFromTheRecordThatAlreadyCarriesIt(unittest.TestCase):
    """E-03. A READER and a NORMALIZER: no new key, no write, no second vocabulary for the ids."""

    def test_a_usable_not_mine_yields_the_NORMALIZED_attributed_set(self) -> None:
        record = _real_answer_record(R.GATE_ANSWER_NOT_MINE)
        self.assertEqual(
            R.attributed_away_failure_ids(
                {"id6": "x", R.GATE_ANSWER_RECORD_KEY: record}
            ),
            (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),),
        )

    def test_the_FIVE_answer_shapes_and_only_the_FIRST_carries_anything(self) -> None:
        """V-03's five shapes, driven through the REAL producer for the four real answers."""

        observed: dict[str, tuple[str, ...]] = {}
        for answer in R.GATE_ANSWERS:
            record = _real_answer_record(answer)
            observed[answer] = R.attributed_away_failure_ids(
                {"id6": "x", R.GATE_ANSWER_RECORD_KEY: record}
            )
        observed["<absent>"] = R.attributed_away_failure_ids({"id6": "x"})

        self.assertEqual(
            observed[R.GATE_ANSWER_NOT_MINE],
            (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),),
        )
        for token in (
            R.GATE_ANSWER_FIXED,
            R.GATE_ANSWER_MINE,
            R.GATE_ANSWER_NEEDS_HUMAN,
            "<absent>",
        ):
            self.assertEqual(
                observed[token],
                (),
                f"{token} must carry NO attributed set; only `not-mine` releases on the answer alone",
            )

    def test_the_gate_is_the_TOKEN_and_NOT_the_presence_of_the_SET(self) -> None:
        """The whole of guard (c). Every answer's record carries a NON-EMPTY `failing_tests`.

        Measured here rather than asserted: it is what the agent was SHOWN, so a reader keyed on "is
        it non-empty" would release on `mine` and `needs-human` too.
        """

        for answer in R.GATE_ANSWERS:
            record = _real_answer_record(answer)
            self.assertTrue(
                record["failing_tests"],
                f"{answer}'s record carries the shown ids, which is why a presence check is wrong",
            )

    def test_an_UNUSABLE_verdict_carries_NOTHING_even_saying_not_mine(self) -> None:
        self.assertEqual(
            R.attributed_away_failure_ids(
                {
                    "id6": "x",
                    R.GATE_ANSWER_RECORD_KEY: {
                        "answer": R.GATE_ANSWER_NOT_MINE,
                        "usable": False,
                        "failing_tests": [MEASURED_ATTRIBUTED_FAILURE],
                    },
                }
            ),
            (),
        )

    def test_the_record_is_UNCHANGED_key_for_key_and_NO_key_is_added_to_the_item(
        self,
    ) -> None:
        """READ-ONLY, because one call path makes that load-bearing (both hosts pass `dict(item)`)."""

        record = _real_answer_record(R.GATE_ANSWER_NOT_MINE)
        before_record = json.loads(json.dumps(record))
        item = {"id6": "x", R.GATE_ANSWER_RECORD_KEY: record}
        before_keys = set(item)
        R.attributed_away_failure_ids(item)
        self.assertEqual(
            set(item), before_keys, "no new key may be written to the item"
        )
        self.assertEqual(record, before_record, "the answer record must be untouched")

    def test_the_SAME_node_id_with_DIFFERENT_trailing_text_MATCHES(self) -> None:
        """The reason a normalizer is needed at all: the two runs report different trailing text."""

        record = _real_answer_record(R.GATE_ANSWER_NOT_MINE)
        attributed = R.attributed_away_failure_ids(
            {"id6": "x", R.GATE_ANSWER_RECORD_KEY: record}
        )
        self.assertIn(R.normalize_failure_id(MEASURED_MERGED_FAILURE), attributed)

    def test_an_UNPARSEABLE_attributed_line_is_DROPPED_so_it_can_EXCUSE_NOTHING(
        self,
    ) -> None:
        """The sentinel used in the OPPOSITE direction from the baseline arm, on purpose.

        Keeping it would let an unparseable ATTRIBUTED line match an unparseable MERGED line and
        excuse it, though neither is a known node id: a silent fail-open.
        """

        attributed = R.attributed_away_failure_ids(
            {
                "id6": "x",
                R.GATE_ANSWER_RECORD_KEY: {
                    "answer": R.GATE_ANSWER_NOT_MINE,
                    "usable": True,
                    "failing_tests": ["not a pytest failure line at all"],
                },
            }
        )
        self.assertEqual(attributed, ())
        self.assertNotIn(R.UNPARSEABLE_FAILURE_ID, attributed)


# ==================================================================================================
# E-04 / V-04: the consumption, at exactly ONE return path
# ==================================================================================================
class TheAnswerReachesThePostMergeVerdict(_GateCase):
    """E-04. The measured `ld8lb3` replay, and the refusal that must survive beside it."""

    def test_the_MEASURED_ld8lb3_REPLAY_now_PASSES(self) -> None:
        """The whole point of the item: gate 2 stops re-blaming what gate 1 already released."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE),
            )
            self.assertTrue(
                self._gate(item, repo=repo, root=root),
                "a measured red whose every failing id the agent ATTRIBUTED AWAY with a usable "
                "`not-mine` must not be re-refused after the merge; that is the measured defect",
            )
            record = _revalidation(item)
            self.assertTrue(record["passed"])
            self.assertTrue(
                record["measured"], "this WAS a measurement and must say so"
            )
            self.assertIn("not-mine", record["reason"])

    def test_ONE_UNATTRIBUTED_id_REFUSES_and_names_ONLY_that_id(self) -> None:
        """OQ-02. One legitimate excuse never licenses ignoring a regression beside it."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE),
            )
            self.assertFalse(
                self._gate(
                    item,
                    repo=repo,
                    root=root,
                    merged_failures=(MEASURED_MERGED_FAILURE, UNATTRIBUTED),
                )
            )
            reason = _revalidation(item)["reason"]
            self.assertIn("test_introduced_here", reason)
            self.assertNotIn(
                "test_no_bare_except_was_introduced_around_the_new_code",
                reason,
                "the refusal must not list the legitimately attributed id as a reason; that is "
                "what made the original refusals so hard to diagnose",
            )

    def test_ANTI_FAIL_OPEN_1_MINE_releases_NOTHING(self) -> None:
        """CONTROL. `mine` refuses by design and there is no override, deliberately."""

        self._assert_answer_releases_nothing(R.GATE_ANSWER_MINE)

    def test_ANTI_FAIL_OPEN_2_NEEDS_HUMAN_releases_NOTHING(self) -> None:
        """CONTROL. The item waits on a DECISION; releasing it would ship an unreviewed one."""

        self._assert_answer_releases_nothing(R.GATE_ANSWER_NEEDS_HUMAN)

    def test_ANTI_FAIL_OPEN_3_FIXED_releases_NOTHING_THROUGH_THIS_PATH(self) -> None:
        """CONTROL, AND ONE OF THE THREE MEASURED-REACHABLE CASES.

        A verified `fixed` DOES release at GATE 1, and its record carries a NON-EMPTY PRE-REPAIR
        `failing_tests` set, so an answer-agnostic read of that set would clear exactly the ids whose
        repair did not survive the merge. `fixed` earns its gate-1 release from an OBSERVED RE-RUN and
        never from its id set; this channel preserves that asymmetry by gating on the TOKEN.
        """

        outcome = _real_gate_answer(R.GATE_ANSWER_FIXED, rerun_passes=True)
        self.assertTrue(
            outcome.release,
            "the fixture must reproduce the measured shape: a verified `fixed` DOES release at gate 1",
        )
        self.assertTrue(
            outcome.record["failing_tests"],
            "and its record carries a NON-EMPTY PRE-REPAIR id set, which is the fail-open trap",
        )
        self.assertIs(outcome.record["recheck_passed"], True)
        self._assert_answer_releases_nothing(R.GATE_ANSWER_FIXED)

    def test_a_FIXED_answer_whose_RERUN_FAILED_also_releases_NOTHING(self) -> None:
        """The other half of `fixed`: an unverified repair must not leak through this channel either."""

        outcome = _real_gate_answer(R.GATE_ANSWER_FIXED, rerun_passes=False)
        self.assertFalse(outcome.release, "a failing re-run does not release at gate 1")
        self.assertEqual(
            R.attributed_away_failure_ids(
                {"id6": "x", R.GATE_ANSWER_RECORD_KEY: outcome.record}
            ),
            (),
        )

    def _assert_answer_releases_nothing(self, answer: str) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(base, branch, answer_record=_real_answer_record(answer))
            self.assertFalse(
                self._gate(item, repo=repo, root=root),
                f"{answer} must release NOTHING through the post-merge channel",
            )
            self.assertFalse(_revalidation(item)["passed"])

    def test_ANTI_FAIL_OPEN_4_an_UNUSABLE_answer_releases_NOTHING(self) -> None:
        """CONTROL. An unusable verdict is not an answer, and silence is the fail-closed direction."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                answer_record={
                    "answer": R.GATE_ANSWER_NOT_MINE,
                    "usable": False,
                    "failing_tests": [MEASURED_ATTRIBUTED_FAILURE],
                    "violation": "the answer object was malformed",
                },
            )
            self.assertFalse(self._gate(item, repo=repo, root=root))

    def test_ANTI_FAIL_OPEN_5_an_ABSENT_answer_leaves_TODAYS_verdict_UNCHANGED(
        self,
    ) -> None:
        """CONTROL. This is `65cuw0`'s shape, and it must keep refusing on gate 2's own verdict.

        Asserted as EQUALITY against the no-answer verdict rather than merely as False, because the
        claim being made is "byte-identical to today", not "also refuses".
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            without = _item(base, branch, id6="65cuw0")
            self.assertFalse(self._gate(without, repo=repo, root=root))
            record = _revalidation(without)
            self.assertFalse(record["passed"])
            self.assertTrue(record["measured"])
            self.assertNotIn(
                "not-mine",
                record["reason"],
                "an item that was never asked must not be described as having answered",
            )

    def test_ANTI_FAIL_OPEN_6_THE_32ij2j_INVERSION_an_EMPTY_list_on_a_RED_suite(
        self,
    ) -> None:
        """CONTROL, AND THE SINGLE MOST IMPORTANT CASE IN THIS FILE.

        With a merged list of `()`, "every failing id was attributed away" is VACUOUSLY TRUE. Plan
        `32ij2j` shipped exactly that comparison over an always-empty string and "every lane passed
        including one that broke everything". A red suite reporting NO ids must REFUSE, forever.
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE),
            )
            self.assertFalse(
                self._gate(item, repo=repo, root=root, merged_failures=()),
                "a red tree reporting no ids must REFUSE; passing it is how plan 32ij2j would have "
                "integrated a lane that broke everything",
            )

        # And at the predicate, where the vacuous truth actually lives.
        verdict = R.unattributed_merged_failures(
            (),
            (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),),
            suite_passed=False,
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_UNKNOWN)
        self.assertFalse(verdict.introduced_nothing)
        self.assertIn("32ij2j", verdict.reason)

    def test_a_GREEN_suite_with_an_empty_list_is_NOT_the_inversion_case(self) -> None:
        """The complement, so control 6 is a DISCRIMINATION and not a blanket refusal.

        The EXIT CODE is what tells "empty because green" from "empty because nothing parsed".
        """

        verdict = R.unattributed_merged_failures(
            (),
            (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),),
            suite_passed=True,
        )
        self.assertEqual(verdict.judgement, R.REVALIDATION_NO_REGRESSION)

    def test_ANTI_FAIL_OPEN_7_EITHER_list_at_the_CAP_releases_NOTHING(self) -> None:
        """CONTROL, AND THE SECOND MEASURED-REACHABLE CASE. Here the cap fails OPEN.

        The constructed fixture IS the measurement: 45 attributed pre-existing failures plus ONE
        genuine lane regression, both truncated at 40 in first-seen order, so the regression is
        truncated OUT of the merged list and a naive subtraction finds nothing new.
        """

        cap = R.SUITE_FAILURE_LIST_CAP
        pre_existing = tuple(
            f"FAILED tests/test_many.py::T::test_{i:03d}" for i in range(45)
        )
        regression = "FAILED tests/test_new.py::T::test_the_lane_broke_this"
        attributed_kept = pre_existing[:cap]
        merged_kept = (pre_existing + (regression,))[:cap]

        self.assertNotIn(
            regression,
            merged_kept,
            "the fixture must reproduce the measured hazard: the REGRESSION is truncated OUT",
        )
        naive_unexcused = [
            i
            for i in (R.normalize_failure_id(x) for x in merged_kept)
            if i not in {R.normalize_failure_id(x) for x in attributed_kept}
        ]
        self.assertEqual(
            naive_unexcused,
            [],
            "and a naive subtraction therefore finds NOTHING new, which would pass a lane that "
            "introduced a failure",
        )

        verdict = R.unattributed_merged_failures(
            merged_kept,
            tuple(R.normalize_failure_id(x) for x in attributed_kept),
            suite_passed=False,
        )
        self.assertEqual(
            verdict.judgement,
            R.REVALIDATION_UNKNOWN,
            "with either list at the cap the subtraction is unsound and must refuse to judge; "
            "otherwise a truncated-out regression is merged unverified",
        )
        self.assertIn(str(cap), verdict.reason)

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                answer_record=_real_answer_record(
                    R.GATE_ANSWER_NOT_MINE, failures=attributed_kept
                ),
            )
            self.assertFalse(
                self._gate(item, repo=repo, root=root, merged_failures=merged_kept),
                "the cap must refuse AT THE GATE and not only at the predicate",
            )

    def test_the_cap_is_detected_by_LENGTH_on_EITHER_side(self) -> None:
        cap = R.SUITE_FAILURE_LIST_CAP
        many = tuple(f"FAILED tests/test_many.py::T::test_{i:03d}" for i in range(cap))
        one = (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),)
        self.assertEqual(
            R.unattributed_merged_failures(many, one, suite_passed=False).judgement,
            R.REVALIDATION_UNKNOWN,
            "a merged list at the cap",
        )
        self.assertEqual(
            R.unattributed_merged_failures(
                (MEASURED_MERGED_FAILURE,), many, suite_passed=False
            ).judgement,
            R.REVALIDATION_UNKNOWN,
            "an ATTRIBUTED list at the cap, which lies in the other direction",
        )

    def test_the_cap_CONSTANT_still_equals_the_DRIVERS_extractor_limit(self) -> None:
        """A drift between the two makes both guards miss, so it is asserted rather than assumed."""

        self.assertEqual(R.SUITE_FAILURE_LIST_CAP, OC.SUITE_FAILURE_LINE_LIMIT)


class TheCacheServesAMeasurementAndNotAPerItemJudgement(_GateCase):
    """E-04, OQ-03. The cache is keyed on the merged TREE; the verdict is now PER-ITEM.

    OQ-03 was resolved to (b), matching the sibling baseline plan's resolution of the identical trap:
    cache the MEASUREMENT and re-derive the JUDGEMENT per item. So the suite must still run ONCE (the
    property the cache exists for, ~107s) while two items reaching the SAME merge result with
    DIFFERENT answers reach DIFFERENT verdicts. Widening the KEY instead would re-run the suite for a
    comparison that needs none, and would make the two sibling fixes disagree about what the cache
    means.
    """

    def test_TWO_items_ONE_tree_get_their_OWN_judgements_from_ONE_suite_run(
        self,
    ) -> None:
        calls: list[str] = []

        def counting(path: Any, _run_id: Any) -> Any:
            calls.append(str(path))
            return _suite_result(failures=(MEASURED_MERGED_FAILURE,))

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            state = self._state(repo)

            answered = _item(
                base,
                branch,
                answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE),
                id6="ld8lb3",
            )
            never_asked = _item(base, branch, id6="65cuw0")

            first = self._gate(
                answered,
                repo=repo,
                root=root,
                state=state,
                run_dir=run_dir,
                suite_check=counting,
            )
            second = self._gate(
                never_asked,
                repo=repo,
                root=root,
                state=state,
                run_dir=run_dir,
                suite_check=counting,
            )

            self.assertEqual(
                len(calls),
                1,
                "the cache must still measure one merge result ONCE; re-running a ~107s suite for a "
                "judgement that needs none defeats the property the cache exists for",
            )
            self.assertTrue(
                first,
                "the item WITH a usable `not-mine` has every failing id attributed away",
            )
            self.assertFalse(
                second,
                "the item that was NEVER ASKED carries no attributed set, so the same failure is "
                "unexcused for IT; serving the cached verdict wholesale would integrate a lane "
                "nothing cleared",
            )
            self.assertTrue(
                _revalidation(never_asked)["cached"], "it is still a cache HIT"
            )


class TheFiveNonMeasuredRedPathsAreUNCHANGED(_GateCase):
    """`_runner` has SIX return paths and only ONE is a measured red. The other five must not move.

    Each `measured`/`skipped` flag is asserted beside its boolean because that flag decides the
    refusal KIND (`revalidation_was_unmeasured` -> `merge-unchecked` versus `merge-refused`), and
    reclassifying a harness fault as a code red restores the `l2mzxn` defect. Every item here carries
    a usable `not-mine`, which is the point: the answer must not leak into a path that measured
    nothing.
    """

    def test_VALIDATE_ON_still_SKIPS_and_runs_NO_suite(self) -> None:
        ran: list[str] = []

        def should_not_run(path: Any, _run_id: Any) -> Any:
            ran.append(str(path))
            return _suite_result()

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertTrue(
                self._gate(
                    item,
                    repo=repo,
                    root=root,
                    state={
                        "repo": str(repo),
                        "run_id": "r",
                        "options": {"validate": True},
                    },
                    suite_check=should_not_run,
                )
            )
            record = _revalidation(item)
            self.assertTrue(record["skipped"])
            self.assertEqual(ran, [], "the verifier mode must not gain a second gate")

    def test_NO_suite_check_still_refuses_as_UNMEASURED(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, Any] = {
                "id6": "xx1111",
                R.GATE_ANSWER_RECORD_KEY: _real_answer_record(R.GATE_ANSWER_NOT_MINE),
            }
            self.assertFalse(
                R.make_integration_validation_runner(
                    {"options": {"validate": False}}, run_dir, item
                )("d", ())
            )
            self.assertIs(_revalidation(item)["measured"], False)
            self.assertTrue(R.revalidation_was_unmeasured(item))

    def test_an_UNRESOLVABLE_base_or_head_still_refuses_as_UNMEASURED(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, _base, _branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item: dict[str, Any] = {
                "id6": "xx2222",
                R.GATE_ANSWER_RECORD_KEY: _real_answer_record(R.GATE_ANSWER_NOT_MINE),
            }
            self.assertFalse(
                R.make_integration_validation_runner(
                    self._state(repo),
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(),
                )("d", ())
            )
            self.assertIs(_revalidation(item)["measured"], False)

    def test_an_UNMATERIALIZABLE_merge_still_refuses_as_UNMEASURED(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, _branch = _repo_with_a_lane(root)
            run_dir = root / "run"
            run_dir.mkdir()
            item = _item(
                base,
                "aw/lane/ld8lb3",
                answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE),
            )
            # A head that does not exist: the merge result cannot be built.
            item["lane_head"] = "0" * 40
            self.assertFalse(
                R.make_integration_validation_runner(
                    self._state(repo),
                    run_dir,
                    item,
                    suite_check=lambda *_a: _suite_result(),
                )("d", ())
            )
            self.assertIs(_revalidation(item)["measured"], False)

    def test_a_SUITE_EXCEPTION_still_refuses_as_UNMEASURED(self) -> None:
        def boom(*_args: Any) -> Any:
            raise RuntimeError("the harness broke")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertFalse(
                self._gate(item, repo=repo, root=root, suite_check=boom),
                "an answer must never excuse a measurement that never happened",
            )
            record = _revalidation(item)
            self.assertIs(record["measured"], False)
            self.assertTrue(R.revalidation_was_unmeasured(item))

    def test_the_EXIT_5_reading_short_circuits_BEFORE_the_comparison(self) -> None:
        """A tree that collected NOTHING has no failing set, so no comparison may see it.

        Feeding its empty list to either arm would hit the `32ij2j` guard and answer `unknown`,
        converting a deliberate pass back into a refusal.
        """

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertTrue(
                self._gate(
                    item,
                    repo=repo,
                    root=root,
                    suite_check=lambda *_a: _suite_result(
                        passing=False,
                        exit_code=5,
                        summary="",
                        reason="no tests ran",
                        failures=(),
                    ),
                )
            )
            record = _revalidation(item)
            self.assertIn("collected NO tests", record["reason"])
            self.assertNotIn(
                "baseline_comparison",
                record,
                "no comparison was made, and the record must not imply one was",
            )

    def test_a_GREEN_merged_tree_passes_with_NO_comparison_made(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertTrue(
                self._gate(
                    item,
                    repo=repo,
                    root=root,
                    passing=True,
                    exit_code=0,
                    merged_failures=(),
                )
            )
            self.assertNotIn("baseline_comparison", _revalidation(item))


class TheRefusalVocabularyGainsNoNewKindAndNoNewKey(_GateCase):
    """The plan's own scope rule: no new refusal kind, no new status, no new answer token, no new key.

    Asserted because the tempting implementation is a new `INTEGRATION_REFUSAL_*` kind or a second
    key on the item, either of which would touch every renderer and reintroduce the `render_stream`
    F-4 producer/reader drift this module's comments cite twice.
    """

    def test_an_answer_RELEASED_pass_is_not_reclassified_as_a_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertTrue(self._gate(item, repo=repo, root=root))
            self.assertFalse(
                R.revalidation_was_unmeasured(item),
                "a PASSING record is not a refusal of any kind",
            )

    def test_the_ANSWER_TOKEN_VOCABULARY_is_UNCHANGED(self) -> None:
        self.assertEqual(
            R.GATE_ANSWERS,
            (
                R.GATE_ANSWER_NOT_MINE,
                R.GATE_ANSWER_FIXED,
                R.GATE_ANSWER_MINE,
                R.GATE_ANSWER_NEEDS_HUMAN,
            ),
        )

    def test_the_revalidation_RECORD_gains_NO_new_key(self) -> None:
        """The answer arm is legible in the reason string and in the item's own answer record."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self.assertTrue(self._gate(item, repo=repo, root=root))
            self.assertEqual(
                set(_revalidation(item)),
                {
                    "passed",
                    "tree",
                    "reason",
                    "failures",
                    "merged_files",
                    "cached",
                    "skipped",
                    "measured",
                    "baseline_comparison",
                },
            )

    def test_the_record_stays_JSON_SERIALIZABLE(self) -> None:
        """It is written into `state.json`, so a tuple or NamedTuple leaking in would break a run."""

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base, branch, answer_record=_real_answer_record(R.GATE_ANSWER_NOT_MINE)
            )
            self._gate(item, repo=repo, root=root)
            self.assertTrue(json.loads(json.dumps(_revalidation(item)))["passed"])


# ==================================================================================================
# E-07 / V-07: the COMPOSITION with the sibling baseline fix, on the merged result
# ==================================================================================================
class TheCompositionWithTheBaselineArmIsAUnionOfTwoExcuses(_GateCase):
    """E-07. Both plans modify the SAME `_runner` verdict, so the composed rule is pinned HERE.

    THE ONLY ACCEPTABLE COMPOSITION IS A UNION OF TWO EXCUSES OVER ONE REFUSAL: an id excused by
    EITHER the baseline or the answer is not new, and an id excused by NEITHER still refuses. The
    union is PER-ID and not per-judgement, which the MIXED case proves is a correctness requirement
    rather than a refinement: composing the two booleans would refuse a lane that introduced nothing.

    AND THE COMPOSITION MUST ADD NO THIRD UNKNOWN-HANDLING RULE. Both arms make an unknown REFUSE, so
    two refusing unknowns must compose to a REFUSAL; a composition that turned them into a pass would
    be the `32ij2j` inversion arriving by a new route.
    """

    def _matrix_case(
        self,
        *,
        baseline_ids: tuple[str, ...],
        attributed: tuple[str, ...],
        merged: tuple[str, ...],
    ) -> tuple[bool, str]:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo, base, branch = _repo_with_a_lane(root)
            item = _item(
                base,
                branch,
                baseline=_completed_baseline(baseline_ids),
                answer_record=(
                    None
                    if attributed is None
                    else {
                        "answer": R.GATE_ANSWER_NOT_MINE,
                        "usable": True,
                        "failing_tests": list(attributed),
                        "reason": "the agent's reason",
                    }
                ),
            )
            passed = self._gate(item, repo=repo, root=root, merged_failures=merged)
            return passed, _revalidation(item)["reason"]

    def test_THE_FOUR_WAY_MATRIX(self) -> None:
        """A failing id in the baseline only, the attributed set only, both, and neither."""

        both_arms = (BASELINE_ONLY,), (ANSWER_ONLY,)

        passed, reason = self._matrix_case(
            baseline_ids=both_arms[0], attributed=both_arms[1], merged=(BASELINE_ONLY,)
        )
        self.assertTrue(passed, "IN BASELINE ONLY: already red before the work")
        self.assertIn(LD8LB3_BASE, reason)

        passed, reason = self._matrix_case(
            baseline_ids=both_arms[0], attributed=both_arms[1], merged=(ANSWER_ONLY,)
        )
        self.assertTrue(passed, "IN ATTRIBUTED SET ONLY: the agent attributed it away")
        self.assertIn("not-mine", reason)

        passed, _reason = self._matrix_case(
            baseline_ids=(IN_BOTH,), attributed=(IN_BOTH,), merged=(IN_BOTH,)
        )
        self.assertTrue(passed, "IN BOTH: excused twice over")

        passed, reason = self._matrix_case(
            baseline_ids=both_arms[0], attributed=both_arms[1], merged=(IN_NEITHER,)
        )
        self.assertFalse(
            passed,
            "IN NEITHER: the composed gate must still be able to say no; this is the case whose "
            "failure would mean the two fixes together integrate anything",
        )
        self.assertIn("test_in_neither", reason)

    def test_the_MIXED_case_needs_the_PER_ID_union(self) -> None:
        """Each arm holds ONE leftover the OTHER excuses, so both arms say `regressed` and it PASSES.

        This is the case a per-JUDGEMENT composition gets wrong, and it is why the union is per-id.
        """

        passed, reason = self._matrix_case(
            baseline_ids=(BASELINE_ONLY,),
            attributed=(ANSWER_ONLY,),
            merged=(BASELINE_ONLY, ANSWER_ONLY),
        )
        self.assertTrue(
            passed,
            "merged {A, B} with A in the baseline and B attributed away leaves NO id unexcused; "
            "refusing it would reintroduce the defect both plans exist to remove",
        )
        self.assertIn("excused by the pre-work baseline or by the agent", reason)

    def test_the_MIXED_case_PLUS_one_unexcused_id_still_REFUSES(self) -> None:
        passed, reason = self._matrix_case(
            baseline_ids=(BASELINE_ONLY,),
            attributed=(ANSWER_ONLY,),
            merged=(BASELINE_ONLY, ANSWER_ONLY, IN_NEITHER),
        )
        self.assertFalse(passed)
        self.assertIn("test_in_neither", reason)
        self.assertNotIn(
            "test_in_baseline_only",
            reason,
            "OQ-02: the refusal names ONLY the unexcused ids",
        )
        self.assertNotIn("test_in_attributed_set_only", reason)

    def test_the_TWO_UNKNOWN_shapes_still_REFUSE_UNDER_COMPOSITION(self) -> None:
        """Two refusing unknowns must not become a pass, which is the new-route inversion."""

        passed, reason = self._matrix_case(
            baseline_ids=(BASELINE_ONLY,), attributed=(ANSWER_ONLY,), merged=()
        )
        self.assertFalse(passed, "EMPTY merged list on a red suite, under composition")
        self.assertIn("UNKNOWN", reason)

        cap = R.SUITE_FAILURE_LIST_CAP
        many = tuple(f"FAILED tests/test_many.py::T::test_{i:03d}" for i in range(cap))
        passed, reason = self._matrix_case(
            baseline_ids=many, attributed=(ANSWER_ONLY,), merged=many
        )
        self.assertFalse(passed, "AT-THE-CAP, under composition")
        self.assertIn(str(cap), reason)

    def test_the_COMPOSER_reads_an_UNKNOWN_arm_as_EXCUSING_NOTHING(self) -> None:
        """Directly at the composer, because this is the whole no-third-rule argument.

        An `unknown` arm's `new_ids` "must NOT be acted on": for the absent cases it is the WHOLE
        merged set, and for the vacuous-truth case it is EMPTY, which read as a leftover set would
        excuse EVERYTHING.
        """

        unknown = R.RevalidationComparison(
            judgement=R.REVALIDATION_UNKNOWN,
            new_ids=(),
            reason="nothing could be measured",
            merged_ids=(IN_NEITHER,),
        )
        unexcused, why = R._compose_revalidation_excuses(unknown, unknown)
        self.assertIsNone(
            unexcused,
            "two unknowns must compose to a REFUSAL; reading their empty new_ids as a leftover set "
            "would excuse every failing id in the tree",
        )
        self.assertIn("NEITHER", why)

    def test_BOTH_sibling_predicates_are_STILL_PRESENT_and_INDEPENDENT(self) -> None:
        """The composition must not have replaced either arm with the other."""

        self.assertTrue(callable(R.new_failures_since_baseline))
        self.assertTrue(callable(R.unattributed_merged_failures))
        baseline_only = R.new_failures_since_baseline(
            (MEASURED_MERGED_FAILURE,),
            _completed_baseline((MEASURED_ATTRIBUTED_FAILURE,)),
            suite_passed=False,
        )
        self.assertEqual(baseline_only.judgement, R.REVALIDATION_NO_REGRESSION)
        answer_only = R.unattributed_merged_failures(
            (MEASURED_MERGED_FAILURE,),
            (R.normalize_failure_id(MEASURED_ATTRIBUTED_FAILURE),),
            suite_passed=False,
        )
        self.assertEqual(answer_only.judgement, R.REVALIDATION_NO_REGRESSION)


if __name__ == "__main__":
    unittest.main()
