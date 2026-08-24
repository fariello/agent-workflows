"""Command surface declaration, leaf inventory, and standalone script classification.

awcliux Order 04 (`10jpsa`) E-03 / V-03.

Declares the exhaustive inventory of all CLI parser leaves, command classes,
human presentation recipes, agent record kinds, mutation authorization gates,
legacy format flags, and exit contracts across the agent-workflows (`aw`) CLI surface.

Consumable by the Order 05 (`e8hu4s`) conformance test harness to fail CI on any
undeclared or untested leaf.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple


@dataclass(frozen=True)
class CommandDeclaration:
    """Normative contract declaration for a single CLI command or parser leaf."""

    command: str  # Canonical command string (e.g. "status", "backlog set", "ipd lint")
    command_class: (
        str  # "read", "check", "mutation", "preview", "family", "bare", "alias"
    )
    human_recipe: str  # "status", "check", "preview", "table", "board", "list", "text", "help", "detail"
    agent_record_kind: str  # "result", "summary", "item", "error", "raw_path"
    mutation_gate: (
        str  # "none", "dry_run_default", "confirmation", "auth_floor", "policy"
    )
    empty_error_renderer: (
        str  # "shared_empty_result", "renderer_boundary", "delegated"
    ) = "renderer_boundary"
    legacy_flags: Tuple[str, ...] = field(default_factory=tuple)
    exit_contract: Tuple[int, ...] = (0, 1, 2)
    migrated: bool = True
    in_boundary: bool = True
    canonical_command: Optional[str] = None  # If an alias, the canonical target command


@dataclass(frozen=True)
class StandaloneScriptDeclaration:
    """Classification for non-CLI standalone installer scripts in the repository."""

    name: str
    in_boundary: bool
    classification: str  # "in_boundary" | "out_of_boundary"
    rationale: str


# --------------------------------------------------------------------------------------------------
# Standalone Scripts Classification (Order 04 Scope Check & E-03)
# --------------------------------------------------------------------------------------------------

STANDALONE_SCRIPTS: Tuple[StandaloneScriptDeclaration, ...] = (
    StandaloneScriptDeclaration(
        name="install-workflows.py",
        in_boundary=False,
        classification="out_of_boundary",
        rationale=(
            "Deprecated root-level Python wrapper shim delegating to engine.main() "
            "for legacy compatibility. Canonical entrypoint is 'aw install'."
        ),
    ),
    StandaloneScriptDeclaration(
        name="install-workflows.sh",
        in_boundary=False,
        classification="out_of_boundary",
        rationale=(
            "Deprecated root-level Shell wrapper shim delegating to install-workflows.py. "
            "Canonical entrypoint is 'aw install'."
        ),
    ),
)


# --------------------------------------------------------------------------------------------------
# Comprehensive Command Surface Inventory (All 78 leaves)
# --------------------------------------------------------------------------------------------------

COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
    # --- Bare Root & Aliases ---
    CommandDeclaration(
        command="aw",
        command_class="bare",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--no-color",),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="att",
        command_class="alias",
        human_recipe="board",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        legacy_flags=("--agent", "--format"),
        canonical_command="attention",
    ),
    CommandDeclaration(
        command="todo",
        command_class="alias",
        human_recipe="board",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        legacy_flags=("--agent",),
        canonical_command="attention",
    ),
    CommandDeclaration(
        command="sanitize",
        command_class="alias",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="delegated",
        legacy_flags=("--agent", "--fix", "--yes", "--dry-run"),
        canonical_command="check-local-leaks",
    ),
    # --- Status / Context / Discovery / Inspection Reads ---
    CommandDeclaration(
        command="status",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="list-repos",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="context",
        command_class="read",
        human_recipe="detail",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--json", "--agent", "--public"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="path",
        command_class="read",
        human_recipe="text",
        agent_record_kind="raw_path",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent",),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="show",
        command_class="read",
        human_recipe="detail",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="record-history",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="doctor",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--include-untracked", "--include-executed", "--all"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="attention",
        command_class="read",
        human_recipe="board",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--format", "--check", "--agent", "--all", "--long"),
        exit_contract=(0, 1, 2),
    ),
    # --- Project Family ---
    CommandDeclaration(
        command="project status",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="project attach",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--yes", "--dry-run"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="project move",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--yes", "--dry-run"),
        exit_contract=(0, 2),
    ),
    # --- Storage Family ---
    CommandDeclaration(
        command="storage status",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage preflight",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--json",),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage init",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--no-git", "--acknowledge-remote", "--yes", "--dry-run"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage attach",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--companion-dir",
            "--classes",
            "--acknowledge-remote",
            "--yes",
            "--dry-run",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage detach",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--dry-run",),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage move",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--new-dir", "--dry-run"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="storage reattach",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--companion-dir", "--dry-run"),
        exit_contract=(0, 1, 2),
    ),
    # --- Config & Repos Management ---
    CommandDeclaration(
        command="config exclude add",
        command_class="mutation",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="config exclude list",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="config exclude rm",
        command_class="mutation",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="exclude",
        command_class="mutation",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="include",
        command_class="mutation",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        exit_contract=(0, 2),
    ),
    # --- Noun-Verb Grammar Operations ---
    CommandDeclaration(
        command="check",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="find",
        command_class="read",
        human_recipe="table",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--json", "--agent"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="search",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--json", "--agent", "--line-numbers"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="index",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--json", "--agent", "--check", "--limit"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="rename",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--slug", "--order", "--apply", "--no-refs", "--json", "--agent"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="group",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--set",
            "--order",
            "--rename",
            "--apply",
            "--no-refs",
            "--json",
            "--agent",
        ),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="archive",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--keep", "--apply"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="set",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--message",
            "--by-human",
            "--gate-kind",
            "--gate-ref",
            "--gate-summary",
            "--blocks-release",
            "--dry-run",
            "--json",
            "--agent",
        ),
        exit_contract=(0, 1, 2),
    ),
    # --- Lifecycle, Setup & Migration Mutations ---
    CommandDeclaration(
        command="install",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--dry-run",
            "--no-backup",
            "--no-prune",
            "-y",
            "--yes",
            "--preset",
            "--delivery-mode",
            "--records-backend",
            "--companion-dir",
            "--to-aw",
            "--keep-legacy",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="setup",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--root",
            "--recursive",
            "-y",
            "--yes",
            "--preset",
            "--delivery-mode",
            "--records-backend",
            "--companion-dir",
            "--to-aw",
            "--keep-legacy",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="uninstall",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("-y", "--yes", "--dry-run", "--deep", "--force"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="normalize-lanes",
        command_class="mutation",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--dir",),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="migrate-layout",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--config",
            "--target-backend",
            "--root",
            "--output",
            "--dry-run",
            "--apply",
            "--confirm",
            "--fault-injection",
            "--leftovers",
            "--rename-to-grammar",
            "--json",
            "-y",
            "--yes",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="check-local-leaks",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--history",
            "--max-commits",
            "--wheel",
            "--warn",
            "--staged",
            "--agent",
            "--fix",
            "--yes",
            "--dry-run",
            "--configure",
        ),
        exit_contract=(0, 1, 2),
    ),
    # --- IPD / Plans Family ---
    CommandDeclaration(
        command="ipd board",
        command_class="read",
        human_recipe="board",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--status", "--agent"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="ipd lint",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--phase", "--all", "--legacy", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="ipd scaffold",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--kind",
            "--title",
            "--path",
            "--set",
            "--order",
            "--legacy-name",
            "--author",
            "--apply",
            "--overwrite",
        ),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="ipd sync",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--apply",),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        # ipdgates Order xjbvu2: fail-closed execution-start receipt. A check-class gate: it
        # runs pre-execution lint and writes only a LOCAL, gitignored receipt (mutates no tracked
        # file), so it carries no tracked-tree mutation gate. Exit 0 ok / 1 findings / 2 cannot-run.
        command="ipd begin",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--actor", "--dir", "--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        # ipdgates Order v7e88a: atomic terminal transaction. A mutation-class verb (moves the plan,
        # refreshes the owned index, creates a path-scoped lifecycle commit) gated dry-run-by-default
        # (--apply performs it). Exit 0 ok / 1 refusal (gate/scope) / 2 cannot-run.
        command="ipd finalize",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--actor",
            "--message",
            "--apply",
            "--scope-reason",
            "--scope-ack",
            "--dir",
            "--agent",
            "--json",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="ipd set",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--message", "--by-human", "--dry-run", "--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    # --- Workflow Family ---
    CommandDeclaration(
        command="workflow validate",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="workflow compile",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--apply", "--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="workflow check-generated",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    # --- Run Ledger Family ---
    CommandDeclaration(
        command="run show",
        command_class="read",
        human_recipe="detail",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="run evidence",
        command_class="read",
        human_recipe="detail",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="run verify-ledger",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="run start",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--actor", "--step", "--agent", "--json"),
        exit_contract=(0, 2, 3, 5, 6),
    ),
    CommandDeclaration(
        command="run next",
        command_class="read",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--agent", "--json"),
        exit_contract=(0, 3),
    ),
    CommandDeclaration(
        command="run record",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--workflow",
            "--actor",
            "--step",
            "--state",
            "--agent",
            "--json",
        ),
        exit_contract=(0, 2, 3, 5, 6),
    ),
    CommandDeclaration(
        command="run resume",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--agent", "--json"),
        exit_contract=(0, 3),
    ),
    CommandDeclaration(
        command="run cancel",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--actor", "--reason", "--agent", "--json"),
        exit_contract=(0, 5, 6),
    ),
    CommandDeclaration(
        command="run status",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--agent", "--json"),
        exit_contract=(0, 1, 3, 5),
    ),
    CommandDeclaration(
        command="run finalize",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--workflow", "--actor", "--agent", "--json"),
        exit_contract=(0, 1, 4, 6),
    ),
    # --- Research Family ---
    CommandDeclaration(
        command="research new",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--kind",
            "--slug",
            "--summary",
            "--set",
            "--model",
            "--topic",
            "--date",
            "--apply",
            "--overwrite",
        ),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research new-comparison",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--set",
            "--slug",
            "--models",
            "--summary",
            "--topic",
            "--date",
            "--apply",
            "--overwrite",
        ),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research set-assign",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--set", "--order", "--date", "--apply"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research mv",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--slug", "--kind", "--model", "--apply"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research check-refs",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent",),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="research index",
        command_class="mutation",
        human_recipe="list",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--check", "--limit", "--agent"),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="research find",
        command_class="read",
        human_recipe="table",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--id", "--set", "--topic", "--status"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research promote",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--to", "--apply"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="research check-miscategorized",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        exit_contract=(0, 1, 2),
    ),
    # --- Backlog Family ---
    CommandDeclaration(
        command="backlog new",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--summary",
            "--set",
            "--status",
            "--priority",
            "--kind",
            "--slug",
            "--gate-kind",
            "--gate-ref",
            "--body",
            "--apply",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="backlog set",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--status",
            "--message",
            "--gate-kind",
            "--gate-ref",
            "--blocks-release",
            "--dry-run",
            "--json",
            "--agent",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="backlog check",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent",),
        exit_contract=(0, 1, 2),
    ),
    # --- Specs Family & Spec Aliases ---
    CommandDeclaration(
        command="specs set",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--status",
            "--message",
            "--gate-kind",
            "--gate-ref",
            "--gate-summary",
            "--blocks-release",
            "--evidence",
            "--by-human",
            "--date",
            "--dry-run",
            "--json",
            "--agent",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="specs note",
        command_class="mutation",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--message", "--date"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="specs check",
        command_class="check",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent",),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="specs migrate",
        command_class="mutation",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--status",
            "--canonical",
            "--gate-kind",
            "--gate-ref",
            "--gate-summary",
            "--date",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="spec set",
        command_class="alias",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="delegated",
        canonical_command="specs set",
    ),
    CommandDeclaration(
        command="spec note",
        command_class="alias",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        canonical_command="specs note",
    ),
    CommandDeclaration(
        command="spec check",
        command_class="alias",
        human_recipe="check",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        canonical_command="specs check",
    ),
    CommandDeclaration(
        command="spec migrate",
        command_class="alias",
        human_recipe="text",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        canonical_command="specs migrate",
    ),
    # --- Prompts Family ---
    CommandDeclaration(
        command="prompts set",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="auth_floor",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--message", "--by-human", "--dry-run", "--json", "--agent"),
        exit_contract=(0, 1, 2),
    ),
)

_DECLARATION_INDEX: Dict[str, CommandDeclaration] = {
    decl.command: decl for decl in COMMAND_INVENTORY
}


# --------------------------------------------------------------------------------------------------
# Query and Discovery API (Consumable by Order 05 Conformance Harness)
# --------------------------------------------------------------------------------------------------


def get_all_declarations() -> Tuple[CommandDeclaration, ...]:
    """Return all declared command leaves."""
    return COMMAND_INVENTORY


def get_declaration(command_name: str) -> Optional[CommandDeclaration]:
    """Lookup a command declaration by its command path string."""
    return _DECLARATION_INDEX.get(command_name.strip())


def get_declared_leaves() -> Set[str]:
    """Return the set of all declared command leaf strings (excluding bare 'aw')."""
    return {decl.command for decl in COMMAND_INVENTORY if decl.command != "aw"}


def get_standalone_scripts() -> Tuple[StandaloneScriptDeclaration, ...]:
    """Return all standalone installer script classifications."""
    return STANDALONE_SCRIPTS


def discover_parser_leaves(
    parser: argparse.ArgumentParser, prefix: str = ""
) -> Set[str]:
    """Recursively extract all leaf command paths from an argparse.ArgumentParser tree."""
    leaves: Set[str] = set()
    subparsers_actions = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    if not subparsers_actions:
        leaf = prefix.strip()
        if leaf:
            leaves.add(leaf)
        return leaves

    for sa in subparsers_actions:
        for choice_name, subparser in sa.choices.items():
            full_name = f"{prefix} {choice_name}".strip()
            leaves.update(discover_parser_leaves(subparser, full_name))
    return leaves


def find_undeclared_leaves(parser: argparse.ArgumentParser) -> Set[str]:
    """Return any parser leaves that lack a contract declaration in COMMAND_INVENTORY."""
    parser_leaves = discover_parser_leaves(parser)
    declared = get_declared_leaves()
    return parser_leaves - declared
