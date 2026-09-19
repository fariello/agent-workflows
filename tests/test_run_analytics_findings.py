#!/usr/bin/env python3
"""runanalytics Order 06 (`aflsz3`) E-09: the ranked findings contract.

HERMETICITY. Every fixture is a literal built in this file; nothing reads `.aw/records/runs/`. See the
header of `test_run_analytics_taxonomy.py` for the reasoning.

WHAT THIS SUITE IS FOR. A findings contract asserted only in a docstring is a contract nobody enforces,
so every required field has a REFUSAL test, the no-causal-language check has a CONTROL that plants a
violation, and the price-era Simpson's-paradox case ships as a golden test using the MEASURED figures
rather than a synthetic example.

MUCH OF THIS FILE IS TABLE-DRIVEN, because much of it was one shape repeated: build one finding (or one
small set of them), call one function, assert one property. Where those differed only in their DATA
they are now rows in a class-level table that evaluates EVERY row and reports all the wrong ones
together, which is the information needed to tell "the function broke" from "this one case broke".

WHAT WAS A CLASS OR A TEST PER MODE IS NOW A COLUMN: `is_stratified` in the pooled-comparison table,
the verdict mix in the refusal-fan-out table, and the finding SET (one actionable, one refusal, none at
all) in the report table. In every case the property worth asserting is that the SAME subject gets a
DIFFERENT answer in a different mode, which no single-mode test can state.

ASSERTIONS ARE ACCUMULATED, NEVER MADE INSIDE THE LOOP, so a change that moves several rows at once
reports as ONE failure naming all of them. Several tables came out STRICTER than the tests they
replaced, and each says so where it happens: the ranking rows now assert the answer is the same for
BOTH input orders (only the id-tiebreak test did), the causal-scan rows assert the EXACT match list
(the old loops asserted only truthy / empty), and the report rows apply the no-absolute-path check to
EVERY rendering rather than to one.

REFUSAL TESTS (`assertRaises`) ARE DELIBERATELY NOT TABULATED, even where they differ only in which
field was emptied. The claim they make is that construction RAISES, which has no return value to put in
a row, and the refusal message needle each one asserts is the specific sentence that teaches the author
what to fix. They stay one test per refusal, each with a one-line docstring. The same goes for tests
whose subject is a module constant rather than a produced finding.
"""

from __future__ import annotations

import unittest

from agent_workflows import run_analytics_findings as fd
from agent_workflows.run_analytics_findings import FindingRefusal, Severity
from agent_workflows.run_analytics_statistics import AnalysisResult, Verdict


def _valid_kwargs(**overrides):
    """A finding that MEETS the contract, so each refusal test can remove exactly one field."""

    kwargs = {
        "finding_id": "F-01",
        "title": "Attempts in the later price era show a higher blended token rate",
        "severity": Severity.MEDIUM,
        "affected_slice": "attempts in price era B",
        "effect_size": 1.27,
        "effect_units": "ratio of mean step cost, last decile to first",
        "sample_size": 345,
        "coverage": 0.92,
        "uncertainty": "the interval spans 1.10 to 1.44 at n=345 sessions",
        "data_quality_caveats": (
            "13 percent of spend is invisible at the attempt grain",
        ),
        "alternative_explanations": ("later work in a session may simply be harder",),
        "next_experiment": "re-run stratified by price era and compare within-era gradients",
        "evidence_sources": ("within-session-cost-gradient",),
        "recommendation": "",
    }
    kwargs.update(overrides)
    return kwargs


class ContractRefusalTests(unittest.TestCase):
    """E-09: every evidence field is REQUIRED, and a missing one is refused at construction.

    LEFT AS ONE TEST PER REFUSAL, deliberately. Every method here is an `assertRaises`: the claim is
    that construction RAISES, which produces no value to put in a table row, and each asserts the
    specific SENTENCE the refusal teaches the author with. Collapsing them into a table would either
    drop those needles or reduce them to 'a refusal happened', and 'a refusal happened' is satisfied by
    a constructor that refuses everything. The positive control that rules that out is
    `test_a_conforming_finding_is_built` below, which the whole class depends on.
    """

    def test_a_conforming_finding_is_built(self):
        """THE POSITIVE CONTROL for every refusal in this class: a contract-meeting finding is BUILT.

        Kept separate rather than merged into the refusals for the same reason it must exist at all:
        a `build_finding` that raised unconditionally would satisfy every `assertRaises` here.
        """
        finding = fd.build_finding(**_valid_kwargs())
        self.assertEqual(finding.finding_id, "F-01")
        self.assertTrue(finding.is_actionable)

    def test_NO_ALTERNATIVE_EXPLANATION_is_refused(self):
        """The most important refusal: an association with no competing account reads as a cause."""

        for empty in ((), ("",), ("   ",)):
            with self.subTest(empty=empty):
                with self.assertRaises(FindingRefusal) as ctx:
                    fd.build_finding(**_valid_kwargs(alternative_explanations=empty))
                self.assertIn("NO alternative explanation", str(ctx.exception))
                self.assertIn("reads as a cause", str(ctx.exception))

    def test_no_UNCERTAINTY_statement_is_refused(self):
        """Kept separate: an assertRaises, and the needle is the sentence that teaches the fix."""
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(uncertainty="  "))
        self.assertIn("read as precise", str(ctx.exception))

    def test_no_DATA_QUALITY_CAVEAT_is_refused(self):
        """Kept separate: an assertRaises, over a different field and a different refusal sentence."""
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(data_quality_caveats=()))
        self.assertIn("implies there are none", str(ctx.exception))

    def test_no_NEXT_EXPERIMENT_is_refused(self):
        """Kept separate: an assertRaises; the needle names why a finding needs a next step."""
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(next_experiment=""))
        self.assertIn("claim rather than a hypothesis", str(ctx.exception))

    def test_no_TITLE_is_refused(self):
        """Kept separate: an assertRaises, and the only one asserting the raise ALONE."""
        with self.assertRaises(FindingRefusal):
            fd.build_finding(**_valid_kwargs(title="   "))

    def test_a_RECOMMENDATION_on_a_cannot_determine_finding_is_refused(self):
        """Advice on insufficient evidence is the specific output the plan forbids.

        Kept separate: an assertRaises, and materially different from the field refusals above. It
        refuses a COMBINATION of two individually-legal values rather than an empty field.
        """

        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(
                **_valid_kwargs(
                    severity=Severity.CANNOT_DETERMINE,
                    recommendation="raise the retry budget",
                )
            )
        self.assertIn("advice on insufficient evidence", str(ctx.exception).lower())

    def test_every_contract_field_survives_serialization(self):
        """Kept separate: the subject is the SERIALIZED dict's key set, not a refusal.

        Every other test in this class asserts construction RAISES. This one asserts a successfully
        built finding round-trips every contract field through `to_dict`, which is the only guard that a
        field enforced at construction is not silently dropped on the way to a machine consumer.
        """
        payload = fd.build_finding(**_valid_kwargs()).to_dict()
        for key in (
            "finding_id",
            "title",
            "severity",
            "affected_slice",
            "effect_size",
            "effect_units",
            "sample_size",
            "coverage",
            "uncertainty",
            "data_quality_caveats",
            "alternative_explanations",
            "next_experiment",
            "evidence_sources",
            "recommendation",
        ):
            with self.subTest(key=key):
                self.assertIn(key, payload)


