# agent-workflows

Reusable, installable **agent workflows** for AI coding assistants (OpenCode, Claude
Code, Codex, Cursor, Antigravity, and others). Drop them into any repo and your AI
agent can run a deep pre-release review, review a plan before you build it, set the repo
up with security best practices, or assess one specific concern (security, performance,
accessibility, tests, secrets, ...) and propose a plan.

The workflows are plain instruction files plus two small Python helpers, so the
substance works in **any** agent; tools that support native slash commands (OpenCode,
Claude Code) also get `/release-review`, `/assess security`, etc. for free.

---

## Quick start

**1. Install into your repo.** Requires Python 3.7+ and a git repo. From your target
repo's root:

```
python3 /path/to/agent-workflows/install-workflows.py
```

This copies the workflows into `.agents/workflows/`, generates slash-command shims for
OpenCode and Claude Code, and adds a pointer to your `AGENTS.md`. It **stages** changes
with git but never commits and never touches your code, so review and commit yourself:

```
git status && git commit -m "chore: add agent-workflows"
```

(Prefer to preview first? Add `--dry-run`. Re-run any time to update; it is idempotent.)

**2. Set the repo up (recommended first run).** In your agent, run the guided setup:

| Your tool | How to run it |
|---|---|
| **OpenCode** or **Claude Code** | type `/setup-repo` |
| **Codex, Cursor, Antigravity, VS Code Copilot, any other agent** | tell the agent: `Read and execute .agents/workflows/setup-repo/setup-repo.md` |

`setup-repo` walks you through best practices (secret scanning, `.gitignore`, CI,
pre-commit hooks, the plan/IPD lifecycle, hygiene files) - asking before each change,
safe to re-run.

**3. Run any workflow the same way** - a native `/command` (OpenCode / Claude Code) or
"Read and execute `<body path>`" (any other agent). For example, to check for committed
secrets:

```
/assess secrets                         # OpenCode / Claude Code
Read and execute .agents/workflows/assess/assess.md for the concern "secrets"  # any other agent
```

`/assess` takes the concern as its first argument; add a scope after it, e.g.
`/assess performance src/` or `/assess compliance-readiness nist-800-171`. Run bare
`/assess` to list the concerns and be asked which to run.

---

## What you can run

Seven core workflows plus one parameterized `/assess <concern>` command covering a family
of single-concern assessments. Not sure what is available or which version is installed?
Run `/list-workflows`. For any tool without native slash commands, run the body file
shown in the manifest (`.agents/workflows/index.md`) via "Read and execute ...".

### Core workflows

| Command | What it does | Changes code? |
|---|---|---|
| `/setup-repo` | Guided, idempotent setup + conformance check: security scanning, `.gitignore`, CI, pre-commit, plan lifecycle, hygiene files. | Yes, with per-step confirmation |
| `/release-review` | Deep, all-concerns pre-release review of the repo; finds and fixes issues, produces an auditable run record and a GO / NO-GO recommendation. | Yes (the fix-in-place review) |
| `/release-review-plan` | The release review in planning-only mode: audit + a consolidated implementation plan, stopping before changes. | No |
| `/plan-review` | Review and improve a proposed implementation plan (IPD) **before** any code is written. | No (edits the plan doc) |
| `/scaffold` | Guided creation of a new assessment lens, workflow, or command, wired into the manifest. | Framework files only |
| `/list-workflows` | Toolkit discovery: lists what this toolkit can do (core workflows, the `/assess` concerns, personas) and the installed framework version, read from the manifest. Optional filter, e.g. `/list-workflows security`. | No (read-only) |
| `/verify` | Proof, not prose: discovers the repo's own test/lint/build/type-check commands, runs the approved ones (confirm-per-check by default; hard denylist for network/deploy/publish/install), and captures real exit codes, metrics, and logs as committed evidence. `release-review` and `assess` cite it. | Runs repo checks; writes only an evidence record |

### Assessments (`/assess <concern>`)

`/assess <concern>` assesses **one** concern deeply and writes a dated Implementation
Plan Document (IPD) into `.agents/plans/pending/` for your review - it does **not**
change code and does **not** auto-execute. Run bare `/assess` to list the concerns and
be asked which to run; concern names are matched case-insensitively with common aliases
(`a11y`->accessibility, `perf`->performance, `deps`/`supply`->supply-chain).

