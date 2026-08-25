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
import io
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, List, Optional, Union

from . import __version__, config, discovery, engine, versioning
from .project_schema import DeliveryMode, Preset, RecordsBackend
from .result_types import ConflictingFlagsError, select_output
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
    "list-repos": (
        "List the configured and discovered repos and each one's currency (installed, "
        "stale, current, not-installed). Read-only; makes no changes. --agent / --json "
        "emits machine-readable JSON."
    ),
    "normalize-lanes": (
        "Rename any prompts/comms 'local/' quarantine lane to 'untracked/' across both layouts "
        "(.aw/records/ and legacy .agents/), preserving contents and ensuring a nested .gitignore "
        "ignores 'untracked/'. Retroactive + idempotent; needs no reinstall."
    ),
    "doctor": (
        "Read-only deep repo inspection: aggregate every existing check signal (attention view "
        "validity, git working-tree state, installed-vs-packaged version drift) into one Drift "
        "report. Exit 0 clean, 1 findings; --agent for machine-readable output."
    ),
    "status": (
        "Show an environment and currency summary: resolved versions, config location, "
        "git working-tree status, attention summaries, and per-repo install currency. "
        "Read-only diagnostics; --agent / --json emits machine-readable JSON."
    ),
    "run": (
        "Run ledger inspection and verification tooling: 'show' (inspect run state and completion "
        "predicates), 'evidence' (inspect captured provenance envelopes and tool events), 'verify-ledger' "
        "(verify hash chain integrity and evidence validity). Read-only; makes no writes."
    ),
    "run show": (
        "Inspect a workflow run's ledger, steps, verifier decisions, and completion predicate status. "
        "Read-only; makes no writes. Exit 0 complete, 1 incomplete, 2 corrupted or missing."
    ),
    "run evidence": (
        "List and validate all captured evidence envelopes, tool events, and artifact refs in a run ledger. "
        "Exit 0 all valid, 1 invalid/missing evidence, 2 corrupted or missing."
    ),
    "run verify-ledger": (
        "Verify SHA-256 hash chaining, sequence continuity, schema conformance, and evidence validity "
        "across a run ledger. Exit 0 clean, 1 invalid evidence, 2 corrupted chain."
    ),
    "exclude": (
        "Exclude specified repositories from agent-workflows management. "
        "Syntax: 'aw exclude [repo|repos] repodir1 [repodir2 ...]' (or bare 'aw exclude' to list)."
    ),
    "include": (
        "Include specified repositories in agent-workflows management. "
        "Syntax: 'aw include [repo|repos] repodir1 [repodir2 ...]' (or bare 'aw include' to list)."
    ),
    "ipd": (
        "Work with IPDs (Implementation Plan Documents: the structured plan files under "
        ".aw/records/plans/ that describe a change as numbered execution + validation steps). "
        "Subcommands: 'board' (show the plan board; also bare 'aw ipd'), 'lint' (deterministic "
        "structural/state check), 'scaffold' (create a new conformant skeleton), 'sync' (assign "
        "step ids + validation skeletons)."
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
        "Inspect a record or action and print its full content. Resolves the given selector as a "
        "RECORDS artifact first (an id6 like pp6y76, a set id, a filename fragment, or a status, "
        "across plans/specs/research/backlog/prompts/walkthroughs/roadmaps), and falls back to the "
        "operational action ledger (an action id, or id@generation) if nothing matches. Use --dir to "
        "point the records lookup at a specific repo."
    ),
    "record-history": "Print a record's full chronological workflow history from the global .aw/records/history.jsonl sidecar, looked up by its 6-char id6.",
    "check": "Validate the artifacts of a given TYPE (plans, specs, ...) against their contract; exit 0 clean, 1 findings, 2 cannot-run.",
    "find": "Find artifacts of a given TYPE by selector (id6, status, Set, filename fragment), or across all types when omitted.",
    "search": "Search the artifacts of a given TYPE for matching content (regex-enabled), or across all types when omitted. Groups matches by file with color highlighting.",
    "index": "Rebuild and print the manifest/index for a given artifact TYPE.",
    "rename": "Rename or move an artifact of a given TYPE, rewriting references to it across the repo.",
    "group": "Assign an artifact of a given TYPE to a Set/group, re-clustering its name.",
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
        "Owner verbs for the design specifications and RFC documents in .aw/records/specs/: "
        "'set' transitions status (draft -> to-review -> reviewed -> approved -> implementing -> implemented, "
        "or deferred/parked/superseded), 'note' records workflow annotations, 'check' validates the contract "
        "fail-closed, and 'migrate' first-normalizes legacy status bullets."
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
    "spec": (
        "Owner verbs for the design specifications and RFC documents in .aw/records/specs/: "
        "'set' transitions status (draft -> to-review -> reviewed -> approved -> implementing -> implemented, "
        "or deferred/parked/superseded), 'note' records workflow annotations, 'check' validates the contract "
        "fail-closed, and 'migrate' first-normalizes legacy status bullets."
    ),
    "spec set": (
        "Transition a spec's status (enforcing the legal transition table, the anti-self-approval "
        "floor, and typed deferral gates) and append a workflow-history record. Syntax: "
        "'aw spec set <status> <id6|setid|fname>...'."
    ),
    "spec note": (
        "Append a workflow-history record to a spec WITHOUT changing its status. Use to log "
        "a decision, review, or correction."
    ),
    "spec check": (
        "Validate one spec (or all specs) against the spec contract (status enum, required "
        "sections, gate typing) and fail closed on a violation. CI-friendly."
    ),
    "spec migrate": (
        "One-time first-normalization of a legacy/free-form spec status to the bare enum "
        "and canonical shape. Use only on pre-contract specs."
    ),
    "set": (
        "Transition lifecycle status for one or more plan, spec, prompt, or backlog artifacts, "
        "or an entire set by set-id. Atomically validates that all targets exist, type constraints "
        "match, and statuses are valid before applying changes. Syntax: "
        "'aw set [type] <status> <id6|setid|fname>...'."
    ),
    "ipd set": (
        "Transition the lifecycle status of one or more plan/IPD artifacts or plan sets. "
        "Enforces type consistency (rejects non-plan targets) and moves files across "
        "disposition directories as required. Syntax: 'aw ipd set <status> <id6|setid|fname>...'."
    ),
    "archive": (
        "Deliberately deep-shelve research docs: a targeted move, or a bare aged-and-uncited "
        "sweep (with a preview) that shelves stale, unreferenced research."
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
    "ipd-executed-gate": (
        "Local pre-commit gate (ipdgates Order dulzpy): refuse a raw (non-finalize) plan-to-"
        "executed commit. Inspects the staged diff and, for each plan gaining '- Status: executed'/"
        "'done' or moved into an executed/ directory, requires matching finalize evidence in "
        ".aw/state/ (the transaction journal proving 'aw ipd finalize' performed the transition); "
        "absent evidence refuses the commit naming 'aw ipd finalize <plan>'. LOCAL best-effort only "
        "(--no-verify bypasses it; 'aw check'/'aw doctor' proclint is the backstop); no CI. Exit 0 "
        "= ok/no-op, 1 = refused. Invoked by the repo:local pre-commit hook, not typically by hand."
    ),
    "ipd-status-untooled-gate": (
        "Local pre-commit gate (proclint 79li67): flag a raw (untooled) INTERMEDIATE plan status "
        "change - the sibling of the dulzpy terminal gate. Inspects the staged diff and, for each "
        "plan whose '- Status:' changed in this commit with NO matching tool-authored "
        "'## Workflow history' transition line for the new status (the fingerprint of a hand-edit), "
        "refuses the commit naming 'aw set <status> <id6>'. Commit-scoped (only changed plan files; "
        "executed/ and history-less types excluded; no whole-tree scan, no grandfathering). LOCAL "
        "best-effort only (--no-verify bypasses it; a hand-edit that also adds a plausible line "
        "evades it; 'aw check'/'aw doctor' is the backstop); no CI. Exit 0 = ok/no-op, 1 = refused. "
        "Invoked by the repo:local pre-commit hook, not typically by hand."
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


class _AlphaHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help formatter that lists subcommands alphabetically (clianx-01 E-05), preserves the raw
    line breaks of description/epilog blocks (awhelp Order 02: the when/why + examples blocks),
    and dynamically adapts to terminal width (awcliux Order 02 E-03).

    Display-only: it sorts the sub-actions shown under a ``{cmd ...}`` listing by their
    name so ``--help`` is scannable, WITHOUT reordering how parsers were registered and
    WITHOUT affecting dispatch (argparse still routes by the parsed command name).
    """

    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: Optional[int] = None,
    ) -> None:
        if width is None:
            if "COLUMNS" in os.environ:
                try:
                    width = int(os.environ["COLUMNS"])
                except ValueError:
                    width = None
            if width is None:
                import shutil

                width = min(120, max(40, shutil.get_terminal_size((80, 24)).columns))
        super().__init__(
            prog,
            indent_increment=indent_increment,
            max_help_position=max_help_position,
            width=width,
        )

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


class _AwArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that formats standard usage errors with next action recommendations."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("conflict_handler", "resolve")
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        prog = self.prog
        hint_cmd = prog.replace("agent-workflows", "aw")
        print(f"{prog}: error: {message}", file=sys.stderr)
        print(f"Next  {hint_cmd} --help", file=sys.stderr)
        self.exit(2)


def _build_parser() -> argparse.ArgumentParser:
    # A shared parent so --no-color, --agent, and --json work consistently across all subcommands.
    common = _AwArgumentParser(add_help=False)
    common.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color (also honored via NO_COLOR).",
    )
    common.add_argument(
        "--agent",
        dest="agent",
        action="store_true",
        help="Machine-readable output (aw.agent/v1 JSONL).",
    )
    common.add_argument(
        "--json",
        dest="json",
        action="store_true",
        help="Emit full structured JSON representation.",
    )

    parser = _AwArgumentParser(
        prog="agent-workflows",
        description="Install and manage the agent-workflows framework across your repos.",
        parents=[common],
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "WHEN AND WHY TO USE aw\n"
            "  aw manages the agent-workflows framework INSIDE a repo: it installs the\n"
            "  reusable workflows, and it reads/checks/organizes the records (plans, specs,\n"
            "  backlog, research, releases) that live under .aw/records/. Use it to see what\n"
            "  needs attention, validate artifacts before a commit, and keep names/indexes tidy.\n"
            "\n"
            "COMMON EXAMPLES\n"
            "  aw attention                 # what needs attention across every records tree\n"
            "  aw doctor                    # read-only deep health check (git + names + version)\n"
            "  aw ipd board                 # the plan/IPD readiness board\n"
            "  aw check all                 # validate every records tree; exit nonzero on findings\n"
            "  aw find plans --status approved   # list approved plans\n"
            "  aw rename plans <id6> --slug new-name --apply   # rename a plan + rewrite refs\n"
            "  aw install <dir>             # install/update the framework in a repo\n"
            "\n"
            "OUTPUT CONTRACT\n"
            "  aw commands follow a dual-audience output contract:\n"
            "  - Interactive TTY: human-formatted, 256-color status views.\n"
            "  - Non-TTY / Piped / --agent: deterministic machine-readable aw.agent/v1 JSONL.\n"
            "  - Explicit --json: full structured JSON representation.\n"
            "  - Styling: --no-color and NO_COLOR change color styling only.\n"
            "  - Exit codes: 0 clean, 1 findings, 2 cannot-run/usage error.\n"
            "  See docs/cli-output-contract.md for normative contract specifications.\n"
        ),
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
        help="Also remove durable records scaffolding and legacy stale litter "
        "(plans/docs/prompts/comms/workflows under .aw/records/ or legacy .agents/); "
        "normally offered interactively.",
    )
    p_uninstall.add_argument(
        "--force",
        action="store_true",
        help="Also remove files you have edited (drifted) instead of preserving them.",
    )

    # awcmdsurf Order 05 (hard cutover): the old `list` verb was removed; `list-repos` is the name.
    p_list_repos = sub.add_parser(
        "list-repos",
        parents=[common],
        help="List configured/discovered repos and their currency.",
    )
    p_list_repos.add_argument(
        "--recursive", action="store_true", help="Discover repos recursively."
    )

    sub.add_parser(
        "status", parents=[common], help="Show environment + currency summary."
    )

    # awuntrackedfix Order 01: rename local/ quarantine lanes to untracked/ (retroactive, tools-free).
    p_norm_lanes = sub.add_parser(
        "normalize-lanes",
        parents=[common],
        help="Rename any prompts/comms 'local/' quarantine lane to 'untracked/' (both layouts), preserving contents + gitignore.",
    )
    p_norm_lanes.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # awdoctor Order 03: a read-only deep repo inspector aggregating every check signal.
    p_doctor = sub.add_parser(
        "doctor",
        parents=[common],
        help="Read-only deep repo inspection: aggregate attention/git/version signals into one report.",
    )
    p_doctor.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_doctor.add_argument(
        "--include-untracked",
        action="store_true",
        help="Include artifacts in untracked/ directories in checks (default: excluded).",
    )

    p_doctor.add_argument(
        "--include-executed",
        action="store_true",
        help="Strictly check historical executed/ artifacts as errors (default: advisory warning).",
    )
    p_doctor.add_argument(
        "-a",
        "--all",
        dest="include_all",
        action="store_true",
        help="Include both untracked/ artifacts and strict executed/ checks.",
    )

    # aw exclude [repo|repos] repodir1 [repodir2 ...]
    p_exclude = sub.add_parser(
        "exclude",
        parents=[common],
        help="Exclude specified repositories from agent-workflows management.",
    )
    p_exclude.add_argument(
        "repos",
        nargs="*",
        help="Repository directories to exclude (optional leading 'repo'/'repos' noun).",
    )

    # aw include [repo|repos] repodir1 [repodir2 ...]
    p_include = sub.add_parser(
        "include",
        parents=[common],
        help="Include specified repositories in agent-workflows management.",
    )
    p_include.add_argument(
        "repos",
        nargs="*",
        help="Repository directories to include (optional leading 'repo'/'repos' noun).",
    )

    # awcmdsurf Order 05 (hard cutover): the old plan-family verbs (plans, plans-index, plans-find,
    # plans-set-assign, plans-mv, plans-archive) were REMOVED. Their capabilities are now the
    # noun-verb grammar: `aw ipd board`, `aw index plans`, `aw find plans`, `aw group plans`,
    # `aw rename plans`, `aw archive plans`.

    p_ipd = sub.add_parser(
        "ipd",
        parents=[common],
        help="IPD tooling (structure/state). 'ipd lint' deterministically checks an IPD.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw ipd board                         # the plan/IPD readiness board (also bare 'aw ipd')\n"
            "  aw ipd lint --phase author FILE      # structural lint of a freshly drafted plan\n"
            "  aw ipd scaffold --kind child ...     # create a new conformant IPD skeleton\n"
            "  aw ipd sync FILE --apply             # assign step ids + validation skeletons\n"
        ),
    )
    ipd_sub = p_ipd.add_subparsers(dest="ipd_command")
    p_ipd_lint = ipd_sub.add_parser(
        "lint",
        parents=[common],
        help="Deterministically lint an IPD's structure/state (read-only; no model/network/writes).",
    )
    p_ipd_lint.add_argument(
        "path",
        nargs="*",
        default=None,
        help="Zero or more IPD files to lint (default: every pending plan; or a repo root with --all).",
    )
    p_ipd_lint.add_argument(
        "--phase",
        default="author",
        help=(
            "Lifecycle checkpoint to lint against: "
            "author (a freshly drafted plan: structure + ids present), "
            "review-finalize (after /plan-review: revisions applied, Status reviewed), "
            "pre-execution (approved + ready to run), "
            "pre-transition (every E step performed + every V step verified, still approved), "
            "post-transition (moved to executed/: Status executed, executed history line present)."
        ),
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
        help="Destination file path (must match clustering grammar YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md unless --legacy-name is passed). Omit to derive the canonical clustered `.ipd.md` name into .aw/records/plans/pending/.",
    )
    p_ipd_scaffold.add_argument(
        "--set",
        dest="set",
        required=True,
        help="Ordered-Set id (required, with --order).",
    )
    p_ipd_scaffold.add_argument(
        "--order",
        type=int,
        required=True,
        help="Order in the Set (required; 0 for orchestrator, >=1 for child).",
    )
    p_ipd_scaffold.add_argument(
        "--legacy-name",
        action="store_true",
        default=False,
        help="Allow explicit --path that does not follow the clustering grammar.",
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

    # execset Order 01 (iy1a2g): compile an approved Set into a plan-only execution manifest.
    p_ipd_execset = ipd_sub.add_parser(
        "execute-set",
        parents=[common],
        help="Compile an approved IPD Set into a plan-only execution manifest (launches no worker).",
        description=(
            "Compile an approved IPD Set's children and E-items into a validated cross-IPD "
            "dependency graph and an immutable execution manifest, then inspect it. v1 supports "
            "ONLY --plan-only: it never launches a model or worktree, never mutates an authoritative "
            "record, and never grants execution authority (scheduling is a later Order). Unapproved "
            "children are classified deferred_gate and block ONLY their descendants; independent "
            "approved siblings remain runnable. Ambiguous ownership serializes conservatively. "
            "--agent emits byte-stable JSON; the default is a compact human snapshot."
        ),
    )
    p_ipd_execset.add_argument("set_id", help="The Set id to compile (e.g. execset).")
    p_ipd_execset.add_argument(
        "--plan-only",
        dest="plan_only",
        action="store_true",
        help="Compile and inspect only; launch no worker (required in this build).",
    )
    p_ipd_execset.add_argument(
        "--resume",
        dest="resume_run_id",
        default=None,
        metavar="RUN-ID",
        help="Reconstruct and continue a prior run without replaying completed side effects "
        "(fails closed on an unreconciled unknown outcome). Requires the executed scheduler.",
    )
    p_ipd_execset.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # awcmdsurf Order 04 (OQ-1: bare `ipd` = board): the IPD board (pending+reusable by default).
    p_ipd_board = ipd_sub.add_parser(
        "board",
        parents=[common],
        help="Show the IPD board (pending + reusable by default; --status to filter dispositions).",
        description="Show the IPD board: pending + reusable plans by default, or filter by disposition with --status (executed, superseded, etc.). Bare 'aw ipd' also shows this board.",
    )
    p_ipd_board.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_ipd_board.add_argument(
        "--status",
        dest="status_filter",
        default=None,
        help="Filter by disposition (e.g. executed, pending, reusable).",
    )

    p_ipd_set = ipd_sub.add_parser(
        "set",
        parents=[common],
        help="Transition plan status (e.g. 'aw ipd set approved <id6|setid|fname>...').",
        description=(
            "Transition the lifecycle status of one or more plan/IPD artifacts or plan sets. "
            "Enforces type consistency (rejects non-plan targets) and moves files across "
            "disposition directories as required."
        ),
    )
    p_ipd_set.add_argument("args", nargs="+", help="<status> <selector...>")
    p_ipd_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_ipd_set.add_argument(
        "--message", "-m", default=None, help="History record message."
    )
    p_ipd_set.add_argument(
        "--by-human", action="store_true", help="Attest human approval."
    )
    p_ipd_set.add_argument(
        "--actor",
        default=None,
        help="Executing agent/model identity. REQUIRED when moving a PLAN to 'executed' (that "
        "transition delegates into the gated `aw ipd finalize`); ignored otherwise.",
    )
    p_ipd_set.add_argument(
        "--scope-reason",
        dest="scope_reason",
        action="append",
        default=None,
        metavar="PATH=WHY",
        help="Forwarded to `aw ipd finalize` on a delegated plan->executed transition (repeatable).",
    )
    p_ipd_set.add_argument(
        "--scope-ack",
        dest="scope_ack",
        action="append",
        default=None,
        metavar="PATH[=NOTE]",
        help="Forwarded to `aw ipd finalize` on a delegated plan->executed transition (repeatable).",
    )
    p_ipd_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_ipd_set.add_argument(
        "--yes", "-y", action="store_true", help="Confirm mutation without prompting."
    )

    # ipdgates Order 03 (xjbvu2): `aw ipd begin` fail-closed execution-start receipt.
    p_ipd_begin = ipd_sub.add_parser(
        "begin",
        parents=[common],
        help="Fail-closed start of single-IPD execution: pre-execution gate + a local frozen receipt.",
        description=(
            "Begin execution of an APPROVED IPD. Runs the pre-execution lint gate, then freezes the "
            "plan's requirements and Scope-Paths and writes a LOCAL, gitignored receipt under "
            ".aw/state/ipd-lifecycle/<id6>.receipt.json binding {plan Id, plan content digest, "
            "frozen requirement/scope digest, base HEAD, actor/model, timestamp}. Fail-closed: a "
            "non-conforming or unrunnable lint, a dirty/ambiguous baseline, a missing --actor, or an "
            "interrupted write leaves NO valid receipt (and thus NO execution authority). Mutates no "
            "tracked file; the receipt is never committed. Exit 0 = receipt written, 1 = gate "
            "findings, 2 = cannot run."
        ),
    )
    p_ipd_begin.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_ipd_begin.add_argument(
        "--actor",
        required=True,
        help="The executing agent/model identity to bind into the receipt (required, non-empty).",
    )
    p_ipd_begin.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # ipdgates Order 04 (v7e88a): `aw ipd finalize` atomic terminal transaction.
    p_ipd_finalize = ipd_sub.add_parser(
        "finalize",
        parents=[common],
        help="Atomic terminal transition of a single IPD (scope-checked, evidenced, path-scoped commit).",
        description=(
            "Finalize an APPROVED, executed IPD in one atomic terminal transaction. Validates the "
            "matching `aw ipd begin` receipt, runs pre-transition lint, compares the paths this "
            "execution changed since the frozen base HEAD against the reviewed Scope-Paths (refusing "
            "any unexplained path or an intervening in-scope collision), then appends the attributed "
            "history entry, sets terminal status, moves the plan, refreshes the owned plans index "
            "fail-loud, creates the path-scoped lifecycle commit, and runs post-transition lint. "
            "Preview by default; pass --apply to perform the transition. Exit 0 = ok, 1 = refusal "
            "(gate/scope), 2 = cannot run."
        ),
    )
    p_ipd_finalize.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_ipd_finalize.add_argument(
        "--actor",
        required=True,
        help="The executing agent/model identity for the history entry.",
    )
    p_ipd_finalize.add_argument(
        "--message", "-m", required=True, help="The terminal history-entry summary."
    )
    p_ipd_finalize.add_argument(
        "--apply",
        action="store_true",
        help="Perform the transition (default: preview the precheck).",
    )
    p_ipd_finalize.add_argument(
        "--scope-reason",
        dest="scope_reason",
        action="append",
        default=None,
        metavar="PATH=WHY",
        help="Record a reason for an out-of-scope changed path (repeatable). Headless answer to the "
        "two-way scope reconciliation; required to finalize when this execution changed a path "
        "outside the reviewed Scope-Paths.",
    )
    p_ipd_finalize.add_argument(
        "--scope-ack",
        dest="scope_ack",
        action="append",
        default=None,
        metavar="PATH[=NOTE]",
        help="Acknowledge a Scope-Paths path declared but not modified (repeatable; note defaults to "
        "'acknowledged', e.g. --scope-ack tests/=not-needed).",
    )
    p_ipd_finalize.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # awoptimize Order 01 E-06: canonical workflow schema/compiler CLI (validate/compile/
    # check-generated). The heavy lifting is in workflow_schema/source/loader/compiler; this only
    # registers the parser. compile is dry-run by default (--apply writes); validate + check-generated
    # never write. --agent/--json emit machine output with no ANSI.
    p_workflow = sub.add_parser(
        "workflow",
        parents=[common],
        help="Canonical workflow schema/compiler tooling (validate/compile/check-generated).",
        description=(
            "Canonical workflow schema and compiler tooling. Validate a typed workflow source "
            "package, compile it into deterministic generated projections, or check that the "
            "generated output has not drifted from source. Read-only except 'compile --apply'."
        ),
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw workflow validate PKG          # schema-validate a canonical workflow package\n"
            "  aw workflow compile PKG           # preview generated projections (dry-run)\n"
            "  aw workflow compile PKG --apply   # write the generated projections\n"
            "  aw workflow check-generated PKG   # fail if generated output drifts from source\n"
        ),
    )
    workflow_sub = p_workflow.add_subparsers(dest="workflow_command")
    for _wf_sub, _wf_help, _wf_desc in (
        (
            "validate",
            "Load + schema-validate a canonical package (read-only).",
            "Load a canonical workflow source package and validate it against the typed schema "
            "(ids, enums, evidence bindings, permissions, dependency graph). Read-only; makes no "
            "writes. Exit 0 clean, 1 conformance failure, 2 bad path or invocation error.",
        ),
        (
            "compile",
            "Compile workflow source packages into generated files (dry-run by default; --apply to write).",
            "Compile typed workflow source packages into runtime-ingestible projections. "
            "Dry-run by default: shows what would change without touching disk. Pass --apply "
            "to write the generated files. Exit 0 on success, 1 on a compiler failure, 2 on a bad path.",
        ),
        (
            "check-generated",
            "Fail if any _generated/ file drifts from a fresh compile (read-only).",
            "Recompile from source and compare against the on-disk _generated/ files, failing if "
            "any is missing, changed (hand-edited), or unexpected. Read-only; makes no writes. "
            "Exit 0 clean, 1 on drift, 2 on a bad path.",
        ),
    ):
        _p = workflow_sub.add_parser(
            _wf_sub, parents=[common], help=_wf_help, description=_wf_desc
        )
        _p.add_argument(
            "path", nargs="*", default=None, help="One or more workflow package roots."
        )
        if _wf_sub == "compile":
            _p.add_argument(
                "--apply",
                action="store_true",
                help="Write generated files (default: preview only).",
            )

    # awoptimize Order 04 E-04: run ledger inspection CLI (show/evidence/verify-ledger).
    # Thin CLI layer over run_evidence and run_ledger_store. Read-only: makes no writes.
    # OWNERSHIP: Order 04 owns the `aw run` parser-group registration; Order 07 extends it.
    p_run = sub.add_parser(
        "run",
        parents=[common],
        help="Run ledger inspection and verification tooling (show/evidence/verify-ledger).",
        description=(
            "Run ledger inspection and verification tooling. Read-only inspection commands: "
            "'show' (inspect run state and completion predicates), 'evidence' (inspect captured "
            "provenance envelopes and tool events), 'verify-ledger' (verify hash chain integrity "
            "and evidence validity). Read-only; makes no writes by default."
        ),
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw run show <target>             # inspect run state and completion predicates\n"
            "  aw run evidence <target>         # inspect captured evidence envelopes\n"
            "  aw run verify-ledger <target>    # verify ledger hash chain and evidence validity\n"
        ),
    )
    run_sub = p_run.add_subparsers(dest="run_command")
    for _r_sub, _r_help, _r_desc in (
        (
            "show",
            "Inspect run state, steps, verifier decisions, and completion predicates (read-only).",
            "Inspect a workflow run's ledger, steps, verifier decisions, and completion predicate "
            "status. Read-only; makes no writes. Exit 0 complete, 1 incomplete, 2 corrupted or missing.",
        ),
        (
            "evidence",
            "List and validate captured evidence envelopes and tool events (read-only).",
            "List and validate all captured evidence envelopes, tool events, and artifact refs in a "
            "run ledger. Exit 0 all valid, 1 invalid/missing evidence, 2 corrupted or missing.",
        ),
        (
            "verify-ledger",
            "Verify hash chain integrity and evidence validity of a run ledger (read-only).",
            "Verify SHA-256 hash chaining, sequence continuity, schema conformance, and evidence "
            "validity across a run ledger. Exit 0 clean, 1 invalid evidence, 2 corrupted chain.",
        ),
        # awoptimize Order 07 E-03: mutating subcommands appended to the same parser group.
        (
            "start",
            "Release + start a runnable step (pending -> runnable -> running).",
            "Acquire the single-writer lease and transition a runnable step to running. Exit 0 "
            "success, 2 bad invocation/missing ledger, 3 not runnable, 5 corrupted, 6 operational.",
        ),
        (
            "next",
            "List the currently runnable steps per the DAG and gate approvals.",
            "Reconstruct run state and list steps whose dependencies + gates are satisfied. Exit 0 "
            "when runnable steps exist or the run is terminal, 3 when nothing is runnable.",
        ),
        (
            "record",
            "Record a step attempt outcome (performed | blocked | failed) in the ledger.",
            "Append a step_attempt record to the append-only ledger. Exit 0 on performed, 3 on "
            "blocked/failed, 2 bad invocation, 5 corrupted, 6 operational.",
        ),
        (
            "resume",
            "Reconstruct state and report resumable steps; refuse on interrupted side effects.",
            "Reconstruct run state purely from the ledger and report resumable steps. Refuses "
            "(exit 3) when a side effect was interrupted mid-flight (unknown_outcome) pending "
            "explicit reconciliation.",
        ),
        (
            "cancel",
            "Cancel an active run (records a terminal cancellation transaction).",
            "Record a terminal cancellation through the engine. Exit 0 success, 6 on illegal or "
            "unauthorized cancellation, 5 corrupted.",
        ),
        (
            "status",
            "Report reconstructed run + step state from the ledger.",
            "Reconstruct and print run + per-step state. Exit 0 complete, 1 incomplete, 3 cancelled, "
            "5 corrupted.",
        ),
        (
            "finalize",
            "Compute the completion predicate and record terminal completion (coordinator only).",
            "Run the Order-04 completion predicate over the ledger and, if satisfied, record the "
            "terminal completion. Requires coordinator authority. Exit 0 complete, 1 incomplete, "
            "4 invalid evidence, 6 unauthorized/operational.",
        ),
        # execset Order 05 (2h7777): read-only inspection of a Set run's durable projections.
        (
            "decisions",
            "Show a Set run's recorded autonomous decisions (read-only).",
            "Print the autonomous decisions recorded for a Set run, read from the run's durable "
            "decisions projection under .aw/workflow-artifacts/<workflow>/<run-id>/. Read-only. "
            "Exit 0 found, 1 none recorded, 2 no such run projection.",
        ),
        (
            "questions",
            "Show a Set run's unresolved deferred questions (read-only).",
            "Print the unresolved questions recorded for a Set run, read from the run's durable "
            "open-questions projection under .aw/workflow-artifacts/<workflow>/<run-id>/. Read-only. "
            "Exit 0 found, 1 none open, 2 no such run projection.",
        ),
    ):
        _pr = run_sub.add_parser(
            _r_sub, parents=[common], help=_r_help, description=_r_desc
        )
        _pr.add_argument(
            "target", help="Run ID (run-<hex>) or path to events.jsonl ledger file."
        )
        _pr.add_argument(
            "--dir",
            default=None,
            help="Repo root directory (default: current directory).",
        )
        # The projection inspectors need the workflow name that owns the run-artifacts subdir.
        if _r_sub in ("decisions", "questions"):
            _pr.add_argument(
                "--workflow",
                default="exec-set",
                help="Workflow that owns the run-artifacts dir (default: exec-set).",
            )

        if _r_sub in (
            "start",
            "next",
            "record",
            "resume",
            "cancel",
            "status",
            "finalize",
        ):
            _pr.add_argument(
                "--workflow",
                default=None,
                help="Optional workflow JSON (id/steps/requirements); else derived from the ledger.",
            )
        if _r_sub in ("start", "record", "cancel", "finalize"):
            _pr.add_argument(
                "--actor",
                default=None,
                help="Authoring role (runtime/coordinator/executor/verifier/corrector/human).",
            )
        if _r_sub in ("start", "record"):
            _pr.add_argument(
                "--step", default=None, help="Step id (S-NN) to start or record."
            )
        if _r_sub == "record":
            _pr.add_argument(
                "--state",
                default=None,
                help="Attempt outcome: performed | blocked | failed.",
            )
        if _r_sub == "cancel":
            _pr.add_argument(
                "--reason",
                default=None,
                help="Cancellation reason (recorded in the ledger).",
            )

    p_research = sub.add_parser(
        "research",
        parents=[common],
        help="Research artifact tooling. 'research new'/'new-comparison' create correctly-named docs.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw research find --topic perf       # query index by topic\n"
            "  aw research index --check          # verify index currency (CI gate)\n"
            "  aw research new --slug memory-audit --kind spike --apply  # create research doc\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  'new' and 'new-comparison' are dry-run by default; pass --apply to write.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean, 1 drift/dangling citations, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
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

    p_research_pending = research_sub.add_parser(
        "pending",
        parents=[common],
        help="List UNRUN research prompts (a set whose NN=00 prompt has no report sibling).",
    )
    p_research_pending.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    p_research_promote = research_sub.add_parser(
        "promote",
        parents=[common],
        help="Deliberately set a doc's status (e.g. --to reference) and move it to the shard.",
    )
    p_research_promote.add_argument(
        "id",
        nargs="?",
        default=None,
        help="The <id6> of the doc (omit with --suggest).",
    )
    p_research_promote.add_argument("--to", default="reference", help="Target status.")
    p_research_promote.add_argument(
        "--suggest",
        action="store_true",
        help="Classify the stale hot cohort (cited/run -> reference; uncited dead-end -> archive) and preview the moves; requires --apply to write.",
    )
    p_research_promote.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_promote.add_argument(
        "--apply",
        action="store_true",
        help="Perform the move (default is preview only).",
    )

    p_research_set_outcome = research_sub.add_parser(
        "set-outcome",
        parents=[common],
        help="Set a doc's outcome and consumed-by provenance (preview unless --apply).",
    )
    p_research_set_outcome.add_argument("id", help="The <id6> of the doc.")
    p_research_set_outcome.add_argument(
        "--to",
        default=None,
        choices=["adopted", "informational", "rejected", "none-yet"],
        help="Set the outcome value.",
    )
    p_research_set_outcome.add_argument(
        "--consumed-by",
        dest="consumed_by",
        default=None,
        help="Comma-separated plan/spec/backlog id6s that consumed this research; '-' clears the list.",
    )
    p_research_set_outcome.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_set_outcome.add_argument(
        "--apply",
        action="store_true",
        help="Perform the update (default is preview only).",
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

    p_project = sub.add_parser(
        "project",
        parents=[common],
        help="Owner verbs for project identity, registry status, attach, and move.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw project status            # inspect project identity and registry matching\n"
            "  aw project attach PRJ_ID     # attach this repository to project ID\n"
            "  aw project move PRJ_ID PATH  # update project target path association\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Mutations (attach/move) support --dry-run to preview before write.\n"
            "  Interactive confirmation required unless --yes is passed.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean/matched, 1 mismatch, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL; --json for formatted JSON.\n"
        ),
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
        epilog=(
            "EXAMPLES\n"
            "  aw storage status            # inspect the records backend + durability for this repo\n"
            "  aw storage status --json     # machine-readable status\n"
            "  aw storage init              # initialize records storage (+ optional git)\n"
            "  aw storage attach --acknowledge-remote  # set remote durability policy\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Mutations preview by default; pass --apply to write changes.\n"
            "  Remote durability changes require explicit policy acknowledgement.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean/valid, 1 findings/uninitialized, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL; --json for structured JSON.\n"
        ),
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

    p_config = sub.add_parser(
        "config",
        parents=[common],
        help="Manage user CLI config (the never-install exclude list).",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw config exclude list       # list never-install exclude entries\n"
            "  aw config exclude add ~/src/legacy  # add path to exclude list\n"
            "  aw config exclude rm ~/src/legacy   # remove path from exclude list\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 success, 1 not found, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
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
    p_todo.add_argument("--all", action="store_true", help="Include non-open actions.")

    p_show = sub.add_parser(
        "show",
        parents=[common],
        help="Inspect a record or action by id6, set id, filename, or status (records first, then the action ledger).",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw show pp6y76               # print the record with id6 pp6y76 (plans/specs/research/...)\n"
            "  aw show <set-id>             # the records in a Set\n"
            "  aw show setup-repo-v1        # an action from the ledger\n"
        ),
    )
    p_show.add_argument(
        "action_ref",
        help="A selector: an id6 (e.g. pp6y76), a set id, a filename fragment, a status, or an action id[@generation].",
    )
    p_show.add_argument(
        "--dir",
        default=None,
        help="Repo root to search for a records artifact (default: current directory).",
    )

    # setupmarker Order 01: the operational-action ledger was removed (redundant with backlog);
    # the complete/dismiss/reopen/history action verbs are gone. The post-install "run setup"
    # reminder is now the `.aw/setup-repo-needed.md` marker, cleared by `aw setup` / the /setup-repo
    # workflow / deleting the file. `aw record-history` (the records sidecar) is unrelated and stays.

    p_record_history = sub.add_parser(
        "record-history",
        parents=[common],
        help="Print a record's full chronological workflow history from the global sidecar (by id6).",
    )
    p_record_history.add_argument(
        "id6", help="The 6-char record id (from a file's `- Id:`)."
    )
    p_record_history.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # awcmdsurf Order 01: the six noun-verb top-level verbs (spec 20260818-1525-01). Each takes a
    # positional TYPE (plans/specs/... or `all`, validated at dispatch) + a minimal selector + the
    # shared --json/--agent. Backends are wired lazily via artifact_types.TYPE_BACKENDS; verbs/types
    # without a backend report "not supported for <type>" (exit 2). The existing top-level `archive`
    # verb is intentionally NOT touched here (Order 03 generalizes it atomically).
    for _verb, _vhelp in (
        (
            "check",
            "Validate artifacts of a TYPE against their contract (0 ok / 1 findings / 2 cannot-run).",
        ),
        (
            "find",
            "Find artifacts of a TYPE by selector (or across all types if omitted).",
        ),
        ("search", "Search artifacts of a TYPE (or across all types if omitted)."),
        ("index", "Rebuild/print the index for a TYPE."),
        ("rename", "Rename/move an artifact of a TYPE (rewriting references)."),
        ("group", "Assign an artifact of a TYPE to a Set/group."),
    ):
        _p = sub.add_parser(_verb, parents=[common], help=_vhelp)
        if _verb in ("search", "find"):
            _p.add_argument(
                "type",
                nargs="?",
                default=None,
                help="Artifact type (plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms, releases) or 'all' (optional).",
            )
            _p.add_argument(
                "selector",
                nargs="*",
                help="Selector / search pattern / args for the verb.",
            )
        else:
            _p.add_argument(
                "type",
                help="Artifact type (plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms, releases) or 'all'.",
            )
            _p.add_argument(
                "selector",
                nargs="*",
                help="Selector/args for the verb (id6, status, filename, ...).",
            )
        _p.add_argument(
            "--dir", default=None, help="Repo root (default: current directory)."
        )
        if _verb == "search":
            _p.add_argument(
                "--line-numbers",
                "-n",
                dest="line_numbers",
                action="store_true",
                help="Print line numbers for matched lines.",
            )
        # backend-relevant passthrough flags (index/find/check)
        _p.add_argument(
            "--check",
            action="store_true",
            help="Validation mode (index/check): fail on drift.",
        )
        _p.add_argument("--status", default=None, help="Filter/selector: status.")
        _p.add_argument("--id", default=None, help="Filter/selector: id6.")
        _p.add_argument("--set", default=None, help="Filter/selector: Set id.")
        _p.add_argument(
            "--topic", default=None, help="Filter/selector: topic (research)."
        )
        _p.add_argument(
            "--limit", type=int, default=None, help="Max rows (index/find)."
        )
        # mutation flags (rename/group)
        _p.add_argument("--slug", default=None, help="New slug (rename).")
        _p.add_argument(
            "--order", type=int, default=None, help="Order NN (rename/group)."
        )
        _p.add_argument(
            "--rename",
            action="store_true",
            help="group: also re-cluster the filename to the new Set.",
        )
        _p.add_argument(
            "--apply",
            action="store_true",
            help="Apply the change (default is a preview).",
        )
        _p.add_argument(
            "--no-refs",
            dest="no_refs",
            action="store_true",
            help="rename/group: rename the file only; do NOT rewrite citing documents.",
        )
        # IPD laykok E-07: --force overrides a filename-substring multi-match on mutating verbs
        # (rename/group). It does NOT override a unique-id (id6/path/stem) collision; a setid
        # multi-target needs no force.
        _p.add_argument(
            "--force",
            action="store_true",
            help="rename/group: act on ALL matches when a filename-substring selector is ambiguous "
            "(does not override a unique-id collision).",
        )
        if _verb == "check":
            _p.formatter_class = _AlphaHelpFormatter
            _p.epilog = (
                "EXAMPLES\n"
                "  aw check plans               # validate plan artifacts\n"
                "  aw check all                 # validate every records tree\n"
                "  aw check specs names         # check spec filename conformance\n"
                "\n"
                "OUTPUT & EXITS\n"
                "  Exit codes: 0 clean, 1 findings, 2 cannot-run/usage error.\n"
                "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL; --json for formatted JSON.\n"
            )

    p_set = sub.add_parser(
        "set",
        parents=[common],
        help="Transition status for one or more artifacts or sets across types (e.g. 'aw set approved <id6|setid|fname>...').",
        description=(
            "Transition lifecycle status for one or more plan, spec, prompt, or backlog artifacts, "
            "or an entire set by set-id. Atomically validates that all targets exist, type constraints "
            "match, and statuses are valid before applying changes."
        ),
    )
    p_set.add_argument("args", nargs="+", help="[type] <status> <selector...>")
    p_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_set.add_argument("--message", "-m", default=None, help="History record message.")
    p_set.add_argument("--by-human", action="store_true", help="Attest human approval.")
    p_set.add_argument(
        "--actor",
        default=None,
        help="Executing agent/model identity. REQUIRED when moving a PLAN to 'executed' (that "
        "transition transparently delegates into the gated `aw ipd finalize`, which needs an "
        "attributed actor); ignored for other transitions.",
    )
    p_set.add_argument(
        "--scope-reason",
        dest="scope_reason",
        action="append",
        default=None,
        metavar="PATH=WHY",
        help="Forwarded to `aw ipd finalize` when a plan->executed transition delegates: reason for "
        "an out-of-scope changed path (repeatable).",
    )
    p_set.add_argument(
        "--scope-ack",
        dest="scope_ack",
        action="append",
        default=None,
        metavar="PATH[=NOTE]",
        help="Forwarded to `aw ipd finalize` on a delegated plan->executed transition: acknowledge a "
        "declared-but-unmodified Scope-Paths path (repeatable).",
    )
    p_set.add_argument(
        "--gate-kind",
        dest="gate_kind",
        default=None,
        help="Gate kind (for deferred/blocked).",
    )
    p_set.add_argument(
        "--gate-ref",
        dest="gate_ref",
        default=None,
        help="Gate ref (for deferred/blocked).",
    )
    p_set.add_argument(
        "--gate-summary", dest="gate_summary", default=None, help="Gate summary."
    )
    p_set.add_argument(
        "--blocks-release",
        dest="blocks_release",
        default=None,
        help="Blocks-Release flag.",
    )
    p_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_set.add_argument(
        "--force",
        action="store_true",
        help="Act on ALL matches when a filename-substring selector is ambiguous "
        "(does not override a unique-id collision; a setid multi-target needs no force).",
    )
    p_set.add_argument(
        "--yes", "-y", action="store_true", help="Confirm execution without prompt."
    )

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
        "--all", action="store_true", help="Show done/parked groups in the board."
    )
    p_attention.add_argument(
        "--long",
        dest="long",
        action="store_true",
        help="Show the full repo-relative path instead of the compact identity stem.",
    )

    p_backlog = sub.add_parser(
        "backlog",
        parents=[common],
        help="Owner verbs for the attention-visible backlog tier. 'backlog new' creates an item; 'set' transitions status; 'check' validates.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw backlog check             # validate backlog tree fail-closed\n"
            '  aw backlog new --summary "Fix auth" --set auth-01 --apply\n'
            "  aw backlog set open <id6>    # transition backlog item status\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  'new' is dry-run by default; pass --apply to write.\n"
            "  Moving to 'blocked' requires a typed --gate-kind and --gate-ref pair.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean, 1 contract findings, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
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
        help="Transition a backlog item's status + append history (e.g. 'aw backlog set done <id6|setid|fname>...').",
    )
    p_backlog_set.add_argument(
        "args", nargs="+", help="<status> <selector...> (or <path> with --status)."
    )
    p_backlog_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_backlog_set.add_argument(
        "--status", default=None, help="Target status: open | blocked | parked | done."
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
    p_backlog_set.add_argument(
        "--blocks-release",
        dest="blocks_release",
        default=None,
        help="Declare this item gates a release: a release id6, 'next', or '-' to clear.",
    )
    p_backlog_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_backlog_set.add_argument(
        "--yes", "-y", action="store_true", help="Confirm mutation without prompting."
    )

    p_backlog_check = backlog_sub.add_parser(
        "check",
        parents=[common],
        description="Validate the backlog tree against the contract; fail closed.",
        help="Check backlog items conform (valid status/gate/id/summary); exit nonzero on any violation.",
    )
    p_backlog_check.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    p_specs = sub.add_parser(
        "specs",
        aliases=["spec"],
        parents=[common],
        help="Owner verbs for the specs tree. 'specs set'/'note' write status+history; 'specs check' validates.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw specs check               # validate all specs against contract\n"
            "  aw specs set reviewed <id6>  # advance spec status to reviewed\n"
            '  aw specs note <id6> "Reviewed with team"  # append history note\n'
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Enforces legal transition table and anti-self-approval floor.\n"
            "  Setting 'approved' requires explicit --by-human attestation.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean, 1 contract violations, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
        description=(
            "Owner verbs for the design specifications and RFC documents in .aw/records/specs/: "
            "'set' transitions status (draft -> to-review -> reviewed -> approved -> implementing -> implemented, "
            "or deferred/parked/superseded), 'note' records workflow annotations, 'check' validates the contract "
            "fail-closed, and 'migrate' first-normalizes legacy status bullets."
        ),
    )
    specs_sub = p_specs.add_subparsers(dest="specs_command")
    p_specs_set = specs_sub.add_parser(
        "set",
        parents=[common],
        help="Transition a spec's status (+ typed gates) and append history (e.g. 'aw spec set to-review <id6|setid|fname>...').",
        description=(
            "Transition a specification document's lifecycle status, update or clear typed gate fields, "
            "and append workflow history. Enforces transition authority and validation rules."
        ),
    )
    p_specs_set.add_argument(
        "args", nargs="+", help="<status> <selector...> (or <path> with --status)."
    )
    p_specs_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_specs_set.add_argument(
        "--status", default=None, help="Target spec status (the closed enum)."
    )
    p_specs_set.add_argument("--message", default="", help="History record message.")
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
        "--blocks-release",
        dest="blocks_release",
        default=None,
        help="Declare this spec gates a release: a release id6, 'next', or '-' to clear.",
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
    p_specs_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_specs_set.add_argument(
        "--yes", "-y", action="store_true", help="Confirm mutation without prompting."
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Deliberately deep-shelve artifacts of a TYPE (research or plans); targeted or an age-based sweep with preview.",
        description="Deliberately deep-shelve artifacts of a TYPE (research or plans). Supports targeted "
        "archiving of specific documents/sets or an automated sweep based on an age threshold (--age/-a). "
        "Sets of artifacts are kept together: a set is only swept if its most recently created/edited member "
        "meets the age threshold.",
        epilog="""
DURATION FORMATS
  The --age/-a option accepts human-readable duration strings:
    1h, 12h   - Hours (1/24 days)
    5d, 14d   - Days (default unit if omitted, e.g. 14)
    2w, 10w   - Weeks (7 days per week)
    1m, 4m    - Months (30 days per month)
    1y        - Years (365 days per year)

EXAMPLES
  # Preview sweep of research older than 14 days (default)
  aw archive research

  # Preview sweep of research older than 30 days
  aw archive research --age 30d

  # Apply sweep of terminal plans older than 4 weeks
  aw archive plans -a 4w --apply

  # Targeted archival of a specific research doc or set (immediate)
  aw archive research <id6|set-id> --apply

  # Apply sweep across both research and plans older than 10 weeks
  aw archive all -a 10w --apply
""",
    )
    p_archive.add_argument(
        "type_or_target",
        nargs="?",
        default=None,
        help="An artifact TYPE (research|plans|all) OR, for back-compat, a research <set-id>/<id6> to archive.",
    )
    p_archive.add_argument(
        "target",
        nargs="?",
        default=None,
        help="A <set-id> or <id6> to archive (omit for a sweep).",
    )
    p_archive.add_argument(
        "-a",
        "--age",
        default=None,
        help="Minimum age threshold to sweep (e.g. 1h, 5d, 10w, 4m, 1y; default: 14d). "
        "Sets are kept together based on their newest member.",
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

    # awcmdsurf Order 05 (hard cutover): the old `plan-names` verb was REMOVED; name conformance is
    # now `aw check plans names` (and `aw check <type> names`).

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

    # ipdgates Order dulzpy: local pre-commit gate on raw plan->executed commits. Backs the
    # `repo: local` hook; refuses a staged plan gaining executed status / moved into executed/ that
    # has no matching finalize evidence. LOCAL best-effort only (no CI).
    sub.add_parser(
        "ipd-executed-gate",
        parents=[common],
        help="Local pre-commit gate: refuse a raw (non-finalize) plan->executed commit "
        "(verifies aw ipd finalize evidence; LOCAL prevention, no CI).",
    )

    # proclint 79li67: local pre-commit gate on raw (untooled) INTERMEDIATE plan status changes. The
    # sibling of ipd-executed-gate; refuses a staged plan whose `- Status:` changed with no matching
    # tool-authored `## Workflow history` line. Commit-scoped, LOCAL best-effort only (no CI).
    sub.add_parser(
        "ipd-status-untooled-gate",
        parents=[common],
        help="Local pre-commit gate: flag a raw (untooled) intermediate plan status change "
        "(no attributed history line; use aw set <status> <id6>; LOCAL prevention, no CI).",
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


def _confirm_install(
    term: Term, repo_root: Union[str, Path], assume_yes: bool, default: bool = True
) -> bool:
    """Single final install confirmation gate (E-04). Defaults YES for interactive."""
    if assume_yes:
        return True
    is_interactive = (
        hasattr(sys.stdin, "isatty") and sys.stdin.isatty()
    ) or isinstance(sys.stdin, io.StringIO)
    if not is_interactive:
        term.status(
            "warn",
            f"Proceed and install into {repo_root}? (declining: non-interactive; pass --yes to proceed)",
        )
        return False
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = (
            input(f"Proceed and install into {repo_root}? {suffix} ").strip().lower()
        )
    except EOFError:
        return default
    except KeyboardInterrupt:
        from agent_workflows.install_wizard import PolicyCancelledError

        raise PolicyCancelledError(f"{repo_root}: install cancelled; nothing written.")
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


def _split_brain_guard(term: Term, repo_root: Path, args) -> str:
    """Guard against split-brain layout (.aw/system + live .agents/workflows).

    Returns:
      - "proceed": layout is clean, or split-brain was resolved/consented.
      - "skip": split-brain detected and not resolved (declined or non-interactive/--yes fail-safe).
    """
    if getattr(args, "_split_brain_consented", None) is True:
        return "proceed"

    if not engine.detect_split_brain_layout(repo_root):
        return "proceed"

    term.status("warn", engine.describe_split_brain(repo_root))

    # Fail-safe: never auto-install or auto-migrate non-interactively / under --yes.
    if getattr(args, "yes", False) or not sys.stdin.isatty():
        term.status(
            "skip",
            f"{repo_root}: split-brain layout; skipped (run 'aw migrate-layout' or use "
            "an interactive install to consolidate). Nothing changed.",
        )
        return "skip"

    # Interactive branch: offer migrate-now
    if _prompt_yes_no(
        "Consolidate now with 'aw migrate-layout' (moves .agents/ content into .aw/)?",
        default=True,
    ):
        from agent_workflows.layout_migration import MigrationManager

        mgr = MigrationManager(target_repo=str(repo_root))
        mgr.execute_migration(target_backend="repository", leftover_disposition="defer")
        if not engine.detect_split_brain_layout(repo_root):
            term.status("ok", f"{repo_root}: consolidated split-brain layout into .aw/")
            return "proceed"
        else:
            term.status(
                "skip",
                f"{repo_root}: split-brain condition persists after migration; skipped. Nothing changed.",
            )
            return "skip"

    if _prompt_yes_no(
        "Continue anyway and install into .aw/ beside the stale .agents/ tree?",
        default=False,
    ):
        try:
            args._split_brain_consented = True
        except (AttributeError, TypeError):
            pass
        return "proceed"

    term.status(
        "skip",
        f"{repo_root}: split-brain install declined. Nothing changed.",
    )
    return "skip"


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

    if _split_brain_guard(term, repo_root, args) == "skip":
        return "nochange"

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

    # Record install history event & drop the self-explaining setup-repo-needed marker (setupmarker
    # Order 01: replaces the old operational-action ledger). Install history is a genuine append-only
    # audit; the marker is the per-machine "run setup here" reminder that `aw setup`/deletion clears.
    try:
        from agent_workflows.install_history import record_install_history

        record_install_history(
            target_repo=str(repo_root),
            event_type="install" if outcome == "ok" else "check",
            details={
                "version": result.get("version", ""),
                "installed_files": len(result.get("installed", [])),
            },
        )
        engine.write_setup_marker(repo_root)
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

        # Split-brain layout guard (backlog u298fd / 0qj4on): refuse/warn on mixed layout
        # (.aw/system + live .agents/workflows) BEFORE any policy/interview work.
        if _split_brain_guard(term, repo_root, args) == "skip":
            continue

        kept_legacy = _handle_legacy_migration(repo_root, args, term)

        policy = None
        if not kept_legacy:
            # Resolve policy via install_wizard (E-01..E-05) for .aw/ layout
            from agent_workflows.install_wizard import (
                PolicyCancelledError,
                PolicyError,
                collect_policy_interactive,
                persist_project_policy,
                render_pre_write_plan,
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
            except PolicyCancelledError:
                term.status("skip", f"{repo_root}: install cancelled; nothing written.")
                returncode = 1
                continue
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

        try:
            if not _confirm_install(term, repo_root, getattr(args, "yes", False)):
                term.status("skip", f"{repo_root}: aborted; nothing changed.")
                continue
        except PolicyCancelledError:
            term.status("skip", f"{repo_root}: install cancelled; nothing written.")
            returncode = 1
            continue

        if not kept_legacy and policy is not None:
            # Atomic installation step: Materialize companion + Persist policy + Install bundle
            if getattr(policy, "companion_dir", None):
                from agent_workflows import storage

                comp_p = Path(policy.companion_dir).expanduser().resolve()
                if getattr(policy, "create_companion", False) or not comp_p.exists():
                    comp_p.mkdir(parents=True, exist_ok=True)
                if (
                    getattr(policy, "init_companion_git", False)
                    or not (comp_p / ".git").exists()
                ):
                    import subprocess

                    subprocess.run(
                        ["git", "-C", str(comp_p), "init"],
                        check=False,
                        capture_output=True,
                    )
                storage.attach_companion(
                    target_repo=str(repo_root),
                    companion_dir=str(comp_p),
                    dry_run=False,
                )

            # Persist confirmed policy to .aw/config/project.json and local.json
            persist_project_policy(
                repo_path=str(repo_root),
                policy=policy,
                dry_run=False,
            )

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


def _format_cleanup_root(repo_root: Path, root: str, n: int) -> str:
    plural = "file" if n == 1 else "files"
    target = repo_root / root
    if target.is_file() or not root.startswith((".aw/records", ".agents")):
        return f"{root} ({n} {plural})"
    return f"{n} {plural} under {root}/"


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
            print(f"    - {_format_cleanup_root(repo_root, root, n)}")
        if deep.at_risk:
            print(
                f"    ! {len(deep.at_risk)} of these are NOT recoverable from git "
                "(untracked/uncommitted)"
            )
    return 0


def _offer_deep_cleanup(
    term: Term, repo_root: Path, use_git: bool, args, changed: list[str]
) -> None:
    """Offer (or, under --deep, perform) the deeper scaffolding and records cleanup."""

    plan = engine.plan_deep_cleanup(repo_root)
    if plan.is_empty:
        return

    if args.deep:
        for a in engine.run_deep_cleanup(
            repo_root, plan, use_git, changed_out=changed, remove_records=True
        ):
            term.status("ok", a)
        return

    if args.yes or args.force or not sys.stdin.isatty():
        # Non-interactive (--yes/--force/no TTY) without --deep: do NOT silently delete the
        # scaffolding; it holds user content. Skip the deeper cleanup unless --deep is set.
        term.status(
            "warn",
            "scaffolding left in place (pass --deep to remove it non-interactively).",
        )
        return

    # Interactive flow: prompt for non-records scaffolding and records separately (E-03).
    remove_other = False
    if plan.other_files:
        print()
        print("A deeper cleanup can also remove other agent-workflows scaffolding:")
        for root, n in sorted(plan.counts.items()):
            if not root.startswith((".aw/records", ".agents")):
                print(f"  - {_format_cleanup_root(repo_root, root, n)}")
        other_at_risk = [f for f in plan.at_risk if f in plan.other_files]
        if other_at_risk:
            print(
                term.colorize(
                    f"  WARNING: {len(other_at_risk)} of these are NOT recoverable from git "
                    "(untracked, uncommitted, or ignored). Deleting them is permanent:",
                    "yellow",
                )
            )
            for rel in other_at_risk:
                print(f"    ! {rel}")

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
            on_diff=lambda: [print(f"    - {f}") for f in plan.other_files],
        )
        remove_other = choice == "yes"

    remove_records = False
    if plan.records_files:
        print()
        print("Authoring records found under .aw/records/ (or .agents/):")
        for root, n in sorted(plan.counts.items()):
            if root.startswith((".aw/records", ".agents")):
                print(f"  - {_format_cleanup_root(repo_root, root, n)}")
        records_at_risk = [f for f in plan.at_risk if f in plan.records_files]
        if records_at_risk:
            print(
                term.colorize(
                    f"  WARNING: {len(records_at_risk)} of these are NOT recoverable from git "
                    "(untracked, uncommitted, or ignored). Deleting them is permanent:",
                    "yellow",
                )
            )
            for rel in records_at_risk:
                print(f"    ! {rel}")

        choice_rec = engine.prompt_choice(
            "Keep your authored records under .aw/records/ (plans, specs, walkthroughs, etc.)? [Y/n/list/help]: ",
            [
                "  Y    = Yes, keep authored records [default]",
                "  N    = No, remove records too",
                "  list = show every record file, then ask again",
                "  help = show this help",
            ],
            default="yes",
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
            on_diff=lambda: [print(f"    - {f}") for f in plan.records_files],
        )
        remove_records = choice_rec == "no"

    if remove_other or remove_records:
        filtered_plan = plan.filtered(records=remove_records, other=remove_other)
        for a in engine.run_deep_cleanup(
            repo_root,
            filtered_plan,
            use_git,
            changed_out=changed,
            remove_records=remove_records,
        ):
            term.status("ok", a)
    else:
        term.status("skip", "deeper cleanup skipped; scaffolding left in place.")


def _run_uninstall(args: argparse.Namespace, term: Term) -> int:
    repo_root = Path(args.target).expanduser().resolve()
    has_footprint = (
        (repo_root / engine.AW_SYSTEM_WORKFLOWS_DIR).is_dir()
        or (repo_root / engine.WORKFLOWS_DIR).is_dir()
        or (repo_root / ".aw" / "config").is_dir()
        or (repo_root / ".aw" / "state").is_dir()
        or (repo_root / ".aw" / "records").is_dir()
        or (repo_root / ".aw" / "system").is_dir()
        or (repo_root / ".aw").is_dir()
    )
    if not has_footprint:
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

    staged_proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    staged_paths = (
        set(staged_proc.stdout.splitlines()) if staged_proc.returncode == 0 else set()
    )
    paths = sorted(p for p in set(changed) if p in staged_paths)
    if not paths:
        return

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
    """Config repos plus repos discovered under the config search roots (deduped and sorted)."""

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
    out.sort(key=lambda p: str(p).lower())
    return out


def _run_list(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
    packaged = _packaged_version()
    repos = _repos_for_report(args.recursive)
    rows = []
    for repo in repos:
        installed = engine.read_installed_version(repo)
        rows.append(
            {
                "repo": str(repo),
                "installed": installed or None,
                "state": versioning.status(installed, packaged),
            }
        )

    if ctx.is_agent or ctx.is_json:
        data = {"packaged": packaged, "repos": rows}
        next_acts = (
            [NextAction(command="aw setup", description="set up repositories")]
            if not repos
            else []
        )
        res = CommandResult(
            command="list-repos",
            status="clean",
            exit_code=0,
            summary=f"discovered {len(repos)} repo(s)"
            if repos
            else "no configured or discovered repos",
            evidence=[
                Evidence(key="repos", value={"count": len(repos)}, status="verified")
            ],
            next_actions=next_acts,
            data=data,
        )
        return get_renderer(ctx).emit(res, ctx)

    if not repos:
        term.empty_result(
            summary="no configured or discovered repos",
            filters={"recursive": args.recursive}
            if getattr(args, "recursive", False)
            else None,
            next_action=NextAction(
                command="aw setup", description="set up repositories"
            ),
        )
        return 0
    term.heading("Repositories")
    for repo in repos:
        installed = engine.read_installed_version(repo)
        state = versioning.status(installed, packaged)
        detail = installed if installed else "not installed"
        term.status(state, f"{repo}  ({detail})")
    return 0


def _status_badge_256(status: str, term: Term) -> str:
    s = status.lower()
    if s in ("current", "ok", "pass"):
        return "[" + term.color256("current", 46, bold=True) + "]"
    if s in ("source-root", "source", "dev"):
        label = "source root" if s in ("source-root", "source") else "dev"
        return "[" + term.color256(label, 39, bold=True) + "]"
    if s in ("stale", "warn"):
        return "[" + term.color256("stale", 226, bold=True) + "]"
    if s in ("not-installed", "not installed", "fail", "error"):
        return "[" + term.color256("not installed", 196, bold=True) + "]"
    if s == "ahead":
        return "[" + term.color256("ahead", 207, bold=True) + "]"
    return "[" + term.color256(status, 244, bold=True) + "]"


def _collect_repo_status_details(repo: Path, packaged: str) -> dict:
    installed = engine.read_installed_version(repo)
    is_source = False
    if (repo / "agent_workflows").is_dir() and (repo / "pyproject.toml").is_file():
        try:
            pyproject = (repo / "pyproject.toml").read_text(encoding="utf-8")
            if 'name = "agent-workflows"' in pyproject:
                is_source = True
        except OSError:
            pass

    state = "source-root" if is_source else versioning.status(installed, packaged)

    has_aw = (repo / ".aw").is_dir()
    has_agents = (repo / ".agents").is_dir()
    if has_aw and has_agents:
        layout = ".aw + .agents"
        split_brain = True
    elif has_aw:
        layout = ".aw"
        split_brain = False
    elif has_agents:
        layout = ".agents"
        split_brain = False
    else:
        layout = "none"
        split_brain = False

    preset = None
    backend = None
    if layout != "none":
        cfg_file = repo / (".aw" if has_aw else ".agents") / "config.json"
        if cfg_file.is_file():
            try:
                import json

                c_json = json.loads(cfg_file.read_text(encoding="utf-8"))
                preset = c_json.get("preset")
                backend = c_json.get("records_backend")
            except Exception:
                pass

    # Inspect attention metrics
    attn_total = 0
    attn_by_class: dict[str, int] = {}
    attn_blockers = 0
    if layout != "none":
        try:
            from agent_workflows import attention

            items, drift = attention.scan(repo)
            attn_total = len(items)
            for it in items:
                attn_by_class[it.attention_class] = (
                    attn_by_class.get(it.attention_class, 0) + 1
                )
            attn_blockers = len(attention.release_blockers(items, repo))
        except Exception:
            pass

    # Inspect git metrics
    git_info = {
        "available": False,
        "branch": None,
        "upstream": None,
        "ahead": 0,
        "behind": 0,
        "dirty": False,
        "changes_count": 0,
    }
    if engine.git_available(repo):
        try:
            import subprocess

            # Branch
            r_br = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if r_br.returncode == 0:
                git_info["available"] = True
                git_info["branch"] = r_br.stdout.strip()

            # Upstream tracking
            r_up = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "rev-parse",
                    "--abbrev-ref",
                    "@{upstream}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if r_up.returncode == 0:
                git_info["upstream"] = r_up.stdout.strip()
                # Ahead/behind counts
                r_ab = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo),
                        "rev-list",
                        "--left-right",
                        "--count",
                        "HEAD...@{upstream}",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if r_ab.returncode == 0:
                    parts = r_ab.stdout.strip().split()
                    if len(parts) == 2:
                        git_info["ahead"] = int(parts[0])
                        git_info["behind"] = int(parts[1])

            # Status (dirty / changes count)
            r_st = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )
            if r_st.returncode == 0:
                lines = [line for line in r_st.stdout.split("\n") if line.strip()]
                git_info["changes_count"] = len(lines)

                git_info["dirty"] = len(lines) > 0
        except Exception:
            pass

    return {
        "path": str(repo),
        "installed": installed or None,
        "is_source": is_source,
        "state": state,
        "layout": layout,
        "preset": preset,
        "backend": backend,
        "split_brain": split_brain,
        "attention": {
            "total": attn_total,
            "by_class": attn_by_class,
            "release_blockers": attn_blockers,
        },
        "git": git_info,
    }


def _run_status(args, term: Term, context: Optional[Any] = None) -> int:
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        select_output,
    )

    ctx = context or select_output(args)
    packaged = _packaged_version()
    cfg = config.load()
    repos = _repos_for_report(recursive=False)
    # If no repos configured in search roots, include current working directory if it's a git repo or has layout
    if not repos:
        cwd = Path.cwd().resolve()
        if (
            (cwd / ".git").is_dir()
            or (cwd / ".aw").is_dir()
            or (cwd / ".agents").is_dir()
        ):
            repos = [cwd]

    repo_details = [_collect_repo_status_details(r, packaged) for r in repos]
    repo_details.sort(key=lambda rd: str(rd["path"]).lower())
    excluded_entries = sorted(cfg.get("exclude", []), key=lambda e: str(e).lower())
    counts: dict = {}
    for rd in repo_details:
        state = rd["state"]
        counts[state] = counts.get(state, 0) + 1

    data = {
        "packaged_version": packaged,
        "python": sys.version.split()[0],
        "git": engine.git_available(Path.cwd()),
        "config": str(config.config_path()),
        "config_present": config.config_path().is_file(),
        "search_roots": cfg.get("search_roots", []),
        "repos_configured": len(cfg.get("repos", [])),
        "repos_excluded": len(excluded_entries),
        "currency": counts,
        "repositories": repo_details,
        "excluded": excluded_entries,
    }

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="status",
            status="clean",
            exit_code=0,
            summary=f"status: {len(repo_details)} repo(s) inspected, packaged version {packaged}",
            evidence=[Evidence(key="currency", value=counts, status="verified")],
            data=data,
        )
        return get_renderer(ctx).emit(res, ctx)

    term.heading("agent-workflows status")
    term.line(term.colorize("Environment:", "bold"))
    term.kv("  Packaged version", packaged)
    term.kv("  Python", f"{sys.version.split()[0]} ({sys.executable})")
    term.kv("  git", "present" if engine.git_available(Path.cwd()) else "not found")
    term.kv(
        "  Config",
        str(config.config_path())
        + ("" if config.config_path().is_file() else "  (none yet; run 'aw setup')"),
    )
    term.kv("  Search roots", ", ".join(cfg.get("search_roots", [])) or "(none)")
    term.kv("  Repos configured", str(len(cfg.get("repos", []))))
    term.kv("  Repos excluded", str(len(excluded_entries)))
    term.line()

    # Repositories Section
    if repo_details:
        term.heading(f"Managed Repositories ({len(repo_details)})")
        for rd in repo_details:
            rp = Path(rd["path"])
            disp = config._preserve_home(str(rp))
            st = rd["state"]

            badge = _status_badge_256(st, term)

            # Format version suffix in header
            if rd["is_source"]:
                v_desc = f"v{packaged or '0.1.0'} (source checkout)"
            elif rd["installed"]:
                inst = rd["installed"]
                inst_v = inst if inst.startswith("v") else f"v{inst}"
                if st == "stale":
                    v_desc = f"{inst_v} (current: {packaged})"
                elif st == "ahead":
                    v_desc = f"{inst_v} (packaged: {packaged})"
                else:
                    v_desc = inst_v
            else:
                v_desc = ""

            header_parts = [f"- {term.color256(disp, 39, bold=True)}", badge]
            if v_desc:
                header_parts.append(v_desc)
            term.line(" ".join(header_parts))

            # Layout line
            if rd["layout"] != "none":
                layout_parts = [rd["layout"]]
                if rd["preset"] or rd["backend"]:
                    layout_parts.append(
                        f"(preset: {rd['preset'] or 'standard'}, backend: {rd['backend'] or 'repo-tracked'})"
                    )
                if rd.get("split_brain"):
                    term.line(
                        f"  Layout:    {term.color256(' '.join(layout_parts) + ' [dual layout / split-brain - run aw migrate-layout]', 208, bold=True)}"
                    )
                else:
                    term.line(f"  Layout:    {' '.join(layout_parts)}")

            # Git line
            git = rd["git"]
            if git["available"]:
                git_parts = [term.color256(git["branch"] or "HEAD", 255, bold=True)]
                if git["upstream"]:
                    sync_note = f"tracking {git['upstream']}"
                    if git["ahead"]:
                        sync_note += f", ahead {git['ahead']}"
                    if git["behind"]:
                        sync_note += f", behind {git['behind']}"
                    if not git["ahead"] and not git["behind"]:
                        sync_note += ", up to date"
                    git_parts.append(f"({sync_note})")

                if git["dirty"]:
                    git_parts.append(
                        term.color256(
                            f"{git['changes_count']} change(s)", 214, bold=True
                        )
                    )
                else:
                    git_parts.append(term.color256("Clean", 46))
                term.line(f"  Git:       {' '.join(git_parts)}")

            # Attention line
            if rd["layout"] != "none":
                attn = rd["attention"]
                if attn["total"] > 0:
                    cls_str = ", ".join(
                        f"{cnt} {cls}" for cls, cnt in attn["by_class"].items()
                    )
                    attn_line = f"{attn['total']} items ({cls_str})"
                    if attn["release_blockers"]:
                        attn_line += " - " + term.color256(
                            f"{attn['release_blockers']} release blocker(s)",
                            208,
                            bold=True,
                        )
                else:
                    attn_line = "0 items"
                term.line(f"  Attention: {attn_line}")
        term.line()

    # Excluded Repositories Section
    if excluded_entries:
        term.heading(f"Excluded Repositories ({len(excluded_entries)})")
        for exc in excluded_entries:
            term.line(
                f"- {term.color256(exc, 244)} {term.color256('[excluded]', 244, bold=True)}"
            )
        term.line()

    # Currency Summary
    counts = {}
    for rd in repo_details:
        st = rd["state"]
        counts[st] = counts.get(st, 0) + 1

    term.heading("Currency")
    for state in (
        "current",
        "source-root",
        "dev",
        "stale",
        "ahead",
        "not-installed",
        "unknown",
    ):
        if counts.get(state):
            badge = _status_badge_256(state, term)
            term.line(f"  {badge} {counts[state]} repo(s)")

    return 0


def _run_exclude(args: argparse.Namespace, term: Term) -> int:
    """aw exclude [repo|repos] repodir1 [repodir2 ...]: exclude repos from aw management."""
    from agent_workflows.result_types import NextAction

    raw_repos = list(getattr(args, "repos", []) or [])
    if raw_repos and raw_repos[0] in ("repo", "repos"):
        raw_repos = raw_repos[1:]

    cfg = config.load()
    current_exclude = sorted(list(cfg.get("exclude", [])), key=lambda s: str(s).lower())
    current_repos = sorted(list(cfg.get("repos", [])), key=lambda s: str(s).lower())
    cfg_path_str = config._preserve_home(str(config.config_path()))
    term.line(
        f"{term.colorize('Config:', 'bold')} {term.color256(cfg_path_str, 39)} "
        f"({len(current_exclude)} excluded, {len(current_repos)} configured)"
    )
    term.line()

    if not raw_repos:
        if not current_exclude:
            term.empty_result(
                summary="no repositories are currently excluded",
                filters=None,
                next_action=NextAction(
                    command="aw exclude <path>", description="exclude a repository"
                ),
            )
            return 0
        term.heading(f"Excluded Repositories ({len(current_exclude)})")
        for e in current_exclude:
            term.line(f"  - {term.color256(e, 244)}")
        return 0

    modified = False
    for target in raw_repos:
        target_path = Path(target).expanduser().resolve()
        entry = config._preserve_home(str(target_path))
        if entry in current_exclude:
            term.status("warn", f"Already excluded: {entry}")
            continue

        current_exclude.append(entry)
        for r_entry in list(current_repos):
            r_path = config.expand_path(str(r_entry)).resolve()
            if r_entry == entry or r_path == target_path:
                current_repos.remove(r_entry)

        term.status("ok", f"Excluded repository: {term.color256(entry, 39, bold=True)}")
        modified = True

    if modified:
        cfg["exclude"] = current_exclude
        cfg["repos"] = current_repos
        config.save(cfg)
    return 0


def _run_include(args: argparse.Namespace, term: Term) -> int:
    """aw include [repo|repos] repodir1 [repodir2 ...]: include repos in aw management."""
    from agent_workflows.result_types import NextAction

    raw_repos = list(getattr(args, "repos", []) or [])
    if raw_repos and raw_repos[0] in ("repo", "repos"):
        raw_repos = raw_repos[1:]

    cfg = config.load()
    current_exclude = sorted(list(cfg.get("exclude", [])), key=lambda s: str(s).lower())
    current_repos = sorted(list(cfg.get("repos", [])), key=lambda s: str(s).lower())
    cfg_path_str = config._preserve_home(str(config.config_path()))
    term.line(
        f"{term.colorize('Config:', 'bold')} {term.color256(cfg_path_str, 39)} "
        f"({len(current_exclude)} excluded, {len(current_repos)} configured)"
    )
    term.line()

    if not raw_repos:
        if not current_repos:
            term.empty_result(
                summary="no explicit repositories configured",
                filters=None,
                next_action=NextAction(
                    command="aw setup", description="set up repositories"
                ),
            )
            return 0
        term.heading(f"Configured Repositories ({len(current_repos)})")
        for e in current_repos:
            term.line(f"  - {term.color256(e, 39)}")
        return 0

    modified = False
    for target in raw_repos:
        target_path = Path(target).expanduser().resolve()
        entry = config._preserve_home(str(target_path))

        removed_from_exclude = False
        for exc_entry in list(current_exclude):
            exc_path = config.expand_path(str(exc_entry)).resolve()
            if exc_entry == entry or exc_path == target_path:
                current_exclude.remove(exc_entry)
                removed_from_exclude = True
                modified = True

        if entry not in current_repos:
            current_repos.append(entry)
            modified = True

        note = " (un-excluded)" if removed_from_exclude else ""
        term.status(
            "ok", f"Included repository: {term.color256(entry, 39, bold=True)}{note}"
        )

    if modified:
        cfg["exclude"] = current_exclude
        cfg["repos"] = current_repos
        config.save(cfg)
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
        return _run_status(argparse.Namespace(as_json=False), term)

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
    from agent_workflows.result_types import NextAction

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
            term.empty_result(
                summary="never-install exclude list is empty",
                filters=None,
                next_action=NextAction(
                    command="aw config exclude add <path>",
                    description="exclude a repository",
                ),
            )
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


def _run_plans(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    from agent_workflows.project_context import (
        is_project_dir,
        no_project_message,
        resolve_verb_repo_root,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    from . import plans as plans_mod

    ctx = context or select_output(args)
    # Climb to the project root so `aw plans` works from any subdirectory; explicit --dir verbatim
    # (IPD awretrofit Order 06).
    explicit_dir = getattr(args, "dir", None)
    root = resolve_verb_repo_root(explicit_dir)
    if not explicit_dir and not is_project_dir(root):
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd board",
                status="cannot-run",
                exit_code=3,
                summary=no_project_message("plans"),
            )
            return get_renderer(ctx).emit(res, ctx)
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
        err_msg = f"Unrecognized --status '{status_filter}'. Valid readiness statuses: {valid}."
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd board",
                status="cannot-run",
                exit_code=2,
                summary=err_msg,
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status(
            "warn",
            err_msg,
        )
        return 2

    # Layout-aware (IPD awretrofit Order 01): resolve the plans dir (.aw/records/plans with a
    # legacy .agents/plans read-fallback) rather than gating on the vanished legacy path.
    plans_dir = plans_mod._resolve_area_dir(root, "plans")
    if not plans_dir.is_dir():
        plans_name = (
            plans_dir.relative_to(root).as_posix()
            if plans_dir.is_relative_to(root)
            else plans_dir.name
        )
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd board",
                status="clean",
                exit_code=0,
                summary="no plans found",
                evidence=[Evidence(key="plans", value={"count": 0}, status="verified")],
                next_actions=[
                    NextAction(
                        command="aw ipd scaffold", description="scaffold a new plan"
                    )
                ],
                data={"plans": []},
            )
            return get_renderer(ctx).emit(res, ctx)
        term.empty_result(
            summary=f"no plans found (no {plans_name} under {root})",
            filters=None,
            next_action=NextAction(
                command="aw ipd scaffold", description="scaffold a new plan"
            ),
        )
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

    if ctx.is_agent or ctx.is_json:
        plan_rows = []
        for r in records:
            try:
                rel = str(r.path.relative_to(root).as_posix())
            except Exception:
                rel = str(r.path)
            plan_rows.append(
                {
                    "path": rel,
                    "area": r.area,
                    "disposition": r.disposition,
                    "status": r.status,
                    "set_id": r.set_id,
                    "order": r.order,
                }
            )
        filters_map = {}
        if getattr(args, "pending", False):
            filters_map["disposition"] = "pending"
        if status_filter:
            filters_map["status"] = status_filter
        next_act = (
            [NextAction(command="aw ipd board", description="view full board")]
            if filters_map and not records
            else [
                NextAction(command="aw ipd scaffold", description="scaffold a new plan")
            ]
            if not records
            else []
        )
        res = CommandResult(
            command="ipd board",
            status="clean",
            exit_code=0,
            summary=f"ipd board: {len(records)} plan(s)"
            if records
            else "no matching plans",
            evidence=[
                Evidence(
                    key="plans-board",
                    value={"count": len(records)},
                    status="verified",
                )
            ],
            next_actions=next_act,
            data={"plans": plan_rows, "count": len(records), "filters": filters_map},
        )
        return get_renderer(ctx).emit(res, ctx)

    if not records:
        filters_map = {}
        if getattr(args, "pending", False):
            filters_map["disposition"] = "pending"
        if status_filter:
            filters_map["status"] = status_filter
        next_act = (
            NextAction(command="aw ipd board", description="view full board")
            if filters_map
            else NextAction(
                command="aw ipd scaffold", description="scaffold a new plan"
            )
        )
        term.empty_result(
            summary="no matching plans",
            filters=filters_map if filters_map else None,
            next_action=next_act,
        )
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


def _run_context(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    """Inspect resolved AW project context (spec Section 9 & Order 02 E-05)."""
    import json

    from agent_workflows.project_context import (
        ProjectContextError,
        redact_public_context,
        resolve_project_context,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        select_output,
    )

    ctx_out = context or select_output(args)
    try:
        ctx = resolve_project_context(target_repo=getattr(args, "repo", None))
    except ProjectContextError as exc:
        if ctx_out.is_agent or ctx_out.is_json:
            res = CommandResult(
                command="context",
                status="cannot-run",
                exit_code=1,
                summary=str(exc),
                diagnostics=[
                    Diagnostic(
                        location=str(getattr(args, "repo", None) or "."),
                        rule="context.error",
                        detail=str(exc),
                        severity="error",
                    )
                ],
            )
            return get_renderer(ctx_out).emit(res, ctx_out)
        term.status("fail", str(exc))
        return 1

    if getattr(args, "public", False):
        redacted = redact_public_context(ctx.to_dict())
        if ctx_out.is_agent or ctx_out.is_json:
            res = CommandResult(
                command="context",
                status="clean",
                exit_code=0,
                summary="project context (public redacted)",
                data=redacted,
            )
            return get_renderer(ctx_out).emit(res, ctx_out)
        print(json.dumps(redacted, indent=2))
        return 0

    if ctx_out.is_agent or ctx_out.is_json:
        res = CommandResult(
            command="context",
            status="clean",
            exit_code=0,
            summary="project context",
            data=ctx.to_dict(),
        )
        return get_renderer(ctx_out).emit(res, ctx_out)

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
        ProjectContextError,
        resolve_project_context,
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


def _run_project_status(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    import os

    from agent_workflows import config
    from agent_workflows.project_registry import (
        find_project,
        get_registry_path,
        load_registry,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
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
        "filters": {"target_repo": repo_path},
    }

    if ctx.is_agent or ctx.is_json:
        next_act = (
            [
                NextAction(
                    command="aw project attach <project-id>",
                    description="attach to project",
                )
            ]
            if not match_res.entry
            else []
        )
        res = CommandResult(
            command="project status",
            status="clean",
            exit_code=0,
            summary=(
                f"matched project {match_res.entry.project_id}"
                if match_res.entry
                else "no registered project association found"
            ),
            evidence=[
                Evidence(
                    key="project-match",
                    value={
                        "matched": bool(match_res.entry),
                        "kind": match_res.match_kind,
                    },
                    status="verified" if match_res.entry else "unverified",
                )
            ],
            next_actions=next_act,
            data=status_data,
        )
        return get_renderer(ctx).emit(res, ctx)

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
        term.empty_result(
            summary="no registered project association found",
            filters={"target_repo": repo_path},
            next_action=NextAction(
                command="aw project attach <project-id>",
                description="attach to project",
            ),
        )
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


def _run_storage_status(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    import os

    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        select_output,
    )
    from agent_workflows.storage import StorageError, get_storage_status

    ctx = context or select_output(args)
    repo_path = getattr(args, "repo", None) or os.getcwd()
    try:
        st = get_storage_status(repo_path=repo_path)
    except StorageError as exc:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="storage status",
                status="cannot-run",
                exit_code=1,
                summary=str(exc),
                diagnostics=[
                    Diagnostic(
                        location=repo_path,
                        rule="storage.error",
                        detail=str(exc),
                        severity="error",
                    )
                ],
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status("fail", str(exc))
        return 1

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="storage status",
            status="clean",
            exit_code=0,
            summary=f"records storage: {st.records_backend} ({st.durability_state})",
            evidence=[
                Evidence(
                    key="storage",
                    value={
                        "backend": st.records_backend,
                        "durability": st.durability_state,
                    },
                    status="verified",
                )
            ],
            data=st.to_dict(),
        )
        return get_renderer(ctx).emit(res, ctx)

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

    from agent_workflows.storage import StorageError, init_records_storage

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
        StorageError,
        acknowledge_remote_durability,
        attach_companion,
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

    from agent_workflows.storage import StorageError, detach_companion

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

    from agent_workflows.storage import StorageError, move_companion

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

    from agent_workflows.storage import StorageError, reattach_companion

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

    from agent_workflows.storage import StorageError, validate_companion_preflight

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


def _run_show(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    from agent_workflows import selectors
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
    ref = args.action_ref
    # 1. Try to resolve the token as a RECORDS artifact (id6 | setid | filename | status),
    #    searching each record type; print every match.
    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    record_types = (
        "plans",
        "specs",
        "research",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
    )
    hits: list = []
    for rt in record_types:
        hits.extend(selectors.resolve_selectors(repo_root, rt, [ref]))
    # de-dup preserving order
    seen: set = set()
    unique = [p for p in hits if not (str(p) in seen or seen.add(str(p)))]
    if unique:
        if ctx.is_agent or ctx.is_json:
            contents = {}
            for p in unique:
                try:
                    contents[str(p)] = p.read_text(encoding="utf-8")
                except OSError:
                    pass
            res = CommandResult(
                command="show",
                status="clean",
                exit_code=0,
                summary=f"matched {len(unique)} artifact(s)",
                evidence=[
                    Evidence(
                        key="show-match",
                        value={"count": len(unique)},
                        status="verified",
                    )
                ],
                data={"matches": [str(p) for p in unique], "contents": contents},
            )
            return get_renderer(ctx).emit(res, ctx)

        for p in unique:
            term.heading(str(p))
            print(p.read_text(encoding="utf-8"))
        return 0

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="show",
            status="findings",
            exit_code=1,
            summary=f"No records artifact matched '{ref}'.",
            diagnostics=[
                Diagnostic(
                    location=ref,
                    rule="show.not_found",
                    detail=f"No records artifact matched '{ref}'.",
                    severity="error",
                )
            ],
            next_actions=[
                NextAction(command="aw find", description="list all records")
            ],
        )
        return get_renderer(ctx).emit(res, ctx)

    term.empty_result(
        summary=f"no records artifact matched '{ref}'",
        filters={"ref": ref},
        next_action=NextAction(command="aw find", description="list all records"),
        status="fail",
    )
    return 1


def _run_record_history(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    import os
    from pathlib import Path

    from agent_workflows import record_history as rh
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    id6 = args.id6
    records = rh.read_for(repo_root, id6)
    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="record-history",
            status="clean",
            exit_code=0,
            summary=(
                f"history for {id6} ({len(records)} entries)"
                if records
                else f"no sidecar history for id6 {id6}"
            ),
            evidence=[
                Evidence(
                    key="history-count",
                    value={"count": len(records)},
                    status="verified" if records else "unverified",
                )
            ],
            next_actions=[
                NextAction(command=f"aw show {id6}", description="view record content")
            ]
            if not records
            else [],
            data={"id6": id6, "history": records, "filters": {"id6": id6}},
        )
        return get_renderer(ctx).emit(res, ctx)

    if not records:
        term.empty_result(
            summary=f"no sidecar history for id6 {id6}",
            filters={"id6": id6},
            next_action=NextAction(
                command=f"aw show {id6}", description="view record content"
            ),
            status="clean",
        )
        return 0
    term.heading(f"History for {id6}")
    for r in records:
        date = r.get("date", "")
        workflow = r.get("workflow", "")
        actor = r.get("actor", "")
        tree = r.get("tree", "")
        message = r.get("message", "")
        who = f" ({actor})" if actor else ""
        wf = f" {workflow}" if workflow else ""
        term.line(f"- {date} [{tree}]{wf}{who}: {message}")
    return 0


def _nv_resolve_types(args, term, verb):
    """Resolve the verb's TYPE argument to a list of supported types, or None on error (after
    emitting a fail). `all` expands to every type this verb has a backend for."""
    from agent_workflows import artifact_types as at

    try:
        norm = at.normalize_type(args.type)
    except ValueError as exc:
        term.status("fail", str(exc))
        return None
    if norm == "all":
        types = [t for t in at.ARTIFACT_TYPES if at.backend_name(t, verb)]
        if not types:
            term.status("fail", f"'{verb}' is not supported for any type yet.")
            return None
        return types
    if at.backend_name(norm, verb) is None:
        term.status("warn", f"'{verb}' is not supported for {norm}.")
        return None
    return [norm]


def _nv_backend_args(args, artifact_type):
    """Build an args namespace a legacy backend runner understands from the noun-verb args."""
    import os

    sub = argparse.Namespace(**vars(args))
    sub.dir = getattr(args, "dir", None) or os.getcwd()
    sub.agent = bool(getattr(args, "as_agent", False))
    sub.resolved_type = artifact_type
    # Map a positional selector onto the backend's expected --id (rename/group take an id6 positional).
    sel = list(getattr(args, "selector", None) or [])
    if sel and not getattr(sub, "id", None):
        sub.id = sel[0]
    # group (run_set_assign) takes a LIST of ids; rename (run_mv) takes one --id.
    if sel:
        sub.ids = sel
    return sub


def _highlight_matches(text: str, rx: re.Pattern, term: Term) -> str:
    """Highlight regex match(es) in text using bold yellow when color is active."""
    if not term.color:
        return text
    return rx.sub(lambda m: term.colorize(m.group(0), "bold", "yellow"), text)


def _run_noun_verb(
    args: argparse.Namespace,
    term: Term,
    context: Optional[Any] = None,
) -> int:
    """awcmdsurf: dispatch a noun-verb command to the right backend. Order 01 scaffolded the router;
    Order 02 wires index/find/search/check; Order 03 wires rename/group (+ archive)."""
    verb = args.command
    if verb == "search":
        return _run_search(args, term, context=context)
    if verb == "check":
        return _run_check(args, term, context=context)
    if verb == "find":
        return _run_find(args, term, context=context)
    types = _nv_resolve_types(args, term, verb)
    if types is None:
        return 2
    from agent_workflows import artifact_types as at

    rc = 0
    for t in types:
        fn = at.resolve_backend(t, verb)
        if fn is None:
            term.status("warn", f"'{verb}' is not yet wired / not supported for {t}.")
            rc = max(rc, 2)
            continue
        result = fn(_nv_backend_args(args, t))
        if isinstance(result, int):
            rc = max(rc, result)
    return rc


def _find_type_records(
    repo_root: Path,
    artifact_type: str,
    selectors_list: List[str],
    args: argparse.Namespace,
    term: Term,
) -> List[str]:
    """Find and format matching records for a given artifact type. Returns lines to print."""
    from agent_workflows import selectors as sel_mod

    if artifact_type == "plans":
        from agent_workflows import plans_index as pi

        _repo, plans_dir = pi._dirs(args)
        entries, _drift = pi.scan_plans(plans_dir)
        explicit_id = getattr(args, "id", None)
        explicit_set = getattr(args, "set", None)
        explicit_status = getattr(args, "status", None)
        explicit_disp = getattr(args, "disposition", None)

        if selectors_list:
            matched = set(
                p.resolve()
                for p in sel_mod.resolve_selectors(repo_root, "plans", selectors_list)
            )
            results = [
                e
                for e in entries
                if (plans_dir / e.path).resolve() in matched
                or (repo_root / e.path).resolve() in matched
            ]
            if explicit_set or explicit_status or explicit_disp or explicit_id:
                results = pi.query(
                    results,
                    plan_id=explicit_id,
                    set_id=explicit_set,
                    status=explicit_status,
                    disposition=explicit_disp,
                )
        else:
            results = pi.query(
                entries,
                plan_id=explicit_id,
                set_id=explicit_set,
                status=explicit_status,
                disposition=explicit_disp,
            )

        lines = []
        for e in results:
            status = e.disposition or e.status or "-"
            status_txt = term.status_256(status, width=12)
            id6_txt = (
                term.color256(e.plan_id or "??????", 39, bold=True)
                if term.color
                else (e.plan_id or "??????")
            )
            set_txt = f"{e.set_id or '-':<14}"
            lines.append(f"{status_txt}  {id6_txt}  {set_txt}  {e.path}")
        return lines

    if artifact_type == "research":
        from agent_workflows import research_index as ri

        _repo, research_root = ri._roots(args)
        entries, _drift = ri._scan_docs(research_root)
        explicit_id = getattr(args, "id", None)
        explicit_set = getattr(args, "set", None)
        explicit_topic = getattr(args, "topic", None)
        explicit_status = getattr(args, "status", None)

        if selectors_list:
            matched = set(
                p.resolve()
                for p in sel_mod.resolve_selectors(
                    repo_root, "research", selectors_list
                )
            )
            results = [
                e
                for e in entries
                if (research_root / e.path).resolve() in matched
                or (repo_root / e.path).resolve() in matched
            ]
            if explicit_set or explicit_status or explicit_topic or explicit_id:
                results = ri.query(
                    results,
                    id6=explicit_id,
                    set_id=explicit_set,
                    topic=explicit_topic,
                    status=explicit_status,
                )
        else:
            results = ri.query(
                entries,
                id6=explicit_id,
                set_id=explicit_set,
                topic=explicit_topic,
                status=explicit_status,
            )

        lines = []
        for e in results:
            status = e.status or "-"
            status_txt = term.status_256(status, width=12)
            id6_txt = (
                term.color256(e.id6 or "??????", 39, bold=True)
                if term.color
                else (e.id6 or "??????")
            )
            summary = f"  {e.summary}" if e.summary else ""
            lines.append(f"{status_txt}  {id6_txt}  {e.path}{summary}")
        return lines

    # All other types: specs, prompts, backlog, walkthroughs, roadmaps, comms, releases
    if selectors_list:
        matched_paths = sel_mod.resolve_selectors(
            repo_root, artifact_type, selectors_list
        )
    else:
        matched_paths = [p for p, _ in sel_mod._iter_files(repo_root, artifact_type)]

    lines = []
    for p in sorted(matched_paths):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        id6 = sel_mod._read_id(text) or "-"
        status = sel_mod._read_status(text) or "-"
        try:
            rel = str(p.relative_to(repo_root))
        except ValueError:
            rel = str(p)
        status_txt = term.status_256(status, width=12)
        id6_txt = term.color256(id6, 39, bold=True) if term.color else id6
        lines.append(f"{status_txt}  {id6_txt}  {rel}")
    return lines


def _run_find(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    """awcmdsurf Order 02 / highpbacklog0822 Order 04: find artifacts with empty-state UX."""
    import os
    from pathlib import Path

    from agent_workflows import artifact_types as at
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
    raw_type = getattr(args, "type", None)
    raw_selector = list(getattr(args, "selector", None) or [])

    if at.is_type_token(raw_type):
        norm = at.normalize_type(raw_type)
        selectors = raw_selector
    else:
        norm = "all"
        selectors = ([raw_type] if raw_type is not None else []) + raw_selector

    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    types = at.ARTIFACT_TYPES if norm == "all" else (norm,)

    all_lines = []
    explicit_flags = argparse.Namespace(
        id=getattr(args, "id", None),
        set=getattr(args, "set", None),
        status=getattr(args, "status", None),
        topic=getattr(args, "topic", None),
        disposition=getattr(args, "disposition", None),
        dir=getattr(args, "dir", None),
    )
    for t in types:
        lines = _find_type_records(repo_root, t, selectors, explicit_flags, term)
        all_lines.extend(lines)

    # Active filter facts and next action recommendation (highpbacklog0822 Order 04 E-03)
    filters_dict = {"type": norm}
    if selectors:
        filters_dict["selector"] = " ".join(selectors)

    if selectors:
        next_cmd = f"aw find {norm}" if norm != "all" else "aw find"
        next_desc = (
            f"list all {norm} without selector filter"
            if norm != "all"
            else "list all artifacts without selector filter"
        )
    elif norm != "all":
        next_cmd = "aw find"
        next_desc = "search across all artifact types"
    else:
        next_cmd = "aw status"
        next_desc = "check workspace status"

    summary_text = (
        f"found {len(all_lines)} {norm} artifact(s)"
        if all_lines
        else (f"no matching {norm}" if norm != "all" else "no matching artifacts")
    )

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="find",
            status="clean",
            exit_code=0,
            summary=summary_text,
            evidence=[
                Evidence(
                    key="find-count",
                    value={
                        "count": len(all_lines),
                        "type": norm,
                        "selectors": selectors,
                    },
                    status="verified",
                )
            ],
            next_actions=[NextAction(command=next_cmd, description=next_desc)],
            data={
                "matches": all_lines,
                "type": norm,
                "selectors": selectors,
                "count": len(all_lines),
                "filters": filters_dict,
            },
        )
        return get_renderer(ctx).emit(res, ctx)

    if not all_lines:
        term.empty_result(
            summary=summary_text,
            filters=filters_dict,
            next_action=NextAction(command=next_cmd, description=next_desc),
        )
        return 0

    for line in all_lines:
        term.line(line)
    return 0


def _run_archive(args: argparse.Namespace, term: Term) -> int:
    """awcmdsurf Order 03: generalized `archive <type> [target]`. If the first positional is a known
    TYPE (research|plans|all), route by type; otherwise treat it as a research target (back-compat:
    `aw archive <id6>` still archives research)."""
    from agent_workflows import artifact_types as at

    tot = getattr(args, "type_or_target", None)
    resolved_type = None
    if tot is not None:
        try:
            resolved_type = at.normalize_type(tot)
        except ValueError:
            resolved_type = None  # not a type -> it's a research target (back-compat)

    def _archive_one(t):
        sub = argparse.Namespace(**vars(args))
        # a type-led invocation shifts target to the second positional; a back-compat invocation
        # keeps `type_or_target` as the research target.
        if resolved_type is not None:
            sub.target = getattr(args, "target", None)
        else:
            sub.target = tot
        if t == "plans":
            from agent_workflows import plans_archive as pa

            return pa.run_archive(sub)
        from agent_workflows import research_archive as ra

        return ra.run_archive(sub)

    if resolved_type == "all":
        rc = 0
        for t in ("research", "plans"):
            r = _archive_one(t)
            if isinstance(r, int):
                rc = max(rc, r)
        return rc
    if resolved_type in ("plans", "research"):
        r = _archive_one(resolved_type)
        return r if isinstance(r, int) else 0
    # back-compat: research target (or bare sweep)
    r = _archive_one("research")
    return r if isinstance(r, int) else 0


def _run_search(
    args: argparse.Namespace, term: Term, context: Optional[Any] = None
) -> int:
    """Search record tree(s) for regex matches. If the first positional is a known TYPE,
    restricts search to that type; otherwise searches 'all' types. Prints file path once
    in bold blue, followed by matching lines with matches highlighted in bold yellow
    (with line numbers if --line-numbers)."""
    import os
    import re
    from pathlib import Path

    from agent_workflows import artifact_types as at
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    ctx = context or select_output(args)
    raw_type = getattr(args, "type", None)
    raw_selector = list(getattr(args, "selector", None) or [])

    if at.is_type_token(raw_type):
        norm = at.normalize_type(raw_type)
        pattern_tokens = raw_selector
    else:
        norm = "all"
        pattern_tokens = ([raw_type] if raw_type is not None else []) + raw_selector

    pattern = " ".join(pattern_tokens) if pattern_tokens else None
    if not pattern:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="search",
                status="cannot-run",
                exit_code=2,
                summary="search requires a pattern (positional selector).",
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status("fail", "search requires a pattern (positional selector).")
        return 2
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="search",
                status="cannot-run",
                exit_code=2,
                summary=f"invalid regex: {exc}",
            )
            return get_renderer(ctx).emit(res, ctx)
        term.status("fail", f"invalid regex: {exc}")
        return 2

    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    types = at.ARTIFACT_TYPES if norm == "all" else (norm,)
    line_numbers = getattr(args, "line_numbers", False)

    hits = 0
    json_results = []

    for t in types:
        for base in (repo_root / ".aw" / "records" / t, repo_root / ".agents" / t):
            if not base.is_dir():
                continue
            for p in sorted(base.rglob("*.md")):
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue

                file_matches = []
                for i, line in enumerate(text.split("\n"), 1):
                    if rx.search(line):
                        hits += 1
                        file_matches.append((i, line))
                        json_results.append(
                            {"path": str(p), "line": i, "text": line.strip()}
                        )

                if file_matches and not (ctx.is_agent or ctx.is_json):
                    file_header = (
                        term.color256(str(p), 39, bold=True) if term.color else str(p)
                    )
                    term.line(file_header)
                    for i, line in file_matches:
                        highlighted = _highlight_matches(line.strip(), rx, term)
                        if line_numbers:
                            line_no = (
                                term.color256(f"{i}:", 244) if term.color else f"{i}:"
                            )
                            term.line(f"  {line_no} {highlighted}")
                        else:
                            term.line(f"  {highlighted}")

    if ctx.is_agent or ctx.is_json:
        exit_code = 0 if hits else 1
        status = "clean" if hits else "findings"
        next_actions = (
            [
                NextAction(
                    command="aw search <pattern>",
                    description="search with broader pattern",
                )
            ]
            if not hits
            else []
        )
        res = CommandResult(
            command="search",
            status=status,
            exit_code=exit_code,
            summary=f"found {hits} match(es)"
            if hits
            else f"no matching lines for '{pattern}'",
            evidence=[
                Evidence(
                    key="search-hits",
                    value={"count": hits},
                    status=status,
                )
            ],
            next_actions=next_actions,
            data={
                "pattern": pattern,
                "hits": hits,
                "matches": json_results,
                "filters": {"type": norm, "pattern": pattern},
            },
        )
        return get_renderer(ctx).emit(res, ctx)

    if not hits:
        term.empty_result(
            summary=f"no matching lines for '{pattern}'",
            filters={"type": norm, "pattern": pattern},
            next_action=NextAction(
                command="aw search <pattern>",
                description="search with broader pattern",
            ),
            status="findings",
        )
        return 1

    return 0


def _run_check(
    args: argparse.Namespace,
    term: Term,
    context: Optional[Any] = None,
) -> int:
    """awcmdsurf Order 02 / awcliux Order 02: validate a TYPE via the check engine with the doctor-derived recipe."""
    import os
    import time
    from pathlib import Path

    from agent_workflows import artifact_core as core
    from agent_workflows import artifact_types as at
    from agent_workflows import check_engine as ce
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        NextAction,
        select_output,
    )

    start_time = time.monotonic()
    ctx = context or select_output(args)
    raw_type = getattr(args, "type", None) or "all"
    repo_root = Path(getattr(args, "dir", None) or os.getcwd())

    try:
        norm = at.normalize_type(raw_type)
    except ValueError as exc:
        err_msg = str(exc)
        result = CommandResult(
            command="check",
            status="error",
            exit_code=2,
            summary=err_msg,
            next_actions=[NextAction(command="aw check --help")],
            data={"target": raw_type, "repo_root": repo_root},
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(result, ctx)

    selectors = list(getattr(args, "selector", None) or [])
    only_names = "names" in selectors
    target_types = [norm] if norm != "all" else list(at.ARTIFACT_TYPES)

    try:
        drift = ce.check_types(
            repo_root,
            [norm] if norm != "all" else ["all"],
            names_only=only_names,
            collisions=(norm == "all"),
        )
    except Exception:
        fn = at.resolve_backend(norm, "check")
        if fn is None:
            result = CommandResult(
                command="check",
                status="error",
                exit_code=2,
                summary=f"'check' is not supported for {norm}.",
                next_actions=[NextAction(command="aw check --help")],
                data={"target": norm, "repo_root": repo_root},
            )
            return get_renderer(ctx).emit(result, ctx)
        res_code = fn(_nv_backend_args(args, norm))
        return res_code if isinstance(res_code, int) else 0

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    # Count checked files
    type_counts: dict[str, int] = {}
    total_checked = 0
    for t in target_types:
        try:
            files = list(ce._iter_type_files(repo_root, t))
            type_counts[t] = len(files)
            total_checked += len(files)
        except Exception:
            type_counts[t] = 0

    # Build diagnostics from drift
    diagnostics = []
    from agent_workflows import doctor as _doctor

    seen_fixes = set()
    for d in drift:
        try:
            title, dir_str, fname, extra, fix = _doctor._categorize_drift(d, repo_root)
        except Exception:
            fix = None
        diagnostics.append(
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity="error",
                fix=fix or None,
            )
        )
        if fix and fix not in seen_fixes:
            seen_fixes.add(fix)

    exit_code = core.drift_exit_code(drift)
    status = "conforms" if exit_code == 0 else "findings"
    target_label = norm if norm != "all" else "all"

    if exit_code == 0:
        summary = f"{total_checked} {target_label} checked"
    else:
        summary = (
            f"{len(drift)} finding(s) detected across {total_checked} {target_label}"
        )

    # Evidence breakdown
    evidence = []
    if norm == "plans":
        plans_dir = repo_root / ".aw" / "records" / "plans"
        if not plans_dir.is_dir():
            plans_dir = repo_root / ".agents" / "plans"
        pending_cnt = (
            len(list((plans_dir / "pending").glob("*.md")))
            if (plans_dir / "pending").is_dir()
            else 0
        )
        reusable_cnt = (
            len(list((plans_dir / "reusable").glob("*.md")))
            if (plans_dir / "reusable").is_dir()
            else 0
        )
        terminal_cnt = sum(
            len(list((plans_dir / d).glob("*.md")))
            for d in ("executed", "parked", "superseded", "not-executed")
            if (plans_dir / d).is_dir()
        )
        evidence.append(
            Evidence(
                key="inventory",
                value={
                    "pending": pending_cnt,
                    "reusable": reusable_cnt,
                    "terminal": terminal_cnt,
                },
                status="verified",
            )
        )
    else:
        evidence.append(
            Evidence(
                key="inventory",
                value=type_counts
                if len(type_counts) > 1
                else {"checked": total_checked},
                status="verified",
            )
        )

    err_cnt = sum(1 for d in drift if not d.rule.startswith("warn"))
    warn_cnt = sum(1 for d in drift if d.rule.startswith("warn"))
    evidence.append(
        Evidence(
            key="rules",
            value={"errors": err_cnt, "warnings": warn_cnt},
            status="clean" if exit_code == 0 else "findings",
        )
    )

    # Next actions
    next_actions = []
    if exit_code == 0:
        if norm in ("plans", "all"):
            next_actions.append(NextAction(command="aw ipd board"))
        elif norm == "specs":
            next_actions.append(NextAction(command="aw specs check"))
        elif norm == "research":
            next_actions.append(NextAction(command="aw research find"))
        elif norm == "backlog":
            next_actions.append(NextAction(command="aw backlog check"))
    else:
        for f in seen_fixes:
            next_actions.append(NextAction(command=f))
        if not next_actions:
            next_actions.append(NextAction(command=f"aw check {norm}"))

    result = CommandResult(
        command="check",
        status=status,
        exit_code=exit_code,
        summary=summary,
        diagnostics=diagnostics,
        evidence=evidence,
        next_actions=next_actions,
        data={
            "target": target_label,
            "elapsed_ms": elapsed_ms,
            "repo_root": repo_root,
            "drift": drift,
            "type_counts": type_counts,
        },
        verified=True,
        complete=True,
    )
    return get_renderer(ctx).emit(result, ctx)


def _run_migrate_layout(args: argparse.Namespace, term: Term) -> int:
    import io
    import json
    import os
    import sys
    from pathlib import Path

    from agent_workflows import layout_inventory as inv_mod
    from agent_workflows.layout_migration import (
        MigrationError,
        MigrationManager,
        is_stale_tool_litter,
    )

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
        stale_litter = []
        workflows_dir = repo_path / ".agents" / "workflows"
        if workflows_dir.is_dir():
            for p in sorted(workflows_dir.rglob("*")):
                rel = str(p.relative_to(repo_path).as_posix())
                if is_stale_tool_litter(repo_path, rel):
                    stale_litter.append(rel)

        term.line()
        term.line(
            "Post-move leftover disposition (legacy material not moved by migration):"
        )
        if stale_litter:
            term.status(
                "warn",
                f"Detected {len(stale_litter)} untracked stale-tool litter item(s) under .agents/workflows/ "
                "(e.g. __pycache__/*.pyc or emptied tools dirs).",
            )
            term.line(
                "  Choosing [3] 'remove' will sweep this litter; [1] 'defer' and [2] 'keep' will leave it intact."
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
        if stale_litter:
            term.status(
                "info",
                f"Stale-Tool Litter:     {len(stale_litter)} item(s) ({'swept' if selected_leftovers == 'remove' else 'preserved'})",
            )
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


def _rewrite_help_token(argv):
    """awhelparg Order 01: rewrite a standalone `help` subcommand token to `--help` so `aw help`,
    `aw ipd help`, `aw <verb> help` all show help. A `help` that is an OPTION VALUE (the token
    immediately follows an option like `--message`) is left verbatim. Returns a new list."""
    if not argv:
        return []
    # If the root command is a freeform search/query verb, do NOT rewrite positional 'help' to '--help'
    # because 'help' is a valid query or selector (e.g. `aw search help`, `aw find help`, `aw show help`).
    if argv[0] in ("search", "find", "show"):
        return list(argv)
    out = []
    for i, tok in enumerate(argv):
        prev = argv[i - 1] if i > 0 else ""
        if tok == "help" and not prev.startswith("-"):
            out.append("--help")
        else:
            out.append(tok)
    return out


def _show_family_help(
    parser: argparse.ArgumentParser,
    cmd_name: str,
    next_cmd: str,
    term: Term,
    context: Optional[Any] = None,
) -> int:
    subparsers_action = next(
        (a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None
    )
    subparser = subparsers_action.choices.get(cmd_name) if subparsers_action else None
    if subparser:
        help_text = subparser.format_help()
    else:
        help_text = parser.format_help()

    if context and getattr(context, "is_agent", False):
        from agent_workflows.renderers import get_renderer
        from agent_workflows.result_types import CommandResult, NextAction

        res = CommandResult(
            command=cmd_name,
            status="cannot-run",
            exit_code=2,
            summary=f"missing required subcommand for {cmd_name}",
            next_actions=[NextAction(command=next_cmd)],
            data={"target": cmd_name},
            verified=False,
            complete=False,
        )
        return get_renderer(context).emit(res, context)

    print(help_text.rstrip())
    print()
    print(term.format_next_action(next_cmd))
    return 2


def _dispatch(argv: Optional[Sequence[str]]) -> int:
    parser = _build_parser()
    # awcmdsurf Order 05 (hard cutover): the `aw plans <verb>` -> `plans-<verb>` alias shim was
    # removed with the plan-family verbs; the grammar is now `aw <verb> plans` (index/find/...).
    # awhelparg Order 01: a bare `help` token becomes `--help` (natural `aw ipd help` UX).
    argv_list = list(sys.argv[1:] if argv is None else argv)
    argv = _rewrite_help_token(argv_list)
    args = parser.parse_args(argv)

    try:
        context = select_output(args)
    except ConflictingFlagsError as exc:
        print(f"agent-workflows: error: {exc}", file=sys.stderr)
        print("Next  aw --help", file=sys.stderr)
        return 2

    term = Term(color=context.color)

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
            if context.is_agent or context.is_json:
                return _run_status(
                    argparse.Namespace(as_json=False), term, context=context
                )
            term.status("warn", "Not configured. Run 'aw setup' to get started.")
            return _run_status(argparse.Namespace(as_json=False), term, context=context)
        if context.is_agent or context.is_json:
            return _run_status(argparse.Namespace(as_json=False), term, context=context)
        _run_status(argparse.Namespace(as_json=False), term, context=context)
        term.line()
        term.line(
            "Commands: install <dir>|all, setup, todo, complete, dismiss, status, plans, "
            "check-local-leaks. See 'aw --help'."
        )
        return 0

    if args.command == "project":
        project_cmd = getattr(args, "project_command", None)
        if project_cmd == "status":
            return _run_project_status(args, term, context=context)
        if project_cmd == "attach":
            return _run_project_attach(args, term)
        if project_cmd == "move":
            return _run_project_move(args, term)
        return _show_family_help(parser, "project", "aw project status", term, context)
    if args.command == "storage":
        storage_cmd = getattr(args, "storage_command", None)
        if storage_cmd == "status":
            return _run_storage_status(args, term, context=context)
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
        return _show_family_help(parser, "storage", "aw storage status", term, context)
    if args.command == "config":
        if getattr(args, "config_command", None) == "exclude":
            return _run_config_exclude(args, term)
        return _show_family_help(
            parser, "config", "aw config exclude list", term, context
        )
    if args.command == "todo":
        # awcmdsurf Order 04 (item 32/D5): `todo` is an alias of `attention` (the cross-tree board).
        from agent_workflows import attention as att

        return att.run(args)
    if args.command == "show":
        return _run_show(args, term, context=context)
    if args.command == "record-history":
        return _run_record_history(args, term, context=context)
    if args.command in ("check", "find", "search", "index", "rename", "group"):
        return _run_noun_verb(args, term, context=context)
    if args.command == "migrate-layout":
        return _run_migrate_layout(args, term)
    if args.command == "install":
        return _run_install(args, term)
    if args.command == "uninstall":
        return _run_uninstall(args, term)
    if args.command == "list-repos":
        return _run_list(args, term, context=context)
    if args.command == "exclude":
        return _run_exclude(args, term)
    if args.command == "include":
        return _run_include(args, term)
    if args.command == "status":
        return _run_status(args, term, context=context)

    if args.command == "normalize-lanes":
        import os as _os

        from agent_workflows import engine as _engine

        repo_root = Path(getattr(args, "dir", None) or _os.getcwd())
        renamed = _engine.migrate_local_lanes_to_untracked(repo_root, {})
        if renamed:
            for r in renamed:
                term.status("ok", f"renamed lane -> {r}")
        else:
            term.status("ok", "no 'local/' lane to rename; nothing to do.")
        return 0
    if args.command == "doctor":
        from agent_workflows import doctor as _doctor

        return _doctor.run(args, term, context=context)
    if args.command == "setup":
        return _run_setup(args, term)
    # awcmdsurf Order 05 (hard cutover): the plan-family + `list` + `plan-names` command dispatch was
    # removed. Those capabilities are the noun-verb grammar (ipd board / index|find|group|rename|
    # archive plans / check <type> names / list-repos). _run_plans is retained: `ipd board` calls it.
    if args.command == "workflow":
        if not getattr(args, "workflow_command", None):
            return _show_family_help(
                parser, "workflow", "aw workflow validate <pkg>", term, context=context
            )
        from agent_workflows import workflow_cli

        return workflow_cli.run_workflow(args)
    if args.command == "run":
        if not getattr(args, "run_command", None):
            return _show_family_help(
                parser, "run", "aw run show <target>", term, context=context
            )
        from agent_workflows import run_cli

        return run_cli.run_cli(args)
    if args.command == "set":
        from agent_workflows import status_set

        return status_set.run_set_command(
            args.args,
            scoped_type=None,
            args=args,
            term=term,
        )
    if args.command in ("ipd", "plan", "plans"):
        ipd_cmd = (
            getattr(args, "ipd_command", None)
            or getattr(args, "plans_command", None)
            or getattr(args, "plan_command", None)
        )
        if ipd_cmd == "set":
            from agent_workflows import status_set

            return status_set.run_set_command(
                args.args,
                scoped_type="plans",
                args=args,
                term=term,
            )
        if ipd_cmd == "lint":
            from agent_workflows import ipd_lint

            return ipd_lint.run_lint(args)
        if ipd_cmd == "scaffold":
            from agent_workflows import ipd_authoring

            return ipd_authoring.run_scaffold(args)
        if ipd_cmd == "sync":
            from agent_workflows import ipd_authoring

            return ipd_authoring.run_sync(args)
        if ipd_cmd == "execute-set":
            from agent_workflows import ipd_set_plan

            return ipd_set_plan.run_execute_set(args)
        if ipd_cmd == "begin":
            from agent_workflows import ipd_lifecycle

            return ipd_lifecycle.run_begin(args)
        if ipd_cmd == "finalize":
            from agent_workflows import ipd_lifecycle

            return ipd_lifecycle.run_finalize(args)
        # awcmdsurf Order 04: `ipd board` and bare `aw ipd` both show the IPD board.
        if ipd_cmd == "board" or ipd_cmd is None:
            return _run_plans(args, term, context=context)
        return _show_family_help(parser, "ipd", "aw ipd board", term, context)
    if args.command in ("prompt", "prompts"):
        prompt_cmd = getattr(args, "prompts_command", None) or getattr(
            args, "prompt_command", None
        )
        if prompt_cmd == "set":
            from agent_workflows import status_set

            return status_set.run_set_command(
                args.args,
                scoped_type="prompts",
                args=args,
                term=term,
            )
        return _show_family_help(
            parser, "prompts", "aw prompts set <status> <target>", term, context
        )
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
        if research_cmd == "set-outcome":
            from agent_workflows import research_cmd as rc

            return rc.run_set_outcome(args)
        if research_cmd == "pending":
            from agent_workflows import research_index as ri

            return ri.run_pending(args)
        if research_cmd == "check-miscategorized":
            from agent_workflows import research_archive as ra

            return ra.run_check_miscategorized(args)
        return _show_family_help(parser, "research", "aw research find", term, context)
    if args.command == "context":
        return _run_context(args, term, context=context)
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
            if getattr(args, "status", None) is None:
                from agent_workflows import status_set

                return status_set.run_set_command(
                    args.args,
                    scoped_type="backlog",
                    args=args,
                    term=term,
                )
            else:
                args.path = (
                    args.args[0]
                    if getattr(args, "args", None)
                    else getattr(args, "path", None)
                )
                return backlog_mod.run_set(args)
        if backlog_cmd == "check":
            return backlog_mod.run_check(args)
        return _show_family_help(parser, "backlog", "aw backlog check", term, context)
    if args.command in ("specs", "spec"):
        specs_cmd = getattr(args, "specs_command", None) or getattr(
            args, "spec_command", None
        )
        if specs_cmd == "set":
            if getattr(args, "status", None) is None:
                from agent_workflows import status_set

                return status_set.run_set_command(
                    args.args,
                    scoped_type="specs",
                    args=args,
                    term=term,
                )
            else:
                from agent_workflows import specs as sp

                args.path = (
                    args.args[0]
                    if getattr(args, "args", None)
                    else getattr(args, "path", None)
                )
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
        return _show_family_help(parser, "specs", "aw specs check", term, context)
    if args.command == "archive":
        return _run_archive(args, term)
    if args.command in ("check-local-leaks", "sanitize"):
        return _run_check_local_leaks(args, term)

    if args.command == "ipd-executed-gate":
        from agent_workflows.hooks import executed_transition_gate as _gate

        return _gate.main([])

    if args.command == "ipd-status-untooled-gate":
        from agent_workflows.hooks import status_untooled_gate as _sgate

        return _sgate.main([])

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
