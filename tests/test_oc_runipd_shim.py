"""Tests for awocrunner Order 03 (4tlkgj): the tools/ipdrunner/runipd.py compatibility shim.

The shim must preserve `python3 tools/ipdrunner/runipd.py ...` while holding NO copy of the runner
logic - it delegates to `agent_workflows.oc_runipd`. These tests prove behavioral parity (via a real
subprocess) and that the re-exported public names ARE the packaged objects (identity, no shadow copy).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest

from agent_workflows import oc_runipd
from tests.support import REPO_ROOT

_SHIM_PATH = REPO_ROOT / "tools" / "ipdrunner" / "runipd.py"


def _load_shim_module():
    """Import the shim file as a module object (without relying on cwd/sys.path order)."""
    spec = importlib.util.spec_from_file_location("_runipd_shim_under_test", _SHIM_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RunipdShimTests(unittest.TestCase):
    def test_shim_exists_and_is_small(self):
        self.assertTrue(_SHIM_PATH.is_file())
        # A thin delegating shim, not the ~2200-line runner.
        line_count = len(_SHIM_PATH.read_text(encoding="utf-8").splitlines())
        self.assertLess(line_count, 80, "shim should be small (no copied runner logic)")

    def test_shim_contains_no_runner_logic(self):
        text = _SHIM_PATH.read_text(encoding="utf-8")
        self.assertIn("from agent_workflows import oc_runipd", text)
        # Sentinels of the actual runner implementation must NOT appear in the shim.
        self.assertNotIn("def run_queue", text)
        self.assertNotIn("def initialize_run", text)
        self.assertNotIn("def dependency_status", text)

    def test_public_names_are_the_packaged_objects(self):
        shim = _load_shim_module()
        for name in ("main", "DriverError", "Palette", "Heartbeat", "PlanRecord"):
            self.assertTrue(hasattr(shim, name), f"shim missing re-export {name}")
            self.assertIs(
                getattr(shim, name),
                getattr(oc_runipd, name),
                f"{name} must be the same object as oc_runipd.{name} (no shadow copy)",
            )

    def test_help_parity_via_subprocess(self):
        # Running the shim file directly renders the runner's own help, identical to `-m`.
        shim_out = subprocess.run(
            [sys.executable, str(_SHIM_PATH), "--help"],
            capture_output=True,
            text=True,
        )
        pkg_out = subprocess.run(
            [sys.executable, "-m", "agent_workflows.oc_runipd", "--help"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(shim_out.returncode, 0, shim_out.stderr)
        self.assertEqual(shim_out.stdout, pkg_out.stdout)
        self.assertIn("runipd", shim_out.stdout)

    def test_status_parity_via_subprocess(self):
        # A non-mutating `status` against a missing run yields the same rc as the packaged main.
        shim_res = subprocess.run(
            [sys.executable, str(_SHIM_PATH), "status", "no-such-run-xyz"],
            capture_output=True,
            text=True,
        )
        rc_direct = oc_runipd.main(["status", "no-such-run-xyz"])
        self.assertEqual(shim_res.returncode, rc_direct)


if __name__ == "__main__":
    unittest.main()
