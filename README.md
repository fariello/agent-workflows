# ai-coding

A collection of resources for coding with AI: prompts, workflows, and tooling for
AI-assisted software development.

The centerpiece is **`release-review/`**, an executable, modular runbook that an AI
coding agent (OpenCode, Antigravity, or another modern agent) follows to perform a
deep pre-release review of *another* repository and leave it materially better, with
a durable, auditable record of what it did and why.

## Contents

- `release-review/` - the release-review framework (canonical source of truth).
- `release-review.zip` - distributable bundle of the framework plus its installer
  payload, for dropping into another repository.
- `prompts/` - reusable prompts for AI-assisted development (e.g. `fix-bar.md`, the
  source of the framework's Fix Bar policy).
- `.opencode/commands/` - OpenCode slash-command wrappers (`/release-review`,
  `/release-review-plan`).

## Using the release-review framework

In another repository, either install it from `release-review.zip` with
`release-review/install-release-review-to-opencode.py`, or copy the `release-review/`
directory in and tell your agent:

```
Read and execute release-review/README.md
```

With OpenCode, run `/release-review` (full review) or `/release-review-plan` (audit
and plan only). See `release-review/README.md` for the controlling instructions and
`release-review/MANIFEST.md` for the file map.

## Understanding this project (start here for context)

This repository practices the durable-knowledge discipline its own framework
prescribes. For a no-context orientation:

- `GUIDING_PRINCIPLES.md` - the values guiding the work.
- `ARCHITECTURE.md` - how the framework is structured and why that shape.
- `DECISIONS.md` - the dated log of significant decisions, with alternatives and
  trade-offs (the "why").
