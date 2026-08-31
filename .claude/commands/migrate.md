---
description: Assess-and-plan a high-risk migration (framework/DB/dependency-major/layout): inventory the blast radius, name the invariants that must survive, and propose a staged, reversible plan with characterization tests first and per-stage rollback + verify checks. Emits an IPD; does not execute.
argument-hint: "[optional target path or flags]"
---

<!-- Deprecation notice: `/migrate` is deprecated; prefer `/aw migrate`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/migrate/migrate.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
