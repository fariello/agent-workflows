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
  ``paths``, leave the rest untouched) or ``"refuse"`` (return ``refused-dirty``, commit nothing).

IMPORTANT (import direction): this leaf MUST NOT import ``cli`` (that would invert the
dependency and risk a cycle); the tiny yes/no prompt is reimplemented here instead. The
canonical git subprocess runner lives here as :func:`_git`; ``ipd_lifecycle._git`` delegates to
it so there is a single git-subprocess wrapper across the codebase.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

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
    rc, out, err = _git(repo_root, ["commit", "-m", message, "--", *our_staged])
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
