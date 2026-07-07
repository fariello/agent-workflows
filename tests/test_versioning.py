"""Self-tests for versioning.py (git-tag-driven version resolution). Stdlib unittest only.

The resolver is tested by FEEDING the parser the exact real ``git describe --long``
strings rather than shelling out, so the tests are deterministic and do not depend on
the repo's tag state. The subprocess-fallback path is tested by stubbing ``_git_describe``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.support import REPO_ROOT, load_module

VER = load_module("versioning", REPO_ROOT / "versioning.py")

DATE = "20260706"  # fixed UTC date for deterministic dev-segment assertions


class ParseDescribeTests(unittest.TestCase):
    """The seven real describe shapes -> exact PEP 440 strings (IPD-1 Step 1)."""

    def test_exact_tag_clean(self):
        self.assertEqual(VER.parse_describe("v1.0.0-0-gd644d2d", date=DATE), "1.0.0")

    def test_exact_tag_dirty(self):
        # Release commit with local edits: not a clean release; dev of the next patch.
        self.assertEqual(
            VER.parse_describe("v1.0.0-0-gd644d2d-dirty", date=DATE),
            "1.0.1.dev0+gd644d2d.d20260706",
        )

    def test_ahead_clean(self):
        self.assertEqual(
            VER.parse_describe("v1.0.0-2-g49f2bdc", date=DATE), "1.0.1.dev2+g49f2bdc"
        )

    def test_ahead_dirty(self):
        self.assertEqual(
            VER.parse_describe("v1.0.0-2-g49f2bdc-dirty", date=DATE),
            "1.0.1.dev2+g49f2bdc.d20260706",
        )

    def test_no_tags_clean(self):
        self.assertEqual(VER.parse_describe("d644d2d", date=DATE), "0.0.0+gd644d2d")

    def test_no_tags_dirty(self):
        # V-7: the real dirty-no-tags form appends -dirty to the bare sha.
        self.assertEqual(
            VER.parse_describe("9042038-dirty", date=DATE), "0.0.0+g9042038.d20260706"
        )

    def test_next_patch_bump(self):
        # A non-zero minor tag bumps only the patch.
        self.assertEqual(
            VER.parse_describe("v2.3.4-1-gabc1234", date=DATE), "2.3.5.dev1+gabc1234"
        )


class ResolveVersionTests(unittest.TestCase):
    """resolve_version: git branch vs VERSION-file fallback (V-8)."""

    def test_falls_back_to_version_file_when_git_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            vpath = root / ".agents" / "workflows" / "VERSION"
            vpath.parent.mkdir(parents=True)
            vpath.write_text("1.2.3\n", encoding="utf-8")
            # Stub the describe helper to simulate no-git / non-zero-exit -> None.
            orig = VER._git_describe
            VER._git_describe = lambda repo_root: None
            try:
                self.assertEqual(VER.resolve_version(root), "1.2.3")
            finally:
                VER._git_describe = orig

    def test_uses_git_when_available(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            orig = VER._git_describe
            VER._git_describe = lambda repo_root: "v1.0.0-0-gd644d2d"
            try:
                self.assertEqual(VER.resolve_version(root), "1.0.0")
            finally:
                VER._git_describe = orig

    def test_missing_file_and_no_git_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            orig = VER._git_describe
            VER._git_describe = lambda repo_root: None
            try:
                self.assertEqual(VER.resolve_version(root), "unknown")
            finally:
                VER._git_describe = orig


class ComparatorTests(unittest.TestCase):
    """The dependency-free comparator over our controlled shape (V-5)."""

    def test_dev_sorts_before_release(self):
        self.assertEqual(VER.compare("1.0.1.dev2", "1.0.1"), -1)
        self.assertEqual(VER.compare("1.0.1", "1.0.1.dev2"), 1)

    def test_release_ordering(self):
        self.assertEqual(VER.compare("1.0.1", "1.1.0"), -1)
        self.assertEqual(VER.compare("1.1.0", "1.0.1"), 1)
        self.assertEqual(VER.compare("1.0.0", "1.0.0"), 0)

    def test_local_segment_ignored_for_ordering(self):
        # Two dev builds of the same base with different local segments compare equal.
        self.assertEqual(
            VER.compare("1.0.1.dev2+gaaaa", "1.0.1.dev2+gbbbb.d20260706"), 0
        )

    def test_dev_number_ordering(self):
        self.assertEqual(VER.compare("1.0.1.dev1", "1.0.1.dev2"), -1)

    def test_compare_rejects_legacy(self):
        with self.assertRaises(ValueError):
            VER.compare("20260704-06", "1.0.0")


class StatusTests(unittest.TestCase):
    """status(target, packaged) state mapping (V-5)."""

    def test_not_installed(self):
        self.assertEqual(VER.status(None, "1.0.0"), "not-installed")
        self.assertEqual(VER.status("", "1.0.0"), "not-installed")
        self.assertEqual(VER.status("unknown", "1.0.0"), "not-installed")

    def test_stale(self):
        self.assertEqual(VER.status("1.0.0", "1.0.1"), "stale")

    def test_current(self):
        self.assertEqual(VER.status("1.0.1", "1.0.1"), "current")

    def test_ahead(self):
        self.assertEqual(VER.status("1.1.0", "1.0.1"), "ahead")

    def test_dev_target_is_dev(self):
        # A .devN or +local target is a dev/dirty build regardless of comparison.
        self.assertEqual(VER.status("1.0.1.dev2+gabc1234", "1.0.0"), "dev")
        self.assertEqual(VER.status("1.0.0+gabc1234.d20260706", "1.0.0"), "dev")

    def test_legacy_target_is_unknown(self):
        # A pre-migration YYYYMMDD-NN install cannot be classified: unknown, not stale.
        self.assertEqual(VER.status("20260704-06", "1.0.0"), "unknown")

    def test_prebaseline_is_unknown(self):
        self.assertEqual(VER.status("0.0.0+gd644d2d", "1.0.0"), "unknown")


if __name__ == "__main__":
    unittest.main()
