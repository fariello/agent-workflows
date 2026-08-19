"""Tests for agent_workflows.record_history (awhistory Order 01): the global history.jsonl store."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_workflows import record_history as rh


class RecordHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_append_and_read(self) -> None:
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m1",
            date="20260101",
        )
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m2",
            date="20260102",
        )
        rh.append(
            self.root,
            id6="bbb222",
            tree="specs",
            workflow="spec",
            actor="b",
            message="s1",
            date="20260103",
        )
        forr = rh.read_for(self.root, "aaa111")
        self.assertEqual([r["message"] for r in forr], ["m1", "m2"])
        self.assertEqual(len(rh.read_all(self.root)), 3)

    def test_missing_file_returns_empty(self) -> None:
        self.assertEqual(rh.read_for(self.root, "aaa111"), [])
        self.assertEqual(rh.read_all(self.root), [])

    def test_malformed_line_skipped(self) -> None:
        p = rh.history_path(self.root)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            'this is not json\n{"id6":"aaa111","date":"20260101","tree":"plans","workflow":"ipd","actor":"a","message":"ok"}\n',
            encoding="utf-8",
        )
        recs = rh.read_all(self.root)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["message"], "ok")

    def test_bad_id6_raises(self) -> None:
        with self.assertRaises(ValueError):
            rh.append(
                self.root,
                id6="TOOLONG",
                tree="plans",
                workflow="ipd",
                actor="a",
                message="m",
            )

    def test_date_defaults_today(self) -> None:
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m",
        )
        self.assertEqual(
            rh.read_all(self.root)[0]["date"], date.today().strftime("%Y%m%d")
        )

    def test_managed_by_directive(self) -> None:
        self.assertIn("Managed-by: aw", rh.MANAGED_BY_DIRECTIVE)


if __name__ == "__main__":
    unittest.main()
