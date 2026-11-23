"""Local pre-push fast-forward gate: fail in <1s when the remote moved ahead.

WHY THIS EXISTS:
Git's `pre-push` hook runs BEFORE git sends the ref update, and `pre-commit` silently falls back
to stale local remote-tracking refs when the remote's live SHA is not yet in the local object DB.
Without this check, `git push` spends ~15 minutes running the thorough test suite, mypy, and
attention checks only to be rejected at the very end with `! [rejected] main -> main (fetch first)`.

This hook queries the live remote tip via read-only `git ls-remote` (touching zero local refs)
and checks `git merge-base --is-ancestor <remote_sha> <local_sha>` before any slow pre-push hook
runs. Set `AW_ALLOW_NON_FF_PUSH=1` to bypass for an intentional force push.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Mapping, Optional, Tuple

ALLOW_NON_FF_ENV = "AW_ALLOW_NON_FF_PUSH"
_ZERO_SHA = "0" * 40


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _resolve_upstream(repo_root: Path) -> Optional[Tuple[str, str]]:
    rc, out, _err = _git(
        repo_root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]
    )
    if rc != 0:
        return None
    upstream = out.strip()
    if "/" not in upstream:
        return None
    remote, branch = upstream.split("/", 1)
    if not remote or not branch:
        return None
    return remote, f"refs/heads/{branch}"


def _extract_remote_sha(ls_remote_output: str, remote_branch: str) -> Optional[str]:
    candidates = {remote_branch}
    if not remote_branch.startswith("refs/"):
        candidates.add(f"refs/heads/{remote_branch}")
    for line in ls_remote_output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        sha, ref = parts[0], parts[1]
        if ref in candidates:
            return sha
    return None


def check(
    repo_root: Optional[Path] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[int, List[str]]:
    """Verify the target remote ref is an ancestor of the local commit being pushed.

    Returns (exit_code, messages). Exit 0 means fast-forward (or new branch / delete / opt-out);
    exit 1 means the push would be rejected (remote moved ahead, diverged, or unreachable).
    """
    root = Path(repo_root) if repo_root is not None else Path(".")
    environ = os.environ if env is None else env

    if environ.get(ALLOW_NON_FF_ENV, "").strip().lower() not in (
        "",
        "0",
        "false",
        "no",
    ):
        return 0, []

    local_ref = (
        environ.get("PRE_COMMIT_TO_REF")
        or environ.get("PRE_COMMIT_LOCAL_BRANCH")
        or "HEAD"
    ).strip()
    if local_ref == _ZERO_SHA:
        return 0, []

    remote = (
        environ.get("PRE_COMMIT_REMOTE_NAME")
        or environ.get("PRE_COMMIT_REMOTE_URL")
        or ""
    ).strip()
    remote_branch = (environ.get("PRE_COMMIT_REMOTE_BRANCH") or "").strip()

    if not remote or not remote_branch:
        resolved = _resolve_upstream(root)
        if resolved is None:
            return 0, []
        if not remote:
            remote = resolved[0]
        if not remote_branch:
            remote_branch = resolved[1]

    rc_local, out_local, err_local = _git(
        root, ["rev-parse", "--verify", f"{local_ref}^{{commit}}"]
    )
    if rc_local != 0:
        detail = (err_local or out_local).strip()
        return 1, [
            f"cannot resolve local ref {local_ref!r} ({detail}); aborting before slow pre-push checks."
        ]
    local_sha = out_local.strip()

    rc_ls, out_ls, err_ls = _git(root, ["ls-remote", "--", remote, remote_branch])
    if rc_ls != 0:
        detail = (err_ls or out_ls).strip()
        return 1, [
            f"cannot reach remote {remote!r} to verify fast-forward ({detail}); "
            "aborting before slow pre-push checks."
        ]

    remote_sha = _extract_remote_sha(out_ls, remote_branch)
    if remote_sha is None:
        # New branch on remote: trivially fast-forward.
        return 0, []

    if remote_sha == local_sha:
        return 0, []

    rc_anc, _out_anc, _err_anc = _git(
        root, ["merge-base", "--is-ancestor", remote_sha, local_sha]
    )
    if rc_anc == 0:
        return 0, []

    rc_has, _out_has, _err_has = _git(
        root, ["cat-file", "-e", f"{remote_sha}^{{commit}}"]
    )
    remote_short = remote_sha[:12]
    local_short = local_sha[:12]
    if rc_has != 0:
        return 1, [
            f"remote {remote} {remote_branch} is at {remote_short}, which is not in local history "
            f"(fetch first); aborting before slow pre-push checks. Run 'git fetch {remote}' and "
            "integrate (for example 'git pull --rebase' or 'git merge') before pushing."
        ]
    return 1, [
        f"local {local_ref} ({local_short}) is not a fast-forward of {remote} {remote_branch} "
        f"({remote_short}); aborting before slow pre-push checks. Rebase or merge before pushing, "
        f"or set {ALLOW_NON_FF_ENV}=1 for an intentional force push."
    ]


def main(argv: Optional[List[str]] = None) -> int:
    _ = argv
    rc, messages = check()
    for msg in messages:
        sys.stderr.write(f"prepush-fast-forward-gate: {msg}\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
