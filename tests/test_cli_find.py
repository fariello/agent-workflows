"""Tests for aw find and token-efficient bare path discovery (--paths / -p).

Plan v8xdz4 (findpaths-01).
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli


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


if __name__ == "__main__":
    unittest.main()
