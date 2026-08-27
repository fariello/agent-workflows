"""Tests for awlintmulti Order 01: `aw ipd lint` accepts multiple files + defaults to all-pending."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import ipd_lint as L
from tests.support import CONFORMING_ORCHESTRATOR


def _lint(argv_paths, phase="author"):
    import argparse

    args = argparse.Namespace(
        path=argv_paths,
        phase=phase,
        all=False,
        agent=False,
        legacy=False,
        no_color=True,
    )
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        rc = L.run_lint(args)
    return rc, out.getvalue()


class IpdLintMultiTests(unittest.TestCase):
    def test_two_files_both_linted(self):
        p = str(CONFORMING_ORCHESTRATOR)
        _rc, out = _lint([p, p])
        # two formatted lines (one per file)
        self.assertEqual(out.count("- "), 2)

    def test_single_string_backcompat(self):
        # a bare string path (not a list) still works
        _rc, out = _lint(str(CONFORMING_ORCHESTRATOR))
        self.assertEqual(out.count("- "), 1)

    def test_nonexistent_path_exits_2(self):
        rc, _out = _lint(["/no/such/plan.ipd.md"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
