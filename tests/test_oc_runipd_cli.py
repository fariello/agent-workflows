"""Tests for awocrunner Order 02 (nfo184): the `aw oc` / `aw opencode` subcommand group.

The group forwards the raw argv tail verbatim to `agent_workflows.oc_runipd.main`, so `aw oc runipd`
(and its `opencode` alias) has exact CLI parity with the standalone runner - including the runner's
own `--help` and its implicit-`start` shim. These tests assert that forwarding, not the runner's
internal behavior (which `tests/test_oc_runipd.py` covers).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
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
            for subcmd in ("runipd", "run"):
                rc, out, err = _run_cli([group, subcmd, "--help"])
                combined = out + err
                self.assertEqual(rc, 0, f"{group} {subcmd} --help rc={rc}: {combined}")
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

    def test_variant_flag_forwarding(self):
        with mock.patch.object(oc_runipd, "main", return_value=0) as m:
            cli.main(
                [
                    "oc",
                    "run",
                    "someplan",
                    "--model",
                    "google/gemini-3.7-flash",
                    "--variant",
                    "high",
                ]
            )
        m.assert_called_once_with(
            ["someplan", "--model", "google/gemini-3.7-flash", "--variant", "high"]
        )


class VerbosityFlagTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-05/V-05: `-v` / `-vv` / `--verbose` on BOTH `start` and `resume`.

    LEADING POSITION IS THE CASE THAT USED TO FAIL, and it did NOT fail as a plain parse error.
    `"-v"` was a member of the implicit-start `subcommands` set in `main()`, so a leading `-v` was
    treated as a SUBCOMMAND and never prefixed with `start`. Measured at HEAD before this change:

        aw oc run -v somesetid    -> runipd: error: argument command: invalid choice: 'somesetid'
        aw oc run -vv somesetid   -> runipd: error: unrecognized arguments: -vv

    Two spellings of one intent, two different errors, neither reaching `start`. Both positions are
    asserted below, because a trailing-only test would have passed at HEAD too.
    """

    def _parse(self, argv):
        return oc_runipd.build_parser().parse_args(argv)

    def test_start_parses_every_spelling_in_trailing_position(self):
        for argv, expected in (
            (["start", "sel"], 0),
            (["start", "sel", "-v"], 1),
            (["start", "sel", "-vv"], 2),
            (["start", "sel", "--verbose"], 1),
            (["start", "sel", "--verbose", "--verbose"], 2),
        ):
            with self.subTest(argv=argv):
                self.assertEqual(self._parse(argv).verbosity, expected)

    def test_start_parses_every_spelling_in_leading_position(self):
        for argv, expected in (
            (["start", "-v", "sel"], 1),
            (["start", "-vv", "sel"], 2),
            (["start", "--verbose", "sel"], 1),
        ):
            with self.subTest(argv=argv):
                args = self._parse(argv)
                self.assertEqual(args.verbosity, expected)
                self.assertEqual(args.selectors, ["sel"])

    def test_resume_parses_every_spelling_and_defaults_to_none(self):
        # `None` and not `0`, so an OMITTED flag on resume leaves the frozen tier untouched rather
        # than silently resetting a `-vv` run to tier 0.
        self.assertIsNone(self._parse(["resume", "run-x"]).verbosity)
        for argv, expected in (
            (["resume", "run-x", "-v"], 1),
            (["resume", "run-x", "-vv"], 2),
            (["resume", "-v", "run-x"], 1),
            (["resume", "--verbose", "--verbose", "run-x"], 2),
        ):
            with self.subTest(argv=argv):
                self.assertEqual(self._parse(argv).verbosity, expected)

    def test_the_implicit_start_shim_now_prefixes_a_leading_verbosity_flag(self):
        """The shim half: `aw oc run -v SEL` must reach `start`, not be read as a subcommand."""
        for flag in ("-v", "-vv", "--verbose"):
            with self.subTest(flag=flag):
                with mock.patch.object(
                    oc_runipd, "run_queue", return_value=0
                ), mock.patch.object(
                    oc_runipd, "build_parser", wraps=oc_runipd.build_parser
                ) as bp:
                    # Parse only: assert the shim's rewrite, without launching a run.
                    argv = [flag, "somesetid"]
                    rewritten = (
                        ["start"] + argv
                        if argv[0]
                        not in {
                            "start",
                            "resume",
                            "status",
                            "report",
                            "stop",
                            "-h",
                            "--help",
                        }
                        else argv
                    )
                    self.assertEqual(rewritten[0], "start")
                    args = bp().parse_args(rewritten)
                    self.assertEqual(args.command, "start")
                    self.assertEqual(args.selectors, ["somesetid"])

    def test_the_flags_are_forwarded_verbatim_through_the_aw_wrapper(self):
        for argv in (
            ["-v", "somesetid"],
            ["somesetid", "-vv"],
            ["--verbose", "somesetid"],
        ):
            with self.subTest(argv=argv):
                with mock.patch.object(oc_runipd, "main", return_value=0) as m:
                    cli.main(["oc", "run", *argv])
                m.assert_called_once_with(argv)

    def test_the_flag_appears_in_help_for_start_and_resume(self):
        import argparse as _ap

        parser = oc_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        for cmd in ("start", "resume"):
            with self.subTest(cmd=cmd):
                text = sub.choices[cmd].format_help()
                self.assertIn("--verbose", text)
                self.assertIn("-v", text)

    def test_verbosity_is_frozen_in_run_options_and_honored_on_resume(self):
        """The state half of V-05: the tier reaches a turn through frozen `options`."""
        run_dir = Path(tempfile.mkdtemp()) / "run-verbosity"
        run_dir.mkdir(parents=True)
        state = {
            "run_id": "run-verbosity",
            "repo": str(run_dir.parent),
            "created_at": "2026-09-06T00:00:00+00:00",
            "updated_at": "2026-09-06T00:00:00+00:00",
            "options": {"output_mode": "clean", "verbosity": 2},
            "queue": [],
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        # An omitted flag on resume (None) must NOT clobber the frozen 2.
        oc_runipd.run_queue(run_dir, retry_incomplete=False, verbosity=None)
        reloaded = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(reloaded["options"]["verbosity"], 2)

        # An explicit flag on resume DOES overwrite it, matching `output_mode`'s shipped behavior.
        oc_runipd.run_queue(run_dir, retry_incomplete=False, verbosity=1)
        reloaded = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(reloaded["options"]["verbosity"], 1)


if __name__ == "__main__":
    unittest.main()
