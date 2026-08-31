# agent-workflows

Reusable, installable **agent workflows** for AI coding assistants (OpenCode, Claude
Code, Codex, Cursor, Antigravity, and others). Drop them into any repo and your AI
agent can run a deep pre-release review, review a plan before you build it, set the repo
up with security best practices, or assess one specific concern (security, performance,
accessibility, tests, secrets, etc.) and propose a plan.

The workflows are plain instruction files plus a few small dependency-free Python tools and an installer/CLI, so the
substance works in **any** agent; tools that support native slash commands (OpenCode,
Claude Code) also get `/release-review`, `/assess security`, etc. for free.

> **Direction (2.x, in progress).** A major rewrite, update, and upgrade is under way.
> The goals: broader first-class support across the hosts we use daily (OpenCode, Hermes,
> Codex CLI, Antigravity CLI, and Claude Code); lower token cost to invoke and run
> workflows and tools; higher compliance and rigor (deterministic gates and honest
> validation, so "done" and "tests passed" mean what they say); more consistency and
> formality across commands, documents, and workflows; and more dependable tools for both
> agents and users. Some of this has shipped and some is still landing; see `CHANGELOG.md`
> for what is actually released versus in progress.

---

## Quick start

**1. Install the CLI, then install into your repo.** Requires Python 3.9+ (CI-verified
floor; older 3.x likely works but is untested) and a git repo. Works on Linux, macOS, and
Windows.

```bash
pipx install agent-workflows      # or: pip install agent-workflows
```

This gives you the `aw` command (aliases: `agent-workflows`, `agentwf`). If `aw` is
already used by another tool on your system, use `agentwf` or `agent-workflows`.

Then, from your target repo's root:

```bash
aw install .            # install or update the framework in this repo (idempotent)
```

Or set up many repos at once with the guided wizard, which remembers your repos in a
config file (under `~/.config/agent-workflows/`, never in your home directory root):

```bash
aw setup                # asks where your repos are, discovers them, installs, teaches
aw install all          # later: install or update every configured repo
aw list-repos           # see each repo's installed version and currency
aw attention            # on-demand board of what needs attention across records
aw ipd board            # board of your plan/IPD readiness Status, grouped by lifecycle
aw ipd set approved <id> # transition plan status (or aw set approved <id>)
aw check plans names    # check plan/IPD filenames match convention
```

Re-run `aw install <dir>` any time to UPDATE an installed repo to the current version; it is
idempotent and no-clobber (your own edits are never overwritten), so it doubles as the updater.
There is no separate "update" command.

### Shell Tab Completion

`aw` ships native tab-completion for Bash, Zsh, and Fish with no external dependencies. It
completes commands and flags, plus live repository artifacts (plan/spec/backlog `id6` handles,
Set ids, run ids, and the status words valid for each artifact type).

One command installs it:

```bash
aw completion install          # detects your shell from $SHELL
aw completion install --shell zsh --dry-run   # preview the exact paths first
aw completion uninstall        # remove it again
```

This writes a single drop-in file into the directory your shell already auto-discovers, so it
**never edits `~/.bashrc`, `~/.zshrc`, or `config.fish`**:

| Shell | Drop-in file |
|---|---|
| Bash | `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/aw` |
| Zsh | `${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions/_aw` |
| Fish | `${XDG_CONFIG_HOME:-~/.config}/fish/completions/aw.fish` |

Start a new shell afterwards to pick it up. All three console aliases (`aw`, `agentwf`,
`agent-workflows`) are completed. Installing is idempotent, and it refuses to overwrite an `aw`
completion file it did not write; uninstall removes only its own files.

You can also enable it during install or setup, or print the script and source it directly
without installing anything:

```bash
aw install . --completion auto   # or --completion bash|zsh|fish; default is none
source <(aw completion bash)     # one-off for the current shell only
```

`aw setup` also offers completion with a single confirmation when run interactively. Batch and
`--yes` runs write nothing to your completion directories unless you pass `--completion`.

### The `.aw/` Physical Layout and Four Roots

Fresh installations create the canonical `.aw/` directory structure with four dedicated roots:

