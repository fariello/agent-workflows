"""Unit tests for the shared commit-what-I-changed helper (selfcommit child cv1rfd).

Covers V-01: path-scoping (only requested paths committed, unrelated dirty file untouched),
the TTY gate (non-TTY no-op, assume_yes commit, no_commit short-circuit, interactive yes/no),
both on_unrelated_staged policies, and a captured-git-argv assertion proving the helper never
uses ``add -A``/``-a``, ``push``, or ``--no-verify`` on any branch.

Also covers the optional ``trailers=`` parameter (IPD m73aet): ``AW-Run``/``AW-Item`` trailers are
appended as a real Git trailer block. Those assertions go THROUGH GIT'S OWN PARSER
(``git interpret-trailers --parse`` / ``git log --format=%(trailers)``) rather than through string
comparison, because a string assertion passes on a malformed block that git does not recognize -
the exact silent failure the feature exists to avoid.
"""

from __future__ import annotations

import argparse
import subprocess
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
    # Bytes, not text mode: on Windows text mode writes CRLF, and the whitespace-fixing hook
    # below rewrites with LF, which would turn a whitespace-only edit into a real line-ending diff.
    p.write_bytes(text.encode("utf-8"))
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


def test_path_scoping_and_deletion(repo: Path, rec):
    mine = _write(repo, "mine.txt", "mine\n")
    _write(repo, "other.txt", "not mine\n")  # unrelated, dirty, NOT in paths

    before = _head(repo)
    out = H.offer_commit(
        repo, [mine], message="chore(test): mine only", assume_yes=True
    )

    assert out.status == H.STATUS_COMMITTED
    assert out.commit and out.commit != before
    assert _committed_files(repo, out.commit) == {"mine.txt"}
    status = git(repo, "status", "--porcelain").stdout
    assert "?? other.txt" in status

    a = _write(repo, "a.txt", "a\n")
    b = _write(repo, "sub/b.txt", "b\n")
    git(repo, "add", "--", "a.txt", "sub/b.txt")
    git(repo, "commit", "-q", "-m", "add a,b")
    (repo / "a.txt").unlink()
    _write(repo, "sub/b.txt", "b2\n")

    out2 = H.offer_commit(
        repo, [a, b], message="chore(test): update a,b", assume_yes=True
    )
    assert out2.status == H.STATUS_COMMITTED
    assert set(out2.staged) == {"a.txt", "sub/b.txt"}
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (b) TTY gate branches
# --------------------------------------------------------------------------------------


def test_non_interactive_commit_modes(repo: Path, rec, monkeypatch):
    mine = _write(repo, "mine.txt", "mine\n")
    before = _head(repo)

    # 1. non-interactive without assume_yes is no-op
    out = H.offer_commit(
        repo, [mine], message="msg", assume_yes=False, interactive=False
    )
    assert out.status == H.STATUS_SKIPPED
    assert out.commit is None
    assert _head(repo) == before
    assert all("commit" not in c for c in rec.calls)

    # 2. interactive=None defaults to isatty probe
    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    out_probe = H.offer_commit(repo, [mine], message="msg")
    assert out_probe.status == H.STATUS_SKIPPED

    # 3. no_commit short-circuits regardless of tty
    rec.calls.clear()
    out_no_commit = H.offer_commit(
        repo,
        [mine],
        message="msg",
        assume_yes=True,
        no_commit=True,
        interactive=True,
    )
    assert out_no_commit.status == H.STATUS_SKIPPED
    assert _head(repo) == before
    assert rec.calls == []

    # 4. assume_yes commits non-interactively
    out_yes = H.offer_commit(
        repo, [mine], message="msg", assume_yes=True, interactive=False
    )
    assert out_yes.status == H.STATUS_COMMITTED
    assert _head(repo) != before
    rec.assert_contract_clean()


