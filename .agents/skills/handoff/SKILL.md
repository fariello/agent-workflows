---
name: handoff
description: Use when the user asks to handoff (Session-continuity generator: capture this session's ephemeral context (discussion, decisions and their why, abandoned approaches, tacit preferences) into a resume document so a fresh session resumes with continuity. Session context is the core, the on-disk record a thin frame. Writes a `Kind: session-handoff` draft to the gitignored `.aw/records/prompts/untracked/` lane, applies a sensitivity/privacy gate, and never auto-commits (the human promotes). Optional focus argument). Do not use for unrelated requests or when no handoff action was requested.
semantic-digest: 661f6f7b0198a1d2cd5b4d2fb41e2c70ee210b04a01aaf1eee422b760cbab2ed
---

# Skill: handoff

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/handoff/handoff.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `661f6f7b0198a1d2cd5b4d2fb41e2c70ee210b04a01aaf1eee422b760cbab2ed`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/handoff/handoff.md

## Package resources

- `reference/canonical-body.md` (reference)