class CausalLanguageTests(unittest.TestCase):
    """E-09: no causal language, checked MECHANICALLY rather than by convention.

    ONE table replaces three loop-over-phrases tests (`the_pattern_list_catches_the_common_causal
    _constructions`, `CORRELATION_language_is_explicitly_PERMITTED`, and `the_scan_returns_the_MATCHES`).
    All three called `scan_for_causal_language` on a phrase and asked about the result, differing only
    in the phrase and in how much of the result they looked at. THE VERDICT IS THEREFORE THE DATA, and
    a permitted phrase is just a row expecting an empty match list.

    THE TABLE IS STRICTER THAN WHAT IT REPLACES, which is the argument for merging rather than merely
    shortening. The causal loop asserted only `assertTrue(matches)`, so a scanner returning the WRONG
    pattern for a phrase passed; the permitted loop asserted `== []`, so the two halves were held to
    different standards. Every row here pins the EXACT match list, which is what makes the refusal
    message trustworthy: it quotes these matches back to the author as the words to remove. The
    multi-match row (the old third test) is now just the row whose expected list has two entries.

    THE PERMITTED ROWS ARE IN THE SAME TABLE deliberately, and they carry unusual weight here. A
    scanner that matched nothing and a scanner that matched everything are opposite failures, and the
    second is the one this layer actually risks: 'because', 'due to' and 'the reason' are ordinary
    English, so an over-broad pattern would refuse honest association phrasing and push authors toward
    vaguer prose, which is the opposite of the contract's purpose.
    """

    #: (phrase, the EXACT expected match list, why this row exists)
    #:
    #: The expected lists are in the order the scanner reports them, which is what the refusal quotes
    #: back to the author, so the ORDER is part of the contract and not incidental.
    PHRASES = (
        (
            "this causes that",
            ["causes"],
            "the bare present-tense assertion of causation",
        ),
        (
            "it caused a rise",
            ["caused"],
            "the past tense, which a stem-only matcher would miss",
        ),
        (
            "because of context",
            ["because"],
            "the most common causal connective in ordinary prose, and the one most likely to be "
            "written without noticing it is a causal claim",
        ),
        (
            "due to growth",
            ["due to"],
            "a MULTI-WORD pattern, so the scanner cannot be word-split only",
        ),
        (
            "leads to higher cost",
            ["leads to"],
            "forward-directed phrasing, present tense",
        ),
        (
            "led to a retry",
            ["led to"],
            "the same construction in the past tense (irregular stem)",
        ),
        (
            "context drives cost",
            ["drives"],
            "a causal VERB rather than a connective, which a connective-only list would miss",
        ),
        (
            "driven by cache reads",
            ["driven by"],
            "the PASSIVE voice, where the causal claim is inverted",
        ),
        ("results in a rise", ["results in"], "outcome-directed phrasing"),
        (
            "responsible for the delta",
            ["responsible for"],
            "attribution phrased as responsibility, which reads as a cause while sounding like a "
            "description",
        ),
        (
            "the reason is context",
            ["the reason"],
            "a noun-phrase causal claim, with no causal verb at all",
        ),
        (
            "therefore cost rises",
            ["therefore"],
            "an INFERENCE marker: the causation is in the logical move",
        ),
        (
            "consequently slower",
            ["consequently"],
            "the same inference move in a different register",
        ),
        (
            "explains the rise",
            ["explains"],
            "explanation IS a causal claim, and is the word an analyst most naturally reaches for",
        ),
        (
            "attributable to context",
            ["attributable to"],
            "the formal-register attribution phrasing",
        ),
        (
            "cost is correlated with position",
            [],
            "PERMITTED, and the phrasing this whole layer exists to produce: naming a correlation is "
            "exactly what it is allowed to do. If this row fails the scanner has become over-broad, "
            "which pushes authors toward vaguer prose rather than honest prose",
        ),
        (
            "an association was observed",
            [],
            "PERMITTED: the passive observation phrasing, which must not be caught by the "
            "passive-voice causal pattern (`driven by`) above",
        ),
        (
            "the two co-occur",
            [],
            "PERMITTED: co-occurrence is the weakest honest claim available and must stay sayable",
        ),
        (
            "consistent with context growth",
            [],
            "PERMITTED: naming a hypothesis the data is CONSISTENT WITH, which is how a mechanism is "
            "allowed to appear in `alternative_explanations` (see the paradox finding, whose own "
            "mechanism is phrased this way and must pass its own check)",
        ),
        (
            "it causes X because Y",
            ["causes", "because"],
            "MULTIPLE MATCHES, IN ORDER. The scan RETURNS its matches rather than a bool precisely so "
            "the refusal can quote every offending word; a scanner that stopped at the first match "
            "would leave an author fixing one word at a time, re-running between each",
        ),
    )

    def test_the_scanner_returns_exactly_the_causal_matches_for_every_phrase(self):
        wrong = []
        permitted_rows_broken = 0
        for phrase, expected, why in self.PHRASES:
            got = fd.scan_for_causal_language(phrase)
            if got != expected:
                if not expected:
                    permitted_rows_broken += 1
                wrong.append(
                    f"  {phrase!r}:\n"
                    f"    - expected matches {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        vacuity = ""
        if permitted_rows_broken:
            vacuity = (
                f" {permitted_rows_broken} PERMITTED row(s) are among the failures, and that is the "
                "OVER-BROAD direction: the scanner is now refusing honest association phrasing, which "
                "pushes authors toward vaguer prose instead of more careful prose."
            )
        self.assertEqual(
            wrong,
            [],
            f"run_analytics_findings.scan_for_causal_language was wrong on {len(wrong)} of "
            f"{len(self.PHRASES)} phrases.{vacuity} SEVERAL CAUSAL ROWS FAILING TOGETHER means the "
            "pattern list was edited or reordered rather than one construction being missed, so fix "
            "the list once; ONE row failing alone means that construction is no longer recognized. "
            "FIX: the expected lists pin the exact matches IN ORDER because the refusal quotes them "
            "back to the author as the words to remove, so a right-count-wrong-word result is as bad "
            "as no detection.\n" + "\n".join(wrong),
        )

    #: (case, the field to poison, the value, the exact substring the refusal must name, why this row
    #: exists)
    POISONED_FIELDS = (
        (
            "the title",
            "title",
            "X causes Y",
            "title",
            "the headline, and the field a reader takes as the finding's claim. A lint covering ONLY "
            "the title would be the obvious under-implementation, which is why every other row exists",
        ),
        (
            "the affected slice",
            "affected_slice",
            "attempts affected because of retries",
            "affected_slice",
            "the slice description is prose too, and is where a mechanism gets smuggled in as a "
            "definition of what was measured",
        ),
        (
            "the uncertainty statement",
            "uncertainty",
            "wide, due to the small sample",
            "uncertainty",
            "the field MOST likely to contain an innocent-looking `due to`, since explaining why an "
            "interval is wide invites exactly that construction",
        ),
        (
            "the next experiment",
            "next_experiment",
            "re-run; therefore the effect will be clearer",
            "next_experiment",
            "a proposed experiment must not PRESUPPOSE its result, which is what a causal claim here "
            "amounts to",
        ),
        (
            "the recommendation",
            "recommendation",
            "reduce context, which leads to lower cost",
            "recommendation",
            "advice is where causation is most tempting, because a recommendation implies the action "
            "will produce the outcome",
        ),
        (
            "a data-quality caveat",
            "data_quality_caveats",
            ("coverage is low because logs were lost",),
            "data_quality_caveats[0]",
            "A SEQUENCE FIELD, and the refusal must name the INDEX: with a dozen caveats, being told "
            "only 'a caveat is causal' leaves the author reading all of them",
        ),
        (
            "an alternative explanation",
            "alternative_explanations",
            ("cost rises because of context",),
            "alternative_explanations[0]",
            "THE HARDEST CASE, because an alternative explanation is INHERENTLY about a mechanism and "
            "the temptation to phrase it causally is greatest. The rule still holds: it must be "
            "phrased as an account the data is consistent with. The paradox finding does exactly this "
            "and passes its own check, which is what proves the constraint is satisfiable",
        ),
    )

    def test_every_human_readable_field_is_scanned_and_named_in_the_refusal(self):
        wrong = []
        for case, field, value, needle, why in self.POISONED_FIELDS:
            problems = []
            try:
                fd.build_finding(**_valid_kwargs(**{field: value}))
            except FindingRefusal as exc:
                message = str(exc)
                if needle not in message:
                    problems.append(
                        f"the refusal does not name {needle!r}: {message!r}. An author given a "
                        "refusal that does not say WHICH field is causal has to re-read the whole "
                        "finding"
                    )
                if "causal language" not in message:
                    problems.append(
                        f"the refusal does not say it is about causal language: {message!r}"
                    )
            else:
                problems.append(
                    "NO REFUSAL AT ALL: the finding was built with causal language in this field, so "
                    "this field is not being scanned"
                )
            if problems:
                wrong.append(
                    f"  {case} (field {field!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.POISONED_FIELDS)} human-readable fields are not properly "
            "scanned for causal language. ONE FIELD FAILING means that field was left out of the "
            "scan's field list, which makes the whole check trivially evadable by moving the claim "
            "there; SEVERAL FAILING TOGETHER means the scan is no longer wired into `build_finding` "
            "at all. FIX: the two SEQUENCE rows additionally require the refusal to name the INDEX "
            "(`data_quality_caveats[0]`), because a finding may carry many and 'one of them is "
            "causal' is not actionable.\n" + "\n".join(wrong),
        )

    def test_it_is_CLEAN_on_the_association_phrasing(self):
        """Kept separate: the POSITIVE counterpart of the poisoned-field table, and it asserts a
        RETURNED FINDING rather than a refusal.

        Every row in that table expects a raise, so all of them are satisfied by a `build_finding`
        that refuses unconditionally. This is the control that rules that out, and it is deliberately
        the phrasing the contract wants authors to use rather than a neutral string.
        """

        finding = fd.build_finding(
            **_valid_kwargs(
                title="Per-step cost is associated with position in the session"
            )
        )
        self.assertEqual(
            finding.title, "Per-step cost is associated with position in the session"
        )

    def test_the_check_FIRES_on_a_planted_causal_claim(self):
        """The control V-09 requires. A checker that refused nothing looks identical to one that
        was not looking, so a planted violation must be shown to be caught.

        Kept separate: an assertRaises whose claim is about the refusal MESSAGE naming the offending
        word itself (`causes`), not merely the field. That is the plant-and-catch control V-09 demands
        by name, so it stays legible as one.
        """

        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(
                **_valid_kwargs(
                    title="Context growth causes the per-step cost to rise",
                )
            )
        message = str(ctx.exception)
        self.assertIn("causal language", message)
        self.assertIn("causes", message)
        self.assertIn("title", message)


class CannotDetermineFindingTests(unittest.TestCase):
    """E-09: insufficient evidence yields a `cannot-determine` finding, NEVER advice.

    TWO tables replace five tests. The first covers ONE constructed refusal finding: three tests each
    built the identical `cannot_determine_finding` and asserted a different property of it (the
    severity/n/no-advice group, the full-contract group, and the specific alternative), so the PROPERTY
    is the data and the fixture is shared. The second covers the fan-out from analysis results, where
    the verdict MIX is a column: two tests each passed one list to `findings_from_results` and counted,
    differing only in which verdicts were in the list.

    Why the first table beats the three: they described one object from three angles and would all fail
    together if `cannot_determine_finding` regressed, each reporting only its own fragment. A reader
    then has to reassemble what the refusal finding is supposed to look like from three separate red
    lines. As a table, the whole shape of a refusal is visible in one place and one failure lists every
    property that moved.

    THE ROWS ARE THE SAME CLAIM FROM BOTH SIDES, deliberately: a refusal must carry NO advice and NO
    effect size (or it is advice on insufficient evidence), and it must carry EVERY evidence field (or
    it is an exemption from the contract). A regression in either direction is caught, and a
    `cannot_determine_finding` that returned a bare stub would fail the second group while passing the
    first.
    """

    @staticmethod
    def _refusal(**over):
        kwargs = {
            "finding_id": "F-09",
            "analysis_name": "merge-conflict-share-and-recurrence",
            "sample_size": 3,
            "reason": "observed n=3 is below the declared minimum n=12",
        }
        kwargs.update(over)
        return fd.cannot_determine_finding(**kwargs)

    #: (case, a callable taking the finding and returning the observed value, the expected value, why
    #: this row exists)
    REFUSAL_PROPERTIES = (
        (
            "its severity",
            lambda f: f.severity,
            Severity.CANNOT_DETERMINE,
            "the severity IS the refusal. Anything else routes it into the ranked, actionable part of "
            "the report, which is where a reader looks for things to act on",
        ),
        (
            "is_actionable",
            lambda f: f.is_actionable,
            False,
            "the derived flag the report header counts with, so it must follow from the severity "
            "rather than being set independently",
        ),
        (
            "the observed sample size",
            lambda f: f.sample_size,
            3,
            "the refusal must carry the n it OBSERVED, not zero or nothing: 'cannot determine' with no "
            "number gives a reader no way to judge how far short the slice fell",
        ),
        (
            "whether the title states the observed n",
            lambda f: "n=3" in f.title,
            True,
            "the n must be visible in the ONE LINE a scanning reader sees, because that is what "
            "distinguishes 'nearly enough data' from 'almost none'",
        ),
        (
            "the recommendation",
            lambda f: f.recommendation,
            "",
            "THE LOAD-BEARING ROW: a refusal carries NO advice. Advice on insufficient evidence is the "
            "specific output this contract forbids, and `build_finding` refuses the combination "
            "outright (see ContractRefusalTests), so a refusal that carried one could not even be "
            "constructed",
        ),
        (
            "the effect size",
            lambda f: f.effect_size,
            None,
            "no effect size is REPORTED, which is the numeric half of carrying no advice: any "
            "magnitude computed from n=3 would be an artifact of the individual observations rather "
            "than a measurement, and a printed number gets quoted",
        ),
        (
            "whether it carries alternative explanations",
            lambda f: bool(f.alternative_explanations),
            True,
            "A REFUSAL IS A FINDING, NOT AN EXEMPTION from the evidence contract. This row and the "
            "three below are the opposite direction from the two above: together they forbid both a "
            "refusal that smuggles in advice AND a refusal that is a bare stub",
        ),
        (
            "whether it carries data-quality caveats",
            lambda f: bool(f.data_quality_caveats),
            True,
            "the caveat is where the shortfall itself is recorded, so a refusal with none has not "
            "said why it refused",
        ),
        (
            "whether it proposes a next experiment",
            lambda f: bool(f.next_experiment),
            True,
            "a refusal is only useful if it says what WOULD settle the question; without it the "
            "reader learns nothing they can act on and the analysis is simply missing",
        ),
        (
            "whether it states its uncertainty",
            lambda f: bool(f.uncertainty),
            True,
            "required of every finding, refusals included, because the contract has no exemptions; "
            "here it is what explains that no magnitude is reportable at this n",
        ),
        (
            "whether its alternatives include that the effect may be ABSENT",
            lambda f: "the effect may be absent entirely" in f.alternative_explanations,
            True,
            "THE ALTERNATIVE A READER MOST NEEDS AND IS MOST LIKELY TO FORGET. Without it, 'cannot "
            "determine' is read as 'probably real, just not proven yet', which is the exact "
            "misreading that turns an underpowered slice into an assumed effect. Pinned as an EXACT "
            "string because it is the sentence doing that work",
        ),
    )

    def test_a_refusal_finding_carries_no_advice_and_every_evidence_field(self):
        finding = self._refusal()
        wrong = []
        for case, observe, expected, why in self.REFUSAL_PROPERTIES:
            got = observe(finding)
            if got != expected or (expected is None and got is not None):
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"cannot_determine_finding produced the wrong refusal on {len(wrong)} of "
            f"{len(self.REFUSAL_PROPERTIES)} properties. THE ROWS RUN IN TWO DIRECTIONS and which "
            "ones failed says what broke: the `recommendation` / `effect_size` rows failing means a "
            "refusal has started carrying ADVICE, which is the forbidden output; the four `whether it "
            "carries ...` rows failing means the refusal has become a BARE STUB that skips the "
            "evidence contract. FIX: all of them failing at once means the constructor changed shape "
            "rather than any single policy changing, so read it before editing rows.\n"
            + "\n".join(wrong),
        )

    #: (case, the analysis results, how many findings must be produced, the severities they must all
    #: carry, why this row exists)
    FAN_OUT = (
        (
            "a mix of cannot-determine, computed and refused",
            (
                AnalysisResult(
                    name="a",
                    verdict=Verdict.CANNOT_DETERMINE,
                    sample_size=3,
                    reason="n",
                ),
                AnalysisResult(name="b", verdict=Verdict.COMPUTED, sample_size=50),
                AnalysisResult(
                    name="c", verdict=Verdict.REFUSED, sample_size=2, reason="coverage"
                ),
            ),
            2,
            {Severity.CANNOT_DETERMINE},
            "EVERY NON-COMPUTED RESULT BECOMES A FINDING, and BOTH non-computed verdicts are in one "
            "list on purpose: `CANNOT_DETERMINE` and `REFUSED` are different verdicts that must reach "
            "the report the same way, so a fan-out handling one and dropping the other is caught here. "
            "A silently absent refusal is indistinguishable from an oversight, which is the whole "
            "reason refusals are materialized as findings at all",
        ),
        (
            "a COMPUTED result alone",
            (AnalysisResult(name="b", verdict=Verdict.COMPUTED, sample_size=50),),
            0,
            set(),
            "A COMPUTED RESULT DOES NOT AUTO-GENERATE A FINDING. Manufacturing one finding per "
            "analysis is how a report fills with empty assertions a reader then has to triage. This is "
            "also the row that keeps the row above honest: without it, 'return a finding for every "
            "result' would pass",
        ),
        (
            "no results at all",
            (),
            0,
            set(),
            "THE BOUNDARY a run with no analyses produces. It must return empty rather than raising, "
            "because an early or filtered run legitimately has nothing to report",
        ),
    )

    def test_every_non_computed_result_becomes_exactly_one_finding(self):
        wrong = []
        for case, results, count, severities, why in self.FAN_OUT:
            findings = fd.findings_from_results(list(results))
            problems = []
            if len(findings) != count:
                problems.append(
                    f"expected {count} finding(s), got {len(findings)} "
                    f"({[(f.finding_id, f.severity) for f in findings]!r})"
                )
            got_severities = {f.severity for f in findings}
            if got_severities != severities:
                problems.append(
                    f"expected severities {severities!r}, got {got_severities!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"findings_from_results fanned out wrongly on {len(wrong)} of {len(self.FAN_OUT)} result "
            "sets. READ THE DIRECTION: producing TOO FEW means a refusal was silently dropped, and a "
            "missing refusal is indistinguishable from an analysis nobody ran, which is the failure "
            "materializing refusals exists to prevent. Producing TOO MANY means computed results are "
            "generating empty findings, which fills the report with assertions a reader must triage. "
            "FIX: the mixed row contains BOTH non-computed verdicts, so if it reports 1 rather than 2 "
            "the fan-out is handling one verdict and ignoring the other.\n"
            + "\n".join(wrong),
        )


