---
name: advise-domain-expert
description: Use when the user asks to advise-domain-expert (Stakeholder proxy: would a real user/buyer want this; does it serve the actual goal; what is missing). Do not use for unrelated requests or when no advise-domain-expert action was requested.
semantic-digest: 76544ce7423e6afd58a05149a31e7d70d644cea46484844f9af7ef0ce4e1277a
---

# Skill: advise-domain-expert

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `76544ce7423e6afd58a05149a31e7d70d644cea46484844f9af7ef0ce4e1277a`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