def test_interactive_commit_prompts_and_responses(repo: Path, rec, monkeypatch):
    # Prompt rendering
    p1 = _write(repo, "a.txt", "a\n")
    p2 = _write(repo, "b.txt", "b\n")
    captured = []
    monkeypatch.setattr(
        "builtins.input", lambda prompt: (captured.append(prompt), "y")[1]
    )
    H.offer_commit(repo, [p1, p2], message="msg", interactive=True)
    assert len(captured) == 1
    expected = (
        "The following path-scoped changes are ready to commit:\n"
        "  a.txt\n"
        "  b.txt\n"
        "Commit these path-scoped changes? [Y/n] "
    )
    assert captured[0] == expected

    # Responses: "n" declines
    mine = _write(repo, "mine.txt", "mine\n")
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "n")
    before = _head(repo)
    out_no = H.offer_commit(repo, [mine], message="msg", interactive=True)
    assert out_no.status == H.STATUS_DECLINED
    assert out_no.commit is None
    assert _head(repo) == before

    # Responses: "" (empty enter) defaults to yes
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
    out_enter = H.offer_commit(repo, [mine], message="msg", interactive=True)
    assert out_enter.status == H.STATUS_COMMITTED
    assert _head(repo) != before
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (c) on_unrelated_staged: scope vs refuse
# --------------------------------------------------------------------------------------


def test_on_unrelated_staged_policies(repo: Path, rec):
    with pytest.raises(ValueError):
        H.offer_commit(repo, ["seed.txt"], message="msg", on_unrelated_staged="bogus")

    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(
        repo,
        [mine],
        message="msg",
        assume_yes=True,
        on_unrelated_staged="refuse",
    )
    assert out.status == H.STATUS_COMMITTED

    _write(repo, "other.txt", "other\n")
    git(repo, "add", "--", "other.txt")
    before = _head(repo)

    mine2 = _write(repo, "mine2.txt", "mine2\n")
    out_refuse = H.offer_commit(
        repo,
        [mine2],
        message="chore(test): refuse",
        assume_yes=True,
        on_unrelated_staged="refuse",
    )
    assert out_refuse.status == H.STATUS_REFUSED_DIRTY
    assert out_refuse.commit is None
    assert _head(repo) == before

    out_scope = H.offer_commit(
        repo,
        [mine2],
        message="chore(test): scope",
        assume_yes=True,
        on_unrelated_staged="scope",
    )
    assert out_scope.status == H.STATUS_COMMITTED
    assert _committed_files(repo, out_scope.commit) == {"mine2.txt"}
    staged = git(repo, "diff", "--name-only", "--cached").stdout
    assert "other.txt" in staged
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# (d) edge cases + argv contract
# --------------------------------------------------------------------------------------


def test_nothing_to_commit_and_argv_contract(repo: Path, rec):
    out_empty = H.offer_commit(repo, [], message="msg", assume_yes=True)
    assert out_empty.status == H.STATUS_NOTHING_TO_COMMIT

    out_unchanged = H.offer_commit(repo, ["seed.txt"], message="msg", assume_yes=True)
    assert out_unchanged.status == H.STATUS_NOTHING_TO_COMMIT
    assert out_unchanged.commit is None

    rec.calls.clear()
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


# --------------------------------------------------------------------------------------
# (e) Optional AW-Run / AW-Item trailers (IPD m73aet)
#
# Every "are the trailers there?" assertion goes through GIT'S parser, never through a string
# comparison: a malformed block still produces a successful commit, so only git can tell us
# whether the trailers actually parse as trailers.
# --------------------------------------------------------------------------------------

RUN_ID = "run-20260901T042331Z-118022"
ITEM_ID = "m73aet"
TRAILERS = [f"AW-Run: {RUN_ID}", f"AW-Item: {ITEM_ID}"]


def _parse_trailers(text: str) -> list:
    """Ask GIT to parse the trailers out of a message (the authority, not our own regex)."""

    proc = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"git interpret-trailers failed: {proc.stderr}"
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def _commit_trailers(repo: Path, sha: str | None) -> list:
    """The trailers git itself reports for a real commit (``%(trailers)``)."""

    assert sha is not None, "expected a commit sha"
    out = git(repo, "log", "-1", "--format=%(trailers)", sha).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _raw_commit_message(repo: Path, sha: str | None) -> str:
    """The message EXACTLY as stored in the commit object.

    ``--format=%B`` appends a newline of its own, so it cannot support a byte-for-byte claim;
    ``cat-file commit`` gives the stored bytes (everything after the first blank line).
    """

    assert sha is not None, "expected a commit sha"
    raw = git(repo, "cat-file", "commit", sha).stdout
    return raw.split("\n\n", 1)[1]


