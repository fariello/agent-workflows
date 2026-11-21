---
name: assess-compliance-readiness
description: Use when the user asks to assess-compliance-readiness (Assess readiness for a formal regime (FIPS / NIST 800-171 / CMMC L2, parameterized) - repo-slice only, not a certification - and propose an IPD). Do not use for unrelated requests or when no assess-compliance-readiness action was requested.
semantic-digest: 14d79f5febecdc9ddac03d33e296b1fc6274ff570c3b314a4f8d4fb9a3be9f67
---

# Skill: assess-compliance-readiness

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `14d79f5febecdc9ddac03d33e296b1fc6274ff570c3b314a4f8d4fb9a3be9f67`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
