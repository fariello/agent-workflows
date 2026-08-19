"""Tests for awcmdsurf Order 04: merge plans->ipd (board), rename list->list-repos, todo->attention."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as e:
            rc = int(e.code or 0)
    return rc, out.getvalue() + err.getvalue()


class MergeAndRenamesTests(unittest.TestCase):
    def test_ipd_board_matches_plans_board(self):
        rc_b, out_b = _run(["ipd", "board"])
        rc_p, out_p = _run(["plans"])
        self.assertEqual(rc_b, rc_p)
        self.assertEqual(out_b, out_p)

    def test_bare_ipd_routes_to_board(self):
        rc_bare, out_bare = _run(["ipd"])
        rc_board, out_board = _run(["ipd", "board"])
        self.assertEqual(out_bare, out_board)

    def test_list_repos_matches_list(self):
        rc_lr, out_lr = _run(["list-repos"])
        rc_l, out_l = _run(["list"])
        self.assertEqual(rc_lr, rc_l)
        self.assertEqual(out_lr, out_l)

    def test_todo_matches_attention(self):
        rc_t, out_t = _run(["todo"])
        rc_a, out_a = _run(["attention"])
        self.assertEqual(rc_t, rc_a)
        self.assertEqual(out_t, out_a)

    def test_ipd_lint_unaffected(self):
        rc, out = _run(["ipd", "lint", "--help"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
