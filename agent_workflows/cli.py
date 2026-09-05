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

# PYTHON_ARGCOMPLETE_OK
# tabcomp Order 02 (4f1j25) E-03: the argcomplete global-completion marker. It MUST be a real `#`
# comment within the first 1024 bytes of the INVOKED script and cannot live inside the docstring
# above (argcomplete scans for a bare comment token). HONEST SCOPE: the `aw`/`agentwf`/
# `agent-workflows` entrypoints are pip/hatchling-generated console-script wrappers (pyproject.toml
# [project.scripts]) that do NOT carry this marker, so `activate-global-python-argcomplete` will not
# auto-discover them from this file. This marker covers the marker-bearing invocation `python -m
# agent_workflows` (and any wrapper that carries it) and the explicit `register-python-argcomplete`
# path; the PRIMARY completion mechanism for the aliases is the child-01 native scripts calling
# `aw __complete` (see completion.complete_query / _run_dunder_complete). argcomplete is an OPTIONAL,
# best-effort enhancement only - there is NO new runtime dependency (see the soft import in `main`).

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

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
    # Machine-only leaf: the shell calls it, a human never does, so its `help` is
    # `argparse.SUPPRESS` and it is absent from `aw --help`. It still needs a description, because
    # `--help` on it must explain what it is to whoever stumbles onto it while debugging completion.
    "__complete": (
        "INTERNAL completion resolver, invoked by the generated shell completion scripts rather than "
        "by a person. Given the current word index and the tokens typed so far, it prints the "
        "candidate completions for that position, one per line, and nothing else. Not a stable "
        "public interface: its arguments and output exist to serve the scripts emitted by "
        "`aw completion` and may change with them."
    ),
    "completion": (
        "Emit a native shell completion script for the aw CLI to stdout. `aw completion bash` "
        "(also zsh, fish) prints a self-contained script that completes commands and flags for all "
        "three entrypoints (aw, agentwf, agent-workflows); with no shell argument it detects the "
        "active shell from $SHELL (falling back to bash). Evaluate it directly, e.g. "
        "`source <(aw completion bash)`. Static generation only; dynamic id/enum completion and "
        "drop-in install arrive in later tabcomp children."
    ),
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
    # runnamecollapse 0soncw E-07: the run surface is split by DIRECTION. `aw run` WRITES,
    # `aw runs` READS, so these help entries follow the leaves to their owning noun.
    "run": (
        "Run ledger transaction verbs (the WRITING half of the run surface): 'start' (take the "
        "single-writer lease and move a runnable step to running), 'record' (append a step attempt "
        "outcome), 'cancel' (record a terminal cancellation), 'finalize' (evaluate the completion "
        "predicate and record terminal completion). To INSPECT a run, use 'aw runs'."
    ),
    "runs": (
        "Inspect driver execution runs and run ledgers (the READING half of the run surface): bare "
        "'aw runs' renders the run table, and the leaves are 'show' (run state and completion "
        "predicates), 'status', 'next', 'resume', 'evidence' (captured provenance envelopes and tool "
        "events), 'verify-ledger' (hash chain integrity and evidence validity), 'decisions', "
        "'questions', and 'list'. Read-only, except the opt-in 'repair' verb."
    ),
    "runs show": (
        "Inspect a workflow run's ledger, steps, verifier decisions, and completion predicate status. "
        "Read-only; makes no writes. Exit 0 complete, 1 incomplete, 2 corrupted or missing."
    ),
    "runs evidence": (
        "List and validate all captured evidence envelopes, tool events, and artifact refs in a run ledger. "
        "Exit 0 all valid, 1 invalid/missing evidence, 2 corrupted or missing."
    ),
    "runs verify-ledger": (
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
    "reviews": (
        "Tooling for the typed plan-review records under .aw/records/reviews. Subcommands "
        "report what a review recorded; the whole namespace is read-only and writes nothing."
    ),
    # hostcap-01 (mjx7ne) E-06: read-only inspection over the probed host capability contract.
    "host": (
        "Inspect what an agent host can actually GUARANTEE, as decided by executed probes "
        "rather than by configuration or version strings. 'host probe <host>' runs the "
        "probes and reports what each one observed; 'host capabilities [host]' prints the "
        "capability contract plus, per action class, whether that action would be allowed or "
        "refused. Read-only with respect to the repository: writes nothing, so there is no "
        "--apply."
    ),
    "host probe": (
        "Execute the host capability probes and report what they OBSERVED, including the "
        "recorded reason for every not-supported verdict. Two runner-safety capabilities "
        "(commit gateway, push denial) are declared but never probed because the enforcement "
        "they name does not exist here yet, so they always read not-supported and any action "
        "requiring them is refused; that is fail-closed, not a host defect. Exit 0 whenever "
        "the probes could run (a not-supported verdict is an ANSWER), 2 cannot-run/usage."
    ),
    "host capabilities": (
        "Print the host capability contract and the per-action verdicts derived from it: for "
        "each of the four action classes, whether this host satisfies its requirements, which "
        "required capabilities are missing, and which spec-required capabilities the contract "
        "cannot yet represent. With no host argument, reports every runner host. Read-only. "
        "Exit 0 whenever it can run, 2 cannot-run/usage."
    ),
    "reviews decisions": (
        "Audit the judgement calls reviewers made on their own authority instead of asking the "
        "maintainer, read from the review record's Decisions section. Use --irreversible for the "
        "ones that cannot be undone. Read-only; exits 0 even when nothing is recorded."
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
    "prompts": (
        "Owner verbs for the operational prompt STAGING tree in .aw/records/prompts/: 'new' mints a "
        "conforming staged prompt into pending/, and 'set' transitions a staged prompt's status. "
        "The prompt's lifecycle is its directory, so a transition moves the file."
    ),
    "prompts new": (
        "Mint a conforming staged prompt under .aw/records/prompts/pending/ (dry-run by default; "
        "--apply to write). Derives the filename (YYYYMMDD-HHMM-NN-<slug>.prompt.md) and writes the "
        "single leading `<!-- aw-prompt: ... -->` metadata comment, and NO body: the prompt body is "
        "yours to author, since any other content would break prompt purity. Never auto-staged."
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
    "backlog-blocking-close-gate": (
        "Local pre-commit gate (bklggrad f1dhht): refuse committing a release-blocking backlog item "
        "closed to '- Status: done' (or moved into done/) without a preserved-or-satisfied gate - the "
        "bypass-catcher for a hand-edit that skips 'aw backlog set done'. Inspects the staged diff and "
        "delegates to the shared 'check_engine.evaluate_blocking_close' predicate (via the commit-scoped "
        "'check.blocking-item-closed-without-gate' rule), reconstructing legitimacy from PERSISTED state "
        "(HANDOFF: a From-Backlog blocking plan; DE-GATED: Blocks-Release cleared), so the hook, setter, "
        "and 'aw check' never diverge. Gates the 'done' case only (park/demote warns are surfaced by "
        "'aw check'/'aw attention'). LOCAL best-effort, OPT-IN only (--no-verify bypasses it; the "
        "portable authority is the 'aw check' rule + CI); commit-scoped (historical done items "
        "grandfathered). Exit 0 = ok/no-op, 1 = refused. Invoked by the repo:local pre-commit hook."
    ),
    "ipd-dependency-statement-gate": (
        "Local pre-commit gate (ipddeps mp88bl): refuse committing a staged IPD whose "
        "'- Item-Dependencies' statement is malformed, dangling, ambiguous, or cyclic - the "
        "bypass-catcher for a hand-edit that skips 'aw ipd dependencies set'. Inspects the staged "
        "diff over a staged-overlay snapshot and delegates to the shared "
        "'check_engine.evaluate_ipd_dependencies' evaluator (the same authority as 'aw check'/'aw ipd "
        "lint'), keeping only findings on staged files so an unrelated commit is never blocked; a "
        "plain draft carrying 'unresolved' stays committable (it blocks only when the staged plan is "
        "advancing to a blocking phase). LOCAL best-effort, OPT-IN only (--no-verify bypasses it; the "
        "portable authority is the 'aw check' rule + CI); commit-scoped. Exit 0 = ok/no-op, 1 = "
        "refused. Invoked by the repo:local pre-commit hook."
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


class _ViewerOrLeafSubParsersAction(argparse._SubParsersAction):
    """Route `aw runs`' first positional either to a LEAF subparser or to the bare VIEWER.

    runnamecollapse 0soncw E-03. `aw runs` must carry BOTH shapes at once:

      * `aw runs <leaf> <target> [leaf flags]` - nine read-only leaves, each with a REQUIRED single
        positional and its own flags (`--workflow`, `--actor`, ...).
      * `aw runs [<target> ...] [viewer flags]` - the bare viewer, `targets nargs="*"` plus twelve
        filter/format flags (`--last`, `--issues`, ...).

    Plain argparse CANNOT express that combination: a parser holding `targets nargs="*"` PLUS
    `add_subparsers()` is accepted at construction but then rejects every non-empty argv, because the
    greedy positional consumes the first token and the subparsers action reports it as an invalid
    choice (measured on CPython 3.14: `["RUN1"]`, `["RUN1","RUN2"]` and `["show","RUN1"]` all exit 2;
    only empty argv parses).

    So the disambiguation is done HERE, explicitly, at the one point that sees the collected
    positionals: if the first token exactly matches a registered leaf name, delegate to that leaf's
    subparser (native help, native usage errors, native flag validation); otherwise hand the whole
    list to the sibling VIEWER parser, which owns `targets` and the viewer flags.

    WHY REAL SUBPARSERS rather than reading `argv[0]` in the handler (the route `aw runs repair`
    takes, see `run_viewer.REPAIR_HELP`): only a real subparser is discoverable by
    `command_surface.discover_parser_leaves`, which enumerates leaves from `_SubParsersAction.choices`
    alone. A positionally-routed leaf is invisible to the normative command surface, so declaring it
    in `COMMAND_INVENTORY` would register as declaration/parser DRIFT and fail
    `tests/test_cli_conformance_matrix.py`. It also gets no argparse help, the documented cost that
    forced the special case at `_dispatch`'s `aw runs repair --help` interception.

    AMBIGUITY RULE, documented because set ids are free-form: a first positional equal to a leaf name
    routes to the LEAF. A Set or run id colliding with a leaf name is therefore reachable only via the
    `--` escape hatch (`aw runs -- status`). No collision exists in the repo today (zero of the
    tracked set ids and run ids match a leaf name), but the rule is explicit and tested. NOTE the
    hatch itself is NOT implemented here: argparse strips `--` while splitting argv, so this action
    cannot tell an escaped token from a leaf name. It is handled pre-parse in `_dispatch`.
    """

    #: Set by `_build_parser` to the sibling parser owning `targets` + the viewer flags.
    viewer_parser: Optional[argparse.ArgumentParser] = None

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        # `values` is a list for this action's `nargs=PARSER`, but normalize defensively: a bare
        # string or None here must not become a list of characters or raise.
        if values is None:
            collected: list = []
        elif isinstance(values, str):
            collected = [values]
        else:
            collected = list(values)
        if collected and collected[0] in self._name_parser_map:
            # A real leaf: let argparse parse the remainder with the leaf's own parser.
            setattr(namespace, "targets", [])
            return super().__call__(parser, namespace, collected, option_string)
        # The bare viewer: no leaf was named, so re-parse the positionals with the viewer parser.
        setattr(namespace, self.dest, None)
        viewer = type(self).viewer_parser
        # pragma: no cover - a wiring bug; fail loud rather than silently drop the targets.
        if viewer is None:
            raise RuntimeError("viewer_parser was never wired for `aw runs`")
        viewer.parse_args(collected, namespace)


class _RunsTargetsPlaceholderAction(argparse.Action):
    """`aw runs`' `targets` positional: documented in help, but never clobbers the routed value.

    The routing action above has `nargs=PARSER`, so it consumes EVERY remaining positional and this
    placeholder is always invoked with an empty list afterwards. Assigning that empty list blindly
    erased the targets the viewer parser had just resolved (measured: `aw runs RUN1` reached the
    viewer with `targets=[]`, i.e. "show all runs", silently ignoring the requested run).

    So this keeps the positional visible in usage/help while writing only when it actually has
    values, or when nothing has populated the dest yet.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        collected = list(values or [])
        if collected or getattr(namespace, self.dest, None) is None:
            setattr(namespace, self.dest, collected)


class _RunsArgumentParser(_AwArgumentParser):
    """`aw runs`' parser: suppresses choice validation for the viewer-or-leaf routing action.

    argparse would otherwise reject a bare run id as an "invalid choice" before
    `_ViewerOrLeafSubParsersAction` ever gets to decide that it is a viewer TARGET, not a leaf name.
    """

    def _check_value(self, action, value):  # type: ignore[override]
        if isinstance(action, _ViewerOrLeafSubParsersAction):
            return
        super()._check_value(action, value)


def _positive_int(value: str) -> int:
    try:
        val = int(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer")
    if val <= 0:
        raise argparse.ArgumentTypeError(f"'{value}' must be a positive integer (> 0)")
    return val


def _add_commit_flags(parser: argparse.ArgumentParser) -> None:
    """selfcommit jgcm68 E-01: register the SHARED ``--commit``/``--no-commit`` arg group on a
    records-mutating parser. ``--commit`` commits the verb's own path-scoped changes without
    prompting (the only way to commit non-interactively); ``--no-commit`` skips the offer entirely.
    With neither, on a TTY the verb prompts, and non-interactively it is a NO-OP (never commits
    silently). One shared registration keeps the UX identical across archive/group/rename/set/
    research set-assign/mv (OQ-01)."""
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        "--commit",
        dest="commit",
        action="store_true",
        help="Commit the change this command made (path-scoped, no push); required to commit "
        "non-interactively.",
    )
    grp.add_argument(
        "--no-commit",
        dest="no_commit",
        action="store_true",
        help="Do NOT offer to commit the change this command made.",
    )


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
    # tabcomp Order 03 (jolfpj) E-04: opt-in shell-completion setup during install. Default `none`
    # keeps a non-interactive/batch install non-destructive toward the user's completion dirs.
    p_install.add_argument(
        "--completion",
        choices=["auto", "bash", "zsh", "fish", "none"],
        default=None,
        help="Also install drop-in shell completion ('auto' detects $SHELL). Default: none "
        "(non-interactively nothing is written; interactively you are asked).",
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
    # tabcomp Order 03 (jolfpj) E-04: same opt-in completion flag on the setup verb.
    p_setup.add_argument(
        "--completion",
        choices=["auto", "bash", "zsh", "fish", "none"],
        default=None,
        help="Also install drop-in shell completion ('auto' detects $SHELL). Default: none "
        "(non-interactively nothing is written; interactively you are asked).",
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
    # awpypi: OPT-IN network probe. Off by default so `aw doctor` stays offline, deterministic,
    # and fast; a failed lookup degrades to "unknown" and never becomes a finding.
    p_doctor.add_argument(
        "--check-pypi",
        action="store_true",
        help="Also check PyPI for a newer published release (network; off by default).",
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
    p_ipd_lint.add_argument(
        "--detail",
        "--long",
        action="store_true",
        dest="detail",
        help="Show detailed diagnostic and advisory findings underneath items.",
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
        "--blocks-release",
        dest="blocks_release",
        default=None,
        help="Set the plan's Blocks-Release gate (a release id6 or 'next'); '-' clears it.",
    )
    p_ipd_set.add_argument(
        "--from-backlog",
        dest="from_backlog",
        default=None,
        help="Link this plan to the backlog item it graduated from (a backlog id6); '-' clears it.",
    )
    p_ipd_set.add_argument(
        "--priority",
        dest="priority",
        default=None,
        choices=["low", "medium", "high", "-"],
        help="Set the plan's Priority (low|medium|high); '-' clears it (xprio). Persists on a no-op "
        "transition.",
    )
    # wkindname ng2blv: the recognized-but-optional `- Work-Kind:` field (the NATURE of the work),
    # mirroring `--priority` above. Named `--work-kind`, not `--kind`, because `Kind` is already the
    # plan's REQUIRED structural field (child|orchestrator). Shared vocab is backlog.KINDS.
    p_ipd_set.add_argument(
        "--work-kind",
        dest="work_kind",
        default=None,
        choices=["bug", "feature", "chore", "security", "followup", "-"],
        help="Set the plan's Work-Kind (bug|feature|chore|security|followup); '-' clears it "
        "(wkindname). Persists on a no-op transition.",
    )
    p_ipd_set.add_argument(
        "--by-human", action="store_true", help="Attest human approval."
    )
    # apprvguard d7bnhc E-06: the ONE named override on the approval gate. It is deliberately NOT
    # implied by --by-human (a human attesting they approved is not a human saying which question
    # they decided to approve over), and it overrides ONLY the blocking-open-question refusal - a
    # negative review verdict has no override at all, by design.
    p_ipd_set.add_argument(
        "--allow-open-questions",
        dest="allow_open_questions",
        action="store_true",
        help="Approve a plan over an unresolved BLOCKING open question, recording the override in "
        "its history. Does NOT override a negative review verdict (that has no override).",
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
    _add_commit_flags(p_ipd_set)  # selfcommit jgcm68 E-01/E-05

    # ipddeps Order g69y23: `aw ipd dependencies set` writes the machine-readable, id6-grounded
    # cross-IPD `Item-Dependencies` field (a DIFFERENT layer from the intra-plan `Depends on:`
    # E-item field). It routes through the SAME hoisted no-op-safe write as `aw ipd set
    # --from-backlog`, so the value persists on a same-status transition.
    p_ipd_deps = ipd_sub.add_parser(
        "dependencies",
        parents=[common],
        help="Manage a plan's cross-IPD Item-Dependencies (e.g. 'aw ipd dependencies set <id6> "
        "executed:<id6> exists:spec:<id6>').",
        description=(
            "Get or set the machine-readable, id6-grounded cross-IPD `Item-Dependencies` statement "
            "of one or more plans. Edges are `none` | `unresolved` | comma/space-separated "
            "`executed:<id6>` | `exists:<type>:<id6>` | `state:<type>:<status>:<id6>` "
            "(type in ipd|spec|backlog; `executed:` targets IPDs; `state:ipd:executed:` is illegal "
            "- use `executed:`). This is a DIFFERENT field from the intra-plan `Depends on:` E-item "
            "ordering. The value is canonicalized and validated before writing and persists on a "
            "same-status no-op transition (mirroring `aw ipd set --from-backlog`)."
        ),
    )
    p_ipd_deps_sub = p_ipd_deps.add_subparsers(dest="ipd_dependencies_command")
    p_ipd_deps_set = p_ipd_deps_sub.add_parser(
        "set",
        parents=[common],
        help="Set/clear a plan's Item-Dependencies (canonicalizes + validates; '-'/'none' clears).",
        description=(
            "Write the cross-IPD `Item-Dependencies` statement of one or more plans, replacing any "
            "existing value. Each edge is `executed:<id6>` (that IPD must be executed), "
            "`exists:<type>:<id6>` (the artifact must exist), or `state:<type>:<status>:<id6>` (the "
            "artifact must hold that status); pass `none` or `-` to clear the statement. Every edge "
            "is canonicalized and validated against the repository before anything is written, so a "
            "malformed, dangling, ambiguous, or cyclic edge is refused rather than persisted, and "
            "the value survives a same-status no-op transition."
        ),
    )
    p_ipd_deps_set.add_argument(
        "selector", help="Plan selector (id6, setid, or filename)."
    )
    p_ipd_deps_set.add_argument(
        "edges",
        nargs="*",
        help="Zero or more edges (space- or comma-separated). Omit, or pass 'none'/'-', to clear.",
    )
    p_ipd_deps_set.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_ipd_deps_set.add_argument(
        "--message", "-m", default=None, help="History record message."
    )
    p_ipd_deps_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_ipd_deps_set.add_argument(
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

    # agentadhere Phase 2 (IPD 8dto0g): atomic workflow primitives that validate-then-act via the
    # phase-1 engine and produce evidence at the action boundary. `aw work begin`, `aw test`,
    # `aw commit`, `aw finish`. Delegates to work_cmd (reusing worktree_lease/git_commit_helper/
    # status_set); no forked worktree/commit/finalize path.
    p_work = sub.add_parser(
        "work",
        parents=[common],
        help="Atomic workflow primitives. 'work begin <ipd>' validates a plan and allocates an isolated worktree.",
        description=(
            "Atomic workflow primitives (agentadhere Phase 2). 'aw work begin <ipd>' validates the "
            "plan via the shared policy engine (fail closed on findings) and allocates an isolated "
            "git worktree with a recorded lease, making the compliant path the easy path."
        ),
    )
    work_sub = p_work.add_subparsers(dest="work_command")
    p_work_begin = work_sub.add_parser(
        "begin",
        parents=[common],
        help="Validate a plan (fail closed) and allocate an isolated worktree for its execution.",
        description=(
            "Start work on one plan the compliant way, in two steps that both have to succeed. First "
            "the plan is validated through the shared policy engine, and any finding refuses the "
            "command rather than warning, so execution cannot begin against a plan that does not "
            "conform. Then an isolated git worktree is allocated with a recorded lease, so the work "
            "happens off the shared checkout and the lease says who holds it. Use this instead of "
            "hand-creating a worktree: it is the same validation the repository gates on later."
        ),
    )
    p_work_begin.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_work_begin.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    p_test = sub.add_parser(
        "test",
        parents=[common],
        help="Run a command and capture tree-bound test evidence for a plan: 'aw test <ipd> -- <cmd>'.",
        description=(
            "Execute a command and capture its stdout/stderr/exit + env metadata (command line, cwd, "
            "timestamp, git HEAD/tree) as an evidence record bound to the current tree/commit under "
            "the plan's local run-record area. The evidence is honestly labeled locally-produced and "
            "forgeable by a privileged local agent; a non-forgeable / CI-reproduced boundary is a "
            "later phase. Exit mirrors the command's own exit."
        ),
    )
    p_test.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_test.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    # dest MUST NOT be `command` (that is the top-level subcommand dest); use `cmd_argv`. Place any
    # options (e.g. --dir) BEFORE the `--` so REMAINDER captures only the command tokens.
    p_test.add_argument(
        "cmd_argv",
        nargs=argparse.REMAINDER,
        help="The test command, after `--` (e.g. `-- pytest tests`).",
    )

    p_commit = sub.add_parser(
        "commit",
        parents=[common],
        help="Commit ONLY a plan's in-scope paths via the shared path-scoped helper: 'aw commit <ipd> -- <paths>'.",
        description=(
            "Compute a plan's allowed scope from its Scope-Paths, refuse when the staged index holds "
            "any out-of-scope change, run the shared policy engine, then commit ONLY the declared "
            "in-scope paths by reusing the path-scoped git_commit_helper (never git add -A/-a, never "
            "--no-verify, never push). Exit 0 committed, 1 refused/nothing, 2 usage."
        ),
    )
    p_commit.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_commit.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_commit.add_argument("--message", "-m", default=None, help="Commit message.")
    p_commit.add_argument(
        "--no-commit",
        dest="no_commit",
        action="store_true",
        help="Preview only; do not commit.",
    )
    # dest is `path_argv` (NOT `command`); place options before the `--`.
    p_commit.add_argument(
        "path_argv",
        nargs=argparse.REMAINDER,
        help="The in-scope paths to commit, after `--`.",
    )

    p_finish = sub.add_parser(
        "finish",
        parents=[common],
        help="Verify bound evidence then perform a non-authoritative plan transition: 'aw finish <ipd> --to <status>'.",
        description=(
            "Verify the plan's required test evidence (from `aw test`) is present and bound to the "
            "current tree, then perform ONLY a valid NON-AUTHORITATIVE status transition via the "
            "tooled `aw set` path. It never performs the authoritative terminal 'executed' transition "
            "(that stays with `aw ipd finalize`), never pushes, and never tags."
        ),
    )
    p_finish.add_argument(
        "plan", help="Plan selector (id6, setid, stem, path, or substring)."
    )
    p_finish.add_argument(
        "--to",
        default=None,
        help="Target non-authoritative status (never executed/done).",
    )
    p_finish.add_argument(
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

    # awoptimize Order 04 E-04: the run ledger CLI. Thin layer over run_evidence/run_ledger_store.
    # OWNERSHIP: Order 04 owns the registration; Order 07 extended it.
    #
    # runnamecollapse 0soncw E-03/E-05: the surface is SPLIT BY DIRECTION across two nouns, per the
    # maintainer's 2026-08-31 ruling. `aw run` WRITES; `aw runs` READS. Both groups are registered
    # from the ONE leaf table below so a leaf cannot drift between its two nouns:
    #
    #   aw run  (writers) : start, record, cancel, finalize
    #   aw runs (readers) : show, status, list, next, resume, decisions, questions, evidence,
    #                       verify-ledger   (`next`/`resume` only reconstruct state and report, so
    #                                        they are viewers despite sounding like actions)
    #
    # `aw run` is deliberately NOT retired: it stays the writing/dispatch noun, which is what the
    # approved `runprofile` Set extends with `aw run as <profile>`.
    p_run = sub.add_parser(
        "run",
        parents=[common],
        help="Run ledger WRITE verbs (start/record/cancel/finalize). Read with `aw runs`.",
        description=(
            "Run ledger transaction verbs: the WRITING half of the run surface. 'start' (take the "
            "single-writer lease and move a runnable step to running), 'record' (append a step "
            "attempt outcome), 'cancel' (record a terminal cancellation), 'finalize' (evaluate the "
            "completion predicate and record terminal completion). To INSPECT a run, use `aw runs` "
            "(show/status/next/resume/evidence/verify-ledger/decisions/questions)."
        ),
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw run start <target> --step S-01      # take the lease and start a runnable step\n"
            "  aw run record <target> --step S-01 --state performed\n"
            "  aw run cancel <target> --reason ...    # record a terminal cancellation\n"
            "  aw run finalize <target>               # complete the run (coordinator authority)\n"
            "\n"
            "READING A RUN LIVES UNDER `aw runs`\n"
            "  aw runs show <target>                  # run state and completion predicates\n"
            "  aw runs status <target>                # reconstructed run + step state\n"
            "  aw runs verify-ledger <target>         # hash chain + evidence validity\n"
        ),
    )
    run_sub = p_run.add_subparsers(dest="run_command")
    #: The nine READ-ONLY leaves that live under `aw runs` (0soncw E-03). Everything else in the leaf
    #: table below stays under `aw run`.
    _RUNS_VIEWER_LEAVES = frozenset(
        {
            "show",
            "status",
            "list",
            "next",
            "resume",
            "decisions",
            "questions",
            "evidence",
            "verify-ledger",
        }
    )
    _run_leaf_specs = (
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
    )

    def _register_run_leaf(group, name: str, help_text: str, desc: str) -> None:
        """Register one run-family leaf on `group` (either the `run` or the `runs` subparsers)."""
        _pr = group.add_parser(name, parents=[common], help=help_text, description=desc)
        _pr.add_argument(
            "target",
            help=(
                "Run ID (run-<hex>) or path to a ledger.jsonl file. NOTE: a run id resolves only to "
                "a ledger.jsonl; the drivers' own events.jsonl is a different format."
            ),
        )
        _pr.add_argument(
            "--dir",
            default=None,
            help="Repo root directory (default: current directory).",
        )
        # The projection inspectors need the workflow name that owns the run-artifacts subdir.
        if name in ("decisions", "questions"):
            _pr.add_argument(
                "--workflow",
                default="exec-set",
                help="Workflow that owns the run-artifacts dir (default: exec-set).",
            )

        if name in (
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
        if name in ("start", "record", "cancel", "finalize"):
            _pr.add_argument(
                "--actor",
                default=None,
                help="Authoring role (runtime/coordinator/executor/verifier/corrector/human).",
            )
        if name in ("start", "record"):
            _pr.add_argument(
                "--step", default=None, help="Step id (S-NN) to start or record."
            )
        if name == "record":
            _pr.add_argument(
                "--state",
                default=None,
                help="Attempt outcome: performed | blocked | failed.",
            )
        if name == "cancel":
            _pr.add_argument(
                "--reason",
                default=None,
                help="Cancellation reason (recorded in the ledger).",
            )

    # runnamecollapse 0soncw E-04: the duplicate `aw run list` registration is DELETED. It rendered
    # the same viewer table as bare `aw runs` through the same renderer, so one job had two names.
    # The viewer's flags now live on the shared `_runs_viewer_flags` parent below, so the bare viewer
    # and the `aw runs list` leaf cannot drift apart the way `run list` and `runs` silently did.

    # runnamecollapse 0soncw E-03: `aw runs` is the READING noun. It carries BOTH the bare viewer
    # (`aw runs [<target> ...]` + filter/format flags) and the nine read-only leaves moved off
    # `aw run`. The viewer's flags live on this shared parent so the bare form and the `aw runs list`
    # leaf are registered from ONE definition and cannot drift apart.
    _runs_viewer_flags = _AwArgumentParser(add_help=False)
    _runs_viewer_flags.add_argument(
        "--dir",
        default=None,
        help="Target Git repository root (default: current directory).",
    )
    _runs_viewer_flags.add_argument(
        "--last",
        "--latest",
        "-l",
        dest="last",
        nargs="?",
        const=1,
        type=_positive_int,
        default=None,
        metavar="N",
        help="Show only the last N runs (default: 1).",
    )
    _runs_viewer_flags.add_argument(
        "--active",
        action="store_true",
        help="Show only runs with active/running steps.",
    )
    _runs_viewer_flags.add_argument(
        "--failed",
        action="store_true",
        help="Show only runs with failed, partial, or blocked steps.",
    )
    _runs_viewer_flags.add_argument(
        "--set",
        help="Filter runs by Set ID.",
    )
    _runs_viewer_flags.add_argument(
        "--ipd",
        "--id6",
        dest="ipd",
        help="Filter runs by IPD id6.",
    )
    _runs_viewer_flags.add_argument(
        "--status",
        help="Filter runs by step status (e.g. executed, partial, blocked, failed).",
    )
    _runs_viewer_flags.add_argument(
        "--since",
        help="Show runs created since date (YYYY-MM-DD), timestamp, or relative timespec (e.g. 1d, 12h, 1.5w, 1m, 1y).",
    )
    _runs_viewer_flags.add_argument(
        "--detail",
        "--long",
        action="store_true",
        dest="detail",
        help="Show detailed incomplete requirements and step summaries.",
    )
    _runs_viewer_flags.add_argument(
        "--short",
        "-s",
        action="store_true",
        dest="short",
        help="Show short table with status, item, action, and verified columns only.",
    )
    _runs_viewer_flags.add_argument(
        "--summary-only",
        "-S",
        action="store_true",
        dest="summary_only",
        help="Show only the aggregate summary breakdown tables (omits individual runs).",
    )
    _runs_viewer_flags.add_argument(
        "--latest-only",
        "-L",
        action="store_true",
        dest="latest_only",
        help="Show only the latest state for each item across matched runs in one table.",
    )
    _runs_viewer_flags.add_argument(
        "--issues",
        "-i",
        action="store_true",
        dest="issues",
        help="Show only the artifact location and status discrepancies table.",
    )

    _RUNS_EPILOG = (
        "EXAMPLES\n"
        "  aw runs                          # summary of all execution runs\n"
        "  aw runs --last                   # summary of the most recent run\n"
        "  aw runs --last 5                 # summary of the last 5 runs\n"
        "  aw runs -l 5                     # summary of the last 5 runs\n"
        "  aw runs -L                       # unified table of latest item states\n"
        "  aw runs --since 1d               # summary of runs in the last day\n"
        "  aw runs <run-id-or-path>         # summary of a specific run\n"
        "  aw runs --set <setid>            # filter runs by Set ID\n"
        "  aw runs --ipd <id6>              # filter runs by IPD id6\n"
        "  aw runs --detail                 # include incomplete items and step summaries\n"
        "  aw runs --short                  # short table without cost/token columns\n"
        "  aw runs --summary-only           # summary breakdown only\n"
        "  aw runs --latest-only            # latest status per item in unified table\n"
        "\n"
        "LEDGER INSPECTION LEAVES (read-only)\n"
        "  aw runs show <target>            # run state, steps, and completion predicates\n"
        "  aw runs status <target>          # reconstructed run + step state\n"
        "  aw runs next <target>            # steps whose dependencies and gates are satisfied\n"
        "  aw runs resume <target>          # resumable steps (refuses on interrupted side effects)\n"
        "  aw runs evidence <target>        # captured evidence envelopes and tool events\n"
        "  aw runs verify-ledger <target>   # hash chain integrity and evidence validity\n"
        "  aw runs decisions <run-id>       # a Set run's recorded autonomous decisions\n"
        "  aw runs questions <run-id>       # a Set run's unresolved deferred questions\n"
        "  aw runs list [<target> ...]      # the viewer table (same as bare `aw runs`)\n"
        "\n"
        "  aw runs repair <run-id>          # MUTATES: reconcile a crashed run's `running` step\n"
        "  aw runs repair --help            # what repair decides, and what it refuses to do\n"
        "\n"
        "WRITING A RUN LIVES UNDER `aw run` (start/record/cancel/finalize)\n"
        "\n"
        "A TARGET NAMED LIKE A LEAF\n"
        "  A first positional equal to a leaf name routes to that LEAF. To view a run or Set whose id\n"
        "  collides with a leaf name, force viewer interpretation with `--`:\n"
        "  aw runs -- status                # `status` is a TARGET here, not the leaf\n"
    )
    _RUNS_DESCRIPTION = (
        "Inspect driver execution runs under .aw/records/runs/ and display a unified "
        "summary of the ending status of each IPD step in each run, and inspect run LEDGERS "
        "(show/status/next/resume/evidence/verify-ledger/decisions/questions). This is the READING "
        "half of the run surface; the writing verbs live under `aw run` "
        "(start/record/cancel/finalize). Read-only, with ONE exception: the `repair` verb "
        "(`aw runs repair <run-id>`) durably reconciles a run abandoned without a terminal status, "
        "so a step a crashed driver left as `running` stops being reported `abandoned?`. "
        "Run `aw runs repair --help` for that verb."
    )

    # The sibling VIEWER parser. It owns `targets` and, via the shared parent, every viewer flag.
    # `_ViewerOrLeafSubParsersAction` delegates to it whenever the first positional is not a leaf
    # name. It is not registered as a subcommand, so it never appears as a parser leaf.
    _p_runs_viewer = _AwArgumentParser(
        prog="aw runs",
        parents=[common, _runs_viewer_flags],
        add_help=False,
        formatter_class=_AlphaHelpFormatter,
        description=_RUNS_DESCRIPTION,
        epilog=_RUNS_EPILOG,
    )
    _p_runs_viewer.add_argument(
        "targets",
        nargs="*",
        default=None,
        help="Zero or more run IDs, directory paths, or set IDs to inspect (default: all runs).",
    )

    # `add_parser` builds the child from the subparsers action's own parser class, so the ONLY way to
    # give `runs` (and only `runs`) the routing-aware parser is to swap that class for this one call.
    # Restored immediately in `finally` so every other command keeps the standard parser.
    _prev_parser_class = sub._parser_class
    try:
        sub._parser_class = _RunsArgumentParser
        p_runs = sub.add_parser(
            "runs",
            parents=[common, _runs_viewer_flags],
            help="Inspect driver execution runs and run ledgers (read-only). Write with `aw run`.",
            description=_RUNS_DESCRIPTION,
            formatter_class=_AlphaHelpFormatter,
            epilog=_RUNS_EPILOG,
        )
    finally:
        sub._parser_class = _prev_parser_class
    # REGISTRATION ORDER IS LOAD-BEARING. The routing action must be registered BEFORE `targets`:
    # argparse consumes positionals in registration order, so a `targets nargs="*"` declared first
    # greedily swallows the leaf name and the action never sees it (measured: `runs show <t>` arrived
    # at the action as `['<t>']`, silently rendering the viewer instead of dispatching `show`).
    _ViewerOrLeafSubParsersAction.viewer_parser = _p_runs_viewer
    runs_sub = p_runs.add_subparsers(
        dest="runs_command",
        action=_ViewerOrLeafSubParsersAction,
        metavar="[<leaf>]",
    )
    p_runs.add_argument(
        "targets",
        nargs="*",
        default=None,
        action=_RunsTargetsPlaceholderAction,
        help="Zero or more run IDs, directory paths, or set IDs to inspect (default: all runs).",
    )
    for _leaf_name, _leaf_help, _leaf_desc in _run_leaf_specs:
        if _leaf_name in _RUNS_VIEWER_LEAVES:
            _register_run_leaf(runs_sub, _leaf_name, _leaf_help, _leaf_desc)
        else:
            _register_run_leaf(run_sub, _leaf_name, _leaf_help, _leaf_desc)
    # `list` is the viewer table under its own name. It takes the viewer's positional/flag shape, not
    # the single-`target` leaf shape, so it is registered directly rather than via _register_run_leaf.
    _p_runs_list = runs_sub.add_parser(
        "list",
        parents=[common, _runs_viewer_flags],
        help="List and summarize driver execution runs and step outcomes (read-only).",
        description=(
            "Inspect driver execution runs under .aw/records/runs/ and summarize the ending status "
            "of each step. Identical to bare `aw runs`."
        ),
    )
    _p_runs_list.add_argument(
        "targets",
        nargs="*",
        default=None,
        help="Zero or more run IDs, directory paths, or set IDs to inspect (default: all runs).",
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
        "--priority",
        dest="priority",
        default=None,
        choices=["low", "medium", "high"],
        help="Optional research Priority (low|medium|high); emits a `priority:` frontmatter line (xprio).",
    )
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
    _add_commit_flags(p_research_setassign)  # selfcommit jgcm68 E-01/E-04

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
    _add_commit_flags(p_research_mv)  # selfcommit jgcm68 E-01/E-04

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
        description=(
            "List the research prompts that have been written but never answered. A prompt counts as "
            "unrun when its set's `NN=00` prompt file has no report sibling, which is a structural "
            "test rather than a status field, so a prompt cannot look answered merely because someone "
            "edited its metadata. Use it to find research you asked for and never got back before "
            "starting new work that depends on the answer."
        ),
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
        description=(
            "Record what a piece of research was actually WORTH, and which work consumed it. The "
            "outcome is one of `adopted`, `informational`, `rejected`, or `none-yet`, and "
            "`--consumed-by` names the plan, spec, or backlog id6s that used it (`-` clears the "
            "list). This is the provenance link that lets a later reader tell research that changed a "
            "decision from research nobody read. Previews by default; pass `--apply` to write."
        ),
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

    p_research_set_priority = research_sub.add_parser(
        "set-priority",
        parents=[common],
        help="Set/clear a research doc's optional Priority (preview unless --apply); xprio.",
        description=(
            "Set or clear a research document's optional `Priority` field, using the same "
            "`low|medium|high` vocabulary that plans, specs, and backlog items use, so one word means "
            "the same thing across every artifact type. Pass `-` to clear it, which is different from "
            "setting `low`: cleared means nobody has judged the priority. Previews by default; pass "
            "`--apply` to write."
        ),
    )
    p_research_set_priority.add_argument("id", help="The <id6> of the doc.")
    p_research_set_priority.add_argument(
        "--to",
        default=None,
        choices=["low", "medium", "high", "-"],
        help="Set the priority value (low|medium|high); '-' clears it.",
    )
    p_research_set_priority.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_research_set_priority.add_argument(
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

    # revgate Order 04 (c621h9 E-04): the `reviews` namespace. Read-only reporting over the typed
    # review records; this verb brings the noun into existence.
    p_reviews = sub.add_parser(
        "reviews",
        parents=[common],
        help="Typed plan-review record tooling. 'reviews decisions' audits what agents decided without asking.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw reviews decisions                 # every recorded self-resolved decision\n"
            "  aw reviews decisions --irreversible  # only the ones that cannot be undone\n"
            "  aw reviews decisions c621h9          # one reviewed plan (matched by filename)\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Read-only: this namespace writes nothing, so there is no --apply.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 always when it can run (an empty audit trail is a valid answer),\n"
            "  2 cannot-run/usage error. There is no exit 1: reporting is not judging.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
    )
    reviews_sub = p_reviews.add_subparsers(dest="reviews_command")
    p_reviews_decisions = reviews_sub.add_parser(
        "decisions",
        parents=[common],
        help="Print the judgement calls reviewers made on their own authority instead of asking.",
    )
    p_reviews_decisions.add_argument(
        "selector",
        nargs="?",
        default=None,
        help="Optional review/plan selector (path, or a filename match embedding the plan id6/set id).",
    )
    p_reviews_decisions.add_argument(
        "--irreversible",
        action="store_true",
        help="Show only decisions marked 'Reversible: no' (the ones that cannot be undone).",
    )
    p_reviews_decisions.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # hostcap-01 (mjx7ne) E-06: the `host` namespace. Read-only inspection over the PROBED
    # capability contract in `host_sandbox_profile`; this verb brings the noun into existence.
    p_host = sub.add_parser(
        "host",
        parents=[common],
        help="Inspect what an agent host can actually guarantee (executed probes, not config).",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw host capabilities                 # every runner host's contract + action verdicts\n"
            "  aw host capabilities opencode        # one host\n"
            "  aw host probe opencode               # run the probes and report what they observed\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Read-only with respect to the repository: writes nothing, so there is no --apply.\n"
            "  'probe' does EXECUTE probes (the sandbox probe builds and removes a temporary\n"
            "  jail), so it is repository-read-only rather than side-effect-free.\n"
            "  Two runner-safety capabilities (commit gateway, push denial) are declared but\n"
            "  never probed, because the enforcement they name does not exist here yet. They\n"
            "  always read not-supported, so actions requiring them are refused: fail-closed.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 whenever the report could be produced (a not-supported verdict is\n"
            "  an ANSWER, not a failure), 2 cannot-run/usage error. There is no exit 1.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
    )
    host_sub = p_host.add_subparsers(dest="host_command")
    p_host_probe = host_sub.add_parser(
        "probe",
        parents=[common],
        help="Execute the host capability probes and report what each one observed.",
    )
    p_host_probe.add_argument(
        "host",
        nargs="?",
        default=None,
        help="Host to probe (default: opencode).",
    )
    p_host_capabilities = host_sub.add_parser(
        "capabilities",
        parents=[common],
        help="Print the capability contract and the per-action allowed/refused verdicts.",
    )
    p_host_capabilities.add_argument(
        "host",
        nargs="?",
        default=None,
        help="Host to report on (default: every runner host).",
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
        aliases=["conf"],
        parents=[common],
        help="Manage user CLI config (show, get, set, add, remove, is, and exclude list).",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw config show               # display config file and current settings\n"
            "  aw config show repos         # inspect a whole settings group\n"
            "  aw config show repos.search  # inspect a specific variable\n"
            "  aw config get defaults.backup # get specific variable\n"
            "  aw config set defaults.backup to false  # set specific variable\n"
            "  aw config set repos.search ~/src,~/work # set list variable\n"
            "  aw config add ~/src to repos.search     # add item to list variable\n"
            "  aw config remove ~/src from repos.search # remove item from list variable\n"
            "  aw config is ~/src in repos.search      # check membership in list variable\n"
            "  aw config exclude list       # list never-install exclude entries\n"
            "  aw config exclude add ~/src/legacy  # add path to exclude list\n"
            "  aw config exclude rm ~/src/legacy   # remove path from exclude list\n"
            "  aw conf show                 # shorthand alias\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 success, 1 not found, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
    )
    config_sub = p_config.add_subparsers(dest="config_command")

    p_config_show = config_sub.add_parser(
        "show",
        parents=[common],
        help="Display the configuration file location, status, and all current settings (or a single variable).",
        description=(
            "Show where the user configuration file lives, whether it exists, and what it currently "
            "contains. With no argument every setting is printed; pass a name to narrow to one group "
            "(`repos`) or one variable (`repos.search`). This is the read-only orientation command: it "
            "answers 'what is configured right now, and which file would a change land in' without "
            "modifying anything."
        ),
    )
    p_config_show.add_argument(
        "varname",
        nargs="?",
        default=None,
        help="Optional variable name to inspect (e.g. 'repos', 'repos.search', 'defaults.backup').",
    )

    p_config_get = config_sub.add_parser(
        "get",
        parents=[common],
        help="Get the value of a configuration variable (e.g. 'defaults.backup', 'repos').",
        description=(
            "Print the value of exactly one configuration variable, resolved the same way the rest of "
            "the toolkit resolves it. Unlike `config show`, the output is the value alone, which makes "
            "it usable in a script or a shell substitution. Exits nonzero when the variable is not "
            "set, so a caller can distinguish 'unset' from 'set to an empty value'."
        ),
    )
    p_config_get.add_argument(
        "varname",
        help="Variable name to read (e.g. 'defaults.backup', 'repos.search', 'aw_home').",
    )

    p_config_set = config_sub.add_parser(
        "set",
        parents=[common],
        help="Set the value of a configuration variable (syntax: 'var val', 'var=val', 'var = val', 'var to val').",
        description=(
            "Write a configuration variable, REPLACING whatever it held before. Several spellings are "
            "accepted for the same operation (`var val`, `var=val`, `var = val`, `var to val`) so the "
            "command reads naturally either way. For a list-valued variable this replaces the entire "
            "list; use `config add` or `config remove` to change one entry without disturbing the rest."
        ),
    )
    p_config_set.add_argument(
        "set_args",
        nargs="+",
        help="Variable name and value (e.g. 'defaults.backup false', 'repos.search to ~/src,~/work').",
    )

    p_config_add = config_sub.add_parser(
        "add",
        parents=[common],
        help="Add an item to a list configuration variable (syntax: 'aw config add <value> to <varname>').",
        description=(
            "Append one item to a list-valued configuration variable, leaving the existing entries "
            "alone. This is the difference from `config set`, which replaces the whole list: use `add` "
            "when you mean 'also this'. Adding an item the list already contains is a no-op rather "
            "than a duplicate or an error."
        ),
    )
    p_config_add.add_argument(
        "add_args",
        nargs="+",
        help="Item value and variable name (e.g. '~/src to repos.search', '~/src repos.search').",
    )

    p_config_remove = config_sub.add_parser(
        "remove",
        aliases=["rm"],
        parents=[common],
        help="Remove an item from a list configuration variable (syntax: 'aw config remove <value> from <varname>').",
        description=(
            "Delete one item from a list-valued configuration variable, leaving every other entry in "
            "place. The counterpart to `config add`, and the safe alternative to rewriting the whole "
            "list with `config set`. Removing an item that is not present is reported rather than "
            "silently treated as success, so a typo in the value does not look like it worked."
        ),
    )
    p_config_remove.add_argument(
        "remove_args",
        nargs="+",
        help="Item value and variable name (e.g. '~/src from repos.search', '~/src repos.search').",
    )

    p_config_is = config_sub.add_parser(
        "is",
        parents=[common],
        help="Check if an item is present in a list configuration variable (syntax: 'aw config is <value> in <varname>').",
        description=(
            "Test whether one item is a member of a list-valued configuration variable, and report the "
            "answer through the EXIT CODE so it can be used directly in a shell conditional. Nothing "
            "is modified. Prefer this over grepping `config show`, which would also match a "
            "coincidental substring of an unrelated entry."
        ),
    )
    p_config_is.add_argument(
        "is_args",
        nargs="+",
        help="Item value and variable name (e.g. '~/src in repos.search', '~/src repos.search').",
    )

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
        if _verb in ("search", "find", "check"):
            _p.add_argument(
                "type",
                nargs="?",
                default=None,
                help=(
                    "Artifact type (plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms, releases) or 'all' (default: all)."
                    if _verb == "check"
                    else "Artifact type (plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms, releases) or 'all' (optional)."
                ),
            )
            _p.add_argument(
                "selector",
                nargs="*",
                help="Selector/sub-check for the verb ('names', id6, ...)."
                if _verb == "check"
                else "Selector / search pattern / args for the verb.",
            )
        if _verb in ("search", "find"):
            _p.add_argument(
                "-p",
                "--paths",
                action="store_true",
                help="Output bare matching repo-relative file paths only (one per line, token-efficient).",
            )
        if _verb == "find":
            # Traversal guard escape hatches. By default `.git/`, `runs/`, `tmp/`, `temp/`,
            # `scratch/`, `.system_generated/` and `__pycache__/` are never descended into.
            _p.add_argument(
                "--include-ignored",
                action="store_true",
                help="Also search normally-skipped directories (.git, runs, tmp, temp, scratch, .system_generated, __pycache__). Slower.",
            )
            _p.add_argument(
                "--max-depth",
                type=int,
                default=None,
                metavar="N",
                help="Limit search to N directory levels below each record root (0 = the root itself).",
            )
        elif _verb != "check":
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
            _p.add_argument(
                "--files-with-matches",
                "--files-only",
                "--files",
                "--filenames",
                "-l",
                dest="files_only",
                action="store_true",
                help="Only print filenames of matching files (like grep -l).",
            )
            _p.add_argument(
                "--short",
                "-s",
                dest="short",
                action="store_true",
                help="Print matching files with type and status in attention format (- [type] path (status)).",
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
        _p.add_argument(
            "--to-id6",
            dest="to_id6",
            action="store_true",
            help="rename: id6-minting conversion - convert a legacy timestamp name "
            "(YYYYMMDD-HHMM-NN-<slug>.<type>.md) to the uniform id6-clustered form "
            "(YYYYMMDD-<id6>-01-<id6>-<slug>.<type>.md), minting an id6 and injecting it as "
            "'- Id:' (reuses an existing '- Id:', never re-mints).",
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
        if _verb in ("rename", "group"):
            # selfcommit jgcm68 E-01: offer to commit the rename/group's own path-scoped changes.
            _add_commit_flags(_p)
        if _verb == "check":
            _p.add_argument(
                "-a",
                "--all",
                action="store_true",
                help="Include retired, archived, and terminal artifacts (executed/superseded/parked/done/shipped).",
            )
            _p.formatter_class = _AlphaHelpFormatter
            _p.epilog = (
                "AVAILABLE TYPES\n"
                "  plans         Implementation Plan Documents (.ipd.md) under pending/ and reusable/\n"
                "  specs         Technical specification documents (.spec.md)\n"
                "  backlog       Committed/uncommitted backlog items (.backlog.md)\n"
                "  research      Research reports, prompts, summaries, reconciliations\n"
                "  prompts       System and research prompt records\n"
                "  walkthroughs  Narrative walkthroughs (.walkthrough.md)\n"
                "  roadmaps      Project roadmaps (.roadmap.md)\n"
                "  comms         Inter-agent communication inbox/records\n"
                "  releases      Release definition records (.release.md)\n"
                "  all           All supported record types across the repository (default)\n"
                "\n"
                "RESERVED SUB-CHECKS & OPTIONS\n"
                "  names         Check filename grammar and clustering conformity only\n"
                "  -a, --all     Include retired, archived, and terminal artifacts (executed/superseded/parked/done/shipped)\n"
                "  --agent       Emit machine-readable JSONL (aw.agent/v1)\n"
                "  --json        Emit full structured JSON representation\n"
                "\n"
                "EXAMPLES\n"
                "  aw check                     # validate all active/in-play artifacts across all types\n"
                "  aw check plans               # validate active plan artifacts (pending and reusable)\n"
                "  aw check specs               # validate active spec contracts\n"
                "  aw check backlog             # validate active backlog items (open, graduated, blocked)\n"
                "  aw check research            # validate active research artifacts\n"
                "  aw check all                 # validate every active records tree with cross-tree collisions\n"
                "  aw check plans names         # check plan filename grammar only\n"
                "  aw check specs names         # check spec filename grammar only\n"
                "  aw check --all               # include retired/archived/executed artifacts in the check\n"
                "  aw check plans --all         # validate all plans including executed, superseded, and archived\n"
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
    # apprvguard d7bnhc E-06: same named override as `aw ipd set`, declared on every surface that
    # reaches the approval path so the gate is not bypassable by choosing a different spelling.
    p_set.add_argument(
        "--allow-open-questions",
        dest="allow_open_questions",
        action="store_true",
        help="Approve an artifact over an unresolved BLOCKING open question, recording the override "
        "in its history. Does NOT override a negative review verdict (that has no override).",
    )
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
    # selfcommit jgcm68 E-01: `aw set` (and every family routing through it) offers to commit its
    # own path-scoped metadata rewrite. The subcommand `set` parsers (ipd/spec/prompts/backlog) that
    # also route through status_set register the flags on their own parsers below.
    _add_commit_flags(p_set)

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
    p_attention.add_argument(
        "--details",
        "-d",
        dest="details",
        action="store_true",
        help="Show summary, scope, or description details beneath each item.",
    )
    p_attention.add_argument(
        "--type",
        "-t",
        "--tree",
        dest="types",
        action="append",
        default=[],
        help="Filter by artifact type (plans/specs/backlog/research/releases/roadmaps/walkthroughs). Supports multiple flags or comma-separated lists (e.g. -t plans,specs or -t plans -t specs).",
    )
    p_attention.add_argument(
        "--status",
        "-s",
        dest="status",
        action="append",
        default=[],
        help="Filter by artifact status (e.g. to-review, draft, open, approved). Supports multiple flags or comma-separated lists (e.g. --status to-review,draft or --status to-review --status draft).",
    )
    p_attention.add_argument(
        "--priority",
        "-p",
        dest="priority",
        action="append",
        default=[],
        help="Filter by priority (e.g. high, medium, low, -). Supports multiple flags or comma-separated lists (e.g. --priority high,medium or --priority high --priority medium).",
    )
    p_attention.add_argument(
        "--blocking",
        "-b",
        dest="blocking",
        action="append",
        default=[],
        help="Filter by release-blocking status or release version (e.g. 2.0.0, next, -, true, false). Supports multiple flags or comma-separated lists (e.g. --blocking 2.0.0,-).",
    )
    p_attention.add_argument(
        "--readiness",
        "-r",
        dest="readiness",
        action="append",
        default=[],
        help="Filter by readiness (e.g. go-pending-approval, -). Supports multiple flags or comma-separated lists.",
    )
    p_attention.add_argument(
        "--open-questions",
        "--oqs",
        dest="open_questions",
        action="store_true",
        default=False,
        help="Filter to show only artifacts with unresolved open questions.",
    )
    p_attention.add_argument(
        "selectors",
        nargs="*",
        default=[],
        help="Optional selector tokens (id6, setid, path, filename, tree, or status) to filter items.",
    )

    # awocrunner Order 02 (nfo184): the `oc` (alias `opencode`) host group surfaces the packaged
    # OpenCode IPD runner as `aw oc runipd`. `runipd` captures ALL remaining tokens verbatim
    # (argparse.REMAINDER) and forwards the raw argv to `agent_workflows.oc_runipd.main(...)`
    # unchanged, so the runner's own parser (including its implicit-`start` shim and `--help`) drives
    # behavior with exact parity - re-declaring its flags here would drift and drop the implicit-start
    # shim that lives in main(), not build_parser().
    p_oc = sub.add_parser(
        "oc",
        aliases=["opencode"],
        parents=[common],
        help="OpenCode host tooling. 'aw oc runipd' runs the restartable IPD review/execute driver; 'aw oc update-models' syncs provider models/pricing from your configured gateways. Alias: 'aw opencode'.",
        description=(
            "Everything specific to the OpenCode host, grouped under one noun. `aw oc runipd` (alias "
            "`aw oc run`) is the restartable driver that reviews or executes IPDs in a durable queue, "
            "and `aw oc update-models` refreshes model and pricing data from the gateways declared in "
            "your own OpenCode config. Spelled `aw opencode` if you prefer the long form; the two are "
            "the same commands."
        ),
    )
    oc_sub = p_oc.add_subparsers(dest="oc_command")
    p_oc_runipd = oc_sub.add_parser(
        "runipd",
        aliases=["run"],
        help="Restartable non-interactive OpenCode driver for reviewing/executing IPDs.",
        add_help=False,
        description=(
            "Run the OpenCode IPD driver. It freezes a queue from your selector, then reviews or "
            "executes each item in order, committing as it goes and recording durable run state so an "
            "interrupted run can be resumed rather than restarted. ALL arguments after `runipd` are "
            "forwarded verbatim to the driver, so consult `aw oc runipd --help` for the real flag set: "
            "this wrapper deliberately declares none of them, which is what keeps the two in step."
        ),
    )
    p_oc_runipd.add_argument(
        "runipd_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the runipd driver (start/resume/status/report ...).",
    )
    # ocsync Order 01 (g7hljt): `aw oc update-models` refreshes each OpenAI-compatible provider's
    # models/pricing from the gateway declared in the user's OWN OpenCode config (no hardcoded host).
    # Unlike `runipd` this verb has STRUCTURED flags, so it is declared here and dispatched from the
    # parsed namespace rather than forwarded as argparse.REMAINDER.
    p_oc_models = oc_sub.add_parser(
        "update-models",
        aliases=["sync-models"],
        parents=[common],
        help="Sync provider models + pricing from the gateways in your OpenCode config (preview unless --apply).",
        description=(
            "Refresh OpenCode provider model lists and pricing from the gateways declared in your "
            "own OpenCode config. Previews by default; pass --apply to write. Pricing is read from "
            "a provider's LiteLLM endpoints (/model/info, /model_group/info) and converted to $ per "
            "million tokens; providers without a pricing endpoint (plain OpenAI, Google) are "
            "reported as skipped and left untouched. --apply rewrites the file with normalized JSON "
            "formatting: the existing indent width is detected and reused, but byte-for-byte "
            "formatting is not preserved. Credentials are sent over https only and are never printed."
        ),
    )
    p_oc_models.add_argument(
        "--config",
        help="Path to opencode.json (default: the config OpenCode itself would load).",
    )
    p_oc_models.add_argument(
        "--apply",
        action="store_true",
        help="Write the changes (default: preview only).",
    )
    p_oc_models.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit synonym for the default preview behavior.",
    )
    p_oc_models.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not write a timestamped .bak beside the config before applying.",
    )
    p_oc_models.add_argument(
        "--allow-insecure",
        action="store_true",
        help="Permit a non-https baseURL, and only for a loopback host.",
    )

    p_agy = sub.add_parser(
        "agy",
        aliases=["antigravity"],
        parents=[common],
        help="Antigravity host tooling. 'aw agy runipd' runs the restartable IPD review/execute driver. Alias: 'aw antigravity'.",
        description=(
            "Everything specific to the Antigravity host, grouped under one noun. `aw agy runipd` "
            "(aliases `run`, `runagy`) is the restartable multi-IPD queue driver; `aw agy exec` runs a "
            "SINGLE target with the two-turn skeptical audit and is deliberately a separate verb; "
            "`aw agy sessions` and `aw agy view` inspect sessions and event logs. Spelled "
            "`aw antigravity` if you prefer the long form."
        ),
    )
    agy_sub = p_agy.add_subparsers(dest="agy_command")
    p_agy_runipd = agy_sub.add_parser(
        "runipd",
        aliases=["run", "runagy"],
        help="Restartable non-interactive Antigravity driver for reviewing/executing IPDs.",
        add_help=False,
        description=(
            "Run the Antigravity IPD driver. It freezes a queue from your selector, then reviews or "
            "executes each item in order, committing as it goes and recording durable run state so an "
            "interrupted run can be resumed rather than restarted. ALL arguments after `runipd` are "
            "forwarded verbatim to the driver, so consult `aw agy runipd --help` for the real flag "
            "set: this wrapper deliberately declares none of them, which is what keeps the two in step."
        ),
    )
    p_agy_runipd.add_argument(
        "runipd_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the runagy driver (start/resume/status/report ...).",
    )
    # runnernorm Order 02 (puot79): graduate the remaining Antigravity source-checkout tools
    # under the same packaged-core + host-subcommand pattern. Each captures REMAINDER verbatim and
    # forwards to its packaged core's main(), so the tool's own parser (incl. --help) drives behavior
    # with exact parity. NOTE: `run`/`runagy` above already alias `runipd`; `sessions`/`view` are new
    # non-colliding surfaces (agy_run.py's disposition is tracked separately under OQ-02).
    p_agy_sessions = agy_sub.add_parser(
        "sessions",
        help="List and inspect Antigravity sessions for a workspace/directory.",
        add_help=False,
        description=(
            "List the Antigravity conversation sessions recorded for a workspace, so you can find the "
            "session id a run attached to and inspect what it did. Read-only. ALL arguments are "
            "forwarded verbatim to the underlying tool, so see its own `--help` for the flag set."
        ),
    )
    p_agy_sessions.add_argument(
        "sessions_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the agy sessions tool.",
    )
    p_agy_view = agy_sub.add_parser(
        "view",
        aliases=["view-antigravity-jsonl"],
        help="Format Antigravity JSONL event logs as readable terminal text.",
        add_help=False,
        description=(
            "Render an Antigravity JSONL event log as readable terminal text, turning the raw "
            "machine stream a run leaves behind into something a human can follow. Read-only. ALL "
            "arguments are forwarded verbatim to the underlying tool, so see its own `--help`."
        ),
    )
    p_agy_view.add_argument(
        "view_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the agy view tool.",
    )
    # runnernorm follow-up (puot79e04): graduate tools/agy_run.py (single-target multi-mode
    # runner + two-turn skeptical protocol) under the NON-colliding `aw agy exec` surface. It is
    # genuinely distinct from the multi-IPD queue driver that `run`/`runagy`/`runipd` alias, so it
    # must NOT reuse `aw agy run`. Captures REMAINDER verbatim and forwards to the packaged core's
    # main(), so the runner's own parser (incl. --help) drives behavior with exact parity.
    p_agy_exec = agy_sub.add_parser(
        "exec",
        help="Execute an IPD/spec/prompt-file/prompt with Antigravity + two-turn skeptical audit.",
        add_help=False,
        description=(
            "Execute ONE target (an IPD, a spec, a prompt file, or an inline prompt) with Antigravity, "
            "using the two-turn protocol where a second clean session skeptically audits the first "
            "session's work. This is deliberately NOT `aw agy run`: that name belongs to the multi-IPD "
            "queue driver, and conflating a single-target run with a queue run is exactly the "
            "collision this separate verb avoids. ALL arguments are forwarded verbatim; see its own "
            "`--help`."
        ),
    )
    p_agy_exec.add_argument(
        "exec_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the agy exec runner.",
    )

    # runnernorm Order 02 (puot79): top-level `aw pwatch` graduates tools/pwatch.py.
    p_pwatch = sub.add_parser(
        "pwatch",
        parents=[common],
        help="Watch and summarize processes (graduated from tools/pwatch.py).",
        description=(
            "Watch running processes and summarize them, with include/exclude matching so a long-lived "
            "agent run can be monitored without the noise of every unrelated process on the machine. "
            "Read-only: it observes and reports, and never signals or kills anything. ALL arguments "
            "are forwarded verbatim to the packaged core, so see its own `--help` for the flag set."
        ),
        add_help=False,
    )
    p_pwatch.add_argument(
        "pwatch_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the packaged pwatch core.",
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
    # wkindname Order 01 (9trlc3) E-02 / OQ-01: `--work-kind` is the PREFERRED spelling, matching the
    # on-disk `- Work-Kind:` field; `--kind` is KEPT as an accepted alias so no existing caller breaks.
    # Neither carries an argparse default: the "chore" fallback lives in `backlog.run_new`, because a
    # default here would make `--kind` indistinguishable from "not passed" and mask `--work-kind`.
    p_backlog_new.add_argument(
        "--work-kind",
        dest="work_kind",
        default=None,
        help="bug | feature | chore | security | followup (default: chore).",
    )
    p_backlog_new.add_argument(
        "--kind",
        dest="kind",
        default=None,
        help="Alias of --work-kind (accepted for compatibility).",
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
    p_backlog_new.add_argument(
        "--blocks-release",
        dest="blocks_release",
        default=None,
        help="Declare this item gates a release: a release id6, 'next', or '-' to omit.",
    )
    p_backlog_new.add_argument(
        "--message",
        default="",
        help="Custom note for the workflow history creation entry (default: summary).",
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
        "--evidence",
        dest="evidence",
        default=None,
        help=(
            "Resolvable in-tree artifact path satisfying a release gate, so a blocking item may "
            "close 'done' (SATISFIED path). Alternatives: hand the gate to a From-Backlog plan, or "
            "clear it with '--blocks-release -'."
        ),
    )
    p_backlog_set.add_argument(
        "--dry-run", action="store_true", help="Preview without writing."
    )
    p_backlog_set.add_argument(
        "--yes", "-y", action="store_true", help="Confirm mutation without prompting."
    )
    _add_commit_flags(p_backlog_set)  # selfcommit jgcm68 E-01/E-05

    p_backlog_check = backlog_sub.add_parser(
        "check",
        parents=[common],
        description="Validate the backlog tree against the contract; fail closed.",
        help="Check backlog items conform (valid status/gate/id/summary); exit nonzero on any violation.",
    )
    p_backlog_check.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )

    # IPD w0ln4q: the releases owner verb, bringing `.aw/records/releases/` to parity with the other
    # record classes. Subcommands are DELIBERATELY list/show/new only - there is no `releases check`,
    # because `aw check releases` is the canonical validator (check_engine -> validate_release) and a
    # second entry point could drift from it.
    p_releases = sub.add_parser(
        "releases",
        aliases=["release"],
        parents=[common],
        help="Owner verbs for release records (ship-gate anchors). 'list' shows every release; 'show' details one plus its blockers; 'new' scaffolds one.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw releases                  # list every release record (default)\n"
            "  aw releases show next        # the planned release + everything gating it\n"
            '  aw releases new --version 2.1.0 --summary "why" --apply\n'
            "\n"
            "SAFETY & DEFAULTS\n"
            "  'new' is dry-run by default; pass --apply to write.\n"
            "  Bare 'aw releases' lists; 'show' defaults to the 'next' (single planned) release.\n"
            "  Validation lives in 'aw check releases' - there is no 'releases check'.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean, 2 cannot-run/usage error (e.g. an unresolvable selector).\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
        description=(
            "Owner verbs for the release records in .aw/records/releases/ (the ship-gate anchors that "
            "'Blocks-Release: <id6|next>' resolves against): 'list' tabulates every release record, "
            "'show' details one release plus the LIVE items gating it (the same blocker set 'aw "
            "attention' reports), and 'new' scaffolds a conformant record (preview by default). "
            "Validate release records with 'aw check releases'."
        ),
    )
    # Unlike the other record families (whose bare form prints help), a bare `aw releases` IS a real
    # leaf that lists, so `--dir` must be accepted BEFORE the subcommand too. The subparsers therefore
    # default their own `--dir` to argparse.SUPPRESS: absent means "leave the parent's value alone",
    # so `aw releases --dir X` and `aw releases list --dir X` both resolve the same repo root.
    p_releases.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    releases_sub = p_releases.add_subparsers(dest="releases_command")
    p_releases_list = releases_sub.add_parser(
        "list",
        parents=[common],
        description="List every release record (id6, status, version, summary). Read-only.",
        help="List every release record (the default for a bare 'aw releases').",
    )
    p_releases_list.add_argument(
        "--dir",
        default=argparse.SUPPRESS,
        help="Repo root (default: current directory).",
    )
    p_releases_show = releases_sub.add_parser(
        "show",
        parents=[common],
        description=(
            "Show one release record in full plus every LIVE item declaring it a blocker. The "
            "selector accepts a release id6, a version string, a filename, or 'next' (the single "
            "planned release); it defaults to 'next'. Read-only."
        ),
        help="Show one release + its release-blockers (selector defaults to 'next').",
    )
    p_releases_show.add_argument(
        "selector",
        nargs="?",
        default=None,
        help="Release id6, version, filename, or 'next' (default: next).",
    )
    p_releases_show.add_argument(
        "--dir",
        default=argparse.SUPPRESS,
        help="Repo root (default: current directory).",
    )
    p_releases_new = releases_sub.add_parser(
        "new",
        parents=[common],
        description="Create a conformant release record (dry-run by default; --apply to write).",
        help="Create a release record (dry-run by default; --apply to write).",
    )
    p_releases_new.add_argument(
        "--dir",
        default=argparse.SUPPRESS,
        help="Repo root (default: current directory).",
    )
    p_releases_new.add_argument(
        "--version", default=None, help="Release version, e.g. 2.1.0 (required)."
    )
    p_releases_new.add_argument(
        "--summary",
        default=None,
        help="One-line summary of what this release is for (required).",
    )
    p_releases_new.add_argument(
        "--status",
        default="planned",
        help="planned | blocked | shipped (default: planned).",
    )
    p_releases_new.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
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
    p_specs_new = specs_sub.add_parser(
        "new",
        aliases=["scaffold"],
        parents=[common],
        description=(
            "Create a forward-conforming, id6-clustered spec (dry-run by default; --apply to write). "
            "Mints a fresh id6 and writes it into both the filename "
            "(YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md) and the `- Id:` metadata."
        ),
        help="Create an id6-clustered spec (dry-run by default; --apply to write).",
    )
    p_specs_new.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_specs_new.add_argument(
        "--title", default=None, help="Spec title (required; used in the H1 heading)."
    )
    p_specs_new.add_argument(
        "--slug",
        default=None,
        help="Short descriptive kebab slug (default: derived from --title).",
    )
    p_specs_new.add_argument(
        "--summary", default=None, help="Optional one-line scope/summary."
    )
    p_specs_new.add_argument(
        "--date", default=None, help="Override the authored date (YYYY-MM-DD)."
    )
    p_specs_new.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
    )

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
        "--priority",
        dest="priority",
        default=None,
        choices=["low", "medium", "high", "-"],
        help="Set the spec's Priority (low|medium|high); '-' clears it (xprio). Written as a "
        "side-effect of the status transition; an out-of-vocab value is refused.",
    )
    # wkindname ng2blv: the same recognized-but-optional Work-Kind field on a spec, mirroring
    # `--priority` above. A spec will mostly use `feature` or `chore`; the vocabulary is shared with
    # backlog and plans by design (OQ-01) rather than forked per type.
    p_specs_set.add_argument(
        "--work-kind",
        dest="work_kind",
        default=None,
        choices=["bug", "feature", "chore", "security", "followup", "-"],
        help="Set the spec's Work-Kind (bug|feature|chore|security|followup); '-' clears it "
        "(wkindname). Written as a side-effect of the status transition; an out-of-vocab value "
        "is refused.",
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
    # apprvguard d7bnhc E-07: `aw specs set --status approved <path>` routes to the FORKED
    # `specs.run_set`, not through status_set, so the override must exist on this surface too or the
    # spelling itself would be the bypass.
    p_specs_set.add_argument(
        "--allow-open-questions",
        dest="allow_open_questions",
        action="store_true",
        help="Approve a spec over an unresolved BLOCKING open question, recording the override in "
        "its history. Does NOT override a negative review verdict (that has no override).",
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
    _add_commit_flags(p_specs_set)  # selfcommit jgcm68 E-01/E-05/E-06 (dual path)

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

    p_prompts = sub.add_parser(
        "prompts",
        parents=[common],
        help="Owner verbs for the staged prompts tree. 'prompts new' mints a conforming staged prompt.",
        formatter_class=_AlphaHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  aw prompts new --kind research --slug token-compression\n"
            "  aw prompts new --kind research --slug token-compression --apply\n"
            "\n"
            "SAFETY & DEFAULTS\n"
            "  Dry-run by default: nothing is written without --apply.\n"
            "  A minted prompt is NEVER staged or committed; that stays a deliberate act.\n"
            "\n"
            "OUTPUT & EXITS\n"
            "  Exit codes: 0 clean, 2 cannot-run/usage error.\n"
            "  Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.\n"
        ),
        description=(
            "Owner verbs for the operational prompt STAGING tree in .aw/records/prompts/: 'new' mints a "
            "conforming staged prompt (derived filename + the single leading `aw-prompt` metadata comment) "
            "into pending/, so a prompt is a tooled artifact instead of a hand-named file."
        ),
    )
    prompts_sub = p_prompts.add_subparsers(dest="prompts_command")
    p_prompts_new = prompts_sub.add_parser(
        "new",
        parents=[common],
        help="Mint a conforming staged prompt in pending/ (dry-run by default; --apply to write).",
        description=(
            "Create a conforming staged prompt under .aw/records/prompts/pending/ (dry-run by default; "
            "--apply to write). Derives the filename (YYYYMMDD-HHMM-NN-<slug>.prompt.md, with NN a "
            "per-minute sequence computed across the whole prompts tree) and writes the single leading "
            "`<!-- aw-prompt: ... -->` metadata comment. It writes NO body: the prompt body is yours to "
            "author, and any other content would violate the prompt-purity contract. Never auto-staged."
        ),
    )
    p_prompts_new.add_argument(
        "--dir", default=None, help="Repo root (default: current directory)."
    )
    p_prompts_new.add_argument(
        "--slug",
        default=None,
        help="Short descriptive kebab slug (required; becomes the filename slug).",
    )
    p_prompts_new.add_argument(
        "--kind",
        default="research",
        help="Prompt kind: run-once, research, or session-handoff (default: research).",
    )
    p_prompts_new.add_argument(
        "--status",
        default="pending",
        help="Status recorded in the metadata comment (default: pending).",
    )
    p_prompts_new.add_argument(
        "--author",
        default=None,
        help="Authoring agent and model (e.g. 'opencode (provider/model)'). Omitted from the "
        "metadata comment when not supplied; never guessed.",
    )
    p_prompts_new.add_argument(
        "--targets",
        default=None,
        help="The target AI(s) this prompt is written for (optional metadata field).",
    )
    p_prompts_new.add_argument(
        "--concerns",
        default=None,
        help="One-line statement of what the prompt is about (optional metadata field).",
    )
    p_prompts_new.add_argument(
        "--date", default=None, help="Override the created date (YYYY-MM-DD)."
    )
    p_prompts_new.add_argument(
        "--time", default=None, help="Override the filename time component (HHMM)."
    )
    p_prompts_new.add_argument(
        "--apply", action="store_true", help="Write the file (default is preview only)."
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
    _add_commit_flags(p_archive)  # selfcommit jgcm68 E-01/E-02

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

    # bklggrad f1dhht: OPT-IN local pre-commit gate refusing a release-blocking backlog item closed
    # to done without a preserved-or-satisfied gate. Delegates to the child-02 shared predicate.
    sub.add_parser(
        "backlog-blocking-close-gate",
        parents=[common],
        help="Local pre-commit gate: refuse a release-blocking backlog item closed to done without a "
        "handoff/evidence/de-gate (OPT-IN, LOCAL prevention, no CI; the aw check rule is the backstop).",
    )

    # ipddeps mp88bl: OPT-IN local pre-commit gate refusing a staged IPD with an invalid/cyclic
    # cross-IPD Item-Dependencies statement. Delegates to the child-02 shared evaluator.
    sub.add_parser(
        "ipd-dependency-statement-gate",
        parents=[common],
        help="Local pre-commit gate: refuse a staged IPD with a malformed/dangling/ambiguous/cyclic "
        "Item-Dependencies statement (OPT-IN, LOCAL prevention, no CI; the aw check rule is the backstop).",
    )

    # agentadhere diundn: OPT-IN local pre-commit gate running the shared commit-invariant checker
    # (status-untooled + release-gate + scope-drift) over the staged commit with teaching errors.
    sub.add_parser(
        "precommit-scope-gate",
        parents=[common],
        help="Local pre-commit gate: refuse a staged commit that violates a repository invariant or "
        "a plan's declared Scope-Paths, teaching the recovery command (OPT-IN, LOCAL; CI is the authority).",
        description=(
            "Inspect the STAGED diff and refuse the commit when it violates a repository invariant or "
            "strays outside the declared `Scope-Paths` of the plan being executed, printing the "
            "recovery command rather than just a rejection. Normally invoked by a git pre-commit hook "
            "rather than typed by hand. Honest about its own limits: it is OPT-IN, purely LOCAL, and "
            "bypassable with `--no-verify`, so CI remains the actual authority; this exists to catch "
            "the mistake early, not to be the boundary."
        ),
    )
    # agentadhere diundn: OPT-IN local pre-push gate that prevents an accidental push and explains
    # real authorization. FEEDBACK ONLY, honestly NOT an authority boundary.
    sub.add_parser(
        "prepush-authorization-gate",
        parents=[common],
        help="Local pre-push gate: prevent an accidental push and explain real authorization "
        "(OPT-IN, LOCAL FEEDBACK ONLY, bypassable; NOT an authority boundary - CI/protected branch is).",
        description=(
            "Stop an ACCIDENTAL push and explain where real authorization comes from. Normally invoked "
            "by a git pre-push hook rather than typed by hand. Deliberately described as FEEDBACK "
            "ONLY: it is opt-in, local, and bypassable, so it is not an authority boundary and must "
            "not be relied on as one. Branch protection and CI are the enforcement; this is the "
            "reminder that arrives before you need them."
        ),
    )

    # tabcomp Order 01 (bja8og): `aw completion <shell>` streams a native completion script to
    # stdout. PARSER SHAPE (forward-compatibility, blocks tabcomp-03 jolfpj E-02): `shell` is NOT a
    # bare `choices={bash,zsh,fish}` positional - that would collide with the `install`/`uninstall`
    # verbs tabcomp-03 adds. Instead `target` is a free-form optional positional (validated in the
    # handler): today it accepts a shell name (or is omitted -> $SHELL detection, OQ-01 bash
    # fallback); tabcomp-03 can additively accept `install`/`uninstall` as the first token WITHOUT
    # reshaping this parser. Do NOT convert `target` to a fixed-choices positional.
    # Single source of truth for the supported shell vocabulary (stdlib-only, cheap import).
    from agent_workflows import completion as completion_mod

    p_completion = sub.add_parser(
        "completion",
        parents=[common],
        help="Emit a native shell completion script (bash|zsh|fish) to stdout for `aw`, `agentwf`, "
        "and `agent-workflows`; e.g. `source <(aw completion bash)`.",
    )
    p_completion.add_argument(
        "target",
        nargs="?",
        default=None,
        metavar="bash|zsh|fish|install|uninstall",
        help="Shell to generate for (default: detect from $SHELL, else bash), or the verb "
        "'install'/'uninstall' to manage the drop-in auto-discovery file.",
    )
    # tabcomp Order 03 (jolfpj) E-02: the install/uninstall verbs are ADDITIVE on child 01's
    # free-form `target` positional (see the shape note above) - `aw completion <shell>` output is
    # unchanged. These flags only apply when `target` is install|uninstall.
    p_completion.add_argument(
        "--shell",
        choices=list(completion_mod.SUPPORTED_SHELLS),
        default=None,
        help="Shell to install/uninstall completion for (default: detect from $SHELL, else bash).",
    )
    p_completion.add_argument(
        "--dir",
        dest="completion_dir",
        default=None,
        help="Override the drop-in directory (default: the shell's XDG auto-discovery dir).",
    )
    p_completion.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the drop-in paths that would be written/removed without touching the filesystem.",
    )

    # tabcomp Order 02 (4f1j25) E-02: the HIDDEN `__complete` shell callback. help=SUPPRESS keeps it
    # out of `--help` AND out of child 01's static completion output (introspect_cli_tree's
    # `_visible_subcommands` drops any subparser whose help is argparse.SUPPRESS). WIRE PROTOCOL (the
    # exact shape child 01's generated bash/zsh/fish scripts invoke): the current command tokens are
    # passed AFTER a literal `--` separator so option-like tokens are never mis-parsed as flags -
    #   aw __complete --cword <N> -- <tok0> <tok1> ...
    # `<N>` is the index of the word being completed; candidates print newline-delimited to stdout;
    # empty output means no candidates; the query ALWAYS exits 0 (a completion query never errors the
    # shell). `--` + REMAINDER is required so a leading `-x` token in the completed line is data, not
    # a flag of `__complete` itself.
    p_dunder_complete = sub.add_parser("__complete", help=argparse.SUPPRESS)
    p_dunder_complete.add_argument("--cword", type=int, default=0)
    p_dunder_complete.add_argument(
        "words", nargs=argparse.REMAINDER, metavar="-- <tokens>"
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


def _offer_records_commit(
    args: argparse.Namespace,
    repo_root: Union[str, Path],
    *,
    paths: Sequence[str],
    message: str,
    on_unrelated_staged: str = "scope",
) -> None:
    """selfcommit jgcm68: offer to path-scoped-commit exactly ``paths`` after a records mutation.

    Threads the SHARED ``--commit``/``--no-commit`` flags (E-01) onto the child-01
    ``git_commit_helper.offer_commit`` call. Interactive-gated: on a TTY it prompts; non-interactive
    without ``--commit`` is a NO-OP (never commits silently). Path-scoped, never ``add -A``/``-a``,
    never push, never ``--no-verify``. A commit failure or decline is non-fatal - the mutation
    already happened; we only surface a short status line so the run is not derailed.
    """
    from agent_workflows import git_commit_helper as _gch

    if not paths:
        return
    assume_yes = bool(getattr(args, "commit", False))
    no_commit = bool(getattr(args, "no_commit", False))
    # jgcm68 D2: the backends git-mv their renames (pre-staging them), which makes offer_commit's
    # `git add -- <old-path>` fail. Unstage exactly these touched paths first so the helper cleanly
    # re-stages (and re-detects) them; scoped to the verb's own paths, never global.
    _gch._git(Path(repo_root), ["reset", "--quiet", "HEAD", "--", *paths])
    outcome = _gch.offer_commit(
        Path(repo_root),
        paths,
        message=message,
        assume_yes=assume_yes,
        no_commit=no_commit,
        on_unrelated_staged=on_unrelated_staged,
    )
    if outcome.status == _gch.STATUS_COMMITTED:
        print(f"committed {len(outcome.staged)} path(s): {outcome.commit}")
    elif outcome.status == _gch.STATUS_ERROR:
        print(f"warning: self-commit skipped: {outcome.message}")


def _nv_offer_selector_label(args: argparse.Namespace) -> str:
    """A terse label of the group/rename selector(s) for the default commit message."""
    ids = getattr(args, "ids", None)
    if ids:
        return ",".join(str(i) for i in ids)
    one = getattr(args, "id", None) or getattr(args, "selector", None)
    if isinstance(one, list):
        one = one[0] if one else None
    return str(one) if one else "records"


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
        for entry in config.repo_setting(cfg, "exclude")
        if not discovery._is_excluded(
            rp, [os.path.expandvars(os.path.expanduser(str(entry)))]
        )
    ]
    config.set_repo_setting(cfg, "exclude", kept)
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

    # tabcomp Order 03 (jolfpj) E-04: host-level completion setup + discovery tip, ONCE per
    # invocation (not per repo) because completion is a per-user/per-machine concern.
    _configure_completion(args, term)
    _completion_tip(term)
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
    # jolfpj E-04: once per invocation for the `install all` batch path too (parity with the
    # single-repo path); still a per-user concern, so it is NOT inside the per-repo loop.
    _configure_completion(args, term)
    _completion_tip(term)
    return 1 if failed else 0


def _completion_configured() -> bool:
    """True when OUR drop-in completion is already installed for the detected shell (jolfpj E-04)."""
    try:
        from agent_workflows import completion as _completion

        return _completion.is_completion_installed(_detect_shell())
    except Exception:
        return False


def _completion_tip(term: Term) -> None:
    """Print the tab-completion discovery tip when completion is not yet configured (jolfpj E-04).

    A per-user/per-machine hint, so it is printed ONCE per command invocation (not once per repo in
    a batch install) and stays silent when completion is already in place.
    """
    if _completion_configured():
        return
    term.line()
    term.status("ok", "Tip: Enable tab-completion with 'aw completion install'")


def _resolve_completion_choice(args: argparse.Namespace) -> Optional[str]:
    """Resolve `--completion [auto|bash|zsh|fish|none]` to a shell name, or None for 'do nothing'.

    `auto` detects from $SHELL (bash fallback). `none` (and an absent flag) yield None; the absent
    case is then handled by the interactive prompt in `_run_setup` (E-03), which is skipped
    non-interactively so a batch/`--yes` run touches no completion directory (the safe default).
    """
    choice = getattr(args, "completion", None)
    if choice in (None, "none"):
        return None
    return _detect_shell() if choice == "auto" else choice


def _configure_completion(args: argparse.Namespace, term: Term) -> None:
    """Install shell completion per `--completion`, else offer it interactively (jolfpj E-03/E-04).

    HOST-LEVEL, once-per-user concern: this lives on the `aw setup`/`aw install` host flow, NOT in
    `install_wizard.py` (the per-target-repo project-policy wizard), so it does not re-prompt on
    every repo install. Explicit `--completion <shell>|auto` installs without asking. With no flag,
    a single confirm is offered ONLY on an interactive TTY without `--yes`; non-interactive and
    `--yes` runs install nothing (safe, non-destructive default). Never edits an rc/dotfile.
    """
    from agent_workflows import completion as _completion

    shell = _resolve_completion_choice(args)
    explicit = shell is not None

    if not explicit:
        if getattr(args, "completion", None) == "none":
            return  # explicit opt-out: do not prompt.
        if getattr(args, "yes", False) or not sys.stdin.isatty():
            return  # non-interactive / batch: safe default is to touch nothing.
        shell = _detect_shell()
        if _completion.is_completion_installed(shell):
            return  # already ours; nothing to offer.
        term.line()
        term.heading("Shell tab-completion")
        term.line(
            f"Enable tab-completion for aw in {shell}? This writes one file to "
            f"{_completion.resolve_completion_dir(shell)} "
            "and does NOT modify your ~/.bashrc, ~/.zshrc, or config.fish."
        )
        try:
            answer = input("  Install shell completion? [y/N] ").strip().lower()
        except EOFError:
            return
        if answer not in ("y", "yes"):
            term.status(
                "skip", "Skipped; enable it later with 'aw completion install'."
            )
            return

    try:
        result = _completion.install_shell_completion(shell)
    except (_completion.CompletionInstallError, OSError) as exc:
        # Never fail a setup/install over an optional convenience feature.
        term.status("warn", f"Shell completion not installed: {exc}")
        return
    term.status(
        "ok",
        f"{shell} completion installed in {result['dir']} (no rc/dotfile modified). "
        f"Start a new {shell} shell to pick it up.",
    )


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
    installed = config.repo_setting(cfg, "installed")
    stored = [p for p in installed if config.expand_path(p).resolve() != repo_root]
    if len(stored) != len(installed):
        config.set_repo_setting(cfg, "installed", stored)
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
            ignore=config.ignore_patterns(cfg),
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


def _release_label_for(repo: Path) -> str | None:
    """Return a short 'version (id6)' label for the single planned release, or None.
    Lets `aw status` name what a release-blocker count is gating instead of an
    anonymous number."""
    try:
        from agent_workflows import releases as _releases

        rel = _releases.describe_planned_release(repo)
    except Exception:
        return None
    return f"{rel[1]} ({rel[0]})" if rel else None


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
            # Name the planned release (version) so a blocker count is attributable, not anonymous.
            "release_label": _release_label_for(repo),
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
    excluded_entries = sorted(
        config.repo_setting(cfg, "exclude"), key=lambda e: str(e).lower()
    )
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
        # aw.agent/v1 payload keys are a published contract (docs/cli-output-contract.md):
        # the on-disk layout moved to repos.*, these WIRE names deliberately did not.
        "search_roots": config.repo_setting(cfg, "search"),
        "repos_configured": len(config.repo_setting(cfg, "installed")),
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
    term.kv("  Search roots", ", ".join(config.repo_setting(cfg, "search")) or "(none)")
    term.kv("  Repos configured", str(len(config.repo_setting(cfg, "installed"))))
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
                        _rlabel = attn.get("release_label")
                        _for = f" for {_rlabel}" if _rlabel else ""
                        attn_line += " - " + term.color256(
                            f"{attn['release_blockers']} release blocker(s){_for}",
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
    current_exclude = sorted(
        config.repo_setting(cfg, "exclude"), key=lambda s: str(s).lower()
    )
    current_repos = sorted(
        config.repo_setting(cfg, "installed"), key=lambda s: str(s).lower()
    )
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
        config.set_repo_setting(cfg, "exclude", current_exclude)
        config.set_repo_setting(cfg, "installed", current_repos)
        config.save(cfg)
    return 0


def _run_include(args: argparse.Namespace, term: Term) -> int:
    """aw include [repo|repos] repodir1 [repodir2 ...]: include repos in aw management."""
    from agent_workflows.result_types import NextAction

    raw_repos = list(getattr(args, "repos", []) or [])
    if raw_repos and raw_repos[0] in ("repo", "repos"):
        raw_repos = raw_repos[1:]

    cfg = config.load()
    current_exclude = sorted(
        config.repo_setting(cfg, "exclude"), key=lambda s: str(s).lower()
    )
    current_repos = sorted(
        config.repo_setting(cfg, "installed"), key=lambda s: str(s).lower()
    )
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
        config.set_repo_setting(cfg, "exclude", current_exclude)
        config.set_repo_setting(cfg, "installed", current_repos)
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
        existing = config.repo_setting(cfg, "search")
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
        merged = list(dict.fromkeys(config.repo_setting(cfg, "search") + roots))
        config.set_repo_setting(cfg, "search", merged)

    # Discover repos under the roots.
    expanded_roots = config.expanded_search_roots(cfg)
    found = discovery.discover(
        expanded_roots,
        ignore=config.ignore_patterns(cfg),
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
        cfg_repos = config.repo_setting(cfg, "installed")
        for repo in found.targets:
            cfg_repos.append(str(repo))
        config.set_repo_setting(cfg, "installed", list(dict.fromkeys(cfg_repos)))

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

    # tabcomp Order 03 (jolfpj) E-03/E-04: the HOST-LEVEL, once-per-user completion step. It runs
    # here (after the per-repo installs, before orientation) rather than inside install_wizard.py,
    # which is the per-target-repo project-policy wizard and would re-prompt on every repo.
    _configure_completion(args, term)

    _orient(term)
    _completion_tip(term)
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


def _run_config_show(args: argparse.Namespace, term: Term) -> int:
    """Display the configuration file location, status, and settings (or a single variable)."""
    cfg = config.load()
    cfg_file = config.config_path()
    present = cfg_file.is_file()
    cfg_path_str = config._preserve_home(str(cfg_file))
    varname = getattr(args, "varname", None)

    if varname:
        varname = str(varname).strip()
        try:
            canon_key, val = config.get_config_value(varname, cfg)
        except config.ConfigError as exc:
            term.status("fail", str(exc))
            return 2

        if getattr(args, "json", False) or getattr(args, "as_json", False):
            payload = {
                "config_file": str(cfg_file),
                "config_present": present,
                "key": canon_key,
                "value": val,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        if getattr(args, "agent", False):
            from agent_workflows.term import format_agent_json

            print(
                format_agent_json(
                    kind="result",
                    cmd="config-show",
                    outcome="clean",
                    exit_code=0,
                    extra={
                        "config_file": str(cfg_file),
                        "config_present": present,
                        "key": canon_key,
                        "value": val,
                    },
                )
            )
            return 0

        term.heading("agent-workflows configuration")
        term.line(
            f"  {term.colorize('File:', 'bold')}    {term.color256(cfg_path_str, 39)} "
            f"({'present' if present else 'none yet; default values in effect'})"
        )
        term.line()
        term.heading("Setting")
        if isinstance(val, dict):
            # A container key such as `repos`: print each of its settings, not the raw mapping.
            for sub_key in sorted(val):
                _config_show_setting_line(term, f"{canon_key}.{sub_key}", val[sub_key])
        else:
            _config_show_setting_line(term, canon_key, val)
        return 0

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        payload = {
            "config_file": str(cfg_file),
            "config_present": present,
            "config": cfg,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-show",
                outcome="clean",
                exit_code=0,
                extra={
                    "config_file": str(cfg_file),
                    "config_present": present,
                    "config": cfg,
                },
            )
        )
        return 0

    term.heading("agent-workflows configuration")
    term.line(
        f"  {term.colorize('File:', 'bold')}    {term.color256(cfg_path_str, 39)} "
        f"({'present' if present else 'none yet; default values in effect'})"
    )
    term.line()
    # Group the schema by section so the nested `repos.*` settings read as a unit. The bare
    # container keys (`repos`, `defaults`) are section HEADINGS here, so they are never also
    # printed as a raw mapping value; that would show the same data twice.
    container_keys = {
        key
        for key, spec in config.CONFIG_SCHEMA.items()
        if spec.type_name == "dict" and "." not in key
    }
    sections: List[Tuple[str, List[str]]] = []
    plain_keys = sorted(
        key
        for key in config.CONFIG_SCHEMA
        if "." not in key and key not in container_keys
    )
    if plain_keys:
        sections.append(("Settings", plain_keys))
    for container in sorted(container_keys):
        child_keys = sorted(
            key for key in config.CONFIG_SCHEMA if key.startswith(f"{container}.")
        )
        if child_keys:
            sections.append((f"Settings ({container})", child_keys))

    for heading, keys in sections:
        term.heading(heading)
        for key in keys:
            _, val = config.get_config_value(key, cfg)
            _config_show_setting_line(term, key, val)
    return 0


def _config_show_setting_line(term: Term, label: str, val: Any) -> None:
    """Print one ``aw config show`` setting line, expanding a list over several lines."""

    if isinstance(val, list):
        if not val:
            term.line(f"  {term.color256(label, 244):<20} = []")
        elif len(val) == 1:
            term.line(
                f"  {term.color256(label, 244):<20} = [{term.color256(str(val[0]), 39)}]"
            )
        else:
            term.line(f"  {term.color256(label, 244):<20} = [")
            for item in val:
                term.line(f"      {term.color256(str(item), 39)},")
            term.line("  ]")
        return
    disp_val = "-" if val is None else str(val)
    term.line(f"  {term.color256(label, 244):<20} = {term.color256(disp_val, 39)}")


def _run_config_get(args: argparse.Namespace, term: Term) -> int:
    """Get the value of a configuration variable."""
    cfg = config.load()
    varname = getattr(args, "varname", "").strip()
    if not varname:
        term.status("fail", "Missing variable name. Usage: aw config get <varname>")
        return 2

    try:
        canon_key, val = config.get_config_value(varname, cfg)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(json.dumps({canon_key: val}, indent=2, sort_keys=True))
        return 0

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-get",
                outcome="clean",
                exit_code=0,
                extra={"key": canon_key, "value": val},
            )
        )
        return 0

    if isinstance(val, bool):
        print(str(val).lower())
    elif isinstance(val, (list, dict)):
        print(json.dumps(val))
    elif val is None:
        print("")
    else:
        print(str(val))
    return 0


def _run_config_set(args: argparse.Namespace, term: Term) -> int:
    """Set the value of a configuration variable."""
    raw_tokens = getattr(args, "set_args", []) or []
    try:
        varname, val_expr = config.parse_set_args(raw_tokens)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    try:
        updated_cfg, canon_key, final_val = config.set_config_value(
            varname, val_expr, auto_save=True
        )
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    cfg_file = config.config_path()
    cfg_path_str = config._preserve_home(str(cfg_file))

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(
            json.dumps(
                {canon_key: final_val, "config_file": str(cfg_file)},
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-set",
                outcome="clean",
                exit_code=0,
                extra={
                    "key": canon_key,
                    "value": final_val,
                    "config_file": str(cfg_file),
                },
            )
        )
        return 0

    term.status(
        "ok",
        f"{term.color256(canon_key, 39, bold=True)} = {term.colorize(str(final_val), 'bold')} (saved to {cfg_path_str})",
    )
    return 0


def _run_config_add(args: argparse.Namespace, term: Term) -> int:
    """Add an item to a list configuration variable."""
    raw_tokens = getattr(args, "add_args", []) or []
    try:
        item_val, varname = config.parse_add_args(raw_tokens)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    try:
        updated_cfg, canon_key, updated_list, was_added, stored = (
            config.add_config_item(varname, item_val, auto_save=True)
        )
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    cfg_file = config.config_path()
    cfg_path_str = config._preserve_home(str(cfg_file))

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(
            json.dumps(
                {
                    "key": canon_key,
                    "item": stored,
                    "added": was_added,
                    "value": updated_list,
                    "config_file": str(cfg_file),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-add",
                outcome="clean",
                exit_code=0,
                extra={
                    "key": canon_key,
                    "item": stored,
                    "added": was_added,
                    "value": updated_list,
                    "config_file": str(cfg_file),
                },
            )
        )
        return 0

    if was_added:
        term.status(
            "ok",
            f"Added '{term.color256(stored, 39, bold=True)}' to {term.color256(canon_key, 39, bold=True)} (saved to {cfg_path_str})",
        )
    else:
        term.status(
            "ok",
            f"Already present: '{term.color256(stored, 39, bold=True)}' is already in {term.color256(canon_key, 39, bold=True)}",
        )
    return 0


def _run_config_remove(args: argparse.Namespace, term: Term) -> int:
    """Remove an item from a list configuration variable."""
    raw_tokens = getattr(args, "remove_args", []) or []
    try:
        item_val, varname = config.parse_remove_args(raw_tokens)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    try:
        updated_cfg, canon_key, updated_list, was_removed, stored = (
            config.remove_config_item(varname, item_val, auto_save=True)
        )
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    cfg_file = config.config_path()
    cfg_path_str = config._preserve_home(str(cfg_file))

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(
            json.dumps(
                {
                    "key": canon_key,
                    "item": stored,
                    "removed": was_removed,
                    "value": updated_list,
                    "config_file": str(cfg_file),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if was_removed else 1

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-remove",
                outcome="clean" if was_removed else "not_found",
                exit_code=0 if was_removed else 1,
                extra={
                    "key": canon_key,
                    "item": stored,
                    "removed": was_removed,
                    "value": updated_list,
                    "config_file": str(cfg_file),
                },
            )
        )
        return 0 if was_removed else 1

    if was_removed:
        term.status(
            "ok",
            f"Removed '{term.color256(stored, 39, bold=True)}' from {term.color256(canon_key, 39, bold=True)} (saved to {cfg_path_str})",
        )
        return 0
    else:
        term.status(
            "warn",
            f"No entry matching '{stored}' in {canon_key}",
        )
        return 1


def _run_config_is(args: argparse.Namespace, term: Term) -> int:
    """Check if an item is present in a list configuration variable."""
    raw_tokens = getattr(args, "is_args", []) or []
    try:
        item_val, varname = config.parse_is_args(raw_tokens)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    try:
        canon_key, present, stored = config.is_config_item_present(varname, item_val)
    except config.ConfigError as exc:
        term.status("fail", str(exc))
        return 2

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(
            json.dumps(
                {"key": canon_key, "item": stored, "present": present},
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if present else 1

    if getattr(args, "agent", False):
        from agent_workflows.term import format_agent_json

        print(
            format_agent_json(
                kind="result",
                cmd="config-is",
                outcome="clean" if present else "not_found",
                exit_code=0 if present else 1,
                extra={"key": canon_key, "item": stored, "present": present},
            )
        )
        return 0 if present else 1

    if present:
        term.status(
            "ok",
            f"Yes, '{term.color256(stored, 39, bold=True)}' is in {term.color256(canon_key, 39, bold=True)}",
        )
        return 0
    else:
        term.status(
            "warn",
            f"No, '{term.color256(stored, 39, bold=True)}' is not in {term.color256(canon_key, 39, bold=True)}",
        )
        return 1


def _run_config_exclude(args: argparse.Namespace, term: Term) -> int:
    """Manage the never-install exclude blocklist (clianx-01 E-04): add/list/rm."""
    from agent_workflows.result_types import NextAction

    sub = getattr(args, "exclude_command", None)
    cfg = config.load()
    current = config.repo_setting(cfg, "exclude")

    if sub == "add":
        entry = config._preserve_home(str(args.path))
        if entry in current:
            term.status("ok", f"Already excluded: {entry}")
            return 0
        current.append(entry)
        config.set_repo_setting(cfg, "exclude", current)
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
        config.set_repo_setting(cfg, "exclude", kept)
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
        # Honor the traversal-guard escape hatches for this invocation only.
        _inc = bool(getattr(args, "include_ignored", False))
        _depth = getattr(args, "max_depth", None)
        if _inc or _depth is not None:
            from agent_workflows import selectors as _sel

            with _sel.search_limits(include_ignored=_inc, max_depth=_depth):
                return _run_find(args, term, context=context)
        return _run_find(args, term, context=context)
    types = _nv_resolve_types(args, term, verb)
    if types is None:
        return 2
    from agent_workflows import artifact_types as at
    from agent_workflows.plans_refs import MutationResult

    rc = 0
    # selfcommit jgcm68 E-07: for group/rename, backends RETURN a MutationResult (touched +
    # index paths) and perform NO commit; we aggregate across the (possibly several) types and
    # place the self-commit offer ONCE here at the dispatch site (PR-012: never inside a shared
    # backend, so `aw group research` fires exactly once from here and NOT again in the backend).
    touched_all: list[str] = []
    index_all: list[str] = []
    for t in types:
        fn = at.resolve_backend(t, verb)
        if fn is None:
            term.status("warn", f"'{verb}' is not yet wired / not supported for {t}.")
            rc = max(rc, 2)
            continue
        result = fn(_nv_backend_args(args, t))
        if isinstance(result, MutationResult):
            rc = max(rc, result.rc)
            touched_all.extend(result.touched_paths)
            index_all.extend(result.index_paths)
        elif isinstance(result, int):
            rc = max(rc, result)
    if verb in ("group", "rename") and (touched_all or index_all):
        from agent_workflows.project_context import resolve_verb_repo_root

        repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
        sel = _nv_offer_selector_label(args)
        _offer_records_commit(
            args,
            repo_root,
            paths=[*touched_all, *index_all],
            message=f"refactor({','.join(types)}): {verb} {sel} and rewrite refs",
        )
    return rc


def _find_type_records(
    repo_root: Path,
    artifact_type: str,
    selectors_list: List[str],
    args: argparse.Namespace,
    term: Term,
) -> tuple[List[str], List[str]]:
    """Find and format matching records for a given artifact type. Returns (lines, paths)."""
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
        paths = []
        for e in results:
            status = e.disposition or e.status or "-"
            status_txt = term.status_256(status, width=12)
            id6_txt = (
                term.color256(e.plan_id or "??????", 39, bold=True)
                if term.color
                else (e.plan_id or "??????")
            )
            set_txt = f"{e.set_id or '-':<14}"
            full_p = (plans_dir / e.path).resolve()
            try:
                rel_p = str(full_p.relative_to(repo_root.resolve()))
            except Exception:
                rel_p = str(e.path)
            lines.append(f"{status_txt}  {id6_txt}  {set_txt}  {rel_p}")
            paths.append(rel_p)
        return lines, paths

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
        paths = []
        for e in results:
            status = e.status or "-"
            status_txt = term.status_256(status, width=12)
            id6_txt = (
                term.color256(e.id6 or "??????", 39, bold=True)
                if term.color
                else (e.id6 or "??????")
            )
            summary = f"  {e.summary}" if e.summary else ""
            full_p = (research_root / e.path).resolve()
            try:
                rel_p = str(full_p.relative_to(repo_root.resolve()))
            except Exception:
                rel_p = str(e.path)
            lines.append(f"{status_txt}  {id6_txt}  {rel_p}{summary}")
            paths.append(rel_p)
        return lines, paths

    # All other types: specs, prompts, backlog, walkthroughs, roadmaps, comms, releases
    if selectors_list:
        matched_paths = sel_mod.resolve_selectors(
            repo_root, artifact_type, selectors_list
        )
    else:
        matched_paths = [p for p, _ in sel_mod._iter_files(repo_root, artifact_type)]

    lines = []
    paths = []
    for p in sorted(matched_paths):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        id6 = sel_mod._read_id(text) or "-"
        status = sel_mod._read_status(text) or "-"
        try:
            rel = str(p.resolve().relative_to(repo_root.resolve()))
        except Exception:
            rel = str(p)
        status_txt = term.status_256(status, width=12)
        id6_txt = term.color256(id6, 39, bold=True) if term.color else id6
        lines.append(f"{status_txt}  {id6_txt}  {rel}")
        paths.append(rel)
    return lines, paths


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
    all_paths = []
    explicit_flags = argparse.Namespace(
        id=getattr(args, "id", None),
        set=getattr(args, "set", None),
        status=getattr(args, "status", None),
        topic=getattr(args, "topic", None),
        disposition=getattr(args, "disposition", None),
        dir=getattr(args, "dir", None),
    )
    for t in types:
        lines, paths = _find_type_records(repo_root, t, selectors, explicit_flags, term)
        all_lines.extend(lines)
        all_paths.extend(paths)

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

    if getattr(args, "paths", False) or (ctx.is_agent and all_paths):
        for p in all_paths:
            print(p)
        return 0 if (all_paths or not selectors) else 1

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
                "paths": all_paths,
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
    short_format = getattr(args, "short", False)
    files_only = getattr(args, "files_only", False)

    hits = 0
    json_results = []
    matching_files = []

    def _artifact_status(p: Path, text: str) -> str:
        m = re.search(r"(?m)^-\s*Status:\s*(\S+)", text)
        if m:
            return m.group(1)
        parts = p.parts
        for bucket in (
            "executed",
            "active",
            "pending",
            "reviewed",
            "approved",
            "reusable",
            "superseded",
            "not-executed",
            "open",
            "done",
            "parked",
            "todo",  # rstodo p3o9je: research hot state (renamed from `intake`)
            "intake",  # legacy alias kept for any unmigrated on-disk path bucket
            "reference",
            "archived",
            "planned",
            "shipped",
        ):
            if bucket in parts:
                return bucket
        return "-"

    item_map = None
    if short_format:
        try:
            from agent_workflows import attention as att

            items_scanned, _ = att.scan(repo_root)
            item_map = {(repo_root / it.path).resolve(): it for it in items_scanned}
        except Exception:
            item_map = {}

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

                if file_matches:
                    matching_files.append(str(p))
                    if not (ctx.is_agent or ctx.is_json):
                        if short_format:
                            from agent_workflows import attention as att

                            it = item_map.get(p.resolve()) if item_map else None
                            if it:
                                status_word = it.native_status
                                status_padded = term.status_256(status_word, width=12)
                                age = att._age_marker(it.last_history_at, it.tree)
                                gate_glyph = "#" if it.gate else ""
                                rb_glyph = ">" if it.blocks_release else ""
                                blk = (age + gate_glyph + rb_glyph).strip()
                                lead = f"{blk:<3}" if blk else "   "
                                path_txt = att._identity_stem(it.path)
                                type_word = att._SINGULAR_TYPE.get(it.tree, it.tree)
                                type_txt = (
                                    term.color256(
                                        type_word, att._TREE_COLOR_256, bold=True
                                    )
                                    if term.color
                                    else type_word
                                )
                                type_prefix = (
                                    type_txt
                                    + (" " * max(0, 10 - len(type_word)))
                                    + "  "
                                )
                                prio = ""
                                if it.priority:
                                    pcode = {
                                        "high": 196,
                                        "medium": 214,
                                        "low": 244,
                                    }.get(it.priority, 244)
                                    prio = "  " + (
                                        term.color256(
                                            f"[{it.priority}]", pcode, bold=True
                                        )
                                        if term.color
                                        else f"[{it.priority}]"
                                    )
                                blocking = ""
                                if it.blocks_release:
                                    blocking = "  " + (
                                        term.color256("[blocking]", 196, bold=True)
                                        if term.color
                                        else "[blocking]"
                                    )
                                inline_gate = ""
                                if it.gate and it.attention_class != "blocked":
                                    g = it.gate
                                    g_kind = g.get("kind")
                                    g_ref = att.A.escape_detail(g.get("ref", ""))
                                    inline_gate = f"  [gate {g_kind}: {g_ref}]"
                                term.line(
                                    f"- {lead}{status_padded}  {type_prefix}{path_txt}{prio}{blocking}{inline_gate}"
                                )
                            else:
                                try:
                                    rel = str(p.relative_to(repo_root))
                                except ValueError:
                                    rel = str(p)
                                stem = att._identity_stem(rel)
                                status_word = _artifact_status(p, text)
                                status_padded = term.status_256(status_word, width=12)
                                type_word = att._SINGULAR_TYPE.get(t, t)
                                type_txt = (
                                    term.color256(
                                        type_word, att._TREE_COLOR_256, bold=True
                                    )
                                    if term.color
                                    else type_word
                                )
                                type_prefix = (
                                    type_txt
                                    + (" " * max(0, 10 - len(type_word)))
                                    + "  "
                                )
                                term.line(f"-    {status_padded}  {type_prefix}{stem}")
                        elif files_only:
                            file_header = (
                                term.color256(str(p), 39, bold=True)
                                if term.color
                                else str(p)
                            )
                            term.line(file_header)
                        else:
                            file_header = (
                                term.color256(str(p), 39, bold=True)
                                if term.color
                                else str(p)
                            )
                            term.line(file_header)
                            for i, line in file_matches:
                                highlighted = _highlight_matches(line.strip(), rx, term)
                                if line_numbers:
                                    line_no = (
                                        term.color256(f"{i}:", 244)
                                        if term.color
                                        else f"{i}:"
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
                "files": matching_files,
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
    include_retired = bool(getattr(args, "all", False))

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
            include_retired=include_retired,
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
            files = list(
                ce._iter_type_files(repo_root, t, include_retired=include_retired)
            )
            type_counts[t] = len(files)
            total_checked += len(files)
        except Exception:
            type_counts[t] = 0

    # Build diagnostics from drift
    diagnostics = []
    from agent_workflows import doctor as _doctor

    # agentadhere Phase 1 (IPD uisjns): build the versioned, JSON-safe finding shape alongside the
    # compact Diagnostic. Each finding carries the stable rule id, severity, assurance class (from
    # the Phase-0 catalog via the rule registry), observed-vs-required, the exact recovery command,
    # and the determinism tag under a policy schema_version. This rides in `data["findings"]` so the
    # existing Diagnostic/compact-agent shape stays byte-compatible for current consumers.
    findings: list = []
    seen_fixes = set()
    for d in drift:
        try:
            title, dir_str, fname, extra, fix = _doctor._categorize_drift(d, repo_root)
        except Exception:
            fix = None
        # Prefer any determinism/assurance/severity already stamped on the Drift, else the registry.
        enriched = ce.enrich_drift(d, recovery=fix or "")
        diagnostics.append(
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity=enriched.severity or "error",
                fix=fix or None,
            )
        )
        findings.append(ce.finding_dict(enriched, repo_root))
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
            # str(), not the raw PosixPath: `data` is serialized verbatim by CommandResult.to_dict
            # (the `--json` renderer), and a PosixPath is not JSON-serializable. Passing a str keeps
            # to_agent_record's path-normalization working AND fixes the pre-existing
            # `aw check --json` crash. (agentadhere Phase 1, IPD uisjns.)
            "repo_root": str(repo_root),
            # agentadhere Phase 1: the versioned, JSON-safe finding shape and the policy schema
            # version. Replaces the raw (non-JSON-serializable) Drift list in the serialized output.
            # Keyed `policy_findings` (NOT `findings`) because `to_agent_record` reserves the
            # `findings` data key for an integer count.
            "policy_schema_version": ce.POLICY_SCHEMA_VERSION,
            "policy_findings": findings,
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


def _detect_shell() -> str:
    """Detect the active shell from $SHELL for `aw completion` (OQ-01: bash fallback).

    Returns the basename of $SHELL when it is one of bash|zsh|fish, else 'bash' (the POSIX baseline
    when $SHELL is unset, empty, or names an unsupported shell)."""
    raw = os.environ.get("SHELL", "") or ""
    name = os.path.basename(raw).strip()
    return name if name in ("bash", "zsh", "fish") else "bash"


def _run_completion(args: argparse.Namespace, term: Optional[Term] = None) -> int:
    """`aw completion [bash|zsh|fish|install|uninstall]` (bja8og E-03 + jolfpj E-02).

    A shell-name (or omitted) `target` streams the native completion script to stdout - clean stdout
    only (the raw script), so `source <(aw completion bash)` works; bare invocation detects the shell
    from $SHELL (bash fallback, OQ-01). The `install`/`uninstall` verbs are routed ADDITIVELY here
    (jolfpj E-02) on child 01's free-form `target` positional; the script-output path is unchanged."""
    from agent_workflows import completion as _completion

    target = getattr(args, "target", None)
    if target in ("install", "uninstall"):
        return _run_completion_install(args, verb=target, term=term)
    shell = target if target else _detect_shell()
    if shell not in ("bash", "zsh", "fish"):
        print(
            f"agent-workflows: error: unknown completion target {shell!r} "
            "(expected bash|zsh|fish|install|uninstall).",
            file=sys.stderr,
        )
        print("Next  aw completion --help", file=sys.stderr)
        return 2
    sys.stdout.write(_completion.generate(shell))
    return 0


def _run_completion_install(
    args: argparse.Namespace, *, verb: str, term: Optional[Term] = None
) -> int:
    """`aw completion install|uninstall` -> manage the drop-in auto-discovery file (jolfpj E-02).

    Writes/removes ONLY inside the shell's own auto-discovery directory (XDG-first). Never edits a
    user rc/dotfile. Refuses to clobber or delete a completion file this tool did not create
    (sentinel-gated), reporting that as exit 1 rather than silently overwriting someone else's file.
    Exit 0 ok, 1 refusal, 2 usage error."""
    from agent_workflows import completion as _completion

    term = term or Term(color=False if getattr(args, "no_color", False) else None)
    shell = getattr(args, "shell", None) or _detect_shell()
    raw_dir = getattr(args, "completion_dir", None)
    target_dir = Path(raw_dir).expanduser() if raw_dir else None
    dry_run = bool(getattr(args, "dry_run", False))
    prefix = "[dry-run] " if dry_run else ""

    try:
        if verb == "install":
            result = _completion.install_shell_completion(
                shell, target_dir=target_dir, dry_run=dry_run
            )
            for path in result["paths"]:
                term.status("ok", f"{prefix}completion file: {path}")
            term.status(
                "ok",
                f"{prefix}{shell} completion "
                f"{'would be installed' if dry_run else 'installed'} in {result['dir']} "
                "(no rc/dotfile modified).",
            )
            if not dry_run:
                term.line(
                    f"Next  start a new {shell} shell (or run `exec {shell}`) to pick it up."
                )
        else:
            result = _completion.uninstall_shell_completion(
                shell, target_dir=target_dir, dry_run=dry_run
            )
            for path in result["removed"]:
                term.status("ok", f"{prefix}removed: {path}")
            for path in result["skipped"]:
                term.status(
                    "skip",
                    f"{path}: not created by agent-workflows; left untouched.",
                )
            if not result["removed"]:
                term.status(
                    "ok",
                    f"{prefix}no agent-workflows {shell} completion file found in "
                    f"{result['dir']}; nothing to remove.",
                )
    except _completion.CompletionInstallError as exc:
        term.status("fail", str(exc))
        print("Next  aw completion --help", file=sys.stderr)
        return 1
    except OSError as exc:
        term.status("fail", f"{verb} failed: {exc}")
        return 1
    return 0


def _run_dunder_complete(args: argparse.Namespace) -> int:
    """`aw __complete --cword N -- <tokens>` -> newline-delimited candidates, always exit 0 (E-02).

    This is the shell callback child 01's generated scripts invoke to get dynamic, repository-state
    completions. It NEVER raises into the shell: any failure yields no candidates and exit 0. The
    `words` list already has argparse's REMAINDER leading `--` stripped."""
    from agent_workflows import completion as _completion

    words = list(getattr(args, "words", None) or [])
    # argparse REMAINDER keeps the literal `--` separator as the first captured token; drop it so
    # `words` is exactly the completed command line (`["aw", "ipd", "lint", "b"]`).
    if words and words[0] == "--":
        words = words[1:]
    cword = int(getattr(args, "cword", 0) or 0)
    try:
        candidates = _completion.complete_query(words, cword, repo_root=Path.cwd())
    except Exception:
        candidates = []
    if candidates:
        sys.stdout.write("\n".join(candidates) + "\n")
    return 0


def _argcomplete_completer(prefix, parsed_args=None, **_kwargs):
    """A custom argcomplete completer delegating to `completion.complete_query` (E-03).

    argcomplete exposes the full line it is completing via the `COMP_LINE`/`COMP_POINT` environment
    it sets up; we reconstruct the token stream from `COMP_LINE` and defer to the same query engine
    the `__complete` path uses, so argcomplete-driven and script-driven completion agree. Best-effort
    only: any failure yields no suggestions."""
    from agent_workflows import completion as _completion

    try:
        line = os.environ.get("COMP_LINE", "")
        words = line.split()
        if line.endswith(" "):
            words.append("")
        cword = max(len(words) - 1, 0)
        cands = _completion.complete_query(words, cword, repo_root=Path.cwd())
        return [c for c in cands if c.startswith(prefix or "")]
    except Exception:
        return []


def _maybe_argcomplete(parser: argparse.ArgumentParser) -> None:
    """Soft-import argcomplete and, if present, run its completion hook (E-03).

    ZERO hard dependency: `argcomplete` is optional; if it is not installed the import fails and
    normal execution proceeds unchanged. When present, `autocomplete` is a no-op unless argcomplete's
    completion environment is set (i.e. only fires during an actual shell completion request), so
    calling it on every invocation is safe. A custom completer delegating to `complete_query` is
    attached to the artifact/Set positionals so argcomplete offers dynamic candidates too. See the
    `# PYTHON_ARGCOMPLETE_OK` marker + honest-scope note at the top of this module."""
    try:
        import argcomplete  # type: ignore
    except Exception:
        return
    try:
        # Attach the dynamic completer to free-form artifact/Set/target positionals across the tree.
        _attach_argcomplete_completers(parser)
        argcomplete.autocomplete(parser)
    except Exception:
        # Never let an optional enhancement break the real CLI.
        return


def _attach_argcomplete_completers(parser: argparse.ArgumentParser) -> None:
    """Attach `_argcomplete_completer` to positional actions likely to accept an artifact selector,
    Set id, run id, or status token, recursing into subparsers. Best-effort and side-effect-free on
    behavior (argparse ignores an unknown `.completer` attribute)."""
    seen: set = set()

    def walk(p: argparse.ArgumentParser) -> None:
        if id(p) in seen:
            return
        seen.add(id(p))
        for action in p._actions:
            if isinstance(action, argparse._SubParsersAction):
                for sub in action.choices.values():
                    walk(sub)
            elif not action.option_strings:
                # A positional: give it the dynamic completer (argcomplete reads `.completer`).
                action.completer = _argcomplete_completer  # type: ignore[attr-defined]

    walk(parser)


def _dispatch(argv: Optional[Sequence[str]]) -> int:
    parser = _build_parser()
    _maybe_argcomplete(parser)
    # awcmdsurf Order 05 (hard cutover): the `aw plans <verb>` -> `plans-<verb>` alias shim was
    # removed with the plan-family verbs; the grammar is now `aw <verb> plans` (index/find/...).
    # awhelparg Order 01: a bare `help` token becomes `--help` (natural `aw ipd help` UX).
    argv_list = list(sys.argv[1:] if argv is None else argv)
    # awocrunner Order 02 (nfo184): `aw oc runipd ...` / `aw opencode runipd ...` forward the tail
    # VERBATIM to the packaged runner's own parser (incl. its `--help` and implicit-`start` shim), so
    # the top-level parser never intercepts the runner's flags (e.g. a leading `--help`). This is the
    # single mechanism that guarantees exact CLI parity with the standalone script.
    if (
        len(argv_list) >= 2
        and argv_list[0] in ("oc", "opencode")
        and argv_list[1] in ("runipd", "run")
    ):
        from agent_workflows import oc_runipd

        return oc_runipd.main(list(argv_list[2:]))
    if (
        len(argv_list) >= 2
        and argv_list[0] in ("agy", "antigravity")
        and argv_list[1] in ("runipd", "run", "runagy")
    ):
        from agent_workflows import agy_runipd

        return agy_runipd.main(list(argv_list[2:]))
    # runnamecollapse 0soncw E-03: the `--` ESCAPE HATCH for a viewer target that collides with a leaf
    # name (`aw runs -- status` means "view the run/Set called `status`", not "run the `status` leaf").
    # It must be handled here, before `parse_args`, because argparse STRIPS `--` while splitting argv,
    # so by the time the routing action runs the token is indistinguishable from a leaf name (measured:
    # `runs -- status` reached the `status` leaf and failed demanding its required `target`).
    # Set ids are free-form, so this is the documented way to reach a colliding one.
    if len(argv_list) >= 2 and argv_list[0] == "runs" and "--" in argv_list[1:]:
        _sep = argv_list.index("--", 1)
        _forced = [tok for tok in argv_list[_sep + 1 :] if tok != "--"]
        _rest = argv_list[1:_sep]
        args_ns = parser.parse_args(["runs", *_rest])
        # Whatever followed `--` is a TARGET, never a leaf name.
        existing = [t for t in (getattr(args_ns, "targets", None) or []) if t]
        setattr(args_ns, "targets", existing + _forced)
        setattr(args_ns, "runs_command", None)
        from agent_workflows import run_viewer

        return run_viewer.run_viewer_cli(args_ns)
    # `aw runs repair --help` must describe the REPAIR verb, not the read-only inspector. `repair` is
    # routed from `aw runs`' first POSITIONAL token (run_viewer, ssk6nf E-04) so that every read path
    # stays side-effect free, which means argparse never learns it is a verb: it consumed `--help` and
    # printed the generic `runs` help, documenting a read-only command while the user was asking about
    # the one MUTATING verb. Intercept it here, before the parser sees the tail, exactly as the runner
    # forwarding above does for `aw oc runipd --help`.
    if (
        len(argv_list) >= 3
        and argv_list[0] == "runs"
        and argv_list[1] == "repair"
        and any(tok in ("-h", "--help") for tok in argv_list[2:])
    ):
        from agent_workflows import run_viewer

        print(run_viewer.REPAIR_HELP)
        return 0
    # runnernorm Order 02 (puot79): forward `aw agy sessions|view ...` and `aw pwatch ...` VERBATIM
    # to the packaged core's own parser (incl. its `--help`), matching the runipd forwarding above.
    if (
        len(argv_list) >= 2
        and argv_list[0] in ("agy", "antigravity")
        and argv_list[1] in ("sessions",)
    ):
        from agent_workflows import agy_sessions

        return agy_sessions.main(list(argv_list[2:]))
    if (
        len(argv_list) >= 2
        and argv_list[0] in ("agy", "antigravity")
        and argv_list[1] in ("view", "view-antigravity-jsonl")
    ):
        from agent_workflows import agy_view

        return agy_view.main(list(argv_list[2:]))
    # runnernorm follow-up (puot79e04): forward `aw agy exec ...` VERBATIM to the packaged
    # agy_run core's own parser (incl. its `--help`), matching the sessions/view forwarding above.
    if (
        len(argv_list) >= 2
        and argv_list[0] in ("agy", "antigravity")
        and argv_list[1] == "exec"
    ):
        from agent_workflows import agy_run

        return agy_run.main(list(argv_list[2:]))
    if len(argv_list) >= 1 and argv_list[0] == "pwatch":
        from agent_workflows import pwatch

        return pwatch.main(list(argv_list[1:]))
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

    if args.command == "completion":
        return _run_completion(args, term)

    if args.command == "__complete":
        return _run_dunder_complete(args)

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
    if args.command in ("config", "conf"):
        subcmd = getattr(args, "config_command", None)
        if subcmd == "show":
            return _run_config_show(args, term)
        if subcmd == "get":
            return _run_config_get(args, term)
        if subcmd == "set":
            return _run_config_set(args, term)
        if subcmd == "add":
            return _run_config_add(args, term)
        if subcmd in ("remove", "rm"):
            return _run_config_remove(args, term)
        if subcmd == "is":
            return _run_config_is(args, term)
        if subcmd == "exclude":
            return _run_config_exclude(args, term)
        return _show_family_help(parser, "config", "aw config show", term, context)
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
    if args.command == "runs":
        # runnamecollapse 0soncw E-03: `aw runs` carries two shapes. When the routing action matched a
        # LEAF, `runs_command` names it and the ledger handlers own the turn; otherwise it is None and
        # this is the bare viewer. `list` is the viewer under its own name.
        runs_cmd = getattr(args, "runs_command", None)
        if runs_cmd and runs_cmd != "list":
            from agent_workflows import run_cli

            return run_cli.run_cli(args)
        from agent_workflows import run_viewer

        return run_viewer.run_viewer_cli(args)
    if args.command == "set":
        from agent_workflows import status_set

        return status_set.run_set_command(
            args.args,
            scoped_type=None,
            args=args,
            term=term,
        )
    if args.command in ("oc", "opencode"):
        oc_cmd = getattr(args, "oc_command", None)
        if oc_cmd in ("runipd", "run"):
            from agent_workflows import oc_runipd

            # Forward the captured REMAINDER verbatim so the runner's own parser (incl. its
            # implicit-`start` shim and `--help`) drives behavior with exact parity.
            return oc_runipd.main(list(getattr(args, "runipd_args", []) or []))
        # ocsync Order 01 (g7hljt): structured verb, so rebuild argv from the parsed namespace.
        if oc_cmd in ("update-models", "sync-models"):
            from agent_workflows import oc_models

            forwarded = []
            if getattr(args, "config", None):
                forwarded += ["--config", str(args.config)]
            for flag in ("apply", "dry_run", "no_backup", "allow_insecure"):
                if getattr(args, flag, False):
                    forwarded.append("--" + flag.replace("_", "-"))
            return oc_models.run(forwarded)
        return _show_family_help(
            parser,
            "oc",
            "aw oc runipd status <run-id> | aw oc update-models",
            term,
            context,
        )
    if args.command in ("agy", "antigravity"):
        agy_cmd = getattr(args, "agy_command", None)
        if agy_cmd in ("runipd", "run", "runagy"):
            from agent_workflows import agy_runipd

            # Forward the captured REMAINDER verbatim so the runner's own parser (incl. its
            # implicit-`start` shim and `--help`) drives behavior with exact parity.
            return agy_runipd.main(list(getattr(args, "runipd_args", []) or []))
        # runnernorm Order 02 (puot79): graduated agy sessions/view tools.
        if agy_cmd == "sessions":
            from agent_workflows import agy_sessions

            return agy_sessions.main(list(getattr(args, "sessions_args", []) or []))
        if agy_cmd in ("view", "view-antigravity-jsonl"):
            from agent_workflows import agy_view

            return agy_view.main(list(getattr(args, "view_args", []) or []))
        # runnernorm follow-up (puot79e04): graduated single-target multi-mode runner.
        if agy_cmd == "exec":
            from agent_workflows import agy_run

            return agy_run.main(list(getattr(args, "exec_args", []) or []))
        return _show_family_help(
            parser, "agy", "aw agy runipd status <run-id>", term, context
        )
    # runnernorm Order 02 (puot79): top-level `aw pwatch` graduated from tools/pwatch.py.
    if args.command == "pwatch":
        from agent_workflows import pwatch

        return pwatch.main(list(getattr(args, "pwatch_args", []) or []))
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
        if ipd_cmd == "dependencies":
            from agent_workflows import status_set

            dep_cmd = getattr(args, "ipd_dependencies_command", None)
            if dep_cmd == "set":
                return status_set.run_dependencies_set_command(args, term=term)
            return _show_family_help(
                parser,
                "ipd dependencies",
                "aw ipd dependencies set <id6> <edge...>",
                term,
                context,
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
    # agentadhere Phase 2 (IPD 8dto0g): atomic workflow primitives.
    if args.command == "work":
        from agent_workflows import work_cmd

        if getattr(args, "work_command", None) == "begin":
            return work_cmd.run_work_begin(args)
        return _show_family_help(parser, "work", "aw work begin", term, context)
    if args.command == "test":
        from agent_workflows import work_cmd

        return work_cmd.run_test(args)
    if args.command == "commit":
        from agent_workflows import work_cmd

        return work_cmd.run_commit(args)
    if args.command == "finish":
        from agent_workflows import work_cmd

        return work_cmd.run_finish(args)
    if args.command in ("prompt", "prompts"):
        prompt_cmd = getattr(args, "prompts_command", None) or getattr(
            args, "prompt_command", None
        )
        if prompt_cmd == "new":
            from agent_workflows import prompts as prompts_mod

            return prompts_mod.run_new(args)
        if prompt_cmd == "set":
            from agent_workflows import status_set

            return status_set.run_set_command(
                args.args,
                scoped_type="prompts",
                args=args,
                term=term,
            )
        return _show_family_help(
            parser, "prompts", "aw prompts new --slug <slug>", term, context
        )
    if args.command == "research":
        research_cmd = getattr(args, "research_command", None)
        if research_cmd == "new":
            from agent_workflows import research_cmd as rc

            return rc.run_new(args)
        if research_cmd == "new-comparison":
            from agent_workflows import research_cmd as rc

            return rc.run_new_comparison(args)
        if research_cmd in ("set-assign", "mv"):
            from agent_workflows import research_refs as rr
            from agent_workflows.project_context import resolve_verb_repo_root

            # selfcommit jgcm68 E-04: the offer lives HERE at the command-branch call site (NOT
            # inside the shared research_refs backend), so `aw research set-assign`/`mv` fires
            # exactly once and does NOT double-fire with the `aw group/rename research` path (E-07),
            # which reaches the SAME backend from the noun-verb dispatch (PR-012).
            if research_cmd == "set-assign":
                mr = rr.run_set_assign(args)
                _verb = "set-assign"
                _sel = (
                    ",".join(str(i) for i in (getattr(args, "ids", None) or []))
                    or "records"
                )
            else:
                mr = rr.run_mv(args)
                _verb = "mv"
                _sel = str(getattr(args, "id", None) or "records")
            if mr.touched_paths or mr.index_paths:
                repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
                _offer_records_commit(
                    args,
                    repo_root,
                    paths=[*mr.touched_paths, *mr.index_paths],
                    message=f"refactor(research): {_verb} {_sel} and rewrite refs",
                )
            return mr.rc
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
        if research_cmd == "set-priority":
            from agent_workflows import research_cmd as rc

            return rc.run_set_priority(args)
        if research_cmd == "pending":
            from agent_workflows import research_index as ri

            return ri.run_pending(args)
        if research_cmd == "check-miscategorized":
            from agent_workflows import research_archive as ra

            return ra.run_check_miscategorized(args)
        return _show_family_help(parser, "research", "aw research find", term, context)
    if args.command == "reviews":
        reviews_cmd = getattr(args, "reviews_command", None)
        if reviews_cmd == "decisions":
            from agent_workflows import reviews as _reviews

            return _reviews.run_decisions(args)
        return _show_family_help(
            parser, "reviews", "aw reviews decisions", term, context
        )
    if args.command == "host":
        host_cmd = getattr(args, "host_command", None)
        if host_cmd in ("probe", "capabilities"):
            from agent_workflows import host_cmd as _host_cmd

            if host_cmd == "probe":
                return _host_cmd.run_probe(args)
            return _host_cmd.run_capabilities(args)
        return _show_family_help(parser, "host", "aw host capabilities", term, context)
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
    if args.command in ("releases", "release"):
        from agent_workflows import releases as releases_mod

        releases_cmd = getattr(args, "releases_command", None) or getattr(
            args, "release_command", None
        )
        if releases_cmd == "show":
            return releases_mod.run_show(args)
        if releases_cmd == "new":
            return releases_mod.run_new(args)
        # Bare `aw releases` (and explicit `list`) both list: OQ-01 resolved to list, matching
        # `aw backlog`-family conventions, so the family help is NOT shown for a bare invocation.
        return releases_mod.run_list(args)
    if args.command in ("specs", "spec"):
        specs_cmd = getattr(args, "specs_command", None) or getattr(
            args, "spec_command", None
        )
        if specs_cmd in ("new", "scaffold"):
            from agent_workflows import specs as sp

            return sp.run_new(args)
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

    if args.command == "backlog-blocking-close-gate":
        from agent_workflows.hooks import backlog_blocking_close_gate as _bgate

        return _bgate.main([])

    if args.command == "ipd-dependency-statement-gate":
        from agent_workflows.hooks import ipd_dependency_statement_gate as _dgate

        return _dgate.main([])

    if args.command == "precommit-scope-gate":
        from agent_workflows.hooks import precommit_scope_gate as _pcgate

        return _pcgate.main([])

    if args.command == "prepush-authorization-gate":
        from agent_workflows.hooks import prepush_authorization_gate as _ppgate

        return _ppgate.main([])

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
