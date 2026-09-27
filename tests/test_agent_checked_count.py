"""Tests that --agent records emit checked:0 instead of omitting the count (IPD kifrou).

Verifies that aw specs check --agent and aw backlog check --agent report
{"checked": 0} on empty artifact trees rather than omitting the count key,
and includes a non-zero control asserting {"checked": 1}.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.support import init_repo, run_cli


def _run_cli_with_fallback(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    unfixed_tree = os.environ.get("AW_UNFIXED_TREE")
    if unfixed_tree:
        env = dict(os.environ)
        env["PYTHONPATH"] = unfixed_tree
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows.cli", *args],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    return run_cli(*args, cwd=cwd)


def _parse_agent_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("schema") == "aw.agent/v1" and data.get("kind") == "result":
            return data
    raise AssertionError(f"No aw.agent/v1 result record found in stdout:\n{stdout}")


class AgentCheckedCountTests(unittest.TestCase):
    def test_specs_check_agent_emits_checked_zero_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            (repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
            proc = _run_cli_with_fallback("specs", "check", "--agent", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"specs check failed: {proc.stderr}")
            rec = _parse_agent_result(proc.stdout)
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["cmd"], "specs check")
            self.assertIn("checked", rec)
            self.assertEqual(rec["checked"], 0)

    def test_backlog_check_agent_emits_checked_zero_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            (repo / ".aw" / "records" / "backlog" / "open").mkdir(
                parents=True, exist_ok=True
            )
            proc = _run_cli_with_fallback("backlog", "check", "--agent", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"backlog check failed: {proc.stderr}")
            rec = _parse_agent_result(proc.stdout)
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["cmd"], "backlog check")
            self.assertIn("checked", rec)
            self.assertEqual(rec["checked"], 0)

    def test_checked_count_non_zero_control(self):
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            (repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
            new_proc = _run_cli_with_fallback(
                "specs",
                "new",
                "--title",
                "Control Spec",
                "--slug",
                "control-spec",
                "--apply",
                cwd=repo,
            )
            self.assertEqual(
                new_proc.returncode, 0, f"specs new failed: {new_proc.stderr}"
            )
            proc = _run_cli_with_fallback("specs", "check", "--agent", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"specs check failed: {proc.stderr}")
            rec = _parse_agent_result(proc.stdout)
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["cmd"], "specs check")
            self.assertIn("checked", rec)
            self.assertEqual(rec["checked"], 1)


if __name__ == "__main__":
    unittest.main()
