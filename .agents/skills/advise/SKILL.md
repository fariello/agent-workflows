---
name: advise
description: Use when the user asks to advise (Interrogate and coach: an expert persona examines the current context or a named artifact (spec/plan/design/decision), asks probing questions, surfaces gaps and assumptions, and coaches the author. `/advise <persona> [artifact]` (e.g. `/advise skeptic`, `/advise spec-editor plan.md`); bare `/advise` lists personas and asks. Interactive; edits planning/prose only with per-change consent; never runs code. The `advise-<persona>` rows below are the persona catalog, not separate commands). Do not use for unrelated requests or when no advise action was requested.
semantic-digest: 4da08e33c4ae6251176f63a30f5389dc50d21fd4bc16812ca5ceede667eacf44
---

# Skill: advise

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/advise/advise.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `4da08e33c4ae6251176f63a30f5389dc50d21fd4bc16812ca5ceede667eacf44`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/advise/advise.md

## Package resources

- `reference/canonical-body.md` (reference)
