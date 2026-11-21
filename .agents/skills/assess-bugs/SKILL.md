---
name: assess-bugs
description: Use when the user asks to assess-bugs (Assess for bugs/correctness defects and propose an IPD). Do not use for unrelated requests or when no assess-bugs action was requested.
semantic-digest: 9e7e09efe8c9e88002c6d455da3f6313ca289589f02e4d22bb376c1b9b13e06d
---

# Skill: assess-bugs

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `9e7e09efe8c9e88002c6d455da3f6313ca289589f02e4d22bb376c1b9b13e06d`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