def test_compose_trailers_parse_for_every_body_shape():
    """PURE composition (no git invoked to build it), verified BY git's parser."""
    cases = [
        ("single-line", "chore(test): subject only"),
        ("multiline", "chore(test): subject\n\nwhy this matters\nand more detail"),
        (
            "ends-in-trailer-block",
            "chore(test): subject\n\nbody\n\nCo-authored-by: x <x@e.com>",
        ),
        (
            "no-trailing-newline",
            "chore(test): subject\n\nbody with no trailing newline",
        ),
        ("trailing-newline", "chore(test): subject\n\nbody\n"),
        (
            "gitgen-mixed-block",
            "chore(test): subject\n\nprose line\nSigned-off-by: z <z@e.com>",
        ),
        (
            "markdown-divider",
            "chore(test): subject\n\nbody\n\n---\n\ndiffstat-ish tail",
        ),
    ]
    for label, body in cases:
        composed = H.compose_message_with_trailers(body, TRAILERS)
        parsed = _parse_trailers(composed)
        assert (
            f"AW-Run: {RUN_ID}" in parsed
        ), f"{label}: AW-Run did not parse: {composed!r}"
        assert (
            f"AW-Item: {ITEM_ID}" in parsed
        ), f"{label}: AW-Item did not parse: {composed!r}"
        blocks = [
            b
            for b in composed.strip().split("\n\n")
            if "AW-Run:" in b or "AW-Item:" in b
        ]
        assert len(blocks) == 1, f"{label}: trailers split across blocks: {composed!r}"


def test_compose_block_boundary_and_existing_trailers():
    body = "chore(test): subject\n\nbody\n\nCo-authored-by: x <x@e.com>"
    naive = body + "\n\n" + "\n".join(TRAILERS) + "\n"
    assert "Co-authored-by: x <x@e.com>" not in _parse_trailers(naive)
    ours = H.compose_message_with_trailers(body, TRAILERS)
    parsed = _parse_trailers(ours)
    assert "Co-authored-by: x <x@e.com>" in parsed, f"earlier trailer lost: {ours!r}"
    assert f"AW-Run: {RUN_ID}" in parsed
    assert f"AW-Item: {ITEM_ID}" in parsed

    non_blocks = [
        ("mixed-no-gitgen", "chore(test): subject\n\nprose line\nKey: value"),
        (
            "gitgen-under-25pct",
            "chore(test): subject\n\np1\np2\np3\np4\nSigned-off-by: z <z@e.com>",
        ),
        ("single-para-looks-like-trailers", "Key: value\nOther: thing"),
    ]
    for label, b in non_blocks:
        composed = H.compose_message_with_trailers(b, TRAILERS)
        p = _parse_trailers(composed)
        assert f"AW-Run: {RUN_ID}" in p, f"{label}: AW-Run did not parse: {composed!r}"
        assert (
            f"AW-Item: {ITEM_ID}" in p
        ), f"{label}: AW-Item did not parse: {composed!r}"
        assert composed.startswith(
            b.rstrip("\n")
        ), f"{label}: body altered: {composed!r}"


def test_is_trailer_block_matches_git_on_the_25_percent_rule():
    cases = [
        (["Key: v"], True),
        (["A: 1", "B: 2"], True),
        (["Signed-off-by: z", "  folded continuation"], True),
        (["prose", "Key: v"], False),
        (["p1", "p2", "p3", "Signed-off-by: z"], True),
        (["p1", "p2", "p3", "p4", "Signed-off-by: z"], False),
        (["prose only"], False),
        ([], False),
    ]
    for lines, expected in cases:
        assert H._is_trailer_block(lines) is expected, f"predicate wrong for {lines!r}"
        if lines:
            msg = "subject\n\n" + "\n".join(lines) + "\n"
            git_sees_block = bool(_parse_trailers(msg))
            assert (
                git_sees_block is expected
            ), f"git disagrees with the predicate for {lines!r}: git_sees={git_sees_block}"


