"""Tests for the shared area-agnostic artifact core (Set plans-adopter, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the extracted primitives (id6, shard math,
kebab, scan-root iteration, the area-parameterized dangling detector, and the drift/--check shape)
behave as the research modules relied on before extraction.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as C


class Id6Tests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(C.is_valid_id6("k7m2xq"))
        self.assertTrue(C.is_valid_id6("000000"))

    def test_reject(self):
        self.assertFalse(C.is_valid_id6("k7m2x"))  # 5
        self.assertFalse(C.is_valid_id6("k7m2xqq"))  # 7
        self.assertFalse(C.is_valid_id6("K7M2XQ"))  # uppercase

    def test_word_scan(self):
        self.assertEqual(C.iter_id6_in_text("see k7m2xq here"), ["k7m2xq"])

    def test_generate_avoids_existing(self):
        seq = iter(["a", "a", "a", "a", "a", "a", "b", "c", "d", "e", "f", "g"])
        got = C.generate_id6({"aaaaaa"}, _rng=lambda alphabet: next(seq))
        self.assertNotIn(got, {"aaaaaa"})
        self.assertTrue(C.is_valid_id6(got))


class KebabTests(unittest.TestCase):
    def test_kebab(self):
        self.assertEqual(C.kebab("AW Delivery & X"), "aw-delivery-x")
        self.assertEqual(C.kebab("  a  b  "), "a-b")


class ShardTests(unittest.TestCase):
    def test_shard_for_date(self):
        self.assertEqual(C.shard_for_date("20260701"), "202607")

    def test_shard_dirname_and_valid(self):
        self.assertEqual(C.shard_dirname("202607"), "202607")
        self.assertTrue(C.is_valid_shard_dirname("202607"))
        self.assertTrue(
            C.is_valid_shard_dirname("202607-W30")
        )  # legacy weekly tolerance
        self.assertFalse(C.is_valid_shard_dirname("2026-07"))
        self.assertFalse(C.is_valid_shard_dirname("2026"))


class ScanRootTests(unittest.TestCase):
    def test_scan_roots_include_plans_and_docs(self):
        self.assertIn(".agents/plans", C.SCAN_ROOTS)
        self.assertIn(".agents/docs", C.SCAN_ROOTS)
        self.assertIn("DECISIONS.md", C.SCAN_ROOTS)

    def test_scan_roots_include_both_releases_generations(self):
        """durablecapture-02 (`m867ox`) E-01: the tracked `releases` tree must be SCANNED.

        `.aw/records/releases` is the LOAD-BEARING entry, because `releases._releases_dir` writes and
        reads there; `.agents/releases` is the `TreePolicy` root spelling, carried for symmetry with
        the plans/backlog pairs and for pre-migration repositories. Membership, not length, following
        this module's existing pattern: the cross-list guard that makes a future tracked tree fail
        closed lives in `tests/test_attention_contract.py::TrackedTreeScanCoverageTests`.
        """

        self.assertIn(".aw/records/releases", C.SCAN_ROOTS)
        self.assertIn(".agents/releases", C.SCAN_ROOTS)

    def test_iter_scan_files_reaches_a_release_record_and_drops_the_readme(self):
        """The root must actually YIELD the record: a root that `iter_scan_files` skips for an
        unrelated reason (an ignore rule, a suffix filter) would look like a fix and change nothing.
        """

        root = Path(tempfile.mkdtemp())
        rel_dir = root / ".aw/records/releases"
        rel_dir.mkdir(parents=True)
        (rel_dir / "20260101-rel-01-rel001-r.release.md").write_text(
            "- Status: planned\n", encoding="utf-8"
        )
        (rel_dir / "README.md").write_text("x\n", encoding="utf-8")
        got = {f.name for f in C.iter_scan_files(root)}
        self.assertIn("20260101-rel-01-rel001-r.release.md", got)
        # The README is scanned here but is filtered out of the VIEW by
        # `attention_contract.is_nonartifact_name`, not by the scan root.
        self.assertIn("README.md", got)

    def test_iter_scan_files_bounded(self):
        root = Path(tempfile.mkdtemp())
        (root / "DECISIONS.md").write_text("x", encoding="utf-8")
        (root / ".agents" / "docs").mkdir(parents=True)
        (root / ".agents" / "docs" / "a.md").write_text("x", encoding="utf-8")
        (root / "stray").mkdir()
        (root / "stray" / "b.md").write_text("x", encoding="utf-8")
        names = {f.name for f in C.iter_scan_files(root)}
        self.assertIn("DECISIONS.md", names)
        self.assertIn("a.md", names)
        self.assertNotIn("b.md", names)


class DanglingTests(unittest.TestCase):
    """The area-parameterized detector: caller supplies current_ids + a cite_matcher."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def _matcher(self, line):
        # A minimal citation matcher: only tokens of the form CITE-<id6>.
        import re

        return re.findall(r"\bCITE-([0-9a-z]{6})\b", line)

    def test_stale_cite_flagged(self):
        (self.root / "DECISIONS.md").write_text(
            "gone CITE-zqzqzq here\n", encoding="utf-8"
        )
        d = C.find_dangling_citations(
            self.root, current_ids={"aaaaaa"}, cite_matcher=self._matcher
        )
        self.assertTrue(any(x.id6 == "zqzqzq" for x in d))

    def test_present_cite_not_flagged(self):
        (self.root / "DECISIONS.md").write_text(
            "ok CITE-aaaaaa here\n", encoding="utf-8"
        )
        d = C.find_dangling_citations(
            self.root, current_ids={"aaaaaa"}, cite_matcher=self._matcher
        )
        self.assertEqual(d, [])

    def test_bare_word_not_a_citation(self):
        (self.root / "DECISIONS.md").write_text(
            "design prompt naming here\n", encoding="utf-8"
        )
        d = C.find_dangling_citations(
            self.root, current_ids=set(), cite_matcher=self._matcher
        )
        self.assertEqual(d, [])

    def test_exclude_root_skips_own_tree(self):
        area = self.root / ".agents" / "docs" / "area"
        area.mkdir(parents=True)
        (area / "self.md").write_text("CITE-zqzqzq\n", encoding="utf-8")
        d = C.find_dangling_citations(
            self.root, current_ids=set(), cite_matcher=self._matcher, exclude_root=area
        )
        self.assertEqual(d, [])


