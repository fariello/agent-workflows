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
        # 20260701 -> monthly shard 202607
        self.assertIn("reference/202607", mv.new_path.as_posix())
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

    def test_sweep_set_cohesion_holds_young_set(self):
        # A set with one old member and one brand new member
        _write_doc(
            self.root,
            set_id="mixedset",
            order=0,
            id6="mixold",
            slug="m1",
            status="intake",
            created="20260101",
        )
        recent = date.today().strftime("%Y%m%d")
        _write_doc(
            self.root,
            set_id="mixedset",
            order=1,
            id6="mixnew",
            slug="m2",
            status="intake",
            created=recent,
        )
        # Another set where all members are old
        _write_doc(
            self.root,
            set_id="alloldset",
            order=0,
            id6="allol1",
            slug="a1",
            status="intake",
            created="20260101",
        )
        _write_doc(
            self.root,
            set_id="alloldset",
            order=1,
            id6="allol2",
            slug="a2",
            status="intake",
            created="20260105",
        )

        cands = A.sweep_candidates(self.root, self.rroot)
        # mixedset has a new member, so NEITHER member is swept (set cohesion)
        self.assertNotIn("mixold", cands)
        self.assertNotIn("mixnew", cands)
        # alloldset has only old members, so BOTH members are swept together
        self.assertIn("allol1", cands)
        self.assertIn("allol2", cands)

    def test_sweep_custom_age_duration(self):
        import argparse

        # With --age 1y (365d), oldddd (from 20260101, ~235d ago) is excluded
        cands_1y = A.sweep_candidates(self.root, self.rroot, older_than_days=365.0)
        self.assertNotIn("oldddd", cands_1y)

        # With --age 5d, oldddd is included
        cands_5d = A.sweep_candidates(self.root, self.rroot, older_than_days=5.0)
        self.assertIn("oldddd", cands_5d)

        # CLI args with --age
        args = argparse.Namespace(
            target=None, dir=str(self.root), keep=None, age="10w", apply=False
        )
        self.assertEqual(A.run_archive(args), 0)

        # Invalid age
        bad_args = argparse.Namespace(
            target=None, dir=str(self.root), keep=None, age="invalid-age", apply=False
        )
        self.assertEqual(A.run_archive(bad_args), 2)

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


def _write_kind_doc(root, *, set_id, order, id6, slug, status, created, kind):
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
            kind=kind,
        )
    )
    content = C.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=["t"],
        model=None,
        kind=kind,
        status=status,
        outcome="none-yet",
        summary="s",
    )
    p = rroot / name
    p.write_text(content, encoding="utf-8")
    return p


