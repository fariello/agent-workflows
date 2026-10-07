# IPD: Give fix-it turns for hook refusals and a red suite at finalize and merge

- Date: 2026-10-07
- Kind: child
- Concern: Three refusals the agent can fix fail the item on the first occurrence. (1) A pre-commit hook refusing the finalize commit (`ipd_lifecycle._CommitRefused`, rc 1) matches neither arm of `runner_shared.finalize_refusal_is_retryable`, so it is preserved and reported. (2) A hook refusing an integration commit is recorded as `INTEGRATION_REFUSAL_CONFLICT` and is skipped by the send-back loop because it is not tagged `INTEGRATION_CAUSE_GIT_CONFLICT`. (3) A red combined suite after merging the lane with current main (`INTEGRATION_CAUSE_GATE_COMBINED_RED`) is terminal on the first attempt (`terminal_refusal_verdict`), with only one same-session gate-answer ask when a session exists. The maintainer reports hours lost to exactly these: "this hook is not happy; fix the underlying issue and we'll try again" almost always works.
- Scope: Make each of the three a fix-it send-back under the per-kind budget, carrying the hook's output or the failing tests verbatim through Order 03's message, resuming the turn's session where one exists, and re-running the same gate afterwards. Keep the existing gate-answer exchange as the first step for a red suite (its `not-mine` answer stays meaningful) and send back on `mine`. EXCLUDES transient integration refusals (already on the deferral ladder), conflict markers and lifecycle-duplicate placement (unchanged), and any change to what the hooks check.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, tests/test_hook_and_suite_fix_it.py
- Item-Dependencies: executed:mcbph5
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: w9nvq4

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a hook refuses a commit or the merged suite goes red, the agent is shown exactly what the hook or the tests said and fixes it, and the runner tries again, instead of the item failing until a human notices.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: hook refusal at finalize

- [ ] E-01 Make a hook-refused finalize commit identifiable: have `ipd_lifecycle` surface `_CommitRefused` as a refusal whose summary names the hook refusal and carries the hook's output, then add a third arm to `finalize_refusal_is_retryable` admitting exactly that summary. Route it through `handle_finalize_refusal` with Order 03's message, evidence = the hook output verbatim.
  - Depends on: none
  - Expected outcome: a scratch repo whose pre-commit hook rejects the finalize commit once yields one fix-it turn whose prompt contains the hook's output, then a successful finalize.
  - Execution state: pending

### Task group 2: hook refusal at integration

- [ ] E-02 Tag a hook-refused integration commit (the records re-derive and history auto-resolve commits whose refusal today falls through to `INTEGRATION_REFUSAL_CONFLICT`) with a new cause `INTEGRATION_CAUSE_HOOK_REFUSED`, carrying the hook output, and admit that cause to the same send-back loop that handles `INTEGRATION_CAUSE_GIT_CONFLICT`, resuming the turn's session. The agent fixes the cause in its lane; the runner re-runs integration.
  - Depends on: none
  - Expected outcome: an integration commit rejected once by a hook yields one send-back with the hook output and a successful merge on the retry; a second cause (conflict markers) remains terminal.
  - Execution state: pending

### Task group 3: red suite after merge

- [ ] E-03 For `INTEGRATION_CAUSE_GATE_COMBINED_RED`: keep the gate-answer ask (`gate_answer_is_warranted`) first; on `mine`, or when no session exists to ask, send the lane back with the failing test ids and their output (`extract_suite_failures`) through Order 03's message, then re-run the combined suite. `not-mine` keeps today's handling. `needs-human` routes to Order 02's stop.
  - Depends on: none
  - Expected outcome: a lane whose merged suite fails once yields a send-back listing the failing tests, then a green merge; `not-mine` behavior is unchanged.
  - Execution state: pending

- [ ] E-04 Account each kind against its own budget counter and stop as today when it is exhausted, with the run summary naming which kind ran out.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: with `--retry-budget 1`, a hook that always refuses yields exactly one fix-it turn and then the item fails with a summary naming the hook refusal.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_hook_and_suite_fix_it.py` driving the real runner with a scripted host in a scratch repo with real git hooks for each of E-01 to E-04, asserting on item status, attempt count, the delivered prompt text and git state. No source introspection.
  - Depends on: E-04
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `terminal_refusal_verdict` changes words, never verdicts; a verdict change belongs at the classification sites, which is where this plan acts.
- `classify_integration_refusal` is fail-closed for unknown kinds; the new cause is admitted explicitly.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A hook-refused finalize is not retryable. | `ipd_lifecycle._CommitRefused`; `finalize_refusal_is_retryable` arms 1 and 2 cover only E/V-state findings and stale receipts. |
| F-02 | A hook-refused integration commit is recorded as a conflict and never sent back. | Integration path comment "The commit was refused (a hook, most likely): restore the conflicted state for the ordinary refusal below by aborting"; send-back loop admits only `INTEGRATION_CAUSE_GIT_CONFLICT`. |
| F-03 | A red merged suite is terminal after at most one gate-answer ask, which needs a session. | `terminal_refusal_verdict`; `gate_answer_is_warranted(session_id=...)`. |
| F-04 | Maintainer ruling 2026-10-07: send hook refusals back to the agent to fix the underlying issue. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Finalize hook refusal retryable (E-01).
2. Integration hook refusal retryable (E-02).
3. Red suite sent back (E-03).
4. Budget accounting (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none. `runner_shared.py` E-01 to E-04; `ipd_lifecycle.py` E-01; the test module E-05.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_hook_and_suite_fix_it.py tests/test_production_correction_turn.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: spec `25kzda` 5.5/5.7 are amended by Order 01.

## Open questions

### OQ-01: Should a red suite skip the gate-answer ask and go straight to a send-back?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: Keep the ask first. `not-mine` (a failure already on main) is the case where sending the lane back would waste a turn; the ask costs one short exchange and only runs when a session exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the delivered fix-it prompt containing the hook output, and the item's final status.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the send-back record with cause `INTEGRATION_CAUSE_HOOK_REFUSED`, the delivered prompt, and `git log` on main after the retry.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the send-back prompt listing failing tests and the green re-run; paste a `not-mine` case unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the budget-1 run's attempt count and summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module runs with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
