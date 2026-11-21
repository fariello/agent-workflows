---
name: aw
description: Use when the user invokes the aw slash command or asks to run any repository workflow. Do not use for unrelated requests or when no workflow action was requested.
semantic-digest: 9f388d757067505c00b66cf6897dde545d9d2803262b4bbb0b1f360b2644b05d
---

# Skill: aw

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read the workflow manifest @.aw/system/workflows/index.md.

The first argument names the workflow VERB (e.g. `assess`, `plan-review`, `verify`, `handoff`, `spec`, `whatnext`, `setup-repo`); any remaining arguments are passed through to the resolved workflow. Resolve the verb to its workflow entry in the manifest, then read and execute that workflow's body file. If NO verb was given, consult the manifest or list available workflows below to prompt the user.

- Canonical semantic digest: `9f388d757067505c00b66cf6897dde545d9d2803262b4bbb0b1f360b2644b05d`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/index.md

## Available verbs

- `release-review`
- `release-review-plan`
- `plan-review`
- `plan-review-long`
- `spec-review`
- `verify-execution`
- `ipd-lifecycle`
- `exec-set`
- `getting-started`
- `list-workflows`
- `whatnext`
- `handoff`
- `askme`
- `plain`
- `research`
- `verify`
- `spec`
- `incident`
- `release-notes`
- `migrate`
- `benchmark`
- `setup-repo`
- `scaffold`
- `assess`
- `assess-all`
- `advise`

## Package resources

- `reference/canonical-body.md` (reference)
