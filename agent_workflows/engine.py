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
import os
import shlex
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import versioning as _VERSIONING
from ._compat import packaged_source_root
from .term import Term
import json


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


LEGACY_FRAMEWORK_DIR = "release-review"  # pre-D17 root location; migrated on install

MANIFEST_BEGIN = "<!-- WORKFLOWS-MANIFEST:BEGIN -->"
MANIFEST_END = "<!-- WORKFLOWS-MANIFEST:END -->"

VERSION_FILE = "VERSION"  # under the source .agents/workflows/; stamped into targets


def read_version(source_root: Path) -> str:
    """Return the framework version for the source at ``source_root``.

    Prefers the git-tag-driven resolver (versioning.py) when the source is a real git
    work tree of this project, so a clean tagged checkout reports the semver (e.g.
    ``1.0.0``) and a dirty/ahead checkout reports a ``.devN`` string that cannot be
    mistaken for a release. When the source is not a git tree (a copied-out install, a
    plain file copy, or an unpacked wheel) it reads the baked ``VERSION`` file, which is
    copied verbatim into each target so the installed copy carries its own marker.

    The VERSION file is a DERIVED artifact (regenerated from the tag via
    ``make version-file``), no longer hand-edited.

    Returns:
        The resolved/trimmed version string, or "unknown" if unresolvable.
    """

    if _VERSIONING is not None:
        # The resolver runs `git describe` in source_root (git works from any subdir of
        # the work tree) and falls back to the VERSION file itself when there is no git.
        return _VERSIONING.resolve_version(
            source_root, version_file=source_root / VERSION_FILE
        )

    # Degraded path (versioning.py unavailable): read the file directly.
    path = source_root / VERSION_FILE
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


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
    no_color: bool = False
    yes: bool = False
    diff: bool = False


def parse_args(argv=None) -> argparse.Namespace:
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
        dest="repo_roots",
        type=Path,
        nargs="*",
        default=None,
        help="Repository roots to install into. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actions without writing."
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up before overwrite/prune.",
    )
    parser.add_argument(
        "--no-prune", action="store_true", help="Do not remove stale framework files."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color (also honored via NO_COLOR).",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the framework version (from the source VERSION file) and exit.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Automatically answer yes to all prompts.",
    )
    parser.add_argument(
        "--diff",
        "-d",
        action="store_true",
        help="Show a unified diff of differences instead of writing.",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Roll back the installation to the state of the last backup.",
    )
    return parser.parse_args(argv)


def resolve_source_root(provided: Path | None) -> Path:
    """Resolve the source `.agents/workflows` directory and validate it.

    Resolution order:

    1. An explicit ``--source`` (accepts either the `.agents/workflows` dir itself or a
       repo root containing it).
    2. The tree BUNDLED in the installed package (`agent_workflows/_data/.agents/
       workflows/`), located via `_compat.packaged_source_root()`. This is the wheel /
       `pipx install` case, so the CLI works from `site-packages` with no sibling source.
    3. The repo-root checkout tree, relative to this module (`agent_workflows/engine.py`
       -> repo root is two parents up). This is the dev / clone-and-run case.
    """

    if provided is not None:
        candidate = provided.expanduser().resolve()
        # Accept either the workflows dir itself or a repo root containing it.
        if (
            candidate.name != "workflows"
            and (candidate / ".agents" / "workflows").is_dir()
        ):
            candidate = candidate / ".agents" / "workflows"
        source_root = candidate
    else:
        bundled = packaged_source_root()
        if bundled is not None:
            source_root = bundled
        else:
            # Dev/clone: repo root is two dirs up from agent_workflows/engine.py.
            source_root = (
                Path(__file__).resolve().parent.parent / ".agents" / "workflows"
            )

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
        no_color=getattr(args, "no_color", False),
        yes=getattr(args, "yes", False),
        diff=getattr(args, "diff", False),
    )


