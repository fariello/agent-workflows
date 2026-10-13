"""Unit and integration tests for tools/mutation_probe.py."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.mutation_probe import apply_operator, probe

PROBE_SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "mutation_probe.py"


class ApplyOperatorUnitTests(unittest.TestCase):
    """Unit tests for apply_operator on fixture source strings."""

    def test_return_none(self):
        src = "def f(x):\n    return x + 1\n"
        mutated = apply_operator(src, "f", "return-none")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIsNone(ns["f"](10))

    def test_return_true(self):
        src = "def f(x):\n    return False\n"
        mutated = apply_operator(src, "f", "return-true")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIs(ns["f"](10), True)

    def test_return_false(self):
        src = "def f(x):\n    return True\n"
        mutated = apply_operator(src, "f", "return-false")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIs(ns["f"](10), False)

    def test_raise(self):
        src = "def f(x):\n    return x\n"
        mutated = apply_operator(src, "f", "raise")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        with self.assertRaises(RuntimeError) as ctx:
            ns["f"](10)
        self.assertEqual(str(ctx.exception), "mutant")

    def test_negate_return(self):
        src = "def is_even(n):\n    return n % 2 == 0\n"
        mutated = apply_operator(src, "is_even", "negate-return")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIs(ns["is_even"](2), False)
        self.assertIs(ns["is_even"](3), True)

    def test_method_c_m(self):
        src = "class C:\n    def m(self):\n        return 42\n"
        mutated = apply_operator(src, "C.m", "return-none")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        inst = ns["C"]()
        self.assertIsNone(inst.m())

    def test_decorated_function(self):
        src = (
            "def dec(fn):\n"
            "    return fn\n\n"
            "@dec\n"
            "def g():\n"
            "    return 100\n"
        )
        mutated = apply_operator(src, "g", "return-true")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIs(ns["g"](), True)

    def test_one_line_def(self):
        src = "def f(): return 1\n"
        mutated = apply_operator(src, "f", "return-false")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        self.assertIs(ns["f"](), False)

    def test_nested_function_negate_return_inner_preserved(self):
        src = (
            "def outer(x):\n"
            "    def inner():\n"
            "        return 10\n"
            "    return inner() == x\n"
        )
        mutated = apply_operator(src, "outer", "negate-return")
        self.assertIsNotNone(mutated)
        compile(mutated, "<test>", "exec")
        ns = {}
        exec(mutated, ns)
        # unmutated outer(10) is True; mutated outer(10) should be not True -> False
        self.assertIs(ns["outer"](10), False)
        # unmutated outer(5) is False; mutated outer(5) should be not False -> True
        self.assertIs(ns["outer"](5), True)

    def test_missing_qualname_returns_none(self):
        src = "def f():\n    return 1\n"
        self.assertIsNone(apply_operator(src, "nonexistent", "return-true"))
        self.assertIsNone(apply_operator(src, "C.m", "return-true"))

    def test_negate_return_no_return_expr_returns_none(self):
        src1 = "def f():\n    pass\n"
        self.assertIsNone(apply_operator(src1, "f", "negate-return"))
        src2 = "def f():\n    return\n"
        self.assertIsNone(apply_operator(src2, "f", "negate-return"))

    def test_unknown_operator_returns_none(self):
        src = "def f():\n    return 1\n"
        self.assertIsNone(apply_operator(src, "f", "unknown-op"))


class ProbeGitFixtureTests(unittest.TestCase):
    """Tests for probe against synthesized git repositories."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self.temp_dir.name

        subprocess.run(
            ["git", "init"], cwd=self.repo_dir, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Probe Test"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "probe@example.com"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )

        pkg_dir = Path(self.repo_dir) / "agent_workflows"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        (pkg_dir / "m.py").write_text(
            "def is_even(n):\n"
            "    return n % 2 == 0\n\n"
            "def unused():\n"
            "    return 1\n\n"
            "def boot():\n"
            "    return 1\n\n"
            "BOOT = boot()\n",
            encoding="utf-8",
        )

        tests_dir = Path(self.repo_dir) / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "test_m.py").write_text(
            "from agent_workflows.m import is_even\n\n"
            "def test_even():\n"
            "    assert is_even(2)\n\n"
            "def test_odd():\n"
            "    assert not is_even(3)\n\n"
            "def test_always_fails():\n"
            "    assert False\n",
            encoding="utf-8",
        )
        (tests_dir / "test_other.py").write_text(
            "def test_other():\n" "    assert True\n",
            encoding="utf-8",
        )
        (tests_dir / "test_unused.py").write_text(
            "from agent_workflows.m import unused\n\n"
            "def test_unused():\n"
            "    assert unused() == 1\n",
            encoding="utf-8",
        )
        (tests_dir / "test_always_fails_extra.py").write_text(
            "def test_fails_extra():\n" "    assert False\n",
            encoding="utf-8",
        )
        (tests_dir / "test_sleep.py").write_text(
            "import time\n\n" "def test_sleep_slow():\n" "    time.sleep(5)\n",
            encoding="utf-8",
        )

        subprocess.run(
            ["git", "add", "."], cwd=self.repo_dir, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "commit 1: all tests"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )

        # Commit 2: delete test_unused.py and test_always_fails_extra.py
        (tests_dir / "test_unused.py").unlink()
        (tests_dir / "test_always_fails_extra.py").unlink()
        subprocess.run(
            ["git", "rm", "tests/test_unused.py", "tests/test_always_fails_extra.py"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "commit 2: trim deleted tests"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )

        rev_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.sha2 = rev_res.stdout.strip()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _assert_clean_checkout_and_no_worktrees(self):
        wt_out = subprocess.run(
            ["git", "-C", self.repo_dir, "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        worktrees = [
            line for line in wt_out.splitlines() if line.startswith("worktree ")
        ]
        self.assertEqual(
            len(worktrees),
            1,
            f"Expected only fixture root worktree, got: {worktrees}",
        )
        status_out = subprocess.run(
            ["git", "-C", self.repo_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(
            status_out.strip(),
            "",
            f"Expected clean git status, got: {status_out}",
        )

    def test_verdict_killed_is_even_negate_return(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::is_even",
            "negate-return",
            pytest_args=["tests/test_m.py"],
        )
        self.assertEqual(res.verdict, "killed")
        self.assertEqual(res.baseline_failing, 1)
        self.assertEqual(res.mutant_failing, 3)
        self.assertEqual(res.newly_failing_total, 2)
        self.assertEqual(len(res.newly_failing), 2)
        # Exactly the two assertion nodes in newly_failing
        self.assertTrue(any("test_even" in nid for nid in res.newly_failing))
        self.assertTrue(any("test_odd" in nid for nid in res.newly_failing))
        # Always failing node in neither newly_failing nor flaky
        self.assertFalse(any("test_always_fails" in nid for nid in res.newly_failing))
        self.assertFalse(any("test_always_fails" in nid for nid in res.flaky))
        self._assert_clean_checkout_and_no_worktrees()

    def test_verdict_survived_unused_return_none(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::unused",
            "return-none",
            pytest_args=["tests/test_m.py"],
        )
        self.assertEqual(res.verdict, "survived")
        self.assertEqual(res.newly_failing, [])
        self.assertEqual(res.newly_failing_total, 0)
        self._assert_clean_checkout_and_no_worktrees()

    def test_positive_control_extra_test_kills_unused(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::unused",
            "return-none",
            pytest_args=["tests/test_m.py", "tests/test_unused.py"],
            extra_tests=[f"{self.sha2}:tests/test_unused.py"],
        )
        self.assertEqual(res.verdict, "killed")
        self.assertEqual(res.baseline_failing, 1)
        self.assertEqual(res.mutant_failing, 2)
        self.assertEqual(res.newly_failing_total, 1)
        self.assertTrue(any("test_unused" in nid for nid in res.newly_failing))
        self._assert_clean_checkout_and_no_worktrees()

    def test_verdict_killed_by_import_boot_raise(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::boot",
            "raise",
            pytest_args=["tests/test_m.py", "tests/test_other.py"],
        )
        self.assertEqual(res.verdict, "killed-by-import")
        self.assertEqual(res.newly_failing_total, 1)
        # test_other passes and its node is not in newly_failing
        self.assertFalse(any("test_other" in nid for nid in res.newly_failing))
        self.assertTrue(any("test_m.py" in nid for nid in res.newly_failing))
        self._assert_clean_checkout_and_no_worktrees()

    def test_verdict_invalid_qualname_no_pytest_run(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::nope",
            "return-none",
            pytest_args=["tests/test_m.py"],
        )
        self.assertEqual(res.verdict, "invalid")
        self.assertIsNone(res.baseline_failing)
        self.assertIsNone(res.mutant_failing)
        self.assertEqual(res.newly_failing, [])
        self.assertEqual(res.newly_failing_total, 0)
        self._assert_clean_checkout_and_no_worktrees()

    def test_always_failing_extra_test_not_credited_as_kill(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::unused",
            "return-none",
            pytest_args=["tests/test_m.py", "tests/test_always_fails_extra.py"],
            extra_tests=[f"{self.sha2}:tests/test_always_fails_extra.py"],
        )
        self.assertEqual(res.verdict, "survived")
        self.assertEqual(res.baseline_failing, 2)
        self.assertEqual(res.mutant_failing, 2)
        self.assertEqual(res.newly_failing, [])
        self.assertEqual(res.newly_failing_total, 0)
        self._assert_clean_checkout_and_no_worktrees()

    def test_flaky_test_excluded_from_kill(self):
        counter_fd, counter_path = tempfile.mkstemp(prefix="flaky_counter_")
        os.close(counter_fd)
        try:
            flaky_test_file = Path(self.repo_dir) / "tests" / "test_flaky.py"
            flaky_test_file.write_text(
                f"from pathlib import Path\n\n"
                f"def test_flaky_counter():\n"
                f"    p = Path({counter_path!r})\n"
                f"    count = int(p.read_text().strip()) if p.exists() and p.read_text().strip() else 0\n"
                f"    p.write_text(str(count + 1))\n"
                f"    if count >= 1:\n"
                f"        assert False\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "tests/test_flaky.py"],
                cwd=self.repo_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "add flaky test"],
                cwd=self.repo_dir,
                capture_output=True,
                check=True,
            )

            res = probe(
                self.repo_dir,
                "agent_workflows/m.py::unused",
                "return-none",
                pytest_args=["tests/test_flaky.py"],
            )
            self.assertEqual(res.verdict, "survived")
            self.assertEqual(res.newly_failing, [])
            self.assertEqual(res.newly_failing_total, 0)
            self.assertEqual(len(res.flaky), 1)
            self.assertTrue(any("test_flaky_counter" in nid for nid in res.flaky))
            self._assert_clean_checkout_and_no_worktrees()
        finally:
            if os.path.exists(counter_path):
                os.unlink(counter_path)

    def test_verdict_timeout(self):
        res = probe(
            self.repo_dir,
            "agent_workflows/m.py::is_even",
            "negate-return",
            pytest_args=["tests/test_sleep.py"],
            timeout_s=1,
        )
        self.assertEqual(res.verdict, "timeout")
        self.assertIn("timed out", str(res.reason))
        self._assert_clean_checkout_and_no_worktrees()

    def test_verdict_error_isolation_preflight(self):
        bad_dir = tempfile.TemporaryDirectory()
        try:
            bad_repo = bad_dir.name
            subprocess.run(
                ["git", "init"], cwd=bad_repo, capture_output=True, check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=bad_repo, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=bad_repo,
                check=True,
            )

            pkg = Path(bad_repo) / "agent_workflows"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "__init__.py").write_text(
                "raise ImportError('forced isolation failure')\n"
            )
            (pkg / "m.py").write_text("def is_even(n):\n    return n % 2 == 0\n")

            tests = Path(bad_repo) / "tests"
            tests.mkdir(parents=True, exist_ok=True)
            (tests / "test_m.py").write_text("def test_x(): assert True\n")

            subprocess.run(["git", "add", "."], cwd=bad_repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "bad repo"], cwd=bad_repo, check=True
            )

            res = probe(
                bad_repo,
                "agent_workflows/m.py::is_even",
                "negate-return",
                pytest_args=["tests/test_m.py"],
            )
            self.assertEqual(res.verdict, "error")
            self.assertEqual(res.reason, "isolation")
        finally:
            bad_dir.cleanup()

    def test_cli_subprocess_json_and_exit_codes(self):
        cmd = [
            sys.executable,
            str(PROBE_SCRIPT),
            "agent_workflows/m.py::is_even",
            "--op",
            "negate-return",
            "--format",
            "json",
            "--",
            "tests/test_m.py",
        ]
        res = subprocess.run(cmd, cwd=self.repo_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI failed: {res.stderr}")
        data = json.loads(res.stdout)

        expected_keys = {
            "head",
            "target",
            "operator",
            "selection",
            "verdict",
            "reason",
            "baseline_failing",
            "mutant_failing",
            "newly_failing",
            "newly_failing_total",
            "flaky",
            "extra_tests_overwrote",
            "wall_s",
            "checkout_status_changed",
        }
        for k in expected_keys:
            self.assertIn(k, data)

        self.assertEqual(data["verdict"], "killed")
        self.assertEqual(data["baseline_failing"], 1)
        self.assertEqual(data["mutant_failing"], 3)
        self.assertEqual(data["newly_failing_total"], 2)

        bad_cmd = [
            sys.executable,
            str(PROBE_SCRIPT),
            "agent_workflows/m.py::is_even",
            "--op",
            "bad-operator",
            "--format",
            "json",
            "--",
            "tests/test_m.py",
        ]
        bad_res = subprocess.run(
            bad_cmd, cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertEqual(bad_res.returncode, 2)
        self._assert_clean_checkout_and_no_worktrees()


if __name__ == "__main__":
    unittest.main()
