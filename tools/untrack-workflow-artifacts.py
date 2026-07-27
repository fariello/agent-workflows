#!/usr/bin/env python3
"""Safely stop tracking a repository's workflow-artifacts/ directory.

The default is a dry run.  --apply removes tracked entries only from Git's
index, retains the working-tree directory, writes an ignore rule, and stages
the two intentional changes.  --commit is deliberately separate and rejects
unrelated staged changes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ARTIFACTS = "workflow-artifacts"
IGNORE_COMMENT = (
    "# agent-workflows working material (local-only; may contain sensitive local context, "
    "home paths, or session detail; do not commit)"
)

IGNORE_RULE = f"{ARTIFACTS}/"


class MigrationError(RuntimeError):
    """A safe migration cannot proceed."""


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_output(root: Path, *args: str) -> str:
    result = git(root, *args)
    return result.stdout


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise MigrationError("Run this command from inside a Git working tree.")
    return Path(result.stdout.strip())


def tracked_paths(root: Path) -> list[str]:
    raw = git_output(root, "ls-files", "-z", "--", ARTIFACTS)
    return [entry for entry in raw.split("\0") if entry]


def ignore_is_present(contents: str) -> bool:
    return any(line.strip() == IGNORE_RULE for line in contents.splitlines())


def append_ignore_rule(gitignore: Path) -> None:
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ignore_is_present(existing):
        return
    separator = "" if not existing or existing.endswith("\n") else "\n"
    gitignore.write_text(
        f"{existing}{separator}{IGNORE_COMMENT}\n{IGNORE_RULE}\n", encoding="utf-8"
    )


def gitignore_is_clean(root: Path) -> bool:
    # Staging it would otherwise also stage a user's unrelated edit.
    return (
        git(root, "diff", "--quiet", "--", ".gitignore", check=False).returncode == 0
        and git(
            root, "diff", "--cached", "--quiet", "--", ".gitignore", check=False
        ).returncode
        == 0
    )


def staged_paths(root: Path) -> list[str]:
    return [
        line
        for line in git_output(root, "diff", "--cached", "--name-only").splitlines()
        if line
    ]


def acceptable_commit_paths(paths: list[str]) -> bool:
    return bool(paths) and all(
        path == ".gitignore" or path == ARTIFACTS or path.startswith(f"{ARTIFACTS}/")
        for path in paths
    )


def run(args: argparse.Namespace) -> int:
    root = repository_root()
    gitignore = root / ".gitignore"
    tracked = tracked_paths(root)
    present = (root / ARTIFACTS).exists()
    ignored = ignore_is_present(
        gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    )

    print(f"Repository: {root}")
    print(f"Local {ARTIFACTS}/ exists: {'yes' if present else 'no'}")
    print(f"Tracked paths: {len(tracked)}")
    print(f"Ignore rule present: {'yes' if ignored else 'no'}")

    if not args.apply:
        print(
            "Dry run only. Re-run with --apply to make the index and .gitignore changes."
        )
        return 0

    if not ignored and not gitignore_is_clean(root):
        raise MigrationError(
            "Refusing to stage .gitignore because it has existing staged or unstaged edits. "
            "Resolve or commit those edits first, then re-run."
        )

    if tracked:
        # --cached is the critical safeguard: keep every local artifact file intact.
        git(root, "rm", "-r", "--cached", "--ignore-unmatch", "--", ARTIFACTS)
        print(
            f"Removed {len(tracked)} tracked path(s) from the Git index; local files were retained."
        )
    else:
        print(
            "No tracked workflow artifacts found; nothing was removed from the index."
        )

    if not ignored:
        append_ignore_rule(gitignore)
        git(root, "add", "--", ".gitignore")
        print("Added and staged the workflow-artifacts/ ignore rule.")

    if args.commit:
        paths = staged_paths(root)
        if not acceptable_commit_paths(paths):
            raise MigrationError(
                "Refusing to commit because the index contains paths outside this migration: "
                + ", ".join(paths)
            )
        git(root, "commit", "-m", "chore: stop tracking workflow artifacts")
        print("Created migration commit.")
    else:
        print(
            "Changes are staged but not committed. Review them, then commit deliberately."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Perform the index-only migration."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit only migration paths after --apply; rejects unrelated staged changes.",
    )
    args = parser.parse_args()
    if args.commit and not args.apply:
        parser.error("--commit requires --apply")
    try:
        return run(args)
    except MigrationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(error.stderr.strip() or str(error), file=sys.stderr)
        return error.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
