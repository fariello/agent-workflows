---
name: plain
description: Use when the user asks to plain (Rewrite your previous message for a capable engineer who has not seen this work: explain each term, tell a failure as the steps that happened, mark an unverified cause as unverified, keep every fact, and send only the rewrite. Use when the user says the message was unclear or asks for the plain version). Do not use for unrelated requests or when no plain action was requested.
semantic-digest: dae7e3c8dd288d10ffab8908bbff7d91bea0c26912bb5a441adb87ba94c1a4ca
---

# Skill: plain

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/plain/plain.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `dae7e3c8dd288d10ffab8908bbff7d91bea0c26912bb5a441adb87ba94c1a4ca`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/plain/plain.md

## Package resources

- `reference/canonical-body.md` (reference)
