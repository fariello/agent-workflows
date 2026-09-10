"""Anti-deletion presence guards for the `askme` workflow body's composition rules.

WHAT THESE TESTS ARE, AND WHAT THEY EMPHATICALLY ARE NOT. They assert that specific sentences
still exist in `askme.md` (and that one relocated list has exactly one home). That stops a
later agent silently stripping rules that were added to fix a measured failure. It proves
NOTHING about whether the rules work.

Nothing in the exchange these rules govern passes through a tool either party controls: the
maintainer's request and the agent's question are chat turns, not tool calls, so no test can
observe a composed prompt or a human's reply. A green run here therefore means "the rules are
still written down", never "questions are comprehensible". The only evidence of the latter is
the human's actual reply, which arrives long after any test.

This limit is stated because the defect being guarded was precisely a mechanical gate passing
a prompt that failed its only purpose (backlog `t156g1`, plan `5wtzqv`): nine mechanically
decidable exit-gate checks all passed on a prompt the maintainer could not read. Do not add a
check here that pretends to measure comprehensibility; that would repeat the error.

Shape follows `tests/test_plan_review_parity.py`, which pins the Fix Bar sentence verbatim.
Stdlib unittest only.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.support import REPO_ROOT
from tests.support import SOURCE_WORKFLOWS as WF

ASKME = WF / "askme" / "askme.md"
PRINCIPLES = REPO_ROOT / "GUIDING_PRINCIPLES.md"

# The four questions of the pre-flight self-check list relocated out of P12 (E-06).
PREFLIGHT_QUESTIONS = (
    "Can the user answer without reopening other material?",
    "Is every included fact necessary?",
    "Is the reason for asking clear?",
    "Have I avoided repeating the tool's choices?",
)


def _read(p: Path) -> str:
    """Read a file with runs of whitespace collapsed to single spaces.

    Assertions here pin the MEANING of a rule, not the line wrapping that happens to carry it.
    Collapsing whitespace keeps a harmless re-wrap (or a reflow by a later editor) from failing
    a test that has nothing to say about line breaks, while still catching deletion or
    rewording, which is all these guards claim to catch.
    """
    return re.sub(r"\s+", " ", p.read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    """Normalize an expected snippet the same way, so it can be written readably above."""
    return re.sub(r"\s+", " ", s)


class SortTestPresenceTests(unittest.TestCase):
    """E-01: Step 1 must test whether the owning artifact already states a decision rule."""

    def test_already_states_a_rule_test_present(self):
        t = _read(ASKME)
        self.assertIn(
            "TEST WHETHER THE OWNING ARTIFACT ALREADY STATES A DECISION RULE",
            t,
            "askme.md must retain the already-states-a-decision-rule sort test (E-01)",
        )
        self.assertIn(
            _norm(
                'A question whose own artifact says "do X if measurement M, else Y and record '
                'it" is YOURS the moment M is measured.'
            ),
            t,
            "askme.md must retain the rule-shape that makes the sort test actionable",
        )

    def test_measure_then_apply_corollary_present(self):
        self.assertIn(
            _norm(
                "if the artifact states a rule and you have NOT measured M, your work is to "
                "MEASURE, not to ask."
            ),
            _read(ASKME),
            "askme.md must retain the measure-then-apply corollary (E-01)",
        )

    def test_sort_test_is_confined_to_rules_decidable_once_measured(self):
        t = _read(ASKME)
        self.assertIn(
            "THE TEST FIRES ONLY ON A RULE THAT IS DECIDABLE ONCE MEASURED",
            t,
            "askme.md must confine the sort test so a lean is not mistaken for a decision (E-01)",
        )

    def test_when_in_doubt_ask_tiebreak_survives_verbatim(self):
        """MUST NOT REGRESS: E-01 edits this rule's neighbourhood."""
        self.assertIn(
            _norm(
                "WHEN IN DOUBT ABOUT A BLOCKING QUESTION, ASK. A question its own author marked "
                "`Blocking: yes` is a question someone judged load-bearing; silently downgrading "
                "it to save a prompt is the failure this workflow exists to stop."
            ),
            _read(ASKME),
            "askme.md must retain the when-in-doubt-ask tiebreak unweakened",
        )

    def test_sort_test_cites_the_tiebreak(self):
        self.assertIn(
            _norm(
                "If that leaves you genuinely unsure on a question marked blocking, the tiebreak "
                "below settles it: ASK."
            ),
            _read(ASKME),
            "the sort test must point at the when-in-doubt-ask tiebreak (E-01)",
        )


