---
name: assess-reliability
description: Use when the user asks to assess-reliability (Assess reliability/resilience/fault-tolerance and propose an IPD). Do not use for unrelated requests or when no assess-reliability action was requested.
semantic-digest: 6847d647b21c66991e6a74cf686be5c1bfa1dd00d8392916617fc214fcb1f520
---

# Skill: assess-reliability

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `6847d647b21c66991e6a74cf686be5c1bfa1dd00d8392916617fc214fcb1f520`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
