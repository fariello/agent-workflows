"""Tests for agent_workflows.discovery (IPD-2 Batch C; AC-13). Stdlib unittest only."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import discovery as DISC


def _make_repo(path: Path) -> Path:
    """Create a directory that looks like a git repo (a .git dir is enough here)."""

    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").mkdir()
    return path


class IsGitRepoTests(unittest.TestCase):
    def test_dir_with_git_dir_is_repo(self):
        with tempfile.TemporaryDirectory() as d:
            r = _make_repo(Path(d) / "r")
            self.assertTrue(DISC.is_git_repo(r))

    def test_git_file_also_counts(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / "r"
            r.mkdir()
            (r / ".git").write_text("gitdir: ../.git/modules/r\n", encoding="utf-8")
            self.assertTrue(DISC.is_git_repo(r))

    def test_plain_dir_is_not_repo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(DISC.is_git_repo(Path(d)))


class DiscoverTests(unittest.TestCase):
    def test_configured_path_that_is_a_repo_is_the_target_no_descent(self):
        with tempfile.TemporaryDirectory() as d:
            root = _make_repo(Path(d) / "solo")
            # A nested repo inside must NOT be discovered (we do not descend into a repo).
            _make_repo(root / "nested")
            res = DISC.discover([root])
            self.assertEqual(res.targets, [root.resolve()])

    def test_scans_immediate_children_of_a_non_repo_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            a = _make_repo(root / "a")
            b = _make_repo(root / "b")
            (root / "not_a_repo").mkdir()
            res = DISC.discover([root])
            self.assertEqual(set(res.targets), {a.resolve(), b.resolve()})
            self.assertIn((root / "not_a_repo").resolve(), res.skipped)
            self.assertEqual(
                res.skipped[(root / "not_a_repo").resolve()], "not-a-git-repo"
            )

    def test_submodule_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            # 'root' is not a repo; it has a child repo 'lib' declared as a submodule.
            lib = _make_repo(root / "lib")
            (root / ".gitmodules").write_text(
                '[submodule "lib"]\n\tpath = lib\n\turl = https://example/lib.git\n',
                encoding="utf-8",
            )
            res = DISC.discover([root])
            self.assertNotIn(lib.resolve(), res.targets)
            self.assertEqual(res.skipped.get(lib.resolve()), "submodule")

    def test_ignore_glob_excludes_from_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            keep = _make_repo(root / "keep")
            skip = _make_repo(root / "vendor_pkg")
            res = DISC.discover([root], ignore=["*/vendor_*"])
            self.assertIn(keep.resolve(), res.targets)
            self.assertNotIn(skip.resolve(), res.targets)
            self.assertIn(skip.resolve(), res.ignored)

    def test_exclude_exact_path_blocklists_from_discovery(self):
        # E-02: an exact-path exclude lands in `excluded`, not `targets`, and NOT `ignored`.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            keep = _make_repo(root / "keep")
            blocked = _make_repo(root / "legacy")
            res = DISC.discover([root], exclude=[str(blocked.resolve())])
            self.assertIn(keep.resolve(), res.targets)
            self.assertNotIn(blocked.resolve(), res.targets)
            self.assertIn(blocked.resolve(), res.excluded)
            self.assertNotIn(blocked.resolve(), res.ignored)

    def test_exclude_glob_blocklists_from_discovery(self):
        # E-02: a glob exclude also lands in `excluded` (distinct from the ignore filter).
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            keep = _make_repo(root / "keep")
            blocked = _make_repo(root / "never_install_me")
            res = DISC.discover([root], exclude=["*/never_install_*"])
            self.assertIn(keep.resolve(), res.targets)
            self.assertIn(blocked.resolve(), res.excluded)
            self.assertNotIn(blocked.resolve(), res.targets)

    def test_exclude_and_ignore_are_distinct(self):
        # E-02: ignore keeps its own meaning; an ignore match goes to `ignored`, an
        # exclude match goes to `excluded`, never conflated.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            root.mkdir()
            ignored = _make_repo(root / "vendor_pkg")
            excluded = _make_repo(root / "legacy")
            res = DISC.discover(
                [root], ignore=["*/vendor_*"], exclude=[str(excluded.resolve())]
            )
            self.assertIn(ignored.resolve(), res.ignored)
            self.assertNotIn(ignored.resolve(), res.excluded)
            self.assertIn(excluded.resolve(), res.excluded)
            self.assertNotIn(excluded.resolve(), res.ignored)

    def test_explicit_repo_root_exclude_lands_in_excluded(self):
        # A configured path that IS a repo and is excluded goes to `excluded`, not targets.
        with tempfile.TemporaryDirectory() as d:
            r = _make_repo(Path(d) / "legacy")
            res = DISC.discover([r], exclude=[str(r.resolve())])
            self.assertIn(r.resolve(), res.excluded)
            self.assertEqual(res.targets, [])

    def test_missing_root_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "does_not_exist"
            res = DISC.discover([missing])
            self.assertEqual(res.skipped.get(missing.resolve()), "missing")

    def test_recursive_opt_in_finds_nested_repos(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "src"
            (root / "team" / "deep").mkdir(parents=True)
            nested = _make_repo(root / "team" / "deep" / "proj")
            # Non-recursive: nothing at the immediate level is a repo.
            shallow = DISC.discover([root])
            self.assertEqual(shallow.targets, [])
            # Recursive: the deep repo is found.
            deep = DISC.discover([root], recursive=True)
            self.assertIn(nested.resolve(), deep.targets)

    def test_explicit_repo_not_subject_to_ignore_is_caller_responsibility(self):
        # discover() applies ignore uniformly; the CLI only passes ignore for `all`,
        # never for an explicit `install <dir>`. Here we verify ignore DOES apply when
        # provided, so the CLI's decision to omit it for explicit installs is meaningful.
        with tempfile.TemporaryDirectory() as d:
            r = _make_repo(Path(d) / "vendor_thing")
            res = DISC.discover([r], ignore=["*/vendor_*"])
            self.assertIn(r.resolve(), res.ignored)
            self.assertEqual(res.targets, [])


if __name__ == "__main__":
    unittest.main()
