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


def test_interactive_empty_enter_defaults_to_yes(repo: Path, rec, monkeypatch):
    mine = _write(repo, "mine.txt", "mine\n")
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
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


def test_interactive_prompt_renders_paths_one_per_line(repo: Path, monkeypatch):
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


@pytest.mark.parametrize(
    "label,body",
    [
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
    ],
)
def test_compose_trailers_parse_for_every_body_shape(label, body):
    """PURE composition (no git invoked to build it), verified BY git's parser."""

    composed = H.compose_message_with_trailers(body, TRAILERS)
    parsed = _parse_trailers(composed)
    assert f"AW-Run: {RUN_ID}" in parsed, f"{label}: AW-Run did not parse: {composed!r}"
    assert (
        f"AW-Item: {ITEM_ID}" in parsed
    ), f"{label}: AW-Item did not parse: {composed!r}"
    # Never two blank-line-separated trailer blocks: both keys must live in ONE paragraph.
    blocks = [
        b for b in composed.strip().split("\n\n") if "AW-Run:" in b or "AW-Item:" in b
    ]
    assert len(blocks) == 1, f"{label}: trailers split across blocks: {composed!r}"


def test_compose_preserves_preexisting_trailers_joining_the_block():
    """F5's SILENT failure: a naive blank-line append makes the EARLIER trailers stop parsing.

    A string comparison cannot catch this; only git's parser can.
    """

    body = "chore(test): subject\n\nbody\n\nCo-authored-by: x <x@e.com>"
    naive = body + "\n\n" + "\n".join(TRAILERS) + "\n"
    assert (
        "Co-authored-by: x <x@e.com>" not in _parse_trailers(naive)
    ), "expected the naive append to LOSE the earlier trailer (the hazard being guarded against)"
    ours = H.compose_message_with_trailers(body, TRAILERS)
    parsed = _parse_trailers(ours)
    assert "Co-authored-by: x <x@e.com>" in parsed, f"earlier trailer lost: {ours!r}"
    assert f"AW-Run: {RUN_ID}" in parsed
    assert f"AW-Item: {ITEM_ID}" in parsed


@pytest.mark.parametrize(
    "label,body",
    [
        # A last paragraph that MIXES prose with a non-git-generated trailer is NOT a trailer block
        # to git (rule (ii) needs a git-generated trailer). Joining it would put our trailers into a
        # paragraph git refuses to parse, yielding a commit with NO trailers at all.
        ("mixed-no-gitgen", "chore(test): subject\n\nprose line\nKey: value"),
        # Ratio arm: a git-generated trailer present but under 25% trailers -> also not a block.
        (
            "gitgen-under-25pct",
            "chore(test): subject\n\np1\np2\np3\np4\nSigned-off-by: z <z@e.com>",
        ),
        # A lone FIRST paragraph is never a trailer block (git requires a preceding blank line).
        ("single-para-looks-like-trailers", "Key: value\nOther: thing"),
    ],
)
def test_compose_starts_a_new_block_when_git_would_not_see_one(label, body):
    """Joining is only correct when git ACTUALLY parses the last paragraph as trailers.

    These are the shapes where a too-eager "looks like Key: value" heuristic would join a
    paragraph git does not recognize, silently producing a commit with no parseable trailers.
    """

    composed = H.compose_message_with_trailers(body, TRAILERS)
    parsed = _parse_trailers(composed)
    assert f"AW-Run: {RUN_ID}" in parsed, f"{label}: AW-Run did not parse: {composed!r}"
    assert (
        f"AW-Item: {ITEM_ID}" in parsed
    ), f"{label}: AW-Item did not parse: {composed!r}"
    # The original body text must be preserved verbatim ahead of the trailers.
    assert composed.startswith(
        body.rstrip("\n")
    ), f"{label}: body altered: {composed!r}"


