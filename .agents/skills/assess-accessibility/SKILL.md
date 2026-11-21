---
name: assess-accessibility
description: Use when the user asks to assess-accessibility (Assess accessibility and propose an IPD: WCAG 2.1 AA for graphical UIs, plus a WCAG-inspired rubric for terminal/CLI/TUI output (color never the sole signal, no load-bearing dim/blink, honor NO_COLOR/FORCE_COLOR/TERM/non-TTY, screen-reader-friendly plain mode). Preserves polish via graceful degradation + an opt-out toggle rather than stripping color/spinners; consults interactively before proposing look/feel changes). Do not use for unrelated requests or when no assess-accessibility action was requested.
semantic-digest: d6c020c28c7d486780bb2c1a8c5a71ef11458ec79047d9b898bad32e9b92fb8a
---

# Skill: assess-accessibility

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `d6c020c28c7d486780bb2c1a8c5a71ef11458ec79047d9b898bad32e9b92fb8a`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
