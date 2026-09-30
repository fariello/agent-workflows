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
        # plan `vhbvwz` E-08: inline history is PRESERVED, newest-first. This assertion used to demand
        # exactly ONE record (awhistory Order 02's slimming), on the premise that the full log lived in
        # `.aw/records/history.jsonl`; that sidecar is gitignored, so the dropped records did not
        # survive a clone. The transition record now LEADS and the `created` record it used to destroy
        # is still beneath it.
        self.assertIn("finished", text)
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(len(inline), 2, inline)
        self.assertIn("finished", inline[0])
        self.assertIn("created", inline[1])

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

    def test_new_blocks_release_valid_and_appears_in_release_blockers(self):
        from agent_workflows import releases

        releases.create_release(self.repo, "2.0.0", "Release 2.0.0")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="Gate release",
                    set="relgate",
                    priority="high",
                    kind="feature",
                    slug="gate-rel",
                    blocks_release="next",
                    message="custom creation note",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        items = list((self.repo / ".agents/backlog/open").glob("*.md"))
        self.assertEqual(len(items), 1)
        text = items[0].read_text(encoding="utf-8")
        parsed = B.parse_item(text)
        self.assertEqual(parsed.blocks_release, "next")
        self.assertIn("- Blocks-Release: next", text)
        self.assertIn("created (aw backlog): custom creation note", text)
        self.assertEqual(releases.check_blocks_release(self.repo), [])
        items_att, drift = ATT.scan(self.repo)
        # durablecapture-02 (`m867ox`): the `releases` tree is TRACKED and now actually SCANNED, so
        # the record `create_release` wrote above is a legitimate second attention item. Assert the
        # RELATIONSHIP (which trees contributed which items) rather than a total count, so this test
        # fails again if the release record silently disappears from the view for any other reason.
        by_tree = {}
        for it in items_att:
            by_tree.setdefault(it.tree, []).append(it)
        self.assertEqual(sorted(by_tree), ["backlog", "releases"])
        self.assertEqual(len(by_tree["releases"]), 1)
        self.assertEqual(by_tree["releases"][0].native_status, "planned")
        self.assertEqual(by_tree["releases"][0].attention_class, A.READY)
        backlog_items = by_tree["backlog"]
        self.assertEqual(len(backlog_items), 1)
        self.assertEqual(backlog_items[0].blocks_release, "next")
        blockers = ATT.release_blockers(items_att, self.repo)
        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0].path, backlog_items[0].path)

    def test_new_blocks_release_unresolvable_fails_closed(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="Invalid gate",
                    set="badgate",
                    priority="high",
                    kind="feature",
                    slug="bad-gate",
                    blocks_release="next",
                    apply=True,
                )
            )
        self.assertEqual(rc, 2)
        items = list((self.repo / ".agents/backlog/open").glob("*.md"))
        self.assertEqual(len(items), 0)

    def test_new_blocks_release_dash_omits_field(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="No gate",
                    set="nogate",
                    priority="low",
                    kind="chore",
                    slug="no-gate",
                    blocks_release="-",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        items = list((self.repo / ".agents/backlog/open").glob("*.md"))
        self.assertEqual(len(items), 1)
        text = items[0].read_text(encoding="utf-8")
        parsed = B.parse_item(text)
        self.assertIsNone(parsed.blocks_release)
        self.assertNotIn("Blocks-Release", text)

    def test_new_custom_message_and_default_message(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc1 = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="Default msg",
                    set="s1",
                    priority="medium",
                    kind="chore",
                    slug="s1",
                    message="",
                    apply=True,
                )
            )
            rc2 = B.run_new(
                _args(
                    dir=str(self.repo),
                    summary="Custom summary",
                    set="s2",
                    priority="medium",
                    kind="chore",
                    slug="s2",
                    message="explicit note",
                    apply=True,
                )
            )
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        items = sorted((self.repo / ".agents/backlog/open").glob("*.md"))
        self.assertEqual(len(items), 2)
        t1 = items[0].read_text(encoding="utf-8")
        t2 = items[1].read_text(encoding="utf-8")
        self.assertIn("created (aw backlog): Default msg", t1)
        self.assertIn("created (aw backlog): explicit note", t2)

    def test_one_call_vs_two_call_parity(self):
        from agent_workflows import releases

        # Repo 1: One-call creation
        tmp1 = tempfile.TemporaryDirectory()
        r1 = Path(tmp1.name)
        releases.create_release(r1, "2.0.0", "Release 2.0.0")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            B.run_new(
                _args(
                    dir=str(r1),
                    summary="Parity check",
                    set="parity",
                    priority="high",
                    kind="feature",
                    slug="parity-check",
                    blocks_release="next",
                    message="parity note",
                    apply=True,
                )
            )
        item1_file = next((r1 / ".agents/backlog/open").glob("*.md"))
        p1 = B.parse_item(item1_file.read_text(encoding="utf-8"))

        # Repo 2: Two-call creation (new then set)
        tmp2 = tempfile.TemporaryDirectory()
        r2 = Path(tmp2.name)
        releases.create_release(r2, "2.0.0", "Release 2.0.0")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            B.run_new(
                _args(
                    dir=str(r2),
                    summary="Parity check",
                    set="parity",
                    priority="high",
                    kind="feature",
                    slug="parity-check",
                    apply=True,
                )
            )
            item2_file = next((r2 / ".agents/backlog/open").glob("*.md"))
            B.run_set(
                _args(
                    dir=str(r2),
                    path=str(item2_file),
                    status="open",
                    blocks_release="next",
                    message="parity note",
                    apply=True,
                )
            )
        p2 = B.parse_item(item2_file.read_text(encoding="utf-8"))

        self.assertEqual(p1.status, p2.status)
        self.assertEqual(p1.set, p2.set)
        self.assertEqual(p1.priority, p2.priority)
        self.assertEqual(p1.kind, p2.kind)
        self.assertEqual(p1.summary, p2.summary)
        self.assertEqual(p1.blocks_release, p2.blocks_release)
        self.assertEqual(p1.blocks_release, "next")

        tmp1.cleanup()
        tmp2.cleanup()


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


