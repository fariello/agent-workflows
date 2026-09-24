#!/usr/bin/env python3
"""The tri-state defect report: every state, and the two cases that must NOT fire (defreport `b7xarm`).

WHAT THIS PROVES, and why each case exists rather than merely that it passes:

  * (a) FOUND with well-formed findings is used AS-IS.
  * (b) NONE-FOUND stated affirmatively is accepted with NO re-ask. THIS IS THE POINT OF THE WHOLE
    PLAN: an agent that looked and found nothing must be able to say so, and that answer must be
    DISTINGUISHABLE ON DISK from having said nothing. If a test cannot tell (b) from (c), the feature
    has not been implemented.
  * (c) ABSENT triggers EXACTLY ONE re-ask.
  * (d) A bare string where an object was expected is COERCED and the coercion is RECORDED. This is
    the MEASURED defect: across the execute-turn outcome corpus every entry agents wrote into the
    sibling list field was a bare string and none was an object, because the prompt literal showed
    `[]` and never an element. Discarding such an entry would throw away a real finding.
  * (e) A re-ask that itself yields nothing is RECORDED DURABLY. "Asked and still silent" is a fact a
    human needs and is materially different from "nobody asked".
  * (f) A turn that did no work is NOT re-asked, so a blocked item is not billed for a follow-up.
  * (g) BOTH HOSTS persist the IDENTICAL shape, so a consumer's behavior cannot depend on which
    runner executed the plan.

NO REAL MODEL TURN IS SPENT. Every host invocation is stubbed the way the existing driver tests stub
it (replace the launcher, count the calls), so the suite is deterministic and free.

NOTHING READS `.aw/records/runs/`. That tree is GITIGNORED, so a test asserting against it passes on
one machine and fails in CI (recorded by `rbftpl`, which pinned a committed fixture corpus for the
same reason). Every record here is built in `tmp_path`.
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, reporting_contract as RC
from agent_workflows import runner_shared as R

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVERS = (oc_runipd, agy_runipd)


def _effective_source(mod: Any) -> str:
    src = Path(str(mod.__file__)).read_text(encoding="utf-8")
    if "execute_item_core" in src:
        src += "\n" + inspect.getsource(R.execute_item_core)
    return src


def _outcome(**over: Any) -> dict[str, Any]:
    """A minimal agent-written outcome; `over` supplies the report under test."""

    base: dict[str, Any] = {
        "schema_version": 1,
        "disposition": "executed",
        "summary": "did the thing",
        "incomplete_requirements": [],
        "pushed": False,
    }
    base.update(over)
    return base


# ---- E-01 / V-01: the schema itself ---------------------------------------------------------------


class SchemaTests(unittest.TestCase):
    """The tri-state must be carried by an EXPLICIT VALUE, never by list emptiness."""

    def test_the_three_states_are_distinct_named_values(self) -> None:
        self.assertEqual(
            R.DEFECT_REPORT_STATES,
            (
                R.DEFECT_REPORT_FOUND,
                R.DEFECT_REPORT_NONE_FOUND,
                R.DEFECT_REPORT_ABSENT,
            ),
        )
        self.assertEqual(len(set(R.DEFECT_REPORT_STATES)), 3)

    def test_absent_is_not_reachable_by_an_empty_list(self) -> None:
        """THE DEFECT THIS CLOSES: `[]` must not be the encoding of any state.

        An affirmative none-found carries an empty `findings` list AND an explicit state, so the two
        differ in BYTES, not merely in interpretation.
        """

        none_found = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )
        absent = R.validate_defect_report(_outcome())
        self.assertEqual(none_found.state, R.DEFECT_REPORT_NONE_FOUND)
        self.assertEqual(absent.state, R.DEFECT_REPORT_ABSENT)
        self.assertFalse(none_found.needs_reask)
        self.assertTrue(absent.needs_reask)

    def test_the_key_set_is_the_written_budget(self) -> None:
        """OQ-02: JSON was accepted ON CONDITION the report stays SMALL. The budget is a contract."""

        self.assertEqual(R.DEFECT_FINDING_KEYS, ("what", "where"))
        literal = R.defect_report_schema_literal()
        parsed = json.loads("{" + literal.rstrip(",") + "}")
        report = parsed[R.DEFECT_REPORT_KEY]
        self.assertEqual(sorted(report), ["findings", "state"])
        self.assertEqual(sorted(report["findings"][0]), ["what", "where"])
        # No nesting beyond one list of small objects.
        self.assertIsInstance(report["findings"], list)
        self.assertIsInstance(report["findings"][0], dict)

    def test_the_literal_shows_a_FILLED_example_element(self) -> None:
        """The measured reason: an element shape the prompt does not SHOW is missed every time."""

        literal = R.defect_report_schema_literal()
        self.assertIn('"what":', literal)
        self.assertIn('"where":', literal)
        element = json.loads("{" + literal.rstrip(",") + "}")[R.DEFECT_REPORT_KEY][
            "findings"
        ][0]
        self.assertTrue(element["what"].strip(), "the example element must be FILLED")
        self.assertTrue(element["where"].strip())


class PromptSizeBudgetTests(unittest.TestCase):
    """OQ-02's condition, stated as a NUMBER rather than an adjective."""

    #: The execute prompt's length WITHOUT the defect report, measured on both hosts.
    #:
    #: RE-BASED by rununify Order 04 (`tx6q0h`), and the reason matters more than the number. The two
    #: hosts' `build_prompt` was de-duplicated into `runner_shared` and, by the maintainer's ruling
    #: recorded in that plan's OQ-03, the OpenCode instruction text was adopted for BOTH hosts. So the
    #: Antigravity prompt legitimately GREW (measured 6199 -> 6606 characters) because its agent now
    #: receives instructions it previously lacked, including preserving partial work through a
    #: nonterminal checkpoint and never claiming executed unless the terminal state supports it. The
    #: OpenCode figure is UNCHANGED at this HEAD, which is the evidence that the lift took oc's text
    #: rather than inventing a third variant.
    #:
    #: NOT A WEAKENING: the CEILING below is untouched, and the property this class exists to
    #: enforce (the defect report itself must stay under budget) is now measured against a
    #: same-HEAD baseline instead of a stale one. Measured cost after the change: 1137 characters on
    #: BOTH hosts, comfortably under the 1500 ceiling.
    #:
    #: RE-BASED AGAIN (backlog `q1z9gn`) for the same reason and by the same method: the shared execute
    #: prompt gained a foreground-execution instruction, so the report-free prompt legitimately grew by
    #: 623 characters on both hosts (5466 -> 6089 on oc, 5469 -> 6092 on agy). The instruction exists
    #: because an execute turn backgrounded the validation suite, polled it with a scheduled task, and
    #: ended while it was still running, producing no work and blocking three siblings
    #: (run-20260918T045802Z-2547360, item `zqs0px`).
    #:
    #: WHY RE-BASING IS THE CORRECT FIX AND NOT A DODGE: this constant is DEFINED as "the execute
    #: prompt's length WITHOUT the defect report", so it is a snapshot that MUST move whenever the
    #: surrounding prompt legitimately changes. Leaving it stale would silently attribute unrelated
    #: prompt growth to the defect report and fail this test for a reason it does not measure. The
    #: quantity actually under test is UNCHANGED: measured at this HEAD the report still costs exactly
    #: 1137 characters on both hosts, the same figure as before, against an untouched 1500 ceiling.
    #:
    #: RE-BASED AGAIN (roleadv-01 `8b9ufm`, from backlog `fvl44r`) by the same method and for the same
    #: reason: the shared execute prompt gained the LIFECYCLE-ROLE statement (394 characters, from
    #: `ipd_lifecycle.runner_owns_lifecycle_notice`, emitted only when the driver owns the transition)
    #: and its preserve-partial-work sentence was reworded (+44), so the report-free prompt legitimately
    #: grew by 438 on both hosts (6089 -> 6527 on oc, 6092 -> 6530 on agy). The statement exists because
    #: the prompt previously said NOTHING about who performs begin/finalize while its only mention of
    #: finalize presupposed the agent did, so a managed lane paid a whole turn to discover
    #: `AW-LIFECYCLE-ROLE-001` (measured: plan `03ie04`). The report cost is again EXACTLY 1137 on both
    #: hosts, which is the evidence that this re-base moves the snapshot and not the property.
    BASELINE = {"agent_workflows.oc_runipd": 6527, "agent_workflows.agy_runipd": 6530}

    #: What the report may cost. The demand plus the schema literal is ~1.2KB; the ceiling leaves
    #: room for a wording fix and no room for a fifth field.
    CEILING = 1500

    def _prompt(self, mod: Any) -> str:
        return mod.build_prompt(
            {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []},
            {"run_id": "run-x", "repo": "."},
            Path("/tmp/r"),
            Path("/tmp/p.md"),
            False,
        )

    def test_the_report_costs_less_than_its_stated_ceiling(self) -> None:
        for mod in DRIVERS:
            with self.subTest(host=mod.__name__):
                grew = len(self._prompt(mod)) - self.BASELINE[mod.__name__]
                self.assertGreater(grew, 0, "the report must actually be in the prompt")
                self.assertLessEqual(
                    grew,
                    self.CEILING,
                    f"{mod.__name__}: the defect report added {grew} characters to a "
                    f"{self.BASELINE[mod.__name__]}-character prompt, over the "
                    f"{self.CEILING} ceiling. Re-open OQ-02 rather than raising this.",
                )

    def test_both_hosts_pay_the_same_cost(self) -> None:
        grew = {
            mod.__name__: len(self._prompt(mod)) - self.BASELINE[mod.__name__]
            for mod in DRIVERS
        }
        self.assertEqual(len(set(grew.values())), 1, grew)


