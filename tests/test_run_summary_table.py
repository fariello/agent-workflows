from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pytest

from agent_workflows import agy_runipd, oc_runipd, run_viewer, runner_shared
from agent_workflows.artifact_audit import ArtifactAudit
from agent_workflows.render_stream import (
    Palette,
    StreamTracker,
    _strip_ansi,
    format_duration,
    render_run_summary_table,
)
from agent_workflows.runner_shared import (
    LANDED_NA,
    LANDED_NO,
    LANDED_UNKNOWN,
    LANDED_YES,
    landed_verdict,
)
from agent_workflows.term import Term, strip_ansi

pytestmark = pytest.mark.core


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


# ======================================================================================
# Restored tests from backlog q86fxm (findings b1mx2w, source revision 19313eed^).
# Excludes test_both_hosts_and_the_summary_share_ONE_definition (structure pin per AGENTS.md).
# ======================================================================================


def test_format_duration() -> None:
    assert format_duration(None) == "0s"
    assert format_duration(-5) == "0s"
    assert format_duration(0) == "0s"
    assert format_duration(12) == "12s"
    assert format_duration(59) == "59s"
    assert format_duration(60) == "1m 00s"
    assert format_duration(84) == "1m 24s"
    assert format_duration(3600) == "1h 00m 00s"
    assert format_duration(3725) == "1h 02m 05s"
    assert format_duration(86400) == "1d 0h 00m 00s"
    assert format_duration(86400 + 3 * 3600 + 7 * 60 + 56) == "1d 3h 07m 56s"


def test_render_run_summary_table_borders_and_alignment() -> None:
    sample_state = {
        "run_id": "run-20260830T185011Z-2301181",
        "repo": "/tmp/test-repo",
        "created_at": "2026-08-30T18:50:11+00:00",
        "updated_at": "2026-08-30T18:54:23+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "jb6vys",
                "setid": "sessrot",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:50:12+00:00",
                        "ended_at": "2026-08-30T18:51:36+00:00",
                        "cost": 4.12,
                        "tokens": {
                            "total": 3200000,
                            "input": 45200,
                            "output": 32100,
                            "cache": 3100000,
                        },
                        "session_id": "ses_01",
                    }
                ],
            },
            {
                "position": 2,
                "id6": "bmh754",
                "setid": "detrun",
                "action": "review",
                "status": "reviewed",
                "verification_status": None,
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:51:37+00:00",
                        "ended_at": "2026-08-30T18:52:10+00:00",
                        "cost": 1.50,
                        "tokens": {
                            "total": 1800000,
                            "input": 22000,
                            "output": 15200,
                            "cache": 1700000,
                        },
                        "session_id": "ses_02",
                    }
                ],
            },
            {
                "position": 3,
                "id6": "a54m79",
                "setid": "detrun",
                "action": "execute",
                "status": "interrupted",
                "verification_status": None,
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:52:11+00:00",
                        "ended_at": "2026-08-30T18:52:21+00:00",
                        "cost": 0.85,
                        "tokens": {
                            "total": 1200000,
                            "input": 18000,
                            "output": 12000,
                            "cache": 1150000,
                        },
                        "session_id": "ses_03",
                    }
                ],
            },
            {
                "position": 4,
                "id6": "kaygwo",
                "setid": "detrun",
                "action": "execute",
                "status": "queued",
                "verification_status": None,
                "attempts": [],
            },
        ],
    }

    output = render_run_summary_table(sample_state, pal=Palette(False))
    lines = output.splitlines()

    border_lines = [
        lines[0],
        lines[4],
        lines[6],
        lines[11],
        lines[13],
    ]
    border_lens = [len(b) for b in border_lines]
    assert len(set(border_lens)) == 1, f"Border lengths differ: {border_lens}"
    table_width = border_lens[0]

    for idx, line in enumerate(lines[:14]):
        clean_line = _strip_ansi(line)
        assert (
            len(clean_line) == table_width
        ), f"Line {idx} width {len(clean_line)} != {table_width}"

    assert "AW RUN SUMMARY: run-20260830T185011Z-2301181" in output
    assert "jb6vys" in output
    assert "bmh754" in output
    assert "a54m79" in output
    assert "kaygwo" in output
    assert ".12" in output
    assert ".50" in output
    assert ".47" in output