def ensure_repo_root(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Repository root is not a directory: {path}")
    if not (path / ".git").exists():
        print(
            "Warning: target directory does not contain .git. Continuing anyway.",
            file=sys.stderr,
        )


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
        raise SystemExit(
            f"index.md is missing the manifest markers {MANIFEST_BEGIN} / {MANIFEST_END}."
        )

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
    elif command == "advise":
        # The parameterized advise command: the argument names the expert PERSONA; the
        # harness resolves it to a persona charter or, if empty, lists personas and asks.
        # Personas are cataloged as the `advise-<persona>` manifest rows.
        lens_note = (
            "\nThe first argument names the expert PERSONA (e.g. `skeptic`, `spec-editor`, "
            "`architect`, `red-teamer`, `staff-engineer`, `domain-expert`, `naive-user`); "
            "any further arguments name the artifact to examine (a spec, plan, design, or "
            "decision doc) - otherwise the persona examines the current context. Resolve "
            "the persona to its charter `.agents/workflows/advise/personas/<persona>.md` "
            "and adopt it: conduct a genuine question-driven session, surface gaps and "
            "assumptions, and coach the author. It may edit a planning/prose artifact only "
            "with per-change consent; it never executes code. Accept case-insensitive "
            "aliases (e.g. `skeptic`/`grill`/`grill-me` -> skeptic, `mentor` -> "
            "staff-engineer, `red-team`/`adversary` -> red-teamer, `naive`/`novice` -> "
            "naive-user); on an unknown persona, show the closest matches. If NO persona "
            "was given, list the available personas (the `advise/personas/*.md` files) and "
            "ask the user which to use.\n"
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
            'argument-hint: "[optional target path or flags]"\n'
            "---\n"
        )
    else:  # opencode
        frontmatter = (
            "---\n" f"description: {workflow.description}\n" "agent: build\n" "---\n"
        )

    return (
        f"{frontmatter}\n"
        f"Read and execute @{workflow.body}.{planning_note}\n"
        f"{lens_note}\n"
        "If the user provided arguments, treat them as the target path(s) and/or flags "
        "for this workflow: $ARGUMENTS\n\n"
        "Treat the referenced file as the controlling instruction and follow it fully.\n"
    )


# Manifest rows with these command prefixes are CATALOG entries for a parameterized
# command, not commands in their own right. `assess-<concern>` rows catalog the assess
# lenses; `advise-<persona>` rows catalog the advise personas. Each family collapses to a
# single parameterized shim (`assess`, `advise`); the catalog rows are the source of truth
# for the picker and for `/list-workflows`, but generate no shim of their own.
CATALOG_ROW_PREFIXES: tuple[str, ...] = ("assess-", "advise-")

# Real commands that happen to share a catalog prefix and must STILL get their own shim
# (they are standalone workflows, not catalog entries). `assess-all` is the rollup
# orchestration command, not an assess concern.
CATALOG_PREFIX_EXCEPTIONS: frozenset[str] = frozenset({"assess-all"})


def is_concern_catalog_row(workflow: Workflow) -> bool:
    """Whether a manifest row is a catalog entry (assess concern / advise persona).

    Catalog rows are the source of truth for a parameterized command's set (the assess
    lenses, the advise personas) and feed its picker and `/list-workflows`. They do NOT
    each generate their own shim; the single parameterized row (`assess`, `advise`) does.
    Commands in CATALOG_PREFIX_EXCEPTIONS are standalone workflows despite the prefix.
    """

    if workflow.command in CATALOG_PREFIX_EXCEPTIONS:
        return False
    return workflow.command.startswith(CATALOG_ROW_PREFIXES)


def generate_shim_members(
    workflows: list[Workflow], source_root: Path
) -> dict[str, str]:
    """Build the map of shim repo-relative path -> file content for all tools.

    One shim per command row, EXCEPT `assess-<concern>` catalog rows, which are folded
    into the single parameterized `/assess` command.
    """

    shims: dict[str, str] = {}
    template_path = source_root / "templates" / "shim-README.md"
    try:
        readme_content = template_path.read_text(encoding="utf-8")
    except OSError:
        readme_content = (
            "# Generated Slash Commands\n\n"
            "This directory contains auto-generated slash-command shims for developer agents.\n\n"
            "⚠️ **DO NOT EDIT THESE FILES MANUALLY.**\n"
            "Any modifications will be overwritten or pruned the next time the agent-workflows installer is run.\n\n"
            "To install, update, or prune commands, run:\n"
            "  aw install <dir>\n"
        )

    for shim_dir in COMMAND_SHIM_DIRS:
        tool = "claude" if shim_dir.startswith(".claude") else "opencode"
        for workflow in workflows:
            if is_concern_catalog_row(workflow):
                continue  # catalog entry, not its own command
            rel = f"{shim_dir}/{workflow.command}.md"
            shims[rel] = shim_body(workflow.command, workflow, tool)
        shims[f"{shim_dir}/README.md"] = readme_content
    return shims


def agents_pointer_block() -> str:
    """The managed AGENTS.md pointer block (pointer only, never the payload)."""

    return (
        f"{AGENTS_BEGIN}\n"
        "## Agent workflows\n\n"
        "This repository includes reusable agent workflows under `.agents/workflows/`. "
        "They are invoked on demand and are NOT always-loaded context. See "
        "`.agents/workflows/index.md` for the list and how to run each (native `/commands` "
        'in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).\n\n'
        "### Guidelines for Antigravity & Other Agents\n"
        'When requested to run one of these workflows (e.g. "run release-review", "assess <concern>", "run setup-repo", "run scaffold"):\n'
        "1. Locate the workflow's entry file under `.agents/workflows/` (referenced in `.agents/workflows/index.md`).\n"
        "2. Read and execute the instructions defined in that workflow file step-by-step.\n"
        f"{AGENTS_END}\n"
    )


def is_interactive_session(plan: InstallPlan) -> bool:
    """Helper to check if we are in a real interactive terminal session."""
    if plan.yes:
        return False
    if os.environ.get("CI"):
        return False
    if not sys.stdin.isatty():
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            handle = ctypes.windll.kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            mode = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
        except Exception:
            return False
    return True


def print_stdout_safe(text: str) -> None:
    """Safely print a string to stdout without raising UnicodeEncodeError."""
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))
        sys.stdout.flush()


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
            [
                "git",
                "-C",
                str(repo_root),
                "ls-files",
                "--error-unmatch",
                relative_posix,
            ],
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0


