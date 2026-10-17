# IPD: Consume answers at dispatch checkpoints and resume the parked item in the same session

- Date: 2026-10-17
- Kind: child
- Concern: An answer written to `answers/` (Order 03) changes nothing until the driver reads it. Spec `6kwd2e` R9.3-R9.4 (amended 2026-10-17) require the live driver to consume answers at every dispatch checkpoint, re-queue the answered item AHEAD of not-yet-started work, and resume the SAME agent session with the answer, falling back to a fresh turn on the same preserved lane; R5.6 requires a stale answer (artifact changed since the question) to be refused, not applied.
- Scope: IN: a checkpoint step at the top of both drivers' `run_queue` loops (beside `runner_stop.poll_stop`, the dependency cascade and the deferred-integration retry); staleness check; priority re-queue; same-session resume through `resume_via_launcher` with an answer notice built like `build_fix_it_notice`; fresh-turn fallback on the preserved lane with the answer in the prompt (R5.5); start-of-run and resume drain so answers written while no driver was live are consumed; marking a consumed question `answered` in the inbox and refreshing `open-questions.md`. OUT: re-asking after a stale answer (Order 08 drain), the CLI (Order 05), channels (Orders 09-11).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/question_inbox.py, tests/test_question_resume.py
- Item-Dependencies: executed:mtmqlm
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: j0ufrj

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an answer given while a run is live take effect at the next checkpoint, cheaply and in the agent's own context (spec `6kwd2e` R9.3, R9.4, R9.4a, R5.5, R5.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: consume at checkpoints

- [ ] E-01 Add `consume_answers(run_dir, state) -> list[str]` in `runner_shared.py`: for each `awaiting-human` item, read its answers via `question_inbox.read_answers`; when every `gates_verdict` question of the item is answered, recompute the artifact hash and compare with each answer's `artifact_hash`; on mismatch mark the answer `stale` (event + question status `stale`), keep the item parked and do not apply it (R5.6, A12); otherwise set the item `queued`, mark it `resume_with_answers`, and record the answers on the attempt. Call it at the top of the `run_queue` loop on BOTH hosts, after `poll_stop` and before selection, and once before the first dispatch of `run_queue` on start and resume.
  - Depends on: none
  - Expected outcome: an answer written while another item runs moves the parked item to `queued` at the next loop iteration; a stale one does not.
  - Execution state: pending

- [ ] E-02 Give answered items priority: in the selection step, choose a dispatchable `queued` item with `resume_with_answers` before any other, preserving dependency depth as the first key among answered items (`queue_sort_key`).
  - Depends on: E-01
  - Expected outcome: in a 3-item run where item 1 parks and its answer arrives while item 2 runs, item 1 dispatches before item 3 (A43).
  - Execution state: pending

### Task group 2: resume

- [ ] E-03 When dispatching an item marked `resume_with_answers`, build an answer notice listing each question text and the human's answer (and channel), and resume the item's recorded session through `resume_via_launcher` on its preserved lane (the same lane id, base and branch Order 02 recorded). If the host cannot resume (no session id, or the launcher reports the session gone), start a fresh turn on the SAME preserved lane with the notice prepended to the execute or review prompt (R5.5). A parked REVIEW has no per-item lane: Order 02 (`epsti7` E-06) moved its commits to `aw/parked/<run_id>/<id6>` and reset the shared sweep lane, so before resuming a review, fast-forward or merge that branch into the sweep lane (refusing on a dirty sweep lane, as `refresh_sweep_lane` does), then delete the parked branch once the review's output is integrated. Clear `resume_with_answers` and mark the questions `answered` in the inbox only after the turn starts.
  - Depends on: E-02
  - Expected outcome: the resumed turn's argv carries the recorded session id and its prompt carries the answer; with the session removed, a fresh turn runs on the same lane branch and base (A44, A6).
  - Execution state: pending

- [ ] E-04 Re-park if the resumed turn asks again: the Order 02 park branch already handles a new `questions[]`; ensure the earlier answered questions stay `answered` and only new ones are written as open.
  - Depends on: E-03
  - Expected outcome: a scripted resumed turn that returns a second question ends `awaiting-human` with the first question answered and the second open.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_resume.py` on BOTH hosts with the scripted-host pattern: checkpoint consumption mid-run (A43), priority, same-session resume and fresh-turn fallback (A44, A6), staleness (A12), start-of-run drain (answer written before `resume`), re-park, and review semantics after an answer: a resumed review whose finding is not cleared still records NO-GO (A36) and no `- Readiness:` value appears that the resumed review did not itself write (A37). Assert dispatch ORDER from `events.jsonl`, never from timing.
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The `run_queue` loop top already reloads state and runs cheap per-iteration steps (cascade, deferred integration retry); new checkpoint work goes there (`oc_runipd.run_queue` comments).
- Follow-up turns use `runner_shared.resume_via_launcher` so each host keeps exactly two launcher callers (its docstring).
- Preserved lanes are resolved from `preserved_lane_id`/`preserved_base`/`preserved_branch` (spec `6kwd2e` 0.4).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `resume_via_launcher` already serves combined-red and spec-anchor send-backs, so resuming a session mid-run is proven on both hosts.
- Both drivers re-run selection every iteration, so a status flip at the loop top is picked up without new scheduling machinery.

## Proposed changes (ordered, validatable)

1. E-01 consume + staleness. 2. E-02 priority. 3. E-03 resume and fallback. 4. E-04 re-park. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Re-asking a stale question interactively: Order 08.
  - Carrier: jshwxb
- Notifying the human that an answer was consumed: Order 09 (R10.7).
  - Carrier: txl556

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_resume.py tests/test_question_parking.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R9.3, R9.4, R5.5, R5.6 as amended.

## Open questions

### OQ-01: Resume when SOME but not all of an item's questions are answered?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: no, unless every unanswered one has `gates_verdict: false`. A turn resumed with a decision still missing would park again immediately and spend a turn for nothing; non-gating questions do not block resumption (they are still delivered as answered or 'unanswered' in the notice).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the event lines from a scripted run showing `answer-consumed` for the parked item at the checkpoint after the answer was written, and `answer-stale` for the stale case with the item still `awaiting-human` (produced by E-01's `consume_answers` call in `run_queue`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ordered `ipd-started` events showing item 1 resumed before item 3.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the recorded argv of the resumed turn showing the session id, an excerpt of its prompt containing the answer, and for the fallback case the lane branch and base matching the preserved values.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the final question statuses showing the first `answered` and the second `open` after re-park.
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
