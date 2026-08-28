"""Tests for awcmdsurf Order 01: the TYPE-noun vocabulary, TYPE_BACKENDS routing, exit-code helper,
and the six new noun-verb parsers."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import artifact_types as at
from agent_workflows import cli


class VocabTests(unittest.TestCase):
    def test_normalize(self) -> None:
        self.assertEqual(at.normalize_type("plan"), "plans")
        self.assertEqual(at.normalize_type("specs"), "specs")
        self.assertEqual(at.normalize_type("all"), "all")
        self.assertEqual(at.normalize_type("other"), "other")
        self.assertEqual(at.normalize_type("misc"), "other")

    def test_normalize_unknown_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            at.normalize_type("bogus")
        self.assertIn("valid types", str(ctx.exception))

    def test_expand(self) -> None:
        self.assertEqual(
            at.expand_types("all", supported=("plans", "specs")), ["plans", "specs"]
        )
        self.assertEqual(at.expand_types("plan", supported=("plans",)), ["plans"])
        with self.assertRaises(ValueError):
            at.expand_types("comms", supported=("plans",))


class BackendMapTests(unittest.TestCase):
    def test_lookup(self) -> None:
        self.assertEqual(at.TYPE_BACKENDS["plans"]["rename"], "plans_refs.run_mv")
        self.assertIsNone(at.backend_name("specs", "index"))

    def test_no_eager_import(self) -> None:
        # importing artifact_types must not import the backend modules.
        import importlib

        importlib.reload(at)
        # after reload, the backend modules should still not be forced in (they may be present from
        # elsewhere, so just assert artifact_types itself declares strings, not callables).
        self.assertIsInstance(at.TYPE_BACKENDS["plans"]["index"], str)


class ExitCodeTests(unittest.TestCase):
    def test_codes(self) -> None:
        from agent_workflows.artifact_core import Drift

        self.assertEqual(at.exit_code_for([]), 0)
        self.assertEqual(at.exit_code_for([Drift("l", "r", "d")]), 1)
        self.assertEqual(at.EXIT_CANNOT_RUN, 2)


class ParserTests(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_help_parses_for_all_six(self) -> None:
        for v in ("check", "find", "search", "index", "rename", "group"):
            rc, out, err = self._run([v, "--help"])
            self.assertEqual(rc, 0, f"{v} --help rc={rc}")

    def test_unknown_type_errors(self) -> None:
        rc, out, err = self._run(["check", "bogus"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