def test_compose_is_pure_and_handles_empty_trailers(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("composition must not run a subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(H, "_git", _boom)
    out = H.compose_message_with_trailers("chore(test): subject\n\nbody", TRAILERS)
    assert out.endswith(f"AW-Run: {RUN_ID}\nAW-Item: {ITEM_ID}\n")

    for body in (
        "chore(test): subject only",
        "chore(test): subject\n\nmultiline\nbody",
        "chore(test): subject\n\nCo-authored-by: x <x@e.com>",
        "chore(test): subject\n\nno trailing newline",
        "",
    ):
        assert H.compose_message_with_trailers(body, []) == body
        assert H.compose_message_with_trailers(body, ()) == body


def test_trailers_on_real_commit_lifecycle(repo: Path, rec):
    # 1. Plain commit without trailers is unchanged
    message = "chore(test): plain\n\nbody line\n"
    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(repo, [mine], message=message, assume_yes=True)
    assert out.status == H.STATUS_COMMITTED
    assert _raw_commit_message(repo, out.commit) == message
    assert _commit_trailers(repo, out.commit) == []

    # 2. Trailers land on real commit and don't widen scope
    _write(repo, "other.txt", "not mine\n")
    _write(repo, "third.txt", "third\n")
    git(repo, "add", "--", "third.txt")
    mine2 = _write(repo, "mine2.txt", "mine2\n")
    out2 = H.offer_commit(
        repo,
        [mine2],
        message="chore(test): trailered\n\nsome body prose",
        assume_yes=True,
        trailers=TRAILERS,
    )
    assert out2.status == H.STATUS_COMMITTED
    assert out2.commit
    reported = _commit_trailers(repo, out2.commit)
    assert f"AW-Run: {RUN_ID}" in reported
    assert f"AW-Item: {ITEM_ID}" in reported
    assert _committed_files(repo, out2.commit) == {"mine2.txt"}
    assert set(out2.staged) == {"mine2.txt"}
    assert "?? other.txt" in git(repo, "status", "--porcelain").stdout
    assert "third.txt" in git(repo, "diff", "--name-only", "--cached").stdout

    # 3. Trailers join existing block on a real commit
    mine3 = _write(repo, "mine3.txt", "mine3\n")
    out3 = H.offer_commit(
        repo,
        [mine3],
        message="chore(test): joined\n\nbody\n\nCo-authored-by: x <x@e.com>",
        assume_yes=True,
        trailers=TRAILERS,
    )
    assert out3.status == H.STATUS_COMMITTED
    rep3 = _commit_trailers(repo, out3.commit)
    assert "Co-authored-by: x <x@e.com>" in rep3
    assert f"AW-Run: {RUN_ID}" in rep3
    assert f"AW-Item: {ITEM_ID}" in rep3
    rec.assert_contract_clean()


def test_no_trailers_commit_is_byte_identical_to_pre_change_behavior(repo: Path):
    for i, message in enumerate(
        [
            "chore(test): subject only",
            "chore(test): subject\n\nbody line\n",
            "chore(test): subject\n\nmultiline\nbody",
            "chore(test): subject\n\nCo-authored-by: x <x@e.com>",
        ]
    ):
        rel = _write(repo, f"f{i}.txt", f"v{i}\n")
        out = H.offer_commit(repo, [rel], message=message, assume_yes=True)
        assert out.status == H.STATUS_COMMITTED
        via_helper = _raw_commit_message(repo, out.commit)

        rel2 = _write(repo, f"g{i}.txt", f"v{i}\n")
        git(repo, "add", "--", rel2)
        git(repo, "commit", "-q", "-m", message, "--", rel2)
        via_raw_git = _raw_commit_message(repo, _head(repo))
        assert (
            via_helper == via_raw_git
        ), f"diverged from raw git commit -m for {message!r}"


def test_trailer_validation_and_shaping(repo: Path, rec):
    bad_trailers = [
        "AW-Run: one\nAW-Item: two",
        "AW-Run: one\rmore",
        "no-separator-at-all",
        ": empty key",
        "AW Run: whitespace in key",
        "AW_Run: underscore is not a git trailer token",
        "AW.Run: dot is not either",
    ]
    for bad in bad_trailers:
        with pytest.raises(H.TrailerError):
            H.validate_trailer(bad)
        with pytest.raises(H.TrailerError):
            H.compose_message_with_trailers("chore(test): subject", [bad])

    mine = _write(repo, "mine.txt", "mine\n")
    before = _head(repo)
    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): bad trailer",
        assume_yes=True,
        trailers=["AW-Run: has\nnewline"],
    )
    assert out.status == H.STATUS_ERROR
    assert out.commit is None
    assert _head(repo) == before
    assert git(repo, "diff", "--name-only", "--cached").stdout.strip() == ""
    assert rec.calls == []

    assert H.validate_trailer("AW-Run: r1") == "AW-Run: r1"
    assert H.validate_trailer(f"AW-Item: {ITEM_ID}") == f"AW-Item: {ITEM_ID}"
    assert H.validate_trailer("Key:") == "Key:"
    assert H.validate_trailer("AW-Run:r1") == "AW-Run: r1"
    assert _parse_trailers("subject\n\nKey:\n") == ["Key:"]

    assert H.run_item_trailers(RUN_ID, ITEM_ID) == TRAILERS
    assert H.run_item_trailers(RUN_ID, None) == [f"AW-Run: {RUN_ID}"]
    assert H.run_item_trailers(None, ITEM_ID) == [f"AW-Item: {ITEM_ID}"]
    assert H.run_item_trailers(None, None) == []
    assert H.run_item_trailers("", "  ") == []
    assert H.TRAILER_KEY_RUN == "AW-Run"
    assert H.TRAILER_KEY_ITEM == "AW-Item"
    composed = H.compose_message_with_trailers(
        "chore(test): subject", H.run_item_trailers(RUN_ID, ITEM_ID)
    )
    assert _parse_trailers(composed) == TRAILERS
    rec.assert_contract_clean()


