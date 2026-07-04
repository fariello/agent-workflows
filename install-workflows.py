#!/usr/bin/env python3
"""
Install the agent workflows (release-review, plan-review, ...) into a repository.

This copies the workflow bodies from this directory tree into a target repository
under `.agents/workflows/`, generates per-tool slash-command shims from the manifest
in `index.md`, and adds a one-line pointer to the target's agent-instructions file
(it updates an EXISTING `AGENTS.md` or `.agents/AGENTS.md` in place rather than
creating a duplicate; edits only its own marker-delimited block, idempotently; backs
up the file before the first edit; and fails safe on malformed markers). There is no
zip; it copies directly from the source tree.

Layout it installs into a target repo:

    .agents/workflows/                  workflow bodies + index.md (the manifest)
    .opencode/commands/<command>.md     OpenCode slash-command shims
    .claude/commands/<command>.md       Claude Code slash-command shims
    AGENTS.md                           one-line pointer to .agents/workflows/index.md

Design (see the repo's DECISIONS.md D12, D15, D16, D17):

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
  it never touches `workflow-artifacts/` run records, user code, or anything else.
- Git-aware but never commits: tracked changes are staged (`git add`/`git rm`),
  untracked changes are written/removed on disk; the user reviews and commits.
- Does NOT git-ignore anything. Run artifacts in `workflow-artifacts/` are committed
  deliverables (D5/D14); the installer only warns if the target ignores them.
- Migrates a pre-restructure repo on install (staged, never committed): removes the
  old root `release-review/` framework dir and `git mv`s old `repository-review/` run
  records into `workflow-artifacts/release-review/` (see D17/D19).

This script lives at the agent-workflows repo root; it installs the framework from its
`.agents/workflows/` subdirectory.

Typical usage from the target repository root:

    python3 /path/to/agent-workflows/install-workflows.py

Updating an existing install: just re-run the installer. Framework files are updated in
place (a timestamped backup is written unless --no-backup) and staged with git; nothing
is committed.

Dry run / no-prune / specific repo / custom source:

    python3 install-workflows.py --dry-run
    python3 install-workflows.py --no-prune
    python3 install-workflows.py --repo /path/to/target-repo
    python3 install-workflows.py --source /path/to/agent-workflows
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

# Filenames that, if found under the source `.agents/workflows/` tree, are never
# installed into a target nor pruned from one. The installer scripts now live at the
# repo root (outside the source tree), so these are defensive guards in case a copy is
# ever placed under .agents/workflows/.
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

# Candidate locations for the agent-instructions file, in preference order. The
# installer updates an EXISTING one (so it does not create a second, ignored file);
# it creates the first candidate only if none exists.
AGENTS_FILE_CANDIDATES: tuple[str, ...] = ("AGENTS.md", ".agents/AGENTS.md")
AGENTS_BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
AGENTS_END = "<!-- AGENT-WORKFLOWS:END -->"

ARTIFACTS_DIR = "workflow-artifacts/"
LEGACY_ARTIFACTS_DIR = "repository-review/"  # pre-D19 name; migrated on install

# The installer's own local backup scratch dir in the target. Auto-ignored in the
# target's .gitignore (the one narrow exception to "the installer does not touch
# .gitignore"); it is local scratch, not a committed deliverable.
BACKUPS_DIR = ".agent-workflows-installer-backups"


def is_ignored_source_path(path: Path) -> bool:
    """Return True for paths that must never be installed or pruned.

    Excludes the installer's own authoring files, Windows Zone.Identifier streams, and
    Python build cruft (``__pycache__`` dirs and ``.pyc``/``.pyo`` files) so a stray
    compiled artifact in the source tree is never copied into a target, and a compiled
    artifact in a target is never treated as a framework file to prune. Applied at both
    filesystem-walk sites so the install set and the prune set cannot diverge.
    """

    if path.name in SOURCE_EXCLUDED_NAMES or path.name.endswith(":Zone.Identifier"):
        return True
    if path.suffix in (".pyc", ".pyo"):
        return True
    if "__pycache__" in path.parts:
        return True
    return False
LEGACY_FRAMEWORK_DIR = "release-review"      # pre-D17 root location; migrated on install

MANIFEST_BEGIN = "<!-- WORKFLOWS-MANIFEST:BEGIN -->"
MANIFEST_END = "<!-- WORKFLOWS-MANIFEST:END -->"


@dataclass(frozen=True)
class Workflow:
    """A single workflow capability from the manifest."""

    command: str
    body: str
    description: str
    lens: str = ""  # optional: a lens file applied on top of a shared body


@dataclass(frozen=True)
class InstallPlan:
    """Resolved installer inputs and behavior."""

    source_root: Path
    repo_root: Path
    dry_run: bool
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
    parser.add_argument("--no-backup", action="store_true", help="Do not back up before overwrite/prune.")
    parser.add_argument("--no-prune", action="store_true", help="Do not remove stale framework files.")
    return parser.parse_args()


def resolve_source_root(provided: Path | None) -> Path:
    """Resolve the source `.agents/workflows` directory and validate it.

    This installer lives at the repo root, so the default source is
    `<script dir>/.agents/workflows/`. `--source` may point at either that directory
    directly, or at a repo root that contains it (we resolve the `.agents/workflows`
    subdirectory in that case).
    """

    if provided is not None:
        candidate = provided.expanduser().resolve()
        # Accept either the workflows dir itself or a repo root containing it.
        if candidate.name != "workflows" and (candidate / ".agents" / "workflows").is_dir():
            candidate = candidate / ".agents" / "workflows"
        source_root = candidate
    else:
        source_root = Path(__file__).resolve().parent / ".agents" / "workflows"

    index = source_root / "index.md"
    if not index.is_file() or source_root.name != "workflows":
        raise SystemExit(
            f"Source does not look like an .agents/workflows directory: {source_root}\n"
            "Provide it with --source /path/to/agent-workflows (or .../.agents/workflows).",
        )
    return source_root


def build_install_plan(args: argparse.Namespace) -> InstallPlan:
    return InstallPlan(
        source_root=resolve_source_root(args.source_root),
        repo_root=args.repo_root.expanduser().resolve(),
        dry_run=args.dry_run,
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
        # Support both 3-column (command|body|description) and 4-column
        # (command|body|lens|description) manifest rows.
        if len(cells) == 4:
            command, body, lens, description = cells
        elif len(cells) == 3:
            command, body, description = cells
            lens = "-"
        else:
            continue
        if command in ("command", "") or set(command) <= {"-"}:
            continue  # header or separator row
        lens = "" if lens.strip() in ("", "-") else lens.strip()
        workflows.append(
            Workflow(command=command, body=body, description=description, lens=lens)
        )

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
        if is_ignored_source_path(path):
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

    lens_note = ""
    if command == "assess":
        # The parameterized assess command: the argument names the concern; the harness
        # resolves it to a lens (with aliases/fuzzy match) or, if empty, lists concerns
        # and asks. Concerns are cataloged as the `assess-<concern>` manifest rows.
        lens_note = (
            "\nThe first argument names the CONCERN to assess (e.g. `security`, `prose`, "
            "`compliance-readiness`); any further arguments narrow the scope (a path/module) "
            "or carry options. Resolve the concern to its lens `.agents/workflows/assess/"
            "lenses/<concern>.md` and apply it on top of the harness (assess that single "
            "concern deeply and write an IPD; do not change code or execute the plan). "
            "Accept case-insensitive aliases and common short forms (e.g. `a11y` -> "
            "accessibility, `perf` -> performance, `deps`/`supply` -> supply-chain); on an "
            "unknown concern, show the closest matches. If NO concern was given, list the "
            "available concerns (the `assess/lenses/*.md` files) and ask the user which to "
            "run.\n"
        )
    elif workflow.lens:
        lens_note = (
            f"\nApply the concern lens @{workflow.lens} on top of that harness: it "
            "selects the concern, its lead personas, and its rubric. Assess that single "
            "concern deeply and write an IPD into the project's pending-plans directory; "
            "do not change code and do not execute the plan.\n"
        )

    # Tool-specific frontmatter. Both OpenCode and Claude Code read a markdown command
    # file with YAML frontmatter, but their supported fields differ:
    #   - OpenCode uses `agent:` to pick the executing agent.
    #   - Claude Code (.claude/commands, which still works) does NOT use `agent:`; it
    #     uses fields like `argument-hint`. Emitting OpenCode's `agent:` there is
    #     meaningless, so we tailor the frontmatter per tool.
    if tool == "claude":
        frontmatter = (
            "---\n"
            f"description: {workflow.description}\n"
            "argument-hint: \"[optional target path or flags]\"\n"
            "---\n"
        )
    else:  # opencode
        frontmatter = (
            "---\n"
            f"description: {workflow.description}\n"
            "agent: build\n"
            "---\n"
        )

    return (
        f"{frontmatter}\n"
        f"Read and execute @{workflow.body}.{planning_note}\n"
        f"{lens_note}\n"
        "If the user provided arguments, treat them as the target path(s) and/or flags "
        "for this workflow: $ARGUMENTS\n\n"
        "Treat the referenced file as the controlling instruction and follow it fully.\n"
    )


def is_concern_catalog_row(workflow: Workflow) -> bool:
    """Whether a manifest row is an assess CONCERN catalog entry, not its own command.

    The `assess-<concern>` rows are the source of truth for the concern -> lens mapping
    (used by the parameterized `/assess <thing>` command's picker and by the discovery
    catalog). They do NOT each generate their own shim; the single `assess` row does.
    """

    return workflow.command.startswith("assess-")


def generate_shim_members(workflows: list[Workflow]) -> dict[str, str]:
    """Build the map of shim repo-relative path -> file content for all tools.

    One shim per command row, EXCEPT `assess-<concern>` catalog rows, which are folded
    into the single parameterized `/assess` command.
    """

    shims: dict[str, str] = {}
    for shim_dir in COMMAND_SHIM_DIRS:
        tool = "claude" if shim_dir.startswith(".claude") else "opencode"
        for workflow in workflows:
            if is_concern_catalog_row(workflow):
                continue  # catalog entry, not its own command
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
    return repo_root / BACKUPS_DIR / timestamp / relative_path


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
    """Install one file.

    Framework-namespace files are updated in place by default (this is how an update
    works); a stale/differing file is overwritten, not treated as a conflict. Every
    overwrite is backed up first unless --no-backup. The only genuine conflict is a
    directory where a file must go. This mirrors the installer's prune-by-default
    posture (DECISIONS D15): if deleting a stale framework file by default is safe with
    backups + git staging + dry-run, overwriting one is strictly safer.
    """

    destination = plan.repo_root / relative_posix
    if destination.exists():
        if destination.is_dir():
            conflicted.append(relative_posix + " [destination is directory]")
            return
        if same_bytes(destination, data):
            skipped.append(relative_posix + " [already current]")
            return

    action = "overwrite" if destination.exists() else "install"
    if plan.dry_run:
        installed.append(f"{relative_posix} [{action}, dry-run]")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and plan.backup:
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
        source_path = plan.source_root / source_relative
        data = source_path.read_bytes()
        write_file(plan, member, data, use_git, timestamp, installed, skipped, conflicted)
        # Preserve the executable bit for scripts/tools (e.g. tools/*.py, *.sh).
        if not plan.dry_run:
            dest = plan.repo_root / member
            try:
                src_exec = source_path.stat().st_mode & 0o111
                if src_exec and dest.is_file():
                    dest.chmod(dest.stat().st_mode | 0o111)
            except OSError:
                pass

    for rel, content in sorted(shim_members.items()):
        write_file(plan, rel, content.encode("utf-8"), use_git, timestamp, installed, skipped, conflicted)

    if conflicted:
        message = [
            "Cannot install: a target path that must hold a framework file is a directory.",
            "No files were installed or pruned. Resolve these paths and re-run:",
            "",
        ]
        message.extend(f"  - {item}" for item in conflicted)
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
            if is_ignored_source_path(path):
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


def resolve_agents_file(repo_root: Path) -> str:
    """Choose which agent-instructions file to update.

    Prefer an EXISTING candidate (so the pointer lands in the file the project's tools
    already read, not a new ignored one). If none exists, use the first candidate.

    Args:
        repo_root: Target repository root.

    Returns:
        Repo-relative path of the AGENTS file to manage.
    """

    for candidate in AGENTS_FILE_CANDIDATES:
        if (repo_root / candidate).is_file():
            return candidate
    return AGENTS_FILE_CANDIDATES[0]


def update_agents_pointer(plan: InstallPlan, use_git: bool, timestamp: str) -> str:
    """Add or refresh the managed pointer block in the target's AGENTS file.

    Safety contract (deliberately stricter than an append-to-config installer):
    - Updates an existing AGENTS file in place rather than creating a duplicate.
    - Edits ONLY the marked region; never reflows or touches the user's own prose.
    - Idempotent: a well-formed BEGIN..END pair is replaced, so re-runs do not stack
      blocks.
    - Fail-safe on malformed markers: if exactly one well-formed pair is not present,
      it appends a fresh block instead of risking a destructive regex over user text.
    - Backs up the existing file before the first modification (unless --no-backup).
    """

    rel = resolve_agents_file(plan.repo_root)
    agents_path = plan.repo_root / rel
    block = agents_pointer_block()
    existing = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""

    # Only treat the file as having a managed block when there is exactly one
    # well-formed BEGIN..END pair, in order. Otherwise fail safe (append).
    begins = existing.count(AGENTS_BEGIN)
    ends = existing.count(AGENTS_END)
    well_formed = (
        begins == 1
        and ends == 1
        and existing.find(AGENTS_BEGIN) < existing.find(AGENTS_END)
    )

    if well_formed:
        new_text = re.sub(
            re.escape(AGENTS_BEGIN) + r".*?" + re.escape(AGENTS_END),
            lambda _m: block.strip(),  # lambda avoids backref interpretation in block
            existing,
            count=1,
            flags=re.DOTALL,
        )
        verb = f"refreshed pointer in {rel}"
    elif (begins or ends):
        # Malformed/partial markers present: do not risk mangling. Append a clean block.
        new_text = existing.rstrip("\n") + "\n\n" + block
        verb = f"appended pointer to {rel} (left existing malformed marker untouched)"
    elif existing:
        new_text = existing.rstrip("\n") + "\n\n" + block
        verb = f"appended pointer to existing {rel}"
    else:
        new_text = "# AGENTS\n\n" + block
        verb = f"created {rel} with pointer"

    if new_text == existing:
        return f"{rel} pointer already current"
    if plan.dry_run:
        return f"{rel} would be updated ({verb}) [dry-run]"

    # Back up an existing file before the first modification.
    if existing and plan.backup:
        backup = create_backup_path(plan.repo_root, Path(rel), timestamp)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agents_path, backup)

    agents_path.parent.mkdir(parents=True, exist_ok=True)
    agents_path.write_text(new_text, encoding="utf-8")
    if use_git:
        git_run(plan.repo_root, ["add", "--", rel])
    return verb


def _git_mv(repo_root: Path, src: str, dst: str) -> None:
    """git mv with parent creation; falls back to filesystem move if needed."""

    (repo_root / dst).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(repo_root), "mv", "--", src, dst],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # untracked or partially-tracked: fall back to filesystem move + stage
        shutil.move(str(repo_root / src), str(repo_root / dst))


def _remove_path(repo_root: Path, rel: str, use_git: bool, backup_root: Path | None) -> None:
    """Remove a file or directory, git rm if tracked, else filesystem; back up first."""

    target = repo_root / rel
    if backup_root is not None:
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if target.is_dir():
            shutil.copytree(target, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(target, dest)
    tracked = use_git and git_is_tracked(repo_root, rel)
    if tracked:
        git_run(repo_root, ["rm", "-r", "--quiet", "--", rel])
    elif target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def migrate_legacy_layout(plan: InstallPlan, use_git: bool) -> list[str]:
    """Migrate a repo that has the pre-restructure layout.

    Handles two legacy forms (see DECISIONS D17 / D19):
    - Pre-D17: the framework lived at the repo-root `release-review/` (now
      `.agents/workflows/release-review/`). The old root directory is removed (the
      new content is installed under .agents/workflows/), backed up first.
    - Pre-D19: run records lived in `repository-review/` (now
      `workflow-artifacts/release-review/`). These are migrated with `git mv` so the
      committed history moves rather than being lost.

    All changes are staged (never committed) and reported. Honors --dry-run.

    Returns:
        Human-readable descriptions of the migrations performed (or that would be).
    """

    actions: list[str] = []
    repo = plan.repo_root
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = None if (plan.dry_run or not plan.backup) else create_backup_path(
        repo, Path("legacy-migration"), timestamp
    )

    # 1) Pre-D19: migrate run records repository-review/ -> workflow-artifacts/release-review/
    legacy_artifacts = repo / LEGACY_ARTIFACTS_DIR
    if legacy_artifacts.is_dir():
        for run_dir in sorted(p for p in legacy_artifacts.iterdir() if p.is_dir()):
            rel_src = f"{LEGACY_ARTIFACTS_DIR}{run_dir.name}"
            rel_dst = f"{ARTIFACTS_DIR}release-review/{run_dir.name}"
            if (repo / rel_dst).exists():
                actions.append(f"{rel_src} -> {rel_dst} [skip: destination exists]")
                continue
            if plan.dry_run:
                actions.append(f"{rel_src} -> {rel_dst} [git mv, dry-run]")
                continue
            _git_mv(repo, rel_src, rel_dst)
            if use_git:
                git_run(repo, ["add", "--", rel_dst])
            actions.append(f"{rel_src} -> {rel_dst} [migrated]")
        # remove the now-empty legacy dir if anything remains (e.g. stray files)
        remaining = list(legacy_artifacts.rglob("*")) if legacy_artifacts.exists() else []
        if not any(p.is_file() for p in remaining) and not plan.dry_run and legacy_artifacts.exists():
            try:
                shutil.rmtree(legacy_artifacts)
            except OSError:
                pass

    # 2) Pre-D17: remove the old root release-review/ framework directory.
    # Only treat it as legacy if it is NOT the source we are installing from (i.e.
    # the target is a different repo than this framework's own checkout).
    legacy_framework = repo / LEGACY_FRAMEWORK_DIR
    new_framework = repo / WORKFLOWS_DIR / "release-review"
    is_self = legacy_framework.resolve() == (plan.source_root / "release-review").resolve() \
        if legacy_framework.exists() else False
    if legacy_framework.is_dir() and not is_self and new_framework != legacy_framework:
        rel = LEGACY_FRAMEWORK_DIR
        if plan.dry_run:
            actions.append(f"{rel}/ [remove legacy root framework dir, dry-run]")
        else:
            _remove_path(repo, rel, use_git, backup_root)
            actions.append(f"{rel}/ [removed legacy root framework dir; new copy under .agents/workflows/]")

    return actions


def check_gitignore(plan: InstallPlan) -> str:
    gitignore_path = plan.repo_root / ".gitignore"
    if not gitignore_path.exists():
        return "no .gitignore present; workflow-artifacts/ will be tracked (correct)"
    lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
    ignored = []
    for d in (ARTIFACTS_DIR, LEGACY_ARTIFACTS_DIR):
        if any(line in (d, d.rstrip("/")) for line in lines):
            ignored.append(d)
    if ignored:
        return (
            f"WARNING: .gitignore ignores {', '.join(ignored)}. Run artifacts are committed "
            "deliverables; remove that ignore line so the run record can be tracked."
        )
    return "workflow-artifacts/ is not ignored (correct)"


def ensure_backups_gitignored(plan: InstallPlan, use_git: bool) -> str:
    """Ensure the target's .gitignore ignores the installer's own backups dir.

    This is the one narrow, deliberate exception to "the installer does not modify
    .gitignore": it manages ONLY its own local backup scratch dir (BACKUPS_DIR), never
    user or artifact ignores. Idempotent (a plain "line already present?" check; no
    marker block needed for a single entry). Honors --dry-run. Creates .gitignore if
    absent. Returns a short status for the summary.
    """

    pattern = BACKUPS_DIR + "/"
    gitignore_path = plan.repo_root / ".gitignore"

    existing = ""
    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        if any(line.strip() in (pattern, BACKUPS_DIR) for line in existing.splitlines()):
            return f"{pattern} already ignored (correct)"

    if plan.dry_run:
        return f"would add {pattern} to .gitignore [dry-run]"

    block = "# agent-workflows installer local backups\n" + pattern + "\n"
    if existing and not existing.endswith("\n"):
        block = "\n" + block
    elif existing:
        block = "\n" + block
    with gitignore_path.open("a", encoding="utf-8") as handle:
        handle.write(block)

    if use_git:
        git_run(plan.repo_root, ["add", "--", ".gitignore"])
    return f"added {pattern} to .gitignore"


def print_summary(
    plan: InstallPlan,
    workflows: list[Workflow],
    migrated: list[str],
    installed: list[str],
    skipped: list[str],
    pruned: list[str],
    agents_status: str,
    gitignore_status: str,
    backups_ignore_status: str,
    use_git: bool,
) -> None:
    mode = "DRY RUN" if plan.dry_run else "COMPLETE"
    print(f"Agent workflows installer: {mode}")
    print(f"Repository root: {plan.repo_root}")
    print(f"Source: {plan.source_root}")
    print(f"Git: {'staging changes (no commit)' if use_git else 'not a git repo; filesystem only'}")
    print()

    if migrated:
        print("Legacy layout migrated (pre-restructure repo):")
        for item in migrated:
            print(f"  - {item}")
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
    print(f"Gitignore (workflow-artifacts): {gitignore_status}")
    print(f"Gitignore (installer backups): {backups_ignore_status}")

    if use_git and not plan.dry_run and (installed or pruned or backups_ignore_status.startswith("added")):
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

    # Recommended next step: run the setup-repo wizard, phrased for both tool families.
    # It is idempotent and drift-aware, so it doubles as a post-update conformance check.
    setup = next((w for w in workflows if w.command == "setup-repo"), None)
    if setup is not None:
        updated = any("[install]" in i or "[overwrite]" in i or "migrated" in i.lower()
                      for i in (installed + pruned + migrated))
        print()
        if updated:
            print("NEXT STEP - the framework changed; re-run setup-repo to re-check")
            print("best-practice CONFORMANCE (it detects drift and only proposes gaps):")
        else:
            print("NEXT STEP - set up this repo for best practices and security:")
        print("  - OpenCode or Claude Code: run  /setup-repo")
        print("  - Cursor / Codex / Antigravity / VS Code agents / any other agent:")
        print(f"    tell the agent:  Read and execute {setup.body}")
        print("  (Guided + idempotent: it asks before each change, is safe to re-run as a")
        print("   conformance check, and stages changes without committing.)")


def main() -> int:
    args = parse_args()
    plan = build_install_plan(args)

    ensure_repo_root(plan.repo_root)
    use_git = git_available(plan.repo_root)

    workflows = parse_manifest(plan.source_root)
    body_members = collect_source_members(plan.source_root)
    shim_members = generate_shim_members(workflows)

    run_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    migrated = migrate_legacy_layout(plan, use_git)
    installed, skipped, _ = install_all(plan, body_members, shim_members, use_git)
    pruned = prune_stale(plan, body_members, shim_members, use_git)
    agents_status = update_agents_pointer(plan, use_git, run_timestamp)
    gitignore_status = check_gitignore(plan)
    backups_ignore_status = ensure_backups_gitignored(plan, use_git)

    print_summary(
        plan=plan,
        workflows=workflows,
        migrated=migrated,
        installed=installed,
        skipped=skipped,
        pruned=pruned,
        agents_status=agents_status,
        gitignore_status=gitignore_status,
        backups_ignore_status=backups_ignore_status,
        use_git=use_git,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
