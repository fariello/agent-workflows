"""Shared "commit-what-I-changed" helper: path-scoped, TTY-gated, no ``add -A``, no push.

This is a low-level LEAF module. Records-mutating verbs (``aw archive``, ``aw group``,
``aw rename``, ``aw research set-assign``/``mv``, the shared ``set`` engine, ``specs``) and,
later, the agentadhere ``aw commit`` primitive all reuse :func:`offer_commit` so there is a
SINGLE reusable commit path enforcing the repository contract (AGENTS.md):

* stage ONLY the explicit files the caller touched (``git add -- <paths>``); never ``-A``/``-a``;
* commit with the caller's message; never ``--no-verify``; never ``push``;
* INTERACTIVE-GATED - on a TTY prompt ``[Y/n]`` unless ``assume_yes`` (the ``--commit`` flag);
  NON-interactive without ``assume_yes`` is a NO-OP (skip), matching ``cli._confirm``'s ACTUAL
  decline-on-non-TTY behavior (cli.py:2696) - NOT auto-yes; ``no_commit`` short-circuits to skip;
* NEVER folds in unrelated staged/unstaged changes. ``on_unrelated_staged`` selects the policy
  when the index already holds staged paths OUTSIDE ``paths``: ``"scope"`` (default; commit only
  ``paths``, leave the rest untouched) or ``"refuse"`` (return ``refused-dirty``, commit nothing);
* OPTIONALLY appends Git TRAILERS to the message (``trailers=``, default EMPTY so every existing
  caller is byte-for-byte unaffected). This lets a caller record WHICH run and work item produced
  a commit (``AW-Run: <run-id>``, ``AW-Item: <id6>``) so a deterministic checker can identify
  run-owned commits instead of assuming every commit between a baseline and HEAD belongs to the
  run - which is wrong in a SHARED checkout. The trailers are additive to the MESSAGE only: they
  change no staging, scoping, or rollback behavior. See :func:`compose_message_with_trailers`.

  HONEST LIMIT: a trailer is a CLAIM in a commit message, not an enforced boundary. An agent
  committing by hand can omit or forge one. Identifying run-owned commits is not the same as
  guaranteeing them; the enforcement half (a commit gateway) is deliberately NOT implemented here.

IMPORTANT (import direction): this leaf MUST NOT import ``cli`` (that would invert the
dependency and risk a cycle); the tiny yes/no prompt is reimplemented here instead. The
canonical git subprocess runner lives here as :func:`_git`; ``ipd_lifecycle._git`` delegates to
it so there is a single git-subprocess wrapper across the codebase.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

# --------------------------------------------------------------------------------------
# Git trailer conventions (see compose_message_with_trailers)
# --------------------------------------------------------------------------------------

# Canonical trailer KEYS this repository uses to mark a commit as run-owned. Spec 25kzda 4.6:
# the deterministic checker "finds run-owned commits by required immutable trailers such as
# `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs".
TRAILER_KEY_RUN = "AW-Run"
TRAILER_KEY_ITEM = "AW-Item"

# A trailer token, per `git-interpret-trailers`: "there can be no whitespace before or inside the
# <key>, but any number of regular space and tab characters are allowed between the <key> and the
# separator". VERIFIED against git 2.43.0 by probing `git interpret-trailers --parse`: `AW-Run`
# and `A1-b2` parse; `AW_Run`, `AW.Run`, `AW+Run`, `AW/Run`, `AW*Run` and non-ASCII keys do NOT.
# So the accepted token charset is alphanumerics and hyphen only - deliberately NARROWER than a
# permissive guess, because a key git will not parse yields a SILENTLY trailer-less commit.
_TRAILER_TOKEN_RE = re.compile(r"^[A-Za-z0-9-]+$")

# A line that git counts as a trailer when deciding whether a paragraph IS a trailer block.
_TRAILER_LINE_RE = re.compile(r"^([A-Za-z0-9-]+)[ \t]*:")

# A continuation of the preceding trailer's value ("may be split over multiple lines with each
# subsequent line starting with at least one whitespace").
_TRAILER_CONT_RE = re.compile(r"^[ \t]+\S")

# git also ignores comment lines when parsing a trailer block.
_TRAILER_COMMENT_RE = re.compile(r"^#")

# git-generated trailers, which let an OTHERWISE-mixed paragraph still count as a trailer block
# (rule (ii) below). `Signed-off-by:` and the cherry-pick line are the git-generated ones.
_GIT_GENERATED_RE = re.compile(r"^(Signed-off-by[ \t]*:|\(cherry picked from )")

# A `---` divider ends the trailer-searchable region: the trailer group "must either be at the end
# of the input or be the last non-whitespace lines before a line that starts with `---` (followed
# by a space or the end of the line)". VERIFIED: `---` and `--- ` divide; `----` and `---foo` do not.
_DIVIDER_RE = re.compile(r"^---(\s|$)")


class TrailerError(ValueError):
    """A trailer whose SHAPE git could not parse (bad token, embedded newline, no separator).

    Raised at COMPOSITION time rather than producing a commit whose trailers silently fail to
    parse. Per the plan's OQ-02: validate the SHAPE here, and leave REFERENTIAL validity (does
    this id6 resolve to a real artifact?) to the ``aw check`` surface, where every other
    id6-resolution rule in this repo already lives. Do not fork that resolution into a commit helper.
    """


def _is_trailer_block(lines: Sequence[str]) -> bool:
    """Would git parse this paragraph as a trailer block?

    Implements the rule from ``git-interpret-trailers``: a group of one or more lines that
    "(i) is all trailers, or (ii) contains at least one Git-generated or user-configured trailer
    and consists of at least 25% trailers".

    Only case (i) and the git-generated arm of (ii) are modeled. A USER-CONFIGURED trailer
    (``trailer.<token>.key`` in git config) would also satisfy (ii), and this function cannot see
    git config, so it may answer False where git would answer True. That direction is SAFE: we
    then start a new blank-line-separated block, which parses correctly on its own (the earlier
    lines simply keep whatever status they already had). Answering True where git answers False
    is the dangerous direction, and that cannot happen here.
    """

    trailer_count = 0
    other_count = 0
    saw_git_generated = False
    seen_trailer = False
    for line in lines:
        if _TRAILER_COMMENT_RE.match(line):
            continue  # git ignores comments when parsing a block
        if seen_trailer and _TRAILER_CONT_RE.match(line):
            continue  # folded continuation of the previous trailer's value
        if _TRAILER_LINE_RE.match(line):
            trailer_count += 1
            seen_trailer = True
            if _GIT_GENERATED_RE.match(line):
                saw_git_generated = True
        else:
            other_count += 1
            seen_trailer = False
    if trailer_count == 0:
        return False
    if other_count == 0:
        return True  # (i) all trailers
    # (ii) at least one git-generated trailer AND >= 25% trailers, i.e. other <= 3 * trailers.
    return saw_git_generated and other_count <= 3 * trailer_count


def validate_trailer(trailer: str) -> str:
    """Return ``trailer`` unchanged if git can parse it as ``Key: value``, else raise.

    Rejects an embedded newline (which would break OUT of the trailer block and silently drop
    everything after it), a missing ``:`` separator, an empty key, and a key containing any
    character outside git's token charset. An EMPTY VALUE is allowed: git parses ``Key:`` fine.
    """

    if not isinstance(trailer, str):
        raise TrailerError(f"trailer must be a string, got {type(trailer).__name__}")
    if "\n" in trailer or "\r" in trailer:
        raise TrailerError(
            f"trailer must not contain a newline (it would terminate the trailer block): {trailer!r}"
        )
    if ":" not in trailer:
        raise TrailerError(
            f"trailer must be 'Key: value' (no ':' separator found): {trailer!r}"
        )
    key, _, value = trailer.partition(":")
    key = key.rstrip(" \t")  # git allows space/tab between the key and the separator
    if not key:
        raise TrailerError(f"trailer key must not be empty: {trailer!r}")
    if not _TRAILER_TOKEN_RE.match(key):
        raise TrailerError(
            "trailer key must contain only letters, digits, and '-' (git will not parse "
            f"anything else as a trailer): {trailer!r}"
        )
    if value.strip() and value[:1] not in (" ", "\t"):
        # Not an error for git (`Key:v` parses), but normalize on the conventional single space.
        return f"{key}: {value.strip()}"
    return trailer


def compose_message_with_trailers(message: str, trailers: Sequence[str]) -> str:
    """PURE composition: return ``message`` with ``trailers`` appended as a Git trailer block.

    No git invocation, no I/O - so every body shape is testable directly. With an empty
    ``trailers`` the message is returned COMPLETELY UNCHANGED (byte-for-byte), which is what keeps
    this leaf module's six-plus existing callers unaffected.

    Handles the body shapes that break naive concatenation:

    * a MULTILINE body - the block goes after the whole body, not after the subject;
    * a body that ALREADY ends in a trailer block - the new trailers JOIN that block instead of
      starting a second one. This is the subtle case: a blank line INSIDE a trailer block
      TERMINATES it, so a naive ``message + "\\n\\n" + trailers`` makes git stop recognizing the
      EARLIER trailers. VERIFIED with git 2.43.0: appending ``AW-Run: r1`` after a blank line to a
      body ending ``Co-authored-by: x`` makes ``--parse`` report ONLY ``AW-Run``, silently losing
      the co-author. Joining the block reports both. The commit SUCCEEDS either way, so this
      failure is invisible without asking git to parse.
    * a body with NO trailing newline - normalized before the separator is added;
    * a body containing a ``---`` divider - the trailers are inserted BEFORE the divider, since
      git only recognizes a trailer group at the end of the input or immediately before such a
      divider. This matches what ``git interpret-trailers`` itself does with the same input.
    * a SINGLE-PARAGRAPH message whose only paragraph looks like trailers - a new block is started
      rather than joined, because git requires a trailer group to be "preceded by one or more empty
      lines" and so does not treat a lone first paragraph as trailers at all. Joining there would
      produce a message with NO parseable trailers. (910 of the last 2211 commit messages in this
      repository are single-paragraph, so this shape is the common case, not an edge case.)

    Raises :class:`TrailerError` on a structurally unparseable trailer (see :func:`validate_trailer`).
    """

    cleaned = [validate_trailer(t) for t in trailers]
    if not cleaned:
        return message  # byte-for-byte identical: the existing-caller guarantee

    trailer_text = "\n".join(cleaned)
    if not message.strip():
        # No body to attach to; the trailers ARE the message. git does not parse a lone first
        # paragraph as trailers, but there is no body to preserve, so this is the honest result.
        return trailer_text + "\n"

    body = message.rstrip(
        "\n"
    )  # handles "no trailing newline" and over-long runs alike

    # --- A `---` divider ends the trailer-searchable region: insert BEFORE it. ---
    lines = body.split("\n")
    divider_idx = next((i for i, ln in enumerate(lines) if _DIVIDER_RE.match(ln)), None)
    if divider_idx is not None:
        head = "\n".join(lines[:divider_idx]).rstrip("\n")
        tail = "\n".join(lines[divider_idx:])
        return f"{compose_message_with_trailers(head, cleaned)}\n{tail}\n"

    # --- Does the LAST paragraph already parse as a trailer block? If so, JOIN it. ---
    paragraphs = re.split(r"\n[ \t]*\n", body)
    if len(paragraphs) > 1:
        last_lines = [ln for ln in paragraphs[-1].split("\n") if ln.strip()]
        if _is_trailer_block(last_lines):
            # Join: NO blank line, or the earlier trailers stop parsing as trailers.
            return f"{body}\n{trailer_text}\n"

    # --- Otherwise start a NEW block, separated from the body by exactly one blank line. ---
    return f"{body}\n\n{trailer_text}\n"


def run_item_trailers(run_id: Optional[str], item_id6: Optional[str]) -> List[str]:
    """Build the canonical ``AW-Run``/``AW-Item`` trailer list, skipping any absent value.

    A convenience so callers do not hand-format the keys (and drift). Returns ``[]`` when both are
    absent, which composes to an unchanged message.
    """

    out: List[str] = []
    if run_id and str(run_id).strip():
        out.append(f"{TRAILER_KEY_RUN}: {str(run_id).strip()}")
    if item_id6 and str(item_id6).strip():
        out.append(f"{TRAILER_KEY_ITEM}: {str(item_id6).strip()}")
    return out


# Outcome status literals (kept as plain strings so callers/tests can compare directly).
STATUS_COMMITTED = "committed"
STATUS_SKIPPED = "skipped"
STATUS_DECLINED = "declined"
STATUS_REFUSED_DIRTY = "refused-dirty"
STATUS_NOTHING_TO_COMMIT = "nothing-to-commit"
STATUS_ERROR = "error"


class CommitOutcome(NamedTuple):
    """Structured result of an :func:`offer_commit` attempt.

    ``status`` is one of the ``STATUS_*`` literals. ``commit`` is the new HEAD sha on
    ``committed``, else ``None``. ``staged`` is the exact repo-relative path set that was
    staged/committed (subset of the requested ``paths`` that actually existed/were tracked).
    ``message`` is a human-readable explanation (used for warnings/errors).
    """

    status: str
    commit: Optional[str]
    staged: Tuple[str, ...]
    message: str


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr).

    The single canonical git-subprocess wrapper for the codebase; ``ipd_lifecycle._git``
    delegates here so there is no duplicated runner.
    """

    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_interactive(interactive: Optional[bool]) -> bool:
    """Resolve the effective interactivity.

    ``interactive`` explicitly overrides (used by tests and callers that already know the
    channel); ``None`` falls back to ``sys.stdin.isatty()`` - the same signal ``cli._confirm``
    keys off (cli.py:2701).
    """

    if interactive is not None:
        return interactive
    try:
        return bool(sys.stdin.isatty())
    except (ValueError, AttributeError):  # detached/!closed stdin
        return False