def test_render_run_summary_table_ascii_borders() -> None:
    sample_state = {
        "run_id": "run-ascii-test",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "set1",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [],
            }
        ],
    }
    output = render_run_summary_table(
        sample_state, use_unicode=False, pal=Palette(False)
    )
    lines = output.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].endswith("+")
    assert "|" in lines[1]


def test_render_run_summary_table_diagnostics() -> None:
    sample_state = {
        "run_id": "run-diag-test",
        "queue": [
            {
                "position": 1,
                "id6": "dep001",
                "setid": "myset",
                "action": "execute",
                "status": "dependency-blocked",
                "unsatisfied_dependencies": ["base01"],
                "unsatisfied_dependency_reasons": {"base01": "spec approval required"},
            },
            {
                "position": 2,
                "id6": "err002",
                "setid": "myset",
                "action": "execute",
                "status": "failed-safely",
                "driver_error": "merge conflict in tests/test_main.py",
            },
            {
                "position": 3,
                "id6": "int003",
                "setid": "myset",
                "action": "execute",
                "status": "interrupted",
                "interrupt_reason": "stall_timeout",
            },
        ],
    }
    output = render_run_summary_table(sample_state, pal=Palette(False))
    assert "Diagnostics / Blocked Items:" in output
    assert "• dep001: dependency-blocked (base01 (spec approval required))" in output
    assert "• err002: failed-safely (merge conflict in tests/test_main.py)" in output
    assert "• int003: interrupted (stall_timeout)" in output


def test_render_run_summary_table_tracker_override() -> None:
    sample_state = {
        "run_id": "run-track-test",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "myset",
                "action": "execute",
                "status": "executed",
                "attempts": [
                    {
                        "started_at": "2026-08-30T10:00:00+00:00",
                        "ended_at": "2026-08-30T10:01:00+00:00",
                        "cost": 1.0,
                        "tokens": {
                            "total": 1000,
                            "input": 500,
                            "output": 500,
                            "cache": 0,
                        },
                    }
                ],
            }
        ],
    }
    tracker = StreamTracker()
    tracker.cost = 5.50
    tracker.input_tokens = 20000
    tracker.output_tokens = 10000
    tracker.cache_tokens = 50000

    output = render_run_summary_table(sample_state, tracker=tracker, pal=Palette(False))
    assert ".50" in output
    assert "80k" in output


def test_oc_runipd_print_status_renders_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run"
    run_dir.mkdir()
    state = {
        "run_id": "run-test-oc-status",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "test01",
                "setid": "set1",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    oc_runipd.print_status(run_dir)
    val = buf.getvalue()

    assert "AW RUN SUMMARY: run-test-oc-status" in val
    assert "test01" in val


def test_agy_runipd_print_status_renders_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_agy"
    run_dir.mkdir()
    state = {
        "run_id": "run-test-agy-status",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "agy001",
                "setid": "agyset",
                "action": "review",
                "status": "reviewed",
                "verification_status": None,
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    agy_runipd.print_status(run_dir)
    val = buf.getvalue()

    assert "AW RUN SUMMARY: run-test-agy-status" in val
    assert "agy001" in val


def test_oc_runipd_main_sigterm_and_sigint_handling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_sig"
    run_dir.mkdir()
    state = {
        "run_id": "run-sig-test",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:01:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "sig001",
                "setid": "sigset",
                "action": "execute",
                "status": "interrupted",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Test SIGTERM exit 143
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        oc_runipd, "run_queue", side_effect=KeyboardInterrupt("Terminated by SIGTERM")
    ), patch.object(oc_runipd, "locked_run"):
        rc = oc_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 143
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-sig-test" in val
        assert "TERMINATED (SIGTERM)" in val

    # Test SIGINT exit 130
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        oc_runipd, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
    ), patch.object(oc_runipd, "locked_run"):
        rc = oc_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 130
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-sig-test" in val
        assert "INTERRUPTED (SIGINT / Ctrl-C)" in val


def test_agy_runipd_main_sigterm_and_sigint_handling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_agy_sig"
    run_dir.mkdir()
    state = {
        "run_id": "run-agy-sig-test",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:01:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "agysig",
                "setid": "sigset",
                "action": "execute",
                "status": "interrupted",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Test SIGTERM exit 143
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        agy_runipd, "run_queue", side_effect=KeyboardInterrupt("Terminated by SIGTERM")
    ), patch.object(agy_runipd, "locked_run"):
        rc = agy_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 143
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-agy-sig-test" in val
        assert "TERMINATED (SIGTERM)" in val

    # Test SIGINT exit 130
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        agy_runipd, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
    ), patch.object(agy_runipd, "locked_run"):
        rc = agy_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 130
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-agy-sig-test" in val
        assert "INTERRUPTED (SIGINT / Ctrl-C)" in val


