# IPD: sample fixture (Set fixture, Order 0)

- Date: 2026-08-03
- Kind: orchestrator
- Concern: TODO.
- Scope: TODO.
- Status: draft
- Set: fixture
- Order: 0
- Highest E allocated: 01
- Author: fixture

## Workflow history

- 2026-08-03 draft (fixture): created.

## Goal

TODO: one or two sentences on what this plan achieves and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: TODO

- [ ] E-01 TODO one observable action.
  - Depends on: none
  - Expected outcome: TODO observable result.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

TODO: child IPD table (Order | File | What it does | Depends on).

## Completion criteria (the whole Set is done only when)

- TODO: whole-Set completion criteria.

## Cross-IPD validation

- TODO: cross-IPD consistency / no-drift / dependency checks.

## Deferred / out of scope (with reason)

TODO: deferred / out of scope, with reason (or 'none').

## Scope check

- Over-scope: none.
- Under-scope: TODO.

## Required tests / validation

TODO: how the executed plan is verified.

## Open questions

### OQ-01: TODO a question

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: TODO.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
