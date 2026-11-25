"""Tests for duplicated single-valued metadata bullet detection on specs (IPD 1znlxy).

Exercises specs.validate_spec on constructed spec texts (behavior testing, no code-pinning):
(a) duplicated - Blocks-Release: is reported once with the expected detail;
(b) duplicated - Gate-Kind: on a deferred spec is reported and does not suppress or duplicate existing gate findings:
    (b1) both lines carry the same valid kind with a valid - Gate-Ref:, so the new rule is the only finding;
    (b2) the lines carry different kinds where the first one makes the ref invalid, so exactly one attention.gate-malformed
         and exactly one spec.metadata-bullet-repeated are both present;
(c) four - Constrained-by: lines are not reported;
(d) a duplicate appearing only after the first ## heading (prose example) is not reported;
(e) a conformant single-valued spec yields no finding;
(f) the rule id is present in check_engine.RULE_REGISTRY with severity error.
"""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import artifact_meta, check_engine, spec_citations, specs
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
        """(b2) lines carry different kinds where the first one (which `artifact_meta.read_text`, the one
        metadata reader, keeps) makes the ref invalid: gate-malformed and bullet-repeated."""
        text = RecordBuilder().spec(
            title="Deferred Different Gate-Kinds",
            status="deferred",
            gate_kind="decision",
            gate_ref="2027-01-01",
            history=["- 2026-10-01 deferred: waiting"],
            raw_fields={"Gate-Kind": "decision\n- Gate-Kind: date"},
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

    @pytest.mark.core
    def test_run_migrate_captures_trailing_prose_status_via_artifact_meta(self):
        """specs.run_migrate preserves legacy trailing-prose `- Status:` values via artifact_meta."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            specs_dir = root / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_path = specs_dir / "20261124-ab12cd-01-ab12cd-legacy-status.spec.md"
            spec_path.write_text(
                "# Spec: Legacy Status\n\n"
                "- Id: ab12cd\n"
                "- Status: approved (2026-09-25 legacy note)\n\n"
                "## Scope\n\n"
                "Body text.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                path=str(spec_path),
                status="approved",
                canonical=False,
                gate_kind=None,
                gate_ref=None,
                gate_summary=None,
                date="2026-11-24",
            )
            rc = specs.run_migrate(args)
            self.assertEqual(rc, 0)
            migrated = spec_path.read_text(encoding="utf-8")
            self.assertIn("- Status: approved\n", migrated)
            self.assertIn("(was: approved (2026-09-25 legacy note))", migrated)
            self.assertEqual(specs.validate_spec(spec_path, migrated), [])
            self.assertEqual(
                artifact_meta.read_text(migrated, record_type="spec").id6, "ab12cd"
            )

    @pytest.mark.core
    def test_refusals_read_loose_id_bullets_via_artifact_meta(self):
        """_review_attestation_refusal and _deferred_ids_refusal read loose -Id: / -  Id: bullets."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            specs_dir = root / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_path = specs_dir / "20261124-ab12cd-01-ab12cd-loose.spec.md"

            for bullet, expected_id in (
                ("-Id: ab12cd", "ab12cd"),
                ("-  Id:   cd34ef  ", "cd34ef"),
            ):
                text = (
                    "# Spec: Loose Id\n\n"
                    f"{bullet}\n"
                    "- Status: to-review\n\n"
                    "## Requirements\n\n"
                    "- R-1 [Deferred]: Deferred requirement.\n"
                )
                review_msg = specs._review_attestation_refusal(spec_path, text)
                self.assertIsNotNone(review_msg)
                self.assertIn(f"- Subject-Id: {expected_id}", review_msg or "")

                deferred_msg = specs._deferred_ids_refusal(spec_path, text)
                self.assertIsNotNone(deferred_msg)
                self.assertIn(f"spec {expected_id}", deferred_msg or "")
                self.assertIn("R-1", deferred_msg or "")

            body_only_text = (
                "# Spec: Body Id Only\n\n"
                "- Status: to-review\n\n"
                "## Requirements\n\n"
                "- Id: zz99yy\n"
                "- R-1 [Deferred]: Deferred requirement.\n"
            )
            review_msg_body = specs._review_attestation_refusal(
                spec_path, body_only_text
            )
            self.assertIsNotNone(review_msg_body)
            self.assertIn("- Subject-Id: <spec-id6>", review_msg_body or "")
            self.assertNotIn("zz99yy", review_msg_body or "")

            deferred_msg_body = specs._deferred_ids_refusal(spec_path, body_only_text)
            self.assertIsNotNone(deferred_msg_body)
            self.assertIn(spec_path.name, deferred_msg_body or "")
            self.assertNotIn("zz99yy", deferred_msg_body or "")

    @pytest.mark.core
    def test_stale_spec_anchors_resolves_spec_id_via_artifact_meta(self):
        """spec_citations.stale_spec_anchors resolves spec id6 through artifact_meta.read_text."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            specs_dir = root / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            (specs_dir / "20261124-xy12zw-01-xy12zw-sample.spec.md").write_text(
                "# Spec: Sample\n\n"
                "- Id: xy12zw\n"
                "- Status: approved\n\n"
                "## 1. Real Heading\n\n"
                "Body line.\n",
                encoding="utf-8",
            )
            (specs_dir / "20261124-bad000-01-bad000-body-only.spec.md").write_text(
                "# Spec: Body Id Only\n\n"
                "- Status: approved\n\n"
                "## 1. Body\n\n"
                "- Id: qq88rr\n",
                encoding="utf-8",
            )
            src_dir = root / "agent_workflows"
            src_dir.mkdir(parents=True)
            py_path = src_dir / "sample.py"
            py_path.write_text(
                "# spec xy12zw:999\n# spec qq88rr:999\n",
                encoding="utf-8",
            )

            findings = spec_citations.stale_spec_anchors(root, [py_path])
            resolved_ids = [f.id6 for f in findings if f.id6]
            self.assertEqual(resolved_ids, ["xy12zw"])
            xy_findings = [f for f in findings if f.id6 == "xy12zw"]
            self.assertEqual(len(xy_findings), 1)
            self.assertEqual(xy_findings[0].offset, 999)
            self.assertEqual(xy_findings[0].validity, "past_eof")