def test_resume_statusbar_starts_from_resume_time(tmp_path: Path) -> None:
    """Verify resume invocation sets _invocation_start_mono so statusbar does not count old time."""
    import time

    # Created 10 hours ago
    created_at = "2026-08-30T00:00:00+00:00"
    state = {
        "run_id": "run-resume-time-test",
        "repo": str(tmp_path),
        "created_at": created_at,
        "updated_at": "2026-08-30T00:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "testset",
                "action": "execute",
                "status": "queued",
                "attempts": [],
            }
        ],
    }
    run_dir = tmp_path / "run-resume-time-test"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    t_before = time.monotonic()
    # In run_queue, state["_invocation_start_mono"] is populated with current monotonic time
    captured_state = {}
    with patch.object(oc_runipd, "execute_item") as mock_exec:

        def fake_exec(r_dir, st, item, *args, **kwargs):
            captured_state["_invocation_start_mono"] = st.get("_invocation_start_mono")
            st["queue"][0]["status"] = "executed"
            (r_dir / "state.json").write_text(json.dumps(st), encoding="utf-8")

        mock_exec.side_effect = fake_exec
        rc = oc_runipd.run_queue(run_dir, retry_incomplete=False)
        assert rc == 0
        assert captured_state.get("_invocation_start_mono") is not None
        assert captured_state["_invocation_start_mono"] >= t_before


# ======================================================================================
# ys1dor: A RUN WHOSE WORK NEVER LANDED IS REPORTED AS `STRANDED`, IN RED, FROM THE RUN'S
# OWN RECORD.
#
# THE MEASURED DEFECT, from `run-20260908T140845Z-2489897`: a single-item run whose entire
# product was stranded printed `Outcome: COMPLETED   Spend: $32.83` at
# `Progress: 1/1 [##########] 100% (1 substantially-complete)` while NOTHING had been
# integrated; the work sat on `aw/lane/03ie04_attempt2` and the maintainer found it only by
# auditing `git worktree list` by hand. Eleven lanes were stranded that way on one unrelated
# red test, and plan `03ie04` was paid for twice ($16.59, then $32.83).
#
# THE MECHANISM WAS A MISSING QUESTION, not a wrong answer: the outcome was derived purely
# from per-item STATUS, and `substantially-complete` sits inside the success tuple, so a
# stranded run and a landed one were indistinguishable to it. The verdict, its reason and the
# recovery route were all recorded at the time and NO report read any of them.
#
# THE RULE THESE TESTS PIN, which is the whole reason this plan superseded `xtklpd`: the
# verdict comes from the run's OWN RECORD and never from the filesystem. `xtklpd` derived it
# from a filesystem audit, and its review measured the consequence - re-rendering a run that
# had since been recovered by hand reported `COMPLETED` again, so the summary silently
# REWROTE HISTORY.
# ======================================================================================

STRANDED_FIXTURE = (
    Path(__file__).parent / "fixtures" / "run_summary" / "stranded-run-state.json"
)


def _outcome_line(state: dict, *, color: bool = False) -> str:
    """The rendered `Outcome:` line, with ANSI intact when `color` is set."""
    rendered = render_run_summary_table(state, pal=Palette(color))
    for line in rendered.splitlines():
        if "Outcome:" in line:
            return line
    raise AssertionError("no Outcome line was rendered")


def _item(**overrides: object) -> dict:
    """One queue entry in the shape a real run persists (the measured item's field set)."""
    item: dict = {
        "position": 1,
        "id6": "03ie04",
        "setid": "depreview",
        "action": "execute",
        "status": "substantially-complete",
        "verification_status": "-",
        "attempts": [{"number": 1}],
    }
    item.update(overrides)
    return item


def _state(*items: dict, **extra: object) -> dict:
    state: dict = {"run_id": "run-ys1dor-test", "queue": list(items)}
    state.update(extra)
    return state


