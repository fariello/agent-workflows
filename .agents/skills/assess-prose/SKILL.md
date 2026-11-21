---
name: assess-prose
description: Use when the user asks to assess-prose (Assess prose quality/style across ALL prose (docs, comments/docstrings, UI strings, error/help/CLI text, commit messages) against the distilled nonfiction style guide - quiet force, no mechanical fingerprints, modifier restraint, no em dashes. IPD by default; supports an optional author-in-the-loop interactive mode). Do not use for unrelated requests or when no assess-prose action was requested.
semantic-digest: 79d6106726ff46c8f2e2318123645723a19ff27e7ebe5bb0b9722edd81db0e4d
---

# Skill: assess-prose

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `79d6106726ff46c8f2e2318123645723a19ff27e7ebe5bb0b9722edd81db0e4d`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
