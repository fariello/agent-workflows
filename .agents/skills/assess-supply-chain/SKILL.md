---
name: assess-supply-chain
description: Use when the user asks to assess-supply-chain (Assess dependencies/licensing/supply-chain and propose an IPD). Do not use for unrelated requests or when no assess-supply-chain action was requested.
semantic-digest: e15f71c6e3b3eacf7d82858402528edd4cf3bcdc2ffb5329547d71f53a22ed8f
---

# Skill: assess-supply-chain

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `e15f71c6e3b3eacf7d82858402528edd4cf3bcdc2ffb5329547d71f53a22ed8f`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
