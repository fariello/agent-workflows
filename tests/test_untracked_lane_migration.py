"""Tests for awuntracked Order 01: migrating an existing repo's `local/` quarantine lanes to
`untracked/` (rename + content preservation + idempotency)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine


class UntrackedLaneMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dirs = {
            "prompts": ".aw/records/prompts",
            "comms": ".aw/records/comms",
        }
        pl = self.root / ".aw/records/prompts/local"
        pl.mkdir(parents=True)
        (pl / "notes.md").write_text("draft prompt\n", encoding="utf-8")
        cl = self.root / ".aw/records/comms/local/inbox"
        cl.mkdir(parents=True)
        (cl / "msg.md").write_text("hello\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_rename_preserves_contents(self):
        renamed = engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        self.assertIn(".aw/records/prompts/untracked", renamed)
        self.assertIn(".aw/records/comms/untracked", renamed)
        self.assertFalse((self.root / ".aw/records/prompts/local").exists())
        self.assertEqual(
            (self.root / ".aw/records/prompts/untracked/notes.md").read_text(),
            "draft prompt\n",
        )
        self.assertEqual(
            (self.root / ".aw/records/comms/untracked/inbox/msg.md").read_text(),
            "hello\n",
        )

    def test_idempotent(self):
        engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        again = engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        self.assertEqual(again, [])  # nothing left to rename

    def test_noop_when_no_local(self):
        empty = Path(self._tmp.name) / "sub"
        empty.mkdir()
        self.assertEqual(engine.migrate_local_lanes_to_untracked(empty, self.dirs), [])


if __name__ == "__main__":
    unittest.main()
