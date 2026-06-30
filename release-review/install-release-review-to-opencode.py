#!/usr/bin/env python3
"""
Install the modular release-review runbook and OpenCode command wrappers.

This installer copies the framework from its live source directory (next to this
script) into a target repository root:

    release-review/
    .opencode/commands/release-review.md
    .opencode/commands/release-review-plan.md

It copies directly from the source tree; there is no zip step. The source of truth
is the checked-out `release-review/` directory plus the `.opencode/commands/`
wrappers. (See DECISIONS.md D12: a committed zip was dropped in favor of
install-from-directory to avoid drift and a redundant binary blob.)

It is intentionally conservative:

1. It refuses to overwrite changed existing files unless --force is provided.
2. It creates timestamped backups by default before overwriting.
3. It supports --dry-run.
4. It validates that required framework files are present before installing.
5. It copies only safe, in-tree relative paths.
6. It does NOT modify .gitignore: run artifacts in repository-review/ are committed
   deliverables (DECISIONS.md D5/D14). It warns if repository-review/ is ignored.

Typical usage from the target repository root:

    python3 /path/to/ai-coding/release-review/install-release-review-to-opencode.py

Install into a specific repository:

    python3 install-release-review-to-opencode.py --repo /path/to/target-repo

Dry run:

    python3 install-release-review-to-opencode.py --dry-run

Force overwrite with backups:

    python3 install-release-review-to-opencode.py --force

Force overwrite without backups:

    python3 install-release-review-to-opencode.py --force --no-backup

Override where the framework is copied from (rarely needed):

    python3 install-release-review-to-opencode.py --source /path/to/ai-coding
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# Files that must exist in the source for an install to be valid.
REQUIRED_SOURCE_FILES: tuple[str, ...] = (
    "release-review/README.md",
    "release-review/00-run-protocol.md",
    "release-review/fix-decision-policy.md",
    ".opencode/commands/release-review.md",
    ".opencode/commands/release-review-plan.md",
)

# Files inside release-review/ that are authoring/installer artifacts and are NOT
# part of what gets installed into a target repository.
SOURCE_EXCLUDED_NAMES: frozenset[str] = frozenset(
    {
        "install-release-review-to-opencode.py",
        "install-release-review-to-opencode.sh",
        "release-review-validation-report.md",
    }
)

REPOSITORY_REVIEW_DIR = "repository-review/"


@dataclass(frozen=True)
class InstallPlan:
    """Represents the resolved installer inputs and behavior."""

    source_root: Path
    repo_root: Path
    dry_run: bool
    force: bool
    backup: bool


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed argument namespace.
    """

    parser = argparse.ArgumentParser(
        description="Install the release-review runbook and OpenCode commands into a repository.",
    )
    parser.add_argument(
        "--source",
        dest="source_root",
        type=Path,
        default=None,
        help=(
            "Root that contains release-review/ and .opencode/commands/. "
            "Defaults to the parent of this script's release-review/ directory."
        ),
    )
    parser.add_argument(
        "--repo",
        dest="repo_root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to install into. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite conflicting files. Existing files are backed up unless --no-backup is provided.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backups when --force overwrites files.",
    )

    return parser.parse_args()


def resolve_source_root(provided_source_root: Path | None) -> Path:
    """Resolve the framework source root.

    Args:
        provided_source_root: User-provided source root, if any.

    Returns:
        A directory that contains release-review/ and .opencode/commands/.

    Raises:
        SystemExit: If no valid source root can be found.
    """

    if provided_source_root is not None:
        source_root = provided_source_root.expanduser().resolve()
    else:
        # This script lives at <root>/release-review/install-...py, so the source
        # root that contains both release-review/ and .opencode/ is its grandparent.
        source_root = Path(__file__).resolve().parent.parent

    missing = [name for name in REQUIRED_SOURCE_FILES if not (source_root / name).is_file()]
    if missing:
        raise SystemExit(
            f"Source root does not look like the framework source: {source_root}\n"
            + "Missing required files:\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\nProvide the correct location with --source /path/to/ai-coding.",
        )

    return source_root


def build_install_plan(args: argparse.Namespace) -> InstallPlan:
    """Create a validated install plan from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        The resolved install plan.
    """

    return InstallPlan(
        source_root=resolve_source_root(args.source_root),
        repo_root=args.repo_root.expanduser().resolve(),
        dry_run=args.dry_run,
        force=args.force,
        backup=not args.no_backup,
    )


def ensure_repo_root(path: Path) -> None:
    """Ensure the target repository path exists and is a directory.

    The installer does not require Git because the runbook can be useful in
    non-Git directories, but it warns when .git is absent.

    Args:
        path: Repository root path.

    Raises:
        SystemExit: If the path is not a directory.
    """

    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Repository root is not a directory: {path}")

    if not (path / ".git").exists():
        print("Warning: target directory does not contain .git. Continuing anyway.", file=sys.stderr)


