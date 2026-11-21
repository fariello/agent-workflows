---
name: plan-review-long
description: Use when the user asks to plan-review-long (Same as plan-review, in a multi-file orchestrator form: a small memory-kernel orchestrator that loads one step at a time (discover/snapshot, review/revise, resolve/finalize) with a shared rubric and report template, to reduce directive drift on long runs. Kept in deliberate parity with the single-file plan-review). Do not use for unrelated requests or when no plan-review-long action was requested.
semantic-digest: 40887449a89ae59cccaaf2c4e4f47a11bd5a79c4446f73ca0315f7ca54a139da
---

# Skill: plan-review-long

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/plan-review-long/plan-review-long.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `40887449a89ae59cccaaf2c4e4f47a11bd5a79c4446f73ca0315f7ca54a139da`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/plan-review-long/plan-review-long.md

## Package resources

- `reference/canonical-body.md` (reference)