def _stranded_item(**overrides: object) -> dict:
    """The measured stranded shape: a SUCCESS-TUPLE status with a REFUSING signal."""
    base: dict = {
        "integration_signal": "suite-failed",
        "preserved_branch": "aw/lane/03ie04_attempt2",
        "preserved_worktree": "/home/user/repo/.aw/worktrees/03ie04_attempt2",
        "attempts": [
            {
                "number": 1,
                "integration_signal": "suite-failed",
                "integration_detail": (
                    "no verifier ran (validation off) and the driver-run suite did not "
                    "pass: suite FAILED with exit 1 in /home/user/repo (no summary "
                    "line parsed)"
                ),
            }
        ],
    }
    base.update(overrides)
    return _item(**base)


def test_a_stranded_run_is_not_reported_completed() -> None:
    """THE FALSIFIABLE CORE: the measured shape must not read as success.

    This is the case NOTHING else catches. The item kept a SUCCESS-TUPLE status
    (`substantially-complete`, which is legitimate and load-bearing: `reconcile_disposition`
    downgrades a claimed `executed` to it as an anti-fabrication guard) while its own
    `integration_signal` recorded that integration was REFUSED.
    """
    outcome = _strip_ansi(_outcome_line(_state(_stranded_item())))
    assert "COMPLETED" not in outcome, (
        "a run whose own record says integration was REFUSED must not report COMPLETED; "
        f"got {outcome!r}"
    )
    assert "STRANDED" in outcome


def test_a_landed_run_still_reports_completed_in_green() -> None:
    """The honest success case is untouched, including its color."""
    item = _item(status="executed", integration_signal="driver-run-suite")
    line = _outcome_line(_state(item), color=True)
    assert "COMPLETED" in _strip_ansi(line)
    assert "\033[32mCOMPLETED" in line, f"a landed run must stay GREEN; got {line!r}"


def test_a_review_only_run_with_no_integration_signal_key_reports_completed() -> None:
    """THE MOST LIKELY FALSE POSITIVE: absent must not read as refusing.

    A review-only run integrates nothing by design, so its item carries NO
    `integration_signal` key at all. Keying on falsiness rather than on PRESENCE would report
    every review run as stranded.
    """
    item = _item(action="review", status="reviewed")
    assert "integration_signal" not in item
    assert "COMPLETED" in _strip_ansi(_outcome_line(_state(item)))


def test_an_explicitly_empty_signal_is_treated_as_absent_not_as_a_refusal() -> None:
    """A present-but-empty value carries no verdict; inventing one would be a false alarm."""
    for empty in ("", None):
        item = _item(status="executed", integration_signal=empty)
        assert "COMPLETED" in _strip_ansi(
            _outcome_line(_state(item))
        ), f"integration_signal={empty!r} must behave as absent"


def test_a_partially_stranded_run_reports_stranded() -> None:
    """OQ-02, resolved as STRANDED: a partial strand is still a strand.

    A run where one item landed and one did not is a run with unintegrated work sitting in a
    lane, which is the fact an operator must act on. This precedence matches the `FAILED`
    branch's established shape in this same function (it fires on `any(...)`, not on all), and
    the recovery section names WHICH items are affected so the body still distinguishes
    "everything" from "one of two".
    """
    landed = _item(
        position=1, id6="aaaaaa", status="executed", integration_signal="verifier"
    )
    stranded = _stranded_item(position=2, id6="bbbbbb")
    outcome = _strip_ansi(_outcome_line(_state(landed, stranded)))
    assert "STRANDED" in outcome
    assert "COMPLETED" not in outcome


def test_an_unknown_future_signal_reads_as_a_refusal_not_as_success() -> None:
    """THE PROPERTY THE DESIGN EXISTS TO GUARANTEE, and why EARNED is the enumerated set.

    The renderer tests for the two EARNED values and treats every other non-empty signal as a
    refusal, so a signal added later fails SAFE by construction. Enumerating the three REFUSAL
    reasons instead would make each new signal read as landed until somebody remembered to
    extend the list - the same miss class as the `integration-blocked` allowlist that once
    rendered nothing at all.
    """
    item = _stranded_item(integration_signal="some-refusal-invented-in-2027")
    assert "STRANDED" in _strip_ansi(_outcome_line(_state(item)))


