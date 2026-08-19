"""Tests for awdoctor Order 01: the compact COLORED attention board (folded dir prefix + bare names +
age/gate markers). render_board is pure over a list of Items, so no disk fixture is needed."""

from __future__ import annotations

import re
import unittest
from datetime import date, timedelta

from agent_workflows import attention
from agent_workflows import term as T


def _item(path, cls="ready", status="open", gate=None, lha=None):
    return attention.Item("aaa111", path, "backlog", status, cls, gate, lha)


def _strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


class AttentionCompactTests(unittest.TestCase):
    def _colored(self, items):
        term = T.Term(color=True)
        return _strip_ansi(attention.render_board(items, [], show_all=True, term=term))

    def _plain(self, items):
        term = T.Term(color=False)
        return attention.render_board(items, [], show_all=True, term=term)

    def test_common_prefix_in_header_and_bare_names(self):
        items = [
            _item(".aw/records/backlog/open/a.backlog.md"),
            _item(".aw/records/backlog/open/b.backlog.md"),
        ]
        out = self._colored(items)
        # awdoctorfix Order 02: the default colored view shows the compact identity stem, not the
        # folded-prefix/full-path form. A non-clustered name like `a.backlog.md` -> facet-stripped `a`.
        self.assertRegex(out, r"- (?:[!?#>]+ +)?open +backlog +a")
        self.assertNotIn(".aw/records/backlog/open/a.backlog.md (open)", out)

    def test_stale_marker(self):
        old = (date.today() - timedelta(days=60)).strftime("%Y-%m-%d")
        out = self._colored([_item(".aw/records/backlog/open/a.backlog.md", lha=old)])
        self.assertRegex(out, r"- !\s+open\s+backlog\s+a")

    def test_unknown_and_gate_markers(self):
        # lha=None -> '?'; gate -> '#'
        out = self._colored(
            [
                _item(
                    ".aw/records/backlog/blocked/a.backlog.md",
                    cls="blocked",
                    status="blocked",
                    gate={"kind": "artifact", "ref": "TODO.md"},
                    lha=None,
                )
            ]
        )
        self.assertRegex(out, r"- [?]?#\s+blocked\s+backlog\s+a")

    def test_plain_board_unchanged(self):
        # the machine-readable (uncolored) form keeps the stable [tree] path (status) shape.
        items = [_item(".aw/records/backlog/open/a.backlog.md")]
        out = self._plain(items)
        self.assertIn("- [backlog] .aw/records/backlog/open/a.backlog.md (open)", out)


if __name__ == "__main__":
    unittest.main()
