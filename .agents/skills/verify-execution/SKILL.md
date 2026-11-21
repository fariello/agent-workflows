---
name: verify-execution
description: Use when the user asks to verify-execution (Post-execution cross-check: verify an EXECUTED plan (IPD) was actually done as written AND in spirit. Runs a 5-dimension Intent & Spirit Audit (explicit requirements, implicit intent, empirical validation, scope, artifacts) against the real diff, MANDATES re-running the repo's real validation with captured output (no un-run "tests pass" claims), and rates execution fidelity (FIDELITY_EXEMPLARY..DIVERGED) mapped onto the verdict. Always writes a run record and EMITS a corrective IPD for any gap (never fixes in place; commits only its own files path-scoped, safe to run while another agent works). Verdict MATCHES/DIVERGES/INCOMPLETE + GO/NO-GO on "truly executed?". Used to cross-check another agent's or a past session's work). Do not use for unrelated requests or when no verify-execution action was requested.
semantic-digest: 231aa855044dd94ef7f5c37f9dad891232986d0560bb308a9fac2eb2412e429f
---

# Skill: verify-execution

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/verify-execution/verify-execution.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `231aa855044dd94ef7f5c37f9dad891232986d0560bb308a9fac2eb2412e429f`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/verify-execution/verify-execution.md

## Package resources

- `reference/canonical-body.md` (reference)
