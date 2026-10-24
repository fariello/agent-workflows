"""Behavioral tests for benchmark ablation cell key, metric summaries, and gate results.

Restores behavioral coverage for residual benchmark keys recorded in backlog item nzc6dm
(Set trimgap), plan 1z19cn, and research findings wo21z5.
"""

from __future__ import annotations

import json
import unittest

import pytest

from agent_workflows import benchmark_ablations
from agent_workflows import benchmark_metrics
from agent_workflows import benchmark_runners
from agent_workflows import benchmark_thresholds

pytestmark = pytest.mark.core


class CellKeyTests(unittest.TestCase):
    """Behavioral tests for AblationTrialSpec.cell_key and schedule cell partitioning."""

    def test_ablation_trial_spec_cell_key(self) -> None:
        mp = benchmark_runners.ModelProfile(
            model_id="m1",
            reasoning_effort="high",
            display_name="M",
            vendor="v",
        )
        scheduler = benchmark_ablations.AblationScheduler(
            task_seeds=["t1"],
            model_profiles=[mp],
            hosts=["opencode"],
            architectures=[
                benchmark_ablations.ARCH_MONOLITH,
                benchmark_ablations.ARCH_MODULAR,
            ],
            trial_count=2,
            timeout_seconds=60.0,
            random_seed=7,
        )
        specs = scheduler.generate_schedule()
        assert len(specs) == 4

        # The set of their cell_key values is exactly {("t1","m1","high","opencode",1), ("t1","m1","high","opencode",2)}
        cell_keys = {s.cell_key for s in specs}
        assert cell_keys == {
            ("t1", "m1", "high", "opencode", 1),
            ("t1", "m1", "high", "opencode", 2),
        }

        # Each of those two keys is carried by exactly two specs whose ablation_config.architecture values are {ARCH_MONOLITH, ARCH_MODULAR}
        for key in cell_keys:
            matching = [s for s in specs if s.cell_key == key]
            assert len(matching) == 2
            assert {s.ablation_config.architecture for s in matching} == {
                benchmark_ablations.ARCH_MONOLITH,
                benchmark_ablations.ARCH_MODULAR,
            }

        # A single AblationTrialSpec built directly with trial=2 has cell_key == ("t1","m1","high","opencode",2)
        ceilings = benchmark_ablations.make_ceilings(
            per_trial_wall_seconds=60.0,
            trial_count=2,
        )
        direct_spec = benchmark_ablations.AblationTrialSpec(
            task_seed="t1",
            model_profile=mp,
            host="opencode",
            ablation_config=benchmark_ablations.STANDARD_ABLATION_CONFIGS[
                benchmark_ablations.ARCH_MONOLITH
            ],
            trial=2,
            timeout_seconds=60.0,
            ceilings=ceilings,
            order_index=0,
        )
        assert direct_spec.cell_key == ("t1", "m1", "high", "opencode", 2)


class MetricSummaryToDictTests(unittest.TestCase):
    """Behavioral tests for MetricSummary.to_dict payload formatting."""

    def test_metric_summary_to_dict_payload(self) -> None:
        summary_dict = benchmark_metrics.compute_aggregate_metrics([]).to_dict()
        assert set(summary_dict.keys()) == {
            "sample_size",
            "completed_trials",
            "pending_trials",
            "metrics",
            "credits_or_quota_records",
        }
        assert summary_dict["sample_size"] == 0
        assert len(summary_dict["metrics"]) == 14
        assert summary_dict["metrics"]["task_correctness"] == {
            "name": "task_correctness",
            "value": 0.0,
            "sample_size": 0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "is_available": True,
            "unit": "ratio",
        }
        dumped = json.dumps(summary_dict)
        assert json.loads(dumped) == summary_dict


class GateEvaluationResultToDictTests(unittest.TestCase):
    """Behavioral tests for GateEvaluationResult.to_dict serialization."""

    def test_gate_evaluation_result_to_dict_payload(self) -> None:
        result = benchmark_thresholds.GateEvaluationResult(
            passed=False,
            risk_class="high",
            findings=("f1", "f2"),
            checked_thresholds={"a": False},
            model_profile_name="m",
        ).to_dict()
        assert result == {
            "passed": False,
            "risk_class": "high",
            "findings": ["f1", "f2"],
            "checked_thresholds": {"a": False},
            "model_profile_name": "m",
        }

    def test_gate_evaluation_result_to_dict_default_model_profile_name(self) -> None:
        result = benchmark_thresholds.GateEvaluationResult(
            passed=True,
            risk_class="low",
            findings=(),
            checked_thresholds={},
        ).to_dict()
        assert result["model_profile_name"] is None
