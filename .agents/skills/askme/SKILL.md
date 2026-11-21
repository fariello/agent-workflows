---
name: askme
description: Use when the user asks to askme (Ask or rewrite one decision question at a time with plain language and all context needed to answer. Accept a current question, conversational instructions such as "that question again", or project records to examine. Wait for answers and record project decisions. Explicitly noninteractive runs preserve unanswered decisions without guessing). Do not use for unrelated requests or when no askme action was requested.
semantic-digest: bf6f3d42dbb2847005f8a862e8daddff29f427edf3298398c067e35c458248ff
---

# Skill: askme

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/askme/askme.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `bf6f3d42dbb2847005f8a862e8daddff29f427edf3298398c067e35c458248ff`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/askme/askme.md

## Package resources

- `reference/canonical-body.md` (reference)
