# IPD: Park a questioning item non-terminally and keep the queue moving

- Date: 2026-10-17
- Kind: child
- Concern: When a worker returns a valid question (Order 01), the driver has no status for it. The only stop available is a TERMINAL refusal: proposals use `fail-gate` + `needs_input` (`execute_item_core` proposal branch), so the item can never resume in the same run, its dependents are killed by `cascade_dependency_blocked`, and when every remaining item waits on a human the selection loop marks them all `fail-depend` and breaks (spec `6kwd2e` R3.6, the fail-open hazard). Spec R3 requires a NON-terminal `awaiting-human` disposition that keeps the lane, holds dependents, and lets independent work continue.
- Scope: IN: the `awaiting-human` item status (absent from `TERMINAL_STATES` and every success set), recognized by `runner_shutdown.KNOWN_ITEM_STATUSES` and the resume coherence check; setting it when an execute or review turn returns valid questions; preserving the lane with `preserved_lane_id`/`preserved_base`/`preserved_branch`; holding dependents non-terminally (parked, not `fail-depend`); a queue drained only by parked items exiting with the distinct non-failure exit 3 (`run_exit_code`) instead of failing; no `- Readiness: no-go` written for a parked review (R6.1). OUT: writing the inbox (Order 03), consuming answers (Order 04), runaway bounds and the drain ask (Order 08).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/runner_shutdown.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/lifecycle_style.py, agent_workflows/run_evidence.py, agent_workflows/lane_containment.py, tests/test_question_parking.py
- Item-Dependencies: executed:0jooqz
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: epsti7
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let one item wait on a human without ending the run, losing its work, or killing unrelated items (spec `6kwd2e` R3, R6.1, R7.3).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the status

