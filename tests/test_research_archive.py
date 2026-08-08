"""Tests for research state lifecycle + archival shards (Set research-org, Order 05).

Stdlib unittest, throwaway git repos (moves use git mv). Verifies promote-to-reference shard move
(id/cites intact, correct weekly shard), targeted archive, the aged-and-uncited sweep with per-item
override + recorded status, the miscategorization flag, and the INDEX refresh (archive out,
reference in).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_workflows import research_archive as A
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R
from agent_workflows import research_index as I


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)


def _write_doc(
    root: Path, *, set_id, order, id6, slug, status, created, consumed_by=None
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
            model=None,
            kind="notes",
        )
    )
    content = C.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=["t"],
        model=None,
        kind="notes",
        status=status,
        outcome="none-yet",
        summary="s",
        consumed_by=consumed_by,
    )
    p = rroot / name
    p.write_text(content, encoding="utf-8")
    return p


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        _write_doc(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )

    def test_promote_to_reference_moves_to_weekly_shard_keeps_id(self):
        mv, err = A.plan_transition(self.rroot, "aaaaaa", "reference")
        self.assertIsNone(err)
        # 20260701 -> ISO week 27 -> shard 202607-W27
        self.assertIn("reference/202607-W", mv.new_path.as_posix())
        A.apply_moves(self.root, self.rroot, [mv])
        # File now lives in the shard, id unchanged, status rewritten.
        moved = list((self.rroot / R.REFERENCE_DIR).rglob("*aaaaaa*.md"))
        self.assertEqual(len(moved), 1)
        fm = R.parse_frontmatter(moved[0].read_text(encoding="utf-8"))
        self.assertEqual(fm["id"], "aaaaaa")
        self.assertEqual(fm["status"], "reference")

    def test_invalid_status_rejected(self):
        mv, err = A.plan_transition(self.rroot, "aaaaaa", "cold")
        self.assertIsNone(mv)
        self.assertIn("status must be", err)


class TargetedArchiveTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        _write_doc(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="active",
            created="20260705",
        )

    def test_targeted_archive_moves_to_archive_shard(self):
        import argparse

        args = argparse.Namespace(
            target="bbbbbb", dir=str(self.root), keep=None, apply=True
        )
        rc = A.run_archive(args)
        self.assertEqual(rc, 0)
        moved = list((self.rroot / R.ARCHIVE_DIR).rglob("*bbbbbb*.md"))
        self.assertEqual(len(moved), 1)
        fm = R.parse_frontmatter(moved[0].read_text(encoding="utf-8"))
        self.assertEqual(fm["status"], "archive")


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        # Aged + uncited (should be a candidate).
        _write_doc(
            self.root,
            set_id="old",
            order=0,
            id6="oldddd",
            slug="o",
            status="intake",
            created="20260101",
        )
        # Recent (not aged) -> excluded.
        recent = date.today().strftime("%Y%m%d")
        _write_doc(
            self.root,
            set_id="new",
            order=0,
            id6="newwww",
            slug="n",
            status="intake",
            created=recent,
        )
        # Aged but CITED -> excluded.
        _write_doc(
            self.root,
            set_id="cited",
            order=0,
            id6="citedd",
            slug="c",
            status="intake",
            created="20260101",
            consumed_by=["D1"],
        )

    def test_sweep_selects_aged_uncited_only(self):
        cands = A.sweep_candidates(self.root, self.rroot)
        self.assertIn("oldddd", cands)
        self.assertNotIn("newwww", cands)
        self.assertNotIn("citedd", cands)

    def test_sweep_per_item_override_records_status(self):
        import argparse

        # Send the aged-uncited candidate to reference via --keep.
        args = argparse.Namespace(
            target=None, dir=str(self.root), keep=["oldddd"], apply=True
        )
        rc = A.run_archive(args)
        self.assertEqual(rc, 0)
        moved = list((self.rroot / R.REFERENCE_DIR).rglob("*oldddd*.md"))
        self.assertEqual(len(moved), 1)
        fm = R.parse_frontmatter(moved[0].read_text(encoding="utf-8"))
        self.assertEqual(fm["status"], "reference")


class MiscategorizedTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT

    def test_archived_but_cited_flagged(self):
        # An archived doc with a non-empty consumed-by.
        rroot = self.rroot / R.ARCHIVE_DIR / "202601-W01"
        rroot.mkdir(parents=True)
        name = R.format_name(
            R.ResearchName(
                date="20260101",
                set_id="x",
                order="00",
                id6="arccit",
                slug="a",
                model=None,
                kind="notes",
            )
        )
        (rroot / name).write_text(
            C.build_frontmatter(
                id6="arccit",
                created="20260101",
                set_id="x",
                order="00",
                topic=[],
                model=None,
                kind="notes",
                status="archive",
                outcome="rejected",
                summary="s",
                consumed_by=["D9"],
            ),
            encoding="utf-8",
        )
        flagged = A.find_miscategorized(self.root, self.rroot)
        self.assertIn("arccit", flagged)


class IndexRefreshTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        _write_doc(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )

    def test_archived_leaves_index_md(self):
        import argparse

        args = argparse.Namespace(
            target="aaaaaa", dir=str(self.root), keep=None, apply=True
        )
        A.run_archive(args)
        md = (self.rroot / I.INDEX_MD).read_text(encoding="utf-8")
        self.assertNotIn("aaaaaa", md)  # archived -> excluded from the hot glance


class ShardDateTests(unittest.TestCase):
    def test_shard_for_date(self):
        self.assertEqual(R.shard_for_date("20260701"), "202607-W27")


if __name__ == "__main__":
    unittest.main()
