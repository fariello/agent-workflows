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

    def test_quantiles_deterministic_and_refusals(self):
        values = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(st.quantile(values, 0.0), 1.0)
        self.assertEqual(st.quantile(values, 1.0), 4.0)
        self.assertEqual(st.quantile(values, 0.5), 2.5)
        self.assertEqual(st.quantile(values, 0.25), 1.75)
        self.assertEqual(st.quantile([7.0], 0.5), 7.0)

        with self.assertRaises(StatisticsError) as ctx:
            st.quantile([], 0.5)
        self.assertIn("is not zero", str(ctx.exception))

        for bad in (-0.1, 1.1, 2.0):
            with self.subTest(q=bad):
                with self.assertRaises(StatisticsError):
                    st.quantile([1.0, 2.0], bad)

    def test_missing_values_and_empty_sample_never_zero(self):
        distribution = st.describe("x", [1.0, None, 3.0, None])
        self.assertEqual(distribution.sample_size, 2)
        self.assertEqual(distribution.missing_count, 2)
        self.assertEqual(distribution.mean, 2.0)
        self.assertAlmostEqual(distribution.coverage, 0.5)

        empty = st.describe("x", [])
        self.assertEqual(empty.sample_size, 0)
        for value in (
            empty.mean,
            empty.median,
            empty.stdev,
            empty.minimum,
            empty.maximum,
            empty.p90,
        ):
            self.assertIsNone(value)

        nan_sample = st.describe(
            "x", [1.0, float("nan"), float("inf"), True, "12", None]
        )  # type: ignore[list-item]
        self.assertEqual(nan_sample.sample_size, 1)
        self.assertEqual(nan_sample.missing_count, 5)

    def test_describe_sample_properties_and_distinct_zero_vs_absent(self):
        self.assertIsNone(st.describe("x", [5.0]).stdev)
        self.assertIsNotNone(st.describe("x", [5.0, 7.0]).stdev)

        skewed = st.describe("x", [1.0] * 9 + [1000.0])
        self.assertEqual(skewed.median, 1.0)
        self.assertGreater(skewed.mean or 0, 100.0)

        zeros = st.describe("x", [0.0, 0.0, 0.0])
        absent = st.describe("x", [None, None, None])
        self.assertEqual(zeros.sample_size, 3)
        self.assertEqual(zeros.mean, 0.0)
        self.assertEqual(absent.sample_size, 0)
        self.assertIsNone(absent.mean)