- [ ] E-01 Add `AWAITING_HUMAN_STATUS = "awaiting-human"` in `runner_shared.py`; add it to `runner_shutdown.KNOWN_ITEM_STATUSES` (in-flight/recoverable group) and to `IN_FLIGHT_QUEUE_STATUSES`; keep it OUT of `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `EXECUTION_SUCCESS_STATES` and every `*_REPORTING_SUCCESS_STATES` set (R3.1, R3.3, A32). `lifecycle_style` ALREADY maps `awaiting-human` to `WAITING_INPUT` (both status tables), so confirm the rendered glyph and label rather than adding a mapping; add `"awaiting-human": run_state.STATE_BLOCKED` to `runner_shared.map_driver_status_to_run_state` so the authority check never reports it as an unmapped status (`ST-UNMAPPED-SOURCE`).
  - Depends on: none
  - Expected outcome: `awaiting-human` is a known, non-terminal, non-success status on both hosts, maps to a run state, renders with the waiting-input glyph, and a resumed run holding one passes the ledger coherence check and is NOT re-queued by `requeue_interrupted` (it stays parked).
  - Execution state: pending

### Task group 2: park on a question

- [ ] E-02 EXECUTE turns: in `execute_item_core`, directly after Order 01's intake records `attempt["questions_verdict"]` (`0jooqz` E-06; already filtered to an outcome THIS attempt wrote) and BEFORE the proposal branch, verification, finalize and integration, when it holds at least one valid entry with `gates_verdict: true`: set the item to `awaiting-human`, store the validated questions on the item and attempt (`item["questions"]`), set `needs_input`, add a new reason code `lane_containment.RETENTION_AWAITING_HUMAN = "awaiting-human"` and record the lane with `lane_containment.record_lane_preserved` (which writes `preserved_lane_id`/`preserved_base`/`preserved_branch` through `record_preserved_lane_state`), and return without verification, finalize, integration or teardown. Valid questions with `gates_verdict: false` do NOT park: they are recorded on the attempt and the turn is scored as today, so a non-gating question never holds work back.
  - Depends on: E-01
  - Expected outcome: a scripted execute turn that commits in its lane and returns one gating question ends `awaiting-human` with the lane branch present, its commit absent from main, main's head unchanged, and no verifier or finalize event in `events.jsonl`; the same turn with `gates_verdict: false` is scored and integrated as today.
  - Execution state: pending

- [ ] E-06 REVIEW turns, which all share ONE sweep lane per run (`deferred_review_lane_handle` docstring: "there is exactly ONE sweep lane per run"), so the per-item preservation of E-02 cannot be reused: preserving the sweep lane for one item would stall every later review, and leaving the parked review's commits on it would merge them to main with the NEXT review's integration. In the review branch of `execute_item_core`, BEFORE `commit_review_lane_output` and `integrate_review_lane_branch`, when the attempt carries a valid gating question: (1) commit the review's own dirty paths with `commit_review_lane_output` (the same `own_paths` classification), (2) create `aw/parked/<run_id>/<id6>` at the sweep lane's tip, (3) `git reset --hard` the sweep lane to `attempt["review_lane_tip_before"]`, which removes only this review's commits and keeps every earlier (including integration-deferred) review's commits, (4) record `preserved_branch` = that parked branch, `preserved_base` = `review_lane_tip_before`, `preserved_lane_id` = `parked-<id6>`, and reason code `RETENTION_AWAITING_HUMAN` on the item, and (5) set `awaiting-human`, `needs_input` and `item["questions"]`, skip integration, and write no `- Readiness:` (R6.1). Refuse to park (score `fail-gate` with a recorded refusal, lane untouched) when `review_lane_tip_before` is absent or the lane tip is not a descendant of it, rather than resetting blind. Order 04 (`j0ufrj` E-03) resumes a parked REVIEW from `preserved_branch`.
  - Depends on: E-02
  - Expected outcome: in a scripted run of three reviews where review 2's integration is deferred and review 3 parks with one commit plus a dirty path, review 3's work is on `aw/parked/<run_id>/<id6>`, the sweep lane is clean at `review_lane_tip_before`, a fourth review integrates review 2's and review 4's commits to main, and review 3's change is absent from main.
  - Execution state: pending

- [ ] E-03 Make dependents of an `awaiting-human` item WAIT rather than die: `cascade_dependency_blocked` must treat `awaiting-human` as not-yet-satisfied and non-terminal, so a dependent stays `queued`. This already holds by construction for the cascade (it acts only on statuses in `TERMINAL_STATES`) and for `dependency_status`, which treats a non-success prerequisite as unsatisfied; the work is to pin it in a test and to attach the A7 reason: when a queued item is skipped because a prerequisite is `awaiting-human`, record on it `awaiting_upstream = {<prereq id6>: [question texts]}`, cleared when the prerequisite leaves `awaiting-human`. The dependent is NOT given a parked status of its own (OQ-01).
  - Depends on: E-06
  - Expected outcome: in a fixture A (parks) <- C (depends on A) <- D (depends on C), B (independent): B executes, C and D stay `queued`, C's `awaiting_upstream` names A's question text, nothing is `fail-depend`.
  - Execution state: pending

- [ ] E-04 Fix the drain (R3.6) on BOTH hosts' drain arms (`oc_runipd.run_queue` / `agy_runipd.run_queue`, the `runnable is None` branch). TODAY'S PATH, verified: `classify_drain_block` already returns TRANSIENT for an item whose only unmet prerequisite is non-terminal, and `record_transient_dependency_wait` leaves it `queued`; but `aggregated_run_items` then counts a `queued` item under `stopped=False` as a FAILURE (its clause 6), so the run exits 1, and a parked item's descendants are reported with `TRANSIENT_DEPENDENCY_WAIT_HINT`, which tells the operator to resume rather than to answer. Change: (a) add a shared predicate `waits_on_awaiting_human(item, state)` (true when a prerequisite, transitively, is `awaiting-human`); (b) in the drain arm, for such an item record the wait with a parked-specific hint naming the upstream id6 and `aw runs answer` instead of the generic transient hint; (c) in `aggregated_run_items`, map an `awaiting-human` item to `needs_input=True` (it carries `needs_input` from E-02) and a `queued` item for which `waits_on_awaiting_human` holds to `benign_skip=True`, so a drain caused only by parked questions aggregates to exit 3 (`AGGREGATE_NEEDS_INPUT`) and a genuinely failed sibling still exits per `_CLASSIFICATION_PRIORITY`; (d) print one summary line `N item(s) parked awaiting answers; M waiting on them` with the run directory (the answer-file path itself is Order 08's `answers.md`). Unrelated items keep their own outcomes. Shape the predicate so Order 04 (`j0ufrj` E-01) can call `consume_answers` before the drain decides.
  - Depends on: E-03
  - Expected outcome: a run whose only incomplete items are parked or waiting on a parked item exits 3, prints the parked and waiting counts, and marks no item `fail-depend`; the same run plus one independent `fail-gate` item still exits 3 (needs-input outranks item failure); a run with no parked item is unchanged.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_parking.py` covering spec `6kwd2e` A3, A4, A5, A7, A8, A13, A15, A32, A38 and A39 on BOTH hosts with the scripted-host pattern (`tests/test_run_proposal_channel.py`): a 10-item queue where item 3 parks completes the other 9 (A4); the antigravity path parks with no permission configuration (A39); the same fixture yields the same item statuses and preserved fields on both hosts (A15); the review sweep-lane park of E-06; a non-gating question does not park. A38's answer-file path is asserted by Order 08 (`jshwxb`), which writes `answers.md`; here assert the parked count and the run directory in the summary line.
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
- Reviews share ONE sweep lane per run (`deferred_review_lane_handle`, `acquire_review_sweep_lane`); `refresh_sweep_lane` refuses on a dirty lane, and `attempt["review_lane_tip_before"]` is recorded before every review turn.
- `aggregated_run_items` clause 6 makes a `queued` item under `stopped=False` a failure, and `_CLASSIFICATION_PRIORITY` ranks `AGGREGATE_NEEDS_INPUT` above `AGGREGATE_ITEM_FAILURE`.
- `lifecycle_style` already maps `awaiting-human` to `WAITING_INPUT`; `map_driver_status_to_run_state` has no entry for it.

