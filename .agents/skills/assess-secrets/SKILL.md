---
name: assess-secrets
description: Use when the user asks to assess-secrets (Scan the working tree and git history for committed secrets/keys/PII/PHI (via tools/scan_secrets.py, read-only, redacted) and propose a rotate-first remediation IPD). Do not use for unrelated requests or when no assess-secrets action was requested.
semantic-digest: 936f23065145505800fa4981a72c12ea306580d2c653c65a2872d77424375e57
---

# Skill: assess-secrets

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `936f23065145505800fa4981a72c12ea306580d2c653c65a2872d77424375e57`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