def test_aw_commit_threads_trailers_and_lifecycle_delegates():
    from agent_workflows import work_cmd
    from agent_workflows import ipd_lifecycle as LC

    ns = argparse.Namespace(trailers=list(TRAILERS))
    assert work_cmd._trailers_from_args(ns) == TRAILERS
    ns2 = argparse.Namespace(run_id=RUN_ID, item_id6=ITEM_ID)
    assert work_cmd._trailers_from_args(ns2) == TRAILERS
    assert work_cmd._trailers_from_args(argparse.Namespace()) == []

    rc, out, _err = LC._git(Path("."), ["rev-parse", "--is-inside-work-tree"])
    assert rc == 0
    assert out.strip() == "true"


# --------------------------------------------------------------------------------------
# (g) A HOOK THAT REWRITES-AND-REJECTS: one bounded retry (IPD lqly9m E-07)
# --------------------------------------------------------------------------------------
#
# THE GAP THESE CLOSE IS WHY THE DEFECT SHIPPED. Before them this 767-line module made 16
# `offer_commit` calls and covered a hook-rejected commit ZERO times, because the shared fixture
# (`tests.support.init_repo`) does a bare `git init` and installs no hook at all. So the behavior that
# cost every agent a commit round trip for a stripped trailing space was invisible to the suite.
#
# WHY BOTH LAYERS. The detection and the retry live in `commit_lock.commit_isolated` (the only layer
# that can SEE the rewrite, since it happens inside the private worktree), while callers see the result
# through `offer_commit`. `tests/test_commit_lock.py` asserts the lower layer; these assert what a
# CALLER observes, including the `hook_fixed` report that keeps the mutation from being silent.

_HOOK_REWRITES_AND_REJECTS = """#!/bin/sh
# The pre-commit auto-fix shape: FIX the staged file, then exit nonzero.
changed=0
for f in $(git diff --cached --name-only); do
  [ -f "$f" ] || continue
  sed -e 's/[ \t]*$//' "$f" > "$f.awtmp"
  if cmp -s "$f" "$f.awtmp"; then
    rm -f "$f.awtmp"
  else
    mv "$f.awtmp" "$f"
    echo "Fixing $f"
    changed=1
  fi
done
[ "$changed" = 1 ] && exit 1
exit 0
"""

_HOOK_REFUSES_WITHOUT_TOUCHING = """#!/bin/sh
echo "refusing: policy violation" >&2
exit 1
"""


def _install_hook(repo: Path, body: str) -> Path:
    """Install a real `.git/hooks/pre-commit`, which the isolated worktree also runs."""

    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(body, encoding="utf-8")
    hook.chmod(0o755)
    return hook


