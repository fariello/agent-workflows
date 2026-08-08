"""Tests for the research index generator + find + --check (Set research-org, Order 03).

Stdlib unittest, throwaway dirs. Verifies JSON completeness, INDEX.md bounding (archive excluded,
reference included, intake shown, N honored), determinism (regenerate twice byte-identical), find
filters, and --check across the spec-5.2 four drift classes including dangling citations (via the
Order 04 detector).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import research_contract as R
from agent_workflows import research_cmd as C
from agent_workflows import research_index as I


def _write(
    root: Path, *, set_id, order, id6, slug, status, created, kind="notes", model=None
):
    rroot = root / R.RESEARCH_ROOT
    rroot.mkdir(parents=True, exist_ok=True)
    name = R.format_name(
        R.ResearchName(
            date=created,
            set_id=set_id,
            order=f"{order:02d}",
            id6=id6,
            slug=slug,
            model=model,
            kind=kind,
        )
    )
    content = C.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=["t1"],
        model=model,
        kind=kind,
        status=status,
        outcome="none-yet",
        summary=f"summary {id6}",
    )
    (rroot / name).write_text(content, encoding="utf-8")
    return rroot / name


class IndexBuildTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )
        _write(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="reference",
            created="20260705",
        )
        _write(
            self.root,
            set_id="gamma",
            order=0,
            id6="cccccc",
            slug="c",
            status="archive",
            created="20260710",
        )

    def test_json_contains_every_doc(self):
        entries, drift = I._scan_docs(self.rroot)
        self.assertEqual(drift, [])
        ids = {e.id6 for e in entries}
        self.assertEqual(ids, {"aaaaaa", "bbbbbb", "cccccc"})

    def test_index_md_archive_excluded_reference_included_intake_shown(self):
        entries, _ = I._scan_docs(self.rroot)
        md = I.build_index_md(entries)
        self.assertIn("aaaaaa", md)  # intake shown
        self.assertIn("bbbbbb", md)  # reference included
        self.assertNotIn("cccccc", md)  # archive excluded
        self.assertIn("Needs addressing (intake)", md)

    def test_n_honored(self):
        # Add more hot docs and bound to 2.
        for i in range(5):
            _write(
                self.root,
                set_id=f"s{i}",
                order=0,
                id6=f"d{i}{i}{i}{i}{i}",
                slug="x",
                status="active",
                created="2026080%d" % (i + 1),
            )
        entries, _ = I._scan_docs(self.rroot)
        md = I.build_index_md(entries, limit=2)
        # "Most recent" section should list only 2 bullets.
        recent_block = md.split("## Most recent")[1]
        bullets = [ln for ln in recent_block.splitlines() if ln.startswith("- `")]
        self.assertEqual(len(bullets), 2)

    def test_determinism(self):
        entries, _ = I._scan_docs(self.rroot)
        a = I.build_index_json(entries) + I.build_index_md(entries)
        entries2, _ = I._scan_docs(self.rroot)
        b = I.build_index_json(entries2) + I.build_index_md(entries2)
        self.assertEqual(a, b)


class FindTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )
        _write(
            self.root,
            set_id="alpha",
            order=1,
            id6="aaaaab",
            slug="a2",
            status="active",
            created="20260702",
        )
        _write(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="reference",
            created="20260705",
        )

    def test_find_by_set(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, set_id="alpha")
        self.assertEqual({e.id6 for e in res}, {"aaaaaa", "aaaaab"})

    def test_find_by_status(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, status="reference")
        self.assertEqual([e.id6 for e in res], ["bbbbbb"])

    def test_find_by_id(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, id6="aaaaab")
        self.assertEqual([e.id6 for e in res], ["aaaaab"])


class CheckDriftTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="reference",
            created="20260701",
        )

    def _regen(self):
        entries, _ = I._scan_docs(self.rroot)
        (self.rroot / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.rroot / I.INDEX_MD).write_text(
            I.build_index_md(entries), encoding="utf-8"
        )

    def test_clean_after_regen(self):
        self._regen()
        drift = I.check_drift(self.root, self.rroot)
        self.assertEqual(drift, [])

    def test_stale_index_detected(self):
        self._regen()
        (self.rroot / I.INDEX_MD).write_text("stale", encoding="utf-8")
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "stale-index" for d in drift))

    def test_invalid_frontmatter_detected(self):
        # A file with frontmatter missing 'id'.
        bad = self.rroot / "20260701-alpha-01-zzzzzz-bad.notes.md"
        bad.write_text(
            "---\ncreated: 20260701\nkind: notes\nstatus: intake\n---\n",
            encoding="utf-8",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "frontmatter-invalid" for d in drift))

    def test_dangling_citation_detected(self):
        self._regen()
        (self.root / "DECISIONS.md").write_text(
            "cite 20260601-old-00-qppqpp-gone.notes.md\n", encoding="utf-8"
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "dangling-citation" for d in drift))


class DefaultLimitTests(unittest.TestCase):
    def test_default_is_40(self):
        self.assertEqual(I.DEFAULT_INDEX_LIMIT, 40)


if __name__ == "__main__":
    unittest.main()
