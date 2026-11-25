# IPD: Proposal from 9o83cr: Cherry-pick or land the prepared commits from branch

- Date: 2026-11-24
- Kind: child
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: superseded
- Blocks-Release: next
- Work-Kind: feature
- Priority: high
- Set: prop-9o83cr
- Order: 1
- Highest E allocated: 01
- Author: aw agy run model=Gemini-4-Neon-High
- Id: rg5i76

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-25 superseded (aw set): Superseded by direct split of rgva3w into Orders 301-304 (wgn3bl, t3t7za, fkvrc7, 75jciz) ahead of 9o83cr
- 2026-11-25 draft (aw agy run model=Gemini-4-Neon-High): created.

## Goal

TODO: one or two sentences on what this plan achieves and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: TODO

- [ ] E-01 TODO one observable action.
  - Depends on: none
  - Expected outcome: TODO observable result.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- TODO: relevant conventions discovered during Step 0.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

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

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

## Agent Proposal from 9o83cr

- Run-Id: run-20261125T031842Z-2538031
- Proposing-Item: 9o83cr
- Lane-Branch: aw/lane/9o83cr_attempt2
- Blocked-By: Plan 9o83cr now depends on executed:rgva3w per maintainer decision OQ-06, and rgva3w (Order 300, status to-review) has not yet landed its flipped dependency on main or been reviewed, approved, and executed.
- Kind: different-approach
- Size: small

### Why
This lane executes only 9o83cr and cannot merge an unexecuted lane to main or execute rgva3w in place.

### Proposed Change
Cherry-pick or land the prepared commits from branch aw/lane/9o83cr_attempt2 (HEAD 3ef9552926dfd415ce3a96c4569769e704df0eeb: tests/test_metadata_single_owner.py, backlog items s9fet0/rzxd1x/iedbnn/avze51, and the flipped dependencies on 9o83cr and rgva3w) onto main under aw integration-lock, sync 63ib9r's child table rows for 9o83cr and rgva3w with a coverage refresh, review/approve/execute rgva3w (which removes the 19 survivors), close s9fet0, and then re-run 9o83cr so V-14 passes cleanly.

### Affected Paths
- tests/test_metadata_single_owner.py
- .aw/records/plans/pending/20261124-metastore-300-rgva3w-delete-surviving-legacy-metadata-parsers-and-writers-found-b.ipd.md
- .aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md
- .aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md
- .aw/records/backlog/open/20261124-s9fet0-01-s9fet0-plan-rgva3w-deadlocks-on-executed-9o83cr-while-9o8.backlog.md
- .aw/records/backlog/open/20261124-rzxd1x-01-rzxd1x-surviving-workflow-history-section-readers-outside.backlog.md
- .aw/records/backlog/open/20261124-iedbnn-01-iedbnn-surviving-aw-prompt-and-aw-managed-prompt-parsers.backlog.md
- .aw/records/backlog/open/20261124-avze51-01-avze51-surviving-scope-paths-bullet-writer-artifact-refs.backlog.md