class MetricValueReuseTests(unittest.TestCase):
    """E-08 and DECISION 03-aflsz3-D3: the SHIPPED vocabulary is reused, not copied."""

    def test_metric_value_vocabulary_and_wilson_interval(self):
        metrics = st.describe("cost", [1.0, 2.0, 3.0], unit="USD").as_metric_values()
        for name, metric in metrics.items():
            self.assertIs(type(metric), MetricValue)
            self.assertEqual(metric.sample_size, 3)
            self.assertEqual(metric.unit, "USD")

        empty_metrics = st.describe("cost", [], unit="USD").as_metric_values()
        self.assertFalse(empty_metrics["mean"].is_available)
        self.assertIsNone(empty_metrics["mean"].value)

        self.assertIs(st.wilson_score_interval, benchmark_metrics.wilson_score_interval)

    def test_benchmark_dollar_cost_guard_and_no_third_party_dependencies(self):
        for forbidden in ("cost", "usd", "price", "dollars", "spending", "dollar_cost"):
            self.assertIn(forbidden, benchmark_metrics._FORBIDDEN_COST_KEYS)

        with self.assertRaises(benchmark_metrics.MetricError):
            benchmark_metrics.evaluate_trial_metrics(
                _FakeTrial(usage={"cost": 1.0}),  # type: ignore[arg-type]
            )


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

    def test_unattributed_time_ratio_serialization_and_scaling(self):
        model = st.build_time_model(
            wall_seconds=1000.0,
            activities=[{"session_id": "s1", "start": 0.0, "end": 38.0}],
        )
        self.assertAlmostEqual(model.observed_activity_seconds, 38.0)
        self.assertAlmostEqual(model.unattributed_seconds, 962.0)
        self.assertAlmostEqual(model.activity_share_of_wall, 0.038)
        self.assertAlmostEqual(model.unattributed_share_of_wall, 0.962)
        self.assertEqual(model.dominant_term(), "unattributed")

        payload = model.to_dict()
        self.assertEqual(list(payload)[0], "unattributed_seconds")
        self.assertEqual(payload["dominant_term"], "unattributed")

        # Activity is not scaled up to fill elapsed time
        self.assertNotAlmostEqual(model.wall_seconds, model.observed_activity_seconds)

    def test_shared_sessions_overlap_negatives_and_malformed(self):
        # Shared session counted once
        model = st.build_time_model(
            wall_seconds=200.0,
            activities=[
                {"session_id": "s1", "start": 0.0, "end": 100.0},
                {"session_id": "s1", "start": 0.0, "end": 100.0},
            ],
        )
        self.assertAlmostEqual(model.observed_activity_seconds, 100.0)
        self.assertAlmostEqual(model.double_counted_seconds_avoided, 100.0)
        self.assertEqual(model.shared_session_count, 1)

        # Overlapping activities
        overlap_model = st.build_time_model(
            wall_seconds=100.0,
            activities=[
                {"session_id": "s1", "start": 0.0, "end": 20.0},
                {"session_id": "s1", "start": 10.0, "end": 30.0},
            ],
        )
        self.assertAlmostEqual(overlap_model.observed_activity_seconds, 30.0)
        self.assertAlmostEqual(overlap_model.overlap_seconds, 10.0)

        # Negative unattributed value reported
        neg_model = st.build_time_model(
            wall_seconds=10.0,
            activities=[{"session_id": "s", "start": 0.0, "end": 50.0}],
        )
        self.assertLess(neg_model.unattributed_seconds, 0.0)

        # Malformed activity skipped
        clean = st.build_time_model(
            wall_seconds=100.0,
            activities=[
                {"session_id": "s", "start": None, "end": 10.0},
                {"session_id": "s", "start": 10.0, "end": 5.0},
                {"session_id": "s", "start": "x", "end": "y"},
                {"session_id": "s", "start": 0.0, "end": 10.0},
            ],
        )
        self.assertAlmostEqual(clean.observed_activity_seconds, 10.0)


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

    def test_instruction_burden_tokens_dollars_and_inventory(self):
        res = self._burden()
        values = res.values
        self.assertEqual(values["median_first_step_input_tokens"], 15067.0)
        self.assertAlmostEqual(
            values["cost_per_turn_usd"], 15067 * 5.50 / 1_000_000, places=6
        )
        self.assertAlmostEqual(values["total_injected_cost_usd"], 8.28685, places=4)

        footnote = values["read_time_footnote"]
        self.assertEqual(footnote["share_of_wall_time_percent"], "0.014%")
        self.assertIn("0.014%", footnote["derivation"])
        self.assertEqual(footnote["label"], "FOOTNOTE, NOT A HEADLINE")
        self.assertIn("NOT-CURRENT", footnote["basis"])

        self.assertEqual(values["standing_instruction_bytes"]["AGENTS.md"], 33101)
        self.assertEqual(
            values["standing_instruction_tokens_approx"]["AGENTS.md"], 8275
        )
        self.assertGreater(values["standing_instruction_total_bytes"], 33101)

    def test_instruction_burden_observed_fallback_and_under_powered(self):
        observed = self._burden(
            read_tool_seconds=10.0, tool_seconds=1000.0, wall_seconds=100_000.0
        ).values["read_time_footnote"]
        self.assertEqual(observed["basis"], "observed-in-this-corpus")
        self.assertAlmostEqual(observed["share_of_tool_time"], 0.01)

        # Partial set falls back to snapshot
        partial = self._burden(read_tool_seconds=10.0, tool_seconds=1000.0).values[
            "read_time_footnote"
        ]
        self.assertIn("NOT-CURRENT", partial["basis"])

        # Under-powered sample refuses
        refusal = self._burden(first_step_input_tokens=[15067.0, 15067.0])
        self.assertIs(refusal.verdict, Verdict.CANNOT_DETERMINE)
        self.assertFalse(refusal.renderable)


