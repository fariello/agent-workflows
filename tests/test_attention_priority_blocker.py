"""Tests for awdoctorfix Order 01: the attention board's priority + release-blocker columns + legend.
render_board is pure over a list of Items, so these build Items in code (no disk fixture)."""

from __future__ import annotations

import json
import re
import unittest

from agent_workflows import attention
from agent_workflows import term as T


def _strip(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)


def _item(path, *, priority=None, blocks_release=None, lha="2026-05-01"):
    return attention.Item(
        "aaa111",
        path,
        "backlog",
        "open",
        "ready",
        None,
        lha,
        priority=priority,
        blocks_release=blocks_release,
    )


class AttentionPriorityBlockerTests(unittest.TestCase):
    def _colored(self, items):
        return _strip(
            attention.render_board(items, [], show_all=True, term=T.Term(color=True))
        )

    def _plain(self, items):
        return attention.render_board(
            items, [], show_all=True, term=T.Term(color=False)
        )

    def test_priority_bracket_rendered(self):
        out = self._colored(
            [_item(".aw/records/backlog/open/a.backlog.md", priority="high")]
        )
        self.assertIn("[high]", out)

    def test_release_blocker_marker(self):
        item = _item(".aw/records/backlog/open/a.backlog.md", blocks_release="next")
        out = self._colored([item])
        # the '>' release-blocker glyph leads the item line and [blocking] tag is present
        self.assertRegex(out, r"- [!?#]*>\s+open\s+backlog\s+a")
        self.assertIn("[blocking]", out)

        raw = attention.render_board([item], [], show_all=True, term=T.Term(color=True))
        # [blocking] is styled in red (256-color code 196, bold)
        self.assertIn("\033[1;38;5;196m[blocking]\033[0m", raw)

        out_noblock = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertNotIn("[blocking]", out_noblock)

    def test_legend_present_colored(self):
        out = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertIn("legend:", out)
        self.assertIn("release-blocker", out)

    def test_plain_board_unchanged(self):
        out = self._plain(
            [
                _item(
                    ".aw/records/backlog/open/a.backlog.md",
                    priority="high",
                    blocks_release="next",
                )
            ]
        )
        self.assertNotIn("legend:", out)
        self.assertNotIn("[high]", out)
        self.assertNotIn("[blocking]", out)
        self.assertIn("- [backlog] .aw/records/backlog/open/a.backlog.md (open)", out)

    def test_schema_version_and_json_keys(self):
        self.assertEqual(attention.SCHEMA_VERSION, 2)
        obj = json.loads(
            attention.render_json(
                [_item(".aw/records/backlog/open/a.backlog.md", priority="low")], []
            )
        )
        it = obj["items"][0]
        self.assertEqual(it["priority"], "low")
        self.assertIn("blocks_release", it)


class PlanReleaseBlockerSurfacingTests(unittest.TestCase):
    """IPD 7mw7m5 E-02: a plan carrying Blocks-Release surfaces in the release-blocker set AND its
    Item.blocks_release is populated by the plans reader (display parity with specs/backlog)."""

    def _mk_plan(self, root, br_value):
        import pathlib

        pdir = pathlib.Path(root) / ".aw" / "records" / "plans" / "pending"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "20260101-demo-01-pl0001-x.ipd.md").write_text(
            "# IPD: pl0001\n\n- Date: 2026-08-22\n- Kind: child\n- Status: draft\n"
            f"- Set: demo\n- Order: 1\n- Id: pl0001\n- Blocks-Release: {br_value}\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def test_plans_reader_populates_blocks_release_and_surfaces(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_plan(root, "next")
            items, _drift = attention.scan(root)
            plan_items = [it for it in items if it.tree == "plans"]
            self.assertEqual(len(plan_items), 1)
            # E-02: the plans reader now populates blocks_release (was None before).
            self.assertEqual(plan_items[0].blocks_release, "next")
            # set membership: the plan appears in the release-blocker set.
            blockers = attention.release_blockers(items, root)
            self.assertTrue(
                any(it.tree == "plans" and it.id == "pl0001" for it in blockers),
                "release-blocking plan must appear in release_blockers",
            )

    def test_plan_release_blocker_renders_blocking_markers(self):
        # Display parity: an Item with blocks_release set renders the `>` glyph / [blocking] label.
        it = attention.Item(
            "pl0001",
            ".aw/records/plans/pending/20260101-demo-01-pl0001-x.ipd.md",
            "plans",
            "draft",
            "ready",
            None,
            "2026-05-01",
            blocks_release="next",
        )
        out = _strip(
            attention.render_board([it], [], show_all=True, term=T.Term(color=True))
        )
        self.assertIn("[blocking]", out)


if __name__ == "__main__":
    unittest.main()