def test_an_integration_blocked_status_still_reports_failed() -> None:
    """THE REGRESSION THIS CHANGE COULD HAVE SHIPPED, so it gets its own test.

    The outcome block ALREADY had a `FAILED` branch firing on `("failed-safely",
    "integration-blocked", "merge-refused")`, and an `integration-blocked` item ALSO carries a
    refusing `integration_signal`. An implementation that tested the signal BEFORE the status
    would have RELABELLED that existing outcome to `STRANDED`: a regression dressed as the
    feature. The landing question is therefore asked LAST, inside the success branch only.
    """
    item = _stranded_item(status="merge-needs-human")
    outcome = _strip_ansi(_outcome_line(_state(item)))
    assert (
        "FAILED" in outcome
    ), f"expected the pre-existing FAILED word; got {outcome!r}"
    assert "STRANDED" not in outcome


def test_an_exit_reason_still_short_circuits_the_whole_outcome_block() -> None:
    """The `exit_reason` passthrough is the FIRST branch and must keep winning.

    A stranded run that ALSO exited on a signal keeps the exit wording: that is what the
    operator pressed Ctrl-C about, and hijacking it would hide the interruption.
    """
    line = _strip_ansi(
        render_run_summary_table(
            _state(_stranded_item()),
            pal=Palette(False),
            exit_reason="INTERRUPTED (SIGINT / Ctrl-C)",
        ).splitlines()[2]
    )
    assert "INTERRUPTED (SIGINT / Ctrl-C)" in line
    assert "STRANDED" not in line


def test_a_refusal_released_by_the_agents_answer_is_not_stranded() -> None:
    """gatewire-01's rung, which the measured incident predates and which must not false-alarm.

    When an agent adjudicates a failing suite and its answer RELEASES the gate, the run
    integrates and the item reaches `executed`, yet `integration_signal` KEEPS its refusing
    value because it records what the SUITE said. Only `integration_released_by_answer` records
    the override, so ignoring it would report a LANDED run as stranded.
    """
    item = _stranded_item(
        status="executed",
        integration_released_by_answer="not-mine",
    )
    assert "COMPLETED" in _strip_ansi(_outcome_line(_state(item)))


def test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step() -> (
    None
):
    """E-03: an alarm an operator cannot ACT on trains them to ignore it."""
    rendered = _strip_ansi(
        render_run_summary_table(_state(_stranded_item()), pal=Palette(False))
    )
    assert "STRANDED WORK - NOT IN YOUR PROJECT:" in rendered
    assert "aw/lane/03ie04_attempt2" in rendered, "the preserved branch must be named"
    assert "suite-failed" in rendered, "the refusal reason must be named"
    assert (
        "git log HEAD..aw/lane/03ie04_attempt2" in rendered
    ), "state the concrete next step"
    assert "Do NOT delete the branch" in rendered


def test_the_recovery_section_prints_NO_absolute_path() -> None:
    """THE ONE WAY THIS CHANGE COULD DO REAL HARM, measured rather than supposed.

    `preserved_worktree` is an absolute path under the maintainer's home directory, and
    `integration_detail`'s recorded text embeds the repository's absolute path too. The
    end-of-run summary is the most-copied output in the product (an operator pastes it into an
    issue, a chat, or a plan's `Observed evidence`), so a leak here is a leak everywhere.
    """
    rendered = _strip_ansi(
        render_run_summary_table(_state(_stranded_item()), pal=Palette(False))
    )
    assert (
        "/home/" not in rendered
    ), f"an absolute home path reached the render:\n{rendered}"
    assert "/home/user/repo/.aw/worktrees" not in rendered
    assert (
        "preserved_worktree" not in rendered
    ), "the worktree field must not be printed at all"
    # The useful part of the reason SURVIVES the redaction rather than the line being dropped.
    assert "the driver-run suite did not pass" in rendered


def test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated() -> None:
    """F-10: `integration_detail` is on the ATTEMPT, not the item.

    Measured on the real record: the item's keys include `integration_signal`,
    `preserved_branch` and `preserved_worktree` but NO `integration_detail`; both drivers write
    it onto `attempt`. An item with no attempts (or a record frozen by an older driver) must
    still render rather than raise.
    """
    from agent_workflows import render_stream

    with_attempt = _stranded_item()
    assert "integration_detail" not in with_attempt
    assert render_stream.integration_refusal_detail(with_attempt)

    no_attempts = _stranded_item(attempts=[])
    assert render_stream.integration_refusal_detail(no_attempts) is None
    rendered = _strip_ansi(
        render_run_summary_table(_state(no_attempts), pal=Palette(False))
    )
    assert (
        "STRANDED WORK" in rendered
    ), "an item with no attempts must still be reported"
    assert "aw/lane/03ie04_attempt2" in rendered


