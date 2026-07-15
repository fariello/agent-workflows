# agent-workflows

Reusable, installable **agent workflows** for AI coding assistants (OpenCode, Claude
Code, Codex, Cursor, Antigravity, and others). Drop them into any repo and your AI
agent can run a deep pre-release review, review a plan before you build it, set the repo
up with security best practices, or assess one specific concern (security, performance,
accessibility, tests, secrets, ...) and propose a plan.

The workflows are plain instruction files plus a few small dependency-free Python tools and an installer/CLI, so the
substance works in **any** agent; tools that support native slash commands (OpenCode,
Claude Code) also get `/release-review`, `/assess security`, etc. for free.

---

## Quick start

**1. Install the CLI, then install into your repo.** Requires Python 3.9+ (CI-verified
floor; older 3.x likely works but is untested) and a git repo. Works on Linux, macOS, and
Windows.

```
pipx install agent-workflows      # or: pip install agent-workflows
```

This gives you the `aw` command (aliases: `agent-workflows`, `agentwf`). If `aw` is
already used by another tool on your system, use `agentwf` or `agent-workflows`.

Then, from your target repo's root:

```
aw install .            # install/update the framework into this repo (idempotent)
```

Or set up many repos at once with the guided wizard, which remembers your repos in a
config file (under `~/.config/agent-workflows/`, never in your home directory root):

```
aw setup                # asks where your repos are, discovers them, installs, teaches
aw install all          # later: install/update every configured repo
aw list                 # see each repo's installed version and currency
aw plans                # board of your plan/IPD readiness Status, grouped by lifecycle
aw plan-names           # check plan/IPD filenames match the convention (--apply to fix)
```

Re-run `aw install <dir>` any time to UPDATE an installed repo to the current version; it is
idempotent and no-clobber (your own edits are never overwritten), so it doubles as the updater,
there is no separate "update" command.

`aw plans` reads each plan/IPD's front-matter `Status:` (the readiness vocabulary
`draft -> to-review -> reviewed -> approved`, then the terminal state) and prints a board grouped
by lifecycle directory, with counts. Filter with `--pending` or `--status <s>`; `--write-index`
(re)generates a plain `.agents/plans/STATUS.md` for the no-CLI / GitHub-web view. It reads
front-matter only and never moves or renames a plan.

`aw plan-names` checks that plan/IPD filenames follow the `YYYYMMDD-HHMM-NN-<slug>.md` convention
(local date+time); it is check-only by default and `--apply` performs the staged `git mv` renames.
This surfaces the filename normalizer as a first-class command rather than a buried script.

`aw install` copies the workflows into `.agents/workflows/`, generates slash-command shims
for OpenCode and Claude Code, adds a pointer to your `AGENTS.md` (mirroring it into existing `CLAUDE.md` or `GEMINI.md` files), and scaffolds the
deterministic setup files (plan-lifecycle dirs, a `.gitleaksignore` baseline, a
secret-scan CI workflow, and a short explanatory `README.md` in each `.agents/` directory
so the tree is self-documenting). All are written no-clobber (your own versions are never
overwritten). It **stages** changes with git but never commits and never
touches your code, so review and commit yourself:

```
git status && git commit -m "chore: add agent-workflows"
```

(Preview first with `aw install . --dry-run`; re-run any time to update, it is idempotent;
`aw uninstall .` removes it. Prefer color off? Set `NO_COLOR=1` or pass `--no-color`.)

**Developing agent-workflows itself, or installing without pip?** Clone the repo and run
the installer directly (the deprecated but supported path); an editable install exposes
the same CLI:

```
python3 /path/to/agent-workflows/install-workflows.py    # from your target repo root
# or, for development:
pip install -e /path/to/agent-workflows                  # then use `aw` as above
```

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

New here? Run **`/getting-started`** for a guided, in-agent tour: it detects your repo's
state, asks what you are trying to do, and routes you to the right workflow with the exact
command for your tool. `/list-workflows` shows the full catalog.

---

## What you can run

A family of core workflows - spanning onboarding (`/getting-started`), discovery (`/spec`),
build/review (`/release-review`, `/release-review-plan`, `/plan-review`, `/plan-review-long`,
`/verify`, `/verify-execution`), performance (`/benchmark`), ship (`/release-notes`), operate
(`/incident`), high-risk change (`/migrate`), setup (`/setup-repo`, `/scaffold`), and discovery
of the toolkit itself (`/list-workflows`) - plus two parameterized commands, `/assess <concern>`
(single-concern assessments) and `/advise <persona>` (expert interrogation and coaching). The
table below lists the core workflows and `/advise` (16 rows); `/assess` has its own section after
it. New here? Start with `/getting-started`. Not sure what is
available or which version is installed? Run `/list-workflows`. For any tool without native
slash commands, run the body file shown in the manifest (`.agents/workflows/index.md`) via
"Read and execute ...".

### Core workflows