def collect_source_members(source_root: Path) -> list[str]:
    """Collect the relative paths to install from the source tree.

    Includes every file under release-review/ (except authoring/installer files)
    and the two .opencode/commands wrappers.

    Args:
        source_root: Validated framework source root.

    Returns:
        Sorted list of repo-relative paths to install.

    Raises:
        SystemExit: If the source layout is unexpectedly empty.
    """

    members: list[str] = []

    release_review_dir = source_root / "release-review"
    for path in sorted(release_review_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SOURCE_EXCLUDED_NAMES:
            continue
        if path.name.endswith(":Zone.Identifier"):
            continue
        members.append(path.relative_to(source_root).as_posix())

    for wrapper in ("release-review.md", "release-review-plan.md"):
        members.append(f".opencode/commands/{wrapper}")

    members = sorted(set(members))

    if not members:
        raise SystemExit(f"No installable files found under {release_review_dir}.")

    return members


def same_bytes(path: Path, data: bytes) -> bool:
    """Return whether an existing file already has the given content.

    Args:
        path: File path to compare.
        data: Expected bytes.

    Returns:
        True when the file exists and has identical content.
    """

    if not path.exists() or not path.is_file():
        return False

    return path.read_bytes() == data


def create_backup_path(repo_root: Path, relative_path: Path, timestamp: str) -> Path:
    """Create the backup destination path for a file.

    Args:
        repo_root: Repository root.
        relative_path: Path relative to the repository root.
        timestamp: Timestamp for the backup directory.

    Returns:
        The full backup path.
    """

    return repo_root / ".release-review-installer-backups" / timestamp / relative_path


def install_files(plan: InstallPlan, members: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Install source members into the repository root.

    Args:
        plan: Install plan.
        members: Repo-relative paths to install (also relative to the source root).

    Returns:
        A tuple of installed, skipped, and conflicted relative paths.

    Raises:
        SystemExit: If conflicts exist and --force was not provided.
    """

    installed: list[str] = []
    skipped: list[str] = []
    conflicted: list[str] = []
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for member_name in members:
        data = (plan.source_root / member_name).read_bytes()
        relative_path = Path(member_name)
        destination = plan.repo_root / relative_path

        if destination.exists():
            if destination.is_dir():
                conflicted.append(member_name + " [destination is directory]")
                continue

            if same_bytes(destination, data):
                skipped.append(member_name + " [already current]")
                continue

            if not plan.force:
                conflicted.append(member_name)
                continue

        action = "install"
        if destination.exists() and plan.force:
            action = "overwrite"

        if plan.dry_run:
            installed.append(f"{member_name} [{action}, dry-run]")
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and plan.force and plan.backup:
            backup_path = create_backup_path(plan.repo_root, relative_path, timestamp)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup_path)

        destination.write_bytes(data)
        installed.append(f"{member_name} [{action}]")

    if conflicted and not plan.force:
        message = [
            "Conflicting files already exist and differ from the source contents.",
            "No files were overwritten.",
            "",
            "Conflicts:",
        ]
        message.extend(f"  - {item}" for item in conflicted)
        message.extend(
            [
                "",
                "Run again with --force to overwrite them.",
                "By default, --force creates backups in .release-review-installer-backups/.",
            ],
        )
        raise SystemExit("\n".join(message))

    return installed, skipped, conflicted


def check_gitignore(plan: InstallPlan) -> str:
    """Check that repository-review/ is not git-ignored, and warn if it is.

    Run artifacts in repository-review/ are committed deliverables (DECISIONS.md
    D5/D14). The installer must not add an ignore line; it only warns if the target
    repo already ignores the directory, since that would suppress the run record.

    Args:
        plan: Install plan.

    Returns:
        A short status message.
    """

    gitignore_path = plan.repo_root / ".gitignore"
    if not gitignore_path.exists():
        return "no .gitignore present; repository-review/ will be tracked (correct)"

    lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
    ignored = any(
        line == REPOSITORY_REVIEW_DIR or line == REPOSITORY_REVIEW_DIR.rstrip("/")
        for line in lines
    )
    if ignored:
        return (
            "WARNING: .gitignore ignores repository-review/. Run artifacts are committed "
            "deliverables; remove that ignore line so the run record can be tracked."
        )

    return "repository-review/ is not ignored (correct; run artifacts are committed deliverables)"


def print_summary(
    plan: InstallPlan,
    installed: list[str],
    skipped: list[str],
    gitignore_status: str,
) -> None:
    """Print a user-facing install summary.

    Args:
        plan: Install plan.
        installed: Installed file descriptions.
        skipped: Skipped file descriptions.
        gitignore_status: Gitignore status message.
    """

    mode = "DRY RUN" if plan.dry_run else "COMPLETE"

    print(f"Release review installer: {mode}")
    print(f"Repository root: {plan.repo_root}")
    print(f"Source: {plan.source_root}")
    print()

    print("Installed or updated:")
    if installed:
        for item in installed:
            print(f"  - {item}")
    else:
        print("  - None")

    print()
    print("Skipped:")
    if skipped:
        for item in skipped:
            print(f"  - {item}")
    else:
        print("  - None")

    print()
    print(f"Gitignore: {gitignore_status}")

    print()
    print("OpenCode commands:")
    print("  - /release-review")
    print("  - /release-review-plan")

    print()
    print("Manual fallback:")
    print("  Read and execute release-review/README.md")

    if not plan.dry_run:
        print()
        print("Next step:")
        print("  Start or restart OpenCode from the repository root, then run /release-review.")


def main() -> int:
    """Run the installer.

    Returns:
        Process exit code.
    """

    args = parse_args()
    plan = build_install_plan(args)

    ensure_repo_root(plan.repo_root)
    members = collect_source_members(plan.source_root)

    installed, skipped, _ = install_files(plan, members)
    gitignore_status = check_gitignore(plan)

    print_summary(
        plan=plan,
        installed=installed,
        skipped=skipped,
        gitignore_status=gitignore_status,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