def test_an_item_with_no_preserved_branch_still_gets_an_actionable_line() -> None:
    """A refusal recorded without a branch is still a strand, and still needs a next step."""
    item = _stranded_item()
    item.pop("preserved_branch")
    rendered = _strip_ansi(render_run_summary_table(_state(item), pal=Palette(False)))
    assert "STRANDED" in rendered
    assert "no branch recorded" in rendered
    assert "aw attention" in rendered


def test_the_item_table_gains_NO_column() -> None:
    """E-03 adds a SECTION, never a table column: the column contract is unchanged.

    Compared by COLUMN SET rather than byte width, because the table already auto-sizes each
    column to its widest cell, so `substantially-complete` legitimately makes the `Status`
    column wider than `executed` does at HEAD too. The contract this pins is WHICH columns
    exist and in what order; the byte-identity of a like-for-like render is demonstrated
    against pre-change code in the plan's V-03 evidence.
    """
    landed = _item(status="executed", integration_signal="driver-run-suite")
    stranded = _stranded_item()
    expected = [
        "Run",
        "Pos",
        "ID6",
        "Set",
        "Action",
        "Status",
        "Verify",
        "Duration",
        "Spend",
        "Tok tot",
        "Tok in",
        "Tok out",
        "Tok cache",
    ]
    for state in (_state(landed), _state(stranded)):
        header = render_run_summary_table(state, pal=Palette(False)).splitlines()[5]
        cells = [c.strip() for c in header.strip("│").split("│")]
        assert cells == expected, f"the table's column contract changed: {cells}"

    # The stranded render differs from the clean one ONLY by appended lines: every line of the
    # box itself is unchanged in COUNT, so nothing was inserted into the table.
    clean = render_run_summary_table(_state(landed), pal=Palette(False)).splitlines()
    strand = render_run_summary_table(_state(stranded), pal=Palette(False)).splitlines()
    assert len(strand) > len(clean), "the stranded render must append a section"
    assert len([ln for ln in clean if ln.startswith("│")]) == len(
        [ln for ln in strand if ln.startswith("│")]
    ), "a row or banner line was added to the box itself"


def test_the_earned_signal_constants_match_the_runners_definitions() -> None:
    """The renderer MIRRORS two producer constants; this is what stops the copy going stale.

    `render_stream` is a LEAF: it imports no first-party module, and `runner_shared` imports
    FROM it at module level, so reading `INTEGRATION_EARNED_BY_*` from its home would be a
    circular import. The copy is therefore deliberate, and cross-checked here instead.
    """
    from agent_workflows import render_stream
    from agent_workflows import runner_shared

    assert render_stream.INTEGRATION_EARNED_SIGNALS == frozenset(
        {
            runner_shared.INTEGRATION_EARNED_BY_VERIFIER,
            runner_shared.INTEGRATION_EARNED_BY_SUITE,
        }
    ), (
        "the renderer's mirrored EARNED signals drifted from the producer's; update "
        "INTEGRATION_EARNED_SIGNALS (and note that an unknown value reads as a REFUSAL)"
    )
    # And the runners' REFUSAL values are all on the refusal side, by construction rather than
    # by enumeration.
    for refused in (
        runner_shared.INTEGRATION_REFUSED_VERIFIER_DECLINED,
        runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
        runner_shared.INTEGRATION_REFUSED_NO_SIGNAL,
    ):
        assert render_stream.integration_was_refused(
            {"integration_signal": refused}
        ), f"{refused!r} must read as a refusal"


def test_the_stranded_word_is_the_same_one_the_cross_tree_view_uses() -> None:
    """One condition, one vocabulary: `aw attention` and the run summary must not diverge."""
    from agent_workflows import render_stream
    from agent_workflows import runner_shared

    assert render_stream.STRANDED_OUTCOME == runner_shared.LANE_STRANDED


