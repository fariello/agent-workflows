"""Unit tests for `agent_workflows.run_viewer` (aw runs / run viewer)."""

from __future__ import annotations

import argparse
import io
import json
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
        # aw runs --latest
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                cli.main(["runs", "--latest", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf.getvalue())

        # aw run list --latest
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            try:
                cli.main(["run", "list", "--latest", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf2.getvalue())

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