1. **System (`.aw/system/`)**: The CLI-owned framework bundle. Invokable workflow bodies and `index.md` live nested at `.aw/system/workflows/`, with sibling framework metadata (`VERSION`, `managed-sections.json`, `templates/`) at `.aw/system/`.
2. **Records (`.aw/records/`)**: Durable project records created during development, including plans/IPDs (`.aw/records/plans/`), specs (`.aw/records/specs/`), research (`.aw/records/research/`), walkthroughs (`.aw/records/walkthroughs/`), roadmaps (`.aw/records/roadmaps/`), backlog items (`.aw/records/backlog/`), inter-agent comms (`.aw/records/comms/`), and prompt templates (`.aw/records/prompts/`, `.aw/records/prompt-library/`).
3. **Config (`.aw/config/`)**: Project policy and configuration. `config.json` and `local-leaks-allowlist.toml` are tracked; local overrides (`local.json`) are gitignored.
4. **State (`.aw/state/`)**: Runtime scratch, cache, and migration transaction logs. Files here are strictly gitignored and never committed.

Host adapters (`.claude/commands/`, `.opencode/commands/`, `AGENTS.md`) remain at the repository root, pointing directly to `.aw/system/workflows/`.

### Placement Presets and Storage Backends

During installation or setup (`aw install --preset <name>` or `aw setup`), choose a preset tailored to your repository's visibility:

| Preset | System Root | Records Backend | Target Repo Git Tracking | Best For |
|---|---|---|---|---|
| `private-target` (default) | `.aw/system/` | `repository` (`.aw/records/`) | Tracked in target git repo | Private repositories where all plans and records can be committed directly. |
| `public-target-private-companion` | `.aw/system/` | `companion` (`<companion>/.aw/records/`) | System tracked in public repo; records tracked in private companion repo | Public open-source repositories requiring private internal planning and security audits. |
| `completely-clean-target` | `.aw/system/` | `home` (`~/.aw/projects/<id>/records/`) | System tracked; records stored locally in user home | Public repositories where no companion repo is desired and records stay local to the machine. |
| `local-only` | `.aw/system/` | `repository` | Entire `.aw/` tree is gitignored | Testing, evaluation, or personal use without committing any workflow files. |

Inspect your active project layout and resolved roots anytime:

```bash
aw context              # inspect active roots, storage backend, and policy
aw path records         # print absolute filesystem path for records root
aw storage status       # check storage backend attachment and durability
```

---

## In-Agent Setup and Workflow Execution

**2. Set the repo up (recommended first run).** In your agent, run the guided setup:

| Your tool | How to run it |
|---|---|
| **OpenCode** or **Claude Code** | type `/setup-repo` |
| **Codex, Cursor, Antigravity, VS Code Copilot, any other agent** | tell the agent: `Read and execute .aw/system/workflows/setup-repo/setup-repo.md` |

`setup-repo` walks you through best practices (secret scanning, `.gitignore`, CI,
pre-commit hooks, the plan/IPD lifecycle, hygiene files), asking before each change,
safe to re-run.

**3. Run any workflow the same way**: a native `/command` (OpenCode / Claude Code) or
"Read and execute `<body path>`" (any other agent). For example, to check for committed
secrets:

```text
/assess secrets                                                                    # OpenCode / Claude Code
Read and execute .aw/system/workflows/assess/assess.md for the concern "secrets"    # any other agent
```

`/assess` takes the concern as its first argument; add a scope after it, e.g.
`/assess performance src/` or `/assess compliance-readiness nist-800-171`. Run bare
`/assess` to list the concerns and be asked which to run.

New here? Run **`/getting-started`** for a guided, in-agent tour: it detects your repo's
state, asks what you are trying to do, and routes you to the right workflow with the exact
command for your tool. `/list-workflows` shows the full catalog.

---

## What you can run

A family of core workflows spanning onboarding (`/getting-started`), discovery (`/spec`),
build/review (`/release-review`, `/release-review-plan`, `/plan-review`, `/plan-review-long`,
`/verify`, `/verify-execution`), performance (`/benchmark`), ship (`/release-notes`), operate
(`/incident`), high-risk change (`/migrate`), setup (`/setup-repo`, `/scaffold`), and discovery
of the toolkit itself (`/list-workflows`), plus two parameterized commands, `/assess <concern>`
(single-concern assessments) and `/advise <persona>` (expert interrogation and coaching).

