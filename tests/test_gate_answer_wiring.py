#!/usr/bin/env python3
"""gatewire-01 (`h5pyqa`): the integration-refusal answer, WIRED.

WHAT THIS FILE PROVES, and why each case earns its place rather than merely passing.

THE DEFECT BEING CLOSED IS MEASURED, not hypothetical. In run `run-20260919T194413Z-2056285` ONE test
unrelated to any lane's work went red; because every lane's trust signal is the same
whole-repository suite, THREE lanes were refused, nothing merged, eight further items cascaded to
`dependency-blocked`, and the run spent 2h 10m and $55.02 producing no integrated work. Every one of
those lanes had done its job and had no way to say so. The vocabulary to answer that refusal shipped
inert at `395fc06b`; this plan is its only consumer.

THE CASES:

  * ONLY `suite-failed` IS ASKABLE (V-01). A `verifier-declined` refusal must NOT be answerable away by
    the agent it judged - `integration_is_earned`'s own rule is that "a green suite deliberately does
    NOT override an explicit verifier verdict", so letting the answer override it would make
    `--validate` WEAKER than the default. `no-trust-signal` is not asked because there is nothing to
    attribute.
  * THE FAILING TEST NAMES REACH THE QUESTION (V-02/V-07). This is the finding that made the plan's
    original E-02 unsatisfiable: `_SUITE_SUMMARY_RE` captures only the COUNT line, so an agent asked
    to attribute "1 failed" is being asked to attribute a failure it was never shown.
  * ONLY `not-mine` RELEASES (V-03), on BOTH lane shapes. `mine`, `needs-human`, silence, an unknown
    token and a reasonless `not-mine` all refuse, which is the fail-closed direction: a wrongly
    REFUSED lane is preserved and recoverable, a wrongly INTEGRATED one merges work no trust signal
    cleared.
  * A `fixed` CLAIM IS RE-VERIFIED, NEVER TRUSTED (V-04), and the re-run count never exceeds the run's
    existing `--retry-budget`.
  * THE ANSWER IS DURABLE AND ATTRIBUTED (V-05). This is not bookkeeping: it IS the safeguard. The
    maintainer ruled (2026-09-20, OQ-02) that `not-mine` may release in ANY run because attribution,
    not supervision, is what makes an agent's assertion safe - exactly as a `- Readiness:` field and a
    `V-*` evidence block are made safe.
  * `needs-human` IS VISIBLE WHERE AN OPERATOR LOOKS (V-06), and distinct from an ordinary refusal,
    because it routes to a different person.

NO REAL MODEL TURN IS SPENT and NO REAL SUITE IS RUN. Every host invocation and every suite re-run is
a stub, as the sibling `tests/test_defect_report.py` does, so this file is deterministic and free.

NOTHING READS `.aw/records/runs/`, which is GITIGNORED: a test asserting against it passes on one
machine and fails in CI. Every record here is built in a `tempfile` directory.
"""

from __future__ import annotations

import ast
import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, render_stream
from agent_workflows import runner_shared as R

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _suite(
    passing: bool,
    *,
    exit_code: int = 1,
    summary: str = "1 failed, 7080 passed, 3 skipped, 2 xfailed in 98.49s",
    failures: tuple[str, ...] = (
        "FAILED tests/test_unrelated.py::test_a_thing - assert 1 == 2",
    ),
) -> oc_runipd.SuiteCheckResult:
    return oc_runipd.SuiteCheckResult(
        passing=passing,
        exit_code=0 if passing else exit_code,
        summary="7081 passed in 97.10s" if passing else summary,
        reason="stub",
        cwd="/primary",
        timeout_seconds=oc_runipd.SUITE_CHECK_TIMEOUT_SECONDS,
        elapsed_seconds=98.49,
        failures=() if passing else failures,
    )


def _answer_writer(path: Path, *answers: Any):
    """A stubbed `ask` that writes the NEXT scripted answer into the outcome file each time.

    Mirrors how `tests/test_defect_report.py` stubs the re-ask: the resume primitive is replaced by a
    function that performs what a real agent turn would have performed (rewriting the outcome file),
    so the code under test exercises its real read path.
    """

    calls: list[str] = []
    queue = list(answers)

    def ask(prompt: str) -> tuple[int, str, Path, list[str]]:
        calls.append(prompt)
        payload: dict[str, Any] = {"schema_version": 1, "disposition": "executed"}
        if queue:
            nxt = queue.pop(0)
            if nxt is not None:
                payload[R.GATE_ANSWER_KEY] = nxt
        path.write_text(json.dumps(payload), encoding="utf-8")
        return 0, "ses-1", path, ["stub"]

    return ask, calls


# ---- E-01 / V-01: only the SUITE refusal is askable ----------------------------------------------