| Area | Concerns (the `<concern>` value) |
|---|---|
| Correctness & reliability | `bugs` `edge-cases` `reliability` `memory-resources` |
| Security & privacy | `security` `secrets` `privacy` `data-exfiltration` `intrusion-detection` `ransomware-resilience` `threat-model` `logging-audit` |
| Compliance | `compliance` `compliance-readiness` (FIPS / NIST 800-171 / CMMC L2 - repo-slice only, not a certification) |
| UX & docs | `ui-ux` `accessibility` (WCAG 2.1 AA) `self-documentation` `documentation` `prose` (writing style across all prose) |
| Product & design | `functionality` `use-cases` `architecture` `api-design` `generalization` |
| Delivery & quality | `testing` `performance` `compatibility` `supply-chain` `guiding-principles` |

The intended pipeline:

```
/assess <concern>  ->  IPD in .agents/plans/pending/  ->  plan-review (optional)  ->  you approve  ->  execute
```

Rule of thumb: use `/assess <concern>` to investigate one thing and propose a plan;
`release-review` for a broad review that fixes in place; `plan-review` before you build;
`release-review` again before you ship.

---

## Running workflows by tool

The workflow *bodies* are tool-agnostic; only the native `/command` convenience is
tool-specific.

| Tool | How to run a workflow |
|---|---|
| **OpenCode** | Native `/command` from `.opencode/commands/`. E.g. `/release-review`, `/assess security`, `/setup-repo`. |
| **Claude Code** | Native `/command` from `.claude/commands/`. Same commands; arguments supported. |
| **Codex, Cursor, Antigravity, VS Code Copilot, any other agent** | No repo-file slash-command mechanism. Use the universal fallback: tell the agent "Read and execute `.agents/workflows/<body path>`". `.agents/workflows/index.md` lists every workflow and its body path; `AGENTS.md` points there so tools that read it can discover them. |

See `.agents/workflows/index.md` ("Running a workflow (by tool)") for the full table and
each workflow's body path.

---

## Install details

- **Prerequisites:** Python 3.7+; a git repo target. The installer stages changes but
  never commits, and never modifies your own code.
- **Options:** `--dry-run` (preview), `--repo <path>` (target another repo),
  `--source <path>` (framework source), `--no-prune` (do not remove stale framework
  files), `--no-backup`, `--version` (print the framework version and exit).
- **Versioning:** the framework carries a version (scheme `YYYYMMDD-NN`) in
  `.agents/workflows/VERSION`. The installer stamps it into each target (copied with the
  files) and prints it in the summary; `/list-workflows` reports the installed version.
  `install-workflows.py --version` and `scan_secrets.py --version` print it too.
- **Updating:** just re-run the installer. It is idempotent, clean-syncs the framework,
  regenerates shims, and (if it changed anything) reminds you to re-run `/setup-repo` as
  a conformance check.
- **Outputs:** run records go to `workflow-artifacts/<workflow>/<run-id>/` at the repo
  root (committed deliverables); assessment IPDs go to `.agents/plans/pending/`.

### Upgrading a repo set up with an older layout

If a repo used an earlier layout (framework at a root `release-review/`, run records in
`repository-review/`), just run the installer again. It migrates in place and stages the
changes: removes the old root `release-review/`, `git mv`s old `repository-review/<run-id>/`
records into `workflow-artifacts/release-review/` (preserving history), and regenerates
shims + the `AGENTS.md` pointer. It prints exactly what it migrated; review and commit.
Use `--dry-run` first. It only triggers when a legacy layout is present and never touches
your code.

---

## What's in this repo

- `.agents/workflows/` - the workflows (canonical source):
  - `release-review/` - the full pre-release review runbook (its `README.md` is the
    controlling instruction; `MANIFEST.md` maps its files).
  - `plan-review/`, `setup-repo/`, `scaffold/` - the plan reviewer and the two guided
    wizards.
  - `assess/` - the single-concern assessment harness (`assess.md`) + one lens per
    concern under `lenses/`, plus `tools/scan_secrets.py`.
  - `index.md` - the workflow manifest (source of truth; the installer reads it).
- `install-workflows.py` / `.sh` - the installer (at the repo root; it is a human-run
  bootstrap tool, distinct from the agent-executed workflows, and installs the framework
  from `.agents/workflows/`).
- `.opencode/commands/`, `.claude/commands/` - generated slash-command shims.
- `AGENTS.md` - a one-line pointer to the workflow index.
- `prompts/` - a reusable prompt library (independent of the workflows).

## Understanding this project

This repo practices the durable-knowledge discipline its own framework prescribes:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why.
- `DECISIONS.md` - the dated, append-only log of significant decisions and their
  rationale (this is also the project's changelog).
