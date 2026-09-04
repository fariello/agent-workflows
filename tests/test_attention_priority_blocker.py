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
        self.assertIn("high", out)
        raw = attention.render_board(
            [_item(".aw/records/backlog/open/a.backlog.md", priority="high")],
            [],
            show_all=True,
            term=T.Term(color=True),
        )
        self.assertIn("\033[1;38;5;196mhigh", raw)

    def test_release_blocker_marker(self):
        item = _item(".aw/records/backlog/open/a.backlog.md", blocks_release="next")
        out = self._colored([item])
        # the Blocking column renders the resolved release version or 'next'
        self.assertRegex(out, r"open\s+backlog\s+(?:2\.0\.0|next)\s+-\s+-\s+a")

        raw = attention.render_board([item], [], show_all=True, term=T.Term(color=True))
        # blocking release version is styled in red (256-color code 196, bold)
        self.assertIn("\033[1;38;5;196m", raw)

        out_noblock = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertRegex(out_noblock, r"open\s+backlog\s+-\s+-\s+-\s+a")

    def test_table_header_present_colored(self):
        out = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertIn(
            "Status    Type    Blocking Priority Readiness  Artifact Set / ID", out
        )

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
        # Display parity: an Item with blocks_release set renders in the Blocking column
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
        self.assertRegex(
            out, r"draft\s+plan\s+(?:2\.0\.0|next)\s+-\s+-\s+20260101-demo-01-pl0001"
        )


class RetiredPlanIsNotAReleaseBlockerTests(unittest.TestCase):
    """A RETIRED artifact keeps its `Blocks-Release` field on purpose (the field records what the
    artifact was for, and erasing it would falsify the record), but it must NOT be counted as an
    outstanding release blocker: nobody is going to do it. `release_blockers` previously skipped only
    the DONE class, so a plan retired to `superseded/` kept appearing in the release-blocker list."""

    def _mk_plan(self, root, disposition, status):
        import pathlib

        pdir = pathlib.Path(root) / ".aw" / "records" / "plans" / disposition
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "20260101-demo-01-pl0002-x.ipd.md").write_text(
            "# IPD: pl0002\n\n- Date: 2026-08-22\n- Kind: child\n"
            f"- Status: {status}\n"
            "- Set: demo\n- Order: 1\n- Id: pl0002\n- Blocks-Release: next\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def _blockers(self, disposition, status):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_plan(root, disposition, status)
            items, _drift = attention.scan(root)
            return (
                [it.id for it in attention.release_blockers(items, root)],
                [it.attention_class for it in items if it.tree == "plans"],
            )

    def test_superseded_plan_is_not_an_outstanding_release_blocker(self):
        # The regression: a split/retired plan keeps Blocks-Release but cannot gate a release.
        blockers, classes = self._blockers("superseded", "superseded")
        self.assertEqual(classes, ["parked"], "superseded must map to the parked class")
        self.assertNotIn(
            "pl0002",
            blockers,
            "a superseded plan must NOT be counted as an outstanding release blocker",
        )

    def test_pending_plan_is_still_an_outstanding_release_blocker(self):
        # The guard against over-filtering: a live plan must still be counted.
        blockers, _classes = self._blockers("pending", "approved")
        self.assertIn(
            "pl0002",
            blockers,
            "a live pending plan carrying Blocks-Release must still be counted",
        )


if __name__ == "__main__":
    unittest.main()