class OnlyTheSuiteRefusalIsAskable(unittest.TestCase):
    """V-01. The two exclusions are the substance of the predicate, not padding."""

    def test_a_suite_failure_refusal_IS_asked_about(self) -> None:
        warranted, reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_SUITE_FAILED,
            session_id="ses-1",
        )
        self.assertTrue(warranted, reason)

    def test_a_verifier_DECLINE_is_never_answerable_away_by_the_agent_it_judged(
        self,
    ) -> None:
        """The decisive exclusion: a verifier verdict outranks a suite, so it must not be askable.

        If this ever passes `warranted=True`, `--validate` becomes WEAKER than the default, because the
        judged agent could talk its way past an explicit decline while a mere red suite could not.
        """

        warranted, reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_VERIFIER_DECLINED,
            session_id="ses-1",
        )
        self.assertFalse(warranted)
        self.assertIn("verifier-declined", reason)

    def test_no_trust_signal_at_all_is_not_asked_about(self) -> None:
        warranted, _reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_NO_SIGNAL,
            session_id="ses-1",
        )
        self.assertFalse(warranted)

    def test_an_EARNED_integration_is_not_asked_about(self) -> None:
        warranted, _reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=True,
            integration_signal=R.INTEGRATION_EARNED_BY_SUITE,
            session_id="ses-1",
        )
        self.assertFalse(warranted)

    def test_a_turn_with_no_resumable_session_is_not_asked(self) -> None:
        """An isolated lane turn is ALWAYS a fresh session by design, so there may be none to resume.

        Resuming the wrong session would run the follow-up in a DIFFERENT worktree, which is the
        measured `xd9sll` defect that cost four consecutive lanes.
        """

        warranted, reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_SUITE_FAILED,
            session_id=None,
        )
        self.assertFalse(warranted)
        self.assertIn("session", reason)

    def test_it_is_bounded_at_exactly_one_ask_per_attempt(self) -> None:
        warranted, reason = R.gate_answer_is_warranted(
            integration_gate_relevant=True,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_SUITE_FAILED,
            session_id="ses-1",
            already_asked=True,
        )
        self.assertFalse(warranted)
        self.assertIn("already been spent", reason)

    def test_a_review_turn_is_never_asked(self) -> None:
        """A review has no suite result to refuse on, so the whole mechanism is out of scope for it."""

        warranted, _reason = R.gate_answer_is_warranted(
            integration_gate_relevant=False,
            earned=False,
            integration_signal=R.INTEGRATION_REFUSED_SUITE_FAILED,
            session_id="ses-1",
        )
        self.assertFalse(warranted)


# ---- E-02 / V-02: the failing test NAMES, which did not exist before ------------------------------


