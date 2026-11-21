"""Behavioral tests for `aw runs analyze` with external runs directories (inside and outside a repo)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import (
    cli,
    run_analytics_cache,
    run_analytics_query,
    run_viewer,
)


def _write_run(
    runs_parent: Path,
    run_id: str,
    *,
    setid: str = "extset",
    tokens_total: int = 150,
    startup_exec_s: float | None = None,
) -> Path:
    run_dir = runs_parent / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-11-20T10:00:00+00:00",
        "updated_at": "2026-11-20T10:05:00+00:00",
        "repo": str(runs_parent),
        "manifest": str(run_dir / "manifest.json"),
        "manifest_sha256": "a" * 64,
        "runbook": str(run_dir / "runbook.md"),
        "runbook_sha256": "b" * 64,
        "selectors": [setid],
        "set_sessions": {},
        "driver": {"id": "agy_runipd", "path": "agent_workflows/agy_runipd.py"},
        "options": {"model": "gemini-4-neon-high"},
        "queue": [
            {
                "id6": "ex1001",
                "setid": setid,
                "action": "execute",
                "status": "executed",
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-11-20T10:00:10+00:00",
                        "ended_at": "2026-11-20T10:04:50+00:00",
                        "tokens": {
                            "input": tokens_total - 50,
                            "output": 50,
                            "total": tokens_total,
                        },
                        "cost": 0.25,
                    }
                ],
            }
        ],
    }
    if startup_exec_s is not None:
        state["startup_timings"] = {
            "invocation_kind": "start",
            "script_start_at": "2026-11-20T10:00:00+00:00",
            "first_output_at": "2026-11-20T10:00:01+00:00",
            "startup_to_first_output_seconds": 1.0,
            "first_execution_start_at": "2026-11-20T10:00:10+00:00",
            "startup_to_first_execution_seconds": startup_exec_s,
            "first_output_to_first_execution_seconds": max(0.0, startup_exec_s - 1.0),
        }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        json.dumps({"at": "2026-11-20T10:00:00+00:00", "event": "run-created"}) + "\n",
        encoding="utf-8",
    )
    return run_dir


def _run_cli(argv: list[str]) -> tuple[str, str, int]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return out.getvalue(), err.getvalue(), rc


class RunsAnalyzeExtraDirsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_inside_repo_runs_dir_includes_external_containers_single_run_and_other_repo(
        self,
    ) -> None:
        repo = self.root / "main-repo"
        (repo / ".aw" / "config").mkdir(parents=True)
        local_runs = repo / ".aw" / "records" / "runs"
        local_runs.mkdir(parents=True)
        _write_run(
            local_runs,
            "run-20261120T100000Z-1001",
            setid="localset",
            startup_exec_s=10.0,
        )

        # External runs container directory outside any repo
        ext_container = self.root / "external-backup-runs"
        _write_run(
            ext_container,
            "run-20261120T101000Z-2001",
            setid="backupset",
            startup_exec_s=20.0,
        )
        _write_run(
            ext_container,
            "run-20261120T102000Z-2002",
            setid="backupset",
            startup_exec_s=30.0,
        )

        # Another repo root passed directly to --runs-dir
        other_repo = self.root / "other-repo"
        other_runs = other_repo / ".aw" / "records" / "runs"
        _write_run(
            other_runs,
            "run-20261120T103000Z-3001",
            setid="otherset",
            startup_exec_s=40.0,
        )

        # Single external run directory passed directly to --runs-dir
        single_parent = self.root / "single-runs"
        single_run = _write_run(
            single_parent,
            "run-20261120T104000Z-4001",
            setid="singleset",
            startup_exec_s=50.0,
        )

        out, err, rc = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(ext_container),
                "--runs-dir",
                str(other_repo),
                "--runs-dir",
                str(single_run),
                "--json",
            ]
        )
        self.assertEqual(rc, 0, out + err)
        payload = json.loads(out)
        self.assertEqual(payload["data"]["totals"]["total"], 5)
        self.assertEqual(payload["data"]["totals"]["skip"], 0)
        self.assertEqual(payload["data"]["extra_runs_dirs"], 3)
        st = payload["data"]["startup_timings"]
        self.assertEqual(st["runs_analyzed"], 5)
        self.assertEqual(st["runs_with_startup_timings"], 5)
        self.assertAlmostEqual(
            st["metrics"]["startup_to_first_execution_seconds"]["median"], 30.0
        )

        # Positional setid target resolves into --runs-dir pool too!
        out_set, err_set, rc_set = _run_cli(
            [
                "runs",
                "analyze",
                "backupset",
                "--dir",
                str(repo),
                "--runs-dir",
                str(ext_container),
                "--json",
            ]
        )
        self.assertEqual(rc_set, 0, out_set + err_set)
        self.assertEqual(json.loads(out_set)["data"]["totals"]["total"], 2)

    def test_outside_any_repo_with_runs_dir_and_positional_container_dirs(self) -> None:
        # Completely non-repo working directory (no .git, no .aw)
        non_repo = self.root / "plain-scratch-dir"
        non_repo.mkdir()
        ext_a = self.root / "runs-a"
        ext_b = self.root / "runs-b"
        _write_run(
            ext_a, "run-20261120T110000Z-5001", setid="seta", startup_exec_s=12.0
        )
        _write_run(
            ext_b, "run-20261120T111000Z-5002", setid="setb", startup_exec_s=18.0
        )

        # Isolate HOME so ~/.aw/projects lands inside self.root and never touches real user home
        fake_home = self.root / "fake-home"
        fake_home.mkdir()
        orig_cwd = Path.cwd()
        orig_home = os.environ.get("HOME")
        try:
            os.environ["HOME"] = str(fake_home)
            os.chdir(non_repo)

            # 1. Via repeatable --runs-dir outside any repo (using cwd implicitly, no --dir)
            out, err, rc = _run_cli(
                [
                    "runs",
                    "analyze",
                    "--runs-dir",
                    str(ext_a),
                    "--runs-dir",
                    str(ext_b),
                    "--json",
                ]
            )
            self.assertEqual(rc, 0, out + err)
            payload = json.loads(out)
            self.assertEqual(payload["data"]["totals"]["total"], 2)
            self.assertEqual(payload["data"]["totals"]["skip"], 0)
            self.assertEqual(payload["data"]["startup_timings"]["runs_analyzed"], 2)
            self.assertAlmostEqual(
                payload["data"]["startup_timings"]["metrics"][
                    "startup_to_first_execution_seconds"
                ]["median"],
                15.0,
            )

            # Report exists and `aw runs analyze --path` + `aw runs query overview` work outside a repo
            out_path, err_path, rc_path = _run_cli(
                ["runs", "analyze", "--path", "--json"]
            )
            self.assertEqual(rc_path, 0, out_path + err_path)
            rel_report = json.loads(out_path)["data"]["path"]
            self.assertTrue((non_repo / rel_report).is_file())

            ov = run_analytics_query.run_query("overview", repo=non_repo)
            self.assertEqual(ov.payload["cached_runs"], 2)

            # 2. Via positional runs container directories directly outside any repo
            out2, err2, rc2 = _run_cli(
                ["runs", "analyze", str(ext_a), str(ext_b), "--json"]
            )
            self.assertEqual(rc2, 0, out2 + err2)
            payload2 = json.loads(out2)
            self.assertEqual(payload2["data"]["totals"]["total"], 2)
            self.assertEqual(payload2["data"]["totals"]["hit"], 2)
        finally:
            os.chdir(orig_cwd)
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home

    def test_duplicate_run_names_across_distinct_runs_dirs_partition_cleanly_in_cache(
        self,
    ) -> None:
        repo = self.root / "repo-dup"
        (repo / ".aw" / "config").mkdir(parents=True)
        local_runs = repo / ".aw" / "records" / "runs"
        ext_runs = self.root / "ext-dup"
        shared_name = "run-20261120T120000Z-7777"
        _write_run(local_runs, shared_name, tokens_total=100, startup_exec_s=10.0)
        _write_run(ext_runs, shared_name, tokens_total=300, startup_exec_s=30.0)

        out, err, rc = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(ext_runs),
                "--json",
            ]
        )
        self.assertEqual(rc, 0, out + err)
        payload = json.loads(out)
        self.assertEqual(payload["data"]["totals"]["total"], 2)
        self.assertEqual(payload["data"]["totals"]["skip"], 0)
        # Both runs have distinct cache entries under distinct pseudonymized source_root_ids
        entries = list(
            run_analytics_cache.cache_root(repo).rglob(
                run_analytics_cache.ENTRY_FILENAME
            )
        )
        self.assertEqual(len(entries), 2)
        st = payload["data"]["startup_timings"]
        self.assertEqual(st["runs_with_startup_timings"], 2)
        self.assertAlmostEqual(
            st["metrics"]["startup_to_first_execution_seconds"]["median"], 20.0
        )

    def test_refuses_missing_file_or_analytics_runs_dir_and_allows_empty_dir(
        self,
    ) -> None:
        repo = self.root / "repo-val"
        (repo / ".aw" / "config").mkdir(parents=True)
        (repo / ".aw" / "records" / "runs").mkdir(parents=True)

        # Missing path -> exit 2
        out, err, rc = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(self.root / "does-not-exist"),
                "--json",
            ]
        )
        self.assertEqual(rc, 2, out + err)

        # Regular file -> exit 2
        f = self.root / "not-a-dir.txt"
        f.write_text("hi\n", encoding="utf-8")
        out_f, err_f, rc_f = _run_cli(
            ["runs", "analyze", "--dir", str(repo), "--runs-dir", str(f), "--json"]
        )
        self.assertEqual(rc_f, 2, out_f + err_f)

        # Local analytics tree -> exit 2
        local_analytics = repo / ".aw" / "records" / "runs" / "analytics"
        local_analytics.mkdir(parents=True)
        out_a, err_a, rc_a = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(local_analytics),
                "--json",
            ]
        )
        self.assertEqual(rc_a, 2, out_a + err_a)

        # External analytics snapshot tree -> refused both via --runs-dir and positional target
        ext_analytics = self.root / "other" / "analytics"
        ext_snap = ext_analytics / "snapshots" / "s1"
        ext_snap.mkdir(parents=True)
        (ext_analytics / "manifest.json").write_text("{}", encoding="utf-8")
        _write_run(ext_snap, "run-20261120T120000Z-8888")
        out_ea, err_ea, rc_ea = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(ext_snap),
                "--json",
            ]
        )
        self.assertEqual(rc_ea, 2, out_ea + err_ea)
        resolved_ext, unresolved_ext = run_viewer.resolve_target_runs_detailed(
            [str(ext_snap)], repo
        )
        self.assertEqual(resolved_ext, [])
        self.assertEqual(unresolved_ext, [str(ext_snap)])

        # Existing empty runs dir -> succeeds with 0 runs
        empty_dir = self.root / "empty-runs"
        empty_dir.mkdir()
        out_e, err_e, rc_e = _run_cli(
            [
                "runs",
                "analyze",
                "--dir",
                str(repo),
                "--runs-dir",
                str(empty_dir),
                "--json",
            ]
        )
        self.assertEqual(rc_e, 0, out_e + err_e)
        self.assertEqual(json.loads(out_e)["data"]["totals"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
