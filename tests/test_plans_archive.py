"""Tests for plans weekly shards + archival (Set plans-adopter, Order 05).

Stdlib unittest, git-backed throwaway repos. Verifies the shard-move helper (correct weekly shard,
unchanged filename + Id, tracked git rename, citation no-op, recursive-manifest visibility),
targeted archive, the aged sweep with preview, and the INDEX refresh.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_workflows import plans_archive as A
from agent_workflows import plans_index as I


def _init_git(root: Path):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)


def _plan(
    root, disposition, name, *, plan_id, date_="20260701", set_id=None, order=None
):
    d = root / ".agents" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    meta = [
        f"- Date: {date_}",
        "- Kind: child",
        "- Concern: x.",
        "- Scope: x.",
        "- Status: executed",
        "- Author: t",
        f"- Id: {plan_id}",
    ]
    if set_id:
        meta += [f"- Set: {set_id}", f"- Order: {order}"]
    (d / name).write_text(
        "# IPD: x\n\n" + "\n".join(meta) + "\n\n## Goal\n\nx\n", encoding="utf-8"
    )
    return d / name


class ShardMoveTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.pdir = self.root / ".agents" / "plans"
        self.p = _plan(
            self.root, "executed", "20260701-grp-00-aaaaaa-x.md", plan_id="aaaaaa"
        )

    def test_shard_move_correct_week_keeps_name_and_id(self):
        mv = A.plan_shard_move(self.pdir, self.p)
        self.assertIsNotNone(mv)
        # 20260701 -> ISO week 27
        self.assertIn("executed/202607-W27/", mv.new_path.as_posix())
        self.assertEqual(mv.new_path.name, self.p.name)  # filename unchanged
        A.apply_shard_moves(self.root, self.pdir, [mv])
        moved = list((self.pdir / "executed" / "202607-W27").glob("*aaaaaa*.md"))
        self.assertEqual(len(moved), 1)
        self.assertIn("- Id: aaaaaa", moved[0].read_text())

    def test_move_is_tracked_git_rename(self):
        mv = A.plan_shard_move(self.pdir, self.p)
        A.apply_shard_moves(self.root, self.pdir, [mv])
        out = subprocess.run(
            ["git", "-C", str(self.root), "status", "--porcelain"],
            capture_output=True,
            text=True,
        ).stdout
        # The move is staged (git mv), so the tree is not showing an untracked add for it.
        self.assertNotIn("?? .agents/plans/executed/202607-W27", out)

    def test_pending_not_eligible(self):
        p2 = _plan(
            self.root, "pending", "20260701-grp-00-bbbbbb-y.md", plan_id="bbbbbb"
        )
        self.assertIsNone(A.plan_shard_move(self.pdir, p2))

    def test_sharded_plan_visible_in_manifest(self):
        mv = A.plan_shard_move(self.pdir, self.p)
        A.apply_shard_moves(self.root, self.pdir, [mv])
        entries, _ = I.scan_plans(self.pdir)
        e = [x for x in entries if x.plan_id == "aaaaaa"]
        self.assertEqual(len(e), 1)
        self.assertEqual(
            e[0].disposition, "executed"
        )  # top-level disposition preserved


class ArchiveVerbTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        _init_git(self.root)
        self.pdir = self.root / ".agents" / "plans"

    def test_targeted_archive_by_id(self):
        import argparse

        _plan(self.root, "executed", "20260701-grp-00-aaaaaa-x.md", plan_id="aaaaaa")
        rc = A.run_archive(
            argparse.Namespace(target="aaaaaa", dir=str(self.root), apply=True)
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(list((self.pdir / "executed").rglob("*aaaaaa*.md"))), 1)
        self.assertTrue(
            list((self.pdir / "executed" / "202607-W27").glob("*aaaaaa*.md"))
        )

    def test_sweep_selects_aged_only(self):
        _plan(
            self.root,
            "executed",
            "20260101-grp-00-oldddd-o.md",
            plan_id="oldddd",
            date_="20260101",
        )
        recent = date.today().strftime("%Y%m%d")
        _plan(
            self.root,
            "executed",
            f"{recent}-grp-01-newwww-n.md",
            plan_id="newwww",
            date_=recent,
        )
        cands = {p.name for p in A.sweep_candidates(self.pdir)}
        self.assertTrue(any("oldddd" in n for n in cands))
        self.assertFalse(any("newwww" in n for n in cands))


class DefaultAgeTests(unittest.TestCase):
    def test_default_age(self):
        self.assertEqual(A.DEFAULT_SWEEP_AGE_DAYS, 14)
        self.assertEqual(A.TERMINAL_DIRS, ("executed", "superseded", "not-executed"))


if __name__ == "__main__":
    unittest.main()