### CLI output modes (human and agent)

The `aw` CLI serves two audiences from one code path. At an interactive terminal you get a
styled, scannable human view; when stdout is a pipe, a file, or an agent, you get the
`aw.agent/v1` JSONL machine format automatically. As of 2.0.0 this is a HARD CUTOVER: piped
output is machine JSONL, not the old plain text. Override with `--agent` (force machine JSONL),
`--json` (pretty structured), or `--no-color` (human, no ANSI). Exit codes are uniform: `0`
clean, `1` findings, `2` cannot run. See the [Human TTY guide](docs/cli-human-guide.md), the
[Agent protocol reference](docs/cli-agent-protocol.md), the
[migration guide](docs/cli-migration.md), and the normative
[CLI Output Mode Contract](docs/cli-output-contract.md).

### Concise agent reporting

Installing agent-workflows also makes concise, essential-information-only reporting the
default for the AGENT's own prose: lead with the outcome, skip preambles and narration and
recaps, and report only material outcomes, changed files, verification status, and blockers.
It reaches OpenCode, Codex CLI, Claude Code, and Antigravity through the managed
`AGENTS.md#aw:reporting` section, a pointer line in every generated command shim, and both IPD
drivers' worker and verifier prompts. Concision governs REPORTING only: a workflow that
mandates a long report still gets it in full, required evidence is still pasted, and nothing is
truncated. It is a separately owned managed section, so you may decline it or edit it and the
installer will not clobber your version. See the
[concise reporting contract](docs/reporting-contract.md).

### Core workflows

| Command | What it does | Changes code? |
|---|---|---|
| `/setup-repo` | Guided, idempotent setup and conformance check: security scanning, `.gitignore`, CI, pre-commit, plan lifecycle, hygiene files. | Yes, with per-step confirmation |
| `/release-review` | Deep, all-concerns pre-release review of the repo; finds and fixes issues, produces an auditable run record and a GO / NO-GO recommendation. | Yes (the fix-in-place review) |
| `/release-review-plan` | The release review in planning-only mode: audit plus a consolidated implementation plan, stopping before changes. | No |
| `/plan-review` | Review and improve a proposed implementation plan (IPD) **before** any code is written. | No (edits the plan doc) |
| `/plan-review-long` | Same as `/plan-review`, in a multi-file orchestrator form (loads one step at a time to reduce drift on long runs). | No (edits the plan doc) |
| `/verify-execution` | Cross-check that an **executed** plan was actually done: read the diff, check each required change, re-run real validation, and emit a corrective plan for any gap. | No (emits a plan; never fixes in place) |
| `/ipd-lifecycle` | Authoritative gate for **beginning execution** of an approved IPD and its **terminal transition**: runs `aw ipd lint` at pre-execution/pre-transition/post-transition and fails closed. | Executes the approved plan; never approves or tags/releases |
| `/exec-set` | Autonomous IPD **Set** execution: a thin entry point over the deterministic Set coordinator that runs every approved, runnable child with maximal safe parallelism (isolated worktrees + per-path leases), routes each lane to a configured model role, integrates on the combined HEAD, records decisions/deferred questions, and stops only under the exact two-part rule. `--plan-only` inspects without launching. | Executes the approved plans; never approves, pushes, tags, or releases |
| `/scaffold` | Guided creation of a new assessment lens, workflow, or command, wired into the manifest. | Framework files only |
| `/getting-started` | Guided in-agent tour for newcomers: detects your repo/toolkit state, explains the mental model, asks your goal, and routes you to the right workflow. | No (read-only) |
| `/list-workflows` | Toolkit discovery: lists what this toolkit can do and the installed framework version. | No (read-only) |
| `/verify` | Proof, not prose: discovers the repo's own test/lint/build/type-check commands, runs approved checks, and captures real exit codes and logs as committed evidence. | Runs repo checks; writes only an evidence record |
| `/benchmark` | Guided performance benchmarking: captures machine environment (`bench_env.py`), runs benchmark iterations, detects HPC schedulers, and produces shareable results. | Guided; authors `benchmarks/`, writes evidence record |
| `/advise <persona>` | Interrogate and coach: an expert persona (`skeptic`, `spec-editor`, `architect`, `red-teamer`, `staff-engineer`, `domain-expert`, `naive-user`) examines artifact and coaches improvements. | Interactive; edits planning/prose only with consent |
| `/spec` | Front of funnel: turns a fuzzy request into a reviewable specification (goals, non-goals, users, testable acceptance criteria, constraints, open questions). | Guided; writes a spec doc |
| `/incident` | Blameless post-mortem: timeline, impact, systemic contributing factors, and follow-up actions emitted as IPDs. | Guided; writes a post-mortem plus action IPDs |
| `/release-notes` | Decides the version bump from actual changes and drafts changelog plus human release notes. Never publishes, tags, pushes, or deploys. | Guided; updates changelog/version files |
| `/migrate` | Plans a high-risk migration (framework/DB/dependency-major/layout): blast radius, invariants, and a staged, reversible plan with per-stage rollback and verify checks. | No (emits a plan) |

