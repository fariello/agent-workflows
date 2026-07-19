"""Regression guard: no personal-path / identity leaks in tracked files (D92).

Verifies (a) THIS repo's tracked tree is clean, and (b) the scanner actually catches a
planted leak. The planted-leak fixture is SYNTHESIZED at runtime in a throwaway git repo
so this test file never itself contains a real leak token. Stdlib unittest only.
"""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import REPO_ROOT

_SCANNER = REPO_ROOT / "tools" / "check_personal_paths.py"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("check_personal_paths", _SCANNER)
    assert spec and spec.loader, "could not load scanner module spec"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NoPersonalPathsTests(unittest.TestCase):
    def test_scanner_exists(self):
        self.assertTrue(_SCANNER.is_file(), f"scanner missing: {_SCANNER}")

    def test_this_repo_is_clean(self):
        mod = _load_scanner()
        violations = mod.scan(REPO_ROOT)
        self.assertEqual(
            violations,
            [],
            "personal-path leak(s) in tracked files:\n" + "\n".join(violations),
        )

    def test_scanner_catches_a_planted_leak(self):
        mod = _load_scanner()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "-C", td, "init", "-q"], check=True)
            # Synthesize a leak token at runtime (never stored literally in this file).
            leak = "/home/" + "someuser" + "/VC/agent-workflows"
            (root / "leaky.md").write_text(f"see {leak}\n", encoding="utf-8")
            subprocess.run(["git", "-C", td, "add", "leaky.md"], check=True)
            violations = mod.scan(root)
            self.assertTrue(
                any("home-path" in v for v in violations),
                f"scanner failed to flag a planted leak: {violations}",
            )

    def test_scanner_allows_public_identifiers(self):
        mod = _load_scanner()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "-C", td, "init", "-q"], check=True)
            (root / "meta.md").write_text(
                "author gfariello@fariel.com; origin git@github.com:fariello/agent-workflows.git\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", td, "add", "meta.md"], check=True)
            self.assertEqual(
                mod.scan(root),
                [],
                "scanner false-flagged an allowlisted public identifier",
            )


if __name__ == "__main__":
    unittest.main()
