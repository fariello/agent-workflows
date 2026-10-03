"""Tests for IPD qgpanb (Set sevreg Order 01).

Pin the registration of the five live drift rules, their recorded severities,
emitter agreement for lane drift, the emitter stamp reaching the gate on a
fixture repository, and preservation of the fail-closed fallback.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    artifact_core,
    attention,
    check_engine,
    research_cmd,
    research_contract,
    research_index,
    runner_shared,
)


class DriftRuleRegistrationTests(unittest.TestCase):
    """Pin the properties established by IPD qgpanb."""

    FIVE_RULES = (
        "attention.lane-stranded",
        "attention.lane-superseded",
        "dangling-citation",
        "adopted-without-consumer",
        "stale-state-to-promote",
    )

    def test_property_1_registration_resolves_non_default_spec(self):
        """(1) check_engine.rule_spec returns a registered spec (not _DEFAULT_RULESPEC)."""
        default_spec = check_engine._DEFAULT_RULESPEC
        for rule_id in self.FIVE_RULES:
            resolved = check_engine.rule_spec(rule_id)
            self.assertIsNot(
                resolved,
                default_spec,
                f"Rule {rule_id} unexpectedly resolved to fallback _DEFAULT_RULESPEC",
            )

    def test_property_2_per_rule_severities(self):
        """(2) Severities: lane-stranded is error, lane-superseded is info, research/plans are info."""
        self.assertEqual(
            check_engine.rule_spec("attention.lane-stranded").severity, "error"
        )
        self.assertEqual(
            check_engine.rule_spec("attention.lane-superseded").severity, "info"
        )
        self.assertEqual(check_engine.rule_spec("dangling-citation").severity, "info")
        self.assertEqual(
            check_engine.rule_spec("adopted-without-consumer").severity, "info"
        )
        self.assertEqual(
            check_engine.rule_spec("stale-state-to-promote").severity, "info"
        )

    def test_property_3_emitter_agreement_for_lane_pair(self):
        """(3) attention.lane_drift_severity matches rule_spec for lane states."""
        # STRANDED -> attention.lane-stranded (error)
        stranded_severity = attention.lane_drift_severity(runner_shared.LANE_STRANDED)
        stranded_spec = check_engine.rule_spec("attention.lane-stranded")
        self.assertEqual(stranded_severity, stranded_spec.severity)

        # SUPERSEDED -> attention.lane-superseded (info)
        superseded_severity = attention.lane_drift_severity(
            runner_shared.LANE_SUPERSEDED
        )
        superseded_spec = check_engine.rule_spec("attention.lane-superseded")
        self.assertEqual(superseded_severity, superseded_spec.severity)

    def test_property_4_emitter_stamp_reaches_gate_on_fixture(self):
        """(4) Emitter stamp reaches gate on a temporary fixture repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rroot = root / research_contract.RESEARCH_ROOT
            rroot.mkdir(parents=True, exist_ok=True)

            # 1. doc tripping adopted-without-consumer
            doc_name = research_contract.format_name(
                research_contract.ResearchName(
                    date="20260701",
                    set_id="testset",
                    order="00",
                    id6="adopt1",
                    slug="adopt-test",
                    model=None,
                    kind="research-report",
                )
            )
            frontmatter = research_cmd.build_frontmatter(
                id6="adopt1",
                created="20260701",
                set_id="testset",
                order="00",
                topic=["test"],
                model=None,
                kind="research-report",
                status="reference",
                outcome="adopted",
                summary="summary adopt1",
            )
            (rroot / doc_name).write_text(frontmatter, encoding="utf-8")

            # 2. dangling citation in DECISIONS.md
            (root / "DECISIONS.md").write_text(
                "cite 20260601-old-00-dangle-gone.notes.md\n", encoding="utf-8"
            )

            # Regenerate manifest so index-missing/stale do not interfere
            entries, _ = research_index._scan_docs(rroot)
            (rroot / research_index.INDEX_JSON).write_text(
                research_index.build_index_json(entries), encoding="utf-8"
            )
            (rroot / research_index.INDEX_MD).write_text(
                research_index.build_index_md(entries), encoding="utf-8"
            )

            drift = research_index.check_drift(root, rroot)
            rules = {d.rule: d.severity for d in drift}

            self.assertIn("adopted-without-consumer", rules)
            self.assertIn("dangling-citation", rules)
            self.assertEqual(rules["adopted-without-consumer"], "info")
            self.assertEqual(rules["dangling-citation"], "info")

            exit_code = artifact_core.drift_exit_code(drift)
            self.assertEqual(exit_code, 0)

    def test_property_5_fail_closed_preserved_for_unregistered_rules(self):
        """(5) rule_spec on an unregistered rule id still returns severity error."""
        unregistered = "completely-unregistered-test-rule-id-xyz"
        spec = check_engine.rule_spec(unregistered)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec, check_engine._DEFAULT_RULESPEC)