### Assessments (`/assess <concern>`)

`/assess <concern>` assesses **one** concern deeply and writes a dated Implementation
Plan Document (IPD) into `.aw/records/plans/pending/` for your review. It does **not**
change code and does **not** auto-execute. Run bare `/assess` to list the concerns and
be asked which to run.

| Area | Concerns (the `<concern>` value) |
|---|---|
| Correctness & reliability | `bugs` `edge-cases` `reliability` `memory-resources` |
| Security & privacy | `security` `secrets` `privacy` `data-exfiltration` `intrusion-detection` `ransomware-resilience` `threat-model` `logging-audit` |
| Compliance | `compliance` `compliance-readiness` (FIPS / NIST 800-171 / CMMC L2, repo-slice only) |
| UX & docs | `ui-ux` `accessibility` (WCAG 2.1 AA for GUIs + terminal/CLI rubric) `self-documentation` `documentation` `prose` |
| Product & design | `functionality` `use-cases` `architecture` `api-design` `data-modeling` `generalization` |
| Delivery & quality | `testing` `performance` `compatibility` `supply-chain` `guiding-principles` |

Want the whole picture at once? **`/assess-all`** runs the family and synthesizes ONE prioritized,
de-duplicated, cross-concern plan instead of many separate IPDs.

The intended pipeline:

```text
/assess <concern>  ->  IPD in .aw/records/plans/pending/  ->  plan-review (optional)  ->  you approve  ->  execute
```

---

## Layout Migration (`aw migrate-layout`)

If you have an existing repository using the legacy `.agents/` layout, use `aw migrate-layout` to transition safely to the physical `.aw/` hierarchy.

### How Migration Works

1. **Interactive Wizard by Default**: Running `aw migrate-layout` (or `aw migrate-layout wizard`) launches a step-by-step interactive workflow:
   - **Inventory & Plan Preview**: Scans all legacy files, checks for symlinks and uncommitted modifications, and displays a dry-run preview of planned moves.
   - **Backend & Placement Selection**: Choose records storage destination (`repository`, `companion`, or `home`).
   - **Leftover Disposition**: Choose how to handle unclassified legacy files (`keep` in place, `remove` safely, or `defer` to a later cleanup pass).
   - **Confirmation with Preview**: Displays the final move matrix and requires explicit confirmation before modifying any files.
   - **Transactional Execution**: Moves tracked files with `git mv` (preserving git history and staging renames) and untracked files with filesystem moves.
2. **Move, Not Copy**: The engine moves items directly to avoid duplicate installations or split-brain states where both `.agents/` and `.aw/` exist concurrently.
3. **Crash-Safe Journaling and Rollback**: Every move is recorded in a transactional journal under `.aw/state/durable/`. If interrupted, run `aw migrate-layout resume` to complete the transaction or `aw migrate-layout rollback` to restore all files to their original locations.
4. **Non-Interactive Automation**: For CI or scripting, pass `--config <path.json>` or explicit flags (`--target-backend`, `--leftovers`, `--yes`). Non-interactive runs without explicit confirmation fail closed.