def _prompt(message: str, paths: Sequence[str]) -> bool:
    """Tiny ``[Y/n]`` yes/no render, equivalent to ``cli._confirm``'s interactive branch.

    Reimplemented locally (NOT imported from ``cli``) to keep this a leaf module. Only ever
    called when already known-interactive; an empty answer defaults to YES, while an EOF or
    explicit 'n'/'no' is a safe NO.
    """

    shown = ", ".join(paths)
    prompt = f"{message}\n  {shown}\nCommit these path-scoped changes? [Y/n] "
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return False
    return answer in ("", "y", "yes")


def _staged_paths(repo_root: Path) -> List[str]:
    """Repo-relative paths currently in the index (staged), rename-aware."""

    rc, out, _err = _git(repo_root, ["diff", "--name-only", "--cached"])
    if rc != 0:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _normalize(paths: Sequence[str], repo_root: Path) -> List[str]:
    """Coerce the caller's paths to repo-relative POSIX strings, de-duplicated, order-stable."""

    seen: dict = {}
    root = repo_root.resolve()
    for p in paths:
        pp = Path(p)
        if pp.is_absolute():
            try:
                rel = pp.resolve().relative_to(root).as_posix()
            except ValueError:
                rel = pp.as_posix()
        else:
            rel = pp.as_posix()
        rel = rel.strip()
        if rel:
            seen.setdefault(rel, None)
    return list(seen.keys())