class TheFailingTestNamesAreCaptured(unittest.TestCase):
    """V-02. A COUNT is not attributable to a diff; a NAME is."""

    #: Real pytest output, shape-for-shape (verified 2026-09-20 by running a deliberately red suite
    #: under this repository's own `addopts`).
    REAL_OUTPUT = (
        "F.F                                                                      [100%]\n"
        "=================================== FAILURES ===================================\n"
        "___________________________________ test_bad ___________________________________\n"
        "    def test_bad():\n"
        ">       assert 1 == 2\n"
        "E       assert 1 == 2\n"
        "=========================== short test summary info ============================\n"
        "FAILED tests/test_demo.py::test_err - RuntimeError: boom\n"
        "FAILED tests/test_demo.py::test_bad - assert 1 == 2\n"
        "2 failed, 1 passed in 0.04s\n"
    )

    def test_the_OLD_behavior_yields_only_a_count_line(self) -> None:
        """The contrast V-02 demands: this is what the agent would have been shown before.

        Asserted rather than described, because the plan's original E-02 said to pass
        `suite_result.summary` and that was UNSATISFIABLE for exactly this reason.
        """

        m = oc_runipd._SUITE_SUMMARY_RE.search(self.REAL_OUTPUT)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual("2 failed, 1 passed in 0.04s", m.group(1).strip())
        self.assertNotIn("FAILED", m.group(1))
        self.assertNotIn("test_bad", m.group(1))

    def test_the_new_field_carries_the_actual_node_ids(self) -> None:
        failures = oc_runipd.extract_suite_failures(self.REAL_OUTPUT)
        self.assertIn("FAILED tests/test_demo.py::test_bad - assert 1 == 2", failures)
        self.assertIn(
            "FAILED tests/test_demo.py::test_err - RuntimeError: boom", failures
        )
        self.assertEqual(2, len(failures))

    def test_a_COLLECTION_ERROR_is_captured_too(self) -> None:
        """MEASURED 2026-09-20: a module that cannot be imported yields `ERROR`, never `FAILED`.

        Matching only `FAILED` would show an agent NOTHING for the whole collection-error class, which
        is the class most likely to be somebody else's fault and so most likely to be a true
        `not-mine` - precisely the case this feature exists to serve.
        """

        out = (
            "==================================== ERRORS ====================================\n"
            "ERROR test_broken.py\n"
            "1 failed, 1 passed, 1 error in 1.79s\n"
        )
        self.assertIn("ERROR test_broken.py", oc_runipd.extract_suite_failures(out))

    def test_duplicate_lines_are_collapsed(self) -> None:
        dupe = "FAILED tests/a.py::t - x\nFAILED tests/a.py::t - x\n"
        self.assertEqual(1, len(oc_runipd.extract_suite_failures(dupe)))

    def test_the_line_count_is_capped_so_one_bad_suite_cannot_crowd_out_the_question(
        self,
    ) -> None:
        many = "\n".join(f"FAILED tests/t.py::test_{i} - boom" for i in range(500))
        self.assertLessEqual(
            len(oc_runipd.extract_suite_failures(many)),
            oc_runipd.SUITE_FAILURE_LINE_LIMIT,
        )

    def test_a_real_run_populates_the_field_and_the_summary_stays_a_count(self) -> None:
        """END TO END through `run_suite_check` on a REAL red suite, not a parser unit test."""

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "pyproject.toml").write_text(
                '[tool.pytest.ini_options]\naddopts = "-q"\n', encoding="utf-8"
            )
            (repo / "test_red.py").write_text(
                "def test_ok():\n    assert True\n\n"
                "def test_bad():\n    assert 1 == 2\n",
                encoding="utf-8",
            )
            result = oc_runipd.run_suite_check(repo, "run-test", timeout=180.0)

        self.assertFalse(result.passing)
        self.assertTrue(
            any("test_bad" in line for line in result.failures),
            f"the failing test name must be captured, got {result.failures!r}",
        )
        self.assertNotIn(
            "FAILED",
            result.summary,
            "`summary` must remain the COUNT line; the names belong in `failures`",
        )

    def test_a_count_only_field_would_FAIL_this_item(self) -> None:
        """V-02's explicit bar: a field containing just "N failed" is not sufficient.

        Stated as an assertion so the bar cannot be met by a field that merely EXISTS.
        """

        counted = _suite(False, failures=("1 failed",))
        self.assertNotIn(
            "::",
            counted.failures[0],
            "a count carries no node id, which is why V-02 refuses it",
        )
        named = _suite(False)
        self.assertIn("::", named.failures[0])

    def test_the_field_is_DEFAULTED_so_existing_construction_sites_are_unchanged(
        self,
    ) -> None:
        legacy = oc_runipd.SuiteCheckResult(
            passing=False,
            exit_code=1,
            summary="1 failed",
            reason="r",
            cwd="/",
            timeout_seconds=60.0,
            elapsed_seconds=1.0,
        )
        self.assertEqual((), legacy.failures)

    def test_failing_text_never_renders_an_empty_section_into_the_prompt(self) -> None:
        """An empty evidence section reads as "no failures" and would invite a false `not-mine`."""

        blank = oc_runipd.SuiteCheckResult(
            passing=False,
            exit_code=127,
            summary="",
            reason="suite could not be executed",
            cwd="/",
            timeout_seconds=60.0,
            elapsed_seconds=1.0,
        )
        self.assertTrue(blank.failing_text.strip())
        count_only = _suite(False, failures=())
        self.assertIn("could not be recovered", count_only.failing_text)

    def test_the_names_are_PERSISTED_on_the_attempt_record(self) -> None:
        """V-02's second half: a human reading the run record must see them too."""

        src = inspect.getsource(R.execute_item_core)
        block = src[src.index('attempt["suite_check"] = {') :]
        block = block[: block.index("}")]
        self.assertIn(
            '"failures"',
            block,
            'attempt["suite_check"] must persist the failing test names beside the count',
        )


# ---- E-03 / V-03: only `not-mine` releases -------------------------------------------------------


