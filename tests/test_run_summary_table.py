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
        self.assertIn("Item", table_full)
        self.assertIn("Action", table_full)
        self.assertIn("Attempts", table_full)
        self.assertIn("Elapsed", table_full)
        self.assertIn("Cost", table_full)
        self.assertIn("Total Tok", table_full)
        self.assertIn("Verified", table_full)
        self.assertIn("Issue", table_full)

        # Short 6-column variant
        table_short = run_viewer.render_steps_table(
            steps, term, short=True, repo_root=self.root
        )
        self.assertIn("Status", table_short)
        self.assertIn("Landed", table_short)
        self.assertIn("Item", table_short)
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
        lines = [line for line in plain.splitlines() if "│" in line]
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
