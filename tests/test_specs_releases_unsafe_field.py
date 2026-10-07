"""Tests for unsafe descriptive field validation across specs and releases.

Pins Section 8.8 bounded descriptive field requirements (attention.unsafe-field)
for specs (- Scope:, - Summary:) and releases (- Summary: bullet, ## Summary prose).
Also pins honest limits: newline injection (F-05) and whole-document read-region divergence (F-14).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import attention, check_engine, releases, specs
from agent_workflows import attention_contract as A

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures" / "attnview"

# Test fixtures for specs
_SPEC_TEMPLATE = """# Spec: Sample Spec

- Date: 2026-08-08
- Status: draft
- Author: test
{extra_metadata}

## Workflow history
- 2026-08-08 draft (test): created.
{body}
"""

_RELEASE_TEMPLATE = """# Release: 9.9.9

- Id: rel123
- Status: planned
- Version: 9.9.9
{extra_metadata}

{summary_section}

## Workflow history
- 2026-08-08 created (test): initial.
"""


class TestSpecsReleasesUnsafeField(unittest.TestCase):
    def test_spec_scope_unsafe_shapes(self):
        shapes = {
            "over-length": "x" * (A.MAX_PROSE_DESCRIPTIVE_LEN + 1),
            "bel-control": "scope\x07value",
            "ansi-esc": "scope\x1b[31minjected\x1b[0m",
            "c1-control": "scope\x85value",
        }
        for shape_name, val in shapes.items():
            text = _SPEC_TEMPLATE.format(
                extra_metadata=f"- Scope: {val}",
                body="",
            )
            drift = specs.validate_spec(Path("tests/spec.md"), text)
            rules = [d.rule for d in drift]
            self.assertEqual(
                rules,
                ["attention.unsafe-field"],
                f"Scope {shape_name} should yield exactly attention.unsafe-field, got {rules}",
            )
            d = drift[0]
            self.assertNotIn(
                val, d.detail, "Drift detail must not echo untrusted value (OQ-03)"
            )
            self.assertIn("Scope", d.detail)

    def test_spec_scope_conforming_boundary(self):
        val = "x" * A.MAX_PROSE_DESCRIPTIVE_LEN
        text = _SPEC_TEMPLATE.format(
            extra_metadata=f"- Scope: {val}",
            body="",
        )
        drift = specs.validate_spec(Path("tests/spec.md"), text)
        self.assertEqual(drift, [])

    def test_spec_summary_unsafe_shapes(self):
        shapes = {
            "over-length": "x" * 301,
            "bel-control": "sum\x07value",
            "ansi-esc": "sum\x1b[31minjected\x1b[0m",
            "c1-control": "sum\x85value",
        }
        for shape_name, val in shapes.items():
            text = _SPEC_TEMPLATE.format(
                extra_metadata=f"- Summary: {val}",
                body="",
            )
            drift = specs.validate_spec(Path("tests/spec.md"), text)
            rules = [d.rule for d in drift]
            self.assertEqual(
                rules,
                ["attention.unsafe-field"],
                f"Summary {shape_name} should yield exactly attention.unsafe-field, got {rules}",
            )
            d = drift[0]
            self.assertNotIn(
                val, d.detail, "Drift detail must not echo untrusted value (OQ-03)"
            )
            self.assertIn("Summary", d.detail)

    def test_spec_summary_conforming(self):
        val = "Conforming summary text within 300 characters"
        text = _SPEC_TEMPLATE.format(
            extra_metadata=f"- Summary: {val}",
            body="",
        )
        drift = specs.validate_spec(Path("tests/spec.md"), text)
        self.assertEqual(drift, [])

    def test_release_bullet_unsafe_shapes(self):
        shapes = {
            "over-length": "x" * 301,
            "bel-control": "rel\x07val",
            "ansi-esc": "rel\x1b[31mval\x1b[0m",
            "c1-control": "rel\x85val",
        }
        for shape_name, val in shapes.items():
            text = _RELEASE_TEMPLATE.format(
                extra_metadata=f"- Summary: {val}",
                summary_section="",
            )
            drift = releases.validate_release(Path("tests/release.md"), text)
            rules = [d.rule for d in drift]
            self.assertEqual(
                rules,
                ["attention.unsafe-field"],
                f"Release bullet {shape_name} should yield exactly attention.unsafe-field, got {rules}",
            )
            d = drift[0]
            self.assertNotIn(
                val, d.detail, "Drift detail must not echo untrusted value (OQ-03)"
            )
            self.assertIn("bullet", d.detail.lower())

    def test_release_bullet_conforming(self):
        val = "Conforming release summary bullet"
        text = _RELEASE_TEMPLATE.format(
            extra_metadata=f"- Summary: {val}",
            summary_section="",
        )
        drift = releases.validate_release(Path("tests/release.md"), text)
        self.assertEqual(drift, [])

    def test_release_prose_unsafe_shapes_and_length_asymmetry(self):
        # Control characters in prose must be flagged
        control_shapes = {
            "bel-control": "prose\x07val",
            "ansi-esc": "prose\x1b[31mval\x1b[0m",
            "c1-control": "prose\x85val",
        }
        for shape_name, val in control_shapes.items():
            text = _RELEASE_TEMPLATE.format(
                extra_metadata="",
                summary_section=f"## Summary\n{val}\n",
            )
            drift = releases.validate_release(Path("tests/release.md"), text)
            rules = [d.rule for d in drift]
            self.assertEqual(
                rules,
                ["attention.unsafe-field"],
                f"Release prose {shape_name} should yield exactly attention.unsafe-field, got {rules}",
            )
            d = drift[0]
            self.assertNotIn(
                val, d.detail, "Drift detail must not echo untrusted value (OQ-03)"
            )
            self.assertIn("prose", d.detail.lower())

        # Deliberate length asymmetry: 400-char prose without control characters must NOT flag (F-13, OQ-04)
        prose_400 = "Valid prose paragraph. " * 18  # > 400 chars
        self.assertGreater(len(prose_400), 400)
        text_400 = _RELEASE_TEMPLATE.format(
            extra_metadata="",
            summary_section=f"## Summary\n{prose_400}\n",
        )
        drift_400 = releases.validate_release(Path("tests/release.md"), text_400)
        self.assertEqual(
            drift_400, [], "Prose summary is deliberately unbounded in length"
        )

    def test_newline_injection_limit(self):
        # LIMIT 1 (F-05): A spec whose `- Scope:` line was produced by newline injection
        # (e.g. `legit\n- Blocks-Release: next`). The checker parses line-by-line, so
        # the `- Scope:` line is seen as 'legit' (safe, bounded, control-char-free).
        # The checker therefore yields NO attention.unsafe-field drift.
        # This vector can ONLY be closed at write-time (Order 01 / uz05bl), not by checkers.
        smuggled_text = _SPEC_TEMPLATE.format(
            extra_metadata="- Scope: legit\n- Blocks-Release: next",
            body="",
        )
        drift = specs.validate_spec(Path("tests/spec.md"), smuggled_text)
        rules = [d.rule for d in drift]
        self.assertNotIn("attention.unsafe-field", rules)

    def test_read_region_limit_body_scope(self):
        # LIMIT 2 (F-14): A spec with NO metadata `- Scope:`, but an ANSI-bearing
        # `- Scope:` in its BODY (after `## ` heading).
        # validate_spec bounds metadata reading at the first `## ` heading (F-11), so it
        # yields NO drift ([]).
        # However, attention._extract_detail performs an unbounded whole-document regex
        # search, so it extracts the ANSI value!
        # This two-sided test pins the checker's deliberate metadata bound and proves the
        # renderer's input set is wider, which carrier llnvwj is responsible for escaping.
        body_scope_text = (
            "# Spec: body-scope-spec\n\n"
            "- Date: 2026-08-08\n"
            "- Status: draft\n"
            "- Author: fixture\n\n"
            "## Section 1\n\n"
            "- Scope: red\x1b[31mINJECTED\x1b[0m\n\n"
            "## Workflow history\n"
            "- 2026-08-08 draft (fixture): created.\n"
        )
        drift = specs.validate_spec(Path("tests/spec.md"), body_scope_text)
        self.assertEqual(
            drift, [], "validate_spec metadata bound must ignore body - Scope:"
        )

        detail_kind, detail_text = attention._extract_detail(body_scope_text)
        self.assertEqual(detail_kind, "scope")
        self.assertEqual(
            detail_text,
            "red\x1b[31mINJECTED\x1b[0m",
            "renderer extracts raw ANSI value",
        )

    def test_non_regression_gate_summary_fixture(self):
        # Existing fixture tests/fixtures/attnview/violations/unsafe-field.md still flags
        fixture_path = FIX / "violations" / "unsafe-field.md"
        self.assertTrue(fixture_path.exists())
        drift = specs.validate_spec(
            fixture_path, fixture_path.read_text(encoding="utf-8")
        )
        rules = [d.rule for d in drift]
        self.assertIn("attention.unsafe-field", rules)

    def test_non_regression_metadata_region_bound(self):
        # A spec quoting `- Scope: <301 chars>` inside a fenced block after a `## ` heading yields []
        quoted_text = _SPEC_TEMPLATE.format(
            extra_metadata="",
            body="## 1. Documentation\n\nExample:\n```\n- Scope: "
            + ("x" * 301)
            + "\n```\n",
        )
        drift = specs.validate_spec(Path("tests/spec.md"), quoted_text)
        self.assertEqual(drift, [])

    def test_non_regression_valid_specs_fixtures(self):
        # Every spec in tests/fixtures/attnview/specs-valid/ validates clean
        valid_specs = list((FIX / "specs-valid").glob("*.md"))
        self.assertTrue(len(valid_specs) > 0)
        for f in valid_specs:
            drift = specs.validate_spec(f, f.read_text(encoding="utf-8"))
            self.assertEqual(drift, [], f"{f.name} should be clean, got {drift}")

    def test_non_regression_live_committed_release(self):
        # The ACTUAL committed 2.0.0 release record validates clean through validate_release
        release_paths = list(
            (REPO / ".aw" / "records" / "releases").glob("*.release.md")
        )
        self.assertTrue(len(release_paths) > 0, "Committed release records must exist")
        for p in release_paths:
            text = p.read_text(encoding="utf-8")
            drift = releases.validate_release(p, text)
            self.assertEqual(
                drift,
                [],
                f"Live release record {p.name} must validate clean, got {drift}",
            )

    def test_rule_registry_entry(self):
        # Registry entry assertion: check_engine.rule_spec("attention.unsafe-field")
        # must return declared RuleSpec with severity error
        spec = check_engine.rule_spec("attention.unsafe-field")
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "")
        self.assertIn("attention.unsafe-field", check_engine.RULE_REGISTRY)