class UnderPowerRefusalTests(unittest.TestCase):
    """E-06: the four measured slices refuse, and a chart CANNOT be produced from a refusal."""

    def test_shared_predicate_and_refusal_rendering_guard(self):
        for n in (0, 1, 3, 6, st.MINIMUM_SAMPLE_SIZE - 1):
            result = st.under_power_verdict("x", n)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
            self.assertEqual(result.sample_size, n)

        for n in (st.MINIMUM_SAMPLE_SIZE, st.MINIMUM_SAMPLE_SIZE + 1):
            self.assertIsNone(st.under_power_verdict("x", n))

        # Chart request on underpowered analysis refuses
        for name, result in st.refuse_under_powered_required_analyses().items():
            self.assertIs(result.verdict, Verdict.CANNOT_DETERMINE)
            self.assertFalse(result.renderable)
            with self.assertRaises(StatisticsError) as ctx:
                result.require_values()
            self.assertIn("cannot-determine", str(ctx.exception))

    def test_grown_analysis_and_baseline_properties(self):
        # Grown sample computes
        grown = st.refuse_under_powered_required_analyses(
            {"merge_conflict_attempts": 500, "items_with_multiple_attempts": 500}
        )
        for name, result in grown.items():
            self.assertIs(result.verdict, Verdict.COMPUTED)
            self.assertEqual(result.sample_size, 500)

        baseline = st.CORPUS_BASELINE
        self.assertEqual(baseline["queue_item_count"], 733)
        self.assertEqual(baseline["items_with_multiple_attempts"], 6)
        self.assertEqual(baseline["recovery_attempts"], 6)
        self.assertEqual(baseline["merge_conflict_attempts"], 3)
        self.assertEqual(baseline["provenance"], "review-time-snapshot")
        self.assertIs(baseline["is_current"], False)


class ModelComparisonRefusalTests(unittest.TestCase):
    """E-08: the model arm REFUSES at the measured 1.1 percent coverage; price-era proceeds."""

    def test_model_comparison_refusal_and_caveats(self):
        attempts = [{"cost": 1.0} for _ in range(177)] + [
            {"cost": 1.0, "model": "provider/model-a"},
            {"cost": 1.0, "model": "provider/model-b"},
        ]
        result = st.model_comparison(attempts)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertFalse(result.renderable)
        self.assertEqual(result.sample_size, 2)
        self.assertAlmostEqual(result.values["observed_coverage"], 2 / 179, places=6)

        # Host default identifies nothing
        default_res = st.model_comparison([{"model": "host-default", "cost": 1.0}] * 50)
        self.assertIs(default_res.verdict, Verdict.REFUSED)

        caveats = " ".join(st.model_comparison([{"cost": 1.0}] * 10).caveats)
        self.assertIn("run date", caveats)
        self.assertIn("PRICE ERA", caveats)
        self.assertIn("sub-agent", caveats)
        self.assertIn("price-era stratification IS available", caveats)

    def test_model_comparison_computes_with_coverage_and_baseline(self):
        attempts = [{"model": "provider/model-a", "cost": 1.0} for _ in range(20)] + [
            {"model": "provider/model-b", "cost": 2.0} for _ in range(20)
        ]
        result = st.model_comparison(attempts)
        self.assertIs(result.verdict, Verdict.COMPUTED)
        self.assertEqual(
            set(result.values["per_model_cost_usd"]),
            {"provider/model-a", "provider/model-b"},
        )

        baseline = st.CORPUS_BASELINE
        self.assertEqual(baseline["attempts_with_resolvable_model"], 2)
        self.assertEqual(baseline["runs_with_null_options_model"], 130)
        self.assertAlmostEqual(baseline["model_identity_coverage"], 0.011)


class VerifierPhaseTests(unittest.TestCase):
    """E-06: the verifier phase is DERIVED from a filename and must be labeled derived."""

    def test_verifier_phase_parsing_from_filenames(self):
        phase, derived = st.verifier_phase_of_log("03-aflsz3-attempt-1-verify.jsonl")
        self.assertEqual(phase, "verify")
        self.assertTrue(derived)

        phase2, derived2 = st.verifier_phase_of_log("03-aflsz3-attempt-1.jsonl")
        self.assertEqual(phase2, "execute")
        self.assertTrue(derived2)

        phase3, _ = st.verifier_phase_of_log(
            "/some/where/sessions/01-abc123-attempt-2-verify.jsonl"
        )
        self.assertEqual(phase3, "verify")

    def test_verifier_phase_summary_and_baseline(self):
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
        self.assertEqual(result.values["cost_by_phase_usd"]["verify"], 1.0)
        self.assertEqual(result.values["cost_by_phase_usd"]["execute"], 10.0)
        self.assertEqual(result.values["cost_by_phase_usd"]["review"], 5.0)

        baseline = st.CORPUS_BASELINE
        self.assertEqual(baseline["verifier_log_count"], 57)
        self.assertEqual(baseline["verifier_log_cost_usd"], 64.08)
        self.assertEqual(baseline["attempts_with_verify_cost"], 0)