def git_run(repo_root: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")


def git_add_optional(repo_root: Path, relative_posix: str) -> bool:
    """Stage a path, tolerating the case where it is ignored by .gitignore.

    Command shims live under .opencode/ or .claude/, which a repo may legitimately
    gitignore. In that case the file is still written to disk (it works locally) but
    cannot be tracked; we warn once and continue rather than aborting the whole install.
    Any OTHER git failure is a real error and is raised.

    Returns:
        True if the path was staged; False if it was skipped because it is ignored.
    """

    result = subprocess.run(
        ["git", "-C", str(repo_root), "add", "--", relative_posix],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    if "ignored by" in result.stderr:
        return False
    raise SystemExit(f"git add -- {relative_posix} failed:\n{result.stderr.strip()}")


def in_framework_namespace(relative_posix: str) -> bool:
    """Whether a path is one the installer is allowed to add or remove."""

    if relative_posix.startswith(WORKFLOWS_DIR + "/"):
        return True
    return any(
        relative_posix.startswith(shim_dir + "/") for shim_dir in COMMAND_SHIM_DIRS
    )


def _wants_executable(mode: int) -> bool:
    """Whether a filesystem mode has any executable bit set."""

    return bool(mode & 0o111)


def write_file(
    plan: InstallPlan,
    relative_posix: str,
    data: bytes,
    use_git: bool,
    timestamp: str,
    installed: list[str],
    skipped: list[str],
    conflicted: list[str],
    executable: bool = False,
) -> None:
    """Install one file.

    Framework-namespace files are updated in place by default (this is how an update
    works); a stale/differing file is overwritten, not treated as a conflict. Every
    overwrite is backed up first unless --no-backup. The only genuine conflict is a
    directory where a file must go. This mirrors the installer's prune-by-default
    posture (DECISIONS D15): if deleting a stale framework file by default is safe with
    backups + git staging + dry-run, overwriting one is strictly safer.

    The source file's executable bit is synced to the destination (tool scripts must stay
    executable). A file whose CONTENT is already current but whose MODE differs is still
    fixed and re-staged, so a mode-only change is not silently left unstaged.
    """

    destination = plan.repo_root / relative_posix
    content_current = False
    if destination.exists():
        if destination.is_dir():
            conflicted.append(relative_posix + " [destination is directory]")
            return
        content_current = same_bytes(destination, data)

    # Detect a mode-only difference on an otherwise-current file.
    mode_differs = False
    if content_current:
        current_exec = _wants_executable(destination.stat().st_mode)
        mode_differs = current_exec != executable
        if not mode_differs:
            skipped.append(relative_posix + " [already current]")
            return

    action = "overwrite" if destination.exists() else "install"
    if content_current and mode_differs:
        action = "chmod"

    if action == "overwrite" and not content_current:
        is_shim = any(
            relative_posix.startswith(sd + "/") for sd in COMMAND_SHIM_DIRS
        ) and relative_posix.endswith(".md")
        if is_shim and not relative_posix.endswith("README.md"):
            try:
                current_text = destination.read_text(encoding="utf-8")
                if is_shim_customized(current_text):
                    term = Term(plan.no_color)
                    print(
                        term.colorize(
                            f"Warning: {relative_posix} has manual modifications.",
                            "yellow",
                        )
                    )
                    is_interactive = is_interactive_session(plan)
                    choice = "n"
                    if is_interactive:
                        try:
                            choice = (
                                input("Do you want to overwrite it? [y/N]: ")
                                .strip()
                                .lower()
                            )
                        except (KeyboardInterrupt, EOFError):
                            print()
                            choice = "n"
                    if not plan.yes and choice not in ("y", "yes"):
                        skipped.append(relative_posix + " [already current]")
                        return
            except OSError:
                pass

    if plan.dry_run:
        installed.append(f"{relative_posix} [{action}, dry-run]")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and plan.backup and not content_current:
        backup = create_backup_path(plan.repo_root, Path(relative_posix), timestamp)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup)
    if not content_current:
        destination.write_bytes(data)
    _apply_executable_bit(destination, executable)
    if use_git:
        _stage_installed_file(plan.repo_root, relative_posix)
    installed.append(f"{relative_posix} [{action}]")


def _apply_executable_bit(path: Path, executable: bool) -> None:
    """Set or clear the user/group/other execute bits to match the source."""

    mode = path.stat().st_mode
    if executable:
        path.chmod(mode | 0o111)
    else:
        path.chmod(mode & ~0o111)


def _stage_installed_file(repo_root: Path, relative_posix: str) -> None:
    """Stage an installed file. Shim dirs (.opencode/.claude) may be gitignored; if so,
    warn and continue. Framework-namespace files must stage, so a failure there is real.
    """

    if in_framework_namespace(relative_posix) and not (
        relative_posix.startswith(".opencode/") or relative_posix.startswith(".claude/")
    ):
        git_run(repo_root, ["add", "--", relative_posix])
        return
    staged = git_add_optional(repo_root, relative_posix)
    if not staged:
        _warn_ignored_shim(relative_posix)


_IGNORED_SHIM_WARNED: set[str] = set()


def _warn_ignored_shim(relative_posix: str) -> None:
    """Warn once per shim directory that files are written but not tracked (gitignored)."""

    top = relative_posix.split("/", 1)[0]
    if top in _IGNORED_SHIM_WARNED:
        return
    _IGNORED_SHIM_WARNED.add(top)
    print(
        f"note: {top}/ is ignored by .gitignore; its command shims are written to disk "
        f"(they work locally) but are not tracked in git.",
        file=sys.stderr,
    )


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
        source_relative = member[len(prefix) :] if member.startswith(prefix) else member
        source_path = plan.source_root / source_relative
        data = source_path.read_bytes()
        # Sync the source's executable bit (tool scripts stay executable); write_file
        # applies it and re-stages even on a mode-only change.
        executable = _wants_executable(source_path.stat().st_mode)
        write_file(
            plan,
            member,
            data,
            use_git,
            timestamp,
            installed,
            skipped,
            conflicted,
            executable=executable,
        )

    for rel, content in sorted(shim_members.items()):
        # Generated shims are plain markdown, never executable.
        write_file(
            plan,
            rel,
            content.encode("utf-8"),
            use_git,
            timestamp,
            installed,
            skipped,
            conflicted,
            executable=False,
        )

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

        is_shim = any(
            rel.startswith(sd + "/") for sd in COMMAND_SHIM_DIRS
        ) and rel.endswith(".md")
        if is_shim and not rel.endswith("README.md"):
            try:
                current_text = destination.read_text(encoding="utf-8")
                if is_shim_customized(current_text):
                    term = Term(plan.no_color)
                    print(
                        term.colorize(
                            f"Warning: {rel} has manual modifications and is no longer needed (stale).",
                            "yellow",
                        )
                    )
                    is_interactive = is_interactive_session(plan)
                    choice = "n"
                    if is_interactive:
                        try:
                            choice = (
                                input("Do you want to delete it? [y/N]: ")
                                .strip()
                                .lower()
                            )
                        except (KeyboardInterrupt, EOFError):
                            print()
                            choice = "n"
                    if not plan.yes and choice not in ("y", "yes"):
                        continue
            except OSError:
                pass

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
    elif begins or ends:
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


def _remove_path(
    repo_root: Path, rel: str, use_git: bool, backup_root: Path | None
) -> None:
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
    backup_root = (
        None
        if (plan.dry_run or not plan.backup)
        else create_backup_path(repo, Path("legacy-migration"), timestamp)
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
        remaining = (
            list(legacy_artifacts.rglob("*")) if legacy_artifacts.exists() else []
        )
        if (
            not any(p.is_file() for p in remaining)
            and not plan.dry_run
            and legacy_artifacts.exists()
        ):
            try:
                shutil.rmtree(legacy_artifacts)
            except OSError:
                pass

    # 2) Pre-D17: remove the old root release-review/ framework directory.
    # Only treat it as legacy if it is NOT the source we are installing from (i.e.
    # the target is a different repo than this framework's own checkout).
    legacy_framework = repo / LEGACY_FRAMEWORK_DIR
    new_framework = repo / WORKFLOWS_DIR / "release-review"
    is_self = (
        legacy_framework.resolve() == (plan.source_root / "release-review").resolve()
        if legacy_framework.exists()
        else False
    )
    if legacy_framework.is_dir() and not is_self and new_framework != legacy_framework:
        rel = LEGACY_FRAMEWORK_DIR
        if plan.dry_run:
            actions.append(f"{rel}/ [remove legacy root framework dir, dry-run]")
        else:
            _remove_path(repo, rel, use_git, backup_root)
            actions.append(
                f"{rel}/ [removed legacy root framework dir; new copy under .agents/workflows/]"
            )

    return actions


def check_gitignore(plan: InstallPlan) -> str:
    gitignore_path = plan.repo_root / ".gitignore"
    if not gitignore_path.exists():
        return "no .gitignore present; workflow-artifacts/ will be tracked (correct)"
    lines = [
        line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()
    ]
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
        if any(
            line.strip() in (pattern, BACKUPS_DIR) for line in existing.splitlines()
        ):
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


def run_git_diagnostics(plan: InstallPlan) -> bool:
    """Run Git pre-flight checks (dirty, sync).

    If interactive, display a consolidated diagnostic block and prompt menu.
    Returns True if we should proceed with the install, or False if we should abort.
    """
    if not git_available(plan.repo_root):
        return True

    # 1. Run git status --porcelain
    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(plan.repo_root),
        capture_output=True,
        text=True,
        shell=False,
    )
    is_dirty = bool(status_proc.stdout.strip())
    dirty_lines = status_proc.stdout.strip().split("\n") if is_dirty else []

    # 2. Run fast git fetch with a timeout
    try:
        subprocess.run(
            ["git", "fetch", "--quiet"],
            cwd=str(plan.repo_root),
            timeout=3.0,
            shell=False,
        )
    except (subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError):
        pass

    # 3. Check tracking branch sync status
    branch_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(plan.repo_root),
        capture_output=True,
        text=True,
        shell=False,
    )
    branch = branch_proc.stdout.strip()

    tracking_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "@{u}"],
        cwd=str(plan.repo_root),
        capture_output=True,
        text=True,
        shell=False,
    )
    has_tracking = tracking_proc.returncode == 0
    tracking_branch = tracking_proc.stdout.strip() if has_tracking else ""

    behind = 0
    _ahead = 0
    if has_tracking:
        sync_proc = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"HEAD...{tracking_branch}"],
            cwd=str(plan.repo_root),
            capture_output=True,
            text=True,
            shell=False,
        )
        if sync_proc.returncode == 0:
            m = re.match(r"(\d+)\s+(\d+)", sync_proc.stdout.strip())
            if m:
                _ahead = int(m.group(1))
                behind = int(m.group(2))

    # If clean and remote is synced, proceed silently
    if not is_dirty and behind == 0:
        return True

    # If non-interactive, print warnings to stderr and proceed
    is_interactive = is_interactive_session(plan) and not plan.diff

    warnings = []
    if is_dirty:
        warnings.append(
            f"Repository has {len(dirty_lines)} uncommitted local files (dirty)."
        )
    if has_tracking and behind > 0:
        warnings.append(
            f"Branch '{branch}' is behind '{tracking_branch}' by {behind} commit{'s' if behind > 1 else ''} (needs pull)."
        )
    elif not has_tracking:
        warnings.append(f"Branch '{branch}' has no tracking remote branch configured.")

    if not is_interactive:
        for warn in warnings:
            sys.stderr.write(f"Git Warning: {warn}\n")
        return True

    term = Term(plan.no_color)
    print()
    print(term.colorize("Git Diagnostics:", "yellow"))
    for warn in warnings:
        print(f"  - {warn}")
    print()
    print("What would you like to do?")
    print("  [1] Pull latest changes (git pull --rebase) and proceed")
    print("  [2] Proceed anyway (risk of merge/overwrite)")
    print("  [3] Abort installation")

    try:
        val = input("Select an option [1-3, default 1]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if not val:
        val = "1"

    if val == "1":
        print("Running: git pull --rebase ...")
        pull_proc = subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=str(plan.repo_root),
            shell=False,
        )
        if pull_proc.returncode != 0:
            sys.stderr.write(
                term.colorize("Error: git pull failed. Aborting installation.\n", "red")
            )
            return False
        return True
    elif val == "2":
        return True
    else:
        print("Aborted.")
        return False


