---
name: getting-started
description: Use when the user asks to getting-started (Guided in-agent tour and router for newcomers: detect repo/toolkit context, explain the mental model briefly, ask the user's goal, and route to the right workflow (offering to run it with consent) with the exact invocation for their tool. Orients and routes; references `/list-workflows` for the full catalog. Read-only by default). Do not use for unrelated requests or when no getting-started action was requested.
semantic-digest: 7230909b166eb700d72d296b1aa92073aafc4924caa1bdbfb7151f310cf65b4b
---

# Skill: getting-started

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/getting-started/getting-started.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `7230909b166eb700d72d296b1aa92073aafc4924caa1bdbfb7151f310cf65b4b`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/getting-started/getting-started.md

## Package resources

- `reference/canonical-body.md` (reference)
