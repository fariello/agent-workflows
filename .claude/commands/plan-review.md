---
description: Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). Single-file version.
argument-hint: "[optional target path or flags]"
---

<!-- Deprecation notice: `/plan-review` is deprecated; prefer `/aw plan-review`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/plan-review/plan-review.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