class PriceEraParadoxTests(unittest.TestCase):
    """E-09: the MEASURED Simpson's-paradox case, shipped as a golden test.

    TWO tables replace nine tests. The first covers the golden FINDING and the BASELINE it is derived
    from: six tests each read one value out of `PRICE_ERA_PARADOX_BASELINE` or one property of
    `price_era_paradox_finding()` and asserted it, so the PROPERTY is the data. The second covers
    `detect_pooled_era_comparison`, where `is_stratified` and the eras present are COLUMNS: three tests
    called it and asked whether a warning came back, differing only in those inputs.

    Why the first table beats the six: this is a GOLDEN test over measured figures, and the figures are
    load-bearing as a SET rather than individually. A reader checking whether the numbers still describe
    reality needs them side by side; a change that re-measured the corpus would move several at once and
    the old shape reported that as several unrelated failures. Pinning them together is also what makes
    the derived effect size checkable: it is `era_b_low / era_a_high`, so the ratio row and the two
    range rows must agree or the finding is quoting arithmetic nobody can reproduce.

    THE MEASURED FIGURES ARE WRITTEN AS LITERALS, not read back from the baseline, for the rows whose
    job is to pin them. Reading `baseline[...]` to check `baseline[...]` cannot fail; the point is that
    a re-measurement must be a deliberate edit to this table with a fresh measurement date, not a silent
    drift. (`test_reporting_contract.py` records the same trap: a test interpolating the constant it
    asserts is vacuous.)

    THE STRATIFIED AND SINGLE-ERA ROWS ARE IN THE SAME TABLE as the flagged one because the detector's
    whole value is DISCRIMINATION. One that warned on every comparison would be turned off within a
    week, and one that warned on none is the state before this work existed.
    """

    #: (case, a callable taking (finding, baseline) and returning the observed value, the expected
    #: value, an absolute tolerance or None for exact equality, why this row exists)
    GOLDEN = (
        (
            "the era A blended rate range",
            lambda f, b: b["era_a_blended_usd_per_mtok_range"],
            (0.054, 0.071),
            None,
            "THE MEASURED FIGURE, written as a literal so a re-measurement is a deliberate edit here "
            "rather than a silent drift. This is the EARLIER era, when cache_read was free",
        ),
        (
            "the era B blended rate range",
            lambda f, b: b["era_b_blended_usd_per_mtok_range"],
            (0.635, 0.737),
            None,
            "the LATER era, when cache_read became billable. Roughly ten times era A, which is the "
            "apparent movement the whole finding is about",
        ),
        (
            "the cache_read share of tokens",
            lambda f, b: b["cache_read_share_of_tokens"],
            0.9862,
            1e-9,
            "THE NUMBER THAT MAKES THE PARADOX WORK: cache_read is 98.62 percent of all tokens, so a "
            "component whose rate changed dominates the blended rate almost completely. Without this "
            "figure the ninefold movement looks like a real price rise",
        ),
        (
            "the actual published rate increase",
            lambda f, b: b["actual_rate_increase"],
            0.10,
            1e-9,
            "the REAL change, 10 percent, against the ninefold apparent one. The gap between these two "
            "numbers is the entire finding, and it is why a pooled comparison across the boundary is "
            "not interpretable as a workflow measurement",
        ),
        (
            "the boundary instant",
            lambda f, b: b["boundary_instant"],
            "2026-08-29T05:38:43Z",
            None,
            "the exact instant to split on. An analyst cannot stratify by an era they cannot locate, so "
            "this timestamp is the actionable part of the whole record",
        ),
        (
            "the finding's effect size",
            lambda f, b: f.effect_size or 0.0,
            0.635 / 0.071,
            1e-4,
            "DERIVED, not independently stated: the ratio of the measured range endpoints (era B low "
            "over era A high). Written as the division so the arithmetic is visible; if this row fails "
            "while the two range rows pass, the finding is quoting a number that no longer follows "
            "from its own baseline",
        ),
        (
            "the finding's severity",
            lambda f, b: f.severity,
            Severity.HIGH,
            None,
            "HIGH, because an analyst who pools across this boundary will report a ninefold cost "
            "regression that did not happen. The severity is what puts it at the top of the ranking, "
            "where it is seen before the comparison is made",
        ),
        (
            "whether the title names the apparent ninefold rise",
            lambda f, b: "ninefold" in f.title,
            True,
            None,
            "THE WHOLE POINT, and it must be in the TITLE rather than the body: the apparent movement "
            "and the real rate change differ by about 90x, and a reader who only scans headlines is "
            "exactly the reader who would otherwise quote the ninefold figure",
        ),
        (
            "whether the title names the real 10 percent change",
            lambda f, b: "10 percent" in f.title,
            True,
            None,
            "the other half of the same sentence. Naming only the apparent rise would make the "
            "headline itself the misleading claim the finding exists to prevent",
        ),
        (
            "whether the mechanism appears in the alternatives",
            lambda f, b: (
                "cache_read rate moved from free to billable"
                in " ".join(f.alternative_explanations)
            ),
            True,
            None,
            "THE MECHANISM IS CAUSAL, so it may not be asserted as the finding's claim; it belongs in "
            "`alternative_explanations` as one account among others. This is the no-causal-language "
            "constraint applied to the paradox finding ITSELF, which is what proves the constraint is "
            "satisfiable rather than merely imposed on others",
        ),
        (
            "whether the alternatives quote the cache_read share",
            lambda f, b: "98.62%" in " ".join(f.alternative_explanations),
            True,
            None,
            "the mechanism is not credible without the share: 'a rate changed' explains nothing until "
            "you know that rate covers 98.62 percent of the tokens",
        ),
        (
            "how many competing accounts are offered",
            lambda f, b: len(f.alternative_explanations),
            3,
            None,
            "THREE, so the schedule change is not presented as the only possible account. An exact "
            "count rather than a minimum, because dropping to one makes a competing-accounts list into "
            "an explanation, which is the causal claim this layer may not make",
        ),
        (
            "whether the alternatives include a workflow-behavior account",
            lambda f, b: "workflow behavior" in " ".join(f.alternative_explanations),
            True,
            None,
            "the rival account that would produce the SAME blended movement with no rate change at "
            "all (more or fewer cache reads per unit of work), and is not separable without "
            "stratifying",
        ),
        (
            "whether the alternatives include a model-mix account",
            lambda f, b: "mix of models" in " ".join(f.alternative_explanations),
            True,
            None,
            "the third account: a changed mix across the boundary moves a blended rate while neither "
            "the rates nor the behavior changed. Together with the two above it is what makes this a "
            "competing-accounts list rather than a stated cause",
        ),
        (
            "the baseline's provenance label",
            lambda f, b: b["provenance"],
            "review-time-snapshot",
            None,
            "THE FIGURES ARE A SNAPSHOT, LABELED AS ONE. They were measured over a corpus that grows "
            "with every run, so presenting them as current would make this golden test a source of "
            "stale claims rather than a guard against them",
        ),
        (
            "the baseline's is_current flag",
            lambda f, b: b["is_current"],
            False,
            None,
            "the machine-readable half of the same admission, for a consumer that checks the flag "
            "rather than reading the prose label",
        ),
        (
            "whether the caveats tell a citer to re-measure",
            lambda f, b: "re-measure" in " ".join(f.data_quality_caveats),
            True,
            None,
            "the label is not enough: the finding must tell anyone about to CITE these numbers what to "
            "do instead, which is re-measure",
        ),
        (
            "whether the caveats carry the measurement date",
            lambda f, b: "2026-09-08" in " ".join(f.data_quality_caveats),
            True,
            None,
            "a reader cannot judge how stale a snapshot is without its date, so the date travels with "
            "the caveat rather than living only in the baseline dict",
        ),
    )

    def test_the_golden_finding_and_its_baseline_carry_the_measured_figures(self):
        finding = fd.price_era_paradox_finding()
        baseline = fd.PRICE_ERA_PARADOX_BASELINE
        wrong = []
        for case, observe, expected, tolerance, why in self.GOLDEN:
            got = observe(finding, baseline)
            if tolerance is None:
                ok = got == expected and type(got) is type(expected)
            else:
                ok = isinstance(got, (int, float)) and abs(got - expected) <= tolerance
            if not ok:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected!r}"
                    + (f" (within {tolerance})" if tolerance else "")
                    + f", got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the price-era golden finding is wrong on {len(wrong)} of {len(self.GOLDEN)} properties. "
            "SEVERAL FIGURE ROWS FAILING TOGETHER almost certainly means the corpus was RE-MEASURED, "
            "which is legitimate: update these literals AND the measurement date in the caveat, in one "
            "deliberate edit, so the snapshot stays internally consistent. Do NOT relax the rows to "
            "read the baseline back instead of pinning literals, which makes the test vacuous. FIX: if "
            "the effect-size row failed while the two range rows passed, the finding is quoting "
            "arithmetic that no longer follows from its own baseline (it must be era B low over era A "
            "high), and THAT is a defect rather than a re-measurement.\n"
            + "\n".join(wrong),
        )

    #: (case, the eras present, is_stratified, substrings the warning must contain, or None meaning
    #: NO warning at all, why this row exists)
    POOLING = (
        (
            "two real eras, NOT stratified",
            ["era-a", "era-b"],
            False,
            (
                "SIMPSON'S-PARADOX HAZARD",
                "era-a, era-b",
                "9-fold",
                "10%",
                "Stratify by price era",
            ),
            "THE HAZARD ITSELF. The warning must NAME the eras being pooled, state BOTH figures (the "
            "9-fold apparent movement and the 10% real one), and say what to do instead, because a "
            "warning that only says 'hazard' gets ignored and one that omits the remedy gets "
            "rediscovered",
        ),
        (
            "two real eras, STRATIFIED",
            ["era-a", "era-b"],
            True,
            None,
            "THE COLUMN THAT MAKES THIS A TABLE: the SAME two eras, and the answer flips. Stratifying "
            "is the prescribed remedy, so warning anyway would punish the correct behavior and train "
            "analysts to suppress the check. Either half alone is satisfiable by a constant",
        ),
        (
            "a single era",
            ["era-b"],
            False,
            None,
            "NOTHING TO CONFOUND when only one era is present: a within-era comparison cannot mix two "
            "pricing schedules. Without this row the detector could warn on every comparison, which is "
            "the noise failure",
        ),
        (
            "one real era plus `unknown`",
            ["era-b", "unknown"],
            False,
            None,
            "`unknown` IS NOT AN ERA, and this is the subtle row: naively counting two distinct labels "
            "as two eras would warn here. An unclassifiable bucket is a coverage gap to report "
            "elsewhere, not a second pricing schedule to stratify by",
        ),
        (
            "no eras at all",
            [],
            False,
            None,
            "THE BOUNDARY an empty or filtered corpus produces. It must return no warning rather than "
            "raising, because a comparison over nothing is vacuous rather than hazardous",
        ),
    )

    def test_a_pooled_era_comparison_is_flagged_and_a_stratified_one_is_not(self):
        wrong = []
        clean_rows_broken = 0
        for case, eras, stratified, needles, why in self.POOLING:
            warning = fd.detect_pooled_era_comparison(
                eras_present=list(eras), is_stratified=stratified
            )
            problems = []
            if needles is None:
                if warning:
                    clean_rows_broken += 1
                    problems.append(f"expected NO warning, got {warning!r}")
            else:
                missing = [n for n in needles if n not in warning]
                if missing:
                    problems.append(
                        f"the warning omits {missing!r}; it was "
                        f"{warning or 'EMPTY (no warning at all)'}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (eras {list(eras)!r}, is_stratified={stratified}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if clean_rows_broken:
            vacuity = (
                f" {clean_rows_broken} row(s) that must NOT warn are among the failures, which is the "
                "NOISE direction: a detector that warns on every comparison, including the stratified "
                "one it prescribes, gets switched off."
            )
        self.assertEqual(
            wrong,
            [],
            f"detect_pooled_era_comparison answered wrongly for {len(wrong)} of {len(self.POOLING)} "
            f"comparisons.{vacuity} READ WHICH DIRECTION FAILED. If the FLAGGED row went silent, "
            "nothing now stops an analyst reporting a ninefold cost regression that did not happen, "
            "which is the measured incident behind this whole finding. If a CLEAN row started warning, "
            "note the `unknown` row is the one most likely to break, because treating an unclassifiable "
            "bucket as a second era is the natural implementation mistake. FIX: the two-era rows differ "
            "ONLY in `is_stratified`, so if both moved together the era counting broke rather than the "
            "stratification check.\n" + "\n".join(wrong),
        )

    def test_the_paradox_finding_passes_its_own_causal_language_check(self):
        """Kept separate: the assertion is the ABSENCE OF A RAISE, which has no value to put in a row.

        The golden table asserts the mechanism is present in `alternative_explanations`; this asserts
        the whole finding survives `assert_no_causal_language`. That matters precisely because this
        finding's subject IS a mechanism: if the contract could not be met here it would be a rule that
        forbids the honest case, so this is the existence proof that it is satisfiable.
        """

        fd.assert_no_causal_language(fd.price_era_paradox_finding())


class RankingStabilityTests(unittest.TestCase):
    """E-09: ranking is DETERMINISTIC and TOTAL, or two runs disagree about what matters.

    ONE table replaces six tests. Each built two findings, called `rank_findings`, and asserted the
    resulting id order, differing only in which sort key the two findings disagreed on. THE SORT KEY IS
    THEREFORE THE DATA, and expressing it as rows makes the key PRECEDENCE readable as a list: severity,
    then effect magnitude, then coverage, then id.

    THE TABLE IS STRICTER THAN WHAT IT REPLACED, in two ways that both come from merging. FIRST, every
    row is now ranked in BOTH input orders and the two must agree; only the id-tiebreak test did that
    before, so a comparator accidentally depending on input sequence passed the other four. SECOND,
    every row is ranked FIVE TIMES and must give the same answer, which absorbs the separate
    repeated-calls stability test and applies it to every key instead of to one three-element list.
    Neither addition needed a new fixture: they are properties of the SAME call, which is exactly what a
    table can assert cheaply and a test-per-case cannot.

    Why this matters beyond tidiness: a ranking that is not reproducible is not evidence. If two runs
    over the same findings disagree about what is at the top, the report cannot be cited, and the
    failure is silent because each individual run looks perfectly plausible.
    """

    def _finding(self, finding_id, severity, effect, coverage=0.5):
        return fd.build_finding(
            **_valid_kwargs(
                finding_id=finding_id,
                severity=severity,
                effect_size=effect,
                coverage=coverage,
            )
        )

    def _refusal(self, finding_id):
        return fd.cannot_determine_finding(
            finding_id=finding_id, analysis_name="x", sample_size=3, reason="n"
        )

    #: (case, a callable returning the findings to rank, the expected id order, why this row exists)
    #:
    #: The findings are built by a callable rather than stored directly so each row gets fresh objects
    #: and the repeated-ranking check below cannot be satisfied by mutation.
    ORDERINGS = (
        (
            "a LOW with a huge effect against a HIGH with a tiny one",
            lambda s: [
                s._finding("F-02", Severity.LOW, 100.0),
                s._finding("F-01", Severity.HIGH, 0.1),
            ],
            ["F-01", "F-02"],
            "SEVERITY OUTRANKS EFFECT SIZE, and the numbers are deliberately extreme (100.0 against "
            "0.1) so the row cannot pass by accident. Severity encodes consequence while effect size "
            "encodes magnitude, and a large movement in something that does not matter must not "
            "displace a small movement in something that does",
        ),
        (
            "two HIGHs differing only in effect size",
            lambda s: [
                s._finding("F-01", Severity.HIGH, 1.0),
                s._finding("F-02", Severity.HIGH, 9.0),
            ],
            ["F-02", "F-01"],
            "WITHIN a severity, the larger effect comes first. This is the second key, and it is what "
            "makes the ordering useful rather than merely grouped: a reader working down a severity "
            "band should meet the biggest movement first",
        ),
        (
            "a NEGATIVE effect against a smaller positive one",
            lambda s: [
                s._finding("F-01", Severity.HIGH, 1.0),
                s._finding("F-02", Severity.HIGH, -9.0),
            ],
            ["F-02", "F-01"],
            "MAGNITUDE, NOT SIGNED VALUE. A cost that halved is as interesting as one that doubled, and "
            "a comparator sorting on the raw number would bury every improvement at the bottom where "
            "nobody reads",
        ),
        (
            "two HIGHs tied on effect, differing in coverage",
            lambda s: [
                s._finding("F-01", Severity.HIGH, 5.0, coverage=0.2),
                s._finding("F-02", Severity.HIGH, 5.0, coverage=0.9),
            ],
            ["F-02", "F-01"],
            "COVERAGE BREAKS AN EFFECT TIE, higher first: the same measured effect over 90 percent of "
            "the data is better evidence than over 20 percent, so the better-supported finding is what "
            "a reader should meet first",
        ),
        (
            "two findings identical on every key except their ids",
            lambda s: [
                s._finding("F-AAA", Severity.HIGH, 5.0, coverage=0.5),
                s._finding("F-BBB", Severity.HIGH, 5.0, coverage=0.5),
            ],
            ["F-AAA", "F-BBB"],
            "THE FINAL TIEBREAK, and the row the whole class is named for: without it, findings equal "
            "on every other key fall back to INPUT SEQUENCE, and a ranking that is not reproducible is "
            "not evidence. Note EVERY row here is checked in both input orders, so this property is "
            "now asserted across the whole table rather than only on this fixture",
        ),
        (
            "a cannot-determine against the lowest actionable severity",
            lambda s: [
                s._refusal("F-99"),
                s._finding("F-01", Severity.INFO, 0.01),
            ],
            ["F-01", "F-99"],
            "A REFUSAL RANKS LAST BUT STILL APPEARS, which is two claims at once and both matter. It "
            "must not crowd the top, because it is not an opportunity to act on; and it must not be "
            "DROPPED, because a silently absent refusal is indistinguishable from an analysis nobody "
            "ran. It is set against `INFO` with a near-zero effect, the weakest actionable finding "
            "available, so the row proves the refusal sorts below even that",
        ),
        (
            "a three-element mix of severities and a refusal",
            lambda s: [
                s._finding("F-01", Severity.HIGH, 5.0),
                s._finding("F-02", Severity.MEDIUM, 5.0),
                s._refusal("F-03"),
            ],
            ["F-01", "F-02", "F-03"],
            "MORE THAN A PAIR, because a comparator can be right on every two-element case and still "
            "produce a non-transitive order on three. This is also the fixture the old separate "
            "stability test used, and the repeated-ranking check below now applies to it and to every "
            "other row",
        ),
    )

    def test_the_ranking_keys_hold_in_precedence_and_do_not_depend_on_input_order(self):
        wrong = []
        for case, build, expected, why in self.ORDERINGS:
            findings = build(self)
            problems = []
            forward = [f.finding_id for f in fd.rank_findings(findings)]
            if forward != expected:
                problems.append(f"expected order {expected!r}, got {forward!r}")
            reverse = [f.finding_id for f in fd.rank_findings(list(reversed(findings)))]
            if reverse != forward:
                problems.append(
                    f"INPUT ORDER CHANGED THE RANKING: {forward!r} forward versus {reverse!r} "
                    "reversed. A ranking that depends on input sequence is not reproducible, so the "
                    "report cannot be cited"
                )
            repeats = {
                tuple(f.finding_id for f in fd.rank_findings(findings))
                for _ in range(5)
            }
            if len(repeats) != 1:
                problems.append(
                    f"REPEATED CALLS DISAGREED: five rankings of the same list produced {repeats!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"rank_findings was wrong on {len(wrong)} of {len(self.ORDERINGS)} orderings. THE ROWS ARE "
            "IN KEY PRECEDENCE ORDER (severity, effect magnitude, coverage, id), so READ THE FIRST "
            "FAILING ROW: a break in an earlier key makes every later row's fixture ambiguous, since "
            "those rows deliberately tie on the earlier keys to isolate the later one. SEVERAL ROWS "
            "FAILING TOGETHER usually means the sort key tuple was reordered rather than four "
            "comparisons breaking. FIX: an INPUT ORDER or REPEATED CALL failure is the worst kind and "
            "is not a tie-break detail: two runs over the same findings would then disagree about what "
            "matters most, and each run looks plausible on its own, so nothing surfaces the "
            "disagreement.\n" + "\n".join(wrong),
        )

    def test_the_severity_order_covers_EVERY_severity_so_ranking_is_total(self):
        """Kept separate: the subject is a MODULE CONSTANT's completeness, not any ranking result.

        No fixture can state this. A severity missing from `_SEVERITY_ORDER` makes the comparison
        PARTIAL, so findings carrying it would sort by whatever the lookup fell back to, and the table
        above would keep passing as long as its rows happened to avoid that severity. Asserted against
        `set(Severity)` rather than a literal list so a newly added severity fails here rather than
        silently ranking last.
        """
        self.assertEqual(set(fd._SEVERITY_ORDER), set(Severity))


class ReportTests(unittest.TestCase):
    """The pasteable report V-09 requires: every contract field, on every finding.

    ONE table replaces five tests. Each called `format_findings_report` on a finding set and asserted
    some substrings were present, differing only in the SET (one actionable plus one refusal, a refusal
    alone, none at all) and in which substrings mattered. THE FINDING SET IS THEREFORE A COLUMN, and
    that is what turns five anecdotes into a claim about the renderer: the report has to be correct for
    every mix, and the mixes are where it breaks (an empty set divides by zero, a refusal has no effect
    size to print).

    THE TABLE IS STRICTER THAN WHAT IT REPLACED: the no-absolute-path check ran on ONE rendering before
    and now runs on EVERY row. That check is the one worth generalizing, because a leaked home directory
    or `.aw/records/runs` path in a report a maintainer pastes into an issue is a privacy problem rather
    than a formatting problem, and the finding set that leaks it is exactly the one nobody thought to
    test. It is asserted here IN ADDITION to the repository's leak-sanitizer, not instead of it: this
    catches the report builder specifically, at the point where a path would enter.

    THE EMPTY-SET ROW IS IN THE SAME TABLE rather than being a smoke test: a renderer that produced
    plausible text for populated sets and crashed on the empty one would pass every other row, and a
    run with no findings is a completely ordinary outcome.
    """

    @staticmethod
    def _paradox():
        return fd.price_era_paradox_finding()

    @staticmethod
    def _refusal():
        return fd.cannot_determine_finding(
            finding_id="F-99",
            analysis_name="merge-conflict-share-and-recurrence",
            sample_size=3,
            reason="observed n=3 is below the declared minimum",
        )

    #: (case, a callable returning the finding list, substrings the rendering must contain, why this
    #: row exists)
    RENDERINGS = (
        (
            "one actionable finding and one refusal",
            lambda s: [s._paradox(), s._refusal()],
            (
                # Every contract field must be LABELED in the output, or a pasted report is missing
                # the evidence the contract required to be collected.
                "slice",
                "effect",
                "sample",
                "uncertainty",
                "caveat",
                "alternative",
                "next test",
                "recommend",
                # And the header must count the two kinds SEPARATELY.
                "actionable=1",
                "cannot-determine=1",
            ),
            "THE MIXED SET, which is what a real run produces. Every contract field must appear as a "
            "LABEL: the whole point of refusing to construct a finding without (say) an alternative "
            "explanation is that a reader SEES it, and a renderer that collected the field and then "
            "dropped it defeats the contract silently. The header counts are in the same row because "
            "`actionable=1  cannot-determine=1` is the line that stops a reader treating two findings "
            "as two opportunities to act",
        ),
        (
            "a refusal alone",
            lambda s: [s._refusal()],
            (
                "insufficient evidence for advice",
                "none (refused)",
                "CANNOT-DETERMINE",
            ),
            "A REFUSAL MUST RENDER AS A REFUSAL, SAYING SO. An empty recommendation line would read as "
            "an oversight, so the renderer prints `(none; insufficient evidence for advice)` and "
            "`none (refused)` for the absent effect size. This row is what makes the ABSENCE explicit "
            "rather than blank, which is the difference between a stated refusal and a gap",
        ),
        (
            "no findings at all",
            lambda s: [],
            ("findings=0",),
            "THE BOUNDARY, and an ordinary outcome rather than an error: a run may legitimately produce "
            "nothing. It must render a report that SAYS zero rather than raising or emitting an empty "
            "string, because a caller pasting the output needs to see that the analysis ran",
        ),
        (
            "one actionable finding alone",
            lambda s: [s._paradox()],
            ("actionable=1", "cannot-determine=0"),
            "the counterpart of the refusal-alone row: with no refusals present the header must still "
            "print `cannot-determine=0` rather than omitting the field, so a consumer parsing the "
            "header line does not have to handle a missing key",
        ),
    )

    #: Substrings that must NEVER appear in ANY rendering. These are machine-identifying, and a report
    #: is pasted into issues and handed between agents.
    FORBIDDEN = (
        (
            "/home/",
            "an absolute home directory path identifies the maintainer's machine",
        ),
        (
            ".aw/records/runs",
            "a run-record path leaks where the corpus lives and is never needed to read a finding",
        ),
    )

    def test_every_finding_set_renders_completely_and_leaks_no_location(self):
        wrong = []
        for case, build, needles, why in self.RENDERINGS:
            report = fd.format_findings_report(build(self))
            problems = []
            missing = [n for n in needles if n not in report]
            if missing:
                problems.append(
                    f"the rendering omits {missing!r}; it was {report!r}"
                    if len(report) < 400
                    else f"the rendering omits {missing!r}"
                )
            for forbidden, reason in self.FORBIDDEN:
                if forbidden in report:
                    problems.append(
                        f"the rendering CONTAINS {forbidden!r}, which it must not: {reason}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"format_findings_report rendered {len(wrong)} of {len(self.RENDERINGS)} finding sets "
            "wrongly. A MISSING FIELD LABEL failing on the mixed row alone means one field stopped "
            "rendering, which silently defeats the construction-time refusal that forced the author to "
            "supply it; failing on every row means the renderer changed shape. A FORBIDDEN SUBSTRING is "
            "a different class of problem entirely and takes priority: this report is pasted into "
            "issues and handed between agents, so a leaked home path or run-record path is a privacy "
            "defect, not a formatting one. FIX: run the repository leak-sanitizer too "
            "(`aw sanitize --agent`); this check is the narrow one that catches the report BUILDER at "
            "the point a path would enter.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
