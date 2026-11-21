---
name: assess-architecture
description: Use when the user asks to assess-architecture (Assess architecture and extensibility and propose an IPD). Do not use for unrelated requests or when no assess-architecture action was requested.
semantic-digest: 03088b7bfbd99a429d87a5d85e042af48f16d6c4adb1ef58fa6e9f45ff9aa337
---

# Skill: assess-architecture

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `03088b7bfbd99a429d87a5d85e042af48f16d6c4adb1ef58fa6e9f45ff9aa337`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
