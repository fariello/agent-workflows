#!/usr/bin/env python3
"""runanalytics Order 06 (`aflsz3`) E-03..E-08: time, analyses, refusals, pricing, statistics.

HERMETICITY. Every fixture is a literal built in this file; nothing reads `.aw/records/runs/`. See the
header of `test_run_analytics_taxonomy.py` for the full reasoning and the plan's stop condition.

THE TESTS THAT MATTER MOST HERE ARE THE REFUSALS. Four required analyses rest on n between 3 and 6 and
one on 1.1 percent identity coverage, so the tests assert that those REFUSE and that a chart CANNOT be
produced from a refusal. A suite that only checked the computed paths would pass while the module
happily rendered n=3 as a finding, which is the specific defect the plan's stop conditions name.
"""

from __future__ import annotations

import unittest

from agent_workflows import benchmark_metrics
from agent_workflows import run_analytics_pricing as pricing
from agent_workflows import run_analytics_statistics as st
from agent_workflows.benchmark_metrics import MetricValue
from agent_workflows.run_analytics_statistics import StatisticsError, Verdict


class QuantileAndDescribeTests(unittest.TestCase):
    """E-08: deterministic quantiles, and missing values that are NEVER zero."""

    def test_quantiles_are_deterministic_and_interpolated(self):
        values = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(st.quantile(values, 0.0), 1.0)
        self.assertEqual(st.quantile(values, 1.0), 4.0)
        self.assertEqual(st.quantile(values, 0.5), 2.5)
        # Determinism: the same input yields the same output, every time.
        for _ in range(5):
            self.assertEqual(st.quantile(values, 0.25), 1.75)

    def test_a_quantile_of_an_EMPTY_sample_is_REFUSED_not_zero(self):
        with self.assertRaises(StatisticsError) as ctx:
            st.quantile([], 0.5)
        self.assertIn("is not zero", str(ctx.exception))

    def test_an_out_of_range_q_is_refused(self):
        for bad in (-0.1, 1.1, 2.0):
            with self.subTest(q=bad):
                with self.assertRaises(StatisticsError):
                    st.quantile([1.0, 2.0], bad)

    def test_a_single_observation_quantile_is_that_observation(self):
        self.assertEqual(st.quantile([7.0], 0.5), 7.0)
        self.assertEqual(st.quantile([7.0], 0.9), 7.0)

    def test_None_counts_as_MISSING_and_never_as_zero(self):
        """The four-state provenance rule applied to a sample: absence is not zero."""

        distribution = st.describe("x", [1.0, None, 3.0, None])
        self.assertEqual(distribution.sample_size, 2)
        self.assertEqual(distribution.missing_count, 2)
        self.assertEqual(
            distribution.mean, 2.0, "the Nones did not drag the mean toward 0"
        )
        self.assertAlmostEqual(distribution.coverage, 0.5)

    def test_an_EMPTY_sample_yields_None_statistics_and_not_zeros(self):
        distribution = st.describe("x", [])
        self.assertEqual(distribution.sample_size, 0)
        for value in (
            distribution.mean,
            distribution.median,
            distribution.stdev,
            distribution.minimum,
            distribution.maximum,
            distribution.p90,
        ):
            self.assertIsNone(value, "no observations is not an observation of zero")

    def test_stdev_of_ONE_observation_is_None_rather_than_zero(self):
        """The dispersion of a single observation is undefined, not 0."""

        self.assertIsNone(st.describe("x", [5.0]).stdev)
        self.assertIsNotNone(st.describe("x", [5.0, 7.0]).stdev)

    def test_a_non_finite_or_non_numeric_value_counts_as_missing(self):
        distribution = st.describe(
            "x",
            [1.0, float("nan"), float("inf"), True, "12", None],  # type: ignore[list-item]
        )
        self.assertEqual(distribution.sample_size, 1)
        self.assertEqual(distribution.missing_count, 5)

    def test_a_skewed_sample_reports_median_AND_mean_so_the_skew_is_visible(self):
        distribution = st.describe("x", [1.0] * 9 + [1000.0])
        self.assertEqual(distribution.median, 1.0)
        self.assertGreater(distribution.mean or 0, 100.0)

    def test_a_zero_valued_sample_is_DISTINCT_from_an_absent_one(self):
        zeros = st.describe("x", [0.0, 0.0, 0.0])
        absent = st.describe("x", [None, None, None])
        self.assertEqual(zeros.sample_size, 3)
        self.assertEqual(zeros.mean, 0.0)
        self.assertEqual(absent.sample_size, 0)
        self.assertIsNone(absent.mean)


class MetricValueReuseTests(unittest.TestCase):
    """E-08 and DECISION 03-aflsz3-D3: the SHIPPED vocabulary is reused, not copied."""

    def test_distributions_are_expressed_in_the_SHIPPED_MetricValue_type(self):
        metrics = st.describe("cost", [1.0, 2.0, 3.0], unit="USD").as_metric_values()
        for name, metric in metrics.items():
            with self.subTest(name=name):
                # THE SHIPPED CLASS, not a local copy. `is` on the type is the assertion.
                self.assertIs(type(metric), MetricValue)
                self.assertEqual(metric.sample_size, 3)
                self.assertEqual(metric.unit, "USD")

    def test_an_empty_sample_marks_MetricValue_unavailable_rather_than_zero(self):
        metrics = st.describe("cost", [], unit="USD").as_metric_values()
        self.assertFalse(metrics["mean"].is_available)
        self.assertIsNone(metrics["mean"].value)

    def test_the_wilson_interval_is_the_SHIPPED_function(self):
        self.assertIs(st.wilson_score_interval, benchmark_metrics.wilson_score_interval)

    def test_the_benchmark_dollar_cost_GUARD_still_fires_and_was_not_relaxed(self):
        """The plan's third stop condition, as a test.

        OQ-04 settled that the two measurement contracts COEXIST: `benchmark_metrics` forbids dollar
        cost for cross-model comparison, and this layer's dollar cost is runner-recorded. So the guard
        must still bite. This asserts the shipped constant is intact and that a cost key is still
        refused where it was always refused.
        """

        for forbidden in ("cost", "usd", "price", "dollars", "spending", "dollar_cost"):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, benchmark_metrics._FORBIDDEN_COST_KEYS)

        # And the enforcement path is untouched: a usage mapping carrying a cost key is refused.
        with self.assertRaises(benchmark_metrics.MetricError):
            benchmark_metrics.evaluate_trial_metrics(
                _FakeTrial(usage={"cost": 1.0}),  # type: ignore[arg-type]
            )

    def test_no_new_runtime_dependency_is_imported(self):
        """E-08: stdlib only. Asserted against the module's own import graph."""

        import agent_workflows.run_analytics_statistics as module

        source = module.__file__ or ""
        self.assertTrue(source.endswith("run_analytics_statistics.py"))
        # Only stdlib and in-repo imports. A third-party statistics package would appear here.
        forbidden = ("numpy", "scipy", "pandas", "statsmodels", "sklearn")
        with open(source, "r", encoding="utf-8") as handle:
            text = handle.read()
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(f"import {name}", text)


