"""Tests for Read and Check Commands Surface Migration.

awcliux Order 04 (`10jpsa`) E-01 / V-01.

Asserts:
1. Every read and check command routes through the unified renderer boundary.
2. Agent mode (`--agent` or non-TTY piped) emits valid `aw.agent/v1` records with honest exit codes.
3. No raw unrendered TSV or unmodeled print leaks exist across migrated handlers.
4. JSON mode (`--json`) emits valid structured JSON representations.
"""

from __future__ import annotations

import pytest

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_workflows import agent_schema as schema

# Heavy subprocess/CLI suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow

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

    def test_find_plans_agent_mode_emits_bare_paths_not_a_record(self):
        """`aw find --agent` is a DISCOVERY verb: bare repo-relative paths, NOT an agent record.

        This test previously demanded an `aw.agent/v1` record and became wrong when `findpaths-01`
        (`v8xdz4`) deliberately carved `find` out of the record contract: path discovery under
        `--agent` emits newline-delimited repo-relative paths because wrapping a path list in a JSON
        envelope costs tokens for no benefit. `docs/cli-output-contract.md:233-237` states that
        exemption explicitly, and `cli.py`'s `if getattr(args, "paths", False) or (ctx.is_agent and
        all_paths)` branch implements it AHEAD of the record branch.

        So the assertion is inverted rather than deleted: callers wanting the metadata dictionary use
        `--json`, which is asserted below. Deleting the case outright would leave the carve-out
        unpinned and let a future change silently re-wrap `find --agent` in an envelope.
        """
        proc = _run_aw("find", "plans", "--agent")
        self.assertEqual(proc.returncode, 0)
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        self.assertTrue(lines, "find --agent emitted nothing")
        # Bare paths, not JSON: no line may parse as an agent record.
        self.assertFalse(
            proc.stdout.lstrip().startswith("{"),
            f"find --agent must not emit a JSON envelope, got {lines[0]!r}",
        )
        for ln in lines:
            self.assertTrue(
                ln.startswith(".aw/") or ln.startswith(".agents/"),
                f"expected a bare repo-relative path, got {ln!r}",
            )

    def test_find_plans_json_mode_still_emits_the_structured_record(self):
        """The metadata dictionary remains available under `--json` (the documented escape hatch).

        `--json` emits the FULL structured representation (`command`/`exit_code`/`data`), which is a
        different shape from `--agent`'s compact record (`cmd`/`exit`), so this asserts the full-form
        keys rather than running `assert_valid_agent_record`. That distinction is the point of the
        carve-out above: `find --agent` gives paths, `find --json` gives metadata.
        """
        proc = _run_aw("find", "plans", "--json")
        self.assertEqual(proc.returncode, 0)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["command"], "find")
        self.assertEqual(rec["exit_code"], 0)
        self.assertIn("paths", rec["data"])
        self.assertIn("matches", rec["data"])

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