class OnlyNotMineReleases(unittest.TestCase):
    """V-03. Silence and every malformed answer refuse: the fail-closed direction."""

    def _perform(self, answer: Any, **kw: Any) -> R.GateAnswerOutcome:
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, calls = _answer_writer(outcome, answer)
            result = R.perform_gate_answer(
                suite_result=_suite(False),
                changed_files=["agent_workflows/mine.py"],
                ask=ask,
                outcome_path=outcome,
                **kw,
            )
            self.assertEqual(
                1 + int(result.record["recheck_attempts"]),
                len(calls),
                "one ask, plus one per re-run handed back",
            )
            return result

    def test_not_mine_with_a_reason_RELEASES(self) -> None:
        out = self._perform(
            {
                "answer": "not-mine",
                "reason": "the test is in a file my diff never touched",
            }
        )
        self.assertTrue(out.release)
        self.assertEqual("not-mine", out.record["answer"])

    def test_mine_REFUSES_and_there_is_no_override(self) -> None:
        out = self._perform({"answer": "mine"})
        self.assertFalse(out.release)
        self.assertEqual("mine", out.record["answer"])
        self.assertTrue(out.record["refuses"])

    def test_needs_human_REFUSES_and_is_marked_as_awaiting_a_DECISION(self) -> None:
        out = self._perform(
            {"answer": "needs-human", "reason": "two repairs are both defensible"}
        )
        self.assertFalse(out.release)
        self.assertTrue(out.record["awaits_human_decision"])

    def test_SILENCE_refuses(self) -> None:
        out = self._perform(None)
        self.assertFalse(out.release)
        self.assertEqual("", out.record["answer"])
        self.assertTrue(out.record["violation"])

    def test_an_UNKNOWN_TOKEN_refuses_and_is_refused_BY_NAME(self) -> None:
        out = self._perform({"answer": "probably-fine", "reason": "trust me"})
        self.assertFalse(out.release)
        self.assertIn("probably-fine", out.record["violation"])

    def test_a_REASONLESS_not_mine_refuses(self) -> None:
        """The reason is what makes the claim reviewable, so a claim without one is not usable."""

        out = self._perform({"answer": "not-mine"})
        self.assertFalse(out.release)
        self.assertEqual("", out.record["answer"])

    def test_a_release_is_recorded_as_integrating_and_a_refusal_is_not(self) -> None:
        released = self._perform({"answer": "not-mine", "reason": "not my file"})
        refused = self._perform({"answer": "mine"})
        self.assertTrue(released.record["integrates"])
        self.assertFalse(refused.record["integrates"])

    def test_the_release_reaches_BOTH_lane_shapes_from_ONE_site(self) -> None:
        """V-03's decisive structural assertion: a fix on one lane shape is a fix on NEITHER.

        The isolated-lane self-finalize arm and the non-isolated arm each test `integration.earned`.
        Rather than patching both, the wiring releases the VERDICT at its source, BEFORE either arm
        reads it. This asserts that ordering on the source, which is what makes one wiring serve both.

        THE LOCATORS ARE FORMATTING-INSENSITIVE, and that is not cosmetic. Both arms were originally
        found by an exact substring INCLUDING the `if `/`elif ` keyword, which made this test fail
        whenever the FORMATTER re-wrapped a condition it had not otherwise changed - measured
        2026-09-21 in integearn-05 (`9lyg5h`), whose added `try:`/`finally:` deepened the indentation
        by four columns and so pushed the isolated arm past the line limit, which `ruff-format` split
        into `if (\\n    self_finalize\\n    and work_dir\\n    ...\\n):`. The ORDERING property this
        test exists for was completely intact; only the locator broke.
        So the source is whitespace-collapsed and the keyword is dropped from the needle, leaving the
        CONDITION itself as the locator. That keeps the assertion about the ordering rather than about
        line wrapping. Offsets into the collapsed text stay valid for the `<` comparison because
        collapsing is monotonic in position.
        """

        src = " ".join(inspect.getsource(R.execute_item_core).split())
        release_site = src.index("integration = integration.__class__(")
        arms = [
            m
            for m in (
                src.find(
                    "self_finalize and work_dir and wt_handle is not None and integration.earned"
                ),
                src.find("self_finalize and not work_dir and integration.earned"),
            )
        ]
        for arm in arms:
            self.assertGreater(
                arm, 0, "both self-finalize arms must still be present to gate on"
            )
            self.assertLess(
                release_site,
                arm,
                "the answer must release the verdict BEFORE either lane shape reads it, or the "
                "fix reaches only one of them",
            )


# ---- E-04 / V-04: a `fixed` claim is re-verified, never trusted -----------------------------------


