# ai-coding

A collection of resources for coding with AI: prompts, workflows, and tooling for
AI-assisted software development.

The centerpiece is a set of reusable **agent workflows** under `.agents/workflows/`.
The flagship is **`release-review`**, an executable, modular runbook that an AI coding
agent (OpenCode, Claude Code, Antigravity, or another modern agent) follows to perform
a deep pre-release review of *another* repository and leave it materially better, with
a durable, auditable record of what it did and why. Its plan-time sibling
**`plan-review`** reviews a proposed implementation plan before any code is written.

## Contents

- `.agents/workflows/` - the reusable agent workflows (canonical source of truth):
  - `release-review/` - the full, all-concerns pre-release review framework (fixes in
    place).
  - `plan-review/` - the pre-execution plan reviewer (reviews/improves a plan).
  - `setup-repo/` - a guided, wizard-style setup for best practices and security
    (installs tools, adds secret-scanning/CI/hooks/hygiene files; ask-before-each-change).
  - `scaffold/` - a guided, wizard-style creator for new assess lenses / workflows /
    commands (generates from the pattern, wires the manifest, regenerates shims).
  - `assess/` - a family of single-concern assessment workflows that each produce an
    IPD for human approval. Engineering/UX/docs/verification concerns (performance,
    security, accessibility, ui-ux, self-documentation, documentation, functionality,
    use-cases, edge-cases, bugs, reliability, testing, architecture, api-design,
    compatibility, supply-chain, guiding-principles, compliance, memory-resources,
    generalization),
    cybersecurity (data-exfiltration, intrusion-detection, ransomware-resilience,
    threat-model, logging-audit), and a parameterized compliance-readiness lens
    (FIPS / NIST 800-171 / CMMC L2 - repo-slice only, not a certification). A shared
    harness + per-concern lens files.
  - `index.md` - the workflow manifest (the installer reads it to generate shims).
  - `install-workflows.py` / `.sh` - the installer.
- `prompts/` - a reusable prompt library for AI-assisted development, used across the
  maintainer's coding environments and as a home for generated/reusable prompts;
  independent of this repo's workflows (they do not consume it). Includes `fix-bar.md`,
  an origin/source note for the Fix Bar (see `DECISIONS.md` D4); the canonical, enforced
  policy is `.agents/workflows/release-review/fix-decision-policy.md`.
- `.opencode/commands/`, `.claude/commands/` - generated slash-command shims
  (`/release-review`, `/release-review-plan`, `/plan-review`).
- `AGENTS.md` - a one-line pointer to the workflow index (not the payload).

## Using the workflows in another repository

Prerequisites: Python 3.7 or newer, and a git repository as the target. The installer
stages its changes with git but never commits, so review the staged changes and commit
them yourself afterward.

Run the installer from the target repo root:

```
python3 /path/to/ai-coding/.agents/workflows/install-workflows.py
```

It clean-syncs the workflows into the target's `.agents/workflows/`, generates the
slash-command shims (including every `/assess-<concern>`) for OpenCode and Claude
Code, adds a one-line pointer to the target's `AGENTS.md`, prunes stale framework
files from a prior version, migrates a pre-restructure repo (removes the old root
`release-review/` and moves old `repository-review/` run records into
`workflow-artifacts/release-review/`), stages changes with git but does not commit,
and leaves `workflow-artifacts/` and your own code untouched. (`--dry-run`,
`--no-prune`, `--no-backup`, `--repo`, `--source` are available.)

To **update** an existing install, just re-run the installer: framework files are
updated in place (a timestamped backup is written unless `--no-backup`) and staged with
git, never committed. No flag is required.

Run records are written to `workflow-artifacts/<workflow>/<run-id>/` at the repo root
(committed deliverables); assessment IPDs go to the project's pending-plans directory
(default `.agents/plans/pending/`).

### Upgrading a repo that has an older install

If a target repo was set up with an earlier layout (the framework at a root
`release-review/` directory, and/or run records in `repository-review/`), just run the
installer again. It migrates the repo in place and stages (does not commit) the
changes:

- removes the old root `release-review/` directory (the current framework installs
  under `.agents/workflows/`);
- moves old `repository-review/<run-id>/` run records to
  `workflow-artifacts/release-review/<run-id>/` via `git mv`, preserving history;
- regenerates the command shims and refreshes the `AGENTS.md` pointer.

It prints exactly what it migrated. Review the staged changes and commit them (one
commit per repo, e.g. `git commit -m "chore: migrate to .agents/workflows layout"`).
Use `--dry-run` first to preview. The migration only triggers when a legacy layout is
actually present, and never touches your own code; backups are written under
`.agent-workflows-installer-backups/` unless `--no-backup`.

Then run a workflow. How you invoke it depends on your tool (the *substance* works in
any agent; only the native `/command` convenience is tool-specific):

- **OpenCode** (native `/command`, from `.opencode/commands/`): e.g. `/release-review`,
  `/release-review-plan`, `/plan-review <plan-path>`, `/assess-security`, `/setup-repo`.
- **Claude Code** (native `/command`, from `.claude/commands/`): same commands, e.g.
  `/assess-security`. Arguments are supported.
- **Cursor, Codex, Antigravity, VS Code Copilot, or any other agent** (no repo-file
  slash-command mechanism): use the **universal fallback** - tell the agent to *read and
  execute* the workflow body, e.g. "Read and execute
  `.agents/workflows/release-review/README.md`" or "Read and execute
  `.agents/workflows/setup-repo/setup-repo.md`". `.agents/workflows/index.md` lists every
  workflow and its body path, and the root `AGENTS.md` points there for discovery.

See `.agents/workflows/index.md` ("Running a workflow (by tool)") for the full per-tool
table.

For a deep, single-concern pass that proposes a plan instead of fixing in place, use
an `/assess-<concern>` command (e.g. `/assess-security`, `/assess-performance`,
`/assess-accessibility`, `/assess-testing`). Each writes a dated IPD into the
project's pending-plans directory (default `.agents/plans/pending/`) and stops for
human review and approval; it does not auto-execute. The intended pipeline is:

```
assess-<concern>  ->  IPD in pending/  ->  plan-review (optional)  ->  approval  ->  execution
```

Use `assess-<concern>` to investigate one concern and propose a plan, `release-review`
for a broad all-concerns review that fixes in place, `plan-review` before building,
and `release-review` before shipping. See `.agents/workflows/index.md` for the full
command list, `.agents/workflows/release-review/README.md` for the runbook, and its
`MANIFEST.md` for the file map.

Two guided, wizard-style meta-workflows differ from the reviewers (they are interactive
and MAY change files, with per-step confirmation): **`/setup-repo`** walks you through
best-practices/security setup (installing tools, adding secret scanning, CI, hooks, and
hygiene files, idempotently); **`/scaffold`** walks you through adding a new assess
lens, workflow, or command and wiring it in. A good first step in a new repo is
`/setup-repo`.

## Understanding this project (start here for context)

This repository practices the durable-knowledge discipline its own framework
prescribes. For a no-context orientation:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why that shape.
- `DECISIONS.md` - the dated log of significant decisions, with alternatives and
  trade-offs (the "why").
