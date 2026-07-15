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
        for sub in ("pending", "reusable", "executed", "superseded", "not-executed"):
            self.assertTrue(
                (self.repo / ".agents/plans" / sub / ".gitkeep").is_file(),
                f"missing plan dir {sub}",
            )
        for sub in ("research", "walkthroughs"):
            self.assertTrue(
                (self.repo / ".agents/docs" / sub / ".gitkeep").is_file(),
                f"missing docs dir {sub}",
            )
        # Verify no-clobber READMEs
        self.assertTrue((self.repo / ".agents/docs/README.md").is_file())
        self.assertTrue((self.repo / ".agents/docs/research/README.md").is_file())
        self.assertTrue((self.repo / ".agents/docs/walkthroughs/README.md").is_file())
        self.assertTrue((self.repo / ".gitleaksignore").is_file())
        self.assertTrue((self.repo / ".github/workflows/secret-scan.yml").is_file())
        # Inter-agent comms skeleton (D81): nested .gitignore, README, shared/ gitkeeps.
        self.assertTrue((self.repo / ".agents/comms/.gitignore").is_file())
        self.assertTrue((self.repo / ".agents/comms/README.md").is_file())
        for sub in ("inbox", "sent", "archive"):
            self.assertTrue(
                (self.repo / ".agents/comms/shared" / sub / ".gitkeep").is_file(),
                f"missing comms shared dir {sub}",
            )
        # `local/` is ignored by the nested .gitignore, so it gets NO committed .gitkeep.
        self.assertFalse((self.repo / ".agents/comms/local/inbox/.gitkeep").exists())
        # The nested .gitignore ignores local/ and does NOT touch the target root .gitignore.
        self.assertIn(
            "local/",
            (self.repo / ".agents/comms/.gitignore").read_text(encoding="utf-8"),
        )
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
            (self.repo / ".github/workflows/secret-scan.yml").read_text(
                encoding="utf-8"
            ),
        )

    def test_engine_returns_created_list(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git)
        # 5 plan-dir gitkeeps (pending/executed/superseded/not-executed/reusable)
        # + 4 docs-dir gitkeeps (research/walkthroughs/specs/prompts)
        # + gitleaksignore + secret-scan CI
        # + comms .gitignore + comms README + 3 comms shared/ gitkeeps (inbox/sent/archive) = 16.
        self.assertEqual(len(created), 16)

    def test_install_does_not_touch_target_root_gitignore(self):
        # The comms nested .gitignore is a created deliverable; the ROOT .gitignore must not be
        # created/modified by comms scaffolding. (ensure_backups_gitignored is a separate path.)
        root_gi = self.repo / ".gitignore"
        before = root_gi.read_text(encoding="utf-8") if root_gi.exists() else None
        use_git = engine.git_available(self.repo)
        engine.create_setup_artifacts(self.repo, use_git)
        after = root_gi.read_text(encoding="utf-8") if root_gi.exists() else None
        self.assertEqual(
            before, after, "create_setup_artifacts must not touch the root .gitignore"
        )

    def test_dry_run_reports_without_writing(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git, dry_run=True)
        self.assertTrue(all("dry-run" in c for c in created))
        self.assertFalse((self.repo / ".gitleaksignore").exists())


if __name__ == "__main__":
    unittest.main()
