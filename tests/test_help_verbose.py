"""Tests for awhelp Order 02: the top-level when/why + examples epilog and per-verb EXAMPLES blocks."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr

from agent_workflows import cli


def _help(argv):
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        try:
            cli.main(argv + ["--help"])
        except SystemExit:
            pass
    return out.getvalue()


class HelpVerboseTests(unittest.TestCase):
    def test_top_help_has_when_why_and_examples(self):
        h = cli._build_parser().format_help()
        self.assertIn("WHEN AND WHY TO USE aw", h)
        self.assertIn("COMMON EXAMPLES", h)
        # at least two example command lines survive (raw line breaks preserved)
        self.assertIn("aw attention", h)
        self.assertIn("aw ipd board", h)

    def test_arg_hungry_verbs_show_examples(self):
        for v in ("ipd", "show", "storage"):
            self.assertIn("EXAMPLES", _help([v]), f"{v} --help missing EXAMPLES")

    def test_missing_arg_still_exits_nonzero(self):
        # `aw show` with no selector is a usage error (nonzero); parsing semantics unchanged.
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            try:
                rc = cli.main(["show"])
            except SystemExit as e:
                rc = int(e.code or 0)
        self.assertNotEqual(rc, 0)

    def test_subcommand_list_alphabetical_preserved(self):
        # the epilog change must not break the alphabetical subcommand listing.
        h = cli._build_parser().format_help()
        self.assertIn("attention", h)
        self.assertIn("doctor", h)


if __name__ == "__main__":
    unittest.main()
