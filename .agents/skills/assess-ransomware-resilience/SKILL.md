---
name: assess-ransomware-resilience
description: Use when the user asks to assess-ransomware-resilience (Assess ransomware resilience (immutable/tested backups, blast radius, integrity) and propose an IPD). Do not use for unrelated requests or when no assess-ransomware-resilience action was requested.
semantic-digest: 4259cd222a9b65953435231c84049f2d621bc5c7fcbbacd3ec156f96af326d4a
---

# Skill: assess-ransomware-resilience

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `4259cd222a9b65953435231c84049f2d621bc5c7fcbbacd3ec156f96af326d4a`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
