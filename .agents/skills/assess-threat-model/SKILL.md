---
name: assess-threat-model
description: Use when the user asks to assess-threat-model (Assess overall threat model and defense-in-depth hardening and propose an IPD). Do not use for unrelated requests or when no assess-threat-model action was requested.
semantic-digest: b1cfeed71c197bd12ae5e54de2bdbf0e7e18353017605a3ac09a6e6ddae8c620
---

# Skill: assess-threat-model

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `b1cfeed71c197bd12ae5e54de2bdbf0e7e18353017605a3ac09a6e6ddae8c620`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
