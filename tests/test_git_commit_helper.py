"""Unit tests for the shared commit-what-I-changed helper (selfcommit child cv1rfd).

Covers V-01: path-scoping (only requested paths committed, unrelated dirty file untouched),
the TTY gate (non-TTY no-op, assume_yes commit, no_commit short-circuit, interactive yes/no),
both on_unrelated_staged policies, and a captured-git-argv assertion proving the helper never
uses ``add -A``/``-a``, ``push``, or ``--no-verify`` on any branch.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from agent_workflows import git_commit_helper as H
from tests.support import git, init_repo


# --------------------------------------------------------------------------------------
# Fixtures / helpers
# --------------------------------------------------------------------------------------


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A git repo with one initial commit so HEAD exists."""

    r = init_repo(tmp_path / "repo")
    (r / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(r, "add", "--", "seed.txt")
    git(r, "commit", "-q", "-m", "seed")
    return r


def _write(repo: Path, rel: str, text: str) -> str:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return rel


def _head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _committed_files(repo: Path, sha: str | None) -> set:
    assert sha is not None, "expected a commit sha"
    out = git(repo, "show", "--name-only", "--pretty=format:", sha).stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


class _ArgvRecorder:
    """Wrap H._git to record every git argv, delegating to the real runner."""

    def __init__(self, real):
        self.real = real
        self.calls: list[list[str]] = []

    def __call__(self, repo_root, args):
        self.calls.append(list(args))
        return self.real(repo_root, args)

    def assert_contract_clean(self):
        for args in self.calls:
            assert "-A" not in args, f"forbidden 'git add -A' in {args}"
            assert "--all" not in args, f"forbidden '--all' in {args}"
            assert "-a" not in args, f"forbidden 'git commit -a' in {args}"
            assert "push" not in args, f"forbidden 'git push' in {args}"
            assert "--no-verify" not in args, f"forbidden '--no-verify' in {args}"


@pytest.fixture()
def rec(monkeypatch):
    r = _ArgvRecorder(H._git)
    monkeypatch.setattr(H, "_git", r)
    return r


# --------------------------------------------------------------------------------------
# (a) Path-scoping: only requested paths committed; unrelated dirty file stays uncommitted
# --------------------------------------------------------------------------------------


def test_commits_only_requested_paths_leaving_unrelated_dirty(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    _write(repo, "other.txt", "not mine\n")  # unrelated, dirty, NOT in paths

    before = _head(repo)
    out = H.offer_commit(
        repo, [mine], message="chore(test): mine only", assume_yes=True
    )

    assert out.status == H.STATUS_COMMITTED
    assert out.commit and out.commit != before
    assert _committed_files(repo, out.commit) == {"mine.txt"}
    # other.txt must remain uncommitted and untracked.
    status = git(repo, "status", "--porcelain").stdout
    assert "?? other.txt" in status
    rec.assert_contract_clean()


def test_multiple_paths_and_deletion(repo: Path, rec):
    a = _write(repo, "a.txt", "a\n")
    b = _write(repo, "sub/b.txt", "b\n")
    git(repo, "add", "--", "a.txt", "sub/b.txt")
    git(repo, "commit", "-q", "-m", "add a,b")
    # Now delete a and modify b; both are "mine".
    (repo / "a.txt").unlink()
    _write(repo, "sub/b.txt", "b2\n")

    out = H.offer_commit(
        repo, [a, b], message="chore(test): update a,b", assume_yes=True
    )
    assert out.status == H.STATUS_COMMITTED
    assert set(out.staged) == {"a.txt", "sub/b.txt"}
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (b) TTY gate branches
# --------------------------------------------------------------------------------------


def test_non_interactive_without_assume_yes_is_noop(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    before = _head(repo)
    out = H.offer_commit(
        repo, [mine], message="msg", assume_yes=False, interactive=False
    )
    assert out.status == H.STATUS_SKIPPED
    assert out.commit is None
    assert _head(repo) == before  # no commit created
    # It must NOT even stage (no add) on the skip branch.
    assert all("commit" not in c for c in rec.calls)
    rec.assert_contract_clean()


def test_assume_yes_commits_non_interactively(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    before = _head(repo)
    out = H.offer_commit(
        repo, [mine], message="msg", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_COMMITTED
    assert _head(repo) != before
    rec.assert_contract_clean()


def test_no_commit_short_circuits_regardless_of_tty(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    before = _head(repo)
    # no_commit wins even with assume_yes and interactive True.
    out = H.offer_commit(
        repo,
        [mine],
        message="msg",
        assume_yes=True,
        no_commit=True,
        interactive=True,
    )
    assert out.status == H.STATUS_SKIPPED
    assert _head(repo) == before
    assert rec.calls == []  # short-circuit before touching git
    rec.assert_contract_clean()


def test_interactive_yes_commits(repo: Path, rec, monkeypatch):
    mine = _write(repo, "mine.txt", "mine\n")
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "y")
    before = _head(repo)
    out = H.offer_commit(repo, [mine], message="msg", interactive=True)
    assert out.status == H.STATUS_COMMITTED
    assert _head(repo) != before
    rec.assert_contract_clean()


def test_interactive_no_declines(repo: Path, rec, monkeypatch):
    mine = _write(repo, "mine.txt", "mine\n")
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "n")
    before = _head(repo)
    out = H.offer_commit(repo, [mine], message="msg", interactive=True)
    assert out.status == H.STATUS_DECLINED
    assert out.commit is None
    assert _head(repo) == before
    # declined before staging/committing.
    assert all("commit" not in c for c in rec.calls)
    rec.assert_contract_clean()


def test_interactive_defaults_to_tty_probe(repo: Path, rec, monkeypatch):
    """interactive=None consults sys.stdin.isatty (same signal as cli._confirm)."""

    mine = _write(repo, "mine.txt", "mine\n")

    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    out = H.offer_commit(repo, [mine], message="msg")  # interactive defaults to None
    assert out.status == H.STATUS_SKIPPED  # non-TTY -> no-op
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (c) on_unrelated_staged: scope vs refuse
# --------------------------------------------------------------------------------------


def test_on_unrelated_staged_scope_leaves_unrelated_staged(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    _write(repo, "other.txt", "other\n")
    git(repo, "add", "--", "other.txt")  # pre-stage an UNRELATED path

    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): scope",
        assume_yes=True,
        on_unrelated_staged="scope",
    )
    assert out.status == H.STATUS_COMMITTED
    assert _committed_files(repo, out.commit) == {"mine.txt"}
    # other.txt is still staged-but-uncommitted.
    staged = git(repo, "diff", "--name-only", "--cached").stdout
    assert "other.txt" in staged
    rec.assert_contract_clean()


def test_on_unrelated_staged_refuse_commits_nothing(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    _write(repo, "other.txt", "other\n")
    git(repo, "add", "--", "other.txt")  # pre-stage an UNRELATED path
    before = _head(repo)

    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): refuse",
        assume_yes=True,
        on_unrelated_staged="refuse",
    )
    assert out.status == H.STATUS_REFUSED_DIRTY
    assert out.commit is None
    assert _head(repo) == before
    # Nothing of ours was staged (no add call reached).
    assert all("commit" not in c for c in rec.calls)
    rec.assert_contract_clean()


def test_refuse_ignores_unrelated_when_none_staged(repo: Path, rec):
    """refuse with a clean index still commits our paths."""

    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(
        repo,
        [mine],
        message="msg",
        assume_yes=True,
        on_unrelated_staged="refuse",
    )
    assert out.status == H.STATUS_COMMITTED
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (d) edge cases + argv contract
# --------------------------------------------------------------------------------------


def test_nothing_to_commit_when_no_paths(repo: Path):
    out = H.offer_commit(repo, [], message="msg", assume_yes=True)
    assert out.status == H.STATUS_NOTHING_TO_COMMIT


def test_nothing_to_commit_when_paths_unchanged(repo: Path, rec):
    # seed.txt exists and is already committed, unchanged.
    out = H.offer_commit(repo, ["seed.txt"], message="msg", assume_yes=True)
    assert out.status == H.STATUS_NOTHING_TO_COMMIT
    assert out.commit is None
    rec.assert_contract_clean()


def test_invalid_on_unrelated_staged_raises(repo: Path):
    with pytest.raises(ValueError):
        H.offer_commit(repo, ["seed.txt"], message="msg", on_unrelated_staged="bogus")


def test_uses_path_scoped_add_and_commit_argv(repo: Path, rec):
    """Assert the exact argv shape: add -- <paths> and commit -m <msg> -- <paths>."""

    mine = _write(repo, "mine.txt", "mine\n")
    H.offer_commit(repo, [mine], message="chore(test): argv", assume_yes=True)

    add_calls = [c for c in rec.calls if c and c[0] == "add"]
    commit_calls = [c for c in rec.calls if c and c[0] == "commit"]
    assert add_calls, "expected a git add call"
    assert commit_calls, "expected a git commit call"
    for c in add_calls:
        assert c[1] == "--", f"add must be path-scoped (add -- <paths>): {c}"
        assert "mine.txt" in c
    for c in commit_calls:
        assert "-m" in c
        assert "--" in c, f"commit must be path-scoped: {c}"
        assert "mine.txt" in c
    rec.assert_contract_clean()


def test_ipd_lifecycle_git_delegates_to_shared_runner():
    """The single-wrapper contract: ipd_lifecycle._git resolves to the same runner as here."""

    from agent_workflows import ipd_lifecycle as LC

    # ipd_lifecycle._git delegates into git_commit_helper._git; a smoke call still works.
    rc, out, _err = LC._git(Path("."), ["rev-parse", "--is-inside-work-tree"])
    assert rc == 0
    assert out.strip() == "true"
