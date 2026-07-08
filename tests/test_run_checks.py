"""Self-tests for run_checks.py: discovery, classification, the safety denylist, honest
pass/fail evidence, and --version. Stdlib unittest only.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.support import RUN_CHECKS, REPO_ROOT, run_tool, load_module

RC = load_module("run_checks", RUN_CHECKS)


class ClassificationUnitTests(unittest.TestCase):
    def test_classify_categories(self):
        self.assertEqual(RC.classify("test", "pytest"), "test")
        self.assertEqual(RC.classify("lint", "ruff check ."), "lint")
        self.assertEqual(RC.classify("build", "make build"), "build")
        self.assertEqual(RC.classify("typecheck", "mypy ."), "typecheck")
        self.assertEqual(RC.classify("deploy", "kubectl apply"), "")

    def test_denylist_blocks_dangerous(self):
        self.assertTrue(RC.denied_reason("npm publish"))
        self.assertTrue(RC.denied_reason("git push origin main"))
        self.assertTrue(RC.denied_reason("terraform apply"))
        self.assertTrue(RC.denied_reason("pip install requests"))
        self.assertTrue(RC.denied_reason("curl http://evil"))
        self.assertFalse(RC.denied_reason("pytest -q"))
        self.assertFalse(RC.denied_reason("ruff check ."))

    def test_metrics_scrape_is_clean(self):
        # Empty / banner output must not produce a spurious test count.
        self.assertEqual(RC._extract_metrics("> pkg@1.0.0 test\n"), {})
        m = RC._extract_metrics("collected 12 items\n8 passed, 2 failed\nTOTAL 87%")
        self.assertEqual(m.get("passed"), 8)
        self.assertEqual(m.get("failed"), 2)
        self.assertEqual(m.get("coverage_pct"), 87.0)

    def test_version_flag(self):
        proc = run_tool(RUN_CHECKS, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = (REPO_ROOT / ".agents/workflows/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(proc.stdout.strip(), expected)


@unittest.skipIf(
    os.name == "nt",
    "run_checks.py's npm-script execution behaves differently on Windows (npm.cmd / shell "
    "resolution); these node-runner e2e checks are POSIX-verified. run_checks is unrelated "
    "to IPD-2 distribution; Windows support for it is a separate follow-up.",
)
class RunChecksEndToEndTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_pkg(self, scripts: dict):
        import json as _json
        (self.repo / "package.json").write_text(
            _json.dumps({"name": "fix", "version": "1.0.0", "scripts": scripts}),
            encoding="utf-8",
        )

    def test_passing_check_exit_zero(self):
        self._write_pkg({"test": "node -e \"process.exit(0)\""})
        proc = run_tool(RUN_CHECKS, "--repo", str(self.repo), "--yes", "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["summary"]["all_ran_passed"])
        self.assertEqual(data["summary"]["failed"], 0)

    def test_failing_check_exit_one(self):
        self._write_pkg({"test": "node -e \"process.exit(3)\""})
        proc = run_tool(RUN_CHECKS, "--repo", str(self.repo), "--yes", "--format", "json")
        self.assertEqual(proc.returncode, 1, "a failing check must exit 1")
        data = json.loads(proc.stdout)
        self.assertEqual(data["summary"]["failed"], 1)
        self.assertFalse(data["summary"]["all_ran_passed"])

    def test_denylisted_never_runs_even_with_yes(self):
        self._write_pkg({"deploy": "node -e \"require('fs').writeFileSync('RAN','1')\""})
        proc = run_tool(RUN_CHECKS, "--repo", str(self.repo), "--yes", "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.repo / "RAN").exists(),
                         "a denylisted command was executed under --yes")

    def test_no_checks_repo_is_honest(self):
        proc = run_tool(RUN_CHECKS, "--repo", str(self.repo), "--yes", "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["summary"]["ran"], 0)
        self.assertFalse(data["summary"]["all_ran_passed"],
                         "a repo with no checks must not read as passed")


if __name__ == "__main__":
    unittest.main()
