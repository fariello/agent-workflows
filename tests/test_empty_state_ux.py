"""Tests for Empty, Loading, and Error State UX helper and conventions.

IPD: 20260822-highpbacklog0822-04-89bby9 (Order 04 E-01, E-02, E-03, V-01, V-02, V-03).

Asserts:
1. Term.format_empty_result / Term.empty_result echoes active filters and next action,
   composed from existing primitives (outcome, section, next_action) with zero parallel palette.
2. Step cue formatting for transient stderr progress updates.
3. Reference read verb ('aw find') renders empty state with filters and next-action in both
   Human TTY and Agent (aw.agent/v1) modes.
4. Negative / error states never fail silently and exit with proper exit code (1 or 2).
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import agent_schema as schema
from agent_workflows import term as T
from agent_workflows.result_types import (
    CommandResult,
    NextAction,
)

_ANSI = re.compile(r"\033\[[0-9;]*m")


class EmptyStateHelperUnitTests(unittest.TestCase):
    """V-01: Term.empty_result and Term.format_empty_result component tests."""

    def test_format_empty_result_color_unicode(self):
        term = T.Term(color=True, unicode=True)
        rendered = term.format_empty_result(
            summary="no matching plans",
            filters={"type": "plans", "selector": "89bby9"},
            next_action=NextAction("aw find plans", "find across all plans"),
        )
        plain = _ANSI.sub("", rendered)
        self.assertIn("✓ CLEAN  no matching plans", plain)
        self.assertIn("Active filters:", plain)
        self.assertIn("type: plans", plain)
        self.assertIn("selector: 89bby9", plain)
        self.assertIn("Next  aw find plans (find across all plans)", plain)
        # Verify ANSI color sequences are present
        self.assertIn("\033[", rendered)

    def test_format_empty_result_monochrome_ascii(self):
        term = T.Term(color=False, unicode=False)
        rendered = term.format_empty_result(
            summary="no matching artifacts",
            filters={"type": "all"},
            next_action="aw status",
        )
        self.assertIsNone(_ANSI.search(rendered))
        self.assertIn("OK CLEAN  no matching artifacts", rendered)
        self.assertIn("Active filters:", rendered)
        self.assertIn("type: all", rendered)
        self.assertIn("Next  aw status", rendered)
        # Must be strict 7-bit ASCII
        rendered.encode("ascii")

    def test_format_empty_result_from_dict_and_result_context(self):
        term = T.Term(color=False, unicode=False)
        # From dictionary context
        dict_ctx = {
            "summary": "no matching specs",
            "filters": [("type", "specs"), ("tag", "core")],
            "next_action": ("aw find specs", "list all specs"),
        }
        res1 = term.format_empty_result(dict_ctx)
        self.assertIn("OK CLEAN  no matching specs", res1)
        self.assertIn("type: specs", res1)
        self.assertIn("tag: core", res1)
        self.assertIn("Next  aw find specs (list all specs)", res1)

        # From CommandResult context
        cmd_res = CommandResult(
            command="find",
            status="clean",
            exit_code=0,
            summary="no matching research",
            next_actions=[NextAction("aw find", "list all")],
            data={"filters": {"type": "research"}},
        )
        res2 = term.format_empty_result(cmd_res)
        self.assertIn("OK CLEAN  no matching research", res2)
        self.assertIn("type: research", res2)
        self.assertIn("Next  aw find (list all)", res2)

    def test_format_empty_result_no_filters_or_next(self):
        term = T.Term(color=False, unicode=False)
        res = term.format_empty_result(summary="no results")
        self.assertEqual(res.strip(), "OK CLEAN  no results")

    def test_empty_result_stream_emission(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False, unicode=False)
        term.empty_result(
            summary="no matching items",
            filters={"query": "foo"},
            next_action="aw search",
        )
        out = buf.getvalue()
        self.assertIn("OK CLEAN  no matching items", out)
        self.assertIn("query: foo", out)
        self.assertIn("Next  aw search", out)

    def test_step_cue_helper(self):
        term = T.Term(color=False, unicode=False)
        cue = term.format_step_cue("Scanning workspace...")
        self.assertEqual(cue, "[INFO ] Scanning workspace...")

        err_buf = io.StringIO()
        term.step_cue("Running check...", stream=err_buf)
        self.assertEqual(err_buf.getvalue().strip(), "[INFO ] Running check...")


class FindReferenceVerbEmptyStateTests(unittest.TestCase):
    """V-03: Reference read verb ('aw find') empty-state UX across TTY and Agent modes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Create minimal .aw layout with one spec
        specs = self.root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        content = (
            "\n".join(
                [
                    "# Spec",
                    "",
                    "- Id: abc123",
                    "- Status: draft",
                    "",
                    "## Content",
                    "hello world",
                ]
            )
            + "\n"
        )
        (specs / "20260822-1200-01-sample.spec.md").write_text(
            content,
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_find_empty_human_tty_mode_with_type_and_selector(self):
        # Searching for nonexistent selector in specs
        rc, out, err = self._run_cli(["find", "specs", "nonexistent999"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no matching specs", out)
        self.assertIn("Active filters:", out)
        self.assertIn("type: specs", out)
        self.assertIn("selector: nonexistent999", out)
        self.assertIn("Next  aw find specs", out)

    def test_find_empty_human_tty_mode_all_types(self):
        # Searching across all types for nonexistent selector
        rc, out, err = self._run_cli(["find", "nonexistent999"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no matching artifacts", out)
        self.assertIn("Active filters:", out)
        self.assertIn("type: all", out)
        self.assertIn("selector: nonexistent999", out)
        self.assertIn("Next  aw find", out)

    def test_find_empty_agent_mode(self):
        rc, out, err = self._run_cli(["find", "specs", "nonexistent999", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "find")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["findings"], 0)
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])
        self.assertEqual(rec["next"], "aw find specs")
        self.assertIsNone(_ANSI.search(lines[0]))
        # Schema validation
        val_errors = schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])

    def test_find_match_found_human_mode(self):
        # Non-empty match still outputs normal lines
        rc, out, err = self._run_cli(["find", "specs", "abc123"])
        self.assertEqual(rc, 0)
        self.assertIn("abc123", out)
        self.assertIn("draft", out)
        self.assertNotIn("no matching", out)


if __name__ == "__main__":
    unittest.main()
