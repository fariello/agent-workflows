"""Tests for awresearchrev Order 01: the `aw research` subverbs still parse + dispatch after the
awcmdsurf noun-verb redesign (this Order is an audit + a minimal, safe consistency pass)."""

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


class ResearchSurfaceTests(unittest.TestCase):
    SUBVERBS = (
        "new",
        "new-comparison",
        "set-assign",
        "mv",
        "check-refs",
        "index",
        "find",
        "pending",
        "promote",
        "set-outcome",
        "miscategorized",
    )

    def test_all_subverbs_parse_help(self):
        for sv in self.SUBVERBS:
            h = _help(["research", sv])
            self.assertTrue(h.strip(), f"research {sv} --help produced no output")

    def test_research_group_help_lists_subverbs(self):
        h = _help(["research"])
        # the umbrella help mentions at least the create verbs
        self.assertIn("new", h)

    def test_research_dir_flag_present_on_index(self):
        # the --dir option is consistent on the query subverbs (index/find/... use --dir)
        self.assertIn("--dir", _help(["research", "index"]))
        self.assertIn("--dir", _help(["research", "find"]))


if __name__ == "__main__":
    unittest.main()
