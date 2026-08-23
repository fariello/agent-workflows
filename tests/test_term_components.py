"""Tests for Term components, 256-color palette extension, ASCII fallback, and single-palette invariant.

awcliux Order 02 (`czw99i`) E-01 / V-01.
"""

from __future__ import annotations

import io
import re
import unittest
from agent_workflows import term as T

_ANSI = re.compile(r"\033\[[0-9;]*m")


class PaletteSingleSourceTests(unittest.TestCase):
    """V-01: Exactly one palette exists (extended STATUS_COLOR_256) with documented roles."""

    def test_status_color_256_contains_all_roles(self):
        palette = T.STATUS_COLOR_256
        # Success / approved / implemented / executed -> 46
        self.assertEqual(palette["success"], 46)
        self.assertEqual(palette["approved"], 46)
        self.assertEqual(palette["implemented"], 46)
        self.assertEqual(palette["executed"], 46)
        self.assertEqual(palette["conforms"], 46)

        # Info / active / reusable -> 39
        self.assertEqual(palette["info"], 39)
        self.assertEqual(palette["active"], 39)
        self.assertEqual(palette["reusable"], 39)

        # Implementing -> 51
        self.assertEqual(palette["implementing"], 51)

        # Warning / reviewed -> 226
        self.assertEqual(palette["warning"], 226)
        self.assertEqual(palette["warn"], 226)
        self.assertEqual(palette["reviewed"], 226)

        # Action / to-review / preview -> 214
        self.assertEqual(palette["action"], 214)
        self.assertEqual(palette["to-review"], 214)
        self.assertEqual(palette["preview"], 214)

        # Failure / error / fail -> 196
        self.assertEqual(palette["failure"], 196)
        self.assertEqual(palette["error"], 196)
        self.assertEqual(palette["fail"], 196)

        # Blocked -> 203
        self.assertEqual(palette["blocked"], 203)

        # Deferred -> 208 (existing)
        self.assertEqual(palette["deferred"], 208)

        # Paths -> 33 (new role)
        self.assertEqual(palette["paths"], 33)
        self.assertEqual(palette["path"], 33)

        # Secondary / draft -> 245, done -> 244
        self.assertEqual(palette["secondary"], 245)
        self.assertEqual(palette["draft"], 245)
        self.assertEqual(palette["done"], 244)

    def test_no_parallel_palette_defined(self):
        """Assert no secondary or parallel palette dict exists in term module."""
        term_dicts = [
            k
            for k, v in T.__dict__.items()
            if isinstance(v, dict) and "COLOR" in k.upper()
        ]
        self.assertEqual(term_dicts, ["STATUS_COLOR_256"])