def is_shim_customized(content: str) -> bool:
    """Detect if a command shim file has manual user customizations."""
    standard_prefixes = (
        "---",
        "description:",
        "agent: build",
        "argument-hint:",
        "Read and execute @.agents/workflows",
        "The first argument names",
        "any further",
        "Resolve the",
        "Accept case-insensitive",
        "on an unknown",
        "If NO",
        "Apply the concern lens @.agents/workflows",
    )
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return False

    if not any(
        line.startswith("Read and execute @.agents/workflows") for line in lines
    ):
        return True

    for line in lines:
        if any(line.startswith(prefix) for prefix in standard_prefixes):
            continue
        if any(
            term in line.lower()
            for term in (
                "concern",
                "persona",
                "charter",
                "adoption",
                "harness",
                "audit",
                "conduct a",
                "coach",
            )
        ):
            continue
        return True
    return False


def save_created_files_record(
    repo_root: Path, timestamp: str, newly_created: list[str]
) -> None:
    """Save the list of newly created files in the backup directory."""
    if not newly_created:
        return
    backup_dir = repo_root / BACKUPS_DIR / timestamp
    if not backup_dir.is_dir():
        backup_dir.mkdir(parents=True, exist_ok=True)

    record_path = backup_dir / ".created-files.json"
    try:
        record_path.write_text(json.dumps(newly_created, indent=2), encoding="utf-8")
    except OSError:
        pass


def prune_old_backups(repo_root: Path) -> None:
    """Keep only the 5 most recent backups under BACKUPS_DIR."""
    backups_path = repo_root / BACKUPS_DIR
    if not backups_path.is_dir():
        return
    try:
        dirs = sorted(
            [d for d in backups_path.iterdir() if d.is_dir()], key=lambda d: d.name
        )
        if len(dirs) > 5:
            to_delete = dirs[:-5]
            for d in to_delete:
                shutil.rmtree(d, ignore_errors=True)
    except OSError:
        pass


def show_install_diffs(
    plan: InstallPlan,
    body_members: list[str],
    shim_members: dict[str, str],
) -> None:
    """Generate and display a colorized unified diff of the proposed changes."""
    import difflib

    term = Term(plan.no_color)
    prefix = WORKFLOWS_DIR + "/"
    proposed: dict[str, bytes] = {}

    for member in body_members:
        source_relative = member[len(prefix) :] if member.startswith(prefix) else member
        source_path = plan.source_root / source_relative
        try:
            proposed[member] = source_path.read_bytes()
        except OSError:
            pass

    for rel, content in shim_members.items():
        proposed[rel] = content.encode("utf-8")

    artifacts_readme = "workflow-artifacts/README.md"
    artifacts_dest = plan.repo_root / artifacts_readme
    if not artifacts_dest.is_file():
        template_path = plan.source_root / "templates" / "workflow-artifacts-README.md"
        try:
            proposed[artifacts_readme] = template_path.read_bytes()
        except OSError:
            proposed[artifacts_readme] = (
                "# Workflow Run Artifacts\n\n"
                "This directory contains review records, verification evidence, and audit logs "
                "generated by AI agent workflows (such as release reviews or plan reviews).\n\n"
                "## ⚠️ Git Guidelines\n"
                "* **DO NOT gitignore this folder.**\n"
                "* These records represent the review and approval history of this repository "
                "and are intended to be committed to git alongside your code changes.\n"
            ).encode("utf-8")

    has_diffs = False
    for rel, new_bytes in sorted(proposed.items()):
        dest_path = plan.repo_root / rel
        current_lines = []
        if dest_path.is_file():
            try:
                current_text = dest_path.read_text(encoding="utf-8", errors="replace")
                current_lines = current_text.splitlines(keepends=True)
            except OSError:
                pass

        new_text = new_bytes.decode("utf-8", errors="replace")
        new_lines = new_text.splitlines(keepends=True)

        if "".join(current_lines) == "".join(new_lines):
            continue

        has_diffs = True
        print(term.colorize(f"\nDiff: {rel}", "bold"))

        diff = difflib.unified_diff(
            current_lines,
            new_lines,
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            n=3,
        )

        for line in diff:
            stripped = line.rstrip("\r\n")
            if stripped.startswith("+") and not stripped.startswith("+++"):
                print_stdout_safe(term.colorize(stripped, "green"))
            elif stripped.startswith("-") and not stripped.startswith("---"):
                print_stdout_safe(term.colorize(stripped, "red"))
            elif stripped.startswith("@@"):
                print_stdout_safe(term.colorize(stripped, "cyan"))
            else:
                print_stdout_safe(stripped)

    if not has_diffs:
        print("No changes (everything is already current).")


