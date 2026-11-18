# IPD: Proposal from ijpay0: Implement backlog item x

- Date: 2026-11-18
- Kind: child
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: draft
- Blocks-Release: next
- Work-Kind: feature
- Priority: high
- Set: prop-ijpay0
- Order: 1
- Highest E allocated: 01
- Author: aw agy run model=Gemini-4-Hydrogen-High
- Id: mbkyv8

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-18 draft (aw agy run model=Gemini-4-Hydrogen-High): created.

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

## Agent Proposal from ijpay0

- Run-Id: run-20261117T053214Z-2141189
- Proposing-Item: ijpay0
- Lane-Branch: aw/lane/ijpay0
- Blocked-By: tests/test_record_builder.py::RecordBuilderRoundTripTests::test_round_trip_prompt FAILED: AssertionError: None != 'research' on st.fields['prompt_kind'] (and st.fields['created_day'] is None)
- Kind: tool-defect
- Size: small

### Why
ijpay0's Approval and execution gate declares that production code under agent_workflows/ and tools/ is out of this plan's purpose and requires stopping to report the missing capability. The defect is already tracked in open backlog item xxdzcq (.aw/records/backlog/open/20261118-xxdzcq-01-xxdzcq-artifact-meta-load-legacy-artifact-drops-prompt-ki.backlog.md).

### Proposed Change
Implement backlog item xxdzcq in agent_workflows/artifact_meta.py::load_legacy_artifact to map 'Kind' -> 'prompt_kind' and 'Created' -> 'created_day' when art_type == 'prompt', then re-run ijpay0.

### Affected Paths
- agent_workflows/artifact_meta.py