## Proposed changes (ordered, validatable)

1. E-01 status. 2. E-02 execute park. 3. E-06 review park on the shared sweep lane. 4. E-03 dependents wait with the upstream reason. 5. E-04 drain exit 3. 6. E-05 tests.

## Deferred / out of scope (with reason)

- Writing the inbox and notifying: Orders 03, 06.
  - Carrier: mtmqlm, y1vjzp
- Resuming on an answer: Order 04.
  - Carrier: j0ufrj
- Runaway-escalation bound, drain-time ask and the `answers.md` path of A38: Order 08.
  - Carrier: jshwxb
- Resuming a parked review from its `aw/parked/<run_id>/<id6>` branch, and deleting that branch once the review lands: Order 04.
  - Carrier: j0ufrj

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

### OQ-02: How is a parked REVIEW preserved when every review shares one sweep lane?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED by demonstration (review round 1, D-2): move the parked review's commits to `aw/parked/<run_id>/<id6>` and reset the sweep lane to `review_lane_tip_before` (E-06). A scratch-repository run of the exact git steps showed the sweep lane clean after the park, the parked branch holding the review's commit and its committed leftover, a later review's merge carrying the earlier deferred review's commit to main, and the parked review's change absent from main. Preserving the whole sweep lane was rejected because it would stall every later review in the run; leaving the commits in place was rejected because the next review's integration would merge them.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing `awaiting-human` in `KNOWN_ITEM_STATUSES` and `IN_FLIGHT_QUEUE_STATUSES`, absent from `TERMINAL_STATES` and every success set on both hosts' re-exports, and `map_driver_status_to_run_state("awaiting-human")` returning `blocked`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test output for the parking case and the non-gating case, plus `git rev-parse main` before and after and `git log main..<preserved_branch>` from the fixture (produced by E-02's branch in `execute_item_core`), and the fixture's `events.jsonl` event names showing no verifier or finalize event.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fixture run's final queue statuses showing B executed, C and D queued, C's `awaiting_upstream` naming A's question, and no `fail-depend`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the fixture runs' exit codes (3 for parked-only, 3 for parked plus an independent `fail-gate`) and the summary line naming the parked and waiting counts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the three-review fixture's `git log --oneline main`, `git log --oneline aw/parked/<run_id>/<id6>`, `git -C <sweep lane> status --porcelain` (empty) and `git -C <sweep lane> rev-parse HEAD` equal to the recorded `review_lane_tip_before`, plus the test output for the refuse-to-park case.
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
