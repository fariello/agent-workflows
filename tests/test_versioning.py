"""Self-tests for versioning.py (git-tag-driven version resolution). Stdlib unittest only.

The resolver is tested by FEEDING the parser the exact real ``git describe --long``
strings rather than shelling out, so the tests are deterministic and do not depend on
the repo's tag state. The subprocess-fallback path is tested by stubbing ``_git_describe``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import versioning as VER

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

    def test_rc_tag_clean(self):
        # A clean release-candidate tag normalizes to valid PEP 440 (X.Y.ZrcN),
        # not the raw SemVer spelling, so pip treats it as a pre-release.
        self.assertEqual(
            VER.parse_describe("v1.2.0-rc.1-0-g49f2bdc", date=DATE), "1.2.0rc1"
        )

    def test_rc_tag_ahead_clean(self):
        # Ahead of an rc tag: a dev build of the NEXT candidate of the same release,
        # so it sorts AFTER the rc (1.2.0rc2.devN > 1.2.0rc1), and it is normalized
        # (not the accidental raw "1.2.0-rc.2.dev3").
        self.assertEqual(
            VER.parse_describe("v1.2.0-rc.1-3-g49f2bdc", date=DATE),
            "1.2.0rc2.dev3+g49f2bdc",
        )

    def test_rc_tag_ahead_dirty(self):
        self.assertEqual(
            VER.parse_describe("v1.2.0-rc.1-3-g49f2bdc-dirty", date=DATE),
            "1.2.0rc2.dev3+g49f2bdc.d20260706",
        )

    def test_rc_pep440_spelling_tag(self):
        # A tag already in PEP 440 spelling (rcN, no hyphen/dot) is handled too.
        self.assertEqual(
            VER.parse_describe("v1.2.0rc1-0-g49f2bdc", date=DATE), "1.2.0rc1"
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

    def test_rc_versions_parse_and_order(self):
        # An rc version (emitted by parse_describe) must be parseable and ordered.
        self.assertIsNotNone(VER.parse_our_version("1.2.0rc1"))
        # rc1 < rc2 < final; and rc2.dev3 < rc2 (dev sorts before its target).
        self.assertEqual(VER.compare("1.2.0rc1", "1.2.0rc2"), -1)
        self.assertEqual(VER.compare("1.2.0rc2", "1.2.0"), -1)
        self.assertEqual(VER.compare("1.2.0rc2.dev3", "1.2.0rc2"), -1)
        self.assertEqual(VER.compare("1.2.0", "1.2.0rc9"), 1)

    def test_rc_status_is_not_unknown(self):
        # A tagged rc install must report a real status, not "unknown".
        self.assertEqual(VER.status("1.2.0rc1", "1.2.0rc1"), "current")

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


class BakedVersionGuardTests(unittest.TestCase):
    """Guard against the stale/dirty baked VERSION bug (the installer copies this file
    verbatim into every target, so it must be a clean release version, never a .dev/local
    string and never lagging the tag)."""

    import re as _re

    _RELEASE_RE = _re.compile(r"^\d+\.\d+\.\d+(rc\d+)?$")

    def _repo_root(self) -> Path:
        # tests/ -> repo root
        return Path(__file__).resolve().parent.parent

    def test_baked_version_is_a_clean_release_string(self):
        # The tracked .agents/workflows/VERSION must be a plain release (X.Y.Z or X.Y.Zrc N),
        # NOT a .devN / +local string. A dev/local value here means it was baked from a
        # dirty/ahead tree and would stamp a dev version into every install.
        vpath = self._repo_root() / ".agents" / "workflows" / "VERSION"
        baked = vpath.read_text(encoding="utf-8").strip()
        self.assertRegex(
            baked,
            self._RELEASE_RE,
            f"baked VERSION {baked!r} is not a clean release version "
            "(no .dev/+local allowed; re-bake with `make version-file VERSION=<x.y.z>`)",
        )

    def test_baked_version_matches_tag_when_head_is_a_release_tag(self):
        # When HEAD is exactly an annotated release tag, the baked VERSION must equal it
        # (bake-then-tag). If HEAD is not a clean tag, this check is skipped (dev/ahead trees
        # legitimately carry the intended next release in the baked file).
        import subprocess

        root = self._repo_root()
        proc = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            self.skipTest("HEAD is not exactly a release tag; baked-vs-tag check N/A")
        tag = proc.stdout.strip().lstrip("v")
        baked = (
            (root / ".agents" / "workflows" / "VERSION")
            .read_text(encoding="utf-8")
            .strip()
        )
        self.assertEqual(
            baked,
            VER._normalize_tag("v" + tag),
            "baked VERSION must equal the release tag it is committed under (bake-then-tag)",
        )


class NonReleaseTagGuardTests(unittest.TestCase):
    """Only semver release tags drive the version; non-release tags degrade safely (D44 fix)."""

    def test_recreated_tag_degrades_not_bumped(self):
        # A non-semver tag (v1.2.0-recreated, the history-rewrite marker) must NOT be bumped
        # into an invalid `1.3.0-recreated.dev...`; it degrades to the no-tag 0.0.0+g<sha>.
        self.assertEqual(
            VER.parse_describe("v1.2.0-recreated-3-gabc1234", date=DATE),
            "0.0.0+gabc1234",
        )

    def test_recreated_tag_dirty_degrades(self):
        self.assertEqual(
            VER.parse_describe("v1.2.0-recreated-3-gabc1234-dirty", date=DATE),
            "0.0.0+gabc1234.d" + DATE,
        )

    def test_release_tags_still_resolve(self):
        # Normal, rc, and multi-digit-patch release tags are unaffected by the guard.
        self.assertEqual(
            VER.parse_describe("v1.1.0-2-g49f2bdc", date=DATE), "1.1.1.dev2+g49f2bdc"
        )
        self.assertEqual(
            VER.parse_describe("v1.2.0-rc.1-4-gbdc3fdc", date=DATE),
            "1.2.0rc2.dev4+gbdc3fdc",
        )
        self.assertEqual(
            VER.parse_describe("v1.10.20-2-gabc1234", date=DATE),
            "1.10.21.dev2+gabc1234",
        )

    def test_is_release_tag_predicate(self):
        for good in ("1.0.0", "1.10.20", "1.2.0rc1", "2.3"):
            self.assertTrue(VER._is_release_tag(good), good)
        for bad in ("1.2.0-recreated", "nightly", "backup", "1.2.0-rc.1"):
            # note: `1.2.0-rc.1` is the RAW (un-normalized) spelling; _normalize_tag turns it
            # into `1.2.0rc1` before this predicate sees it, so the raw hyphenated form is
            # correctly NOT a release core.
            self.assertFalse(VER._is_release_tag(bad), bad)

    def test_git_describe_filters_to_release_tags(self):
        # _git_describe must ask git to match only version tags and exclude recreated markers.
        import unittest.mock as mock

        captured = {}

        def fake_run(argv, **kwargs):
            captured["argv"] = argv

            class R:
                returncode = 0
                stdout = "v1.1.0-230-g2734544\n"

            return R()

        with mock.patch(
            "agent_workflows.versioning.subprocess.run", side_effect=fake_run
        ):
            VER._git_describe(Path("."))
        argv = captured["argv"]
        self.assertIn("--match", argv)
        self.assertIn("v[0-9]*", argv)
        self.assertIn("--exclude", argv)
        self.assertIn("*-recreated", argv)


if __name__ == "__main__":
    unittest.main()
