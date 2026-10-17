# IPD: Park a questioning item non-terminally and keep the queue moving

- Date: 2026-10-17
- Kind: child
- Concern: When a worker returns a valid question (Order 01), the driver has no status for it. The only stop available is a TERMINAL refusal: proposals use `fail-gate` + `needs_input` (`execute_item_core` proposal branch), so the item can never resume in the same run, its dependents are killed by `cascade_dependency_blocked`, and when every remaining item waits on a human the selection loop marks them all `fail-depend` and breaks (spec `6kwd2e` R3.6, the fail-open hazard). Spec R3 requires a NON-terminal `awaiting-human` disposition that keeps the lane, holds dependents, and lets independent work continue.
- Scope: IN: the `awaiting-human` item status (absent from `TERMINAL_STATES` and every success set), recognized by `runner_shutdown.KNOWN_ITEM_STATUSES` and the resume coherence check; setting it when an execute or review turn returns valid questions; preserving the lane with `preserved_lane_id`/`preserved_base`/`preserved_branch`; holding dependents non-terminally (parked, not `fail-depend`); a queue drained only by parked items exiting with the distinct non-failure exit 3 (`run_exit_code`) instead of failing; no `- Readiness: no-go` written for a parked review (R6.1). OUT: writing the inbox (Order 03), consuming answers (Order 04), runaway bounds and the drain ask (Order 08).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/runner_shutdown.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/lifecycle_style.py, agent_workflows/run_evidence.py, tests/test_question_parking.py
- Item-Dependencies: executed:0jooqz
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: epsti7

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let one item wait on a human without ending the run, losing its work, or killing unrelated items (spec `6kwd2e` R3, R6.1, R7.3).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the status

- [ ] E-01 Add `AWAITING_HUMAN_STATUS = "awaiting-human"` in `runner_shared.py`; add it to `runner_shutdown.KNOWN_ITEM_STATUSES` (in-flight/recoverable group) and to `IN_FLIGHT_QUEUE_STATUSES`; keep it OUT of `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `EXECUTION_SUCCESS_STATES` and every `*_REPORTING_SUCCESS_STATES` set (R3.1, R3.3, A32). Give it a lifecycle glyph and label in `render_stream`/`lifecycle_style` (the existing `awaiting-human` waiting-input style).
  - Depends on: none
  - Expected outcome: `awaiting-human` is a known, non-terminal, non-success status on both hosts, and a resumed run holding one passes the ledger coherence check.
  - Execution state: pending

### Task group 2: park on a question

- [ ] E-02 In `execute_item_core`, after the outcome is read and BEFORE the proposal branch, when `validate_questions` (Order 01) returns at least one valid entry: set the item to `awaiting-human`, store the validated questions on the item and attempt (`item["questions"]`), set `needs_input`, record the lane as preserved (`lane_containment.record_lane_preserved` with reason code `awaiting-human`, recording `preserved_lane_id`/`preserved_base`/`preserved_branch` as the missing-input path does), skip integration, and write no `- Readiness:` for a review. Applies to execute and review turns alike.
  - Depends on: E-01
  - Expected outcome: a scripted execute turn that commits in its lane and returns one question ends `awaiting-human` with the lane branch present, its commit absent from main, and main's head unchanged.
  - Execution state: pending

- [ ] E-03 Make dependents of an `awaiting-human` item WAIT rather than die: `cascade_dependency_blocked` must treat `awaiting-human` as not-yet-satisfied and non-terminal, so a dependent stays `queued`; the selection loop must skip a `queued` item whose prerequisite is `awaiting-human` (it is not dispatchable) without marking it `fail-depend`.
  - Depends on: E-02
  - Expected outcome: in a fixture A (parks) <- C (depends on A), B (independent): B executes, C stays `queued` with a reason naming A's question, nothing is `fail-depend`.
  - Execution state: pending

- [ ] E-04 Fix the drain (R3.6): when no queued item is dispatchable and every non-terminal remainder is `awaiting-human` or waits on one, end the loop WITHOUT marking anything `fail-depend`, and return the needs-input aggregate from `run_exit_code` (exit 3) with a summary line naming the parked count. Unrelated items keep their own outcomes.
  - Depends on: E-03
  - Expected outcome: a run whose only incomplete items are parked or waiting on a parked item exits 3, prints the parked count, and marks no item `fail-depend`.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_parking.py` covering A3, A4, A5, A7, A8, A13, A32, A38 and A39 on BOTH hosts with the scripted-host pattern (`tests/test_run_proposal_channel.py`): a 10-item queue where item 3 parks completes the other 9 (A4); the antigravity path parks with no permission configuration (A39).
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Item status vocabulary must be admitted by BOTH `TERMINAL_STATES` (or not) and `runner_shutdown.KNOWN_ITEM_STATUSES`, or resume refuses (`TERMINAL_QUEUE_STATUSES` comment in `runner_shared`).
- `needs_input` drives exit 3 through `run_evidence.aggregate_run_exit` (`command_surface` exit-contract comment).
- Lane preservation reuses `lane_containment.record_lane_preserved` and the `preserved_*` fields that `lane_preserved_for_missing_input` established.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- The proposal branch in `execute_item_core` sets `fail-gate` + `needs_input`: terminal, so it is not reusable for parking.
- `cascade_dependency_blocked` kills dependents of any non-success TERMINAL prerequisite; a non-terminal status is left alone by design (`integration-deferred` precedent in the `run_queue` loop comments).
- `IN_FLIGHT_QUEUE_STATUSES` already models recoverable statuses.

## Proposed changes (ordered, validatable)

1. E-01 status. 2. E-02 park. 3. E-03 dependents wait. 4. E-04 drain exit. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Writing the inbox and notifying: Orders 03, 06.
  - Carrier: mtmqlm, y1vjzp
- Resuming on an answer: Order 04.
  - Carrier: j0ufrj
- Runaway-escalation bound and drain-time ask: Order 08.
  - Carrier: jshwxb

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_parking.py tests/test_run_proposal_channel.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R3, R6.1 and R7.3 as written.

## Open questions

### OQ-01: Should a dependent of a parked item be marked parked too (R3.5) or stay queued?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: it stays `queued` and is skipped while its prerequisite is `awaiting-human`. R3.5's intent is that it is not dispatched and not killed; a second parked status for dependents would need its own answer routing and adds nothing, since the dependent has no question of its own. Its rendered reason names the upstream question (A7).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing `awaiting-human` in `KNOWN_ITEM_STATUSES` and `IN_FLIGHT_QUEUE_STATUSES`, and absent from `TERMINAL_STATES` and every success set, on both hosts' re-exports.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test output for the parking case plus `git rev-parse main` before and after and `git log main..aw/lane/<id6>` from the fixture (produced by E-02's branch in `execute_item_core`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fixture run's final queue statuses showing B executed, C queued with the upstream reason, and no `fail-depend`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the fixture run's exit code (3) and summary line naming the parked count.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
