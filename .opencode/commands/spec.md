---
description: Front of funnel: turn a fuzzy request into a reviewable specification (goals, non-goals, users, requirements, testable acceptance criteria, constraints, open questions). Guided/interactive; writes the spec to the repo's convention. Produces the artifact that `/advise spec-editor` interrogates and `plan-review` reviews.
agent: build
---

<!-- Deprecation notice: `/spec` is deprecated; prefer `/aw spec`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/spec/spec.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