class TermComponentsTests(unittest.TestCase):
    """V-01: 11 shared Term components format correctly in color, monochrome, Unicode, and ASCII fallback."""

    def test_title_component(self):
        term = T.Term(color=True, unicode=True)
        title_str = term.format_title("check", "plans", elapsed_ms=38, width=60)
        plain = _ANSI.sub("", title_str)
        self.assertTrue(plain.startswith("AW check  plans"))
        self.assertTrue(plain.endswith("38 ms"))
        self.assertIn("\033[", title_str)

        # Monochrome & ASCII fallback
        term_plain = T.Term(color=False, unicode=False)
        title_plain = term_plain.format_title("check", "plans", elapsed_ms=38, width=60)
        self.assertIsNone(_ANSI.search(title_plain))
        self.assertEqual(title_plain, plain)

    def test_outcome_component(self):
        term_u = T.Term(color=True, unicode=True)
        out_conforms = term_u.format_outcome("conforms", "17 plans checked")
        self.assertIn("✓ CONFORMS", _ANSI.sub("", out_conforms))
        self.assertIn("17 plans checked", out_conforms)

        out_preview = term_u.format_outcome("preview", "No files changed. Add --apply.")
        self.assertIn("! PREVIEW", _ANSI.sub("", out_preview))

        out_findings = term_u.format_outcome("findings", "3 issues found")
        self.assertIn("✗ FINDINGS", _ANSI.sub("", out_findings))

        # ASCII fallback
        term_a = T.Term(color=False, unicode=False)
        out_a_conforms = term_a.format_outcome("conforms", "17 plans checked")
        self.assertEqual(out_a_conforms, "OK CONFORMS  17 plans checked")
        self.assertIsNone(_ANSI.search(out_a_conforms))

        out_a_preview = term_a.format_outcome(
            "preview", "No files changed. Add --apply."
        )
        self.assertEqual(out_a_preview, "! PREVIEW  No files changed. Add --apply.")

        out_a_findings = term_a.format_outcome("findings", "3 issues found")
        self.assertEqual(out_a_findings, "FAIL FINDINGS  3 issues found")

    def test_section_component(self):
        term = T.Term(color=True)
        sec = term.format_section("Evidence")
        self.assertEqual(_ANSI.sub("", sec), "Evidence")
        self.assertIn("\033[", sec)

        term_plain = T.Term(color=False)
        self.assertEqual(term_plain.format_section("Evidence"), "Evidence")

    def test_table_component(self):
        term = T.Term(color=False)
        headers = ["ID", "Status", "Path"]
        rows = [
            ["czw99i", "approved", "plans/czw99i.ipd.md"],
            ["hd3kln", "executed", "plans/hd3kln.ipd.md"],
        ]
        tbl = term.format_table(headers, rows)
        lines = tbl.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("ID", lines[0])
        self.assertIn("czw99i", lines[1])
        self.assertIn("hd3kln", lines[2])

    def test_badge_component(self):
        term = T.Term(color=True)
        err_badge = term.badge("ERROR", "error")
        self.assertIn("\033[1;38;5;196mERROR\033[0m", err_badge)

        path_badge = term.badge("PLANS", "paths")
        self.assertIn("\033[1;38;5;33mPLANS\033[0m", path_badge)

        term_plain = T.Term(color=False)
        self.assertEqual(term_plain.badge("ERROR", "error"), "[ERROR]")

    def test_path_component(self):
        term = T.Term(color=True)
        p = term.format_path(".aw/records/plans")
        self.assertIn("\033[38;5;33m.aw/records/plans\033[0m", p)

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_path(".aw/records/plans"), ".aw/records/plans"
        )

    def test_diagnostic_component(self):
        term = T.Term(color=True, unicode=True)
        diag = term.format_diagnostic(
            location="plans/test.ipd.md:12",
            rule="check.status-invalid",
            detail="status 'foo' is invalid",
            severity="error",
            fix="aw set plans draft plans/test.ipd.md",
        )
        plain = _ANSI.sub("", diag)
        self.assertIn(
            "plans/test.ipd.md:12: [check.status-invalid] status 'foo' is invalid",
            plain,
        )
        self.assertIn("Fix: aw set plans draft plans/test.ipd.md", plain)

        term_plain = T.Term(color=False, unicode=False)
        diag_plain = term_plain.format_diagnostic(
            location="plans/test.ipd.md:12",
            rule="check.status-invalid",
            detail="status 'foo' is invalid",
            severity="error",
            fix="aw set plans draft plans/test.ipd.md",
        )
        self.assertIsNone(_ANSI.search(diag_plain))
        self.assertEqual(diag_plain, plain)

    def test_preview_component(self):
        term = T.Term(color=True, unicode=True)
        prev = term.format_preview("file", "old.md", "new.md")
        self.assertIn("old.md → new.md", _ANSI.sub("", prev))

        term_plain = T.Term(color=False, unicode=False)
        prev_plain = term_plain.format_preview("file", "old.md", "new.md")
        self.assertEqual(prev_plain, "  file  old.md -> new.md")
        self.assertIsNone(_ANSI.search(prev_plain))

    def test_evidence_and_grid_component(self):
        term = T.Term(color=True)
        ev = term.format_evidence("pending", 17, status="verified")
        self.assertIn("pending: 17", _ANSI.sub("", ev))

        grid = term.format_evidence_grid(
            [("pending", 17), ("reusable", 2), ("terminal", 41)]
        )
        plain_grid = _ANSI.sub("", grid)
        self.assertIn("pending  17", plain_grid)
        self.assertIn("reusable  2", plain_grid)
        self.assertIn("terminal  41", plain_grid)

    def test_fix_component(self):
        term = T.Term(color=True)
        f = term.format_fix("run 'aw ipd sync'")
        self.assertIn("Fix: run 'aw ipd sync'", _ANSI.sub("", f))

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_fix("run 'aw ipd sync'"), "Fix: run 'aw ipd sync'"
        )

    def test_next_action_component(self):
        term = T.Term(color=True)
        nxt = term.format_next_action("aw ipd board")
        self.assertIn("Next  aw ipd board", _ANSI.sub("", nxt))

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_next_action("aw ipd board"), "Next  aw ipd board"
        )

    def test_stream_print_methods(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False, unicode=False)
        term.title("check", "plans", elapsed_ms=12)
        term.outcome("conforms", "0 errors")
        term.section("Evidence")
        term.diagnostic("file.txt:1", "rule", "detail", fix="fix cmd")
        term.preview("file", "a.txt", "b.txt")
        term.evidence("total", 10)
        term.fix("run fix")
        term.next_action("aw next")

        lines = [line.strip() for line in buf.getvalue().splitlines() if line.strip()]
        self.assertTrue(any("AW check  plans" in line_str for line_str in lines))
        self.assertTrue(any("OK CONFORMS  0 errors" in line_str for line_str in lines))
        self.assertTrue(any("Evidence" in line_str for line_str in lines))
        self.assertTrue(
            any("file.txt:1: [rule] detail" in line_str for line_str in lines)
        )
        self.assertTrue(any("a.txt -> b.txt" in line_str for line_str in lines))
        self.assertTrue(any("total: 10" in line_str for line_str in lines))
        self.assertTrue(any("Fix: run fix" in line_str for line_str in lines))
        self.assertTrue(any("Next  aw next" in line_str for line_str in lines))