### Migration Scenarios

- **Private All-In-Repository**:
  ```bash
  aw migrate-layout --target-backend repository --leftovers defer
  ```
  Moves all plans, specs, research, comms, and prompts to `.aw/records/`. Staged in git; review and commit.
- **Public Repository with Private Companion**:
  ```bash
  aw migrate-layout --target-backend companion --companion-dir /path/to/companion-repo
  ```
  Moves public workflow definitions to `.aw/system/` in the public repository, and moves internal plans, specs, and prompts to `.aw/records/` inside the private companion repository.
- **Clean-Target (Local Records in Home)**:
  ```bash
  aw migrate-layout --target-backend home
  ```
  Moves records to `~/.aw/projects/<project-id>/records/`, keeping the target repository clean of internal planning documents.
- **Interrupted Migration Recovery**:
  ```bash
  aw migrate-layout status     # inspect active transaction journal
  aw migrate-layout resume     # resume interrupted moves to completion
  aw migrate-layout rollback   # or reverse all staged moves back to legacy locations
  ```

---

## Bounded Legacy Compatibility & Deprecation Policy

To support gradual adoption, `agent-workflows` maintains a bounded compatibility window for repositories with legacy `.agents/` layouts:

1. **Automatic Detection**: When `aw install` or `aw setup` runs against a repository with only `.agents/workflows/` present, it detects the legacy structure and interactively offers migration to `.aw/`.
2. **Compatibility Window**: If migration is declined (or when running non-interactively with `--keep-legacy`), the tool updates the legacy `.agents/workflows/` directory in place and prints a one-time deprecation notice.
3. **No Dual-Writer Operation**: The framework will never operate in a mixed state where both `.agents/workflows/` and `.aw/system/workflows/` are written simultaneously. If `.aw/system/` is present, it is strictly authoritative.
4. **Removal Gate**: Legacy `.agents/` support is deprecated and will be removed in major version `3.0.0`. All users are encouraged to run `aw migrate-layout` during the 2.x lifecycle.

---

## What's in this repo

- `.aw/system/` - the framework bundle:
  - `workflows/` - invokable workflow bodies and `index.md` manifest (canonical source).
  - `VERSION` - derived framework version stamped during build.
  - `templates/` - initial templates for plans, prompts, and runbooks.
- `.aw/records/` - project records and durable knowledge:
  - `plans/` - IPDs organized by lifecycle state (`pending/`, `executed/`, `reusable/`, `superseded/`, `not-executed/`).
  - `specs/` - specifications; `research/` - durable research reports (with `INDEX.json`/`INDEX.md`); `walkthroughs/` - narrative walkthroughs; `roadmaps/` - roadmaps.
  - `backlog/` - lightweight committed backlog items (`open/`, `done/`, `parked/`).
  - `comms/` - inter-agent messaging inbox and archives (`shared/`, `untracked/`).
  - `prompts/` - prompt templates and execution records.
- `.aw/config/` - tracked project policy and leak-allowlist configuration.
- `.aw/state/` - local runtime scratch, install logs, and migration journals (never committed).
- `.opencode/commands/`, `.claude/commands/` - generated slash-command shims.
- `AGENTS.md` (and existing `CLAUDE.md`/`GEMINI.md` files) - managed pointer block referencing `.aw/system/workflows/index.md`.

---

## License, Attribution & Citation

`agent-workflows` is licensed under the **Apache License 2.0** (see `LICENSE` and `NOTICE`).

**Attribution (required).** Under Apache-2.0 Section 4(d), any distribution of this software or a
derivative work must retain the `NOTICE` file and display its attribution reasonably
prominently:

> Based on the original agent-workflows by Gabriele Fariello (https://github.com/fariello/agent-workflows).

**Citation.** If you use `agent-workflows` in academic or scholarly work, please cite it. GitHub's
"Cite this repository" button (backed by `CITATION.cff`) provides ready-to-use formats:

> Fariello, Gabriele. *agent-workflows*. 2026. https://github.com/fariello/agent-workflows