class AntiJargonPositiveHalfTests(unittest.TestCase):
    """E-02: the anti-jargon rule must not be satisfiable by deleting nouns."""

    def test_positive_obligation_present(self):
        t = _read(ASKME)
        self.assertIn(
            "THE POSITIVE HALF IS THE HALF THAT MATTERS",
            t,
            "askme.md must retain the anti-jargon rule's positive obligation (E-02)",
        )
        self.assertIn(
            "When you drop an internal name, replace it with what the thing DOES in the reader's "
            "terms.",
            t,
            "askme.md must state what to write INSTEAD of a dropped internal name",
        )

    def test_generic_container_word_named_a_violation(self):
        t = _read(ASKME)
        self.assertIn(
            "A GENERIC CONTAINER WORD IS A VIOLATION, NOT COMPLIANCE",
            t,
            "askme.md must name the generic-placeholder anti-pattern a violation (E-02)",
        )
        self.assertIn(
            _norm(
                "a pair of helpers`, `a module`, `a mechanism`, `a component`, `a system`"
            ),
            t,
            "askme.md must enumerate the generic container words that fail the rule",
        )

    def test_name_and_explain_escape_present(self):
        self.assertIn(
            "IF A THING CANNOT BE DESCRIBED FUNCTIONALLY, NAME IT AND EXPLAIN IT IN ONE CLAUSE",
            _read(ASKME),
            "askme.md must permit naming-plus-one-clause when functional description fails (E-02)",
        )

    def test_original_prohibition_not_weakened(self):
        """MUST NOT REGRESS: the ban itself survives alongside its new positive half."""
        self.assertIn(
            _norm(
                "No id6 handles as nouns, no symbol names, no finding codes, no internal "
                "vocabulary."
            ),
            _read(ASKME),
            "askme.md must retain the original anti-jargon prohibition unweakened",
        )


class SymptomBeforeChoiceTests(unittest.TestCase):
    """E-03: the malfunction must be stated before any option."""

    def test_symptom_rule_present(self):
        self.assertIn(
            "STATE THE SYMPTOM BEFORE THE CHOICE",
            _read(ASKME),
            "askme.md must retain the symptom-before-choice kernel item (E-03)",
        )

    def test_fixed_order_stated_as_part_of_the_rule(self):
        self.assertIn(
            "THE ORDER IS PART OF THE RULE, not a stylistic preference: SYMPTOM, then CHOICE, then "
            "the CONSEQUENCE",
            _read(ASKME),
            "askme.md must fix the symptom-choice-consequence order (E-03)",
        )

    def test_unstateable_symptom_means_not_yet_understood(self):
        self.assertIn(
            "IF YOU CANNOT STATE THE SYMPTOM, YOU DO NOT YET UNDERSTAND THE DECISION WELL ENOUGH "
            "TO ASK ABOUT IT.",
            _read(ASKME),
            "askme.md must state that an unstateable symptom means the decision is not understood",
        )


