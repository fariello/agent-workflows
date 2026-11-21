"""Behavioral tests for attention board handling of info-only superseded lanes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import attention as att
from agent_workflows import runner_shared as rs
from agent_workflows import term as T


class SupersededLaneBoardUxTests(unittest.TestCase):
    """Info-only superseded lanes must not trigger VIEW INVALID or suggest integrating husks."""

    def test_info_only_superseded_drift_does_not_mark_human_board_invalid(self) -> None:
        items = [
            att.Item(
                id="abc123",
                path=".aw/records/plans/pending/20261121-demo-01-abc123-item.ipd.md",
                tree="plans",
                native_status="to-review",
                attention_class="ready",
                gate=None,
                last_history_at="2026-11-21",
            )
        ]
        superseded = core.Drift(
            "aw/lane/old123",
            att.LANE_SUPERSEDED_RULE,
            "SUPERSEDED lane; plan old123: commits not in HEAD; plan terminal. Prune worktree + branch.",
            severity="info",
        )

        # Both the table renderer (default colored/compact) and the section renderer must
        # agree with render_json/drift_exit_code: no VIEW INVALID banner for info-only drift.
        table_out = att.render_table(items, [superseded], term=T.Term(color=False))
        self.assertNotIn("VIEW INVALID", table_out)
        self.assertNotIn("attention.lane-superseded", table_out)

        section_out = att.render_board(items, [superseded], term=T.Term(color=False))
        self.assertNotIn("VIEW INVALID", section_out)

        # Superseded lanes are still surfaced cleanly in the dedicated bottom section.
        lane_sec = att.render_stranded_lane_section([superseded])
        self.assertIn("SUPERSEDED LANES (1)", lane_sec)
        self.assertIn("Prune worktree + branch.", lane_sec)

    def test_error_drift_still_marks_human_board_invalid_and_omits_info_from_violation_block(
        self,
    ) -> None:
        items: list[att.Item] = []
        superseded = core.Drift(
            "aw/lane/old123",
            att.LANE_SUPERSEDED_RULE,
            "SUPERSEDED lane; plan old123",
            severity="info",
        )
        stranded = core.Drift(
            "aw/lane/bad456",
            att.LANE_STRANDED_RULE,
            "STRANDED lane; plan bad456: Recover it with `aw oc integrate bad456`.",
            severity="error",
        )

        table_out = att.render_table(
            items, [superseded, stranded], term=T.Term(color=False)
        )
        self.assertIn("VIEW INVALID", table_out)
        self.assertIn("attention.lane-stranded", table_out)
        self.assertNotIn("attention.lane-superseded", table_out)

        section_out = att.render_board(
            items, [superseded, stranded], term=T.Term(color=False)
        )
        self.assertIn("VIEW INVALID", section_out)
        self.assertIn("attention.lane-stranded", section_out)
        self.assertNotIn("attention.lane-superseded", section_out)

    def test_stranded_lane_drift_emits_prune_remedy_for_superseded_and_integrate_for_stranded(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            run_dir = repo / ".aw" / "records" / "runs" / "run-20261121T000000Z-1"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(
                json.dumps({"run_id": "run-20261121T000000Z-1", "queue": []}),
                encoding="utf-8",
            )
            wt_sup = repo / ".aw" / "worktrees" / "sup111"
            wt_sup.mkdir(parents=True)
            fake_records = [
                {
                    "branch": "aw/lane/sup111",
                    "lane_id": "sup111",
                    "id6": "sup111",
                    "lane_state": rs.LANE_SUPERSEDED,
                    "commits_ahead": 2,
                    "dirty": False,
                    "worktree": str(wt_sup),
                    "run_id": "run-20261121T000000Z-1",
                    "why": "commits not in HEAD; plan terminal; work landed by later attempt; prune superseded husk, not work at risk",
                },
                {
                    "branch": "aw/lane/sup222",
                    "lane_id": "sup222",
                    "id6": "sup222",
                    "lane_state": rs.LANE_SUPERSEDED,
                    "commits_ahead": 1,
                    "dirty": False,
                    "worktree": str(repo / ".aw" / "worktrees" / "sup222"),
                    "run_id": "run-20261121T000000Z-1",
                    "why": "commits not in HEAD; plan terminal; work landed by later attempt; prune superseded husk, not work at risk",
                },
                {
                    "branch": "aw/lane/str333",
                    "lane_id": "str333",
                    "id6": "str333",
                    "lane_state": rs.LANE_STRANDED,
                    "commits_ahead": 1,
                    "dirty": False,
                    "worktree": "",
                    "run_id": "run-20261121T000000Z-1",
                    "why": "commits not in HEAD",
                },
            ]
            with (
                mock.patch.object(
                    rs, "stranded_lane_records", return_value=fake_records
                ),
                mock.patch(
                    "agent_workflows.run_viewer.discover_run_dirs",
                    return_value=[run_dir],
                ),
                mock.patch(
                    "agent_workflows.run_viewer.driver_holder_state",
                    return_value="absent",
                ),
            ):
                drifts = att.stranded_lane_drift(repo)

        by_loc = {d.location: d for d in drifts}
        self.assertEqual(by_loc["aw/lane/sup111"].severity, "info")
        self.assertIn("Prune worktree + branch.", by_loc["aw/lane/sup111"].detail)
        self.assertNotIn("aw oc integrate", by_loc["aw/lane/sup111"].detail)

        self.assertEqual(by_loc["aw/lane/sup222"].severity, "info")
        self.assertIn("Prune branch.", by_loc["aw/lane/sup222"].detail)
        self.assertNotIn("aw oc integrate", by_loc["aw/lane/sup222"].detail)

        self.assertEqual(by_loc["aw/lane/str333"].severity, "error")
        self.assertIn("aw oc integrate str333", by_loc["aw/lane/str333"].detail)


if __name__ == "__main__":
    unittest.main()
