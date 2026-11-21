---
name: assess-memory-resources
description: Use when the user asks to assess-memory-resources (Assess memory/resource/lifetime/concurrency safety and propose an IPD). Do not use for unrelated requests or when no assess-memory-resources action was requested.
semantic-digest: 2ba112172c3d1965be930e328ad0e9a50a6bf145b5dfe83435c31f3aa56786b3
---

# Skill: assess-memory-resources

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `2ba112172c3d1965be930e328ad0e9a50a6bf145b5dfe83435c31f3aa56786b3`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
