---
name: assess-security
description: Use when the user asks to assess-security (Assess security posture and propose an IPD). Do not use for unrelated requests or when no assess-security action was requested.
semantic-digest: e62e6913e4e7e1a3c92b037ea753826351ee921958e53a080acc5b4dd7850a83
---

# Skill: assess-security

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `e62e6913e4e7e1a3c92b037ea753826351ee921958e53a080acc5b4dd7850a83`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
