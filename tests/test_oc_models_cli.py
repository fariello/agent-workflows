"""Tests for ocsync Order 01 (g7hljt) E-05: the `aw oc update-models` CLI wiring.

Unlike `aw oc runipd` (which forwards argparse.REMAINDER verbatim), this verb declares
STRUCTURED flags in `cli.py` and is dispatched from the parsed namespace. These tests assert the
parser surface and that dispatch reaches `oc_models.run` with the flags the user typed; the
module's own behavior is covered by `tests/test_oc_models.py`.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from agent_workflows import cli


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


class ParserSurfaceTests(unittest.TestCase):
    def test_oc_help_lists_update_models(self):
        rc, out, err = _run_cli(["oc", "--help"])
        text = out + err
        self.assertEqual(rc, 0)
        self.assertIn("update-models", text)
        self.assertIn("sync-models", text)

    def test_update_models_help_shows_every_flag(self):
        rc, out, err = _run_cli(["oc", "update-models", "--help"])
        text = out + err
        self.assertEqual(rc, 0)
        for flag in (
            "--config",
            "--apply",
            "--dry-run",
            "--no-backup",
            "--allow-insecure",
        ):
            self.assertIn(flag, text, f"{flag} missing from --help")

    def test_help_states_formatting_caveat_honestly(self):
        """E-06: --help must not overclaim byte preservation."""
        _rc, out, err = _run_cli(["oc", "update-models", "--help"])
        text = (out + err).replace("\n", " ")
        self.assertIn("not preserved", text)
        self.assertIn("https", text)


class DispatchTests(unittest.TestCase):
    def test_dispatch_invokes_oc_models_run(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as run:
            rc, _, _ = _run_cli(["oc", "update-models"])
        self.assertEqual(rc, 0)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], [])

    def test_alias_sync_models_dispatches(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as run:
            rc, _, _ = _run_cli(["oc", "sync-models"])
        self.assertEqual(rc, 0)
        run.assert_called_once()

    def test_opencode_alias_dispatches(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as run:
            rc, _, _ = _run_cli(["opencode", "update-models"])
        self.assertEqual(rc, 0)
        run.assert_called_once()

    def test_flags_are_forwarded(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as run:
            _run_cli(
                [
                    "oc",
                    "update-models",
                    "--config",
                    "/tmp/x.json",
                    "--apply",
                    "--no-backup",
                    "--allow-insecure",
                ]
            )
        forwarded = run.call_args.args[0]
        self.assertIn("--config", forwarded)
        self.assertIn("/tmp/x.json", forwarded)
        self.assertIn("--apply", forwarded)
        self.assertIn("--no-backup", forwarded)
        self.assertIn("--allow-insecure", forwarded)

    def test_dry_run_flag_forwarded(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as run:
            _run_cli(["oc", "update-models", "--dry-run"])
        self.assertIn("--dry-run", run.call_args.args[0])

    def test_exit_code_propagates(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=2):
            rc, _, _ = _run_cli(["oc", "update-models"])
        self.assertEqual(rc, 2)

    def test_bare_oc_still_shows_family_help(self):
        """Adding the verb must not break the existing family-help behavior."""
        _rc, out, err = _run_cli(["oc"])
        text = out + err
        self.assertIn("update-models", text)


class RunipdParityTests(unittest.TestCase):
    """Adding a structured verb must not disturb the REMAINDER forwarding of `runipd`."""

    def test_runipd_still_forwards_verbatim(self):
        with mock.patch("agent_workflows.oc_runipd.main", return_value=0) as main:
            rc, _, _ = _run_cli(["oc", "runipd", "status", "abc123"])
        self.assertEqual(rc, 0)
        main.assert_called_once_with(["status", "abc123"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
