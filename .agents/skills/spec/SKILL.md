---
name: spec
description: Use when the user asks to spec (Front of funnel: turn a fuzzy request into a reviewable specification (goals, non-goals, users, requirements, testable acceptance criteria, constraints, open questions). Guided/interactive; writes the spec to the repo's convention. Produces the artifact that `/advise spec-editor` interrogates and `spec-review` reviews). Do not use for unrelated requests or when no spec action was requested.
semantic-digest: d189c90b33641d1d748096e646e9c6c05d95838994f2ab6ba26ba5ed61397fc9
---

# Skill: spec

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/spec/spec.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `d189c90b33641d1d748096e646e9c6c05d95838994f2ab6ba26ba5ed61397fc9`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/spec/spec.md

## Package resources

- `reference/canonical-body.md` (reference)
