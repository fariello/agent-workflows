# ai-coding

A collection of resources for coding with AI: prompts, workflows, and tooling for
AI-assisted software development.

The centerpiece is **`release-review/`**, an executable, modular runbook that an AI
coding agent (OpenCode, Antigravity, or another modern agent) follows to perform a
deep pre-release review of *another* repository and leave it materially better, with
a durable, auditable record of what it did and why.

## Contents

- `release-review/` - the release-review framework (canonical source of truth),
  including its installer (`install-release-review-to-opencode.py`).
- `prompts/` - reusable prompts for AI-assisted development (e.g. `fix-bar.md`, the
  source of the framework's Fix Bar policy).
- `.opencode/commands/` - OpenCode slash-command wrappers (`/release-review`,
  `/release-review-plan`).

## Using the release-review framework

In another repository, install it by running
`release-review/install-release-review-to-opencode.py` (it clean-syncs the
`release-review/` directory and the `.opencode/commands/` wrappers from this repo
into the target: it copies current files, prunes stale framework files from a prior
version, stages the changes with git but does not commit, and leaves
`repository-review/` and your own code untouched), or simply copy the
`release-review/` directory in yourself, then tell your agent:

```
Read and execute release-review/README.md
```

With OpenCode, run `/release-review` (full review) or `/release-review-plan` (audit
and plan only). See `release-review/README.md` for the controlling instructions and
`release-review/MANIFEST.md` for the file map.

There is also a **plan-time** sibling reviewer: `/plan-review` (or "read and execute
`release-review/plan-review.md`") reviews and improves a proposed implementation plan
*before any code is written*. It uses the same Fix Bar and personas, discovers the
project's own conventions, and edits planning documents only. Use `plan-review`
before building and `release-review` before shipping.

## Understanding this project (start here for context)

This repository practices the durable-knowledge discipline its own framework
prescribes. For a no-context orientation:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why that shape.
- `DECISIONS.md` - the dated log of significant decisions, with alternatives and
  trade-offs (the "why").
