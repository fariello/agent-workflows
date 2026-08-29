"""Tests for runnernorm Order 02 (puot79) + follow-up (puot79e04): graduate the agy tools.

The unambiguous source-checkout tools were graduated under the awocrunner
packaged-core + host-subcommand + compat-shim pattern:
  - tools/agy_sessions.py         -> agent_workflows.agy_sessions  -> `aw agy sessions`
  - tools/view-antigravity-jsonl.py -> agent_workflows.agy_view    -> `aw agy view`
  - tools/pwatch.py               -> agent_workflows.pwatch        -> `aw pwatch`

The follow-up (puot79e04) graduated the remaining tool under a NON-colliding surface:
  - tools/agy_run.py              -> agent_workflows.agy_run        -> `aw agy exec`

These tests assert:
1. Each `aw` surface forwards the raw argv tail verbatim to the packaged core's main().
2. `aw agy run`/`aw agy runagy`/`runipd` STILL resolve to the runipd driver (no collision
   from the `sessions`/`view`/`exec` subcommands) - the OQ-02 invariant.
3. Each `tools/*.py` compat shim forwards to its packaged core and re-exports its symbols.

agy_run.py was dispositioned per OQ-02 as genuinely distinct from the multi-IPD queue
driver, so it is graduated as `aw agy exec` (NOT `aw agy run`, which stays aliased to
runipd), tools/agy_run.py is a compat shim, and agent_workflows/agy_run.py is the core.
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from agent_workflows import agy_run, agy_runipd, agy_sessions, agy_view, cli, pwatch
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

    def test_agy_exec_surface_exists(self):
        # puot79e04 graduated agy_run.py under the non-colliding `aw agy exec` surface;
        # its `--help` must now succeed and show the runner usage (NOT an invalid-choice error).
        rc, out, err = _run_cli(["agy", "exec", "--help"])
        combined = out + err
        self.assertEqual(rc, 0, combined)
        self.assertIn("agy_run.py", combined)
        self.assertNotIn("invalid choice", combined.lower())


class AgyExecSurfaceTests(unittest.TestCase):
    """puot79e04: `aw agy exec` forwards to the packaged agy_run core (both invocation forms)."""

    def test_forwarding_delegates_to_packaged_core(self):
        with mock.patch.object(agy_run, "main", return_value=0) as m:
            rc = cli.main(["agy", "exec", "-p", "do the thing"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["-p", "do the thing"])

    def test_antigravity_alias_delegates_identically(self):
        with mock.patch.object(agy_run, "main", return_value=0) as m:
            cli.main(["antigravity", "exec", "7cvh9t"])
        m.assert_called_once_with(["7cvh9t"])

    def test_help_forwards_to_core(self):
        rc, out, err = _run_cli(["agy", "exec", "--help"])
        combined = out + err
        self.assertEqual(rc, 0, combined)
        self.assertIn("agy_run.py", combined)

    def test_exec_does_not_route_to_runipd(self):
        # exec is a distinct surface: it must NOT reach the multi-IPD queue driver.
        with mock.patch.object(agy_run, "main", return_value=0) as m_run:
            with mock.patch.object(agy_runipd, "main", return_value=0) as m_ipd:
                cli.main(["agy", "exec", "-p", "x"])
        m_run.assert_called_once_with(["-p", "x"])
        m_ipd.assert_not_called()


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


class AgyRunGraduatedTests(unittest.TestCase):
    """puot79e04: agy_run.py is graduated - tool reduced to a shim, packaged core added."""

    def test_agy_run_tool_reduced_to_shim(self):
        agy_run_path = REPO_ROOT / "tools" / "agy_run.py"
        self.assertTrue(agy_run_path.is_file())
        text = agy_run_path.read_text(encoding="utf-8")
        # The tool is now a thin compat shim: it re-exports the packaged core and holds no
        # tool logic (so the standalone parser `prog="agy_run.py"` no longer lives here).
        self.assertNotIn('prog="agy_run.py"', text)
        self.assertIn("from agent_workflows import agy_run", text)

    def test_packaged_agy_run_core_exists(self):
        core = REPO_ROOT / "agent_workflows" / "agy_run.py"
        self.assertTrue(core.exists())
        # The parser (prog="agy_run.py") now lives in the packaged core.
        self.assertIn('prog="agy_run.py"', core.read_text(encoding="utf-8"))

    def test_agy_run_shim_reexports_and_delegates(self):
        shim = _load_shim(REPO_ROOT / "tools" / "agy_run.py", "shim_agy_run")
        self.assertIs(shim.agy_run, agy_run)
        self.assertIs(shim.ScriptError, agy_run.ScriptError)
        self.assertIs(shim.AgyResult, agy_run.AgyResult)
        self.assertIs(shim.resolve_ipd, agy_run.resolve_ipd)
        self.assertIs(shim.run_agy, agy_run.run_agy)
        self.assertIs(shim.main, agy_run.main)


if __name__ == "__main__":
    unittest.main()
