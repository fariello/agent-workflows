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

import re
from typing import Any
from unittest import mock

from tests.conformance_matrix import run_cli_inproc
from tests.support import git, init_repo


def _run_cli_with_fallback(*args: str, cwd: Path) -> Any:
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
    return run_cli_inproc(list(args), cwd=cwd)


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


def _anchored_repo(td: str, tree: str) -> Path:
    """A temp git repo anchored as a project BEFORE any CLI call (fixture-anchoring, akhwp7 F-9).

    ``backlog check``, ``attention --check`` and ``research check-refs`` climb to the nearest
    ancestor project; creating ``.aw/records/<tree>`` first keeps them inside the temp repo.
    """
    repo = init_repo(Path(td))
    (repo / ".aw" / "records" / tree).mkdir(parents=True, exist_ok=True)
    return repo


def _new_backlog_item(repo: Path) -> None:
    proc = _run_cli_with_fallback(
        "backlog",
        "new",
        "--summary",
        "Probe item",
        "--priority",
        "low",
        "--work-kind",
        "chore",
        "--apply",
        cwd=repo,
    )
    assert proc.returncode == 0, f"backlog new failed: {proc.stdout}{proc.stderr}"


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

    def test_specs_check_human_emits_checked_zero_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            (repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
            proc = _run_cli_with_fallback("specs", "check", "--no-color", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"specs check failed: {proc.stderr}")
            self.assertIn("0 specs checked", proc.stdout)
            self.assertIn("all specs conform", proc.stdout)

    def test_specs_check_human_emits_checked_nonzero_control(self):
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
            proc = _run_cli_with_fallback("specs", "check", "--no-color", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"specs check failed: {proc.stderr}")
            self.assertIn("1 specs checked", proc.stdout)
            self.assertIn("all specs conform", proc.stdout)


class HumanCheckedCountTests(unittest.TestCase):
    """rolswj/akhwp7: the HUMAN surface of four check commands states its examined count."""

    # --- backlog check ---------------------------------------------------------------------
    def test_backlog_check_human_emits_checked_zero_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "backlog/open")
            proc = _run_cli_with_fallback("backlog", "check", "--no-color", cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(
                "all backlog items conform. 0 backlog items checked.", proc.stdout
            )

    def test_backlog_check_human_emits_checked_nonzero_control(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "backlog/open")
            _new_backlog_item(repo)
            proc = _run_cli_with_fallback("backlog", "check", "--no-color", cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(
                "all backlog items conform. 1 backlog items checked.", proc.stdout
            )

    # --- attention --check -----------------------------------------------------------------
    def test_attention_check_human_emits_checked_zero_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "backlog/open")
            proc = _run_cli_with_fallback(
                "attention", "--check", "--no-color", cwd=repo
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(
                "the view is valid. 0 items checked, 0 violations.", proc.stdout
            )

    def test_attention_check_human_count_matches_json_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "backlog/open")
            _new_backlog_item(repo)
            proc = _run_cli_with_fallback(
                "attention", "--check", "--no-color", cwd=repo
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(
                "the view is valid. 1 items checked, 0 violations.", proc.stdout
            )
            m = re.search(r"(\d+) items checked", proc.stdout)
            self.assertIsNotNone(m, proc.stdout)
            jproc = _run_cli_with_fallback("attention", "--check", "--json", cwd=repo)
            self.assertEqual(jproc.returncode, 0, jproc.stderr)
            payload = json.loads(jproc.stdout)
            self.assertEqual(payload["evidence"][0]["value"]["items"], int(m.group(1)))

    # --- research check-refs ---------------------------------------------------------------
    def test_research_check_refs_reports_zero_files_on_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "plans")
            proc = _run_cli_with_fallback("research", "check-refs", cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("no dangling citations across 0 files", proc.stdout)
            aproc = _run_cli_with_fallback(
                "research", "check-refs", "--agent", cwd=repo
            )
            self.assertEqual(aproc.returncode, 0, aproc.stderr)
            self.assertEqual(_parse_agent_result(aproc.stdout)["checked"], 0)

    def test_research_check_refs_reports_files_on_dangling_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _anchored_repo(td, "plans")
            (repo / ".aw" / "records" / "plans" / "note.md").write_text(
                "See RSCH-zzz999 for details.\n", encoding="utf-8"
            )
            proc = _run_cli_with_fallback("research", "check-refs", cwd=repo)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("zzz999", proc.stdout)
            self.assertIn("across 1 files", proc.stdout)
            aproc = _run_cli_with_fallback(
                "research", "check-refs", "--agent", cwd=repo
            )
            self.assertEqual(aproc.returncode, 1, aproc.stderr)
            self.assertEqual(_parse_agent_result(aproc.stdout)["checked"], 1)

    # --- check-local-leaks (aw sanitize) ---------------------------------------------------
    def _leak_repo(self, td: str) -> Path:
        repo = init_repo(Path(td) / "repo")
        (repo / "README.txt").write_text("hello world\n", encoding="utf-8")
        git(repo, "add", "README.txt")
        git(repo, "commit", "-q", "-m", "init")
        return repo

    def test_sanitize_reports_files_checked_on_clean_repo(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(
            os.environ, {"XDG_CONFIG_HOME": str(Path(td) / "cfg")}
        ):
            repo = self._leak_repo(td)
            proc = _run_cli_with_fallback(
                "check-local-leaks", str(repo), "--no-color", cwd=repo
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("No local leaks found. 1 files checked.", proc.stderr)
            aproc = _run_cli_with_fallback(
                "check-local-leaks", str(repo), "--agent", cwd=repo
            )
            self.assertEqual(aproc.returncode, 0, aproc.stderr)
            self.assertEqual(_parse_agent_result(aproc.stdout)["checked"], 1)

    def test_sanitize_reports_files_checked_on_leaking_repo(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(
            os.environ, {"XDG_CONFIG_HOME": str(Path(td) / "cfg")}
        ):
            repo = self._leak_repo(td)
            (repo / "leak.txt").write_text(
                "path " + "/home/" + "someuser" + "/x\n", encoding="utf-8"
            )
            git(repo, "add", "leak.txt")
            git(repo, "commit", "-q", "-m", "leak")
            proc = _run_cli_with_fallback(
                "check-local-leaks", str(repo), "--no-color", cwd=repo
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("home-path", proc.stderr)
            self.assertIn("across 2 files", proc.stderr)


if __name__ == "__main__":
    unittest.main()
