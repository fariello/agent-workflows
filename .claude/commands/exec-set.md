---
description: Autonomous IPD Set execution: a thin entry point over the deterministic Set coordinator that runs every approved, runnable child of a Set with maximal safe parallelism (isolated git worktrees + per-path leases), routes each lane to a configured model role, integrates results through the merge-and-revalidate gate on the combined HEAD, records every autonomous decision/deferred question/skip, and stops the whole Set only when human input is required and neither the affected subgraph nor the IPD can be safely deferred. `/exec-set <set-id> [--plan-only]`; explicit `aw ipd execute-set` is always available. Never approves, pushes, tags, or releases.
argument-hint: "[treat them as the Set id plus optional flags (`--plan-only`); omit to be prompted for the Set]"
---

<!-- Deprecation notice: `/exec-set` is deprecated; prefer `/aw exec-set`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/exec-set/exec-set.md.

If the user provided arguments, treat them as the Set id plus optional flags (`--plan-only`); omit to be prompted for the Set: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
