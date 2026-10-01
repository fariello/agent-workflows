"""Tests for decision-ref grammar widening and check.decision-ref-dangling resolution.

Covers:
(1) validate_gate_ref accepts additive-suffixed decision IDs (D22b, D23b, D24b).
(2) validate_gate_ref accepts all heading IDs parsed from the live DECISIONS.md (floor > 100).
(3) validate_gate_ref rejects malformed and unanchored tokens (d12, D, D1x2, empty, D12-garbage).
(4) parse_decision_ids fails open to empty set on absent file.
(5) parse_decision_ids parses headings only and ignores body-only tokens (PR-D02, IPD-D701, D401).
(6) check_decision_ref_dangling reports a dangling decision ref on a throwaway tree.
(7) check_decision_ref_dangling reports nothing for a resolvable decision ref.
(8) check_decision_ref_dangling skips a malformed decision ref (no double reporting).
(9) check_decision_ref_dangling returns nothing when DECISIONS.md is absent (managed-repo portability).
(10) Falsifiable negative asserting finding rule id and warning severity.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from agent_workflows import attention_contract as A
from agent_workflows import check_engine


class DecisionRefResolutionTests(unittest.TestCase):
    def test_suffixed_decision_refs_accepted(self):
        """Case 1: validate_gate_ref accepts the three additive-suffixed headings in DECISIONS.md."""
        self.assertTrue(A.validate_gate_ref("decision", "D22b"))
        self.assertTrue(A.validate_gate_ref("decision", "D23b"))
        self.assertTrue(A.validate_gate_ref("decision", "D24b"))

    def test_all_live_decision_headings_accepted(self):
        """Case 2: every heading id parsed from the live DECISIONS.md is accepted by validate_gate_ref.

        Asserts a floor above 100 (never equality with a pinned live count).
        """
        repo_root = Path(__file__).resolve().parent.parent
        decisions_path = repo_root / "DECISIONS.md"
        self.assertTrue(
            decisions_path.is_file(), "DECISIONS.md must exist in this toolkit repo"
        )
        heading_ids = check_engine.parse_decision_ids(decisions_path)
        self.assertGreater(
            len(heading_ids), 100, "Must parse a substantive floor of headings (>100)"
        )
        for d_id in sorted(heading_ids):
            self.assertTrue(
                A.validate_gate_ref("decision", d_id),
                f"validate_gate_ref rejected parsed heading {d_id!r}",
            )

    def test_rejections_and_anchoring(self):
        """Case 3: existing malformed cases still fail, and D12-garbage confirms both ends are anchored."""
        self.assertFalse(A.validate_gate_ref("decision", "d12"))
        self.assertFalse(A.validate_gate_ref("decision", "D"))
        self.assertFalse(A.validate_gate_ref("decision", "D1x2"))
        self.assertFalse(A.validate_gate_ref("decision", ""))
        self.assertFalse(A.validate_gate_ref("decision", "D12-garbage"))

    def test_parser_absent_file(self):
        """Case 4: parse_decision_ids returns an empty set for an absent file rather than raising."""
        nonexistent = Path("/nonexistent/path/to/DECISIONS.md")
        result = check_engine.parse_decision_ids(nonexistent)
        self.assertEqual(result, set())

    def test_parser_ignores_body_tokens(self):
        """Case 5: parse_decision_ids does not return body-only tokens sharing the shape.

        Given a log with PR-D02, IPD-D701, and D401 in body prose and one real heading,
        it must return only the real heading id.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "DECISIONS.md"
            log_path.write_text(
                "# Project Decisions\n\n"
                "Prose mentioning PR-D02 finding, IPD-D701 retired lint, and D401 noqa tag.\n\n"
                "### D42. Real ruling that is a heading\n\n"
                "Body referencing D99 in text.\n",
                encoding="utf-8",
            )
            parsed = check_engine.parse_decision_ids(log_path)
            self.assertEqual(parsed, {"D42"})

    def test_sweep_reports_dangling_decision_ref(self):
        """Case 6: check_decision_ref_dangling reports a dangling decision ref on a throwaway tree."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "DECISIONS.md").write_text(
                "### D10. Existing ruling\n", encoding="utf-8"
            )
            item_dir = root / ".aw" / "records" / "backlog" / "blocked"
            item_dir.mkdir(parents=True)
            (item_dir / "20261001-test01-01-aaaaaa-item.backlog.md").write_text(
                "- Id: aaaaaa\n"
                "- Status: blocked\n"
                "- Set: test01\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: test item\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D999\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (test): created\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0].rule, "check.decision-ref-dangling")
            self.assertIn("D999", drift[0].detail)

    def test_sweep_reports_nothing_for_resolvable_ref(self):
        """Case 7: check_decision_ref_dangling reports nothing when the ref resolves to a heading."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "DECISIONS.md").write_text(
                "### D10. Existing ruling\n", encoding="utf-8"
            )
            item_dir = root / ".aw" / "records" / "backlog" / "blocked"
            item_dir.mkdir(parents=True)
            (item_dir / "20261001-test01-01-aaaaaa-item.backlog.md").write_text(
                "- Id: aaaaaa\n"
                "- Status: blocked\n"
                "- Set: test01\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: test item\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D10\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (test): created\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(drift, [])

    def test_sweep_skips_malformed_ref(self):
        """Case 8: check_decision_ref_dangling does not report a malformed ref (avoids double-reporting)."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "DECISIONS.md").write_text(
                "### D10. Existing ruling\n", encoding="utf-8"
            )
            item_dir = root / ".aw" / "records" / "backlog" / "blocked"
            item_dir.mkdir(parents=True)
            (item_dir / "20261001-test01-01-aaaaaa-item.backlog.md").write_text(
                "- Id: aaaaaa\n"
                "- Status: blocked\n"
                "- Set: test01\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: test item\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D10-garbage\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (test): created\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(drift, [])

    def test_sweep_suppressed_when_decisions_log_absent(self):
        """Case 9: THE MANAGED-REPO CASE: a tree carrying a decision gate and NO DECISIONS.md yields zero findings.

        This ensures check_engine does not emit false positives in managed target repos
        where DECISIONS.md is not installed.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertFalse((root / "DECISIONS.md").exists())
            item_dir = root / ".aw" / "records" / "backlog" / "blocked"
            item_dir.mkdir(parents=True)
            (item_dir / "20261001-test01-01-aaaaaa-item.backlog.md").write_text(
                "- Id: aaaaaa\n"
                "- Status: blocked\n"
                "- Set: test01\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: test item\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D999\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (test): created\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(drift, [])

    def test_falsifiable_negative_rule_id_and_severity(self):
        """Case 10: Falsifiable negative asserting the rule id and severity of the emitted finding."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "DECISIONS.md").write_text(
                "### D10. Existing ruling\n", encoding="utf-8"
            )
            item_dir = root / ".aw" / "records" / "backlog" / "blocked"
            item_dir.mkdir(parents=True)
            (item_dir / "20261001-test01-01-aaaaaa-item.backlog.md").write_text(
                "- Id: aaaaaa\n"
                "- Status: blocked\n"
                "- Set: test01\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: test item\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D999\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (test): created\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(len(drift), 1)
            finding = drift[0]
            # Exact assertions on rule id and warning severity:
            self.assertEqual(finding.rule, "check.decision-ref-dangling")
            self.assertEqual(finding.severity, "warning")

    def test_sweep_reports_dangling_decision_ref_in_spec(self):
        """Extra coverage: verify that spec records carrying a dangling decision gate are also flagged."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "DECISIONS.md").write_text(
                "### D10. Existing ruling\n", encoding="utf-8"
            )
            spec_dir = root / ".aw" / "records" / "specs" / "approved"
            spec_dir.mkdir(parents=True)
            (spec_dir / "20261001-test01-01-bbbbbb-spec.spec.md").write_text(
                "# Spec: Test\n\n"
                "- Id: bbbbbb\n"
                "- Status: approved\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D999\n\n"
                "## Workflow history\n"
                "- 2026-10-01 approved (test): approved\n\n"
                "Prose\n",
                encoding="utf-8",
            )
            drift = check_engine.check_decision_ref_dangling(root)
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0].rule, "check.decision-ref-dangling")
            self.assertIn("D999", drift[0].detail)