class _FakeTrial:
    """The minimum shape `evaluate_trial_metrics` reads, so the guard can be exercised.

    Deliberately minimal and local: constructing a real `TrialResult` would couple this test to that
    type's evolving constructor for no benefit, since the guard fires on the FIRST loop over
    `trial.usage` before any other field is read.
    """

    def __init__(self, usage):
        self.usage = usage
        self.trial_id = "t1"
        self.is_pending = False
        self.transcript = None


class TimeModelTests(unittest.TestCase):
    """E-03: unattributed time is the DOMINANT term, and a shared session is counted ONCE."""

    def test_unattributed_time_is_published_and_dominant_at_the_measured_ratio(self):
        """Reproduces the measured 3.8 percent activity ratio in a fixture."""

        model = st.build_time_model(
            wall_seconds=1000.0,
            activities=[{"session_id": "s1", "start": 0.0, "end": 38.0}],
        )
        self.assertAlmostEqual(model.observed_activity_seconds, 38.0)
        self.assertAlmostEqual(model.unattributed_seconds, 962.0)
        self.assertAlmostEqual(model.activity_share_of_wall, 0.038)
        self.assertAlmostEqual(model.unattributed_share_of_wall, 0.962)
        self.assertEqual(model.dominant_term(), "unattributed")

    def test_the_serialized_form_leads_with_unattributed_time(self):
        """A view that buries the dominant term invites the misreading the rule forbids."""

        payload = st.build_time_model(
            wall_seconds=100.0,
            activities=[{"session_id": "s", "start": 0.0, "end": 4.0}],
        ).to_dict()
        self.assertEqual(list(payload)[0], "unattributed_seconds")
        self.assertEqual(payload["dominant_term"], "unattributed")

    def test_a_SHARED_session_is_attributed_ONCE_and_not_once_per_attempt(self):
        """27 real attempts exceeded their own wall time without this correction."""

        # Two attempts share session `s1`, each reporting the SAME 100s span.
        model = st.build_time_model(
            wall_seconds=200.0,
            activities=[
                {"session_id": "s1", "start": 0.0, "end": 100.0},
                {"session_id": "s1", "start": 0.0, "end": 100.0},
            ],
        )
        self.assertAlmostEqual(
            model.observed_activity_seconds,
            100.0,
            msg="the shared session's activity is counted once, not twice",
        )
        self.assertAlmostEqual(model.double_counted_seconds_avoided, 100.0)
        self.assertEqual(model.shared_session_count, 1)
        self.assertEqual(model.attempts_sharing_a_session, 2)
        self.assertGreater(model.unattributed_seconds, 0.0)

    def test_WITHOUT_the_shared_session_rule_activity_would_EXCEED_wall_time(self):
        """The measured defect made concrete: the naive sum is what produced 27 bad attempts."""

        activities = [
            {"session_id": "s1", "start": 0.0, "end": 100.0},
            {"session_id": "s1", "start": 0.0, "end": 100.0},
        ]
        naive_total = sum(a["end"] - a["start"] for a in activities)
        wall = 150.0
        self.assertGreater(
            naive_total, wall, "the naive sum exceeds wall time: the defect"
        )

        model = st.build_time_model(wall_seconds=wall, activities=activities)
        self.assertLessEqual(
            model.observed_activity_seconds, wall, "the corrected model does not"
        )

    def test_overlapping_activities_in_DIFFERENT_sessions_report_overlap(self):
        model = st.build_time_model(
            wall_seconds=100.0,
            activities=[
                {"session_id": "s1", "start": 0.0, "end": 20.0},
                {"session_id": "s1", "start": 10.0, "end": 30.0},
            ],
        )
        self.assertAlmostEqual(
            model.observed_activity_seconds, 30.0, msg="union, not sum"
        )
        self.assertAlmostEqual(model.overlap_seconds, 10.0)

    def test_activity_is_NEVER_scaled_up_to_fill_elapsed_time(self):
        """The mutation V-03 asks for: scaling activity to wall time breaks the ratio assertion."""

        model = st.build_time_model(
            wall_seconds=1000.0,
            activities=[{"session_id": "s", "start": 0.0, "end": 38.0}],
        )
        self.assertAlmostEqual(model.observed_activity_seconds, 38.0)

        # THE MUTATION: a model that distributed elapsed time across activities.
        mutated_activity = model.wall_seconds
        self.assertNotAlmostEqual(
            mutated_activity,
            model.observed_activity_seconds,
            msg="scaling activity to fill elapsed manufactures 96 percent of the number",
        )
        self.assertAlmostEqual(
            mutated_activity / model.observed_activity_seconds, 1000 / 38, places=6
        )

    def test_a_NEGATIVE_unattributed_value_is_reported_rather_than_clamped(self):
        """A negative is real evidence of a clock or attribution defect; flooring it erases it."""

        model = st.build_time_model(
            wall_seconds=10.0,
            activities=[{"session_id": "s", "start": 0.0, "end": 50.0}],
        )
        self.assertLess(model.unattributed_seconds, 0.0)

    def test_a_malformed_activity_is_skipped_rather_than_crashing(self):
        model = st.build_time_model(
            wall_seconds=100.0,
            activities=[
                {"session_id": "s", "start": None, "end": 10.0},
                {"session_id": "s", "start": 10.0, "end": 5.0},
                {"session_id": "s", "start": "x", "end": "y"},
                {"session_id": "s", "start": 0.0, "end": 10.0},
            ],
        )
        self.assertAlmostEqual(model.observed_activity_seconds, 10.0)


