---
description: Same as plan-review, in a multi-file orchestrator form: a small memory-kernel orchestrator that loads one step at a time (discover/snapshot, review/revise, resolve/finalize) with a shared rubric and report template, to reduce directive drift on long runs. Kept in deliberate parity with the single-file plan-review.
argument-hint: "[optional target path or flags]"
---

<!-- Deprecation notice: `/plan-review-long` is deprecated; prefer `/aw plan-review-long`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/plan-review-long/plan-review-long.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
