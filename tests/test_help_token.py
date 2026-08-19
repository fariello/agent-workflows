"""Tests for awhelparg Order 01: a bare `help` token is rewritten to `--help` (option values spared)."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr

from agent_workflows import cli


class HelpTokenTests(unittest.TestCase):
    def test_pure_rewrite(self):
        r = cli._rewrite_help_token
        self.assertEqual(r(["help"]), ["--help"])
        self.assertEqual(r(["ipd", "help"]), ["ipd", "--help"])
        self.assertEqual(r(["check", "specs"]), ["check", "specs"])

    def test_option_value_help_preserved(self):
        r = cli._rewrite_help_token
        self.assertEqual(
            r(["backlog", "set", "x", "--message", "help"]),
            ["backlog", "set", "x", "--message", "help"],
        )

    def _run(self, argv):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue()

    def test_aw_help_shows_usage(self):
        rc, out = self._run(["help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_aw_ipd_help_shows_ipd_usage(self):
        rc, out = self._run(["ipd", "help"])
        self.assertEqual(rc, 0)
        self.assertIn("ipd", out.lower())


if __name__ == "__main__":
    unittest.main()
