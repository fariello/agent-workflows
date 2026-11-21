---
name: assess
description: Use when the user asks to assess (Assess ONE concern deeply and propose an IPD. `/assess <concern> [scope]` (e.g. `/assess security`, `/assess prose src/`); bare `/assess` lists concerns and asks. The `assess-<concern>` rows below are the concern catalog (they define the lenses), not separate commands). Do not use for unrelated requests or when no assess action was requested.
semantic-digest: bfbcf12f52db247bbcd39395108f402f92189dd243bf3d97414559694d124819
---

# Skill: assess

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/assess/assess.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `bfbcf12f52db247bbcd39395108f402f92189dd243bf3d97414559694d124819`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/assess/assess.md

## Package resources

- `reference/canonical-body.md` (reference)
