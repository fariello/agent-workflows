#!/usr/bin/env python3
"""Safely migrate and stop tracking a repository's root workflow-artifacts/ directory.

DEPRECATED shim: delegates to engine.migrate_root_workflow_artifacts to relocate
run records from the retired repo-root workflow-artifacts/ into .aw/workflow-artifacts/
with git history preserved.

The default is a dry run. --apply executes the migration. --commit is accepted for
backwards compatibility but is a no-op because the migration creates its own
path-scoped commits.

Prefer 'aw install' (or 'agent-workflows install'), which performs this migration
alongside standard repository setup.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Make the sibling agent_workflows package importable when run directly from a checkout.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent_workflows import engine  # noqa: E402


class MigrationError(RuntimeError):
    """A safe migration cannot proceed."""


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


def run(args: argparse.Namespace) -> int:
    print(
        "note: tools/untrack-workflow-artifacts.py is deprecated; 'aw install' performs "
        "this migration alongside standard repository setup. Delegating to engine.",
        file=sys.stderr,
    )

    root = repository_root()
    use_git = engine.git_available(root)
    actions = engine.migrate_root_workflow_artifacts(
        root, use_git=use_git, dry_run=not args.apply
    )

    for action in actions:
        print(action)

    if args.commit:
        print(
            "note: --commit is a no-op; the migration now commits its own path-scoped relocation."
        )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Perform the run-scratch migration."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Accepted for compatibility; migration commits its own path-scoped relocation.",
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
