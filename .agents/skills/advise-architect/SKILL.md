---
name: advise-architect
description: Use when the user asks to advise-architect (Interrogate design trade-offs, coupling, boundaries, and extensibility vs. over-engineering). Do not use for unrelated requests or when no advise-architect action was requested.
semantic-digest: 0810ca43cde3dd6fee452c8df72f406af9b323589c9d745ae2590d9810f96a89
---

# Skill: advise-architect

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `0810ca43cde3dd6fee452c8df72f406af9b323589c9d745ae2590d9810f96a89`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