# ---- E-02 / E-03 / V-02 / V-03: the demand and the carrier rule -----------------------------------


class PromptDemandTests(unittest.TestCase):
    """Both directions demanded, identically on both hosts, with the contract still LAST."""

    def _prompt(self, mod: Any) -> str:
        return mod.build_prompt(
            {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []},
            {"run_id": "run-x", "repo": "."},
            Path("/tmp/r"),
            Path("/tmp/p.md"),
            False,
        )

    def test_both_hosts_carry_byte_identical_text_from_one_constant(self) -> None:
        block = R.defect_report_prompt_block()
        for mod in DRIVERS:
            self.assertIn(block, self._prompt(mod), mod.__name__)

    def test_finding_nothing_is_demanded_as_a_reportable_result(self) -> None:
        flat = " ".join(R.defect_report_prompt_block().split())
        self.assertIn("Finding NOTHING is a REPORTABLE RESULT", flat)
        self.assertIn("must state affirmatively", flat)
        self.assertIn("Omitting the report is not the same answer", flat)

    def test_what_counts_is_named_beyond_this_plans_own_requirements(self) -> None:
        flat = " ".join(R.defect_report_prompt_block().split())
        self.assertIn("beyond this plan's own unmet requirements", flat)
        self.assertIn("bug in adjacent code", flat)
        self.assertIn("gap between a spec and its implementation", flat)
        self.assertIn("design concern you had to work around", flat)

    def test_the_carrier_rule_names_the_tool_and_fences_the_spec(self) -> None:
        flat = " ".join(R.defect_report_prompt_block().split())
        self.assertIn("FILE A BACKLOG ITEM with `aw backlog new`", flat)
        self.assertIn("a spec is supporting material and is NEVER the carrier", flat)
        self.assertIn("reporting outranks filing", flat)

    def test_no_just_a_spec_judgement_is_delegated(self) -> None:
        """The maintainer explicitly chose the rule that REMOVES this judgement."""

        low = R.defect_report_prompt_block().lower()
        for forbidden in (
            "just a spec",
            "if it is only a spec",
            "decide whether a spec",
        ):
            self.assertNotIn(forbidden, low)

    def test_the_reporting_contract_is_still_the_LAST_thing_in_each_prompt(
        self,
    ) -> None:
        """The byte-equality-to-end invariant, which appending anywhere else would break."""

        for mod in DRIVERS:
            prompt = self._prompt(mod)
            start = prompt.find(RC.REPORTING_SECTION_TITLE)
            self.assertGreater(start, -1, mod.__name__)
            self.assertEqual(
                prompt[start:].strip("\n"),
                RC.contract_text().strip("\n"),
                f"{mod.__name__}: text was added AFTER the reporting contract",
            )

    def test_incomplete_requirements_is_untouched_and_still_rendered(self) -> None:
        """It has a live reader and a DISTINCT meaning; overloading it would break a display."""

        for mod in DRIVERS:
            self.assertIn('"incomplete_requirements": [],', self._prompt(mod))
        viewer = (REPO_ROOT / "agent_workflows/run_viewer.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('outcome.get("incomplete_requirements")', viewer)

    def test_prompts_are_still_pure_ascii(self) -> None:
        for mod in DRIVERS:
            bad = sorted({c for c in self._prompt(mod) if ord(c) > 127})
            self.assertEqual(bad, [], f"{mod.__name__}: {bad}")


# ---- E-04 / V-04: the validator ------------------------------------------------------------------


class ValidatorTests(unittest.TestCase):
    """Three verdicts, tolerant coercion, and NEVER an exception."""

    def test_case_a_found_with_wellformed_findings_is_used_as_is(self) -> None:
        v = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "found",
                    "findings": [{"what": "leaks a fd", "where": "mod.py:12"}],
                }
            )
        )
        self.assertEqual(v.verdict, R.DEFECT_VERDICT_VALID)
        self.assertEqual(v.state, R.DEFECT_REPORT_FOUND)
        self.assertEqual(v.findings, ({"what": "leaks a fd", "where": "mod.py:12"},))
        self.assertFalse(v.coerced)
        self.assertFalse(v.needs_reask)

    def test_case_b_none_found_is_accepted_with_no_reask(self) -> None:
        """THE CENTRAL PROPERTY: the honest affirmative answer is accepted SILENTLY."""

        v = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )
        self.assertEqual(v.verdict, R.DEFECT_VERDICT_VALID)
        self.assertEqual(v.state, R.DEFECT_REPORT_NONE_FOUND)
        self.assertEqual(v.findings, ())
        self.assertFalse(
            v.needs_reask, "an affirmative none-found must NEVER be re-asked (OQ-03)"
        )

    def test_case_c_absent_is_absent_and_names_the_violation(self) -> None:
        v = R.validate_defect_report(_outcome())
        self.assertEqual(v.verdict, R.DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS)
        self.assertEqual(v.state, R.DEFECT_REPORT_ABSENT)
        self.assertTrue(v.needs_reask)
        self.assertIn("defect_report", v.violation)
        self.assertIn("never looked", v.violation)

    def test_case_d_a_bare_string_is_COERCED_and_the_coercion_RECORDED(self) -> None:
        """The measured shape defect. Discarding the entry would lose a REAL finding."""

        v = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "found",
                    "findings": ["run_viewer mis-renders a null cost"],
                }
            )
        )
        self.assertEqual(v.verdict, R.DEFECT_VERDICT_COERCED)
        self.assertEqual(v.state, R.DEFECT_REPORT_FOUND)
        self.assertEqual(
            v.findings,
            (
                {
                    "what": "run_viewer mis-renders a null cost",
                    "where": R.DEFECT_WHERE_UNSPECIFIED,
                },
            ),
            "the finding must be KEPT, not discarded on a formatting technicality",
        )
        self.assertTrue(v.coerced, "the coercion must be RECORDED, not silent")
        self.assertTrue(any("bare string" in c for c in v.coercions), v.coercions)
        self.assertFalse(v.needs_reask, "a coerced report is usable")

    def test_an_empty_report_object_is_ambiguous_rather_than_read_as_none_found(
        self,
    ) -> None:
        """`{}` says nothing. Reading it as none-found would re-create the original defect."""

        v = R.validate_defect_report(_outcome(defect_report={}))
        self.assertEqual(v.verdict, R.DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS)
        self.assertTrue(v.needs_reask)

    def test_a_found_state_with_no_findings_is_ambiguous(self) -> None:
        v = R.validate_defect_report(
            _outcome(defect_report={"state": "found", "findings": []})
        )
        self.assertTrue(v.needs_reask)
        self.assertIn("what was found is unknown", v.violation)

    def test_findings_win_over_a_contradicting_state_label(self) -> None:
        """The findings are the evidence; the label is not."""

        v = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "none-found",
                    "findings": [{"what": "x", "where": "y"}],
                }
            )
        )
        self.assertEqual(v.state, R.DEFECT_REPORT_FOUND)
        self.assertTrue(v.coerced)

    def test_the_validator_never_raises_on_any_input(self) -> None:
        """A validator that crashes gets wrapped in a bare `except` and neutered."""

        for junk in (
            None,
            "",
            "nothing to report",
            [],
            [{"what": "a"}],
            0,
            3.5,
            True,
            {"defect_report": []},
            {"defect_report": "found a thing"},
            {"defect_report": 7},
            {"defect_report": {"state": None, "findings": None}},
            {"defect_report": {"findings": [None, {}, "", 5]}},
            {"defect_report": {"state": "FOUND", "findings": {"what": "x"}}},
        ):
            with self.subTest(junk=junk):
                v = R.validate_defect_report(junk)
                self.assertIn(v.verdict, R.DEFECT_VERDICTS)
                self.assertIn(v.state, R.DEFECT_REPORT_STATES)


