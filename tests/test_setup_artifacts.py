"""Tests for deterministic setup-artifact creation on install (IPD-2 Batch E; AC-16).

Verifies the CLI/engine creates the plan lifecycle dirs, a .gitleaksignore baseline, and
the secret-scan CI workflow in a target repo (staged, idempotent, no-clobber - R-2), and
that the "run /setup-repo" guidance is emitted. Stdlib unittest only.
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.support import init_repo
from agent_workflows import cli, engine


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class SetupArtifactTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        os.environ["NO_COLOR"] = "1"
        self.repo = init_repo(self.base / "r")

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        os.environ.pop("NO_COLOR", None)
        self._tmp.cleanup()

    def test_install_creates_all_artifacts_and_guidance(self):
        code, out = _run(["install", str(self.repo), "--yes"])
        self.assertEqual(code, 0, out)
        for sub in ("pending", "reusable", "executed"):
            self.assertTrue(
                (self.repo / ".agents/plans" / sub / ".gitkeep").is_file(),
                f"missing plan dir {sub}",
            )
        self.assertTrue((self.repo / ".gitleaksignore").is_file())
        self.assertTrue((self.repo / ".github/workflows/secret-scan.yml").is_file())
        # AC-16: guidance to run /setup-repo is emitted.
        self.assertIn("/setup-repo", out)

    def test_idempotent_rerun_creates_nothing_new(self):
        _run(["install", str(self.repo), "--yes"])
        # Second engine call directly: no artifacts created the second time.
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git)
        self.assertEqual(created, [])

    def test_no_clobber_preserves_existing_files(self):
        # A user's own .gitleaksignore and CI must not be overwritten (R-2).
        (self.repo / ".gitleaksignore").write_text("MY BASELINE\n", encoding="utf-8")
        (self.repo / ".github/workflows").mkdir(parents=True)
        (self.repo / ".github/workflows/secret-scan.yml").write_text(
            "name: my-own-scan\n", encoding="utf-8"
        )
        _run(["install", str(self.repo), "--yes"])
        self.assertEqual(
            (self.repo / ".gitleaksignore").read_text(encoding="utf-8"), "MY BASELINE\n"
        )
        self.assertIn(
            "my-own-scan",
            (self.repo / ".github/workflows/secret-scan.yml").read_text(encoding="utf-8"),
        )

    def test_engine_returns_created_list(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git)
        # 3 gitkeeps + gitleaksignore + secret-scan CI = 5 on a fresh repo.
        self.assertEqual(len(created), 5)

    def test_dry_run_reports_without_writing(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git, dry_run=True)
        self.assertTrue(all("dry-run" in c for c in created))
        self.assertFalse((self.repo / ".gitleaksignore").exists())


if __name__ == "__main__":
    unittest.main()
