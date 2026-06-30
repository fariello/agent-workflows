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
  - `release-review/` - the full pre-release review framework.
  - `plan-review/` - the pre-execution plan reviewer.
  - `index.md` - the workflow manifest (the installer reads it to generate shims).
  - `install-workflows.py` / `.sh` - the installer.
- `prompts/` - reusable prompts for AI-assisted development (e.g. `fix-bar.md`, the
  source of the framework's Fix Bar policy).
- `.opencode/commands/`, `.claude/commands/` - generated slash-command shims
  (`/release-review`, `/release-review-plan`, `/plan-review`).
- `AGENTS.md` - a one-line pointer to the workflow index (not the payload).

## Using the workflows in another repository

Run the installer from the target repo root:

```
python3 /path/to/ai-coding/.agents/workflows/install-workflows.py
```

It clean-syncs the workflows into the target's `.agents/workflows/`, generates the
`/release-review`, `/release-review-plan`, and `/plan-review` shims for OpenCode and
Claude Code, adds a one-line pointer to the target's `AGENTS.md`, prunes stale
framework files from a prior version, stages changes with git but does not commit, and
leaves `repository-review/` and your own code untouched. (`--dry-run`, `--force`,
`--no-prune`, `--repo` are available.)

Then run a workflow:

- **OpenCode / Claude Code:** `/release-review` (full), `/release-review-plan` (audit +
  plan only), or `/plan-review <plan-path>` (review a plan before building).
- **Any other agent (universal fallback):** "Read and execute
  `.agents/workflows/release-review/README.md`" (or `plan-review/plan-review.md`), as
  listed in `.agents/workflows/index.md`.

Use `plan-review` before building and `release-review` before shipping. See
`.agents/workflows/release-review/README.md` for the controlling instructions and
`MANIFEST.md` for the file map.

## Understanding this project (start here for context)

This repository practices the durable-knowledge discipline its own framework
prescribes. For a no-context orientation:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why that shape.
- `DECISIONS.md` - the dated log of significant decisions, with alternatives and
  trade-offs (the "why").