| Command | What it does | Changes code? |
|---|---|---|
| `/setup-repo` | Guided, idempotent setup + conformance check: security scanning, `.gitignore`, CI, pre-commit, plan lifecycle, hygiene files. | Yes, with per-step confirmation |
| `/release-review` | Deep, all-concerns pre-release review of the repo; finds and fixes issues, produces an auditable run record and a GO / NO-GO recommendation. | Yes (the fix-in-place review) |
| `/release-review-plan` | The release review in planning-only mode: audit + a consolidated implementation plan, stopping before changes. | No |
| `/plan-review` | Review and improve a proposed implementation plan (IPD) **before** any code is written. | No (edits the plan doc) |
| `/plan-review-long` | Same as `/plan-review`, in a multi-file orchestrator form (loads one step at a time to reduce drift on long runs). Currently an experimental parallel variant, kept in parity with `/plan-review`. | No (edits the plan doc) |
| `/verify-execution` | Cross-check that an **executed** plan was actually done: read the diff, check each required change, re-run real validation, and emit a corrective plan for any gap. Useful for checking another agent's work. | No (emits a plan; never fixes in place) |
| `/scaffold` | Guided creation of a new assessment lens, workflow, or command, wired into the manifest. | Framework files only |
| `/getting-started` | Guided in-agent tour for newcomers: detects your repo/toolkit state, explains the mental model, asks your goal, and routes you to the right workflow with the exact command for your tool. Orients and routes; runs nothing without your say-so. | No (read-only) |
| `/list-workflows` | Toolkit discovery: lists what this toolkit can do (core workflows, the `/assess` concerns, personas) and the installed framework version, read from the manifest. Optional filter, e.g. `/list-workflows security`. | No (read-only) |
| `/verify` | Proof, not prose: discovers the repo's own test/lint/build/type-check commands, runs the approved ones (confirm-per-check by default; hard denylist for network/deploy/publish/install), and captures real exit codes, metrics, and logs as committed evidence. `release-review` and `assess` cite it. | Runs repo checks; writes only an evidence record |
| `/benchmark` | Guided performance benchmarking (informational, not a regression gate): authors an isolated `benchmarks/` suite (inert when unused), deeply captures and diagnoses the machine/environment (`bench_env.py`: CPU/RAM/GPU/load/filesystem; flags NFS working sets, powersave governor, swapping, busy or login-node hosts, with suggested remedies), runs with warm-up and at least two iterations, detects HPC schedulers and (on explicit per-submission consent) generates and submits a job script, and produces a shareable, anonymizable results bundle. Read-only on system state; never publishes. | Guided; authors `benchmarks/`, runs it with consent, writes an evidence record |
| `/advise <persona>` | Interrogate and coach: an expert persona (`skeptic`, `spec-editor`, `architect`, `red-teamer`, `staff-engineer`, `domain-expert`, `naive-user`) examines the current context or a named artifact, asks probing questions, and helps you improve it. Bare `/advise` lists personas and asks. | Interactive; edits planning/prose only with consent; never runs code |
| `/spec` | Front of funnel: turns a fuzzy request into a reviewable specification (goals, non-goals, users, testable acceptance criteria, constraints, open questions). Feeds `/advise spec-editor` and `/plan-review`. | Guided; writes a spec doc |
| `/incident` | Blameless post-mortem: timeline, impact, systemic contributing factors, and follow-up actions emitted as IPDs. Repo-scoped (the operator holds the real monitoring/on-call data). | Guided; writes a post-mortem + action IPDs |
| `/release-notes` | Decides the version bump from the actual changes and drafts the changelog + human release notes (breaking changes prominent). Never publishes, tags, pushes, or deploys. | Guided; updates changelog/version files |
| `/migrate` | Plans a high-risk migration (framework/DB/dependency-major/layout): blast radius, invariants that must survive, and a staged, reversible plan with per-stage rollback and verify checks. Emits an IPD. | No (emits a plan) |

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
| UX & docs | `ui-ux` `accessibility` (WCAG 2.1 AA for GUIs + a WCAG-inspired rubric for terminal/CLI/ANSI output) `self-documentation` `documentation` `prose` (writing style across all prose) |
| Product & design | `functionality` `use-cases` `architecture` `api-design` `data-modeling` `generalization` |
| Delivery & quality | `testing` `performance` `compatibility` `supply-chain` `guiding-principles` |

Want the whole picture at once? **`/assess-all`** runs the family (all, a group, or a
subset - it confirms the scope and cost first) and synthesizes ONE prioritized,
de-duplicated, cross-concern plan instead of many separate IPDs. It is the broad
propose-a-plan review; `/release-review` is the broad fix-in-place review.

The intended pipeline:

```
/assess <concern>  ->  IPD in .agents/plans/pending/  ->  plan-review (optional)  ->  you approve  ->  execute
```

Rule of thumb: use `/assess <concern>` to investigate one thing and propose a plan;
`release-review` for a broad review that fixes in place; `plan-review` before you build;
`release-review` again before you ship.

### Coaching (`/advise <persona>`)

Where assess/review find faults and report, `/advise <persona>` is a conversation: an
expert persona examines your artifact (a spec, plan, design, or decision), asks probing
questions, and coaches you to a stronger result. Run bare `/advise` to list personas and
be asked which to use.

