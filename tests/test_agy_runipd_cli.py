"""Tests for the `aw agy` / `aw antigravity` subcommand group.

The group forwards the raw argv tail verbatim to `agent_workflows.agy_runipd.main`, so `aw agy runipd`
(and its `antigravity` alias and `run`/`runagy` subcommands) has exact CLI parity with the standalone
runner - including the runner's own `--help` and its implicit-`start` shim.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from agent_workflows import agy_runipd, cli


def _run_cli(argv):
    """Run `aw <argv...>` capturing (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:  # argparse may exit
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


class AgyRunipdCliTests(unittest.TestCase):
    def test_help_forwards_to_runner_both_aliases(self):
        for group in ("agy", "antigravity"):
            for subcmd in ("runipd", "run", "runagy"):
                rc, out, err = _run_cli([group, subcmd, "--help"])
                combined = out + err
                self.assertEqual(rc, 0, f"{group} {subcmd} --help rc={rc}: {combined}")
                self.assertIn("runagy", combined)
                self.assertIn("start", combined)
                self.assertIn("resume", combined)
                self.assertIn("status", combined)
                self.assertIn("report", combined)

    def test_forwarding_delegates_to_agy_runipd_main(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            rc = cli.main(["agy", "runipd", "status", "run-xyz"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["status", "run-xyz"])

    def test_antigravity_alias_delegates_identically(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            cli.main(["antigravity", "run", "resume", "run-xyz", "--retry-incomplete"])
        m.assert_called_once_with(["resume", "run-xyz", "--retry-incomplete"])

    def test_implicit_start_shim_preserved_through_wrapper(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            cli.main(["agy", "runipd", "somesetid", "--dry-run"])
        m.assert_called_once_with(["somesetid", "--dry-run"])

    def test_bare_agy_group_shows_family_help(self):
        rc, out, err = _run_cli(["agy"])
        self.assertIn("runipd", out + err)


if __name__ == "__main__":
    unittest.main()
