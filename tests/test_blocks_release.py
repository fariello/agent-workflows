"""Tests for awrelease Order 02: the Blocks-Release gate field (parse + setter + dangling validation)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import backlog, releases, specs


class BlocksReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_backlog_parse_field(self) -> None:
        item = backlog.parse_item(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: next\n"
        )
        self.assertEqual(item.blocks_release, "next")
        item2 = backlog.parse_item("- Id: aaa111\n- Status: open\n")
        self.assertIsNone(item2.blocks_release)

    def test_specs_read_field(self) -> None:
        lines = (
            "# Spec\n\n- Status: draft\n- Blocks-Release: r1a2b3\n\n## Body\n".split(
                "\n"
            )
        )
        self.assertEqual(specs._read_blocks_release(lines), "r1a2b3")
        self.assertIsNone(
            specs._read_blocks_release("# Spec\n\n- Status: draft\n".split("\n"))
        )

    def test_setter_set_and_clear(self) -> None:
        text = "# X\n\n- Id: aaa111\n- Status: open\n\n## Goal\n\nx\n"
        with_field = releases.set_blocks_release_line(text, "next")
        self.assertIn("- Blocks-Release: next", with_field)
        cleared = releases.set_blocks_release_line(with_field, "-")
        self.assertNotIn("Blocks-Release", cleared)

    def test_dangling_flagged(self) -> None:
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True)
        (bl / "20260101-demo-01-aaa111-x.backlog.md").write_text(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: nonexist\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )
        drift = releases.check_blocks_release(self.root)
        self.assertTrue(any(d.rule == "check.blocks-release-dangling" for d in drift))

    def test_next_resolves(self) -> None:
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True)
        (bl / "20260101-demo-01-aaa111-x.backlog.md").write_text(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: next\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )
        # no release yet -> dangling
        self.assertTrue(
            any(
                d.rule == "check.blocks-release-dangling"
                for d in releases.check_blocks_release(self.root)
            )
        )
        # create the single planned release -> next resolves, no drift
        releases.create_release(self.root, "2.0.0", "x")
        self.assertEqual(releases.check_blocks_release(self.root), [])


if __name__ == "__main__":
    unittest.main()
