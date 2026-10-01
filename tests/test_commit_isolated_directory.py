"""Unit tests for commit_isolated directory argument handling (IPD o39zn9).

Covers E-03 and E-05: commit_isolated returns a typed ISO_ERROR result instead of raising
IsADirectoryError when passed a directory path (both live and deleted directories),
leaves no worktree residue, and preserves deletion commit support for plain files.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from agent_workflows import commit_lock as L
from tests.support import git, init_repo


def _init_fixture(tmp_path: Path) -> Path:
    repo = init_repo(tmp_path / "repo")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    (repo / "sub").mkdir()
    (repo / "sub" / "a.txt").write_text("a\n", encoding="utf-8")
    (repo / "sub" / "b.txt").write_text("b\n", encoding="utf-8")
    (repo / "file.txt").write_text("file\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def test_commit_isolated_refuses_live_directory(tmp_path: Path):
    """E-03: commit_isolated returns ISO_ERROR on a live directory without worktree residue."""
    repo = _init_fixture(tmp_path)
    (repo / "sub" / "a.txt").write_text("a mod\n", encoding="utf-8")

    head_before = git(repo, "rev-parse", "HEAD").stdout.strip()
    status_before = git(repo, "status", "--porcelain").stdout

    res = L.commit_isolated(repo, ["sub"], message="commit live sub")

    assert res.status == L.ISO_ERROR
    assert res.commit is None
    assert "sub" in res.detail

    # HEAD and working tree untouched
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == head_before
    assert git(repo, "status", "--porcelain").stdout == status_before

    # No worktree residue
    wt_lines = git(repo, "worktree", "list").stdout.splitlines()
    assert len(wt_lines) == 1
    assert list(repo.parent.glob(".aw-isocommit-*")) == []


def test_commit_isolated_refuses_deleted_directory(tmp_path: Path):
    """E-05: commit_isolated returns ISO_ERROR on a deleted directory without worktree residue."""
    repo = _init_fixture(tmp_path)
    shutil.rmtree(repo / "sub")
    assert not (repo / "sub").is_dir()

    head_before = git(repo, "rev-parse", "HEAD").stdout.strip()
    status_before = git(repo, "status", "--porcelain").stdout

    res = L.commit_isolated(repo, ["sub"], message="commit deleted sub")

    assert res.status == L.ISO_ERROR
    assert res.commit is None
    assert "sub" in res.detail

    # HEAD and working tree untouched
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == head_before
    assert git(repo, "status", "--porcelain").stdout == status_before

    # No worktree residue
    wt_lines = git(repo, "worktree", "list").stdout.splitlines()
    assert len(wt_lines) == 1
    assert list(repo.parent.glob(".aw-isocommit-*")) == []


def test_commit_isolated_commits_deleted_plain_file(tmp_path: Path):
    """E-05 control: commit_isolated still commits a deleted plain file through the deletion arm."""
    repo = _init_fixture(tmp_path)
    (repo / "file.txt").unlink()

    res = L.commit_isolated(repo, ["file.txt"], message="delete plain file")

    assert res.status == L.ISO_COMMITTED
    assert res.commit is not None

    shown = git(repo, "show", "--name-status", "--pretty=format:", res.commit).stdout
    assert "D\tfile.txt" in shown

    wt_lines = git(repo, "worktree", "list").stdout.splitlines()
    assert len(wt_lines) == 1
    assert list(repo.parent.glob(".aw-isocommit-*")) == []
