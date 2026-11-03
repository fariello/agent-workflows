# Technical writing standard

agent-workflows ships one writing standard that covers all technical text an agent or a person
produces in a managed repository. That includes backlog items, specifications, plans, research,
prompts, reviews, walkthroughs, documentation, commit messages, code comments, and reports.

The full standard lives in one file:

```text
.aw/system/workflows/technical-writing/technical-writing.md
```

Read it there. This page explains how it is delivered and how it relates to the other rules. It
does not repeat the requirements, so the two texts cannot drift apart.

## How it is delivered

- `aw install` copies the standard into every managed repository, together with the rest of the
  workflow bundle under `.aw/system/workflows/`.
- The managed `AGENTS.md` block that `aw install` writes tells agents to read and follow the
  standard before they create, revise, review, or proofread technical text.
- The spec, spec-review, plan-review, and research-prompt workflows repeat that instruction at the
  point where the writing happens.
- For an external AI that cannot read the repository, attach the file. The standard ends with a
  ready-to-use instruction for that case.

## How it relates to other rules

- **Artifact structure and lifecycle rules** come first. A writing fix never changes scope,
  approval, status, or recorded evidence.
- **The reporting contract** ([reporting-contract.md](reporting-contract.md)) decides what a
  report contains and how long it is. The writing standard decides how its sentences read.
- **Dashes.** The standard adds no dash rule of its own. The agent execution contract in
  `AGENTS.md` still applies: no em or en dashes in user-facing prose, and no effort spent avoiding
  them in internal artifacts.

## Limits

Delivery is deterministic: tests check that the file is installed and that the `AGENTS.md` block
points at it. Whether an agent follows it is not deterministic. A tool can catch mechanical
problems but cannot judge clarity or preserved meaning, so the author and reviewer checks in the
standard remain required.