def run_rollback(repo_root: Path, no_color: bool) -> int:
    """Revert the last installation using the latest backup."""
    term = Term(no_color)
    backups_path = repo_root / BACKUPS_DIR
    if not backups_path.is_dir():
        sys.stderr.write(
            term.colorize("Error: No backups found. Cannot roll back.\n", "red")
        )
        return 1

    dirs = sorted(
        [d for d in backups_path.iterdir() if d.is_dir()], key=lambda d: d.name
    )
    if not dirs:
        sys.stderr.write(
            term.colorize(
                "Error: No backup directories found. Cannot roll back.\n", "red"
            )
        )
        return 1

    latest_backup = dirs[-1]
    print(f"Rolling back using backup from {latest_backup.name}...")

    use_git = git_available(repo_root)

    created_record = latest_backup / ".created-files.json"
    created_files = []
    if created_record.is_file():
        try:
            created_files = json.loads(created_record.read_text(encoding="utf-8"))
        except OSError:
            pass

    for rel in created_files:
        target = repo_root / rel
        if target.is_file():
            print(f"  [removed  ] {rel}")
            try:
                target.unlink()
                if use_git:
                    git_run(
                        repo_root, ["rm", "--cached", "--ignore-unmatch", "--", rel]
                    )
            except OSError as e:
                sys.stderr.write(term.colorize(f"Error removing {rel}: {e}\n", "red"))

    for path in sorted(latest_backup.rglob("*")):
        if not path.is_file():
            continue
        rel_to_backup = path.relative_to(latest_backup)
        if rel_to_backup.as_posix() == ".created-files.json":
            continue

        target = repo_root / rel_to_backup
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [restored ] {rel_to_backup.as_posix()}")
        try:
            shutil.copy2(path, target)
            if use_git:
                git_run(repo_root, ["add", "--", rel_to_backup.as_posix()])
        except OSError as e:
            sys.stderr.write(
                term.colorize(f"Error restoring {rel_to_backup}: {e}\n", "red")
            )

    shutil.rmtree(latest_backup, ignore_errors=True)
    print(term.colorize("Rollback completed successfully.", "green"))
    return 0


def prompt_and_run_commit(
    plan: InstallPlan,
    installed: list[str],
    pruned: list[str],
    agents_status: str,
    backups_ignore_status: str,
    use_git: bool,
    artifacts: list[str] = None,
) -> None:
    """Offer to commit only the installer-modified files."""
    if not use_git or plan.dry_run:
        return

    term = Term(plan.no_color)
    files_to_commit: dict[str, str] = {}

    if artifacts:
        for art in artifacts:
            parts = art.rsplit(" [", 1)
            rel_path = parts[0]
            action = parts[1].rstrip("]") if len(parts) == 2 else "added"
            if "dry-run" in action:
                continue
            files_to_commit[rel_path] = "added"

    for item in installed:
        parts = item.rsplit(" [", 1)
        if len(parts) == 2:
            rel_path = parts[0]
            action = parts[1].rstrip("]")
            if "dry-run" in action:
                continue
            if action == "install":
                files_to_commit[rel_path] = "added"
            elif action == "overwrite":
                files_to_commit[rel_path] = "modified"
            elif action == "chmod":
                files_to_commit[rel_path] = "chmod"

    for item in pruned:
        parts = item.rsplit(" [", 1)
        if len(parts) == 2:
            rel_path = parts[0]
            action = parts[1].rstrip("]")
            if "dry-run" in action:
                continue
            files_to_commit[rel_path] = "removed"

    if (
        not agents_status.endswith("already current")
        and "[dry-run]" not in agents_status
    ):
        agents_rel = resolve_agents_file(plan.repo_root)
        files_to_commit[agents_rel] = "modified"

    if (
        backups_ignore_status.startswith("added ")
        and "[dry-run]" not in backups_ignore_status
    ):
        files_to_commit[".gitignore"] = "modified"

    if not files_to_commit:
        return

    print()
    print("Ready to commit framework sync changes:")
    for path, action in sorted(files_to_commit.items()):
        if action == "added":
            prefix = term.colorize("[added    ]", "green", "bold")
        elif action == "modified":
            prefix = term.colorize("[modified ]", "yellow", "bold")
        elif action == "chmod":
            prefix = term.colorize("[chmod    ]", "cyan", "bold")
        else:
            prefix = term.colorize("[removed  ]", "red", "bold")
        print(f"  {prefix} {path}")

    print()
    is_interactive = is_interactive_session(plan)
    choice = "n"

    if is_interactive:
        try:
            choice = (
                input("Would you like the installer to commit these changes? [Y/n] ")
                .strip()
                .lower()
            )
            if choice not in ("", "y", "yes"):
                is_interactive = False
        except (KeyboardInterrupt, EOFError):
            print()
            is_interactive = False

    paths_list = sorted(files_to_commit.keys())
    if plan.yes or (is_interactive and choice in ("", "y", "yes")):
        print("Committing changes...")
        cmd = [
            "git",
            "commit",
            "-m",
            "agent-workflows: sync via installer",
            "--",
        ] + paths_list
        res = subprocess.run(cmd, cwd=str(plan.repo_root), shell=False)
        if res.returncode == 0:
            print(term.colorize("Changes committed successfully.", "green"))
        else:
            sys.stderr.write(term.colorize("Error: git commit failed.\n", "red"))
    else:
        quoted_paths = []
        for p in paths_list:
            if " " in p or '"' in p or "'" in p:
                quoted_paths.append(shlex.quote(p))
            else:
                quoted_paths.append(p)
        print()
        print("To commit these changes manually, run:")
        print(f"  git commit -m \"sync agent-workflows\" -- {' '.join(quoted_paths)}")


