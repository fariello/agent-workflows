---
name: scaffold
description: Use when the user asks to scaffold (Guided, wizard-style creation of a new assess-* lens, standalone workflow, or command: generate from the existing patterns, wire the manifest, and regenerate shims. Authoring/meta workflow). Do not use for unrelated requests or when no scaffold action was requested.
semantic-digest: 798cc0c7e9ae35e835abd55150b6e96fad40d5a613c619c2da96b0afe662422c
---

# Skill: scaffold

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/scaffold/scaffold.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `798cc0c7e9ae35e835abd55150b6e96fad40d5a613c619c2da96b0afe662422c`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/scaffold/scaffold.md

## Package resources

- `reference/canonical-body.md` (reference)
