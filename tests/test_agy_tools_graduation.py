"""Tests for runnernorm Order 02 (puot79): graduate agy sessions/view + pwatch.

The three unambiguous source-checkout tools were graduated under the awocrunner
packaged-core + host-subcommand + compat-shim pattern:
  - tools/agy_sessions.py         -> agent_workflows.agy_sessions  -> `aw agy sessions`
  - tools/view-antigravity-jsonl.py -> agent_workflows.agy_view    -> `aw agy view`
  - tools/pwatch.py               -> agent_workflows.pwatch        -> `aw pwatch`

These tests assert:
1. Each `aw` surface forwards the raw argv tail verbatim to the packaged core's main().
2. `aw agy run`/`aw agy runagy` STILL resolve to the runipd driver (no collision from
   the new `sessions`/`view` subcommands) - the OQ-02 invariant.
3. Each `tools/*.py` compat shim forwards to its packaged core and re-exports its symbols.

agy_run.py is dispositioned per OQ-02 as genuinely distinct (graduation split to a
follow-up plan); it is intentionally NOT graduated here, so there is no `aw agy exec`
surface yet and `tools/agy_run.py` is untouched.
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, agy_sessions, agy_view, cli, pwatch
from tests.support import REPO_ROOT


def _run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


class AgySessionsSurfaceTests(unittest.TestCase):
    def test_forwarding_delegates_to_packaged_core(self):
        with mock.patch.object(agy_sessions, "main", return_value=0) as m:
            rc = cli.main(["agy", "sessions", "--json", "/some/dir"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["--json", "/some/dir"])

    def test_antigravity_alias_delegates_identically(self):
        with mock.patch.object(agy_sessions, "main", return_value=0) as m:
            cli.main(["antigravity", "sessions", "--all"])
        m.assert_called_once_with(["--all"])

    def test_help_forwards_to_core(self):
        rc, out, err = _run_cli(["agy", "sessions", "--help"])
        combined = out + err
        self.assertEqual(rc, 0, combined)
        self.assertIn("agy sessions", combined)


class AgyViewSurfaceTests(unittest.TestCase):
    def test_forwarding_delegates_to_packaged_core(self):
        with mock.patch.object(agy_view, "main", return_value=0) as m:
            rc = cli.main(["agy", "view", "--raw", "-"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["--raw", "-"])

    def test_legacy_name_alias_delegates(self):
        with mock.patch.object(agy_view, "main", return_value=0) as m:
            cli.main(["agy", "view-antigravity-jsonl", "--match", "x"])
        m.assert_called_once_with(["--match", "x"])

    def test_help_forwards_to_core(self):
        rc, out, err = _run_cli(["agy", "view", "--help"])
        combined = out + err
        self.assertEqual(rc, 0, combined)
        self.assertIn("agy view", combined)


class PwatchSurfaceTests(unittest.TestCase):
    def test_forwarding_delegates_to_packaged_core(self):
        with mock.patch.object(pwatch, "main", return_value=0) as m:
            rc = cli.main(["pwatch", "-M", "python", "--once"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["-M", "python", "--once"])

    def test_help_forwards_to_core(self):
        rc, out, err = _run_cli(["pwatch", "--help"])
        combined = out + err
        self.assertEqual(rc, 0, combined)
        self.assertIn("pwatch", combined)


class NoAgyRunCollisionTests(unittest.TestCase):
    """OQ-02 invariant: `aw agy run`/`runagy` still resolve to the runipd driver."""

    def test_agy_run_still_routes_to_runipd(self):
        for alias in ("run", "runagy", "runipd"):
            with mock.patch.object(agy_runipd, "main", return_value=0) as m_ipd:
                with mock.patch.object(agy_sessions, "main", return_value=0) as m_sess:
                    with mock.patch.object(agy_view, "main", return_value=0) as m_view:
                        rc = cli.main(["agy", alias, "status", "run-xyz"])
            self.assertEqual(rc, 0)
            m_ipd.assert_called_once_with(["status", "run-xyz"])
            m_sess.assert_not_called()
            m_view.assert_not_called()

    def test_no_agy_exec_surface_yet(self):
        # agy_run.py graduation is deferred (OQ-02 disposition B, split to follow-up);
        # there must be no `aw agy exec` surface in this turn.
        rc, out, err = _run_cli(["agy", "exec", "--help"])
        combined = out + err
        self.assertNotEqual(rc, 0)
        self.assertIn("invalid choice", combined.lower())


def _load_shim(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompatShimForwardingTests(unittest.TestCase):
    """Each tools/*.py shim forwards to its packaged core and re-exports its symbols."""

    def test_agy_sessions_shim_reexports_and_delegates(self):
        shim = _load_shim(REPO_ROOT / "tools" / "agy_sessions.py", "shim_agy_sessions")
        self.assertIs(shim.agy_sessions, agy_sessions)
        self.assertIs(shim.get_sessions, agy_sessions.get_sessions)
        self.assertIs(shim.SessionInfo, agy_sessions.SessionInfo)
        self.assertIs(shim.main, agy_sessions.main)

    def test_agy_view_shim_reexports_and_delegates(self):
        shim = _load_shim(
            REPO_ROOT / "tools" / "view-antigravity-jsonl.py", "shim_agy_view"
        )
        self.assertIs(shim.agy_view, agy_view)
        self.assertIs(shim.format_record, agy_view.format_record)
        self.assertIs(shim.main, agy_view.main)

    def test_pwatch_shim_reexports_and_delegates(self):
        shim = _load_shim(REPO_ROOT / "tools" / "pwatch.py", "shim_pwatch")
        self.assertIs(shim.pwatch, pwatch)
        self.assertIs(shim.main, pwatch.main)
        self.assertIs(shim.build_parser, pwatch.build_parser)


class AgyRunUntouchedTests(unittest.TestCase):
    """agy_run.py is intentionally NOT graduated this turn (OQ-02 -> follow-up plan)."""

    def test_agy_run_tool_still_present_as_standalone(self):
        agy_run_path = REPO_ROOT / "tools" / "agy_run.py"
        self.assertTrue(agy_run_path.is_file())
        text = agy_run_path.read_text(encoding="utf-8")
        # Still the standalone multi-mode runner, not reduced to a shim.
        self.assertIn('prog="agy_run.py"', text)

    def test_no_packaged_agy_run_core_yet(self):
        self.assertFalse((REPO_ROOT / "agent_workflows" / "agy_run.py").exists())


if __name__ == "__main__":
    unittest.main()