def format_output_item(item: str, term: Term) -> str:
    """Parse an item from installed/skipped/pruned and format it with aligned tags and optional colors.

    Format of input is: "path [action]" or "path [action, dry-run]"
    """
    match = re.search(r"^(.*?) \[([^\]]+)\]$", item)
    if not match:
        return item

    path = match.group(1).strip()
    action_part = match.group(2).strip()

    parts = [p.strip() for p in action_part.split(",")]
    action = parts[0]
    dry_run = "dry-run" in parts

    tag = ""
    color = ""

    if action == "install":
        tag = "[added    ]"
        color = "green"
    elif action == "overwrite":
        tag = "[overwrite]"
        color = "red"
    elif action == "chmod":
        tag = "[chmod    ]"
        color = "cyan"
    elif action == "already current":
        tag = "[no change]"
        color = "yellow"
    elif action in ("git rm", "rm"):
        tag = "[removed  ]"
        color = "red"
    else:
        # Fallback
        cleaned = action[:9]
        padded = cleaned.ljust(9)
        tag = f"[{padded}]"
        color = "gray"

    styled_tag = term.colorize(tag, color, "bold") if color else tag
    suffix = " (dry-run)" if dry_run else ""
    return f"{styled_tag} {path}{suffix}"


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
    term = Term(color=False if plan.no_color else None)

    mode = "DRY RUN" if plan.dry_run else "COMPLETE"
    print(f"Agent workflows installer: {mode}")
    print(f"Version: {read_version(plan.source_root)}")
    print(f"Repository root: {plan.repo_root}")
    print(f"Source: {plan.source_root}")
    print(
        f"Git: {'staging changes (no commit)' if use_git else 'not a git repo; filesystem only'}"
    )
    print()

    if migrated:
        print("Legacy layout migrated (pre-restructure repo):")
        for item in migrated:
            print(f"  - {item}")
        print()

    print("Installed or updated:")
    for item in installed or ["None"]:
        if item == "None":
            print(f"  - {item}")
        else:
            print(format_output_item(item, term))
    print()
    print("Skipped:")
    for item in skipped or ["None"]:
        if item == "None":
            print(f"  - {item}")
        else:
            print(format_output_item(item, term))
    print()
    if plan.prune:
        print("Pruned (stale framework files):")
        for item in pruned or ["None"]:
            if item == "None":
                print(f"  - {item}")
            else:
                print(format_output_item(item, term))
    else:
        print("Pruned: disabled by --no-prune")
    print()
    print(f"AGENTS.md: {agents_status}")
    print(f"Gitignore (workflow-artifacts): {gitignore_status}")
    print(f"Gitignore (installer backups): {backups_ignore_status}")

    if (
        use_git
        and not plan.dry_run
        and (installed or pruned or backups_ignore_status.startswith("added"))
    ):
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
        updated = any(
            "[install]" in i or "[overwrite]" in i or "migrated" in i.lower()
            for i in (installed + pruned + migrated)
        )
        print()
        if updated:
            print("NEXT STEP - the framework changed; re-run setup-repo to re-check")
            print(
                "best-practice CONFORMANCE (it detects drift and only proposes gaps):"
            )
        else:
            print("NEXT STEP - set up this repo for best practices and security:")
        print("  - OpenCode or Claude Code: run  /setup-repo")
        print("  - Cursor / Codex / Antigravity / VS Code agents / any other agent:")
        print(f"    tell the agent:  Read and execute {setup.body}")
        print(
            "  (Guided + idempotent: it asks before each change, is safe to re-run as a"
        )
        print("   conformance check, and stages changes without committing.)")


def remove_agents_pointer(repo_root: Path, use_git: bool) -> str:
    """Remove the managed AGENTS pointer block; leave the rest of the file untouched.

    Only strips a single well-formed BEGIN..END block (the same fail-safe discipline as
    update_agents_pointer). Returns a human-readable status string.
    """

    rel = resolve_agents_file(repo_root)
    agents_path = repo_root / rel
    if not agents_path.is_file():
        return f"{rel} absent (no pointer to remove)"
    existing = agents_path.read_text(encoding="utf-8")
    begins = existing.count(AGENTS_BEGIN)
    ends = existing.count(AGENTS_END)
    well_formed = (
        begins == 1
        and ends == 1
        and existing.find(AGENTS_BEGIN) < existing.find(AGENTS_END)
    )
    if not well_formed:
        return f"{rel} pointer not found (nothing removed)"

    new_text = re.sub(
        re.escape(AGENTS_BEGIN) + r".*?" + re.escape(AGENTS_END),
        "",
        existing,
        count=1,
        flags=re.DOTALL,
    )
    # Tidy: collapse the blank hole left behind, keep a trailing newline.
    new_text = re.sub(r"\n{3,}", "\n\n", new_text).rstrip("\n") + "\n"
    agents_path.write_text(new_text, encoding="utf-8")
    if use_git and git_is_tracked(repo_root, rel):
        git_add_optional(repo_root, rel)
    return f"removed pointer block from {rel}"


def _uninstall_remove(repo_root: Path, rel: str, use_git: bool) -> None:
    """Remove a framework path for uninstall: `git rm -rf` when tracked/staged, else FS.

    Uses -f so a path that is STAGED but not yet committed (the normal post-install state,
    since the installer stages without committing) is removed cleanly; `git rm` without
    -f refuses those. Falls back to filesystem removal for untracked paths.
    """

    target = repo_root / rel
    if not target.exists():
        return
    if use_git and git_is_tracked(repo_root, rel):
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rm", "-rf", "--quiet", "--", rel],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        # Fall through to filesystem removal if git refused for any reason.
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def uninstall_repo(repo_root: Path, use_git: bool) -> list[str]:
    """Remove the framework from a repo: .agents/workflows/, our shims, the AGENTS block.

    Stages deletions (git rm -f when tracked/staged) and never commits. Never touches user
    content outside the framework namespace. Returns human-readable actions taken.
    """

    actions: list[str] = []

    # 1. The workflow tree.
    if (repo_root / WORKFLOWS_DIR).is_dir():
        _uninstall_remove(repo_root, WORKFLOWS_DIR, use_git)
        actions.append(f"removed {WORKFLOWS_DIR}/")

    # 2. The generated command shims (only the .md files we generate).
    for shim_dir in COMMAND_SHIM_DIRS:
        d = repo_root / shim_dir
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            rel = path.relative_to(repo_root).as_posix()
            _uninstall_remove(repo_root, rel, use_git)
            actions.append(f"removed {rel}")

    # 3. The managed AGENTS pointer block (leaves the user's own AGENTS prose intact).
    actions.append(remove_agents_pointer(repo_root, use_git))

    return actions


