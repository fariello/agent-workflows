---
name: assess-all
description: Use when the user asks to assess-all (Cross-concern rollup: run the assess family (all, a group, or a subset - confirms scope and cost first) and synthesize ONE prioritized, de-duplicated, cross-concern IPD plus a rollup record, instead of many separate IPDs. The broad propose-a-plan review (release-review is the broad fix-in-place review). Reuses the lenses as the single source of truth). Do not use for unrelated requests or when no assess-all action was requested.
semantic-digest: df9ae16beb1ddab32e76bb82fd6ca7e7806194c8fbb147a7558938ecd352d993
---

# Skill: assess-all

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess-all/assess-all.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `df9ae16beb1ddab32e76bb82fd6ca7e7806194c8fbb147a7558938ecd352d993`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess-all/assess-all.md

## Package resources

- `reference/canonical-body.md` (reference)
