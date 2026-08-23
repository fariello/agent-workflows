"""Tests for awhelp Order 03: --json on read verbs + documented 0/1/2 exit codes on check verbs."""

from __future__ import annotations

import io
import json
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
    return rc, out.getvalue(), err.getvalue()


class JsonAndExitCodesTests(unittest.TestCase):
    def test_status_json_is_valid(self):
        rc, out, err = _run(["status", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["schema"], "aw.agent/v1")
        self.assertIn("packaged_version", data.get("data", data))
        self.assertIn("currency", data.get("data", data))

    def test_list_repos_json_is_valid(self):
        rc, out, err = _run(["list-repos", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["schema"], "aw.agent/v1")
        repos = data["data"]["repos"] if "data" in data else data["repos"]
        self.assertIsInstance(repos, list)

    def test_status_human_unchanged(self):
        rc, out, err = _run(["status"])
        self.assertEqual(rc, 0)
        self.assertIn("agent-workflows status", out)

    def test_check_exit_codes(self):
        # cannot-run (unknown type) -> 2
        rc, _o, _e = _run(["check", "bogus"])
        self.assertEqual(rc, 2)
        # a supported type runs (0 clean or 1 findings, never crash)
        rc, _o, _e = _run(["check", "specs"])
        self.assertIn(rc, (0, 1))

    def test_check_help_states_exit_codes(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                cli.main(["check", "--help"])
            except SystemExit:
                pass
        h = out.getvalue()
        self.assertIn("0", h)
        self.assertIn("cannot-run", h)


if __name__ == "__main__":
    unittest.main()
