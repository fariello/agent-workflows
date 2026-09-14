#!/usr/bin/env python3
"""runanalytics Order 06 (`aflsz3`) E-09: the ranked findings contract.

HERMETICITY. Every fixture is a literal built in this file; nothing reads `.aw/records/runs/`. See the
header of `test_run_analytics_taxonomy.py` for the reasoning.

WHAT THIS SUITE IS FOR. A findings contract asserted only in a docstring is a contract nobody enforces,
so every required field has a REFUSAL test, the no-causal-language check has a CONTROL that plants a
violation, and the price-era Simpson's-paradox case ships as a golden test using the MEASURED figures
rather than a synthetic example.
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
    """E-09: every evidence field is REQUIRED, and a missing one is refused at construction."""

    def test_a_conforming_finding_is_built(self):
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
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(uncertainty="  "))
        self.assertIn("read as precise", str(ctx.exception))

    def test_no_DATA_QUALITY_CAVEAT_is_refused(self):
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(data_quality_caveats=()))
        self.assertIn("implies there are none", str(ctx.exception))

    def test_no_NEXT_EXPERIMENT_is_refused(self):
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(**_valid_kwargs(next_experiment=""))
        self.assertIn("claim rather than a hypothesis", str(ctx.exception))

    def test_no_TITLE_is_refused(self):
        with self.assertRaises(FindingRefusal):
            fd.build_finding(**_valid_kwargs(title="   "))

    def test_a_RECOMMENDATION_on_a_cannot_determine_finding_is_refused(self):
        """Advice on insufficient evidence is the specific output the plan forbids."""

        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(
                **_valid_kwargs(
                    severity=Severity.CANNOT_DETERMINE,
                    recommendation="raise the retry budget",
                )
            )
        self.assertIn("advice on insufficient evidence", str(ctx.exception).lower())

    def test_every_contract_field_survives_serialization(self):
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
    """E-09: no causal language, checked MECHANICALLY rather than by convention."""

    def test_the_check_FIRES_on_a_planted_causal_claim(self):
        """The control V-09 requires. A checker that refused nothing looks identical to one that
        was not looking, so a planted violation must be shown to be caught."""

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

    def test_it_is_CLEAN_on_the_association_phrasing(self):
        """And the same check passes on the honest phrasing, so it discriminates."""

        finding = fd.build_finding(
            **_valid_kwargs(
                title="Per-step cost is associated with position in the session"
            )
        )
        self.assertEqual(
            finding.title, "Per-step cost is associated with position in the session"
        )

    def test_EVERY_human_readable_field_is_scanned(self):
        """A lint that covered only the title would be trivially evaded."""

        for field, value in (
            ("title", "X causes Y"),
            ("affected_slice", "attempts affected because of retries"),
            ("uncertainty", "wide, due to the small sample"),
            ("next_experiment", "re-run; therefore the effect will be clearer"),
            ("recommendation", "reduce context, which leads to lower cost"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(FindingRefusal) as ctx:
                    fd.build_finding(**_valid_kwargs(**{field: value}))
                self.assertIn(field, str(ctx.exception))

    def test_caveats_and_alternatives_are_scanned_too(self):
        with self.assertRaises(FindingRefusal) as ctx:
            fd.build_finding(
                **_valid_kwargs(
                    data_quality_caveats=("coverage is low because logs were lost",)
                )
            )
        self.assertIn("data_quality_caveats[0]", str(ctx.exception))

    def test_the_pattern_list_catches_the_common_causal_constructions(self):
        for phrase in (
            "this causes that",
            "it caused a rise",
            "because of context",
            "due to growth",
            "leads to higher cost",
            "led to a retry",
            "context drives cost",
            "driven by cache reads",
            "results in a rise",
            "responsible for the delta",
            "the reason is context",
            "therefore cost rises",
            "consequently slower",
            "explains the rise",
            "attributable to context",
        ):
            with self.subTest(phrase=phrase):
                self.assertTrue(fd.scan_for_causal_language(phrase), phrase)

    def test_CORRELATION_language_is_explicitly_PERMITTED(self):
        """Naming a correlation is exactly what this layer is allowed to do."""

        for phrase in (
            "cost is correlated with position",
            "an association was observed",
            "the two co-occur",
            "consistent with context growth",
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual(fd.scan_for_causal_language(phrase), [])

    def test_the_scan_returns_the_MATCHES_so_a_refusal_can_name_them(self):
        self.assertEqual(
            fd.scan_for_causal_language("it causes X because Y"), ["causes", "because"]
        )


class CannotDetermineFindingTests(unittest.TestCase):
    """E-09: insufficient evidence yields a `cannot-determine` finding, NEVER advice."""

    def test_it_carries_the_observed_n_and_NO_recommendation(self):
        finding = fd.cannot_determine_finding(
            finding_id="F-09",
            analysis_name="merge-conflict-share-and-recurrence",
            sample_size=3,
            reason="observed n=3 is below the declared minimum n=12",
        )
        self.assertIs(finding.severity, Severity.CANNOT_DETERMINE)
        self.assertFalse(finding.is_actionable)
        self.assertEqual(finding.sample_size, 3)
        self.assertIn("n=3", finding.title)
        self.assertEqual(finding.recommendation, "", "a refusal carries no advice")
        self.assertIsNone(finding.effect_size, "no effect size is reported")

    def test_it_still_meets_the_full_evidence_contract(self):
        """A refusal is a finding, not an exemption from the contract."""

        finding = fd.cannot_determine_finding(
            finding_id="F-09", analysis_name="x", sample_size=3, reason="too few"
        )
        self.assertTrue(finding.alternative_explanations)
        self.assertTrue(finding.data_quality_caveats)
        self.assertTrue(finding.next_experiment)
        self.assertTrue(finding.uncertainty)

    def test_its_alternatives_include_that_the_effect_may_be_ABSENT(self):
        """The alternative a reader most needs and is most likely to forget."""

        finding = fd.cannot_determine_finding(
            finding_id="F-09", analysis_name="x", sample_size=3, reason="too few"
        )
        self.assertIn(
            "the effect may be absent entirely", finding.alternative_explanations
        )

    def test_EVERY_refusal_becomes_a_finding_and_none_is_dropped(self):
        """A silently absent refusal is indistinguishable from an oversight."""

        results = [
            AnalysisResult(
                name="a", verdict=Verdict.CANNOT_DETERMINE, sample_size=3, reason="n"
            ),
            AnalysisResult(name="b", verdict=Verdict.COMPUTED, sample_size=50),
            AnalysisResult(
                name="c", verdict=Verdict.REFUSED, sample_size=2, reason="coverage"
            ),
        ]
        findings = fd.findings_from_results(results)
        self.assertEqual(len(findings), 2, "both non-computed results became findings")
        self.assertEqual({f.severity for f in findings}, {Severity.CANNOT_DETERMINE})

    def test_a_COMPUTED_result_does_NOT_auto_generate_a_finding(self):
        """Manufacturing one finding per analysis is how a report fills with empty assertions."""

        findings = fd.findings_from_results(
            [AnalysisResult(name="b", verdict=Verdict.COMPUTED, sample_size=50)]
        )
        self.assertEqual(findings, [])


class PriceEraParadoxTests(unittest.TestCase):
    """E-09: the MEASURED Simpson's-paradox case, shipped as a golden test."""

    def test_the_golden_finding_uses_the_MEASURED_figures(self):
        finding = fd.price_era_paradox_finding()
        baseline = fd.PRICE_ERA_PARADOX_BASELINE

        self.assertEqual(baseline["era_a_blended_usd_per_mtok_range"], (0.054, 0.071))
        self.assertEqual(baseline["era_b_blended_usd_per_mtok_range"], (0.635, 0.737))
        self.assertAlmostEqual(baseline["cache_read_share_of_tokens"], 0.9862)
        self.assertAlmostEqual(baseline["actual_rate_increase"], 0.10)
        self.assertEqual(baseline["boundary_instant"], "2026-08-29T05:38:43Z")

        # The effect size is the ratio of the measured range endpoints: 0.635 / 0.071.
        self.assertAlmostEqual(finding.effect_size or 0.0, 0.635 / 0.071, places=4)
        self.assertIs(finding.severity, Severity.HIGH)

    def test_the_finding_names_the_ninefold_apparent_rise_AND_the_ten_percent_real_one(
        self,
    ):
        """The whole point: the apparent movement and the real rate change differ by ~90x."""

        finding = fd.price_era_paradox_finding()
        self.assertIn("ninefold", finding.title)
        self.assertIn("10 percent", finding.title)

    def test_the_MECHANISM_is_stated_as_a_co_occurrence_not_as_a_cause(self):
        """The mechanism IS causal, so it belongs in `alternative_explanations`, phrased as one
        account among others. This is the constraint the no-causal-language check imposes even on
        the paradox finding itself."""

        finding = fd.price_era_paradox_finding()
        alternatives = " ".join(finding.alternative_explanations)
        self.assertIn("cache_read rate moved from free to billable", alternatives)
        self.assertIn("98.62%", alternatives)
        # And it passes its own check.
        fd.assert_no_causal_language(finding)

    def test_it_offers_the_WORKFLOW_and_MIX_alternatives_too(self):
        """Three competing accounts, so the schedule change is not presented as the only one."""

        alternatives = fd.price_era_paradox_finding().alternative_explanations
        self.assertEqual(len(alternatives), 3)
        joined = " ".join(alternatives)
        self.assertIn("workflow behavior", joined)
        self.assertIn("mix of models", joined)

    def test_a_POOLED_comparison_across_eras_is_FLAGGED(self):
        warning = fd.detect_pooled_era_comparison(
            eras_present=["era-a", "era-b"], is_stratified=False
        )
        self.assertIn("SIMPSON'S-PARADOX HAZARD", warning)
        self.assertIn("era-a, era-b", warning)
        self.assertIn("9-fold", warning)
        self.assertIn("10%", warning)
        self.assertIn("Stratify by price era", warning)

    def test_a_STRATIFIED_comparison_is_NOT_flagged(self):
        self.assertEqual(
            fd.detect_pooled_era_comparison(
                eras_present=["era-a", "era-b"], is_stratified=True
            ),
            "",
        )

    def test_a_SINGLE_era_comparison_is_NOT_flagged(self):
        """Nothing to confound when only one era is present."""

        self.assertEqual(
            fd.detect_pooled_era_comparison(
                eras_present=["era-b"], is_stratified=False
            ),
            "",
        )
        self.assertEqual(
            fd.detect_pooled_era_comparison(
                eras_present=["era-b", "unknown"], is_stratified=False
            ),
            "",
        )

    def test_the_baseline_is_LABELED_a_snapshot(self):
        self.assertEqual(
            fd.PRICE_ERA_PARADOX_BASELINE["provenance"], "review-time-snapshot"
        )
        self.assertIs(fd.PRICE_ERA_PARADOX_BASELINE["is_current"], False)

    def test_the_finding_caveats_say_the_figures_are_NOT_current(self):
        caveats = " ".join(fd.price_era_paradox_finding().data_quality_caveats)
        self.assertIn("re-measure", caveats)
        self.assertIn("2026-09-08", caveats)


