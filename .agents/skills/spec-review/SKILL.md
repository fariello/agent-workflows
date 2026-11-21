---
name: spec-review
description: Use when the user asks to spec-review (Pre-approval SPEC reviewer: review a specification at `to-review`, record typed findings + a verdict, and advance it to `reviewed` via `aw specs set` (that transition now requires the record as its attestation). The spec-time sibling of plan-review, kept a separate body because plan-review's IPD-lint preflight, required `Readiness` write, and E/V rubric each corrupt a spec; findings/verdict/record machinery stays shared. Asks spec questions (testable requirements, covering acceptance criteria, recorded decisions, dispositioned open questions). Never approves: only a human may). Do not use for unrelated requests or when no spec-review action was requested.
semantic-digest: 24025d8c44af44252788eff58e6aa5287921bc9ba580be3b200088c813a25b0f
---

# Skill: spec-review

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/spec-review/spec-review.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `24025d8c44af44252788eff58e6aa5287921bc9ba580be3b200088c813a25b0f`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/spec-review/spec-review.md

## Package resources

- `reference/canonical-body.md` (reference)
