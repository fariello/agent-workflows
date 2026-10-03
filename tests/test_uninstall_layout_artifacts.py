"""Tests for uninstall removal of install-emitted layout artifacts (IPD 5j7jv1, backlog 4vfkl1)."""

import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import engine
from tests.support import SOURCE_WORKFLOWS, git, init_repo


class UninstallLayoutArtifactsTests(unittest.TestCase):
    """Behavioral unit tests for removal of layout artifacts during uninstall_repo.

    Default-visible (no module-level slow mark). Built on a minimal hand-crafted fixture repo
    rather than a real install so pytest runs them in milliseconds.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self.tmp.name) / "repo")
        (self.repo / "README.md").write_text("initial\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "init")

        self.aw_dir = self.repo / ".aw"
        self.system_dir = self.aw_dir / "system"
        self.system_dir.mkdir(parents=True, exist_ok=True)
        (self.system_dir / "layout.json").write_text("{}", encoding="utf-8")
        (self.system_dir / "layout.schema.json").write_text("{}", encoding="utf-8")
        (self.aw_dir / ".gitignore").write_text(
            "system/layout.json\nsystem/layout.schema.json\n", encoding="utf-8"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_uninstall_removes_layout_artifacts(self):
        """(1) Both layout files are gone after uninstall_repo."""
        changed = []
        engine.uninstall_repo(self.repo, use_git=True, force=True, changed_out=changed)
        self.assertFalse((self.system_dir / "layout.json").exists())
        self.assertFalse((self.system_dir / "layout.schema.json").exists())

    def test_uninstall_records_layout_artifacts_in_changed_out(self):
        """(2) Both repo-relative paths appear in the changed_out list."""
        changed = []
        engine.uninstall_repo(self.repo, use_git=True, force=True, changed_out=changed)
        self.assertIn(".aw/system/layout.json", changed)
        self.assertIn(".aw/system/layout.schema.json", changed)

    def test_uninstall_prunes_empty_aw_system_and_aw_base(self):
        """(3) .aw/system/ is pruned when it held nothing else, and .aw/ with it."""
        changed = []
        engine.uninstall_repo(self.repo, use_git=True, force=True, changed_out=changed)
        self.assertFalse(self.system_dir.exists())
        self.assertFalse(self.aw_dir.exists())

    def test_negative_control_unrelated_sibling_preserves_aw_system(self):
        """(4) Negative control: a non-owned .aw/system/ sibling survives and keeps .aw/system/ alive."""
        unrelated = self.system_dir / "custom_tool.py"
        unrelated.write_text("# user custom tool\n", encoding="utf-8")
        changed = []
        engine.uninstall_repo(self.repo, use_git=True, force=True, changed_out=changed)
        self.assertFalse((self.system_dir / "layout.json").exists())
        self.assertFalse((self.system_dir / "layout.schema.json").exists())
        self.assertTrue(unrelated.exists())
        self.assertTrue(self.system_dir.exists())
        self.assertTrue(self.aw_dir.exists())


class RealInstallIntegrationTests(unittest.TestCase):
    """Integration test on a full real install.

    Class-scoped slow mark: deselected under `-m 'not slow'` while primary tests run.
    """

    pytestmark = pytest.mark.slow

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self.tmp.name) / "repo")

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_install_uninstall_deep_cleanup_removes_aw_directory(self):
        """Real install proves shipped emit_layout_artifacts and uninstall agree to leave no .aw/."""
        engine.install_into_repo(self.repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        engine.write_setup_marker(self.repo)

        changed = []
        engine.uninstall_repo(self.repo, use_git=True, force=True, changed_out=changed)
        self.assertIn(".aw/system/layout.json", changed)
        self.assertIn(".aw/system/layout.schema.json", changed)

        plan = engine.plan_deep_cleanup(self.repo)
        engine.run_deep_cleanup(self.repo, plan, use_git=True, remove_records=True)

        self.assertFalse(
            (self.repo / ".aw").exists(),
            "NO .aw/ directory must remain after install, uninstall, and deep cleanup with records remove",
        )
