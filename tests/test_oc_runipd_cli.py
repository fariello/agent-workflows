"""Tests for awocrunner Order 02 (nfo184): the `aw oc` / `aw opencode` subcommand group.

The group forwards the raw argv tail verbatim to `agent_workflows.oc_runipd.main`, so `aw oc runipd`
(and its `opencode` alias) has exact CLI parity with the standalone runner - including the runner's
own `--help` and its implicit-`start` shim. These tests assert that forwarding, not the runner's
internal behavior (which `tests/test_oc_runipd.py` covers).
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

from agent_workflows import cli
from agent_workflows import oc_runipd


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


class OcRunipdCliTests(unittest.TestCase):
    def test_help_forwards_to_runner_both_aliases(self):
        for group in ("oc", "opencode"):
            rc, out, err = _run_cli([group, "runipd", "--help"])
            combined = out + err
            self.assertEqual(rc, 0, f"{group} runipd --help rc={rc}: {combined}")
            # The RUNNER's own help (prog 'runipd' with its subcommands), not a cli.py stub.
            self.assertIn("runipd", combined)
            self.assertIn("start", combined)
            self.assertIn("resume", combined)
            self.assertIn("status", combined)
            self.assertIn("report", combined)

    def test_forwarding_delegates_to_oc_runipd_main(self):
        # `aw oc runipd status X` must call oc_runipd.main(["status", "X"]) verbatim.
        with mock.patch.object(oc_runipd, "main", return_value=0) as m:
            rc = cli.main(["oc", "runipd", "status", "run-xyz"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["status", "run-xyz"])

    def test_opencode_alias_delegates_identically(self):
        with mock.patch.object(oc_runipd, "main", return_value=0) as m:
            cli.main(["opencode", "runipd", "resume", "run-xyz", "--retry-incomplete"])
        m.assert_called_once_with(["resume", "run-xyz", "--retry-incomplete"])

    def test_implicit_start_shim_preserved_through_wrapper(self):
        # A bare non-subcommand first token is forwarded unchanged; the implicit-`start` shim lives
        # in oc_runipd.main (not build_parser), so forwarding the raw tail preserves it.
        with mock.patch.object(oc_runipd, "main", return_value=0) as m:
            cli.main(["oc", "runipd", "somesetid", "--prepare-only"])
        m.assert_called_once_with(["somesetid", "--prepare-only"])

    def test_status_invocation_parity_with_direct_main(self):
        # `aw oc runipd status <missing>` returns the same rc as oc_runipd.main(["status", <missing>]).
        rc_direct = oc_runipd.main(["status", "definitely-no-such-run"])
        rc_cli, _out, _err = _run_cli(
            ["oc", "runipd", "status", "definitely-no-such-run"]
        )
        self.assertEqual(rc_cli, rc_direct)

    def test_bare_oc_group_shows_family_help(self):
        rc, out, err = _run_cli(["oc"])
        # Non-zero family-help exit, listing the runipd subcommand.
        self.assertIn("runipd", out + err)


if __name__ == "__main__":
    unittest.main()
