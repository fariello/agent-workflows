---
name: assess-intrusion-detection
description: Use when the user asks to assess-intrusion-detection (Assess intrusion-detection readiness (security signals, audit-trail detectability) and propose an IPD). Do not use for unrelated requests or when no assess-intrusion-detection action was requested.
semantic-digest: 83809e04f61e35ce954082ed63cc7af9e2d18cc2ff3f6c9bd83484ce8c94f027
---

# Skill: assess-intrusion-detection

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `83809e04f61e35ce954082ed63cc7af9e2d18cc2ff3f6c9bd83484ce8c94f027`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
