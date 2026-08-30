"""Tests for awcmdsurf Order 04: merge plans->ipd (board), rename list->list-repos, todo->attention."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention, cli


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as e:
            rc = int(e.code or 0)
    return rc, out.getvalue() + err.getvalue()


class MergeAndRenamesTests(unittest.TestCase):
    def test_ipd_board_shows_board(self):
        # awcmdsurf Order 05 removed the old `plans` verb; `ipd board` is the board now.
        rc_b, out_b = _run(["ipd", "board"])
        self.assertEqual(rc_b, 0)
        self.assertIn("plan", out_b.lower())

    def test_old_plans_verb_removed(self):
        rc_p, out_p = _run(["plans"])
        self.assertEqual(rc_p, 2)  # invalid choice after the hard cutover

    def test_bare_ipd_routes_to_board(self):
        rc_bare, out_bare = _run(["ipd"])
        rc_board, out_board = _run(["ipd", "board"])
        self.assertEqual(out_bare, out_board)

    def test_list_repos_works_and_list_removed(self):
        rc_lr, out_lr = _run(["list-repos"])
        self.assertEqual(rc_lr, 0)
        rc_l, out_l = _run(["list"])
        self.assertEqual(rc_l, 2)  # old `list` removed

    def test_todo_matches_attention(self):
        """`todo` is an alias of `attention`, asserted STRUCTURALLY (i79rgh E-03).

        This used to shell `todo` and `attention` as two SEPARATE live `cli.main` calls and
        compare their stdout byte-for-byte. That was a race, not a test: the attention board
        renders the repository's CURRENT tracked records, so any concurrent agent committing
        a plan or backlog item between the two calls changed the second output and failed
        the assertion, and the default suite runs with `-n auto` so even sibling workers
        could perturb it.

        The property under test is real and worth keeping, but it is a STATIC property of
        the dispatcher, so it is provable without executing either command against live
        state: both branches must resolve to the same handler. `attention.run` is the single
        implementation, and `todo` must not acquire a body of its own.
        """
        import inspect
        import re

        src = inspect.getsource(cli._dispatch)

        def _dispatch_body(pattern: str) -> list[str]:
            match = re.search(pattern + r":\n(.*?)(?=\n    if |\n    elif )", src, re.S)
            if match is None:
                self.fail(f"dispatch branch not found in cli._dispatch: {pattern}")
            return [
                line.strip()
                for line in match.group(1).splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

        todo_body = _dispatch_body(r'if args\.command == "todo"')
        attention_body = _dispatch_body(r'if args\.command in \("attention", "att"\)')

        # Both branches delegate to the same handler, so they cannot diverge in behavior.
        self.assertEqual(todo_body, attention_body)
        self.assertEqual(
            todo_body,
            [
                "from agent_workflows import attention as att",
                "return att.run(args)",
            ],
        )

        # `att` must remain an alias reaching that same branch. argparse keeps the invoked
        # spelling in `command` (it does NOT canonicalize an alias), which is exactly why
        # the dispatch tests membership in ("attention", "att") rather than equality.
        parser = cli._build_parser()
        self.assertEqual(parser.parse_args(["att"]).command, "att")
        self.assertIn('("attention", "att")', src)

        # Output-level check WITHOUT a second live read: render ONE snapshot through both
        # argument namespaces. Any difference here is a dispatch difference, not a
        # repository change, because `attention.run` is called once per namespace against
        # the same immutable temp fixture.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            (root / ".aw" / "config").mkdir(parents=True)
            (root / ".aw" / "config" / "project.json").write_text(
                "{}", encoding="utf-8"
            )

            rendered = []
            for argv in (["todo"], ["attention"]):
                ns = parser.parse_args([*argv, "--no-color"])
                # `todo` has no --dir of its own; point both at the same fixture.
                ns.dir = str(root)
                buf = io.StringIO()
                with redirect_stdout(buf), redirect_stderr(buf):
                    rc = attention.run(ns)
                rendered.append((rc, buf.getvalue()))

            self.assertEqual(rendered[0], rendered[1])

    def test_ipd_lint_unaffected(self):
        rc, out = _run(["ipd", "lint", "--help"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