# `test_render_stream_still_imports_no_first_party_module` WAS DELETED HERE, DELIBERATELY, BY THE
# MERGE OF lifeglyph `qdd5jq`. It asserted that `render_stream` imports NO first-party module at all,
# which spec `uonrjg` R10.3 makes impossible: the lifecycle rendering must consume the shared
# resolver, which lives in `lifecycle_style` with its rendering boundary in `term`.
#
# THE GUARD WAS NOT DROPPED, IT MOVED AND GOT STRONGER:
# `tests/test_refusal_surfacing.py::test_render_stream_imports_no_first_party_module_that_could_cycle`
# now allows exactly `{lifecycle_style, term}` and walks the TRANSITIVE CLOSURE of every import in
# those modules (including function-local ones) to prove the closure reaches neither `render_stream`
# nor `runner_shared` nor either driver. A THIRD first-party import still fails.
#
# RECORDED RATHER THAN SILENTLY REMOVED because the lane deleted this function while main still had
# it, so the merge RESURRECTED a test whose premise its own change had retired; a future reader
# seeing the absence needs to know the protection survived.


def test_the_recovered_run_fixture_STILL_reports_stranded() -> None:
    """E-05: THE SHARPEST TEST OF THE DIFFERENCE between this design and the rejected one.

    `run-20260908T140845Z-2489897` (plan `03ie04`) was stranded, and has SINCE been recovered
    by hand: `03ie04` now sits in `.aw/records/plans/executed/`. A filesystem-derived summary
    therefore reports it CLEAN today - measured on `xtklpd`'s approach, which is why that plan
    was superseded rather than revised. Because the verdict here comes from the run's own
    durable record, re-rendering it says STRANDED forever, which is what a historical report
    must do.

    ASSERTED AGAINST A COMMITTED REDACTED FIXTURE, not the live record: `.aw/records/runs/` is
    GITIGNORED, so a test bound to it would fail in every other checkout and in every clean
    worktree.
    """
    state = json.loads(STRANDED_FIXTURE.read_text(encoding="utf-8"))
    rendered = render_run_summary_table(state, pal=Palette(False))
    plain = _strip_ansi(rendered)
    assert "STRANDED" in plain
    assert "COMPLETED" not in plain
    # The status that misled the outcome is still shown honestly in the table.
    assert "substantially-complete" in plain
    # The recovery route is present and leaks nothing.
    assert "aw/lane/03ie04_attempt2" in plain
    assert "/home/" not in plain, f"the fixture's absolute paths leaked:\n{plain}"


def test_the_committed_fixture_is_tracked_and_not_gitignored() -> None:
    """Guards the F-13 trap: a fixture under a gitignored path would pass only here."""
    import subprocess

    assert STRANDED_FIXTURE.is_file()
    rc = subprocess.run(
        ["git", "check-ignore", "-q", str(STRANDED_FIXTURE)],
        capture_output=True,
    ).returncode
    assert rc != 0, (
        "the stranded fixture is GITIGNORED, so this suite would pass only in this checkout; "
        "commit it somewhere tracked"
    )


# ==================================================================================================
# progdenom: the progress fraction counts DISPATCHABLE WORK, not queue length
# ==================================================================================================
#
# THE MAINTAINER'S STATEMENT OF THE BUG, quoted because it is the specification: running a 5-member
# and a 6-member Set with 3 and 2 members already executed "will start counting at 5/11 instead of
# 0/6. The run will not run the 5 that are executed and therefore it MUST NOT count them in the
# progress."
#
# MEASURED on live run `run-20260922T003657Z-1022108` before the fix: 62 queue entries of which TEN
# arrived `initial_status: executed` and TWO arrived frozen `reviewed`, so the runner announced
# `13/62` when it had performed 1 item of 50 it could ever dispatch.


def _q(**kw):
    """One queue entry with the two fields the predicate reads."""
    entry = {"id6": kw.pop("id6", "aaaaaa")}
    entry.update(kw)
    return entry


def test_an_already_executed_set_member_is_not_dispatchable_work() -> None:
    """The core discrimination: `initial_status` is what says "this arrived done"."""
    from agent_workflows.render_stream import item_is_dispatchable_work

    assert not item_is_dispatchable_work(
        _q(initial_status="executed", status="executed")
    )
    # An item that this run EXECUTED is still work: it arrived approved and was dispatched.
    assert item_is_dispatchable_work(
        _q(initial_status="approved", status="executed", attempts=[{"n": 1}])
    )
    # The ordinary pending case.
    assert item_is_dispatchable_work(_q(initial_status="approved", status="queued"))