class SuggestTriageTests(unittest.TestCase):
    """IPD m383qb E-03: the human-confirmed triage classifier (promote --suggest)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        # RUN prompt-set whose intake report is cited by an EXECUTED plan -> reference.
        _write_kind_doc(
            self.root,
            set_id="runset",
            order=0,
            id6="prmpt2",
            slug="ask",
            status="reference",
            created="20260802",
            kind="research-prompt",
        )
        _write_kind_doc(
            self.root,
            set_id="runset",
            order=1,
            id6="rprt01",
            slug="answer",
            status="intake",
            created="20260803",
            kind="research-report",
        )
        # A stale, UNCITED, non-run-prompt intake doc must NOT be classified (genuinely untriaged).
        _write_kind_doc(
            self.root,
            set_id="lonenote",
            order=0,
            id6="lone01",
            slug="n",
            status="intake",
            created="20260804",
            kind="notes",
        )
        # An executed plan citing the run-set report -> makes rprt01 cited (=> reference).
        pl = self.root / ".aw" / "records" / "plans" / "executed"
        pl.mkdir(parents=True, exist_ok=True)
        (pl / "20260805-set-01-plnexe-x.ipd.md").write_text(
            "# Plan\n\n- Id: plnexe\n\nAdopts research RSCH-rprt01.\n", encoding="utf-8"
        )

    def test_suggest_classifies_and_previews_without_mutation(self):
        moves = A.suggest_triage(self.root, self.rroot)
        by_id = {m.id6: m.new_status for m in moves}
        # rprt01 is in a RUN set AND cited by an executed plan -> reference.
        self.assertEqual(by_id.get("rprt01"), "reference")
        # lone01 is uncited and not part of a run prompt-set -> not classified at all.
        self.assertNotIn("lone01", by_id)
        # No files moved during a suggest (preview computes Moves only).
        self.assertTrue(
            (
                self.rroot / "20260803-runset-01-rprt01-answer.research-report.md"
            ).exists()
        )

    def test_suggest_apply_promotes_as_previewed(self):
        import argparse

        args = argparse.Namespace(
            id=None, to="reference", suggest=True, dir=str(self.root), apply=True
        )
        rc = A.run_promote(args)
        self.assertEqual(rc, 0)
        moved = list((self.rroot / R.REFERENCE_DIR).rglob("*rprt01*.md"))
        self.assertEqual(len(moved), 1)
        fm = R.parse_frontmatter(moved[0].read_text(encoding="utf-8"))
        self.assertEqual(fm["status"], "reference")

    def test_suggest_archives_uncited_run_set_deadend(self):
        # A RUN prompt-set report that is NOT cited anywhere -> archive (dead end).
        _write_kind_doc(
            self.root,
            set_id="deadset",
            order=0,
            id6="dprmpt",
            slug="ask",
            status="reference",
            created="20260701",
            kind="research-prompt",
        )
        _write_kind_doc(
            self.root,
            set_id="deadset",
            order=1,
            id6="drpt01",
            slug="answer",
            status="intake",
            created="20260701",
            kind="research-report",
        )
        moves = A.suggest_triage(self.root, self.rroot)
        by_id = {m.id6: m.new_status for m in moves}
        self.assertEqual(by_id.get("drpt01"), "archive")


class ShardDateTests(unittest.TestCase):
    def test_shard_for_date(self):
        self.assertEqual(R.shard_for_date("20260701"), "202607")


class IntakeToTodoMigrationTests(unittest.TestCase):
    """rstodo lpqy64: migrating a legacy `intake` doc to `todo` through the contract tool
    (`aw research promote --to todo`) flips ONLY the status line, preserves the rest, keeps the
    doc at the hot root (no shard move), and leaves it validating + INDEX regenerated."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.rroot = self.root / R.RESEARCH_ROOT
        # a legacy `intake` doc on disk (the pre-migration corpus shape)
        self.doc = _write_doc(
            self.root,
            set_id="mig",
            order=0,
            id6="migx01",
            slug="m",
            status="intake",
            created="20260701",
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def test_promote_intake_to_todo_flips_only_status_in_place(self):
        before = self.doc.read_text(encoding="utf-8")
        mv, err = A.plan_transition(self.rroot, "migx01", "todo")
        self.assertIsNone(
            err, f"promote --to todo must be accepted post child-01: {err}"
        )
        # hot->hot: same path (no shard move)
        self.assertEqual(mv.old_path.resolve(), mv.new_path.resolve())
        A.apply_moves(self.root, self.rroot, [mv])
        after = self.doc.read_text(encoding="utf-8")
        # ONLY the status line changed: intake -> todo; every other line identical.
        b_lines = before.splitlines()
        a_lines = after.splitlines()
        self.assertEqual(len(b_lines), len(a_lines))
        diffs = [(b, a) for b, a in zip(b_lines, a_lines) if b != a]
        self.assertEqual(diffs, [("status: intake", "status: todo")])
        # the migrated doc still validates through the contract.
        fm = R.parse_frontmatter(after)
        self.assertEqual(fm["status"], "todo")
        self.assertFalse(any(e.field == "status" for e in R.validate_frontmatter(fm)))

    def test_legacy_intake_still_accepted_during_window(self):
        # backward-compat: a not-yet-migrated `intake` doc is still accepted (normalizes to todo).
        self.assertEqual(R.normalize_status("intake").value, "todo")
        errs = R.validate_frontmatter(
            R.parse_frontmatter(self.doc.read_text(encoding="utf-8"))
        )
        self.assertFalse(any(e.field == "status" for e in errs))


if __name__ == "__main__":
    unittest.main()
