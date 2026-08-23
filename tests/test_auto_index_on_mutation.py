"""Tests for automatic manifest index refresh on status transitions and mutations (IPD autoindex-01, hszr72)."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import plans_index, plans_refs, research_index, status_set


class TestAutoIndexOnMutation(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="aw_autoindex_test_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))

        # Setup standard layout
        self.plans_dir = self.tmp_dir / ".aw" / "records" / "plans"
        self.plans_pending = self.plans_dir / "pending"
        self.plans_executed = self.plans_dir / "executed"
        self.plans_pending.mkdir(parents=True, exist_ok=True)
        self.plans_executed.mkdir(parents=True, exist_ok=True)

        self.research_dir = self.tmp_dir / ".aw" / "records" / "research"
        self.research_open = self.research_dir / "open"
        self.research_done = self.research_dir / "done"
        self.research_open.mkdir(parents=True, exist_ok=True)
        self.research_done.mkdir(parents=True, exist_ok=True)

        self.backlog_dir = self.tmp_dir / ".aw" / "records" / "backlog"
        self.backlog_open = self.backlog_dir / "open"
        self.backlog_done = self.backlog_dir / "done"
        self.backlog_open.mkdir(parents=True, exist_ok=True)
        self.backlog_done.mkdir(parents=True, exist_ok=True)

    def _create_sample_plan(
        self,
        id6="ab12cd",
        status="to-review",
        set_id="testset",
        order=1,
        slug="sample-plan",
    ) -> Path:
        p = self.plans_pending / f"20260823-{set_id}-{order:02d}-{id6}-{slug}.ipd.md"
        content = f"""# IPD: Sample Plan

- Date: 2026-08-23
- Kind: child
- Status: {status}
- Set: {set_id}
- Order: {order}
- Author: Test Author
- Id: {id6}

## Workflow history
- 2026-08-23 {status} (test): created

## Goal
Sample goal.

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Sample task
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: test
  - Observed evidence:
  - Result: pending

## Open questions
### OQ-01: Sample question
- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: done
"""
        p.write_text(content, encoding="utf-8")
        return p

    def _create_sample_research(
        self,
        id6="res123",
        status="intake",
        set_id="resset",
        order=1,
        slug="sample-research",
    ) -> Path:
        p = (
            self.research_open
            / f"20260823-{set_id}-{order:02d}-{id6}-{slug}.sonnet5.findings.md"
        )
        content = f"""---
id: {id6}
set: {set_id}
order: {order:02d}
created: 20260823
model: sonnet5
kind: findings
status: {status}
outcome: none-yet
topic: [test-topic]
summary: Test summary
consumed-by: []
---

# Research: Sample Finding

## Workflow history
- 2026-08-23 {status} (test): created

