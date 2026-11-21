---
name: list-workflows
description: Use when the user asks to list-workflows (Toolkit discovery: list what this toolkit can do (core workflows, the `/assess` concerns, any personas) and the installed framework version, read from the manifest. Optional filter argument (`/list-workflows security`, `/list-workflows assess`). Read-only). Do not use for unrelated requests or when no list-workflows action was requested.
semantic-digest: e010046f5dc77a75b0e57a79ed0c1593b942656387f6a4e2ddf165fa0c5e9bba
---

# Skill: list-workflows

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/list-workflows/list-workflows.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `e010046f5dc77a75b0e57a79ed0c1593b942656387f6a4e2ddf165fa0c5e9bba`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/list-workflows/list-workflows.md

## Package resources

- `reference/canonical-body.md` (reference)