class AFixedClaimIsVerifiedByTheSuite(unittest.TestCase):
    """V-04. The RE-RUN decides, and the loop is bounded by the run's existing budget."""

    def _perform(
        self, *answers: Any, reruns: tuple[bool, ...], budget: int = 2
    ) -> tuple[R.GateAnswerOutcome, list[str], int]:
        runs = list(reruns)
        performed: list[bool] = []

        def rerun() -> oc_runipd.SuiteCheckResult:
            passing = runs.pop(0) if runs else False
            performed.append(passing)
            return _suite(passing)

        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, calls = _answer_writer(outcome, *answers)
            out = R.perform_gate_answer(
                suite_result=_suite(False),
                changed_files=["agent_workflows/mine.py"],
                ask=ask,
                outcome_path=outcome,
                rerun_suite=rerun,
                retry_budget=budget,
            )
        return out, calls, len(performed)

    FIXED = {"answer": "fixed", "reason": "I repaired the assertion I had broken"}

    def test_a_fixed_claim_whose_RERUN_PASSES_integrates(self) -> None:
        out, _calls, runs = self._perform(self.FIXED, reruns=(True,))
        self.assertTrue(out.release)
        self.assertEqual(1, runs)
        self.assertIs(True, out.record["recheck_passed"])

    def test_a_fixed_claim_that_fails_then_succeeds_on_a_FURTHER_attempt_integrates(
        self,
    ) -> None:
        out, calls, runs = self._perform(
            self.FIXED, self.FIXED, reruns=(False, True), budget=2
        )
        self.assertTrue(out.release)
        self.assertEqual(2, runs)
        self.assertEqual(
            2, len(calls), "the NEW failure must be handed back and re-asked"
        )
        self.assertIn(
            "STILL DID NOT PASS",
            calls[1],
            "the second question must state that the re-run, not the claim, decided",
        )

    def test_a_fixed_claim_that_NEVER_passes_refuses_with_the_lane_preserved(
        self,
    ) -> None:
        out, _calls, runs = self._perform(
            self.FIXED, self.FIXED, self.FIXED, reruns=(False, False, False), budget=2
        )
        self.assertFalse(out.release)
        self.assertEqual(2, runs, "never more than the budget")
        self.assertIs(False, out.record["recheck_passed"])

    def test_the_rerun_count_NEVER_exceeds_the_resolved_retry_budget(self) -> None:
        for budget in (0, 1, 2, 3):
            with self.subTest(budget=budget):
                out, _calls, runs = self._perform(
                    *([self.FIXED] * (budget + 2)),
                    reruns=tuple([False] * (budget + 2)),
                    budget=budget,
                )
                self.assertLessEqual(runs, budget)
                self.assertEqual(budget, out.record["recheck_budget"])
                self.assertEqual(runs, out.record["recheck_attempts"])

    def test_a_budget_of_ZERO_never_verifies_and_therefore_refuses(self) -> None:
        """Spec 5.5's reading of 0 is "no corrections", so an unverifiable claim must refuse."""

        out, _calls, runs = self._perform(self.FIXED, reruns=(True,), budget=0)
        self.assertFalse(out.release)
        self.assertEqual(0, runs)
        self.assertIn("NOT verified", out.record["recheck_summary"])

    def test_a_PASSING_rerun_is_what_releases_and_not_the_claim(self) -> None:
        """The distinction the whole item rests on, asserted directly.

        Same answer, same everything; only the RE-RUN's verdict differs, and only it decides.
        """

        passed, _c, _r = self._perform(self.FIXED, reruns=(True,))
        failed, _c2, _r2 = self._perform(self.FIXED, reruns=(False,), budget=1)
        self.assertTrue(passed.release)
        self.assertFalse(failed.release)

    def test_no_SECOND_retry_knob_was_introduced(self) -> None:
        """Maintainer ruling 2026-09-20: SHARE `--retry-budget`. A new dial is the re-fork to avoid."""

        src = inspect.getsource(R.execute_item_core)
        block = src[src.index("gate_answer_asked, gate_answer_reason") :]
        self.assertIn("retry_budget=frozen_retry_budget(state)", block)
        for host, module in HOSTS:
            with self.subTest(host=host):
                parser_src = Path(str(module.__file__)).read_text(encoding="utf-8")
                self.assertNotIn("--gate-answer-retry", parser_src)
                self.assertNotIn("--gate-retry-budget", parser_src)

    def test_the_budget_comes_from_the_runs_FROZEN_value(self) -> None:
        """Resolved once at queue build, never re-resolved from a bare None by a later reader."""

        self.assertEqual(3, R.frozen_retry_budget({"options": {"retry_budget": 3}}))
        self.assertEqual(0, R.frozen_retry_budget({"options": {"retry_budget": 0}}))


# ---- E-05 / V-05: the answer is durable and ATTRIBUTED --------------------------------------------


class TheAnswerIsDurableAndAttributable(unittest.TestCase):
    """V-05. This record IS the safeguard, not bookkeeping (maintainer ruling, OQ-02)."""

    #: Sentinel meaning "script an ask that writes NO answer key at all", which is what an agent that
    #: was asked and stayed silent produces. Distinct from `None`, which `_record` reads as "use the
    #: default answer": conflating them is how this test first passed while asserting nothing.
    SILENT = object()

    def _record(self, answer: Any = None) -> dict[str, Any]:
        if answer is None:
            answer = {
                "answer": "not-mine",
                "reason": "the red test is in a file I never touched",
            }
        elif answer is self.SILENT:
            answer = None
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, _calls = _answer_writer(outcome, answer)
            return R.perform_gate_answer(
                suite_result=_suite(False),
                changed_files=["agent_workflows/mine.py"],
                ask=ask,
                outcome_path=outcome,
                session_id="ses-abc",
                ask_reason="the suite refused and the session is resumable",
            ).record

    def test_a_reader_can_identify_WHO_claimed_not_mine_and_WHY(self) -> None:
        rec = self._record()
        self.assertEqual("not-mine", rec["answer"])
        self.assertEqual("the red test is in a file I never touched", rec["reason"])
        self.assertEqual("ses-abc", rec["session_id"])
        self.assertTrue(rec["asked"])

    def test_the_failing_tests_the_answer_was_given_ABOUT_are_recorded(self) -> None:
        """Without these, a reviewer cannot check the claim: they would have only the agent's word."""

        rec = self._record()
        self.assertTrue(rec["failing_tests"])
        self.assertIn("test_a_thing", rec["failing_tests"][0])

    def test_the_rerun_outcome_is_recorded_beside_the_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, _calls = _answer_writer(
                outcome, {"answer": "fixed", "reason": "repaired"}
            )
            rec = R.perform_gate_answer(
                suite_result=_suite(False),
                ask=ask,
                outcome_path=outcome,
                rerun_suite=lambda: _suite(True),
                retry_budget=2,
                session_id="ses-abc",
            ).record
        self.assertEqual(1, rec["recheck_attempts"])
        self.assertIs(True, rec["recheck_passed"])
        self.assertTrue(rec["recheck_summary"])

    def test_ASKED_AND_SILENT_is_distinguishable_from_NEVER_ASKED(self) -> None:
        """The same distinction `defect_report_record` draws, and for the same reason."""

        silent = self._record(answer=self.SILENT)
        self.assertTrue(silent["asked"])
        self.assertEqual("", silent["answer"])
        self.assertTrue(silent["violation"])
        never = R.gate_answer_record(
            R.validate_gate_answer(None), asked=False, ask_reason="not warranted"
        )
        self.assertFalse(never["asked"])

    def test_the_record_is_json_serializable(self) -> None:
        json.dumps(self._record())

    def test_it_is_written_at_the_SAME_seam_as_the_integration_signal(self) -> None:
        """The location is the CONTRACT a consumer codes against, so it is asserted structurally."""

        src = inspect.getsource(R.execute_item_core)
        self.assertIn("attempt[GATE_ANSWER_RECORD_KEY]", src)
        self.assertIn("item[GATE_ANSWER_RECORD_KEY]", src)
        signal_site = src.index('item["integration_signal"] = integration.signal')
        record_site = src.index("item[GATE_ANSWER_RECORD_KEY]")
        self.assertLess(signal_site, record_site)

    def test_a_SKIPPED_ask_still_records_why(self) -> None:
        """ "Nobody asked" and "asked and refused" are different facts for a human."""

        src = inspect.getsource(R.execute_item_core)
        self.assertIn('attempt["gate_answer_skipped_reason"]', src)


