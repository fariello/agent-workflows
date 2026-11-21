---
name: assess-logging-audit
description: Use when the user asks to assess-logging-audit (Assess logging and audit-trail quality/integrity/safety and propose an IPD). Do not use for unrelated requests or when no assess-logging-audit action was requested.
semantic-digest: 8afa994d65d52048935e77128de91cee81829fe7f90496fc879b9a67f53279c5
---

# Skill: assess-logging-audit

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `8afa994d65d52048935e77128de91cee81829fe7f90496fc879b9a67f53279c5`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