## Findings
Sample findings.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def _create_sample_backlog(
        self, id6="bkl123", status="open", set_id="bklset", priority="high"
    ) -> Path:
        p = self.backlog_open / f"20260823-{set_id}-01-{id6}-sample-backlog.backlog.md"
        content = f"""# Backlog: Sample Item

- Date: 2026-08-23
- Id: {id6}
- Status: {status}
- Set: {set_id}
- Priority: {priority}
- Kind: feature
- Summary: sample backlog summary

## Workflow history
- 2026-08-23 {status} (test): created

Body
"""
        p.write_text(content, encoding="utf-8")
        return p

    def test_aw_set_plan_auto_refreshes_manifest_index(self):
        plan_file = self._create_sample_plan(id6="ab12cd", status="to-review")
        # Build initial index
        rc = plans_index.run_index(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                limit=None,
                check=False,
                agent=False,
                as_agent=False,
                json=False,
                no_color=True,
            )
        )
        self.assertEqual(rc, 0)

        index_json_path = self.plans_dir / "INDEX.json"
        self.assertTrue(index_json_path.exists())
        data = json.loads(index_json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["plan_id"], "ab12cd")
        self.assertEqual(data[0]["status"], "to-review")
        self.assertIn("pending", data[0]["path"])

        # Execute aw set executed ab12cd
        rc = status_set.run_set_command(
            ["executed", "ab12cd"],
            repo_root=self.tmp_dir,
            args=argparse.Namespace(dir=str(self.tmp_dir), yes=True),
        )
        self.assertEqual(rc, 0)

        # Verify plan moved to executed/
        executed_file = self.plans_executed / plan_file.name
        self.assertTrue(executed_file.exists())
        self.assertFalse(plan_file.exists())

        # Verify OQ status was NOT modified
        executed_text = executed_file.read_text(encoding="utf-8")
        self.assertIn("- Status: resolved", executed_text)

        # Verify INDEX.json was AUTOMATICALLY refreshed with executed status and path
        fresh_data = json.loads(index_json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fresh_data), 1)
        self.assertEqual(fresh_data[0]["plan_id"], "ab12cd")
        self.assertEqual(fresh_data[0]["status"], "executed")
        self.assertIn("executed", fresh_data[0]["path"])

        # Verify zero check drift
        drift = plans_index.check_drift(self.tmp_dir, self.plans_dir)
        self.assertEqual(drift, [])

    def test_aw_set_research_auto_refreshes_manifest_index(self):
        self._create_sample_research(id6="res123", status="intake")
        rc = research_index.run_index(
            argparse.Namespace(
                dir=str(self.tmp_dir), limit=None, check=False, agent=False
            )
        )
        self.assertEqual(rc, 0)

        index_json_path = self.research_dir / "INDEX.json"
        self.assertTrue(index_json_path.exists())
        data = json.loads(index_json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id6"], "res123")
        self.assertEqual(data[0]["status"], "intake")

        # Execute aw set research active res123
        rc = status_set.run_set_command(
            ["research", "active", "res123"],
            repo_root=self.tmp_dir,
            args=argparse.Namespace(dir=str(self.tmp_dir), yes=True),
        )
        self.assertEqual(rc, 0)

        # Verify INDEX.json was AUTOMATICALLY refreshed
        fresh_data = json.loads(index_json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fresh_data), 1)
        self.assertEqual(fresh_data[0]["id6"], "res123")
        self.assertEqual(fresh_data[0]["status"], "active")

        # Verify zero drift
        drift = research_index.check_drift(self.tmp_dir, self.research_dir)
        self.assertEqual(drift, [])

    def test_aw_set_non_indexed_type_no_op_clean(self):
        bkl_file = self._create_sample_backlog(id6="bkl123", status="open")
        rc = status_set.run_set_command(
            ["backlog", "done", "bkl123"],
            repo_root=self.tmp_dir,
            args=argparse.Namespace(dir=str(self.tmp_dir), yes=True),
        )
        self.assertEqual(rc, 0)
        done_file = self.backlog_done / bkl_file.name
        self.assertTrue(done_file.exists())
        self.assertFalse(bkl_file.exists())

    def test_aw_set_agent_output_includes_index_in_changes(self):
        self._create_sample_plan(id6="ag12cd", status="to-review")
        plans_index.run_index(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                limit=None,
                check=False,
                agent=False,
                as_agent=False,
                json=False,
                no_color=True,
            )
        )

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = status_set.run_set_command(
                ["executed", "ag12cd"],
                repo_root=self.tmp_dir,
                args=argparse.Namespace(dir=str(self.tmp_dir), as_agent=True, yes=True),
            )
        self.assertEqual(rc, 0)
        output = buf.getvalue()
        # Parse JSONL output
        lines = [line for line in output.strip().split("\n") if line.strip()]
        self.assertTrue(lines)
        rec = json.loads(lines[-1])
        self.assertEqual(rec["cmd"], "set")
        self.assertEqual(rec["outcome"], "clean")
        # Check that changes includes INDEX.json and INDEX.md
        changed_paths = [c.get("path", "") for c in rec.get("changes", [])]
        self.assertTrue(any("INDEX.json" in p for p in changed_paths))
        self.assertTrue(any("INDEX.md" in p for p in changed_paths))

    def test_aw_rename_plan_auto_refreshes_manifest_index(self):
        self._create_sample_plan(id6="mv12cd", status="to-review", slug="old-slug")
        plans_index.run_index(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                limit=None,
                check=False,
                agent=False,
                as_agent=False,
                json=False,
                no_color=True,
            )
        )

        # Run plans_refs.run_mv with apply=True
        rc = plans_refs.run_mv(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                id="mv12cd",
                slug="new-fresh-slug",
                apply=True,
                no_refs=True,
            )
        )
        self.assertEqual(rc, 0)

        # Verify INDEX.json was automatically updated with new-fresh-slug
        index_json_path = self.plans_dir / "INDEX.json"
        data = json.loads(index_json_path.read_text(encoding="utf-8"))
        matched = [e for e in data if e.get("plan_id") == "mv12cd"]
        self.assertEqual(len(matched), 1)
        self.assertIn("new-fresh-slug", matched[0]["path"])

        # Verify check_drift is clean
        drift = plans_index.check_drift(self.tmp_dir, self.plans_dir)
        self.assertEqual(drift, [])

    def test_aw_group_plan_auto_refreshes_manifest_index(self):
        self._create_sample_plan(id6="gp12cd", status="to-review", set_id="oldset")
        plans_index.run_index(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                limit=None,
                check=False,
                agent=False,
                as_agent=False,
                json=False,
                no_color=True,
            )
        )

        # Run plans_refs.run_set_assign with apply=True
        rc = plans_refs.run_set_assign(
            argparse.Namespace(
                dir=str(self.tmp_dir),
                ids=["gp12cd"],
                set="newbrandset",
                order=5,
                rename=True,
                apply=True,
                no_refs=True,
            )
        )
        self.assertEqual(rc, 0)

        # Verify INDEX.json was automatically updated with newbrandset
        index_json_path = self.plans_dir / "INDEX.json"
        data = json.loads(index_json_path.read_text(encoding="utf-8"))
        matched = [e for e in data if e.get("plan_id") == "gp12cd"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["set_id"], "newbrandset")
        self.assertEqual(matched[0]["order"], 5)

        # Verify check_drift is clean
        drift = plans_index.check_drift(self.tmp_dir, self.plans_dir)
        self.assertEqual(drift, [])


if __name__ == "__main__":
    unittest.main()
