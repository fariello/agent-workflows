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
    """Every real ``git describe --long`` shape -> the exact PEP 440 string it must produce.

    ONE table, not fifteen one-line tests. The subject is a pure function from a describe string to
    a version string, so the only thing that differed between the old tests was the row. Tabulating
    it makes the mapping readable as a mapping AND reports every wrong row in one run: a change to
    the bump logic typically breaks a whole class of shapes at once (all rc rows, all dirty rows),
    and seeing which rows moved together is what identifies the cause.

    Non-release tags are in the SAME table as release tags on purpose. The D44 fix makes a
    non-semver tag degrade to the no-tag form rather than bump into an invalid version, so a
    regression would show up as a degrade row producing a bumped value, which is only visible if
    both kinds are asserted against the same function in the same place.
    """

    #: (describe string, expected version, why this row exists)
    CASES = (
        ("v1.0.0-0-gd644d2d", "1.0.0", "exact clean tag is the release itself"),
        (
            "v1.0.0-0-gd644d2d-dirty",
            "1.0.1.dev0+gd644d2d.d20260706",
            "a release commit with local edits is NOT that release; it is dev of the next patch",
        ),
        ("v1.0.0-2-g49f2bdc", "1.0.1.dev2+g49f2bdc", "ahead of a tag bumps the patch"),
        (
            "v1.0.0-2-g49f2bdc-dirty",
            "1.0.1.dev2+g49f2bdc.d20260706",
            "ahead and dirty carries both the dev count and the date",
        ),
        ("d644d2d", "0.0.0+gd644d2d", "no tags at all degrades to 0.0.0 plus the sha"),
        (
            "9042038-dirty",
            "0.0.0+g9042038.d20260706",
            "the real dirty-no-tags form appends -dirty to a bare sha (V-7)",
        ),
        (
            "v2.3.4-1-gabc1234",
            "2.3.5.dev1+gabc1234",
            "a non-zero minor bumps ONLY the patch",
        ),
        (
            "v1.2.0-rc.1-0-g49f2bdc",
            "1.2.0rc1",
            "a clean rc normalizes to PEP 440 (X.Y.ZrcN) so pip treats it as a pre-release",
        ),
        (
            "v1.2.0-rc.1-3-g49f2bdc",
            "1.2.0rc2.dev3+g49f2bdc",
            "ahead of an rc is a dev of the NEXT candidate, so it sorts after rc1",
        ),
        (
            "v1.2.0-rc.1-3-g49f2bdc-dirty",
            "1.2.0rc2.dev3+g49f2bdc.d20260706",
            "ahead of an rc and dirty",
        ),
        (
            "v1.2.0rc1-0-g49f2bdc",
            "1.2.0rc1",
            "a tag ALREADY in PEP 440 spelling is handled, not double-normalized",
        ),
        (
            "v1.2.0-recreated-3-gabc1234",
            "0.0.0+gabc1234",
            "D44: a non-semver tag must DEGRADE, never bump into an invalid 1.3.0-recreated.devN",
        ),
        (
            "v1.2.0-recreated-3-gabc1234-dirty",
            "0.0.0+gabc1234.d20260706",
            "D44 degrade path, dirty",
        ),
        (
            "v1.1.0-2-g49f2bdc",
            "1.1.1.dev2+g49f2bdc",
            "the D44 guard did not break normal tags",
        ),
        (
            "v1.10.20-2-gabc1234",
            "1.10.21.dev2+gabc1234",
            "multi-digit patch still bumps correctly",
        ),
    )

    def test_every_describe_shape_maps_to_its_pep440_version(self):
        wrong = []
        for describe, expected, why in self.CASES:
            got = VER.parse_describe(describe, date=DATE)
            if got != expected:
                wrong.append(
                    f"  {describe!r}\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"versioning.parse_describe produced the wrong version for {len(wrong)} of "
            f"{len(self.CASES)} describe shapes:\n" + "\n".join(wrong),
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

    #: (left, right, expected sign, why)
    ORDERING = (
        ("1.0.1.dev2", "1.0.1", -1, "a dev build sorts BEFORE its target release"),
        ("1.0.1", "1.0.1.dev2", 1, "and the comparison is antisymmetric"),
        ("1.0.1", "1.1.0", -1, "minor outranks patch"),
        ("1.1.0", "1.0.1", 1, "antisymmetric again"),
        ("1.0.0", "1.0.0", 0, "equal versions compare equal"),
        (
            "1.0.1.dev2+gaaaa",
            "1.0.1.dev2+gbbbb.d20260706",
            0,
            "the LOCAL segment is ignored for ordering, so two builds of one base tie",
        ),
        ("1.0.1.dev1", "1.0.1.dev2", -1, "dev numbers order numerically"),
        ("1.2.0rc1", "1.2.0rc2", -1, "rc numbers order"),
        ("1.2.0rc2", "1.2.0", -1, "an rc sorts before the final release"),
        ("1.2.0rc2.dev3", "1.2.0rc2", -1, "a dev of an rc sorts before that rc"),
        ("1.2.0", "1.2.0rc9", 1, "the final release outranks every rc"),
    )

    def test_the_ordering_is_total_and_antisymmetric_over_our_shapes(self):
        wrong = []
        for left, right, expected, why in self.ORDERING:
            got = VER.compare(left, right)
            if got != expected:
                wrong.append(
                    f"  compare({left!r}, {right!r}) expected {expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"versioning.compare ordered {len(wrong)} of {len(self.ORDERING)} pairs wrongly. "
            "Ordering decides upgrade prompts, so an inversion here is user-visible.\n"
            + "\n".join(wrong),
        )

    def test_an_rc_version_is_parseable_at_all(self):
        """Precondition of the rc rows above: if this returns None they tie vacuously."""
        self.assertIsNotNone(
            VER.parse_our_version("1.2.0rc1"),
            "an rc version emitted by parse_describe must be parseable by the comparator, "
            "otherwise every rc ordering row above compares two unparsed values",
        )

    def test_compare_rejects_a_legacy_version(self):
        """A pre-migration YYYYMMDD-NN version must RAISE, not silently sort somewhere."""
        with self.assertRaises(ValueError):
            VER.compare("20260704-06", "1.0.0")


class StatusTests(unittest.TestCase):
    """status(target, packaged) -> state. A pure mapping, so it is asserted as a table (V-5)."""

    #: (target, packaged, expected state, why)
    CASES = (
        (None, "1.0.0", "not-installed", "no target at all"),
        ("", "1.0.0", "not-installed", "empty string is not a version"),
        ("unknown", "1.0.0", "not-installed", "the literal 'unknown' target"),
        ("1.0.0", "1.0.1", "stale", "target behind the packaged version"),
        ("1.0.1", "1.0.1", "current", "equal versions"),
        ("1.1.0", "1.0.1", "ahead", "target ahead of the packaged version"),
        (
            "1.0.1.dev2+gabc1234",
            "1.0.0",
            "dev",
            "a .devN target is a dev build regardless of how it compares",
        ),
        (
            "1.0.0+gabc1234.d20260706",
            "1.0.0",
            "dev",
            "a +local target is a dirty build regardless of how it compares",
        ),
        (
            "20260704-06",
            "1.0.0",
            "unknown",
            "a pre-migration YYYYMMDD-NN install cannot be classified, so unknown NOT stale",
        ),
        ("0.0.0+gd644d2d", "1.0.0", "unknown", "the pre-baseline no-tag version"),
        (
            "1.2.0rc1",
            "1.2.0rc1",
            "current",
            "a tagged rc must report a real status, not unknown",
        ),
    )

    def test_every_target_and_packaged_pair_maps_to_its_state(self):
        wrong = []
        for target, packaged, expected, why in self.CASES:
            got = VER.status(target, packaged)
            if got != expected:
                wrong.append(
                    f"  status({target!r}, {packaged!r}) expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"versioning.status misclassified {len(wrong)} of {len(self.CASES)} cases. A wrong "
            "state here is user-visible: it decides whether `aw` tells someone to upgrade.\n"
            + "\n".join(wrong),
        )


class BakedVersionGuardTests(unittest.TestCase):
    """Guard against the stale/dirty baked VERSION bug (the installer copies this file
    verbatim into every target, so it must be a clean release version, never a .dev/local
    string and never lagging the tag)."""

    import re as _re

    _RELEASE_RE = _re.compile(r"^\d+\.\d+\.\d+(rc\d+)?$")

    def _repo_root(self) -> Path:
        # tests/ -> repo root
        return Path(__file__).resolve().parent.parent

    def _baked_version_path(self) -> Path:
        # Canonical source VERSION is the .aw/system/ sibling after the physical-layout
        # migration; fall back to the legacy .agents/workflows/VERSION for a pre-migration tree.
        root = self._repo_root()
        aw = root / ".aw" / "system" / "VERSION"
        return aw if aw.is_file() else root / ".agents" / "workflows" / "VERSION"

    def test_baked_version_is_a_clean_release_string(self):
        # The tracked source VERSION must be a plain release (X.Y.Z or X.Y.Zrc N),
        # NOT a .devN / +local string. A dev/local value here means it was baked from a
        # dirty/ahead tree and would stamp a dev version into every install.
        vpath = self._baked_version_path()
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
        baked = self._baked_version_path().read_text(encoding="utf-8").strip()
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
