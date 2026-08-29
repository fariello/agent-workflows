"""Unit tests for `agent_workflows.run_viewer` (aw runs / run viewer)."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase

from agent_workflows import cli, run_viewer
from agent_workflows.term import Term


class RunViewerTests(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_discover_run_dirs(self):
        runs = run_viewer.discover_run_dirs(Path("."))
        self.assertTrue(len(runs) > 0)
        self.assertTrue(all(r.is_dir() for r in runs))
        self.assertTrue(all(r.name.startswith("run-") for r in runs))

    def test_resolve_target_runs_empty(self):
        all_runs = run_viewer.discover_run_dirs(Path("."))
        resolved = run_viewer.resolve_target_runs([], Path("."))
        self.assertEqual(len(resolved), len(all_runs))

    def test_resolve_target_runs_by_substring_and_setid(self):
        resolved = run_viewer.resolve_target_runs(["2367239"], Path("."))
        self.assertEqual(len(resolved), 1)
        self.assertIn("2367239", resolved[0].name)

        # Match by setid
        resolved_set = run_viewer.resolve_target_runs(["runnernorm"], Path("."))
        self.assertTrue(len(resolved_set) >= 1)

    def test_load_run_summary_state_json(self):
        runs = run_viewer.resolve_target_runs(["2367239"], Path("."))
        self.assertEqual(len(runs), 1)
        summary = run_viewer.load_run_summary(runs[0], Path("."))
        self.assertIsNotNone(summary)
        self.assertEqual(summary.run_id, "run-20260827T212958Z-2367239")
        self.assertEqual(summary.driver, "OpenCode")
        self.assertIn("runnernorm", summary.setids)
        self.assertEqual(len(summary.steps), 3)

        s1 = summary.steps[0]
        self.assertEqual(s1.id6, "ryvoi5")
        self.assertEqual(s1.status, "partial")
        self.assertEqual(s1.disposition, "dependency-blocked")
        self.assertTrue(len(s1.incomplete_requirements) > 0)

        s2 = summary.steps[1]
        self.assertEqual(s2.id6, "dg28i9")
        self.assertEqual(s2.status, "substantially-complete")
        self.assertEqual(s2.verification_status, "verified")

    def test_load_run_summary_fallback_report_md(self, tmp_path_factory=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            run_d = Path(td) / "run-20260825T000000Z-999999"
            run_d.mkdir()
            report = run_d / "execution-report.md"
            report.write_text(
                "# Execution Report: run-20260825T000000Z-999999\n\n"
                "- Created: 2026-08-25T00:00:00+00:00\n"
                "- Updated: 2026-08-25T01:00:00+00:00\n"
                "- Selectors: `testset`\n\n"
                "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |\n"
                "|---:|---|---|---|---|---|---:|---|\n"
                "| 1 | `abc123` | `testset` | `execute` | executed | verified | 1 | `ses_123` |\n",
                encoding="utf-8",
            )
            summary = run_viewer.load_run_summary(run_d, Path("."))
            self.assertIsNotNone(summary)
            self.assertEqual(summary.run_id, "run-20260825T000000Z-999999")
            self.assertEqual(len(summary.steps), 1)
            self.assertEqual(summary.steps[0].id6, "abc123")
            self.assertEqual(summary.steps[0].status, "executed")
            self.assertEqual(summary.steps[0].verification_status, "verified")

    def test_format_step_line(self):
        term = Term(color=False)
        step = run_viewer.StepSummary(
            position=1,
            id6="ryvoi5",
            setid="runnernorm",
            action="execute",
            status="partial",
            configured_file=".aw/records/plans/pending/20260825-runnernorm-00-ryvoi5-test.ipd.md",
            stem="20260825-runnernorm-00-ryvoi5",
            attempts_count=1,
            disposition="dependency-blocked",
        )
        line = run_viewer.format_step_line(step, term)
        self.assertIn("partial", line)
        self.assertIn("plan", line)
        self.assertIn("20260825-runnernorm-00-ryvoi5", line)
        self.assertIn("[attempts: 1]", line)
        self.assertIn("dependency-blocked", line)

    def test_format_run_human(self):
        term = Term(color=False)
        run_d = Path(".aw/records/runs/run-20260827T212958Z-2367239")
        summary = run_viewer.load_run_summary(run_d, Path("."))
        self.assertIsNotNone(summary)
        formatted = run_viewer.format_run_human(summary, term, detail=False)
        self.assertIn("run-20260827T212958Z-2367239", formatted)
        self.assertIn("[runnernorm]", formatted)
        self.assertIn("ryvoi5", formatted)
        self.assertIn("dg28i9", formatted)
        self.assertIn("puot79", formatted)

        # Test detail mode
        formatted_detail = run_viewer.format_run_human(summary, term, detail=True)
        self.assertIn("! incomplete:", formatted_detail)
        self.assertIn("* summary:", formatted_detail)

        # Test short mode
        formatted_short = run_viewer.format_run_human(summary, term, short=True)
        self.assertIn("│ Status", formatted_short)
        self.assertIn("Item", formatted_short)
        self.assertIn("Action", formatted_short)
        self.assertIn("Verified", formatted_short)
        self.assertNotIn("Attempts", formatted_short)
        self.assertNotIn("Total Cost", formatted_short)
        self.assertNotIn("Total Tok", formatted_short)

    def test_run_viewer_cli_target_human(self):
        ns = argparse.Namespace(
            dir=".",
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            short=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("run-20260827T212958Z-2367239", out)
        self.assertIn("runnernorm", out)

    def test_run_viewer_cli_short(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Verified", out)
        self.assertNotIn("Total Tok", out)
        self.assertNotIn("Summary across", out)
        self.assertNotIn("Breakdown by Status:", out)

    def test_run_viewer_cli_summary_only(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Summary across", out)
        self.assertIn("Breakdown by Status:", out)
        self.assertNotIn("pid:", out)

    def test_run_viewer_cli_short_and_summary_only_conflict(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=True,
            summary_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn("error: --summary-only/-S cannot be used with --short/-s", out)

    def test_run_viewer_cli_latest_only(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=3,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Data from", out)
        self.assertIn("Verified", out)
        self.assertNotIn("Summary across", out)

    def test_run_viewer_cli_latest_only_single_run(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=1,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("run-", out)
        self.assertNotIn("Data from", out)

    def test_run_viewer_cli_latest_only_conflict(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn(
            "error: --latest-only/-L cannot be used with --summary-only/-S", out
        )

    def test_run_viewer_cli_json(self):
        ns = argparse.Namespace(
            dir=".",
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        parsed = json.loads(buf.getvalue())
        self.assertIn("runs", parsed)
        self.assertEqual(len(parsed["runs"]), 1)
        self.assertEqual(parsed["runs"][0]["run_id"], "run-20260827T212958Z-2367239")

    def test_run_viewer_cli_agent(self):
        ns = argparse.Namespace(
            dir=".",
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=False,
            agent=True,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        lines = [line for line in buf.getvalue().strip().splitlines() if line]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["run_id"], "run-20260827T212958Z-2367239")

    def test_run_viewer_cli_filters(self):
        # Filter by set
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set="ipddeps",
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("ipddeps", out)

        # Filter by status
        ns_st = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status="partial",
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns_st)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("partial", out)

    def test_aw_cli_entry_points(self):
        # aw runs --last
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                cli.main(["runs", "--last", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf.getvalue())

        # aw runs -l
        buf_l = io.StringIO()
        with redirect_stdout(buf_l):
            try:
                cli.main(["runs", "-l", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf_l.getvalue())

        # aw runs -l 2
        buf_l2 = io.StringIO()
        with redirect_stdout(buf_l2):
            try:
                cli.main(["runs", "-l", "2", "--json"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data_l2 = json.loads(buf_l2.getvalue())
        self.assertLessEqual(len(data_l2["runs"]), 2)

        # aw runs --last 2
        buf_n = io.StringIO()
        with redirect_stdout(buf_n):
            try:
                cli.main(["runs", "--last", "2", "--json"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data = json.loads(buf_n.getvalue())
        self.assertLessEqual(len(data["runs"]), 2)

        # aw runs --latest (backwards-compat)
        buf_compat = io.StringIO()
        with redirect_stdout(buf_compat):
            try:
                cli.main(["runs", "--latest", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf_compat.getvalue())

        # aw run list --last
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            try:
                cli.main(["run", "list", "--last", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf2.getvalue())

        # aw run list --last 2
        buf3 = io.StringIO()
        with redirect_stdout(buf3):
            try:
                cli.main(["run", "list", "--last", "2", "--json"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data3 = json.loads(buf3.getvalue())
        self.assertLessEqual(len(data3["runs"]), 2)

        # aw runs --last 0 (validation error)
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exc_ctx:
                cli.main(["runs", "--last", "0"])
            self.assertEqual(exc_ctx.exception.code, 2)

    def test_parse_since_timestamp_relative(self):
        from datetime import datetime, timezone

        fixed_now = datetime(2026, 8, 27, 19, 0, 0, tzinfo=timezone.utc)
        # 1d = 24 hours
        dt_1d = run_viewer.parse_since_timestamp("1d", fixed_now)
        self.assertEqual(dt_1d, datetime(2026, 8, 26, 19, 0, 0, tzinfo=timezone.utc))

        # 0.5d = 12 hours
        dt_half_d = run_viewer.parse_since_timestamp("0.5d", fixed_now)
        self.assertEqual(dt_half_d, datetime(2026, 8, 27, 7, 0, 0, tzinfo=timezone.utc))

        # 2h = 2 hours
        dt_2h = run_viewer.parse_since_timestamp("2h", fixed_now)
        self.assertEqual(dt_2h, datetime(2026, 8, 27, 17, 0, 0, tzinfo=timezone.utc))

        # 1.5h = 90 mins
        dt_1_5h = run_viewer.parse_since_timestamp("1.5h", fixed_now)
        self.assertEqual(dt_1_5h, datetime(2026, 8, 27, 17, 30, 0, tzinfo=timezone.utc))

        # 1w = 7 days
        dt_1w = run_viewer.parse_since_timestamp("1w", fixed_now)
        self.assertEqual(dt_1w, datetime(2026, 8, 20, 19, 0, 0, tzinfo=timezone.utc))

        # 1m = ~30 days
        dt_1m = run_viewer.parse_since_timestamp("1m", fixed_now)
        self.assertTrue((fixed_now - dt_1m).days >= 30)

        # 1y = ~365 days
        dt_1y = run_viewer.parse_since_timestamp("1y", fixed_now)
        self.assertTrue((fixed_now - dt_1y).days >= 365)

    def test_parse_since_timestamp_dates(self):
        from datetime import datetime, timezone

        dt_ymd = run_viewer.parse_since_timestamp("2026-08-25")
        self.assertEqual(dt_ymd, datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc))

        dt_dense = run_viewer.parse_since_timestamp("20260825")
        self.assertEqual(dt_dense, datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc))

        dt_iso = run_viewer.parse_since_timestamp("2026-08-27T13:00:00Z")
        self.assertEqual(dt_iso, datetime(2026, 8, 27, 13, 0, 0, tzinfo=timezone.utc))

    def test_parse_since_timestamp_invalid(self):
        with self.assertRaises(ValueError):
            run_viewer.parse_since_timestamp("invalid-date-or-spec")

    def test_run_viewer_cli_since_filter(self):
        # Filtering with --since 10y should return runs
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="10y",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        self.assertIn("run-", buf.getvalue())

        # Filtering with a specific run ID should include that run and subsequent runs
        ns_run_id = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="run-20260827T212854Z-2364829",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf_run = io.StringIO()
        with redirect_stdout(buf_run):
            code_run = run_viewer.run_viewer_cli(ns_run_id)
        self.assertEqual(code_run, 0)
        self.assertIn("run-20260827T212854Z-2364829", buf_run.getvalue())
        self.assertIn("run-20260827T212958Z-2367239", buf_run.getvalue())

        # Filtering with an invalid --since should return code 2
        ns_bad = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="not-a-timespec",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf_bad = io.StringIO()
        with redirect_stdout(buf_bad):
            code_bad = run_viewer.run_viewer_cli(ns_bad)
        self.assertEqual(code_bad, 2)

    def test_extract_log_metrics_opencode(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            log_p = Path(td) / "session.jsonl"
            lines = [
                json.dumps(
                    {
                        "type": "step_finish",
                        "part": {
                            "tokens": {
                                "input": 1000,
                                "output": 200,
                                "total": 1200,
                                "cache": {"read": 50, "write": 10},
                            },
                            "cost": 0.052,
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "step_finish",
                        "part": {
                            "tokens": {
                                "input": 2000,
                                "output": 300,
                                "total": 2300,
                            },
                            "cost": 0.081,
                        },
                    }
                ),
            ]
            log_p.write_text("\n".join(lines), encoding="utf-8")
            cost, toks = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost, 0.133, places=3)
            self.assertEqual(toks["total"], 3500)
            self.assertEqual(toks["input"], 3000)
            self.assertEqual(toks["output"], 500)
            self.assertEqual(toks["cache"], 60)

    def test_extract_log_metrics_usage_shape(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            log_p = Path(td) / "session.jsonl"
            lines = [
                json.dumps(
                    {
                        "type": "agent_response",
                        "usage": {
                            "total_tokens": 500,
                            "input_tokens": 400,
                            "output_tokens": 100,
                        },
                        "cost": 0.015,
                    }
                )
            ]
            log_p.write_text("\n".join(lines), encoding="utf-8")
            cost, toks = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost, 0.015, places=3)
            self.assertEqual(toks["total"], 500)
            self.assertEqual(toks["input"], 400)
            self.assertEqual(toks["output"], 100)

    def test_format_step_line_cost_badge(self):
        term = Term(color=False)
        step = run_viewer.StepSummary(
            position=1,
            id6="abc123",
            setid="testset",
            action="execute",
            status="executed",
            configured_file="",
            stem="testset-abc123",
            cost=12.3456,
            tokens={"total": 50000},
        )
        line = run_viewer.format_step_line(step, term)
        self.assertIn("[$12.35]", line)
        self.assertIn("executed", line)

    def test_format_run_human_with_cost_and_detail(self):
        term = Term(color=False)
        step1 = run_viewer.StepSummary(
            position=1,
            id6="abc123",
            setid="testset",
            action="execute",
            status="executed",
            configured_file="",
            stem="testset-abc123",
            cost=10.50,
            tokens={"total": 100000, "input": 80000, "output": 20000},
        )
        step2 = run_viewer.StepSummary(
            position=2,
            id6="def456",
            setid="testset",
            action="review",
            status="reviewed",
            configured_file="",
            stem="testset-def456",
            cost=5.25,
            tokens={"total": 50000, "input": 40000, "output": 10000},
        )
        run = run_viewer.RunSummary(
            run_id="run-20260829T000000Z-111111",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00+00:00",
            setids=["testset"],
            steps=[step1, step2],
            counts={"executed": 1, "reviewed": 1},
            total_cost=15.75,
            total_tokens={"total": 150000, "input": 120000, "output": 30000},
        )
        formatted = run_viewer.format_run_human(run, term, detail=True)
        self.assertIn("$15.75", formatted)
        self.assertIn("150.00K tok", formatted)
        self.assertIn("$10.50", formatted)
        self.assertIn("$5.25", formatted)
        self.assertIn("$ cost: $10.50", formatted)
        self.assertIn("* tokens: 100.00K tot", formatted)

    def test_multi_run_summary_dict_and_format(self):
        term = Term(color=False)
        step1 = run_viewer.StepSummary(
            position=1,
            id6="a1",
            setid="s1",
            action="execute",
            status="executed",
            configured_file="",
            stem="s1-a1",
            cost=10.00,
            tokens={"total": 100000},
        )
        step2 = run_viewer.StepSummary(
            position=2,
            id6="a2",
            setid="s1",
            action="review",
            status="reviewed",
            configured_file="",
            stem="s1-a2",
            cost=6.00,
            tokens={"total": 60000},
        )
        step3 = run_viewer.StepSummary(
            position=1,
            id6="b1",
            setid="s2",
            action="review",
            status="reviewed",
            configured_file="",
            stem="s2-b1",
            cost=8.00,
            tokens={"total": 80000},
        )
        step4 = run_viewer.StepSummary(
            position=2,
            id6="b2",
            setid="s2",
            action="execute",
            status="queued",
            configured_file="",
            stem="s2-b2",
            cost=None,
            tokens={},
        )
        run1 = run_viewer.RunSummary(
            run_id="run-1",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00Z",
            setids=["s1"],
            steps=[step1, step2],
            counts={"executed": 1, "reviewed": 1},
            total_cost=16.00,
            total_tokens={"total": 160000},
        )
        run2 = run_viewer.RunSummary(
            run_id="run-2",
            run_dir=Path("."),
            created_at="2026-08-29T01:00:00Z",
            setids=["s2"],
            steps=[step3, step4],
            counts={"reviewed": 1, "queued": 1},
            total_cost=8.00,
            total_tokens={"total": 80000},
        )
        summary_dict = run_viewer.build_multi_run_summary_dict([run1, run2])
        self.assertEqual(summary_dict["runs_count"], 2)
        self.assertEqual(summary_dict["steps_count"], 4)
        self.assertEqual(summary_dict["steps_with_cost"], 3)
        self.assertEqual(summary_dict["total_cost"], 24.00)
        self.assertEqual(summary_dict["avg_cost_per_run"], 12.00)

        # Check by_status
        self.assertEqual(summary_dict["by_status"]["executed"]["total_cost"], 10.00)
        self.assertEqual(
            summary_dict["by_status"]["executed"]["avg_cost_per_step"], 10.00
        )
        self.assertEqual(
            summary_dict["by_status"]["executed"]["avg_cost_per_run"], 5.00
        )
        self.assertEqual(summary_dict["by_status"]["reviewed"]["total_cost"], 14.00)
        self.assertEqual(
            summary_dict["by_status"]["reviewed"]["avg_cost_per_step"], 7.00
        )
        self.assertEqual(
            summary_dict["by_status"]["reviewed"]["avg_cost_per_run"], 7.00
        )
        self.assertEqual(summary_dict["by_status"]["queued"]["count"], 1)
        self.assertEqual(summary_dict["by_status"]["queued"]["steps_with_cost"], 0)

        # Check by_action
        self.assertEqual(summary_dict["by_action"]["review"]["avg_cost_per_step"], 7.00)
        self.assertEqual(summary_dict["by_action"]["review"]["avg_cost_per_run"], 7.00)
        self.assertEqual(
            summary_dict["by_action"]["execute"]["avg_cost_per_step"], 10.00
        )
        self.assertEqual(summary_dict["by_action"]["execute"]["avg_cost_per_run"], 5.00)

        # Check format_multi_run_summary text with color=False
        text = run_viewer.format_multi_run_summary([run1, run2], term)
        self.assertIn("Summary across 2 runs (4 steps)", text)
        self.assertIn(
            "Total Cost:   $24.00 (across 3/4 steps with usage; avg $12.00/run)", text
        )
        self.assertIn("Breakdown by Status:", text)
        self.assertIn("╭", text)
        self.assertIn("│ Status", text)
        self.assertIn("Type", text)
        self.assertIn("Cost", text)
        self.assertIn("Tokens", text)
        self.assertIn("In", text)
        self.assertIn("Out", text)
        self.assertIn("Cached", text)
        self.assertIn("Total", text)
        self.assertIn("Avg", text)
        self.assertIn("reviewed", text)
        self.assertIn("$14.00", text)
        self.assertIn("$7.00", text)
        self.assertIn("executed", text)
        self.assertIn("$10.00", text)
        self.assertIn("queued", text)
        self.assertIn("╰", text)

        # Check format_multi_run_summary text with color=True
        color_term = Term(color=True)
        color_text = run_viewer.format_multi_run_summary([run1, run2], color_term)
        self.assertIn("Summary across 2 runs (4 steps)", color_text)
        self.assertIn("Total Cost:", color_text)
        self.assertIn("Breakdown by Status:", color_text)
        self.assertIn("Breakdown by Action:", color_text)
        self.assertIn("╭", color_text)
        self.assertIn("╰", color_text)

    def test_multi_run_summary_breakdown_with_verification(self):
        term = Term(color=False)
        step1 = run_viewer.StepSummary(
            position=1,
            id6="a1",
            setid="s1",
            action="execute",
            status="executed",
            configured_file="",
            stem="s1-a1",
            cost=10.00,
            tokens={"total": 100000, "input": 10000, "output": 5000, "cache": 85000},
            exec_cost=7.00,
            exec_tokens={"total": 70000, "input": 7000, "output": 3500, "cache": 59500},
            verify_cost=3.00,
            verify_tokens={
                "total": 30000,
                "input": 3000,
                "output": 1500,
                "cache": 25500,
            },
        )
        run1 = run_viewer.RunSummary(
            run_id="run-1",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00Z",
            setids=["s1"],
            steps=[step1],
            counts={"executed": 1},
            total_cost=10.00,
            total_tokens={
                "total": 100000,
                "input": 10000,
                "output": 5000,
                "cache": 85000,
            },
            exec_cost=7.00,
            exec_tokens={"total": 70000, "input": 7000, "output": 3500, "cache": 59500},
            verify_cost=3.00,
            verify_tokens={
                "total": 30000,
                "input": 3000,
                "output": 1500,
                "cache": 25500,
            },
        )

        # Single run format
        run_txt = run_viewer.format_run_human(run1, term)
        self.assertIn("Total:        $10.00, 100.00K tok", run_txt)
        self.assertIn("- Execute:  $7.00, 70.00K tok", run_txt)
        self.assertIn("- Verify:   $3.00, 30.00K tok", run_txt)

        # Step details format
        details = run_viewer.render_step_details([step1], term)
        details_txt = "\n".join(details)
        self.assertIn("$ cost: $10.00 (exec: $7.00, verify: $3.00)", details_txt)
        self.assertIn("[exec: 70.00K, verify: 30.00K]", details_txt)

        # Multi-run summary format
        summary_dict = run_viewer.build_multi_run_summary_dict([run1])
        self.assertIn("by_phase", summary_dict)
        self.assertEqual(summary_dict["by_phase"]["execution"]["total_cost"], 7.00)
        self.assertEqual(summary_dict["by_phase"]["verification"]["total_cost"], 3.00)

        sum_txt = run_viewer.format_multi_run_summary([run1], term)
        self.assertIn("Total Cost:   $10.00", sum_txt)
        self.assertIn("- Execute:  $7.00 (avg $7.00/run)", sum_txt)
        self.assertIn("- Verify:   $3.00 (avg $3.00/run)", sum_txt)
        self.assertIn("Total Tokens: 100.00K", sum_txt)
        self.assertIn("- Execute:  70.00K (avg 70.00K/run)", sum_txt)
        self.assertIn("- Verify:   30.00K (avg 30.00K/run)", sum_txt)
        self.assertIn("Breakdown by Phase:", sum_txt)
        self.assertIn("execution", sum_txt)
        self.assertIn("verification", sum_txt)

    def test_multi_run_cli_json_summary(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        parsed = json.loads(buf.getvalue())
        self.assertIn("runs", parsed)
        self.assertIn("summary", parsed)
        self.assertEqual(parsed["summary"]["runs_count"], 2)
        self.assertIn("by_status", parsed["summary"])
        self.assertIn("by_action", parsed["summary"])

    def test_format_duration(self):
        self.assertEqual(run_viewer.format_duration(None), "0s")
        self.assertEqual(run_viewer.format_duration(-5), "0s")
        self.assertEqual(run_viewer.format_duration(5.4), "5.4s")
        self.assertEqual(run_viewer.format_duration(45), "45s")
        self.assertEqual(run_viewer.format_duration(125), "2m 05s")
        self.assertEqual(run_viewer.format_duration(3665), "1h 01m 05s")

    def test_inspect_run_pid_and_runtime(self):
        import tempfile
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as td:
            rd = Path(td) / "run-20260829T100000Z-99999"
            rd.mkdir()
            (rd / "driver.lock").write_text(
                "pid=99999 started=2026-08-29T10:00:00+00:00"
            )
            (rd / "state.json").write_text(
                json.dumps({"updated_at": "2026-08-29T10:05:30+00:00"})
            )

            dt = datetime(2026, 8, 29, 10, 0, 0, tzinfo=timezone.utc)
            pid, pid_state, is_live, runtime_secs, runtime_str = (
                run_viewer.inspect_run_pid_and_runtime(
                    rd, "2026-08-29T10:00:00Z", "2026-08-29T10:05:30Z", dt
                )
            )
            self.assertEqual(pid, 99999)
            self.assertEqual(runtime_secs, 330.0)
            self.assertEqual(runtime_str, "5m 30s")

    def test_format_run_human_pid_and_runtime(self):
        term = Term(color=False)
        run = run_viewer.RunSummary(
            run_id="run-20260829T100000Z-12345",
            run_dir=Path("."),
            created_at="2026-08-29T10:00:00+00:00",
            setids=["myset"],
            steps=[],
            counts={"executed": 2},
            total_cost=5.50,
            total_tokens={
                "total": 50000,
                "input": 40000,
                "output": 10000,
                "cache": 30000,
            },
            pid=12345,
            pid_state="exited",
            is_live=False,
            runtime_seconds=125.0,
            runtime_str="2m 05s",
        )
        out = run_viewer.format_run_human(run, term)
        lines = out.splitlines()
        self.assertIn("run-20260829T100000Z-12345", lines[0])
        self.assertIn("pid: 12345 [exited]", lines[1])
        self.assertIn("runtime: 2m 05s", lines[1])
        self.assertIn("0 steps: 2 executed", lines[2])
        self.assertIn(
            "$5.50, 50.00K tok (40.00K in, 10.00K out, 30.00K cached)", lines[3]
        )

    def test_audit_step_artifact_and_summary(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            pending_dir.mkdir(parents=True)
            executed_dir.mkdir(parents=True)

            # Plan 1: In pending with status approved, but step is complete (loc & status mismatch)
            p1 = pending_dir / "20260829-test-01-item01.ipd.md"
            p1.write_text("- Id: item01\n- Status: approved\n")

            # Plan 2: In executed with status executed, step executed (clean)
            p2 = executed_dir / "20260829-test-02-item02.ipd.md"
            p2.write_text("- Id: item02\n- Status: executed\n")

            st1 = run_viewer.StepSummary(
                position=1,
                id6="item01",
                setid="test",
                action="execute",
                status="complete",
                configured_file="",
                stem="20260829-test-01-item01",
            )
            st2 = run_viewer.StepSummary(
                position=2,
                id6="item02",
                setid="test",
                action="execute",
                status="executed",
                configured_file="",
                stem="20260829-test-02-item02",
            )
            st3 = run_viewer.StepSummary(
                position=3,
                id6="item03",
                setid="test",
                action="execute",
                status="queued",
                configured_file="",
                stem="20260829-test-03-item03",
            )

            a1 = run_viewer.audit_step_artifact(st1, repo_root=root)
            self.assertTrue(a1.location_mismatch)
            self.assertTrue(a1.status_mismatch)
            self.assertFalse(a1.missing_entirely)
            self.assertEqual(a1.actual_dir, "pending")
            self.assertEqual(a1.expected_dir, "executed")
            self.assertEqual(a1.file_status, "approved")

            a2 = run_viewer.audit_step_artifact(st2, repo_root=root)
            self.assertFalse(a2.location_mismatch)
            self.assertFalse(a2.status_mismatch)
            self.assertFalse(a2.missing_entirely)

            a3 = run_viewer.audit_step_artifact(st3, repo_root=root)
            self.assertTrue(a3.missing_entirely)

            term = Term(color=False)
            sum_txt = run_viewer.format_artifact_audit_summary([a1, a2, a3], term)
            self.assertIn("Artifact & Status Discrepancies", sum_txt)
            self.assertIn("Expected", sum_txt)
            self.assertIn("Actual", sum_txt)
            self.assertIn("20260829-test-01-item01", sum_txt)
            self.assertIn("pending/", sum_txt)
            self.assertIn("approved", sum_txt)
            self.assertIn("20260829-test-03-item03", sum_txt)
            self.assertIn("missing", sum_txt)

            # Check table rendering decoration
            tbl = run_viewer.render_steps_table([st1, st2, st3], term, repo_root=root)
            self.assertIn("Issue", tbl)
            self.assertIn("YES", tbl)
            self.assertIn("no", tbl)

    def test_run_viewer_cli_issues_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            p1 = pending_dir / "20260829-test-01-item01.ipd.md"
            p1.write_text("- Id: item01\n- Status: approved\n")

            run_dir = root / ".aw" / "records" / "runs" / "run-20260829T000000Z-111111"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260829T000000Z-111111",
                "queue": [
                    {
                        "position": 1,
                        "id6": "item01",
                        "setid": "test",
                        "action": "execute",
                        "status": "complete",
                        "configured_file": "",
                        "stem": "20260829-test-01-item01",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state))

            ns = argparse.Namespace(
                dir=str(root),
                target=[],
                set=None,
                ipd=None,
                status=None,
                failed=False,
                active=False,
                latest=False,
                last=1,
                since=None,
                detail=False,
                short=False,
                summary_only=False,
                latest_only=False,
                issues=True,
                json=False,
                agent=False,
                no_color=True,
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = run_viewer.run_viewer_cli(ns)
            self.assertEqual(code, 0)
            out = buf.getvalue()
            self.assertIn("Artifact & Status Discrepancies", out)
            self.assertIn("20260829-test-01-item01", out)
            self.assertNotIn("pid:", out)

    def test_run_viewer_cli_issues_conflict(self):
        ns = argparse.Namespace(
            dir=".",
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=1,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            latest_only=False,
            issues=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn("error: --issues/-i cannot be used with --summary-only/-S", out)
