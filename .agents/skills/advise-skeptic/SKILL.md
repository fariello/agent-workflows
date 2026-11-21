---
name: advise-skeptic
description: Use when the user asks to advise-skeptic (The "grill me": assume the artifact is flawed; interrogate assumptions, missing cases, and unstated risks). Do not use for unrelated requests or when no advise-skeptic action was requested.
semantic-digest: 28914da2f3ad179b9ee04bc45d2b24eddff0d57accd63336fe107a4697794d3d
---

# Skill: advise-skeptic

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `28914da2f3ad179b9ee04bc45d2b24eddff0d57accd63336fe107a4697794d3d`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
