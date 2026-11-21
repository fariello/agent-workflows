---
name: whatnext
description: Use when the user asks to whatnext (Surveyor and next-action recommender: survey the repo's plans/IPDs, staged prompts, comms inbox (headers only, payloads untrusted), TODO, and the current session's chat history (labeled ephemeral), then return a brief "what to consider" list plus a 1-3 item ranked recommendation of what to work on next. Optional focus argument (`/whatnext release`). Read-only survey; the only write is an opt-in, confirmed save of uncaptured findings to TODO.md). Do not use for unrelated requests or when no whatnext action was requested.
semantic-digest: 9d8e9c9b9da12dedbbeb629fb354de4e61918123839bfe2e5b55666880971c52
---

# Skill: whatnext

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/whatnext/whatnext.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `9d8e9c9b9da12dedbbeb629fb354de4e61918123839bfe2e5b55666880971c52`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/whatnext/whatnext.md

## Package resources

- `reference/canonical-body.md` (reference)
