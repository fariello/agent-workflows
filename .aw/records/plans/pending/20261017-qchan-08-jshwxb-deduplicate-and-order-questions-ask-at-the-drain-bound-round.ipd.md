# IPD: Deduplicate and order questions, ask at the drain, bound rounds and runaway escalation

- Date: 2026-10-17
- Kind: child
- Concern: With parking (Order 02), the inbox (Order 03) and live resume (Order 04), a large queue whose siblings ask the same question still makes the human answer it once per artifact, in arbitrary order, and nothing stops a broken prompt from parking every item. Spec `6kwd2e` R4 (cross-queue dedup by driver-computed fingerprint, one answer applied to every raiser, ordering by unblock count then execute-before-review), R4b (runaway-escalation bound), and R5.1-R5.3a (answer file at the drain, terminal ask at the drain when a human is present, bounded re-dispatch rounds) are not yet implemented.
- Scope: IN: grouping open questions by fingerprint across the run (and across the pre-flight batch), applying one answer to every raiser through the shared writer, the R4.3/R4.3a ordering, the R4.4 pre-ask summary, the drain-time terminal ask (reusing Order 07's bounded prompt) with same-run re-dispatch, the round bound (R5.3a), the runaway threshold with a minimum absolute count (R4b) and its distinct exit reporting, and `answers.md` (human-readable, editable list with the resume command) at the drain (R5.1, R5.2). OUT: channels.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/question_inbox.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_question_drain.py
- Item-Dependencies: executed:j0ufrj, executed:4kkcex
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 8
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jshwxb

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Ask each distinct question once, in the order that frees the most work, and stop a run that is escalating everything (spec `6kwd2e` R4, R4b, R5.1-R5.3a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: dedup and order

- [ ] E-01 In `question_inbox`, add `group_open_questions(run_dir) -> list[QuestionGroup]` keyed by fingerprint; questions whose fingerprints match but whose option sets differ are NOT merged (R4.1b). Each group records every raising artifact and its unblock count (the raiser plus its transitive dependents still queued). Order groups by unblock count descending, then execute before review at equal counts (R4.3, R4.3a).
  - Depends on: none
  - Expected outcome: 74 fixture questions sharing one fingerprint form one group naming 74 raisers; a fixture with known unblock counts orders as expected; a review/execute tie puts execute first (A9, A10, A21).
  - Execution state: pending

- [ ] E-02 Make one answer resolve a group: `write_answer` on any member, when the question belongs to a group, writes the same answer for every member (each record naming all members, R4.2) in one locked operation; `aw runs answer` and channels show a group once with its raiser count.
  - Depends on: E-01
  - Expected outcome: answering one member of a 74-member group writes 74 answer files, each listing all 74 artifacts; `aw runs answer` lists it once.
  - Execution state: pending

### Task group 2: the drain

- [ ] E-03 At the drain (no dispatchable item, parked questions exist): write `answers.md` in the run directory listing each group (id, question, options, raisers) with the literal resume command; if `is_interactive_run`, print the R4.4 summary (distinct questions, artifacts affected, unblock counts) and ask each group with Order 07's `prompt_for_free_text`, writing each answer before the next; then run Order 04's consumption and continue the loop in the SAME run. Bound ask-and-redispatch rounds (default 2, `--question-rounds N`); at the bound, stop asking and leave items parked (R5.3, R5.3a).
  - Depends on: E-02
  - Expected outcome: with a TTY fixture answering at the drain, parked items re-dispatch in the same run (no second invocation, A35); a fixture whose resumed turns always ask again stops after 2 rounds and leaves `answers.md` (A26, A34); the resume command in `answers.md` runs.
  - Execution state: pending

- [ ] E-04 Runaway bound (R4b): after each park, if parked/dispatched exceeds a threshold (default 0.5, `--max-park-ratio`) AND parked >= a minimum count (default 5), stop dispatching, print the observed ratio and the diagnosis that a prompt or classification defect is more likely than a real backlog, record a distinct `runaway-escalation` outcome that the summary and exit reporting distinguish from an ordinary parked run (R4b.3), and keep every parked item's lane and questions (R4b.4).
  - Depends on: E-03
  - Expected outcome: a fixture where every worker escalates stops at the threshold with the ratio printed and a summary distinguishable from an ordinary parked run; all parked lanes remain; a 2-item run with 1 parked item does not breach (A22-A25).
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_drain.py` on both hosts covering A9, A10, A17 (pre-flight batch dedup via Order 07's sweep), A20, A21, A22-A26, A33, A34, A35.
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Dependency depth stays the first queue sort key (`queue_sort_key`); answered-group priority (Order 04) applies within it.
- Prompts follow Order 07's bounded free-text prompt; presence via `is_interactive_run` only.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Spec `6kwd2e` R4 rationale: asking 74 questions serially at the drain merely moves the wall the design exists to remove.

## Proposed changes (ordered, validatable)

1. E-01 group and order. 2. E-02 group answers. 3. E-03 drain ask, rounds, answers.md. 4. E-04 runaway bound. 5. E-05 tests.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_drain.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R4, R4b, R5.1-R5.3a.

## Open questions

### OQ-01: Default runaway threshold?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: ratio 0.5 with a minimum of 5 parked items, both flags. R4b.1 asks for a conservative default with a configurable threshold and R4b.5 for an absolute floor; half the dispatched items escalating is far above any legitimate rate seen in this repository's runs, and 5 keeps small queues from tripping it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the grouping output for the 74-raiser fixture, the ordered list for the known-count fixture, and the tie case.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the count of answer files written by one group answer and one file's `artifacts` list length, plus `aw runs answer --no-interactive` listing the group once.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the drain transcript from the TTY fixture showing same-run re-dispatch, the round-bound stop, the `answers.md` contents, and the exit code of running its resume command.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the runaway fixture's stop message with the ratio and the summary line, `git branch --list 'aw/lane/*'` showing parked lanes kept, and the 2-item no-breach result.
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
