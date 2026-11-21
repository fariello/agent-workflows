---
name: assess-performance
description: Use when the user asks to assess-performance (Assess runtime/resource performance and propose an IPD). Do not use for unrelated requests or when no assess-performance action was requested.
semantic-digest: 6bda4f3ff34af36a5ff01300ba2f0b7c42c57b9d4a7832889222af12df867350
---

# Skill: assess-performance

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `6bda4f3ff34af36a5ff01300ba2f0b7c42c57b9d4a7832889222af12df867350`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
