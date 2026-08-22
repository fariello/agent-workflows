# IPD: Verifier Roles Clean Packet Procedures and Corrective Routing

- Date: 2026-08-21
- Kind: child
- Concern: Make independent verification an architectural role with least privilege and fresh evidence, not a second prompt in the executor's conversation.
- Scope: Coordinator/executor/investigator/verifier/corrector/human role contracts + the clean verifier packet (frozen requirements + actual diff + raw evidence, no executor conclusion) + verification procedures + corrective-IPD routing. No concurrency/isolation machinery (Order 09).
- Status: draft
- Set: awoptimize
- Order: 8
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 5hu6bd

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

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

## Project conventions discovered (Step 0)

- TODO: relevant conventions discovered during Step 0.

## Findings

TODO: findings table or notes.

## Proposed changes (ordered, validatable)

TODO: ordered, validatable proposed changes.

## Deferred / out of scope (with reason)

TODO: deferred / out of scope, with reason (or 'none').

## Scope check

- Over-scope: none.
- Under-scope: TODO.

## Required tests / validation

TODO: how the executed plan is verified.

## Spec / documentation sync

TODO: specs/docs to update, or 'N/A with reason'.

## Open questions

### OQ-01: TODO a question

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: TODO.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
