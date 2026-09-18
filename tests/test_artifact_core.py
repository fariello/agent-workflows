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


class ScanRootClassificationInvariantTests(unittest.TestCase):
    """durablecapture-03 (`diof9n`) E-06: no scan root may be SCANNED AND SILENTLY DROPPED.

    THE DEFECT THIS CLOSES. `TODO.md` was listed in `SCAN_ROOTS` while
    `attention._classify_tree("TODO.md")` returned `None`, because no `TreePolicy` root covers a
    repository-root file. `attention.scan` appends an `attention.unclassified-tree` violation ONLY
    for a path under `.agents/`, so the file was read and then dropped with NO drift recorded:
    anything written there vanished with no warning. That both-scanned-and-silently-dropped state is
    what this test forbids returning.

    THE EXEMPTION IS A CLOSED, NAMED SET, DELIBERATELY NOT A PREDICATE. `DECISIONS.md`,
    `README.md` and `ARCHITECTURE.md` are in the identical STRUCTURAL state (they also classify to
    `None`), but their PURPOSE differs and purpose is what decides it: they are DOCUMENTATION that
    sits in `SCAN_ROOTS` so the reference tools and the dangling detector scan them for CITATIONS
    (see the comment above `SCAN_ROOTS`), not because anyone records work in them. Being absent from
    the attention view is therefore CORRECT for them. Do NOT "fix" the three by removing them from
    `SCAN_ROOTS`: that would silently break citation scanning and the dangling detector.
    A predicate such as "any root-level file is exempt" is the WRONG encoding, because it would
    silently absorb the next root-level file someone adds with no policy, which is exactly the defect
    above. Naming the three means a FOURTH such file FAILS this test and forces a decision.
    """

    CITATION_ONLY_ROOT_DOCS = frozenset(
        {
            "DECISIONS.md",
            "README.md",
            "ARCHITECTURE.md",
        }
    )

    # A SECOND, SEPARATELY JUSTIFIED closed set. `.agents/docs` is the pre-migration CONTAINER
    # directory, not a leaf tree: it holds the typed `specs/`, `research/`, `walkthroughs/` ...
    # subtrees, and each of THOSE has its own `TreePolicy`, so a real artifact under it DOES
    # classify (asserted below). Only the bare container string classifies to `None`, which is not
    # the `TODO.md` defect (a scanned FILE that swallowed work). Kept distinct from the root docs
    # above so each exemption carries its own reason rather than one vague catch-all.
    LEGACY_CONTAINER_ROOTS = frozenset({".agents/docs"})

    def test_no_scan_root_is_scanned_then_silently_dropped(self):
        from agent_workflows import attention

        exempt = self.CITATION_ONLY_ROOT_DOCS | self.LEGACY_CONTAINER_ROOTS
        offenders = sorted(
            root
            for root in C.SCAN_ROOTS
            if root not in exempt and attention._classify_tree(root) is None
        )
        self.assertEqual(
            offenders,
            [],
            "These SCAN_ROOTS entries are scanned but classify to None, so anything written "
            "there is dropped with no drift violation and vanishes silently: "
            f"{offenders}. Either give the root a `TreePolicy` so a write is reported, or "
            "remove it from SCAN_ROOTS so it is honestly out of scope. If it is documentation "
            "scanned only for CITATIONS, add it to CITATION_ONLY_ROOT_DOCS with a reason.",
        )

    def test_todo_md_is_not_a_scan_root(self):
        """The specific regression: `TODO.md` is deprecated as a work surface, so it must not be
        scanned as one. The controlling spec authorizes this
        (`20260813-1833-01-attention-visible-backlog-tier` G5: `TODO.md` "is then either retired or
        reduced to a pointer at the backlog tree + the Notes section"). The FILE still exists and
        keeps its Tier-3 `## Notes` context; only its scan-root membership is retired.
        """

        self.assertNotIn("TODO.md", C.SCAN_ROOTS)

    def test_the_exemption_is_a_closed_named_set_not_a_predicate(self):
        """Guard the GUARD: every exempted name must really be an exempt-by-design root doc that is
        still present in `SCAN_ROOTS`. A stale exemption would quietly widen the hole.
        """

        for name in self.CITATION_ONLY_ROOT_DOCS | self.LEGACY_CONTAINER_ROOTS:
            self.assertIn(
                name,
                C.SCAN_ROOTS,
                f"{name} is exempted from the no-silently-dropped invariant but is no longer a "
                "scan root; drop it from the exemption set so it stays honest.",
            )

    def test_the_legacy_container_exemption_is_justified_by_its_children(self):
        """`.agents/docs` is exempt ONLY because its typed children classify. Prove that, so the
        exemption cannot survive the day the child policies go away.
        """

        from agent_workflows import attention

        self.assertIsNotNone(attention._classify_tree(".agents/docs/specs/x.spec.md"))
        self.assertIsNotNone(attention._classify_tree(".agents/docs/research/y.md"))


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
