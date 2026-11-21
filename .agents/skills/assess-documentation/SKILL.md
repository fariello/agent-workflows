---
name: assess-documentation
description: Use when the user asks to assess-documentation (Assess repository documentation and propose an IPD). Do not use for unrelated requests or when no assess-documentation action was requested.
semantic-digest: 5ff1d435e72ee26dd18e44802a8c11bfbe627c15fa491d6c00fe6854532cbece
---

# Skill: assess-documentation

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `5ff1d435e72ee26dd18e44802a8c11bfbe627c15fa491d6c00fe6854532cbece`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