class DriftShapeTests(unittest.TestCase):
    def test_agent_render_and_exit(self):
        drift = [C.Drift("f.md:1", "some-rule", "detail")]
        rendered = C.render_agent_drift(drift)
        self.assertIn("\t", rendered)
        self.assertIn("some-rule", rendered)
        self.assertEqual(C.drift_exit_code(drift), 1)
        self.assertEqual(C.drift_exit_code([]), 0)


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_write_no_leftover(self):
        root = Path(tempfile.mkdtemp())
        target = root / "sub" / "f.md"
        C.atomic_write(target, "hello", prefix=".t-")
        # A MARKDOWN write is now normalized on the way out (per-line trailing whitespace stripped,
        # exactly one final newline), so `"hello"` lands as `"hello\n"`. That is the assertion this
        # test previously pinned the other way, changed deliberately by IPD `lqly9m` E-05: the mutating
        # pre-commit hooks would otherwise "fix" every tool-written artifact and REJECT the commit,
        # costing a full round trip for a stripped trailing space. The no-leftover property, which is
        # what this test is actually about, is unchanged.
        self.assertEqual(target.read_text(encoding="utf-8"), "hello\n")
        self.assertEqual(list(target.parent.glob(".t-*")), [])

    def test_markdown_is_normalized_but_json_and_research_are_byte_for_byte(self):
        """The normalization's SCOPE, which is the part that can silently corrupt if it is wrong.

        `atomic_write` is NOT markdown-only: the leak-sanitizer allowlist and OpenCode's
        `opencode.json` are written through this shape too, and the research trees are deliberately
        excluded from every content-mutating pre-commit hook because their delivered formatting is
        intentional. So both must pass through untouched.
        """
        root = Path(tempfile.mkdtemp())

        md = root / "art.md"
        C.atomic_write(md, "title   \n\nbody with trailing   \n\n\n")
        self.assertEqual(
            md.read_text(encoding="utf-8"), "title\n\nbody with trailing\n"
        )

        payload = '{\n  "model": "x"\n}   \n\n'
        cfg = root / "opencode.json"
        C.atomic_write(cfg, payload)
        self.assertEqual(cfg.read_text(encoding="utf-8"), payload)

        verbatim = "delivered heading   \nhard break  \nbody\n\n\n"
        for rel in (
            (".aw", "records", "research", "r.md"),
            (".aw", "records", "docs", "research", "r.md"),
            (".agents", "docs", "research", "r.md"),
        ):
            target = root.joinpath(*rel)
            C.atomic_write(target, verbatim)
            self.assertEqual(target.read_text(encoding="utf-8"), verbatim, rel)

    def test_normalizer_is_idempotent_and_keeps_an_empty_write_empty(self):
        self.assertEqual(C.normalize_artifact_markdown("a  \nb\t\n\n\n"), "a\nb\n")
        once = C.normalize_artifact_markdown("a  \nb\t\n\n\n")
        self.assertEqual(C.normalize_artifact_markdown(once), once)
        # An all-whitespace body stays EMPTY rather than becoming a lone newline, which is what
        # `end-of-file-fixer` itself would do.
        self.assertEqual(C.normalize_artifact_markdown("   \n\n  \n"), "")
        self.assertEqual(C.normalize_artifact_markdown(""), "")


if __name__ == "__main__":
    unittest.main()
