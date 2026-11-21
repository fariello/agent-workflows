---
name: release-review-plan
description: Use when the user asks to release-review-plan (Release review in planning-only mode: audit and consolidated implementation plan, stopping before implementation). Do not use for unrelated requests or when no release-review-plan action was requested.
semantic-digest: 7be68ded659477cf7dafad749373fc754bf36e20fd2baa7b758c839c332ff48a
---

# Skill: release-review-plan

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/release-review/README.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `7be68ded659477cf7dafad749373fc754bf36e20fd2baa7b758c839c332ff48a`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/release-review/README.md

## Package resources

- `reference/canonical-body.md` (reference)
