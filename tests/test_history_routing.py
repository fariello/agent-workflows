"""Tests for awhistory Order 02: status writers append to the global sidecar and slim inline history
to the latest one record, while attention `last_history_at` still resolves from that line."""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from agent_workflows import backlog, record_history, specs
from agent_workflows import attention_contract as A


class HistoryRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_backlog_set_appends_sidecar_and_slims_inline(self) -> None:
        d = self.root / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True)
        item = d / "20260101-demo-01-aaa111-x.backlog.md"
        item.write_text(
            "- Id: aaa111\n- Status: open\n- Priority: medium\n- Kind: chore\n- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n- 2026-01-01 created (aw backlog): x\n- 2026-01-02 set (aw backlog): older\n",
            encoding="utf-8",
        )
        args = types.SimpleNamespace(
            path=str(item),
            dir=str(self.root),
            status="done",
            message="finished",
            apply=True,
        )
        rc = backlog.run_set(args)
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        text = moved.read_text(encoding="utf-8")
        # exactly one history bullet in the ## Workflow history section (the new one)
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(len(inline), 1)
        self.assertIn("finished", inline[0])
        # sidecar has a record for aaa111
        recs = record_history.read_for(self.root, "aaa111")
        self.assertTrue(any("finished" in r["message"] for r in recs))

    def test_attention_last_history_at_preserved(self) -> None:
        # a slimmed file still yields a last_history_at from its single inline record.
        lines = "## Workflow history\n- 2026-05-05 set (aw backlog): only\n".split("\n")
        self.assertEqual(A.last_history_at(lines), "2026-05-05")

    def test_specs_slims_inline(self) -> None:
        # specs have no id6 so no sidecar append, but inline history slims to latest-one.
        out = specs._append_history(
            "# S\n\n- Status: draft\n\n## Workflow history\n- 2026-01-01 draft (t): a\n- 2026-01-02 to-review (t): b\n".split(
                "\n"
            ),
            "- 2026-01-03 reviewed (t): c",
        )
        text = "\n".join(out)
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(inline, ["- 2026-01-03 reviewed (t): c"])


if __name__ == "__main__":
    unittest.main()