class DiscardAndReAskTests(unittest.TestCase):
    """E-04: incomprehension on ANY channel is a defective prompt, not an answer."""

    def test_discard_and_re_ask_rule_present(self):
        self.assertIn(
            "DISCARD AND RE-ASK IF THE ANSWER REPORTS INCOMPREHENSION",
            _read(ASKME),
            "askme.md must frame incomprehension as a defective prompt requiring discard (E-04)",
        )

    def test_free_text_channel_named_explicitly(self):
        t = _read(ASKME)
        self.assertIn(
            "THIS APPLIES ON EVERY CHANNEL, INCLUDING THE TOOL'S FREE-TEXT OPTION",
            t,
            "askme.md must name the free-text channel the maintainer actually used (E-04)",
        )
        self.assertIn(
            _norm(
                "A free-text answer reporting incomprehension is a defective prompt, not a "
                "decision."
            ),
            t,
            "askme.md must state that a free-text incomprehension report is not a decision",
        )

    def test_discarded_answer_is_never_recorded(self):
        self.assertIn(
            "A DISCARDED ANSWER IS NEVER RECORDED AS A RESOLUTION",
            _read(ASKME),
            "askme.md must forbid recording a discarded answer as a resolution (E-04)",
        )

    def test_answer_plus_complaint_distinguished_from_non_answer(self):
        self.assertIn(
            "DISTINGUISH AN ANSWER-PLUS-COMPLAINT FROM A NON-ANSWER",
            _read(ASKME),
            "askme.md must distinguish an answer-plus-complaint from a non-answer (E-04)",
        )


class NonMechanicalExitGateTests(unittest.TestCase):
    """E-05: the one non-mechanical gate item, with its limit stated."""

    def test_stranger_re_read_item_present(self):
        t = _read(ASKME)
        self.assertIn(
            "Re-read the composed prompt as a reader who has NEVER OPENED THIS REPOSITORY",
            t,
            "askme.md must retain the stranger re-read exit-gate item (E-05)",
        )
        self.assertIn(
            "the PROBLEM, the CHOICE, and the CONSEQUENCE of each option",
            t,
            "the stranger re-read item must name all three things to restate",
        )

    def test_failure_conditions_are_explicit(self):
        self.assertIn(
            _norm("It FAILS if the prompt names no symptom (only a remedy)"),
            _read(ASKME),
            "the stranger re-read item must state its failure conditions (E-05)",
        )

    def test_self_assessment_limit_stated_in_the_body(self):
        t = _read(ASKME)
        self.assertIn(
            _norm(
                "this is a SELF-ASSESSMENT by the agent that composed the prompt, so it can be "
                "ticked without being performed and it is NOT proof that the prompt is "
                "comprehensible."
            ),
            t,
            "askme.md must state plainly that the non-mechanical item is not proof (E-05)",
        )

    def test_gate_names_why_mechanical_checks_are_insufficient(self):
        self.assertIn(
            "THE FIRST ITEM IS THE ONE THAT MATTERS AND THE ONLY ONE THAT IS NOT MECHANICAL",
            _read(ASKME),
            "askme.md must explain why a wholly mechanical gate cannot gate comprehensibility",
        )

    def test_nine_pre_existing_gate_items_all_survive(self):
        """MUST NOT REGRESS: E-05 adds a tenth item and must not disturb the nine."""
        t = _read(ASKME)
        for expected in (
            "Every open question in scope is sorted into resolved-by-me, asked-and-answered",
            "Every question the human answered is recorded in its owning artifact",
            "Each prompt asked exactly ONE question and carried its own context",
            "No prompt used an id6 handle, a symbol name, or a finding code as its subject.",
            "Every option set had a recommendation label",
            "Where the human's choice depended on a number, the number was measured and included.",
            "The list of self-resolved decisions was shown to the human.",
            "No answer lives only in a gitignored run directory.",
            "No artifact belonging to another agent was edited.",
        ):
            self.assertIn(
                expected,
                t,
                "askme.md must retain pre-existing exit-gate item: %r" % expected,
            )

    def test_exit_gate_has_exactly_ten_items(self):
        t = _read(ASKME)
        gate = t.split("## Exit gate", 1)[1].split("## Reminders", 1)[0]
        self.assertEqual(
            gate.count("- [ ] "),
            10,
            "the exit gate must carry the nine original items plus exactly one new item (E-05)",
        )


