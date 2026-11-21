---
name: verify
description: Use when the user asks to verify (Proof, not prose: discover the repo's own test/lint/build/type-check commands (`run_checks.py`), run the approved ones (confirm-per-check by default, `--yes` for batch; hard denylist for network/deploy/publish/install), and capture real exit codes/metrics/logs as committed evidence. Honest about what could not be verified. Reused by release-review and assess). Do not use for unrelated requests or when no verify action was requested.
semantic-digest: 56e25ded7e997722223b77756074b68e3d463b957a190e3b5b125e8fef35ff62
---

# Skill: verify

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/verify/verify.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `56e25ded7e997722223b77756074b68e3d463b957a190e3b5b125e8fef35ff62`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/verify/verify.md

## Package resources

- `reference/canonical-body.md` (reference)
