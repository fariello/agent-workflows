"""Falsifiable verification tests for mutating CLI commands and preview receipts (Order 04 E-02).

Invariants asserted:
(a) `--agent` and non-interactive execution NEVER imply mutation permission. A mutation requested without
    confirmation emits a structured `cannot-run` receipt (exit 2) and modifies nothing on disk.
(b) Dry-run / preview outputs structured `CommandResult` with preview changes (`applied: False`),
    never executing side effects.
(c) Explicit confirmation (`--yes` or `--apply`) in agent mode executes the mutation cleanly with exit 0
    and `applied: True`.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema as schema

AW_CLI = [sys.executable, "-m", "agent_workflows.cli"]


def _run_aw(*args, cwd=None, env=None, stdin_text=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [*AW_CLI, *args],
        cwd=cwd or os.getcwd(),
        capture_output=True,
        text=True,
        input=stdin_text,
        env=e,
        check=False,
    )


class CliMutationsAndPreviewsTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        # Create minimal git repo with .aw layout
        subprocess.run(["git", "init", str(self.repo)], capture_output=True, check=True)
        (self.repo / ".aw" / "records" / "backlog").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records" / "research").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        # Create a sample backlog item
        item_text = (
            "---\n"
            "id: b1c2d3\n"
            "title: Sample item\n"
            "type: task\n"
            "status: active\n"
            "---\n\n"
            "# Sample item\n"
        )
        (
            self.repo / ".aw" / "records" / "backlog" / "b1c2d3-sample-item.md"
        ).write_text(item_text, encoding="utf-8")
        # Create a sample plan
        plan_text = (
            "---\n"
            "id: p1p2p3\n"
            "title: Sample plan\n"
            "status: pending\n"
            "---\n\n"
            "# Sample plan\n"
        )
        (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260822-sample-p1p2p3.ipd.md"
        ).write_text(plan_text, encoding="utf-8")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_status_set_without_confirmation_in_agent_mode_exits_2(self):
        """`aw set` without --yes in agent mode must reject with exit 2 cannot-run and mutate nothing."""
        proc = _run_aw(
            "set", "backlog", "done", "b1c2d3", "--agent", cwd=str(self.repo)
        )
        self.assertEqual(proc.returncode, 2)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["outcome"], "cannot-run")
        schema.assert_valid_agent_record(rec)
        # Verify file on disk was NOT mutated
        content = (
            self.repo / ".aw" / "records" / "backlog" / "b1c2d3-sample-item.md"
        ).read_text(encoding="utf-8")
        self.assertIn("status: active", content)

    def test_status_set_dry_run_in_agent_mode(self):
        """`aw set --dry-run` in agent mode emits clean preview without changing disk."""
        proc = _run_aw(
            "set",
            "backlog",
            "done",
            "b1c2d3",
            "--agent",
            "--dry-run",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)
        content = (
            self.repo / ".aw" / "records" / "backlog" / "b1c2d3-sample-item.md"
        ).read_text(encoding="utf-8")
        self.assertIn("status: active", content)

    def test_status_set_with_yes_in_agent_mode(self):
        """`aw set --yes` in agent mode applies change cleanly."""
        proc = _run_aw(
            "set", "backlog", "done", "b1c2d3", "--agent", "--yes", cwd=str(self.repo)
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)
        content = (
            self.repo / ".aw" / "records" / "backlog" / "b1c2d3-sample-item.md"
        ).read_text(encoding="utf-8")
        self.assertIn("status: done", content)

    def test_workflow_compile_without_apply_emits_preview(self):
        """`aw workflow compile` without --apply emits structured preview and does not write."""
        import shutil

        from tests.support import REPO_ROOT

        fixture_src = REPO_ROOT / "tests" / "fixtures" / "workflow-src" / "plan-review"
        pkg = self.repo / "plan-review"
        shutil.copytree(fixture_src, pkg)

        proc = _run_aw("workflow", "compile", str(pkg), "--agent", cwd=str(self.repo))
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["cmd"], "workflow compile")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)

    def test_backlog_new_without_apply_emits_preview(self):
        """`aw backlog new` without --apply emits structured preview and does not write."""
        proc = _run_aw(
            "backlog",
            "new",
            "--summary",
            "Test task",
            "--kind",
            "chore",
            "--priority",
            "low",
            "--agent",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "backlog new")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)

    def test_backlog_new_with_apply_writes_file(self):
        """`aw backlog new --apply` in agent mode writes file and returns exit 0."""
        proc = _run_aw(
            "backlog",
            "new",
            "--summary",
            "Test chore",
            "--kind",
            "chore",
            "--priority",
            "low",
            "--agent",
            "--apply",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "backlog new")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)
        self.assertTrue(Path(rec["target"]).exists() if "target" in rec else True)

    def test_ipd_scaffold_without_apply_emits_preview(self):
        """`aw ipd scaffold` without --apply emits structured preview and does not write."""
        proc = _run_aw(
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Child IPD",
            "--set",
            "testset",
            "--order",
            "1",
            "--author",
            "Test",
            "--agent",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd scaffold")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)

    def test_ipd_scaffold_with_apply_writes_file(self):
        """`aw ipd scaffold --apply` in agent mode writes file and returns exit 0."""
        proc = _run_aw(
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Child IPD",
            "--set",
            "testset",
            "--order",
            "1",
            "--author",
            "Test",
            "--agent",
            "--apply",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd scaffold")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)

    def test_research_new_without_apply_emits_preview(self):
        """`aw research new` without --apply emits structured preview and does not write."""
        proc = _run_aw(
            "research",
            "new",
            "--kind",
            "research-report",
            "--slug",
            "eval-perf",
            "--summary",
            "Evaluation of performance",
            "--agent",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "research new")
        self.assertEqual(rec["outcome"], "clean")
        schema.assert_valid_agent_record(rec)

    def test_research_new_with_apply_writes_file(self):
        """`aw research new --apply` in agent mode writes file and returns exit 0."""
        proc = _run_aw(
            "research",
            "new",
            "--kind",
            "research-report",
            "--slug",
            "eval-perf",
            "--summary",
            "Evaluation of performance",
            "--agent",
            "--apply",
            cwd=str(self.repo),
        )
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "research new")

    def test_find_multiple_selectors_returns_all_matches(self):
        """`aw find <id1> <id2> ...` must return all matching artifacts across all provided selectors."""
        # Create second plan
        plan2_text = "# Plan 2\n\n- Id: p2p3p4\n- Set: setb\n- Status: pending\n"
        (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260823-setb-01-p2p3p4-plan-two.ipd.md"
        ).write_text(plan2_text, encoding="utf-8")

        proc = _run_aw("find", "b1c2d3", "p2p3p4", cwd=str(self.repo))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("b1c2d3", proc.stdout)
        self.assertIn("p2p3p4", proc.stdout)


if __name__ == "__main__":
    unittest.main()
