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
import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__, config, discovery, engine, versioning
from .project_schema import DeliveryMode, Preset, RecordsBackend
from .term import Term


# --------------------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------------------


# Fuller per-command descriptions shown at the top of `aw <command> --help` (clianx-01
# E-06). Keyed by full command path. The short one-liner stays as `help=` in the parent
# listing; this is the multi-sentence "what it does, inputs/outputs, key flags, caveats".
_DESCRIPTIONS = {
    "install": (
        "Install or update the agent-workflows framework in one or more target repos "
        "(idempotent: safe to re-run). With no target, acts on the current directory; "
        "'install all' installs into every configured/discovered repo. Runs the policy "
        "wizard, writes the managed AGENTS.md pointer + host shims, and backs up before "
        "overwrite unless --no-backup. A repo on the never-install exclude list is skipped "
        "(non-interactive) or guarded (interactive). Never pushes."
    ),
    "setup": (
        "Guided first-run wizard: interview for search roots, discover git repos under "
        "them (honoring the ignore noise filter and the never-install exclude list), save "
        "the user config, and optionally install into the discovered repos. Use --root to "
        "supply roots non-interactively."
    ),
    "uninstall": (
        "Remove the agent-workflows framework from a repo (managed pointer block, host "
        "shims, scaffolded dirs), asking for confirmation first unless --yes. Preserves "
        "your own content; only the managed region is removed."
    ),
    "list": (
        "List the configured and discovered repos and each one's currency (installed, "
        "stale, current, not-installed). Read-only; makes no changes."
    ),
    "status": (
        "Show an environment and currency summary: resolved versions, config location, "
        "and per-repo install currency. Read-only diagnostics."
    ),
    "plans": (
        "Show a board of plan/IPD readiness Status grouped by lifecycle (pending/reviewed/"
        "approved/executed/...). Read-only view over .aw/records/plans. Alias of 'plans' verbs."
    ),
    "plans-index": (
        "Regenerate .aw/records/plans/INDEX.json (every plan, all fields) plus a browse-by-Set "
        "INDEX.md from plan front matter. With --check, fail (nonzero) on drift instead of "
        "rewriting (CI gate). Alias: 'plans index'."
    ),
    "plans-find": (
        "Query the plans manifest by --id/--set/--status/--disposition without reading the "
        "corpus (token-cheap). Alias: 'plans find'."
    ),
    "plans-set-assign": (
        "Group plans into a Set (shared Set id + assigned Order metadata); --rename also "
        "clusters the filenames. Dry-run by default. Alias: 'plans set-assign'."
    ),
    "plans-mv": (
        "Rename/re-slug one plan to the clustering filename grammar, preserving its stable "
        "Id. Dry-run by default. Alias: 'plans mv'."
    ),
    "plans-archive": (
        "Deep-shelve terminal plans into weekly shards (a targeted move or an aged sweep) "
        "to keep the active lanes small. Alias: 'plans archive'."
    ),
    "ipd": (
        "IPD (Implementation Plan Document) tooling for structure and state. Subcommands: "
        "'lint' (deterministic structural/state check), 'scaffold' (new skeleton), 'sync' "
        "(assign ids + validation skeletons)."
    ),
    "ipd lint": (
        "Deterministically lint an IPD's STRUCTURE and STATE only (heading order, E-*/V-* "
        "bijection, state legality, metadata) at a given --phase checkpoint. Read-only: no "
        "model, network, or writes. Exit 0=conforming, 1=conformance error, 2=could-not-run. "
        "A terminal-directory plan lints as legacy/not-evaluated. It proves nothing "
        "semantic (coverage, correctness, evidence)."
    ),
    "ipd scaffold": (
        "Write a new conformant IPD skeleton (child or orchestrator) with correct headings, "
        "metadata, and checklists. Dry-run (preview) by default; pass --apply to write."
    ),
    "ipd sync": (
        "Assign stable ids to new E-NEW execution leaves, append matching V-* validation "
        "skeletons (the E/V bijection), and advance the 'Highest E allocated' watermark. "
        "Dry-run by default; refuses if the watermark is below the largest existing E."
    ),
    "research": (
        "Research-artifact tooling for .aw/records/research. Subcommands create correctly "
        "named docs ('new'/'new-comparison'), regroup them ('set-assign'/'mv'), manage the "
        "manifest ('index'/'find'), and check/curate ('check-refs'/'promote'/etc.)."
    ),
    "research new": (
        "Create a correctly-named research doc (per the naming grammar) plus starter front "
        "matter for a given --kind/--slug/--model. Dry-run by default; --apply to write. "
        "Follow with 'research index' to refresh the manifest."
    ),
    "research new-comparison": (
        "Scaffold a multi-model comparison set: one prompt, one report per model, and a "
        "reconciliation doc, all sharing a set id. Dry-run by default."
    ),
    "research set-assign": (
        "Group research docs into a set (shared date + set-id with assigned NN order), "
        "preserving each doc's stable id6. Dry-run by default."
    ),
    "research mv": (
        "Rename/re-slug one research doc within the naming grammar, preserving its id6. "
        "Dry-run by default."
    ),
    "research check-refs": (
        "Report dangling <id6> citations (references to research docs that no longer "
        "resolve) across the scanned trees. Read-only detector; useful as a standalone gate."
    ),
    "research index": (
        "Regenerate the research INDEX.json and INDEX.md from doc front matter. With "
        "--check, fail (nonzero) on drift instead of rewriting (CI gate)."
    ),
    "research find": (
        "Query the research index by --id/--set/--topic/--status without reading the corpus "
        "(token-cheap lookup)."
    ),
    "research promote": (
        "Deliberately set a research doc's status (e.g. --to reference) and move it to the "
        "appropriate shard. Records the disposition change."
    ),
    "research check-miscategorized": (
        "Report archived-but-still-cited research docs (candidates that should be reference "
        "instead of archived). Read-only advisory."
    ),
    "context": (
        "Inspect the resolved AW project context: project id, delivery mode, AW_HOME, "
        "records backend, durability, enabled hosts, and the four logical roots. Read-only; "
        "--agent for machine-readable output."
    ),
    "path": (
        "Resolve and print the physical filesystem path for a logical AW root "
        "(system|config|state|records) for the target repo. --agent prints only the "
        "absolute path (no prose), suitable for scripting."
    ),
    "project": (
        "Owner verbs for AW project identity and the AW_HOME registry: 'status' (identity "
        "and matching), 'attach' (bind a repo to a project id), 'move' (update the target "
        "path association)."
    ),
    "project status": (
        "Inspect this repo's project identity and how it matches the AW_HOME registry "
        "(matched/unmatched, the bound entry). --json for machine-readable output."
    ),
    "project attach": (
        "Attach this repository to a specific project id in the registry. --yes "
        "auto-confirms. Use when a repo should share an existing project's external roots."
    ),
    "project move": (
        "Update a project's target-path association in the registry (e.g. after moving or "
        "renaming the checkout). --yes auto-confirms."
    ),
    "storage": (
        "Owner verbs for records storage backends and durability: 'status' (inspect), "
        "'init' (initialize storage + optional git), 'attach' (acknowledge/set durability "
        "policy)."
    ),
    "storage status": (
        "Inspect observable records-storage status and durability for the target repo "
        "(backend, location, versioned/unversioned). --json / --agent for machine output."
    ),
    "storage init": (
        "Initialize records storage for the target repo and, unless --no-git, run git init "
        "in the records directory. --acknowledge-remote records explicit acceptance of a "
        "remote durability policy. --dry-run previews."
    ),
    "storage attach": (
        "Acknowledge or set the records-storage durability policy for the target repo "
        "(e.g. --acknowledge-remote). --dry-run previews; --yes auto-confirms."
    ),
    "storage detach": (
        "Detach the private companion storage binding from the target repo, leaving the "
        "companion directory and its contents in place. --dry-run previews the change."
    ),
    "storage move": (
        "Move the private companion storage binding to a new directory given by --new-dir, "
        "updating the machine-local binding so records resolve to the relocated companion. "
        "--dry-run previews the change."
    ),
    "storage reattach": (
        "Reattach an existing private companion repository to the target repo by rebinding "
        "its --companion-dir, restoring records resolution after a clone or path change. "
        "--dry-run previews the change."
    ),
    "storage preflight": (
        "Run companion storage preflight checks for the target repo against --companion-dir "
        "(identity, reachability, durability) before attach or move. --json for machine output."
    ),
    "config": (
        "Manage the user-level CLI config. Currently exposes the never-install exclude "
        "blocklist via 'config exclude'."
    ),
    "config exclude": (
        "Manage the never-install exclude blocklist: repos that must never receive an "
        "install. Entries may be absolute repo paths or fnmatch globs. Distinct from the "
        "discovery-only 'ignore' noise filter. Subcommands: add, list, rm."
    ),
    "config exclude add": (
        "Add a repo path (e.g. ~/src/legacy-repo) or fnmatch glob (e.g. */vendored-tool) to "
        "the never-install exclude list. Stored ~-preserved; a duplicate is a no-op."
    ),
    "config exclude list": (
        "List the current never-install exclude entries (paths and globs), or report that "
        "the list is empty."
    ),
    "config exclude rm": (
        "Remove the entry matching the given repo path or entry (exact or glob) from the "
        "never-install exclude list. Returns nonzero if nothing matched."
    ),
    "todo": (
        "List the open operational AW actions (the action ledger). --all includes "
        "non-open (completed/dismissed) actions; --agent prints machine-readable output."
    ),
    "show": (
        "Inspect a single action document by ID (or ID@generation), printing its full "
        "current state and metadata."
    ),
    "complete": "Mark an operational action as completed (a lifecycle transition in the action ledger).",
    "dismiss": "Mark an operational action as dismissed (a lifecycle transition in the action ledger).",
    "reopen": "Reopen a completed or dismissed action, returning it to the open lane.",
    "history": "Show the lifecycle history (state transitions over time) of a single action.",
    "migrate-layout": (
        "Transactional AW layout migration and records-backend cutover, with a rollback "
        "journal. Moves/copies records to the chosen backend and updates the registry "
        "policy. Recoverable on failure; --dry-run previews."
    ),
    "attention": (
        "Read-only cross-tree attention view mapping every tracked .agents artifact's native "
        "status onto a ready/active/blocked/done/parked class. Prints a board (or --format "
        "json). --check fails closed on an invalid view (CI gate); --agent for machine output. "
        "Alias: 'aw att'. --all reveals the hidden done/parked groups."
    ),
    "backlog": (
        "Owner verbs for the attention-visible backlog tier (records/backlog): 'new' creates a "
        "committed/uncommitted backlog item, 'set' transitions its status (open/blocked/parked/done) "
        "and appends history, 'check' validates the tree fail-closed. Committed items surface in "
        "'aw attention'; parked 'maybes' stay hidden until --all."
    ),
    "backlog new": (
        "Create a conformant backlog item (dry-run by default; --apply to write). Owns the "
        "clustering filename + bullet metadata (Id/Status/Set/Priority/Kind/Summary, plus a typed "
        "Gate-Kind/Gate-Ref when --status blocked)."
    ),
    "backlog set": (
        "Transition a backlog item's status, moving the file between the open/blocked/parked/done "
        "directories, appending a workflow-history record. Moving to 'blocked' requires a typed "
        "--gate-kind/--gate-ref pair."
    ),
    "backlog check": (
        "Validate the backlog tree against the contract and fail closed: valid enums, "
        "status-mirrors-directory, gate present-and-valid iff blocked, unique id6, nonempty summary. "
        "--agent emits tab-separated drift records."
    ),
    "specs": (
        "Owner verbs for the specs tree: 'set' (transition status + typed gates, append "
        "history), 'note' (append history without a status change), 'check' (validate "
        "against the contract), 'migrate' (first-normalize a legacy status)."
    ),
    "specs set": (
        "Transition a spec's status (enforcing the legal transition table, the "
        "anti-self-approval floor, and typed deferral gates) and append a workflow-history "
        "record. Setting 'approved' requires an explicit --by-human attestation; "
        "'implemented' requires cited evidence."
    ),
    "specs note": (
        "Append a workflow-history record to a spec WITHOUT changing its status. Use to log "
        "a decision, review, or correction."
    ),
    "specs check": (
        "Validate one spec (or all specs) against the spec contract (status enum, required "
        "sections, gate typing) and fail closed on a violation. CI-friendly."
    ),
    "specs migrate": (
        "One-time first-normalization of a legacy/free-form spec status to the bare enum "
        "and canonical shape. Use only on pre-contract specs."
    ),
    "archive": (
        "Deliberately deep-shelve research docs: a targeted move, or a bare aged-and-uncited "
        "sweep (with a preview) that shelves stale, unreferenced research."
    ),
    "plan-names": (
        "Check (or, with --apply, fix) that plan/prompt filenames match the "
        "YYYYMMDD-HHMM-NN-<slug>.md naming convention. --check-style gate."
    ),
    "check-local-leaks": (
        "Detect (and, with --fix, rewrite) identifying info that must not appear in a public "
        "artifact: home paths, usernames, hostnames, private repo names, and session ids. "
        "Prints one record per finding; --agent for machine-readable output; exits nonzero "
        "on a fail. Alias: 'sanitize'."
    ),
    "sanitize": (
        "Alias of 'check-local-leaks': detect (and with --fix rewrite) identifying info "
        "(home paths, usernames, hostnames, private repo names, session ids) that must not "
        "appear in a public artifact. --agent for machine-readable output; exits nonzero on "
        "a fail."
    ),
}


