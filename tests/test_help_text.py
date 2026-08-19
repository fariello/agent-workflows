"""Tests for awhelp Order 01: plainer help text (define jargon, name where records live, expand
the --phase gloss, self-contained terse lines)."""

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


class HelpTextTests(unittest.TestCase):
    def test_ipd_defines_jargon_and_location(self):
        h = _help(["ipd"])
        self.assertIn("Implementation Plan Document", h)
        self.assertIn(".aw/records/plans/", h)

    def test_phase_gloss_lists_all_checkpoints(self):
        h = _help(["ipd", "lint"])
        for phase in (
            "author",
            "review-finalize",
            "pre-execution",
            "pre-transition",
            "post-transition",
        ):
            self.assertIn(phase, h)
        # not a bare enum anymore: an explanatory gloss word appears
        self.assertIn("performed", h)

    def test_backlog_check_help_is_self_contained(self):
        h = _help(["backlog"])
        # the terse subcommand line names what is validated + the exit behavior
        self.assertRegex(h, r"check.*conform")

    def test_descriptions_avoid_bare_jargon(self):
        # 'IPD' should be expanded at least once in the ipd help (not left as a bare acronym only)
        h = _help(["ipd"])
        self.assertNotIn(
            "IPD tooling for structure and state.", h
        )  # the old terse phrasing


if __name__ == "__main__":
    unittest.main()