class InstructionBurdenTests(unittest.TestCase):
    """E-04: the burden is tokens and dollars, and the 0.014 percent figure IS in the output."""

    def _burden(self, **overrides):
        kwargs = {
            "first_step_input_tokens": [15067.0] * 20,
            "turn_count": 100,
            "input_rate_per_mtok": 5.50,
        }
        kwargs.update(overrides)
        return st.instruction_burden(**kwargs)

    def test_the_0_014_PERCENT_figure_is_published_in_the_OUTPUT(self):
        """V-04's whole purpose: a reader must not mistake a flat chart for an absent cost."""

        footnote = self._burden().values["read_time_footnote"]
        self.assertEqual(footnote["share_of_wall_time_percent"], "0.014%")
        self.assertIn("0.014%", footnote["derivation"])
        self.assertIn("183.2 s of read-tool time", footnote["derivation"])
        self.assertIn("48036 s of tool time", footnote["derivation"])
        self.assertIn("1254107 s of", footnote["derivation"])

    def test_read_time_is_LABELED_a_footnote_and_not_a_headline(self):
        footnote = self._burden().values["read_time_footnote"]
        self.assertEqual(footnote["label"], "FOOTNOTE, NOT A HEADLINE")
        self.assertIn("flat line", footnote["why_it_is_a_footnote"])
        self.assertIn("absent cost", footnote["why_it_is_a_footnote"])

    def test_the_burden_is_measured_in_TOKENS_and_DOLLARS(self):
        values = self._burden().values
        self.assertEqual(values["median_first_step_input_tokens"], 15067.0)
        # 15067 tokens at $5.50/Mtok = $0.0828685, reported rounded to 6 decimal places.
        self.assertAlmostEqual(
            values["cost_per_turn_usd"], 15067 * 5.50 / 1_000_000, places=6
        )
        self.assertAlmostEqual(values["total_injected_cost_usd"], 8.28685, places=4)

    def test_the_standing_instruction_INVENTORY_is_recorded(self):
        values = self._burden().values
        self.assertEqual(values["standing_instruction_bytes"]["AGENTS.md"], 33101)
        self.assertEqual(
            values["standing_instruction_tokens_approx"]["AGENTS.md"], 8275
        )
        self.assertGreater(values["standing_instruction_total_bytes"], 33101)

    def test_OBSERVED_durations_are_used_when_supplied_and_LABELED_as_observed(self):
        """The baseline is a fallback, not a substitute: fresh numbers change the output."""

        footnote = self._burden(
            read_tool_seconds=10.0, tool_seconds=1000.0, wall_seconds=100_000.0
        ).values["read_time_footnote"]
        self.assertEqual(footnote["basis"], "observed-in-this-corpus")
        self.assertAlmostEqual(footnote["share_of_tool_time"], 0.01)
        self.assertEqual(footnote["share_of_wall_time_percent"], "0.010%")

    def test_the_SNAPSHOT_basis_is_labeled_NOT_CURRENT_when_no_durations_are_supplied(
        self,
    ):
        footnote = self._burden().values["read_time_footnote"]
        self.assertIn("NOT-CURRENT", footnote["basis"])

    def test_a_PARTIAL_duration_set_falls_back_rather_than_mixing_bases(self):
        """Mixing an observed numerator with a snapshot denominator yields a number owned by neither."""

        for partial in (
            {"read_tool_seconds": 10.0},
            {"read_tool_seconds": 10.0, "tool_seconds": 1000.0},
            {"read_tool_seconds": 10.0, "tool_seconds": 0.0, "wall_seconds": 100.0},
        ):
            with self.subTest(partial=sorted(partial)):
                footnote = self._burden(**partial).values["read_time_footnote"]
                self.assertIn("NOT-CURRENT", footnote["basis"])

    def test_an_UNDER_POWERED_burden_sample_refuses(self):
        result = self._burden(first_step_input_tokens=[15067.0, 15067.0])
        self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
        self.assertFalse(result.renderable)


