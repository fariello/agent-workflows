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
import json
import subprocess
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, reporting_contract as RC
from agent_workflows import runner_shared as R

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVERS = (oc_runipd, agy_runipd)


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

    def test_the_schema_lives_in_ONE_module_referenced_by_both_hosts(self) -> None:
        """One schema, both hosts: a second copy of a literal is how the two silently disagree.

        RE-BASED by rununify Order 04 (`tx6q0h`). Both hosts' `build_prompt` was de-duplicated into
        `runner_shared`, so the CALL that renders the schema now lives there once instead of twice.
        The property is unchanged and the anti-inlining assertion below still covers BOTH runners, so
        neither host may grow its own copy of the literal.
        """
        shared_src = Path(str(R.__file__)).read_text(encoding="utf-8")
        self.assertIn("defect_report_schema_literal()", shared_src)
        self.assertIn("defect_report_prompt_block()", shared_src)
        for mod in DRIVERS:
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            self.assertNotIn(
                '"defect_report": {',
                src,
                f"{mod.__name__} inlines the schema literal instead of referencing it",
            )
        for mod in DRIVERS:
            tree = ast.parse(Path(str(mod.__file__)).read_text(encoding="utf-8"))
            defined = {
                n.name
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
            self.assertNotIn("validate_defect_report", defined)
            self.assertNotIn("defect_report_schema_literal", defined)
            self.assertNotIn("defect_report_prompt_block", defined)


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
    BASELINE = {"agent_workflows.oc_runipd": 5466, "agent_workflows.agy_runipd": 5469}

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

    def test_no_bare_except_was_introduced_around_the_new_code(self) -> None:
        """`except Exception: pass` is how the spec-edit announcement was silenced (`st5klo`)."""

        src = Path(str(R.__file__)).read_text(encoding="utf-8")
        start = src.index("# ---- THE DEFECT REPORT")
        section = src[start:]
        self.assertNotIn("except Exception:\n        pass", section)
        self.assertNotIn("except:  # noqa", section)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self.assertLess(
                    node.lineno,
                    src[:start].count("\n") + 1,
                    "a BARE except was added in the defect-report section",
                )


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

        src = Path(str(oc_runipd.__file__)).read_text(encoding="utf-8")
        self.assertIn('reask_session = attempt.get("session_id")', src)
        agy = Path(str(agy_runipd.__file__)).read_text(encoding="utf-8")
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

    def test_neither_host_gained_a_third_launcher_call_site(self) -> None:
        """Two callers each (executor + verifier): a third could inherit the wrong profile."""

        for mod, launcher in (
            (oc_runipd, "run_opencode"),
            (agy_runipd, "run_agy_turn"),
        ):
            tree = ast.parse(Path(str(mod.__file__)).read_text(encoding="utf-8"))
            calls = [
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == launcher
            ]
            self.assertEqual(len(calls), 2, f"{mod.__name__}: {len(calls)} callers")

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
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            self.assertIn('item["defect_report"] = record', src, mod.__name__)
            self.assertIn('attempt["defect_report"] = record', src, mod.__name__)
            self.assertIn("runner_shared.defect_report_record(", src, mod.__name__)
            self.assertIn('"event": "defect-report-recorded"', src, mod.__name__)
            # Written at the EXISTING per-item seam, beside the other results.
            seam = src.index('item["last_outcome"] = outcome')
            self.assertGreater(src.index('item["defect_report"] = record'), seam)

    def test_no_gate_logic_was_added(self) -> None:
        """`rnkqrc` owns refusing a transition; this plan only PRODUCES the record.

        Asserted by AST over the STATEMENTS of the persistence block, not by scanning prose: an
        earlier substring form matched the word "refuse" inside a COMMENT explaining an unrelated
        session rule, which is the explanation-versus-code confusion the repo's own refork guard
        records as its reason for parsing rather than grepping.
        """

        for mod in DRIVERS:
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            tree = ast.parse(src)
            func = next(
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "execute_item"
            )
            block = [
                n
                for n in ast.walk(func)
                if isinstance(n, ast.If)
                and "defect_report" in ast.unparse(n)
                and "validate_defect_report" in ast.unparse(n)
            ]
            self.assertTrue(block, f"{mod.__name__}: persistence block not found")
            body = ast.unparse(block[0])
            # No transition is refused, no status is downgraded, nothing is raised.
            for forbidden in (
                "raise DriverError",
                'item["status"] =',
                "disposition =",
                "driver_finalize(",
                "return",
            ):
                self.assertNotIn(
                    forbidden,
                    body,
                    f"{mod.__name__}: the defect-report block must add no gate logic "
                    f"(found {forbidden!r})",
                )

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

    def test_no_real_model_turn_can_be_spent(self) -> None:
        """Every host invocation here is a stub or a Popen that raises before launch.

        Asserted by AST, not by scanning this file's own text: a substring form matched the very
        assertion that names the forbidden pattern, which is the self-reference trap.
        """

        src = Path(__file__).read_text(encoding="utf-8")
        self.assertIn("stop-before-launch", src)
        self.assertIn('"opencode": "/bin/false"', src)
        # No real host binary may be invoked: every `subprocess.run` here is `git`.
        tree = ast.parse(src)
        launched = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"run", "Popen", "check_call", "check_output"}
                and node.args
            ):
                first = node.args[0]
                if isinstance(first, ast.List) and first.elts:
                    head = first.elts[0]
                    if isinstance(head, ast.Constant) and isinstance(head.value, str):
                        launched.append(head.value)
        self.assertEqual(
            sorted(set(launched)),
            ["git"],
            f"only `git` may be spawned by this suite; found {sorted(set(launched))}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