class RankingStabilityTests(unittest.TestCase):
    """E-09: ranking is DETERMINISTIC and TOTAL, or two runs disagree about what matters."""

    def _finding(self, finding_id, severity, effect, coverage=0.5):
        return fd.build_finding(
            **_valid_kwargs(
                finding_id=finding_id,
                severity=severity,
                effect_size=effect,
                coverage=coverage,
            )
        )

    def test_severity_orders_before_effect_size(self):
        ranked = fd.rank_findings(
            [
                self._finding("F-02", Severity.LOW, 100.0),
                self._finding("F-01", Severity.HIGH, 0.1),
            ]
        )
        self.assertEqual([f.finding_id for f in ranked], ["F-01", "F-02"])

    def test_a_larger_effect_ranks_first_within_a_severity(self):
        ranked = fd.rank_findings(
            [
                self._finding("F-01", Severity.HIGH, 1.0),
                self._finding("F-02", Severity.HIGH, 9.0),
            ]
        )
        self.assertEqual([f.finding_id for f in ranked], ["F-02", "F-01"])

    def test_effect_MAGNITUDE_is_used_so_a_negative_effect_still_ranks(self):
        ranked = fd.rank_findings(
            [
                self._finding("F-01", Severity.HIGH, 1.0),
                self._finding("F-02", Severity.HIGH, -9.0),
            ]
        )
        self.assertEqual([f.finding_id for f in ranked], ["F-02", "F-01"])

    def test_higher_coverage_breaks_an_effect_tie(self):
        ranked = fd.rank_findings(
            [
                self._finding("F-01", Severity.HIGH, 5.0, coverage=0.2),
                self._finding("F-02", Severity.HIGH, 5.0, coverage=0.9),
            ]
        )
        self.assertEqual([f.finding_id for f in ranked], ["F-02", "F-01"])

    def test_the_ID_TIEBREAK_makes_the_ranking_REPRODUCIBLE(self):
        """Without it, findings identical on every other key order by input sequence, and a
        ranking that is not reproducible is not evidence."""

        a = self._finding("F-AAA", Severity.HIGH, 5.0, coverage=0.5)
        b = self._finding("F-BBB", Severity.HIGH, 5.0, coverage=0.5)

        forward = [f.finding_id for f in fd.rank_findings([a, b])]
        reverse = [f.finding_id for f in fd.rank_findings([b, a])]
        self.assertEqual(forward, reverse, "input order must not change the ranking")
        self.assertEqual(forward, ["F-AAA", "F-BBB"])

    def test_a_CANNOT_DETERMINE_finding_ranks_LAST_but_still_appears(self):
        """It must be SEEN and must not crowd the top: it is not an opportunity to act on."""

        ranked = fd.rank_findings(
            [
                fd.cannot_determine_finding(
                    finding_id="F-99", analysis_name="x", sample_size=3, reason="n"
                ),
                self._finding("F-01", Severity.INFO, 0.01),
            ]
        )
        self.assertEqual([f.finding_id for f in ranked], ["F-01", "F-99"])
        self.assertEqual(
            len(ranked), 2, "the refusal appears rather than being dropped"
        )

    def test_ranking_is_STABLE_across_repeated_calls(self):
        findings = [
            self._finding("F-01", Severity.HIGH, 5.0),
            self._finding("F-02", Severity.MEDIUM, 5.0),
            fd.cannot_determine_finding(
                finding_id="F-03", analysis_name="x", sample_size=3, reason="n"
            ),
        ]
        first = [f.finding_id for f in fd.rank_findings(findings)]
        for _ in range(5):
            self.assertEqual([f.finding_id for f in fd.rank_findings(findings)], first)

    def test_the_severity_order_covers_EVERY_severity_so_ranking_is_total(self):
        self.assertEqual(set(fd._SEVERITY_ORDER), set(Severity))