# --------------------------------------------------------------------------------------
# Deterministic setup artifacts (IPD-2 Batch E / Goal 8). These are the fixed-template,
# always-the-same scaffolding the CLI creates on install so a repo is useful out of the
# box. The STACK-TAILORED / judgment parts (.gitignore, stack CI, the lifecycle contract
# prose) stay with the LLM /setup-repo workflow. Artifacts are created NO-CLOBBER: an
# existing target file is never overwritten (R-2); the AGENTS pointer is handled
# separately by update_agents_pointer.
# --------------------------------------------------------------------------------------

PLANS_DIR = ".agents/plans"
PLAN_LIFECYCLE_SUBDIRS = (
    "pending",
    "executed",
    "superseded",
    "not-executed",
    "reusable",
)
GITLEAKSIGNORE_FILE = ".gitleaksignore"
SECRET_SCAN_CI = ".github/workflows/secret-scan.yml"

_GITLEAKSIGNORE_TEMPLATE = """\
# gitleaks false-positive baseline (created by agent-workflows).
#
# gitleaks ignores findings by FINGERPRINT, printed in its report as:
#   <commit-sha>:<file-path>:<rule-id>:<line-number>
# Paste a confirmed false positive's fingerprint on its own line to suppress it.
# Do NOT suppress a real secret: rotate it, then purge it from history.
#
# This baseline starts empty. Example (commented out):
# 0a1b2c3d4e5f6a7b8c9d:tests/fixtures/sample.env:generic-api-key:12
"""

_SECRET_SCAN_CI_TEMPLATE = """\
name: secret-scan

# Committed-secret scan on push and PR using gitleaks (created by agent-workflows).
# False positives are managed via the committed .gitleaksignore baseline at the repo root.

on:
  push:
    branches: [main, master]
  pull_request:

permissions:
  contents: read

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          # fetch-depth: 0 so gitleaks scans full history, not just HEAD - a secret
          # removed from HEAD but still in history is the dangerous case.
          fetch-depth: 0

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_ENABLE_UPLOAD_ARTIFACT: "false"
"""


def _create_if_absent(
    repo_root: Path, rel: str, content: str, use_git: bool, created: list[str]
) -> None:
    """Write ``content`` to ``rel`` ONLY if it does not already exist (no-clobber, R-2).

    Stages the new file when tracked-able. An existing file (the user's own) is left
    untouched and recorded as skipped-existing.
    """

    target = repo_root / rel
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    if use_git:
        git_add_optional(repo_root, rel)
    created.append(rel)


def ensure_workflow_artifacts_readme(
    plan: InstallPlan,
    use_git: bool,
    installed: list[str],
    skipped: list[str],
) -> None:
    """Create a default README.md in workflow-artifacts/ if it doesn't already exist."""

    artifacts_dir = plan.repo_root / "workflow-artifacts"
    readme_path = artifacts_dir / "README.md"
    rel_path = "workflow-artifacts/README.md"

    if readme_path.is_file():
        skipped.append(f"{rel_path} [already current]")
        return

    # Read the template from source root.
    template_path = plan.source_root / "templates" / "workflow-artifacts-README.md"
    try:
        readme_content = template_path.read_text(encoding="utf-8")
    except OSError:
        readme_content = (
            "# Workflow Run Artifacts\n\n"
            "This directory contains review records, verification evidence, and audit logs "
            "generated by AI agent workflows (such as release reviews or plan reviews).\n\n"
            "## ⚠️ Git Guidelines\n"
            "* **DO NOT gitignore this folder.**\n"
            "* These records represent the review and approval history of this repository "
            "and are intended to be committed to git alongside your code changes.\n"
        )

    if plan.dry_run:
        installed.append(f"{rel_path} [install, dry-run]")
        return

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(readme_content, encoding="utf-8")
    if use_git:
        git_run(plan.repo_root, ["add", "--", rel_path])
    installed.append(f"{rel_path} [install]")


# Category-1 (user-owned) directory READMEs generated no-clobber from templates. The
# `.agents/` root and `.agents/plans/` overview use fixed template names; each lifecycle
# bucket uses `plans-<bucket>-README.md`. Buckets are driven by PLAN_LIFECYCLE_SUBDIRS so
# they cannot drift from the dirs create_setup_artifacts scaffolds.
_PLANS_README_TARGETS = (
    (".agents/README.md", "agents-README.md"),
    (f"{PLANS_DIR}/README.md", "plans-README.md"),
)


def ensure_plans_readmes(
    plan: InstallPlan,
    use_git: bool,
    installed: list[str],
    skipped: list[str],
) -> None:
    """Create a README.md in `.agents/`, `.agents/plans/`, and each lifecycle bucket.

    No-clobber (a user's own README is never overwritten), staged, dry-run aware. Modeled
    on `ensure_workflow_artifacts_readme`. Templates live under the source
    `.agents/workflows/templates/`; a bucket with no template is skipped defensively.
    """

    targets = list(_PLANS_README_TARGETS)
    for bucket in PLAN_LIFECYCLE_SUBDIRS:
        targets.append((f"{PLANS_DIR}/{bucket}/README.md", f"plans-{bucket}-README.md"))

    for rel_path, template_name in targets:
        readme_path = plan.repo_root / rel_path
        if readme_path.is_file():
            skipped.append(f"{rel_path} [already current]")
            continue
        template_path = plan.source_root / "templates" / template_name
        try:
            content = template_path.read_text(encoding="utf-8")
        except OSError:
            # No template shipped for this target; skip rather than invent content.
            continue
        if plan.dry_run:
            installed.append(f"{rel_path} [install, dry-run]")
            continue
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text(content, encoding="utf-8")
        if use_git:
            git_add_optional(plan.repo_root, rel_path)
        installed.append(f"{rel_path} [install]")


def create_setup_artifacts(
    repo_root: Path, use_git: bool, dry_run: bool = False
) -> list[str]:
    """Create the deterministic setup artifacts in a target repo (no-clobber, idempotent).

    Creates (only when absent): the plan lifecycle dirs with .gitkeep, a .gitleaksignore
    baseline, and the secret-scan CI workflow. Returns the list of created paths (empty on
    a re-run where everything already exists, so it is quiet and idempotent).

    NOTE: the AGENTS pointer is created by update_agents_pointer during install; the
    stack-tailored .gitignore/CI stay with the LLM /setup-repo workflow.
    """

    created: list[str] = []
    if dry_run:
        # Report what WOULD be created without writing.
        for sub in PLAN_LIFECYCLE_SUBDIRS:
            keep = f"{PLANS_DIR}/{sub}/.gitkeep"
            if not (repo_root / keep).exists():
                created.append(keep + " [dry-run]")
        for rel in (GITLEAKSIGNORE_FILE, SECRET_SCAN_CI):
            if not (repo_root / rel).exists():
                created.append(rel + " [dry-run]")
        return created

    for sub in PLAN_LIFECYCLE_SUBDIRS:
        _create_if_absent(
            repo_root, f"{PLANS_DIR}/{sub}/.gitkeep", "", use_git, created
        )
    _create_if_absent(
        repo_root, GITLEAKSIGNORE_FILE, _GITLEAKSIGNORE_TEMPLATE, use_git, created
    )
    _create_if_absent(
        repo_root, SECRET_SCAN_CI, _SECRET_SCAN_CI_TEMPLATE, use_git, created
    )
    return created


