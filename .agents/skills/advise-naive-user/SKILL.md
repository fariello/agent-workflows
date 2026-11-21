---
name: advise-naive-user
description: Use when the user asks to advise-naive-user (The uninitiated newcomer: surface unclear intent, undefined jargon, and unstated prerequisites). Do not use for unrelated requests or when no advise-naive-user action was requested.
semantic-digest: 335a652305f13577115e5d5ed3a64aea42f81fdfbecd10f735dcca18a5ac1a7e
---

# Skill: advise-naive-user

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `335a652305f13577115e5d5ed3a64aea42f81fdfbecd10f735dcca18a5ac1a7e`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
