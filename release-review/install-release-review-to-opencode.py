#!/usr/bin/env python3
"""
Install the modular release-review runbook and OpenCode command wrappers.

This installer copies the contents of release-review.zip into a repository root,
including:

    release-review/
    .opencode/commands/release-review.md
    .opencode/commands/release-review-plan.md

It is intentionally conservative:

1. It refuses to overwrite changed existing files unless --force is provided.
2. It creates timestamped backups by default before overwriting.
3. It supports --dry-run.
4. It validates the zip structure before installing.
5. It protects against unsafe zip paths.
6. It can add repository-review/ to .gitignore so run artifacts remain local.

Typical usage from a repository root:

    python3 install-release-review-to-opencode.py --zip release-review.zip

Or, if the zip is next to this installer:

    python3 install-release-review-to-opencode.py

Dry run:

    python3 install-release-review-to-opencode.py --dry-run

Force overwrite with backups:

    python3 install-release-review-to-opencode.py --force

Force overwrite without backups:

    python3 install-release-review-to-opencode.py --force --no-backup
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_ZIP_MEMBERS: tuple[str, ...] = (
    "release-review/README.md",
    "release-review/00-run-protocol.md",
    ".opencode/commands/release-review.md",
    ".opencode/commands/release-review-plan.md",
)

DEFAULT_GITIGNORE_LINE = "repository-review/"


@dataclass(frozen=True)
class InstallPlan:
    """Represents the resolved installer inputs and behavior."""

    zip_path: Path
    repo_root: Path
    dry_run: bool
    force: bool
    backup: bool
    update_gitignore: bool


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed argument namespace.

    Example:
        args = parse_args()
    """

    parser = argparse.ArgumentParser(
        description="Install release-review runbook and OpenCode commands into a repository.",
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        default=None,
        help="Path to release-review.zip. Defaults to ./release-review.zip or a zip next to this installer.",
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
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not add repository-review/ to .gitignore.",
    )

    return parser.parse_args()


def resolve_zip_path(provided_zip_path: Path | None) -> Path:
    """Resolve the zip path from arguments or common defaults.

    Args:
        provided_zip_path: User-provided zip path, if any.

    Returns:
        An existing zip path.

    Raises:
        SystemExit: If no zip file can be found.
    """

    if provided_zip_path is not None:
        zip_path = provided_zip_path.expanduser().resolve()
        if zip_path.exists():
            return zip_path
        raise SystemExit(f"Zip file not found: {zip_path}")

    candidates = (
        Path.cwd() / "release-review.zip",
        Path(__file__).resolve().parent / "release-review.zip",
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise SystemExit(
        "Could not find release-review.zip. Provide it with --zip /path/to/release-review.zip.",
    )


def build_install_plan(args: argparse.Namespace) -> InstallPlan:
    """Create a validated install plan from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        The resolved install plan.
    """

    zip_path = resolve_zip_path(args.zip_path)
    repo_root = args.repo_root.expanduser().resolve()

    return InstallPlan(
        zip_path=zip_path,
        repo_root=repo_root,
        dry_run=args.dry_run,
        force=args.force,
        backup=not args.no_backup,
        update_gitignore=not args.no_gitignore,
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


def is_safe_zip_member(name: str) -> bool:
    """Return whether a zip member path is safe to extract manually.

    Args:
        name: Zip member name.

    Returns:
        True when the path is relative and does not contain parent traversal.
    """

    path = Path(name)

    if path.is_absolute():
        return False

    if any(part == ".." for part in path.parts):
        return False

    if name.startswith("/") or name.startswith("\\"):
        return False

    return True


def validate_zip(zip_path: Path) -> list[str]:
    """Validate zip safety and required contents.

    Args:
        zip_path: Path to the zip archive.

    Returns:
        Sorted list of file members to install.

    Raises:
        SystemExit: If the zip file is invalid or missing required files.
    """

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            unsafe = [name for name in names if not is_safe_zip_member(name)]
            if unsafe:
                raise SystemExit(
                    "Unsafe zip paths detected:\n" + "\n".join(f"  - {name}" for name in unsafe),
                )

            missing = [name for name in REQUIRED_ZIP_MEMBERS if name not in names]
            if missing:
                raise SystemExit(
                    "Zip file is missing required members:\n" + "\n".join(f"  - {name}" for name in missing),
                )

            file_names = sorted(
                name for name in names
                if name and not name.endswith("/")
            )
            return file_names

    except zipfile.BadZipFile as exc:
        raise SystemExit(f"Invalid zip file: {zip_path}") from exc


def read_zip_bytes(zip_path: Path, member_name: str) -> bytes:
    """Read bytes for a member from a zip file.

    Args:
        zip_path: Path to the zip archive.
        member_name: Member path inside the archive.

    Returns:
        Raw member bytes.
    """

    with zipfile.ZipFile(zip_path, "r") as archive:
        return archive.read(member_name)


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


def install_files(plan: InstallPlan, members: Iterable[str]) -> tuple[list[str], list[str], list[str]]:
    """Install zip members into the repository root.

    Args:
        plan: Install plan.
        members: Zip member paths to install.

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
        data = read_zip_bytes(plan.zip_path, member_name)
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
            "Conflicting files already exist and differ from the zip contents.",
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


def update_gitignore(plan: InstallPlan) -> str:
    """Add repository-review/ to .gitignore if requested and needed.

    Args:
        plan: Install plan.

    Returns:
        A short status message.
    """

    if not plan.update_gitignore:
        return ".gitignore update skipped by --no-gitignore"

    gitignore_path = plan.repo_root / ".gitignore"

    existing = ""
    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")

    lines = [line.strip() for line in existing.splitlines()]
    if DEFAULT_GITIGNORE_LINE in lines:
        return ".gitignore already contains repository-review/"

    if plan.dry_run:
        return ".gitignore would be updated with repository-review/ [dry-run]"

    if gitignore_path.exists() and plan.force and plan.backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = create_backup_path(plan.repo_root, Path(".gitignore"), timestamp)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gitignore_path, backup_path)

    suffix = "" if existing.endswith("\n") or not existing else "\n"
    gitignore_path.write_text(
        existing + suffix + DEFAULT_GITIGNORE_LINE + "\n",
        encoding="utf-8",
    )

    return ".gitignore updated with repository-review/"


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
    print(f"Zip file: {plan.zip_path}")
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
    members = validate_zip(plan.zip_path)

    installed, skipped, _ = install_files(plan, members)
    gitignore_status = update_gitignore(plan)

    print_summary(
        plan=plan,
        installed=installed,
        skipped=skipped,
        gitignore_status=gitignore_status,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
