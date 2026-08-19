"""Tests for the attention-visible backlog tier (spec 20260813-1833-01; IPD backlogtier-01/crv40v).

Covers: the _BACKLOG_MAP attention mapping (pure + total, unknown raises); attention inclusion
(open/blocked in the board, parked hidden-from-board-but-in-JSON, blocked gate rendered); the
aw backlog new|set|check verbs (create, status transition + history, blocked-requires-gate,
status-mirrors-directory, fail-closed check, id6 uniqueness); and a mutation probe proving the
_record_for backlog branch is load-bearing (removing it silently drops the item). Stdlib unittest.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import attention as ATT
from agent_workflows import attention_contract as A
from agent_workflows import backlog as B


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _new(repo, **kw):
    base = dict(
        dir=str(repo),
        summary="an item",
        set="s",
        priority="high",
        kind="bug",
        slug="x",
        apply=True,
    )
    base.update(kw)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        rc = B.run_new(_args(**base))
    return rc


class BacklogMappingTests(unittest.TestCase):
    """(a) _BACKLOG_MAP purity/totality + class_of unknown raises."""

    def test_map_covers_every_status(self):
        self.assertEqual(set(A.CLASS_MAPS["backlog"].keys()), set(B.STATUSES))

    def test_class_of_values(self):
        self.assertEqual(A.class_of("backlog", "open"), A.READY)
        self.assertEqual(A.class_of("backlog", "blocked"), A.BLOCKED)
        self.assertEqual(A.class_of("backlog", "parked"), A.PARKED)
        self.assertEqual(A.class_of("backlog", "done"), A.DONE)

    def test_unknown_status_raises(self):
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("backlog", "frobnicated")


class BacklogVerbTests(unittest.TestCase):
    """(c) aw backlog new|set|check."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_creates_conformant_item_that_checks_clean(self):
        self.assertEqual(_new(self.repo), 0)
        items = list((self.repo / ".agents/backlog/open").glob("*.md"))
        self.assertEqual(len(items), 1)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(B.run_check(_args(dir=str(self.repo), agent=False)), 0)

    def test_new_requires_summary(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="",
                    set="s",
                    priority="high",
                    kind="bug",
                    slug="x",
                    apply=True,
                )
            )
        self.assertEqual(rc, 2)

    def test_new_blocked_requires_gate(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="x",
                    set="s",
                    priority="high",
                    kind="bug",
                    slug="x",
                    status="blocked",
                    gate_kind=None,
                    gate_ref=None,
                    apply=True,
                )
            )
        self.assertEqual(rc, 2)

    def test_set_transitions_status_moves_file_and_appends_history(self):
        _new(self.repo)
        f = next((self.repo / ".agents/backlog/open").glob("*.md"))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(f),
                    status="done",
                    message="finished",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        self.assertFalse((self.repo / ".agents/backlog/open" / f.name).exists())
        moved = self.repo / ".agents/backlog/done" / f.name
        self.assertTrue(moved.exists())
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Status: done", text)
        # awhistory Order 02: inline history is SLIMMED to the latest record (the transition); the full
        # log (incl. the created record) now lives in the global .aw/records/history.jsonl sidecar.
        self.assertIn("finished", text)
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(len(inline), 1)

    def test_set_to_blocked_requires_gate(self):
        _new(self.repo)
        f = next((self.repo / ".agents/backlog/open").glob("*.md"))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(f),
                    status="blocked",
                    gate_kind=None,
                    gate_ref=None,
                    message="",
                    apply=True,
                )
            )
        self.assertEqual(rc, 2)

    def test_set_to_blocked_with_gate_records_it(self):
        _new(self.repo)
        f = next((self.repo / ".agents/backlog/open").glob("*.md"))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(f),
                    status="blocked",
                    gate_kind="artifact",
                    gate_ref="path/to/x.md",
                    message="gated",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        moved = self.repo / ".agents/backlog/blocked" / f.name
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Gate-Kind: artifact", text)
        self.assertIn("- Gate-Ref: path/to/x.md", text)

    def test_check_fails_closed_on_status_dir_mismatch(self):
        # a file whose Status disagrees with its directory
        d = self.repo / ".agents/backlog/open"
        d.mkdir(parents=True)
        (d / "20260101-s-01-aaaaaa-bad.md").write_text(
            "- Id: aaaaaa\n- Status: done\n- Set: s\n- Priority: high\n- Kind: bug\n- Summary: mismatched\n",
            encoding="utf-8",
        )
        out = io.StringIO()
        with redirect_stdout(out):
            rc = B.run_check(_args(dir=str(self.repo), agent=False))
        self.assertEqual(rc, 1)
        self.assertIn("status-dir-mismatch", out.getvalue())

    def test_check_fails_closed_on_duplicate_id(self):
        d = self.repo / ".agents/backlog/open"
        d.mkdir(parents=True)
        for name in ("20260101-s-01-dupdup-a.md", "20260101-s-02-dupdup-b.md"):
            (d / name).write_text(
                "- Id: dupdup\n- Status: open\n- Set: s\n- Priority: low\n- Kind: chore\n- Summary: dup\n",
                encoding="utf-8",
            )
        out = io.StringIO()
        with redirect_stdout(out):
            rc = B.run_check(_args(dir=str(self.repo), agent=False))
        self.assertEqual(rc, 1)
        self.assertIn("id-duplicate", out.getvalue())

    def test_check_rejects_gate_on_non_blocked(self):
        d = self.repo / ".agents/backlog/open"
        d.mkdir(parents=True)
        (d / "20260101-s-01-gategt-g.md").write_text(
            "- Id: gategt\n- Status: open\n- Set: s\n- Priority: low\n- Kind: chore\n- Summary: g\n- Gate-Kind: artifact\n- Gate-Ref: x.md\n",
            encoding="utf-8",
        )
        out = io.StringIO()
        with redirect_stdout(out):
            rc = B.run_check(_args(dir=str(self.repo), agent=False))
        self.assertEqual(rc, 1)
        self.assertIn("gate-unexpected", out.getvalue())


