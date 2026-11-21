---
name: assess-self-documentation
description: Use when the user asks to assess-self-documentation (Assess in-product learn-as-you-go clarity and propose an IPD). Do not use for unrelated requests or when no assess-self-documentation action was requested.
semantic-digest: b456e4f018c9569a1bef5bc3fafbd1ab207a66c26b11c9beb6ea89c15941de02
---

# Skill: assess-self-documentation

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `b456e4f018c9569a1bef5bc3fafbd1ab207a66c26b11c9beb6ea89c15941de02`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
