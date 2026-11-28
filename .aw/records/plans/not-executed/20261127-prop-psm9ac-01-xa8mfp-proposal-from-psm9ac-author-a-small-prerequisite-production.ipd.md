# IPD: Proposal from psm9ac: Author a small prerequisite production-fix child plan ahead

- Date: 2026-11-27
- Kind: child
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: not-executed
- Work-Kind: followup
- Priority: high
- Set: prop-psm9ac
- Order: 1
- Highest E allocated: 01
- Author: aw agy run model=Gemini-4-Neon-High
- Id: xa8mfp

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-28 not-executed (aw set): Fixed directly in metastore-code.cutover.patch (backlog_graduate_legitimacy, check_review_lane_artifacts Plans, chain._EXCLUDED_DIRNAMES 'runs') with tests/test_cutover_log_gradcover_gates.py.
- 2026-11-28 draft (aw agy run model=Gemini-4-Neon-High): created.

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

## Agent Proposal from psm9ac

- Run-Id: run-20261128T005454Z-146130
- Proposing-Item: psm9ac
- Lane-Branch: aw/lane/psm9ac
- Blocked-By: BACKLOG-GRADUATE-LEGITIMACY (agent_workflows/production_checks.py::backlog_graduate_legitimacy rejects op=='set' at history_rows[-1] written in the same append transaction as op=='transition' when --graduated-to is passed) and BACKLOG-INTEGRATION-REFUSED ([aw-integration-cause=artifact-conformance] agent_workflows/runner_shared.py::check_review_lane_artifacts Section 1 calls ipd_lint.parse/lint_text without meta/<id6>.jsonl state or history)
- Kind: tool-defect
- Size: small

### Why
psm9ac is strictly scoped as a test-only conversion batch; its Step 0 rule 5, E-04 stop condition, and Approval and execution gate require stopping and reporting rather than editing production gates inside .aw/system/cutover/metastore-code.cutover.patch (matching prior production-fix splits szykgd, otin36..3e0vfy, ztvubn, and 639g02).

### Proposed Change
Author a small prerequisite production-fix child plan ahead of psm9ac updating .aw/system/cutover/metastore-code.cutover.patch to: (1) make agent_workflows/production_checks.py::backlog_graduate_legitimacy inspect all events in the latest append transaction when verifying op=='transition' to=='graduated'; (2) make agent_workflows/runner_shared.py::check_review_lane_artifacts Section 1 (Plans) load log-backed state and history (from wt_path or branch via artifact_meta) and pass them to ipd_lint.parse and ipd_lint.lint_text; and (3) add 'runs' to agent_workflows/migrations/chain.py::_EXCLUDED_DIRNAMES. Then re-run psm9ac applying the preserved 18-module test conversion patch at .aw/state/lane-submissions/run-20261128T005454Z-146130/01-psm9ac/attempt-1/batch-b-tests-wip.patch.

### Affected Paths
- .aw/system/cutover/metastore-code.cutover.patch
- agent_workflows/production_checks.py
- agent_workflows/runner_shared.py
- agent_workflows/migrations/chain.py
