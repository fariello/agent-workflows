"""Tests for the tools/ipdrunner/runagy.py compatibility shim.

The shim must preserve `python3 tools/ipdrunner/runagy.py ...` while holding NO copy of the runner
logic - it delegates to `agent_workflows.agy_runipd`.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest

from agent_workflows import agy_runipd
from tests.support import REPO_ROOT

_SHIM_PATH = REPO_ROOT / "tools" / "ipdrunner" / "runagy.py"


def _load_shim_module():
    """Import the shim file as a module object (without relying on cwd/sys.path order)."""
    spec = importlib.util.spec_from_file_location("_runagy_shim_under_test", _SHIM_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RunagyShimTests(unittest.TestCase):
    def test_shim_exists_and_is_small(self):
        self.assertTrue(_SHIM_PATH.is_file())
        line_count = len(_SHIM_PATH.read_text(encoding="utf-8").splitlines())
        self.assertLess(line_count, 80, "shim should be small (no copied runner logic)")

    def test_shim_contains_no_runner_logic(self):
        text = _SHIM_PATH.read_text(encoding="utf-8")
        self.assertIn("from agent_workflows import agy_runipd", text)
        self.assertNotIn("def run_queue", text)
        self.assertNotIn("def initialize_run", text)
        self.assertNotIn("def dependency_status", text)

    def test_public_names_are_the_packaged_objects(self):
        shim = _load_shim_module()
        for name in ("main", "DriverError", "Palette", "Heartbeat", "PlanRecord"):
            self.assertTrue(hasattr(shim, name), f"shim missing re-export {name}")
            self.assertIs(
                getattr(shim, name),
                getattr(agy_runipd, name),
                f"{name} must be the same object as agy_runipd.{name} (no shadow copy)",
            )

    def test_help_parity_via_subprocess(self):
        shim_out = subprocess.run(
            [sys.executable, str(_SHIM_PATH), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(shim_out.returncode, 0)
        self.assertIn("Autonomous Antigravity", shim_out.stdout)


if __name__ == "__main__":
    unittest.main()