def _apply_descriptions(parser: argparse.ArgumentParser) -> None:
    """Set each subparser's ``description`` from ``_DESCRIPTIONS`` (clianx-01 E-06).

    Walks every subparser by full command path and assigns the authored fuller
    description so ``aw <command> --help`` explains the command beyond the one-line help.
    Purely additive: it never changes registration order or dispatch.
    """

    def walk(node: argparse.ArgumentParser, prefix: str) -> None:
        for action in node._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, subparser in action.choices.items():
                    path = (prefix + " " + name).strip()
                    desc = _DESCRIPTIONS.get(path)
                    if desc:
                        subparser.description = desc
                    walk(subparser, path)

    walk(parser, "")


class _AlphaHelpFormatter(argparse.HelpFormatter):
    """Help formatter that lists subcommands alphabetically (clianx-01 E-05).

    Display-only: it sorts the sub-actions shown under a ``{cmd ...}`` listing by their
    name so ``--help`` is scannable, WITHOUT reordering how parsers were registered and
    WITHOUT affecting dispatch (argparse still routes by the parsed command name).
    """

    def _iter_indented_subactions(self, action):
        get_subactions = getattr(action, "_get_subactions", None)
        if get_subactions is not None:
            self._indent()
            for subaction in sorted(
                get_subactions(), key=lambda a: (a.dest or "", str(a.metavar or ""))
            ):
                yield subaction
            self._dedent()
        else:
            for subaction in super()._iter_indented_subactions(action):
                yield subaction


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
        formatter_class=_AlphaHelpFormatter,
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
        help="Install or update the framework in a repo (idempotent), creating the canonical .aw/ layout; 'install all' does every configured repo.",
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
        help="Path to source .aw/system or legacy .agents/workflows (dev/override).",
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
    p_install.add_argument(
        "--preset",
        choices=[p.value for p in Preset],
        help="Select physical placement preset: private-target (default), public-private-companion, clean-target, local-only.",
    )
    p_install.add_argument(
        "--delivery-mode",
        choices=[d.value for d in DeliveryMode],
        help="Select framework delivery mode.",
    )
    p_install.add_argument(
        "--records-backend",
        choices=[r.value for r in RecordsBackend],
        help="Select records storage location: repository (default), companion, home.",
    )
    p_install.add_argument(
        "--companion-dir",
        help="Path to companion repository if companion records backend or preset is selected.",
    )
    p_install.add_argument(
        "--to-aw",
        action="store_true",
        help="Migrate a detected legacy .agents/ layout to canonical .aw/ during install or update.",
    )
    p_install.add_argument(
        "--keep-legacy",
        action="store_true",
        help="Keep updating a detected legacy .agents/ layout in place with deprecation notice without migrating.",
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
    p_setup.add_argument(
        "--preset",
        choices=[p.value for p in Preset],
        help="Select physical placement preset: private-target (default), public-private-companion, clean-target, local-only.",
    )
    p_setup.add_argument(
        "--delivery-mode",
        choices=[d.value for d in DeliveryMode],
        help="Select framework delivery mode.",
    )
    p_setup.add_argument(
        "--records-backend",
        choices=[r.value for r in RecordsBackend],
        help="Select records storage location: repository (default), companion, home.",
    )
    p_setup.add_argument(
        "--companion-dir",
        help="Path to companion repository if companion records backend or preset is selected.",
    )
    p_setup.add_argument(
        "--to-aw",
        action="store_true",
        help="Migrate a detected legacy .agents/ layout to canonical .aw/ during setup.",
    )
    p_setup.add_argument(
        "--keep-legacy",
        action="store_true",
        help="Keep updating a detected legacy .agents/ layout in place with deprecation notice without migrating.",
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
        help="Also remove durable records scaffolding (plans/docs/prompts/comms under .aw/records/ or legacy .agents/); "
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
        help="(Re)generate .aw/records/plans/STATUS.md instead of printing.",
    )

    # The plans manifest verbs are separate top-level parsers (`plans-index`, `plans-find`) to avoid
    # colliding the `plans <dir>` positional with an argparse subparser; a thin `aw plans index` /
    # `aw plans find` alias is routed in `_dispatch` before the main parser runs (see below).
    p_plans_index = sub.add_parser(
        "plans-index",
        parents=[common],
        help="Regenerate .aw/records/plans/INDEX.json + a browse-by-Set INDEX.md; --check fails on drift. Alias: 'plans index'.",
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
        formatter_class=_AlphaHelpFormatter,
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
        help="Lint every plan under .aw/records/plans and report a per-disposition inventory.",
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
    p_ipd_scaffold.add_argument(
        "--path",
        default=None,
        help="Destination file path. Omit to derive the canonical clustered `.ipd.md` name into .aw/records/plans/pending/.",
    )
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
        formatter_class=_AlphaHelpFormatter,
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
        help="Inspect resolved AW project context, physical roots (.aw/system, .aw/records, .aw/config, .aw/state), and active storage policy.",
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
    p_context.add_argument(
        "--public",
        "--redact",
        action="store_true",
        dest="public",
        help="Redact absolute local paths and secrets for public-safe output.",
    )

    p_path = sub.add_parser(
        "path",
        parents=[common],
        help="Resolve physical filesystem path for a logical AW root (system | config | state | records).",
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
        formatter_class=_AlphaHelpFormatter,
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
        formatter_class=_AlphaHelpFormatter,
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
        "--companion-dir", default=None, help="Companion directory path to attach."
    )
    p_storage_attach.add_argument(
        "--classes",
        default=None,
        help="Comma-separated root classes (config,durable_state,records).",
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

    p_storage_detach = storage_sub.add_parser(
        "detach",
        parents=[common],
        help="Detach companion storage binding from target repo.",
    )
    p_storage_detach.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_detach.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying filesystem.",
    )

    p_storage_move = storage_sub.add_parser(
        "move",
        parents=[common],
        help="Move companion storage binding to new directory path.",
    )
    p_storage_move.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_move.add_argument(
        "--new-dir", required=True, help="New companion directory path."
    )
    p_storage_move.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying filesystem.",
    )

    p_storage_reattach = storage_sub.add_parser(
        "reattach", parents=[common], help="Reattach existing companion repository."
    )
    p_storage_reattach.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_reattach.add_argument(
        "--companion-dir", default=None, help="Companion directory path to reattach."
    )
    p_storage_reattach.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying filesystem.",
    )

    p_storage_preflight = storage_sub.add_parser(
        "preflight", parents=[common], help="Run companion storage preflight checks."
    )
    p_storage_preflight.add_argument(
        "--repo", default=None, help="Target repository path (default: current dir)."
    )
    p_storage_preflight.add_argument(
        "--companion-dir", required=True, help="Companion directory path."
    )
    p_storage_preflight.add_argument(
        "--json", action="store_true", help="Output preflight report as JSON."
    )

    p_config = sub.add_parser(
        "config",
        parents=[common],
        help="Manage user CLI config (the never-install exclude list).",
        formatter_class=_AlphaHelpFormatter,
    )
    config_sub = p_config.add_subparsers(dest="config_command")

    p_config_exclude = config_sub.add_parser(
        "exclude",
        parents=[common],
        help="Manage the never-install exclude blocklist (add/list/rm).",
    )
    exclude_sub = p_config_exclude.add_subparsers(dest="exclude_command")

    p_exclude_add = exclude_sub.add_parser(
        "add",
        parents=[common],
        help="Add a repo path or fnmatch glob to the never-install exclude list.",
    )
    p_exclude_add.add_argument(
        "path",
        help="Repo path (e.g. ~/src/legacy-repo) or fnmatch glob (e.g. */vendored-tool) "
        "to never install into.",
    )
    exclude_sub.add_parser(
        "list", parents=[common], help="List the current never-install exclude entries."
    )
    p_exclude_rm = exclude_sub.add_parser(
        "rm",
        parents=[common],
        help="Remove a matching entry from the never-install exclude list.",
    )
    p_exclude_rm.add_argument(
        "path", help="Repo path or entry to remove from the exclude list."
    )

    p_todo = sub.add_parser(
        "todo", parents=[common], help="List operational AW actions."
    )
    p_todo.add_argument("--agent", action="store_true", help="Machine-readable output.")
    p_todo.add_argument("--all", action="store_true", help="Include non-open actions.")

    p_show = sub.add_parser(
        "show",
        parents=[common],
        help="Inspect an action document by ID or ID@generation.",
    )
    p_show.add_argument("action_ref", help="Action ID or ID@generation.")

    p_complete = sub.add_parser(
        "complete", parents=[common], help="Mark an action as completed."
    )
    p_complete.add_argument("action_ref", help="Action ID or ID@generation.")

    p_dismiss = sub.add_parser(
        "dismiss", parents=[common], help="Mark an action as dismissed."
    )
    p_dismiss.add_argument("action_ref", help="Action ID or ID@generation.")

    p_reopen = sub.add_parser(
        "reopen", parents=[common], help="Reopen a completed or dismissed action."
    )
    p_reopen.add_argument("action_ref", help="Action ID or ID@generation.")

    p_history = sub.add_parser(
        "history",
        parents=[common],
        help="Show lifecycle history of an action.",
    )
    p_history.add_argument("action_ref", help="Action ID or ID@generation.")

    p_migrate = sub.add_parser(
        "migrate-layout",
        parents=[common],
        help="Transactional AW layout migration (moves legacy .agents/ to canonical .aw/).",
    )
    p_migrate.add_argument(
        "action",
        nargs="?",
        choices=[
            "inventory",
            "plan",
            "apply",
            "status",
            "resume",
            "rollback",
            "cleanup",
            "wizard",
        ],
        default=None,
        help="Action to perform: wizard (default guided flow), inventory, plan, apply, status, resume, rollback, cleanup.",
    )
    p_migrate.add_argument(
        "--config",
        default=None,
        help="Path to JSON configuration file providing answers for non-interactive migration.",
    )
    p_migrate.add_argument(
        "--target-backend",
        choices=["home", "companion", "repository"],
        default=None,
        help="Target records storage backend: repository (default), companion, home.",
    )
    p_migrate.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Additional legacy root to inventory (repeatable).",
    )
    p_migrate.add_argument(
        "--output",
        default=None,
        help="Write JSON output to file path.",
    )
    p_migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Show migration plan without mutating filesystem.",
    )
    p_migrate.add_argument(
        "--apply", action="store_true", help="Execute approved migration transaction."
    )
    p_migrate.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit high-warning confirmation for cleanup/apply.",
    )
    p_migrate.add_argument(
        "--fault-injection", default=None, help="Fault injection name for test harness."
    )
    p_migrate.add_argument(
        "--leftovers",
        choices=["keep", "remove", "defer"],
        default=None,
        help="Disposition for legacy material NOT moved by the migration: keep (leave in "
        "place), remove (delete), or defer (record for a later cleanup; the default). Never "
        "deletes without an explicit 'remove'.",
    )
    p_migrate.add_argument(
        "--rename-to-grammar",
        action="store_true",
        help="Also rename migrated durable records to the uniform .type.md naming grammar "
        "(opt-in; default off). Comms and research keep their own naming. When neither this flag "
        "nor a config 'rename_to_grammar' key is set, an interactive run asks; a non-interactive "
        "run leaves existing names (dual-read keeps them working).",
    )
    p_migrate.add_argument(
        "--json", action="store_true", help="Output migration plan as JSON."
    )
    p_migrate.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Non-interactive; auto-confirm all prompts (leftovers defaults to defer).",
    )

    p_attention = sub.add_parser(
        "attention",
        aliases=["att"],
        parents=[common],
        help="Read-only cross-tree attention view (board or JSON to stdout); --check fails closed. Alias: 'aw att'.",
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

    p_backlog = sub.add_parser(
        "backlog",
        parents=[common],
        help="Owner verbs for the attention-visible backlog tier. 'backlog new' creates an item; 'set' transitions status; 'check' validates.",
        formatter_class=_AlphaHelpFormatter,
    )
    backlog_sub = p_backlog.add_subparsers(dest="backlog_command")
    p_backlog_new = backlog_sub.add_parser(
        "new",
        parents=[common],
        description="Create a conformant backlog item (dry-run by default; --apply to write).",
        help="Create a backlog item (dry-run by default; --apply to write).",
    )
    p_backlog_new.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_backlog_new.add_argument(
        "--summary", default=None, help="One-line summary (required)."
    )
    p_backlog_new.add_argument(
        "--set",
        dest="set",
        default=None,
        help="Set id (default: a singleton from the item id).",
    )
    p_backlog_new.add_argument(
        "--status",
        default="open",
        help="open | blocked | parked | done (default: open).",
    )
    p_backlog_new.add_argument(
        "--priority", default="medium", help="high | medium | low (default: medium)."
    )
    p_backlog_new.add_argument(
        "--kind",
        default="chore",
        help="bug | feature | chore | security | followup (default: chore).",
    )
    p_backlog_new.add_argument(
        "--slug",
        default=None,
        help="Short descriptive kebab slug (default: derived from summary).",
    )
    p_backlog_new.add_argument(
        "--gate-kind",
        dest="gate_kind",
        default=None,
        help="Gate-Kind (required iff --status blocked).",
    )
    p_backlog_new.add_argument(
        "--gate-ref",
        dest="gate_ref",
        default=None,
        help="Gate-Ref (required iff --status blocked).",
    )
    p_backlog_new.add_argument("--body", default=None, help="Optional prose body.")
    p_backlog_new.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
    )

    p_backlog_set = backlog_sub.add_parser(
        "set",
        parents=[common],
        description="Transition a backlog item's status (moving it between open/blocked/parked/done) and append history.",
        help="Transition a backlog item's status + append history.",
    )
    p_backlog_set.add_argument("path", help="Backlog item file to transition.")
    p_backlog_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_backlog_set.add_argument(
        "--status", required=True, help="Target status: open | blocked | parked | done."
    )
    p_backlog_set.add_argument("--message", default="", help="History record message.")
    p_backlog_set.add_argument(
        "--gate-kind",
        dest="gate_kind",
        default=None,
        help="Gate-Kind (required when moving to blocked).",
    )
    p_backlog_set.add_argument(
        "--gate-ref",
        dest="gate_ref",
        default=None,
        help="Gate-Ref (required when moving to blocked).",
    )

    p_backlog_check = backlog_sub.add_parser(
        "check",
        parents=[common],
        description="Validate the backlog tree against the contract; fail closed.",
        help="Validate the backlog tree; fail closed.",
    )
    p_backlog_check.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_backlog_check.add_argument(
        "--agent",
        action="store_true",
        help="Machine-readable tab-separated drift output.",
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
        "--by-human",
        dest="by_human",
        action="store_true",
        help="Attest that a HUMAN approved this transition (records attributed approval; no TTY). For human-only transitions like reviewed -> approved.",
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

    _apply_descriptions(parser)
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


def _prompt_yes_no(prompt: str, default: bool) -> bool:
    """Interactive yes/no prompt with an explicit default on empty input.

    Unlike ``_confirm`` this does NOT consult ``assume_yes`` and never auto-answers: the
    exclude guard must decide the ``--yes``/non-interactive case itself (fail-safe skip),
    so this helper is only ever called on an interactive TTY. ``default=True`` renders
    ``[Y/n]`` (empty -> yes); ``default=False`` renders ``[y/N]`` (empty -> no).
    """

    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{prompt} {suffix} ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


def _exclude_guard(term: Term, repo_root: Path, args) -> str:
    """Guard an explicitly targeted repo against the never-install exclude blocklist.

    Returns one of:
      - "proceed": the repo is not excluded, or the user chose to continue anyway.
      - "skip": the repo is excluded and must NOT be installed (declined, or a fail-safe
        non-interactive/``--yes`` skip).

    Fail-safe contract (clianx-01 E-03 / OQ-02): a NON-interactive run or ``--yes`` NEVER
    silently installs into an excluded repo; it skips with a message. Interactively, it
    warns (colorized) and asks ``Continue anyway? [Y/n]`` (default YES, since the user
    explicitly asked to install here); on continue it then offers ``Remove <repo> from the
    exclude list? [Y/n]`` (default NO) and unexcludes on yes. This does NOT reuse
    ``_confirm`` (which auto-returns True under ``--yes`` and would defeat the guard).
    """

    cfg = config.load()
    excludes = config.expanded_excludes(cfg)
    if not discovery._is_excluded(repo_root.resolve(), excludes):
        return "proceed"

    term.status(
        "warn",
        f"{repo_root} is on the never-install exclude list.",
    )

    # Fail-safe: never auto-install into an excluded repo non-interactively / under --yes.
    if getattr(args, "yes", False) or not sys.stdin.isatty():
        term.status(
            "skip",
            f"{repo_root}: excluded; skipped (run 'aw config exclude rm <path>' or use "
            "an interactive install to override). Nothing changed.",
        )
        return "skip"

    if not _prompt_yes_no("Continue anyway?", default=True):
        term.status("skip", f"{repo_root}: excluded; declined. Nothing changed.")
        return "skip"

    # They chose to install anyway: offer to drop it from the exclude list.
    if _prompt_yes_no(f"Remove {repo_root} from the exclude list?", default=False):
        _exclude_remove(cfg, repo_root)
        term.status("ok", f"Removed {repo_root} from the exclude list.")
    return "proceed"


def _exclude_remove(cfg, repo_root: Path) -> None:
    """Remove any exclude entry that matches ``repo_root`` (exact or glob) and save."""

    rp = repo_root.resolve()
    kept = [
        entry
        for entry in cfg.get("exclude", [])
        if not discovery._is_excluded(
            rp, [os.path.expandvars(os.path.expanduser(str(entry)))]
        )
    ]
    cfg["exclude"] = kept
    config.save(cfg)


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

    # Record install history event & create initial setup-repo action (E-04)
    try:
        from agent_workflows.actions import ActionManager, record_install_history

        record_install_history(
            target_repo=str(repo_root),
            event_type="install" if outcome == "ok" else "check",
            details={
                "version": result.get("version", ""),
                "installed_files": len(result.get("installed", [])),
            },
        )
        mgr = ActionManager(target_repo=str(repo_root))
        try:
            mgr.create_action(
                action_id="setup-repo",
                generation=1,
                title="Setup repository stack-tailored conformance",
                description="Run the LLM '/setup-repo' workflow in this repo for stack-tailored conformance (CI, .gitignore, lifecycle contract).",
            )
        except Exception:
            pass  # Action already exists or already resolved
    except Exception:
        pass

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


def _handle_legacy_migration(
    repo_root: Path, args: argparse.Namespace, term: Term
) -> bool:
    """Detect and handle legacy .agents/-only layout before install/update.

    Returns True if legacy layout is kept (compatibility mode),
    or False if migrated to .aw/ or already .aw/ / fresh.
    """
    is_legacy_only = (repo_root / engine.WORKFLOWS_DIR).exists() and not (
        repo_root / engine.AW_SYSTEM_DIR
    ).exists()
    if not is_legacy_only:
        return False

    to_aw = getattr(args, "to_aw", False)
    keep_legacy = getattr(args, "keep_legacy", False)

    if to_aw:
        from agent_workflows.layout_migration import MigrationManager

        mgr = MigrationManager(target_repo=str(repo_root))
        mgr.execute_migration(target_backend="repository", leftover_disposition="defer")
        term.status("ok", f"{repo_root}: migrated legacy layout to .aw/")
        return False

    if keep_legacy:
        term.status(
            "warn",
            f"{repo_root}: legacy .agents/ layout is deprecated and will be removed in a future release; "
            "continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.",
        )
        return True

    # Interactive check
    is_interactive = sys.stdin.isatty() and not getattr(args, "yes", False)
    if is_interactive:
        term.heading("Legacy .agents/ layout detected")
        if _confirm(
            term,
            f"Migrate {repo_root} from legacy .agents/ to canonical .aw/ now?",
            False,
        ):
            from agent_workflows.layout_migration import MigrationManager

            mgr = MigrationManager(target_repo=str(repo_root))
            mgr.execute_migration(
                target_backend="repository", leftover_disposition="defer"
            )
            term.status("ok", f"{repo_root}: migrated legacy layout to .aw/")
            return False
        else:
            term.status(
                "warn",
                f"{repo_root}: legacy .agents/ layout is deprecated and will be removed in a future release; "
                "continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.",
            )
            return True

    # Unattended / non-interactive default (OQ-01 resolution)
    term.status(
        "warn",
        f"{repo_root}: legacy .agents/ layout is deprecated and will be removed in a future release; "
        "continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.",
    )
    return True


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

        # Never-install exclude guard (clianx-01 E-03): an explicitly targeted excluded
        # repo warns + asks to continue interactively, and is skipped fail-safe under
        # --yes / non-interactive. This runs BEFORE any policy/interview work.
        if _exclude_guard(term, repo_root, args) == "skip":
            continue

        kept_legacy = _handle_legacy_migration(repo_root, args, term)

        if not kept_legacy:
            # Resolve policy via install_wizard (E-01..E-05) for .aw/ layout
            from agent_workflows.install_wizard import (
                collect_policy_interactive,
                render_pre_write_plan,
                persist_project_policy,
                PolicyError,
            )

            explicit_preset = getattr(args, "preset", None)
            if (
                getattr(args, "yes", False)
                and not explicit_preset
                and not getattr(args, "delivery_mode", None)
            ):
                explicit_preset = Preset.PRIVATE_TARGET.value

            try:
                policy = collect_policy_interactive(
                    term=term,
                    repo_path=str(repo_root),
                    assume_yes=getattr(args, "yes", False),
                    explicit_preset=explicit_preset,
                    explicit_delivery=getattr(args, "delivery_mode", None),
                    explicit_backend=getattr(args, "records_backend", None),
                    explicit_companion=getattr(args, "companion_dir", None),
                )
            except PolicyError as exc:
                term.status("fail", str(exc))
                return 1

            if getattr(args, "dry_run", False):
                term.status(
                    "ok", f"[DRY RUN] Install policy pre-write plan for {repo_root}:"
                )
                term.line(render_pre_write_plan(policy, str(repo_root), term=term))
                term.status(
                    "ok", "[DRY RUN] No changes written to filesystem or Git state."
                )
                continue

            # Persist confirmed policy to .aw/config/project.json and local.json
            persist_project_policy(
                repo_path=str(repo_root),
                policy=policy,
                dry_run=False,
            )

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
        _handle_legacy_migration(repo, args, term)
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
    if (
        not (repo_root / engine.AW_SYSTEM_WORKFLOWS_DIR).is_dir()
        and not (repo_root / engine.WORKFLOWS_DIR).is_dir()
    ):
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
            roots,
            ignore=cfg.get("ignore", []),
            recursive=recursive,
            exclude=config.expanded_excludes(cfg),
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
        expanded_roots,
        ignore=cfg.get("ignore", []),
        recursive=args.recursive,
        exclude=config.expanded_excludes(cfg),
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
    for repo in found.excluded:
        term.status("skip", f"{repo} (excluded: never-install list)")

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
            _handle_legacy_migration(Path(repo), args, term)
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


def _run_config_exclude(args: argparse.Namespace, term: Term) -> int:
    """Manage the never-install exclude blocklist (clianx-01 E-04): add/list/rm."""

    sub = getattr(args, "exclude_command", None)
    cfg = config.load()
    current = list(cfg.get("exclude", []))

    if sub == "add":
        entry = config._preserve_home(str(args.path))
        if entry in current:
            term.status("ok", f"Already excluded: {entry}")
            return 0
        current.append(entry)
        cfg["exclude"] = current
        config.save(cfg)
        term.status("ok", f"Added to the never-install exclude list: {entry}")
        return 0

    if sub == "list":
        if not current:
            term.status("ok", "The never-install exclude list is empty.")
            return 0
        term.heading("Never-install exclude list")
        for e in current:
            term.line(f"  {e}")
        return 0

    if sub == "rm":
        want = config._preserve_home(str(args.path))
        target = config.expand_path(str(args.path)).resolve()
        kept = []
        removed = []
        for e in current:
            expanded = os.path.expandvars(os.path.expanduser(str(e)))
            if e == want or discovery._is_excluded(target, [expanded]):
                removed.append(e)
            else:
                kept.append(e)
        if not removed:
            term.status("warn", f"No exclude entry matched: {args.path}")
            return 1
        cfg["exclude"] = kept
        config.save(cfg)
        for e in removed:
            term.status("ok", f"Removed from the exclude list: {e}")
        return 0

    term.status("fail", "Usage: aw config exclude {add|list|rm} ...")
    return 2


def _run_plans(args: argparse.Namespace, term: Term) -> int:
    from . import plans as plans_mod
    from agent_workflows.project_context import (
        resolve_verb_repo_root,
        is_project_dir,
        no_project_message,
    )

    # Climb to the project root so `aw plans` works from any subdirectory; explicit --dir verbatim
    # (IPD awretrofit Order 06).
    explicit_dir = getattr(args, "dir", None)
    root = resolve_verb_repo_root(explicit_dir)
    if not explicit_dir and not is_project_dir(root):
        sys.stderr.write(no_project_message("plans") + "\n")
        return 3

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

    # Layout-aware (IPD awretrofit Order 01): resolve the plans dir (.aw/records/plans with a
    # legacy .agents/plans read-fallback) rather than gating on the vanished legacy path.
    plans_dir = plans_mod._resolve_area_dir(root, "plans")
    if not plans_dir.is_dir():
        term.status("skip", f"No plans found (no {plans_dir} under {root}).")
        return 0

    records = plans_mod.scan(root)

    if getattr(args, "pending", False):
        records = [r for r in records if r.disposition == "pending"]
    if status_filter:
        want = plans_mod.normalize_status(status_filter)
        records = [r for r in records if r.status == want]

    if getattr(args, "write_index", False):
        index_path = plans_dir / "STATUS.md"
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

    # Resolve the workflow bundle root layout-agnostically: engine.resolve_source_root prefers
    # the packaged/nested .aw/system (descending into workflows/) and falls back to the legacy
    # .agents/workflows source checkout. This works before AND after the physical-layout move,
    # where the bundle relocated from .agents/workflows/ to .aw/system/workflows/.
    try:
        root = engine.resolve_source_root(None)
    except SystemExit:
        return None
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
            "non-interactively, edit .aw/config/local-leaks-allowlist.toml directly "
            "(legacy .agents/local-leaks-allowlist.toml is still honored). Nothing changed.",
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
    """Inspect resolved AW project context (spec Section 9 & Order 02 E-05)."""
    import json
    from agent_workflows.project_context import (
        resolve_project_context,
        redact_public_context,
        ProjectContextError,
    )

    try:
        ctx = resolve_project_context(target_repo=getattr(args, "repo", None))
    except ProjectContextError as exc:
        if (
            getattr(args, "json", False)
            or getattr(args, "agent", False)
            or getattr(args, "public", False)
        ):
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            term.status("fail", str(exc))
        return 1

    if getattr(args, "public", False):
        redacted = redact_public_context(ctx.to_dict())
        print(json.dumps(redacted, indent=2))
        return 0

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
        # `aw path <root>` prints the single resolved absolute path (Order 01 contract);
        # record ROUTING detail (backend/commit-destination) is exposed by `aw storage`, not here.
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
    from agent_workflows.storage import (
        attach_companion,
        acknowledge_remote_durability,
        StorageError,
    )

    repo_path = getattr(args, "repo", None) or os.getcwd()
    companion_dir = getattr(args, "companion_dir", None)
    dry_run = getattr(args, "dry_run", False)
    classes_arg = getattr(args, "classes", None)
    selected_classes = (
        [c.strip() for c in classes_arg.split(",")] if classes_arg else None
    )

    if companion_dir:
        if dry_run:
            term.status(
                "info",
                f"[DRY RUN] Would attach companion at {companion_dir} to target repo {repo_path}",
            )
            return 0
        if not _confirm(
            term,
            f"Attach companion repository at {companion_dir} to target repo {repo_path}?",
            getattr(args, "yes", False),
        ):
            term.status("skip", "Attach operation cancelled; nothing changed.")
            return 0
        try:
            res = attach_companion(
                target_repo=repo_path,
                companion_dir=companion_dir,
                selected_root_classes=selected_classes,
                dry_run=False,
                acknowledge_remote=getattr(args, "acknowledge_remote", False),
            )
            term.status(
                "ok",
                f"Successfully attached companion at {res['companion_dir']} (project ID: {res['project_id']}).",
            )
            return 0
        except StorageError as exc:
            term.status("fail", str(exc))
            return 1

    if dry_run:
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

    term.status(
        "ok",
        f"Updated durability policy for {repo_path} (new state: {st.durability_state}).",
    )
    return 0


def _run_storage_detach(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows.storage import detach_companion, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()
    dry_run = getattr(args, "dry_run", False)

    if dry_run:
        term.status(
            "info",
            f"[DRY RUN] Would detach companion binding from target repo {repo_path}",
        )
        return 0

    try:
        res = detach_companion(target_repo=repo_path, dry_run=False)
        term.status(
            "ok",
            f"Detached companion binding for target repo {res['target_repo']} (durable data preserved).",
        )
        return 0
    except StorageError as exc:
        term.status("fail", str(exc))
        return 1


def _run_storage_move(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows.storage import move_companion, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()
    new_dir = getattr(args, "new_dir", None)
    dry_run = getattr(args, "dry_run", False)

    # --new-dir is optional in argparse but required for this verb; fail cleanly (and narrow the
    # type from Any|None to str for move_companion) rather than passing None (Order 05, S2-Q01).
    if not new_dir:
        term.status("fail", "storage move requires --new-dir <path>.")
        return 2

    if dry_run:
        term.status(
            "info",
            f"[DRY RUN] Would move companion binding to {new_dir} for target repo {repo_path}",
        )
        return 0

    try:
        res = move_companion(
            target_repo=repo_path, new_companion_dir=new_dir, dry_run=False
        )
        term.status(
            "ok",
            f"Moved companion binding for {res['target_repo']} to {res['new_companion_dir']}.",
        )
        return 0
    except StorageError as exc:
        term.status("fail", str(exc))
        return 1


def _run_storage_reattach(args: argparse.Namespace, term: Term) -> int:
    import os
    from agent_workflows.storage import reattach_companion, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()
    companion_dir = getattr(args, "companion_dir", None)
    dry_run = getattr(args, "dry_run", False)

    if not companion_dir:
        term.status("fail", "--companion-dir is required for reattach.")
        return 1

    if dry_run:
        term.status(
            "info",
            f"[DRY RUN] Would reattach companion at {companion_dir} to target repo {repo_path}",
        )
        return 0

    try:
        res = reattach_companion(
            target_repo=repo_path, companion_dir=companion_dir, dry_run=False
        )
        term.status(
            "ok",
            f"Reattached companion at {res['companion_dir']} to target repo {res['target_repo']}.",
        )
        return 0
    except StorageError as exc:
        term.status("fail", str(exc))
        return 1


def _run_storage_preflight(args: argparse.Namespace, term: Term) -> int:
    import json
    import os
    from agent_workflows.storage import validate_companion_preflight, StorageError

    repo_path = getattr(args, "repo", None) or os.getcwd()
    companion_dir = getattr(args, "companion_dir", None)

    # --companion-dir is optional in argparse but required for this verb; fail cleanly (and narrow
    # the type from Any|None to str) rather than passing None (Order 05, S2-Q01).
    if not companion_dir:
        term.status("fail", "storage preflight requires --companion-dir <path>.")
        return 2

    try:
        report = validate_companion_preflight(
            target_repo=repo_path, companion_dir=companion_dir
        )
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
            return 0
        term.status(
            "ok", f"Companion preflight passed for {companion_dir} -> {repo_path}."
        )
        if report.get("warnings"):
            for w in report["warnings"]:
                term.status("warn", f"Warning: {w}")
        return 0
    except StorageError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(exc), "valid": False}, indent=2))
            return 1
        term.status("fail", f"Preflight failed: {exc}")
        return 1