class UnderPowerRefusalTests(unittest.TestCase):
    """E-06: the four measured slices refuse, and a chart CANNOT be produced from a refusal."""

    def test_the_shared_predicate_refuses_below_the_declared_minimum(self):
        for n in (0, 1, 3, 6, st.MINIMUM_SAMPLE_SIZE - 1):
            with self.subTest(n=n):
                result = st.under_power_verdict("x", n)
                self.assertIsNotNone(result)
                assert result is not None
                self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
                self.assertEqual(result.sample_size, n)
                self.assertIn(f"n={n}", result.reason)

    def test_the_shared_predicate_returns_None_at_or_above_the_minimum(self):
        for n in (st.MINIMUM_SAMPLE_SIZE, st.MINIMUM_SAMPLE_SIZE + 1, 1000):
            with self.subTest(n=n):
                self.assertIsNone(st.under_power_verdict("x", n))

    def test_the_FOUR_named_required_analyses_each_return_cannot_determine_WITH_its_n(
        self,
    ):
        """The four measured at n between 3 and 6, named rather than discovered at render time."""

        results = st.refuse_under_powered_required_analyses()
        self.assertEqual(len(results), 4)
        self.assertEqual(set(results), set(st.UNDER_POWERED_ANALYSES))
        for name, result in results.items():
            with self.subTest(name=name):
                self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
                self.assertFalse(result.renderable)
                self.assertIn(result.sample_size, (3, 6), "the measured sample sizes")
                self.assertIn(f"n={result.sample_size}", result.reason)

    def test_requesting_a_CHART_for_an_under_powered_slice_REFUSES_rather_than_renders(
        self,
    ):
        """The proof E-06 requires: a renderer cannot get values out of a refusal."""

        for name, result in st.refuse_under_powered_required_analyses().items():
            with self.subTest(name=name):
                with self.assertRaises(StatisticsError) as ctx:
                    result.require_values()
                message = str(ctx.exception)
                self.assertIn("cannot-determine", message)
                self.assertIn("no renderable values", message)

    def test_a_required_analysis_whose_n_has_GROWN_is_computed_rather_than_refused(
        self,
    ):
        """The mirror-image defect: refusing forever would be as wrong as charting n=3."""

        results = st.refuse_under_powered_required_analyses(
            {"merge_conflict_attempts": 500, "items_with_multiple_attempts": 500}
        )
        for name, result in results.items():
            with self.subTest(name=name):
                self.assertIs(result.verdict, Verdict.COMPUTED)
                self.assertEqual(result.sample_size, 500)

    def test_the_measured_sample_sizes_that_force_the_refusals_are_recorded(self):
        baseline = st.CORPUS_BASELINE
        self.assertEqual(baseline["queue_item_count"], 733)
        self.assertEqual(baseline["items_with_multiple_attempts"], 6)
        self.assertEqual(baseline["recovery_attempts"], 6)
        self.assertEqual(baseline["merge_conflict_attempts"], 3)

    def test_the_baseline_is_LABELED_a_snapshot(self):
        self.assertEqual(st.CORPUS_BASELINE["provenance"], "review-time-snapshot")
        self.assertIs(st.CORPUS_BASELINE["is_current"], False)


class ModelComparisonRefusalTests(unittest.TestCase):
    """E-08: the model arm REFUSES at the measured 1.1 percent coverage; price-era proceeds."""

    def test_it_REFUSES_at_the_measured_coverage_and_says_so(self):
        """2 of 179 attempts carry a resolvable model. A chart over that is a fabrication."""

        attempts = [{"cost": 1.0} for _ in range(177)] + [
            {"cost": 1.0, "model": "provider/model-a"},
            {"cost": 1.0, "model": "provider/model-b"},
        ]
        result = st.model_comparison(attempts)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertFalse(result.renderable)
        self.assertEqual(result.sample_size, 2)
        self.assertIn("2 of 179 attempts", result.reason)
        self.assertAlmostEqual(result.values["observed_coverage"], 2 / 179, places=6)

    def test_host_default_does_NOT_count_as_a_resolved_model(self):
        """31 of 33 provenance blocks record `model: host-default`, which identifies nothing."""

        result = st.model_comparison([{"model": "host-default", "cost": 1.0}] * 50)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertEqual(result.sample_size, 0)

    def test_BOTH_tempting_inferences_are_refused_BY_NAME(self):
        """Each is refused in the caveats because each is tempting and each is wrong."""

        caveats = " ".join(st.model_comparison([{"cost": 1.0}] * 10).caveats)
        self.assertIn("run date", caveats)
        self.assertIn("PRICE ERA", caveats)
        self.assertIn("sub-agent", caveats)

    def test_it_states_that_PRICE_ERA_stratification_is_unaffected(self):
        caveats = " ".join(st.model_comparison([{"cost": 1.0}] * 10).caveats)
        self.assertIn("price-era stratification IS available", caveats)

    def test_it_COMPUTES_once_coverage_meets_the_declared_threshold(self):
        """Not a permanent refusal: coverage improves for future runs and the analysis unlocks."""

        attempts = [{"model": "provider/model-a", "cost": 1.0} for _ in range(20)] + [
            {"model": "provider/model-b", "cost": 2.0} for _ in range(20)
        ]
        result = st.model_comparison(attempts)
        self.assertIs(result.verdict, Verdict.COMPUTED)
        self.assertEqual(
            set(result.values["per_model_cost_usd"]),
            {"provider/model-a", "provider/model-b"},
        )

    def test_the_measured_identity_coverage_is_recorded(self):
        self.assertEqual(st.CORPUS_BASELINE["attempts_with_resolvable_model"], 2)
        self.assertEqual(st.CORPUS_BASELINE["runs_with_null_options_model"], 130)
        self.assertAlmostEqual(st.CORPUS_BASELINE["model_identity_coverage"], 0.011)


class VerifierPhaseTests(unittest.TestCase):
    """E-06: the verifier phase is DERIVED from a filename and must be labeled derived."""

    def test_a_verify_log_filename_is_recognized_and_marked_derived(self):
        phase, derived = st.verifier_phase_of_log("03-aflsz3-attempt-1-verify.jsonl")
        self.assertEqual(phase, "verify")
        self.assertTrue(derived)

    def test_a_plain_attempt_log_is_execute_and_STILL_marked_derived(self):
        """Both are derived from the same presentation detail; only one is a verify turn."""

        phase, derived = st.verifier_phase_of_log("03-aflsz3-attempt-1.jsonl")
        self.assertEqual(phase, "execute")
        self.assertTrue(derived)

    def test_a_full_path_is_reduced_to_its_basename(self):
        phase, _ = st.verifier_phase_of_log(
            "/some/where/sessions/01-abc123-attempt-2-verify.jsonl"
        )
        self.assertEqual(phase, "verify")

    def test_the_summary_is_LABELED_derived_and_records_zero_verify_cost_attempts(self):
        result = st.verifier_phase_summary(
            [
                {"filename": "01-a-attempt-1.jsonl", "cost": 10.0, "action": "execute"},
                {"filename": "01-a-attempt-1-verify.jsonl", "cost": 1.0},
                {"filename": "02-b-attempt-1.jsonl", "cost": 5.0, "action": "review"},
            ]
        )
        self.assertTrue(result.is_derived)
        self.assertEqual(
            result.values["verify_phase_provenance"], "derived-from-log-filename"
        )
        self.assertEqual(result.values["attempts_carrying_verify_cost"], 0)
        self.assertEqual(result.values["cost_by_phase_usd"]["verify"], 1.0)
        self.assertEqual(result.values["cost_by_phase_usd"]["execute"], 10.0)
        self.assertEqual(result.values["cost_by_phase_usd"]["review"], 5.0)
        self.assertIn("DERIVED FROM A FILENAME", " ".join(result.caveats))

    def test_the_measured_verifier_spend_is_recorded(self):
        self.assertEqual(st.CORPUS_BASELINE["verifier_log_count"], 57)
        self.assertEqual(st.CORPUS_BASELINE["verifier_log_cost_usd"], 64.08)
        self.assertEqual(st.CORPUS_BASELINE["attempts_with_verify_cost"], 0)


