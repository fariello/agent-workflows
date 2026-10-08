"""Restored docs_render test coverage.

Plan t9lcdu / Set gzmr54.
Restores test coverage deleted in 19313eed for agent_workflows/docs_render.py.
"""

from __future__ import annotations

import datetime
import unittest

from agent_workflows import benchmark_thresholds as bt
from agent_workflows import docs_render as dr
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr
from agent_workflows import workflow_profile as wp


class SupportTableRendersFromRegistryTests(unittest.TestCase):
    def test_unpromoted_capability_renders_unverified(self):
        # Build adapters against an EMPTY registry: everything must render 'unverified'.
        registry = hcr.HostCapabilityRegistry()
        adapters = {
            h: ha.build_host_adapter(h, registry, "1.0.0") for h in ha.ALL_ADAPTER_HOSTS
        }
        table = dr.render_support_table(adapters)
        self.assertIn("Source: host capability-evidence registry", table)
        # No feature was promoted, so no row may claim 'supported'.
        for line in table.splitlines():
            if line.startswith("| ") and " supported " in f" {line} ":
                self.fail(f"unpromoted capability claimed supported: {line}")

    def test_provenance_line_present(self):
        registry = hcr.HostCapabilityRegistry()
        adapters = {
            h: ha.build_host_adapter(h, registry, "1.0.0") for h in ha.ALL_ADAPTER_HOSTS
        }
        table = dr.render_support_table(adapters)
        self.assertIn(
            "A feature is 'supported' only where a live probe promoted it", table
        )

    def test_promoted_capability_renders_supported_positive_control(self):
        # Positive control: promote exactly ONE capability and assert only that cell renders supported.
        registry = hcr.HostCapabilityRegistry()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        pos_rec = hcr.EvidenceRecord(
            host="opencode",
            distribution="native",
            exact_version="1.0.0",
            os="linux",
            mode="default",
            feature="skill",
            configuration={},
            probe_variant="default",
            result=hcr.STATUS_SUPPORTED,
            evidence_artifact="probe-ok.json",
            observed_date=now_str,
            expiry=None,
            source_type=hcr.SOURCE_ISOLATED_PROBE,
            resolved=True,
            followed=True,
            side_effect_verified=True,
            diagnostic_evidence="Verified ok",
        )
        registry.promote_capability(
            "opencode", "1.0.0", "skill", positive_probe=pos_rec
        )
        adapters = {
            h: ha.build_host_adapter(h, registry, "1.0.0") for h in ha.ALL_ADAPTER_HOSTS
        }
        table = dr.render_support_table(adapters)

        supported_rows = [
            line
            for line in table.splitlines()
            if line.startswith("| ") and " supported " in f" {line} "
        ]
        self.assertEqual(len(supported_rows), 1)
        self.assertIn("opencode", supported_rows[0])
        self.assertIn("skill", supported_rows[0])


class BenchmarkThresholdTableTests(unittest.TestCase):
    def test_renders_invariants_from_policy(self):
        policy = bt.ThresholdPolicy()
        table = dr.render_benchmark_thresholds_table(policy)
        self.assertIn("Source: benchmark threshold policy", table)
        self.assertIn(
            "Critical escapes must be 0 and evidence validity must be 1.0", table
        )
        # Every risk class in policy must show 0 critical escapes and 1.0 evidence validity.
        for risk_class in sorted(policy.thresholds):
            matching_rows = [
                line
                for line in table.splitlines()
                if line.startswith(f"| {risk_class} |")
            ]
            self.assertEqual(
                len(matching_rows),
                1,
                f"Expected exactly one row for risk class {risk_class}",
            )
            row = matching_rows[0]
            self.assertTrue(
                row.endswith("| 0 | 1.0 |"),
                f"Row for {risk_class} did not end with '| 0 | 1.0 |': {row}",
            )


class ModelProfileTableTests(unittest.TestCase):
    def test_model_id_distinct_from_profile(self):
        table = dr.render_model_profile_table(
            [
                {
                    "model_id": "(operator-selected)",
                    "profile": {"name": "default", "reasoning_level": "medium"},
                    "notes": "baseline",
                }
            ],
            benchmark_date="2026-08-21",
            host="opencode",
            host_version="1.0.0",
            uncertainty="+/- 0.03 (n=30)",
            pending_combinations=["claude_code x max reasoning"],
        )
        # Header records provenance, and the model ID + reasoning are SEPARATE columns.
        self.assertIn("Benchmark date: 2026-08-21", table)
        self.assertIn("Task corpus:", table)
        self.assertIn("Host / version: opencode 1.0.0", table)
        self.assertIn("Measurement uncertainty:", table)
        self.assertIn("| Model ID | Profile | Reasoning config |", table)
        self.assertIn("(operator-selected)", table)
        self.assertIn("Pending", table)
        self.assertIn("claude_code x max reasoning", table)

    def test_no_universal_quality_claim(self):
        table = dr.render_model_profile_table(
            [{"model_id": "m", "profile": {"name": "p"}}],
            benchmark_date="2026-08-21",
        )
        self.assertIn("not a universal quality claim", table)

    def test_disallowed_profile_key_rejected(self):
        # FALSIFIABLE: smuggling a semantic override under an unknown profile key is rejected.
        with self.assertRaises(wp.ProfileError):
            dr.render_model_profile_table(
                [
                    {
                        "model_id": "m",
                        "profile": {"name": "p", "smuggled_semantics": "x"},
                    }
                ],
                benchmark_date="2026-08-21",
            )

    def test_row_order_follows_input_sequence(self):
        profiles = [
            {"model_id": "model-first", "profile": {"name": "p1"}},
            {"model_id": "model-second", "profile": {"name": "p2"}},
            {"model_id": "model-third", "profile": {"name": "p3"}},
        ]
        table = dr.render_model_profile_table(profiles, benchmark_date="2026-08-21")
        idx_first = table.index("model-first")
        idx_second = table.index("model-second")
        idx_third = table.index("model-third")
        self.assertTrue(idx_first < idx_second < idx_third)

    def test_empty_pending_combinations_omits_pending_section(self):
        profiles = [{"model_id": "m", "profile": {"name": "p"}}]
        table = dr.render_model_profile_table(
            profiles,
            benchmark_date="2026-08-21",
            pending_combinations=[],
        )
        self.assertNotIn("Pending", table)


if __name__ == "__main__":
    unittest.main()