| Persona | Voice |
|---|---|
| `skeptic` | The "grill me": assumes it is flawed; interrogates assumptions and unstated risks. |
| `spec-editor` | Turns fuzzy intent into testable, unambiguous requirements. |
| `architect` | Interrogates design trade-offs, coupling, extensibility vs. over-engineering. |
| `red-teamer` | Security/abuse/misuse interrogation from an attacker's viewpoint. |
| `staff-engineer` | Mentors toward the simplest maintainable approach (KISS/YAGNI). |
| `domain-expert` | Stakeholder proxy: would a real user/buyer want this; what is missing. |
| `naive-user` | The uninitiated newcomer: surfaces unclear intent, jargon, and hidden prerequisites. |

It is interactive, edits planning/prose artifacts only with your per-change consent, and
never runs code. Add personas with `/scaffold`.

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

- **Prerequisites:** Python 3.9+ (the versions CI verifies; the tools use only
  stdlib and `from __future__ import annotations`, so older 3.x is expected to work but is
  not tested); a git repo target. The installer stages changes but
  never commits, and never modifies your own code.
- **Options:** `--dry-run` (preview), `--repo <path>` (target another repo),
  `--source <path>` (framework source), `--no-prune` (do not remove stale framework
  files), `--no-backup`, `--version` (print the framework version and exit).
- **Versioning:** the framework uses git-tag-driven semantic versioning (baseline
  `v1.0.0`). The version is DERIVED from the git tag and baked into
  `.agents/workflows/VERSION` (a generated file, not hand-edited); a clean tagged
  checkout reports the tag's semver (example only: `1.2.1`), while an ahead-of-release or
  dirty checkout reports a `X.Y.Z.devN+g<sha>` string so a copy that differs from a release
  can never be mistaken for one. The installer stamps `VERSION` into each target (copied with
  the files) and prints the resolved version in the summary; `/list-workflows` reports the
  installed version. `aw --version` and `scan_secrets.py --version` print it too.
- **Updating:** just re-run the installer. It is idempotent, clean-syncs the framework,
  regenerates shims, and (if it changed anything) reminds you to re-run `/setup-repo` as
  a conformance check.
- **What changed between versions:** `DECISIONS.md` is the dated, append-only log of
  significant changes and their rationale; it doubles as the changelog. Read its most
  recent entries to see what a version added.
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
  - `plan-review/`, `setup-repo/`, `scaffold/`, `getting-started/`, `list-workflows/` -
    the plan reviewer, the two guided wizards, the newcomer tour, and toolkit discovery.
  - `assess/` - the single-concern assessment harness (`assess.md`) + one lens per
    concern under `lenses/`, plus `tools/scan_secrets.py`; `assess-all/` is the
    cross-concern rollup.
  - `advise/` - the interrogate-and-coach harness + persona charters under `personas/`.
  - `verify/` - the evidence layer (`tools/run_checks.py`).
  - `benchmark/` - guided performance benchmarking + the environment-capture tool
    (`tools/bench_env.py`).
  - `setup-repo/` - the guided repo-setup wizard + its tools (`tools/setup_tools.py` for
    tool detection/install, `tools/normalize_plan_names.py` for checking/normalizing plan
    filenames to the `YYYYMMDD-HHMM-NN-<slug>` convention).
  - `spec/`, `incident/`, `release-notes/`, `migrate/` - the lifecycle workflows.
  - `VERSION` - the framework version; `index.md` - the workflow manifest (source of
    truth; the installer reads it).
- `install-workflows.py` / `.sh` - the installer (at the repo root; it is a human-run
  bootstrap tool, distinct from the agent-executed workflows, and installs the framework
  from `.agents/workflows/`).
- `.opencode/commands/`, `.claude/commands/` - generated slash-command shims.
- `AGENTS.md` (and existing `CLAUDE.md`/`GEMINI.md` files) - a managed pointer block to the workflow index.
- `.agents/docs/prompts/` - a historical/reference prompt library (independent of the workflows;
  origin material, see `.agents/docs/prompts/README.md`).

## Understanding this project

This repo practices the durable-knowledge discipline its own framework prescribes:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why.
- `DECISIONS.md` - the dated, append-only log of significant decisions and their
  rationale (this is also the project's changelog).


---

## License, Attribution & Citation

`agent-workflows` is licensed under the **Apache License 2.0** (see `LICENSE` and `NOTICE`).

**Attribution (required).** Under Apache-2.0 §4(d), any distribution of this software or a
derivative work must retain the `NOTICE` file and display its attribution reasonably
prominently. Concretely, derived/redistributed works must include the following, visibly,
in the project README (or equivalent top-level documentation) and in any "About"/credits
screen the software presents:

> Based on the original agent-workflows by Gabriele Fariello (https://github.com/fariello/agent-workflows).

**Citation.** If you use `agent-workflows` in academic or scholarly work, please cite it. GitHub's
"Cite this repository" button (backed by `CITATION.cff`) provides ready-to-use formats. A
suggested citation:

> Fariello, Gabriele. *agent-workflows*. 2026. https://github.com/fariello/agent-workflows

The attribution and citation requests impose no warranty or liability on the author; the
software is provided "AS IS" per the LICENSE.
