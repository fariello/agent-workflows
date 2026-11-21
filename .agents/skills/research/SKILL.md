---
name: research
description: Use when the user asks to research (Research prompt producer: turns a research topic into a house-conformant, upload-ready research handoff prompt (a `.prompt.md`) staged in `.aw/records/prompts/pending/`). Do not use for unrelated requests or when no research action was requested.
semantic-digest: 18d21a05d32658484f8c8201984e37aa779c880554fd1d5c9c758fdca3e320d6
---

# Skill: research

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/research-prompt/research-prompt.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `18d21a05d32658484f8c8201984e37aa779c880554fd1d5c9c758fdca3e320d6`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/research-prompt/research-prompt.md

## Package resources

- `reference/canonical-body.md` (reference)
