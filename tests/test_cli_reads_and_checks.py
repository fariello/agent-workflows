"""Tests for Read and Check Commands Surface Migration.

awcliux Order 04 (`10jpsa`) E-01 / V-01.

Asserts:
1. Every read and check command routes through the unified renderer boundary.
2. Agent mode (`--agent` or non-TTY piped) emits valid `aw.agent/v1` records with honest exit codes.
3. No raw unrendered TSV or unmodeled print leaks exist across migrated handlers.
4. JSON mode (`--json`) emits valid structured JSON representations.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_workflows import agent_schema as schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_aw(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *args],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
    )


class CliReadsAndChecksTests(unittest.TestCase):
    """Assert all read and check leaves emit valid structured records (E-01 / V-01)."""

    def test_status_agent_mode(self):
        proc = _run_aw("status", "--agent")
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "status")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])
        schema.assert_valid_agent_record(rec)

    def test_status_json_mode(self):
        proc = _run_aw("status", "--json")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout.strip())
        self.assertEqual(data["schema"], "aw.agent/v1")
        self.assertIn("packaged_version", data["data"])
        self.assertIn("repositories", data["data"])

    def test_list_repos_agent_mode(self):
        proc = _run_aw("list-repos", "--agent")
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "list-repos")
        schema.assert_valid_agent_record(rec)

    def test_context_agent_mode(self):
        proc = _run_aw("context", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "context")
        schema.assert_valid_agent_record(rec)

    def test_path_agent_mode_prints_single_clean_path(self):
        proc = _run_aw("path", "records", "--agent")
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout.strip()
        self.assertTrue(out.startswith("/") or out.startswith("."))
        self.assertNotIn("\t", out)
        self.assertNotIn("\n", out)

    def test_project_status_agent_mode(self):
        proc = _run_aw("project", "status", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "project status")
        schema.assert_valid_agent_record(rec)

    def test_storage_status_agent_mode(self):
        proc = _run_aw("storage", "status", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "storage status")
        schema.assert_valid_agent_record(rec)

    def test_attention_check_agent_mode_replaces_tsv(self):
        """`aw attention --check --agent` must emit aw.agent/v1 result record, NEVER raw TSV."""
        proc = _run_aw("attention", "--check", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "attention")
        schema.assert_valid_agent_record(rec)

    def test_ipd_board_agent_mode(self):
        proc = _run_aw("ipd", "board", "--agent")
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd board")
        schema.assert_valid_agent_record(rec)

    def test_ipd_lint_agent_mode(self):
        proc = _run_aw("ipd", "lint", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd lint")
        schema.assert_valid_agent_record(rec)

    def test_check_all_agent_mode(self):
        proc = _run_aw("check", "all", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "check")
        schema.assert_valid_agent_record(rec)

    def test_find_plans_agent_mode(self):
        proc = _run_aw("find", "plans", "--agent")
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "find")
        schema.assert_valid_agent_record(rec)

    def test_specs_check_agent_mode_replaces_tsv(self):
        """`aw specs check --agent` must emit aw.agent/v1 record, NEVER raw TSV."""
        proc = _run_aw("specs", "check", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "specs check")
        schema.assert_valid_agent_record(rec)

    def test_backlog_check_agent_mode_replaces_tsv(self):
        """`aw backlog check --agent` must emit aw.agent/v1 record, NEVER raw TSV."""
        proc = _run_aw("backlog", "check", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "backlog check")
        schema.assert_valid_agent_record(rec)

    def test_check_local_leaks_agent_mode(self):
        proc = _run_aw("check-local-leaks", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "check-local-leaks")
        schema.assert_valid_agent_record(rec)

    def test_research_check_refs_agent_mode(self):
        proc = _run_aw("research", "check-refs", "--agent")
        self.assertIn(proc.returncode, (0, 1))
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "research check-refs")
        schema.assert_valid_agent_record(rec)


if __name__ == "__main__":
    unittest.main()
