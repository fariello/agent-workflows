"""Regression test for IPD awretrofit Order 10: `aw install` must not abort when a `git add` target
is gitignored.

Discovered executing Order 09: `ensure_workflow_artifacts_readme` used a raw `git add` on
`workflow-artifacts/README.md`; on a repo that gitignores `workflow-artifacts/` (Order 07 gitignores
run scratch) the whole install FAILED ("The following paths are ignored... Use -f"). The fix routes it
through the existing tolerant `git_add_optional` helper (skip-when-ignored, no `-f`), matching the
sibling README ensurers. The README is still written to disk; it is just not staged when ignored.

wfartifacts Order 01 (gzhd7t) RE-POINTED these tests rather than deleting them, because the
guarantee they encode is still live and is what this file exists to protect: an install must not
abort, and the README must not end up in the index. Two things changed underneath them.

FIRST, THE PATH. Run scratch moved to `.aw/workflow-artifacts/` (Order 07), so the assertions now
name that path; a repo-root `workflow-artifacts/` is no longer created at all.

SECOND, THE MECHANISM BY WHICH THE README STAYS UNSTAGED, which is the more important note. The
ensurer no longer calls `git add` at all, so "not in the index" is now guaranteed by construction
rather than by the ignore rule happening to match. That is deliberate: git's ignore rules do NOT
untrack an already-tracked path, so relying on the rule leaves a window (a repo installed before the
rule lands keeps the file tracked forever). `git_add_optional` still exists and is still exercised
directly by the second test below, since the sibling README ensurers depend on it.
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
        # The repo gitignores the run-scratch tree (exactly the Order-07 posture that broke install).
        # Both spellings are seeded: `.aw/workflow-artifacts/` is the live path, and the retired
        # repo-root one is kept so this fixture still represents a repo that had ignored the old path.
        (self.repo / ".gitignore").write_text(
            ".aw/workflow-artifacts/\nworkflow-artifacts/\n", encoding="utf-8"
        )
        # `resolve_target_layout` returns 'aw' only when `.aw/system` exists (or neither tree does).
        # A bare temp repo has neither, so it already resolves to 'aw'; create the dir anyway to pin
        # the layout explicitly rather than depending on the fresh-repo default.
        (self.repo / ".aw" / "system").mkdir(parents=True, exist_ok=True)
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
        """The ensurer completes (no abort) on a gitignored run-scratch tree, writes the README,
        and does NOT stage it - the Order-10 guarantee, at the Order-07 path."""
        installed: list[str] = []
        skipped: list[str] = []
        # Must not raise even though the run-scratch tree is gitignored.
        engine.ensure_workflow_artifacts_readme(self._plan(), True, installed, skipped)
        readme = self.repo / ".aw" / "workflow-artifacts" / "README.md"
        self.assertTrue(readme.is_file(), "README should still be written to disk")
        # It must NOT be in the git index (now by construction: the ensurer never stages it).
        ls = _git(self.repo, "ls-files", "--", ".aw/workflow-artifacts/README.md")
        self.assertEqual(ls.stdout.strip(), "", "run-scratch README must not be staged")
        # And the retired repo-root directory must not be created at all (wfartifacts Order 01).
        self.assertFalse(
            (self.repo / "workflow-artifacts").exists(),
            "the ensurer must not create a repo-root workflow-artifacts/ directory",
        )

    def test_git_add_optional_returns_false_on_ignored(self):
        """The helper the sibling README ensurers rely on reports skip (False) rather than raising on
        an ignored path. Exercised directly because the run-scratch ensurer no longer calls it."""
        (self.repo / ".aw" / "workflow-artifacts").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "workflow-artifacts" / "README.md").write_text(
            "x\n", encoding="utf-8"
        )
        staged = engine.git_add_optional(self.repo, ".aw/workflow-artifacts/README.md")
        self.assertFalse(
            staged, "git_add_optional should skip (return False) an ignored path"
        )


if __name__ == "__main__":
    unittest.main()
