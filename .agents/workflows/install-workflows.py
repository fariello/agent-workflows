#!/usr/bin/env python3
"""
Install the agent workflows (release-review, plan-review, ...) into a repository.

This copies the workflow bodies from this directory tree into a target repository
under `.agents/workflows/`, generates per-tool slash-command shims from the manifest
in `index.md`, and adds a one-line pointer to the target's `AGENTS.md`. There is no
zip; it copies directly from the source tree.

Layout it installs into a target repo:

    .agents/workflows/                  workflow bodies + index.md (the manifest)
    .opencode/commands/<command>.md     OpenCode slash-command shims
    .claude/commands/<command>.md       Claude Code slash-command shims
    AGENTS.md                           one-line pointer to .agents/workflows/index.md

Design (see ai-coding DECISIONS.md D12, D15, D16, D17):

- Workflow bodies are tool-agnostic and live together, namespaced by capability,
  under `.agents/workflows/<capability>/`. Adding a capability is a new subdir plus a
  row in `index.md`; the shims are generated, never hand-maintained.
- The same body is invoked everywhere. Native `/commands` (OpenCode, Claude Code) are
  thin generated shims that say "read and execute <body>". Tools without native
  commands use the universal fallback: read `.agents/workflows/index.md` and "read and
  execute" the body, discoverable via the `AGENTS.md` pointer.
- Clean sync by default: framework files in the target that are no longer in the
  source are pruned. Pruning is strictly scoped to the framework namespace
  (`.agents/workflows/`, the generated shim files, and the AGENTS.md pointer block);
  it never touches `repository-review/` run records, user code, or anything else.
- Git-aware but never commits: tracked changes are staged (`git add`/`git rm`),
  untracked changes are written/removed on disk; the user reviews and commits.
- Does NOT git-ignore anything. Run artifacts in `repository-review/` are committed
  deliverables (D5/D14); the installer only warns if the target ignores them.

Typical usage from the target repository root:

    python3 /path/to/ai-coding/.agents/workflows/install-workflows.py

Dry run / force / no-prune / specific repo / custom source:

    python3 install-workflows.py --dry-run
    python3 install-workflows.py --force
    python3 install-workflows.py --no-prune
    python3 install-workflows.py --repo /path/to/target-repo
    python3 install-workflows.py --source /path/to/ai-coding/.agents/workflows
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WORKFLOWS_DIR = ".agents/workflows"
INDEX_FILE = f"{WORKFLOWS_DIR}/index.md"

# Files in the source workflows tree that are authoring/installer artifacts: never
# installed into a target, never pruned from one.
SOURCE_EXCLUDED_NAMES: frozenset[str] = frozenset(
    {
        "install-workflows.py",
        "install-workflows.sh",
    }
)

# Per-tool command shim directories the installer generates into.
COMMAND_SHIM_DIRS: tuple[str, ...] = (
    ".opencode/commands",
    ".claude/commands",
)

AGENTS_FILE = "AGENTS.md"
AGENTS_BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
AGENTS_END = "<!-- AGENT-WORKFLOWS:END -->"

REPOSITORY_REVIEW_DIR = "repository-review/"

MANIFEST_BEGIN = "<!-- WORKFLOWS-MANIFEST:BEGIN -->"
MANIFEST_END = "<!-- WORKFLOWS-MANIFEST:END -->"


@dataclass(frozen=True)
class Workflow:
    """A single workflow capability from the manifest."""

    command: str
    body: str
    description: str


@dataclass(frozen=True)
class InstallPlan:
    """Resolved installer inputs and behavior."""

    source_root: Path
    repo_root: Path
    dry_run: bool
    force: bool
    backup: bool
    prune: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install agent workflows and slash-command shims into a repository.",
    )
    parser.add_argument(
        "--source",
        dest="source_root",
        type=Path,
        default=None,
        help="Path to the source .agents/workflows directory. Defaults to this script's directory.",
    )
    parser.add_argument(
        "--repo",
        dest="repo_root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to install into. Defaults to the current directory.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite locally-modified framework files. Backed up unless --no-backup.",
    )
    parser.add_argument("--no-backup", action="store_true", help="Do not back up before overwrite/prune.")
    parser.add_argument("--no-prune", action="store_true", help="Do not remove stale framework files.")
    return parser.parse_args()


def resolve_source_root(provided: Path | None) -> Path:
    """Resolve the source .agents/workflows directory and validate it."""

    if provided is not None:
        source_root = provided.expanduser().resolve()
    else:
        source_root = Path(__file__).resolve().parent

    index = source_root / "index.md"
    if not index.is_file() or source_root.name != "workflows":
        raise SystemExit(
            f"Source does not look like an .agents/workflows directory: {source_root}\n"
            "Provide it with --source /path/to/ai-coding/.agents/workflows.",
        )
    return source_root


def build_install_plan(args: argparse.Namespace) -> InstallPlan:
    return InstallPlan(
        source_root=resolve_source_root(args.source_root),
        repo_root=args.repo_root.expanduser().resolve(),
        dry_run=args.dry_run,
        force=args.force,
        backup=not args.no_backup,
        prune=not args.no_prune,
    )


def ensure_repo_root(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Repository root is not a directory: {path}")
    if not (path / ".git").exists():
        print("Warning: target directory does not contain .git. Continuing anyway.", file=sys.stderr)


def parse_manifest(source_root: Path) -> list[Workflow]:
    """Parse the workflow manifest table from index.md.

    Returns:
        The list of workflows declared between the manifest markers.

    Raises:
        SystemExit: If the manifest block is missing or empty.
    """

    text = (source_root / "index.md").read_text(encoding="utf-8")
    block = re.search(
        re.escape(MANIFEST_BEGIN) + r"(.*?)" + re.escape(MANIFEST_END),
        text,
        re.DOTALL,
    )
    if not block:
        raise SystemExit(f"index.md is missing the manifest markers {MANIFEST_BEGIN} / {MANIFEST_END}.")

    workflows: list[Workflow] = []
    for line in block.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        command, body, description = cells
        if command in ("command", "") or set(command) <= {"-"}:
            continue  # header or separator row
        workflows.append(Workflow(command=command, body=body, description=description))

    if not workflows:
        raise SystemExit("No workflows found in the index.md manifest.")
    return workflows


def collect_source_members(source_root: Path) -> list[str]:
    """Collect repo-relative paths of workflow body files to install.

    Every file under .agents/workflows/ except authoring/installer artifacts.
    """

    members: list[str] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SOURCE_EXCLUDED_NAMES or path.name.endswith(":Zone.Identifier"):
            continue
        rel = path.relative_to(source_root).as_posix()
        members.append(f"{WORKFLOWS_DIR}/{rel}")

    if not members:
        raise SystemExit(f"No installable files found under {source_root}.")
    return sorted(set(members))


def shim_body(command: str, workflow: Workflow, tool: str) -> str:
    """Generate the markdown body for a per-tool command shim.

    Args:
        command: The command name.
        workflow: The workflow it invokes.
        tool: "opencode" or "claude" (controls minor frontmatter differences).

    Returns:
        Full file content for the shim.
    """

    planning_note = ""
    if command == "release-review-plan":
        planning_note = " Run in planning-only mode: complete the audit and the consolidated implementation plan, and stop before implementation."

    return (
        "---\n"
        f"description: {workflow.description}\n"
        "agent: build\n"
        "---\n\n"
        f"Read and execute @{workflow.body}.{planning_note}\n\n"
        "If the user provided arguments, treat them as the target path(s) and/or flags "
        "for this workflow: $ARGUMENTS\n\n"
        "Treat the referenced file as the controlling instruction and follow it fully.\n"
    )


def generate_shim_members(workflows: list[Workflow]) -> dict[str, str]:
    """Build the map of shim repo-relative path -> file content for all tools."""

    shims: dict[str, str] = {}
    for shim_dir in COMMAND_SHIM_DIRS:
        tool = "claude" if shim_dir.startswith(".claude") else "opencode"
        for workflow in workflows:
            rel = f"{shim_dir}/{workflow.command}.md"
            shims[rel] = shim_body(workflow.command, workflow, tool)
    return shims


def agents_pointer_block() -> str:
    """The managed AGENTS.md pointer block (pointer only, never the payload)."""

    return (
        f"{AGENTS_BEGIN}\n"
        "## Agent workflows\n\n"
        "This repository includes reusable agent workflows under `.agents/workflows/`. "
        "They are invoked on demand and are NOT always-loaded context. See "
        "`.agents/workflows/index.md` for the list and how to run each (native `/commands` "
        "in OpenCode/Claude Code, or \"read and execute <body path>\" in any other agent).\n"
        f"{AGENTS_END}\n"
    )


def same_bytes(path: Path, data: bytes) -> bool:
    return path.exists() and path.is_file() and path.read_bytes() == data


def create_backup_path(repo_root: Path, relative_path: Path, timestamp: str) -> Path:
    return repo_root / ".agent-workflows-installer-backups" / timestamp / relative_path


def git_available(repo_root: Path) -> bool:
    if not (repo_root / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_is_tracked(repo_root: Path, relative_posix: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", relative_posix],
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0


def git_run(repo_root: Path, args: list[str]) -> None:
    result = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")


def in_framework_namespace(relative_posix: str) -> bool:
    """Whether a path is one the installer is allowed to add or remove."""

    if relative_posix.startswith(WORKFLOWS_DIR + "/"):
        return True
    return any(relative_posix.startswith(shim_dir + "/") for shim_dir in COMMAND_SHIM_DIRS)


def write_file(
    plan: InstallPlan,
    relative_posix: str,
    data: bytes,
    use_git: bool,
    timestamp: str,
    installed: list[str],
    skipped: list[str],
    conflicted: list[str],
) -> None:
    """Install one file with the conservative overwrite/backup/conflict policy."""

    destination = plan.repo_root / relative_posix
    if destination.exists():
        if destination.is_dir():
            conflicted.append(relative_posix + " [destination is directory]")
            return
        if same_bytes(destination, data):
            skipped.append(relative_posix + " [already current]")
            return
        if not plan.force:
            conflicted.append(relative_posix)
            return

    action = "overwrite" if destination.exists() and plan.force else "install"
    if plan.dry_run:
        installed.append(f"{relative_posix} [{action}, dry-run]")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and plan.force and plan.backup:
        backup = create_backup_path(plan.repo_root, Path(relative_posix), timestamp)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup)
    destination.write_bytes(data)
    if use_git:
        git_run(plan.repo_root, ["add", "--", relative_posix])
    installed.append(f"{relative_posix} [{action}]")


def install_all(
    plan: InstallPlan,
    body_members: list[str],
    shim_members: dict[str, str],
    use_git: bool,
) -> tuple[list[str], list[str], list[str]]:
    """Install body files and generated shims. Returns (installed, skipped, conflicted)."""

    installed: list[str] = []
    skipped: list[str] = []
    conflicted: list[str] = []
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    prefix = WORKFLOWS_DIR + "/"
    for member in body_members:
        # member is e.g. ".agents/workflows/release-review/README.md"; map to source.
        source_relative = member[len(prefix):] if member.startswith(prefix) else member
        data = (plan.source_root / source_relative).read_bytes()
        write_file(plan, member, data, use_git, timestamp, installed, skipped, conflicted)

    for rel, content in sorted(shim_members.items()):
        write_file(plan, rel, content.encode("utf-8"), use_git, timestamp, installed, skipped, conflicted)

    if conflicted and not plan.force:
        message = [
            "Conflicting files already exist and differ from the source contents.",
            "No files were installed or pruned.",
            "",
            "Conflicts:",
        ]
        message.extend(f"  - {item}" for item in conflicted)
        message.append("")
        message.append("Run again with --force to overwrite them (backups are created by default).")
        raise SystemExit("\n".join(message))

    return installed, skipped, conflicted


def collect_target_framework_files(repo_root: Path) -> set[str]:
    """Framework-namespace files currently present in the target (prune candidates).

    Scope: everything under .agents/workflows/ (minus authoring files) and any shim
    files in the command shim dirs.
    """

    present: set[str] = set()

    workflows_dir = repo_root / WORKFLOWS_DIR
    if workflows_dir.is_dir():
        for path in workflows_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.name in SOURCE_EXCLUDED_NAMES:
                continue
            present.add(path.relative_to(repo_root).as_posix())

    for shim_dir in COMMAND_SHIM_DIRS:
        d = repo_root / shim_dir
        if d.is_dir():
            for path in d.glob("*.md"):
                present.add(path.relative_to(repo_root).as_posix())

    return present


def prune_stale(
    plan: InstallPlan,
    body_members: list[str],
    shim_members: dict[str, str],
    use_git: bool,
) -> list[str]:
    """Remove framework files in the target that are no longer in the source."""

    if not plan.prune:
        return []

    desired = set(body_members) | set(shim_members.keys())
    present = collect_target_framework_files(plan.repo_root)
    orphans = sorted(present - desired)

    pruned: list[str] = []
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for rel in orphans:
        if not in_framework_namespace(rel):  # defense in depth
            continue
        destination = plan.repo_root / rel
        tracked = use_git and git_is_tracked(plan.repo_root, rel)
        how = "git rm" if tracked else "rm"

        if plan.dry_run:
            pruned.append(f"{rel} [{how}, dry-run]")
            continue

        if plan.backup:
            backup = create_backup_path(plan.repo_root, Path(rel), timestamp)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        if tracked:
            git_run(plan.repo_root, ["rm", "--quiet", "--", rel])
        else:
            destination.unlink()
        pruned.append(f"{rel} [{how}]")

    return pruned


def update_agents_pointer(plan: InstallPlan, use_git: bool) -> str:
    """Add or refresh the managed pointer block in the target's AGENTS.md."""

    agents_path = plan.repo_root / AGENTS_FILE
    block = agents_pointer_block()
    existing = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""

    if AGENTS_BEGIN in existing and AGENTS_END in existing:
        new_text = re.sub(
            re.escape(AGENTS_BEGIN) + r".*?" + re.escape(AGENTS_END),
            block.strip(),
            existing,
            flags=re.DOTALL,
        )
        verb = "refreshed"
    elif existing:
        new_text = existing.rstrip("\n") + "\n\n" + block
        verb = "appended pointer to existing"
    else:
        new_text = "# AGENTS\n\n" + block
        verb = "created with pointer"

    if new_text == existing:
        return "AGENTS.md pointer already current"
    if plan.dry_run:
        return f"AGENTS.md would be {verb} [dry-run]"

    agents_path.write_text(new_text, encoding="utf-8")
    if use_git:
        git_run(plan.repo_root, ["add", "--", AGENTS_FILE])
    return f"AGENTS.md {verb}"


