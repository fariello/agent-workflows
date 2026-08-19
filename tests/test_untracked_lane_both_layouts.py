"""Tests for awuntrackedfix Order 01: rename local/ -> untracked/ across BOTH layouts, recursive
content merge (PR-002 regression), and nested-gitignore ensure. Idempotent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine


class UntrackedBothLayoutsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # populated local/ lanes in BOTH layouts, incl. a NESTED file (PR-002)
        for rel in (
            ".aw/records/comms",
            ".aw/records/prompts",
            ".agents/comms",
            ".agents/prompts",
        ):
            d = self.root / rel / "local" / "acks"
            d.mkdir(parents=True)
            (d / "x.json").write_text('{"ack":1}', encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_both_layouts_renamed_contents_preserved(self):
        renamed = engine.migrate_local_lanes_to_untracked(self.root, {})
        self.assertEqual(len(renamed), 4)
        for rel in (
            ".aw/records/comms",
            ".aw/records/prompts",
            ".agents/comms",
            ".agents/prompts",
        ):
            base = self.root / rel
            self.assertFalse((base / "local").exists(), f"{rel}/local should be gone")
            self.assertEqual(
                (base / "untracked" / "acks" / "x.json").read_text(),
                '{"ack":1}',
                f"{rel} nested ack must be preserved",
            )
            gi = (base / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("untracked/", gi)

    def test_pr002_nested_merge_when_untracked_preexists(self):
        # a pre-existing EMPTY untracked/acks/ must not strand local/acks/x.json (the reinstall bug)
        base = self.root / ".aw/records/comms"
        (base / "untracked" / "acks").mkdir(parents=True)
        engine.migrate_local_lanes_to_untracked(self.root, {})
        self.assertTrue((base / "untracked" / "acks" / "x.json").is_file())
        self.assertFalse((base / "local").exists())

    def test_idempotent(self):
        engine.migrate_local_lanes_to_untracked(self.root, {})
        again = engine.migrate_local_lanes_to_untracked(self.root, {})
        self.assertEqual(again, [])  # nothing left to rename


if __name__ == "__main__":
    unittest.main()