def read_installed_version(repo_root: Path) -> str | None:
    """Return the framework VERSION installed in ``repo_root``, or None if not installed."""

    vpath = repo_root / WORKFLOWS_DIR / VERSION_FILE
    try:
        value = vpath.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def install_into_repo(
    repo_root: Path,
    source_root: Path,
    *,
    dry_run: bool = False,
    backup: bool = True,
    prune: bool = True,
) -> dict:
    """Install/update the framework into a single repo. Returns a structured result.

    This is the multi-repo-friendly entry the CLI's `install all` drives per repo, so a
    failure in one repo can be isolated and reported without aborting the batch. It reuses
    the exact same engine steps as the single-repo `run()` path.
    """

    plan = InstallPlan(
        source_root=source_root,
        repo_root=repo_root,
        dry_run=dry_run,
        backup=backup,
        prune=prune,
    )
    use_git = git_available(plan.repo_root)
    workflows = parse_manifest(plan.source_root)
    body_members = collect_source_members(plan.source_root)
    shim_members = generate_shim_members(workflows, plan.source_root)

    migrate_legacy_layout(plan, use_git)
    installed, skipped, _ = install_all(plan, body_members, shim_members, use_git)
    pruned = prune_stale(plan, body_members, shim_members, use_git)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    agents_status = update_agents_pointer(plan, use_git, timestamp)
    gitignore_status = check_gitignore(plan)
    backups_ignore_status = ensure_backups_gitignored(plan, use_git)
    ensure_workflow_artifacts_readme(plan, use_git, installed, skipped)
    artifacts = create_setup_artifacts(repo_root, use_git, dry_run=dry_run)
    ensure_plans_readmes(plan, use_git, installed, skipped)

    newly_created = [
        item.rsplit(" [", 1)[0] for item in installed if item.endswith(" [install]")
    ]
    save_created_files_record(plan.repo_root, timestamp, newly_created)
    prune_old_backups(plan.repo_root)

    return {
        "repo": repo_root,
        "installed": installed,
        "skipped": skipped,
        "pruned": pruned,
        "artifacts": artifacts,
        "use_git": use_git,
        "version": read_installed_version(repo_root),
        "agents_status": agents_status,
        "gitignore_status": gitignore_status,
        "backups_ignore_status": backups_ignore_status,
    }


def run(args: argparse.Namespace) -> int:
    """Execute an install run from an already-parsed args namespace.

    Split out of `main()` so the packaged CLI (`agent_workflows.cli`) and the deprecated
    root shim can both drive the exact same behavior from a namespace they construct,
    without re-reading `sys.argv`.
    """

    if args.version:
        # Report the framework version and exit; do not touch any repo.
        print(read_version(resolve_source_root(args.source_root)))
        return 0

    repo_roots = getattr(args, "repo_roots", None)
    if not repo_roots:
        # Check if the caller supplied repo_root directly (e.g. from cli.py)
        repo_root = getattr(args, "repo_root", None)
        if repo_root is not None:
            repo_roots = [repo_root]
        else:
            repo_roots = [Path.cwd()]

    if getattr(args, "undo", False):
        returncode = 0
        for root in repo_roots:
            res = run_rollback(
                root.expanduser().resolve(), getattr(args, "no_color", False)
            )
            if res != 0:
                returncode = res
        return returncode

    returncode = 0
    import copy

    for root in repo_roots:
        repo_args = copy.copy(args)
        repo_args.repo_root = root

        plan = build_install_plan(repo_args)

        if len(repo_roots) > 1:
            term = Term(plan.no_color)
            print(term.colorize("\n========================================", "bold"))
            print(term.colorize(f"Target Repo: {plan.repo_root}", "bold"))
            print(term.colorize("========================================", "bold"))

        if plan.diff:
            workflows = parse_manifest(plan.source_root)
            body_members = collect_source_members(plan.source_root)
            shim_members = generate_shim_members(workflows, plan.source_root)
            show_install_diffs(plan, body_members, shim_members)
            continue

        try:
            ensure_repo_root(plan.repo_root)
        except SystemExit as exc:
            print(f"Error: {exc}", file=sys.stderr)
            returncode = 1
            continue

        # Run Git Diagnostics pre-flight checks
        if not run_git_diagnostics(plan):
            returncode = 1
            continue

        use_git = git_available(plan.repo_root)

        workflows = parse_manifest(plan.source_root)
        body_members = collect_source_members(plan.source_root)
        shim_members = generate_shim_members(workflows, plan.source_root)

        run_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        migrated = migrate_legacy_layout(plan, use_git)
        installed, skipped, _ = install_all(plan, body_members, shim_members, use_git)
        pruned = prune_stale(plan, body_members, shim_members, use_git)
        agents_status = update_agents_pointer(plan, use_git, run_timestamp)
        gitignore_status = check_gitignore(plan)
        backups_ignore_status = ensure_backups_gitignored(plan, use_git)
        ensure_workflow_artifacts_readme(plan, use_git, installed, skipped)
        ensure_plans_readmes(plan, use_git, installed, skipped)
        artifacts = create_setup_artifacts(
            plan.repo_root, use_git, dry_run=plan.dry_run
        )

        newly_created = [
            item.rsplit(" [", 1)[0] for item in installed if item.endswith(" [install]")
        ]
        save_created_files_record(plan.repo_root, run_timestamp, newly_created)
        prune_old_backups(plan.repo_root)

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
        if artifacts:
            print()
            print(
                "Setup artifacts created (staged; run /setup-repo for stack-tailored setup):"
            )
            for item in artifacts:
                print(f"  - {item}")

        prompt_and_run_commit(
            plan=plan,
            installed=installed,
            pruned=pruned,
            agents_status=agents_status,
            backups_ignore_status=backups_ignore_status,
            use_git=use_git,
            artifacts=artifacts,
        )
    return 0


def main(argv=None) -> int:
    """Parse args (from argv or sys.argv) and run an install. Back-compat entry point."""

    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