def test_is_trailer_block_matches_git_on_the_25_percent_rule():
    """Our block predicate must agree with git's own parser, not merely look plausible.

    Cross-checks the predicate against ``git interpret-trailers --parse`` for the boundary shapes
    of the documented rule: "all trailers, or contains at least one Git-generated ... trailer and
    consists of at least 25% trailers".
    """

    cases = [
        (["Key: v"], True),  # (i) all trailers
        (["A: 1", "B: 2"], True),
        (["Signed-off-by: z", "  folded continuation"], True),
        (["prose", "Key: v"], False),  # mixed, no git-generated -> not a block
        (["p1", "p2", "p3", "Signed-off-by: z"], True),  # 1/4 = 25% w/ gitgen
        (["p1", "p2", "p3", "p4", "Signed-off-by: z"], False),  # 1/5 = 20% -> no
        (["prose only"], False),
        ([], False),
    ]
    for lines, expected in cases:
        assert H._is_trailer_block(lines) is expected, f"predicate wrong for {lines!r}"
        # And confirm git agrees, by putting the paragraph AFTER a subject (blank-line separated).
        if lines:
            msg = "subject\n\n" + "\n".join(lines) + "\n"
            git_sees_block = bool(_parse_trailers(msg))
            assert (
                git_sees_block is expected
            ), f"git disagrees with the predicate for {lines!r}: git_sees={git_sees_block}"


def test_compose_is_pure_and_needs_no_git(monkeypatch):
    """Composition must not invoke git at all (it is a pure function over strings)."""

    def _boom(*_a, **_k):
        raise AssertionError("composition must not run a subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(H, "_git", _boom)
    out = H.compose_message_with_trailers("chore(test): subject\n\nbody", TRAILERS)
    assert out.endswith(f"AW-Run: {RUN_ID}\nAW-Item: {ITEM_ID}\n")


def test_compose_with_no_trailers_is_byte_identical():
    """The existing-caller guarantee: no trailers -> the message is returned untouched."""

    for body in (
        "chore(test): subject only",
        "chore(test): subject\n\nmultiline\nbody",
        "chore(test): subject\n\nCo-authored-by: x <x@e.com>",
        "chore(test): subject\n\nno trailing newline",
        "",
    ):
        assert H.compose_message_with_trailers(body, []) == body
        assert H.compose_message_with_trailers(body, ()) == body


def test_trailers_land_on_a_real_commit(repo: Path, rec):
    """End-to-end through offer_commit: git reports the trailers on the actual commit."""

    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): trailered\n\nsome body prose",
        assume_yes=True,
        trailers=TRAILERS,
    )
    assert out.status == H.STATUS_COMMITTED
    assert out.commit
    reported = _commit_trailers(repo, out.commit)
    assert f"AW-Run: {RUN_ID}" in reported, f"git did not report AW-Run: {reported}"
    assert f"AW-Item: {ITEM_ID}" in reported, f"git did not report AW-Item: {reported}"
    # The surrounding contract still holds WITH trailers present.
    assert _committed_files(repo, out.commit) == {"mine.txt"}
    rec.assert_contract_clean()


def test_trailers_do_not_widen_scope_or_stage_extra(repo: Path, rec):
    """With trailers present, path-scoping is unchanged and nothing extra is staged/committed."""

    mine = _write(repo, "mine.txt", "mine\n")
    _write(repo, "other.txt", "not mine\n")  # unrelated, dirty, NOT in paths
    _write(repo, "third.txt", "third\n")
    git(repo, "add", "--", "third.txt")  # unrelated, PRE-STAGED

    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): scoped+trailered",
        assume_yes=True,
        trailers=TRAILERS,
    )
    assert out.status == H.STATUS_COMMITTED
    assert _committed_files(repo, out.commit) == {"mine.txt"}
    assert set(out.staged) == {"mine.txt"}
    assert "?? other.txt" in git(repo, "status", "--porcelain").stdout
    assert "third.txt" in git(repo, "diff", "--name-only", "--cached").stdout
    rec.assert_contract_clean()  # still no -A/-a/push/--no-verify


def test_commit_without_trailers_message_is_unchanged(repo: Path, rec):
    """REGRESSION GUARD for the six-plus existing callers: same message as before, byte for byte."""

    message = "chore(test): plain\n\nbody line\n"
    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(repo, [mine], message=message, assume_yes=True)
    assert out.status == H.STATUS_COMMITTED
    assert _raw_commit_message(repo, out.commit) == message
    assert _commit_trailers(repo, out.commit) == []
    rec.assert_contract_clean()


def test_no_trailers_commit_is_byte_identical_to_pre_change_behavior(repo: Path):
    """The pre-change code path was `git commit -m <message>` verbatim; prove we still match it.

    Committing the SAME tree with the SAME message via raw git and via the helper must yield the
    identical stored message bytes for every body shape a caller in this repo actually uses.
    """

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
        git(
            repo, "commit", "-q", "-m", message, "--", rel2
        )  # the pre-change invocation
        via_raw_git = _raw_commit_message(repo, _head(repo))

        assert (
            via_helper == via_raw_git
        ), f"diverged from raw `git commit -m` for {message!r}"


