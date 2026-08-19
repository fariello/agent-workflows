"""Tests for awcmdsurf Order 02: the noun-verb READ verbs (index/find/search/check) over a fixture."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


class ReadVerbsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        specs = self.root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260101-1200-01-thing.spec.md").write_text(
            "# Spec\n\n- Id: aaa111\n- Status: draft\n\n## Body\n\nfindable content here\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def test_search_finds_content(self) -> None:
        rc, out = self._run(["search", "specs", "findable content"])
        self.assertEqual(rc, 0)
        self.assertIn("findable content", out)

    def test_search_no_match_exits_1(self) -> None:
        rc, out = self._run(["search", "specs", "zzz-nope-zzz"])
        self.assertEqual(rc, 1)

    def test_search_all_spans_trees_without_crash(self) -> None:
        rc, out = self._run(["search", "all", "findable"])
        self.assertEqual(rc, 0)

    def test_search_bad_regex_exits_2(self) -> None:
        rc, out = self._run(["search", "specs", "["])
        self.assertEqual(rc, 2)

    def test_check_specs(self) -> None:
        rc, out = self._run(["check", "specs"])
        self.assertIn(rc, (0, 1))  # runs (no crash); may or may not have findings

    def test_unsupported_type_verb(self) -> None:
        # index is not supported for backlog -> exit 2 with a message
        rc, out = self._run(["index", "backlog"])
        self.assertEqual(rc, 2)

    def test_search_without_type(self) -> None:
        rc, out = self._run(["search", "findable content"])
        self.assertEqual(rc, 0)
        self.assertIn("findable content", out)

    def test_search_line_numbers(self) -> None:
        rc, out = self._run(["search", "--line-numbers", "specs", "findable content"])
        self.assertEqual(rc, 0)
        self.assertIn("findable content", out)
        # Assert line number 8 appears in output
        self.assertTrue(any(line.strip().startswith("8:") for line in out.splitlines()))

    def test_find_without_type(self) -> None:
        rc, out = self._run(["find", "aaa111"])
        self.assertEqual(rc, 0)
        self.assertIn("aaa111", out)

    def test_find_with_type(self) -> None:
        rc, out = self._run(["find", "specs", "aaa111"])
        self.assertEqual(rc, 0)
        self.assertIn("aaa111", out)

    def test_find_help_query_not_hijacked_as_help_flag(self) -> None:
        rc, out = self._run(["find", "help"])
        self.assertEqual(rc, 0)
        self.assertNotIn("usage: agent-workflows find", out)

    def test_unknown_type(self) -> None:
        rc, out = self._run(["index", "bogus"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
