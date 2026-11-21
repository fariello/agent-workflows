---
name: assess-compliance
description: Use when the user asks to assess-compliance (Assess compliance against applicable regimes (parameterized) and propose an IPD). Do not use for unrelated requests or when no assess-compliance action was requested.
semantic-digest: 733512222820ffecafd773511f7e54e82a74a174192da43e443270b5e06dc317
---

# Skill: assess-compliance

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `733512222820ffecafd773511f7e54e82a74a174192da43e443270b5e06dc317`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
