"""Self-tests for scan_secrets.py: planted-secret detection (tree + history), redaction,
and honesty. Stdlib unittest only.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
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


class ScannerRecommendationTests(unittest.TestCase):
    """The 'RECOMMENDED - install a mature scanner' nag must only appear when NO mature
    scanner is present. When one is installed (and run), do not nag; when external
    scanning was skipped, say so instead."""

    def _emit_text(self, avail, skipped_external=False):
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stderr(err):
            SS.emit([], "text", buf, avail, skipped_external=skipped_external)
        return err.getvalue()

    def _emit_json(self, avail, skipped_external=False):
        buf = io.StringIO()
        with redirect_stderr(io.StringIO()):
            SS.emit([], "json", buf, avail, skipped_external=skipped_external)
        return json.loads(buf.getvalue())

    def test_no_nag_when_mature_scanner_present(self):
        # gitleaks present, others missing: must NOT print the install RECOMMENDED nag.
        avail = {"gitleaks": True, "trufflehog": False, "detect-secrets": False}
        stderr = self._emit_text(avail)
        self.assertNotIn("RECOMMENDED", stderr)
        self.assertIn("gitleaks", stderr)  # still reported as used
        data = self._emit_json(avail)
        self.assertNotIn("install and run a mature", data["note"])
        self.assertIn("gitleaks", data["external_tools"]["available"])

    def test_nag_when_no_mature_scanner_present(self):
        avail = {"gitleaks": False, "trufflehog": False, "detect-secrets": False}
        stderr = self._emit_text(avail)
        self.assertIn("RECOMMENDED", stderr)
        data = self._emit_json(avail)
        self.assertIn("install and run a mature", data["note"])

    def test_skipped_external_does_not_nag(self):
        avail = {"gitleaks": False, "trufflehog": False, "detect-secrets": False}
        stderr = self._emit_text(avail, skipped_external=True)
        self.assertNotIn("RECOMMENDED", stderr)
        self.assertIn("skipped", stderr)
        data = self._emit_json(avail, skipped_external=True)
        self.assertIn("skipped", data["note"])


if __name__ == "__main__":
    unittest.main()
