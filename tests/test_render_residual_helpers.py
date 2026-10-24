"""Residual render and citation behavioral tests.

Provenance:
- Backlog: nzc6dm
- Plan: j77z5h
- Findings: wo21z5
- Mined source: 19313eed^:tests/test_lifecycle_palette_singleness.py
"""

from __future__ import annotations

import unittest

import pytest

from agent_workflows import attention, plan_readiness, render_stream

pytestmark = pytest.mark.core


class RunnerStatusAndGlyphTests(unittest.TestCase):
    def test_palette_status_ready_differs_from_done_and_unmapped_degrades(self) -> None:
        palette_color = render_stream.Palette(True)
        status_approved = palette_color.status("approved")
        status_executed = palette_color.status("executed")

        self.assertIn("38;5;45m", status_approved)
        self.assertIn("38;5;46m", status_executed)
        self.assertNotEqual(status_approved, status_executed)

        status_weird = palette_color.status("weird")
        self.assertIn("weird", status_weird)

        palette_plain = render_stream.Palette(False)
        self.assertEqual(palette_plain.status("executed"), "executed")

    def test_status_glyph_char_unicode_and_ascii(self) -> None:
        # Unicode mode (default use_unicode=True)
        self.assertEqual(
            render_stream._status_glyph_char("completed"), ("\u2713", "green")
        )
        self.assertEqual(render_stream._status_glyph_char("error"), ("\u2717", "red"))
        self.assertEqual(render_stream._status_glyph_char("failed"), ("\u2717", "red"))
        self.assertEqual(
            render_stream._status_glyph_char("running"), ("\u2026", "yellow")
        )
        self.assertEqual(
            render_stream._status_glyph_char("pending"), ("\u2026", "yellow")
        )
        self.assertEqual(
            render_stream._status_glyph_char("in_progress"), ("\u2026", "yellow")
        )
        self.assertEqual(render_stream._status_glyph_char("other"), ("\u2022", "gray"))
        self.assertEqual(
            render_stream._status_glyph_char("unknown_status"), ("\u2022", "gray")
        )

        # ASCII mode (use_unicode=False)
        self.assertEqual(
            render_stream._status_glyph_char("completed", use_unicode=False),
            ("+", "green"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("error", use_unicode=False),
            ("x", "red"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("failed", use_unicode=False),
            ("x", "red"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("running", use_unicode=False),
            (".", "yellow"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("pending", use_unicode=False),
            (".", "yellow"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("in_progress", use_unicode=False),
            (".", "yellow"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("other", use_unicode=False),
            ("-", "gray"),
        )
        self.assertEqual(
            render_stream._status_glyph_char("unknown_status", use_unicode=False),
            ("-", "gray"),
        )


class GateRefDisplayTests(unittest.TestCase):
    def test_gate_ref_display_compact_and_verbatim(self) -> None:
        self.assertEqual(attention._gate_ref_display("TODO.md", long=False), "TODO.md")
        self.assertEqual(
            attention._gate_ref_display("issue#12", long=False), "issue#12"
        )
        self.assertEqual(attention._gate_ref_display("", long=False), "")

        deep_path = (
            ".aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec.ipd.md"
        )
        self.assertEqual(
            attention._gate_ref_display(deep_path, long=False),
            "20260903-runflags-01-uyeko5",
        )
        self.assertEqual(
            attention._gate_ref_display(deep_path, long=True),
            deep_path,
        )


class CiteReviewEntryTests(unittest.TestCase):
    def test_cite_review_entry_derives_citation_without_verdict_token(self) -> None:
        entry = "- 2026-10-01 reviewed (plan-review): findings F-01..F-03 resolved; Readiness go"
        citation = plan_readiness.cite_review_entry(entry)
        self.assertEqual(
            citation,
            "the review of 2026-10-01, findings F-01..F-03",
        )

        words = [w.strip(",.;:()") for w in citation.split()]
        self.assertNotIn("go", words)
        self.assertNotIn("reviewed", citation)

        self.assertEqual(plan_readiness.cite_review_entry(""), "")
        self.assertEqual(plan_readiness.cite_review_entry("garbage"), "")


class SpecImpactAnnouncementTests(unittest.TestCase):
    def test_format_spec_impact_announcement_empty_and_populated(self) -> None:
        pal = render_stream.Palette(False)
        self.assertEqual(
            render_stream.format_spec_impact_announcement([], pal=pal),
            [],
        )

        only_empty_specs = [{"id6": "abc123", "setid": "s", "specs": []}]
        self.assertEqual(
            render_stream.format_spec_impact_announcement(only_empty_specs, pal=pal),
            [],
        )

        impacts = [
            {"id6": "abc123", "setid": "s", "specs": ["a.spec.md", "b.spec.md"]},
            {"id6": "def456", "setid": "s", "specs": []},
        ]
        expected = [
            "SPEC CHANGES: 1 queued plan(s) declare edits to 2 specification file(s).",
            "  A spec is the contract other plans are reviewed against, so review these first.",
            "    abc123 (s) -> a.spec.md",
            "    abc123 (s) -> b.spec.md",
        ]
        self.assertEqual(
            render_stream.format_spec_impact_announcement(impacts, pal=pal),
            expected,
        )
