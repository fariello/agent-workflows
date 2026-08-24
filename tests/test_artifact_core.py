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
        self.assertEqual(target.read_text(encoding="utf-8"), "hello")
        self.assertEqual(list(target.parent.glob(".t-*")), [])


if __name__ == "__main__":
    unittest.main()