def test_hook_rewrite_retry_and_peer_isolation(repo: Path, rec):
    _install_hook(repo, _HOOK_REWRITES_AND_REJECTS)
    mine = _write(repo, "art.md", "mine with trailing   \n")
    _write(repo, "peer.md", "peer work in progress   \n")
    before = _head(repo)

    out = H.offer_commit(repo, [mine], message="chore(test): art", assume_yes=True)

    assert out.status == H.STATUS_COMMITTED, out.message
    assert out.commit and out.commit != before
    assert out.hook_fixed == ("art.md",), out
    assert out.hook_fixed_diverged == ()
    assert "art.md" in out.message and "hooks fixed" in out.message
    assert git(repo, "show", f"{out.commit}:art.md").stdout == "mine with trailing\n"
    assert git(repo, "status", "--porcelain").stdout.strip() == "?? peer.md"
    assert (repo / "art.md").read_text(encoding="utf-8") == "mine with trailing\n"
    assert _committed_files(repo, out.commit) == {"art.md"}
    assert (repo / "peer.md").read_text(
        encoding="utf-8"
    ) == "peer work in progress   \n"
    rec.assert_contract_clean()


def test_hook_refusal_and_whitespace_only_handling(repo: Path, rec):
    _install_hook(repo, _HOOK_REFUSES_WITHOUT_TOUCHING)
    mine = _write(repo, "art.md", "clean content\n")
    before = _head(repo)

    out = H.offer_commit(repo, [mine], message="chore(test): art", assume_yes=True)
    assert out.status == H.STATUS_ERROR, out.message
    assert out.commit is None
    assert out.hook_fixed == ()
    assert _head(repo) == before
    commit_attempts = [c for c in rec.calls if c and c[0] == "commit"]
    assert len(commit_attempts) == 1, commit_attempts

    # Whitespace-only edit erased by hook reports nothing to commit
    rec.calls.clear()
    _install_hook(repo, _HOOK_REWRITES_AND_REJECTS)
    _write(repo, "art.md", "already clean\n")
    git(repo, "add", "--", "art.md")
    git(repo, "commit", "-q", "--no-verify", "-m", "seed art")
    before2 = _head(repo)
    _write(repo, "art.md", "already clean   \n")

    out2 = H.offer_commit(repo, ["art.md"], message="chore(test): art", assume_yes=True)
    assert out2.status == H.STATUS_NOTHING_TO_COMMIT, out2.message
    assert out2.hook_fixed == ("art.md",), out2
    assert _head(repo) == before2
    rec.assert_contract_clean()


def test_commit_outcome_keeps_its_positional_contract(repo: Path, rec):
    """`CommitOutcome` gained fields, so prove the POSITIONAL unpack existing callers use still holds."""

    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(repo, [mine], message="chore(test): mine", assume_yes=True)
    status, commit, staged, message, *rest = out
    assert status == H.STATUS_COMMITTED
    assert commit == out.commit
    assert staged == ("mine.txt",)
    assert message == out.message
    # The new fields are APPENDED with defaults, so a 4-field construction still works.
    legacy = H.CommitOutcome(H.STATUS_SKIPPED, None, (), "legacy 4-field caller")
    assert legacy.hook_fixed == () and legacy.hook_fixed_diverged == ()
    assert list(rest) == [(), ()]


# --------------------------------------------------------------------------------------
# A STAGED RENAME MUST COMMIT AS ONE MOVE, NOT AS A BARE ADDITION
#
# THE MEASURED BUG, 2026-09-22. `_staged_paths` used `git diff --name-only --cached`, which for a
# staged rename prints ONLY THE DESTINATION even though its docstring claimed to be "rename-aware".
# `offer_commit` intersects that set with the caller's paths (`our_staged`) and then commits
# `git commit -- <our_staged>`, so a caller that correctly named BOTH sides of its own `git mv` had
# the SOURCE silently filtered out and committed the addition WITHOUT the paired deletion.
#
# WHY IT MATTERED RATHER THAN BEING COSMETIC: every `aw oc run` backlog close routes here through
# `oc_runipd.commit_backlog_close`, and `status_set` deliberately relocates with `git mv` so the move
# would be ONE staged rename with (its own words) "no halves to pair up and no half to lose". This
# function lost the half anyway, producing 36 backlog items whose id6 existed in TWO status
# directories at once (e.g. `bplplj` in both `graduated/` and `done/`), each from a commit holding
# `A done/...` and no `D graduated/...`. `aw attention` reported 36 `attention.duplicate-id`
# violations and declared its whole board non-authoritative; the uncommitted deletions were still
# sitting in their originating lane worktrees days later. Repairing it also had to MERGE 80 history
# lines back, because each stale copy held provenance the lane's snapshot never had.
# --------------------------------------------------------------------------------------


