---
name: assess-edge-cases
description: Use when the user asks to assess-edge-cases (Assess edge cases and failure modes and propose an IPD). Do not use for unrelated requests or when no assess-edge-cases action was requested.
semantic-digest: c5f0a7ea9c7bf1a22023dccb54f6f6e52f6b73b0d153f15c90e8d668391040e2
---

# Skill: assess-edge-cases

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `c5f0a7ea9c7bf1a22023dccb54f6f6e52f6b73b0d153f15c90e8d668391040e2`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