def offer_commit(
    repo_root: Path,
    paths: Sequence[str],
    *,
    message: str,
    assume_yes: bool = False,
    no_commit: bool = False,
    interactive: Optional[bool] = None,
    on_unrelated_staged: str = "scope",
    trailers: Sequence[str] = (),
) -> CommitOutcome:
    """Offer to commit ONLY ``paths`` (path-scoped), enforcing the repo contract.

    Parameters
    ----------
    repo_root:
        Repository root the git commands run in.
    paths:
        The exact files the caller touched (repo-relative or absolute), including deletions,
        renames, and any regenerated index. ONLY these are ever staged (``git add -- <paths>``).
    message:
        Commit message. Never combined with ``--no-verify``; the commit is path-scoped
        (``git commit -- <paths>``) and is never pushed.
    assume_yes:
        The ``--commit`` flag. When true, commit without prompting (the only way to commit
        non-interactively).
    no_commit:
        The ``--no-commit`` escape hatch. Short-circuits to ``skipped`` regardless of TTY.
    interactive:
        Explicit interactivity override; ``None`` -> ``sys.stdin.isatty()``.
    on_unrelated_staged:
        Policy when the index already holds staged paths OUTSIDE ``paths``:
        ``"scope"`` (default) commits only ``paths`` and leaves the rest staged-but-uncommitted;
        ``"refuse"`` returns ``refused-dirty`` and commits nothing. In BOTH modes a path outside
        ``paths`` is NEVER staged by this helper.
    trailers:
        Optional Git trailers (``"Key: value"`` strings) appended to ``message`` as a trailer
        block, e.g. ``["AW-Run: run-...", "AW-Item: m73aet"]`` so a checker can tell which run and
        work item produced the commit. DEFAULTS EMPTY, in which case the message is used
        byte-for-byte unchanged. Affects the MESSAGE only - never the staging, scoping, or rollback
        behavior. A structurally unparseable trailer returns an ``error`` outcome and commits
        NOTHING, rather than creating a commit whose trailers silently do not parse. See
        :func:`compose_message_with_trailers`.

    Returns
    -------
    CommitOutcome
        ``committed`` (with the new sha), ``skipped`` (gate declined it non-interactively or
        ``no_commit``), ``declined`` (interactive user said no), ``refused-dirty``
        (``on_unrelated_staged="refuse"`` and the index held unrelated staged paths),
        ``nothing-to-commit`` (no requested path exists/changed), or ``error``.
    """

    if on_unrelated_staged not in ("scope", "refuse"):
        raise ValueError(
            f"on_unrelated_staged must be 'scope' or 'refuse', got {on_unrelated_staged!r}"
        )

    # Compose the message BEFORE touching the index: a malformed trailer must abort with nothing
    # staged, not leave a half-prepared index behind. With no trailers this returns `message` itself.
    try:
        full_message = compose_message_with_trailers(message, trailers)
    except TrailerError as exc:
        return CommitOutcome(STATUS_ERROR, None, (), f"invalid trailer: {exc}")

    rel_paths = _normalize(paths, repo_root)
    if not rel_paths:
        return CommitOutcome(
            STATUS_NOTHING_TO_COMMIT, None, (), "no paths given to commit"
        )

    if no_commit:
        return CommitOutcome(STATUS_SKIPPED, None, (), "skipped: --no-commit requested")

    # --- Unrelated pre-staged content: decide BEFORE we stage anything. ---
    pre_staged = set(_staged_paths(repo_root))
    unrelated_staged = sorted(pre_staged - set(rel_paths))
    if unrelated_staged and on_unrelated_staged == "refuse":
        return CommitOutcome(
            STATUS_REFUSED_DIRTY,
            None,
            (),
            "refusing to commit: unrelated staged changes present: "
            + ", ".join(unrelated_staged),
        )

    # --- TTY gate (matches cli._confirm's ACTUAL behavior: decline on non-TTY w/o assume_yes). ---
    if assume_yes:
        proceed = True
    elif _is_interactive(interactive):
        proceed = _prompt(
            "The following path-scoped changes are ready to commit:", rel_paths
        )
        if not proceed:
            return CommitOutcome(
                STATUS_DECLINED, None, (), "declined: user answered no at prompt"
            )
    else:
        # Non-interactive without --commit/assume_yes: NO-OP (never commit silently).
        return CommitOutcome(
            STATUS_SKIPPED,
            None,
            (),
            "skipped: non-interactive; pass --commit to commit these changes",
        )

    # --- Stage ONLY the requested paths (never -A/-a). ---
    # git add -- <path> on a deleted path stages the deletion; a nonexistent, never-tracked
    # path would error, so we let git report it and surface as an error outcome.
    rc, _out, err = _git(repo_root, ["add", "--", *rel_paths])
    if rc != 0:
        # Roll back any partial staging of OUR paths so we leave the index as we found it.
        _git(repo_root, ["reset", "--quiet", "HEAD", "--", *rel_paths])
        return CommitOutcome(STATUS_ERROR, None, (), f"git add failed: {err.strip()}")

    # Which of our requested paths actually ended up staged (existed / had a diff)?
    now_staged = set(_staged_paths(repo_root))
    our_staged = sorted(now_staged & set(rel_paths))
    if not our_staged:
        # Nothing of ours changed (already committed / identical); do not create an empty commit.
        return CommitOutcome(
            STATUS_NOTHING_TO_COMMIT,
            None,
            (),
            "nothing to commit: requested paths have no staged changes",
        )

    # --- Path-scoped commit (never --no-verify, never push). ---
    rc, out, err = _git(repo_root, ["commit", "-m", full_message, "--", *our_staged])
    if rc != 0:
        _git(repo_root, ["reset", "--quiet", "HEAD", "--", *our_staged])
        msg = err.strip() or out.strip() or "git commit exited non-zero"
        return CommitOutcome(
            STATUS_ERROR, None, tuple(our_staged), f"git commit failed: {msg}"
        )

    rc, head, _err = _git(repo_root, ["rev-parse", "HEAD"])
    sha = head.strip() if rc == 0 else None
    return CommitOutcome(
        STATUS_COMMITTED,
        sha,
        tuple(our_staged),
        f"committed {len(our_staged)} path(s) as {sha}",
    )