# ---- E-05 / V-05: the bounded, same-session re-ask ------------------------------------------------


class ReaskPredicateTests(unittest.TestCase):
    """WHEN the follow-up is spent, including the two cases that must NOT fire."""

    ABSENT = None  # set in setUp

    def setUp(self) -> None:
        self.absent = R.validate_defect_report(_outcome())
        self.usable = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )

    def test_absent_with_a_resumable_session_is_warranted(self) -> None:
        ok, why = R.defect_reask_is_warranted(
            self.absent, disposition="executed", session_id="ses-1"
        )
        self.assertTrue(ok, why)

    def test_case_b_none_found_is_never_reasked(self) -> None:
        ok, why = R.defect_reask_is_warranted(
            self.usable, disposition="executed", session_id="ses-1"
        )
        self.assertFalse(ok)
        self.assertIn("usable", why)

    def test_case_f_a_turn_that_did_no_work_is_not_reasked(self) -> None:
        """A blocked/stopped/never-started turn must not be billed for a follow-up."""

        for disposition in sorted(R.DEFECT_REASK_SKIPPED_STATUSES):
            with self.subTest(disposition=disposition):
                ok, why = R.defect_reask_is_warranted(
                    self.absent, disposition=disposition, session_id="ses-1"
                )
                self.assertFalse(ok, disposition)
                self.assertIn("no reportable work", why)

    def test_session_rule_1_no_session_means_no_reask(self) -> None:
        """An ISOLATED turn is ALWAYS a fresh session, so there may be nothing to resume."""

        ok, why = R.defect_reask_is_warranted(
            self.absent, disposition="executed", session_id=None
        )
        self.assertFalse(ok)
        self.assertIn("no resumable session", why)

    def test_session_rule_2_a_rotated_session_cannot_be_resumed_by_accident(
        self,
    ) -> None:
        """The predicate consumes the id observed for THIS attempt, never a set-wide one."""

        src = _effective_source(oc_runipd)
        self.assertIn('reask_session = attempt.get("session_id")', src)
        agy = _effective_source(agy_runipd)
        self.assertIn('reask_session = attempt.get("session_id")', agy)

    def test_session_rule_3_the_reask_counts_against_the_rotation_budget(self) -> None:
        counts: dict[str, int] = {"ses-1": 2}
        R.perform_defect_reask(
            verdict=self.absent,
            prompt_path=Path("/tmp/does-not-matter.md"),
            outcome_path=None,
            resume=lambda _p: (0, "ses-1", Path("/tmp/l"), ["x"]),
            session_turn_counts=counts,
            session_id="ses-1",
        )
        self.assertEqual(counts["ses-1"], 3, "a re-ask consumes a turn, and is counted")

    def test_it_is_bounded_at_exactly_one(self) -> None:
        ok, why = R.defect_reask_is_warranted(
            self.absent,
            disposition="executed",
            session_id="ses-1",
            already_reasked=True,
        )
        self.assertFalse(ok)
        self.assertIn("already been spent", why)


class ReaskMessageTests(unittest.TestCase):
    def test_it_names_the_SPECIFIC_violation_not_the_original_instruction(self) -> None:
        v = R.validate_defect_report(
            _outcome(defect_report={"state": "found", "findings": []})
        )
        msg = R.defect_reask_message(v)
        self.assertIn(v.violation, msg)
        self.assertIn("WHAT WAS WRONG:", msg)
        # It must NOT be the original demand verbatim: a generic re-ask invites the same output.
        self.assertNotIn("FOR EACH FINDING, FILE A BACKLOG ITEM", msg)

    def test_it_scopes_the_follow_up_to_the_report_alone(self) -> None:
        msg = R.defect_reask_message(R.validate_defect_report(_outcome()))
        self.assertIn("REWRITING ONLY", msg)
        self.assertIn("make no further code edits, and create no commit", msg)

    def test_it_shows_both_answers(self) -> None:
        msg = R.defect_reask_message(R.validate_defect_report(_outcome()))
        self.assertIn(R.DEFECT_REPORT_NONE_FOUND, msg)
        self.assertIn('"what"', msg)


