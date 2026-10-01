"""Subdirectory repo-root resolution regression tests for `aw runs`.

Pins that all four `aw runs` root-resolution sites climb to the project root
via `project_context.resolve_verb_repo_root`:
- `run_viewer.run_viewer_cli` (viewer inspection and repair)
- `run_cli.resolve_ledger_path` (ledger readers)
- `run_cli._classify_absent_target` (driver-run signpost in refusal)
- `run_analytics_cli._repo_root` (analytics report publisher)

And pins that emitted `run_dir` is repo-relative across `--json` and `--agent`
for both canonical and legacy run roots.

All fixtures are built in temporary directories; never reads the live checkout's
runs tree. Every test restores `os.chdir` in a `finally` block.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows.project_context import find_project_root, resolve_verb_repo_root
from agent_workflows.run_ledger_store import RunLedgerStore
from agent_workflows.runner_shared import state_root


def _run_cli(args: list[str]) -> tuple[str, str, int]:
    """Invoke CLI with stdout and stderr redirected. Returns (out, err, rc)."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(args)
    except SystemExit as exc:
        rc = int(exc.code or 0)
    return out.getvalue(), err.getvalue(), rc


def _build_fixture_repo(root: Path) -> tuple[Path, Path]:
    """Create a project fixture with .aw/records/, a driver run, and sub/deeper/."""
    records_dir = root / ".aw" / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    runs_dir = records_dir / "runs"
    run_dir = runs_dir / "run-abc123"
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "run_id": "run-abc123",
        "created_at": "2026-09-01T00:00:00+00:00",
        "updated_at": "2026-09-01T01:00:00+00:00",
        "driver": {"path": "agent_workflows/oc_runipd.py", "host": "opencode"},
        "options": {"base_branch": "main", "worktree": "clean"},
        "selectors": ["set123"],
        "queue": [
            {
                "position": 1,
                "id6": "aaa111",
                "setid": "set123",
                "action": "execute",
                "status": "complete",
                "configured_file": "",
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")

    sub_dir = root / "sub" / "deeper"
    sub_dir.mkdir(parents=True, exist_ok=True)
    return root, sub_dir


class RunsSubdirRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        _, self.sub = _build_fixture_repo(self.root)
        self.orig_cwd = os.getcwd()

    def tearDown(self) -> None:
        os.chdir(self.orig_cwd)
        self.tmp.cleanup()

    def test_a_runs_viewer_renders_from_subdir(self) -> None:
        """(a) aw runs <run-id> from sub/ renders rather than refusing, matching root."""
        os.chdir(self.sub)
        try:
            # Assert climb stops at fixture (F-19)
            self.assertEqual(find_project_root(), self.root)
            self.assertEqual(resolve_verb_repo_root(), self.root)

            sub_out, sub_err, sub_rc = _run_cli(["runs", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        os.chdir(self.root)
        try:
            root_out, root_err, root_rc = _run_cli(["runs", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        self.assertEqual(sub_rc, 0)
        self.assertEqual(sub_rc, root_rc)
        self.assertIn("run-abc123", sub_out)
        self.assertNotIn("error: no run matched target", sub_out)
        self.assertEqual(sub_out, root_out)

    def test_b_runs_repair_resolves_from_subdir(self) -> None:
        """(b) aw runs repair <run-id> from sub/ resolves same run, matching root."""
        os.chdir(self.sub)
        try:
            self.assertEqual(find_project_root(), self.root)
            sub_out, sub_err, sub_rc = _run_cli(["runs", "repair", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        os.chdir(self.root)
        try:
            root_out, root_err, root_rc = _run_cli(["runs", "repair", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        self.assertEqual(sub_rc, 0)
        self.assertEqual(sub_rc, root_rc)
        self.assertIn("run-abc123: nothing to repair", sub_out)
        self.assertNotIn("error: no run matched target", sub_out)
        self.assertEqual(sub_out, root_out)

    def test_c_runs_show_ledger_resolves_from_subdir(self) -> None:
        """(c) aw runs show <ledger-run-id> from sub/ resolves same ledger, matching root."""
        ledger_dir = state_root(self.root) / "run-0000abcd"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        store = RunLedgerStore(ledger_dir / "ledger.jsonl")
        store.append(
            {
                "schema_version": 1,
                "kind": "run",
                "run_id": "run-0000abcd",
                "actor": "runtime",
                "parent": "",
                "workflow_digest": "sha256:" + "0" * 64,
                "requirement_digest": "sha256:" + "0" * 64,
                "repo": "test-repo",
                "head": "0000abcd",
            }
        )

        os.chdir(self.sub)
        try:
            self.assertEqual(find_project_root(), self.root)
            sub_out, sub_err, sub_rc = _run_cli(["runs", "show", "run-0000abcd"])
        finally:
            os.chdir(self.orig_cwd)

        os.chdir(self.root)
        try:
            root_out, root_err, root_rc = _run_cli(["runs", "show", "run-0000abcd"])
        finally:
            os.chdir(self.orig_cwd)

        self.assertNotIn("error: ledger file not found", sub_out)
        self.assertEqual(sub_rc, root_rc)
        self.assertIn("Run: run-0000abcd", sub_out)
        self.assertEqual(sub_out, root_out)

    def test_d_runs_show_driver_signpost_from_subdir(self) -> None:
        """(d) aw runs show <driver-run-id> from sub/ emits driver-run signpost."""
        os.chdir(self.sub)
        try:
            self.assertEqual(find_project_root(), self.root)
            sub_out, sub_err, sub_rc = _run_cli(["runs", "show", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        os.chdir(self.root)
        try:
            root_out, root_err, root_rc = _run_cli(["runs", "show", "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)

        self.assertEqual(sub_rc, 2)
        self.assertEqual(sub_rc, root_rc)
        signpost = (
            "That target IS a driver run (it has a state.json and an events.jsonl)"
        )
        self.assertIn(signpost, sub_out)
        self.assertIn("aw runs run-abc123", sub_out)
        self.assertIn("aw runs repair run-abc123", sub_out)
        self.assertEqual(sub_out, root_out)
        self.assertNotIn(str(self.root), sub_out)

        # Fail-open check: classifier condition requires state.json
        events_only = self.root / ".aw" / "records" / "runs" / "run-eventsonly"
        events_only.mkdir(parents=True, exist_ok=True)
        (events_only / "events.jsonl").write_text("{}\n", encoding="utf-8")
        os.chdir(self.sub)
        try:
            eo_out, _, eo_rc = _run_cli(["runs", "show", "run-eventsonly"])
            rep_out, _, rep_rc = _run_cli(["runs", "repair", "run-eventsonly"])
        finally:
            os.chdir(self.orig_cwd)
        self.assertNotIn(signpost, eo_out)
        self.assertEqual(rep_rc, 2)

    def test_e_runs_analyze_publishes_in_repo_from_subdir(self) -> None:
        """(e) aw runs analyze from sub/ publishes inside fixture, no .aw/projects/ tree."""
        projects_dir = Path.home() / ".aw" / "projects"
        before_projects = (
            set(projects_dir.glob("deeper-*")) if projects_dir.exists() else set()
        )

        os.chdir(self.sub)
        try:
            self.assertEqual(find_project_root(), self.root)
            sub_out, sub_err, sub_rc = _run_cli(["runs", "analyze", "--agent"])
        finally:
            os.chdir(self.orig_cwd)

        after_projects = (
            set(projects_dir.glob("deeper-*")) if projects_dir.exists() else set()
        )
        new_projects = after_projects - before_projects
        for p in new_projects:
            shutil.rmtree(p, ignore_errors=True)

        self.assertEqual(
            new_projects, set(), f"Created outside-repo project trees: {new_projects}"
        )
        self.assertEqual(sub_rc, 1)

        payload = json.loads(sub_out.strip().splitlines()[-1])
        evidence = payload.get("evidence", [])
        report_entries = [e for e in evidence if e.startswith("report:")]
        self.assertTrue(report_entries, f"No report: entry in evidence: {evidence}")
        report_path = report_entries[0]
        self.assertNotIn("../", report_path)
        self.assertNotIn(".aw/projects/", report_path)
        self.assertTrue(
            (
                self.root
                / ".aw"
                / "records"
                / "runs"
                / "analytics"
                / "latest"
                / "index.html"
            ).is_file()
        )

    def test_f_explicit_dir_honored_verbatim_from_subdir(self) -> None:
        """(f) explicit --dir is honored verbatim from subdirectory."""
        os.chdir(self.sub)
        try:
            out, err, rc = _run_cli(["runs", "--dir", str(self.root), "run-abc123"])
        finally:
            os.chdir(self.orig_cwd)
        self.assertEqual(rc, 0)
        self.assertIn("run-abc123", out)
        self.assertNotIn("error: no run matched target", out)

    def test_g_outside_project_behavior_unchanged(self) -> None:
        """(g) invoked outside any project, behavior matches cwd fallback."""
        with tempfile.TemporaryDirectory() as td_non_project:
            non_proj = Path(td_non_project).resolve()
            os.chdir(non_proj)
            try:
                out, err, rc = _run_cli(["runs", "run-abc123"])
            finally:
                os.chdir(self.orig_cwd)
        self.assertEqual(rc, 2)
        self.assertIn("error: no run matched target 'run-abc123'", err)

    def test_h_emitted_run_dir_repo_relative_both_surfaces_both_roots(self) -> None:
        """(h) emitted run_dir is repo-relative for canonical and legacy roots, --json and --agent."""
        # Canonical run is run-abc123 under .aw/records/runs/
        # Add legacy fixture run under .aw/runs/
        legacy_dir = self.root / ".aw" / "runs" / "run-legacy1"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        l_state = {
            "run_id": "run-legacy1",
            "created_at": "2026-09-01T00:00:00+00:00",
            "updated_at": "2026-09-01T01:00:00+00:00",
            "driver": {"path": "agent_workflows/oc_runipd.py", "host": "opencode"},
            "options": {"base_branch": "main", "worktree": "clean"},
            "selectors": ["set123"],
            "queue": [],
        }
        (legacy_dir / "state.json").write_text(json.dumps(l_state), encoding="utf-8")

        os.chdir(self.sub)
        try:
            self.assertEqual(find_project_root(), self.root)

            # Canonical root --json
            c_json_out, _, c_json_rc = _run_cli(["runs", "--json", "run-abc123"])
            self.assertEqual(c_json_rc, 0)
            c_json_data = json.loads(c_json_out)
            self.assertEqual(
                c_json_data["runs"][0]["run_dir"], ".aw/records/runs/run-abc123"
            )

            # Canonical root --agent
            c_ag_out, _, c_ag_rc = _run_cli(["runs", "--agent", "run-abc123"])
            self.assertEqual(c_ag_rc, 0)
            c_ag_data = json.loads(c_ag_out.strip().splitlines()[0])
            self.assertEqual(c_ag_data["run_dir"], ".aw/records/runs/run-abc123")

            # Legacy root --json
            l_json_out, _, l_json_rc = _run_cli(["runs", "--json", "run-legacy1"])
            self.assertEqual(l_json_rc, 0)
            l_json_data = json.loads(l_json_out)
            self.assertEqual(l_json_data["runs"][0]["run_dir"], ".aw/runs/run-legacy1")

            # Legacy root --agent
            l_ag_out, _, l_ag_rc = _run_cli(["runs", "--agent", "run-legacy1"])
            self.assertEqual(l_ag_rc, 0)
            l_ag_data = json.loads(l_ag_out.strip().splitlines()[0])
            self.assertEqual(l_ag_data["run_dir"], ".aw/runs/run-legacy1")
        finally:
            os.chdir(self.orig_cwd)
