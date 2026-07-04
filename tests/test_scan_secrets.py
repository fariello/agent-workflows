"""Self-tests for scan_secrets.py: planted-secret detection (tree + history), redaction,
and honesty. Stdlib unittest only.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.support import SCANNER, REPO_ROOT, init_repo, git, run_tool, load_module

SS = load_module("scan_secrets", SCANNER)

# A fake AWS access key id (matches the AKIA rule; not a real credential).
FAKE_AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"[:16]


class ScannerUnitTests(unittest.TestCase):
    def test_redaction_hides_the_secret(self):
        redacted = SS.redact(FAKE_AWS_KEY)
        self.assertNotEqual(redacted, FAKE_AWS_KEY)
        self.assertNotIn(FAKE_AWS_KEY, redacted)
        self.assertIn("*", redacted)

    def test_detects_aws_key_in_text(self):
        findings = SS.scan_text(
            f"aws_key = {FAKE_AWS_KEY}", where="working-tree",
            location="config.txt", use_entropy=False, use_pii=False, commit="",
        )
        self.assertTrue(findings, "planted AWS key not detected")
        self.assertTrue(all(FAKE_AWS_KEY not in f.preview for f in findings),
                        "raw secret leaked into finding preview")

    def test_version_flag(self):
        proc = run_tool(SCANNER, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = (REPO_ROOT / ".agents/workflows/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(proc.stdout.strip(), expected)


class ScannerEndToEndTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")

    def tearDown(self):
        self._tmp.cleanup()

    def test_detects_planted_secret_in_working_tree(self):
        (self.repo / "config.env").write_text(f"AWS_KEY={FAKE_AWS_KEY}\n", encoding="utf-8")
        proc = run_tool(SCANNER, "--repo", str(self.repo), "--format", "json",
                        "--working-tree-only", "--no-external")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["summary"]["total"], 1, "secret in tree not found")
        self.assertNotIn(FAKE_AWS_KEY, proc.stdout, "raw secret leaked into JSON output")

    def test_detects_planted_secret_in_history(self):
        # Commit a secret, then remove it: it should still be found in history.
        f = self.repo / "leak.txt"
        f.write_text(f"key={FAKE_AWS_KEY}\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "oops")
        f.unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "remove")
        proc = run_tool(SCANNER, "--repo", str(self.repo), "--format", "json",
                        "--history-only", "--no-external")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["summary"]["total"], 1, "secret in history not found")

    def test_clean_repo_reports_zero(self):
        (self.repo / "readme.md").write_text("nothing to see here\n", encoding="utf-8")
        proc = run_tool(SCANNER, "--repo", str(self.repo), "--format", "json",
                        "--working-tree-only", "--no-external", "--no-entropy")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["summary"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