class ReaskExecutionTests(unittest.TestCase):
    """The loop is spent ONCE, and its result is re-validated from disk."""

    def _write(self, tmp: Path, payload: Any) -> Path:
        path = tmp / "01-abc123.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_case_c_exactly_one_invocation_and_the_answer_is_picked_up(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            outcome_path = self._write(tmp, _outcome())
            calls: list[Path] = []

            def resume(prompt_path: Path) -> tuple[int, str, Path, list[str]]:
                calls.append(prompt_path)
                # The agent answers this time.
                outcome_path.write_text(
                    json.dumps(
                        _outcome(
                            defect_report={
                                "state": "found",
                                "findings": [{"what": "a bug", "where": "x.py"}],
                            }
                        )
                    ),
                    encoding="utf-8",
                )
                return 0, "ses-1", tmp / "log", ["stub"]

            before = R.validate_defect_report(
                json.loads(outcome_path.read_text(encoding="utf-8"))
            )
            self.assertTrue(before.needs_reask)
            after, rc = R.perform_defect_reask(
                verdict=before,
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=resume,
            )
            self.assertEqual(
                len(calls), 1, "the re-ask must be spent EXACTLY once, never looped"
            )
            self.assertEqual(rc, 0)
            self.assertEqual(after.state, R.DEFECT_REPORT_FOUND)
            self.assertFalse(after.needs_reask)

    def test_case_e_a_fruitless_reask_is_recorded_durably(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            outcome_path = self._write(tmp, _outcome())
            calls = []

            def resume(prompt_path: Path) -> tuple[int, str, Path, list[str]]:
                calls.append(prompt_path)
                return 0, "ses-1", tmp / "log", ["stub"]  # the agent says nothing again

            before = R.validate_defect_report(
                json.loads(outcome_path.read_text(encoding="utf-8"))
            )
            after, _rc = R.perform_defect_reask(
                verdict=before,
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=resume,
            )
            self.assertEqual(len(calls), 1, "still exactly one attempt")
            self.assertTrue(after.needs_reask)
            self.assertIn(
                "re-asked once and the report is still unusable", after.violation
            )
            record = R.defect_report_record(
                before, reasked=True, reask_reason="absent", reask_verdict=after
            )
            self.assertTrue(record["reasked"])
            self.assertEqual(record["state"], R.DEFECT_REPORT_ABSENT)
            self.assertEqual(record["reask_state"], R.DEFECT_REPORT_ABSENT)
            self.assertEqual(
                record["reask_verdict"], R.DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS
            )

    def test_a_missing_or_invalid_outcome_file_is_an_observation_not_a_crash(
        self,
    ) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            bad = tmp / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            self.assertIsNone(R.read_defect_report_outcome(bad))
            self.assertIsNone(R.read_defect_report_outcome(tmp / "absent.json"))
            self.assertIsNone(R.read_defect_report_outcome(None))

    def test_a_failing_recollect_does_not_kill_the_turn(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            outcome_path = self._write(tmp, _outcome())

            def boom() -> None:
                raise RuntimeError("collection failed")

            after, _rc = R.perform_defect_reask(
                verdict=R.validate_defect_report(_outcome()),
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=lambda _p: (0, "s", tmp / "l", ["x"]),
                recollect=boom,
            )
            self.assertTrue(after.needs_reask)


class HostResumeSpellingTests(unittest.TestCase):
    """BOTH hosts' argv, so a single hardcoded flag cannot pass."""

    def _argv(self, driver: Any, **kw: Any) -> list[str]:
        import tempfile

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
            prompt = root / "reask.md"
            prompt.write_text("answer the report question\n", encoding="utf-8")
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
                "setid": "demo",
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

    def test_opencode_resumes_with_session(self) -> None:
        argv = self._argv(oc_runipd)
        self.assertIn("--session", argv)
        self.assertEqual(argv[argv.index("--session") + 1], "ses-1")

    def test_antigravity_resumes_with_conversation(self) -> None:
        argv = self._argv(agy_runipd)
        self.assertIn("--conversation", argv)
        self.assertEqual(argv[argv.index("--conversation") + 1], "ses-1")
        self.assertNotIn(
            "--session", argv, "a hardcoded oc flag would silently fail here"
        )

    def test_a_normal_turn_argv_is_unchanged_by_the_new_parameter(self) -> None:
        """`resume_session` defaults to None, so no existing turn's argv moved."""

        import inspect

        param = inspect.signature(oc_runipd.run_opencode).parameters["resume_session"]
        self.assertIsNone(param.default)


# ---- E-06 / V-06: the persisted record -----------------------------------------------------------


class PersistedRecordTests(unittest.TestCase):
    """The four facts a gate needs, and NONE-FOUND vs ABSENT distinguishable ON DISK."""

    def _record(self, report: Any = "omit", **kw: Any) -> dict[str, Any]:
        outcome = _outcome() if report == "omit" else _outcome(defect_report=report)
        return R.defect_report_record(R.validate_defect_report(outcome), **kw)

    def test_all_four_facts_are_present_and_separate(self) -> None:
        record = self._record({"state": "found", "findings": ["a bare one"]})
        self.assertEqual(
            sorted(record),
            [
                "coerced",
                "coercions",
                "findings",
                "reask_reason",
                "reask_state",
                "reask_verdict",
                "reasked",
                "state",
                "verdict",
            ],
        )
        self.assertEqual(record["state"], R.DEFECT_REPORT_FOUND)
        self.assertTrue(record["coerced"])
        self.assertTrue(record["coercions"])
        self.assertFalse(record["reasked"])

    def test_none_found_and_absent_DIFFER_on_disk(self) -> None:
        """THE PLAN'S CENTRAL PROPERTY, asserted as a byte comparison of two persisted records."""

        none_found = self._record({"state": "none-found", "findings": []})
        absent = self._record()
        found = self._record(
            {"state": "found", "findings": [{"what": "x", "where": "y"}]}
        )
        a = json.dumps(none_found, sort_keys=True)
        b = json.dumps(absent, sort_keys=True)
        c = json.dumps(found, sort_keys=True)
        self.assertNotEqual(
            a, b, "NONE-FOUND and ABSENT must be distinguishable on disk"
        )
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)
        self.assertEqual(none_found["state"], R.DEFECT_REPORT_NONE_FOUND)
        self.assertEqual(absent["state"], R.DEFECT_REPORT_ABSENT)

    def test_the_record_is_json_serializable(self) -> None:
        """It is persisted inside `state.json`, so a non-serializable value would break the run."""

        json.dumps(self._record({"state": "found", "findings": ["x"]}))
        json.dumps(self._record())

    def test_case_g_both_hosts_write_the_identical_shape_at_the_same_seam(self) -> None:
        for mod in DRIVERS:
            src = _effective_source(mod)
            self.assertIn('item["defect_report"] = record', src, mod.__name__)
            self.assertIn('attempt["defect_report"] = record', src, mod.__name__)
            self.assertTrue(
                "runner_shared.defect_report_record(" in src
                or "defect_report_record(" in src,
                mod.__name__,
            )
            self.assertIn('"event": "defect-report-recorded"', src, mod.__name__)
            # Written at the EXISTING per-item seam, beside the other results.
            seam = src.index('item["last_outcome"] = outcome')
            self.assertGreater(src.index('item["defect_report"] = record'), seam)

    def test_the_documented_location_and_shape_are_stated_for_the_consumer(
        self,
    ) -> None:
        """`rnkqrc`'s executor needs a contract to code against (F-16)."""

        doc = R.defect_report_record.__doc__ or ""
        self.assertIn('state["queue"]', doc)
        self.assertIn("state.json", doc)
        self.assertIn("GITIGNORED", doc)
        for key in (
            "state",
            "verdict",
            "findings",
            "coerced",
            "reasked",
            "reask_verdict",
        ):
            self.assertIn(key, doc)


# ==================================================================================================
# reaskscore-01 (`skn8uk`): THE RESCORE AFTER A DEFECT RE-ASK THAT COMPLETED THE WORK
#
# THE DEFECT WAS MEASURED TWICE on 2026-09-18 (`zqs0px` in `run-20260918T193638Z-2963696`, `zz5yxq` in
# `run-20260918T190723Z-2697256`): a first turn wrote no outcome, so it scored `partial`; the defect
# re-ask then resumed the same session, did the ENTIRE job, and its `recollect` wrote a complete
# outcome to exactly the path the scorer reads - and nothing rescored it. Each item landed `partial`
# with `last_outcome: null` beside a complete outcome file, and each cascaded three siblings to
# `dependency-blocked`.
#
# THOSE RUN DIRECTORIES ARE NOT AVAILABLE TO A TEST: `.aw/records/runs/` is GITIGNORED (the sibling
# `FixtureHygieneTests` below pins that this file never reads it), so the measured SHAPE is rebuilt in
# a `tmp_path` fixture instead. NO REAL MODEL TURN IS SPENT and NO REAL SUITE IS RUN: the launcher, the
# lifecycle transitions and the suite check are all stubs, exactly as the re-ask cases above stub them.
# ==================================================================================================


class RescorePredicateTests(unittest.TestCase):
    """E-01 / V-01. `rescore_is_an_improvement` is PURE, MONOTONIC and FAIL-CLOSED.

    WHY A RANK AND NOT A MEMBERSHIP TEST: the question is comparative ("is `after` better than
    `before`"), which no set test can answer. The three kinds of answer are each a case below, and the
    refusal of a DOWNGRADE is the safety property that makes this whole change unable to harm a turn
    that already succeeded.
    """

    def test_an_improvement_is_permitted(self) -> None:
        for before, after in (
            ("partial", "substantially-complete"),
            ("partial", "executed"),
            ("failed-safely", "substantially-complete"),
            ("failed-safely", "executed"),
            ("substantially-complete", "executed"),
        ):
            with self.subTest(before=before, after=after):
                self.assertTrue(R.rescore_is_an_improvement(before, after))

    def test_an_EQUAL_score_is_not_an_improvement(self) -> None:
        """So a re-ask that changed nothing rewrites nothing and emits no event."""

        for status in (
            "partial",
            "substantially-complete",
            "executed",
            "failed-safely",
        ):
            with self.subTest(status=status):
                self.assertFalse(R.rescore_is_an_improvement(status, status))

    def test_every_DOWNGRADE_is_refused(self) -> None:
        for before, after in (
            ("substantially-complete", "partial"),
            ("executed", "partial"),
            ("executed", "substantially-complete"),
            ("executed", "failed-safely"),
            ("partial", "failed-safely"),
        ):
            with self.subTest(before=before, after=after):
                self.assertFalse(R.rescore_is_an_improvement(before, after))

    def test_the_three_never_replaceable_statuses_refuse_in_BOTH_directions(
        self,
    ) -> None:
        """`merge-retry` is the one that MATTERS; the two stop dispositions are defence in depth.

        Stated as the docstring of the predicate states it, so the test does not overclaim: a re-ask
        CAN fire on a deferred item (`merge-retry` is not in `DEFECT_REASK_SKIPPED_STATUSES`), while
        `interrupted` and `unknown_outcome` both ARE in that set and so cannot be the `before` value
        today. Their rows here guard a future widening of the skip set.
        """
        from agent_workflows import runner_stop

        never = (
            R.INTEGRATION_DEFERRED_STATUS,
            runner_stop.STOPPED_DISPOSITION,
            runner_stop.FORCED_DISPOSITION,
        )
        for status in never:
            for other in (
                "partial",
                "substantially-complete",
                "executed",
                "failed-safely",
            ):
                with self.subTest(status=status, other=other):
                    self.assertFalse(R.rescore_is_an_improvement(status, other))
                    self.assertFalse(R.rescore_is_an_improvement(other, status))
        # And the two that are already skipped are named as such, so the docstring's honesty claim is
        # checkable rather than asserted.
        self.assertIn(runner_stop.STOPPED_DISPOSITION, R.DEFECT_REASK_SKIPPED_STATUSES)
        self.assertIn(runner_stop.FORCED_DISPOSITION, R.DEFECT_REASK_SKIPPED_STATUSES)
        self.assertNotIn(
            R.INTEGRATION_DEFERRED_STATUS,
            R.DEFECT_REASK_SKIPPED_STATUSES,
            "if `merge-retry` ever enters the skip set, the E-03 refusal becomes dead code and this "
            "test should be re-based deliberately rather than deleted",
        )

    def test_an_UNRECOGNIZED_status_on_either_side_refuses(self) -> None:
        """Fail closed: a disposition added elsewhere cannot silently acquire replace-ability."""

        for before, after in (
            ("partial", "a-status-nobody-ranked"),
            ("a-status-nobody-ranked", "executed"),
            (None, "executed"),
            ("partial", None),
            ("", ""),
        ):
            with self.subTest(before=before, after=after):
                self.assertFalse(R.rescore_is_an_improvement(before, after))

    def test_it_performs_no_IO_and_mutates_neither_argument(self) -> None:
        """Purity, by AST over the body plus a mutation control on the ranking table.

        The AST half is what a reader can trust: no file is opened, no event appended, no state saved.
        The table half matters because the table is module-level MUTABLE state, so a predicate that
        wrote to it would be impure in a way no argument check would notice.
        """

        func = next(
            n
            for n in ast.parse(Path(str(R.__file__)).read_text(encoding="utf-8")).body
            if isinstance(n, ast.FunctionDef) and n.name == "rescore_is_an_improvement"
        )
        body = ast.unparse(func)
        for forbidden in (
            "open(",
            "read_text",
            "write_text",
            "append_jsonl",
            "save_state",
            "unlink",
            "mkdir",
            "subprocess",
            "[",  # no subscript assignment into the rank table, and no list literal at all
        ):
            self.assertNotIn(
                forbidden,
                body.split('"""')[-1],
                f"`rescore_is_an_improvement` must stay pure (found {forbidden!r})",
            )
        before_table = dict(R.RESCORE_DISPOSITION_RANK)
        args = ["partial", "executed"]
        R.rescore_is_an_improvement(args[0], args[1])
        self.assertEqual(args, ["partial", "executed"])
        self.assertEqual(R.RESCORE_DISPOSITION_RANK, before_table)


class RescoreAfterAReaskTests(unittest.TestCase):
    """E-02..E-05 / V-02, V-04, V-05, and the OQ-02 consequence pinned for V-06.

    ONE HARNESS, MANY CASES, driving the REAL `execute_item` on a REAL git repository with a REAL
    isolated lane, so the receipt and the re-collected outcome are produced by the shipped collection
    code rather than hand-written. Only the model turn, the two lifecycle transitions, the tool-identity
    assertion, the suite check and the suite baseline are stubbed.
    """

    PLAN = (
        "# IPD: rescore fixture\n\n"
        "- Date: 2026-09-19\n"
        "- Kind: child\n"
        "- Id: prb001\n"
        "- Set: reask\n"
        "- Order: 1\n"
        "- Status: approved\n\n"
        "## Goal\n\nfixture\n"
    )

    #: A complete agent outcome: work done, report stated affirmatively. No re-ask is warranted for it.
    GOOD = {
        "schema_version": 1,
        "disposition": "executed",
        "summary": "did the whole job",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }
    #: The RE-ASK's answer in the measured case: the resumed turn did the job and reported properly.
    REASK_COMPLETE = GOOD
    #: An outcome with NO defect report, which is what makes a re-ask warranted.
    NO_REPORT_PARTIAL = {
        "schema_version": 1,
        "disposition": "partial",
        "summary": "got part way",
        "pushed": False,
    }
    #: The re-ask answering honestly that the turn is STILL partial: a rescore must not fire.
    REASK_STILL_PARTIAL = {
        "schema_version": 1,
        "disposition": "partial",
        "summary": "still only part way",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }

    def _git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
        if proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} in {repo}: {proc.stderr}")
        return proc.stdout

    def _fixture(self, root: Path):
        repo = root / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        self._git(root, "init", "-q", str(repo))
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "t")
        # The FIXTURE repository ignores exactly what the real one does, so the run directory built
        # below behaves as the live tree does without this file ever reading the live tree. The path
        # below is WRITTEN INTO the fixture, never read from this checkout; it names the same
        # GITIGNORED directory, which is why it is called out on this line for the hygiene guard.
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n",  # GITIGNORED, in the FIXTURE
            encoding="utf-8",
        )
        plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260919-reask-01-prb001-rescore-fixture.ipd.md"
        )
        plan.write_text(self.PLAN, encoding="utf-8")
        self._git(repo, "add", ".gitignore", str(plan.relative_to(repo)))
        self._git(repo, "commit", "-qm", "init")
        run_dir = repo / ".aw" / "records" / "runs" / "run-rescore"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        item = {
            "position": 1,
            "id6": "prb001",
            "setid": "reask",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-rescore",
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "selectors": ["reask"],
            "options": {
                # stop-before-launch: a stubbed launcher is installed below, and this path would fail
                # immediately if one ever were not.
                "opencode": "/bin/false",
                "agy_executable": "/bin/false",
                "model": "probe",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": True,
                "allow_dirty_base": True,
            },
        }
        return repo, run_dir, state, item

    def _suite(self, passing: bool = True):
        return oc_runipd.SuiteCheckResult(
            passing=passing,
            exit_code=0 if passing else 1,
            summary=("7081 passed in 97.10s" if passing else "1 failed, 7080 passed"),
            reason="stub",
            cwd="/primary",
            timeout_seconds=oc_runipd.SUITE_CHECK_TIMEOUT_SECONDS,
            elapsed_seconds=98.49,
            failures=(
                () if passing else ("FAILED tests/test_x.py::test_y - assert 1 == 2",)
            ),
        )

    def _drive(
        self,
        root: Path,
        *,
        first_outcome: dict[str, Any] | None,
        reask_outcome: dict[str, Any] | None,
        wrap_collect: Any = None,
        reconcile: Any = None,
    ):
        """Drive one real turn; return `(run_dir, state, item, events, gate_kwargs, launches)`.

        `first_outcome=None` reconstructs the measured trigger: the first turn writes NOTHING, so the
        turn is scored from the empty-outcome fallback. `reask_outcome` is what the resumed turn writes
        INTO ITS LANE, so the shipped `collect_lane_submissions` is what copies it and writes the
        receipt.
        """
        from agent_workflows import lane_containment

        repo, run_dir, state, item = self._fixture(root)
        launches: list[dict[str, Any]] = []
        gate_kwargs: dict[str, Any] = {}

        def _lane_write(work_dir: Any, payload: dict[str, Any]) -> None:
            lane_root = lane_containment.lane_submission_root(
                Path(work_dir), state["run_id"], item, 1
            )
            target = lane_root / "outcomes" / f"{lane_containment.item_slug(item)}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload), encoding="utf-8")

        def _launch(*args: Any, **kwargs: Any):
            launches.append(kwargs)
            payload = first_outcome if len(launches) == 1 else reask_outcome
            work_dir = kwargs.get("work_dir")
            if payload is not None and work_dir:
                _lane_write(work_dir, payload)
            return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

        def _gate(**kwargs: Any):
            """Record what the gate was handed, then REFUSE, so no merge is attempted.

            REFUSING RATHER THAN RAISING is what lets the turn run to its end and persist its state,
            which is how the durability half of V-04 is checked. Refusing rather than EARNING keeps a
            scoring test out of the finalize-and-merge machinery, where a stubbed merge would prove
            nothing. The refusal signal is deliberately `no-trust-signal` and not `suite-failed`,
            because only the latter is askable (`gate_answer_is_warranted`) and this fixture must not
            spend a follow-up turn it is not testing.
            """
            gate_kwargs.update(kwargs)
            return oc_runipd.IntegrationVerdict(
                False,
                oc_runipd.INTEGRATION_REFUSED_NO_SIGNAL,
                "refused by the fixture so no merge is attempted",
            )

        patches = [
            mock.patch.object(oc_runipd, "run_opencode", _launch),
            mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
            mock.patch.object(
                oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
            ),
            # No pre-work suite baseline: the real one starts a detached checkout and runs pytest.
            mock.patch.object(oc_runipd, "extract_suite_failures", None),
            mock.patch.object(
                oc_runipd, "run_suite_check", lambda *a, **k: self._suite(True)
            ),
            mock.patch.object(oc_runipd, "integration_is_earned", _gate),
        ]
        if wrap_collect is not None:
            patches.append(
                mock.patch.object(
                    lane_containment,
                    "collect_lane_submissions",
                    wrap_collect(lane_containment.collect_lane_submissions),
                )
            )
        if reconcile is not None:
            patches.append(
                mock.patch.object(oc_runipd, "reconcile_disposition", reconcile)
            )

        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        events_path = run_dir / "events.jsonl"
        events = (
            [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if events_path.is_file()
            else []
        )
        return run_dir, state, item, events, gate_kwargs, launches

    @staticmethod
    def _rescored(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [e for e in events if e.get("event") == "ipd-rescored"]

    # ---- V-02: the measured case, and the three negative controls ---------------------------------

    def test_the_MEASURED_case_is_rescued_instead_of_recorded_partial(self) -> None:
        """V-02. First turn writes nothing; the re-ask does the job; the item must NOT stay `partial`.

        `substantially-complete` and not `executed` is the CORRECT expectation: `reconcile_disposition`
        deliberately downgrades a self-claimed `executed` while the plan is still in `pending/`, and
        that value is inside `EXECUTION_SUCCESS_STATES`, which is what unblocks the siblings.
        """
        with tempfile.TemporaryDirectory() as temp:
            run_dir, _state, item, events, gate_kwargs, launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            from agent_workflows import lane_containment

            receipt = lane_containment.read_collection_receipt(run_dir, item, 1)
            self.assertEqual(2, len(launches), "the re-ask turn must have been spent")
            self.assertIsNotNone(receipt)
            assert receipt is not None
            self.assertIn(
                "outcome",
                receipt["collected"],
                "the recollection must have collected the outcome for the rescore to be permitted",
            )
            self.assertEqual(2, receipt["collection_runs"])
            self.assertEqual("substantially-complete", item["status"])
            self.assertIn(item["status"], oc_runipd.EXECUTION_SUCCESS_STATES)
            self.assertTrue(gate_kwargs, "the integration gate was never reached")
            self.assertEqual(1, len(self._rescored(events)))

    def _control(self, label: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), **kwargs
            )
            outcome_file = (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            )
            self.assertEqual(
                "partial",
                item["status"],
                f"{label}: the rescore must NOT have fired (outcome file present: "
                f"{outcome_file.is_file()})",
            )
            self.assertEqual([], self._rescored(events), label)
            self.assertEqual(
                2, len(launches), f"{label}: the re-ask must still be spent"
            )

    def test_control_a_a_receipt_recording_the_outcome_FAILED_refuses(self) -> None:
        """V-02(a). The outcome file EXISTS; the receipt says its collection failed. Fail closed."""

        from agent_workflows import lane_containment

        def wrap(real: Any) -> Any:
            def wrapper(**kwargs: Any) -> Any:
                receipt = real(**kwargs)
                path = lane_containment.collection_receipt_path(
                    kwargs["run_dir"], kwargs["item"], kwargs["attempt"]
                )
                data = json.loads(path.read_text(encoding="utf-8"))
                if "outcome" in (data.get("collected") or []):
                    data["collected"] = [
                        name for name in data["collected"] if name != "outcome"
                    ]
                    data["failed"] = sorted(set(data.get("failed", []) + ["outcome"]))
                    path.write_text(
                        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
                    )
                    return data
                return receipt

            return wrapper

        self._control(
            "a receipt recording the outcome collection as failed",
            first_outcome=None,
            reask_outcome=self.REASK_COMPLETE,
            wrap_collect=wrap,
        )

    def test_control_b_NO_receipt_at_all_refuses(self) -> None:
        """V-02(b). Spec `7ckptx` R2.5: absence means NOT collected and may not be inferred."""

        from agent_workflows import lane_containment

        def wrap(real: Any) -> Any:
            def wrapper(**kwargs: Any) -> Any:
                receipt = real(**kwargs)
                lane_containment.collection_receipt_path(
                    kwargs["run_dir"], kwargs["item"], kwargs["attempt"]
                ).unlink(missing_ok=True)
                return receipt

            return wrapper

        self._control(
            "no collection receipt at all",
            first_outcome=None,
            reask_outcome=self.REASK_COMPLETE,
            wrap_collect=wrap,
        )

    def test_control_c_an_ABSENT_outcome_with_a_complete_receipt_refuses(self) -> None:
        """V-02(c). THE LOAD-BEARING CONTROL: it is what proves the gate reads the right field.

        A lane that submitted NOTHING yields `status: "complete"`, `collected: []`, `failed: []`,
        because `collect_lane_submissions` sets `status` unconditionally and records a missing source
        `absent` (in neither list). So a gate written against `status`, or against `failed` being
        empty, PASSES this fixture: without this case a decorative gate would ship looking correct.
        """
        with tempfile.TemporaryDirectory() as temp:
            run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=None
            )
            from agent_workflows import lane_containment

            receipt = lane_containment.read_collection_receipt(run_dir, item, 1)
            assert receipt is not None
            self.assertEqual(
                (lane_containment.RECEIPT_COMPLETE, [], []),
                (receipt["status"], receipt["collected"], receipt["failed"]),
                "this control only means anything while the receipt really does report a complete "
                "collection of nothing",
            )
            self.assertEqual(2, len(launches))
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))

    # ---- V-03: the deferral passthrough ----------------------------------------------------------

    def test_a_deferred_item_passes_through_the_rescore_unchanged(self) -> None:
        """V-03 / E-03. `merge-retry` is a driver decision an agent's outcome may not overrule.

        THE FAKE `reconcile_disposition` IS NECESSARY AND THE REASON IS ITSELF A MEASUREMENT.
        `execute_item_core` sets `item["status"] = "running"` at dispatch, so the deferral passthrough
        inside `reconcile_disposition` (which reads `item["status"]`) cannot fire on the FIRST score of
        a live turn; a deferral can therefore only be the `before` value if the score arrives from
        somewhere else. Scripting the two calls is what makes the refusal reachable at all, and it
        reproduces precisely the hazard E-03 names: the second call runs with `item["status"]` already
        overwritten by the first, so without the refusal a deferral would be relabelled. See the
        comment above `reconcile_disposition`'s passthrough (`oc_runipd.py:6120-6132`) for why
        relabelling it destroys it.
        """
        calls: list[int] = []

        def scripted(repo, item, run_dir, exit_code, plan_repo=None):
            calls.append(exit_code)
            if len(calls) == 1:
                return R.INTEGRATION_DEFERRED_STATUS, None
            return "substantially-complete", dict(self.GOOD)

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=None,
                reask_outcome=self.REASK_COMPLETE,
                reconcile=scripted,
            )
            self.assertEqual(2, len(launches), "the re-ask must have been spent")
            self.assertEqual(
                2,
                len(calls),
                "the rescore must have reached its second `reconcile_disposition` call, or this test "
                "proves nothing about the refusal",
            )
            self.assertEqual(
                R.INTEGRATION_DEFERRED_STATUS,
                item["status"],
                "a deferred item must keep its non-terminal status: relabelling it destroys the "
                "automatic re-attempt and resurrects the cascade it exists to prevent",
            )
            self.assertEqual([], self._rescored(events))

    def test_the_deferral_refusal_is_what_holds_that_line(self) -> None:
        """V-03's negative control: with the refusal removed, the test above FAILS.

        Driven rather than described: `rescore_is_an_improvement` is replaced by a rank-only version
        that has LOST the never-replaceable list, and the same fixture is asserted to rewrite the
        deferral. The assertion that fires in the sibling test is its `item["status"]` equality.
        """
        calls: list[int] = []

        def scripted(repo, item, run_dir, exit_code, plan_repo=None):
            calls.append(exit_code)
            if len(calls) == 1:
                return R.INTEGRATION_DEFERRED_STATUS, None
            return "substantially-complete", dict(self.GOOD)

        def rank_only(before: str | None, after: str | None) -> bool:
            """The predicate MINUS its refusal list, i.e. the bug this control proves is prevented."""

            ranks = dict(R.RESCORE_DISPOSITION_RANK)
            ranks[R.INTEGRATION_DEFERRED_STATUS] = 1
            b, a = ranks.get(before or ""), ranks.get(after or "")
            return b is not None and a is not None and a > b

        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(R, "rescore_is_an_improvement", rank_only):
                _run_dir, _state, item, events, _gate, _launches = self._drive(
                    Path(temp),
                    first_outcome=None,
                    reask_outcome=self.REASK_COMPLETE,
                    reconcile=scripted,
                )
            self.assertEqual(
                "substantially-complete",
                item["status"],
                "the control itself is broken: without the refusal the deferral MUST be overwritten, "
                "otherwise the sibling test is passing for some other reason",
            )
            self.assertEqual(1, len(self._rescored(events)))

    # ---- V-04: every carrier moves together -------------------------------------------------------

    def test_all_four_fate_deciding_carriers_agree_after_a_rescore(self) -> None:
        """V-04 / E-04. `last_outcome: null` beside a collected outcome file IS the measured symptom."""

        with tempfile.TemporaryDirectory() as temp:
            run_dir, state, item, _events, _gate, _launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            attempt = item["attempts"][-1]
            collected = json.loads(
                (
                    run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("substantially-complete", item["status"])
            self.assertEqual("substantially-complete", attempt["disposition"])
            self.assertIsNotNone(
                item["last_outcome"],
                "a `None` here beside a collected outcome file is the measured symptom",
            )
            self.assertEqual(collected, item["last_outcome"])
            # And it is DURABLE, not merely in memory: the existing downstream `save_state` persisted it.
            persisted = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            entry = next(q for q in persisted["queue"] if q["id6"] == item["id6"])
            self.assertEqual("substantially-complete", entry["status"])
            self.assertEqual(collected, entry["last_outcome"])
            self.assertIs(state["queue"][0], item)

    # ---- V-05: the durable event ------------------------------------------------------------------

    def test_an_accepted_rescore_emits_exactly_one_durable_event(self) -> None:
        """V-05 / E-05. Read back FROM THE FILE: a silent status rewrite must be auditable afterwards.

        NO CLAIM IS MADE ABOUT `aw runs`: `run_viewer.py` never parses `events.jsonl` and renders no
        driver event at all (plan OQ-03), so the honest property is that the record is durable and
        greppable in the run directory.
        """
        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, _launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            rescored = self._rescored(events)
            self.assertEqual(1, len(rescored), events)
            record = rescored[0]
            self.assertEqual(item["id6"], record["id6"])
            self.assertEqual(1, record["attempt"])
            self.assertEqual("partial", record["before"])
            self.assertEqual("substantially-complete", record["after"])
            self.assertTrue(record["reason"].strip())
            self.assertTrue(record["at"].strip())
            # Emitted AFTER the defect record, so the two facts read in the order they happened.
            names = [e["event"] for e in events]
            self.assertLess(
                names.index("defect-report-recorded"), names.index("ipd-rescored")
            )

    def test_no_event_is_emitted_when_NO_reask_was_performed(self) -> None:
        """V-05's first non-acceptance path. A usable report is never re-asked, so nothing rescores."""

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), first_outcome=self.GOOD, reask_outcome=self.GOOD
            )
            self.assertEqual(1, len(launches), "no re-ask turn may be spent here")
            self.assertEqual("substantially-complete", item["status"])
            self.assertEqual([], self._rescored(events))

    def test_no_event_is_emitted_when_the_rescore_is_NOT_an_improvement(self) -> None:
        """V-05's fourth non-acceptance path: the re-ask answered honestly that it is still partial."""

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=self.NO_REPORT_PARTIAL,
                reask_outcome=self.REASK_STILL_PARTIAL,
            )
            self.assertEqual(2, len(launches), "the re-ask must have been spent")
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))

    # ---- V-06's OQ-02 consequence ----------------------------------------------------------------

    def test_a_rescued_item_reaches_the_gate_with_no_verifier_verdict_and_a_DRIVER_suite(
        self,
    ) -> None:
        """OQ-02's stated consequence, pinned so it cannot regress into "integrated on no signal".

        The rescore deliberately does NOT re-run the verifier (it sits earlier in the body), so a
        rescued item arrives with `verify_disp is None`. `integration_is_earned` then falls to its
        suite branch, and the suite result it is handed is one the DRIVER ran, never an agent claim.
        With no signal at all it refuses fail-closed, which the two control assertions below pin
        against the real predicate.
        """
        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, _events, gate_kwargs, _launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            self.assertEqual("substantially-complete", item["status"])
            self.assertFalse(gate_kwargs["validate"])
            self.assertIsNone(gate_kwargs["verify_disp"])
            self.assertTrue(gate_kwargs["suite_result"].passing)
            attempt = item["attempts"][-1]
            self.assertTrue(
                attempt["suite_check"]["passing"],
                "the driver's own suite result must be recorded on the attempt",
            )
        earned = oc_runipd.integration_is_earned(
            validate=False, verify_disp=None, suite_result=self._suite(True)
        )
        self.assertTrue(earned.earned)
        self.assertEqual(oc_runipd.INTEGRATION_EARNED_BY_SUITE, earned.signal)
        refused = oc_runipd.integration_is_earned(
            validate=False, verify_disp=None, suite_result=None
        )
        self.assertFalse(refused.earned)
        self.assertEqual(oc_runipd.INTEGRATION_REFUSED_NO_SIGNAL, refused.signal)


class RescoreSharedSeamTests(unittest.TestCase):
    """The defect was host-agnostic in the CODE, so the fix must be reached by BOTH hosts."""

    def test_both_hosts_reach_the_rescore_through_the_ONE_shared_core(self) -> None:
        for mod in DRIVERS:
            src = _effective_source(mod)
            self.assertIn("rescore_is_an_improvement(", src, mod.__name__)
            self.assertIn('"event": "ipd-rescored"', src, mod.__name__)
            self.assertIn("read_collection_receipt(", src, mod.__name__)


class FixtureHygieneTests(unittest.TestCase):
    """`.aw/records/runs/` is GITIGNORED: reading it passes on one box and fails in CI."""

    def test_this_test_file_never_reads_the_live_run_tree(self) -> None:
        src = Path(__file__).read_text(encoding="utf-8")
        occurrences = [
            line
            for line in src.splitlines()
            if ".aw/records/runs" in line and "GITIGNORED" not in line
        ]
        self.assertEqual(occurrences, [], occurrences)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
