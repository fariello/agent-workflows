"""Tests for aw find and token-efficient bare path discovery (--paths / -p).

Plan v8xdz4 (findpaths-01).
"""

from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows.term import Term


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    """Run `aw <argv...>` capturing (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


class TestCliFindPaths(unittest.TestCase):
    def test_find_with_paths_flag_emits_bare_relative_paths(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))
            self.assertTrue(line.endswith(".ipd.md"))
            self.assertNotIn(" ", line)  # No column formatting or status text

    def test_find_with_long_paths_flag(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--paths"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))

    def test_find_with_agent_flag_emits_bare_relative_paths(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))
            self.assertTrue(line.endswith(".ipd.md"))
            self.assertNotIn("{", line)  # Zero JSON overhead

    def test_find_all_types_with_paths_flag(self):
        rc, out, err = _run_cli(["find", "v8xdz4", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/"))

    def test_find_nonexistent_with_paths_exits_nonzero(self):
        rc, out, err = _run_cli(
            ["find", "plans", "definitely_nonexistent_id6_9999", "-p"]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "")

    def test_find_json_includes_paths_and_matches(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "find")
        self.assertIn("paths", data.get("data", {}))
        self.assertIn("matches", data.get("data", {}))
        paths = data["data"]["paths"]
        self.assertTrue(len(paths) >= 1)
        self.assertTrue(any("v8xdz4" in p for p in paths))

    def test_highlight_filename_matches_helper(self):
        term_color = Term(color=True)
        term_plain = Term(color=False)
        path = ".aw/records/plans/pending/20260904-runbypass-01-ki6tom-remove.ipd.md"

        # Plain mode returns identical string
        self.assertEqual(
            cli._highlight_filename_matches(path, ["ki6tom"], term_plain),
            path,
        )

        # Empty tokens returns identical string
        self.assertEqual(
            cli._highlight_filename_matches(path, [], term_color),
            path,
        )

        # Color mode highlights match in filename in bold orange-yellow (214)
        highlighted = cli._highlight_filename_matches(path, ["ki6tom"], term_color)
        expected_match = "\033[1;38;5;214mki6tom\033[0m"
        self.assertIn(expected_match, highlighted)
        self.assertTrue(highlighted.startswith(".aw/records/plans/pending/"))
        # Directory portion must not contain the escape code
        dir_part = highlighted[: len(".aw/records/plans/pending/")]
        self.assertEqual(dir_part, ".aw/records/plans/pending/")

    def test_find_highlights_matching_portions_in_color_mode(self):
        old_force = os.environ.get("FORCE_COLOR")
        try:
            os.environ["FORCE_COLOR"] = "1"
            rc, out, err = _run_cli(["find", "ki6tom", "25kzda"])
            self.assertEqual(rc, 0)
            # ki6tom and 25kzda should appear highlighted in bold orange-yellow (214)
            self.assertIn("\033[1;38;5;214mki6tom\033[0m", out)
            self.assertIn("\033[1;38;5;214m25kzda\033[0m", out)
        finally:
            if old_force is None:
                os.environ.pop("FORCE_COLOR", None)
            else:
                os.environ["FORCE_COLOR"] = old_force

    def test_find_no_color_flag_suppresses_color(self):
        rc, out, err = _run_cli(["find", "--no-color", "ki6tom", "25kzda"])
        self.assertEqual(rc, 0)
        self.assertNotIn("\033[", out)
        self.assertIn("ki6tom", out)
        self.assertIn("25kzda", out)


if __name__ == "__main__":
    unittest.main()
