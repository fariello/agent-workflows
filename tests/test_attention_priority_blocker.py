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
        out = self._colored(
            [_item(".aw/records/backlog/open/a.backlog.md", blocks_release="next")]
        )
        # the '>' release-blocker glyph leads the item line
        self.assertRegex(out, r"- [!?#]*>\s+open\s+backlog\s+a")

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


if __name__ == "__main__":
    unittest.main()
