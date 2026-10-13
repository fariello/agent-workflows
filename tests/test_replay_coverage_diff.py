"""Tests for tools/replay_coverage_diff.py.

Exercises baseline generation, dynamic context recording, function AST line mapping,
subprocess reach tracing, worktree-isolated deleted-test replay diffing, and refusal modes.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools import replay_coverage_diff


class TestCoverageRefusal(unittest.TestCase):
    """Refusal tests that run unconditionally without requiring coverage installed."""

    def test_coverage_not_installed_refusal(self) -> None:
        """When coverage cannot be imported, main exits 2 with actionable message."""
        buf = io.StringIO()
        with mock.patch.dict(sys.modules, {"coverage": None}):
            with mock.patch("sys.stderr", buf):
                ret = replay_coverage_diff.main(["baseline"])
        self.assertEqual(ret, 2)
        err = buf.getvalue()
        self.assertIn("coverage is not installed; pip install coverage", err)


def _git(repo_dir: str | Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        capture_output=True,
        text=True,
    )


@unittest.skipUnless(
    importlib.util.find_spec("coverage") is not None,
    "coverage not installed: audit-only tool",
)
class TestReplayCoverageDiff(unittest.TestCase):
    """Behavioral tests over synthesized repositories."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_replay_cov_")
        self.repo_dir = os.path.join(self.temp_dir, "repo")
        os.makedirs(self.repo_dir)

        # Initialize git repo
        _git(self.repo_dir, "init")
        _git(self.repo_dir, "config", "user.name", "Test Committer")
        _git(self.repo_dir, "config", "user.email", "test@example.com")
        _git(self.repo_dir, "config", "commit.gpgsign", "false")

        # Create package layout
        os.makedirs(os.path.join(self.repo_dir, "agent_workflows"))
        with open(
            os.path.join(self.repo_dir, "agent_workflows", "__init__.py"),
            "w",
            encoding="utf-8",
        ) as f:
            pass

        with open(
            os.path.join(self.repo_dir, "agent_workflows", "m.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "def a():\n"
                "    return 1\n\n"
                "def b():\n"
                "    return 2\n\n"
                "def c():\n"
                "    return 3\n"
            )

        os.makedirs(os.path.join(self.repo_dir, "tests"))
        with open(
            os.path.join(self.repo_dir, "tests", "__init__.py"),
            "w",
            encoding="utf-8",
        ) as f:
            pass

        with open(
            os.path.join(self.repo_dir, "tests", "test_m.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "import agent_workflows.m as m\n\n"
                "def test_a():\n"
                "    assert m.a() == 1\n"
            )

        _git(self.repo_dir, "add", ".")
        _git(self.repo_dir, "commit", "-m", "Initial commit with surviving tests")

        # Add deleted test file
        with open(
            os.path.join(self.repo_dir, "tests", "test_deleted.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "import agent_workflows.m as m\n\n"
                "def test_deleted_a_and_b():\n"
                "    assert m.a() == 1\n"
                "    assert m.b() == 2\n"
            )

        _git(self.repo_dir, "add", "tests/test_deleted.py")
        _git(self.repo_dir, "commit", "-m", "Add test_deleted.py")

        # Trim-delete test_deleted.py
        _git(self.repo_dir, "rm", "tests/test_deleted.py")
        _git(self.repo_dir, "commit", "-m", "Trim test_deleted.py")

        trim_res = _git(self.repo_dir, "rev-parse", "HEAD")
        self.trim_commit = trim_res.stdout.strip()

        self.script_path = str(
            Path(__file__).resolve().parent.parent / "tools" / "replay_coverage_diff.py"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, self.script_path, *args],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )

    def test_main_flow_exclusive_and_shared_lines(self) -> None:
        """Main flow: exclusive lines, shared lines, and root-relative worktree keying."""
        base_dir = os.path.join(self.temp_dir, "base_out")
        res_base = self._run_cli("baseline", "--out", base_dir, "--", "-p", "no:xdist")
        self.assertEqual(res_base.returncode, 0, res_base.stderr)

        res_diff = self._run_cli(
            "diff",
            self.trim_commit,
            "tests/test_deleted.py",
            "--baseline",
            base_dir,
            "--format",
            "json",
        )
        self.assertEqual(res_diff.returncode, 0, res_diff.stderr)

        data = json.loads(res_diff.stdout)
        self.assertEqual(len(data), 1)
        record = data[0]
        self.assertEqual(record["verdict"], "pass")
        self.assertEqual(record["tests_count"], 1)

        funcs = record["functions"]
        # 'b' was called only by deleted test: exclusive lines present, shared lines empty
        self.assertIn("agent_workflows/m.py::b", funcs)
        b_info = funcs["agent_workflows/m.py::b"]
        self.assertTrue(len(b_info["exclusive_lines"]) > 0)
        self.assertEqual(b_info["shared_lines"], [])
        self.assertEqual(b_info["baseline_contexts"], 0)

        # 'a' was called by both surviving and deleted test: exclusive empty, shared non-empty
        # (This asserts root-relative keying: if keying were broken across worktrees,
        # 'a' lines would incorrectly appear as exclusive instead of shared).
        self.assertIn("agent_workflows/m.py::a", funcs)
        a_info = funcs["agent_workflows/m.py::a"]
        self.assertEqual(a_info["exclusive_lines"], [])
        self.assertTrue(len(a_info["shared_lines"]) > 0)
        self.assertGreaterEqual(a_info["baseline_contexts"], 1)

        # Fixture repo git status and worktrees must remain clean
        st = _git(self.repo_dir, "status", "--porcelain", "--ignored")
        self.assertEqual(st.stdout.strip(), "")
        wts = _git(self.repo_dir, "worktree", "list")
        self.assertEqual(len(wts.stdout.strip().splitlines()), 1)

    def test_main_flow_contexts(self) -> None:
        """Baseline records non-empty test function context names reaching function bodies."""
        base_dir = os.path.join(self.temp_dir, "base_out")
        res_base = self._run_cli("baseline", "--out", base_dir, "--", "-p", "no:xdist")
        self.assertEqual(res_base.returncode, 0, res_base.stderr)

        base_file = os.path.join(base_dir, "baseline.json")
        with open(base_file, "r", encoding="utf-8") as f:
            base_json = json.load(f)

        self.assertIn("agent_workflows/m.py::a", base_json["functions"])
        a_data = base_json["functions"]["agent_workflows/m.py::a"]
        self.assertIn("tests.test_m.test_a", a_data["contexts"])
        self.assertFalse(a_data["subprocess_only"])

    def test_def_line_exclusion_uncalled_function_absent(self) -> None:
        """An uncalled function (c) is absent from baseline.json despite import-time def execution."""
        base_dir = os.path.join(self.temp_dir, "base_out")
        res_base = self._run_cli("baseline", "--out", base_dir, "--", "-p", "no:xdist")
        self.assertEqual(res_base.returncode, 0, res_base.stderr)

        base_file = os.path.join(base_dir, "baseline.json")
        with open(base_file, "r", encoding="utf-8") as f:
            base_json = json.load(f)

        # m.c was imported, executing `def c():`, but its body was never called.
        self.assertNotIn("agent_workflows/m.py::c", base_json["functions"])

    def test_subprocess_only_flag(self) -> None:
        """A function reached only via subprocess execution carries subprocess_only: true."""
        # Replace test_m.py so that it calls m.b() via subprocess
        with open(
            os.path.join(self.repo_dir, "tests", "test_m.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "import subprocess, sys\n"
                "import agent_workflows.m as m\n\n"
                "def test_a():\n"
                "    assert m.a() == 1\n\n"
                "def test_b_subp():\n"
                "    res = subprocess.run([sys.executable, '-c', 'import agent_workflows.m as m; assert m.b() == 2'])\n"
                "    assert res.returncode == 0\n"
            )
        _git(self.repo_dir, "add", "tests/test_m.py")
        _git(self.repo_dir, "commit", "-m", "Surviving test calls b via subprocess")

        base_dir = os.path.join(self.temp_dir, "base_out")
        res_base = self._run_cli("baseline", "--out", base_dir, "--", "-p", "no:xdist")
        self.assertEqual(res_base.returncode, 0, res_base.stderr)

        base_file = os.path.join(base_dir, "baseline.json")
        with open(base_file, "r", encoding="utf-8") as f:
            base_json = json.load(f)

        self.assertIn("agent_workflows/m.py::b", base_json["functions"])
        b_data = base_json["functions"]["agent_workflows/m.py::b"]
        self.assertTrue(b_data["subprocess_only"])
        self.assertEqual(b_data["contexts"], [])
        self.assertTrue(len(b_data["lines"]) > 0)

    def test_stale_baseline_refusal(self) -> None:
        """Diff against baseline.json with a mismatched head exits 2 and names both SHAs."""
        base_dir = os.path.join(self.temp_dir, "base_out")
        res_base = self._run_cli("baseline", "--out", base_dir, "--", "-p", "no:xdist")
        self.assertEqual(res_base.returncode, 0, res_base.stderr)

        base_file = os.path.join(base_dir, "baseline.json")
        with open(base_file, "r", encoding="utf-8") as f:
            base_json = json.load(f)

        current_head = base_json["head"]
        stale_sha = "0123456789abcdef0123456789abcdef01234567"
        base_json["head"] = stale_sha
        with open(base_file, "w", encoding="utf-8") as f:
            json.dump(base_json, f)

        res_diff = self._run_cli(
            "diff",
            self.trim_commit,
            "tests/test_deleted.py",
            "--baseline",
            base_dir,
        )
        self.assertEqual(res_diff.returncode, 2)
        self.assertIn(stale_sha, res_diff.stderr)
        self.assertIn(current_head, res_diff.stderr)


if __name__ == "__main__":
    unittest.main()