class MandatedReReadRemovedTests(unittest.TestCase):
    """E-06: the mandated P12 re-read is gone; the citation stays."""

    def test_mandated_re_read_instruction_is_absent(self):
        t = _read(ASKME)
        self.assertNotIn(
            _norm("Read P12 before composing anything."),
            t,
            "askme.md must NOT mandate re-reading P12; it was measured to prevent nothing (E-06)",
        )
        self.assertIn(
            "THERE IS DELIBERATELY NO INSTRUCTION HERE TO GO AND RE-READ P12 FIRST",
            t,
            "askme.md must record WHY the mandated re-read was removed, so it is not restored",
        )

    def test_p12_citation_survives(self):
        t = _read(ASKME)
        self.assertIn(
            "The canonical composition rule is `GUIDING_PRINCIPLES.md` P12",
            t,
            "askme.md must retain a P12 citation (P8: P12 stays canonical) (E-06)",
        )
        self.assertIn(
            "Compose per `GUIDING_PRINCIPLES.md` P12 and the memory kernel above.",
            t,
            "askme.md Step 3 must still point at P12 for composition",
        )


class PreflightListHasExactlyOneHomeTests(unittest.TestCase):
    """E-06/E-07: the relocated list must live in ONE place, never two, never zero.

    OQ-01 was resolved as RELOCATE, measured against all seven P12 consumers (none references
    the list). So the workflow body is its home and `GUIDING_PRINCIPLES.md` must not restate
    it. Asserting only "it is present somewhere" would pass in the duplicated state, which is
    the exact drift (P8) this change exists to avoid.
    """

    def test_preflight_list_is_in_the_workflow_body(self):
        t = _read(ASKME)
        self.assertIn(
            "PRE-FLIGHT SELF-CHECK, silently, before you send any prompt.",
            t,
            "the pre-flight self-check list must live in the askme kernel (E-06, OQ-01 relocate)",
        )
        for q in PREFLIGHT_QUESTIONS:
            self.assertIn(q, t, "askme.md must carry pre-flight question: %r" % q)

    def test_preflight_list_is_not_restated_in_principles(self):
        t = _read(PRINCIPLES)
        for q in PREFLIGHT_QUESTIONS:
            self.assertNotIn(
                q,
                t,
                "GUIDING_PRINCIPLES.md must NOT restate the relocated pre-flight question "
                "(P8, no fourth copy): %r" % q,
            )

    def test_principles_points_at_the_new_home(self):
        self.assertIn(
            "MOVED on 2026-09-09 into the `askme` memory kernel",
            _read(PRINCIPLES),
            "P12 must point at the relocated list's new home rather than dropping it silently",
        )

    def test_principles_still_references_askme_as_the_entry_point(self):
        """MUST NOT REGRESS: E-06 edits this paragraph's neighbourhood."""
        self.assertIn(
            "The `askme` workflow is the invocable entry point that applies this principle",
            _read(PRINCIPLES),
            "P12 must retain its pointer to the askme workflow",
        )


class IndexClaimStillTrueTests(unittest.TestCase):
    """E-06: the manifest's 'references rather than restates' claim must remain accurate."""

    def test_index_narrative_claim_is_still_true(self):
        index = _read(WF / "index.md")
        self.assertIn(
            "whose composition rules it references rather than restates",
            index,
            "the manifest narrative claim is asserted here so a body edit cannot silently "
            "falsify it; askme must still REFERENCE P12's composition rules",
        )
        body = _read(ASKME)
        self.assertIn(
            _norm(
                "which this workflow references rather than restates (GUIDING_PRINCIPLES P8"
            ),
            body,
            "askme.md must still say it references P12 rather than restating it",
        )


if __name__ == "__main__":
    unittest.main()