class SupportedAnalysisTests(unittest.TestCase):
    """E-05: the analyses the corpus supports, each with a schema-level AND numeric assertion."""

    def test_per_ipd_usage_aggregates_by_id6_and_reports_the_distribution(self):
        attempts = [
            {
                "ipd_id6": f"id{n:04d}",
                "cost": float(n),
                "tokens": {"total": n * 100},
                "wall_seconds": float(n * 10),
            }
            for n in range(1, 21)
        ]
        result = st.per_ipd_usage(attempts)
        self.assertIs(result.verdict, Verdict.COMPUTED)
        self.assertEqual(result.sample_size, 20)
        values = result.require_values()
        # SCHEMA level.
        for key in ("cost_usd", "tokens", "wall_seconds", "attempts_per_ipd"):
            self.assertIn(key, values)
            self.assertIn("sample_size", values[key])
        # NUMERIC level: costs 1..20.
        self.assertAlmostEqual(values["cost_usd"]["median"], 10.5)
        self.assertAlmostEqual(values["cost_usd"]["minimum"], 1.0)
        self.assertAlmostEqual(values["cost_usd"]["maximum"], 20.0)

    def test_per_ipd_usage_counts_a_RETRIED_ipd_once_not_five_times(self):
        """The sample is 'what does an IPD cost', so retries aggregate rather than multiply."""

        attempts = [{"ipd_id6": "same01", "cost": 1.0} for _ in range(5)]
        attempts += [{"ipd_id6": f"id{n:04d}", "cost": 1.0} for n in range(20)]
        result = st.per_ipd_usage(attempts)
        self.assertEqual(
            result.sample_size, 21, "20 unique plus the one retried five times"
        )
        values = result.require_values()
        self.assertEqual(
            values["cost_usd"]["maximum"], 5.0, "the retried IPD's costs summed"
        )

    def test_per_ipd_usage_REFUSES_an_under_powered_corpus(self):
        result = st.per_ipd_usage([{"ipd_id6": "a", "cost": 1.0}])
        self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)

    def test_implementation_versus_inspection_reports_a_ratio_with_an_INTERVAL(self):
        """Measured: edit 5512 vs read 2332. A bare ratio hides how much data is behind it."""

        result = st.implementation_versus_inspection(
            tool_counts={
                "edit": 5512,
                "write": 575,
                "read": 2332,
                "grep": 49,
                "glob": 21,
            },
            file_categories={
                "source-code": 3200,
                "plan-or-ipd": 3158,
                "test-code": 1095,
            },
        )
        values = result.require_values()
        self.assertEqual(values["implementation_calls"], 6087)
        self.assertEqual(values["inspection_calls"], 2402)
        self.assertAlmostEqual(
            values["ratio_implementation_to_inspection"], 6087 / 2402, places=6
        )
        share = values["implementation_share"]
        self.assertAlmostEqual(share["value"], 6087 / 8489, places=6)
        self.assertIsNotNone(share["ci_lower"])
        self.assertIsNotNone(share["ci_upper"])
        self.assertLess(share["ci_lower"], share["value"])
        self.assertGreater(share["ci_upper"], share["value"])
        # The measured file-category breakdown, recomputed from the supplied counts.
        self.assertAlmostEqual(
            values["file_category_shares"]["source-code"], 3200 / 7453, places=6
        )
        self.assertAlmostEqual(
            sum(values["file_category_shares"].values()), 1.0, places=5
        )

    def test_cache_utilization_shows_cache_dominating_the_tokens(self):
        """Measured: cache_read is 98.62 percent of tokens and 72.1 percent of Era B spend."""

        result = st.cache_utilization(
            token_components={
                "input": 60_000_000,
                "output": 20_000_000,
                "cache": 5_715_743_803,
                "total": 5_795_743_803,
            },
            cost_by_component={"input": 216.0, "output": 588.0, "cache": 2051.0},
        )
        values = result.require_values()
        self.assertAlmostEqual(values["cache_share_of_tokens"], 0.9862, places=4)
        self.assertAlmostEqual(values["cache_share_of_spend"], 0.7183, places=3)
        self.assertIn("cache_write", " ".join(result.caveats))

    def test_cost_concentration_reports_the_top_decile_and_quintile(self):
        """The first named addition. Measured: top 10 percent held 22.8 percent of spend."""

        costs = [1.0] * 90 + [10.0] * 10
        result = st.cost_concentration(costs)
        values = result.require_values()
        self.assertAlmostEqual(values["total_spend_usd"], 190.0)
        self.assertAlmostEqual(
            values["top_decile_spend_share"], 100.0 / 190.0, places=6
        )
        self.assertEqual(values["max_cost_usd"], 10.0)
        self.assertIn("ASSOCIATION ONLY", " ".join(result.caveats))

    def test_cost_concentration_refuses_when_total_spend_is_zero(self):
        """A concentration share of nothing is undefined, not 0."""

        result = st.cost_concentration([0.0] * 20)
        self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
        self.assertIn("undefined rather than 0", result.reason)

    def test_the_within_session_gradient_detects_a_MONOTONIC_rise(self):
        """The second named addition. Measured: $0.0781 to $0.1290, 1.27x over 345 sessions."""

        steps = []
        for session in range(20):
            for position in range(20):
                # A deliberate linear rise from 0.0781 to about 0.1290.
                cost = 0.0781 + (0.1290 - 0.0781) * position / 19
                steps.append(
                    {"session_id": f"s{session}", "position": position, "cost": cost}
                )
        result = st.within_session_gradient(steps)
        values = result.require_values()
        self.assertEqual(values["session_count"], 20)
        self.assertTrue(values["is_monotonic_increasing"])
        self.assertAlmostEqual(values["first_decile_mean_cost_usd"], 0.0794, places=3)
        self.assertAlmostEqual(values["last_decile_mean_cost_usd"], 0.1277, places=3)
        self.assertGreater(values["first_to_last_ratio"], 1.2)

    def test_the_gradient_states_BOTH_explanations_and_asserts_neither(self):
        """The plan forbids asserting context growth; both accounts must be stated."""

        steps = [
            {"session_id": f"s{s}", "position": p, "cost": 0.1}
            for s in range(20)
            for p in range(20)
        ]
        caveats = " ".join(st.within_session_gradient(steps).caveats)
        self.assertIn("ASSOCIATION ONLY", caveats)
        self.assertIn("context growth", caveats)
        self.assertIn("harder work", caveats)

    def test_the_gradient_EXCLUDES_short_sessions(self):
        """A 3-step session's 'last decile' is one step and would not compare like with like."""

        short = [
            {"session_id": f"s{s}", "position": p, "cost": 0.1}
            for s in range(50)
            for p in range(3)
        ]
        result = st.within_session_gradient(short)
        self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
        self.assertEqual(result.sample_size, 0)

    def test_missingness_bias_reports_the_unaccounted_share(self):
        """The fourth named addition. Measured: $394.19 across 215 files, 13.0 percent of spend."""

        logs = {f"s{n}": 10.0 for n in range(100)}
        attempts = {f"s{n}": 10.0 for n in range(87)}
        result = st.missingness_bias(session_log_costs=logs, attempt_costs=attempts)
        values = result.require_values()
        self.assertAlmostEqual(values["session_log_total_usd"], 1000.0)
        self.assertAlmostEqual(values["recorded_attempt_total_usd"], 870.0)
        self.assertAlmostEqual(values["unaccounted_usd"], 130.0)
        self.assertEqual(values["unaccounted_session_count"], 13)
        self.assertAlmostEqual(values["unaccounted_share_of_spend"], 0.13)
        self.assertIn("UNDERSTATES", " ".join(result.caveats))

    def test_missingness_bias_reports_an_attempt_with_NO_log_separately(self):
        """Different cause, different fix, so not folded into the unaccounted figure."""

        result = st.missingness_bias(
            session_log_costs={"s1": 1.0}, attempt_costs={"s1": 1.0, "s2": 5.0}
        )
        self.assertEqual(result.values["attempts_without_a_log_count"], 1)
        self.assertEqual(result.values["unaccounted_usd"], 0.0)

    def test_the_measured_figures_for_the_four_named_additions_are_recorded(self):
        baseline = st.CORPUS_BASELINE
        self.assertAlmostEqual(baseline["top_decile_spend_share"], 0.228)
        self.assertAlmostEqual(baseline["top_quintile_spend_share"], 0.396)
        self.assertAlmostEqual(baseline["first_decile_mean_step_cost_usd"], 0.0781)
        self.assertAlmostEqual(baseline["last_decile_mean_step_cost_usd"], 0.1290)
        self.assertEqual(baseline["gradient_session_count"], 345)
        self.assertAlmostEqual(baseline["unaccounted_cost_usd"], 394.19)
        self.assertEqual(baseline["unaccounted_session_file_count"], 215)


