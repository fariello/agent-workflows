# IPD: Proposal from 9gy5jk: Drop E-04(c)/V-04(c) (ke

- Date: 2026-11-17
- Kind: child
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: draft
- Blocks-Release: next
- Work-Kind: feature
- Priority: high
- Set: prop-9gy5jk
- Order: 1
- Highest E allocated: 01
- Author: aw agy run model=Gemini-4-Hydrogen-High
- Id: 6nj7na

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-17 draft (aw agy run model=Gemini-4-Hydrogen-High): created.

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

## Agent Proposal from 9gy5jk

- Run-Id: run-20261117T053214Z-2141189
- Proposing-Item: 9gy5jk
- Lane-Branch: aw/lane/9gy5jk
- Blocked-By: tests/test_artifact_meta_legacy_writer.py::test_research_yaml_front_matter_field_edit (requires op=='set' to insert absent priority/short-description keys) and tests/test_status_set_meta_writer.py::test_w04_research_without_status_gets_one_before_the_closing_fence (requires aw set transition to insert missing status: before closing --- rather than after kind:)
- Kind: different-approach
- Size: small

### Why
Modifying existing executed tests (7yr827, 2xwb9b) outside 9gy5jk's scope is prohibited, and artifact_meta.render_legacy cannot simultaneously satisfy both contracts with identical inputs and defaults.

### Proposed Change
Drop E-04(c)/V-04(c) (keeping E-01's caller-side key filter in research_refs._apply_renames so 7yr827 and h1kfyp set-priority continue to insert priority:), and resolve whether missing status: placement in research_archive.apply_moves uses an opt-in LegacyRender flag (preserving 2xwb9b's test_w04) or adopts one unified placement and updates the conflicting test/plan.

### Affected Paths
- .aw/records/plans/pending/20261109-metastore-129-9gy5jk-move-the-research-refs-move-and-set-assign-field-writers-ont.ipd.md
- agent_workflows/artifact_meta.py
- agent_workflows/research_archive.py
- tests/test_status_set_meta_writer.py
