"""Regression test for IPD awretrofit Order 10: `aw install` must not abort when a `git add` target
is gitignored.

Discovered executing Order 09: `ensure_workflow_artifacts_readme` used a raw `git add` on
`workflow-artifacts/README.md`; on a repo that gitignores `workflow-artifacts/` (Order 07 gitignores
run scratch) the whole install FAILED ("The following paths are ignored... Use -f"). The fix routes it
through the existing tolerant `git_add_optional` helper (skip-when-ignored, no `-f`), matching the
sibling README ensurers. The README is still written to disk; it is just not staged when ignored.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine


def _git(repo: Path, *args: str):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


class WorkflowArtifactsGitignoredTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "repo"
        self.repo.mkdir()
        for a in (
            ["init", "-q"],
            ["config", "user.email", "t@e.com"],
            ["config", "user.name", "T"],
        ):
            _git(self.repo, *a)
        # The repo gitignores workflow-artifacts/ (exactly the Order-07 posture that broke install).
        (self.repo / ".gitignore").write_text("workflow-artifacts/\n", encoding="utf-8")
        _git(self.repo, "add", ".gitignore")
        _git(self.repo, "commit", "-qm", "seed")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _plan(self):
        return engine.InstallPlan(
            source_root=self.repo,  # unused by ensure_workflow_artifacts_readme's write path
            repo_root=self.repo,
            dry_run=False,
            backup=False,
            prune=False,
            no_color=True,
            yes=True,
        )

    def test_ensure_workflow_artifacts_readme_survives_gitignored_dir(self):
        """The ensurer completes (no abort) on a gitignored workflow-artifacts/, writes the README,
        and does NOT stage it (it is ignored) - the Order-10 fix."""
        installed: list[str] = []
        skipped: list[str] = []
        # Must not raise even though `workflow-artifacts/` is gitignored.
        engine.ensure_workflow_artifacts_readme(self._plan(), True, installed, skipped)
        readme = self.repo / "workflow-artifacts" / "README.md"
        self.assertTrue(readme.is_file(), "README should still be written to disk")
        # It is ignored, so it must NOT be in the git index.
        ls = _git(self.repo, "ls-files", "--", "workflow-artifacts/README.md")
        self.assertEqual(ls.stdout.strip(), "", "ignored README must not be staged")

    def test_git_add_optional_returns_false_on_ignored(self):
        """The helper the fix relies on reports skip (False) rather than raising on an ignored path."""
        (self.repo / "workflow-artifacts").mkdir(exist_ok=True)
        (self.repo / "workflow-artifacts" / "README.md").write_text(
            "x\n", encoding="utf-8"
        )
        staged = engine.git_add_optional(self.repo, "workflow-artifacts/README.md")
        self.assertFalse(
            staged, "git_add_optional should skip (return False) an ignored path"
        )


if __name__ == "__main__":
    unittest.main()
