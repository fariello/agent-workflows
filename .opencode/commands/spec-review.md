---
description: Pre-approval SPEC reviewer: review a specification at `to-review`, record typed findings + a verdict, and advance it to `reviewed` via `aw specs set` (that transition now requires the record as its attestation). The spec-time sibling of plan-review, kept a separate body because plan-review's IPD-lint preflight, required `Readiness` write, and E/V rubric each corrupt a spec; findings/verdict/record machinery stays shared. Asks spec questions (testable requirements, covering acceptance criteria, recorded decisions, dispositioned open questions). Never approves: only a human may.
agent: build
---

<!-- Deprecation notice: `/spec-review` is deprecated; prefer `/aw spec-review`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/spec-review/spec-review.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
