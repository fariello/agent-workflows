"""Tests for awcmdsurf Order 04: merge plans->ipd (board), rename list->list-repos, todo->attention."""

from __future__ import annotations

import argparse
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
        """`todo` is an alias of the cross-tree view, asserted STRUCTURALLY (i79rgh E-03).

        This used to shell `todo` and `attention` as two SEPARATE live `cli.main` calls and
        compare their stdout byte-for-byte. That was a race, not a test: the attention board
        renders the repository's CURRENT tracked records, so any concurrent agent committing
        a plan or backlog item between the two calls changed the second output and failed
        the assertion, and the default suite runs with `-n auto` so even sibling workers
        could perturb it.

        The property under test is real and worth keeping, but it is a STATIC property of
        the dispatcher, so it is provable without executing either command against live
        state: every spelling must resolve to the same handler, and `todo` must not acquire
        a body of its own.

        UPDATED by worksequence i6015i E-01, which made the property STRONGER rather than
        weaker. `next` is now the canonical command and `attention`/`att`/`todo` are true
        argparse aliases of it, so `todo` no longer has a dispatch branch of its own to
        compare: the previous assertion searched for `if args.command == "todo"`, the very
        special-case E-01 deleted. Sharing ONE PARSER OBJECT is a stronger guarantee than two
        branches with matching bodies, because it makes divergence unrepresentable instead of
        merely absent: the earlier arrangement let `todo` carry a NARROWER option set (it
        accepted only `--all`, so `aw todo --format json` failed outright) while both dispatch
        bodies still matched, which is exactly the defect that passed under the old assertion.
        """
        import inspect

        src = inspect.getsource(cli._dispatch)
        parser = cli._build_parser()

        # ONE dispatch branch now covers every spelling, and it delegates to `attention.run`.
        self.assertIn('if args.command in ("next", "attention", "att", "todo")', src)
        self.assertNotIn('if args.command == "todo":', src)

        # Every alias resolves to the SAME parser object as the canonical `next`, so they
        # cannot diverge in options, defaults, or help.
        subparser_actions = [
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        ]
        self.assertTrue(subparser_actions, "the CLI must expose subcommands")
        choices = subparser_actions[0].choices or {}
        for alias in ("attention", "att", "todo"):
            self.assertIs(choices[alias], choices["next"])

        # argparse keeps the invoked spelling in `command` (it does NOT canonicalize an
        # alias), which is why the dispatch tests membership rather than equality.
        self.assertEqual(parser.parse_args(["att"]).command, "att")
        self.assertEqual(parser.parse_args(["todo"]).command, "todo")

        # The options that used to fail under `todo` must now parse under every spelling.
        for name in ("next", "attention", "att", "todo"):
            ns = parser.parse_args([name, "--format", "json", "--check"])
            self.assertEqual(ns.format, "json")
            self.assertTrue(ns.check)

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
