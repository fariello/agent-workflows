"""Behavioral unit and integration tests for tools/deleted_test_replay.py.

Exercises the deleted-test replay harness across all verdict classes (pass, fail,
error-import, error-collect, no-tests, timeout), isolation invariants, and CLI
subprocess invocations over a synthesized throwaway git repository.
Per E-02, P16, and project conventions:
- References NEITHER real trim commit shas NOR the live tree.
- Carries NO livecorpus marker.
- Uses only synthesized tmp_path repositories.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.deleted_test_replay import replay_file


class DeletedTestReplayBehavioralTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="test_replay_fixture_")
        self.addCleanup(self._td.cleanup)
        self.repo_dir = Path(self._td.name).resolve()
        self._setup_fixture_repo()

    def _git(self, *args: str) -> str:
        res = subprocess.run(
            ["git", "-C", str(self.repo_dir)] + list(args),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def _assert_clean_repo(self) -> None:
        status = self._git("status", "--porcelain")
        self.assertEqual(status, "", f"Repo working tree is not clean: {status!r}")
        wt_list = self._git("worktree", "list").splitlines()
        self.assertEqual(
            len(wt_list),
            1,
            f"Expected only 1 worktree (main), got: {wt_list}",
        )

    def _setup_fixture_repo(self) -> None:
        repo = self.repo_dir
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(repo),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Replay"], cwd=str(repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test-replay@example.com"],
            cwd=str(repo),
            check=True,
        )

        # 1. Package structure: pkg/ with function, data file, and pkg/gone.py
        pkg_dir = repo / "pkg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text(
            "def compute(x: int) -> int:\n    return x * 2\n",
            encoding="utf-8",
        )
        (pkg_dir / "data.txt").write_text("replay-fixture-data\n", encoding="utf-8")
        (pkg_dir / "gone.py").write_text("GONE_VALUE = 42\n", encoding="utf-8")

        # 2. Root conftest.py: sets REPLAY_CONFTEST=1
        (repo / "conftest.py").write_text(
            "import os\nos.environ['REPLAY_CONFTEST'] = '1'\n",
            encoding="utf-8",
        )

        # 3. Test files under tests/
        tests_dir = repo / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # (a) Pass
        (tests_dir / "test_a.py").write_text(
            "from pkg import compute\n\ndef test_compute_ok():\n    assert compute(3) == 6\n",
            encoding="utf-8",
        )

        # (b) Fail one assertion
        (tests_dir / "test_b.py").write_text(
            "from pkg import compute\n\ndef test_compute_bad():\n    assert compute(3) == 999\n",
            encoding="utf-8",
        )

        # (c) Import pkg.gone that trim commit will remove
        (tests_dir / "test_c.py").write_text(
            "import pkg.gone\n\ndef test_gone():\n    assert pkg.gone.GONE_VALUE == 42\n",
            encoding="utf-8",
        )

        # (d) Syntax error
        (tests_dir / "test_d.py").write_text(
            "def test_syntax_broken(\n",
            encoding="utf-8",
        )

        # (e) Define no tests
        (tests_dir / "test_e.py").write_text(
            "# Module without tests\nVAL = 123\n",
            encoding="utf-8",
        )

        # (f) Sleep 30s inside one test
        (tests_dir / "test_f.py").write_text(
            "import time\n\ndef test_sleep_slow():\n    time.sleep(30)\n",
            encoding="utf-8",
        )

        # (g) Read Path(__file__).resolve().parents[1] / "pkg" / "data.txt" and check env
        (tests_dir / "test_g.py").write_text(
            "import os\n"
            "from pathlib import Path\n\n"
            "def test_parents_and_conftest():\n"
            "    data_path = Path(__file__).resolve().parents[1] / 'pkg' / 'data.txt'\n"
            "    assert data_path.exists()\n"
            "    assert data_path.read_text(encoding='utf-8').strip() == 'replay-fixture-data'\n"
            "    assert os.environ.get('REPLAY_CONFTEST') == '1'\n",
            encoding="utf-8",
        )

        # Path to be deleted and later recreated at HEAD
        (tests_dir / "test_recreated.py").write_text(
            "def test_recreated_historical():\n    assert True\n",
            encoding="utf-8",
        )

        # Commit initial state
        subprocess.run(
            ["git", "-C", str(repo), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "initial before trim"],
            check=True,
            capture_output=True,
        )

        # Commit trim: deletes pkg/gone.py and all tests
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "rm",
                "pkg/gone.py",
                "tests/test_a.py",
                "tests/test_b.py",
                "tests/test_c.py",
                "tests/test_d.py",
                "tests/test_e.py",
                "tests/test_f.py",
                "tests/test_g.py",
                "tests/test_recreated.py",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "trim commit"],
            check=True,
            capture_output=True,
        )
        self.trim_sha = self._git("rev-parse", "HEAD")

        # Re-create test_recreated.py at HEAD
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_recreated.py").write_text(
            "def test_recreated_at_head():\n    assert True\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(repo), "add", "tests/test_recreated.py"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "recreate test at head"],
            check=True,
            capture_output=True,
        )
        self.head_sha = self._git("rev-parse", "HEAD")

    def test_case_a_pass(self) -> None:
        """Case (a): passing test file produces 'pass' verdict and sorted per-test outcomes."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_a.py")
        self.assertEqual(res.verdict, "pass")
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.tests, [("tests.test_a::test_compute_ok", "passed")])
        self.assertEqual(res.counts["passed"], 1)
        self.assertEqual(res.counts["failed"], 0)
        self.assertFalse(res.overwrote_head_path)
        self.assertIsNone(res.error_line)
        self._assert_clean_repo()

    def test_case_b_fail(self) -> None:
        """Case (b): failing assertion produces 'fail' verdict and per-test failure outcome."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_b.py")
        self.assertEqual(res.verdict, "fail")
        self.assertEqual(res.exit_code, 1)
        self.assertEqual(res.tests, [("tests.test_b::test_compute_bad", "failed")])
        self.assertEqual(res.counts["failed"], 1)
        self.assertEqual(res.counts["passed"], 0)
        self.assertFalse(res.overwrote_head_path)
        self.assertIsNone(res.error_line)
        self._assert_clean_repo()

    def test_case_c_error_import(self) -> None:
        """Case (c): import of missing pkg.gone produces 'error-import' and error_line with ModuleNotFoundError."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_c.py")
        self.assertEqual(res.verdict, "error-import")
        self.assertEqual(res.exit_code, 2)
        self.assertIsNotNone(res.error_line)
        self.assertIn("ModuleNotFoundError", res.error_line or "")
        self.assertIn("pkg.gone", res.error_line or "")
        self.assertFalse(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_case_d_error_collect(self) -> None:
        """Case (d): syntax error produces 'error-collect' and error_line with SyntaxError."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_d.py")
        self.assertEqual(res.verdict, "error-collect")
        self.assertEqual(res.exit_code, 2)
        self.assertIsNotNone(res.error_line)
        self.assertIn("SyntaxError", res.error_line or "")
        self.assertFalse(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_case_e_no_tests(self) -> None:
        """Case (e): test file defining no tests produces 'no-tests' verdict (exit 5)."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_e.py")
        self.assertEqual(res.verdict, "no-tests")
        self.assertEqual(res.exit_code, 5)
        self.assertEqual(res.tests, [])
        self.assertEqual(res.counts["passed"], 0)
        self.assertIsNone(res.error_line)
        self.assertFalse(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_case_f_timeout(self) -> None:
        """Case (f): slow test with timeout_s=1 produces 'timeout' and kills the process group."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_f.py", timeout_s=1)
        self.assertEqual(res.verdict, "timeout")
        self.assertEqual(res.tests, [])
        self.assertIsNone(res.error_line)
        self.assertFalse(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_case_g_parents_and_conftest(self) -> None:
        """Case (g): Path(__file__).resolve().parents[1] repo lookup and root conftest env sandbox."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_g.py")
        self.assertEqual(res.verdict, "pass")
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(
            res.tests, [("tests.test_g::test_parents_and_conftest", "passed")]
        )
        self.assertFalse(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_overwrote_head_path_true(self) -> None:
        """Deleted test recreated at HEAD sets overwrote_head_path: true."""
        res = replay_file(self.repo_dir, self.trim_sha, "tests/test_recreated.py")
        self.assertEqual(res.verdict, "pass")
        self.assertTrue(res.overwrote_head_path)
        self._assert_clean_repo()

    def test_cli_subprocess_from_json(self) -> None:
        """Run CLI as subprocess with --from-json and --format json."""
        tool_path = str(
            Path(__file__).resolve().parents[1] / "tools" / "deleted_test_replay.py"
        )
        inv_path = self.repo_dir.parent / "inventory.json"
        inv_records = [
            {"path": "tests/test_a.py"},
            {"path": "tests/test_b.py"},
            {"path": "tests/test_e.py"},
        ]
        inv_path.write_text(json.dumps(inv_records), encoding="utf-8")

        res = subprocess.run(
            [
                sys.executable,
                tool_path,
                self.trim_sha,
                "--from-json",
                str(inv_path),
                "--format",
                "json",
            ],
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            res.returncode, 0, f"CLI exited with {res.returncode}: {res.stderr}"
        )
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 3)
        self.assertEqual(
            [d["path"] for d in data],
            ["tests/test_a.py", "tests/test_b.py", "tests/test_e.py"],
        )
        self.assertEqual(data[0]["verdict"], "pass")
        self.assertEqual(data[1]["verdict"], "fail")
        self.assertEqual(data[2]["verdict"], "no-tests")
        self._assert_clean_repo()

    def test_cli_no_paths_exits_2(self) -> None:
        """Running CLI without positional paths or --from-json exits 2 via parser.error."""
        tool_path = str(
            Path(__file__).resolve().parents[1] / "tools" / "deleted_test_replay.py"
        )
        res = subprocess.run(
            [sys.executable, tool_path, self.trim_sha, "--format", "json"],
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        self.assertIn("at least one test path must be specified", res.stderr)
        self._assert_clean_repo()
