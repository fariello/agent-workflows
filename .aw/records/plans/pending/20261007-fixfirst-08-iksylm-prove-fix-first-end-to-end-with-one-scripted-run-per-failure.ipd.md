# IPD: Prove fix first end to end with one scripted run per failure kind

- Date: 2026-10-07
- Kind: child
- Concern: Each child in Set `fixfirst` tests its own failure kind. Nothing tests the Set's promises together: that every agent-caused kind in the amended spec actually reaches a fix-it turn through the real runner, that the message is the shared one, that a proposal stops one item while the run continues, that nothing but a corrupt ledger aborts a run, and that spec, transcription and behavior agree. The orchestrator `lxb1ew` carries these as completion criteria and cannot perform them itself, because the runner retires it without running its checks.
- Scope: Add one end-to-end test module and perform the Set-level measurement: one scripted run per fix-it kind on both hosts, one proposal run, one corrupt-ledger run, a spec-to-code cross-check, and the bare suite. EXCLUDES changing any production behavior; a defect found here is fixed in the owning child's code only if it is a one-line slip, otherwise filed as a backlog item and the plan stops.
- Scope-Paths: tests/test_fixfirst_end_to_end.py
- Item-Dependencies: executed:ytas91, executed:w9nvq4, executed:psgyzw, executed:62sdwr
- Status: draft
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 8
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: iksylm

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Show, with real runs, that the whole Set does what the maintainer asked: agent-caused failures come back to the agent with what went wrong, proposals reach a human, and runs keep going.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the end-to-end matrix

- [ ] E-01 In `tests/test_fixfirst_end_to_end.py`, for each fix-it kind in amended spec `25kzda` 5.5 group (a) that this Set implements (nonzero exit / no outcome, stall, spawn failure, hook refusal at finalize, hook refusal at integration, red merged suite, out-of-scope edit, untooled status change, hook-skipping commit), drive a real `aw oc run` and `aw agy run` with a scripted host that fails that way once and succeeds on the fix-it turn; assert the item ends executed with exactly one correction spent. (Completion criterion 1.)
  - Depends on: none
  - Expected outcome: every kind on both hosts ends executed after one fix-it turn.
  - Execution state: pending

- [ ] E-02 In the same runs, capture each delivered fix-it prompt and assert it contains the shared rule from Order 03 exactly once and the kind's own evidence. (Criterion 2; cross-check that Orders 04 to 07 use `build_fix_it_notice`.)
  - Depends on: E-01
  - Expected outcome: every captured prompt carries the rule once and its evidence.
  - Execution state: pending

- [ ] E-03 Drive a three-item run where item A writes a `material` proposal, item B depends on A, and item C is independent; assert A is `needs-human`, B is `dependency-not-met`, C is executed, the proposal record is on main with A's lane unmerged, and the summary lists it first. (Criterion 3.)
  - Depends on: none
  - Expected outcome: as stated.
  - Execution state: pending

- [ ] E-04 Drive a run with a corrupted `state.json` and assert the run aborts with the ledger reason; drive runs that hit each former abort class this Set touched (hook bypass, push recorded) and assert they do not abort. (Criterion 4.)
  - Depends on: none
  - Expected outcome: only the corrupt-ledger run aborts.
  - Execution state: pending

### Task group 2: the Set-level checks

- [ ] E-05 Cross-check spec, transcription and behavior: for each row of amended spec 5.5's mapping table, record the test case in E-01 to E-04 that exercises it, and confirm `run_evidence.ABORT_CLASSES` equals the spec's 4.1 abort set. Record any row with no exercising case. (Criterion 5.)
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a recorded row-to-test table with no gaps, or each gap filed as a backlog item.
  - Execution state: pending

- [ ] E-06 Run the bare suite and record the result; reproduce any failure at the Set's baseline commit (the parent of `tb6lw3`'s first commit) to classify it as pre-existing. (Criterion 6.)
  - Depends on: E-05
  - Expected outcome: green apart from reproduced pre-existing failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Scripted host: `tests/test_silent_turn_observability.py` `fake_opencode`; both hosts: `tests/test_production_correction_turn.py` `_HOSTS`.
- Tests drive the runner and assert on outcomes (GUIDING_PRINCIPLES P16).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The orchestrator's completion criteria need a performer. | AGENTS.md: the runner retires an orchestrator without its E/V checkpoint; uncovered parent work must be owned by a child. `lxb1ew` criteria 1 to 6 each name this plan. |
| F-02 | Both hosts must be covered; the drivers share `runner_shared` but wire separately. | `tests/test_production_correction_turn.py` iterates `_HOSTS`. |

## Proposed changes (ordered, validatable)

1. Fix-it matrix (E-01).
2. Shared-message check (E-02).
3. Proposal continuation (E-03).
4. Abort set (E-04).
5. Spec-to-test cross-check (E-05).
6. Bare suite (E-06).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none. The one test module is written by E-01 to E-04.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_fixfirst_end_to_end.py -o addopts=""`.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: this plan only measures.

## Open questions

### OQ-01: Should the matrix carry the `slow` marker?

- Blocking: no
- Status: open
- Owner: executor of E-01
- Resolution or deferral rationale: Measure the module's wall time at execution. Keep it in the default run if it adds under about 30 seconds with xdist; otherwise mark the per-host duplicates `slow` and keep one host in the default run, and record the choice.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the module run with one passing case per kind per host.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste one captured prompt per kind (or the asserting test output listing each kind).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the three items' final statuses, the proposal record path on main, and the summary's first lines.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the corrupt-ledger run's exit code and reason and the non-aborting runs' exit codes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the row-to-test table and `run_evidence.ABORT_CLASSES`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare-suite summary line and the baseline reproduction of any failure.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