class ReportTests(unittest.TestCase):
    """The pasteable report V-09 requires: every contract field, on every finding."""

    def test_the_report_shows_every_contract_field(self):
        report = fd.format_findings_report(
            [
                fd.price_era_paradox_finding(),
                fd.cannot_determine_finding(
                    finding_id="F-99",
                    analysis_name="merge-conflict-share-and-recurrence",
                    sample_size=3,
                    reason="observed n=3 is below the declared minimum",
                ),
            ]
        )
        for label in (
            "slice",
            "effect",
            "sample",
            "uncertainty",
            "caveat",
            "alternative",
            "next test",
            "recommend",
        ):
            with self.subTest(label=label):
                self.assertIn(label, report)

    def test_a_refusal_renders_with_NO_recommendation_and_says_so(self):
        report = fd.format_findings_report(
            [
                fd.cannot_determine_finding(
                    finding_id="F-99", analysis_name="x", sample_size=3, reason="n"
                )
            ]
        )
        self.assertIn("insufficient evidence for advice", report)
        self.assertIn("none (refused)", report)
        self.assertIn("CANNOT-DETERMINE", report)

    def test_the_header_counts_actionable_and_refused_separately(self):
        report = fd.format_findings_report(
            [
                fd.price_era_paradox_finding(),
                fd.cannot_determine_finding(
                    finding_id="F-99", analysis_name="x", sample_size=3, reason="n"
                ),
            ]
        )
        self.assertIn("actionable=1", report)
        self.assertIn("cannot-determine=1", report)

    def test_an_EMPTY_finding_set_renders_without_crashing(self):
        self.assertIn("findings=0", fd.format_findings_report([]))

    def test_the_report_carries_no_path_and_no_absolute_location(self):
        report = fd.format_findings_report([fd.price_era_paradox_finding()])
        self.assertNotIn("/home/", report)
        self.assertNotIn(".aw/records/runs", report)


if __name__ == "__main__":
    unittest.main()
