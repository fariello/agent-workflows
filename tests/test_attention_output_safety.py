"""Acceptance criteria A14 and Section 8.8 output safety fixtures.

Proves that the attention board renderers deterministically escape Markdown
metacharacters (so untrusted fields cannot break tables, inject links/images,
or inject HTML tags) and neutralize raw control characters (C0, C1, DEL, and
bidirectional overrides/isolates) to U+FFFD before emission, while preserving
benign detail text unchanged and keeping --format markdown free of ANSI escapes.
"""

from __future__ import annotations

import argparse
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import attention as att
from agent_workflows import attention_contract as A
from agent_workflows import term as T


def _make_item(
    id6: str = "abc123",
    path: str = ".aw/records/plans/pending/p.ipd.md",
    tree: str = "plans",
    native_status: str = "approved",
    attention_class: str = A.READY,
    detail_kind: str = "scope",
    detail_text: str = "",
) -> att.Item:
    return att.Item(
        id6,
        path,
        tree,
        native_status,
        attention_class,
        None,
        None,
        detail_kind=detail_kind,
        detail_text=detail_text,
    )


class AttentionOutputSafetyTests(unittest.TestCase):
    """Behavioral tests verifying Section 8.8 and criterion A14 output safety."""

    def test_render_item_row_markdown_escaping(self):
        # F-1 table-breaking value with pipes, links, and images
        f1_val = "a | b | c cell break [link](http://x) ![img](http://y)"
        item_f1 = _make_item(detail_text=f1_val)

        # Uncolored _render_item_row
        term_plain = T.Term(color=False)
        rendered_plain = att._render_item_row(
            item_f1, A.READY, term_plain, False, False, details=True
        )
        detail_line_plain = [
            line for line in rendered_plain.splitlines() if "scope:" in line
        ][0]
        # In detail line, pipes must be escaped: \| and no bare |
        self.assertIn(r"\|", detail_line_plain)
        # Replacing escaped pipes should leave no remaining pipes
        self.assertNotIn("|", detail_line_plain.replace(r"\|", ""))
        self.assertIn(r"\[link\](http://x)", detail_line_plain)
        self.assertIn(r"!\[img\](http://y)", detail_line_plain)

        # Colored _render_item_row
        term_color = T.Term(color=True)
        rendered_color = att._render_item_row(
            item_f1, A.READY, term_color, True, False, details=True
        )
        self.assertIn(r"\|", rendered_color)
        self.assertIn(r"\[link\](http://x)", rendered_color)
        self.assertIn(r"!\[img\](http://y)", rendered_color)

        # HTML tag value
        html_val = "<tag> and <script>alert(1)</script>"
        item_html = _make_item(detail_text=html_val)
        rendered_html = att._render_item_row(
            item_html, A.READY, term_plain, False, False, details=True
        )
        self.assertIn(r"\<tag>", rendered_html)
        self.assertIn(r"\<script>", rendered_html)
        self.assertNotIn("<tag>", rendered_html.replace(r"\<tag>", ""))

        # Backslash value
        bs_val = r"path\to\file and back\slash"
        item_bs = _make_item(detail_text=bs_val)
        rendered_bs = att._render_item_row(
            item_bs, A.READY, term_plain, False, False, details=True
        )
        self.assertIn(r"path\\to\\file and back\\slash", rendered_bs)

    def test_render_item_row_control_character_neutralization(self):
        # F-3 ANSI/BEL value
        f3_val = "red \x1b[31mANSI\x1b[0m and newline-free \x07bell"
        item_f3 = _make_item(detail_text=f3_val)

        # Uncolored _render_item_row
        term_plain = T.Term(color=False)
        rendered_plain = att._render_item_row(
            item_f3, A.READY, term_plain, False, False, details=True
        )
        self.assertIn("\ufffd", rendered_plain)
        self.assertNotIn("\x1b", rendered_plain)
        self.assertNotIn("\x07", rendered_plain)

        # Colored _render_item_row: styling escape sequence is present,
        # but the injected ANSI/BEL is neutralized.
        term_color = T.Term(color=True)
        rendered_color = att._render_item_row(
            item_f3, A.READY, term_color, True, False, details=True
        )
        # color256 adds \x1b[38;5;250m
        self.assertIn("\x1b[38;5;250m", rendered_color)
        # But the injected \x1b[31m and \x07 must be neutralized
        self.assertNotIn("\x1b[31m", rendered_color)
        self.assertNotIn("\x07", rendered_color)
        self.assertIn("\ufffd\\[31mANSI\ufffd\\[0m", rendered_color)

        # Bidi override value (U+202E)
        bidi_val = "bidi \u202eevil override"
        item_bidi = _make_item(detail_text=bidi_val)
        rendered_bidi = att._render_item_row(
            item_bidi, A.READY, term_plain, False, False, details=True
        )
        self.assertNotIn("\u202e", rendered_bidi)
        self.assertIn("bidi \ufffdevil override", rendered_bidi)

    def test_benign_detail_passthrough_unchanged(self):
        # Benign pass-through must not be altered
        benign_val = "Implement feature X cleanly without special characters."
        item_benign = _make_item(detail_text=benign_val)

        term_plain = T.Term(color=False)
        rendered = att._render_item_row(
            item_benign, A.READY, term_plain, False, False, details=True
        )
        expected_line = f"      scope: {benign_val}"
        self.assertIn(expected_line, rendered)

        # Same in render_board
        board = att.render_board(
            [item_benign], drift=[], show_all=True, term=term_plain, details=True
        )
        self.assertIn(expected_line, board)

    def test_render_table_row_output_safety(self):
        term_plain = T.Term(color=False)
        term_color = T.Term(color=True)

        # F-1 in table row
        f1_val = "a | b | c [link](http://x) ![img](http://y)"
        item_f1 = _make_item(detail_text=f1_val)
        row_plain = att._render_table_row(
            item_f1, term_plain, False, False, details=True
        )
        self.assertIn(r"\|", row_plain)
        self.assertIn(r"\[link\](http://x)", row_plain)

        row_color = att._render_table_row(
            item_f1, term_color, True, False, details=True
        )
        self.assertIn(r"\|", row_color)

        # F-3 in table row
        f3_val = "red \x1b[31mANSI\x1b[0m \x07bell"
        item_f3 = _make_item(detail_text=f3_val)
        row_f3_plain = att._render_table_row(
            item_f3, term_plain, False, False, details=True
        )
        self.assertIn("\ufffd", row_f3_plain)
        self.assertNotIn("\x1b", row_f3_plain)
        self.assertNotIn("\x07", row_f3_plain)

        row_f3_color = att._render_table_row(
            item_f3, term_color, True, False, details=True
        )
        self.assertIn("\x1b[38;5;250m", row_f3_color)
        self.assertNotIn("\x1b[31m", row_f3_color)
        self.assertNotIn("\x07", row_f3_color)

    def test_format_plan_detail_line(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # F-1 plan
            p1 = tmp / "plan_f1.ipd.md"
            p1.write_text(
                "# IPD: p1\n\n- Scope: a | b | c [link](http://x) ![img](http://y)\n- Status: approved\n",
                encoding="utf-8",
            )
            # F-3 plan
            p3 = tmp / "plan_f3.ipd.md"
            p3.write_text(
                "# IPD: p3\n\n- Scope: red \x1b[31mANSI\x1b[0m \x07bell\n- Status: approved\n",
                encoding="utf-8",
            )

            # Plain term
            term_plain = T.Term(color=False)
            res1_plain = att.format_plan_detail_line(p1, term=term_plain)
            self.assertIsNotNone(res1_plain)
            self.assertIn(r"\|", res1_plain)
            self.assertIn(r"\[link\](http://x)", res1_plain)
            self.assertIn(r"!\[img\](http://y)", res1_plain)

            res3_plain = att.format_plan_detail_line(p3, term=term_plain)
            self.assertIsNotNone(res3_plain)
            self.assertIn("\ufffd", res3_plain)
            self.assertNotIn("\x1b", res3_plain)
            self.assertNotIn("\x07", res3_plain)

            # Colored term
            term_color = T.Term(color=True)
            res1_color = att.format_plan_detail_line(p1, term=term_color)
            self.assertIsNotNone(res1_color)
            self.assertIn(r"\|", res1_color)
            self.assertIn("\x1b[38;5;250m", res1_color)

            res3_color = att.format_plan_detail_line(p3, term=term_color)
            self.assertIsNotNone(res3_color)
            self.assertIn("\x1b[38;5;250m", res3_color)
            self.assertNotIn("\x1b[31m", res3_color)
            self.assertNotIn("\x07", res3_color)

    def test_end_to_end_run_details(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plans_dir = root / ".agents" / "plans" / "pending"
            plans_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plans_dir / "20260808-test-01-abc123-p.ipd.md"
            plan_file.write_text(
                "# IPD: p\n\n- Scope: a | b [link](http://x)\n- Status: draft\n- Id: abc123\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                dir=str(root),
                format=None,
                check=False,
                selectors=["abc123"],
                no_color=True,
                all=False,
                long=False,
                details=True,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(att.run(args), 0)
            output = buf.getvalue()
            self.assertIn(r"a \| b \[link\](http://x)", output)

    def test_format_markdown_cli_no_ansi(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plans_dir = root / ".agents" / "plans" / "pending"
            plans_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plans_dir / "20260808-test-01-abc123-p.ipd.md"
            plan_file.write_text(
                "# IPD: p\n\n- Scope: Simple plan detail.\n- Status: draft\n- Id: abc123\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                dir=str(root),
                format="markdown",
                check=False,
                selectors=None,
                no_color=False,
                all=False,
                long=False,
                details=True,
            )
            env_patch = {"FORCE_COLOR": "1"}
            with mock.patch.dict(os.environ, env_patch):
                os.environ.pop("NO_COLOR", None)
                buf = io.StringIO()
                with mock.patch("sys.stdout", buf):
                    self.assertEqual(att.run(args), 0)
                output = buf.getvalue()
                self.assertNotIn("\x1b", output)


if __name__ == "__main__":
    unittest.main()