# ---- E-06 / V-06: `needs-human` is visible where an operator looks --------------------------------


class NeedsHumanIsSurfacedAsADecisionRequest(unittest.TestCase):
    """V-06. A `needs-human` answer is worthless if the human never sees it."""

    def _rendered(self, items: list[dict[str, Any]]) -> str:
        return render_stream._strip_ansi(
            render_stream.render_run_summary_table(
                {"queue": items, "run_id": "run-x", "repo": "."}
            )
        )

    def _needs_human_item(self) -> dict[str, Any]:
        item = {
            "id6": "abc123",
            "status": "substantially-complete",
            "position": 1,
            "setid": "gatewire",
            "action": "execute",
        }
        render_stream.record_refusal(
            item,
            code=R.GATE_ANSWER_NEEDS_HUMAN_CODE,
            reason="the agent answered 'needs-human': two repairs are both defensible",
            remedy=R.gate_answer_needs_human_remedy(
                "abc123", "two repairs are both defensible"
            ),
        )
        return item

    def test_the_item_and_the_requested_decision_appear_in_the_operator_output(
        self,
    ) -> None:
        out = self._rendered([self._needs_human_item()])
        self.assertIn("Diagnostics / Blocked Items:", out)
        self.assertIn("abc123", out)
        self.assertIn("AWAITING HUMAN DECISION", out)
        self.assertIn("two repairs are both defensible", out)

    def test_it_is_DISTINCT_from_an_ordinary_refusal_line(self) -> None:
        """Not buried among refusals: it routes to a different person and a different next action."""

        ordinary = {
            "id6": "zzz999",
            "status": "integration-blocked",
            "position": 2,
            "setid": "gatewire",
            "action": "execute",
        }
        render_stream.record_refusal(
            ordinary,
            code="integration-blocked",
            reason="merge conflict",
            remedy="resolve it",
        )
        out = self._rendered([ordinary, self._needs_human_item()])
        lines = [line for line in out.splitlines() if line.startswith("  • ")]
        self.assertIn("AWAITING HUMAN DECISION", lines[0])
        self.assertNotIn("AWAITING HUMAN DECISION", lines[1])

    def test_the_remedy_says_DECIDE_rather_than_RERUN(self) -> None:
        """A message that reads as "this failed" gets handled by re-running, which changes nothing.

        The measured precedent is `probe_refusal_remedy`: a prohibition-shaped message gets complied
        with destructively, so a remedy must name the CONSTRUCTIVE action first.
        """

        remedy = R.gate_answer_needs_human_remedy("abc123", "which fix is correct")
        self.assertIn("DECIDE", remedy)
        self.assertIn("PRESERVED", remedy)
        self.assertIn("do NOT", remedy)

    def test_a_run_with_NO_such_answer_gains_no_spurious_line(self) -> None:
        out = self._rendered(
            [
                {
                    "id6": "ok1234",
                    "status": "executed",
                    "position": 1,
                    "setid": "gatewire",
                    "action": "execute",
                }
            ]
        )
        self.assertNotIn("Diagnostics / Blocked Items:", out)
        self.assertNotIn("AWAITING HUMAN DECISION", out)

    def test_mine_does_NOT_get_the_decision_treatment(self) -> None:
        """`mine` needs WORK, not a decision. Conflating them sends the item to the wrong person."""

        src = inspect.getsource(R.execute_item_core)
        block = src[src.index("gate_answer_asked, gate_answer_reason") :]
        self.assertIn("awaits_human_decision", block)
        self.assertNotIn("GATE_ANSWER_MINE,\n                code=", block)

    def test_the_refusal_code_has_ONE_definition_shared_by_writer_and_renderer(
        self,
    ) -> None:
        """F-4's defect class: a literal at two sites is how a reader and a writer drift apart."""

        self.assertIs(
            R.GATE_ANSWER_NEEDS_HUMAN_CODE, render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE
        )


