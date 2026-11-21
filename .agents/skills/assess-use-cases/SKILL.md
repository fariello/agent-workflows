---
name: assess-use-cases
description: Use when the user asks to assess-use-cases (Assess use-case/scenario coverage and propose an IPD). Do not use for unrelated requests or when no assess-use-cases action was requested.
semantic-digest: 7d344aeca9d17681ea379f6d5e29827d3002b9f16d0a2b7c7c4c70a4d405cc96
---

# Skill: assess-use-cases

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `7d344aeca9d17681ea379f6d5e29827d3002b9f16d0a2b7c7c4c70a4d405cc96`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