def test_trailers_join_existing_block_on_a_real_commit(repo: Path, rec):
    """The F5 case end-to-end: git reports BOTH the pre-existing and the new trailers."""

    mine = _write(repo, "mine.txt", "mine\n")
    out = H.offer_commit(
        repo,
        [mine],
        message="chore(test): joined\n\nbody\n\nCo-authored-by: x <x@e.com>",
        assume_yes=True,
        trailers=TRAILERS,
    )
    assert out.status == H.STATUS_COMMITTED
    reported = _commit_trailers(repo, out.commit)
    assert (
        "Co-authored-by: x <x@e.com>" in reported
    ), f"pre-existing trailer lost: {reported}"
    assert f"AW-Run: {RUN_ID}" in reported
    assert f"AW-Item: {ITEM_ID}" in reported
    rec.assert_contract_clean()


@pytest.mark.parametrize(
    "bad",
    [
        "AW-Run: one\nAW-Item: two",  # embedded newline would terminate the block
        "AW-Run: one\rmore",  # carriage return likewise
        "no-separator-at-all",
        ": empty key",
        "AW Run: whitespace in key",
        "AW_Run: underscore is not a git trailer token",
        "AW.Run: dot is not either",
    ],
)
def test_malformed_trailer_is_rejected(bad):
    with pytest.raises(H.TrailerError):
        H.validate_trailer(bad)
    with pytest.raises(H.TrailerError):
        H.compose_message_with_trailers("chore(test): subject", [bad])


def test_malformed_trailer_commits_nothing(repo: Path, rec):
    """A structurally impossible trailer must ERROR with an untouched index and HEAD (OQ-02)."""

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
    assert rec.calls == []  # aborted BEFORE touching git at all
    rec.assert_contract_clean()


def test_shape_validation_accepts_valid_trailers():
    """Shape validation only: an empty value is legal, and git parses it."""

    assert H.validate_trailer("AW-Run: r1") == "AW-Run: r1"
    assert H.validate_trailer(f"AW-Item: {ITEM_ID}") == f"AW-Item: {ITEM_ID}"
    assert H.validate_trailer("Key:") == "Key:"
    # 'Key:v' (no space) is legal for git; we normalize to the conventional single space.
    assert H.validate_trailer("AW-Run:r1") == "AW-Run: r1"
    assert _parse_trailers("subject\n\nKey:\n") == ["Key:"]


def test_run_item_trailers_helper_shapes_the_canonical_keys():
    """The key spelling is single-sourced so callers cannot drift."""

    assert H.run_item_trailers(RUN_ID, ITEM_ID) == TRAILERS
    assert H.run_item_trailers(RUN_ID, None) == [f"AW-Run: {RUN_ID}"]
    assert H.run_item_trailers(None, ITEM_ID) == [f"AW-Item: {ITEM_ID}"]
    assert H.run_item_trailers(None, None) == []
    assert H.run_item_trailers("", "  ") == []
    assert H.TRAILER_KEY_RUN == "AW-Run"
    assert H.TRAILER_KEY_ITEM == "AW-Item"
    # And what it produces must actually parse as trailers.
    composed = H.compose_message_with_trailers(
        "chore(test): subject", H.run_item_trailers(RUN_ID, ITEM_ID)
    )
    assert _parse_trailers(composed) == TRAILERS


