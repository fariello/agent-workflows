---
name: advise-spec-editor
description: Use when the user asks to advise-spec-editor (Requirements analyst: turn fuzzy intent into testable, unambiguous requirements; hunt ambiguity and missing acceptance criteria). Do not use for unrelated requests or when no advise-spec-editor action was requested.
semantic-digest: 0cedb43d81bd0fe09edff44322eb607be4eb12a523eb88b1fab59acde88cb3af
---

# Skill: advise-spec-editor

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `0cedb43d81bd0fe09edff44322eb607be4eb12a523eb88b1fab59acde88cb3af`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
