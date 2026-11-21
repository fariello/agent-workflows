---
name: assess-privacy
description: Use when the user asks to assess-privacy (Assess privacy/data-protection handling and propose an IPD). Do not use for unrelated requests or when no assess-privacy action was requested.
semantic-digest: f169aedba0556608eae8c65f1d666749bab5f10a7b75dd9bc259830841a67c65
---

# Skill: assess-privacy

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `f169aedba0556608eae8c65f1d666749bab5f10a7b75dd9bc259830841a67c65`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
