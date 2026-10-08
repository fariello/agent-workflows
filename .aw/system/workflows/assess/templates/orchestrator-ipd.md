# IPD: <short title of the coordinated change>

- Date: <YYYY-MM-DD>
- Kind: orchestrator
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: draft
- Work-Kind: unresolved
- Priority: unresolved
- Set: <set-id>
- Order: 0
- Highest E allocated: 01
- Author: <agent/model>
- Id: tmp1d6

## Workflow history

- <YYYY-MM-DD> draft (<agent/model>): created.

## Goal

TODO: one or two sentences on what this plan achieves and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: TODO

- [ ] E-01 CONFIRM c0ch01 REACHED executed
  - Depends on: none
  - Expected outcome: TODO observable result.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `c0ch01` | TODO child plan filename | TODO what it does. | none |

## Completion criteria (the whole Set is done only when)

- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.

## Cross-IPD validation

- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.

## Deferred / out of scope (with reason)

TODO: deferred / out of scope, with reason (or 'none').

## Scope check

- Over-scope: none.
- Under-scope: TODO.

## Required tests / validation

TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.

## Open questions

### OQ-01: TODO a question

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: TODO.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