def test_staged_rename_moves_and_duplicate_prevention(repo: Path, rec):
    src = _write(repo, "records/graduated/item-abc123.md", "body\n")
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed the item")
    (repo / "records/done").mkdir(parents=True, exist_ok=True)
    dest = "records/done/item-abc123.md"
    git(repo, "mv", src, dest)

    staged = H._staged_paths(repo)
    assert "records/graduated/item-abc123.md" in staged
    assert "records/done/item-abc123.md" in staged

    out = H.offer_commit(
        repo, [src, dest], message="close abc123", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_COMMITTED

    shown = git(
        repo, "show", "--name-status", "--pretty=format:", "-M", out.commit or "HEAD"
    ).stdout
    assert shown.strip().startswith("R")
    assert git(repo, "status", "--porcelain").stdout.strip() == ""
    assert _committed_files(repo, out.commit) == {dest}

    tracked = {
        ln.strip()
        for ln in git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
        if ln.strip()
    }
    assert dest in tracked
    assert src not in tracked

    # Naming only destination still works for another rename
    src2 = _write(repo, "records/graduated/item-xyz789.md", "body\n")
    git(repo, "add", "--", src2)
    git(repo, "commit", "-q", "-m", "seed second item")
    dest2 = "records/done/item-xyz789.md"
    git(repo, "mv", src2, dest2)
    out2 = H.offer_commit(
        repo, [dest2], message="close xyz789", assume_yes=True, interactive=False
    )
    assert out2.status == H.STATUS_COMMITTED

    # And a plain deletion is still committed
    victim = _write(repo, "records/open/item-def456.md", "body\n")
    git(repo, "add", "--", victim)
    git(repo, "commit", "-q", "-m", "seed victim")
    (repo / victim).unlink()
    out3 = H.offer_commit(
        repo, [victim], message="remove def456", assume_yes=True, interactive=False
    )
    assert out3.status == H.STATUS_COMMITTED
    assert victim not in git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout
    rec.assert_contract_clean()


# --------------------------------------------------------------------------------------
# UNTRACKED-DESTINATION RECORDS MOVE & DIRECTORY REFUSAL (IPD hv9gar)
# --------------------------------------------------------------------------------------


def _create_untracked_move_fixture(repo: Path) -> tuple[str, str]:
    """Build the writer's real output shape: write+unlink (NOT git mv).

    Leaves the destination UNTRACKED and the source deletion UNSTAGED, matching what
    `core.atomic_write` + `src.unlink()` leaves on disk before staging. Uses a realistic
    multi-line body (30+ lines) so git rename detection reliably scores high.
    """
    body = "".join(f"line {i}: content for record item-abc123\n" for i in range(35))
    src = _write(repo, "records/open/item-abc123.md", body)
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed item-abc123 in open")

    dest = "records/done/item-abc123.md"
    _write(repo, dest, body)
    (repo / src).unlink()
    return src, dest


def test_untracked_destination_shape_commits_both_halves_when_naming_explicit_files(
    repo: Path, rec
):
    """E-04: naming explicit files for an untracked-destination move commits atomically."""

    src, dest = _create_untracked_move_fixture(repo)

    # Prove the fixture starts with unstaged deletion and untracked destination (NOT git mv).
    status_before = git(repo, "status", "--porcelain").stdout
    assert f" D {src}" in status_before
    assert f"?? {dest}" in status_before or "?? records/done/" in status_before

    out = H.offer_commit(
        repo,
        [src, dest],
        message="close item-abc123",
        assume_yes=True,
        interactive=False,
    )
    assert out.status == H.STATUS_COMMITTED
    assert out.commit is not None
    assert set(out.staged) == {src, dest}

    # The commit carries a rename record or paired deletion and addition.
    shown = git(
        repo, "show", "--name-status", "--pretty=format:", "-M", out.commit
    ).stdout
    assert "records/open/item-abc123.md" in shown
    assert "records/done/item-abc123.md" in shown

    # Tree is clean after commit.
    assert git(repo, "status", "--porcelain").stdout.strip() == ""

    # Destination is present in HEAD, source is gone.
    tracked = git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
    assert dest in tracked
    assert src not in tracked
    rec.assert_contract_clean()


def test_mixed_file_and_directory_argument_is_refused_before_staging(repo: Path, rec):
    """E-02 / E-04: passing a directory argument in a mixed call is refused before staging."""

    src, dest = _create_untracked_move_fixture(repo)
    head_before = _head(repo)
    status_before = git(repo, "status", "--porcelain").stdout

    out = H.offer_commit(
        repo,
        [src, "records/done/"],
        message="close item-abc123",
        assume_yes=True,
        interactive=False,
    )
    assert out.status == H.STATUS_ERROR
    assert out.commit is None
    assert out.staged == ()
    # Refusal names the refused directory and the contained file.
    assert "records/done" in out.message
    assert dest in out.message

    # Crucial property: HEAD is unchanged and index/working tree is byte-identical (no staging residue).
    assert _head(repo) == head_before
    assert git(repo, "status", "--porcelain").stdout == status_before
    assert all("commit" not in c for c in rec.calls)
    rec.assert_contract_clean()


def test_all_directories_argument_is_refused_before_staging(repo: Path, rec):
    """E-02 / E-04 / F-6: passing only directory arguments is refused before staging."""

    src, dest = _create_untracked_move_fixture(repo)
    head_before = _head(repo)
    status_before = git(repo, "status", "--porcelain").stdout

    out = H.offer_commit(
        repo,
        ["records/open/", "records/done/"],
        message="close item-abc123",
        assume_yes=True,
        interactive=False,
    )
    assert out.status == H.STATUS_ERROR
    assert out.commit is None
    assert out.staged == ()
    # Refusal names the directories and contained files.
    assert "records/open" in out.message
    assert "records/done" in out.message
    assert src in out.message
    assert dest in out.message

    # HEAD is unchanged and index is completely untouched (no staged rename residue).
    assert _head(repo) == head_before
    assert git(repo, "status", "--porcelain").stdout == status_before
    assert all("commit" not in c for c in rec.calls)
    rec.assert_contract_clean()


def test_committed_outcome_reports_shortfall_for_unchanged_paths(repo: Path, rec):
    """E-03: committed outcome reports which requested paths had nothing to commit."""

    a = _write(repo, "a.txt", "a\n")
    b = _write(repo, "b.txt", "b\n")
    git(repo, "add", "--", a, b)
    git(repo, "commit", "-q", "-m", "seed a,b")

    # Modify only a.txt, pass both a.txt and b.txt.
    _write(repo, "a.txt", "a modified\n")

    out = H.offer_commit(
        repo, [a, b], message="update a", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_COMMITTED
    assert out.staged == ("a.txt",)
    assert "b.txt" in out.message
    assert "1 path(s) had nothing to commit" in out.message
    rec.assert_contract_clean()


def test_nothing_to_commit_reports_shortfall_paths(repo: Path, rec):
    """E-03: nothing-to-commit outcome reports the requested paths that had no changes."""

    out = H.offer_commit(
        repo, ["seed.txt"], message="no changes", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_NOTHING_TO_COMMIT
    assert out.commit is None
    assert "seed.txt" in out.message
    rec.assert_contract_clean()


def test_refused_directory_with_no_contained_changes(repo: Path):
    """E-02: a directory with no changed files is still refused before staging."""

    (repo / "empty_dir").mkdir()
    head_before = _head(repo)
    status_before = git(repo, "status", "--porcelain").stdout

    out = H.offer_commit(
        repo, ["empty_dir"], message="empty dir", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_ERROR
    assert "empty_dir" in out.message
    assert _head(repo) == head_before
    assert git(repo, "status", "--porcelain").stdout == status_before
