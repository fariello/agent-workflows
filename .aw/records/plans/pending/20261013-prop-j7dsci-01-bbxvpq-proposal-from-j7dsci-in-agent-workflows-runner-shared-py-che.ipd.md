# IPD: Proposal from j7dsci: In agent_workflows/runner_shared.py:check_lane_hook_bypass,

- Date: 2026-10-13
- Kind: child
- Concern: TODO.
- Scope: TODO.
- Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
- Item-Dependencies: unresolved
- Status: draft
- Work-Kind: chore
- Priority: low
- Set: prop-j7dsci
- Order: 1
- Highest E allocated: 01
- Author: aw agy run model=Gemini-3.8-Flash-High
- Id: bbxvpq

## Workflow history

- 2026-10-13 draft (aw agy run model=Gemini-3.8-Flash-High): created.

## Goal

TODO: one or two sentences on what this plan achieves and why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: TODO

- [ ] E-01 TODO one observable action.
  - Depends on: none
  - Expected outcome: TODO observable result.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- TODO: relevant conventions discovered during Step 0.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

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

## Agent Proposal from j7dsci

- Run-Id: run-20261013T012222Z-1160687
- Proposing-Item: j7dsci
- Lane-Branch: aw/lane/j7dsci
- Blocked-By: aw ipd executed-transition gate REFUSED this commit (local prevention; the raw plan->executed path bypasses the finalize gates): .aw/records/plans/executed/20260723-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md (qrokie): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/.
- Kind: tool-defect
- Size: small

### Why
check_lane_hook_bypass in runner_shared.py prepares a detached test worktree by checking out head and running git diff --name-only --diff-filter=D base head to find and remove deleted files. Because git diff performs rename detection by default, any rename is classified as R rather than D, leaving proc_diff empty. As a result, the old filename from base is never removed from the disposable worktree while the new filename is added, turning the staged rename into a raw addition (A) into executed/, which triggers the ipd-executed-transition-gate refusal. Fixing this in runner_shared.py requires passing --no-renames to git diff, but editing runner_shared.py is out of scope for IPD j7dsci.

### Proposed Change
In agent_workflows/runner_shared.py:check_lane_hook_bypass, pass --no-renames to git diff: subprocess.run(["git", "diff", "--no-renames", "--name-only", "--diff-filter=D", base, head], ...). In the interim, setting git config diff.renames false in the repository config allows git diff to report the deleted rename source without modifying runner code out of scope.

### Affected Paths
- agent_workflows/runner_shared.py
