---
description: Cross-concern rollup: run the assess family (all, a group, or a subset - confirms scope and cost first) and synthesize ONE prioritized, de-duplicated, cross-concern IPD plus a rollup record, instead of many separate IPDs. The broad propose-a-plan review (release-review is the broad fix-in-place review). Reuses the lenses as the single source of truth.
agent: build
---

<!-- Deprecation notice: `/assess-all` is deprecated; prefer `/aw assess-all`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/assess-all/assess-all.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