# ---- E-07 / V-07: the question, and the SAME-SESSION follow-up on BOTH hosts ----------------------


class TheQuestionCarriesTheEvidenceItNeeds(unittest.TestCase):
    """V-07. The failing tests AND the turn's changed files must both be in front of the agent."""

    def test_the_rendered_question_shows_the_failing_tests_and_the_changed_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, calls = _answer_writer(outcome, {"answer": "mine"})
            R.perform_gate_answer(
                suite_result=_suite(False),
                changed_files=["agent_workflows/runner_shared.py", "tests/test_x.py"],
                ask=ask,
                outcome_path=outcome,
            )
        prompt = calls[0]
        self.assertIn("tests/test_unrelated.py::test_a_thing", prompt)
        self.assertIn("agent_workflows/runner_shared.py", prompt)
        self.assertIn("tests/test_x.py", prompt)

    def test_the_question_does_not_ACCUSE(self) -> None:
        """A question phrased as "what did you break" pushes an honest agent toward a false `mine`."""

        q = R.gate_answer_question(
            failing="FAILED tests/a.py::t", changed_files=["b.py"]
        )
        self.assertIn("This is a question, not an accusation", q)
        self.assertIn("commonest correct answer", q)

    def test_the_question_states_the_CONSEQUENCE_of_each_answer(self) -> None:
        q = R.gate_answer_question(failing="x", changed_files=())
        for consequence in (
            "YOUR LANE IS THEN INTEGRATED",
            "THE FULL TEST SUITE IS RE-RUN",
            "INTEGRATION IS REFUSED",
        ):
            self.assertIn(consequence, q)

    def test_the_follow_up_is_ONE_turn_per_answer_and_never_loops(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, calls = _answer_writer(outcome, None, None, None)
            R.perform_gate_answer(
                suite_result=_suite(False), ask=ask, outcome_path=outcome
            )
        self.assertEqual(1, len(calls), "silence must not be retried")

    def test_the_turn_is_CHARGED_to_the_session_exactly_once(self) -> None:
        """A re-ask consumes a turn against `max_items_per_session`, counted in ONE place."""

        counts: dict[str, int] = {}
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, _calls = _answer_writer(outcome, {"answer": "mine"})
            R.perform_gate_answer(
                suite_result=_suite(False),
                ask=ask,
                outcome_path=outcome,
                session_turn_counts=counts,
                session_id="ses-1",
            )
        self.assertEqual({"ses-1": 1}, counts)

    def test_an_isolated_lane_RECOLLECTS_before_re_reading_the_outcome(self) -> None:
        """The worker rewrites the outcome INSIDE its lane, so the driver must collect it again."""

        seen: list[str] = []
        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, _calls = _answer_writer(outcome, {"answer": "mine"})
            R.perform_gate_answer(
                suite_result=_suite(False),
                ask=ask,
                outcome_path=outcome,
                recollect=lambda: seen.append("collected"),
            )
        self.assertEqual(["collected"], seen)

    def test_a_FAILING_recollect_does_not_kill_the_turn(self) -> None:
        def boom() -> None:
            raise OSError("lane vanished")

        with tempfile.TemporaryDirectory() as temp:
            outcome = Path(temp) / "01-abc123.json"
            outcome.write_text("{}", encoding="utf-8")
            ask, _calls = _answer_writer(outcome, {"answer": "mine"})
            out = R.perform_gate_answer(
                suite_result=_suite(False),
                ask=ask,
                outcome_path=outcome,
                recollect=boom,
            )
        self.assertFalse(out.release)

    def test_a_MISSING_outcome_file_is_an_observation_and_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "nope.json"
            out = R.perform_gate_answer(
                suite_result=_suite(False),
                ask=lambda _p: (0, "s", missing, []),
                outcome_path=missing,
            )
        self.assertFalse(out.release)

    def test_BOTH_hosts_resume_their_OWN_session_flag(self) -> None:
        """A single hardcoded flag would silently fail on one host: the measured one-sided-guard class.

        Asserted on the ARGV each host actually builds, exactly as the sibling defect-re-ask test does,
        rather than on the wiring's source text.
        """

        for module, flag, absent in (
            (oc_runipd, "--session", "--conversation"),
            (agy_runipd, "--conversation", "--session"),
        ):
            with self.subTest(host=module.__name__):
                argv = self._argv(module)
                self.assertIn(flag, argv)
                self.assertEqual("ses-1", argv[argv.index(flag) + 1])
                self.assertNotIn(absent, argv)

    def _argv(self, driver: Any) -> list[str]:
        captured: dict[str, list[str]] = {}

        def fake_popen(argv: Any, **_kw: Any) -> Any:
            captured["argv"] = list(argv)
            raise RuntimeError("stop-before-launch")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
            )
            run_dir = root / "run"
            (run_dir / "sessions").mkdir(parents=True)
            prompt = root / "gate-answer.md"
            prompt.write_text("answer the gate question\n", encoding="utf-8")
            plan = repo / "plan.ipd.md"
            plan.write_text("- Id: abc123\n", encoding="utf-8")
            state = {
                "run_id": "run-x",
                "repo": str(repo),
                "set_sessions": {},
                "session_turn_counts": {},
                "options": {"opencode": "/bin/false", "agy_executable": "/bin/false"},
                "queue": [],
            }
            item = {
                "id6": "abc123",
                "setid": "gatewire",
                "position": 1,
                "action": "execute",
            }
            import subprocess as _sp

            real = _sp.Popen
            _sp.Popen = fake_popen  # type: ignore[assignment]
            try:
                if driver is oc_runipd:
                    driver.run_opencode(
                        state, run_dir, item, plan, prompt, 1, resume_session="ses-1"
                    )
                else:
                    driver.run_agy_turn(
                        state,
                        run_dir,
                        item,
                        prompt,
                        1,
                        session_id="ses-1",
                        use_continue=False,
                    )
            except Exception:
                pass
            finally:
                _sp.Popen = real  # type: ignore[assignment]
        return captured.get("argv", [])

    def test_the_wiring_reuses_the_SHIPPED_follow_up_mechanism(self) -> None:
        """No second re-ask mechanism: `resume_via_launcher` keeps the launcher a NAME.

        That matters mechanically, not stylistically: a call to `run_opencode(...)` inside the driver
        would be a THIRD launcher call site, and the pinned rule is that exactly one may omit the
        verifier-launch marker (a turn that omits it silently runs under the executor's model).
        """

        src = inspect.getsource(R.execute_item_core)
        block = src[src.index("gate_answer_asked, gate_answer_reason") :]
        self.assertIn("resume_via_launcher(", block)
        self.assertIn("raw_launcher", block)

    def test_BOTH_hosts_reach_this_wiring_through_the_ONE_shared_core(self) -> None:
        """The incident was one host; drift is where the twin hides."""

        for host, module in HOSTS:
            with self.subTest(host=host):
                self.assertIn(
                    "runner_shared.execute_item_core(",
                    Path(str(module.__file__)).read_text(encoding="utf-8"),
                )


