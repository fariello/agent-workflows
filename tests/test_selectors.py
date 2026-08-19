"""Tests for agent_workflows.selectors (awselect Order 01): the shared selector resolver."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import selectors


class SelectorResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        pend = self.root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        self.A = pend / "20260101-demo-01-aaa111-alpha.ipd.md"
        self.A.write_text(
            "# IPD: alpha\n\n- Id: aaa111\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        self.B = pend / "20260101-other-01-bbb222-beta.ipd.md"
        self.B.write_text(
            "# IPD: beta\n\n- Id: bbb222\n- Status: draft\n- Set: other\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_resolve_by_id6(self) -> None:
        self.assertEqual(
            selectors.resolve_selectors(self.root, "plans", ["aaa111"]), [self.A]
        )

    def test_resolve_by_status(self) -> None:
        self.assertEqual(
            selectors.resolve_selectors(self.root, "plans", ["approved"]), [self.A]
        )
        self.assertEqual(
            selectors.resolve_selectors(self.root, "plans", ["draft"]), [self.B]
        )

    def test_resolve_by_setid(self) -> None:
        self.assertEqual(
            selectors.resolve_selectors(self.root, "plans", ["demo"]), [self.A]
        )

    def test_resolve_by_filename_fragment(self) -> None:
        self.assertEqual(
            selectors.resolve_selectors(self.root, "plans", ["beta"]), [self.B]
        )

    def test_multiple_tokens_union(self) -> None:
        got = selectors.resolve_selectors(self.root, "plans", ["aaa111", "bbb222"])
        self.assertEqual(sorted(got), sorted([self.A, self.B]))
        self.assertEqual(len(got), 2)

    def test_empty_and_unknown(self) -> None:
        self.assertEqual(selectors.resolve_selectors(self.root, "plans", []), [])
        self.assertEqual(selectors.resolve_selectors(self.root, "bogus", ["x"]), [])


if __name__ == "__main__":
    unittest.main()
