---
name: incident
description: Use when the user asks to incident (Blameless post-mortem for a production incident: timeline, impact, systemic contributing factors, what went right/wrong, and follow-up actions emitted as IPDs into pending/. Reactive complement to the reliability/logging-audit/intrusion-detection lenses. Repo-scoped and honest about it (operator holds the real monitoring/on-call data)). Do not use for unrelated requests or when no incident action was requested.
semantic-digest: b7aa5908eb829538d4eb1799e9c7f5414c4a282aca0691a99ec6b6716442b65f
---

# Skill: incident

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/incident/incident.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `b7aa5908eb829538d4eb1799e9c7f5414c4a282aca0691a99ec6b6716442b65f`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/incident/incident.md

## Package resources

- `reference/canonical-body.md` (reference)