class SupportedAnalysisTests(unittest.TestCase):
    """E-05: the analyses the corpus supports, each with a schema-level AND numeric assertion."""

    def test_per_ipd_usage_and_cache_utilization(self):
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
        for key in ("cost_usd", "tokens", "wall_seconds", "attempts_per_ipd"):
            self.assertIn(key, values)
        self.assertAlmostEqual(values["cost_usd"]["median"], 10.5)

        # Retried IPD counted once in sample_size, costs summed
        retried_attempts = [{"ipd_id6": "same01", "cost": 1.0} for _ in range(5)] + [
            {"ipd_id6": f"id{n:04d}", "cost": 1.0} for n in range(20)
        ]
        retried_res = st.per_ipd_usage(retried_attempts)
        self.assertEqual(retried_res.sample_size, 21)
        self.assertEqual(retried_res.require_values()["cost_usd"]["maximum"], 5.0)

        # Under-powered per-ipd refuses
        self.assertIs(
            st.per_ipd_usage([{"ipd_id6": "a", "cost": 1.0}]).verdict,
            Verdict.CANNOT_DETERMINE,
        )

        # Cache utilization
        cache_res = st.cache_utilization(
            token_components={
                "input": 60_000_000,
                "output": 20_000_000,
                "cache": 5_715_743_803,
                "total": 5_795_743_803,
            },
            cost_by_component={"input": 216.0, "output": 588.0, "cache": 2051.0},
        )
        cvalues = cache_res.require_values()
        self.assertAlmostEqual(cvalues["cache_share_of_tokens"], 0.9862, places=4)
        self.assertAlmostEqual(cvalues["cache_share_of_spend"], 0.7183, places=3)

    def test_implementation_versus_inspection(self):
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
        self.assertLess(share["ci_lower"], share["value"])
        self.assertGreater(share["ci_upper"], share["value"])
        self.assertAlmostEqual(
            values["file_category_shares"]["source-code"], 3200 / 7453, places=6
        )

    def test_cost_concentration_and_session_gradient(self):
        # Cost concentration
        costs = [1.0] * 90 + [10.0] * 10
        result = st.cost_concentration(costs)
        values = result.require_values()
        self.assertAlmostEqual(values["total_spend_usd"], 190.0)
        self.assertAlmostEqual(
            values["top_decile_spend_share"], 100.0 / 190.0, places=6
        )
        self.assertIs(
            st.cost_concentration([0.0] * 20).verdict, Verdict.CANNOT_DETERMINE
        )

        # Within-session gradient
        steps = []
        for session in range(20):
            for position in range(20):
                cost = 0.0781 + (0.1290 - 0.0781) * position / 19
                steps.append(
                    {"session_id": f"s{session}", "position": position, "cost": cost}
                )
        grad_res = st.within_session_gradient(steps)
        gvals = grad_res.require_values()
        self.assertEqual(gvals["session_count"], 20)
        self.assertTrue(gvals["is_monotonic_increasing"])
        self.assertAlmostEqual(gvals["first_decile_mean_cost_usd"], 0.0794, places=3)
        self.assertAlmostEqual(gvals["last_decile_mean_cost_usd"], 0.1277, places=3)

        caveats = " ".join(st.within_session_gradient(steps).caveats)
        self.assertIn("context growth", caveats)
        self.assertIn("harder work", caveats)

        # Excludes short sessions
        short = [
            {"session_id": f"s{s}", "position": p, "cost": 0.1}
            for s in range(50)
            for p in range(3)
        ]
        self.assertIs(
            st.within_session_gradient(short).verdict, Verdict.CANNOT_DETERMINE
        )

    def test_missingness_bias_and_measured_baseline(self):
        logs = {f"s{n}": 10.0 for n in range(100)}
        attempts = {f"s{n}": 10.0 for n in range(87)}
        result = st.missingness_bias(session_log_costs=logs, attempt_costs=attempts)
        values = result.require_values()
        self.assertAlmostEqual(values["session_log_total_usd"], 1000.0)
        self.assertAlmostEqual(values["recorded_attempt_total_usd"], 870.0)
        self.assertAlmostEqual(values["unaccounted_usd"], 130.0)
        self.assertEqual(values["unaccounted_session_count"], 13)

        # Attempt with no log
        no_log = st.missingness_bias(
            session_log_costs={"s1": 1.0}, attempt_costs={"s1": 1.0, "s2": 5.0}
        )
        self.assertEqual(no_log.values["attempts_without_a_log_count"], 1)

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

    def test_pricing_eras_boundaries_and_rates(self):
        # Era A
        priced_a = pricing.price_step(
            tokens={"input": 1_000_000, "output": 100_000, "cache": 10_000_000},
            at="2026-08-01T00:00:00Z",
        )
        self.assertEqual(priced_a.era_id, "era-a")
        self.assertAlmostEqual(priced_a.estimated_usd or 0.0, 5.0 + 2.5 + 0.0, places=9)
        self.assertEqual(priced_a.component_costs["cache"], 0.0)

        # Era B
        priced_b = pricing.price_step(
            tokens={"input": 1_000_000, "output": 100_000, "cache": 10_000_000},
            at="2026-09-01T00:00:00Z",
        )
        self.assertEqual(priced_b.era_id, "era-b")
        self.assertAlmostEqual(
            priced_b.estimated_usd or 0.0, 5.50 + 2.75 + 5.50, places=9
        )

        # Boundaries
        self.assertEqual(pricing.ERA_A_LAST_STEP, "2026-08-29T01:30:43Z")
        self.assertEqual(pricing.ERA_B_FIRST_STEP, "2026-08-29T05:38:43Z")
        self.assertEqual(
            pricing.price_step(
                tokens={"input": 1000}, at=pricing.ERA_A_LAST_STEP
            ).era_id,
            "era-a",
        )
        self.assertEqual(
            pricing.price_step(
                tokens={"input": 1000}, at=pricing.ERA_B_FIRST_STEP
            ).era_id,
            "era-b",
        )

        era_a, era_b = pricing.MEASURED_ERAS
        self.assertFalse(era_a.covers(pricing.parse_instant(pricing.ERA_B_FIRST_STEP)))  # type: ignore[arg-type]
        self.assertTrue(era_b.covers(pricing.parse_instant(pricing.ERA_B_FIRST_STEP)))  # type: ignore[arg-type]

        # No cache write rate column
        rates = pricing.MEASURED_ERAS[0].rates
        self.assertFalse(hasattr(rates, "cache_write_per_mtok"))
        with self.assertRaises(pricing.PricingRefusal):
            rates.rate_for("cache_write")

    def test_pricing_refusals(self):
        # Nonzero cache write
        rep_cw = pricing.validate_against_recorded(
            [
                {
                    "tokens": {"input": 1000, "cache": 5000},
                    "at": "2026-09-01T00:00:00Z",
                    "cost": 1.0,
                    "cache_write": 42,
                }
            ]
        )
        self.assertEqual(rep_cw["refusals"], 1)

        # Reasoning > 0 refused, reasoning == 0 priced
        priced_reas = pricing.price_step(
            tokens={"input": 1000, "reasoning": 50}, at="2026-09-01T00:00:00Z"
        )
        self.assertTrue(priced_reas.is_refused)
        self.assertFalse(
            pricing.price_step(
                tokens={"input": 1000, "reasoning": 0}, at="2026-09-01T00:00:00Z"
            ).is_refused
        )

        # Unpriced model
        self.assertTrue(
            pricing.price_step(
                tokens={"input": 1000},
                at="2026-09-01T00:00:00Z",
                model="google/gemini-3.8-flash",
            ).is_refused
        )

        # Unknown or unparseable date
        self.assertTrue(
            pricing.price_step(
                tokens={"input": 1000}, at="2020-01-01T00:00:00Z"
            ).is_refused
        )
        for bad in ("", "not-a-date", "2026-13-45T99:99:99Z"):
            self.assertTrue(
                pricing.price_step(tokens={"input": 1000}, at=bad).is_refused
            )

        # Currency mismatch
        self.assertTrue(
            pricing.price_step(
                tokens={"input": 1000}, at="2026-09-01T00:00:00Z", currency="EUR"
            ).is_refused
        )

        # Unknown model schedule
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
        self.assertTrue(
            pricing.price_step(
                tokens={"input": 1000},
                at="2026-09-01T00:00:00Z",
                schedule=schedule,
                provider="prov",
                model="model-UNKNOWN",
            ).is_refused
        )

        # Negative rate refused
        with self.assertRaises(pricing.PricingRefusal):
            pricing.PriceRates(-1.0, 25.0, 0.0)

    def test_recorded_vs_estimated_cost_semantics(self):
        priced = pricing.price_step(
            tokens={"input": 1_000_000}, at="2026-09-01T00:00:00Z", recorded_usd=99.0
        )
        self.assertEqual(priced.recorded_usd, 99.0)
        self.assertAlmostEqual(priced.estimated_usd or 0.0, 5.50, places=9)
        self.assertEqual(priced.authoritative_usd, 99.0)
        self.assertFalse(priced.cost_is_estimate)

        estimated = pricing.price_step(
            tokens={"input": 1000}, at="2026-09-01T00:00:00Z"
        )
        self.assertTrue(estimated.cost_is_estimate)
        self.assertEqual(estimated.authoritative_usd, estimated.estimated_usd)

    def test_schedule_reproduction_validation_and_tolerance(self):
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

        # Wrong rate caught
        wrong_rep = pricing.validate_against_recorded(
            [
                {
                    "tokens": {"input": 1_000_000},
                    "at": "2026-09-01T00:00:00Z",
                    "cost": 999.0,
                }
            ]
        )
        self.assertEqual(wrong_rep["exact_matches"], 0)
        self.assertEqual(wrong_rep["mismatches"], 1)

        # Floating point tolerance
        self.assertTrue(
            pricing.PricedCost(
                estimated_usd=1.0, recorded_usd=1.0 + 1e-12, era_id="era-b"
            ).reproduces_exactly()
        )
        self.assertFalse(
            pricing.PricedCost(
                estimated_usd=1.0, recorded_usd=1.01, era_id="era-b"
            ).reproduces_exactly()
        )

    def test_stratification_spend_shares_and_report(self):
        grouped = pricing.stratify_by_era(
            [
                {"at": "2026-08-01T00:00:00Z"},
                {"at": "2026-09-01T00:00:00Z"},
                {"at": "2020-01-01T00:00:00Z"},
            ]
        )
        self.assertEqual(len(grouped["era-a"]), 1)
        self.assertEqual(len(grouped["era-b"]), 1)
        self.assertEqual(len(grouped["unknown"]), 1)

        steps = [
            {
                "tokens": {"input": 60_000, "output": 20_000, "cache": 5_715_743},
                "at": "2026-09-01T00:00:00Z",
            }
        ]
        shares = pricing.component_spend_shares(steps)["per_era_shares"]["era-b"]
        self.assertGreater(shares["cache"], 0.70)
        self.assertLess(shares["input"], 0.10)

        report = pricing.MEASURED_SCHEDULE.format_report()
        self.assertIn("era-a", report)
        self.assertIn("era-b", report)
        self.assertEqual(pricing.MEASURED_ERAS[0].exact_match_count, 7917)
        self.assertEqual(pricing.MEASURED_ERAS[1].exact_match_count, 21731)


class AnalysisResultContractTests(unittest.TestCase):
    """The shape every analysis returns, and the guard a renderer cannot skip."""

    def test_analysis_result_contract_verdicts_and_serialization(self):
        self.assertTrue(
            st.AnalysisResult(
                name="x", verdict=Verdict.COMPUTED, sample_size=5
            ).renderable
        )
        self.assertFalse(
            st.AnalysisResult(
                name="x", verdict=Verdict.CANNOT_DETERMINE, sample_size=5
            ).renderable
        )
        self.assertFalse(
            st.AnalysisResult(
                name="x", verdict=Verdict.REFUSED, sample_size=5
            ).renderable
        )

        refused = st.AnalysisResult(
            name="x", verdict=Verdict.REFUSED, sample_size=2, reason="not enough"
        )
        with self.assertRaises(StatisticsError):
            refused.require_values()

        payload = st.AnalysisResult(
            name="x", verdict=Verdict.COMPUTED, sample_size=20, caveats=("careful",)
        ).to_dict()
        for key in ("verdict", "sample_size", "caveats", "renderable", "is_derived"):
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
