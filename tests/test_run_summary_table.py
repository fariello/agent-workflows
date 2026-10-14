"""Unit tests for the Landed column in run summary table (statusvocab 9x7otz).

Validates:
1. `landed_verdict` predicate maps directories to yes / no / n/a / unknown strictly from disk.
2. Monthly shards (`executed/YYYYMM/`) climb to `executed` and return `yes`.
3. Independence from agent self-report / recorded status (F-01 counterexamples).
4. `render_steps_table` column structure in both short (6-column) and full (10-column) modes.
5. Plain word formatting under `NO_COLOR` and ANSI styling under color mode.
6. Tolerant handling of historical runs, moved plans, and missing plans (`unknown`).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from agent_workflows import run_viewer
from agent_workflows.artifact_audit import ArtifactAudit
from agent_workflows.runner_shared import (
    LANDED_NA,
    LANDED_NO,
    LANDED_UNKNOWN,
    LANDED_YES,
    landed_verdict,
)
from agent_workflows.term import Term, strip_ansi


class LandedVerdictPredicateTests(TestCase):
    def test_pure_directory_name_mapping(self):
        self.assertEqual(landed_verdict("executed"), LANDED_YES)
        self.assertEqual(landed_verdict("pending"), LANDED_NO)
        self.assertEqual(landed_verdict("superseded"), LANDED_NA)
        self.assertEqual(landed_verdict("not-executed"), LANDED_NA)
        self.assertEqual(landed_verdict("reusable"), LANDED_NA)
        self.assertEqual(landed_verdict("unknown"), LANDED_UNKNOWN)
        self.assertEqual(landed_verdict(""), LANDED_UNKNOWN)
        self.assertEqual(landed_verdict(None), LANDED_UNKNOWN)
        self.assertEqual(landed_verdict(12345), LANDED_UNKNOWN)
        self.assertEqual(landed_verdict("draft"), LANDED_UNKNOWN)

    def test_path_and_monthly_shard_climbing(self):
        # Direct executed plan
        p1 = Path(".aw/records/plans/executed/20260901-test-01-abc123-slug.ipd.md")
        self.assertEqual(landed_verdict(p1), LANDED_YES)

        # Monthly sharded executed plan (executed/YYYYMM/)
        p2 = Path(
            ".aw/records/plans/executed/202608/20260815-test-01-abc123-slug.ipd.md"
        )
        self.assertEqual(landed_verdict(p2), LANDED_YES)

        # Pending plan
        p3 = Path(".aw/records/plans/pending/20260901-test-01-abc123-slug.ipd.md")
        self.assertEqual(landed_verdict(p3), LANDED_NO)

        # Terminal non-executed plans
        p4 = Path(".aw/records/plans/superseded/20260901-test-01-abc123-slug.ipd.md")
        self.assertEqual(landed_verdict(p4), LANDED_NA)

        p5 = Path(
            ".aw/records/plans/superseded/202607/20260701-test-01-abc123-slug.ipd.md"
        )
        self.assertEqual(landed_verdict(p5), LANDED_NA)

        p6 = Path(".aw/records/plans/not-executed/20260901-test-01-abc123-slug.ipd.md")
        self.assertEqual(landed_verdict(p6), LANDED_NA)

        p7 = Path(".aw/records/plans/reusable/20260901-test-01-abc123-slug.ipd.md")
        self.assertEqual(landed_verdict(p7), LANDED_NA)

        # String paths
        self.assertEqual(
            landed_verdict(".aw/records/plans/executed/202608/20260815-test.ipd.md"),
            LANDED_YES,
        )
        self.assertEqual(
            landed_verdict(".aw/records/plans/pending/20260901-test.ipd.md"),
            LANDED_NO,
        )

    def test_artifact_audit_input_and_status_independence(self):
        # F-01 counterexamples: status is non-executed, but plan is in executed/
        audit_yeh7gc = ArtifactAudit(
            id6="yeh7gc",
            stem="20260920-set-01-yeh7gc",
            run_status="dependency-blocked",
            actual_path=Path(".aw/records/plans/executed/20260920-yeh7gc.ipd.md"),
            actual_dir="executed",
            expected_dir="pending",
        )
        self.assertEqual(landed_verdict(audit_yeh7gc), LANDED_YES)

        audit_m7gvuz = ArtifactAudit(
            id6="m7gvuz",
            stem="20260920-set-02-m7gvuz",
            run_status="failed-safely",
            actual_path=Path(".aw/records/plans/executed/20260920-m7gvuz.ipd.md"),
            actual_dir="executed",
            expected_dir="pending",
        )
        self.assertEqual(landed_verdict(audit_m7gvuz), LANDED_YES)

        audit_xdvglg = ArtifactAudit(
            id6="xdvglg",
            stem="20260920-set-03-xdvglg",
            run_status="substantially-complete",
            actual_path=Path(".aw/records/plans/executed/20260920-xdvglg.ipd.md"),
            actual_dir="executed",
            expected_dir="pending",
        )
        self.assertEqual(landed_verdict(audit_xdvglg), LANDED_YES)

        # Archived monthly shard in audit
        audit_archived = ArtifactAudit(
            id6="arch01",
            stem="20260801-set-01-arch01",
            run_status="executed",
            actual_path=Path(
                ".aw/records/plans/executed/202608/20260801-arch01.ipd.md"
            ),
            actual_dir="202608",
            expected_dir="executed",
        )
        self.assertEqual(landed_verdict(audit_archived), LANDED_YES)

        # Stranded plan: status says executed, but actual directory is pending
        audit_stranded = ArtifactAudit(
            id6="strnd1",
            stem="20260920-set-04-strnd1",
            run_status="executed",
            actual_path=Path(".aw/records/plans/pending/20260920-strnd1.ipd.md"),
            actual_dir="pending",
            expected_dir="executed",
        )
        self.assertEqual(landed_verdict(audit_stranded), LANDED_NO)

        # Superseded plan: nmlx47
        audit_superseded = ArtifactAudit(
            id6="nmlx47",
            stem="20260901-set-05-nmlx47",
            run_status="superseded",
            actual_path=Path(".aw/records/plans/superseded/20260901-nmlx47.ipd.md"),
            actual_dir="superseded",
            expected_dir="superseded",
        )
        self.assertEqual(landed_verdict(audit_superseded), LANDED_NA)

        # Missing plan
        audit_missing = ArtifactAudit(
            id6="miss01",
            stem="20260920-set-06-miss01",
            run_status="fail-gate",
            missing_entirely=True,
            expected_dir="pending",
        )
        self.assertEqual(landed_verdict(audit_missing), LANDED_UNKNOWN)


class RunSummaryTableRenderingTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Set up plans tree
        self.plans_dir = self.root / ".aw" / "records" / "plans"
        (self.plans_dir / "executed").mkdir(parents=True)
        (self.plans_dir / "pending").mkdir(parents=True)
        (self.plans_dir / "superseded").mkdir(parents=True)
        (self.plans_dir / "executed" / "202608").mkdir(parents=True)

        # Create physical plan files
        (
            self.plans_dir / "executed" / "20260920-test-01-yeh7gc-item.ipd.md"
        ).write_text("- Id: yeh7gc\n- Status: executed\n", encoding="utf-8")
        (
            self.plans_dir
            / "executed"
            / "202608"
            / "20260810-test-02-arch01-item.ipd.md"
        ).write_text("- Id: arch01\n- Status: executed\n", encoding="utf-8")
        (self.plans_dir / "pending" / "20260920-test-03-strnd1-item.ipd.md").write_text(
            "- Id: strnd1\n- Status: approved\n", encoding="utf-8"
        )
        (
            self.plans_dir / "superseded" / "20260901-test-04-nmlx47-item.ipd.md"
        ).write_text("- Id: nmlx47\n- Status: superseded\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_steps(self) -> list[run_viewer.StepSummary]:
        return [
            run_viewer.StepSummary(
                position=1,
                id6="yeh7gc",
                setid="test",
                action="execute",
                status="dependency-blocked",
                configured_file="",
                stem="20260920-test-01-yeh7gc",
                verification_status="verified",
                attempts_count=1,
                elapsed_str="01:23",
                cost=1.50,
                tokens={"total": 5000},
            ),
            run_viewer.StepSummary(
                position=2,
                id6="arch01",
                setid="test",
                action="execute",
                status="executed",
                configured_file="",
                stem="20260810-test-02-arch01",
                verification_status="verified",
                attempts_count=1,
                elapsed_str="02:10",
                cost=2.00,
                tokens={"total": 8000},
            ),
            run_viewer.StepSummary(
                position=3,
                id6="strnd1",
                setid="test",
                action="execute",
                status="fail-verify",
                configured_file="",
                stem="20260920-test-03-strnd1",
                verification_status="verify-failed",
                attempts_count=2,
                elapsed_str="00:45",
                cost=0.75,
                tokens={"total": 3000},
            ),
            run_viewer.StepSummary(
                position=4,
                id6="nmlx47",
                setid="test",
                action="execute",
                status="superseded",
                configured_file="",
                stem="20260901-test-04-nmlx47",
                verification_status=None,
                attempts_count=0,
            ),
            run_viewer.StepSummary(
                position=5,
                id6="miss01",
                setid="test",
                action="execute",
                status="fail-gate",
                configured_file="",
                stem="20260920-test-05-miss01",
                verification_status=None,
                attempts_count=1,
            ),
        ]

    def test_render_steps_table_headers_and_variants(self):
        steps = self._make_steps()
        term = Term(color=False)

        # Full 10-column variant
        table_full = run_viewer.render_steps_table(
            steps, term, short=False, repo_root=self.root
        )
        self.assertIn("Status", table_full)
        self.assertIn("Landed", table_full)
        self.assertIn("Date", table_full)
        self.assertIn("SetID", table_full)
        self.assertIn("N", table_full)
        self.assertIn("ID6", table_full)
        self.assertIn("Action", table_full)
        self.assertIn("Attempts", table_full)
        self.assertIn("Elapsed", table_full)
        self.assertIn("Cost", table_full)
        self.assertIn("Total Tok", table_full)
        self.assertIn("Verified", table_full)
        self.assertIn("Issue", table_full)

        # Short 9-column variant
        table_short = run_viewer.render_steps_table(
            steps, term, short=True, repo_root=self.root
        )
        self.assertIn("Status", table_short)
        self.assertIn("Landed", table_short)
        self.assertIn("Date", table_short)
        self.assertIn("SetID", table_short)
        self.assertIn("N", table_short)
        self.assertIn("ID6", table_short)
        self.assertIn("Action", table_short)
        self.assertIn("Verified", table_short)
        self.assertIn("Issue", table_short)
        self.assertNotIn("Attempts", table_short)
        self.assertNotIn("Elapsed", table_short)
        self.assertNotIn("Cost", table_short)
        self.assertNotIn("Total Tok", table_short)

    def test_landed_column_values_no_color(self):
        steps = self._make_steps()
        term = Term(color=False)
        table = run_viewer.render_steps_table(
            steps, term, short=True, repo_root=self.root
        )
        plain = strip_ansi(table)

        # Verify plain text words appear in rows
        lines = plain.splitlines()
        # Skip header and separator lines
        row_lines = [
            row_line for row_line in lines if any(s.id6 in row_line for s in steps)
        ]
        self.assertEqual(len(row_lines), 5)

        # Row 1 (yeh7gc): status fail-depend (canonical), Landed yes
        self.assertIn("yeh7gc", row_lines[0])
        self.assertIn("yes", row_lines[0])

        # Row 2 (arch01): status executed, Landed yes (climbed monthly shard)
        self.assertIn("arch01", row_lines[1])
        self.assertIn("yes", row_lines[1])

        # Row 3 (strnd1): status fail-verify, Landed no
        self.assertIn("strnd1", row_lines[2])
        self.assertIn("no", row_lines[2])

        # Row 4 (nmlx47): status superseded, Landed n/a
        self.assertIn("nmlx47", row_lines[3])
        self.assertIn("n/a", row_lines[3])

        # Row 5 (miss01): missing plan, Landed unknown
        self.assertIn("miss01", row_lines[4])
        self.assertIn("unknown", row_lines[4])

    def test_landed_column_values_with_color(self):
        steps = self._make_steps()
        term = Term(color=True)
        table = run_viewer.render_steps_table(
            steps, term, short=True, repo_root=self.root
        )

        # 46 green for "yes"
        self.assertIn("\033[38;5;46myes\033[0m", table)
        # 196 red for "no"
        self.assertIn("\033[38;5;196mno\033[0m", table)
        # 245 dimmed for "n/a"
        self.assertIn("\033[38;5;245mn/a\033[0m", table)
        # 214 yellow for "unknown"
        self.assertIn("\033[38;5;214munknown\033[0m", table)


class TestLaneWorktreePathsAndFailVerifyRefusal(TestCase):
    """Verify stream paths inside lane worktrees show actual .aw/worktrees/<lane>/... paths
    and fail-verify outcomes explain WHY the item was placed in fail-verify."""

    def test_stream_events_render_actual_lane_worktree_path_while_tracker_dedupes_logical_path(
        self,
    ):
        import json
        from agent_workflows.agy_runipd import render_agy_event
        from agent_workflows.render_stream import Palette, StreamTracker, render_event

        repo_root = Path("/repo/project")
        lane_dir = repo_root / ".aw" / "worktrees" / "s4z5n8"
        rel_sub = ".aw/state/lane-submissions/run-20261014T004917Z-3785780/01-s4z5n8/attempt-1/outcomes/01-s4z5n8.json"
        abs_in_lane = str(lane_dir / rel_sub)
        expected_display = f".aw/worktrees/s4z5n8/{rel_sub}"

        pal = Palette(False)
        tracker = StreamTracker()

        # 1. Antigravity write_to_file with absolute path inside lane worktree
        agy_write_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "duration_seconds": 3.33,
                    "tool_info": {
                        "name": "write_to_file",
                        "parameters": {"TargetFile": abs_in_lane},
                    },
                },
            }
        )
        out_agy_abs = render_agy_event(
            agy_write_line,
            pal,
            repo_root=repo_root,
            work_dir=lane_dir,
            tracker=tracker,
        )
        self.assertIsNotNone(out_agy_abs)
        self.assertIn(expected_display, out_agy_abs)
        self.assertIn(rel_sub, tracker.modified_files)

        # 2. Antigravity replace_file_content with relative path inside lane worktree
        agy_edit_rel = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "duration_seconds": 2.29,
                    "tool_info": {
                        "name": "replace_file_content",
                        "parameters": {"TargetFile": rel_sub},
                    },
                },
            }
        )
        out_agy_rel = render_agy_event(
            agy_edit_rel,
            pal,
            repo_root=repo_root,
            work_dir=lane_dir,
            tracker=tracker,
        )
        self.assertIsNotNone(out_agy_rel)
        self.assertIn(expected_display, out_agy_rel)

        # 3. OpenCode write event with relative or absolute path inside lane worktree
        oc_write_line = json.dumps(
            {
                "type": "tool_use",
                "part": {
                    "tool": "write",
                    "state": {
                        "status": "completed",
                        "input": {"filePath": rel_sub, "content": "{\n}\n"},
                        "metadata": {"filepath": abs_in_lane, "exists": False},
                    },
                },
            }
        )
        out_oc = render_event(
            oc_write_line,
            pal,
            tracker=tracker,
            repo_root=repo_root,
            work_dir=lane_dir,
        )
        self.assertIsNotNone(out_oc)
        self.assertIn(expected_display, out_oc)

    def test_fail_verify_missing_disposition_surfaces_reason_and_remedy_across_summaries(
        self,
    ):
        from agent_workflows.render_stream import (
            Palette,
            explain_fail_verify_outcome,
            refusal_of_item,
            render_run_summary_table,
        )
        from agent_workflows.run_selection_policy import (
            render_disposition_summary,
            render_queue_dispositions,
        )

        run_id = "run-20261014T004917Z-3785780"
        item = {
            "position": 1,
            "id6": "s4z5n8",
            "setid": "cihealth",
            "action": "execute",
            "status": "fail-verify",
            "preserved_branch": "aw/lane/s4z5n8",
            "last_outcome": {"id6": "s4z5n8", "status": "executed"},
            "attempts": [
                {
                    "attempt": 1,
                    "started_at": "2026-10-14T00:49:17Z",
                    "ended_at": "2026-10-14T02:19:09Z",
                    "exit_code": 0,
                    "disposition": "fail-verify",
                    "worktree_branch": "aw/lane/s4z5n8",
                    "log": f"/tmp/repo/.aw/records/runs/{run_id}/sessions/01-s4z5n8-attempt1.jsonl",
                }
            ],
        }
        code, reason, remedy = explain_fail_verify_outcome(item, run_id=run_id)
        self.assertEqual(code, "outcome-missing-disposition")
        self.assertIn(
            f".aw/records/runs/{run_id}/outcomes/01-s4z5n8.json",
            reason,
        )
        self.assertIn("omitted required field 'disposition'", reason)
        self.assertIn("wrote 'status': 'executed' instead", reason)
        self.assertIn("aw/lane/s4z5n8", reason)
        self.assertIn("set a valid 'disposition'", remedy)

        # Even without an explicit item["refusal"], refusal_of_item synthesizes one for frozen runs
        refusal = refusal_of_item(item)
        self.assertIsNotNone(refusal)
        assert refusal is not None
        self.assertEqual(refusal.code, "outcome-missing-disposition")
        self.assertIn("omitted required field 'disposition'", refusal.reason)

        state = {
            "run_id": run_id,
            "created_at": "2026-10-14T00:49:17Z",
            "updated_at": "2026-10-14T02:19:09Z",
            "queue": [item],
        }
        table = render_run_summary_table(
            state, pal=Palette(False), driver_label="antigravity"
        )
        self.assertIn("Diagnostics / Blocked Items:", table)
        self.assertIn(
            "s4z5n8: fail-verify (outcome file .aw/records/runs/run-20261014T004917Z-3785780/outcomes/01-s4z5n8.json omitted required field 'disposition' (wrote 'status': 'executed' instead)",
            table,
        )
        self.assertIn("→ remedy: set a valid 'disposition'", table)

        q_lines = "\n".join(
            render_queue_dispositions([item], refusal_reader=refusal_of_item)
        )
        self.assertIn("omitted required field 'disposition'", q_lines)

        d_lines = "\n".join(
            render_disposition_summary([item], refusal_reader=refusal_of_item)
        )
        self.assertIn("outcome-missing-disposition", d_lines)
        self.assertIn("remedy: set a valid 'disposition'", d_lines)

    def test_explain_fail_verify_outcome_handles_missing_and_partial_outcomes(self):
        from agent_workflows.render_stream import explain_fail_verify_outcome

        missing_item = {
            "position": 2,
            "id6": "abc123",
            "status": "fail-verify",
            "preserved_branch": "aw/lane/abc123",
            "last_outcome": None,
        }
        code, reason, remedy = explain_fail_verify_outcome(
            missing_item, run_id="run-20261014T010000Z-1"
        )
        self.assertEqual(code, "outcome-missing")
        self.assertIn(
            ".aw/records/runs/run-20261014T010000Z-1/outcomes/02-abc123.json",
            reason,
        )
        self.assertIn("without writing a readable outcome file", reason)

        partial_item = {
            "position": 3,
            "id6": "def456",
            "status": "fail-verify",
            "last_outcome": {
                "disposition": "partial",
                "incomplete_requirements": ["E-02", "V-02"],
                "summary": "Stopped before completing E-02.",
                "recommended_next_action": "Finish E-02 on the preserved lane.",
            },
        }
        code_p, reason_p, remedy_p = explain_fail_verify_outcome(
            partial_item, run_id="run-20261014T010000Z-1"
        )
        self.assertEqual(code_p, "agent-reported-partial")
        self.assertIn("incomplete: E-02, V-02", reason_p)
        self.assertIn("Stopped before completing E-02.", reason_p)
        self.assertEqual(remedy_p, "Finish E-02 on the preserved lane.")
