"""Self-tests for setup_tools.py. Stdlib unittest only. Detection/install paths touch the
real system, so these cover only the pure/safe surface: --version and the tool table shape."""

from __future__ import annotations

import unittest

from tests.support import SETUP_TOOLS, REPO_ROOT, run_tool, load_module

ST = load_module("setup_tools", SETUP_TOOLS)


class SetupToolsTests(unittest.TestCase):
    def test_version_flag(self):
        proc = run_tool(SETUP_TOOLS, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = (REPO_ROOT / ".agents/workflows/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(proc.stdout.strip(), expected)

    def test_tools_table_is_well_formed(self):
        # Every known tool declares purpose, version_cmd, installers, and a manual fallback.
        self.assertTrue(ST.TOOLS, "TOOLS table is empty")
        for name, spec in ST.TOOLS.items():
            self.assertIn("purpose", spec, name)
            self.assertIn("installers", spec, name)
            self.assertIn("manual", spec, name)


if __name__ == "__main__":
    unittest.main()
