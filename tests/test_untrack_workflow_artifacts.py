"""Self-tests for tools/untrack-workflow-artifacts.py in a temporary Git repository.

Stdlib unittest only.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from tests.support import REPO_ROOT, git, load_module

TOOL_PATH = REPO_ROOT / "tools" / "untrack-workflow-artifacts.py"
MIGRATION_TOOL = load_module("untrack_workflow_artifacts", TOOL_PATH)


class UntrackWorkflowArtifactsTests(unittest.TestCase):
    """Test suite for the untrack-workflow-artifacts migration utility."""

    def _init_repo_with_artifacts(self, root: Path) -> None:
        """Initialize a git repo with tracked workflow-artifacts files."""
        git(root, "init", "-q")
        git(root, "config", "user.name", "Test User")
        git(root, "config", "user.email", "test@example.com")

        # Create a tracked file in repo root
        (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        git(root, "add", "README.md")

        # Create tracked workflow-artifacts files
        artifacts_dir = (
            root / "workflow-artifacts" / "assess-security" / "20260727-120000"
        )
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "report.md").write_text(
            "# Assessment Report\n", encoding="utf-8"
        )
        (artifacts_dir / "evidence.md").write_text(
            "Local evidence content\n", encoding="utf-8"
        )

        git(root, "add", "workflow-artifacts")
        git(root, "commit", "-m", "initial commit with tracked artifacts")

    def test_dry_run_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            self._init_repo_with_artifacts(root)

            # Run tool in dry-run mode (no --apply)
            p = subprocess.run(
                [sys.executable, str(TOOL_PATH)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(p.returncode, 0)
            self.assertIn("Dry run only", p.stdout)

            # Confirm index still tracks workflow-artifacts
            tracked = MIGRATION_TOOL.tracked_paths(root)
            self.assertGreater(len(tracked), 0)
            self.assertFalse((root / ".gitignore").exists())

    def test_apply_removes_from_index_retains_local_files_and_stages_gitignore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            self._init_repo_with_artifacts(root)

            p = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--apply"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(p.returncode, 0)

            # Local files MUST still exist on disk
            report_file = (
                root
                / "workflow-artifacts"
                / "assess-security"
                / "20260727-120000"
                / "report.md"
            )
            self.assertTrue(report_file.exists())

            # Index MUST no longer track workflow-artifacts
            tracked = MIGRATION_TOOL.tracked_paths(root)
            self.assertEqual(len(tracked), 0)

            # .gitignore MUST exist and be staged
            gitignore = root / ".gitignore"
            self.assertTrue(gitignore.exists())
            self.assertIn("workflow-artifacts/", gitignore.read_text(encoding="utf-8"))

            staged = MIGRATION_TOOL.staged_paths(root)
            self.assertIn(".gitignore", staged)

    def test_idempotent_when_already_untracked_and_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            self._init_repo_with_artifacts(root)

            # First apply
            subprocess.run(
                [sys.executable, str(TOOL_PATH), "--apply"], cwd=root, check=True
            )

            # Commit the migration
            git(root, "commit", "-m", "chore: stop tracking workflow artifacts")

            # Second apply (should be idempotent)
            p = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--apply"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(p.returncode, 0)
            self.assertIn("No tracked workflow artifacts found", p.stdout)

    def test_commit_refuses_when_unrelated_files_are_staged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            self._init_repo_with_artifacts(root)

            # Stage an unrelated change first
            (root / "unrelated.txt").write_text("unrelated file\n", encoding="utf-8")
            git(root, "add", "unrelated.txt")

            p = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--apply", "--commit"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(p.returncode, 0)
            self.assertIn(
                "Refusing to commit because the index contains paths outside this migration",
                p.stderr,
            )

    def test_refuses_to_stage_dirty_gitignore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            self._init_repo_with_artifacts(root)

            # Create and commit a .gitignore file so git tracks it
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            git(root, "add", ".gitignore")
            git(root, "commit", "-m", "add initial gitignore")

            # Make an unstaged edit to the tracked .gitignore
            (root / ".gitignore").write_text(".env\n*.log\n", encoding="utf-8")

            p = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--apply"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(p.returncode, 0)
            self.assertIn(
                "Refusing to stage .gitignore because it has existing staged or unstaged edits",
                p.stderr,
            )


if __name__ == "__main__":
    unittest.main()
