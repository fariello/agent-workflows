"""Tests for duplicated single-valued metadata bullet detection on specs (IPD 1znlxy).

Exercises specs.validate_spec on constructed spec texts (behavior testing, no code-pinning):
(a) duplicated - Blocks-Release: is reported once with the expected detail;
(b) duplicated - Gate-Kind: on a deferred spec is reported and does not suppress or duplicate existing gate findings:
    (b1) both lines carry the same valid kind with a valid - Gate-Ref:, so the new rule is the only finding;
    (b2) the lines carry different kinds where the last one makes the ref invalid, so exactly one attention.gate-malformed
         and exactly one spec.metadata-bullet-repeated are both present;
(c) four - Constrained-by: lines are not reported;
(d) a duplicate appearing only after the first ## heading (prose example) is not reported;
(e) a conformant single-valued spec yields no finding;
(f) the rule id is present in check_engine.RULE_REGISTRY with severity error.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import check_engine, specs
from tests.record_builder import RecordBuilder


class TestSpecsMetadataDuplicateBullet(unittest.TestCase):
    def test_duplicated_blocks_release(self):
        """(a) duplicated - Blocks-Release: is reported once with the expected detail."""
        text = RecordBuilder().spec(
            title="Duplicate Blocks-Release",
            status="approved",
            history=["- 2026-10-01 approved: ok"],
            raw_fields={"Blocks-Release": "next\n- Blocks-Release: future"},
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].rule, "spec.metadata-bullet-repeated")
        self.assertEqual(
            drift[0].detail, "metadata bullet - Blocks-Release: appears 2 times"
        )
        self.assertFalse(Path(drift[0].location).is_absolute())

    def test_duplicated_gate_kind_same_valid(self):
        """(b1) both lines carry the same valid kind with a valid - Gate-Ref:, new rule is only finding."""
        text = RecordBuilder().spec(
            title="Deferred Same Valid Gate-Kind",
            status="deferred",
            gate_kind="date",
            gate_ref="2027-01-01",
            history=["- 2026-10-01 deferred: waiting for date"],
            raw_fields={"Gate-Kind": "date\n- Gate-Kind: date"},
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].rule, "spec.metadata-bullet-repeated")
        self.assertEqual(
            drift[0].detail, "metadata bullet - Gate-Kind: appears 2 times"
        )

    def test_duplicated_gate_kind_different_invalid_ref(self):
        """(b2) lines carry different kinds where last one makes ref invalid: gate-malformed and bullet-repeated."""
        text = RecordBuilder().spec(
            title="Deferred Different Gate-Kinds",
            status="deferred",
            gate_kind="date",
            gate_ref="2027-01-01",
            history=["- 2026-10-01 deferred: waiting"],
            raw_fields={"Gate-Kind": "date\n- Gate-Kind: decision"},
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        rules = [d.rule for d in drift]
        self.assertEqual(
            rules.count("spec.metadata-bullet-repeated"),
            1,
            f"Expected exactly one spec.metadata-bullet-repeated, got {rules}",
        )
        self.assertEqual(
            rules.count("attention.gate-malformed"),
            1,
            f"Expected exactly one attention.gate-malformed, got {rules}",
        )
        self.assertEqual(len(drift), 2)

    def test_constrained_by_allowlisted(self):
        """(c) four - Constrained-by: lines are not reported as duplicates."""
        text = RecordBuilder().spec(
            title="Multi Constrained-by",
            status="approved",
            history=["- 2026-10-01 approved: ok"],
            raw_fields={
                "Constrained-by": (
                    "spec1\n- Constrained-by: spec2\n"
                    "- Constrained-by: spec3\n- Constrained-by: spec4"
                )
            },
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        repeated_findings = [
            d for d in drift if d.rule == "spec.metadata-bullet-repeated"
        ]
        self.assertEqual(repeated_findings, [])
        self.assertEqual(drift, [])

    def test_duplicate_in_prose_body_ignored(self):
        """(d) a duplicate appearing only after the first ## heading is not reported."""
        text = RecordBuilder().spec(
            title="Prose Duplicate",
            status="approved",
            blocks_release="next",
            history=["- 2026-10-01 approved: ok"],
            body="## Section 1: Examples\n\nHere is a prose example of duplicated fields:\n- Blocks-Release: first\n- Blocks-Release: second",
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        repeated_findings = [
            d for d in drift if d.rule == "spec.metadata-bullet-repeated"
        ]
        self.assertEqual(repeated_findings, [])
        self.assertEqual(drift, [])

    def test_conformant_single_valued_spec(self):
        """(e) a conformant single-valued spec yields no finding."""
        text = RecordBuilder().spec(
            title="Conformant Single Valued",
            status="approved",
            blocks_release="next",
            priority="low",
            work_kind="chore",
            history=["- 2026-10-01 approved: ok"],
            text_only=True,
        )
        drift = specs.validate_spec(Path(".aw/records/specs/test.spec.md"), text)
        self.assertEqual(drift, [])

    def test_rule_registry_entry(self):
        """(f) the rule id is present in check_engine.RULE_REGISTRY with severity error."""
        self.assertIn("spec.metadata-bullet-repeated", check_engine.RULE_REGISTRY)
        rule_spec = check_engine.RULE_REGISTRY["spec.metadata-bullet-repeated"]
        self.assertEqual(rule_spec.severity, "error")