class BacklogAttentionTests(unittest.TestCase):
    """(b) attention inclusion + hot-glance/JSON split + gate render; (d) _record_for mutation probe."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        _new(self.repo, summary="open one", slug="o", status="open")
        _new(
            self.repo,
            summary="maybe one",
            slug="p",
            status="parked",
            priority="low",
            kind="feature",
        )
        # move the open item to blocked with a gate
        f = next((self.repo / ".agents/backlog/open").glob("*.md"))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            B.run_set(
                _args(
                    dir=str(self.repo),
                    path=str(f),
                    status="blocked",
                    gate_kind="artifact",
                    gate_ref="path/x.md",
                    message="gated",
                    apply=True,
                )
            )

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_includes_backlog_with_correct_classes(self):
        items, drift = ATT.scan(self.repo)
        bl = {i.native_status: i for i in items if i.tree == "backlog"}
        self.assertEqual(set(bl), {"blocked", "parked"})
        self.assertEqual(bl["blocked"].attention_class, A.BLOCKED)
        self.assertEqual(bl["parked"].attention_class, A.PARKED)
        self.assertEqual([d for d in drift if "backlog" in d.location], [])

    def test_blocked_item_carries_gate(self):
        items, _ = ATT.scan(self.repo)
        blk = next(
            i for i in items if i.tree == "backlog" and i.native_status == "blocked"
        )
        self.assertEqual(blk.gate, {"kind": "artifact", "ref": "path/x.md"})

    def test_board_hides_parked_shows_blocked_with_gate(self):
        items, drift = ATT.scan(self.repo)
        board = ATT.render_board(items, drift, show_all=False)
        self.assertIn(
            "[gate artifact: path/x.md]", board
        )  # blocked item's gate rendered
        self.assertIn("[hidden; use --all]", board)  # parked group hidden
        board_all = ATT.render_board(items, drift, show_all=True)
        # under --all the parked group is shown (its count line, not "[hidden...]")
        self.assertRegex(board_all, r"## parked \(\d+\)\n")

    def test_json_includes_parked(self):
        items, drift = ATT.scan(self.repo)
        j = json.loads(ATT.render_json(items, drift))
        statuses = {x["native_status"] for x in j["items"] if x["tree"] == "backlog"}
        self.assertIn("parked", statuses)

    def test_record_for_branch_is_load_bearing(self):
        """Mutation probe (PR-001): without the backlog branch in _record_for, a classified
        backlog item is SILENTLY dropped (no Item, no drift)."""
        import agent_workflows.attention as att_mod

        orig = att_mod._record_for

        def patched(tree, rel, path, text):
            if tree == "backlog":
                return None, []  # simulate the missing branch (the fall-through)
            return orig(tree, rel, path, text)

        att_mod._record_for = patched
        try:
            items, drift = att_mod.scan(self.repo)
            backlog_items = [i for i in items if i.tree == "backlog"]
            self.assertEqual(
                backlog_items, [], "expected backlog items to vanish without the branch"
            )
            # and it is SILENT: no drift raised about the dropped items
            self.assertEqual([d for d in drift if "backlog" in d.location], [])
        finally:
            att_mod._record_for = orig
        # restored: items reappear
        items2, _ = att_mod.scan(self.repo)
        self.assertTrue(any(i.tree == "backlog" for i in items2))


if __name__ == "__main__":
    unittest.main()