def test_a_frozen_reviewed_entry_is_not_dispatchable_work() -> None:
    """It is never dispatched, so counting it promises a turn that cannot happen."""
    from agent_workflows.render_stream import item_is_dispatchable_work

    assert not item_is_dispatchable_work(
        _q(initial_status="reviewed", status="reviewed")
    )
    # But an item whose plan was reviewed and which HAS attempts was dispatched, so it counts.
    assert item_is_dispatchable_work(
        _q(initial_status="reviewed", status="reviewed", attempts=[{"n": 1}])
    )


def test_the_maintainers_exact_scenario_counts_zero_of_six() -> None:
    """setA 5 members (3 executed) + setB 6 members (2 executed) must read 0/6, never 5/11."""
    from agent_workflows.render_stream import (
        dispatchable_work_total,
        item_is_dispatchable_work,
    )

    queue = (
        [
            _q(id6=f"a{i}", initial_status="executed", status="executed")
            for i in range(3)
        ]
        + [
            _q(id6=f"a{i}", initial_status="approved", status="queued")
            for i in range(3, 5)
        ]
        + [
            _q(id6=f"b{i}", initial_status="executed", status="executed")
            for i in range(2)
        ]
        + [
            _q(id6=f"b{i}", initial_status="approved", status="queued")
            for i in range(2, 6)
        ]
    )
    assert len(queue) == 11, "fixture must reproduce the stated 5 + 6 shape"
    assert dispatchable_work_total(queue) == 6

    # BOTH HALVES of the fraction must exclude the same entries, which is the half that made the
    # old number look plausible: a pre-executed entry inflated the numerator too, because its
    # status is not `queued`.
    numerator = sum(
        1
        for i in queue
        if i.get("status") not in ("queued", "not-attempted")
        and item_is_dispatchable_work(i)
    )
    assert numerator == 0, "a run that has performed nothing must open at 0"


def test_the_denominator_never_divides_by_zero() -> None:
    """A queue with nothing dispatchable must not crash the progress bar."""
    from agent_workflows.render_stream import dispatchable_work_total

    assert dispatchable_work_total([]) == 0
    all_done = [_q(id6="x", initial_status="executed", status="executed")]
    assert dispatchable_work_total(all_done) == 1, (
        "a non-empty queue with nothing dispatchable must floor at 1 so a caller dividing by it "
        "cannot raise; the honest 'nothing to do' signal is the status counts, not a crash"
    )


def test_the_rendered_progress_line_excludes_pre_executed_members() -> None:
    """End to end through the real renderer, not just the predicate."""
    queue = [
        _q(id6="done01", setid="setA", initial_status="executed", status="executed"),
        _q(id6="done02", setid="setA", initial_status="executed", status="executed"),
        _q(id6="work01", setid="setA", initial_status="approved", status="queued"),
        _q(id6="work02", setid="setA", initial_status="approved", status="queued"),
    ]
    out = _strip_ansi(
        render_run_summary_table(
            {"run_id": "run-progdenom", "queue": queue, "driver": "oc"},
            pal=Palette(enabled=False),
        )
    )
    assert "0/2" in out, (
        "the progress fraction must count only the two dispatchable items; got:\n" + out
    )
    assert "0/4" not in out and "2/4" not in out, (
        "queue length must not appear as the denominator:\n" + out
    )
    # The pre-executed members are still LISTED: excluded from the count, not hidden.
    assert "done01" in out and "done02" in out, (
        "an already-executed Set member is legitimate provenance and must still be shown:\n"
        + out
    )


def test_the_shutdown_report_prints_the_runs_pointer_exactly_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """E-03: Assert on emit_shutdown_report output and verify its idempotence."""
    saved_state = dict(runner_shared._SIGNAL_REPORT_STATE)
    saved_done = runner_shared._SIGNAL_REPORT_DONE.is_set()
    try:
        runner_shared._SIGNAL_REPORT_DONE.clear()
        runner_shared.register_signal_report(
            tmp_path, {"run_id": "run-shut01", "queue": []}
        )
        runner_shared.emit_shutdown_report()
        runner_shared.emit_shutdown_report()
        captured = capsys.readouterr()
        expected = "Run `aw runs run-shut01` for more info."
        assert captured.out.count(expected) == 1
        assert expected in captured.out
        assert captured.err == ""
    finally:
        runner_shared._SIGNAL_REPORT_STATE.clear()
        runner_shared._SIGNAL_REPORT_STATE.update(saved_state)
        if saved_done:
            runner_shared._SIGNAL_REPORT_DONE.set()
        else:
            runner_shared._SIGNAL_REPORT_DONE.clear()