class AsciiFallbackDegradationTests(unittest.TestCase):
    """V-01: Glyphs degrade strictly to ASCII without loss of meaning."""

    def test_all_components_pure_ascii_when_unicode_disabled(self):
        term = T.Term(color=False, unicode=False)
        samples = [
            term.format_title("check", "plans", elapsed_ms=20),
            term.format_outcome("conforms", "all good"),
            term.format_outcome("preview", "changes pending"),
            term.format_outcome("findings", "1 issue"),
            term.format_section("Evidence"),
            term.format_table(["Col1", "Col2"], [["Val1", "Val2"]]),
            term.badge("INFO", "info"),
            term.format_path("a/b/c"),
            term.format_diagnostic("loc:1", "rule", "detail", fix="fix cmd"),
            term.format_preview("file", "a.txt", "b.txt"),
            term.format_evidence("key", "val"),
            term.format_evidence_grid([("k1", 1), ("k2", 2)]),
            term.format_fix("do this"),
            term.format_next_action("next cmd"),
        ]
        for s in samples:
            # Must encode cleanly to 7-bit ASCII
            try:
                s.encode("ascii")
            except UnicodeEncodeError as e:
                self.fail(
                    f"Non-ASCII characters emitted under unicode=False in string: {s!r}: {e}"
                )

    def test_ansi_scan_proves_zero_escapes_when_color_disabled(self):
        term = T.Term(color=False, unicode=True)
        samples = [
            term.format_title("check", "plans", elapsed_ms=20),
            term.format_outcome("conforms", "all good"),
            term.format_outcome("preview", "changes pending"),
            term.format_outcome("findings", "1 issue"),
            term.format_section("Evidence"),
            term.format_table(["Col1", "Col2"], [["Val1", "Val2"]]),
            term.badge("INFO", "info"),
            term.format_path("a/b/c"),
            term.format_diagnostic("loc:1", "rule", "detail", fix="fix cmd"),
            term.format_preview("file", "a.txt", "b.txt"),
            term.format_evidence("key", "val"),
            term.format_evidence_grid([("k1", 1), ("k2", 2)]),
            term.format_fix("do this"),
            term.format_next_action("next cmd"),
        ]
        for s in samples:
            self.assertIsNone(
                _ANSI.search(s), f"ANSI escape found in color=False string: {s!r}"
            )


if __name__ == "__main__":
    unittest.main()
