"""Tests for awdoctorfix Order 02: the attention board shows a compact identity stem by default and
the full path under --long. render_board is pure over a list of Items."""

from __future__ import annotations

import re
import unittest

from agent_workflows import attention
from agent_workflows import term as T


def _strip(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)


def _item(path, tree="backlog"):
    return attention.Item("aaa111", path, tree, "open", "ready", None, "2026-05-01")


class AttentionStemTests(unittest.TestCase):
    def test_identity_stem_grammar_and_fallback(self):
        self.assertEqual(
            attention._identity_stem(
                ".aw/records/backlog/open/20260815-attnview-followups-01-mc5xts-attnview-deferred-followups.backlog.md"
            ),
            "20260815-attnview-followups-01-mc5xts",
        )
        self.assertEqual(
            attention._identity_stem("aw-state/actions/open/setup-repo-v1.md"),
            "setup-repo-v1",
        )

    def test_default_board_shows_stem_not_directory(self):
        # a MIXED-tree ready group: default view shows stems, no directory prefix leaks.
        items = [
            _item(".aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md"),
            _item(".aw/records/specs/20260101-1200-01-thing.spec.md", tree="specs"),
        ]
        out = _strip(
            attention.render_board(items, [], show_all=True, term=T.Term(color=True))
        )
        self.assertIn("20260815-demo-01-aaa111", out)
        self.assertNotIn(".aw/records/backlog/open/", out)

    def test_long_shows_full_path(self):
        items = [_item(".aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md")]
        out = _strip(
            attention.render_board(
                items, [], show_all=True, term=T.Term(color=True), long=True
            )
        )
        self.assertIn(
            ".aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md", out
        )

    def test_plain_board_unchanged(self):
        items = [_item(".aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md")]
        out = attention.render_board(items, [], show_all=True, term=T.Term(color=False))
        self.assertIn(
            "- [backlog] .aw/records/backlog/open/20260815-demo-01-aaa111-x.backlog.md (open)",
            out,
        )


if __name__ == "__main__":
    unittest.main()
