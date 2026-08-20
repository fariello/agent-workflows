"""Regression test asserting layout-inventory walk prunes gitignored directory subtrees (IPD m7e2g3 / ith2xd)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    from agent_workflows import layout_inventory as inv_mod
except ImportError:
    from tools.awphysical import aw_layout_inventory as inv_mod


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class LayoutInventoryGitignoreTests(unittest.TestCase):
    """Regression test suite proving _ignored_dirs, _walk, and inventory prune gitignored subtrees."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="test_layout_inv_gitignore_")
        self.repo = Path(self.tmp) / "repo"
        self.repo.mkdir(parents=True)

        _run_git(self.repo, ["init"])
        _run_git(self.repo, ["config", "user.name", "Test User"])
        _run_git(self.repo, ["config", "user.email", "test@example.com"])

        # Write .gitignore specifying directory subtrees to ignore
        (self.repo / ".gitignore").write_text(
            "node_modules/\nvendor/\n", encoding="utf-8"
        )

        # Create tracked legacy directories and files
        self.agents_dir = self.repo / ".agents" / "workflows"
        self.agents_dir.mkdir(parents=True)
        self.sample_wf = self.agents_dir / "sample.md"
        self.sample_wf.write_text("# Sample Workflow\n", encoding="utf-8")

        self.artifacts_dir = self.repo / "workflow-artifacts" / "run1"
        self.artifacts_dir.mkdir(parents=True)
        self.sample_art = self.artifacts_dir / "output.log"
        self.sample_art.write_text("run output\n", encoding="utf-8")

        _run_git(self.repo, ["add", "."])
        _run_git(self.repo, ["commit", "-m", "initial tracked commit"])

        # Populate gitignored subtrees with files at root and within roots
        self.root_node_modules = self.repo / "node_modules" / "dep_a"
        self.root_node_modules.mkdir(parents=True)
        (self.root_node_modules / "index.js").write_text(
            "module.exports = 1;\n", encoding="utf-8"
        )
        (self.root_node_modules / "package.json").write_text("{}", encoding="utf-8")

        self.agents_node_modules = self.repo / ".agents" / "node_modules" / "dep_b"
        self.agents_node_modules.mkdir(parents=True)
        (self.agents_node_modules / "index.js").write_text(
            "module.exports = 2;\n", encoding="utf-8"
        )

        self.artifacts_node_modules = (
            self.repo / "workflow-artifacts" / "node_modules" / "dep_c"
        )
        self.artifacts_node_modules.mkdir(parents=True)
        (self.artifacts_node_modules / "index.js").write_text(
            "module.exports = 3;\n", encoding="utf-8"
        )

        self.agents_vendor = self.repo / ".agents" / "vendor" / "lib_a"
        self.agents_vendor.mkdir(parents=True)
        (self.agents_vendor / "lib.py").write_text("x = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ignored_dirs_identifies_gitignored_directories(self) -> None:
        """_ignored_dirs returns repo-relative POSIX paths of gitignored directories."""
        ignored = inv_mod._ignored_dirs(self.repo)

        # Positive assertions: gitignored directories must be identified
        self.assertIn("node_modules", ignored)
        self.assertIn(".agents/node_modules", ignored)
        self.assertIn("workflow-artifacts/node_modules", ignored)
        self.assertIn(".agents/vendor", ignored)

        # Negative assertions: tracked directories must not be in ignored_dirs
        self.assertNotIn(".agents", ignored)
        self.assertNotIn(".agents/workflows", ignored)
        self.assertNotIn("workflow-artifacts", ignored)
        self.assertNotIn("workflow-artifacts/run1", ignored)

    def test_walk_prunes_ignored_directory_subtrees(self) -> None:
        """_walk prunes ignored directory subtrees so they and their children are never yielded."""
        ignored = inv_mod._ignored_dirs(self.repo)

        # Walk from repo root
        root_walked = list(
            inv_mod._walk(self.repo, ignored_dirs=ignored, repo=self.repo)
        )
        root_walked_rel = [
            p.relative_to(self.repo).as_posix() for p in root_walked if p != self.repo
        ]

        self.assertIn(".agents/workflows/sample.md", root_walked_rel)
        self.assertIn("workflow-artifacts/run1/output.log", root_walked_rel)

        # Ensure no path under node_modules or vendor was yielded
        leaked = [p for p in root_walked_rel if "node_modules" in p or "vendor" in p]
        self.assertEqual(leaked, [], f"Expected 0 leaked ignored paths, got: {leaked}")

        # Walk from .agents sub-root
        agents_walked = list(
            inv_mod._walk(self.repo / ".agents", ignored_dirs=ignored, repo=self.repo)
        )
        agents_walked_rel = [p.relative_to(self.repo).as_posix() for p in agents_walked]

        self.assertIn(".agents/workflows/sample.md", agents_walked_rel)
        agents_leaked = [
            p for p in agents_walked_rel if "node_modules" in p or "vendor" in p
        ]
        self.assertEqual(
            agents_leaked,
            [],
            f"Expected 0 leaked ignored paths under .agents, got: {agents_leaked}",
        )

    def test_walk_without_ignored_dirs_descends_into_subtrees(self) -> None:
        """Falsifiability: _walk descends into node_modules when ignored_dirs is not supplied."""
        unpruned_walk = list(
            inv_mod._walk(self.repo, ignored_dirs=set(), repo=self.repo)
        )
        unpruned_rel = [
            p.relative_to(self.repo).as_posix() for p in unpruned_walk if p != self.repo
        ]

        # Without ignored_dirs, os.walk encounters node_modules
        node_modules_entries = [p for p in unpruned_rel if "node_modules" in p]
        self.assertTrue(
            len(node_modules_entries) > 0, "Unpruned walk must yield node_modules paths"
        )

    def test_inventory_prunes_ignored_directories_across_roots(self) -> None:
        """inventory() yields items only from non-ignored paths and prunes node_modules subtrees."""
        roots = inv_mod._default_roots(self.repo)
        inv_res = inv_mod.inventory(self.repo, roots, include_paths=False)

        self.assertTrue(
            inv_res.get("valid"), f"Inventory reported errors: {inv_res.get('errors')}"
        )
        items = inv_res.get("items", [])
        self.assertGreater(len(items), 0)

        # Verify tracked items are present
        relpaths = {f"{item['source_root']}:{item['source_relpath']}" for item in items}
        self.assertIn("agents:workflows/sample.md", relpaths)
        self.assertIn("workflow-artifacts:run1/output.log", relpaths)

        # Verify no item belongs to an ignored subtree
        for item in items:
            source_rel = item.get("source_relpath", "")
            self.assertNotIn(
                "node_modules", source_rel, f"Found node_modules item: {item}"
            )
            self.assertNotIn("vendor", source_rel, f"Found vendor item: {item}")


if __name__ == "__main__":
    unittest.main()
