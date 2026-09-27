"""Tests for deep cleanup regenerable scaffolding exemption (backlog 3ypquf, plan baxbdh)."""

import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import engine
from tests.test_installer import SOURCE_WORKFLOWS, git, init_repo


class ClassificationRuleTests(unittest.TestCase):
    """Behavioral unit tests for the at-risk classification rule.

    Default-visible (no module-level slow mark). Built on a hand-crafted minimal fixture repo
    rather than a real install so pytest runs them in milliseconds.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self.tmp.name) / "repo")
        # Scaffolding: .aw/.gitignore with /workflow-artifacts/, .aw/records/README.md tracked,
        # and .aw/workflow-artifacts/README.md untracked and ignored.
        aw_dir = self.repo / ".aw"
        aw_dir.mkdir(parents=True, exist_ok=True)
        (aw_dir / ".gitignore").write_text("/workflow-artifacts/\n", encoding="utf-8")
        rec_dir = aw_dir / "records"
        rec_dir.mkdir(parents=True, exist_ok=True)
        (rec_dir / "README.md").write_text("# Records\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "initial commit")

        # Create the ignored run-scratch README
        art_dir = aw_dir / "workflow-artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        (art_dir / "README.md").write_text("# Artifacts\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_untracked_ignored_readme_is_not_at_risk(self):
        """(1) Untracked ignored README is excluded from at_risk and all_recoverable is True."""
        plan = engine.plan_deep_cleanup(self.repo)
        self.assertEqual(plan.at_risk, [])
        self.assertTrue(plan.all_recoverable)

    def test_negative_control_sibling_untracked_user_file_is_at_risk(self):
        """(2) Negative control: a sibling untracked file in that tree is at-risk."""
        (self.repo / ".aw/workflow-artifacts/my-notes.md").write_text(
            "user notes\n", encoding="utf-8"
        )
        plan = engine.plan_deep_cleanup(self.repo)
        self.assertIn(".aw/workflow-artifacts/my-notes.md", plan.at_risk)
        self.assertFalse(plan.all_recoverable)

    def test_negative_control_tracked_dirty_readme_is_at_risk(self):
        """(3) Negative control: tracked README with uncommitted edits is at-risk (silenced by path-only rule)."""
        git(self.repo, "add", "-f", ".aw/workflow-artifacts/README.md")
        git(self.repo, "commit", "-m", "track readme")
        readme = self.repo / ".aw/workflow-artifacts/README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "local changes\n", encoding="utf-8"
        )
        plan = engine.plan_deep_cleanup(self.repo)
        self.assertIn(".aw/workflow-artifacts/README.md", plan.at_risk)
        self.assertFalse(plan.all_recoverable)

    def test_negative_control_uncommitted_records_edit_is_at_risk(self):
        """(4) Negative control: uncommitted edit to .aw/records/README.md remains at-risk."""
        rec_readme = self.repo / ".aw/records/README.md"
        rec_readme.write_text(
            rec_readme.read_text(encoding="utf-8") + "edit\n", encoding="utf-8"
        )
        plan = engine.plan_deep_cleanup(self.repo)
        self.assertIn(".aw/records/README.md", plan.at_risk)
        self.assertFalse(plan.all_recoverable)


class RealInstallIntegrationTests(unittest.TestCase):
    """Integration test on a full real install.

    Class-scoped slow mark: deselected under `-m 'not slow'` while ClassificationRuleTests runs.
    """

    pytestmark = pytest.mark.slow

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self.tmp.name) / "repo")

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_install_committed_regenerable_readme_lifecycle(self):
        """Real install proves shipped installer and .aw/.gitignore produce exempt state."""
        engine.install_into_repo(self.repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "install")

        # (a) all_recoverable is True and at_risk == []
        plan = engine.plan_deep_cleanup(self.repo)
        self.assertEqual(plan.at_risk, [])
        self.assertTrue(plan.all_recoverable)

        # (b) the README is in plan.files and in plan.other_files, and counts[".aw/workflow-artifacts"] >= 1
        self.assertIn(".aw/workflow-artifacts/README.md", plan.files)
        self.assertIn(".aw/workflow-artifacts/README.md", plan.other_files)
        self.assertGreaterEqual(plan.counts.get(".aw/workflow-artifacts", 0), 1)

        # (c) run_deep_cleanup removes .aw/workflow-artifacts/README.md from disk
        engine.run_deep_cleanup(self.repo, plan, use_git=True)
        self.assertFalse((self.repo / ".aw/workflow-artifacts/README.md").is_file())
