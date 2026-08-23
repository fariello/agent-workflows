"""Tests for CLI Help, Usage Errors, Empty Families, Width Adaptation, and Next Actions.

awcliux Order 02 (`czw99i`) E-03 / V-03.
"""

from __future__ import annotations

import io
import json
import os
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from agent_workflows import cli

_ANSI = re.compile(r"\033\[[0-9;]*m")


class FakeTTYStream(io.StringIO):
    """StringIO stream that simulates a TTY."""

    def isatty(self) -> bool:
        return True


class HelpAndUsageErrorTests(unittest.TestCase):
    """V-03: Root/family/leaf help, empty families, and invalid calls show required sections and next actions."""

    def _run_cli_human(
        self, argv: list[str], columns: int = 80
    ) -> tuple[int, str, str]:
        out_stream = FakeTTYStream()
        err_stream = FakeTTYStream()
        with patch("sys.stdout", out_stream), patch("sys.stderr", err_stream):
            with patch.dict(
                os.environ,
                {
                    "COLUMNS": str(columns),
                    "TERM": "xterm-256color",
                    "NO_COLOR": "1",
                    "AW_ASCII_ONLY": "1",
                },
                clear=True,
            ):
                try:
                    rc = cli.main(argv)
                except SystemExit as e:
                    rc = int(e.code or 0)
        return rc, out_stream.getvalue(), err_stream.getvalue()

    def _run_cli_agent(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_root_help_contains_required_sections(self):
        for arg in ["--help", "-h", "help"]:
            rc, out, err = self._run_cli_human([arg])
            self.assertEqual(rc, 0, err)
            plain = _ANSI.sub("", out)

            # Purpose & Syntax
            self.assertIn("usage:", plain.lower())
            self.assertIn("agent-workflows", plain)

            # Defaults & Safety
            self.assertIn("manage", plain.lower())

            # Exits & Agent behavior
            self.assertIn("0 clean", plain)
            self.assertIn("1 findings", plain)
            self.assertIn("2 cannot-run", plain)
            self.assertIn("aw.agent/v1", plain)

            # Two or more realistic examples
            self.assertIn("aw attention", plain)
            self.assertIn("aw doctor", plain)
            self.assertIn("aw check", plain)

    def test_family_help_contains_required_sections(self):
        families = [
            "check",
            "ipd",
            "research",
            "backlog",
            "specs",
            "storage",
            "project",
            "config",
        ]
        for fam in families:
            rc, out, err = self._run_cli_human([fam, "--help"])
            self.assertEqual(rc, 0, f"{fam} --help failed: {err}")
            plain = _ANSI.sub("", out)

            # Syntax
            self.assertIn("usage:", plain.lower())

            # Purpose & Description
            self.assertTrue(len(plain) > 100)

            # Exits & Agent behavior / examples in help or epilog
            self.assertTrue(
                "0" in plain
                or "exit" in plain.lower()
                or "--agent" in plain
                or "json" in plain.lower()
            )
            self.assertTrue("example" in plain.lower() or "aw " in plain)

    def test_empty_families_show_help_and_next_action_exit_2(self):
        empty_calls = [
            (["project"], "aw project status"),
            (["storage"], "aw storage status"),
            (["config"], "aw config exclude list"),
            (["backlog"], "aw backlog check"),
            (["specs"], "aw specs check"),
            (["research"], "aw research find"),
        ]
        for argv, expected_next in empty_calls:
            # 1. Human mode (TTY)
            rc, out, err = self._run_cli_human(argv)
            self.assertEqual(rc, 2, f"Expected exit 2 for {argv}, got {rc}")
            combined = _ANSI.sub("", out + err)
            self.assertIn(
                "Next", combined, f"Missing 'Next' in {argv} output: {combined}"
            )
            self.assertIn(
                expected_next,
                combined,
                f"Missing {expected_next} in {argv} output: {combined}",
            )

            # 2. Agent mode (non-TTY)
            rc_agent, out_agent, _ = self._run_cli_agent(argv)
            self.assertEqual(rc_agent, 2)
            rec = json.loads(out_agent.strip())
            self.assertEqual(rec["exit"], 2)
            self.assertEqual(rec["next"], expected_next)

    def test_invalid_calls_show_usage_error_and_next_action_exit_2(self):
        invalid_calls = [
            (["check", "invalid_type_12345"], "aw check --help"),
            (["project", "invalid_subcommand"], "aw project"),
            (["storage", "invalid_subcommand"], "aw storage"),
        ]
        for argv, expected_hint in invalid_calls:
            # Human mode
            rc, out, err = self._run_cli_human(argv)
            self.assertEqual(rc, 2, f"Expected exit 2 for invalid call {argv}")
            combined = _ANSI.sub("", out + err)
            self.assertTrue(
                "error" in combined.lower()
                or "not supported" in combined.lower()
                or "usage:" in combined.lower()
            )
            self.assertIn("Next", combined)
            self.assertIn(expected_hint, combined)

            # Agent mode
            rc_agent, out_agent, err_agent = self._run_cli_agent(argv)
            self.assertEqual(rc_agent, 2)
            if out_agent.strip().startswith("{"):
                rec = json.loads(out_agent.strip())
                self.assertEqual(rec["exit"], 2)
                self.assertIn(
                    expected_hint, rec.get("next", "") or rec.get("summary", "")
                )
            else:
                self.assertIn("Next", err_agent)

    def test_width_adaptation_at_40_80_120_columns(self):
        for width in (40, 80, 120):
            rc, out, err = self._run_cli_human(["--help"], columns=width)
            self.assertEqual(rc, 0)
            plain = _ANSI.sub("", out)
            self.assertTrue(len(plain) > 0)
            # Pure 7-bit ASCII
            try:
                plain.encode("ascii")
            except UnicodeEncodeError as e:
                self.fail(f"Non-ASCII characters at width {width}: {e}")

    def test_help_ascii_fallback_when_unicode_disabled(self):
        rc, out, err = self._run_cli_human(["check", "--help"])
        self.assertEqual(rc, 0)
        plain = _ANSI.sub("", out)
        # Asserts no high-Unicode bytes
        plain.encode("ascii")


if __name__ == "__main__":
    unittest.main()
