#!/usr/bin/env python3
"""Tests for UX and progress reporting in `aw runs analyze` and `aw runs query`.

Validates that:
1. `update_cache` invokes the optional `progress(idx, total, rid)` callback.
2. `aw runs analyze` reports active progress on stderr in human mode, and reports published
   HTML report and analysis JSON paths in stdout Evidence (repo-relative, no absolute paths).
3. `aw runs analyze --path` and `--list` emit repo-relative paths.
4. `aw runs query overview` displays corpus metrics (cached, complete, incomplete, flags,
   analyses) in summary and evidence rather than a bare row count.
5. `aw runs query overview --agent` remains conforming to aw.agent/v1 item streams.

Stdlib unittest only.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_cli as analytics_cli
from tests.fixtures.run_analytics import write_run


class RunAnalyticsCliUxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name).resolve()
        self.runs_root = self.repo / ".aw" / "records" / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)

        # Write two synthetic completed runs
        self.run1 = write_run(
            self.runs_root, "run-20260901T000000Z-1111111", repo=str(self.repo)
        )
        self.run2 = write_run(
            self.runs_root, "run-20260901T010000Z-2222222", repo=str(self.repo)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_update_cache_progress_callback(self) -> None:
        """`update_cache` invokes progress callback with (index, total, run_id)."""
        calls = []

        def _on_progress(idx: int, total: int, rid: str) -> None:
            calls.append((idx, total, rid))

        report = cache_mod.update_cache(
            [self.run1, self.run2],
            build_facts=run_analytics.build_cache_facts,
            repo=self.repo,
            progress=_on_progress,
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], (1, 2, "run-20260901T000000Z-1111111"))
        self.assertEqual(calls[1], (2, 2, "run-20260901T010000Z-2222222"))
        self.assertEqual(report.totals.get("total"), 2)

    def test_run_analyze_human_progress_and_evidence(self) -> None:
        """`aw runs analyze` prints step cues to stderr and publishes report paths in Evidence."""
        args = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=False,
            open=False,
            rebuild=False,
            keep_snapshot=None,
            targets=[],
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
        )

        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = analytics_cli.run_analyze(args)

        self.assertEqual(rc, 0)
        err = err_buf.getvalue()
        out = out_buf.getvalue()

        # Step cues on stderr
        self.assertIn("Analyzing 2 run(s)...", err)
        self.assertIn("Analyzed 2 run(s).", err)
        self.assertIn("Publishing report bundle...", err)
        self.assertIn("Report published.", err)

        # Conforming outcome and Evidence on stdout
        self.assertIn("analyzed 2 run(s):", out)
        self.assertIn("report:", out)
        self.assertIn(".aw/records/runs/analytics", out)
        self.assertIn("analysis:", out)
        self.assertIn("analysis.json", out)

        # No absolute home path leaked in stdout
        self.assertNotIn(str(self.repo), out)

        # Next actions suggest inspecting and opening report
        self.assertIn("aw runs query overview", out)
        self.assertIn("aw runs analyze --open", out)

    def test_run_analyze_path_and_list_emit_relative_paths(self) -> None:
        """`aw runs analyze --path` and `--list` return repo-relative paths."""
        # First ensure a report is published
        args_build = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=False,
            open=False,
            rebuild=False,
            keep_snapshot=None,
            targets=[],
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(analytics_cli.run_analyze(args_build), 0)

        # Test --path
        args_path = argparse.Namespace(
            dir=str(self.repo),
            path=True,
            list=False,
            open=False,
            rebuild=False,
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
        )
        out_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(io.StringIO()):
            rc = analytics_cli.run_analyze(args_path)
        self.assertEqual(rc, 0)
        path_out = out_buf.getvalue()
        self.assertIn(".aw/records/runs/analytics", path_out)
        self.assertNotIn(str(self.repo), path_out)

        # Test --list
        args_list = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=True,
            open=False,
            rebuild=False,
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
        )
        out_buf_list = io.StringIO()
        with redirect_stdout(out_buf_list), redirect_stderr(io.StringIO()):
            rc = analytics_cli.run_analyze(args_list)
        self.assertEqual(rc, 0)
        list_out = out_buf_list.getvalue()
        self.assertIn("report file(s)", list_out)
        self.assertNotIn(str(self.repo), list_out)

    def test_run_query_overview_human_metrics(self) -> None:
        """`aw runs query overview` displays rich corpus metrics in human mode."""
        # Populate cache
        cache_mod.update_cache(
            [self.run1, self.run2],
            build_facts=run_analytics.build_cache_facts,
            repo=self.repo,
        )

        args = argparse.Namespace(
            dir=str(self.repo),
            view="overview",
            filter=None,
            group_by=None,
            metric=None,
            stat=None,
            limit=None,
            analysis=None,
            finding=None,
            severity=None,
            taxonomy=None,
            price=None,
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
        )

        out_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(io.StringIO()):
            rc = analytics_cli.run_query_leaf(args)

        self.assertEqual(rc, 0)
        out = out_buf.getvalue()

        # Summary indicates cached runs and completion
        self.assertIn("2 cached run(s): 2 complete, 0 incomplete", out)

        # Evidence contains distinct scalar metrics
        self.assertIn("cached_runs: 2", out)
        self.assertIn("complete_runs: 2", out)
        self.assertIn("quality_flags:", out)
        self.assertIn("has-missing-fields (2)", out)
        self.assertIn("required_analyses:", out)
        self.assertIn("refused_analyses:", out)
        self.assertIn("caveats:", out)

        # Next action points to next inspection
        self.assertIn("aw runs query data-quality", out)

    def test_run_query_overview_agent_unchanged(self) -> None:
        """`aw runs query overview --agent` emits conforming aw.agent/v1 JSONL records."""
        cache_mod.update_cache(
            [self.run1, self.run2],
            build_facts=run_analytics.build_cache_facts,
            repo=self.repo,
        )

        args = argparse.Namespace(
            dir=str(self.repo),
            view="overview",
            filter=None,
            group_by=None,
            metric=None,
            stat=None,
            limit=None,
            analysis=None,
            finding=None,
            severity=None,
            taxonomy=None,
            price=None,
            agent=True,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
        )

        out_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(io.StringIO()):
            rc = analytics_cli.run_query_leaf(args)

        self.assertEqual(rc, 0)
        lines = [line for line in out_buf.getvalue().splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 2)  # item record(s) + summary record

        # First line is item
        item = json.loads(lines[0])
        self.assertEqual(item.get("schema"), "aw.agent/v1")
        self.assertEqual(item.get("kind"), "item")
        self.assertIn("payload", item)
        self.assertEqual(item["payload"].get("cached_runs"), 2)

        # Terminal line is summary
        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("schema"), "aw.agent/v1")
        self.assertEqual(summary.get("kind"), "summary")
        self.assertEqual(summary.get("cmd"), "runs query")
        self.assertEqual(summary.get("exit"), 0)


if __name__ == "__main__":
    unittest.main()
