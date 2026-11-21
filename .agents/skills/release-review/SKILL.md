---
name: release-review
description: Use when the user asks to release-review (Full pre-release repository review and hardening: deep audit through eight personas, the Fix Bar, fix/validate/report, push and release decisions). Do not use for unrelated requests or when no release-review action was requested.
semantic-digest: d0ca355c2dd254933a694380f7f205c3d9d0d54eb589d856dc0cbf992c9f48c8
---

# Skill: release-review

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/release-review/README.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `d0ca355c2dd254933a694380f7f205c3d9d0d54eb589d856dc0cbf992c9f48c8`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/release-review/README.md

## Package resources

- `reference/canonical-body.md` (reference)
