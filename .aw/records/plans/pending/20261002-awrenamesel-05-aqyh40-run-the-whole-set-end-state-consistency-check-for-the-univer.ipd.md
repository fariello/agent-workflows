# IPD: Run the whole-Set end-state consistency check for the universal selector Set

- Date: 2026-10-02
- Kind: child
- Concern: THE ORCHESTRATOR `95jk4s` CARRIED A WHOLE-SET VERIFICATION THAT NO CHILD OWNED. Its `Required tests / validation` section requires "The end-state consistency check, run once after all four" (`aw rename plans <a filename>`, `aw group plans <a filename>`, `aw archive plans <a filename>` all resolve, `aw rename plans <a spec path>` refuses), its V-04 demands that check be pasted, and its completion criterion 7 requires a green `python3 -m pytest` for the Set. Orders 01 to 04 each verify their OWN change; none runs the combined end state. The runner retires an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, so as authored that verification would have been reported complete having never run. The orchestrator coverage probe flagged exactly this. This child owns it.
- Scope: Run, read-only, the Set's end-state consistency check and the full suite at a HEAD where Orders 01 to 04 are all executed, and record the pasted evidence here. EXCLUDES any production code, test, spec, or record change: every verb is run in its default PREVIEW mode (no `--apply`), so nothing on disk moves. If any check fails, this plan records the failure and STOPS; the fix belongs to a new corrective IPD against the owning child, never to this file.
- Scope-Paths: .aw/records/plans/pending/20261002-awrenamesel-05-aqyh40-run-the-whole-set-end-state-consistency-check-for-the-univer.ipd.md
- Item-Dependencies: executed:eby93o, executed:87m438, executed:1x4tdo, executed:3qxuw1
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: aqyh40

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): created to own the whole-Set end-state verification the orchestrator `95jk4s` carried with no child covering it, after the orchestrator coverage probe refused `aw agy run` on it. The parent's checklist is left unchanged; this child is added as Order 05 in its child table.

## Goal

Prove, once, at the Set's combined end state, that the plans tree's mutating verbs accept the reader's selector vocabulary and that a foreign-type path is refused, so the orchestrator's retirement rests on observed evidence rather than on the four children's separate claims.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: preconditions

- [ ] E-01 Confirm all four sibling children read `- Status: executed` on disk and record the HEAD under test.
  - Depends on: none
  - Expected outcome: `eby93o`, `87m438`, `1x4tdo`, `3qxuw1` each sit in `.aw/records/plans/executed/` with `- Status: executed`; `git rev-parse --short HEAD` is recorded. If any is not executed, STOP with state `blocked`.
  - Execution state: pending

### Task group 2: end-state consistency check (preview mode only, never `--apply`)

- [ ] E-02 Run `aw rename plans <filename>` and `aw group plans <filename> --set <scratch-set>` against one existing plan addressed by its FILENAME, both without `--apply`.
  - Depends on: E-01
  - Expected outcome: both exit 0 and preview an action on that plan; neither prints `no plan has Id`; `git status --porcelain` is unchanged afterwards.
  - Execution state: pending

- [ ] E-03 Run `aw archive plans <filename>` against a terminal-root plan addressed by its FILENAME, and `aw archive plans <a token matching nothing>`, both without `--apply`.
  - Depends on: E-01
  - Expected outcome: the filename resolves to that plan in the preview; the unmatched token exits NONZERO rather than printing a `CLEAN` banner at exit 0; `git status --porcelain` is unchanged afterwards.
  - Execution state: pending

- [ ] E-04 Run `aw rename plans <a repo-relative SPEC path> --slug zzz` without `--apply`.
  - Depends on: E-01
  - Expected outcome: exits nonzero with a refusal naming the type mismatch / out-of-tree path; the spec file is untouched.
  - Execution state: pending

### Task group 3: suite

- [ ] E-05 Run the full suite bare, `python3 -m pytest`, at the HEAD recorded in E-01.
  - Depends on: E-01
  - Expected outcome: zero failures; the `N passed` summary line is captured verbatim.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw rename plans`, `aw group plans` and `aw archive plans` all default to a PREVIEW and write only with `--apply` (their `--help`: "Apply the change (default is a preview)", "Perform the moves (default is preview only)"), which is what lets this child verify without mutating anything.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` supplies the flags (AGENTS.md).
- An orchestrator holds orchestration, not work of its own; work found on a parent is moved to a CHILD, and the parent's checklist stays (AGENTS.md).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The orchestrator's end-state check was owned by no child. | `95jk4s` `Required tests / validation`: "The end-state consistency check, run once after all four"; its V-04 requires that check pasted; its completion criterion 7 requires a green suite. Orders 01 to 04 each scope their validation to their own module. |
| F-02 | The orchestrator coverage probe refused the run on this parent. | `aw runs`: `[orchestrator-uncovered-work]` for `95jk4s` with remedy "ADD A CHILD for the uncovered work". |
| F-03 | All four siblings are already executed, so this child is immediately dispatchable. | `.aw/records/plans/executed/20260929-awrenamesel-0{1,2,3,4}-*.ipd.md`, each `- Status: executed`. |

## Proposed changes (ordered, validatable)

1. Confirm preconditions (E-01).
2. Run the three plans verbs by filename in preview mode (E-02, E-03).
3. Confirm a foreign-type path is refused (E-04).
4. Run the suite (E-05).

No file other than this plan changes.

## Deferred / out of scope (with reason)

- FIXING ANY FAILURE THIS CHECK FINDS. Declined here: a failure is a defect in an already-executed child, and an executed plan's record may not be rewritten, so the remedy is a new corrective IPD against that child (AGENTS.md execution contract).
  - Carrier-Declined: verification-only child; fixes belong to a corrective IPD.

## Scope check

- Over-scope: none. The single Scope-Path is this plan, which is where the evidence is recorded.
- Under-scope: none known; this covers exactly the parent's end-state check, V-04's pasted evidence, and criterion 7.

## Required tests / validation

The deliverable IS validation: the pasted outputs of E-02 to E-05, plus an unchanged `git status --porcelain` showing the preview runs mutated nothing.

## Spec / documentation sync

N/A: verification only, no behavior change. Spec `z7nbn1` 1.1 is the contract being checked, not amended.

## Open questions

### OQ-01: Should this be folded into the orchestrator instead of a child?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, A CHILD. The runner retires an orchestrator without running its E/V checkpoint, so verification parked on the parent would never run under a runner (AGENTS.md, orchestrator coverage gate).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the four `- Status: executed` lines with their `executed/` paths, and the HEAD short sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste both commands, their full output and exit codes, and `git status --porcelain` before and after showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both commands, their output and exit codes (filename resolves; unmatched token exits nonzero), and `git status --porcelain` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the command, its refusal text and nonzero exit code, and `git status --porcelain -- .aw/records/specs/` showing the spec untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the actual `python3 -m pytest` summary line showing zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Authored `to-review`; requires `/plan-review` and explicit human approval before execution. EXECUTION CONTRACT: run every verb in preview mode only, never `--apply`; record evidence in this file only; commit through `aw commit aqyh40 -- <this plan>`, never push. POST-GATE LIFECYCLE: move to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`. On any failure, set the item `failed`, stop, and open a corrective IPD. Once this child is executed, the orchestrator `95jk4s` may be retired.