def check_gitignore(plan: InstallPlan) -> str:
    gitignore_path = plan.repo_root / ".gitignore"
    if not gitignore_path.exists():
        return "no .gitignore present; repository-review/ will be tracked (correct)"
    lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
    if any(line in (REPOSITORY_REVIEW_DIR, REPOSITORY_REVIEW_DIR.rstrip("/")) for line in lines):
        return (
            "WARNING: .gitignore ignores repository-review/. Run artifacts are committed "
            "deliverables; remove that ignore line so the run record can be tracked."
        )
    return "repository-review/ is not ignored (correct)"


def print_summary(
    plan: InstallPlan,
    workflows: list[Workflow],
    installed: list[str],
    skipped: list[str],
    pruned: list[str],
    agents_status: str,
    gitignore_status: str,
    use_git: bool,
) -> None:
    mode = "DRY RUN" if plan.dry_run else "COMPLETE"
    print(f"Agent workflows installer: {mode}")
    print(f"Repository root: {plan.repo_root}")
    print(f"Source: {plan.source_root}")
    print(f"Git: {'staging changes (no commit)' if use_git else 'not a git repo; filesystem only'}")
    print()

    print("Installed or updated:")
    for item in installed or ["None"]:
        print(f"  - {item}")
    print()
    print("Skipped:")
    for item in skipped or ["None"]:
        print(f"  - {item}")
    print()
    if plan.prune:
        print("Pruned (stale framework files):")
        for item in pruned or ["None"]:
            print(f"  - {item}")
    else:
        print("Pruned: disabled by --no-prune")
    print()
    print(f"AGENTS.md: {agents_status}")
    print(f"Gitignore: {gitignore_status}")

    if use_git and not plan.dry_run and (installed or pruned):
        print()
        print("Changes are STAGED but NOT committed. Review and commit, e.g.:")
        print('  git commit -m "agent-workflows: sync via installer"')

    print()
    print("Workflows available:")
    for workflow in workflows:
        print(f"  - /{workflow.command}  ->  {workflow.body}")
    print()
    print("Universal fallback (any agent):")
    print("  Read and execute .agents/workflows/index.md, then the workflow body.")


def main() -> int:
    args = parse_args()
    plan = build_install_plan(args)

    ensure_repo_root(plan.repo_root)
    use_git = git_available(plan.repo_root)

    workflows = parse_manifest(plan.source_root)
    body_members = collect_source_members(plan.source_root)
    shim_members = generate_shim_members(workflows)

    installed, skipped, _ = install_all(plan, body_members, shim_members, use_git)
    pruned = prune_stale(plan, body_members, shim_members, use_git)
    agents_status = update_agents_pointer(plan, use_git)
    gitignore_status = check_gitignore(plan)

    print_summary(
        plan=plan,
        workflows=workflows,
        installed=installed,
        skipped=skipped,
        pruned=pruned,
        agents_status=agents_status,
        gitignore_status=gitignore_status,
        use_git=use_git,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
