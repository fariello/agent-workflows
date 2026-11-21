---
name: exec-set
description: Use when the user asks to exec-set (Autonomous IPD Set execution: a thin entry point over the deterministic Set coordinator that runs every approved, runnable child of a Set with maximal safe parallelism (isolated git worktrees + per-path leases), routes each lane to a configured model role, integrates results through the merge-and-revalidate gate on the combined HEAD, records every autonomous decision/deferred question/skip, and stops the whole Set only when human input is required and neither the affected subgraph nor the IPD can be safely deferred. `/exec-set <set-id> [--plan-only]`; explicit `aw ipd execute-set` is always available. Never approves, pushes, tags, or releases). Do not use for unrelated requests or when no exec-set action was requested.
semantic-digest: 4d0078310759cc07d016d73749845f4faae040b6a90551c6c6302b3112abb5de
---

# Skill: exec-set

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/exec-set/exec-set.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `4d0078310759cc07d016d73749845f4faae040b6a90551c6c6302b3112abb5de`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/exec-set/exec-set.md

## Package resources

- `reference/canonical-body.md` (reference)
