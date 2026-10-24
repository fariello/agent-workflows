"""Direct behavioral tests for run_evidence git provenance helpers.

Tests run_evidence.get_git_head, run_evidence._porcelain_paths, and
run_evidence.dirty_within against throwaway git repositories.
Created under backlog i2g20d, IPD s461lz.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_workflows import run_evidence

pytestmark = pytest.mark.core


def _git(root: Path, *args: str) -> str:
    """Run a git command in root with check=True and return stripped stdout."""
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _init_repo(root: Path) -> None:
    """Initialize a git repository in root with user identity configured."""
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "user.email", "test@test.local")


def _make_dirty_repo(root: Path) -> None:
    """Create a repo in the canonical E-04 dirty state."""
    _init_repo(root)
    (root / "a.txt").write_text("initial a\n", encoding="utf-8")
    (root / "b.txt").write_text("initial b\n", encoding="utf-8")
    _git(root, "add", "a.txt", "b.txt")
    _git(root, "commit", "-qm", "initial commit")

    # (a) modifying committed a.txt
    (root / "a.txt").write_text("modified a\n", encoding="utf-8")
    # (b) git mv b.txt c.txt
    _git(root, "mv", "b.txt", "c.txt")
    # (c) creating untracked new/sub/x.py inside a wholly new directory
    (root / "new" / "sub").mkdir(parents=True, exist_ok=True)
    (root / "new" / "sub" / "x.py").write_text("untracked x\n", encoding="utf-8")


def _matcher(path: str, scope: str) -> bool:
    return path == scope or path.startswith(scope.rstrip("/") + "/")


class TestGetGitHead:
    """Direct behavioral tests for run_evidence.get_git_head (E-03)."""

    def test_non_repo_returns_unversioned(self, tmp_path: Path) -> None:
        assert run_evidence.get_git_head(tmp_path) == "unversioned"

    def test_unborn_repo_returns_unversioned(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        assert run_evidence.get_git_head(tmp_path) == "unversioned"

    def test_committed_repo_returns_head_sha(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "a.txt").write_text("test\n", encoding="utf-8")
        _git(tmp_path, "add", "a.txt")
        _git(tmp_path, "commit", "-qm", "initial commit")

        sha = _git(tmp_path, "rev-parse", "HEAD")
        assert len(sha) == 40
        assert run_evidence.get_git_head(tmp_path) == sha


class TestPorcelainPaths:
    """Direct behavioral tests for run_evidence._porcelain_paths (E-04)."""

    def test_non_repo_returns_none(self, tmp_path: Path) -> None:
        assert run_evidence._porcelain_paths(tmp_path) is None

    def test_unborn_repo_returns_empty_list(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        assert run_evidence._porcelain_paths(tmp_path) == []

    def test_clean_committed_repo_returns_empty_list(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "a.txt").write_text("test\n", encoding="utf-8")
        _git(tmp_path, "add", "a.txt")
        _git(tmp_path, "commit", "-qm", "initial commit")
        assert run_evidence._porcelain_paths(tmp_path) == []

    def test_dirty_tree_returns_sorted_deduped_paths(self, tmp_path: Path) -> None:
        _make_dirty_repo(tmp_path)
        paths = run_evidence._porcelain_paths(tmp_path)
        assert paths is not None
        assert sorted(paths) == ["a.txt", "b.txt", "c.txt", "new/sub/x.py"]
        assert len(paths) == len(set(paths))


class TestDirtyWithin:
    """Direct behavioral tests for run_evidence.dirty_within (E-05)."""

    def test_non_repo_with_non_empty_scope_returns_unversioned(
        self, tmp_path: Path
    ) -> None:
        assert run_evidence.dirty_within(tmp_path, ["a.txt"], _matcher) == "unversioned"

    def test_empty_scope_returns_clean_even_when_tree_is_dirty(
        self, tmp_path: Path
    ) -> None:
        _make_dirty_repo(tmp_path)
        assert run_evidence.dirty_within(tmp_path, [], _matcher) == "clean"

    def test_in_scope_dirt_returns_sorted_newline_joined(self, tmp_path: Path) -> None:
        _make_dirty_repo(tmp_path)
        assert run_evidence.dirty_within(tmp_path, ["a.txt"], _matcher) == "a.txt"
        assert (
            run_evidence.dirty_within(tmp_path, ["new/", "a.txt", "b.txt"], _matcher)
            == "a.txt\nb.txt\nnew/sub/x.py"
        )

    def test_disjoint_scope_returns_clean(self, tmp_path: Path) -> None:
        _make_dirty_repo(tmp_path)
        assert run_evidence.dirty_within(tmp_path, ["zzz.txt"], _matcher) == "clean"

    def test_clean_repo_returns_clean(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "a.txt").write_text("test\n", encoding="utf-8")
        _git(tmp_path, "add", "a.txt")
        _git(tmp_path, "commit", "-qm", "initial commit")
        assert run_evidence.dirty_within(tmp_path, ["a.txt"], _matcher) == "clean"