def _run_todo(args: argparse.Namespace, term: Term) -> int:
    import json
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        status_filter = None if getattr(args, "all", False) else "open"
        actions = mgr.list_actions(status_filter=status_filter)
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1

    if getattr(args, "agent", False):
        out = [
            {
                "id": a.id,
                "generation": a.generation,
                "status": a.status,
                "title": a.title,
            }
            for a in actions
        ]
        print(json.dumps(out, indent=2))
        return 0

    term.heading("Operational Actions (AW Todo)")
    if not actions:
        term.status("ok", "No pending operational actions.")
        return 0

    for a in actions:
        term.status(a.status, f"{a.id} (v{a.generation}): {a.title}")
    return 0


def _run_show(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        status, path = mgr.find_action_file(args.action_ref)
        content = path.read_text(encoding="utf-8")
        print(content)
        return 0
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1


def _run_complete(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        doc = mgr.transition_action(args.action_ref, "completed")
        term.status("ok", f"Completed action {doc.id} (v{doc.generation}).")
        return 0
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1


def _run_dismiss(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        doc = mgr.transition_action(args.action_ref, "dismissed")
        term.status("ok", f"Dismissed action {doc.id} (v{doc.generation}).")
        return 0
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1


def _run_reopen(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        doc = mgr.transition_action(args.action_ref, "open")
        term.status("ok", f"Reopened action {doc.id} (v{doc.generation}).")
        return 0
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1


def _run_action_history(args: argparse.Namespace, term: Term) -> int:
    from agent_workflows.actions import ActionManager, ActionError

    try:
        mgr = ActionManager()
        status, path = mgr.find_action_file(args.action_ref)
        term.heading(f"Action History for {args.action_ref}")
        term.status("info", f"Current Status: {status}")
        term.status("info", f"File Path:      {path}")
        return 0
    except ActionError as exc:
        term.status("fail", str(exc))
        return 1


def _run_migrate_layout(args: argparse.Namespace, term: Term) -> int:
    import json
    import os
    import sys
    import io
    from pathlib import Path
    from tools.awphysical import aw_layout_inventory as inv_mod
    from agent_workflows.layout_migration import MigrationManager, MigrationError

    repo_path = Path(os.getcwd())
    action = getattr(args, "action", None)
    output = getattr(args, "output", None)
    json_out = getattr(args, "json", False)

    # 1. Parse --config file if supplied (JSON only per OQ-01 / spec S13)
    config_backend = None
    config_leftovers = None
    config_roots: list[str] = []
    config_confirm = None
    config_rename = None

    config_path = getattr(args, "config", None)
    if config_path:
        cp = Path(config_path).expanduser().resolve()
        if not cp.is_file():
            term.status("fail", f"Config file not found: {config_path}")
            return 1
        try:
            config_data = json.loads(cp.read_text(encoding="utf-8"))
        except Exception as exc:
            term.status("fail", f"Invalid JSON in config file {config_path}: {exc}")
            return 1
        if not isinstance(config_data, dict):
            term.status(
                "fail", f"Config file must contain a JSON object: {config_path}"
            )
            return 1

        raw_b = (
            config_data.get("target_backend")
            or config_data.get("target-backend")
            or config_data.get("backend")
        )
        if raw_b:
            raw_b_str = str(raw_b).strip().lower()
            preset_backend_map = {
                "private-target": "repository",
                "public-private-companion": "companion",
                "clean-target": "home",
                "local-only": "home",
                "repository": "repository",
                "companion": "companion",
                "home": "home",
            }
            if raw_b_str not in preset_backend_map:
                term.status("fail", f"Invalid target_backend in config: {raw_b}")
                return 1
            config_backend = preset_backend_map[raw_b_str]

        raw_l = (
            config_data.get("leftovers")
            or config_data.get("leftover_disposition")
            or config_data.get("leftovers_disposition")
        )
        if raw_l:
            raw_l_str = str(raw_l).strip().lower()
            if raw_l_str not in ("keep", "remove", "defer"):
                term.status("fail", f"Invalid leftovers in config: {raw_l}")
                return 1
            config_leftovers = raw_l_str

        raw_r = config_data.get("roots") or config_data.get("root")
        if raw_r:
            if isinstance(raw_r, str):
                config_roots = [raw_r]
            elif isinstance(raw_r, list):
                config_roots = [str(item) for item in raw_r]

        raw_c = config_data.get("confirm")
        if raw_c is None:
            raw_c = config_data.get("yes")
        if raw_c is not None:
            config_confirm = bool(raw_c)

        raw_rename = config_data.get("rename_to_grammar")
        if raw_rename is None:
            raw_rename = config_data.get("rename-to-grammar")
        if raw_rename is not None:
            config_rename = bool(raw_rename)

    # 2. Formal precedence: explicit CLI flags OVERRIDE --config keys OVERRIDE defaults
    cli_backend = getattr(args, "target_backend", None)
    selected_backend = cli_backend or config_backend or "repository"

    cli_leftovers = getattr(args, "leftovers", None)
    selected_leftovers = cli_leftovers or config_leftovers or "defer"

    cli_roots = list(getattr(args, "root", []) or [])
    all_roots = cli_roots + config_roots

    cli_confirm = (
        getattr(args, "confirm", False)
        or getattr(args, "yes", False)
        or getattr(args, "apply", False)
    )
    resolved_confirm = bool(cli_confirm or (config_confirm is True))

    # Rename-on-migrate (backlog u9cicx / awnaming OQ-02, ask-then-offer): the CLI flag (True when
    # present) OVERRIDES the config key OVERRIDES "unresolved" (None). When unresolved, ASK in an
    # interactive run (a TTY), else default OFF (never rename silently). Resolved to a concrete bool
    # HERE, at the CLI layer that owns the terminal, then passed to execute_migration.
    if getattr(args, "rename_to_grammar", False):
        selected_rename = True
    elif config_rename is not None:
        selected_rename = bool(config_rename)
    elif sys.stdin.isatty():
        selected_rename = _confirm(
            term,
            "Also rename migrated records to the uniform .type.md grammar? "
            "(default: no, leave existing names; dual-read keeps them working)",
            assume_yes=False,
        )
    else:
        selected_rename = False

    # 3. Explicit sub-actions (inventory, status, resume, rollback, cleanup)
    if action == "inventory":
        roots = inv_mod._default_roots(repo_path)
        for r_arg in all_roots:
            roots.append(inv_mod.parse_root(r_arg, repo_path))
        inv_res = inv_mod.inventory(
            repo_path, roots, include_paths=getattr(args, "include_root_paths", False)
        )
        if output:
            inv_mod._atomic_json(Path(output).expanduser().absolute(), inv_res)
        elif json_out:
            print(json.dumps(inv_res, indent=2, sort_keys=True))
        else:
            term.heading("AW Layout Inventory")
            term.status("info", f"Total Items: {len(inv_res.get('items', []))}")
            term.status(
                "ok" if inv_res.get("valid") else "fail",
                f"Inventory Valid: {inv_res.get('valid')}",
            )
        return 0 if inv_res.get("valid") else 2

    mgr = MigrationManager(target_repo=str(repo_path))
    fault_inj = getattr(args, "fault_injection", None)

    if action == "status":
        st = mgr.status_migration()
        if json_out:
            print(json.dumps(st, indent=2))
        else:
            term.heading("AW Layout Migration Status")
            term.status("info", f"Active Transaction: {st.get('active')}")
            term.status("info", f"Transaction ID:    {st.get('transaction_id')}")
            term.status("info", f"Status:            {st.get('status')}")
            term.status(
                "info", f"Checkpoint:        {st.get('last_verified_checkpoint')}"
            )
            term.status("info", f"Authority:         {st.get('authority')}")
        return 0

    if action == "resume":
        try:
            res = mgr.resume_migration(fault_injection=fault_inj)
            if json_out:
                print(json.dumps(res, indent=2))
            else:
                term.status("ok", f"Resumed migration: {res.get('status')}")
            return 0
        except MigrationError as exc:
            if json_out:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                term.status("fail", str(exc))
            return 1

    if action == "rollback":
        try:
            res = mgr.rollback_migration(fault_injection=fault_inj)
            if json_out:
                print(json.dumps(res, indent=2))
            else:
                term.status("ok", f"Rolled back migration: {res.get('status')}")
            return 0
        except MigrationError as exc:
            if json_out:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                term.status("fail", str(exc))
            return 1

    if action == "cleanup":
        try:
            res = mgr.cleanup_migration(
                confirm=resolved_confirm, fault_injection=fault_inj
            )
            if json_out:
                print(json.dumps(res, indent=2))
            elif res.get("status") == "preview":
                term.heading("AW Layout Legacy Source Cleanup (PREVIEW)")
                term.status(
                    "info",
                    f"Items to remove: {len(res.get('would_remove', []))}",
                )
                for p in res.get("would_remove", []):
                    term.status("info", f"  - {p}")
                term.status("warn", res.get("message", ""))
            else:
                term.status(
                    "ok",
                    f"Cleaned up legacy sources: {len(res.get('removed', []))} items removed.",
                )
            return 0
        except MigrationError as exc:
            if json_out:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                term.status("fail", str(exc))
            return 1

    # 4. Preview / dry-run path selection: plan action or explicit --dry-run
    dry_run_requested = getattr(args, "dry_run", False)
    if action == "plan" or dry_run_requested:
        roots = inv_mod._default_roots(repo_path)
        for r_arg in all_roots:
            roots.append(inv_mod.parse_root(r_arg, repo_path))
        inv_res = inv_mod.inventory(
            repo_path, roots, include_paths=getattr(args, "include_root_paths", False)
        )
        map_res = inv_mod.build_migration_map(
            repo_path, inv_res, target_backend=selected_backend
        )
        risk_res = inv_mod.analyze_migration_risks(repo_path, inv_res, map_res)
        plan_doc = {
            "schema_version": inv_mod.SCHEMA_VERSION,
            "inventory": inv_res,
            "migration_map": map_res,
            "risk_analysis": risk_res,
            "valid": inv_res.get("valid", False)
            and map_res.get("valid", False)
            and risk_res.get("valid", False),
        }
        if output:
            inv_mod._atomic_json(Path(output).expanduser().absolute(), plan_doc)
        elif json_out or action == "plan":
            print(json.dumps(plan_doc, indent=2, sort_keys=True))
        else:
            term.heading("AW Layout Migration Plan")
            term.status("info", f"Target Backend: {selected_backend}")
            term.status("info", f"Total Items:    {risk_res['item_counts']['total']}")
            term.status("info", f"Total Bytes:    {risk_res['total_bytes']}")
            term.status(
                "ok" if plan_doc["valid"] else "fail",
                f"Plan Valid:     {plan_doc['valid']}",
            )
        return 0 if plan_doc["valid"] else 2

    # 5. Direct apply sub-action (action == "apply")
    if action == "apply":
        try:
            mgr.execute_migration(
                target_backend=selected_backend,
                dry_run=False,
                fault_injection=fault_inj,
                leftover_disposition=selected_leftovers,
                rename_to_grammar=selected_rename,
            )
        except MigrationError as exc:
            if json_out:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                term.status("fail", str(exc))
            return 1
        term.status("ok", "Successfully executed layout migration.")
        return 0

    # 6. Default Wizard flow (action is None or action == "wizard")
    is_interactive = not resolved_confirm and (
        (hasattr(sys.stdin, "isatty") and sys.stdin.isatty())
        or isinstance(sys.stdin, io.StringIO)
    )

    if is_interactive:
        # Step 1: Read-only inventory and plan preview
        roots = inv_mod._default_roots(repo_path)
        for r_arg in all_roots:
            roots.append(inv_mod.parse_root(r_arg, repo_path))
        inv_res = inv_mod.inventory(
            repo_path, roots, include_paths=getattr(args, "include_root_paths", False)
        )
        map_res = inv_mod.build_migration_map(
            repo_path, inv_res, target_backend=selected_backend
        )
        risk_res = inv_mod.analyze_migration_risks(repo_path, inv_res, map_res)
        total_items = risk_res["item_counts"]["total"]
        total_bytes = risk_res["total_bytes"]

        term.heading("AW Layout Migration Wizard")
        term.status(
            "info",
            f"Found {total_items} legacy item(s) to migrate ({total_bytes} bytes).",
        )

        # Step 2: Destination / backend choice (reuse install_wizard backend choices)
        term.line()
        term.line("Select records destination/backend:")
        term.line(
            "  [1] repository (RECOMMENDED): Target repository carries records (.aw/records). Best for private repos."
        )
        term.line("  [2] companion: Store records in a private companion repository.")
        term.line(
            "  [3] home: Store records in AW home directory (~/.aw/records). Zero records in target repo."
        )
        default_b_choice = (
            "1"
            if selected_backend == "repository"
            else ("2" if selected_backend == "companion" else "3")
        )
        try:
            b_choice = input(f"Select backend [{default_b_choice}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            b_choice = default_b_choice
        if not b_choice:
            b_choice = default_b_choice
        backend_map = {
            "1": "repository",
            "2": "companion",
            "3": "home",
            "repository": "repository",
            "companion": "companion",
            "home": "home",
            "private-target": "repository",
            "public-private-companion": "companion",
            "clean-target": "home",
            "local-only": "home",
        }
        selected_backend = backend_map.get(b_choice.lower(), selected_backend)

        # Step 3: Leftover disposition
        term.line()
        term.line(
            "Post-move leftover disposition (legacy material not moved by migration):"
        )
        term.line(
            "  [1] defer (RECOMMENDED): Record leftover files for later cleanup without deleting now"
        )
        term.line("  [2] keep: Keep leftover legacy files in place without recording")
        term.line("  [3] remove: Permanently delete leftover legacy files after move")
        default_l_choice = (
            "1"
            if selected_leftovers == "defer"
            else ("2" if selected_leftovers == "keep" else "3")
        )
        try:
            l_choice = input(f"Select disposition [{default_l_choice}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            l_choice = default_l_choice
        if not l_choice:
            l_choice = default_l_choice
        leftovers_map = {
            "1": "defer",
            "2": "keep",
            "3": "remove",
            "defer": "defer",
            "keep": "keep",
            "remove": "remove",
        }
        selected_leftovers = leftovers_map.get(l_choice.lower(), selected_leftovers)

        # Step 4: Final Pre-write Preview & Confirmation
        term.line()
        term.heading("Migration Plan Preview")
        term.status("info", f"Target Backend:        {selected_backend}")
        term.status("info", f"Leftover Disposition:  {selected_leftovers}")
        term.status("info", f"Total Items to Move:   {total_items}")
        term.status("info", f"Total Bytes:           {total_bytes}")
        term.line()

        try:
            conf = (
                input("Confirm and execute layout migration? [y/N]: ").strip().lower()
            )
        except (EOFError, KeyboardInterrupt):
            conf = "n"

        if conf not in ("y", "yes"):
            term.status("skip", "Migration cancelled; nothing changed.")
            return 1

        # Step 5: Execute Migration (move-based apply)
        try:
            mgr.execute_migration(
                target_backend=selected_backend,
                dry_run=False,
                fault_injection=fault_inj,
                leftover_disposition=selected_leftovers,
                rename_to_grammar=selected_rename,
            )
        except MigrationError as exc:
            if json_out:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                term.status("fail", str(exc))
            return 1
        term.status("ok", "Successfully executed layout migration.")
        return 0

    # Non-interactive execution: Fail-closed if confirmation is missing
    if not resolved_confirm:
        term.status(
            "fail",
            "Non-interactive migration requires explicit confirmation (--yes or --confirm).",
        )
        return 1

    try:
        mgr.execute_migration(
            target_backend=selected_backend,
            dry_run=False,
            fault_injection=fault_inj,
            leftover_disposition=selected_leftovers,
            rename_to_grammar=selected_rename,
        )
    except MigrationError as exc:
        if json_out:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            term.status("fail", str(exc))
        return 1
    term.status("ok", "Successfully executed layout migration.")
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
            "Commands: install <dir>|all, setup, todo, complete, dismiss, status, plans, "
            "check-local-leaks. See 'aw --help'."
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
        if storage_cmd == "detach":
            return _run_storage_detach(args, term)
        if storage_cmd == "move":
            return _run_storage_move(args, term)
        if storage_cmd == "reattach":
            return _run_storage_reattach(args, term)
        if storage_cmd == "preflight":
            return _run_storage_preflight(args, term)
        parser.print_help()
        return 2
    if args.command == "config":
        if getattr(args, "config_command", None) == "exclude":
            return _run_config_exclude(args, term)
        parser.print_help()
        return 2
    if args.command == "todo":
        return _run_todo(args, term)
    if args.command == "show":
        return _run_show(args, term)
    if args.command == "complete":
        return _run_complete(args, term)
    if args.command == "dismiss":
        return _run_dismiss(args, term)
    if args.command == "reopen":
        return _run_reopen(args, term)
    if args.command == "history":
        return _run_action_history(args, term)
    if args.command == "migrate-layout":
        return _run_migrate_layout(args, term)
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
    if args.command in ("attention", "att"):
        from agent_workflows import attention as att

        return att.run(args)

    if args.command == "backlog":
        from agent_workflows import backlog as backlog_mod

        backlog_cmd = getattr(args, "backlog_command", None)
        if backlog_cmd == "new":
            return backlog_mod.run_new(args)
        if backlog_cmd == "set":
            return backlog_mod.run_set(args)
        if backlog_cmd == "check":
            return backlog_mod.run_check(args)
        print("usage: aw backlog {new|set|check}", file=sys.stderr)
        return 2
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