class PricingTests(unittest.TestCase):
    """E-07: the measured two-era schedule, validated against RECORDED cost."""

    def test_ERA_A_prices_cache_reads_FREE(self):
        priced = pricing.price_step(
            tokens={"input": 1_000_000, "output": 100_000, "cache": 10_000_000},
            at="2026-08-01T00:00:00Z",
        )
        self.assertEqual(priced.era_id, "era-a")
        # 1 Mtok input at $5 + 0.1 Mtok output at $25 + 10 Mtok cache at $0.
        self.assertAlmostEqual(priced.estimated_usd or 0.0, 5.0 + 2.5 + 0.0, places=9)
        self.assertEqual(priced.component_costs["cache"], 0.0)

    def test_ERA_B_prices_cache_reads_at_ten_percent_of_input(self):
        priced = pricing.price_step(
            tokens={"input": 1_000_000, "output": 100_000, "cache": 10_000_000},
            at="2026-09-01T00:00:00Z",
        )
        self.assertEqual(priced.era_id, "era-b")
        # 1 Mtok at $5.50 + 0.1 Mtok at $27.50 + 10 Mtok at $0.55.
        self.assertAlmostEqual(
            priced.estimated_usd or 0.0, 5.50 + 2.75 + 5.50, places=9
        )
        rates = pricing.MEASURED_ERAS[1].rates
        self.assertAlmostEqual(
            rates.cache_read_per_mtok, rates.input_per_mtok * 0.10, places=9
        )

    def test_the_two_BOUNDARY_INSTANTS_land_in_the_correct_eras(self):
        """The boundary located to the step, which is what V-07 requires."""

        self.assertEqual(pricing.ERA_A_LAST_STEP, "2026-08-29T01:30:43Z")
        self.assertEqual(pricing.ERA_B_FIRST_STEP, "2026-08-29T05:38:43Z")

        last_a = pricing.price_step(tokens={"input": 1000}, at=pricing.ERA_A_LAST_STEP)
        self.assertEqual(last_a.era_id, "era-a")
        first_b = pricing.price_step(
            tokens={"input": 1000}, at=pricing.ERA_B_FIRST_STEP
        )
        self.assertEqual(first_b.era_id, "era-b")

    def test_the_interval_is_from_INCLUSIVE_to_EXCLUSIVE_so_the_boundary_belongs_to_one_era(
        self,
    ):
        era_a, era_b = pricing.MEASURED_ERAS
        self.assertEqual(era_a.effective_to, pricing.ERA_B_FIRST_STEP)
        self.assertEqual(era_b.effective_from, pricing.ERA_B_FIRST_STEP)
        self.assertFalse(
            era_a.covers(pricing.parse_instant(pricing.ERA_B_FIRST_STEP)),  # type: ignore[arg-type]
            "the boundary instant belongs to era B alone",
        )
        self.assertTrue(
            era_b.covers(pricing.parse_instant(pricing.ERA_B_FIRST_STEP))  # type: ignore[arg-type]
        )

    def test_there_is_NO_cache_write_rate_column(self):
        """cache_write was measured 0 in all 29611 steps, so a write rate is untestable invention."""

        rates = pricing.MEASURED_ERAS[0].rates
        self.assertFalse(hasattr(rates, "cache_write_per_mtok"))
        payload = rates.to_dict()
        self.assertIsNone(payload["cache_write_per_mtok"])
        self.assertIn("measured 0", payload["cache_write_note"])
        with self.assertRaises(pricing.PricingRefusal):
            rates.rate_for("cache_write")
        self.assertNotIn("cache_write", pricing.PRICED_COMPONENTS)

    def test_a_nonzero_cache_write_is_REFUSED_rather_than_mispriced(self):
        """DECISION 03-aflsz3-D2's falsification path: the licensing measurement no longer holds."""

        report = pricing.validate_against_recorded(
            [
                {
                    "tokens": {"input": 1000, "cache": 5000},
                    "at": "2026-09-01T00:00:00Z",
                    "cost": 1.0,
                    "cache_write": 42,
                }
            ]
        )
        self.assertEqual(report["refusals"], 1)
        self.assertEqual(report["steps_priced"], 0)
        self.assertIn("cache_write=42", report["refusal_detail"][0]["reason"])
        self.assertIn(
            "REFUSES rather than mispricing", report["refusal_detail"][0]["reason"]
        )

    def test_a_REASONING_bearing_step_is_REFUSED_rather_than_estimated(self):
        """These ARE the measured 23 residual steps; pricing one omits a billed component."""

        priced = pricing.price_step(
            tokens={"input": 1000, "output": 100, "reasoning": 50},
            at="2026-09-01T00:00:00Z",
        )
        self.assertTrue(priced.is_refused)
        self.assertIsNone(priced.estimated_usd)
        self.assertIn("reasoning=50", priced.refusal_reason)
        self.assertIn("23 residual steps", priced.refusal_reason)

    def test_a_reasoning_key_of_ZERO_is_priced_normally(self):
        """The refusal is on a BILLED reasoning component, not on the key's presence."""

        priced = pricing.price_step(
            tokens={"input": 1000, "reasoning": 0}, at="2026-09-01T00:00:00Z"
        )
        self.assertFalse(priced.is_refused)

    def test_an_UNPRICED_MODEL_is_refused_and_NAMED(self):
        priced = pricing.price_step(
            tokens={"input": 1000},
            at="2026-09-01T00:00:00Z",
            model="google/gemini-3.8-flash",
        )
        self.assertTrue(priced.is_refused)
        self.assertIn("google/gemini-3.8-flash", priced.refusal_reason)

    def test_an_UNKNOWN_DATE_is_refused_rather_than_priced_at_the_current_era(self):
        priced = pricing.price_step(tokens={"input": 1000}, at="2020-01-01T00:00:00Z")
        self.assertTrue(priced.is_refused)
        self.assertIn("no price era covers", priced.refusal_reason)

    def test_an_UNPARSEABLE_INSTANT_is_refused(self):
        for bad in ("", "not-a-date", "2026-13-45T99:99:99Z"):
            with self.subTest(bad=bad):
                priced = pricing.price_step(tokens={"input": 1000}, at=bad)
                self.assertTrue(priced.is_refused)

    def test_a_CURRENCY_MISMATCH_is_refused(self):
        priced = pricing.price_step(
            tokens={"input": 1000}, at="2026-09-01T00:00:00Z", currency="EUR"
        )
        self.assertTrue(priced.is_refused)
        self.assertIn("currency mismatch", priced.refusal_reason)

    def test_an_UNKNOWN_MODEL_with_no_era_match_refuses_rather_than_inheriting_rates(
        self,
    ):
        """A model-specific schedule must not silently price an unknown model."""

        schedule = pricing.PriceSchedule(
            eras=(
                pricing.PriceEra(
                    era_id="only-a",
                    provider="prov",
                    model="model-a",
                    rates=pricing.PriceRates(1.0, 2.0, 0.1),
                    effective_from="2026-01-01T00:00:00Z",
                ),
            )
        )
        priced = pricing.price_step(
            tokens={"input": 1000},
            at="2026-09-01T00:00:00Z",
            schedule=schedule,
            provider="prov",
            model="model-UNKNOWN",
        )
        self.assertTrue(priced.is_refused)

    def test_RECORDED_and_ESTIMATED_cost_are_kept_SEPARATE_and_recorded_never_overwritten(
        self,
    ):
        priced = pricing.price_step(
            tokens={"input": 1_000_000}, at="2026-09-01T00:00:00Z", recorded_usd=99.0
        )
        self.assertEqual(priced.recorded_usd, 99.0, "recorded is untouched")
        self.assertAlmostEqual(priced.estimated_usd or 0.0, 5.50, places=9)
        self.assertEqual(priced.authoritative_usd, 99.0, "recorded always wins")
        self.assertFalse(priced.cost_is_estimate)
        self.assertNotAlmostEqual(priced.delta or 0.0, 0.0)

    def test_cost_is_estimate_is_True_ONLY_when_no_recorded_value_exists(self):
        estimated = pricing.price_step(
            tokens={"input": 1000}, at="2026-09-01T00:00:00Z"
        )
        self.assertTrue(estimated.cost_is_estimate)
        self.assertEqual(estimated.authoritative_usd, estimated.estimated_usd)

    def test_the_schedule_REPRODUCES_recorded_cost_EXACTLY_across_both_eras(self):
        """The property the authoring plan believed unobtainable, demonstrated on both eras."""

        steps = []
        for at, rates in (
            ("2026-08-01T00:00:00Z", (5.00, 25.00, 0.00)),
            ("2026-09-01T00:00:00Z", (5.50, 27.50, 0.55)),
        ):
            for n in range(1, 11):
                tokens = {"input": n * 1000, "output": n * 100, "cache": n * 50_000}
                exact = (
                    tokens["input"] * rates[0]
                    + tokens["output"] * rates[1]
                    + tokens["cache"] * rates[2]
                ) / 1_000_000
                steps.append({"tokens": tokens, "at": at, "cost": exact})

        report = pricing.validate_against_recorded(steps)
        self.assertEqual(report["steps_priced"], 20)
        self.assertEqual(report["exact_matches"], 20)
        self.assertEqual(report["mismatches"], 0)
        self.assertEqual(report["per_era"]["era-a"]["exact"], 10)
        self.assertEqual(report["per_era"]["era-b"]["exact"], 10)
        self.assertIs(report["has_cache_write_rate_column"], False)

    def test_a_WRONG_rate_is_caught_rather_than_absorbed_by_tolerance(self):
        """A control: the exact-match report must be able to FAIL, or it proves nothing."""

        report = pricing.validate_against_recorded(
            [
                {
                    "tokens": {"input": 1_000_000},
                    "at": "2026-09-01T00:00:00Z",
                    "cost": 999.0,
                }
            ]
        )
        self.assertEqual(report["exact_matches"], 0)
        self.assertEqual(report["mismatches"], 1)
        self.assertAlmostEqual(
            report["mismatch_detail"][0]["delta"], 5.50 - 999.0, places=6
        )

    def test_the_default_tolerance_is_FLOATING_POINT_and_not_a_business_tolerance(self):
        priced = pricing.PricedCost(
            estimated_usd=1.0, recorded_usd=1.0 + 1e-12, era_id="era-b"
        )
        self.assertTrue(priced.reproduces_exactly())
        loose = pricing.PricedCost(estimated_usd=1.0, recorded_usd=1.01, era_id="era-b")
        self.assertFalse(
            loose.reproduces_exactly(), "a 1 percent error is not an exact match"
        )

    def test_a_NEGATIVE_rate_is_refused_at_construction(self):
        with self.assertRaises(pricing.PricingRefusal):
            pricing.PriceRates(-1.0, 25.0, 0.0)

    def test_stratify_by_era_separates_the_two_eras(self):
        grouped = pricing.stratify_by_era(
            [
                {"at": "2026-08-01T00:00:00Z"},
                {"at": "2026-09-01T00:00:00Z"},
                {"at": "2020-01-01T00:00:00Z"},
            ]
        )
        self.assertEqual(len(grouped["era-a"]), 1)
        self.assertEqual(len(grouped["era-b"]), 1)
        self.assertEqual(
            len(grouped["unknown"]), 1, "an unresolvable era is kept, not dropped"
        )

    def test_component_spend_shares_show_cache_dominating_era_B(self):
        """Measured: 72.1 percent of Era B spend is cache_read."""

        steps = [
            {
                "tokens": {"input": 60_000, "output": 20_000, "cache": 5_715_743},
                "at": "2026-09-01T00:00:00Z",
            }
        ]
        shares = pricing.component_spend_shares(steps)["per_era_shares"]["era-b"]
        self.assertGreater(shares["cache"], 0.70)
        self.assertLess(shares["input"], 0.10)

    def test_the_schedule_report_is_pasteable_and_names_the_absent_write_column(self):
        report = pricing.MEASURED_SCHEDULE.format_report()
        self.assertIn("era-a", report)
        self.assertIn("era-b", report)
        self.assertIn("NO cache_write rate column", report)
        self.assertIn("exact_matches=7917", report)
        self.assertIn("exact_matches=21731", report)

    def test_the_measured_exact_match_counts_are_recorded_as_evidence(self):
        self.assertEqual(pricing.MEASURED_ERAS[0].exact_match_count, 7917)
        self.assertEqual(pricing.MEASURED_ERAS[1].exact_match_count, 21731)
        self.assertEqual(
            pricing.MEASURED_ERAS[0].source,
            "fit-to-recorded-cost",
            "recovered from the corpus, therefore checkable",
        )


class AnalysisResultContractTests(unittest.TestCase):
    """The shape every analysis returns, and the guard a renderer cannot skip."""

    def test_only_a_COMPUTED_verdict_is_renderable(self):
        for verdict, expected in (
            (Verdict.COMPUTED, True),
            (Verdict.CANNOT_DETERMINE, False),
            (Verdict.REFUSED, False),
        ):
            with self.subTest(verdict=verdict.value):
                result = st.AnalysisResult(name="x", verdict=verdict, sample_size=5)
                self.assertEqual(result.renderable, expected)

    def test_require_values_REFUSES_rather_than_returning_an_empty_dict(self):
        """An empty dict is the thing a renderer would plot as zero."""

        result = st.AnalysisResult(
            name="x", verdict=Verdict.REFUSED, sample_size=2, reason="not enough"
        )
        with self.assertRaises(StatisticsError):
            result.require_values()

    def test_the_serialized_form_carries_the_verdict_sample_size_and_caveats(self):
        payload = st.AnalysisResult(
            name="x", verdict=Verdict.COMPUTED, sample_size=20, caveats=("careful",)
        ).to_dict()
        for key in ("verdict", "sample_size", "caveats", "renderable", "is_derived"):
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
