---
name: assess-data-exfiltration
description: Use when the user asks to assess-data-exfiltration (Assess data-exfiltration resistance (egress paths, leakage, DLP-relevant patterns) and propose an IPD). Do not use for unrelated requests or when no assess-data-exfiltration action was requested.
semantic-digest: 5aa9bf55f12e182bd58d85d96d0c93dfdc66542c997cc7f4a93091daf112e9f8
---

# Skill: assess-data-exfiltration

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `5aa9bf55f12e182bd58d85d96d0c93dfdc66542c997cc7f4a93091daf112e9f8`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
