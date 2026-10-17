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

    def test_repo_rel_renders_posix_separators_on_windows(self) -> None:
        """Windows CI regression: `os.path.relpath` emits backslashes there, so `aw runs analyze`
        printed `.aw\\records\\...`. Drive the real formatter with Windows path semantics."""
        import ntpath

        rel = analytics_cli._repo_rel(
            "C:\\repo\\.aw\\records\\runs\\analytics\\latest\\index.html",
            "C:\\repo",
            _pathmod=ntpath,
        )
        self.assertEqual(rel, ".aw/records/runs/analytics/latest/index.html")

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

    def test_emit_query_agent_bounded_preserves_next_under_fields_projection(
        self,
    ) -> None:
        """`_emit_query_agent` retains `next` paging continuation under `--fields` projection."""
        from agent_workflows import run_analytics_query as query_mod

        result = query_mod.QueryResult(
            view="metrics",
            rows=({"a": 1}, {"a": 2}),
            total=5,
            emitted=2,
            omitted=3,
            next_command="aw runs query metrics --limit 5",
        )
        args = argparse.Namespace(
            dir=str(self.repo),
            agent=True,
            json=False,
            fields=["cmd"],
        )

        out_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(io.StringIO()):
            rc = analytics_cli._emit_query_agent(result, args)

        self.assertEqual(rc, 0)
        lines = [line for line in out_buf.getvalue().splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 1)

        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("schema"), "aw.agent/v1")
        self.assertEqual(summary.get("kind"), "summary")
        self.assertIn("next", summary)
        self.assertEqual(summary["next"], "aw runs query metrics --limit 5")
        self.assertIs(summary.get("complete"), False)
        self.assertGreater(summary.get("omitted", 0), 0)

    def test_run_analyze_rebuild_behavior(self) -> None:
        """E-05: `aw runs analyze --rebuild` clears cache entries, preserves salt, removes stats cache, and leaves source runs immutable."""
        from agent_workflows import run_dashboard as dash_mod

        # Initial run_analyze with rebuild=False to populate cache
        args_initial = argparse.Namespace(
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
            rc_init = analytics_cli.run_analyze(args_initial)
        self.assertEqual(rc_init, 0)

        # Resolve paths through cache_mod resolver (never hand-composing .aw/records/runs)
        cache_root = cache_mod.cache_root(self.repo)
        salt_file = cache_root / "salt"
        self.assertTrue(salt_file.is_file())
        salt_initial = salt_file.read_text(encoding="utf-8").strip()
        root_id_initial = cache_mod.source_root_id(
            cache_root.parent.parent, salt=salt_initial
        )

        entry1_path = cache_mod.entry_path(root_id_initial, self.run1.name, self.repo)
        entry2_path = cache_mod.entry_path(root_id_initial, self.run2.name, self.repo)
        self.assertTrue(entry1_path.is_file())
        self.assertTrue(entry2_path.is_file())

        entry1_before = cache_mod.load_entry(entry1_path)
        entry2_before = cache_mod.load_entry(entry2_path)

        # Plant dashboard stats cache file to assert _clear_cache removes it
        stats_cache_file = cache_root / dash_mod.STATS_CACHE_FILENAME
        stats_cache_file.write_text('{"planted": true}', encoding="utf-8")
        self.assertTrue(stats_cache_file.is_file())

        # Snapshot non-analytics source run files (size, mtime_ns).
        # Must EXCLUDE analytics/ subtree because analytics/ lives under the runs root
        # and contains the cache files that are legitimately deleted and rebuilt.
        def _source_snapshot() -> dict[Path, tuple[int, int]]:
            snap: dict[Path, tuple[int, int]] = {}
            for run_dir in (self.run1, self.run2):
                for p in run_dir.rglob("*"):
                    if p.is_file():
                        st = p.stat()
                        snap[p] = (st.st_size, st.st_mtime_ns)
            return snap

        snapshot_before = _source_snapshot()
        self.assertTrue(len(snapshot_before) > 0)

        import dataclasses

        entry1_before = dataclasses.replace(
            entry1_before, generated_at="2000-01-01T00:00:00Z"
        )
        entry2_before = dataclasses.replace(
            entry2_before, generated_at="2000-01-01T00:00:00Z"
        )

        # Drive run_analyze with rebuild=True namespace built identical to rebuild=False
        args_rebuild = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=False,
            open=False,
            rebuild=True,
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
            rc_rebuild = analytics_cli.run_analyze(args_rebuild)
        self.assertEqual(rc_rebuild, 0)

        # Property 1: salt file survives and source_root_id is unchanged
        self.assertTrue(salt_file.is_file())
        salt_after = salt_file.read_text(encoding="utf-8").strip()
        self.assertEqual(salt_initial, salt_after)
        root_id_after = cache_mod.source_root_id(
            cache_root.parent.parent, salt=salt_after
        )
        self.assertEqual(root_id_initial, root_id_after)

        # Property 2: dashboard stats cache file was removed by _clear_cache
        self.assertFalse(stats_cache_file.exists())

        # Property 3: every entry was discarded and republished (generated_at updated)
        entry1_after = cache_mod.load_entry(entry1_path)
        entry2_after = cache_mod.load_entry(entry2_path)
        self.assertNotEqual(entry1_before.generated_at, entry1_after.generated_at)
        self.assertNotEqual(entry2_before.generated_at, entry2_after.generated_at)

        # Property 4: no file under source run directories changed in (size, mtime_ns)
        snapshot_after = _source_snapshot()
        self.assertEqual(snapshot_before, snapshot_after)


if __name__ == "__main__":
    unittest.main()
