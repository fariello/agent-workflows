"""Command-line entry point for agent-workflows (`agent-workflows` / `aw` / `agentwf`).

Verbs (spec OQ7): `install <dir>|all`, `setup`, `uninstall <dir>`, `list`, `status`.
There is intentionally NO `update` (install is idempotent) and NO `doctor` (its safety is
preflight-warn+confirm here; its readout is folded into `status`). Bare `aw` is a smart
default: run `setup` when unconfigured, else show `status` + hints.

The CLI (host-level, deterministic, multi-repo) COMPLEMENTS the LLM `/setup-repo` workflow
(in-agent, stack-tailored). After install/setup the CLI points the user at `/setup-repo`
for the judgment layer.

All output goes through `term.Term` for accessible, degrade-when-piped styling (AC-15).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__, config, discovery, engine, versioning
from .term import Term


# --------------------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    # A shared parent so --no-color works both before AND after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color (also honored via NO_COLOR).",
    )

    parser = argparse.ArgumentParser(
        prog="agent-workflows",
        description="Install and manage the agent-workflows framework across your repos.",
        parents=[common],
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"agent-workflows {__version__}",
        help="Print the agent-workflows version and exit.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_install = sub.add_parser(
        "install",
        parents=[common],
        help="Install or update the framework in a repo (idempotent); 'install all' does every configured repo.",
    )
    p_install.add_argument(
        "targets",
        nargs="*",
        default=None,
        help="Repo dirs (default: cwd), or 'all' for every configured repo.",
    )
    p_install.add_argument(
        "--source",
        dest="source_root",
        default=None,
        help="Path to the source .agents/workflows (dev/override).",
    )
    p_install.add_argument(
        "--dry-run", action="store_true", help="Show actions without writing."
    )
    p_install.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up before overwrite/prune.",
    )
    p_install.add_argument(
        "--no-prune", action="store_true", help="Do not remove stale framework files."
    )
    p_install.add_argument(
        "-y", "--yes", action="store_true", help="Skip preflight confirmations."
    )

    p_setup = sub.add_parser(
        "setup", parents=[common], help="Guided first-run setup wizard."
    )
    p_setup.add_argument(
        "--root",
        dest="roots",
        action="append",
        default=None,
        help="A search root to discover repos under (repeatable). "
        "Non-interactive when supplied.",
    )
    p_setup.add_argument(
        "--recursive", action="store_true", help="Discover repos recursively."
    )
    p_setup.add_argument(
        "-y", "--yes", action="store_true", help="Install without per-repo prompts."
    )
    p_setup.add_argument(
        "--source", dest="source_root", default=None, help=argparse.SUPPRESS
    )

    p_uninstall = sub.add_parser(
        "uninstall",
        parents=[common],
        help="Remove the framework from a repo (asks first).",
    )
    p_uninstall.add_argument(
        "target", help="Repo directory to remove the framework from."
    )
    p_uninstall.add_argument(
        "-y", "--yes", action="store_true", help="Skip the confirmation prompt."
    )
    p_uninstall.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed/preserved; change nothing.",
    )
    p_uninstall.add_argument(
        "--deep",
        action="store_true",
        help="Also remove the .agents/ scaffolding (plans/docs/prompts/comms, etc.); "
        "normally offered interactively.",
    )
    p_uninstall.add_argument(
        "--force",
        action="store_true",
        help="Also remove files you have edited (drifted) instead of preserving them.",
    )

    p_list = sub.add_parser(
        "list",
        parents=[common],
        help="List configured/discovered repos and their currency.",
    )
    p_list.add_argument(
        "--recursive", action="store_true", help="Discover repos recursively."
    )

    sub.add_parser(
        "status", parents=[common], help="Show environment + currency summary."
    )

    p_plans = sub.add_parser(
        "plans",
        parents=[common],
        help="Show a board of plan/IPD readiness Status, grouped by lifecycle.",
    )
    p_plans.add_argument(
        "dir",
        nargs="?",
        default=None,
        help="Repo root to read (default: current directory).",
    )
    p_plans.add_argument(
        "--pending",
        action="store_true",
        help="Only show plans in the pending/ directory.",
    )
    p_plans.add_argument(
        "--status",
        dest="status_filter",
        default=None,
        help="Only show one readiness status.",
    )
    p_plans.add_argument(
        "--write-index",
        action="store_true",
        help="(Re)generate .agents/plans/STATUS.md instead of printing.",
    )

    # The plans manifest verbs are separate top-level parsers (`plans-index`, `plans-find`) to avoid
    # colliding the `plans <dir>` positional with an argparse subparser; a thin `aw plans index` /
    # `aw plans find` alias is routed in `_dispatch` before the main parser runs (see below).
    p_plans_index = sub.add_parser(
        "plans-index",
        parents=[common],
        help="Regenerate .agents/plans/INDEX.json + a browse-by-Set INDEX.md; --check fails on drift. Alias: 'plans index'.",
    )
    p_plans_index.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_plans_index.add_argument(
        "--check",
        action="store_true",
        help="Fail (nonzero) on drift instead of regenerating.",
    )
    p_plans_index.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Browse-by-Set view size (default 40 Sets).",
    )
    p_plans_index.add_argument(
        "--agent",
        action="store_true",
        help="Machine output for --check: tab-separated records.",
    )
    p_plans_find = sub.add_parser(
        "plans-find",
        parents=[common],
        help="Query the plans manifest by --id/--set/--status/--disposition. Alias: 'plans find'.",
    )
    p_plans_find.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_plans_find.add_argument("--id", default=None, help="Filter by plan <id6>.")
    p_plans_find.add_argument(
        "--set", dest="set", default=None, help="Filter by Set id."
    )
    p_plans_find.add_argument(
        "--status", default=None, help="Filter by readiness status."
    )
    p_plans_find.add_argument(
        "--disposition", default=None, help="Filter by disposition dir."
    )

    p_plans_setassign = sub.add_parser(
        "plans-set-assign",
        parents=[common],
        help="Group plans into a Set (Set/Order metadata; --rename to cluster). Alias: 'plans set-assign'.",
    )
    p_plans_setassign.add_argument(
        "ids", nargs="+", help="One or more plan <id6> tokens, in order."
    )
    p_plans_setassign.add_argument("--set", dest="set", required=True, help="Set id.")
    p_plans_setassign.add_argument(
        "--order", type=int, default=None, help="Starting Order (default 0)."
    )
    p_plans_setassign.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_plans_setassign.add_argument(
        "--rename", action="store_true", help="Also rename to the clustering grammar."
    )
    p_plans_setassign.add_argument(
        "--apply",
        action="store_true",
        help="Perform the changes (default is preview only).",
    )
    p_plans_mv = sub.add_parser(
        "plans-mv",
        parents=[common],
        help="Rename/re-slug one plan to the clustering grammar, keeping Id. Alias: 'plans mv'.",
    )
    p_plans_mv.add_argument("id", help="The plan <id6>.")
    p_plans_mv.add_argument("--slug", default=None, help="New slug.")
    p_plans_mv.add_argument("--set", dest="set", default=None, help="New Set id.")
    p_plans_mv.add_argument("--order", type=int, default=None, help="New Order.")
    p_plans_mv.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_plans_mv.add_argument(
        "--apply",
        action="store_true",
        help="Perform the rename (default is preview only).",
    )

    p_plans_archive = sub.add_parser(
        "plans-archive",
        parents=[common],
        help="Deep-shelve terminal plans into weekly shards (targeted or an aged sweep). Alias: 'plans archive'.",
    )
    p_plans_archive.add_argument(
        "target",
        nargs="?",
        default=None,
        help="A plan <id6> or Set id (omit for a sweep).",
    )
    p_plans_archive.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_plans_archive.add_argument(
        "--apply",
        action="store_true",
        help="Perform the moves (default is preview only).",
    )

    p_ipd = sub.add_parser(
        "ipd",
        parents=[common],
        help="IPD tooling (structure/state). 'ipd lint' deterministically checks an IPD.",
    )
    ipd_sub = p_ipd.add_subparsers(dest="ipd_command")
    p_ipd_lint = ipd_sub.add_parser(
        "lint",
        parents=[common],
        help="Deterministically lint an IPD's structure/state (read-only; no model/network/writes).",
    )
    p_ipd_lint.add_argument(
        "path",
        nargs="?",
        default=None,
        help="IPD file to lint (or a repo root with --all).",
    )
    p_ipd_lint.add_argument(
        "--phase",
        default="author",
        help="Lint checkpoint: author | review-finalize | pre-execution | pre-transition | post-transition.",
    )
    p_ipd_lint.add_argument(
        "--all",
        action="store_true",
        help="Lint every plan under .agents/plans and report a per-disposition inventory.",
    )
    p_ipd_lint.add_argument(
        "--legacy",
        action="store_true",
        help="Run the reduced legacy checks against a grandfathered terminal file.",
    )
    p_ipd_lint.add_argument(
        "--agent",
        action="store_true",
        help="Machine output: one tab-separated record per finding or disposition; no prose.",
    )

    p_ipd_scaffold = ipd_sub.add_parser(
        "scaffold",
        parents=[common],
        help="Write a new conformant IPD skeleton (dry-run by default; --apply to write).",
    )
    p_ipd_scaffold.add_argument("--kind", required=True, help="child or orchestrator.")
    p_ipd_scaffold.add_argument(
        "--title", required=True, help="IPD title (after the H1 'IPD: ')."
    )
    p_ipd_scaffold.add_argument("--path", required=True, help="Destination file path.")
    p_ipd_scaffold.add_argument(
        "--set", dest="set", default=None, help="Ordered-Set id (with --order)."
    )
    p_ipd_scaffold.add_argument(
        "--order",
        type=int,
        default=None,
        help="Order in the Set (0 for orchestrator, >=1 for child).",
    )
    p_ipd_scaffold.add_argument(
        "--author", default=None, help="Author (or set AW_IPD_AUTHOR)."
    )
    p_ipd_scaffold.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
    )
    p_ipd_scaffold.add_argument(
        "--overwrite", action="store_true", help="Allow overwriting an existing path."
    )

    p_ipd_sync = ipd_sub.add_parser(
        "sync",
        parents=[common],
        help="Assign ids to new E-NEW leaves + append V skeletons + advance the watermark (dry-run by default).",
    )
    p_ipd_sync.add_argument("path", help="IPD file to sync.")
    p_ipd_sync.add_argument(
        "--apply",
        action="store_true",
        help="Write the change (default is preview only).",
    )

    p_research = sub.add_parser(
        "research",
        parents=[common],
        help="Research artifact tooling. 'research new'/'new-comparison' create correctly-named docs.",
    )
    research_sub = p_research.add_subparsers(dest="research_command")
    p_research_new = research_sub.add_parser(
        "new",
        parents=[common],
        help="Create a correctly-named research doc + starter frontmatter (dry-run by default; --apply to write).",
    )
    p_research_new.add_argument(
        "dir", nargs="?", default=None, help="Repo root (default: current directory)."
    )
    p_research_new.add_argument(
        "--kind", required=True, help="Research kind (see the contract vocab)."
    )
    p_research_new.add_argument(
        "--slug", default=None, help="Short descriptive kebab slug."
    )
    p_research_new.add_argument("--summary", default="", help="One-line human summary.")
    p_research_new.add_argument(
        "--set",
        dest="set",
        default=None,
        help="Set id (omitted = a singleton from the slug).",
    )
    p_research_new.add_argument(
        "--model", default=None, help="Optional authorship-facet model."
    )
    p_research_new.add_argument("--topic", default=None, help="Comma-separated topics.")
    p_research_new.add_argument(
        "--date", default=None, help="Override the set date (YYYYMMDD)."
    )
    p_research_new.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
    )
    p_research_new.add_argument(
        "--overwrite", action="store_true", help="Allow overwriting an existing path."
    )

    p_research_cmp = research_sub.add_parser(
        "new-comparison",
        parents=[common],
        help="Scaffold a multi-model comparison set (prompt + one report per model + reconciliation).",
    )
    p_research_cmp.add_argument(
        "dir", nargs="?", default=None, help="Repo root (default: current directory)."
    )
    p_research_cmp.add_argument(
        "--set", dest="set", required=True, help="Set id for the comparison."
    )
    p_research_cmp.add_argument(
        "--slug", required=True, help="Short descriptive kebab slug."
    )
    p_research_cmp.add_argument(
        "--models",
        required=True,
        help="Comma-separated models (e.g. gpt56,sonnet5,gemini31pro).",
    )
    p_research_cmp.add_argument("--summary", default="", help="One-line human summary.")
    p_research_cmp.add_argument("--topic", default=None, help="Comma-separated topics.")
    p_research_cmp.add_argument(
        "--date", default=None, help="Override the set date (YYYYMMDD)."
    )
    p_research_cmp.add_argument(
        "--apply",
        action="store_true",
        help="Write the files (default is preview only).",
    )
    p_research_cmp.add_argument(
        "--overwrite", action="store_true", help="Allow overwriting an existing path."
    )

    p_research_setassign = research_sub.add_parser(
        "set-assign",
        parents=[common],
        help="Group docs into a set (shared date+set-id, assigned NN), keeping id6 (dry-run by default).",
    )
    p_research_setassign.add_argument(
        "ids",
        nargs="+",
        help="One or more <id6> tokens to group into the set, in order.",
    )
    p_research_setassign.add_argument(
        "--set", dest="set", required=True, help="Set id."
    )
    p_research_setassign.add_argument(
        "--order", type=int, default=None, help="Starting NN (default 0)."
    )
    p_research_setassign.add_argument(
        "--date", default=None, help="Set date (YYYYMMDD; default today)."
    )
    p_research_setassign.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_setassign.add_argument(
        "--apply",
        action="store_true",
        help="Perform the renames (default is preview only).",
    )

    p_research_mv = research_sub.add_parser(
        "mv",
        parents=[common],
        help="Rename/re-slug one research doc within the grammar, keeping id6 (dry-run by default).",
    )
    p_research_mv.add_argument("id", help="The <id6> of the doc to rename.")
    p_research_mv.add_argument("--slug", default=None, help="New slug.")
    p_research_mv.add_argument("--kind", default=None, help="New kind.")
    p_research_mv.add_argument("--model", default=None, help="New model facet.")
    p_research_mv.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_mv.add_argument(
        "--apply",
        action="store_true",
        help="Perform the rename (default is preview only).",
    )

    p_research_checkrefs = research_sub.add_parser(
        "check-refs",
        parents=[common],
        help="Report dangling <id6> citations (the reusable detector as a standalone verb).",
    )
    p_research_checkrefs.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_checkrefs.add_argument(
        "--agent",
        action="store_true",
        help="Machine output: tab-separated location/rule/id.",
    )

    p_research_index = research_sub.add_parser(
        "index",
        parents=[common],
        help="Regenerate INDEX.json + INDEX.md from frontmatter; --check fails on drift.",
    )
    p_research_index.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_index.add_argument(
        "--check",
        action="store_true",
        help="Fail (nonzero) on drift instead of regenerating.",
    )
    p_research_index.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Hot-window size for INDEX.md (default 40).",
    )
    p_research_index.add_argument(
        "--agent",
        action="store_true",
        help="Machine output for --check: tab-separated records.",
    )

    p_research_find = research_sub.add_parser(
        "find",
        parents=[common],
        help="Query the index by --id/--set/--topic/--status (token-cheap; no corpus read).",
    )
    p_research_find.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_find.add_argument("--id", default=None, help="Filter by <id6>.")
    p_research_find.add_argument(
        "--set", dest="set", default=None, help="Filter by set id."
    )
    p_research_find.add_argument("--topic", default=None, help="Filter by topic.")
    p_research_find.add_argument("--status", default=None, help="Filter by status.")

    p_research_promote = research_sub.add_parser(
        "promote",
        parents=[common],
        help="Deliberately set a doc's status (e.g. --to reference) and move it to the shard.",
    )
    p_research_promote.add_argument("id", help="The <id6> of the doc.")
    p_research_promote.add_argument("--to", default="reference", help="Target status.")
    p_research_promote.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_promote.add_argument(
        "--apply",
        action="store_true",
        help="Perform the move (default is preview only).",
    )

    p_research_miscat = research_sub.add_parser(
        "check-miscategorized",
        parents=[common],
        help="Report archived-but-cited docs (should they be reference?).",
    )
    p_research_miscat.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    p_context = sub.add_parser(
        "context",
        parents=[common],
        help="Inspect resolved AW project context, logical roots, and policy.",
    )
    p_context.add_argument(
        "--repo",
        default=None,
        help="Target repository directory (default: current directory).",
    )
    p_context.add_argument(
        "--json",
        action="store_true",
        help="Output context as formatted JSON (no ANSI).",
    )
    p_context.add_argument(
        "--agent",
        action="store_true",
        help="Machine-readable JSON output for LLM callers.",
    )

    p_path = sub.add_parser(
        "path",
        parents=[common],
        help="Resolve the physical path for a logical AW root (system|config|state|records).",
    )
    p_path.add_argument(
        "root",
        choices=("system", "config", "state", "records"),
        help="Logical root to resolve.",
    )
    p_path.add_argument(
        "--repo",
        default=None,
        help="Target repository directory (default: current directory).",
    )
    p_path.add_argument(
        "--agent",
        action="store_true",
        help="Print only the absolute resolved path with no prose.",
    )

    p_project = sub.add_parser(
        "project",
        parents=[common],
        help="Owner verbs for project identity, registry status, attach, and move.",
    )
    project_sub = p_project.add_subparsers(dest="project_command")

    p_project_status = project_sub.add_parser(
        "status",
        parents=[common],
        help="Inspect project identity & registry matching status.",
    )
    p_project_status.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_project_status.add_argument(
        "--json", action="store_true", help="Output status as formatted JSON."
    )
    p_project_status.add_argument(
        "--agent", action="store_true", help="Machine-readable output for LLM callers."
    )

    p_project_attach = project_sub.add_parser(
        "attach", parents=[common], help="Attach repository to a project ID."
    )
    p_project_attach.add_argument("project_id", help="Target project ID to attach to.")
    p_project_attach.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_project_attach.add_argument(
        "--yes", action="store_true", help="Auto-confirm attach operation."
    )
    p_project_attach.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying registry.",
    )

    p_project_move = project_sub.add_parser(
        "move", parents=[common], help="Update project target path association."
    )
    p_project_move.add_argument("project_id", help="Target project ID to move.")
    p_project_move.add_argument("new_path", help="New target path for the project.")
    p_project_move.add_argument(
        "--yes", action="store_true", help="Auto-confirm move operation."
    )
    p_project_move.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying registry.",
    )

    p_storage = sub.add_parser(
        "storage",
        parents=[common],
        help="Owner verbs for records storage backends, durability, and initialization.",
    )
    storage_sub = p_storage.add_subparsers(dest="storage_command")

    p_storage_status = storage_sub.add_parser(
        "status",
        parents=[common],
        help="Inspect observable records storage status and durability.",
    )
    p_storage_status.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_status.add_argument(
        "--json", action="store_true", help="Output status as formatted JSON."
    )
    p_storage_status.add_argument(
        "--agent", action="store_true", help="Machine-readable output for LLM callers."
    )

    p_storage_init = storage_sub.add_parser(
        "init",
        parents=[common],
        help="Initialize records storage and optional local Git repo.",
    )
    p_storage_init.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_init.add_argument(
        "--no-git",
        action="store_true",
        help="Do not run git init in records directory.",
    )
    p_storage_init.add_argument(
        "--acknowledge-remote",
        action="store_true",
        help="Record explicit user acknowledgement of remote durability policy.",
    )
    p_storage_init.add_argument(
        "--yes", action="store_true", help="Auto-confirm initialization operation."
    )
    p_storage_init.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying filesystem.",
    )

    p_storage_attach = storage_sub.add_parser(
        "attach", parents=[common], help="Acknowledge or set storage durability policy."
    )
    p_storage_attach.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_attach.add_argument(
        "--acknowledge-remote",
        action="store_true",
        help="Record explicit user acknowledgement of remote durability policy.",
    )
    p_storage_attach.add_argument(
        "--yes", action="store_true", help="Auto-confirm attach operation."
    )
    p_storage_attach.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying filesystem.",
    )

    p_attention = sub.add_parser(
        "attention",
        parents=[common],
        help="Read-only cross-tree attention view (board or JSON to stdout); --check fails closed.",
    )
    p_attention.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_attention.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=None,
        help="Output format (default: human board).",
    )
    p_attention.add_argument(
        "--check",
        action="store_true",
        help="Validate all tracked trees; fail closed on any violation.",
    )
    p_attention.add_argument(
        "--agent",
        action="store_true",
        help="Machine-readable tab-separated drift output (with --check).",
    )
    p_attention.add_argument(
        "--all", action="store_true", help="Show done/parked groups in the board."
    )

    p_specs = sub.add_parser(
        "specs",
        parents=[common],
        help="Owner verbs for the specs tree. 'specs set'/'note' write status+history; 'specs check' validates.",
    )
    specs_sub = p_specs.add_subparsers(dest="specs_command")
    p_specs_set = specs_sub.add_parser(
        "set",
        parents=[common],
        help="Transition a spec's status (+ typed gates) and append history.",
    )
    p_specs_set.add_argument("path", help="Spec file to update.")
    p_specs_set.add_argument(
        "--status", required=True, help="Target spec status (the closed enum)."
    )
    p_specs_set.add_argument("--message", required=True, help="History record message.")
    p_specs_set.add_argument(
        "--gate-kind",
        dest="gate_kind",
        default=None,
        help="Gate kind (required for deferred).",
    )
    p_specs_set.add_argument(
        "--gate-ref",
        dest="gate_ref",
        default=None,
        help="Gate reference (required for deferred).",
    )
    p_specs_set.add_argument(
        "--gate-summary",
        dest="gate_summary",
        default=None,
        help="Optional human gate context.",
    )
    p_specs_set.add_argument(
        "--evidence",
        default=None,
        help="Resolvable implementation-evidence citation (for implemented).",
    )
    p_specs_set.add_argument(
        "--yes-i-am-human",
        dest="yes_i_am_human",
        action="store_true",
        help="Confirm human approval for reviewed -> approved (honored only on an interactive TTY).",
    )
    p_specs_set.add_argument(
        "--date", default=None, help="Override the history date (YYYY-MM-DD)."
    )
    p_specs_note = specs_sub.add_parser(
        "note",
        parents=[common],
        help="Append a history record to a spec (no status change).",
    )
    p_specs_note.add_argument("path", help="Spec file to annotate.")
    p_specs_note.add_argument(
        "--message", required=True, help="History record message."
    )
    p_specs_note.add_argument(
        "--date", default=None, help="Override the history date (YYYY-MM-DD)."
    )
    p_specs_check = specs_sub.add_parser(
        "check",
        parents=[common],
        help="Validate one spec (or all specs) against the contract; fail closed.",
    )
    p_specs_check.add_argument(
        "path", nargs="?", default=None, help="A spec file (omit to check all)."
    )
    p_specs_check.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_specs_check.add_argument(
        "--agent", action="store_true", help="Machine-readable tab-separated output."
    )
    p_specs_migrate = specs_sub.add_parser(
        "migrate",
        parents=[common],
        help="One-time first-normalization of a legacy/free-form spec status to the bare enum (Order 04).",
    )
    p_specs_migrate.add_argument("path", help="Spec file to normalize.")
    p_specs_migrate.add_argument(
        "--status", required=True, help="Target bare-enum status."
    )
    p_specs_migrate.add_argument(
        "--canonical", action="store_true", help="Add a `- Canonical: true` field."
    )
    p_specs_migrate.add_argument(
        "--gate-kind",
        dest="gate_kind",
        default=None,
        help="Gate kind (required for deferred).",
    )
    p_specs_migrate.add_argument(
        "--gate-ref",
        dest="gate_ref",
        default=None,
        help="Gate reference (required for deferred).",
    )
    p_specs_migrate.add_argument(
        "--gate-summary",
        dest="gate_summary",
        default=None,
        help="Optional human gate context.",
    )
    p_specs_migrate.add_argument(
        "--date", default=None, help="Override the history date (YYYY-MM-DD)."
    )

    p_archive = sub.add_parser(
        "archive",
        parents=[common],
        help="Deliberately deep-shelve research (targeted, or a bare aged-and-uncited sweep with preview).",
    )
    p_archive.add_argument(
        "target",
        nargs="?",
        default=None,
        help="A <set-id> or <id6> to archive (omit for a sweep).",
    )
    p_archive.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_archive.add_argument(
        "--keep",
        action="append",
        default=None,
        help="In a sweep, send this <id6> to reference instead of archive.",
    )
    p_archive.add_argument(
        "--apply",
        action="store_true",
        help="Perform the moves (default is preview only).",
    )

    p_names = sub.add_parser(
        "plan-names",
        parents=[common],
        help="Check (or --apply) that plan/prompt filenames match YYYYMMDD-HHMM-NN-<slug>.md.",
    )
    p_names.add_argument(
        "dir", nargs="?", default=None, help="Repo root (default: current directory)."
    )
    p_names.add_argument(
        "--apply",
        action="store_true",
        help="Perform the staged git-mv renames (default: check).",
    )
    p_names.add_argument(
        "--area",
        action="append",
        default=None,
        help="Top-level .agents/ area to scan (repeatable).",
    )
    p_names.add_argument(
        "--all",
        dest="all_areas",
        action="store_true",
        help="Scan every top-level .agents/ area.",
    )
    p_names.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="fnmatch glob to exclude (repeatable).",
    )
    p_names.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Drop the built-in README.md exclude.",
    )
    p_names.add_argument(
        "--include-nested",
        action="store_true",
        help="Also rename eligible *.md nested deeper.",
    )
    p_names.add_argument(
        "--rename-non-numeric",
        action="store_true",
        help="Also rename files not starting with a date.",
    )
    p_names.add_argument(
        "--assume-dates",
        action="store_true",
        help="Accept derived dates for 'imported?' files.",
    )
    p_names.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )

    p_leaks = sub.add_parser(
        "check-local-leaks",
        aliases=["sanitize"],
        parents=[common],
        help="Detect (and with --fix, rewrite) identifying info (home paths, usernames, "
        "private repo names, hostnames, session ids) that must not appear in a public artifact.",
    )
    p_leaks.add_argument(
        "dir", nargs="?", default=".", help="Repo root (default: current directory)."
    )
    p_leaks.add_argument(
        "--history",
        action="store_true",
        help="Scan git history (bounded) instead of the tree.",
    )
    p_leaks.add_argument(
        "--max-commits", type=int, default=None, help="Bound --history to N commits."
    )
    p_leaks.add_argument(
        "--wheel", default=None, help="Scan a built wheel/zip at this path instead."
    )
    p_leaks.add_argument(
        "--warn",
        action="store_true",
        help="Also report advisory auto-derived candidates (for /assess review).",
    )
    p_leaks.add_argument(
        "--staged",
        action="store_true",
        help="Scan STAGED blob content instead of the tree (for the pre-commit hook).",
    )
    p_leaks.add_argument(
        "--agent",
        action="store_true",
        help="Machine-parseable output for an LLM caller (path\\trule\\tseverity, no prose).",
    )
    p_leaks.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite auto-fixable home-style paths to ~ (interactive per file unless --yes; "
        "identity/private tokens are reported, never auto-rewritten).",
    )
    p_leaks.add_argument(
        "--yes",
        "--force",
        dest="assume_yes",
        action="store_true",
        help="With --fix, apply changes without per-file confirmation.",
    )
    p_leaks.add_argument(
        "--dry-run",
        action="store_true",
        help="With --fix, show what would change without writing.",
    )
    p_leaks.add_argument(
        "--configure",
        action="store_true",
        help="Launch the interactive wizard to author the leak-sanitizer config "
        "(allowlist, IP/hostname toggles, personal hints) instead of scanning.",
    )

    return parser


# --------------------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------------------


def _packaged_version() -> str:
    """The version this distribution ships (what installed repos are compared against)."""

    return __version__


def _confirm(term: Term, prompt: str, assume_yes: bool) -> bool:
    """Ask a yes/no question; auto-yes when assume_yes or non-interactive stdin."""

    if assume_yes:
        return True
    if not sys.stdin.isatty():
        # Non-interactive without --yes: refuse to change things silently.
        term.status(
            "warn", f"{prompt} (declining: non-interactive; pass --yes to proceed)"
        )
        return False
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


def _has_uncommitted_changes(repo_root: Path) -> bool:
    """True if the git working tree has staged or unstaged changes (best-effort)."""

    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _preflight_warnings(repo_root: Path, packaged: str) -> List[str]:
    """Return preflight WARN messages for a target (ex-`doctor`; D6).

    Warns on: not a git repo; a would-downgrade (installed is 'ahead' of the packaged
    version). The dirty/behind git state is owned by `engine.run_git_diagnostics` (single
    source of truth), which every interactive install path runs; it is NOT duplicated here.
    """

    warnings: List[str] = []
    if not (repo_root / ".git").exists():
        warnings.append(
            f"{repo_root} is not a git repository (install will still write files)."
        )
    installed = engine.read_installed_version(repo_root)
    if installed is not None:
        state = versioning.status(installed, packaged)
        if state == "ahead":
            warnings.append(
                f"{repo_root} has {installed}, which is AHEAD of this tool's {packaged}; "
                "installing would DOWNGRADE it."
            )
    return warnings


def _diagnostics_ok(repo_root: Path, args: argparse.Namespace) -> bool:
    """Run the shared engine git-diagnostics pre-flight for one repo before installing.

    Returns True to proceed, False to skip/abort this repo. Builds a minimal InstallPlan so
    the CLI runs the SAME pre-flight as engine.main()/install-workflows.py (entry-point
    parity, 1837-01). run_git_diagnostics is no-op-silent when the repo is clean+in-sync or
    non-interactive, and only prompts on real risk (tracked-dirty or behind).
    """

    import copy

    engine_args = copy.copy(args)
    engine_args.repo_root = repo_root
    engine_args.version = False
    engine_args.diff = False
    engine_args.undo = False
    # Different callers (install, install-all, setup) carry different arg shapes; ensure the
    # attributes build_install_plan reads are present with safe defaults.
    for attr, default in (
        ("dry_run", False),
        ("no_backup", False),
        ("no_prune", False),
        ("source_root", None),
        ("yes", False),
        ("no_color", False),
    ):
        if not hasattr(engine_args, attr):
            setattr(engine_args, attr, default)
    plan = engine.build_install_plan(engine_args)
    return engine.run_git_diagnostics(plan)


# --------------------------------------------------------------------------------------
# install
# --------------------------------------------------------------------------------------


def _install_one(
    repo_root: Path,
    source_root: Path,
    args: argparse.Namespace,
    term: Term,
) -> str:
    """Install into ONE repo through the single shared shell, then summarize and offer to commit.

    This is the ONE per-repo orchestration all entry points use (D85: `aw install <dir>`,
    `aw install all`, `aw setup`, and the engine `run()` path), so none can drift into
    staging-without-committing. It runs: install_into_repo (steps) -> print_summary -> a status line
    -> prompt_and_run_commit (auto-commits under --yes, prompts otherwise, and on decline prints the
    "left staged; commit with git commit -- ..." line so a repo is NEVER left SILENTLY dirty). It is
    SystemExit-isolated so a dir-conflict/git failure in one repo cannot abort a batch (R-4).

    Returns one of "ok", "nochange", or "failed" for the caller's tally.
    """

    import copy

    try:
        result = engine.install_into_repo(
            repo_root,
            source_root,
            dry_run=getattr(args, "dry_run", False),
            backup=not getattr(args, "no_backup", False),
            prune=not getattr(args, "no_prune", False),
            yes=getattr(args, "yes", False),
            no_color=getattr(args, "no_color", False),
        )
    except (
        Exception,
        SystemExit,
    ) as exc:  # isolate one repo's failure from a batch (R-4).
        term.status("fail", f"{repo_root}: {exc}")
        return "failed"

    workflows = engine.parse_manifest(source_root)
    engine_args = copy.copy(args)
    engine_args.repo_root = repo_root
    engine_args.version = False
    engine_args.diff = False
    engine_args.undo = False
    # The `setup` / `install all` arg namespaces do not carry the `install`-verb flags, but
    # build_install_plan reads them as hard attributes. Fill the same defaults install_into_repo
    # used above so the shared plan is well-formed for every entry point (behavior-preserving:
    # the single-repo `install` path already has these, so getattr returns its real values).
    engine_args.dry_run = getattr(args, "dry_run", False)
    engine_args.no_backup = getattr(args, "no_backup", False)
    engine_args.no_prune = getattr(args, "no_prune", False)
    plan = engine.build_install_plan(engine_args)

    engine.print_summary(
        plan=plan,
        workflows=workflows,
        migrated=result.get("migrated") or [],
        installed=result["installed"],
        skipped=result["skipped"],
        pruned=result["pruned"],
        agents_status=result["agents_status"],
        gitignore_status=result["gitignore_status"],
        backups_ignore_status=result["backups_ignore_status"],
        use_git=result["use_git"],
    )

    n = len(result["installed"])
    if n == 0:
        term.status(
            "ok",
            f"{repo_root}: already current at version {result['version']}; nothing to update.",
        )
        outcome = "nochange"
    else:
        term.status(
            "ok",
            f"{repo_root}: installed/updated {n} file(s); version {result['version']}.",
        )
        outcome = "ok"

    # Offer to commit (auto under --yes; prompt otherwise; on decline it prints how to commit, so
    # nothing is left SILENTLY staged). This is the step batch paths previously skipped (the bug).
    engine.prompt_and_run_commit(
        plan=plan,
        installed=result["installed"],
        pruned=result["pruned"],
        agents_status=result["agents_status"],
        backups_ignore_status=result["backups_ignore_status"],
        use_git=result["use_git"],
        artifacts=result.get("artifacts") or [],
        untracked_ignore_status=result.get("untracked_ignore_status", ""),
    )
    return outcome


def _run_install(args: argparse.Namespace, term: Term) -> int:
    targets = args.targets if getattr(args, "targets", None) else []
    if "all" in targets:
        return _install_all(args, term)

    repo_roots = (
        [Path(t).expanduser().resolve() for t in targets] if targets else [Path.cwd()]
    )

    if not config.config_path().is_file() and not targets:
        term.status(
            "warn",
            "No config yet. Run 'aw setup' to configure your repos, or "
            "'aw install <dir>' for a one-off.",
        )

    try:
        source_root = engine.resolve_source_root(
            Path(args.source_root).expanduser() if args.source_root else None
        )
    except SystemExit as exc:
        term.status("fail", f"Resolve source root: {exc}")
        return 1

    packaged = _packaged_version()
    returncode = 0

    for repo_root in repo_roots:
        if len(repo_roots) > 1:
            term.line()
            term.heading(f"Target Repo: {repo_root}")

        for w in _preflight_warnings(repo_root, packaged):
            term.status("warn", w)
        # Git diagnostics pre-flight FIRST (dirty/behind handling, shared with the engine);
        # an abort here skips the repo before the install confirm.
        if not _diagnostics_ok(repo_root, args):
            term.status(
                "skip", f"{repo_root}: aborted at git pre-flight; nothing changed."
            )
            returncode = 1
            continue
        if not _confirm(term, f"Install agent-workflows into {repo_root}?", args.yes):
            term.status("skip", f"{repo_root}: aborted; nothing changed.")
            continue

        # Shared per-repo shell (install + summary + commit-offer, SystemExit-isolated).
        if _install_one(repo_root, source_root, args, term) == "failed":
            returncode = 1
    return returncode


def _install_all(args: argparse.Namespace, term: Term) -> int:
    """Install into every repo in the config allowlist, with per-repo isolation (R-3/R-4)."""

    cfg = config.load()
    repos = config.expanded_repos(cfg)
    if not repos:
        term.status(
            "warn", "No repos in your config yet. Run 'aw setup' to add search roots."
        )
        return 1

    try:
        source_root = engine.resolve_source_root(
            Path(args.source_root).expanduser()
            if getattr(args, "source_root", None)
            else None
        )
    except SystemExit as exc:
        term.status("fail", str(exc))
        return 1

    # "all" means every CONFIGURED repo (the allowlist), not every repo on disk. Make that
    # explicit so a user with many on-disk repos is not surprised by the count.
    if not _confirm(
        term,
        f"Install/update agent-workflows into {len(repos)} configured repo(s)?",
        args.yes,
    ):
        term.status("skip", "aborted; nothing changed.")
        return 1

    ok = 0
    failed = 0
    aborted = 0
    for repo in repos:
        if not repo.is_dir():
            term.status("skip", f"{repo}: not a directory")
            continue
        # Same git diagnostics pre-flight as the single-repo path (entry-point parity).
        # No-op-silent when clean/in-sync/non-interactive; an abort skips just this repo.
        if not _diagnostics_ok(repo, args):
            term.status("skip", f"{repo}: aborted at git pre-flight")
            aborted += 1
            continue
        # Shared per-repo shell: installs AND offers to commit (auto under --yes), SystemExit-isolated.
        # Before D85 this batch path staged files and never committed -> a fleet left silently dirty.
        outcome = _install_one(repo, source_root, args, term)
        if outcome == "failed":
            failed += 1
        else:
            ok += 1

    term.line()
    summary = f"{ok} installed, {failed} failed"
    if aborted:
        summary += f", {aborted} aborted"
    summary += f", {len(repos)} configured total"
    term.kv("Summary", summary)
    if ok:
        _teach(term)
    return 1 if failed else 0


def _teach(term: Term) -> None:
    term.line()
    term.status(
        "ok",
        "Next: run the LLM '/setup-repo' workflow in each repo for "
        "stack-tailored conformance (CI, .gitignore, lifecycle contract).",
    )


# --------------------------------------------------------------------------------------
# uninstall
# --------------------------------------------------------------------------------------


def _uninstall_dry_run_report(term: Term, repo_root: Path) -> int:
    """Report what a normal + deep uninstall WOULD do, changing nothing."""

    plan = engine.plan_uninstall(repo_root)
    term.status("ok", f"[dry-run] uninstall plan for {repo_root}:")
    if plan.has_manifest:
        print(f"  would remove {len(plan.remove)} owned file(s)")
        if plan.drifted:
            print(
                f"  would PRESERVE {len(plan.drifted)} file(s) you edited "
                "(pass --force to remove them):"
            )
            for rel in plan.drifted:
                print(f"    - {rel}")
        print("  would strip the managed AGENTS/native + .gitignore blocks")
        print("  would remove the manifest last")
    else:
        print("  no manifest: would fall back to removing the framework namespace")
    deep = engine.plan_deep_cleanup(repo_root)
    if not deep.is_empty:
        print("  deeper cleanup (offered separately) WOULD remove:")
        for root, n in sorted(deep.counts.items()):
            print(f"    - {n} file(s) under {root}/")
        if deep.at_risk:
            print(
                f"    ! {len(deep.at_risk)} of these are NOT recoverable from git "
                "(untracked/uncommitted)"
            )
    return 0


def _offer_deep_cleanup(
    term: Term, repo_root: Path, use_git: bool, args, changed: list[str]
) -> None:
    """Offer (or, under --deep, perform) the deeper .agents/ cleanup with a graduated warning."""

    plan = engine.plan_deep_cleanup(repo_root)
    if plan.is_empty:
        return

    print()
    print(
        "A deeper cleanup can also remove the agent-workflows scaffolding it left behind:"
    )
    for root, n in sorted(plan.counts.items()):
        print(f"  - {n} file(s) under {root}/")
    if plan.all_recoverable:
        print(
            "  All of these are tracked and committed, so they can be restored with "
            "`git checkout` if you change your mind."
        )
    else:
        print(
            term.colorize(
                f"  WARNING: {len(plan.at_risk)} of these are NOT recoverable from git "
                "(untracked, uncommitted, or ignored). Deleting them is permanent:",
                "yellow",
            )
        )
        for rel in plan.at_risk:
            print(f"    ! {rel}")

    do_it = args.deep
    if not do_it:
        if args.yes or args.force or not sys.stdin.isatty():
            # Non-interactive (--yes/--force/no TTY) without --deep: do NOT silently delete the
            # scaffolding; it holds user content. Skip the deeper cleanup unless --deep is set.
            term.status(
                "warn",
                "scaffolding left in place (pass --deep to remove it non-interactively).",
            )
            return
        choice = engine.prompt_choice(
            "Remove this scaffolding too? [y/N/list/help]: ",
            [
                "  Y    = Yes, remove the scaffolding listed above",
                "  N    = No, keep it [default]",
                "  list = show every file that would be removed, then ask again",
                "  help = show this help",
            ],
            default="no",
            accept={
                "y": "yes",
                "yes": "yes",
                "n": "no",
                "no": "no",
                "list": "list",
                "l": "list",
                "help": "help",
                "?": "help",
            },
            on_diff=lambda: [print(f"    - {f}") for f in plan.files],
        )
        do_it = choice == "yes"

    if do_it:
        for a in engine.run_deep_cleanup(repo_root, plan, use_git, changed_out=changed):
            term.status("ok", a)
    else:
        term.status("skip", "deeper cleanup skipped; scaffolding left in place.")


def _run_uninstall(args: argparse.Namespace, term: Term) -> int:
    repo_root = Path(args.target).expanduser().resolve()
    if not (repo_root / engine.WORKFLOWS_DIR).is_dir():
        term.status(
            "warn", f"{repo_root}: framework not installed (nothing to remove)."
        )
        return 1

    if getattr(args, "dry_run", False):
        return _uninstall_dry_run_report(term, repo_root)

    if not _confirm(
        term,
        f"Remove agent-workflows from {repo_root}? "
        "(owned files + generated shims + managed blocks + manifest)",
        args.yes or args.force,
    ):
        term.status("skip", "aborted; nothing changed.")
        return 1

    use_git = engine.git_available(repo_root)

    # Interactive per-drifted-file decision (keep [default] / remove / diff). Non-interactive
    # or --force is handled inside uninstall_repo (preserve unless --force).
    def _drift_decider(rel: str) -> str:
        if not sys.stdin.isatty():
            return "keep"
        term.status("warn", f"you have edited {rel} since install.")
        choice = engine.prompt_choice(
            f"Remove your edited {rel}? [y/N/d/help]: ",
            [
                "  Y    = Yes, remove my edited copy",
                "  N    = No, keep my version [default]",
                "  D    = Show what changed vs the installed version, then ask again",
                "  help = show this help",
            ],
            default="no",
            accept={
                "y": "yes",
                "yes": "yes",
                "n": "no",
                "no": "no",
                "d": "diff",
                "help": "help",
                "?": "help",
            },
            on_diff=lambda: _print_drift_diff(repo_root, rel),
        )
        return "remove" if choice == "yes" else "keep"

    changed: list[str] = []
    actions = engine.uninstall_repo(
        repo_root,
        use_git,
        drift_decider=None if args.force else _drift_decider,
        force=args.force,
        changed_out=changed,
    )
    for a in actions:
        term.status("ok", a)

    # Offer (or, under --deep, perform) the deeper .agents/ cleanup.
    _offer_deep_cleanup(term, repo_root, use_git, args, changed)

    # Drop the repo from the config allowlist, if present.
    cfg = config.load()
    stored = [
        p for p in cfg.get("repos", []) if config.expand_path(p).resolve() != repo_root
    ]
    if len(stored) != len(cfg.get("repos", [])):
        cfg["repos"] = stored
        config.save(cfg)
        term.status("ok", f"removed {repo_root} from the config repo list.")

    # Offer to commit ONLY the files uninstall changed (auto under --yes/--force; prompt
    # otherwise; on decline print the exact path-scoped command). Never push.
    _offer_commit_uninstall(term, repo_root, use_git, changed, args.yes or args.force)
    return 0


def _print_drift_diff(repo_root: Path, rel: str) -> None:
    """Show the user's current file vs the installer's last-written version (from the manifest
    hash we cannot reconstruct content, so show the current file against the freshly generated
    template when it is a shim; otherwise just note the file differs)."""

    # We do not store the original bytes (only a hash), so show the current content with a note.
    try:
        current = (repo_root / rel).read_text(encoding="utf-8")
    except OSError:
        print(f"    (cannot read {rel})")
        return
    print(f"    --- your current {rel} (differs from the installed version) ---")
    for line in current.splitlines():
        print(f"    {line}")


def _offer_commit_uninstall(
    term: Term, repo_root: Path, use_git: bool, changed: list[str], assume_yes: bool
) -> None:
    """Offer to commit ONLY the paths uninstall changed (path-scoped). Never push."""

    import subprocess

    if not use_git or not changed:
        if changed:
            term.status(
                "warn", "Deletions are STAGED, not committed. Review and commit."
            )
        return
    paths = sorted(set(changed))
    quoted = " ".join(f'"{p}"' if " " in p else p for p in paths)
    if not assume_yes and sys.stdin.isatty():
        if not _confirm(
            term, f"Commit these {len(paths)} uninstall change(s) now?", False
        ):
            term.status("warn", "Left staged; commit with:")
            print(f'  git commit -m "uninstall agent-workflows" -- {quoted}')
            return
    elif not assume_yes:
        # Non-interactive without --yes: do not commit; tell the user how.
        term.status("warn", "Left staged; commit with:")
        print(f'  git commit -m "uninstall agent-workflows" -- {quoted}')
        return
    proc = subprocess.run(
        ["git", "commit", "-m", "uninstall agent-workflows", "--", *paths],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        shell=False,
    )
    if proc.returncode == 0:
        term.status("ok", f"committed {len(paths)} uninstall change(s).")
    else:
        term.status("warn", "commit failed; left staged. Commit with:")
        print(f'  git commit -m "uninstall agent-workflows" -- {quoted}')


# --------------------------------------------------------------------------------------
# list / status
# --------------------------------------------------------------------------------------


def _repos_for_report(recursive: bool) -> List[Path]:
    """Config repos plus repos discovered under the config search roots (deduped)."""

    cfg = config.load()
    repos = list(config.expanded_repos(cfg))
    roots = config.expanded_search_roots(cfg)
    if roots:
        found = discovery.discover(
            roots, ignore=cfg.get("ignore", []), recursive=recursive
        )
        repos.extend(found.targets)
    seen = set()
    out = []
    for r in repos:
        rp = r.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def _run_list(args: argparse.Namespace, term: Term) -> int:
    packaged = _packaged_version()
    repos = _repos_for_report(args.recursive)
    if not repos:
        term.status("warn", "No configured or discovered repos. Run 'aw setup'.")
        return 0
    term.heading("Repositories")
    for repo in repos:
        installed = engine.read_installed_version(repo)
        state = versioning.status(installed, packaged)
        detail = installed if installed else "not installed"
        term.status(state, f"{repo}  ({detail})")
    return 0


def _run_status(term: Term) -> int:
    packaged = _packaged_version()
    term.heading("agent-workflows status")
    term.kv("Packaged version", packaged)
    term.kv("Python", sys.version.split()[0])
    term.kv("git", "present" if engine.git_available(Path.cwd()) else "not found")
    term.kv(
        "Config",
        str(config.config_path())
        + ("" if config.config_path().is_file() else "  (none yet; run 'aw setup')"),
    )
    cfg = config.load()
    term.kv("Search roots", ", ".join(cfg.get("search_roots", [])) or "(none)")
    term.kv("Repos configured", str(len(cfg.get("repos", []))))

    repos = _repos_for_report(recursive=False)
    if repos:
        counts = {}
        for repo in repos:
            state = versioning.status(engine.read_installed_version(repo), packaged)
            counts[state] = counts.get(state, 0) + 1
        term.line()
        term.heading("Currency")
        for state in ("current", "stale", "ahead", "dev", "not-installed", "unknown"):
            if counts.get(state):
                term.status(state, f"{counts[state]} repo(s)")
    return 0


# --------------------------------------------------------------------------------------
# setup wizard
# --------------------------------------------------------------------------------------


def _run_setup(args: argparse.Namespace, term: Term) -> int:
    cfg = config.load()
    interactive = args.roots is None and sys.stdin.isatty()

    if args.roots is None and config.is_configured() and not sys.stdin.isatty():
        # Non-interactive re-run of a configured tool: summarize, do not re-interview.
        term.status("ok", "Already configured.")
        return _run_status(term)

    # Gather search roots.
    roots: List[str] = []
    if args.roots:
        roots = list(args.roots)
    elif interactive:
        term.heading("agent-workflows setup")
        term.line(
            "Where do you keep your repositories? Enter one path per line "
            "(use ~ for home); blank to finish."
        )
        existing = cfg.get("search_roots", [])
        if existing:
            term.kv("Current roots", ", ".join(existing))
        while True:
            entry = input("  root> ").strip()  # KeyboardInterrupt/EOF handled in main()
            if not entry:
                break
            expanded = Path(entry).expanduser()
            stored = config._preserve_home(str(expanded))
            if not expanded.exists():
                term.status(
                    "warn",
                    f"{stored} does not exist yet; storing it anyway (roots are scanned "
                    "when you install).",
                )
            elif not expanded.is_dir():
                term.status("fail", f"{stored} is not a directory; skipped.")
                continue
            if stored in roots:
                term.status("skip", f"{stored} already added.")
                continue
            roots.append(stored)
            term.status("ok", f"Added {stored}.")
        if not roots:
            roots = existing
    else:
        term.status(
            "warn", "Non-interactive and no --root given; nothing to configure."
        )
        return 1

    if roots:
        # Merge (store ~-preserved via normalize on save).
        merged = list(dict.fromkeys(list(cfg.get("search_roots", [])) + roots))
        cfg["search_roots"] = merged

    # Discover repos under the roots.
    expanded_roots = [config.expand_path(r) for r in cfg.get("search_roots", [])]
    found = discovery.discover(
        expanded_roots, ignore=cfg.get("ignore", []), recursive=args.recursive
    )
    term.line()
    term.heading("Discovered repositories")
    if not found.targets:
        term.status("warn", "No git repos found under those roots.")
    for repo in found.targets:
        term.status("ok", str(repo))
    for repo, reason in sorted(found.skipped.items()):
        term.status("skip", f"{repo} ({reason})")
    for repo in found.ignored:
        term.status("ignored", str(repo))

    # Record discovered repos into the allowlist.
    if found.targets:
        cfg_repos = list(cfg.get("repos", []))
        for repo in found.targets:
            cfg_repos.append(str(repo))
        cfg["repos"] = list(dict.fromkeys(cfg_repos))

    saved = config.save(cfg)
    term.status("ok", f"Saved config to {saved}")

    # Install into discovered repos (with consent unless --yes).
    if found.targets and _confirm(
        term,
        f"Install agent-workflows into {len(found.targets)} repo(s) now?",
        args.yes,
    ):
        try:
            source_root = engine.resolve_source_root(
                Path(args.source_root).expanduser()
                if getattr(args, "source_root", None)
                else None
            )
        except SystemExit as exc:
            term.status("fail", str(exc))
            return 1
        for repo in found.targets:
            # Same git diagnostics pre-flight as the other install paths (parity).
            if not _diagnostics_ok(repo, args):
                term.status("skip", f"{repo}: aborted at git pre-flight")
                continue
            # Shared per-repo shell: installs AND offers to commit (auto under --yes),
            # SystemExit-isolated. Before D85 setup staged files and never committed.
            _install_one(repo, source_root, args, term)

    _orient(term)
    return 0


def _orient(term: Term) -> None:
    term.line()
    term.heading("You are set up")
    term.line("The workflows are agent instructions your AI coding tool runs. Try:")
    term.line(
        "  /release-review, /assess <concern>, /advise <persona>, /verify, /setup-repo"
    )
    term.line("Or from any agent: 'Read and execute .agents/workflows/index.md'.")
    _teach(term)


# --------------------------------------------------------------------------------------
# dispatch
# --------------------------------------------------------------------------------------


def _run_plans(args: argparse.Namespace, term: Term) -> int:
    from . import plans as plans_mod

    root = (
        Path(args.dir).expanduser().resolve()
        if getattr(args, "dir", None)
        else Path.cwd()
    )

    # Validate --status up front so a typo teaches the valid set instead of silently
    # returning an empty board (assess-self-documentation S1). Handler-side (not argparse
    # choices=) to preserve normalize_status's legacy/alias tolerance.
    status_filter = getattr(args, "status_filter", None)
    if (
        status_filter
        and plans_mod.normalize_status(status_filter) not in plans_mod.RECOGNIZED
    ):
        valid = ", ".join(
            plans_mod.PRE_TERMINAL + plans_mod.TERMINAL + plans_mod.STANDING
        )
        term.status(
            "warn",
            f"Unrecognized --status '{status_filter}'. Valid readiness statuses: {valid}.",
        )
        return 2

    if not (root / ".agents" / "plans").is_dir():
        term.status("skip", f"No plans found (no .agents/plans/ under {root}).")
        return 0

    records = plans_mod.scan(root)

    if getattr(args, "pending", False):
        records = [r for r in records if r.disposition == "pending"]
    if status_filter:
        want = plans_mod.normalize_status(status_filter)
        records = [r for r in records if r.status == want]

    if getattr(args, "write_index", False):
        index_path = root / ".agents" / "plans" / "STATUS.md"
        index_path.write_text(
            plans_mod.render_status_index(root, records), encoding="utf-8"
        )
        term.status(
            "ok",
            f"Wrote {index_path.relative_to(root).as_posix()} ({len(records)} entries).",
        )
        return 0

    if not records:
        term.status("skip", "No matching plans.")
        return 0

    by_disp = plans_mod.group(records)
    term.kv("Total", f"{len(records)} plan/prompt file(s)")
    for disp in plans_mod.DISPOSITION_DIRS:
        statuses = by_disp.get(disp)
        if not statuses:
            continue
        count = sum(len(v) for v in statuses.values())
        term.line()
        term.heading(f"{disp}/ ({count})")
        for status in sorted(statuses, key=plans_mod._status_sort_key):
            recs = statuses[status]
            term.line(f"  {term.colorize(status, 'bold')} ({len(recs)})")
            for rec in sorted(recs, key=lambda r: r.path.name):
                term.line(f"    {rec.path.relative_to(root).as_posix()}")
    return 0


def _load_normalizer():
    """Import the plan-name normalizer script (it lives under the bundled workflow tree).

    Resolves the `.agents/workflows/` root via `_compat.packaged_source_root()` (installed
    wheel) or the repo root (source checkout / editable install), then loads the standalone
    script by path (it is a script, not an importable package module). Returns the module or
    None if it cannot be located/loaded.
    """

    import importlib.util

    from . import _compat

    root = _compat.packaged_source_root()
    if root is None:
        # Source checkout: .agents/workflows lives at the repo root (two levels up from here).
        root = Path(__file__).resolve().parent.parent / ".agents" / "workflows"
    script = root / "setup-repo" / "tools" / "normalize_plan_names.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("aw_normalize_plan_names", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_plan_names(args: argparse.Namespace, term: Term) -> int:
    normalizer = _load_normalizer()
    if normalizer is None:
        term.status("fail", "Could not locate the plan-name normalizer script.")
        return 1

    root = Path(args.dir).expanduser() if getattr(args, "dir", None) else Path.cwd()
    passthrough = ["--repo", str(root), "--format", getattr(args, "fmt", "text")]
    if getattr(args, "apply", False):
        passthrough.append("--apply")
    if getattr(args, "all_areas", False):
        passthrough.append("--all")
    for area in getattr(args, "area", None) or []:
        passthrough += ["--area", area]
    for glob in getattr(args, "exclude", None) or []:
        passthrough += ["--exclude", glob]
    if getattr(args, "no_default_excludes", False):
        passthrough.append("--no-default-excludes")
    if getattr(args, "include_nested", False):
        passthrough.append("--include-nested")
    if getattr(args, "rename_non_numeric", False):
        passthrough.append("--rename-non-numeric")
    if getattr(args, "assume_dates", False):
        passthrough.append("--assume-dates")

    # Delegate to the script's own main(argv); it prints its report and returns its exit code.
    return normalizer.main(passthrough)


def _run_leaks_configure(args: argparse.Namespace, term: Term) -> int:
    """Interactive leak-sanitizer config wizard (`--configure`, D98). Reads/writes the
    tracked allowlist + the gitignored user hints; never scans."""
    from pathlib import Path
    from . import leak_sanitizer_config as lsc

    # An interview needs a real terminal. Unlike --fix, there is no meaningful "accept
    # defaults" batch mode for authoring config (blindly confirming every toggle would flip
    # them ON), so --configure always requires an interactive TTY.
    if not sys.stdin.isatty():
        term.status(
            "warn",
            "sanitize --configure needs an interactive terminal. To configure "
            "non-interactively, edit .agents/local-leaks-allowlist.toml directly. Nothing changed.",
        )
        return 2

    repo_root = Path(getattr(args, "dir", None) or ".").resolve()

    def _confirm_q(question: str) -> bool:
        # assume_yes is intentionally NOT honored here: each toggle must reflect a real
        # choice, and the final write is a deliberate confirmation.
        return _confirm(term, question, assume_yes=False)

    summary = lsc.configure(repo_root, prompt=input, confirm=_confirm_q, emit=term.line)
    if summary["wrote"]:
        term.status(
            "ok",
            "Config updated. Re-run 'aw sanitize --configure' any time; it is safe.",
        )
    return 0


def _run_check_local_leaks(args: argparse.Namespace, term: Term) -> int:
    """Detect local leaks (D92/D93). Delegates to the unified agent_workflows.leak_sanitizer
    engine (local_leaks re-exports it). With --configure, launches the config wizard instead."""
    if getattr(args, "configure", False):
        return _run_leaks_configure(args, term)

    from . import leak_sanitizer

    passthrough = [getattr(args, "dir", None) or "."]
    if getattr(args, "history", False):
        passthrough.append("--history")
    if getattr(args, "max_commits", None) is not None:
        passthrough += ["--max-commits", str(args.max_commits)]
    if getattr(args, "wheel", None):
        passthrough += ["--wheel", args.wheel]
    if getattr(args, "staged", False):
        passthrough.append("--staged")
    if getattr(args, "warn", False):
        passthrough.append("--warn")
    if getattr(args, "agent", False):
        passthrough.append("--agent")
    if getattr(args, "fix", False):
        passthrough.append("--fix")
    if getattr(args, "assume_yes", False):
        passthrough.append("--yes")
    if getattr(args, "dry_run", False):
        passthrough.append("--dry-run")
    return leak_sanitizer.main(passthrough)


def _run_context(args: argparse.Namespace, term: Term) -> int:
    """Inspect resolved AW project context (spec Section 9)."""
    import json
    from agent_workflows.project_context import (
        resolve_project_context,
        ProjectContextError,
    )

    try:
        ctx = resolve_project_context(target_repo=getattr(args, "repo", None))
    except ProjectContextError as exc:
        if getattr(args, "json", False) or getattr(args, "agent", False):
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            term.status("fail", str(exc))
        return 1

    if getattr(args, "json", False) or getattr(args, "agent", False):
        print(ctx.to_json(indent=2))
        return 0

    term.heading("AW Resolved Project Context")
    term.status("info", f"Target Repo:       {ctx.target_repo}")
    term.status("info", f"Project ID:        {ctx.project_id}")
    term.status("info", f"Delivery Mode:     {ctx.delivery_mode}")
    term.status("info", f"AW_HOME:           {ctx.effective_aw_home}")
    term.status("info", f"Records Backend:   {ctx.records_backend}")
    term.status("info", f"Durability State:  {ctx.durability_state}")
    term.status("info", f"Framework Version: {ctx.effective_framework_version}")
    term.status("info", f"Enabled Hosts:     {', '.join(ctx.enabled_hosts)}")
    term.line()
    term.heading("Logical Roots:")
    for root_name, root_path in ctx.logical_roots.items():
        accessible = (
            "accessible" if ctx.root_accessibility.get(root_name) else "UNREADABLE"
        )
        term.status("info", f"  {root_name:<8} -> {root_path} ({accessible})")
    return 0


def _run_path(args: argparse.Namespace, term: Term) -> int:
    """Resolve physical path for a logical AW root (system|config|state|records)."""
    from agent_workflows.project_context import (
        resolve_project_context,
        ProjectContextError,
    )

    try:
        ctx = resolve_project_context(target_repo=getattr(args, "repo", None))
    except ProjectContextError as exc:
        if getattr(args, "agent", False):
            print(f"ERROR: {exc}")
        else:
            term.status("fail", str(exc))
        return 1

    root_name = getattr(args, "root", "")
    resolved_path = ctx.logical_roots.get(root_name)
    if not resolved_path:
        term.status("fail", f"Unknown logical root: {root_name}")
        return 1

    if getattr(args, "agent", False):
        print(resolved_path)
    else:
        term.status("ok", f"{root_name}: {resolved_path}")
    return 0


def _run_project_status(args: argparse.Namespace, term: Term) -> int:
    import json
    import os
    from agent_workflows import config
    from agent_workflows.project_registry import (
        find_project,
        load_registry,
        get_registry_path,
    )

    repo_path = getattr(args, "repo", None) or os.getcwd()
    aw_home, home_source = config.get_aw_home()
    reg_path = get_registry_path(str(aw_home))
    reg_data = load_registry(reg_path)
    match_res = find_project(repo_path, registry_data=reg_data, aw_home=str(aw_home))

    status_data = {
        "target_repo": repo_path,
        "effective_aw_home": str(aw_home),
        "aw_home_source": home_source,
        "matched": bool(match_res.entry),
        "match_kind": match_res.match_kind,
        "ambiguous": match_res.ambiguous,
        "project_entry": match_res.entry.to_dict() if match_res.entry else None,
        "candidate_hint": match_res.candidate_hint.to_dict()
        if match_res.candidate_hint
        else None,
    }

    if getattr(args, "json", False) or getattr(args, "agent", False):
        print(json.dumps(status_data, indent=2))
        return 0

    term.heading("AW Project Registry Status")
    term.status("info", f"Target Repo:       {repo_path}")
    term.status("info", f"AW_HOME:           {aw_home} ({home_source})")
    if match_res.entry:
        term.status(
            "ok",
            f"Matched Project:   {match_res.entry.project_id} (via {match_res.match_kind})",
        )
    elif match_res.ambiguous and match_res.candidate_hint:
        term.status(
            "warn",
            f"Candidate Hint:    {match_res.candidate_hint.project_id} (origin matched; requires 'aw project attach')",
        )
    else:
        term.status("warn", "No registered project association found.")
    return 0


def _run_project_attach(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows import config
    from agent_workflows.project_registry import register_or_update_project

    repo_path = getattr(args, "repo", None) or os.getcwd()
    pid = args.project_id
    aw_home, _ = config.get_aw_home()

    if getattr(args, "dry_run", False):
        term.status(
            "info",
            f"[DRY RUN] Would attach {repo_path} to project ID '{pid}' in {aw_home}",
        )
        return 0

    if not _confirm(
        term, f"Attach {repo_path} to project ID '{pid}'?", getattr(args, "yes", False)
    ):
        term.status("skip", "Attach cancelled; nothing changed.")
        return 0

    entry = register_or_update_project(repo_path, str(aw_home), project_id=pid)
    term.status(
        "ok", f"Successfully attached {repo_path} to project ID '{entry.project_id}'."
    )
    return 0


def _run_project_move(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows import config
    from agent_workflows.project_registry import register_or_update_project

    pid = args.project_id
    new_path = args.new_path
    aw_home, _ = config.get_aw_home()

    if getattr(args, "dry_run", False):
        term.status(
            "info",
            f"[DRY RUN] Would move association of project ID '{pid}' to {new_path}",
        )
        return 0

    if not _confirm(
        term,
        f"Move association of project ID '{pid}' to {new_path}?",
        getattr(args, "yes", False),
    ):
        term.status("skip", "Move cancelled; nothing changed.")
        return 0

    entry = register_or_update_project(new_path, str(aw_home), project_id=pid)
    term.status(
        "ok",
        f"Successfully moved project ID '{entry.project_id}' association to {new_path}.",
    )
    return 0


def _run_storage_status(args: argparse.Namespace, term: Term) -> int:
    import json
    import os
    from agent_workflows.storage import get_storage_status, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()
    try:
        st = get_storage_status(repo_path=repo_path)
    except StorageError as exc:
        if getattr(args, "json", False) or getattr(args, "agent", False):
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            term.status("fail", str(exc))
        return 1

    if getattr(args, "json", False) or getattr(args, "agent", False):
        print(json.dumps(st.to_dict(), indent=2))
        return 0

    term.heading("AW Records Storage Status")
    term.status("info", f"Target Repo:       {st.target_repo}")
    term.status("info", f"Project ID:        {st.project_id}")
    term.status("info", f"Backend:           {st.records_backend}")
    term.status("info", f"Records Path:      {st.records_path}")
    term.status("info", f"Durability State:  {st.durability_state}")
    term.status("info", f"Has Git:           {st.has_git}")
    term.status("info", f"Remote URL:        {st.remote_url or '(none)'}")
    term.status("info", f"Remote Ack:        {st.remote_acknowledged}")
    term.status("ok", f"Recommendation:    {st.recommendation}")
    return 0


def _run_storage_init(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows.storage import init_records_storage, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()

    if getattr(args, "dry_run", False):
        term.status(
            "info", f"[DRY RUN] Would initialize records storage for {repo_path}"
        )
        return 0

    if not _confirm(
        term,
        f"Initialize records storage for {repo_path}?",
        getattr(args, "yes", False),
    ):
        term.status("skip", "Storage initialization cancelled; nothing changed.")
        return 0

    try:
        st = init_records_storage(
            repo_path=repo_path,
            git_init=not getattr(args, "no_git", False),
            acknowledge_remote=getattr(args, "acknowledge_remote", False),
        )
    except StorageError as exc:
        term.status("fail", str(exc))
        return 1

    term.status(
        "ok",
        f"Successfully initialized records storage at {st.records_path} ({st.durability_state}).",
    )
    return 0


def _run_storage_attach(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows.storage import acknowledge_remote_durability, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()

    if getattr(args, "dry_run", False):
        term.status("info", f"[DRY RUN] Would update durability policy for {repo_path}")
        return 0

    if not _confirm(
        term,
        f"Update storage durability policy for {repo_path}?",
        getattr(args, "yes", False),
    ):
        term.status("skip", "Operation cancelled; nothing changed.")
        return 0

    try:
        st = acknowledge_remote_durability(
            repo_path=repo_path,
            acknowledge=getattr(args, "acknowledge_remote", False),
        )
    except StorageError as exc:
        term.status("fail", str(exc))
        return 1

    term.status("ok", f"Updated durability policy status: {st.durability_state}.")
    return 0


def _dispatch(argv: Optional[Sequence[str]]) -> int:
    parser = _build_parser()
    # Alias: `aw plans index` / `aw plans find` -> the `plans-index` / `plans-find` parsers, so the
    # ergonomic `plans <verb>` form works without colliding the `plans <dir>` positional with an
    # argparse subparser.
    argv_list = list(sys.argv[1:] if argv is None else argv)
    if (
        len(argv_list) >= 2
        and argv_list[0] == "plans"
        and argv_list[1] in ("index", "find", "set-assign", "mv", "archive")
    ):
        argv_list = ["plans-" + argv_list[1]] + argv_list[2:]
        argv = argv_list
    args = parser.parse_args(argv)

    term = Term(color=False if args.no_color else None)

    if args.command is None:
        # Smart default (D7): setup if unconfigured, else status + hints.
        if not config.is_configured():
            if sys.stdin.isatty():
                return _run_setup(
                    argparse.Namespace(
                        roots=None, recursive=False, yes=False, source_root=None
                    ),
                    term,
                )
            term.status("warn", "Not configured. Run 'aw setup' to get started.")
            return _run_status(term)
        _run_status(term)
        term.line()
        term.line(
            "Commands: install <dir>|all, setup, uninstall <dir>, list, status, plans, "
            "plan-names, check-local-leaks. See 'aw --help'."
        )
        return 0

    if args.command == "project":
        project_cmd = getattr(args, "project_command", None)
        if project_cmd == "status":
            return _run_project_status(args, term)
        if project_cmd == "attach":
            return _run_project_attach(args, term)
        if project_cmd == "move":
            return _run_project_move(args, term)
        parser.print_help()
        return 2
    if args.command == "storage":
        storage_cmd = getattr(args, "storage_command", None)
        if storage_cmd == "status":
            return _run_storage_status(args, term)
        if storage_cmd == "init":
            return _run_storage_init(args, term)
        if storage_cmd == "attach":
            return _run_storage_attach(args, term)
        parser.print_help()
        return 2
    if args.command == "install":
        return _run_install(args, term)
    if args.command == "uninstall":
        return _run_uninstall(args, term)
    if args.command == "list":
        return _run_list(args, term)
    if args.command == "status":
        return _run_status(term)
    if args.command == "setup":
        return _run_setup(args, term)
    if args.command == "plans":
        return _run_plans(args, term)
    if args.command == "plans-index":
        from agent_workflows import plans_index as pidx

        return pidx.run_index(args)
    if args.command == "plans-find":
        from agent_workflows import plans_index as pidx

        return pidx.run_find(args)
    if args.command == "plans-set-assign":
        from agent_workflows import plans_refs as prefs

        return prefs.run_set_assign(args)
    if args.command == "plans-mv":
        from agent_workflows import plans_refs as prefs

        return prefs.run_mv(args)
    if args.command == "plans-archive":
        from agent_workflows import plans_archive as parch

        return parch.run_archive(args)
    if args.command == "plan-names":
        return _run_plan_names(args, term)
    if args.command == "ipd":
        ipd_cmd = getattr(args, "ipd_command", None)
        if ipd_cmd == "lint":
            from agent_workflows import ipd_lint

            return ipd_lint.run_lint(args)
        if ipd_cmd == "scaffold":
            from agent_workflows import ipd_authoring

            return ipd_authoring.run_scaffold(args)
        if ipd_cmd == "sync":
            from agent_workflows import ipd_authoring

            return ipd_authoring.run_sync(args)
        parser.print_help()
        return 2
    if args.command == "research":
        research_cmd = getattr(args, "research_command", None)
        if research_cmd == "new":
            from agent_workflows import research_cmd as rc

            return rc.run_new(args)
        if research_cmd == "new-comparison":
            from agent_workflows import research_cmd as rc

            return rc.run_new_comparison(args)
        if research_cmd == "set-assign":
            from agent_workflows import research_refs as rr

            return rr.run_set_assign(args)
        if research_cmd == "mv":
            from agent_workflows import research_refs as rr

            return rr.run_mv(args)
        if research_cmd == "check-refs":
            from agent_workflows import research_refs as rr

            return rr.run_check_refs(args)
        if research_cmd == "index":
            from agent_workflows import research_index as ri

            return ri.run_index(args)
        if research_cmd == "find":
            from agent_workflows import research_index as ri

            return ri.run_find(args)
        if research_cmd == "promote":
            from agent_workflows import research_archive as ra

            return ra.run_promote(args)
        if research_cmd == "check-miscategorized":
            from agent_workflows import research_archive as ra

            return ra.run_check_miscategorized(args)
        parser.print_help()
        return 2
    if args.command == "context":
        return _run_context(args, term)
    if args.command == "path":
        return _run_path(args, term)
    if args.command == "attention":
        from agent_workflows import attention as att

        return att.run(args)
    if args.command == "specs":
        specs_cmd = getattr(args, "specs_command", None)
        if specs_cmd == "set":
            from agent_workflows import specs as sp

            return sp.run_set(args)
        if specs_cmd == "note":
            from agent_workflows import specs as sp

            return sp.run_note(args)
        if specs_cmd == "check":
            from agent_workflows import specs as sp

            return sp.run_check(args)
        if specs_cmd == "migrate":
            from agent_workflows import specs as sp

            return sp.run_migrate(args)
        parser.print_help()
        return 2
    if args.command == "archive":
        from agent_workflows import research_archive as ra

        return ra.run_archive(args)
    if args.command in ("check-local-leaks", "sanitize"):
        return _run_check_local_leaks(args, term)

    parser.print_help()
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Catches CTRL-C / EOF at any prompt and exits cleanly (D-CLI-UX).

    Returns the conventional 130 for a user interrupt instead of dumping a traceback.
    MUST return (not sys.exit) so in-process callers/tests reading the int keep working;
    ``__main__`` turns the return value into the process exit code.
    """

    try:
        return _dispatch(argv)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except EOFError:
        print("\nCancelled (end of input).", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