class BacklogNoteVerbTests(unittest.TestCase):
    """`aw backlog note` (plan `vhbvwz` E-05): annotate WITHOUT transitioning.

    WHY THE VERB EXISTS, since that is what these assertions are really protecting. The backlog verb
    set was `new`, `set`, `check` only, so recording a reason on an item REQUIRED a status-setting
    call - and a same-status `aw backlog set` both discarded the message (`x6tk1u`) and slimmed the
    item's history while doing it. Those two defects were hit through exactly that route. `aw specs
    note` already existed; this is its backlog twin, and it removes the incentive to reach for the
    transition verb when annotation is the intent.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        d = self.repo / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True)
        self.item = d / "20260101-demo-01-nt0001-x.backlog.md"
        self.item.write_text(
            "- Id: nt0001\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: a summary\n\n"
            "## Workflow history\n- 2026-01-01 created (aw backlog): a summary\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _records(self, path: Path):
        return [
            ln.strip()
            for ln in path.read_text(encoding="utf-8")
            .split("## Workflow history", 1)[1]
            .split("\n")
            if A.HISTORY_RECORD_RE.match(ln.strip())
        ]

    def _note(self, message, **kw):
        base = dict(
            dir=str(self.repo), path="nt0001", message=message, date="2026-02-02"
        )
        base.update(kw)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_note(_args(**base))
        return rc, out.getvalue(), err.getvalue()

    def test_note_records_history_without_changing_status_or_moving_the_file(self):
        rc, _out, _err = self._note("the reason this matters")
        self.assertEqual(rc, 0)
        self.assertTrue(self.item.exists(), "note must NOT move the item's file")
        text = self.item.read_text(encoding="utf-8")
        self.assertIn("- Status: open", text)
        recs = self._records(self.item)
        self.assertEqual(len(recs), 2, recs)
        self.assertEqual(
            recs[0], "- 2026-02-02 note (aw backlog): the reason this matters"
        )
        self.assertEqual(recs[1], "- 2026-01-01 created (aw backlog): a summary")

    def test_a_second_note_preserves_the_first(self):
        self._note("first reason")
        self._note("second reason")
        recs = self._records(self.item)
        self.assertEqual(len(recs), 3, recs)
        self.assertIn("second reason", recs[0])
        self.assertIn("first reason", recs[1])
        self.assertIn("created", recs[2])

    def test_note_refuses_an_empty_message_and_an_unknown_item(self):
        rc, _out, err = self._note("")
        self.assertEqual(rc, 2)
        self.assertIn("--message is required", err)
        rc, _out, err = self._note("x", path="zzzz99")
        self.assertEqual(rc, 2)
        self.assertIn("no such item", err)

    def test_the_cli_registers_the_verb(self):
        from agent_workflows import cli

        rc = cli.main(
            [
                "backlog",
                "note",
                "nt0001",
                "--message",
                "recorded through the CLI",
                "--dir",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("recorded through the CLI", self.item.read_text(encoding="utf-8"))


class BacklogDryRunTests(unittest.TestCase):
    """Outcome tests for --dry-run on aw backlog set (IPD wd6npl E-05)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        (self.repo / ".aw" / "records" / "releases" / "planned").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_backlog_set_status_dry_run_leaves_file_and_sidecar_untouched(self):
        from agent_workflows import cli

        item_path = (
            self.repo
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260926-demo-01-bk0001-item.backlog.md"
        )
        item_path.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: feature\n"
            "- Set: demo\n"
            "- Custom-Field: KEEP-ME\n"
            "- Summary: an open item\n\n"
            "## Workflow history\n"
            "- 2026-09-26 created (tester): initial\n",
            encoding="utf-8",
        )
        before_bytes = item_path.read_bytes()
        before_listing = sorted(
            p.name for p in (self.repo / ".aw" / "records" / "backlog").rglob("*.md")
        )
        sidecar = self.repo / ".aw" / "records" / "history.jsonl"
        self.assertFalse(sidecar.exists())

        rc = cli.main(
            [
                "backlog",
                "set",
                str(item_path),
                "--status",
                "open",
                "--dry-run",
                "--dir",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(item_path.read_bytes(), before_bytes)
        after_listing = sorted(
            p.name for p in (self.repo / ".aw" / "records" / "backlog").rglob("*.md")
        )
        self.assertEqual(after_listing, before_listing)
        self.assertFalse(sidecar.exists())

    def test_backlog_set_status_done_dry_run_refuses_illegitimate_blocking_close_without_sidecar(
        self,
    ):
        from agent_workflows import cli

        rel_path = (
            self.repo
            / ".aw"
            / "records"
            / "releases"
            / "planned"
            / "20260926-rel001-01-rel001-v1.release.md"
        )
        rel_path.write_text(
            "# Release: v1.0.0\n\n"
            "- Id: rel001\n"
            "- Status: planned\n"
            "- Version: 1.0.0\n",
            encoding="utf-8",
        )
        item_path = (
            self.repo
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260926-demo-01-bk0002-blocked.backlog.md"
        )
        item_path.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Priority: high\n"
            "- Work-Kind: bug\n"
            "- Blocks-Release: rel001\n"
            "- Set: demo\n"
            "- Summary: a release blocker\n\n"
            "## Workflow history\n"
            "- 2026-09-26 created (tester): initial\n",
            encoding="utf-8",
        )
        before_bytes = item_path.read_bytes()
        sidecar = self.repo / ".aw" / "records" / "history.jsonl"
        self.assertFalse(sidecar.exists())

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    str(item_path),
                    "--status",
                    "done",
                    "--dry-run",
                    "--dir",
                    str(self.repo),
                ]
            )
        self.assertEqual(rc, 1)
        self.assertIn("refused:", err.getvalue())
        self.assertEqual(item_path.read_bytes(), before_bytes)
        self.assertFalse(sidecar.exists())

    def test_backlog_set_positional_dry_run_leaves_file_untouched(self):
        from agent_workflows import cli

        item_path = (
            self.repo
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260926-demo-01-bk0003-pos.backlog.md"
        )
        item_path.write_text(
            "- Id: bk0003\n"
            "- Status: open\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Set: demo\n"
            "- Summary: a positional test item\n\n"
            "## Workflow history\n"
            "- 2026-09-26 created (tester): initial\n",
            encoding="utf-8",
        )
        before_bytes = item_path.read_bytes()

        rc = cli.main(
            [
                "backlog",
                "set",
                "open",
                "bk0003",
                "--dry-run",
                "--dir",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(item_path.read_bytes(), before_bytes)


class BacklogPreservationTests(unittest.TestCase):
    """rendrop 2yqt0a E-04 and E-09: source-order metadata preservation, header prose preservation,
    and release-gate close refusal on close_on_answer."""

    def _setup_repo(self, repo: Path) -> None:
        for sub in ("open", "parked", "graduated", "done", "blocked"):
            (repo / ".aw" / "records" / "backlog" / sub).mkdir(
                parents=True, exist_ok=True
            )
        (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "records" / "plans" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        rel = (
            repo
            / ".aw"
            / "records"
            / "releases"
            / "20260901-rel001-01-rel001-v1.release.md"
        )
        rel.write_text(
            "# Release: 1.0.0\n\n"
            "- Id: rel001\n"
            "- Status: planned\n"
            "- Version: 1.0.0\n"
            "- Summary: test release\n",
            encoding="utf-8",
        )

    def test_backlog_set_metadata_preservation_both_spellings_agree(self):
        """(a) BOTH SPELLINGS AGREE: two identical scratch repos, one item carrying
        Blocks-Release, Custom-Field, Graduated-To; both spellings produce equal metadata blocks."""
        from agent_workflows import cli

        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            r1, r2 = Path(tmp1), Path(tmp2)
            self._setup_repo(r1)
            self._setup_repo(r2)

            item_content = (
                "- Id: bk0001\n"
                "- Status: open\n"
                "- Blocks-Release: rel001\n"
                "- Custom-Field: keepme\n"
                "- Graduated-To: foo\n"
                "- Set: demo\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: test item\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n"
            )
            p1 = (
                r1
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0001-item.backlog.md"
            )
            p2 = (
                r2
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0001-item.backlog.md"
            )
            p1.write_text(item_content, encoding="utf-8")
            p2.write_text(item_content, encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc1 = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p1),
                        "--status",
                        "parked",
                        "--dir",
                        str(r1),
                        "--no-commit",
                    ]
                )
                rc2 = cli.main(
                    [
                        "backlog",
                        "set",
                        "parked",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(r2),
                    ]
                )
            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)

            parked1 = r1 / ".aw" / "records" / "backlog" / "parked" / p1.name
            parked2 = r2 / ".aw" / "records" / "backlog" / "parked" / p2.name
            self.assertTrue(parked1.exists())
            self.assertTrue(parked2.exists())

            meta1 = parked1.read_text(encoding="utf-8").split("\n## Workflow history")[
                0
            ]
            meta2 = parked2.read_text(encoding="utf-8").split("\n## Workflow history")[
                0
            ]

            self.assertEqual(meta1, meta2)
            self.assertIn("- Blocks-Release: rel001", meta1)
            self.assertIn("- Custom-Field: keepme", meta1)
            self.assertIn("- Graduated-To: foo", meta1)

    def test_backlog_set_status_graduated_to_replaces_and_preserves_custom_field(self):
        """(b) --status graduated --graduated-to bar replaces value and keeps Custom-Field."""
        from agent_workflows import cli

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0002-item.backlog.md"
            )
            p.write_text(
                "- Id: bk0002\n"
                "- Status: open\n"
                "- Custom-Field: keepme\n"
                "- Graduated-To: foo\n"
                "- Set: demo\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: item with custom field\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n",
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p),
                        "--status",
                        "graduated",
                        "--graduated-to",
                        "bar",
                        "--dir",
                        str(r),
                        "--no-commit",
                    ]
                )
            self.assertEqual(rc, 0)

            grad = r / ".aw" / "records" / "backlog" / "graduated" / p.name
            self.assertTrue(grad.exists())
            text = grad.read_text(encoding="utf-8")
            self.assertIn("- Graduated-To: bar", text)
            self.assertNotIn("- Graduated-To: foo", text)
            self.assertIn("- Custom-Field: keepme", text)

    def test_backlog_set_blocks_release_dash_removes_gate_and_preserves_custom_field(
        self,
    ):
        """(c) --blocks-release - removes the gate and keeps Custom-Field."""
        from agent_workflows import cli

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0003-item.backlog.md"
            )
            p.write_text(
                "- Id: bk0003\n"
                "- Status: open\n"
                "- Blocks-Release: rel001\n"
                "- Custom-Field: keepme\n"
                "- Set: demo\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: item with gate and custom field\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n",
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p),
                        "--status",
                        "parked",
                        "--blocks-release",
                        "-",
                        "--dir",
                        str(r),
                        "--no-commit",
                    ]
                )
            self.assertEqual(rc, 0)

            parked = r / ".aw" / "records" / "backlog" / "parked" / p.name
            self.assertTrue(parked.exists())
            text = parked.read_text(encoding="utf-8")
            self.assertNotIn("- Blocks-Release:", text)
            self.assertIn("- Custom-Field: keepme", text)

    def test_close_on_answer_preserves_custom_field_and_handed_off_blocks_release(self):
        """(d) close_on_answer keeps Custom-Field and Blocks-Release when gate is handed off."""
        from agent_workflows import set_records

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            # Carrier plan in executed/
            carrier = (
                r
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260901-rel001-01-pln001-plan.ipd.md"
            )
            carrier.write_text(
                "# IPD: Carrier\n\n"
                "- Id: pln001\n"
                "- Status: executed\n"
                "- From-Backlog: bk0004\n"
                "- Blocks-Release: rel001\n"
                "- Set: rel001\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: carrier plan\n\n"
                "## Workflow history\n"
                "- 2026-09-01 executed (tester): finished\n",
                encoding="utf-8",
            )

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260926-demo-01-bk0004-item.backlog.md"
            )
            p.write_text(
                "- Id: bk0004\n"
                "- Status: blocked\n"
                "- Gate-Kind: spec\n"
                "- Gate-Ref: rel001\n"
                "- Blocks-Release: rel001\n"
                "- Custom-Field: keepme\n"
                "- Set: demo\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: blocked item\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n",
                encoding="utf-8",
            )

            dest = set_records.close_on_answer(r, p)
            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            self.assertIn("- Custom-Field: keepme", text)
            self.assertIn("- Blocks-Release: rel001", text)
            self.assertNotIn("- Gate-Kind:", text)
            self.assertNotIn("- Gate-Ref:", text)

    def test_close_on_answer_preserves_prior_history_records(self):
        """(a) close_on_answer on a 3-record item yields 4 records, close-record first, originals byte-identical."""
        from agent_workflows import attention as att
        from agent_workflows import attention_contract as ac
        from agent_workflows import set_records

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)
            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260901-demo-01-bk0001-test.backlog.md"
            )
            original_records = [
                "- 2026-09-20 note (aw backlog): note 1",
                "- 2026-09-10 set (aw backlog): set 1",
                "- 2026-09-01 created (aw backlog): created 1",
            ]
            p.write_text(
                "- Id: bk0001\n"
                "- Status: blocked\n"
                "- Set: demo\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D1\n"
                "- Summary: test item\n\n"
                "## Workflow history\n" + "\n".join(original_records) + "\n\n"
                "## Body\n"
                "Test body\n",
                encoding="utf-8",
            )

            dest = set_records.close_on_answer(r, p)
            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            history_lines = [
                ln
                for ln in att._history_section_lines(text)
                if ac.HISTORY_RECORD_RE.match(ln)
            ]
            self.assertEqual(len(history_lines), 4)
            self.assertIn("question answered; close-on-answer", history_lines[0])
            self.assertIn("set (aw backlog)", history_lines[0])
            self.assertEqual(history_lines[1:], original_records)
            self.assertNotIn("created (aw backlog): test item", text)

    def test_close_on_answer_preserves_pre_history_prose_exactly_once(self):
        """(b) close_on_answer on an item with pre-history prose keeps it exactly once."""
        from agent_workflows import set_records

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)
            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260901-demo-01-bk0002-test.backlog.md"
            )
            p.write_text(
                "- Id: bk0002\n"
                "- Status: blocked\n"
                "- Set: demo\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D1\n"
                "- Summary: test item\n\n"
                "PRE_HISTORY_PROSE_PARA_DISTINCTIVE\n\n"
                "## Workflow history\n"
                "- 2026-09-01 created (aw backlog): created 1\n\n"
                "## Body\n\n"
                "POST_HISTORY_PROSE_PARA_DISTINCTIVE\n",
                encoding="utf-8",
            )

            dest = set_records.close_on_answer(r, p)
            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            self.assertEqual(text.count("PRE_HISTORY_PROSE_PARA_DISTINCTIVE"), 1)
            self.assertEqual(text.count("POST_HISTORY_PROSE_PARA_DISTINCTIVE"), 1)

    def test_close_on_answer_does_not_promote_indented_prose_quoted_history_lines(self):
        """(c) indented prose-quoted history-shaped line in body is not promoted into history block."""
        from agent_workflows import attention as att
        from agent_workflows import attention_contract as ac
        from agent_workflows import set_records

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)
            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260901-demo-01-bk0003-test.backlog.md"
            )
            p.write_text(
                "- Id: bk0003\n"
                "- Status: blocked\n"
                "- Set: demo\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Gate-Kind: decision\n"
                "- Gate-Ref: D1\n"
                "- Summary: test item\n\n"
                "## Workflow history\n"
                "- 2026-09-01 created (aw backlog): created 1\n\n"
                "## Body\n\n"
                "Here is an indented quote:\n\n"
                "    - 2020-01-01 fake (aw fake): DO_NOT_PROMOTE\n\n"
                "End of body.\n",
                encoding="utf-8",
            )

            dest = set_records.close_on_answer(r, p)
            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            history_lines = [
                ln
                for ln in att._history_section_lines(text)
                if ac.HISTORY_RECORD_RE.match(ln)
            ]
            self.assertEqual(len(history_lines), 2)
            self.assertTrue(
                any("question answered; close-on-answer" in ln for ln in history_lines)
            )
            for h in history_lines:
                self.assertNotIn("DO_NOT_PROMOTE", h)
            self.assertEqual(text.count("DO_NOT_PROMOTE"), 1)

    def test_header_prose_survives(self):
        """(a) Header prose between metadata bullets and ## Workflow history survives re-render."""
        from agent_workflows import cli

        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            r1, r2 = Path(tmp1), Path(tmp2)
            self._setup_repo(r1)
            self._setup_repo(r2)

            item_text = (
                "- Id: bk0005\n"
                "- Status: open\n"
                "- Set: demo\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: item with header prose\n\n"
                "## What is wrong\n\n"
                "This is important header prose describing the problem in detail.\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n"
            )
            p1 = (
                r1
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0005-item.backlog.md"
            )
            p2 = (
                r2
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0005-item.backlog.md"
            )
            p1.write_text(item_text, encoding="utf-8")
            p2.write_text(item_text, encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc1 = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p1),
                        "--status",
                        "parked",
                        "--dir",
                        str(r1),
                        "--no-commit",
                    ]
                )
                rc2 = cli.main(
                    [
                        "backlog",
                        "set",
                        "parked",
                        "bk0005",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(r2),
                    ]
                )
            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)

            parked1 = r1 / ".aw" / "records" / "backlog" / "parked" / p1.name
            parked2 = r2 / ".aw" / "records" / "backlog" / "parked" / p2.name
            self.assertTrue(parked1.exists())
            self.assertTrue(parked2.exists())

            t1 = parked1.read_text(encoding="utf-8")
            t2 = parked2.read_text(encoding="utf-8")
            self.assertIn(
                "## What is wrong\n\nThis is important header prose describing the problem in detail.",
                t1,
            )

            head1 = t1.split("\n## Workflow history")[0]
            head2 = t2.split("\n## Workflow history")[0]
            self.assertEqual(head1, head2)

    def test_duplicate_work_kind_deduped(self):
        """(b) Item carrying both - Kind: chore and - Work-Kind: bug renders exactly one Work-Kind line."""
        from agent_workflows import backlog, cli

        raw_item = (
            "- Id: bk0006\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Kind: chore\n"
            "- Work-Kind: bug\n"
            "- Summary: item with dual kinds\n\n"
            "## Workflow history\n"
            "- 2026-09-26 created (tester): initial\n"
        )
        parsed = backlog.parse_item(raw_item)
        direct_rendered = backlog._render_item(parsed, "", source_text=raw_item)
        wk_direct = [
            ln for ln in direct_rendered.splitlines() if ln.startswith("- Work-Kind:")
        ]
        self.assertEqual(len(wk_direct), 1)
        self.assertEqual(wk_direct[0], "- Work-Kind: bug")

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260926-demo-01-bk0006-item.backlog.md"
            )
            p.write_text(raw_item, encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p),
                        "--status",
                        "parked",
                        "--dir",
                        str(r),
                        "--no-commit",
                    ]
                )
            self.assertEqual(rc, 0)

            parked = r / ".aw" / "records" / "backlog" / "parked" / p.name
            text = parked.read_text(encoding="utf-8")
            wk_lines = [ln for ln in text.splitlines() if ln.startswith("- Work-Kind:")]
            self.assertEqual(len(wk_lines), 1)
            self.assertEqual(wk_lines[0], "- Work-Kind: bug")
            self.assertFalse(any(ln.startswith("- Kind:") for ln in text.splitlines()))

    def test_stale_gate_summary_dropped(self):
        """(c) Blocked item carrying Gate-Summary transitioned to done drops Gate-Summary."""
        from agent_workflows import backlog, cli

        raw_item = (
            "- Id: bk0007\n"
            "- Status: blocked\n"
            "- Gate-Kind: spec\n"
            "- Gate-Ref: rel001\n"
            "- Gate-Summary: waiting on a ruling\n"
            "- Set: demo\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Summary: blocked item with gate summary\n\n"
            "## Workflow history\n"
            "- 2026-09-26 created (tester): initial\n"
        )
        parsed = backlog.parse_item(raw_item)
        parsed.status = "done"
        direct_rendered = backlog._render_item(parsed, "", source_text=raw_item)
        self.assertNotIn("- Gate-Summary:", direct_rendered)

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260926-demo-01-bk0007-item.backlog.md"
            )
            p.write_text(raw_item, encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(p),
                        "--status",
                        "done",
                        "--dir",
                        str(r),
                        "--no-commit",
                    ]
                )
            self.assertEqual(rc, 0)

            done = r / ".aw" / "records" / "backlog" / "done" / p.name
            self.assertTrue(done.exists())
            text = done.read_text(encoding="utf-8")
            self.assertNotIn("- Gate-Summary:", text)
            self.assertNotIn("- Gate-Kind:", text)
            self.assertNotIn("- Gate-Ref:", text)

    def test_gated_close_refused_without_carrier(self):
        """(d) close_on_answer on item with Blocks-Release and no carrier raises ValueError and leaves file untouched."""
        from agent_workflows import set_records

        with tempfile.TemporaryDirectory() as tmp:
            r = Path(tmp)
            self._setup_repo(r)

            p = (
                r
                / ".aw"
                / "records"
                / "backlog"
                / "blocked"
                / "20260926-demo-01-bk0008-item.backlog.md"
            )
            p.write_text(
                "- Id: bk0008\n"
                "- Status: blocked\n"
                "- Gate-Kind: spec\n"
                "- Gate-Ref: rel001\n"
                "- Blocks-Release: rel001\n"
                "- Set: demo\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: blocked item with gate\n\n"
                "## Workflow history\n"
                "- 2026-09-26 created (tester): initial\n",
                encoding="utf-8",
            )
            before_bytes = p.read_bytes()

            with self.assertRaises(ValueError) as ctx:
                set_records.close_on_answer(r, p)
            self.assertIn("rel001", str(ctx.exception))

            self.assertTrue(p.exists())
            self.assertEqual(p.read_bytes(), before_bytes)
            done_files = list((r / ".aw" / "records" / "backlog" / "done").glob("*.md"))
            self.assertEqual(done_files, [])

    def test_validate_item_release_exempt_findings(self):
        """Validate item release exemption rules: incomplete, kind-invalid, ref-invalid, contradicts-gate."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            p = d / "test.backlog.md"

            # 1. kind without ref -> backlog.release-exempt-incomplete
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Release-Exempt-Kind: decision\n"
            )
            drift = B.validate_item(p, p.read_text())
            rules = [x.rule for x in drift]
            self.assertIn("backlog.release-exempt-incomplete", rules)

            # 2. ref without kind -> backlog.release-exempt-incomplete
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Release-Exempt-Ref: D42\n"
            )
            drift = B.validate_item(p, p.read_text())
            rules = [x.rule for x in drift]
            self.assertIn("backlog.release-exempt-incomplete", rules)

            # 3. kind bogus -> backlog.release-exempt-kind-invalid
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Release-Exempt-Kind: bogus\n- Release-Exempt-Ref: D42\n"
            )
            drift = B.validate_item(p, p.read_text())
            rules = [x.rule for x in drift]
            self.assertIn("backlog.release-exempt-kind-invalid", rules)

            # 4. decision + garbage -> backlog.release-exempt-ref-invalid
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Release-Exempt-Kind: decision\n- Release-Exempt-Ref: garbage\n"
            )
            drift = B.validate_item(p, p.read_text())
            rules = [x.rule for x in drift]
            self.assertIn("backlog.release-exempt-ref-invalid", rules)

            # 5. valid pair, no gate -> clean (no new findings)
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Release-Exempt-Kind: decision\n- Release-Exempt-Ref: D42\n"
            )
            drift = B.validate_item(p, p.read_text())
            exempt_rules = [
                x.rule for x in drift if x.rule.startswith("backlog.release-exempt-")
            ]
            self.assertEqual(exempt_rules, [])

            # 6. valid pair PLUS - Blocks-Release: next -> backlog.release-exempt-contradicts-gate
            p.write_text(
                "- Id: b00001\n- Status: open\n- Set: s\n- Priority: high\n- Work-Kind: bug\n- Summary: Item\n- Blocks-Release: next\n- Release-Exempt-Kind: decision\n- Release-Exempt-Ref: D42\n"
            )
            drift = B.validate_item(p, p.read_text())
            rules = [x.rule for x in drift]
            self.assertIn("backlog.release-exempt-contradicts-gate", rules)

    def test_render_item_preserves_release_exempt_with_source_text(self):
        """_render_item preserves Release-Exempt-Kind and Release-Exempt-Ref in original order when source_text is passed."""
        text = (
            "- Id: b00001\n"
            "- Status: open\n"
            "- Set: s\n"
            "- Priority: high\n"
            "- Work-Kind: bug\n"
            "- Summary: Item\n"
            "- Release-Exempt-Kind: decision\n"
            "- Release-Exempt-Ref: D42\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (aw backlog): initial\n\n"
            "Prose body\n"
        )
        item = B.parse_item(text)
        rendered = B._render_item(item, "Prose body\n", source_text=text)
        self.assertIn("- Release-Exempt-Kind: decision\n", rendered)
        self.assertIn("- Release-Exempt-Ref: D42\n", rendered)
        kind_pos = rendered.index("- Release-Exempt-Kind: decision\n")
        ref_pos = rendered.index("- Release-Exempt-Ref: D42\n")
        self.assertLess(kind_pos, ref_pos)

    def test_render_item_drops_unknown_without_source_text_and_creation_emits_pair(
        self,
    ):
        """_render_item drops exempt fields when source_text is omitted, and run_new emits them via post-render writer."""
        text = (
            "- Id: b00001\n"
            "- Status: open\n"
            "- Set: s\n"
            "- Priority: high\n"
            "- Work-Kind: bug\n"
            "- Summary: Item\n"
            "- Release-Exempt-Kind: decision\n"
            "- Release-Exempt-Ref: D42\n"
        )
        item = B.parse_item(text)
        rendered_no_source = B._render_item(item, "body")
        self.assertNotIn("- Release-Exempt-Kind:", rendered_no_source)
        self.assertNotIn("- Release-Exempt-Ref:", rendered_no_source)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".aw" / "records" / "backlog" / "open").mkdir(
                parents=True, exist_ok=True
            )
            args = _args(
                dir=str(repo),
                summary="exempt bug",
                set="s",
                priority="high",
                work_kind="bug",
                slug="exempt-bug",
                release_exempt_kind="decision",
                release_exempt_ref="D42",
                apply=True,
            )
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = B.run_new(args)
            self.assertEqual(rc, 0)
            created_files = list(
                (repo / ".aw" / "records" / "backlog" / "open").glob("*.md")
            )
            self.assertEqual(len(created_files), 1)
            content = created_files[0].read_text(encoding="utf-8")
            self.assertIn("- Release-Exempt-Kind: decision\n", content)
            self.assertIn("- Release-Exempt-Ref: D42\n", content)
            self.assertNotIn("- Blocks-Release:", content)

    def test_release_exempt_setter_roundtrip_and_parity(self):
        """Setter roundtrip through both spellings writes bullets and history, and produces field-identical output."""
        from agent_workflows import status_set

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".aw" / "records" / "backlog" / "open").mkdir(
                parents=True, exist_ok=True
            )

            item1_text = (
                "- Id: bk0001\n"
                "- Status: open\n"
                "- Set: s\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Bug 1\n\n"
                "## Workflow history\n"
                "- 2026-09-01 created (tester): initial\n\n"
                "Prose\n"
            )
            item2_text = (
                "- Id: bk0002\n"
                "- Status: open\n"
                "- Set: s\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Bug 2\n\n"
                "## Workflow history\n"
                "- 2026-09-01 created (tester): initial\n\n"
                "Prose\n"
            )
            f1 = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260901-s-01-bk0001-bug-1.backlog.md"
            )
            f2 = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260901-s-01-bk0002-bug-2.backlog.md"
            )
            f1.write_text(item1_text, encoding="utf-8")
            f2.write_text(item2_text, encoding="utf-8")

            # Route 1: run_set (--status spelling)
            set_args1 = _args(
                dir=str(repo),
                path=str(f1),
                status="open",
                release_exempt_kind="decision",
                release_exempt_ref="D42",
                message="exempted reason",
            )
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc1 = B.run_set(set_args1)
            self.assertEqual(rc1, 0)
            res1_text = f1.read_text(encoding="utf-8")
            self.assertIn("- Release-Exempt-Kind: decision\n", res1_text)
            self.assertIn("- Release-Exempt-Ref: D42\n", res1_text)
            self.assertIn("exempted reason", res1_text)

            # Route 2: positional spelling via run_set_command
            set_args2 = _args(
                dir=str(repo),
                args=["open", "bk0002"],
                release_exempt_kind="decision",
                release_exempt_ref="D42",
                message="exempted reason",
                yes=True,
                force=False,
                scoped_type="backlog",
            )
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc2 = status_set.run_set_command(
                    set_args2.args, scoped_type="backlog", args=set_args2
                )
            self.assertEqual(rc2, 0)
            res2_text = f2.read_text(encoding="utf-8")
            self.assertIn("- Release-Exempt-Kind: decision\n", res2_text)
            self.assertIn("- Release-Exempt-Ref: D42\n", res2_text)
            self.assertIn("exempted reason", res2_text)

            norm1 = (
                res1_text.replace("bk0001", "bkXXXX")
                .replace("Bug 1", "Bug X")
                .replace("set (aw backlog)", "HIST_ACTOR")
            )
            norm2 = (
                res2_text.replace("bk0002", "bkXXXX")
                .replace("Bug 2", "Bug X")
                .replace("same-status (aw set)", "HIST_ACTOR")
            )
            self.assertEqual(norm1, norm2)


if __name__ == "__main__":
    unittest.main()