# ---- the gate itself is UNCHANGED (the plan's stated OUT-of-scope) --------------------------------


class TheGateItselfStaysHard(unittest.TestCase):
    """OUT of scope, asserted so a later reader cannot mistake this feature for a softened gate."""

    def test_integration_is_earned_still_refuses_a_failing_suite(self) -> None:
        v = oc_runipd.integration_is_earned(
            validate=False, verify_disp=None, suite_result=_suite(False)
        )
        self.assertFalse(v.earned)
        self.assertEqual(R.INTEGRATION_REFUSED_SUITE_FAILED, v.signal)

    def test_integration_is_earned_still_refuses_a_declined_verifier(self) -> None:
        v = oc_runipd.integration_is_earned(
            validate=True, verify_disp="unverified", suite_result=_suite(True)
        )
        self.assertFalse(v.earned)

    def test_the_five_signal_names_have_ONE_definition_and_both_spellings_agree(
        self,
    ) -> None:
        """They MOVED to `runner_shared` so the shared layer could name them; nothing may re-fork them."""

        for name in (
            "INTEGRATION_EARNED_BY_VERIFIER",
            "INTEGRATION_EARNED_BY_SUITE",
            "INTEGRATION_REFUSED_VERIFIER_DECLINED",
            "INTEGRATION_REFUSED_SUITE_FAILED",
            "INTEGRATION_REFUSED_NO_SIGNAL",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    getattr(R, name),
                    getattr(oc_runipd, name),
                    "the runner's binding must be the shared definition, not a second literal",
                )
        defined_in_shared = {
            node.targets[0].id
            for node in ast.parse(
                Path(str(R.__file__)).read_text(encoding="utf-8")
            ).body
            if isinstance(node, ast.Assign)
            and node.targets
            and isinstance(node.targets[0], ast.Name)
        }
        self.assertIn("INTEGRATION_REFUSED_SUITE_FAILED", defined_in_shared)

    def test_no_bare_except_was_introduced_in_the_new_section(self) -> None:
        """A validator or a gate wrapped in a bare `except` is a gate that is OFF (`st5klo`)."""

        src = Path(str(R.__file__)).read_text(encoding="utf-8")
        start = src.index("# ---- gatewire-01 (`h5pyqa`): the WIRING")
        end = src.index("def make_integration_validation_runner")
        section = src[start:end]
        self.assertNotIn("except Exception:\n        pass", section)
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self.assertLess(
                    node.lineno,
                    src[:start].count("\n") + 1,
                    "a BARE except was added in the gate-answer section",
                )


if __name__ == "__main__":
    unittest.main()