def test_trailers_is_keyword_only_and_defaults_empty():
    """Signature contract: `trailers` cannot be passed positionally (no caller's args shift)."""

    import inspect

    sig = inspect.signature(H.offer_commit)
    param = sig.parameters["trailers"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default == ()
    # The two positional parameters are unchanged, so no existing call site shifts.
    positional = [
        n
        for n, p in sig.parameters.items()
        if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    assert positional == ["repo_root", "paths"]


def test_aw_commit_threads_trailers_through(tmp_path: Path, monkeypatch):
    """E-03: `run_commit` passes namespace-supplied trailers into the shared helper."""

    from agent_workflows import work_cmd

    captured = {}
    real = H.offer_commit

    def _spy(repo_root, paths, **kw):
        captured.update(kw)
        return real(repo_root, paths, **kw)

    monkeypatch.setattr(work_cmd._gch, "offer_commit", _spy)

    # Preformatted trailers win as-is.
    ns = argparse.Namespace(trailers=list(TRAILERS))
    assert work_cmd._trailers_from_args(ns) == TRAILERS
    # Raw ids are formatted through the single-sourced keys.
    ns2 = argparse.Namespace(run_id=RUN_ID, item_id6=ITEM_ID)
    assert work_cmd._trailers_from_args(ns2) == TRAILERS
    # Absent both, NOTHING is added -> `aw commit` behaves exactly as before.
    assert work_cmd._trailers_from_args(argparse.Namespace()) == []
    assert captured == {}  # helper not called by the resolver itself


def test_ipd_lifecycle_git_delegates_to_shared_runner():
    """The single-wrapper contract: ipd_lifecycle._git resolves to the same runner as here."""

    from agent_workflows import ipd_lifecycle as LC

    # ipd_lifecycle._git delegates into git_commit_helper._git; a smoke call still works.
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


def test_hook_that_rewrites_our_path_is_retried_once_and_commits(repo: Path, rec):
    """A mutating hook must cost ZERO round trips, and must not do so silently."""

    _install_hook(repo, _HOOK_REWRITES_AND_REJECTS)
    mine = _write(repo, "art.md", "line with trailing space   \n")
    before = _head(repo)

    out = H.offer_commit(repo, [mine], message="chore(test): art", assume_yes=True)

    assert out.status == H.STATUS_COMMITTED, out.message
    assert out.commit and out.commit != before
    # The fix is REPORTED, not absorbed: the committed bytes are the hook's, not ours.
    assert out.hook_fixed == ("art.md",), out
    assert out.hook_fixed_diverged == ()
    assert "art.md" in out.message and "hooks fixed" in out.message
    # The hook's fix is what landed.
    assert (
        git(repo, "show", f"{out.commit}:art.md").stdout == "line with trailing space\n"
    )
    # E-09: and the shared tree agrees with the commit, so the path does not read dirty.
    assert git(repo, "status", "--porcelain").stdout == ""
    assert (repo / "art.md").read_text(encoding="utf-8") == "line with trailing space\n"
    rec.assert_contract_clean()  # across BOTH commit attempts


def test_hook_that_refuses_without_touching_files_is_not_retried(repo: Path, rec):
    """A genuine refusal is unchanged: still an error, no retry, nothing committed.

    This is the property that keeps the retry from being `--no-verify` in disguise, so it asserts the
    ATTEMPT COUNT rather than only the outcome.
    """

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
    rec.assert_contract_clean()


def test_whitespace_only_edit_reports_nothing_to_commit_not_hook_rejected(
    repo: Path, rec
):
    """The COMMONEST shape of the defect: the hook's fix erases our entire diff.

    A naive retry stages an empty index and gets rejected a second time reading `nothing to commit`,
    so the plain retry would NOT fix the case that motivated it. The honest answer is
    `nothing-to-commit`.
    """

    _install_hook(repo, _HOOK_REWRITES_AND_REJECTS)
    # Commit the file CLEAN first (bypassing the hook), then re-add only trailing whitespace.
    _write(repo, "art.md", "already clean\n")
    git(repo, "add", "--", "art.md")
    git(repo, "commit", "-q", "--no-verify", "-m", "seed art")
    before = _head(repo)
    _write(repo, "art.md", "already clean   \n")

    out = H.offer_commit(repo, ["art.md"], message="chore(test): art", assume_yes=True)

    assert out.status == H.STATUS_NOTHING_TO_COMMIT, out.message
    assert out.hook_fixed == ("art.md",), out
    assert _head(repo) == before
    rec.assert_contract_clean()


def test_a_peers_dirty_file_is_absent_from_the_retried_commit(repo: Path, rec):
    """E-04: the retry re-adds ONLY our paths, so a peer's dirty file cannot ride along."""

    _install_hook(repo, _HOOK_REWRITES_AND_REJECTS)
    mine = _write(repo, "art.md", "mine with trailing   \n")
    _write(repo, "peer.md", "peer work in progress   \n")  # a co-worker's, NOT in paths

    out = H.offer_commit(repo, [mine], message="chore(test): art", assume_yes=True)

    assert out.status == H.STATUS_COMMITTED, out.message
    assert out.hook_fixed == ("art.md",)
    assert _committed_files(repo, out.commit) == {"art.md"}
    # The peer's file is untouched AND still dirty (its trailing whitespace is not "fixed" either).
    assert "?? peer.md" in git(repo, "status", "--porcelain").stdout
    assert (repo / "peer.md").read_text(
        encoding="utf-8"
    ) == "peer work in progress   \n"
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


def test_staged_paths_reports_both_sides_of_a_rename(repo: Path):
    """The regression at its root: a staged rename must surface BOTH paths, not just the destination."""

    src = _write(repo, "records/graduated/item-abc123.md", "body\n")
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed the item")
    (repo / "records/done").mkdir(parents=True, exist_ok=True)
    git(repo, "mv", src, "records/done/item-abc123.md")

    staged = H._staged_paths(repo)

    # Proves the defect directly: git's own --name-only view omits the source, so a test that only
    # asserted the destination would have passed against the broken implementation.
    assert "records/graduated/item-abc123.md" in staged, (
        "a staged rename's SOURCE must be reported; omitting it is what committed a move as a bare "
        "addition and duplicated 36 backlog ids"
    )
    assert "records/done/item-abc123.md" in staged


def test_a_git_mv_relocation_commits_as_one_move_with_no_leftover(repo: Path, rec):
    """END TO END, the property the 36 corrupted items violated: no half of a move is left behind."""

    src = _write(repo, "records/graduated/item-abc123.md", "body\n")
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed the item")
    (repo / "records/done").mkdir(parents=True, exist_ok=True)
    dest = "records/done/item-abc123.md"
    git(repo, "mv", src, dest)

    out = H.offer_commit(
        repo, [src, dest], message="close abc123", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_COMMITTED

    # THE COMMIT CARRIES BOTH SIDES. Asserted through git's own rename detection so the assertion
    # cannot pass on a commit that merely happens to mention both names.
    shown = git(
        repo, "show", "--name-status", "--pretty=format:", "-M", out.commit or "HEAD"
    ).stdout
    assert shown.strip().startswith("R"), (
        f"expected a rename record, got: {shown.strip()!r}. An 'A' alone is the measured bug: the "
        "addition committed while the deletion stayed behind."
    )

    # AND NOTHING IS LEFT BEHIND. This is the assertion that actually failed in production: the
    # leftover `D graduated/...` is what made the source file survive in HEAD beside its own
    # destination, which is precisely a duplicate id.
    assert git(repo, "status", "--porcelain").stdout.strip() == ""
    # `git show --name-only` prints only the DESTINATION for a rename (the same view whose
    # single-sidedness caused this bug), so assert membership rather than set equality here; the
    # rename record asserted above is what proves both sides landed.
    assert _committed_files(repo, out.commit) == {dest}
    rec.assert_contract_clean()


def test_the_source_of_a_move_does_not_survive_in_head(repo: Path):
    """State the duplicate-id hazard as its own property, so a future refactor cannot reintroduce it."""

    src = _write(repo, "records/graduated/item-abc123.md", "body\n")
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed the item")
    (repo / "records/done").mkdir(parents=True, exist_ok=True)
    dest = "records/done/item-abc123.md"
    git(repo, "mv", src, dest)
    H.offer_commit(
        repo, [src, dest], message="close abc123", assume_yes=True, interactive=False
    )

    tracked = {
        ln.strip()
        for ln in git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
        if ln.strip()
    }
    assert dest in tracked
    assert src not in tracked, (
        "the item exists at BOTH paths in HEAD, which is the duplicate-id corruption: one artifact "
        "id present in two lifecycle directories at once"
    )


def test_naming_only_the_destination_still_works(repo: Path):
    """A caller that names ONE side must be unaffected: the fix widens a READ, it changes no contract."""

    src = _write(repo, "records/graduated/item-abc123.md", "body\n")
    git(repo, "add", "--", src)
    git(repo, "commit", "-q", "-m", "seed the item")
    (repo / "records/done").mkdir(parents=True, exist_ok=True)
    dest = "records/done/item-abc123.md"
    git(repo, "mv", src, dest)

    out = H.offer_commit(
        repo, [dest], message="close abc123", assume_yes=True, interactive=False
    )
    # Git commits the whole staged rename when either side is named, which is git's behavior and not
    # this helper's choice; the point of the assertion is that the helper does not ERROR or refuse.
    assert out.status == H.STATUS_COMMITTED


def test_a_plain_deletion_is_still_committed(repo: Path):
    """Guard the neighbouring case the rename-parsing rewrite could plausibly break."""

    victim = _write(repo, "records/open/item-def456.md", "body\n")
    git(repo, "add", "--", victim)
    git(repo, "commit", "-q", "-m", "seed")
    (repo / victim).unlink()

    out = H.offer_commit(
        repo, [victim], message="remove def456", assume_yes=True, interactive=False
    )
    assert out.status == H.STATUS_COMMITTED
    tracked = git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout
    assert victim not in tracked


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
